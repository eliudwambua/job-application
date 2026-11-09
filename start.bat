@echo off
title ScholarPilot EU - Master's & Job Application Copilot
echo ==============================================================
echo   Starting ScholarPilot EU...
echo   Local Web App: http://127.0.0.1:8000
echo ==============================================================

:: Open default browser after 2 seconds
start "" http://127.0.0.1:8000

:: Run the FastAPI application
.\.venv\Scripts\python.exe run.py
pause

