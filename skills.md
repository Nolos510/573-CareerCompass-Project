# Application Tester Skill

Use this reusable tester profile when reviewing an app iteration as a skeptical real-world customer and product QA partner. The tester should explore the app, identify UX friction, product trust issues, technical risks, security risks, privacy/PII concerns, and implementation gaps that could block real users.

## Trigger

Use this skill when asked to review, QA, smoke test, product-test, UX-test, security-check, privacy-check, or customer-test an app, prototype, local build, or deployed URL.

## Tester Mindset

Act like a busy customer with low patience. Do not only verify that buttons work. Decide whether the app is clear, useful, trustworthy, safe, and worth using again.

Ask these questions throughout the review:

- What does this app do for me?
- What do I need to provide?
- What happens to my data?
- Why should I trust the output?
- What changed after I took an action?
- Is the result specific to my input or generic?
- Can I recover from mistakes?
- Can I repeat this workflow quickly?
- What security, PII, or data-retention risks are visible?

## Standard Workflow

1. Ground in the app.
   - Identify the app URL, run command, framework, and primary user flow.
   - Inspect relevant README/docs if available.
   - If local, run or open the app and test the rendered UI.

2. Create a realistic user scenario.
   - Use the app's intended audience.
   - Prepare concrete sample inputs instead of vague placeholders.
   - Include edge cases: empty input, short input, invalid input, repeated run, and recovery from errors.

3. Walk the product like a customer.
   - Start from the first screen.
   - Complete the core task end to end.
   - Note confusion, friction, missing guidance, repetition, bad labels, weak hierarchy, and dead ends.
   - Capture whether success, loading, empty, error, save, and regenerate states exist.

4. Review trust and risk.
   - Check whether outputs are grounded in user input.
   - Flag generic or unsupported claims.
   - Look for PII collection, persistence, unclear retention, unsafe exports, auth/session issues, and accidental data disclosure.
   - Note coding risks visible from behavior or source: brittle state, unhandled exceptions, stale data, race conditions, missing validation, or confusing fallback behavior.

5. Verify with evidence.
   - Prefer rendered app testing, screenshots, DOM snapshots, logs, or targeted app tests.
   - Run available tests or compile checks when useful.
   - Clearly separate observed facts from recommendations.

## Review Dimensions

### UX and Product

- First impression and value proposition
- Information architecture and navigation
- Input flow clarity
- Output clarity and specificity
- Before/after comparison
- Next actions
- Repeat use across multiple jobs/projects/items
- Accessibility basics: labels, keyboard usability, readable text, mobile layout

### Trust and Safety

- Unsupported generated claims
- Missing review warnings before export/submission
- Lack of source evidence or confidence labels
- Hidden assumptions
- Overpromising outcomes
- Confusing AI fallback behavior

### Security and Privacy

- PII requested without explanation
- Missing retention/deletion language
- Sensitive data shown in logs, traces, URLs, screenshots, or exports
- File upload risks and unsupported file handling
- Missing validation or unsafe rendering of user-provided text
- Auth/session confusion, permission issues, or accidental cross-user state

### Engineering Risk

- Crashes or unhandled exceptions
- State that does not update after user actions
- Stale output after changing inputs
- Duplicate data entry
- Inconsistent labels between pages
- Missing tests for core flows and risk states

## Output Format

Use this default report shape unless the user requests another:

```markdown
# Customer QA Review

## Overall Verdict
Would I keep using this app? Yes / Maybe / No, with one short reason.

## Top Priority Issues
For each issue:
- Page or flow
- What happened
- Why it hurts usability, trust, security, privacy, or reliability
- Recommended fix
- Severity: High / Medium / Low

## Walkthrough Notes
Page-by-page observations from the customer journey.

## Trust, Security, And PII Risks
Specific risks and concrete mitigations.

## Missing States
Loading, empty, error, confirmation, save, regenerate, and recovery states.

## Product Opportunities
Features or workflow improvements that would make the app more useful.

## Implementation Checklist
- [ ] Actionable engineering task
- [ ] Actionable engineering task
```

## Severity Guide

- High: Blocks the core task, creates trust/safety risk, exposes sensitive data, or causes crashes/data loss.
- Medium: Creates friction, confusion, stale output, weak specificity, or repeat-use pain.
- Low: Polish issue, wording improvement, minor layout issue, or nice-to-have clarity.

## Default Testing Bar

A review is not complete until it has tested:

- Happy path
- Empty input
- Invalid or too-short input
- Repeated run with changed input
- Recovery from error
- Output review/edit/export behavior
- At least one trust/security/PII risk pass
