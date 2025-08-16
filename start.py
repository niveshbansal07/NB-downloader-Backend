#!/usr/bin/env python3
"""
NB Downloader Startup Script
This script helps you start both the backend and frontend servers for local development.
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ ffmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg is not installed")
        print("Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    os.chdir('backend')
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend server failed to start: {e}")

def start_frontend():
    """Start the frontend server"""
    print("🌐 Starting frontend server...")
    os.chdir('frontend')
    try:
        subprocess.run([sys.executable, '-m', 'http.server', '3000'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend server failed to start: {e}")

def main():
    """Main function"""
    print("🎬 NB Downloader - Development Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('backend').exists() or not Path('frontend').exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check ffmpeg
    if not check_ffmpeg():
        print("\n⚠️  Continuing without ffmpeg (some features may not work)")
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    print("\n🎯 Starting servers...")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:3000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop all servers")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()
