# Recon Scanner

An automated, multi-threaded reconnaissance pipeline written in Python and Bash designed for bug bounty hunters, penetration testers, and security researchers. **Recon Scanner** orchestrates passive API discovery, active subdomain enumeration, ASN expansion, reverse IP lookup, DNS resolution, HTTP liveness filtering, and screenshot capturing into a single workflow.

---

## Key Features

- **4-Phase Orchestrated Pipeline**:
  - **Phase 1 (Passive API Enumeration)**: Queries Certspotter (CT logs), VirusTotal API, AlienVault OTX, CommonCrawl archives, and Content Security Policy (CSP) headers.
  - **Phase 2 (Active Subdomain Enumeration)**: Concurrent discovery using `subfinder`, `chaos`, `alterx`, GitHub search, `amass` (active & passive), and `puredns` bruteforcing with dynamic resolver validation.
  - **Phase 3 (ASN & Reverse IP Lookup)**: BGP ASN range enumeration via RIPE API & `bgpq4`, followed by multithreaded reverse IP lookups using `interlace` and `rapiddns`.
  - **Phase 4 (Consolidation & Verification)**: Deduplication with `anew` & `uro`, HTTP probe filtering (`httpx`), DNS resolution (`dnsx`), and web UI snapshot capturing (`gowitness` / Brave).
- **Parallel Execution**: Leverages Python threading for concurrent active scans to maximize throughput.
- **Rich Terminal UI**: Styled terminal output, per-step execution timers, and clean summary tables powered by `rich`.
- **Cross-Platform Setup**: Automated environment setup scripts for Debian/Ubuntu (`setup.sh`) and Arch Linux (`setup-arch.sh`).

---

## System Architecture & Pipeline Workflow

```
                        +----------------------------+
                        |      Target Domain         |
                        +----------------------------+
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
+------------------+        +-------------------+        +-------------------+
|  Phase 1: CURL   |        | Phase 2: SCANNER  |        |   Phase 3: ASN    |
| Passive APIs & CT|        | Active/Subdomains |        | BGP & Reverse IP  |
+------------------+        +-------------------+        +-------------------+
  • CertSpotter               • Subfinder                  • RIPE ASN Lookup
  • VirusTotal                • Chaos + AlterX             • bgpq4 IPv4 Ranges
  • AlienVault OTX            • GitHub Subdomains          • RapidDNS Reverse
  • CommonCrawl               • PureDNS Bruteforce           (via Interlace)
  • CSP Headers               • Amass (Active/Passive)     
       |                              |                              |
       +------------------------------+------------------------------+
                                      |
                                      v
                        +----------------------------+
                        | All_Subdomains.txt (Merge) |
                        +----------------------------+
                                      |
                                      v
                        +----------------------------+
                        |      Phase 4: Output       |
                        +----------------------------+
                          • Live_Domains.txt (httpx)
                          • IPs.txt (dnsx + OTX)
                          • screenshots/ (gowitness)
```

---

## Prerequisites & Required Tools

Ensure you have Python 3 and Go installed. The suite relies on the following tools:

| Category | Tools |
| :--- | :--- |
| **Go Binaries** | `anew`, `httpx`, `dnsx`, `chaos`, `alterx`, `subfinder`, `puredns`, `github-subdomains`, `unfurl`, `uro`, `interlace`, `gowitness`, `bgpq4`, `gau`, `amass` |
| **Python Packages** | `rich`, `mmh3`, `requests`, `dnsvalidator` |
| **System Tools** | `curl`, `git`, `jq`, `bind-tools` (`dnsutils`), `whois`, `nmap` |
| **Wordlists** | SecLists (`/usr/share/seclists`) |
| **Browser** | Brave / Chrome-based browser (for `gowitness` web rendering) |

---

## Installation & Setup

Automatic setup scripts are provided for Debian/Ubuntu and Arch Linux environments.

### 1. Debian / Ubuntu / Mint / Kali
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Arch Linux
```bash
chmod +x setup-arch.sh
./setup-arch.sh
```

The setup script will:
1. Install missing system packages and Go environment tools.
2. Clone SecLists to `/usr/share/seclists`.
3. Prompt for API keys and save them to `~/.bashrc`.
4. Create a global `recon` command symlink at `/usr/local/bin/recon`.

---

## Configuration & API Keys

For maximum enumeration coverage, configure the following environment variables in your shell (`~/.bashrc` or `~/.zshrc`):

```bash
export VIRUS_TOTAL="your_virustotal_api_key"
export GITHUB_TOKEN="your_github_personal_access_token"
export PDCP_API_KEY="your_projectdiscovery_chaos_api_key"
```

---

## Usage

### Using Global Wrapper Command
After running `setup.sh` or `setup-arch.sh`:

```bash
recon target.com
```

### Direct Script Execution
```bash
python3 Final.py target.com
```

---

## Output Structure

Upon scan completion, the following files and directories are generated in your working directory:

| Path / File | Description |
| :--- | :--- |
| `Live_Domains.txt` | HTTP/HTTPS responsive domains verified by `httpx` (StatusCodes: 200, 301, 302, 401, 403). |
| `IPs.txt` | Deduplicated IPv4 addresses resolved via `dnsx` and AlienVault OTX. |
| `IP_Ranges.txt` | Discovered BGP IP prefix ranges (CIDR notation). |
| `screenshots/` | PNG visual snapshots of web interfaces taken by `gowitness`. |
| `All_Subdomains.txt` | Merged raw list of all discovered subdomains prior to liveness filtering. |
| `CURL/` | Raw output files from passive API modules (`crt.txt`, `vt.txt`, `csp.txt`, etc.). |
| `SCANNER/` | Output files from active discovery tools (`subfinder.txt`, `BrtFC.txt`, `Amass_A.txt`, etc.). |
| `ASN/` | Output from ASN enumeration and reverse IP lookup (`ip_ranges.txt`, `reverse_ip.txt`). |

---

## Author

Created & maintained by **-h7n**.
