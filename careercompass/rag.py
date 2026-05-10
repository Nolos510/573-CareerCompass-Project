from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from typing import Any

from careercompass.kaggle_linkedin import load_prepared_or_sample_postings


def retrieve_job_postings(
    target_role: str,
    target_location: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve local job postings for the MVP RAG lane.

    This is a deterministic lexical retriever. It gives the UI and agents real
    retrieved evidence now, while leaving room for ChromaDB/vector search later.
    """

    query_tokens = _tokenize(f"{target_role} {target_location}")
    scored = []
    for posting in load_job_postings():
        haystack = " ".join(
            [
                posting["role"],
                posting["company"],
                posting["location"],
                posting["description"],
                " ".join(posting["skills"]),
            ]
        )
        score = _score_posting(query_tokens, _tokenize(haystack), target_role, target_location, posting)
        if score > 0:
            scored.append((score, posting))

    scored.sort(key=lambda item: (-item[0], item[1]["date"], item[1]["company"]))
    return [
        {
            **posting,
            "retrieval_score": round(score, 2),
            "evidence_summary": _evidence_summary(posting),
        }
        for score, posting in scored[:limit]
    ]


def derive_market_skills(
    retrieved_postings: list[dict[str, Any]],
    fallback_profile_skills: list[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    if not retrieved_postings:
        return [
            {"Skill": skill, "Demand Signal": demand, "Evidence": evidence}
            for skill, demand, evidence in fallback_profile_skills
        ]

    skill_counter: Counter[str] = Counter()
    skill_examples: dict[str, list[str]] = {}
    for posting in retrieved_postings:
        for skill in posting.get("skills", []):
            normalized = _normalize_skill(skill)
            skill_counter[normalized] += 1
            skill_examples.setdefault(normalized, []).append(
                f"{posting['company']} {posting['role']}"
            )

    rows = []
    posting_count = len(retrieved_postings)
    for skill, count in skill_counter.most_common(8):
        examples = ", ".join(skill_examples[skill][:2])
        rows.append(
            {
                "Skill": skill,
                "Demand Signal": _demand_signal(count, posting_count),
                "Evidence": f"Mentioned in {count} of {posting_count} retrieved postings, including {examples}.",
            }
        )
    return rows


def retrieval_confidence(retrieved_postings: list[dict[str, Any]]) -> float:
    if not retrieved_postings:
        return 0.35
    average_score = sum(posting["retrieval_score"] for posting in retrieved_postings) / len(retrieved_postings)
    return round(min(0.9, 0.55 + average_score / 20), 2)


@lru_cache(maxsize=1)
def load_job_postings() -> tuple[dict[str, Any], ...]:
    return load_prepared_or_sample_postings()


def _score_posting(
    query_tokens: set[str],
    posting_tokens: set[str],
    target_role: str,
    target_location: str,
    posting: dict[str, Any],
) -> float:
    overlap = len(query_tokens.intersection(posting_tokens))
    score = float(overlap)

    role_text = posting["role"].lower()
    target_role_lower = target_role.lower()
    if "business analyst" in target_role_lower and "analyst" in role_text:
        score += 3
    if "project" in target_role_lower and ("project" in role_text or "coordinator" in role_text):
        score += 3

    location = target_location.lower()
    posting_location = posting["location"].lower()
    if "bay area" in location and ("bay area" in posting_location or "san francisco" in posting_location):
        score += 2
    if "remote" in location and "remote" in posting_location:
        score += 2

    return score


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in {"and", "the", "for", "with", "into"}
    }


def _normalize_skill(skill: str) -> str:
    aliases = {
        "data storytelling": "stakeholder communication",
        "presentation": "stakeholder communication",
        "timeline management": "milestones",
        "scrum": "Agile",
    }
    return aliases.get(skill.lower(), skill)


def _demand_signal(count: int, posting_count: int) -> str:
    ratio = count / max(posting_count, 1)
    if ratio >= 0.65:
        return "Very high"
    if ratio >= 0.4:
        return "High"
    if ratio >= 0.2:
        return "Medium"
    return "Low"


def _evidence_summary(posting: dict[str, Any]) -> str:
    skills = ", ".join(posting["skills"][:5])
    return f"{posting['company']} {posting['role']} highlights {skills}."
