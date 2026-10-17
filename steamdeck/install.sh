#!/usr/bin/env bash
# Install Linux-only Nucleus Deck launcher; never writes to SteamOS system partitions.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null || { echo 'python3 is required' >&2; exit 1; }
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
bin_home="$HOME/.local/bin"
app_home="$data_home/nucleus-deck"
desktop_home="$data_home/applications"
mkdir -p "$bin_home" "$app_home" "$desktop_home"
install -m 755 "$script_dir/nucleus_deck.py" "$app_home/nucleus_deck.py"
cat > "$bin_home/nucleus-deck" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
exec python3 "$data_home/nucleus-deck/nucleus_deck.py" "$@"
EOF
chmod 755 "$bin_home/nucleus-deck"
cat > "$desktop_home/nucleus-deck.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Nucleus Deck (SteamOS)
Comment=Start the SteamOS native split-screen frontend
Exec=$bin_home/nucleus-deck --gui
Icon=applications-games
Terminal=false
Categories=Game;
StartupNotify=true
EOF
chmod 644 "$desktop_home/nucleus-deck.desktop"
echo "Installed Nucleus Deck to $bin_home/nucleus-deck"
echo "Open 'Nucleus Deck (SteamOS)' from the Desktop Mode applications menu."
echo "Or run: $bin_home/nucleus-deck --doctor"
echo "Install the Linux runtime from the menu (or use --install-backend)."
