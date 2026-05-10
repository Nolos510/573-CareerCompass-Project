# CareerCompass Deployment Notes

## Local Streamlit

```powershell
C:\Users\knolo\anaconda3\python.exe -m streamlit run app.py --server.port 8503
```

Open:

```text
http://localhost:8503
```

## Docker

Build:

```powershell
docker build -t careercompass .
```

Run:

```powershell
docker run --rm -p 8501:8501 careercompass
```

Open:

```text
http://localhost:8501
```

## Optional LLM Mode

The app runs with deterministic fallbacks by default. To enable live OpenAI calls:

```powershell
$env:CAREERCOMPASS_USE_LLM="true"
$env:OPENAI_API_KEY="<your-api-key>"
$env:CAREERCOMPASS_LLM_MODEL="gpt-4o-mini"
```

Docker example:

```powershell
docker run --rm -p 8501:8501 `
  -e CAREERCOMPASS_USE_LLM=true `
  -e OPENAI_API_KEY="$env:OPENAI_API_KEY" `
  careercompass
```

## Pre-Demo Checklist

```powershell
C:\Users\knolo\anaconda3\python.exe -m unittest discover -s tests
C:\Users\knolo\anaconda3\python.exe -m compileall app.py careercompass tests
```

Then open the Streamlit app and complete the demo flow in `docs/demo_flow.md`.

