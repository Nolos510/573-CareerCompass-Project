# CareerCompass Evaluation Plan

This plan supports the final project report and video demo.

## Metrics

| Metric | Target | Current MVP Evidence | Next Validation Step |
| --- | --- | --- | --- |
| End-to-end latency | Under 30 seconds | Streamlit run records local latency after each analysis. | Record 5 demo runs and report average/p95. |
| Skill gap accuracy | 80 percent manual agreement | Gap Analysis Agent compares resume/coursework evidence against retrieved market skills. | Have teammates manually review 10 sample profiles and label agreement. |
| Resume keyword coverage | Increased keyword coverage after optimization | Resume view lists target keywords and suggested bullet rewrites. | Compare before/after keyword count against target postings. |
| Learning resource relevance | 4 out of 5 user rating | Roadmap includes resource relevance scores. | Ask test users to rate roadmap resources. |
| Interview question relevance | 4 out of 5 average relevance | Interview simulator generates role/company/scenario-specific questions. | Rate questions against target job descriptions. |
| Retrieved evidence quality | At least 3 relevant postings for common demo roles | Local retriever returns scored postings and evidence summaries. | Replace local dataset with ChromaDB top-k retrieval and inspect source snippets. |

## Test Profiles

Use at least three profiles:

- MIS student targeting Business Analyst roles.
- MIS student targeting Project Manager roles.
- Hybrid Business Analyst / Project Manager target.

Each profile should include:

- Resume text.
- Coursework list.
- Target role.
- Location.
- Timeline.

## Evaluation Procedure

1. Run CareerCompass for each test profile.
2. Save dashboard, skill gap, resume, interview, and final report screenshots.
3. Record latency from the technical demo panel.
4. Review retrieved job-posting evidence for relevance.
5. Compare skill gaps against the retrieved postings.
6. Rate roadmap and interview outputs using the metrics table.
7. Document limitations and disagreements in the final report.

## Acceptance Criteria For Final Demo

- Streamlit app runs locally or in Docker.
- Analysis completes under 30 seconds in the demo environment.
- Dashboard displays retrieved job evidence.
- Final report includes strategy, roadmap, resume, interview, and ethical safeguard language.
- Tests pass before recording.

