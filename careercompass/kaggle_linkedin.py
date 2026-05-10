from __future__ import annotations

import csv
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KAGGLE_DATASET_URL = "https://www.kaggle.com/datasets/arshkon/linkedin-job-postings"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "linkedin-job-postings"
DEFAULT_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "linkedin_job_postings_mvp.json"
TRACKED_SAMPLE_PATH = Path(__file__).resolve().parent / "data" / "job_postings.json"

POSTINGS_FILENAMES = {"postings.csv", "jobs.csv"}
SKILLS_FILENAMES = {"job_skills.csv", "skills.csv"}


def build_mvp_postings_from_kaggle(
    source_path: str | Path,
    limit: int = 2000,
) -> list[dict[str, Any]]:
    """Normalize the Kaggle LinkedIn postings dataset into CareerCompass records.

    The Kaggle dataset is not committed to this repo. Download it locally, then
    run the prep script to create an ignored processed JSON file.
    """

    source = Path(source_path)
    csv_sources = _discover_csv_sources(source)
    postings_rows = _read_first_matching_csv(csv_sources, POSTINGS_FILENAMES)
    skills_by_job = _read_skills_by_job(csv_sources)

    records = []
    for row in postings_rows:
        record = _normalize_posting(row, skills_by_job)
        if record and _is_useful_posting(record):
            records.append(record)
        if len(records) >= limit:
            break

    return records


def write_mvp_postings(
    source_path: str | Path,
    output_path: str | Path = DEFAULT_PROCESSED_PATH,
    limit: int = 2000,
) -> Path:
    postings = build_mvp_postings_from_kaggle(source_path, limit=limit)
    if not postings:
        raise ValueError("No usable LinkedIn postings were found in the Kaggle dataset files.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(postings, indent=2), encoding="utf-8")
    return output


def load_prepared_or_sample_postings() -> tuple[dict[str, Any], ...]:
    path = DEFAULT_PROCESSED_PATH if DEFAULT_PROCESSED_PATH.exists() else TRACKED_SAMPLE_PATH
    with path.open("r", encoding="utf-8") as file:
        return tuple(json.load(file))


def _discover_csv_sources(source_path: Path) -> dict[str, list[dict[str, str]]]:
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        return _read_zip_csvs(source_path)

    if source_path.is_file() and source_path.suffix.lower() == ".csv":
        return {source_path.name.lower(): _read_csv_file(source_path)}

    if source_path.is_dir():
        csv_sources = {}
        for csv_path in source_path.rglob("*.csv"):
            csv_sources[csv_path.name.lower()] = _read_csv_file(csv_path)
        return csv_sources

    raise FileNotFoundError(f"Dataset path not found: {source_path}")


def _read_zip_csvs(zip_path: Path) -> dict[str, list[dict[str, str]]]:
    csv_sources = {}
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with archive.open(name) as file:
                text = file.read().decode("utf-8", errors="ignore").splitlines()
                csv_sources[Path(name).name.lower()] = list(csv.DictReader(text))
    return csv_sources


def _read_csv_file(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        return list(csv.DictReader(file))


def _read_first_matching_csv(
    csv_sources: dict[str, list[dict[str, str]]],
    names: set[str],
) -> list[dict[str, str]]:
    for name, rows in csv_sources.items():
        if name in names:
            return rows

    available = ", ".join(sorted(csv_sources)) or "none"
    expected = ", ".join(sorted(names))
    raise ValueError(f"Expected one of {expected}; found {available}.")


def _read_skills_by_job(csv_sources: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    skills_by_job: dict[str, list[str]] = defaultdict(list)
    for name, rows in csv_sources.items():
        if name not in SKILLS_FILENAMES:
            continue
        for row in rows:
            job_id = _first_value(row, ["job_id", "id", "posting_id"])
            skill = _first_value(row, ["skill_name", "skill", "name"])
            if job_id and skill:
                skills_by_job[job_id].append(skill)
    return skills_by_job


def _normalize_posting(
    row: dict[str, str],
    skills_by_job: dict[str, list[str]],
) -> dict[str, Any] | None:
    job_id = _first_value(row, ["job_id", "id", "posting_id"])
    role = _first_value(row, ["title", "job_title", "role"])
    company = _first_value(row, ["company_name", "company", "company_id"]) or "Unknown company"
    location = _first_value(row, ["location", "formatted_location"]) or "Unknown location"
    date = _first_value(row, ["listed_time", "original_listed_time", "posted_time", "date"]) or "Unknown date"
    description = _first_value(row, ["description", "job_description", "details"]) or ""

    if not job_id or not role or not description:
        return None

    skills = skills_by_job.get(job_id) or _infer_skills_from_text(description)
    return {
        "id": f"linkedin-{job_id}",
        "role": role,
        "company": company,
        "location": location,
        "date": date,
        "skills": _dedupe_preserve_order(skills),
        "description": description.strip(),
    }


def _is_useful_posting(record: dict[str, Any]) -> bool:
    text = f"{record['role']} {record['description']}".lower()
    useful_terms = [
        "analyst",
        "project",
        "program",
        "product",
        "data",
        "business",
        "systems",
        "operations",
    ]
    return any(term in text for term in useful_terms)


def _infer_skills_from_text(text: str) -> list[str]:
    known_skills = [
        "SQL",
        "Python",
        "Tableau",
        "Power BI",
        "Excel",
        "Agile",
        "Scrum",
        "Jira",
        "stakeholder communication",
        "requirements gathering",
        "risk management",
        "KPIs",
    ]
    text_lower = text.lower()
    return [skill for skill in known_skills if skill.lower() in text_lower]


def _first_value(row: dict[str, str], names: Iterable[str]) -> str:
    normalized = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = normalized.get(name.lower())
        if value:
            return value.strip()
    return ""


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)
    return result

