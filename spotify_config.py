"""
Spotify API Configuration

To set up:
1. Go to https://developer.spotify.com/dashboard
2. Create an app (name it "GestureHub" or whatever you like)
3. In app settings, add redirect URI: http://localhost:8888/callback
4. Copy your Client ID and Client Secret below
5. Make sure you have Spotify Premium (required for playback control)
"""

# Replace these with your actual Spotify app credentials
SPOTIFY_CLIENT_ID = "ffbdb651c4ea4a45a997d16e2c3cff0c"
SPOTIFY_CLIENT_SECRET = "b965ac83b43747e29a9b7a5321044ad3"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Spotify API permissions needed for playback control
SPOTIFY_SCOPE = (
    "user-read-private "
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "streaming"
)
