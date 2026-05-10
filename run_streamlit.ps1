$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$env:TEMP = Join-Path $PSScriptRoot ".tmp"
$env:TMP = Join-Path $PSScriptRoot ".tmp"

$python = "C:\Users\knolo\anaconda3\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = ".\.venv\Scripts\python.exe"
}

& $python -m streamlit run app.py `
  --server.headless true `
  --server.port 8502 `
  --browser.gatherUsageStats false `
  *> "streamlit.out.log"
