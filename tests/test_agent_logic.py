import unittest
from unittest.mock import patch

from careercompass.agent_logic import (
    parse_json_object,
    run_gap_analysis_logic,
    run_interview_evaluation_logic,
    run_market_demand_logic,
    validate_agent_output,
)
from careercompass.agents import _role_profile, create_initial_state
from careercompass.demo_data import SAMPLE_COURSEWORK, SAMPLE_RESUME
from careercompass.llm_client import ModelCallError, call_openai_json, llm_mode_enabled
from careercompass.prompts import build_specialist_prompt


class AgentLogicTest(unittest.TestCase):
    def setUp(self):
        self.state = create_initial_state(
            {
                "resume_text": SAMPLE_RESUME,
                "target_role": "Business Analyst",
                "target_location": "San Francisco Bay Area",
                "timeline_days": 90,
                "coursework": SAMPLE_COURSEWORK,
            }
        )
        self.profile = _role_profile("Business Analyst")

    def test_specialist_prompt_includes_output_contract(self):
        prompt = build_specialist_prompt("gap_analysis", self.state, self.profile)

        self.assertIn("CareerCompass Gap Analysis", prompt)
        self.assertIn("Return JSON", prompt)
        self.assertIn("Severity", prompt)
        self.assertIn("Do not invent credentials", prompt)

    def test_market_and_gap_logic_return_structured_outputs(self):
        skills = run_market_demand_logic(self.state, self.profile)
        gaps = run_gap_analysis_logic(self.state, self.profile)

        self.assertTrue(skills)
        self.assertIn("Skill", skills[0])
        self.assertIn("Demand Signal", skills[0])
        self.assertTrue(gaps)
        self.assertIn(gaps[0]["Severity"], {"High", "Medium", "Low"})
        self.assertIn("First Step", gaps[0])
        self.assertIn("Resume Proof", gaps[0])

    def test_interview_evaluation_scores_empty_answer_as_zero(self):
        result = run_interview_evaluation_logic("Tell me about a project.", "", "STAR")

        self.assertEqual(result["score"], 0)
        self.assertIn("No answer entered", result["feedback"])
        self.assertTrue(result["sample_answer"])

    def test_json_parser_accepts_fenced_model_output(self):
        payload = parse_json_object(
            """```json
            {"market_skills": [{"Skill": "SQL", "Demand Signal": "High", "Evidence": "Common in postings"}]}
            ```"""
        )

        result = validate_agent_output("market_demand", payload)

        self.assertEqual(result[0]["Skill"], "SQL")

    def test_validation_rejects_missing_required_keys(self):
        with self.assertRaises(ValueError):
            validate_agent_output("gap_analysis", {"gap_report": [{"Skill": "Tableau"}]})

    @patch.dict("os.environ", {"CAREERCOMPASS_USE_LLM": ""}, clear=False)
    def test_llm_mode_is_disabled_by_default(self):
        self.assertFalse(llm_mode_enabled())
        self.assertIsNone(call_openai_json("Return JSON"))

    @patch.dict("os.environ", {"CAREERCOMPASS_USE_LLM": "true"}, clear=False)
    def test_llm_mode_requires_api_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(ModelCallError):
                call_openai_json("Return JSON")

    def test_agent_logic_uses_valid_model_json_when_available(self):
        raw_response = (
            '{"market_skills": ['
            '{"Skill": "Tableau", "Demand Signal": "High", "Evidence": "Frequently listed in analyst postings"}'
            "]}"
        )
        with patch("careercompass.agent_logic.call_openai_json", return_value=raw_response):
            skills = run_market_demand_logic(self.state, self.profile)

        self.assertEqual(skills[0]["Skill"], "Tableau")

    def test_agent_logic_falls_back_when_model_json_is_invalid(self):
        with patch("careercompass.agent_logic.call_openai_json", return_value='{"market_skills": [{"Skill": "SQL"}]}'):
            skills = run_market_demand_logic(self.state, self.profile)

        self.assertIn("Demand Signal", skills[0])


if __name__ == "__main__":
    unittest.main()
