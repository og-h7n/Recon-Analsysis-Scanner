<div align="center">

# 🕸️ RECON + ANALYSIS

### *map the attack surface. find the bugs. automate the boring parts.*

`enumerate` → `fingerprint` → `analyze` → `report`

</div>

---

## what even is this 👀

a two-phase automated security research toolkit split into what you do **before** you start poking, and what you do **after** you've got a target list:

```
┌─────────────────────┐        ┌──────────────────────┐
│      /recon          │  ──▶   │      /Analysis        │
│  find everything     │        │  analyze everything   │
│  that exists         │        │  worth attacking      │
└─────────────────────┘        └──────────────────────┘
```

- **[`/recon`](./recon)** — full subdomain + infrastructure enumeration. passive APIs, active scanning, ASN/IP mapping, reverse IP lookup. outputs `Live_Domains.txt`, `IPs.txt`, and screenshots.
- **[`/Analysis`](./Analysis)** — automated analysis on your live targets. URL collection, fingerprinting, JS secret scanning, parameter discovery, directory bruteforce, liveness-checked endpoint lists.

run recon first. feed its output into Analysis. get results.

---

## 🗺️ the full pipeline

```
target.com
     │
     ▼
╔══════════════════════════════════════╗
║           /recon                      ║
║                                       ║
║  Phase 1 — Passive API Enumeration    ║
║  certspotter · VT · AlienVault        ║
║  commoncrawl · CSP headers            ║
║                    ▼                  ║
║  Phase 2 — Active Enumeration         ║
║  chaos · alterx · subfinder           ║
║  github-subdomains · puredns · amass  ║
║                    ▼                  ║
║  Phase 3 — ASN & Reverse IP           ║
║  RIPE → ASNs → bgpq4 → CIDRs         ║
║  rapiddns + interlace → domains       ║
║                    ▼                  ║
║  Phase 4 — Merge + Outputs            ║
║  Live_Domains.txt                     ║
║  IPs.txt                              ║
║  screenshots/                         ║
╚══════════════════════════════════════╝
     │
     ▼
╔══════════════════════════════════════╗
║           /Analysis                   ║
║                                       ║
║  URL Collection                       ║
║  gau · katana · gospider              ║
║  uro + httpx → LiveUrls.txt           ║
║                    ▼                  ║
║  Fingerprinting                       ║
║  whatweb · nmap · wafw00f             ║
║  wappalyzer · httpx · curl            ║
║                    ▼                  ║
║  JS Secret Scanning                   ║
║  mantra · jsecret                     ║
║                    ▼                  ║
║  Parameter Discovery                  ║
║  arjun · grep                         ║
║                    ▼                  ║
║  Directory Bruteforce                 ║
║  feroxbuster · dirsearch              ║
╚══════════════════════════════════════╝
     │
     ▼
  results 🎯
```

---

## 🛠️ tools used

### recon phase

| category | tools |
|---|---|
| passive enum | `certspotter` `virustotal` `alienvault` `commoncrawl` `csp-header` |
| active enum | `chaos` `alterx` `subfinder` `github-subdomains` `puredns` `amass` |
| ASN / IP | `bgpq4` `rapiddns` `interlace` |
| post-processing | `uro` `httpx` `dnsx` `gowitness` |

### analysis phase

| category | tools |
|---|---|
| url collection | `gau` `katana` `gospider` `uro` `httpx` |
| fingerprinting | `whatweb` `nmap` `wafw00f` `wappalyzer` `curl` |
| js secrets | `mantra` `jsecret` |
| parameters | `arjun` |
| directories | `feroxbuster` `dirsearch` |

---

## ⚡ quickstart

### Debian / Ubuntu / Linux Mint

```bash
git clone https://github.com/og-h7n/Recon.git
cd Recon

# setup recon phase
cd recon
chmod +x setup.sh && ./setup.sh
cd ..

# setup analysis phase
cd Analysis
chmod +x install.sh && ./install.sh
cd ..
```

### Arch Linux

```bash
git clone https://github.com/og-h7n/Recon.git
cd Recon

# setup recon phase
cd recon
chmod +x setup-arch.sh && ./setup-arch.sh
cd ..

# setup analysis phase
cd Analysis
chmod +x install.sh && ./install.sh
cd ..
```

---

## 🚀 usage

### phase 1 — recon

```bash
cd recon
recon target.com
```

outputs:
- `Live_Domains.txt` — httpx-verified live subdomains
- `IPs.txt` — resolved IPs
- `screenshots/` — gowitness screenshots

### phase 2 — analysis

```bash
cd Analysis
recon target.com   # or: python3 main.py target.com
```

outputs:
- `Urls_collected/_LiveUrls_.txt` — live endpoints
- `js_files.txt` — JS files for secret scanning
- `param.txt` — parameter-containing endpoints
- `ferox_results.txt` + `Dirseach_results.txt` — directory bruteforce
- `Fingerprint/` — fingerprinting tool outputs

---

## 🔑 API keys needed

| key | where to get it | env var |
|---|---|---|
| VirusTotal | https://www.virustotal.com | `VIRUS_TOTAL` |
| GitHub token | https://github.com/settings/tokens | `GITHUB_TOKEN` |
| Chaos / PDCP | https://cloud.projectdiscovery.io | `PDCP_API_KEY` |
| Shodan | https://account.shodan.io | `SHODAN_API_KEY` |
| FOFA | https://fofa.info | `FOFA_EMAIL` + `FOFA_KEY` |
| Hunter.how | https://hunter.how | `HUNTER_KEY` |

both setup scripts prompt for these and save them to `~/.bashrc` automatically.

---

## 📁 repo structure

```
Recon/
├── recon/                  # phase 1 — enumeration
│   ├── Final.py            # orchestrator
│   ├── UI.py               # terminal dashboard
│   ├── curl.py             # passive API enumeration
│   ├── Scanner.py          # active subdomain discovery
│   ├── amass.py            # amass active + passive
│   ├── Asn.py              # ASN + reverse IP
│   ├── setup.sh            # setup for Debian/Ubuntu/Mint
│   ├── setup-arch.sh       # setup for Arch Linux
│   ├── requirements.txt    # python dependencies
│   └── readme.md           # phase 1 detail
│
└── Analysis/               # phase 2 — analysis
    ├── main.py             # orchestrator
    ├── ui.py               # terminal dashboard
    ├── get_urls.py         # gau + katana + gospider
    ├── Fingerprinting.py   # tech stack + WAF + headers
    ├── jsScan.py           # mantra + jsecret
    ├── param.py            # arjun + grep
    ├── DirBrtfrcing.py     # feroxbuster + dirsearch
    ├── install.sh          # global install script
    ├── requirements.txt    # python dependencies
    └── readme.md           # phase 2 detail
```

---

## ⚠️ authorized use only

everything in this repo is for targets you own or have explicit written authorization to test — bug bounty in-scope assets, your own infrastructure, CTFs. always check scope before scanning anything. running these tools against unauthorized systems may be illegal in your jurisdiction.

---

## 💬 suggestions / feedback

always welcome — open an issue or hit me up directly.

discord → https://discord.gg/d9wFhhnwFe

miro board → https://miro.com/app/board/uXjVHAlbwYw=/?share_link_id=227022886951

<div align="center">

---

made with way too much caffeine by

# **H7N**

</div>
