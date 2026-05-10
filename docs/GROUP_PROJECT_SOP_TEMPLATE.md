# Five-Person Project Git and Ownership SOP

Use this document to keep a group project organized when teammates have different Git/GitHub experience levels.

The goal is simple:

- Everyone works on their own branch.
- Everyone has a clear lane.
- Shared files are edited carefully.
- No one overwrites someone else's work.
- Pull requests are used for review before merging into `main`.

## Team Lanes

Replace the names and lanes below with your actual team members and project areas.

| Person | Branch Name | Primary Lane | Owns Most |
| --- | --- | --- | --- |
| Person 1 | `person1-feature-name` | Project setup / architecture | Core app structure, config, README |
| Person 2 | `person2-feature-name` | User interface | Main screens, layout, styling |
| Person 3 | `person3-feature-name` | Data / models | JSON models, schemas, sample data |
| Person 4 | `person4-feature-name` | Services / backend | API services, mock services, gateway layer |
| Person 5 | `person5-feature-name` | Testing / docs / polish | Tests, demo script, docs, screenshots |

## File Ownership Map

Each person should mostly edit their own files. If you need to edit a shared file, tell the group first.

### Person 1 Mostly Owns

```text
README.md
project config files
main app entry point
architecture docs
```

### Person 2 Mostly Owns

```text
views/
screens/
components/
styles/
```

### Person 3 Mostly Owns

```text
models/
data/
schemas/
sample-data/
```

### Person 4 Mostly Owns

```text
services/
api/
mock-services/
gateway/
backend/
```

### Person 5 Mostly Owns

```text
tests/
docs/
demo/
presentation/
QA checklist
```

### Shared Files

Coordinate before editing these:

```text
README.md
main app/root view
project config files
package/dependency files
navigation/router files
shared state files
database schema files
deployment files
```

Before editing a shared file, send a quick message like:

```text
I need to edit README.md to add setup instructions. Is anyone else touching it right now?
```

## Branch Rules

Do not work directly on `main`.

Each person works on their own branch:

```text
person1-project-setup
person2-ui-flow
person3-data-models
person4-services
person5-tests-docs
```

Better branch names use the person's name plus the task:

```text
alex-login-ui
maya-data-models
jordan-api-services
sam-demo-docs
```

## Daily Start SOP

Run this before starting work:

```bash
git status
git switch main
git pull origin main
git switch -c your-branch-name
```

If your branch already exists:

```bash
git status
git switch main
git pull origin main
git switch your-branch-name
git rebase main
```

If `git rebase main` feels scary, ask the team lead before continuing.

## Save Work SOP

Run this after finishing a chunk of work:

```bash
git status
git add .
git commit -m "Describe what you added"
git push -u origin your-branch-name
```

Good commit messages:

```text
Add account settings page
Create restaurant JSON models
Add mock gateway service
Update README setup steps
Add homepage layout
```

Avoid vague commit messages:

```text
stuff
changes
fixed things
update
final final
```

## Pull Request SOP

After pushing your branch, open a Pull Request into `main`.

PR title format:

```text
Add account settings page
Add data models and sample JSON
Add service gateway mock layer
```

PR description template:

```text
## What changed
- Added ...
- Updated ...

## Files I mostly touched
- path/to/file
- path/to/file

## How I tested it
- Ran the app locally
- Clicked through ...
- Checked that ...

## Notes for reviewers
- I touched a shared file: ...
- I need help checking: ...
```

## Before Merging

Before merging a PR:

- Make sure the app still runs.
- Make sure there are no obvious broken screens.
- Make sure the PR does not overwrite someone else's work.
- Ask for at least one teammate review.
- Ask for two reviews if the PR touches shared files or project setup.

## Shared File Rule

If you edit a shared file, put that in the PR description.

Example:

```text
I edited README.md and the root navigation file. Please check that this does not conflict with anyone else's branch.
```

## Conflict Rule

If GitHub says there is a merge conflict:

1. Do not panic.
2. Do not click random buttons.
3. Message the team.
4. The person who owns the branch should fix the conflict with help from the team lead.

Suggested message:

```text
My PR has a merge conflict. I need help resolving it before merge.
```

## Beginner-Friendly GitHub Desktop Flow

For teammates who do not want to use the command line:

1. Open GitHub Desktop.
2. Click **Current Branch**.
3. Create a new branch for your task.
4. Make your changes in the project.
5. Return to GitHub Desktop.
6. Write a short summary.
7. Click **Commit to your branch**.
8. Click **Publish branch** or **Push origin**.
9. Click **Create Pull Request**.

Do not commit directly to `main`.

## Communication Rules

Use short updates so people know what is happening.

When starting:

```text
I'm starting the Account page on my branch. I should only touch AccountView and account models.
```

When touching shared files:

```text
I need to touch the root navigation file to add my screen. Is anyone else editing it?
```

When done:

```text
I pushed my branch and opened a PR. Please review when you can.
```

When stuck:

```text
I'm stuck on Git / a conflict / running the app. Can someone pair with me for 10 minutes?
```

## Suggested Five-Person Split

Use this if your team does not already have a clear split.

### Person 1: Project Lead / Integration

Owns:

- Project setup.
- Main README.
- App shell.
- Navigation.
- Final integration.

Mostly edits:

```text
README.md
app/root files
navigation/router files
project config
```

### Person 2: UI / Frontend Screens

Owns:

- Main user-facing screens.
- Visual layout.
- Forms.
- Button flows.

Mostly edits:

```text
views/
screens/
components/
styles/
```

### Person 3: Data Models / Sample Data

Owns:

- JSON models.
- Sample data.
- Data validation.
- Model documentation.

Mostly edits:

```text
models/
data/
schemas/
fixtures/
```

### Person 4: Services / API Layer

Owns:

- Mock services.
- API gateway layer.
- Backend boundary.
- Environment variable notes.

Mostly edits:

```text
services/
api/
backend/
gateway/
```

### Person 5: Testing / Docs / Demo

Owns:

- Test checklist.
- Demo script.
- Screenshots.
- Final presentation notes.
- QA pass before submission.

Mostly edits:

```text
tests/
docs/
demo/
presentation/
```

## Priority Levels

Use these to decide what matters most.

| Priority | Meaning | Examples |
| --- | --- | --- |
| P0 | Must work for the project to run | App starts, main flow works, no broken imports |
| P1 | Important for final quality | Good UI, useful data, clean PRs, README setup |
| P2 | Nice improvement | Extra polish, optional screens, minor refactors |
| P3 | Only if time allows | Stretch features, animations, extra docs |

## Minimum Definition of Done

A task is done when:

- The branch is pushed.
- A PR is open.
- The PR description explains what changed.
- The app still runs.
- Any shared files are called out.
- At least one teammate has reviewed it.

## Team Agreement

We agree to:

- Work on separate branches.
- Pull latest `main` before starting.
- Use pull requests.
- Avoid direct commits to `main`.
- Communicate before editing shared files.
- Ask for help when Git gets confusing.
- Review each other's work respectfully.
