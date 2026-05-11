import unittest
from importlib.util import find_spec

from careercompass import AgentState, CareerStrategyOutput
from careercompass.agents import (
    DeterministicCareerWorkflow,
    OUTPUT_CONTRACT_VERSION,
    build_supervisor_workflow,
    create_initial_state,
    run_career_analysis,
    validate_final_output,
)
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

    def test_build_supervisor_workflow_uses_langgraph_when_installed(self):
        if find_spec("langgraph") is None:
            self.skipTest("LangGraph is not installed in this Python environment.")

        workflow = build_supervisor_workflow()

        self.assertNotIsInstance(workflow, DeterministicCareerWorkflow)
        self.assertEqual(type(workflow).__module__, "langgraph.graph.state")
        self.assertTrue(hasattr(workflow, "invoke"))

        final_state = workflow.invoke(create_initial_state(self.inputs))
        self.assertEqual(final_state["final_output"]["output_contract_version"], OUTPUT_CONTRACT_VERSION)
        self.assertEqual(final_state["completed_agents"][0], "supervisor")
        self.assertEqual(final_state["completed_agents"][-1], "synthesis")

    def test_full_supervisor_workflow_returns_ui_contract(self):
        result = run_career_analysis(self.inputs)

        self.assertEqual(result["target_role"], self.inputs["target_role"])
        self.assertGreater(result["match_percentage"], 0)
        self.assertGreaterEqual(result["gap_counts"]["high"], 1)
        self.assertTrue(result["market_skills"])
        self.assertTrue(result["retrieved_job_postings"])
        self.assertTrue(result["gap_report"])
        self.assertTrue(result["learning_roadmap"])
        self.assertTrue(result["resume_recommendations"])
        self.assertTrue(result["interview_questions"])
        self.assertIn("CareerCompass Strategy Report", result["final_strategy_report"])
        self.assertEqual(result["output_contract_version"], OUTPUT_CONTRACT_VERSION)
        self.assertEqual(result["workflow_intent"], "full_strategy")
        self.assertTrue(result["route_plan"])
        self.assertEqual(result["agent_trace"][0], "supervisor")
        self.assertEqual(result["agent_trace"][-1], "synthesis")
        self.assertTrue(result["agent_handoffs"])
        self.assertTrue(CareerStrategyOutput)
        validate_final_output(result)

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

        self.assertFalse(
            [handoff for handoff in result["agent_handoffs"] if handoff["status"] == "queued"]
        )

    def test_workflow_intents_have_expected_routes(self):
        expected_routes = {
            "full_strategy": [
                "market_demand",
                "gap_analysis",
                "curriculum",
                "resume_optimization",
                "interview_simulation",
            ],
            "resume_only": ["market_demand", "gap_analysis", "resume_optimization"],
            "interview_only": ["market_demand", "gap_analysis", "interview_simulation"],
        }

        for intent, route in expected_routes.items():
            with self.subTest(intent=intent):
                result = run_career_analysis({**self.inputs, "workflow_intent": intent})

                self.assertEqual(result["workflow_intent"], intent)
                self.assertEqual(result["route_plan"], route)
                self.assertEqual(result["agent_trace"], ["supervisor", *route, "synthesis"])
                validate_final_output(result)

    def test_final_output_validation_rejects_incomplete_contract(self):
        result = run_career_analysis(self.inputs)
        incomplete = dict(result)
        incomplete.pop("agent_trace")

        with self.assertRaises(ValueError):
            validate_final_output(incomplete)

    def test_existing_tableau_evidence_reduces_tableau_gap_priority(self):
        result = run_career_analysis(
            {
                **self.inputs,
                "resume_text": (
                    self.inputs["resume_text"]
                    + "\nBuilt a Tableau dashboard with KPIs and stakeholder recommendations."
                ),
                "coursework": [*self.inputs["coursework"], "Data Visualization"],
            }
        )

        tableau_gap = next(
            gap for gap in result["gap_report"] if gap["Skill"].lower() == "tableau"
        )
        self.assertEqual(tableau_gap["Severity"], "Low")
        self.assertNotEqual(result["gap_report"][0]["Skill"], "Tableau")

    def test_data_analyst_target_uses_retrieved_data_skills(self):
        result = run_career_analysis(
            {
                **self.inputs,
                "target_role": "Data Analyst",
                "resume_text": "Python coursework, statistics project, and SQL analysis portfolio.",
                "coursework": ["Python Programming", "Statistics", "SQL for Data Analysis"],
            }
        )

        skill_names = {skill["Skill"] for skill in result["market_skills"]}
        self.assertIn("Python", skill_names)
        self.assertIn("experimentation", skill_names)

    def test_strong_skill_evidence_improves_keyword_coverage(self):
        mentioned_result = run_career_analysis(
            {
                **self.inputs,
                "target_role": "Data Analyst",
                "resume_text": "Skills: SQL, Python, Tableau.",
                "coursework": [],
            }
        )
        strong_result = run_career_analysis(
            {
                **self.inputs,
                "target_role": "Data Analyst",
                "resume_text": (
                    "Built SQL reports with joins and CTEs for weekly operations. "
                    "Automated reporting with a Python script and presented Tableau dashboards to stakeholders."
                ),
                "coursework": [],
            }
        )

        self.assertGreater(
            strong_result["keyword_coverage"],
            mentioned_result["keyword_coverage"],
        )

    def test_missing_high_demand_skills_remain_priority_gaps(self):
        result = run_career_analysis(
            {
                **self.inputs,
                "target_role": "Data Analyst",
                "resume_text": "Customer service and team leadership experience.",
                "coursework": [],
            }
        )

        self.assertIn(result["gap_report"][0]["Severity"], {"High", "Medium"})
        self.assertNotEqual(result["gap_report"][0]["Current Evidence"].split(":", 1)[0], "Strong evidence found")

    def test_unknown_custom_role_still_returns_complete_output(self):
        result = run_career_analysis(
            {
                **self.inputs,
                "target_role": "Product Analyst",
                "target_location": "Remote",
                "coursework": ["Product Analytics", "SQL for Data Analysis"],
            }
        )

        self.assertEqual(result["target_role"], "Product Analyst")
        self.assertTrue(result["market_skills"])
        self.assertTrue(result["gap_report"])
        validate_final_output(result)


if __name__ == "__main__":
    unittest.main()
