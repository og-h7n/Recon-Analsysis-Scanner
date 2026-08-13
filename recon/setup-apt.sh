#!/usr/bin/env bash
# =============================================================================
# setup.sh — Recon Scanner full environment setup
#
# Installs all required tools, prompts for API keys, sets up environment
# variables, and creates a global `recon` command.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# -h7n
# =============================================================================

set -e

# colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "  ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗"
    echo "  ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║"
    echo "  ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║"
    echo "  ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║"
    echo "  ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║"
    echo "  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝"
    echo -e "${RESET}"
    echo -e "${BOLD}  Scanner Setup Script${RESET}"
    echo -e "  ${YELLOW}-h7n${RESET}"
    echo ""
}

log()     { echo -e "${GREEN}[+]${RESET} $1"; }
info()    { echo -e "${CYAN}[*]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[!]${RESET} $1"; }
section() { echo ""; echo -e "${BOLD}${CYAN}── $1 ──${RESET}"; echo ""; }

# =============================================================================
# 0. Preflight checks
# =============================================================================
banner

section "Preflight Checks"

# must not be run as root
if [ "$EUID" -eq 0 ]; then
    warn "Running as root is not recommended — some go tools may behave oddly."
    read -rp "Continue anyway? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

# check OS
if ! command -v apt &>/dev/null; then
    error "This script is designed for Debian/Ubuntu/Mint (apt-based systems)."
    error "Adapt the apt install lines for your distro if needed."
    exit 1
fi

# check internet
if ! curl -s --max-time 5 https://github.com > /dev/null; then
    error "No internet connection detected — cannot install tools."
    exit 1
fi

log "System checks passed"

# =============================================================================
# 1. System dependencies
# =============================================================================
section "System Dependencies"

info "Updating apt..."
sudo apt update -qq

info "Installing base packages..."
sudo apt install -y \
    curl wget git jq build-essential \
    python3 python3-pip \
    nmap wafw00f whatweb \
    dnsutils whois \
    golang-go 2>/dev/null || true

log "System packages installed"

# ensure go bin is on PATH
if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
    echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/go/bin:$PATH"
    log "Added ~/go/bin to PATH"
fi

# =============================================================================
# 2. Python dependencies
# =============================================================================
section "Python Dependencies"

pip install rich mmh3 requests --break-system-packages -q
log "Python packages installed (rich, mmh3, requests)"

# =============================================================================
# 3. Go-based recon tools
# =============================================================================
section "Go Tools"

install_go_tool() {
    local name=$1
    local pkg=$2
    if command -v "$name" &>/dev/null; then
        log "$name already installed — skipping"
    else
        info "Installing $name..."
        go install "$pkg" 2>/dev/null && log "$name installed" || warn "$name install failed — check manually"
    fi
}

install_go_tool "anew"               "github.com/tomnomnom/anew@latest"
install_go_tool "httpx"              "github.com/projectdiscovery/httpx/cmd/httpx@latest"
install_go_tool "dnsx"               "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
install_go_tool "chaos"              "github.com/projectdiscovery/chaos-client/cmd/chaos@latest"
install_go_tool "alterx"             "github.com/projectdiscovery/alterx/cmd/alterx@latest"
install_go_tool "subfinder"          "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
install_go_tool "puredns"            "github.com/d3mondev/puredns/v2@latest"
install_go_tool "github-subdomains"  "github.com/gwen001/github-subdomains@latest"
install_go_tool "unfurl"             "github.com/tomnomnom/unfurl@latest"
install_go_tool "uro"                "github.com/s0md3v/uro@latest"
install_go_tool "interlace"          "github.com/codingo/interlace@latest"
install_go_tool "gowitness"          "github.com/sensepost/gowitness@latest"
install_go_tool "bgpq4"              "github.com/bgp/bgpq4@latest"
install_go_tool "gau"                "github.com/lc/gau/v2/cmd/gau@latest"

# =============================================================================
# 4. Amass (separate install — large binary)
# =============================================================================
section "Amass"

if command -v amass &>/dev/null; then
    log "amass already installed — skipping"
else
    info "Installing amass..."
    go install github.com/owasp-amass/amass/v4/...@master 2>/dev/null && \
        log "amass installed" || \
        warn "amass install failed — install manually: https://github.com/owasp-amass/amass"
fi

# =============================================================================
# 5. dnsvalidator
# =============================================================================
section "dnsvalidator"

if command -v dnsvalidator &>/dev/null; then
    log "dnsvalidator already installed — skipping"
