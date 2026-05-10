import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from query_engine import query_jobs

# ── OpenAI Client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_market_demand(role: str, location: str = "") -> dict:
    """
    Analyze market demand for a given role using RAG + OpenAI.
    
    Args:
        role: Job role e.g. "Data Analyst"
        location: Optional location e.g. "San Francisco"
    
    Returns:
        Dict with top_skills, tools, qualifications, summary
    """
    # Step 1 — Query ChromaDB for relevant job postings
    query = f"{role} {location}".strip()
    results = query_jobs(query=query, n_results=10)
    
    # Step 2 — Build context from retrieved postings
    context = "\n\n".join([r["text"] for r in results])
    
    # Step 3 — Ask OpenAI to extract insights
    prompt = f"""You are a career advisor analyzing job market data.
    
Based on the following real job postings for "{role}" roles{f' in {location}' if location else ''}:

{context}

Extract and return a JSON object with these fields:
- top_skills: list of top 5 most required skills
- tools: list of top 5 tools/technologies mentioned
- qualifications: list of top 3 qualifications required
- summary: 2-sentence summary of what employers want

Return ONLY valid JSON, no extra text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    import json
    content = response.choices[0].message.content.strip()
    # Strip markdown code blocks if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    if not content:
        return {"error": "No response from OpenAI - check your API quota"}
    
    result = json.loads(content)
    return result


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Market Demand Agent...")
    result = analyze_market_demand("Data Analyst", "San Francisco")
    import json
    print(json.dumps(result, indent=2))