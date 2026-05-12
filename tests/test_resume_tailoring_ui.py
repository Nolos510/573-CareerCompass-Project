import unittest

from app import (
    build_tailoring_change_summary,
    build_skill_evidence_map,
    build_tailored_resume_draft,
    derive_job_post_keywords,
    extract_resume_education,
    extract_resume_identity,
    friendly_tailoring_error,
    resume_export_allowed,
    resume_format_template_key,
    resume_format_metadata,
    validate_interview_answer,
    validate_job_post_for_tailoring,
    validate_resume_for_analysis,
)
from careercompass.fallbacks import assess_skill_evidence
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

    def test_skill_evidence_map_explains_detected_and_missing_skills(self):
        rows = build_skill_evidence_map(
            analysis=self.analysis,
            resume_text="Skills: SQL\nBuilt a Tableau dashboard to report KPIs to stakeholders.",
            coursework=["Python Programming"],
            job_post=self.job_post + "\nPython required for reporting automation.",
        )
        by_skill = {row["Skill"]: row for row in rows}

        self.assertEqual(by_skill["SQL"]["Resume Evidence"], "Mentioned only")
        self.assertEqual(by_skill["Tableau"]["Resume Evidence"], "Strong evidence")
        self.assertIn("Python", by_skill)
        self.assertEqual(by_skill["Python"]["Found In"], "Coursework")
        self.assertIn("Gap Action", by_skill["Requirements gathering"])

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

    def test_tailored_resume_preserves_contact_and_all_degrees(self):
        saved_resume = """
        Carlo Spampinato
        2180 Greenridge Drive, Richmond, California 94803
        (510) 384-6716
        Knolos510@gmail.com

        PROFESSIONAL EXPERIENCE: A dedicated and experienced professional who balances mission needs with customer satisfaction.
        Highly motivated communicator and problem solver who works well with diverse teams.

        EDUCATION
        June 2019 - Present
        Contra Costa College - In Progress for Business Transfer
        SFSU - Bachelors in Decision Sciences
        SFSU - Bachelors in Information Systems
        SFSU - Bachelors in Business Analytics
        """

        identity = extract_resume_identity(saved_resume)
        education = extract_resume_education(saved_resume)
        tailored = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=saved_resume,
            job_post="Product Marketing Designer\nNeeds stakeholder communication and product marketing.",
            format_name="Experience-forward resume",
        )

        self.assertEqual(identity["name"], "Carlo Spampinato")
        self.assertIn("Knolos510@gmail.com", identity["contact"])
        self.assertIn("(510) 384-6716", identity["contact"])
        self.assertIn("SFSU - Bachelors in Decision Sciences", education)
        self.assertIn("SFSU - Bachelors in Information Systems", tailored)
        self.assertIn("SFSU - Bachelors in Business Analytics", tailored)
        self.assertNotIn("NAME\nEmail | Phone | LinkedIn | Portfolio", tailored)

    def test_resume_format_labels_map_to_template_keys(self):
        self.assertEqual(resume_format_template_key("Project-forward resume"), "Project-forward")
        self.assertEqual(resume_format_template_key("Custom student-supplied template"), "Use my own template")

    def test_empty_resume_validation_blocks_analysis_helper_logic(self):
        self.assertEqual(validate_resume_for_analysis(""), "Add a resume before running analysis.")
        self.assertEqual(validate_resume_for_analysis("Actual resume text"), "")

    def test_empty_interview_answer_validation_blocks_evaluation_helper_logic(self):
        self.assertEqual(
            validate_interview_answer("   "),
            "Write or paste an answer before requesting feedback.",
        )
        self.assertEqual(validate_interview_answer("I used STAR structure."), "")

    def test_job_post_validation_requires_full_posting(self):
        self.assertIn("Paste the job description", validate_job_post_for_tailoring(""))
        self.assertIn("fuller job posting", validate_job_post_for_tailoring("Product Marketing Associate"))

    def test_resume_format_metadata_includes_tradeoffs(self):
        metadata = resume_format_metadata("Project-forward resume", self.analysis, "Project-forward")

        self.assertIn("best_for", metadata)
        self.assertIn("use_when", metadata)
        self.assertIn("avoid_when", metadata)
        self.assertTrue(metadata["sections"])

    def test_tailored_resume_flags_unsupported_keywords_instead_of_inventing_claims(self):
        saved_resume = """
        Maya Rivera
        maya@example.com

        EXPERIENCE
        - Coordinated student club events and wrote weekly member updates.

        EDUCATION
        State University - B.A. Communications
        """
        job_post = """
        Product Marketing Associate
        We need product marketing, positioning, customer insight, campaign strategy,
        conversion optimization, launch planning, and A/B testing experience.
        """
        tailored = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=saved_resume,
            job_post=job_post,
            format_name="Experience-forward resume",
        )
        changes = build_tailoring_change_summary(
            saved_resume=saved_resume,
            analysis=self.analysis,
            job_post=job_post,
        )

        self.assertIn("Maya Rivera", tailored)
        self.assertIn("maya@example.com", tailored)
        self.assertIn("State University - B.A. Communications", tailored)
        self.assertIn("DO NOT ADD UNTIL YOU HAVE EVIDENCE", tailored)
        self.assertIn("A/B testing", tailored)
        self.assertNotIn("Emphasized A/B testing", tailored)
        self.assertTrue(any(row["Safe To Add"] == "Needs evidence" for row in changes))

    def test_missing_claims_do_not_enter_resume_body(self):
        saved_resume = """
        Maya Rivera
        maya@example.com

        EXPERIENCE
        - Coordinated student club events and wrote weekly member updates.

        EDUCATION
        State University - B.A. Communications
        """
        selected = [
            {
                "before": "Resume evidence not found",
                "after": "Built a campaign performance dashboard for a launch copy experiment.",
                "keywords_added": ["Campaign performance", "Launch copy", "A/B testing"],
            }
        ]
        tailored = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=saved_resume,
            job_post="Product Marketing Associate\nNeeds campaign performance, launch copy, and A/B testing.",
            format_name="Experience-forward resume",
            selected_suggestions=selected,
        )
        resume_body = tailored.split("DO NOT ADD UNTIL YOU HAVE EVIDENCE")[0]

        self.assertNotIn("Built a campaign performance dashboard", resume_body)
        self.assertIn("DO NOT ADD UNTIL YOU HAVE EVIDENCE", tailored)

    def test_safe_edits_only_excludes_mentioned_suggestions_from_body(self):
        saved_resume = """
        Jordan Lee
        jordan@example.com

        SKILLS
        Product marketing

        EXPERIENCE
        - Coordinated student club events and wrote weekly member updates.
        """
        selected = [
            {
                "before": "Coordinated student club events and wrote weekly member updates.",
                "after": "Developed a product marketing brief for a student club launch.",
                "keywords_added": ["Product marketing"],
            }
        ]
        relaxed = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=saved_resume,
            job_post="Product Marketing Associate\nNeeds product marketing experience.",
            format_name="Experience-forward resume",
            selected_suggestions=selected,
            safe_edits_only=False,
        )
        strict = build_tailored_resume_draft(
            analysis=self.analysis,
            saved_resume=saved_resume,
            job_post="Product Marketing Associate\nNeeds product marketing experience.",
            format_name="Experience-forward resume",
            selected_suggestions=selected,
            safe_edits_only=True,
        )

        self.assertIn("Developed a product marketing brief", relaxed.split("DO NOT ADD UNTIL YOU HAVE EVIDENCE")[0])
        self.assertNotIn("Developed a product marketing brief", strict.split("DO NOT ADD UNTIL YOU HAVE EVIDENCE")[0])

    def test_keyword_extraction_filters_generic_noise(self):
        job_post = """
        Product Marketing Associate
        The product marketing associate will support product marketing analysis and product work.
        Own go-to-market planning, positioning, launch copy, campaign performance, customer research,
        content calendar work, conversion funnel reviews, A/B testing, and Figma collaboration.
        """
        names = {item["Keyword"] for item in derive_job_post_keywords(job_post, self.analysis)}

        self.assertIn("Go-to-market", names)
        self.assertIn("Positioning", names)
        self.assertIn("A/B testing", names)
        self.assertNotIn("product", names)
        self.assertNotIn("marketing", names)
        self.assertNotIn("analysis", names)
        self.assertNotIn("associate", names)

    def test_ab_testing_not_strong_from_figma_wireframes(self):
        evidence = assess_skill_evidence(
            "A/B testing",
            "Built Figma wireframes to improve conversion from free trial to paid plans.",
            [],
        )

        self.assertNotEqual(evidence["status"], "Strong Evidence")

    def test_export_gate_requires_review_when_unsupported_claims_exist(self):
        rows = [{"Safe To Add": "Yes"}, {"Safe To Add": "Needs evidence"}]

        self.assertFalse(resume_export_allowed(rows, reviewed=False))
        self.assertTrue(resume_export_allowed(rows, reviewed=True))
        self.assertTrue(resume_export_allowed([{"Safe To Add": "Yes"}], reviewed=False))

    def test_friendly_tailoring_error_is_recoverable_copy(self):
        message = friendly_tailoring_error(RuntimeError("session state crash"))

        self.assertIn("recoverable", message)
        self.assertIn("Generate tailored resume", message)


if __name__ == "__main__":
    unittest.main()
