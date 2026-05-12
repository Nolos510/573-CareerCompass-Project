@echo off
cd /d "%~dp0"
"C:\Users\knolo\anaconda3\python.exe" -m streamlit run app.py --server.port 8503 --server.headless true --browser.gatherUsageStats false > live-streamlit.log 2>&1
