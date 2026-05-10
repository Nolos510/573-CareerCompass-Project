# CareerCompass Git Sync Workflow

Use this workflow before committing or pushing so teammates do not overwrite each other.

## Current Repo State

As of the local setup, this copied project has:

- No commits yet.
- No configured Git remote.
- No functional `main` or `master` baseline branch yet.
- Active local branch: `carlo-architecture-langgraph`.

That means there is currently nothing meaningful to pull from. Once the GitHub repo is connected, create or pull the shared baseline before feature work continues.

## Before Starting Work

```powershell
git status --short --branch
git branch --all --verbose
git remote --verbose
```

If a remote exists, fetch everything:

```powershell
git fetch --all --prune
```

Then check which shared branch exists:

```powershell
git branch --all --list *main*
git branch --all --list *master*
```

Use whichever shared baseline the team chooses.

## Before Commit

1. Save your files.
2. Run tests.
3. Check status.
4. Pull or rebase from the team baseline if a remote exists.

```powershell
git status --short --branch
python -m unittest discover -s tests
git fetch --all --prune
git pull --rebase origin main
```

If the repo uses `master` instead:

```powershell
git pull --rebase origin master
```

If neither branch exists yet, do not invent a fake sync step. Confirm with the team first.

## Before Push

```powershell
git status --short --branch
git branch --show-current
git push -u origin <your-branch-name>
```

Open a pull request into the shared baseline branch.

## Team Rule

Do not commit or push until you know:

- Which branch you are on.
- Whether a remote exists.
- Whether `main` or `master` is the shared baseline.
- Whether your tests pass.
- Whether your branch has been synced against the current shared baseline.

