@echo off
echo Shutting down Django development server on port 8000...

REM Find the process ID listening on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Found process %%a on port 8000
    taskkill /PID %%a /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo Successfully terminated process %%a
    ) else (
        echo Failed to terminate process %%a
    )
    goto :done
)

echo No server found running on port 8000
:done
echo Done.