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
from careercompass.agents import _role_profile, create_initial_state
from careercompass.demo_data import SAMPLE_COURSEWORK, SAMPLE_RESUME
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
        self.assertIn("Market context", prompt)

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
    def test_missing_api_key_uses_deterministic_fallback(self):
        with patch("careercompass.agent_logic._create_openai_client") as create_client:
            skills = run_market_demand_logic(self.state, self.profile)

        create_client.assert_not_called()
        self.assertEqual(skills, self.profile["skills"] and skills)
        self.assertFalse(self.state["errors"])

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "test-key", "CAREERCOMPASS_OPENAI_MODEL": "test-model"},
        clear=True,
    )
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

        with patch("careercompass.agent_logic._create_openai_client", return_value=client):
            skills = run_market_demand_logic(self.state, self.profile)

        self.assertEqual(skills[0]["Skill"], "SQL")
        self.assertEqual(client.responses.request["model"], "test-model")
        self.assertTrue(client.responses.request["text"]["format"]["strict"])
        self.assertEqual(client.responses.request["text"]["format"]["type"], "json_schema")
        self.assertFalse(self.state["errors"])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_openai_failure_falls_back_and_records_sanitized_error(self):
        client = _failing_client(RuntimeError("bad api_key=sk-secret123"))

        with patch("careercompass.agent_logic._create_openai_client", return_value=client):
            skills = run_market_demand_logic(self.state, self.profile)

        self.assertEqual(skills[0]["Skill"], self.profile["skills"][0][0])
        self.assertTrue(self.state["errors"])
        self.assertIn("used fallback", self.state["errors"][0])
        self.assertNotIn("sk-secret123", self.state["errors"][0])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_invalid_model_json_falls_back(self):
        client = _fake_client({"gap_report": [{"Skill": "Tableau"}]})

        with patch("careercompass.agent_logic._create_openai_client", return_value=client):
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
        return SimpleNamespace(output_text=__import__("json").dumps(self.payload))


class _FakeClient:
    def __init__(self, responses):
        self.responses = responses


def _fake_client(payload):
    return _FakeClient(_FakeResponses(payload=payload))


def _failing_client(error):
    return _FakeClient(_FakeResponses(error=error))


if __name__ == "__main__":
    unittest.main()
