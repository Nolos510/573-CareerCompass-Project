# CareerCompass Team Development Split

This document defines who owns which part of CareerCompass, how branches should be named, and how teammates can take over a lane when they are ready.

The goal is to keep the project moving without creating merge chaos.

## Current Team Lanes

| Person | Role | Branch Pattern | Status | Owns |
| --- | --- | --- | --- | --- |
| Carlo | Architect / Integration | `carlo-architecture-*` | Finalizing | LangGraph supervisor, shared state, integration |
| Nhi | RAG / Data | `nhi-rag-data-*` | Started | Job postings, ChromaDB/vector search, retrieved evidence |
| TM3 | Agent Logic | `tm3-agent-logic-*` | Started | OpenAI prompts, JSON outputs, fallback behavior |
| TM4 | Frontend / Demo | `tm4-frontend-demo-*` | Started | Streamlit polish, screenshots, video flow |
| TM5 | Evaluation / Deployment | `tm5-eval-deploy-*` | Started | Docker, metrics table, ethics, final report support |

If a teammate has not claimed their role yet, another teammate may make progress on that lane using that lane's branch pattern. When the teammate is ready, they can take over from the latest branch or PR.

## File Ownership Map

### Carlo: Architect / Integration

Owns:

- LangGraph supervisor workflow.
- Shared `AgentState`.
- Agent handoff schema.
- Integration between workflow and Streamlit.
- Cross-agent output contract.

Mostly edits:

```text
careercompass/agents.py
careercompass/__init__.py
tests/test_workflow.py
docs/CAREERCOMPASS_TEAM_DEV_SPLIT.md
README.md
```

Coordinate before editing:

```text
app.py
requirements.txt
CareerCompass_MVP_Build_Spec.md
```

### Nhi: RAG / Data

Owns:

- Job-posting dataset.
- Retrieved market evidence.
- ChromaDB/vector search.
- Retrieval confidence.
- Dataset limitations and bias notes.

Mostly edits:

```text
careercompass/rag.py
careercompass/data/
careercompass/retrieval/
data/
docs/data_notes.md
```

Coordinate before editing:

```text
careercompass/agents.py
requirements.txt
README.md
```

### TM3: Agent Logic

Owns:

- OpenAI prompt templates.
- Structured JSON outputs.
- Fallback behavior when model calls fail.
- Agent-level validation.
- Prompt documentation.

Mostly edits:

```text
careercompass/prompts.py
careercompass/agent_logic.py
careercompass/fallbacks.py
careercompass/schemas.py
tests/test_agent_logic.py
```

Coordinate before editing:

```text
careercompass/agents.py
requirements.txt
```

### TM4: Frontend / Demo

Owns:

- Streamlit polish.
- Demo flow.
- Screenshots.
- Walkthrough/video support.
- Frontend readability and layout.

Mostly edits:

```text
app.py
docs/screenshots/
docs/demo_script.md
docs/demo_flow.md
```

Coordinate before editing:

```text
careercompass/agents.py
README.md
```

### TM5: Evaluation / Deployment

Owns:

- Docker setup.
- Metrics table.
- Evaluation checklist.
- Ethics and risk notes.
- Final report support.
- Deployment notes.

Mostly edits:

```text
Dockerfile
.dockerignore
docs/evaluation.md
docs/ethics.md
docs/deployment.md
tests/test_evaluation.py
```

Coordinate before editing:

```text
README.md
requirements.txt
CareerCompass_MVP_Build_Spec.md
```

## Shared Files

These files can affect multiple teammates. Coordinate before editing them:

```text
README.md
app.py
requirements.txt
careercompass/agents.py
CareerCompass_MVP_Build_Spec.md
```

Suggested message before touching a shared file:

```text
I need to edit app.py to connect my lane. Is anyone else editing it right now?
```

## Branch SOP

Do not work directly on `main`.

Start by pulling the latest main:

```bash
git status
git switch main
git pull origin main
```

Create a branch for the lane:

```bash
git switch -c carlo-architecture-langgraph
```

Examples:

```text
carlo-architecture-langgraph
nhi-rag-data-chromadb
tm3-agent-logic-prompts
tm4-frontend-demo-polish
tm5-eval-deploy-docker
```

Save and push work:

```bash
git status
git add .
git commit -m "Add LangGraph supervisor workflow"
git push -u origin carlo-architecture-langgraph
```

Open a Pull Request into `main`.

## Working On An Unclaimed Lane

If a lane is unclaimed, it is okay to start it so the project keeps moving.

Rules:

- Use that lane's branch name, not your normal branch name.
- Keep the work clean and documented.
- Open a PR even if the lane owner has not joined yet.
- Add notes explaining what is done and what is still open.
- When the teammate claims the role, hand off the branch or PR.

Example:

```text
tm3-agent-logic-prompts
tm4-frontend-demo-polish
tm5-eval-deploy-docker
```

Recommended PR note:

```text
This lane is currently unclaimed, so I started the first pass. TM3/TM4/TM5 can take this over from this branch or continue from the PR comments.
```

## Takeover SOP

When a teammate is ready to claim a lane:

1. Read this file.
2. Read the latest PR for that lane.
3. Pull the branch locally.
4. Ask questions in the PR comments.
5. Continue from the existing branch or create a follow-up branch.

Command-line takeover:

```bash
git fetch origin
git switch tm3-agent-logic-prompts
git pull origin tm3-agent-logic-prompts
```

If the branch has already merged, start from latest main:

```bash
git switch main
git pull origin main
git switch -c tm3-agent-logic-next-step
```

## PR Template

Use this in every Pull Request:

```text
## Lane
Carlo / Nhi / TM3 / TM4 / TM5

## What changed
- Added ...
- Updated ...

## Files touched
- path/to/file
- path/to/file

## Shared files touched
- None

## How I tested it
- Ran ...
- Checked ...

## Handoff notes
- Done:
- Still needed:
- Questions:
```

## Priority Levels

| Priority | Meaning | Examples |
| --- | --- | --- |
| P0 | Needed for the app to run or the class requirement to be satisfied | Supervisor workflow, app launch, required demo path |
| P1 | Important for project quality | RAG evidence, structured JSON, polished UI, metrics |
| P2 | Helpful polish | Screenshots, extra docs, improved copy, optional checks |
| P3 | Stretch | Extra features, advanced deployment, deeper evals |

## Current P0 Checklist

- LangGraph supervisor can run one end-to-end workflow.
- Shared `AgentState` and handoff schema are defined.
- Streamlit app can run locally.
- RAG/data lane can return retrieved evidence, even if mocked at first.
- Agent logic returns stable JSON-like outputs.
- Demo flow is clear enough for presentation.
- Final report includes metrics and ethics notes.

## Team Agreement

We agree to:

- Work on separate branches.
- Pull latest `main` before starting.
- Avoid direct commits to `main`.
- Use PRs for review.
- Coordinate before editing shared files.
- Keep unclaimed lanes easy to take over.
- Leave clear handoff notes when working outside our main lane.
