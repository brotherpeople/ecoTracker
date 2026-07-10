#!/bin/bash
# install.sh - Linux Installer Script

# Move to script directory
cd "$(dirname "$0")"

echo "==========================================="
echo "        EcoTracker Linux Installer         "
echo "==========================================="

INSTALL_DIR="$HOME/.local/share/ecotracker"
echo "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.config/autostart"

# Copy project files
cp -R main.py config.py tracker ui "$INSTALL_DIR/"

# Create executable wrapper in user local bin
cat << EOF > "$HOME/.local/bin/ecotracker"
#!/bin/bash
python3 "$INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/ecotracker"

# Create .desktop file for system applications menu
cat << EOF > "$HOME/.local/share/applications/ecotracker.desktop"
[Desktop Entry]
Type=Application
Name=EcoTracker
Comment=Real-time PC power and carbon footprint tracker
Exec=python3 $INSTALL_DIR/main.py
Icon=$INSTALL_DIR/ui/app.png
Terminal=false
Categories=Utility;System;
EOF
chmod +x "$HOME/.local/share/applications/ecotracker.desktop"

# Copy to autostart so it runs on login
cp "$HOME/.local/share/applications/ecotracker.desktop" "$HOME/.config/autostart/"

# Copy to Desktop if directory exists
if [ -d "$HOME/Desktop" ]; then
    echo "Creating Desktop shortcut..."
    cp "$HOME/.local/share/applications/ecotracker.desktop" "$HOME/Desktop/"
    # For GNOME to trust the desktop file
    gio set "$HOME/Desktop/ecotracker.desktop" metadata::trusted true 2>/dev/null || true
    chmod +x "$HOME/Desktop/ecotracker.desktop" 2>/dev/null || true
fi

echo ""
echo "Installation complete!"
echo "1. EcoTracker installed to ~/.local/bin/ecotracker."
echo "2. Desktop launcher created."
echo "3. Configured to start automatically on login."
echo "==========================================="
