@echo off
cd /d "C:\Users\arvin\Downloads\R_SIM"
start "Backend" cmd /k "cd backend && venv\Scripts\activate && python f_backend.py"
timeout /t 3 /nobreak >nul
start "Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul
start http://localhost:5001