#!/bin/bash

# KniteCrawler Setup Script
# This script installs required dependencies for the KniteCrawler project.

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to compare version numbers
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

echo -e "${GREEN}Starting KniteCrawler setup...${NC}"

# Check for Python 3
if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed.${NC}"
    echo "Please install Python 3 using your package manager:"
    echo "  - Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "  - Fedora: sudo dnf install python3 python3-pip"
    echo "  - macOS: brew install python3 (via Homebrew)"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
    version_compare "$PYTHON_VERSION" "3.8.0"
    if [ $? -eq 2 ]; then
        echo -e "${RED}KniteCrawler requires Python 3.8 or higher. Detected version $PYTHON_VERSION is too old. Please upgrade Python.${NC}"
        exit 1
    fi
fi

# Ensure pip is installed
if ! command_exists pip3; then
    echo -e "${RED}pip3 is not installed.${NC}"
    echo "Installing pip3..."
    if command_exists apt; then
        sudo apt update && sudo apt install -y python3-pip
    elif command_exists dnf; then
        sudo dnf install -y python3-pip
    elif command_exists brew; then
        brew install python3-pip
    else
        echo -e "${RED}Cannot install pip3 automatically. Please install it manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}pip3 is installed.${NC}"
fi

# List of required Python packages (sqlite3 removed as it's part of Python standard library)
DEPENDENCIES=(
    "flask"
    "flask-socketio"
    "requests"
    "beautifulsoup4"
    "stem"
    "praw"
    "telethon"
    "discord.py"
    "transformers"
    "torch"
    "2captcha-python"
)

# Install dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
for package in "${DEPENDENCIES[@]}"; do
    if pip3 show "$package" >/dev/null 2>&1; then
        echo -e "${GREEN}$package is already installed.${NC}"
    else
        echo "Installing $package..."
        pip3 install "$package"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}$package installed successfully.${NC}"
        else
            echo -e "${RED}Failed to install $package. Please check your network or pip configuration.${NC}"
            exit 1
        fi
    fi
done

# Check for Tor binary
TOR_DIR="tor"
TOR_BINARY="tor"
if [ "$(uname)" == "Darwin" ] || [ "$(uname)" == "Linux" ]; then
    TOR_BINARY="tor"
elif [ "$(uname -s | grep -i 'MINGW\|MSYS\|CYGWIN')" ]; then
    TOR_BINARY="tor.exe"
fi

if [ ! -f "$TOR_DIR/$TOR_BINARY" ]; then
    echo -e "${RED}Tor binary not found in $TOR_DIR/.${NC}"
    echo "Please download Tor and place it in the $TOR_DIR/ directory:"
    echo "  1. Visit: https://www.torproject.org/download/tor/"
    echo "  2. Download the Tor Expert Bundle for your OS."
    echo "  3. Extract $TOR_BINARY and place it in $TOR_DIR/ (e.g., KniteCrawler/tor/$TOR_BINARY)."
    echo "After placing the Tor binary, run this script again to verify."
else
    echo -e "${GREEN}Tor binary found at $TOR_DIR/$TOR_BINARY.${NC}"
fi

# Final instructions
echo -e "${GREEN}Setup complete!${NC}"
echo "To run KniteCrawler:"
echo "  1. Navigate to the KniteCrawler directory: cd KniteCrawler"
echo "  2. Run the application: python app.py"
echo "  3. Open your browser and go to: http://127.0.0.1:5000"
echo "Note: Ensure Tor is correctly placed in $TOR_DIR/ for dark web functionality."
