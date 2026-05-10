# CareerCompass Ethics And Risk Notes

## Data Privacy

Resumes can contain personal information such as names, email addresses, phone numbers, employers, education history, and career goals.

Current mitigation:

- The MVP does not persist uploaded resume files.
- Resume text is used in the active Streamlit session.
- `.gitignore` and `.dockerignore` exclude local runtime folders and large data folders.

Final report recommendation:

- State that a production version should avoid storing resumes unless the user explicitly consents.
- Add deletion controls and clear data-retention language.

## Bias In Job Posting Data

Job postings can overrepresent certain industries, locations, companies, credentials, and language patterns.

Current mitigation:

- Retrieved evidence is shown to the user rather than hidden.
- Data notes document that the local sample is directional, not authoritative.
- Confidence scores and advisor-review language are included.

Final report recommendation:

- Document corpus composition.
- Diversify sources beyond Bay Area tech postings.
- Evaluate recommendations across different majors, roles, and geographies.

## Resume Homogenization

Aggressive keyword optimization can make resumes sound generic or exaggerate a student's experience.

Current mitigation:

- Resume suggestions preserve original evidence and only add plausible market-aligned framing.
- The editable resume draft keeps the student in control.

Final report recommendation:

- Require all generated resume claims to be traceable to student-provided evidence.
- Add warning text against inventing credentials, employers, tools, or outcomes.

## Overconfidence

Students may treat AI recommendations as definitive.

Current mitigation:

- The final report includes decision-support and advisor-review language.
- Confidence scores are shown in the technical demo section.

Final report recommendation:

- Avoid language like "guaranteed match" or "must do."
- Present recommendations as prioritized suggestions with confidence levels.

## Access And Equity

Recommended resources may require paid subscriptions or assume access to certain tools.

Current mitigation:

- The MVP includes free or commonly available resources when possible.
- Portfolio suggestions can use public datasets and free dashboard tools.

Final report recommendation:

- Label free versus paid resources.
- Include alternatives for students without access to paid certifications.

