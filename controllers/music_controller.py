from controllers.base_controller import BaseController
import cv2
import os
from pathlib import Path

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("WARNING: pygame not installed. Local music won't work. Install with: pip install pygame")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    import spotify_config
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    print("WARNING: spotipy not installed. Install with: pip install spotipy")


class MusicController(BaseController):
    def __init__(self):
        self.mode = "spotify"  # "local" or "spotify"
        self.music_playing = False
        self.current_track = "No track"
        self.current_artist = "Unknown"
        self.sp = None
        
        # Local music properties
        self.local_tracks = []
        self.current_track_index = 0
        self.local_music_dir = Path(__file__).resolve().parent.parent / "assets"
        
        # Performance optimization: cache state and limit API calls
        self.last_api_update = 0
        self.api_update_interval = 1.0  # Update from API only once per second
        
        # Device selection
        self.device_select_mode = False
        self.available_devices = []
        self.selected_device_index = 0
        self.active_device_id = None
        
        # Initialize local music
        if PYGAME_AVAILABLE:
            self._load_local_tracks()
        
        if SPOTIFY_AVAILABLE:
            self._init_spotify()
        else:
            print("ERROR: Spotify integration requires spotipy library")
            if not PYGAME_AVAILABLE:
                raise ImportError("Neither pygame nor spotipy available")

    def _init_spotify(self):
        """Initialize Spotify client with OAuth authentication."""
        try:
            # Check if credentials are configured
            if (spotify_config.SPOTIFY_CLIENT_ID == "your_client_id_here" or
                spotify_config.SPOTIFY_CLIENT_SECRET == "your_client_secret_here"):
                print("=" * 60)
                print("⚠️  SPOTIFY NOT CONFIGURED")
                print("=" * 60)
                print("1. Go to: https://developer.spotify.com/dashboard")
                print("2. Create an app and get Client ID + Secret")
                print("3. Add redirect URI: http://localhost:8888/callback")
                print("4. Edit spotify_config.py with your credentials")
                print("5. Make sure you have Spotify Premium")
                print("=" * 60)
                raise ValueError("Spotify credentials not configured in spotify_config.py")

            auth_manager = SpotifyOAuth(
                client_id=spotify_config.SPOTIFY_CLIENT_ID,
                client_secret=spotify_config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=spotify_config.SPOTIFY_REDIRECT_URI,
                scope=spotify_config.SPOTIFY_SCOPE,
                cache_path=".spotify_cache"
            )

            self.sp = spotipy.Spotify(auth_manager=auth_manager)

            # Test connection and check for active device
            devices = self.sp.devices()
            if not devices.get('devices'):
                print("=" * 60)
                print("⚠️  NO SPOTIFY DEVICES FOUND")
                print("=" * 60)
                print("CRITICAL: You must have Spotify open and running!")
                print()
                print("Steps to fix:")
                print("1. Open Spotify Desktop App or Mobile App")
                print("2. Wait 5-10 seconds for it to initialize")
                print("3. (Optional) Play any song")
                print("4. Keep Spotify running in background")
                print("5. Then gestures will work!")
                print("=" * 60)
            else:
                active_devices = [d for d in devices['devices'] if d.get('is_active')]
                total = len(devices['devices'])
                print(f"✓ Spotify connected: {total} device(s) available")
                if active_devices:
                    print(f"✓ Active device: {active_devices[0]['name']}")
                else:
                    print(f"⚠️  Devices found but none active - play something on Spotify")

            # Get current playback state
            self._update_playback_state()

        except Exception as e:
            print(f"ERROR: Failed to initialize Spotify: {e}")
            raise

    def _load_local_tracks(self):
        """Load MP3 files from assets directory."""
        try:
            if not self.local_music_dir.exists():
                print(f"WARNING: Music directory not found: {self.local_music_dir}")
                return

            # Find MP3 files in both assets/ and assets/music/
            root_tracks = list(self.local_music_dir.glob("*.mp3"))
            music_subdir = self.local_music_dir / "music"
            nested_tracks = list(music_subdir.glob("*.mp3")) if music_subdir.exists() else []

            self.local_tracks = sorted(root_tracks + nested_tracks, key=lambda p: p.name.lower())

            if self.local_tracks:
                print(f"✓ Found {len(self.local_tracks)} local tracks")
                for i, track in enumerate(self.local_tracks):
                    print(f"  [{i+1}] {track}")
            else:
                print(f"WARNING: No MP3 files found in {self.local_music_dir} or {self.local_music_dir / 'music'}")
        except Exception as e:
            print(f"Error loading local tracks: {e}")

    def _update_playback_state(self, force=False):
        """Update current playback state from Spotify (rate-limited for performance)."""
        import time
        now = time.time()
        
        # Rate limit: only update once per second unless forced
        if not force and (now - self.last_api_update) < self.api_update_interval:
            return
        
        self.last_api_update = now
        
        try:
            playback = self.sp.current_playback()
            if playback and playback.get('item'):
                self.music_playing = playback.get('is_playing', False)
                track = playback['item']
                self.current_track = track.get('name', 'Unknown')
                artists = track.get('artists', [])
                self.current_artist = artists[0].get('name', 'Unknown') if artists else 'Unknown'
            else:
                self.music_playing = False
                self.current_track = "No active device"
                self.current_artist = "Open Spotify & play"
        except Exception as e:
            # Silent fail - no device is common, don't spam console
            self.music_playing = False
            self.current_track = "No active device"
            self.current_artist = "Open Spotify & play"

    # lifecycle hooks
    def on_enter(self):
        print(f"Music Module Activated (Mode: {self.mode.upper()})")
        if self.mode == "spotify":
            self._check_devices_and_select()
            self._update_playback_state()
        else:
            # Local mode - auto-start first track
            if self.local_tracks:
                self.current_track_index = 0
                self.current_track = self.local_tracks[self.current_track_index].stem
                self.current_artist = "Local File"
                print(f"Ready to play: {self.current_track}")
                # Auto-start playback for better UX
                if PYGAME_AVAILABLE:
                    try:
                        track_path = str(self.local_tracks[self.current_track_index])
                        pygame.mixer.music.load(track_path)
                        pygame.mixer.music.play()
                        self.music_playing = True
                        print(f"Auto-playing: {self.current_track}")
                    except Exception as e:
                        print(f"Could not auto-start playback: {e}")
            else:
                print("No local tracks found. Add MP3 files to assets/music/")
    
    def set_mode(self, mode):
        """Set music mode to 'local' or 'spotify'."""
        self.mode = mode
        print(f"Music mode set to: {mode.upper()}")
        if mode == "local" and not PYGAME_AVAILABLE:
            print("ERROR: pygame not available for local playback")
        elif mode == "local":
            self._load_local_tracks()
            if self.local_tracks:
                self.current_track_index = min(self.current_track_index, len(self.local_tracks) - 1)
                self.current_track = self.local_tracks[self.current_track_index].stem
                self.current_artist = "Local File"
        elif mode == "spotify" and not SPOTIFY_AVAILABLE:
            print("ERROR: spotipy not available for Spotify")
    
    def get_spotify_devices(self):
        """Return list of available Spotify devices for menu display."""
        if not SPOTIFY_AVAILABLE or not self.sp:
            return []
        
        try:
            devices_response = self.sp.devices()
            self.available_devices = devices_response.get('devices', [])
            
            if not self.available_devices:
                print("⚠️  No Spotify devices found")
                return []
            
            # Return device info for menu
            return [{"name": d['name'], "type": d['type'], "id": d['id']} 
                    for d in self.available_devices]
        except Exception as e:
            print(f"Error fetching devices: {e}")
            return []
    
    def select_spotify_device(self, index):
        """Select a Spotify device by index."""
        if not self.available_devices or index >= len(self.available_devices):
            print("Invalid device index")
            return
        
        try:
            device = self.available_devices[index]
            self.active_device_id = device['id']
            self.sp.transfer_playback(device_id=self.active_device_id, force_play=False)
            print(f"✓ Selected device: {device['name']}")
        except Exception as e:
            print(f"Error selecting device: {e}")
    
    def _check_devices_and_select(self):
        """Check available devices and enter selection mode if multiple."""
        try:
            devices_response = self.sp.devices()
            self.available_devices = devices_response.get('devices', [])
            
            if not self.available_devices:
                print("⚠️  No Spotify devices found - open Spotify app")
                self.device_select_mode = False
                return
            
            # Find currently active device
            active = [d for d in self.available_devices if d.get('is_active')]
            
            if len(self.available_devices) == 1:
                # Only one device - auto select it
                self.active_device_id = self.available_devices[0]['id']
                self.device_select_mode = False
                print(f"✓ Auto-selected device: {self.available_devices[0]['name']}")
            elif active:
                # Active device exists - use it
                self.active_device_id = active[0]['id']
                self.device_select_mode = False
                print(f"✓ Using active device: {active[0]['name']}")
            else:
                # Multiple devices, none active - show selection menu
                self.device_select_mode = True
                self.selected_device_index = 0
                print(f"→ Select device: {len(self.available_devices)} available")
        except Exception as e:
            print(f"Error checking devices: {e}")
            self.device_select_mode = False

    def on_exit(self):
        print("Music Module Deactivated")

    def handle_command(self, command):
        # Device selection mode - navigate and select
        if self.device_select_mode:
            if command == "NEXT_TRACK":
                self.selected_device_index = (self.selected_device_index + 1) % len(self.available_devices)
                print(f"Device → {self.available_devices[self.selected_device_index]['name']}")
            elif command == "PREV_TRACK":
                self.selected_device_index = (self.selected_device_index - 1) % len(self.available_devices)
                print(f"Device → {self.available_devices[self.selected_device_index]['name']}")
            elif command == "PINCH":
                self._select_device(self.selected_device_index)
            return
        
        # Normal music control
        if command == "TOGGLE_PLAY":
            self.toggle_play_pause()
        elif command == "STOP":
            self.stop_music()
        elif command == "NEXT_TRACK":
            self.next_track()
        elif command == "PREV_TRACK":
            self.prev_track()
    
    def _select_device(self, index):
        """Activate the selected device."""
        try:
            device = self.available_devices[index]
            self.active_device_id = device['id']
            
            # Transfer playback to this device
            self.sp.transfer_playback(device_id=self.active_device_id, force_play=False)
            
            print(f"✓ Selected device: {device['name']}")
            self.device_select_mode = False
        except Exception as e:
            print(f"Error selecting device: {e}")

    def toggle_play_pause(self):
        """Toggle play/pause for current mode."""
        if self.mode == "local":
            self._toggle_local_playback()
        else:
            self._toggle_spotify_playback()
    
    def _toggle_local_playback(self):
        """Toggle local music playback with pygame."""
        if not PYGAME_AVAILABLE:
            print("pygame not available")
            return
        
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.music_playing = False
                print("Local Music Paused")
            else:
                if pygame.mixer.music.get_pos() == -1:
                    # Not loaded, load and play
                    if self.local_tracks:
                        track_path = str(self.local_tracks[self.current_track_index])
                        pygame.mixer.music.load(track_path)
                        pygame.mixer.music.play()
                        self.current_track = self.local_tracks[self.current_track_index].stem
                        self.current_artist = "Local File"
                        self.music_playing = True
                        print(f"Playing: {self.current_track}")
                else:
                    # Resume
                    pygame.mixer.music.unpause()
                    self.music_playing = True
                    print("Local Music Resumed")
        except Exception as e:
            print(f"Error with local playback: {e}")
    
    def _toggle_spotify_playback(self):
        """Toggle play/pause on Spotify."""
        try:
            playback = self.sp.current_playback()
            
            if playback and playback.get('is_playing'):
                self.sp.pause_playback()
                self.music_playing = False
                print("Music Paused")
            else:
                # Try to resume playback on any available device
                devices = self.sp.devices()
                if devices and devices.get('devices'):
                    # If there's a device, try to play
                    device_id = devices['devices'][0]['id']
                    self.sp.start_playback(device_id=device_id)
                    self.music_playing = True
                    print("Music Playing")
                else:
                    print("No Spotify device available - open Spotify and play something first")
                    return
            
            self._update_playback_state(force=True)
        except Exception as e:
            print(f"Error toggling playback: {e}")
            print("Make sure Spotify is open on a device")

    def stop_music(self):
        """Pause playback (Spotify doesn't have 'stop')."""
        try:
            self.sp.pause_playback()
            self.music_playing = False
            print("Music Stopped")
            self._update_playback_state(force=True)
        except Exception as e:
            print(f"Error stopping playback: {e}")

    def next_track(self):
        """Skip to next track."""
        if self.mode == "local":
            self._next_local_track()
        else:
            self._next_spotify_track()
    
    def _next_local_track(self):
        """Play next local track."""
        if not PYGAME_AVAILABLE or not self.local_tracks:
            return
        
        try:
            self.current_track_index = (self.current_track_index + 1) % len(self.local_tracks)
            track_path = str(self.local_tracks[self.current_track_index])
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            self.current_track = self.local_tracks[self.current_track_index].stem
            self.current_artist = "Local File"
            self.music_playing = True
            print(f"Next Track: {self.current_track}")
        except Exception as e:
            print(f"Error playing next track: {e}")
    
    def _next_spotify_track(self):
        """Skip to next track on Spotify."""
        try:
            devices = self.sp.devices()
            if not devices.get('devices'):
                print("No Spotify device available")
                return
                
            self.sp.next_track()
            self.music_playing = True
            print("Next Track")
            # Small delay for Spotify to update
            import time
            time.sleep(0.5)
            self._update_playback_state(force=True)
        except Exception as e:
            print(f"Error skipping to next track: {e}")

    def prev_track(self):
        """Skip to previous track."""
        if self.mode == "local":
            self._prev_local_track()
        else:
            self._prev_spotify_track()
    
    def _prev_local_track(self):
        """Play previous local track."""
        if not PYGAME_AVAILABLE or not self.local_tracks:
            return
        
        try:
            self.current_track_index = (self.current_track_index - 1) % len(self.local_tracks)
            track_path = str(self.local_tracks[self.current_track_index])
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            self.current_track = self.local_tracks[self.current_track_index].stem
            self.current_artist = "Local File"
            self.music_playing = True
            print(f"Previous Track: {self.current_track}")
        except Exception as e:
            print(f"Error playing previous track: {e}")
    
    def _prev_spotify_track(self):
        """Skip to previous track on Spotify."""
        try:
            devices = self.sp.devices()
            if not devices.get('devices'):
                print("No Spotify device available")
                return
                
            self.sp.previous_track()
            self.music_playing = True
            print("Previous Track")
            # Small delay for Spotify to update
            import time
            time.sleep(0.5)
            self._update_playback_state(force=True)
        except Exception as e:
            print(f"Error going to previous track: {e}")

    def get_status(self):
        """Get current playback status (cached, updates automatically)."""
        if self.mode == "local":
            if PYGAME_AVAILABLE:
                self.music_playing = pygame.mixer.music.get_busy()
            return "Playing" if self.music_playing else "Paused"
        else:
            self._update_playback_state()  # Rate-limited internally
            return "Playing" if self.music_playing else "Paused"

    def update(self, frame):
        """Render music module UI overlay onto the frame."""
        
        # Device selection menu
        if self.device_select_mode:
            self._draw_device_menu(frame)
            return
        
        # Normal playback UI
        status = self.get_status()
        
        # Display mode with track count
        if self.mode == "local":
            mode_display = f"LOCAL MUSIC ({len(self.local_tracks)} tracks)"
        else:
            mode_display = f"{self.mode.upper()} MODE"
        cv2.putText(
            frame,
            mode_display,
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 200, 255),
            2,
        )
        
        # Show current track index for local mode
        if self.mode == "local" and self.local_tracks:
            track_indicator = f"[{self.current_track_index + 1}/{len(self.local_tracks)}]"
            cv2.putText(
                frame,
                track_indicator,
                (50, 210),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 100),
                1,
            )
        
        # Display track info
        track_display = self.current_track[:30] + "..." if len(self.current_track) > 30 else self.current_track
        artist_display = self.current_artist[:25] + "..." if len(self.current_artist) > 25 else self.current_artist

        cv2.putText(
            frame,
            f"Status: {status}",
            (50, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Track: {track_display}",
            (50, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
        )
        cv2.putText(
            frame,
            f"Artist: {artist_display}",
            (50, 185),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
        )
    
    def _draw_device_menu(self, frame):
        """Draw device selection menu overlay."""
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (100, 100), (w - 100, h - 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Title
        cv2.putText(frame, "SELECT SPOTIFY DEVICE", (150, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Device list
        y_start = 200
        for i, device in enumerate(self.available_devices):
            y = y_start + i * 50
            
            # Highlight selected device
            if i == self.selected_device_index:
                cv2.rectangle(frame, (120, y - 30), (w - 120, y + 10), (0, 255, 0), -1)
                color = (0, 0, 0)
            else:
                color = (255, 255, 255)
            
            # Device name
            name = device['name'][:35] + "..." if len(device['name']) > 35 else device['name']
            cv2.putText(frame, name, (140, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Device type (smaller text)
            device_type = device.get('type', 'Unknown')
            cv2.putText(frame, f"({device_type})", (140, y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Instructions
        cv2.putText(frame, "Swipe: Navigate | Pinch: Select",
                    (150, h - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
