#!/usr/bin/env python3
"""
Build script for creating macOS .app package using PyInstaller
Run: python build_app.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Get project directories
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent

# Ensure PyInstaller is installed
try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

# Clean previous builds
dist_dir = project_dir / "dist"
build_dir = project_dir / "build"
if dist_dir.exists():
    shutil.rmtree(dist_dir)
if build_dir.exists():
    shutil.rmtree(build_dir)

print("Building GestureHUB macOS .app package...")
print("=" * 60)

# PyInstaller command
pyinstaller_cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--name=GestureHUB",
    "--onefile",
    "--windowed",
    f"--add-data={project_dir / 'assets'}:assets",
    f"--add-data={project_dir / 'config'}:config",
    f"--add-data={project_dir / 'command_layer'}:command_layer",
    f"--add-data={project_dir / 'controllers'}:controllers",
    f"--add-data={project_dir / 'core'}:core",
    f"--add-data={project_dir / 'games'}:games",
    f"--add-data={project_dir / 'gesture_engine'}:gesture_engine",
    f"--add-data={project_dir / 'networking'}:networking",
    "--collect-all=mediapipe",
    "--collect-all=cv2",
    "--hidden-import=mediapipe",
    "--hidden-import=cv2",
    "--hidden-import=pathlib",
    "--hidden-import=psutil",
    "--hidden-import=uvicorn",
    "--hidden-import=fastapi",
    "--osx-bundle-identifier=com.gesturehub.app",
    "--distpath=dist",
    "--buildpath=build",
    "--specpath=build",
    str(project_dir / "app" / "gui_launcher.py"),
]

try:
    subprocess.check_call(pyinstaller_cmd)
    print("\n" + "=" * 60)
    print("✓ macOS .app package built successfully!")
    app_path = dist_dir / "GestureHUB.app"
    print(f"App bundle located at: {app_path}")
    
    # Create a DMG (optional)
    print("\n" + "=" * 60)
    print("To create a .dmg installer file:")
    print("1. Install create-dmg: pip install create-dmg")
    print("2. Run: create-dmg dist/GestureHUB.dmg dist/GestureHUB.app")
    print("=" * 60)
except subprocess.CalledProcessError as e:
    print(f"\n✗ Build failed: {e}")
    sys.exit(1)
