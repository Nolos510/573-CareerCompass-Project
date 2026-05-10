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
        ethics = PROJECT_ROOT / "docs" / "ethics.md"

        self.assertIn("Skill gap accuracy", evaluation.read_text(encoding="utf-8"))
        self.assertIn("Data Privacy", ethics.read_text(encoding="utf-8"))

    def test_dockerfile_runs_streamlit(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("streamlit", dockerfile)
        self.assertIn("8501", dockerfile)


if __name__ == "__main__":
    unittest.main()

