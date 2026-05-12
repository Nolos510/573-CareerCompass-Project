# CareerCompass GitHub Cleanup To-Do

Purpose: this is a careful handoff list for a separate agent or teammate who will prepare the local submission work for GitHub. The local repository has uncommitted work and local `main` is behind remote `main`, so the cleanup must preserve local changes before any sync operation.

## First Gate

1. Read `agents.md` completely before any Git operation.
2. Follow the `agents.md` start and end protocols.
3. Check the live remote `main` branch before changing, committing, pulling, rebasing, merging, or pushing.
4. Do not assume local `origin/main` is current unless it was just fetched or checked with a live remote command.

Recommended non-destructive checks:

```powershell
git status --short --branch
git remote --verbose
git branch --all --verbose
git log --oneline --decorate -5
git ls-remote origin refs/heads/main
```

As of the latest Codex check, live GitHub `origin/main` was:

```text
e7ef80a87b7daada39f2981dc6beb265ab054c46 refs/heads/main
```

The local branch was:

```text
main...origin/main [behind 12]
```

with uncommitted local submission-polish work.

## Do Not Sync Until Local Work Is Protected

Do not run any of these until local uncommitted work is preserved:

```powershell
git pull
git rebase
git reset
git checkout
git switch main
git merge
git push
```

Recommended first preservation step:

```powershell
git switch -c codex/final-submission-cleanup
```

If the branch already exists, stop and inspect it before choosing another branch name.

## Review Local Changes

Classify changes before staging.

Submission polish likely intended to keep:

- `agents.md`
- `.gitignore`
- `.dockerignore`
- `pytest.ini`
- `app.py` rubric evidence / responsible AI / demo UI updates
- `run_streamlit.ps1`
- `run_streamlit_8503.cmd`
- `tests/test_project_artifacts.py`
- `docs/data_notes.md`
- `docs/demo_flow.md`
- `docs/evaluation.md`
- `docs/evaluation_results.md`
- `docs/rubric_evidence.md`
- `docs/final_report_draft.md`
- `docs/github_cleanup_todo.md`
- `docs/screenshots/01-inputs.png`
- `docs/screenshots/02-dashboard.png`
- `docs/screenshots/03-gap-deep-dive.png`
- `docs/screenshots/04-roadmap.png`
- `docs/screenshots/05-resume.png`
- `docs/screenshots/06-interview.png`
- `docs/screenshots/07-final-report.png`
- `docs/screenshots/08-agent-trace.png`
- `docs/screenshots/09-rubric-evidence.png`

Local/runtime noise to exclude unless intentionally needed:

- `live-streamlit.log`
- `streamlit*.log`
- `.tmp/`
- `.pytest_cache/`
- `__pycache__/`
- `.venv/`
- `.packages/`
- nested local workspace copies or copied worktrees

Use review commands before staging:

```powershell
git diff --stat
git diff -- .gitignore .dockerignore app.py run_streamlit.ps1 tests/test_project_artifacts.py
git status --short
```

For new docs/screenshots, inspect the file list and content before staging:

```powershell
Get-ChildItem docs -Recurse | Select-Object FullName,Length
Get-Content -Raw docs\final_report_draft.md
Get-Content -Raw docs\github_cleanup_todo.md
```

## Verification Before Commit

Run:

```powershell
C:\Users\knolo\anaconda3\python.exe -m pytest -q
C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests
```

Verify local Streamlit on canonical demo port:

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

Open:

```text
http://localhost:8503
```

Confirm the screenshot set exists and matches `docs/demo_flow.md`:

```powershell
Get-ChildItem docs\screenshots
```

If Docker is available, verify:

```powershell
docker build -t careercompass .
docker run --rm -p 8501:8501 careercompass
```

Open:

```text
http://localhost:8501
```

Stop any temporary verification container after testing.

## Stage And Commit

Stage only intended files. Do not use `git add .` unless the status has been carefully reviewed and runtime noise is excluded.

Suggested commit message:

```text
Finalize submission evidence and demo polish
```

After committing, record:

```powershell
git rev-parse --short HEAD
git status --short --branch
```

## Integrate With Remote Main

Only after local work is committed on the safety branch:

```powershell
git fetch --all --prune
```

Then compare:

```powershell
git log --oneline --decorate --graph --max-count=20 --all
git diff --stat origin/main...HEAD
```

Prefer opening a pull request from:

```text
codex/final-submission-cleanup
```

into:

```text
main
```

If rebasing or merging is needed, resolve conflicts manually and preserve teammate changes from remote `main`. Do not force-push unless the team explicitly approves it.

## Final Handoff Update

At the end, update `agents.md` with:

- Date.
- Branch name.
- Commit hash.
- Files changed.
- Tests run.
- Docker status.
- Remote `main` hash used for comparison.
- Any blockers or unresolved conflicts.

## Final Repository Checklist

- Streamlit local run works on port `8503`.
- Docker run works on port `8501`, if Docker is available.
- README and `docs/deployment.md` use accurate ports and environment variable names.
- Screenshot set exists and matches `docs/demo_flow.md`.
- `docs/final_report_draft.md` is clearly marked as a support/comparison artifact.
- Final report and video script describe the same agent flow and demo scenario.
- No secrets, API keys, cache folders, virtual environments, or unnecessary log files are staged.
