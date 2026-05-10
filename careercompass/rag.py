from __future__ import annotations

import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parent / "data" / "job_postings.json"

COURSEWORK_BY_SKILL = {
    "Agile": ["Agile Project Management", "Scrum Fundamentals"],
    "Excel": ["Advanced Excel", "Spreadsheet Modeling"],
    "Jira": ["Project Management Tools", "Jira Fundamentals"],
    "KPIs": ["Business Analytics", "Performance Measurement"],
    "Power BI": ["Business Intelligence", "Data Visualization"],
    "Python": ["Python Programming", "Data Analysis with Python"],
    "SQL": ["Database Systems", "SQL for Data Analysis"],
    "Tableau": ["Data Visualization", "Business Intelligence"],
    "business process": ["Business Process Management", "Operations Management"],
    "data analysis": ["Business Analytics", "Statistics"],
    "data storytelling": ["Data Storytelling", "Business Communication"],
    "documentation": ["Technical Writing", "Business Communication"],
    "experimentation": ["Experimentation and A/B Testing", "Statistics"],
    "milestones": ["Project Management", "Project Scheduling"],
    "presentation": ["Business Communication", "Presentation Skills"],
    "process improvement": ["Process Improvement", "Operations Management"],
    "process mapping": ["Business Process Modeling", "Systems Analysis and Design"],
    "project coordination": ["Project Management", "Project Coordination"],
    "requirements gathering": ["Requirements Engineering", "Systems Analysis and Design"],
    "risk management": ["Risk Management", "Project Management"],
    "scope": ["Project Scope Management", "Project Management"],
    "stakeholder communication": ["Stakeholder Communication", "Business Communication"],
    "timeline management": ["Project Scheduling", "Project Management"],
    "user acceptance testing": ["User Acceptance Testing", "Quality Assurance"],
}

BASE_COURSEWORK_OPTIONS = [
    "Database Systems",
    "Business Analytics",
    "Project Management",
    "Systems Analysis and Design",
    "Python Programming",
    "Information Security",
    "Operations Management",
]


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


def available_target_roles() -> list[str]:
    return sorted({posting["role"] for posting in load_job_postings()})


def available_locations() -> list[str]:
    return sorted({posting["location"] for posting in load_job_postings()})


def available_skills() -> list[str]:
    return sorted({skill for posting in load_job_postings() for skill in posting.get("skills", [])})


def available_coursework_options() -> list[str]:
    options = set(BASE_COURSEWORK_OPTIONS)
    for skill in available_skills():
        options.update(COURSEWORK_BY_SKILL.get(skill, []))
    return sorted(options)


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
    mention_counter: Counter[str] = Counter()
    skill_examples: dict[str, list[str]] = {}
    for posting in retrieved_postings:
        retrieval_score = max(float(posting.get("retrieval_score", 1.0)), 1.0)
        weight = retrieval_score * retrieval_score
        for skill in posting.get("skills", []):
            normalized = _normalize_skill(skill)
            skill_counter[normalized] += weight
            mention_counter[normalized] += 1
            skill_examples.setdefault(normalized, []).append(
                f"{posting['company']} {posting['role']}"
            )

    rows = []
    posting_count = len(retrieved_postings)
    for skill, _weighted_count in skill_counter.most_common(8):
        count = mention_counter[skill]
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
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return tuple(json.load(file))


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
    if target_role_lower == role_text:
        score += 12
    if "data analyst" in target_role_lower and "data analyst" in role_text:
        score += 5
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
