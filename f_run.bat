@echo off

REM Navigate to the backend directory and activate virtual environment
cd backend
call venv\Scripts\activate

REM Start backend server in a new command prompt window
start cmd /k "python f_backend.py"

REM Navigate to the frontend directory
cd ..\frontend

REM Start frontend development server in a new command prompt window
start cmd /k "pnpm run dev --host"

REM Open the application in the default web browser
start http://localhost:5173/

exit

