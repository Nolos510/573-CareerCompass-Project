import unittest

from careercompass import AgentState
from careercompass.agents import create_initial_state, run_career_analysis
from careercompass.demo_data import SAMPLE_COURSEWORK, SAMPLE_RESUME


class CareerCompassWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.inputs = {
            "resume_text": SAMPLE_RESUME,
            "target_role": "Business Analyst or Project Manager",
            "target_location": "San Francisco Bay Area",
            "timeline_days": 90,
            "coursework": SAMPLE_COURSEWORK,
        }

    def test_initial_state_matches_shared_contract(self):
        state = create_initial_state(self.inputs)

        self.assertIsInstance(state, dict)
        self.assertEqual(state["target_role"], self.inputs["target_role"])
        self.assertEqual(state["retrieved_job_postings"], [])
        self.assertEqual(state["market_skills"], [])
        self.assertEqual(state["gap_report"], [])
        self.assertEqual(state["workflow_intent"], "full_strategy")
        self.assertTrue(AgentState)

    def test_full_supervisor_workflow_returns_ui_contract(self):
        result = run_career_analysis(self.inputs)

        self.assertEqual(result["target_role"], self.inputs["target_role"])
        self.assertGreater(result["match_percentage"], 0)
        self.assertGreaterEqual(result["gap_counts"]["high"], 1)
        self.assertTrue(result["market_skills"])
        self.assertTrue(result["gap_report"])
        self.assertTrue(result["learning_roadmap"])
        self.assertTrue(result["resume_recommendations"])
        self.assertTrue(result["interview_questions"])
        self.assertIn("CareerCompass Strategy Report", result["final_strategy_report"])
        self.assertEqual(result["agent_trace"][0], "supervisor")
        self.assertEqual(result["agent_trace"][-1], "synthesis")
        self.assertTrue(result["agent_handoffs"])

    def test_resume_only_route_skips_non_resume_agents(self):
        inputs = {**self.inputs, "workflow_intent": "resume_only"}

        result = run_career_analysis(inputs)

        self.assertIn("market_demand", result["agent_trace"])
        self.assertIn("gap_analysis", result["agent_trace"])
        self.assertIn("resume_optimization", result["agent_trace"])
        self.assertNotIn("curriculum", result["agent_trace"])
        self.assertNotIn("interview_simulation", result["agent_trace"])
        self.assertTrue(result["resume_recommendations"])

    def test_handoffs_capture_required_inputs_and_outputs(self):
        result = run_career_analysis(self.inputs)

        for handoff in result["agent_handoffs"]:
            self.assertIn("from_agent", handoff)
            self.assertIn("to_agent", handoff)
            self.assertIn("required_inputs", handoff)
            self.assertIn("expected_outputs", handoff)
            self.assertIn(handoff["status"], {"queued", "completed", "skipped"})


if __name__ == "__main__":
    unittest.main()
