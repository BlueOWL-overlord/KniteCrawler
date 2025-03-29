# KniteCrawler

KniteCrawler is a powerful intelligence-gathering tool designed to monitor and analyze data across multiple platforms, including the dark web, social media, and forums. It leverages AI for sentiment analysis and summarization, supports real-time updates via WebSockets, and integrates Tor for dark web access. This project was developed with assistance from **Grok**, an AI created by xAI, which helped refine code, troubleshoot issues, and optimize functionality.

## Features
- **Multi-Platform Tracking**: Monitors Dark Web (Dread-like forums), 4chan, Reddit, Telegram, Discord, X, Pastebin, GitHub, XSS.is, Exploit.in, and Nulled.to.
- **Leak Detection**: Identifies emails, hashes, passwords, credit cards, IPs, and SSNs with weighted scoring.
- **AI-Powered Analysis**: Uses transformers (e.g., BART, DistilBERT) for summarization and sentiment analysis, with GPU support for NVIDIA cards.
- **Real-Time Updates**: WebSocket-based dashboard for live intel feed and activity status.
- **Search & Filter**: Google-like UI with platform and sentiment filters.
- **Export**: Export findings to CSV.
- **Tor Integration**: Accesses dark web sites via Tor.

## Prerequisites
- **Operating System**: Windows 10/11 or Linux (e.g., Ubuntu 20.04+).
- **NVIDIA GPU (Optional)**: For accelerated AI tasks (requires CUDA-compatible drivers).
- **Internet Connection**: For downloading dependencies and Tor.

## Installation

### Installation on Windows
1. **Download the Installer**:
   - Save `install_knitecrawler.bat` from this repository to `C:\Users\<YourUsername>\Desktop\KniteCrawler`.

2. **Prepare KniteCrawler Files**:
   - Place the `KniteCrawler` folder (containing `app.py`, `trackers.py`, etc.) in the same directory as the installer.

3. **Run the Installer**:
   - Open Command Prompt as Administrator.
   - Navigate to the directory:
     ```cmd
     cd C:\Users\<YourUsername>\Desktop\KniteCrawler
