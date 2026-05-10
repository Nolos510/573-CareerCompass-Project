# Branch Protection and Workflow Rules

This project uses lightweight branch discipline: strict protection for deployable branches, moderate rules for shared integration work, and low-friction feature branches.

## Priority Levels

- **P0 - Required:** Protects production stability, repository history, or CI quality.
- **P1 - Strong Default:** Should be enabled unless it creates a clear workflow problem.
- **P2 - Team Convention:** Useful for consistency, but not worth blocking normal work over.
- **P3 - Scale Later:** Helpful once the project has more repos, more contributors, or more automation.

## Protected Branches

### `main`

`main` must always be deployable.

| Rule | Priority | Policy |
| --- | --- | --- |
| Require pull requests before merging | P0 | No direct commits to `main`. |
| Require status checks to pass | P0 | CI must pass before merge. At minimum: tests, lint, and any build check. |
| Block force pushes | P0 | Do not allow rewritten history on `main`. |
| Block branch deletion | P0 | `main` cannot be deleted. |
| Require at least one approval | P1 | Use two approvals for high-risk production work or larger teams. |
| Require CODEOWNERS review | P1 | Apply to sensitive paths such as auth, billing, security, deployment, infrastructure, database migrations, and CI. |
| Dismiss stale approvals after new commits | P1 | New commits should require reviewers to re-confirm the final version. |
| Require conversation resolution | P1 | All review threads must be resolved before merge. |
| Require up-to-date branch before merge | P1 | Enable if integration conflicts or CI drift become common. |
| Prefer squash merge | P2 | Keeps `main` readable. Rebase merge is also acceptable if the team prefers it. |
| Require linear history | P2 | Enable only if the team agrees to avoid merge commits. |
| Restrict bypass permissions | P1 | Only repo admins or release owners should bypass rules, and bypasses should be rare. |

### `release/*` or `production`

Use these only if the project needs release branches or a separate production branch.

| Rule | Priority | Policy |
| --- | --- | --- |
| Require pull requests | P0 | No direct commits except approved emergency hotfixes. |
| Require status checks | P0 | Release validation must pass. |
| Block force pushes | P0 | Release history must remain stable. |
| Block branch deletion | P0 | Release branches should not be deleted casually. |
| Require one or two approvals | P1 | Two approvals for production-critical changes. |
| Require CODEOWNERS review | P1 | Required for deployment, infra, data, or security-sensitive changes. |

### Feature Branches

Feature branches should stay flexible.

| Rule | Priority | Policy |
| --- | --- | --- |
| Allow force pushes | P2 | Developers may clean up their own branch history before merge. |
| Do not require branch protection | P2 | Avoid heavy rules on personal work branches. |
| Delete after merge | P1 | Enable automatic deletion of merged head branches. |

## Required Status Checks

Start with checks that are fast and reliable. Add heavier checks only when they catch real issues.

- **P0:** Unit tests.
- **P0:** Build or import check.
- **P1:** Linting and formatting check.
- **P1:** Type checking, if the stack supports it.
- **P1:** Dependency or vulnerability scanning for production apps.
- **P2:** Coverage threshold, if the team agrees on a meaningful bar.
- **P2:** End-to-end tests for critical flows.

Avoid making flaky checks required. Fix or quarantine flaky checks before they become merge blockers.

## Pull Request Rules

- **P0:** Every change to `main` goes through a PR.
- **P1:** Keep PRs small and focused.
- **P1:** PR descriptions should explain what changed, why it changed, and how it was tested.
- **P1:** Link the relevant issue, ticket, or task when one exists.
- **P1:** Mark high-risk changes clearly, especially migrations, auth, deployment, security, and data changes.
- **P2:** Use draft PRs for early feedback before a change is ready for full review.
- **P2:** Prefer squash merge unless preserving individual commits adds useful context.

## Multi-Person Approval

Do not require multi-person authentication for ordinary commits or pushes to feature branches. That would slow down normal development too much and would not add much safety, because feature branches are not deployable.

Use multi-person approval at merge time instead:

- **P0:** Require PR approval before merging into `main`.
- **P1:** Require two approvals for high-risk changes, such as auth, secrets, deployment, infrastructure, database migrations, or security-sensitive logic.
- **P1:** Require CODEOWNERS review for sensitive paths.
- **P2:** Keep feature branch pushes flexible so developers can iterate quickly.

Emergency production bypasses should be rare, limited to trusted maintainers, and documented in the PR or incident notes after the fact.

## Branch Naming

Use short, descriptive branch names with a purpose prefix.

Recommended prefixes:

- `feat/` for new features.
- `fix/` for bug fixes.
- `hotfix/` for urgent production fixes.
- `docs/` for documentation.
- `chore/` for maintenance.
- `refactor/` for behavior-preserving code restructuring.
- `test/` for test-only changes.
- `ci/` for CI/CD changes.

Examples:

```text
feat/resume-upload
fix/report-empty-state
hotfix/production-login
docs/branch-rules
chore/update-dependencies
ci/add-test-workflow
```

Ticket numbers are useful when available:

```text
feat/123-resume-upload
fix/456-report-empty-state
```

Do not block merges solely because a branch name is imperfect unless automation depends on the naming format.

## CODEOWNERS Guidance

Use CODEOWNERS for sensitive or specialized areas, not every file.

Good candidates:

- Authentication and authorization.
- Secrets and environment configuration.
- Infrastructure and deployment files.
- CI/CD workflows.
- Database schemas and migrations.
- Payment, billing, or account-management code.
- Security-sensitive application logic.

Avoid requiring too many owners on broad paths. If every PR needs three specialized reviews, the rule will slow work without improving quality.

## Hotfix Process

Hotfixes should be fast, visible, and reviewed.

1. Create a branch named `hotfix/<short-description>`.
2. Open a PR into the production branch or `main`.
3. Require CI and at least one approval unless the incident requires an emergency bypass.
4. Document any bypass in the PR description after the fact.
5. Backport or forward-port the fix to other active branches if needed.

## Merge Strategy

Default:

- Squash merge feature branches into `main`.
- Delete the branch after merge.
- Keep PR titles clear because they become the squashed commit message.

Optional:

- Use rebase merge for clean commit-by-commit history.
- Allow merge commits only when preserving branch structure is useful.

## Repository Settings Checklist

For GitHub, configure these settings where available:

- Enable branch protection or repository rulesets for `main`.
- Require pull request before merge.
- Require approvals.
- Dismiss stale pull request approvals when new commits are pushed.
- Require review from CODEOWNERS for sensitive paths.
- Require status checks to pass before merging.
- Require conversation resolution before merging.
- Disable force pushes on protected branches.
- Disable branch deletion on protected branches.
- Enable automatic deletion of head branches after merge.
- Restrict bypass permissions.
- Consider enabling secret scanning and Dependabot alerts.

## What Not To Overdo

- Do not require two approvals for every small change unless the project is highly regulated or production critical.
- Do not protect every feature branch.
- Do not make flaky checks required.
- Do not make CODEOWNERS so broad that routine PRs stall.
- Do not enforce branch naming so strictly that it becomes process noise.

The goal is simple: protect deployable branches, keep reviews useful, keep CI trustworthy, and let normal development stay fast.