else
    info "Installing dnsvalidator..."
    pip install dnsvalidator --break-system-packages -q && \
        log "dnsvalidator installed" || \
        warn "dnsvalidator install failed"
fi

# =============================================================================
# 6. SecLists
# =============================================================================
section "SecLists"

if [ -d "/usr/share/seclists" ]; then
    log "SecLists already installed at /usr/share/seclists"
    info "Pulling latest updates..."
    sudo git -C /usr/share/seclists pull -q && log "SecLists updated" || warn "SecLists update failed"
else
    info "Cloning SecLists to /usr/share/seclists (this may take a few minutes)..."
    sudo git clone --depth 1 https://github.com/danielmiessler/SecLists.git /usr/share/seclists && \
        log "SecLists installed" || \
        warn "SecLists clone failed — install manually"
fi

# =============================================================================
# 7. Brave browser (for gowitness screenshots)
# =============================================================================
section "Brave Browser (for gowitness)"

if command -v brave-browser &>/dev/null; then
    log "Brave already installed — skipping"
else
    warn "Brave not found — gowitness needs a Chrome-based browser for screenshots."
    read -rp "Install Brave browser now? [y/N] " install_brave
    if [[ "$install_brave" =~ ^[Yy]$ ]]; then
        info "Installing Brave..."
        sudo apt install -y apt-transport-https curl
        sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
            https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64] \
https://brave-browser-apt-release.s3.brave.com/ stable main" | \
            sudo tee /etc/apt/sources.list.d/brave-browser-release.list
        sudo apt update -qq && sudo apt install -y brave-browser
        log "Brave installed"
    else
        warn "Skipping Brave — screenshots will fail until a Chrome-based browser is installed."
    fi
fi

# =============================================================================
# 8. API Keys
# =============================================================================
section "API Keys"

echo -e "The following API keys are needed for full coverage."
echo -e "Press ${YELLOW}Enter${RESET} to skip any you don't have yet.\n"

read -rp "  VirusTotal API key   (VIRUS_TOTAL)  : " VT_KEY
read -rp "  GitHub Token         (GITHUB_TOKEN) : " GH_TOKEN
read -rp "  Chaos/PDCP API key   (PDCP_API_KEY) : " CHAOS_KEY



# write to ~/.bashrc
{
    echo ""
    echo "# ── Recon Scanner API Keys ──"
    [ -n "$VT_KEY"     ] && echo "export VIRUS_TOTAL=\"$VT_KEY\""
    [ -n "$GH_TOKEN"   ] && echo "export GITHUB_TOKEN=\"$GH_TOKEN\""
    [ -n "$CHAOS_KEY"  ] && echo "export PDCP_API_KEY=\"$CHAOS_KEY\""

} >> ~/.bashrc

source ~/.bashrc
log "API keys saved to ~/.bashrc"

# =============================================================================
# 9. Global `recon` command
# =============================================================================
section "Global Command"

WRAPPER="/usr/local/bin/recon"
info "Creating global 'recon' command at $WRAPPER..."

sudo tee "$WRAPPER" > /dev/null << EOF
#!/usr/bin/env bash
# Recon Scanner — global wrapper
# Installed by setup.sh from $SCRIPT_DIR
# -h7n

source "\$HOME/.bashrc" 2>/dev/null || true
python3 "$SCRIPT_DIR/Final.py" "\$@"
EOF

sudo chmod +x "$WRAPPER"
log "Global 'recon' command installed"

# =============================================================================
# 10. Verify everything installed
# =============================================================================
section "Verification"

TOOLS=(
    curl anew httpx dnsx chaos alterx subfinder
    puredns github-subdomains unfurl uro interlace
    gowitness bgpq4 gau amass jq python3
)

MISSING=()
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &>/dev/null; then
        log "$tool ✓"
    else
        warn "$tool ✗ — not found"
        MISSING+=("$tool")
    fi
done

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Setup complete!${RESET}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════${RESET}"
echo ""

if [ ${#MISSING[@]} -gt 0 ]; then
    warn "The following tools didn't install correctly:"
    for t in "${MISSING[@]}"; do
        echo "    - $t"
    done
    echo ""
fi

echo -e "  Run from anywhere:"
echo -e "  ${BOLD}${GREEN}recon target.com${RESET}"
echo ""
echo -e "  Reload your shell first if 'recon' isn't found:"
echo -e "  ${BOLD}source ~/.bashrc${RESET}"
echo ""
echo -e "  ${YELLOW}-h7n${RESET}"
echo ""
