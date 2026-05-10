from __future__ import annotations

import argparse
import csv
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


KAGGLE_LINKEDIN_DATASET_URL = "https://www.kaggle.com/datasets/arshkon/linkedin-job-postings"
KAGGLE_LINKEDIN_DATASET_SLUG = "arshkon/linkedin-job-postings"

DEFAULT_ROLE_KEYWORDS = (
    "business analyst",
    "business systems analyst",
    "data analyst",
    "project manager",
    "project coordinator",
    "program manager",
)
DEFAULT_LOCATION_KEYWORDS = (
    "san francisco",
    "bay area",
    "oakland",
    "san jose",
    "pleasanton",
    "remote",
)
SKILL_KEYWORDS = (
    "SQL",
    "Python",
    "Excel",
    "Tableau",
    "Power BI",
    "KPIs",
    "requirements gathering",
    "stakeholder communication",
    "process improvement",
    "process mapping",
    "user acceptance testing",
    "Agile",
    "Scrum",
    "Jira",
    "risk management",
    "scope",
    "milestones",
    "documentation",
    "data analysis",
    "data storytelling",
)


def convert_kaggle_linkedin_dataset(
    source_path: str | Path,
    output_path: str | Path,
    limit: int = 200,
    role_keywords: Iterable[str] = DEFAULT_ROLE_KEYWORDS,
    location_keywords: Iterable[str] = DEFAULT_LOCATION_KEYWORDS,
) -> list[dict[str, Any]]:
    """Convert Kaggle LinkedIn postings into the MVP retrieval JSON shape."""

    source = Path(source_path)
    company_lookup = _load_company_lookup(source)
    postings = []
    for row in _iter_posting_rows(source):
        posting = _normalize_posting(row, company_lookup)
        if not _matches_keywords(posting["role"], role_keywords):
            continue
        if not _matches_location(posting, location_keywords):
            continue
        postings.append(posting)
        if len(postings) >= limit:
            break

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as file:
        json.dump(postings, file, indent=2)
        file.write("\n")
    return postings


def _iter_posting_rows(source: Path) -> Iterable[dict[str, str]]:
    if source.is_file() and source.suffix.lower() == ".zip":
        yield from _iter_posting_rows_from_zip(source)
        return

    csv_path = _find_postings_csv(source)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def _iter_posting_rows_from_zip(source: Path) -> Iterable[dict[str, str]]:
    with zipfile.ZipFile(source) as archive:
        csv_name = _find_postings_member(archive.namelist())
        with archive.open(csv_name) as raw_file:
            text_file = (line.decode("utf-8-sig") for line in raw_file)
            yield from csv.DictReader(text_file)


def _find_postings_csv(source: Path) -> Path:
    if source.is_file() and source.suffix.lower() == ".csv":
        return source

    candidates = [
        source / "postings.csv",
        source / "job_postings.csv",
        source / "jobs" / "postings.csv",
        source / "jobs" / "job_postings.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Expected postings.csv or job_postings.csv in the Kaggle download.")


def _find_postings_member(names: list[str]) -> str:
    for name in names:
        normalized = name.replace("\\", "/").lower()
        if normalized.endswith("/postings.csv") or normalized.endswith("/job_postings.csv"):
            return name
        if normalized in {"postings.csv", "job_postings.csv"}:
            return name
    raise FileNotFoundError("Expected postings.csv or job_postings.csv in the Kaggle zip.")


def _load_company_lookup(source: Path) -> dict[str, str]:
    csv_path = _find_optional_company_csv(source)
    if not csv_path:
        return {}

    lookup = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            company_id = _clean(row.get("company_id"))
            name = _clean(row.get("name") or row.get("company_name"))
            if company_id and name:
                lookup[company_id] = name
    return lookup


def _find_optional_company_csv(source: Path) -> Path | None:
    if source.is_file():
        return None

    candidates = [
        source / "companies.csv",
        source / "company_details" / "companies.csv",
        source / "companies" / "companies.csv",
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _normalize_posting(row: dict[str, str], company_lookup: dict[str, str]) -> dict[str, Any]:
    job_id = _clean(row.get("job_id")) or _clean(row.get("id")) or "unknown"
    role = _clean(row.get("title") or row.get("job_title") or row.get("role")) or "Untitled role"
    company_id = _clean(row.get("company_id"))
    company = (
        _clean(row.get("company_name"))
        or company_lookup.get(company_id, "")
        or "Unknown company"
    )
    location = _clean(row.get("location")) or "Unknown location"
    if _is_remote(row) and "remote" not in location.lower():
        location = f"{location} / Remote"

    description = _clean(row.get("description") or row.get("job_details")) or "No description supplied."
    skills = _extract_skills(" ".join([role, description, _clean(row.get("skills_desc"))]))

    return {
        "id": f"kaggle-linkedin-{job_id}",
        "role": role,
        "company": company,
        "location": location,
        "date": _listed_date(row),
        "skills": skills,
        "description": _truncate(description, 700),
        "source": "Kaggle LinkedIn Job Postings 2023-2024",
        "source_url": KAGGLE_LINKEDIN_DATASET_URL,
    }


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in lowered:
            found.append(skill)
    return found or ["job description analysis"]


def _matches_keywords(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _matches_location(posting: dict[str, Any], keywords: Iterable[str]) -> bool:
    location = posting["location"].lower()
    return any(keyword.lower() in location for keyword in keywords)


def _is_remote(row: dict[str, str]) -> bool:
    remote_allowed = _clean(row.get("remote_allowed")).lower()
    work_type = _clean(row.get("work_type") or row.get("formatted_work_type")).lower()
    return remote_allowed in {"1", "1.0", "true", "yes"} or "remote" in work_type


def _listed_date(row: dict[str, str]) -> str:
    for key in ("listed_time", "original_listed_time"):
        raw_value = _clean(row.get(key))
        if not raw_value:
            continue
        try:
            timestamp = float(raw_value)
        except ValueError:
            continue
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, UTC).date().isoformat()
    return "2024-01-01"


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Kaggle LinkedIn postings for CareerCompass RAG.")
    parser.add_argument("--input", required=True, help="Path to Kaggle zip, folder, postings.csv, or job_postings.csv.")
    parser.add_argument("--output", default="careercompass/data/job_postings.json", help="Output JSON path.")
    parser.add_argument("--limit", type=int, default=200, help="Maximum postings to keep.")
    parser.add_argument("--role", action="append", dest="roles", help="Role keyword to include. Repeatable.")
    parser.add_argument("--location", action="append", dest="locations", help="Location keyword to include. Repeatable.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    postings = convert_kaggle_linkedin_dataset(
        args.input,
        args.output,
        args.limit,
        args.roles or DEFAULT_ROLE_KEYWORDS,
        args.locations or DEFAULT_LOCATION_KEYWORDS,
    )
    print(f"Wrote {len(postings)} normalized postings to {args.output}")


if __name__ == "__main__":
    main()
