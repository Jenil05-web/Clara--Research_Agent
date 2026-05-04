#!/usr/bin/env python3
"""
Setup script to configure ffmpeg for audio processing.
Run this script to install ffmpeg and configure it for use with pydub.
"""

import os
import subprocess
import sys
import platform
from pathlib import Path


def check_ffmpeg():
    """Check if ffmpeg is available in PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
            check=False
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ffmpeg_windows():
    """Install ffmpeg on Windows using multiple methods."""
    print("🎬 Attempting to install ffmpeg on Windows...")
    
    # Method 1: Try winget
    print("\n[1/3] Trying Windows Package Manager (winget)...")
    try:
        result = subprocess.run(
            ["winget", "install", "ffmpeg"],
            capture_output=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✅ ffmpeg installed via winget!")
            return True
    except Exception as e:
        print(f"❌ winget failed: {e}")
    
    # Method 2: Try Chocolatey
    print("\n[2/3] Trying Chocolatey...")
    try:
        result = subprocess.run(
            ["choco", "install", "ffmpeg", "-y"],
            capture_output=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✅ ffmpeg installed via Chocolatey!")
            return True
    except Exception as e:
        print(f"❌ Chocolatey failed: {e}")
    
    # Method 3: Manual download and setup
    print("\n[3/3] Manual installation guide:")
    print("""
    📥 Download ffmpeg:
    1. Visit: https://ffmpeg.org/download.html
    2. Download the Windows build (full version recommended)
    3. Extract the ZIP file to: C:\\ffmpeg
    
    🔧 Add to PATH:
    1. Right-click "This PC" or "My Computer" → Properties
    2. Click "Advanced system settings"
    3. Click "Environment Variables"
    4. Under "User variables", click "New"
       - Variable name: PATH
       - Variable value: C:\\ffmpeg\\bin
    5. Click OK, then restart your computer
    
    ✅ Verify installation:
    1. Open Command Prompt
    2. Type: ffmpeg -version
    3. If you see version info, it's working!
    """)
    
    return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("🎙️  Audio Processing Setup for Clara")
    print("=" * 60)
    
    # Check if ffmpeg is already available
    print("\n📋 Checking for ffmpeg...")
    if check_ffmpeg():
        print("✅ ffmpeg is already installed and available!")
        print("\nYou're all set to use voice recording. Try it out!")
        return 0
    
    print("❌ ffmpeg not found in system PATH")
    
    # Platform-specific installation
    if platform.system() == "Windows":
        if install_ffmpeg_windows():
            print("\n🎉 ffmpeg installation successful!")
            print("Please restart VS Code/Streamlit to apply changes.")
            return 0
        else:
            print("\n⚠️  Automatic installation failed.")
            print("Please follow the manual installation guide above.")
            print("After installation, restart your terminal/IDE.")
            return 1
    
    elif platform.system() == "Darwin":  # macOS
        print("\n📦 macOS users: install ffmpeg with Homebrew")
        print("brew install ffmpeg")
        return 1
    
    elif platform.system() == "Linux":
        print("\n📦 Linux users: install ffmpeg with your package manager")
        print("Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("Fedora: sudo dnf install ffmpeg")
        print("Arch: sudo pacman -S ffmpeg")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
