#!/usr/bin/env bash
# =============================================================================
# setup-arch.sh — Recon Scanner full environment setup for Arch Linux
#
# Usage:
#   chmod +x setup-arch.sh
#   ./setup-arch.sh
#
# -h7n
# =============================================================================

set -e

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
    echo -e "${BOLD}  Scanner Setup — Arch Linux${RESET}"
    echo -e "  ${YELLOW}-h7n${RESET}"
    echo ""
}

log()     { echo -e "${GREEN}[+]${RESET} $1"; }
info()    { echo -e "${CYAN}[*]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[!]${RESET} $1"; }
section() { echo ""; echo -e "${BOLD}${CYAN}── $1 ──${RESET}"; echo ""; }

# =============================================================================
# 0. Preflight
# =============================================================================
banner
section "Preflight Checks"

if [ "$EUID" -eq 0 ]; then
    error "Do not run as root on Arch — pacman and yay require a normal user."
    exit 1
fi

if ! command -v pacman &>/dev/null; then
    error "pacman not found — this script is for Arch Linux only."
    exit 1
fi

if ! curl -s --max-time 5 https://github.com > /dev/null; then
    error "No internet connection detected."
    exit 1
fi

log "System checks passed"

# =============================================================================
# AUR helper — yay
# =============================================================================
section "AUR Helper (yay)"

if command -v yay &>/dev/null; then
    log "yay already installed — skipping"
else
    info "Installing yay..."
    sudo pacman -S --needed --noconfirm git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay-install
    cd /tmp/yay-install && makepkg -si --noconfirm
    cd "$SCRIPT_DIR"
    rm -rf /tmp/yay-install
    log "yay installed"
fi

# =============================================================================
# 1. System dependencies
# =============================================================================
section "System Dependencies"

info "Updating system..."
sudo pacman -Syu --noconfirm

info "Installing base packages..."
sudo pacman -S --needed --noconfirm \
    curl wget git jq \
    python python-pip \
    nmap go \
    whois bind-tools \
    base-devel

log "System packages installed"

# go bin on PATH
if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
    echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/go/bin:$PATH"
    log "Added ~/go/bin to PATH"
fi

info "Installing wafw00f and whatweb from AUR..."
yay -S --needed --noconfirm wafw00f whatweb 2>/dev/null || \
    warn "wafw00f/whatweb AUR install failed — install manually if needed"

# =============================================================================
# 2. Python dependencies
# =============================================================================
section "Python Dependencies"

pip install rich mmh3 requests --break-system-packages -q 2>/dev/null || \
    pip install rich mmh3 requests -q
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
        go install "$pkg" 2>/dev/null && log "$name installed" || \
            warn "$name install failed — check manually"
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
# 4. Amass
# =============================================================================
section "Amass"

if command -v amass &>/dev/null; then
    log "amass already installed — skipping"
else
    info "Installing amass via AUR..."
    yay -S --needed --noconfirm amass 2>/dev/null && log "amass installed via AUR" || {
        warn "AUR failed — trying go install..."
        go install github.com/owasp-amass/amass/v4/...@master 2>/dev/null && \
            log "amass installed via go" || \
            warn "amass install failed — install manually"
    }
fi

# =============================================================================
# 5. dnsvalidator
# =============================================================================
section "dnsvalidator"

if command -v dnsvalidator &>/dev/null; then
    log "dnsvalidator already installed — skipping"
else
    info "Installing dnsvalidator..."
    pip install dnsvalidator --break-system-packages -q 2>/dev/null || \
        pip install dnsvalidator -q
    log "dnsvalidator installed"
fi

# =============================================================================
# 6. SecLists
# =============================================================================
section "SecLists"

if [ -d "/usr/share/seclists" ]; then
    log "SecLists already at /usr/share/seclists — pulling updates..."
    sudo git -C /usr/share/seclists pull -q && log "SecLists updated" || \
        warn "SecLists update failed"
else
    info "Installing SecLists via AUR..."
    yay -S --needed --noconfirm seclists 2>/dev/null && log "SecLists installed via AUR" || {
        warn "AUR failed — cloning manually..."
        sudo git clone --depth 1 https://github.com/danielmiessler/SecLists.git \
            /usr/share/seclists && log "SecLists cloned" || \
            warn "SecLists clone failed — install manually"
    }
fi

# =============================================================================
# 7. Brave browser
# =============================================================================
section "Brave Browser (for gowitness)"

if command -v brave-browser &>/dev/null || command -v brave &>/dev/null; then
    log "Brave already installed — skipping"
else
    warn "Brave not found — gowitness needs a Chrome-based browser."
    read -rp "Install Brave via AUR? [y/N] " install_brave
    if [[ "$install_brave" =~ ^[Yy]$ ]]; then
        yay -S --needed --noconfirm brave-bin && log "Brave installed" || \
            warn "Brave install failed — try: yay -S brave-bin"
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

read -rp "  VirusTotal API key    (VIRUS_TOTAL)   : " VT_KEY
read -rp "  GitHub Token          (GITHUB_TOKEN)  : " GH_TOKEN
read -rp "  Chaos/PDCP API key    (PDCP_API_KEY)  : " CHAOS_KEY

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
# Installed by setup-arch.sh from $SCRIPT_DIR
# -h7n

source "\$HOME/.bashrc" 2>/dev/null || true
python3 "$SCRIPT_DIR/Final.py" "\$@"
EOF

sudo chmod +x "$WRAPPER"
log "Global 'recon' command installed"

# =============================================================================
# 10. Verification
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
