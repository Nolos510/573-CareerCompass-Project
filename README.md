# 573-CareerCompass-Project

An Agentic AI System for Personalized Career Strategy and Skill Development.

## CareerCompass Streamlit MVP

CareerCompass is a class demo for an agentic AI career strategy system. This MVP uses Streamlit to show the planned end-to-end user journey for a recent MIS graduate targeting Business Analyst roles in San Francisco.

The current implementation includes a LangGraph-ready supervisor workflow with deterministic fallbacks so the UI, demo flow, and final-report evidence can run before API keys or live data sources are connected.

## Run Locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

On this machine, the app is currently running with Anaconda Python:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

Local URL:

```text
http://localhost:8503
```

## Demo Path

1. Open the app.
2. Keep the default target role, location, and 90-day timeline.
3. Use the sample resume text or paste your own.
4. Click **Run CareerCompass analysis**.
5. Review the dashboard, skill gaps, roadmap, resume suggestions, interview practice, and final report.

## Architecture Notes

- `careercompass/state.py` defines the shared `AgentState` and inter-agent handoff schema.
- `careercompass/agents.py` owns supervisor orchestration and Streamlit-facing output assembly.
- `careercompass/agent_logic.py`, `careercompass/prompts.py`, `careercompass/schemas.py`, and `careercompass/fallbacks.py` are the agent-logic handoff points for replacing demo behavior with real model calls.
- `careercompass/rag.py` retrieves local job-posting evidence and derives market skill signals for the Market Demand Agent.
- The existing remote `RAG/` folder is preserved for teammate RAG pipeline work.
- [Architecture handoff](docs/ARCHITECTURE_HANDOFF.md)
- [Data notes](docs/data_notes.md)
- [Demo flow](docs/demo_flow.md)
- [Video script](docs/demo_script.md)

## Next Integration Step

Wire `careercompass/agent_logic.py` to OpenAI or Anthropic calls, validate the returned JSON against the schemas, and keep the same UI output contract.

## Project Governance

- [Branch protection and workflow rules](docs/BRANCH_RULES.md)
- [Git sync workflow for this repo](docs/GIT_SYNC_WORKFLOW.md)
- [CareerCompass team development split](docs/CAREERCOMPASS_TEAM_DEV_SPLIT.md)
- [Reusable group project SOP template](docs/GROUP_PROJECT_SOP_TEMPLATE.md)

