import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from careercompass.agent_logic import (
    parse_json_object,
    run_gap_analysis_logic,
    run_interview_evaluation_logic,
    run_market_demand_logic,
    validate_agent_output,
)
from careercompass.agents import _role_profile, create_initial_state, generate_interview_questions
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
        self.assertIn("Return only valid JSON", prompt)
        self.assertIn("If evidence is missing", prompt)
        self.assertIn("Profile market context", prompt)

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

    def test_interview_questions_do_not_dump_custom_scenario_text(self):
        scenario = (
            "Role Product Marketing Designer at a mid-size SaaS company called FlowForge. "
            "FlowForge makes workflow automation software for small teams. They are hiring someone who can create "
            "launch campaigns, improve product onboarding, and collaborate with product managers, designers, and "
            "growth marketers. Interview Context Maya is interviewing for a role where she would help launch new "
            "product features, design marketing assets, and improve conversion from free trial to paid plans."
        )

        questions = generate_interview_questions("Product Marketing Designer", "Jamba Juice", scenario)
        question_text = " ".join(item["question"] for item in questions)

        self.assertGreaterEqual(len(questions), 5)
        self.assertNotIn("Product Marketing Designer at a mid-size SaaS company called FlowForge", question_text)
        self.assertTrue(all(len(item["question"]) < 260 for item in questions))

    def test_product_marketing_scenario_avoids_generic_sql_question(self):
        scenario = (
            "A product marketing candidate needs to design launch campaigns, improve onboarding, and measure "
            "conversion from free trial to paid plans."
        )

        questions = generate_interview_questions("Product Marketing Designer", "Jamba Juice", scenario)
        question_text = " ".join(item["question"].lower() for item in questions)

        self.assertNotIn("use sql", question_text)
        self.assertIn("conversion", question_text)
        self.assertIn("jamba juice", question_text)

    def test_interview_preset_pool_is_expanded(self):
        self.assertGreaterEqual(len(_role_profile("Business Analyst")["interview_scenarios"]), 6)
        self.assertGreaterEqual(len(_role_profile("Project Manager")["interview_scenarios"]), 6)
        self.assertGreaterEqual(len(_role_profile("Business Analyst / Project Manager")["interview_scenarios"]), 6)

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

    def test_validation_rejects_invalid_enum_values(self):
        with self.assertRaises(ValueError):
            validate_agent_output(
                "interview_simulation",
                {
                    "interview_questions": [
                        {
                            "type": "Puzzle",
                            "question": "How would you solve this?",
                            "rubric_focus": "reasoning",
                        }
                    ]
                },
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_llm_mode_is_disabled_by_default(self):
        self.assertFalse(llm_mode_enabled())
        self.assertIsNone(call_openai_json("Return JSON"))

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_llm_mode_is_enabled_by_api_key(self):
        self.assertTrue(llm_mode_enabled())

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "CAREERCOMPASS_LLM_ENABLED": "false"}, clear=True)
    def test_llm_mode_can_be_disabled_explicitly(self):
        self.assertFalse(llm_mode_enabled())

    @patch.dict(os.environ, {"CAREERCOMPASS_USE_LLM": "true"}, clear=True)
    def test_llm_mode_requires_api_key(self):
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

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "CAREERCOMPASS_OPENAI_MODEL": "test-model"}, clear=True)
    def test_openai_success_returns_validated_structured_output(self):
        client = _fake_client(
            {
                "market_skills": [
                    {
                        "Skill": "SQL",
                        "Demand Signal": "High",
                        "Evidence": "Common in analyst postings.",
                    }
                ]
            }
        )

        with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=object)}):
            with patch("careercompass.llm_client._create_openai_client", return_value=client):
                skills = run_market_demand_logic(self.state, self.profile)

        self.assertEqual(skills[0]["Skill"], "SQL")
        self.assertEqual(client.responses.request["model"], "test-model")
        self.assertTrue(client.responses.request["text"]["format"]["strict"])
        self.assertEqual(client.responses.request["text"]["format"]["type"], "json_schema")
        self.assertFalse(self.state["errors"])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_openai_failure_falls_back_and_records_sanitized_error(self):
        client = _failing_client(RuntimeError("bad api_key=sk-secret123"))

        with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=object)}):
            with patch("careercompass.llm_client._create_openai_client", return_value=client):
                skills = run_market_demand_logic(self.state, self.profile)

        self.assertIn("Demand Signal", skills[0])
        self.assertTrue(self.state["errors"])
        self.assertIn("used fallback", self.state["errors"][0])
        self.assertNotIn("sk-secret123", self.state["errors"][0])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_invalid_model_json_falls_back_and_records_error(self):
        client = _fake_client({"gap_report": [{"Skill": "Tableau"}]})

        with patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=object)}):
            with patch("careercompass.llm_client._create_openai_client", return_value=client):
                gaps = run_gap_analysis_logic(self.state, self.profile)

        self.assertEqual(gaps[0]["Skill"], self.profile["gaps"][0][0])
        self.assertTrue(self.state["errors"])


class _FakeResponses:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.request = {}

    def create(self, **kwargs):
        self.request = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=json.dumps(self.payload))


class _FakeClient:
    def __init__(self, responses):
        self.responses = responses


def _fake_client(payload):
    return _FakeClient(_FakeResponses(payload=payload))


def _failing_client(error):
    return _FakeClient(_FakeResponses(error=error))


if __name__ == "__main__":
    unittest.main()
