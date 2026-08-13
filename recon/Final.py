#!/usr/bin/env python3
"""
Final.py — full recon pipeline orchestrator.
 
Chains all tool classes together and produces three final output files:
 
    Live_Domains.txt  — httpx-verified live subdomains
    IPs.txt           — resolved IPs (dnsx + AlienVault)
    screenshots/      — gowitness PNG screenshots of live pages
 
Usage:
    python3 Final.py target.com
 
-h7n
"""
 
import sys
import os
import threading
from pathlib import Path
 
# --- import all tool classes ---
# note: all source files have been fixed to guard module-level
# execution with if __name__ == "__main__": so imports are safe
 
from curl import curl           # certspotter, VT, AlienVault, commoncrawl, CSP
from Scanner import Scanner     # chaos, alterx, subfinder, github, puredns
from amass import Amass         # active + passive amass
from Asn import asn             # ASN enum + reverse IP lookup
from UI import ReconUI
 
 
TOOLS = [
    "certspotter", "virustotal", "alienvault",
    "commoncrawl", "csp-header",
    "chaos", "alterx", "subfinder",
    "github-subdomains", "puredns", "amass",
    "bgpq4", "rapiddns", "interlace",
    "dnsx", "uro", "httpx", "gowitness",
]
 
 
def count_lines(filepath: str) -> int:
    p = Path(filepath)
    if not p.exists():
        return 0
    return sum(1 for _ in p.open(errors="ignore"))
 
 
def merge_all_subdomains(output: str, *files: str) -> int:
    """Merge multiple subdomain files, dedupe, write to output. Returns line count."""
    seen = set()
    lines = []
    for f in files:
        p = Path(f)
        if not p.exists():
            return 0
        for line in p.read_text(errors="ignore").splitlines():
            line = line.strip()
            # strip http:// https:// so we're deduping on bare hostnames
            line = line.replace("https://", "").replace("http://", "").strip("/")
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
    Path(output).write_text("\n".join(sorted(lines)))
    return len(lines)
 
 
