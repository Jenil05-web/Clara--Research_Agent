# Clara 2.0 - Audio Setup Guide

## Issue: Voice Recording Not Working (FFmpeg Missing)

If you see the error: **"FileNotFoundError: The system cannot find the file specified"** when trying to record audio, you need to install FFmpeg.

## Quick Fix

### Option 1: Automatic Setup (Recommended)

```bash
python setup_ffmpeg.py
```

### Option 2: Manual Installation

#### On Windows:

1. **Download FFmpeg:**
   - Visit: https://www.gyan.dev/ffmpeg/builds/
   - Download the full version (not lite)
   - Extract to: `C:\ffmpeg`

2. **Add to System PATH:**
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "User variables", click "New":
     - Variable name: `PATH`
     - Variable value: `C:\ffmpeg\bin`
   - Click OK multiple times

3. **Verify Installation:**
   ```bash
   ffmpeg -version
   ```
   If you see version info, it's working!

#### On macOS:

```bash
brew install ffmpeg
```

#### On Linux:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

## After Installation

1. **Restart VS Code/Terminal** - Changes to PATH require a restart
2. **Try the voice recording** - Click the 🎙️ Record button in Clara
3. **Report any issues** - If it still doesn't work, check that `ffmpeg` is in your PATH

## What's FFmpeg?

FFmpeg is a multimedia framework that handles audio and video processing. Pydub (the library we use for audio) requires it to convert audio formats.

## Troubleshooting

**Still seeing the error after installing FFmpeg?**

1. Confirm FFmpeg is in PATH:

   ```bash
   where ffmpeg    # Windows
   which ffmpeg    # macOS/Linux
   ```

2. If not found, manually verify the installation:

   ```bash
   C:\ffmpeg\bin\ffmpeg.exe -version
   /usr/local/bin/ffmpeg -version
   ```

3. If found at a different location, add that folder to your PATH instead

4. Restart your IDE/terminal after updating PATH

## Code Changes Made

- Added FFmpeg auto-detection to `app.py`
- Added better error handling for missing FFmpeg
- Created this setup script for easy installation
