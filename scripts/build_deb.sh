#!/bin/bash
# Build script for creating Linux .deb package
# Run: chmod +x build_deb.sh && ./build_deb.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
BUILD_DIR="$PROJECT_DIR/deb_build"
APP_NAME="gesturehub"
VERSION="1.0.1"
MAINTAINER="GestureHUB Team"
MAINTAINER_EMAIL="team@gesturehub.local"

echo "Building GestureHUB Linux .deb package..."
echo "============================================================"

# Clean previous builds
rm -rf "$BUILD_DIR"

# Create directory structure for .deb
mkdir -p "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/bin"
mkdir -p "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME"
mkdir -p "$BUILD_DIR/$APP_NAME-$VERSION/usr/share/applications"
mkdir -p "$BUILD_DIR/$APP_NAME-$VERSION/usr/share/pixmaps"
mkdir -p "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN"

# Copy application files
echo "Copying application files..."
cp -r "$PROJECT_DIR"/app "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/config "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/command_layer "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/controllers "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/core "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/games "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/gesture_engine "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/networking "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp -r "$PROJECT_DIR"/assets "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"
cp "$PROJECT_DIR"/requirements.txt "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/lib/$APP_NAME/"

# Create launcher script
cat > "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/bin/$APP_NAME" << 'EOF'
#!/bin/bash
cd /usr/local/lib/gesturehub
if [ -x "/usr/local/lib/gesturehub/.venv/bin/python" ]; then
    /usr/local/lib/gesturehub/.venv/bin/python app/gui_launcher.py "$@"
else
    python3 app/gui_launcher.py "$@"
fi
EOF

chmod +x "$BUILD_DIR/$APP_NAME-$VERSION/usr/local/bin/$APP_NAME"

# Create .desktop file
cat > "$BUILD_DIR/$APP_NAME-$VERSION/usr/share/applications/gesturehub.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=GestureHUB
Comment=Gesture Recognition & Game Suite
Exec=gesturehub
Icon=gesturehub
Categories=Games;Entertainment;
Terminal=false
EOF

# Copy icon if exists
if [ -f "$PROJECT_DIR/assets/icon.png" ]; then
    cp "$PROJECT_DIR/assets/icon.png" "$BUILD_DIR/$APP_NAME-$VERSION/usr/share/pixmaps/gesturehub.png"
fi

# Create DEBIAN control file
cat > "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN/control" << EOF
Package: $APP_NAME
Version: $VERSION
Architecture: all
Maintainer: $MAINTAINER <$MAINTAINER_EMAIL>
Homepage: https://github.com/yourusername/gesturehub
Description: Gesture Recognition & Game Suite
 A gesture-controlled application featuring:
 - Hand gesture recognition using MediaPipe
 - Multiple games (Dino, Catch, Fruit)
 - Music player with Spotify integration
 - Drawing board with gesture control
 - System controls via gesture
Depends: python3 (>= 3.8), python3-venv, python3-tk
EOF

# Create postinst script
cat > "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "GestureHUB installed successfully."
echo "If dependencies are missing, run:"
echo "  python3 -m venv /usr/local/lib/gesturehub/.venv"
echo "  /usr/local/lib/gesturehub/.venv/bin/pip install -r /usr/local/lib/gesturehub/requirements.txt"
echo "Then launch with: gesturehub"

exit 0
EOF

chmod 755 "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN/postinst"

# Create prerm script
cat > "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

echo "Cleaning up GestureHUB..."

# Kill any running processes
pkill -f app/gui_launcher.py || true
pkill -f app/main.py || true
pkill -f app/run_server.py || true

exit 0
EOF

chmod 755 "$BUILD_DIR/$APP_NAME-$VERSION/DEBIAN/prerm"

# Build the .deb package
echo "Building .deb package..."
cd "$BUILD_DIR"
dpkg-deb --build "$APP_NAME-$VERSION" "$APP_NAME-$VERSION.deb"

# Copy to main directory
cp "$APP_NAME-$VERSION.deb" "$PROJECT_DIR/$APP_NAME-$VERSION.deb"

echo "============================================================"
echo "✓ Linux .deb package built successfully!"
echo "Package located at: $PROJECT_DIR/$APP_NAME-$VERSION.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i $APP_NAME-$VERSION.deb"
echo ""
echo "To run:"
echo "  gesturehub"
echo "============================================================"
