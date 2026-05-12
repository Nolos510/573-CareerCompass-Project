import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ProjectArtifactTest(unittest.TestCase):
    def test_deployment_artifacts_exist(self):
        self.assertTrue((PROJECT_ROOT / "Dockerfile").exists())
        self.assertTrue((PROJECT_ROOT / ".dockerignore").exists())
        self.assertTrue((PROJECT_ROOT / "docs" / "deployment.md").exists())

    def test_evaluation_and_ethics_docs_exist(self):
        evaluation = PROJECT_ROOT / "docs" / "evaluation.md"
        evaluation_results = PROJECT_ROOT / "docs" / "evaluation_results.md"
        ethics = PROJECT_ROOT / "docs" / "ethics.md"
        rubric = PROJECT_ROOT / "docs" / "rubric_evidence.md"

        self.assertIn("Skill gap accuracy", evaluation.read_text(encoding="utf-8"))
        self.assertIn("Five local runs", evaluation.read_text(encoding="utf-8"))
        self.assertIn("Average latency", evaluation_results.read_text(encoding="utf-8"))
        self.assertIn("Data Privacy", ethics.read_text(encoding="utf-8"))
        self.assertIn("Track B", rubric.read_text(encoding="utf-8"))

    def test_pytest_config_ignores_nested_local_workspaces(self):
        pytest_config = (PROJECT_ROOT / "pytest.ini").read_text(encoding="utf-8")

        self.assertIn("testpaths = tests", pytest_config)
        self.assertIn("careercompass-dynamic-ui-worktree", pytest_config)
        self.assertIn("careercompass-latest-main-view", pytest_config)
        self.assertIn("tm4-frontend-demo-polish-worktree", pytest_config)

    def test_dockerfile_runs_streamlit(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("streamlit", dockerfile)
        self.assertIn("8501", dockerfile)


if __name__ == "__main__":
    unittest.main()

