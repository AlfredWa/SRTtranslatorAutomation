@echo off
echo ========================================
echo Initializing Python Virtual Environment...
echo ========================================

:: 使用 .venv 作为文件夹名称（现代推荐规范）
set VENV_NAME=.venv

:: 1. Check if venv exists, create if not
if not exist %VENV_NAME%\Scripts\activate (
    echo [1/4] Creating virtual environment [%VENV_NAME%]...
    python -m venv %VENV_NAME%
) else (
    echo [1/4] Virtual environment [%VENV_NAME%] already exists. Skipping...
)

:: 2. Activate virtual environment
echo [2/4] Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

:: 3. Upgrade pip
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

:: 4. Install dependencies from requirements.txt
if exist requirements.txt (
    echo [4/4] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    echo [4/4] Warning: requirements.txt not found. Skipping...
)

echo ========================================
echo Setup complete! Virtual environment is active.
echo You can now run your scripts (e.g., python main.py).
echo ========================================

:: Keep the command prompt open in the active venv
cmd /k