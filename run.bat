@echo off
cd /d "%~dp0"
call venv\Scripts\streamlit.exe run app\streamlit_app.py
