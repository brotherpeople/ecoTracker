#!/bin/bash
# uninstall.sh - Linux Uninstaller Script

# Move to script directory
cd "$(dirname "$0")"

echo "==========================================="
echo "        EcoTracker Linux Uninstaller       "
echo "==========================================="
echo ""

# Remove applications menu launcher
if [ -f "$HOME/.local/share/applications/ecotracker.desktop" ]; then
    echo "Removing applications menu entry..."
    rm "$HOME/.local/share/applications/ecotracker.desktop" 2>/dev/null
fi

# Remove autostart entry
if [ -f "$HOME/.config/autostart/ecotracker.desktop" ]; then
    echo "Removing autostart configurations..."
    rm "$HOME/.config/autostart/ecotracker.desktop" 2>/dev/null
fi

# Remove executable wrapper
if [ -f "$HOME/.local/bin/ecotracker" ]; then
    echo "Removing local bin executable..."
    rm "$HOME/.local/bin/ecotracker" 2>/dev/null
fi

# Remove Desktop shortcut
if [ -f "$HOME/Desktop/ecotracker.desktop" ]; then
    echo "Removing Desktop shortcut..."
    rm "$HOME/Desktop/ecotracker.desktop" 2>/dev/null
fi

# Delete installation folder
INSTALL_DIR="$HOME/.local/share/ecotracker"
if [ -d "$INSTALL_DIR" ]; then
    echo "Deleting installation folder..."
    rm -rf "$INSTALL_DIR" 2>/dev/null
fi

# Kill any remaining running processes
pkill -f "python3.*ecotracker" 2>/dev/null
pkill -f "python3.*main.py" 2>/dev/null

echo ""
echo "EcoTracker has been successfully uninstalled!"
echo "==========================================="
