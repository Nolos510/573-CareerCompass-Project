import chromadb

# ── Connect to ChromaDB ───────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="DATA/chroma_db")
collection = client.get_or_create_collection("job_postings")

def query_jobs(query: str, n_results: int = 5) -> list[dict]:
    """
    Query the job postings vector store.
    
    Args:
        query: Natural language query e.g. "data engineer python skills"
        n_results: Number of results to return (default 5)
    
    Returns:
        List of dicts with 'text' and 'distance' keys
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "text": doc,
            "distance": results["distances"][0][i]
        })
    
    return output


def get_top_skills(role: str) -> list[str]:
    """
    Get top skills mentioned for a given role.
    
    Args:
        role: Job role e.g. "data scientist", "business analyst"
    
    Returns:
        List of relevant job posting snippets
    """
    results = query_jobs(query=role, n_results=10)
    return [r["text"] for r in results]


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing query engine...")
    results = query_jobs("data engineer python SQL", n_results=3)
    for r in results:
        print(f"\nDistance: {r['distance']:.4f}")
        print(r["text"][:200])