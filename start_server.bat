@echo off
echo "Setting up environment and starting server..."

REM Check for venv directory
IF EXIST .venv (
    echo "Activating virtual environment from .venv..."
    call .venv/Scripts/activate
) ELSE IF EXIST venv (
    echo "Activating virtual environment from venv..."
    call venv/Scripts/activate
) ELSE (
    echo "ERROR: No virtual environment (venv or .venv) found."
    pause
    exit /b
)


REM Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

REM Start the server
echo "Starting the server..."
echo "Your application will be available at http://localhost:5000"
python app.py

pause
