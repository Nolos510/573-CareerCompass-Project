import csv
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from careercompass.kaggle_linkedin import build_mvp_postings_from_kaggle, write_mvp_postings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_TMP_ROOT = PROJECT_ROOT / ".tmp" / "kaggle_tests"


class KaggleLinkedInPrepTest(unittest.TestCase):
    def setUp(self):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)

    def test_builds_mvp_postings_from_extracted_csvs(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as tmp:
            root = Path(tmp)
            self._write_postings_csv(root / "postings.csv")
            self._write_skills_csv(root / "job_skills.csv")

            postings = build_mvp_postings_from_kaggle(root)

        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0]["id"], "linkedin-1001")
        self.assertEqual(postings[0]["role"], "Business Analyst")
        self.assertIn("SQL", postings[0]["skills"])
        self.assertIn("Tableau", postings[0]["skills"])

    def test_builds_mvp_postings_from_zip_download(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as tmp:
            root = Path(tmp)
            zip_path = root / "linkedin-job-postings.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("postings.csv", self._postings_csv_text())
                archive.writestr("job_skills.csv", self._skills_csv_text())

            postings = build_mvp_postings_from_kaggle(zip_path)

        self.assertEqual(postings[0]["company"], "Salesforce")
        self.assertEqual(postings[0]["location"], "San Francisco Bay Area")

    def test_write_mvp_postings_creates_processed_json(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT) as tmp:
            root = Path(tmp)
            self._write_postings_csv(root / "postings.csv")
            output = root / "processed" / "linkedin_job_postings_mvp.json"

            written = write_mvp_postings(root, output, limit=1)

            self.assertTrue(written.exists())
            self.assertIn("Business Analyst", written.read_text(encoding="utf-8"))

    def _write_postings_csv(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["job_id", "title", "company_name", "location", "listed_time", "description"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "job_id": "1001",
                    "title": "Business Analyst",
                    "company_name": "Salesforce",
                    "location": "San Francisco Bay Area",
                    "listed_time": "2026-05-01",
                    "description": "Analyze KPIs with SQL and Tableau for stakeholder reporting.",
                }
            )

    def _write_skills_csv(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["job_id", "skill_name"])
            writer.writeheader()
            writer.writerow({"job_id": "1001", "skill_name": "SQL"})
            writer.writerow({"job_id": "1001", "skill_name": "Tableau"})

    def _postings_csv_text(self) -> str:
        return (
            "job_id,title,company_name,location,listed_time,description\n"
            "1001,Business Analyst,Salesforce,San Francisco Bay Area,2026-05-01,"
            "\"Analyze KPIs with SQL and Tableau for stakeholder reporting.\"\n"
        )

    def _skills_csv_text(self) -> str:
        return "job_id,skill_name\n1001,SQL\n1001,Tableau\n"


if __name__ == "__main__":
    unittest.main()
