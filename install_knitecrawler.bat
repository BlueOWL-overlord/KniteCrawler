@echo off
setlocal EnableDelayedExpansion

echo KniteCrawler Installer for Windows
echo ----------------------------------

REM Set variables
set "INSTALL_DIR=%USERPROFILE%\Desktop\KniteCrawler"
set "TOR_URL=https://www.torproject.org/dist/torbrowser/13.0.15/tor-win64-13.0.15.zip"
set "TOR_ZIP=tor.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PYTHON_INSTALLER=python_installer.exe"

REM Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Downloading and installing Python...
    curl -L -o %PYTHON_INSTALLER% %PYTHON_URL% || (
        echo Failed to download Python. Please install it manually from python.org.
        exit /b 1
    )
    echo Installing Python...
    start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1
    del %PYTHON_INSTALLER%
    echo Python installed. Please restart this script if it doesn’t detect Python immediately.
    pause
    python --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Python installation failed or not added to PATH. Please add it manually and rerun.
        exit /b 1
    )
) else (
    echo Python found: 
    python --version
)

REM Ensure pip is available
python -m ensurepip --upgrade
python -m pip install --upgrade pip

REM Install dependencies
echo Installing Python dependencies...
pip install flask flask-socketio requests beautifulsoup4 stem praw telethon discord.py transformers torch 2captcha-python
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies. Check your internet or pip configuration.
    exit /b 1
)

REM Create install directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo Created directory: %INSTALL_DIR%
) else (
    echo Directory already exists: %INSTALL_DIR%
)

REM Download and extract Tor
if not exist "%INSTALL_DIR%\tor\tor.exe" (
    echo Downloading Tor...
    curl -L -o %TOR_ZIP% %TOR_URL% || (
        echo Failed to download Tor. Please download it manually from torproject.org.
        exit /b 1
    )
    echo Extracting Tor...
    mkdir "%INSTALL_DIR%\tor"
    tar -xf %TOR_ZIP% -C "%INSTALL_DIR%\tor" --strip-components=2 Tor
    del %TOR_ZIP%
    if not exist "%INSTALL_DIR%\tor\tor.exe" (
        echo Failed to extract Tor correctly. Please place tor.exe in %INSTALL_DIR%\tor manually.
        exit /b 1
    )
    echo Tor installed at %INSTALL_DIR%\tor
) else (
    echo Tor already present at %INSTALL_DIR%\tor
)

REM Assuming KniteCrawler files are in the current directory or need to be downloaded
echo Copying KniteCrawler files...
xcopy /E /I /Y "%~dp0KniteCrawler" "%INSTALL_DIR%" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Failed to copy KniteCrawler files. Please ensure the KniteCrawler folder is in the same directory as this script.
    exit /b 1
)

REM Run KniteCrawler
echo Starting KniteCrawler...
cd /d "%INSTALL_DIR%"
python -m KniteCrawler.app
if %ERRORLEVEL% neq 0 (
    echo Failed to start KniteCrawler. Check the logs or dependencies.
    exit /b 1
)

echo KniteCrawler is running. Access it at http://127.0.0.1:5000
pause