#!/bin/bash
# uninstall.command - macOS Uninstaller Script
# Make double-clickable in Finder

# Move to the directory of the script
cd "$(dirname "$0")"

echo "==========================================="
echo "        EcoTracker macOS Uninstaller       "
echo "==========================================="
echo ""

# Unload and remove LaunchAgent
PLIST_FILE="$HOME/Library/LaunchAgents/com.brotherpeople.ecotracker.plist"
if [ -f "$PLIST_FILE" ]; then
    echo "Unloading and removing LaunchAgent..."
    launchctl unload "$PLIST_FILE" 2>/dev/null
    rm "$PLIST_FILE" 2>/dev/null
fi

# Remove Desktop Shortcut
DESKTOP_DIR="$HOME/Desktop"
if [ -f "$DESKTOP_DIR/EcoTracker.command" ]; then
    echo "Removing Desktop shortcut..."
    rm "$DESKTOP_DIR/EcoTracker.command" 2>/dev/null
fi

# Delete installation folder
INSTALL_DIR="$HOME/.local/share/ecotracker"
if [ -d "$INSTALL_DIR" ]; then
    echo "Deleting installation folder..."
    rm -rf "$INSTALL_DIR" 2>/dev/null
fi

# Kill any remaining running app instances
pkill -f "python3.*ecotracker" 2>/dev/null
pkill -f "python3.*main.py" 2>/dev/null

echo ""
echo "EcoTracker has been successfully uninstalled!"
echo "==========================================="
