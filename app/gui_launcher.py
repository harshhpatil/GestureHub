"""
GestureHUB GUI Launcher
A modern tkinter-based interface for the GestureHUB application.
Packageable as .exe (via PyInstaller) and .deb (via fpm).
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import psutil
import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class GestureHUBGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GestureHUB Control Panel")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1a1a1a")
        
        # Set window icon (optional)
        try:
            self.root.iconbitmap(default=None)
        except:
            pass
        
        # Current processes
        self.processes = {
            "main": None,
            "server": None,
        }
        
        # Get the script directory
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # Check dependencies
        self.check_dependencies()
        
        # Configure styles
        self.setup_styles()
        
        # Build UI
        self.create_ui()
        
        # Update status periodically
        self.update_status()

    def check_dependencies(self):
        """Check if required dependencies are available."""
        self.dependencies = {
            "mediapipe": False,
            "cv2": False,
            "pygame": False,
            "spotipy": False,
            "psutil": False,
        }
        
        # Check each dependency
        try:
            import mediapipe
            self.dependencies["mediapipe"] = True
        except ImportError:
            pass
            
        try:
            import cv2
            self.dependencies["cv2"] = True
        except ImportError:
            pass
            
        try:
            import pygame
            self.dependencies["pygame"] = True
        except ImportError:
            pass
            
        try:
            import spotipy
            self.dependencies["spotipy"] = True
        except ImportError:
            pass
            
        try:
            import psutil
            self.dependencies["psutil"] = True
        except ImportError:
            pass

    def setup_styles(self):
        """Configure ttk styles for modern appearance."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Color scheme (cyan accent matching dashboard)
        self.bg_color = "#1a1a1a"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#00ffcc"
        self.accent_dark = "#00cc99"
        self.button_bg = "#2a2a2a"
        self.button_hover = "#3a3a3a"
        
        # Configure ttk styles
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("Title.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Helvetica", 16, "bold"))
        style.configure("Heading.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Helvetica", 12, "bold"))
        style.configure("TButton", background=self.button_bg, foreground=self.fg_color)
        
        # Custom button style
        style.configure("Custom.TButton",
                       background=self.button_bg,
                       foreground=self.accent_color,
                       borderwidth=1,
                       focuscolor="none",
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        style.map("Custom.TButton",
                 background=[("active", self.button_hover)])
        
        style.configure("Danger.TButton",
                       background="#3a1a1a",
                       foreground="white",
                       borderwidth=1,
                       focuscolor="none",
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        style.map("Danger.TButton",
                 background=[("active", "#5a2a2a")])

    def create_ui(self):
        """Build the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main_frame)
        
        # Content area with notebook (tabs)
        self.create_content(main_frame)
        
        # Footer with status
        self.create_footer(main_frame)

    def create_header(self, parent):
        """Create header with title."""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = ttk.Label(header, text="🎮 GestureHUB Control Panel", style="Title.TLabel")
        title.pack(side=tk.LEFT, pady=10)
        
        # Version or info
        info = ttk.Label(header, text="Gesture Recognition & Game Suite", foreground="#999999")
        info.pack(side=tk.LEFT, padx=20)

    def create_content(self, parent):
        """Create main content area with tabs."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure notebook style
        style = ttk.Style()
        style.configure("TNotebook", background=self.bg_color)
        style.configure("TNotebook.Tab", background=self.button_bg, foreground=self.fg_color)
        
        # Tab 1: Quick Launch
        self.create_quick_launch_tab()
        
        # Tab 2: System Control
        self.create_system_control_tab()
        
        # Tab 3: Logs & Monitoring
        self.create_logs_tab()
        
        # Tab 4: Settings
        self.create_settings_tab()

    def create_quick_launch_tab(self):
        """Create the Quick Launch tab with game buttons."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚀 Quick Launch")
        
        # Padding
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(content, text="Select Mode to Launch", style="Heading.TLabel")
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Games Section
        games_label = ttk.Label(content, text="🎮 Games", style="Heading.TLabel")
        games_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.game_buttons = {}
        games = [
            ("🦖 Dino Game", "dino", 2, 0),
            ("🐟 Catch Game", "catch", 2, 1),
            ("🍎 Fruit Game", "fruit", 2, 2),
        ]
        
        for label, key, row, col in games:
            btn = self.create_launch_button(content, label, key, row, col)
            self.game_buttons[key] = btn
        
        # Features Section
        features_label = ttk.Label(content, text="✨ Features", style="Heading.TLabel")
        features_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        
        self.feature_buttons = {}
        features = [
            ("🎵 Music Player", "music", 4, 0),
            ("🎨 Drawing Board", "drawing", 4, 1),
            ("⚙️ System Controls", "system", 4, 2),
        ]
        
        for label, key, row, col in features:
            btn = self.create_launch_button(content, label, key, row, col)
            self.feature_buttons[key] = btn
        
        # Full Experience
        full_label = ttk.Label(content, text="🌟 Full Experience", style="Heading.TLabel")
        full_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        
        full_btn = ttk.Button(content, text="🎥 Start Full Gesture Mode",
                             command=self.launch_main, style="Custom.TButton")
        full_btn.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=10, ipady=10)
        self.full_mode_btn = full_btn
        
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=1)

    def create_launch_button(self, parent, text, key, row, col):
        """Create a styled launch button."""
        btn = ttk.Button(parent, text=text, style="Custom.TButton",
                        command=lambda: self.launch_mode(key))
        btn.grid(row=row, column=col, sticky=tk.EW, padx=5, pady=5, ipady=15)
        return btn

    def create_system_control_tab(self):
        """Create system control tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ System")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(content, text="System Management", style="Heading.TLabel")
        title.pack(pady=(0, 20))
        
        # Server Status Frame
        status_frame = ttk.LabelFrame(content, text="Server Status", padding=15)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.server_status_label = ttk.Label(status_frame, text="Status: Stopped", foreground="#ff6666")
        self.server_status_label.pack(side=tk.LEFT, padx=10)
        
        self.server_port_label = ttk.Label(status_frame, text="Port: 8000", foreground="#cccccc")
        self.server_port_label.pack(side=tk.LEFT, padx=10)
        
        # Server Controls
        server_controls = ttk.Frame(content)
        server_controls.pack(fill=tk.X, pady=10)
        
        self.start_server_btn = ttk.Button(server_controls, text="▶ Start Server",
                                          command=self.start_server, style="Custom.TButton")
        self.start_server_btn.pack(side=tk.LEFT, padx=5, ipady=8, ipadx=15)
        
        self.stop_server_btn = ttk.Button(server_controls, text="⏹ Stop Server",
                                         command=self.stop_server, style="Danger.TButton")
        self.stop_server_btn.pack(side=tk.LEFT, padx=5, ipady=8, ipadx=15)
        
        # Process Info
        info_frame = ttk.LabelFrame(content, text="Running Processes", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.processes_text = scrolledtext.ScrolledText(info_frame, height=10, width=60,
                                                       bg="#2a2a2a", fg="#00ffcc",
                                                       insertbackground="#00ffcc",
                                                       font=("Courier", 9))
        self.processes_text.pack(fill=tk.BOTH, expand=True)
        
        # Stop All Button
        stop_all_btn = ttk.Button(content, text="🛑 Stop All Processes",
                                 command=self.stop_all, style="Danger.TButton")
        stop_all_btn.pack(fill=tk.X, pady=10, ipady=8)

    def create_logs_tab(self):
        """Create logs and monitoring tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Logs & Monitoring")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(content, text="Application Logs", style="Heading.TLabel")
        title.pack(pady=(0, 10))
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(content, height=20, width=80,
                                                 bg="#2a2a2a", fg="#00ff00",
                                                 insertbackground="#00ff00",
                                                 font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.log_text.tag_config("INFO", foreground="#00ffff")
        self.log_text.tag_config("SUCCESS", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffaa00")
        self.log_text.tag_config("ERROR", foreground="#ff6666")
        
        # Add initial log message
        self.add_log("System initialized", "INFO")
        self.add_log(f"Script directory: {self.script_dir}", "INFO")
        
        # Log dependency status
        self.add_log("Checking dependencies...", "INFO")
        for dep, available in self.dependencies.items():
            status = "AVAILABLE" if available else "MISSING"
            level = "SUCCESS" if available else "WARNING"
            self.add_log(f"{dep}: {status}", level)

    def create_settings_tab(self):
        """Create settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Settings")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(content, text="Application Settings", style="Heading.TLabel")
        title.pack(pady=(0, 20))
        
        # Settings options
        settings_frame = ttk.LabelFrame(content, text="Configuration", padding=15)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Camera settings
        ttk.Label(settings_frame, text="Camera Index:", foreground=self.accent_color).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.camera_var = tk.StringVar(value="1")
        camera_spin = ttk.Spinbox(settings_frame, from_=0, to=10, textvariable=self.camera_var, width=10)
        camera_spin.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Resolution
        ttk.Label(settings_frame, text="Resolution:", foreground=self.accent_color).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.resolution_var = tk.StringVar(value="640x480")
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var,
                                       values=["320x240", "640x480", "1280x720", "1920x1080"],
                                       width=15, state="readonly")
        resolution_combo.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # FPS
        ttk.Label(settings_frame, text="FPS:", foreground=self.accent_color).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.StringVar(value="30")
        fps_spin = ttk.Spinbox(settings_frame, from_=15, to=60, textvariable=self.fps_var, width=10)
        fps_spin.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Save Spotify credentials
        oauth_frame = ttk.LabelFrame(content, text="Spotify Integration", padding=15)
        oauth_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(oauth_frame, text="Spotify settings are in spotify_config.py", foreground="#999999").pack()
        
        # Help text
        help_frame = ttk.LabelFrame(content, text="About", padding=15)
        help_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Dependency status
        dep_frame = ttk.LabelFrame(content, text="Dependencies", padding=15)
        dep_frame.pack(fill=tk.X, pady=10)
        
        dep_text = ""
        for dep, available in self.dependencies.items():
            status = "✓" if available else "✗"
            dep_text += f"{status} {dep}\n"
        
        dep_label = ttk.Label(dep_frame, text=dep_text, justify=tk.LEFT, foreground="#cccccc")
        dep_label.pack(anchor=tk.W)
        
        # Help text
        help_text = """
GestureHUB - Gesture Recognition & Game Suite

This application uses MediaPipe for hand gesture recognition to control:
• Games (Dino, Catch, Fruit)
• Music Player (Local & Spotify)
• Drawing Board
• System Controls

Supported Platforms:
✓ Windows (via .exe)
✓ Linux (via .deb)
✓ macOS (via PyInstaller)

To report issues or contribute, visit the project repository.
        """
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, foreground="#999999")
        help_label.pack(anchor=tk.W)

    def create_footer(self, parent):
        """Create footer with status bar."""
        footer = ttk.Frame(parent)
        footer.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        
        self.status_label = ttk.Label(footer, text="Ready", foreground="#666666")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.time_label = ttk.Label(footer, text="", foreground="#666666")
        self.time_label.pack(side=tk.RIGHT, padx=10)

    def launch_mode(self, mode):
        """Launch the main app directly into a specific mode."""
        self.launch_main(start_mode=mode)

    def launch_main(self, start_mode=None):
        """Launch the main gesture recognition application."""
        if self.processes["main"] is not None:
            messagebox.showwarning("Already Running", "Main application is already running!")
            return
        
        # Check critical dependencies
        missing_deps = []
        if not self.dependencies["mediapipe"]:
            missing_deps.append("mediapipe")
        if not self.dependencies["cv2"]:
            missing_deps.append("opencv-python")
            
        if missing_deps:
            messagebox.showerror("Missing Dependencies", 
                               f"Cannot launch main application.\n\nMissing required packages:\n{', '.join(missing_deps)}\n\nRun: pip install -r requirements.txt")
            return
        
        if start_mode:
            self.add_log(f"Starting main gesture recognition in {start_mode} mode...", "INFO")
            self.status_label.config(text=f"Starting {start_mode} mode...")
        else:
            self.add_log("Starting main gesture recognition...", "INFO")
            self.status_label.config(text="Starting main application...")
        
        try:
            main_py = self.script_dir / "main.py"
            if not main_py.exists():
                self.add_log(f"Error: main.py not found at {main_py}", "ERROR")
                messagebox.showerror("Error", f"main.py not found at {main_py}")
                return
            
            env = os.environ.copy()
            if start_mode:
                env["GESTUREHUB_START_MODE"] = start_mode
            self.processes["main"] = subprocess.Popen(
                [sys.executable, str(main_py)],
                env=env,
                cwd=self.project_root,
            )
            self.add_log("Main application started successfully", "SUCCESS")
            self.status_label.config(text="✓ Main application running")
            self.full_mode_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            self.add_log(f"Error launching main: {str(e)}", "ERROR")
            messagebox.showerror("Launch Error", f"Could not launch main application:\n{str(e)}")
            self.status_label.config(text="Error starting application")

    def start_server(self):
        """Start the command server."""
        if self.processes["server"] is not None:
            messagebox.showwarning("Already Running", "Server is already running!")
            return
        
        self.add_log("Starting command server...", "INFO")
        self.status_label.config(text="Starting server...")
        
        try:
            server_py = self.script_dir / "run_server.py"
            if not server_py.exists():
                self.add_log(f"Error: run_server.py not found at {server_py}", "ERROR")
                messagebox.showerror("Error", f"run_server.py not found at {server_py}")
                return
            
            self.processes["server"] = subprocess.Popen(
                [sys.executable, str(server_py)],
                cwd=self.project_root,
            )
            self.add_log("Command server started on http://0.0.0.0:8000", "SUCCESS")
            self.status_label.config(text="✓ Server running on port 8000")
            self.start_server_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            self.add_log(f"Error starting server: {str(e)}", "ERROR")
            messagebox.showerror("Server Error", f"Could not start server:\n{str(e)}")
            self.status_label.config(text="Error starting server")

    def stop_server(self):
        """Stop the command server."""
        if self.processes["server"] is None:
            messagebox.showinfo("Not Running", "Server is not running.")
            return
        
        try:
            self.processes["server"].terminate()
            self.processes["server"].wait(timeout=5)
            self.processes["server"] = None
            self.add_log("Command server stopped", "WARNING")
            self.status_label.config(text="Server stopped")
            self.start_server_btn.config(state=tk.NORMAL)
            
        except subprocess.TimeoutExpired:
            self.processes["server"].kill()
            self.processes["server"] = None
            self.add_log("Command server force killed", "ERROR")

    def stop_all(self):
        """Stop all running processes."""
        if messagebox.askyesno("Confirm", "Stop all running processes?"):
            for key, proc in self.processes.items():
                if proc is not None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=2)
                        self.processes[key] = None
                    except:
                        try:
                            proc.kill()
                            self.processes[key] = None
                        except:
                            pass
            
            self.add_log("All processes stopped", "WARNING")
            self.status_label.config(text="All processes stopped")
            self.full_mode_btn.config(state=tk.NORMAL)
            self.start_server_btn.config(state=tk.NORMAL)

    def add_log(self, message, level="INFO"):
        """Add a message to the log display."""
        try:
            if self.log_text.winfo_exists():
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_msg = f"[{timestamp}] {message}\n"
                self.log_text.insert(tk.END, log_msg, level)
                self.log_text.see(tk.END)
        except:
            pass

    def update_status(self):
        """Update status information periodically."""
        try:
            # Update time
            self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
            
            # Update process status
            if self.processes_text.winfo_exists():
                info = "Running Processes:\n\n"
                
                for name, proc in self.processes.items():
                    if proc is not None and proc.poll() is None:
                        try:
                            p = psutil.Process(proc.pid)
                            info += f"✓ {name.upper()}\n"
                            info += f"  PID: {proc.pid}\n"
                            info += f"  Memory: {p.memory_info().rss / 1024 / 1024:.1f} MB\n"
                            info += f"  Status: Running\n\n"
                        except:
                            info += f"✓ {name.upper()} (PID: {proc.pid})\n\n"
                    else:
                        info += f"✗ {name.upper()}\n"
                        info += f"  Status: Not running\n\n"
                        # Check if process has terminated
                        if proc is not None and proc.poll() is not None:
                            self.processes[name] = None
                            if name == "main":
                                self.full_mode_btn.config(state=tk.NORMAL)
                            elif name == "server":
                                self.start_server_btn.config(state=tk.NORMAL)
                
                self.processes_text.config(state=tk.NORMAL)
                self.processes_text.delete(1.0, tk.END)
                self.processes_text.insert(1.0, info)
                self.processes_text.config(state=tk.DISABLED)
        except:
            pass
        
        # Schedule next update
        self.root.after(1000, self.update_status)

    def on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel("Quit", "Stop all processes and exit?"):
            self.stop_all()
            self.root.destroy()


def main():
    """Main entry point."""
    try:
        root = tk.Tk()
        app = GestureHUBGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Error starting GestureHUB GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
