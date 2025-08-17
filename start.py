#!/usr/bin/env python3
"""
NB Downloader Startup Script
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ ffmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not installed. Please install ffmpeg for downloads to work.")
        return False

def install_dependencies():
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_backend():
    print("🚀 Starting backend server...")
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'app:app',
            '--host', '0.0.0.0',
            '--port', '8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")

def start_frontend():
    print("🌐 Starting frontend server...")
    os.chdir('frontend')
    try:
        subprocess.run([sys.executable, '-m', 'http.server', '3000'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")

def main():
    print("🎬 NB Downloader - Development Startup")
    print("=" * 50)

    if not Path('frontend').exists():
        print("❌ 'frontend' folder not found. Run this from project root.")
        sys.exit(1)

    check_ffmpeg()
    install_dependencies()

    print("\n🎯 Starting servers...")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:3000")

    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    time.sleep(3)
    start_frontend()

if __name__ == "__main__":
    main()
