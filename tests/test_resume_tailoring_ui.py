import unittest

from app import (
    build_tailored_resume_draft,
    derive_job_post_keywords,
    resume_format_template_key,
)
from careercompass.agents import run_career_analysis
from careercompass.demo_data import SAMPLE_COURSEWORK, SAMPLE_RESUME


class ResumeTailoringUiTest(unittest.TestCase):
    def setUp(self):
        self.analysis = run_career_analysis(
            {
                "resume_text": SAMPLE_RESUME,
                "target_role": "Business Analyst",
                "target_location": "San Francisco Bay Area",
                "timeline_days": 90,
                "coursework": SAMPLE_COURSEWORK,
            }
        )
        self.job_post = """
        Business Analyst
        We need a candidate who can gather requirements, build SQL reports, create Tableau dashboards,
        communicate with stakeholders, document acceptance criteria, and improve operational workflows.
        """

    def test_job_post_keywords_are_derived_from_pasted_description(self):
        keywords = derive_job_post_keywords(self.job_post, self.analysis)
        names = {item["Keyword"] for item in keywords}

        self.assertIn("SQL", names)
        self.assertIn("Tableau", names)
        self.assertIn("Requirements gathering", names)

    def test_tailored_resume_uses_saved_resume_and_job_post(self):
        tailored = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=SAMPLE_RESUME,
            job_post=self.job_post,
            format_name="Project-forward resume",
        )

        self.assertIn("Business Analyst", tailored)
        self.assertIn("SQL", tailored)
        self.assertIn("Tableau", tailored)
        self.assertIn("PROJECT EXPERIENCE", tailored)
        self.assertIn("Designed a database schema", tailored)

    def test_resume_format_labels_map_to_template_keys(self):
        self.assertEqual(resume_format_template_key("Project-forward resume"), "Project-forward")
        self.assertEqual(resume_format_template_key("Custom student-supplied template"), "Use my own template")


if __name__ == "__main__":
    unittest.main()
