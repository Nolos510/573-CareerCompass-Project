# CareerCompass Data Notes

This is the first RAG/Data lane implementation.

## Current Dataset

The MVP includes a small local job-posting sample:

```text
careercompass/data/job_postings.json
```

The sample is intentionally lightweight so the app can run without API keys, scraping, network access, or ChromaDB setup. It includes Bay Area and remote postings for:

- Business Analyst.
- Data Analyst.
- Business Systems Analyst.
- Project Manager.
- Associate Project Manager.
- Technical Project Coordinator.

The recommended full source for the next MVP data refresh is the Kaggle
LinkedIn Job Postings dataset:

```text
https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
```

The dataset includes `postings.csv` with job title, description, salary,
location, work type, experience level, application URL, and related metadata.
It also includes company and mapping files for richer future retrieval. Kaggle
downloads usually require a Kaggle account/API token, so the raw files are not
committed to this repo.

To refresh the local MVP fixture after downloading the dataset:

```powershell
python -m careercompass.kaggle_ingest `
  --input DATA/linkedin-job-postings `
  --output careercompass/data/job_postings.json `
  --limit 200
```

Supported input forms are the downloaded zip, the extracted dataset folder, or
a direct `postings.csv` / `job_postings.csv` file. The converter filters for
CareerCompass-relevant analyst/project roles in Bay Area or remote locations
and normalizes rows to the current retrieval contract.

## Current Retrieval Method

`careercompass/rag.py` implements deterministic lexical retrieval:

1. Tokenize the target role and location.
2. Score postings by role/location/skill overlap.
3. Return the top postings with retrieval scores and evidence summaries.
4. Derive market skills by counting skills across retrieved postings.

This gives the Market Demand Agent retrieved evidence now and creates a clean replacement point for ChromaDB/vector search later.

## Next RAG Upgrade

Nhi can replace or extend `retrieve_job_postings()` with:

- Kaggle LinkedIn job posting dataset ingestion via `careercompass/kaggle_ingest.py`.
- ChromaDB collection creation.
- Embeddings using OpenAI `text-embedding-3-small`.
- Metadata filters for role, location, company, and posting date.
- Top-k retrieval with source IDs and evidence snippets.

The output should keep the current shape:

```python
[
    {
        "id": "...",
        "role": "...",
        "company": "...",
        "location": "...",
        "date": "...",
        "skills": ["..."],
        "description": "...",
        "retrieval_score": 1.0,
        "evidence_summary": "..."
    }
]
```

## Bias And Limitations

The current local sample is not representative of the full labor market. It is useful for demo reliability, but the final report should acknowledge that:

- Bay Area tech companies are overrepresented.
- Entry-level postings can vary widely by company.
- Skill counts from small samples should be treated as directional, not authoritative.
- Recommendations should be reviewed with a career advisor.
