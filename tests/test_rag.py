import unittest

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


if __name__ == "__main__":
    unittest.main()
