#!/usr/bin/env python3
"""
NB Downloader Startup Script - Updated
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# === CONFIGURATION ===
# Agar backend Railway pe deployed hai, yahan URL set karo
RAILWAY_BACKEND_URL = "https://your-backend.up.railway.app"
USE_REMOTE_BACKEND = True  # True = Railway, False = local

# Local backend config
LOCAL_BACKEND_HOST = "0.0.0.0"
LOCAL_BACKEND_PORT = "8000"

# Frontend config
FRONTEND_PORT = "3000"


# === UTILITY FUNCTIONS ===
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


# === BACKEND ===
def start_backend():
    if USE_REMOTE_BACKEND:
        print(f"🌐 Using remote backend: {RAILWAY_BACKEND_URL}")
        return  # No need to start local backend
    print("🚀 Starting local backend server...")
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'app:app',
            '--host', LOCAL_BACKEND_HOST,
            '--port', LOCAL_BACKEND_PORT
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")


# === FRONTEND ===
def start_frontend():
    print("🌐 Starting frontend server...")
    if not Path('frontend').exists():
        print("❌ 'frontend' folder not found. Run this from project root.")
        sys.exit(1)

    os.chdir('frontend')

    # Set API URL for frontend (replace in your config file if needed)
    if USE_REMOTE_BACKEND:
        print(f"🔗 Frontend will use remote backend: {RAILWAY_BACKEND_URL}")
    else:
        print(f"🔗 Frontend will use local backend: http://{LOCAL_BACKEND_HOST}:{LOCAL_BACKEND_PORT}")

    try:
        subprocess.run([sys.executable, '-m', 'http.server', FRONTEND_PORT], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")


# === MAIN ===
def main():
    print("🎬 NB Downloader - Development Startup")
    print("=" * 50)

    check_ffmpeg()
    install_dependencies()

    print("\n🎯 Starting servers...")
    if not USE_REMOTE_BACKEND:
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        time.sleep(3)

    start_frontend()


if __name__ == "__main__":
    main()
