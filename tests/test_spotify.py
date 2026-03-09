#!/usr/bin/env python3
"""
Spotify Device Diagnostics
Run this to check your Spotify connection and available devices.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotify_config

def test_spotify_connection():
    print("=" * 60)
    print("SPOTIFY API DIAGNOSTICS")
    print("=" * 60)
    
    try:
        # Initialize Spotify client
        auth_manager = SpotifyOAuth(
            client_id=spotify_config.SPOTIFY_CLIENT_ID,
            client_secret=spotify_config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=spotify_config.SPOTIFY_REDIRECT_URI,
            scope=spotify_config.SPOTIFY_SCOPE,
            cache_path=".spotify_cache"
        )
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("✓ Authentication successful")
        
        # Check user info
        user = sp.current_user()
        print(f"✓ Logged in as: {user['display_name']} ({user['id']})")
        print(f"✓ Account type: {user.get('product', 'unknown')}")
        
        if user.get('product') != 'premium':
            print("\n⚠️  WARNING: You need Spotify Premium for playback control!")
            print("   Free accounts cannot use the Playback API")
            return
        
        print("\n" + "=" * 60)
        print("CHECKING DEVICES")
        print("=" * 60)
        
        # Get devices
        devices_response = sp.devices()
        devices = devices_response.get('devices', [])
        
        if not devices:
            print("❌ No devices found!")
            print("\nTO FIX THIS:")
            print("1. Open Spotify desktop app or mobile app")
            print("2. Play ANY song (even just press play)")
            print("3. The device will become active")
            print("4. Run this script again")
        else:
            print(f"✓ Found {len(devices)} device(s):\n")
            for i, device in enumerate(devices, 1):
                active = "🟢 ACTIVE" if device.get('is_active') else "⚪ Inactive"
                print(f"{i}. {device['name']}")
                print(f"   Type: {device['type']}")
                print(f"   Status: {active}")
                print(f"   Volume: {device.get('volume_percent', 0)}%")
                print(f"   ID: {device['id']}")
                print()
        
        print("=" * 60)
        print("CHECKING CURRENT PLAYBACK")
        print("=" * 60)
        
        # Get current playback
        playback = sp.current_playback()
        
        if playback:
            print("✓ Playback state found")
            print(f"   Playing: {playback.get('is_playing', False)}")
            
            if playback.get('item'):
                track = playback['item']
                artists = ', '.join([a['name'] for a in track['artists']])
                print(f"   Track: {track['name']}")
                print(f"   Artist: {artists}")
                print(f"   Album: {track['album']['name']}")
            
            if playback.get('device'):
                dev = playback['device']
                print(f"   Active Device: {dev['name']} ({dev['type']})")
        else:
            print("❌ No playback state")
            print("   This means no device is currently active")
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60)
        
        if devices and any(d.get('is_active') for d in devices):
            print("✅ Everything looks good! You can use GestureHub.")
        elif devices:
            print("⚠️  Devices found but none active")
            print("   → Start playing something on Spotify")
        else:
            print("❌ No devices found")
            print("   → Open Spotify and play something first")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nCheck:")
        print("1. Are your credentials correct in spotify_config.py?")
        print("2. Did you authorize the app?")
        print("3. Do you have Spotify Premium?")

if __name__ == "__main__":
    test_spotify_connection()
