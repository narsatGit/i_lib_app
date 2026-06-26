@echo off
cd /d "%~dp0"

:: Vérifie si le venv existe, sinon le crée et installe les dépendances
if not exist "venv\Scripts\activate.bat" (
    echo Installation en cours, merci de patienter...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    python -m spacy download fr_core_news_sm
)

:: Tue toute instance Streamlit déjà en cours
:: pour libérer le port avant de relancer
taskkill /f /im pythonw.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

:: Attend 1 seconde que le port soit libéré
timeout /t 1 /nobreak > nul

:: Lance l'application en forçant toujours le port 8501
start /b "" venv\Scripts\pythonw.exe -m streamlit run app.py ^
    --server.headless true ^
    --browser.gatherUsageStats false ^
    --server.port 8501

:: Attend 3 secondes que Streamlit démarre
timeout /t 3 /nobreak > nul

:: Ouvre le navigateur sur l'adresse toujours fixe
start http://localhost:8501