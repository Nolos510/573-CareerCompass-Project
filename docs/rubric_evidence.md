# CareerCompass Rubric Evidence Map

Primary rubric source: `AI Agent Group Project.pdf`.

## Requirement Coverage

| Rubric area | Weight | Evidence in project |
| --- | ---: | --- |
| Agent Architecture & Implementation | 35% | LangGraph-ready supervisor, five specialist agents, synthesis node, typed shared state, structured handoffs, OpenAI structured-output hook, deterministic fallbacks, and tests. |
| Business Value & Relevance | 20% | Clear student/career-center use case: resume plus coursework plus target role becomes a practical 90-day career strategy. |
| Container & Deployment Strategy | 15% | `Dockerfile`, `.dockerignore`, local and Docker run instructions, optional LLM environment variables, and deterministic fallback mode. |
| Ethical Consideration | 15% | Privacy, bias, overconfidence, human review, resume authenticity, confidence scores, retrieved evidence, and visible Responsible AI audit panel. |
| Documentation & Presentation | 15% | README, build spec, architecture handoff, data notes, demo flow, video script, evaluation plan/results, ethics, and deployment docs. |

## Track B Evidence

CareerCompass is framed as Track B: Agentic AI System.

- Supervisor routes shared state through Market Demand, Gap Analysis, Curriculum, Resume Optimization, and Interview Simulation agents.
- Inter-agent handoffs are captured with source agent, target agent, required inputs, expected outputs, reason, and status.
- The synthesis node produces a student-facing strategy report from specialist outputs.
- The Streamlit app exposes agent coordination evidence in the dashboard and Rubric Evidence view.

## Remaining Submission Tasks

- Verify Docker build/run before packaging.
- Capture final screenshots under `docs/screenshots/`.
- Record the 5-minute video demo using `docs/demo_script.md`.
- Reference `docs/evaluation_results.md` in the final report.
