@echo off
cd /d "%~dp0"
python -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir o LCE. Instale as dependencias com:
    echo python -m pip install -r requirements.txt
    echo.
    pause
)
