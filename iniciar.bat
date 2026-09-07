@echo off
REM Lanzador de JL Mantenimiento para Windows
cd /d "%~dp0"
call "%~dp0venv\Scripts\activate.bat"
python main.py