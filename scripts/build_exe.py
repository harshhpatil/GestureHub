"""
Build script for creating Windows .exe using PyInstaller
Run: python build_exe.py
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

print("Building GestureHUB Windows .exe...")
print("=" * 60)

# PyInstaller command with enhanced settings
pyinstaller_cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--name=GestureHUB",
    "--onefile",  # Single executable
    "--windowed",  # No console window
    f"--icon={project_dir / 'assets' / 'icon.ico'}" if (project_dir / "assets" / "icon.ico").exists() else "",
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
    "--distpath=dist",
    str(project_dir / "app" / "gui_launcher.py"),
]

# Filter out empty strings
pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if cmd]

try:
    subprocess.check_call(pyinstaller_cmd)
    print("\n" + "=" * 60)
    print("✓ Windows .exe build completed successfully!")
    print(f"Executable located at: {dist_dir / 'GestureHUB.exe'}")
    print("\nTo distribute:")
    print("1. Copy the .exe file")
    print("2. Create an installer using NSIS or WiX")
    print("=" * 60)
except subprocess.CalledProcessError as e:
    print(f"\n✗ Build failed: {e}")
    sys.exit(1)
