#!/usr/bin/env bash
# Installs a global `recon` command that runs main.py from anywhere.
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
#
# After install, run from any directory:
#   recon target.com
#
# Output files are created in whatever directory you run `recon` from
# (not the install location) - same as running `python3 main.py` directly.
#
# -h7n

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_PATH="/usr/local/bin/analysis"

echo "[*] Analysis tool located at: $SCRIPT_DIR"

if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "[!] main.py not found in $SCRIPT_DIR - run this script from inside the project folder."
    exit 1
fi

echo "[*] Creating wrapper at $WRAPPER_PATH (requires sudo)"

sudo tee "$WRAPPER_PATH" > /dev/null << EOF
#!/usr/bin/env bash
python3 "$SCRIPT_DIR/main.py" "\$@"
EOF

sudo chmod +x "$WRAPPER_PATH"

echo "[+] Installed. Run 'recon target.com' from anywhere."
echo "[+] Uninstall anytime with: sudo rm $WRAPPER_PATH"
