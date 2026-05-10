import unittest
import shutil
import uuid
from pathlib import Path

from careercompass.kaggle_ingest import convert_kaggle_linkedin_dataset
from careercompass.rag import derive_market_skills, retrieval_confidence, retrieve_job_postings


class RagRetrievalTest(unittest.TestCase):
    def test_retrieves_relevant_bay_area_postings(self):
        postings = retrieve_job_postings(
            "Business Analyst or Project Manager",
            "San Francisco Bay Area",
        )

        self.assertGreaterEqual(len(postings), 3)
        self.assertGreater(postings[0]["retrieval_score"], 0)
        self.assertIn("company", postings[0])
        self.assertIn("evidence_summary", postings[0])

    def test_derives_market_skills_from_retrieved_postings(self):
        postings = retrieve_job_postings("Business Analyst", "San Francisco Bay Area")
        skills = derive_market_skills(postings, [])

        skill_names = {item["Skill"] for item in skills}
        self.assertIn("SQL", skill_names)
        self.assertTrue(all("Demand Signal" in item for item in skills))
        self.assertTrue(all("retrieved postings" in item["Evidence"] for item in skills))

    def test_retrieval_confidence_increases_with_evidence(self):
        self.assertLess(retrieval_confidence([]), retrieval_confidence([{"retrieval_score": 5.0}]))

    def test_converts_kaggle_linkedin_postings_to_mvp_shape(self):
        temp_path = Path(__file__).resolve().parents[1] / ".tmp_test_data" / uuid.uuid4().hex
        self.addCleanup(lambda: shutil.rmtree(temp_path, ignore_errors=True))
        temp_path.mkdir(parents=True)
        csv_path = temp_path / "postings.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "job_id,company_name,title,description,location,remote_allowed,listed_time,skills_desc,work_type",
                    "1,Acme,Business Analyst,Build SQL dashboards and gather requirements,San Francisco CA,0,1704067200000,SQL Tableau requirements gathering,Full-time",
                    "2,Other,Warehouse Associate,Pick and pack orders,Sacramento CA,0,1704067200000,,Full-time",
                ]
            ),
            encoding="utf-8",
        )
        output_path = temp_path / "job_postings.json"

        postings = convert_kaggle_linkedin_dataset(csv_path, output_path, limit=10)

        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0]["id"], "kaggle-linkedin-1")
        self.assertEqual(postings[0]["company"], "Acme")
        self.assertIn("SQL", postings[0]["skills"])
        self.assertIn("source_url", postings[0])
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