def main(target: str):
    ui = ReconUI(target=target, tools=TOOLS)
    ui.banner()
 
    base = os.getcwd()
 
    # ---------------------------------------------------------------
    # PHASE 1 — curl-based passive enumeration
    # curl.py uses self.site (not self.target) and its folder() method
    # does makedirs + chdir internally — call folder() first, then
    # run tools, then manually chdir back.
    # ---------------------------------------------------------------
    ui.section("Phase 1 — Passive API Enumeration")
 
    c = curl(target)                        # curl class uses 'site' param
 
    with ui.step("curl — create CURL/ folder") as s:
        try:
            os.makedirs("CURL", exist_ok=True)
            os.chdir("CURL")
            print('[+] CURL folder ready')
            s.result(note="working inside CURL/")
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("certspotter") as s:
        try:
            c.crt()
            s.result(count=count_lines("crt.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("virustotal") as s:
        try:
            c.virus_total()
            s.result(count=count_lines("vt.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("alienvault (IPs)") as s:
        try:
            c.alien_vault()
            s.result(count=count_lines("Alien_v_IP.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("commoncrawl (wayback)") as s:
        try:
            c.wayback()
            s.result(count=count_lines("commoncrawl_subdomains.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("CSP header") as s:
        try:
            c.CSP_header()
            s.result(count=count_lines("csp.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("curl — liveness check + copy Curl_Url.txt to root") as s:
        try:
            # cleaner() dedupes + httpx liveness checks + copies Curl_Url.txt to ../
            c.cleaner()
            s.result(count=count_lines("Curl_Url.txt"))
        except Exception as e:
            s.fail(str(e))
 
    os.chdir(base)                          # back to root after CURL/ phase
 
    # ---------------------------------------------------------------
    # PHASE 2 — active subdomain enumeration (Scanner + Amass in parallel)
    # both write to SCANNER/ folder
    # ---------------------------------------------------------------
    ui.section("Phase 2 — Active Subdomain Enumeration")
 
    os.makedirs("SCANNER", exist_ok=True)
    sc = Scanner(target)
    am = Amass(target)
 
    def run_scanner():
        os.chdir(os.path.join(base, "SCANNER"))
        sc.chaos()
        sc.permutation()
        sc.subfinder()
        sc.github()
        sc.subdomain_brtFC()
 
    def run_amass():
        os.chdir(os.path.join(base, "SCANNER"))
        am.active()
        am.passive()
 
    with ui.step("chaos + alterx + subfinder + github + puredns + amass (parallel)") as s:
        try:
            t1 = threading.Thread(target=run_scanner)
            t2 = threading.Thread(target=run_amass)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
 
            # count total unique subdomains found across all scanner tools
            total = count_lines("SCANNER/chaos.txt") + \
                    count_lines("SCANNER/subfinder.txt") + \
                    count_lines("SCANNER/BrtFC.txt") + \
                    count_lines("SCANNER/Amass_A.txt") + \
                    count_lines("SCANNER/Amass_P.txt")
            s.result(count=total, note="see SCANNER/ for per-tool files")
        except Exception as e:
            s.fail(str(e))
 
    os.chdir(base)
 
    # ---------------------------------------------------------------
    # PHASE 3 — ASN enumeration + reverse IP lookup
    # Asn.py's asn_enum() now uses self.target (fixed from hardcoded paypal)
    # ---------------------------------------------------------------
    ui.section("Phase 3 — ASN & Reverse IP Lookup")
 
    os.makedirs("ASN", exist_ok=True)
    a = asn(target)
 
    with ui.step("ASN lookup + IP ranges (bgpq4)") as s:
        try:
            os.chdir(os.path.join(base, "ASN"))
            a.asn_enum()
            s.result(count=count_lines("ip_ranges.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base)
 
    with ui.step("reverse IP lookup (rapiddns + interlace)") as s:
        try:
            os.chdir(os.path.join(base, "ASN"))
            a.reverse_ip_lookup()
            s.result(count=count_lines("reverse_ip.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base)
 
    # ---------------------------------------------------------------
    # PHASE 4 — merge everything → Live_Domains.txt → IPs.txt → screenshots
    # ---------------------------------------------------------------
    ui.section("Phase 4 — Merge → Live Domains → IPs → Screenshots")
 
    # 4a — merge all raw subdomain files
    with ui.step("merge + dedupe all sources → All_Subdomains.txt") as s:
        try:
            raw = merge_all_subdomains(
                "All_Subdomains.txt",
                "CURL/crt.txt",
                "CURL/vt.txt",
                "CURL/commoncrawl_subdomains.txt",
                "CURL/csp.txt",
                "CURL/Curl_Url.txt",
                "ASN/reverse_ip.txt",
                "SCANNER/chaos.txt",
                "SCANNER/permutation.txt",
                "SCANNER/subfinder.txt",
                f"SCANNER/{target}.txt",          # github-subdomains output
                "SCANNER/BrtFC.txt",
                "SCANNER/Amass_A.txt",
                "SCANNER/Amass_P.txt",
            )
            s.result(count=raw)
        except Exception as e:
            s.fail(str(e))
 
    # 4b — httpx liveness → Live_Domains.txt
    with ui.step("httpx liveness check → Live_Domains.txt") as s:
        try:
            # remove any previous run's output first to avoid self-inclusion
            Path("Live_Domains.txt").unlink(missing_ok=True)
 
            cmd = (
                "cat All_Subdomains.txt "
                "| sed -E 's#^(https?://)##; s#^#https://#' "
                "| uro "
                "| httpx -mc 200,301,302,403,401 -silent > Live_Domains.txt"
            )
            os.system(cmd)
            s.result(count=count_lines("Live_Domains.txt"))
        except Exception as e:
            s.fail(str(e))
 
    # 4c — resolve live domains to IPs → IPs.txt
    with ui.step("IP resolution (dnsx) → IPs.txt") as s:
        try:
            Path("IPs.txt").unlink(missing_ok=True)
 
            # resolve from live domains
            cmd = (
                "cat Live_Domains.txt "
                "| sed -E 's#^https?://##; s#/.*##' "
                "| dnsx -a -resp-only -silent "
                "| sort -u > IPs.txt"
            )
            os.system(cmd)
 
            # also merge in AlienVault IPs
            os.system("cat CURL/Alien_v_IP.txt 2>/dev/null | anew IPs.txt")
 
            # also merge in ASN IP ranges (these are CIDRs, store separately)
            os.system("cat ASN/ip_ranges.txt 2>/dev/null | anew IP_Ranges.txt")
 
            s.result(count=count_lines("IPs.txt"))
        except Exception as e:
            s.fail(str(e))
 
    # 4d — screenshots of HTML pages → screenshots/
    with ui.step("filter screenshot targets") as s:
        try:
            Path("_screenshot_targets_.txt").unlink(missing_ok=True)
            cmd = (
                "cat Live_Domains.txt "
                "| grep -viE '\\.(js|css|json|woff|ttf|svg|png|jpg|gif)($|\\?)' "
                "> _screenshot_targets_.txt"
            )
            os.system(cmd)
            s.result(count=count_lines("_screenshot_targets_.txt"))
        except Exception as e:
            s.fail(str(e))
 
    with ui.step("screenshots (gowitness) → screenshots/") as s:
        try:
            os.makedirs("screenshots", exist_ok=True)
            cmd = (
                "gowitness scan file "
                "-f _screenshot_targets_.txt "
                "--threads 5 "
                "--chrome-path $(which brave-browser) "
                "--db-location screenshots/gowitness.db "
                "--screenshot-path screenshots/"
            )
            os.system(cmd)
            ss_count = len(list(Path("screenshots").glob("*.png")))
            s.result(count=ss_count)
        except Exception as e:
            s.fail(str(e))
 
    # ---------------------------------------------------------------
    # final summary
    # ---------------------------------------------------------------
    live = count_lines("Live_Domains.txt")
    ips = count_lines("IPs.txt")
    ss = len(list(Path("screenshots").glob("*.png"))) if Path("screenshots").exists() else 0
 
    ui.summary(live_count=live, ip_count=ips, screenshot_count=ss)
 
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 Final.py <target.com>")
        sys.exit(1)
    main(sys.argv[1])