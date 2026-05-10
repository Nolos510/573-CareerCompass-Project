import unittest

from careercompass.rag import (
    available_coursework_options,
    available_target_roles,
    derive_market_skills,
    load_job_postings,
    retrieval_confidence,
    retrieve_job_postings,
)


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

    def test_role_options_include_all_dataset_roles(self):
        dataset_roles = {posting["role"] for posting in load_job_postings()}

        self.assertTrue(dataset_roles.issubset(set(available_target_roles())))

    def test_coursework_options_expand_from_dataset_skills(self):
        options = set(available_coursework_options())

        self.assertIn("Data Visualization", options)
        self.assertIn("Agile Project Management", options)
        self.assertIn("Requirements Engineering", options)


if __name__ == "__main__":
    unittest.main()
