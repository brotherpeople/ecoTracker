#!/bin/bash
# install.command - macOS Installer Script
# Make double-clickable in Finder

# Move to the directory of the script
cd "$(dirname "$0")"

echo "==========================================="
echo "        EcoTracker macOS Installer         "
echo "==========================================="

INSTALL_DIR="$HOME/.local/share/ecotracker"
echo "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy source files
cp -R main.py config.py tracker ui "$INSTALL_DIR/"

# Create startup script wrapper
cat << 'EOF' > "$INSTALL_DIR/EcoTracker.sh"
#!/bin/bash
cd "$(dirname "$0")"
# Execute using python3
python3 main.py >/dev/null 2>&1 &
EOF
chmod +x "$INSTALL_DIR/EcoTracker.sh"

# Create Desktop Shortcut
DESKTOP_DIR="$HOME/Desktop"
cat << EOF > "$DESKTOP_DIR/EcoTracker.command"
#!/bin/bash
"$INSTALL_DIR/EcoTracker.sh"
EOF
chmod +x "$DESKTOP_DIR/EcoTracker.command"

# Create LaunchAgent for boot startup
PLIST_FILE="$HOME/Library/LaunchAgents/com.brotherpeople.ecotracker.plist"
echo "Setting up LaunchAgent at $PLIST_FILE..."
cat << EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.brotherpeople.ecotracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$INSTALL_DIR/EcoTracker.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# Load the LaunchAgent
launchctl load "$PLIST_FILE" 2>/dev/null

echo ""
echo "Installation complete!"
echo "1. EcoTracker shortcut created on your Desktop."
echo "2. Configured to start automatically on login."
echo "==========================================="
