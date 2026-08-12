#!/usr/bin/env python3
"""
Final.py — orchestrates the full recon pipeline:

    curl.py   → certspotter, VT, AlienVault, wayback, CSP
    Scanner.py → chaos, alterx, subfinder, github, puredns
    amass.py  → active + passive amass
    Asn.py    → ASN → IP ranges → reverse IP

Final outputs (all in root working directory):
    Live_Domains.txt  — httpx-verified live subdomains
    IPs.txt           — resolved IPs from all subdomains
    screenshots/      — gowitness screenshots of live domains

Usage:
    python3 Final.py target.com

-h7n
"""

import sys
import os
import threading
from pathlib import Path

from curl import curl
from Scanner import Scanner
from amass import Amass
from Asn import asn
from UI import ReconUI

TOOLS = [
    "certspotter", "virustotal", "alienvault", "commoncrawl", "csp",
    "chaos", "alterx", "subfinder", "github-subdomains", "puredns", "amass",
    "bgpq4", "rapiddns", "dnsx", "httpx", "gowitness",
]


def merge_and_dedupe(output_file: str, *input_files: str):
    """cat all input files, dedupe, write to output_file."""
    seen = set()
    lines = []
    for f in input_files:
        p = Path(f)
        if p.exists():
            for line in p.read_text(errors="ignore").splitlines():
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    lines.append(line)
    Path(output_file).write_text("\n".join(sorted(lines)))
    return len(lines)


def main(target: str):
    ui = ReconUI(target=target, tools=TOOLS)
    ui.banner()

    base_dir = os.getcwd()

    # ------------------------------------------------------------------
    # PHASE 1 — curl-based enumeration (certspotter, VT, AlienVault, etc.)
    # ------------------------------------------------------------------
    ui.section("Phase 1 — API / Curl Enumeration")

    os.makedirs("CURL", exist_ok=True)
    c = curl(target)

    with ui.step("certspotter") as s:
        try:
            os.chdir(os.path.join(base_dir, "CURL"))
            c.crt()
            s.result(count=ui.count_lines("crt.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    with ui.step("virustotal") as s:
        try:
            os.chdir(os.path.join(base_dir, "CURL"))
            c.virus_total()
            s.result(count=ui.count_lines("vt.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    with ui.step("alienvault") as s:
        try:
            os.chdir(os.path.join(base_dir, "CURL"))
            c.alien_vault()
            s.result(count=ui.count_lines("Alien_v_IP.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    with ui.step("commoncrawl (wayback)") as s:
        try:
            os.chdir(os.path.join(base_dir, "CURL"))
            c.wayback()
            s.result(count=ui.count_lines("commoncrawl_subdomains.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    with ui.step("CSP header") as s:
        try:
            os.chdir(os.path.join(base_dir, "CURL"))
            c.CSP_header()
            s.result(count=ui.count_lines("csp.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    # ------------------------------------------------------------------
    # PHASE 2 — active subdomain enumeration (parallel)
    # ------------------------------------------------------------------
    ui.section("Phase 2 — Active Subdomain Enumeration")

    os.makedirs("SCANNER", exist_ok=True)
    sc = Scanner(target)
    am = Amass(target)

    def run_scanner_tools():
        os.chdir(os.path.join(base_dir, "SCANNER"))
        sc.chaos()
        sc.permutation()
        sc.subfinder()
        sc.github()
        sc.subdomain_brtFC()
        os.chdir(base_dir)

    def run_amass():
        os.chdir(os.path.join(base_dir, "SCANNER"))
        am.active()
        am.passive()
        os.chdir(base_dir)

    with ui.step("chaos + alterx + subfinder + github + puredns + amass (parallel)") as s:
        try:
            t1 = threading.Thread(target=run_scanner_tools)
            t2 = threading.Thread(target=run_amass)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            s.result(note="see SCANNER/ for individual tool outputs")
        except Exception as e:
            s.fail(str(e))

    # ------------------------------------------------------------------
    # PHASE 3 — ASN → IP ranges → reverse IP
    # ------------------------------------------------------------------
    ui.section("Phase 3 — ASN & Reverse IP")

    os.makedirs("ASN", exist_ok=True)
    a = asn(target)

    with ui.step("ASN enumeration + IP ranges (bgpq4)") as s:
        try:
            os.chdir(os.path.join(base_dir, "ASN"))
            a.asn_enum()
            s.result(count=ui.count_lines("ip_ranges.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    with ui.step("reverse IP lookup (rapiddns + interlace)") as s:
        try:
            os.chdir(os.path.join(base_dir, "ASN"))
            a.reverse_ip_lookup()
            s.result(count=ui.count_lines("reverse_ip.txt"))
        except Exception as e:
            s.fail(str(e))
        finally:
            os.chdir(base_dir)

    # ------------------------------------------------------------------
    # PHASE 4 — merge everything → live domains → IPs → screenshots
    # ------------------------------------------------------------------
    ui.section("Phase 4 — Live Domains + IPs + Screenshots")

    # 4a — merge all subdomain files into one raw list
    with ui.step("merge + dedupe all subdomains") as s:
        try:
            raw_count = merge_and_dedupe(
                "All_Subdomains_raw.txt",
                "CURL/crt.txt",
                "CURL/vt.txt",
                "CURL/commoncrawl_subdomains.txt",
                "CURL/csp.txt",
                "ASN/reverse_ip.txt",
                "SCANNER/chaos.txt",
                "SCANNER/permutation.txt",
                "SCANNER/subfinder.txt",
                f"SCANNER/{target}.txt",
                "SCANNER/BrtFC.txt",
                "SCANNER/Amass_A.txt",
                "SCANNER/Amass_P.txt",
            )
            s.result(count=raw_count)
        except Exception as e:
            s.fail(str(e))

    # 4b — httpx liveness check → Live_Domains.txt
    with ui.step("liveness check (httpx) → Live_Domains.txt") as s:
        try:
            cmd = (
                "cat All_Subdomains_raw.txt "
                "| sed -E 's#^(https?://)##; s#^#https://#' "
                "| uro "
                "| httpx -mc 200,301,302,403,401 -silent > Live_Domains.txt"
            )
            os.system(cmd)
            live_count = ui.count_lines("Live_Domains.txt")
            s.result(count=live_count)
        except Exception as e:
            s.fail(str(e))

    # 4c — resolve all live domains to IPs → IPs.txt
    with ui.step("IP resolution (dnsx) → IPs.txt") as s:
        try:
            cmd = (
                "cat Live_Domains.txt "
                "| sed -E 's#^https?://##' "
                "| dnsx -a -resp-only -silent "
                "| sort -u > IPs.txt"
            )
            os.system(cmd)

            # also add IPs from AlienVault and ASN ranges
            os.system("cat CURL/Alien_v_IP.txt | anew IPs.txt 2>/dev/null || true")

            ip_count = ui.count_lines("IPs.txt")
            s.result(count=ip_count)
        except Exception as e:
            s.fail(str(e))

    # 4d — screenshots of live domains → screenshots/
    with ui.step("screenshots (gowitness) → screenshots/") as s:
        try:
            os.makedirs("screenshots", exist_ok=True)
            cmd = (
                "cat Live_Domains.txt "
                "| grep -viE '\\.(js|css|json|woff|ttf|svg|png|jpg|gif)($|\\?)' "
                "> _screenshot_targets_.txt "
                "&& gowitness scan file -f _screenshot_targets_.txt "
                "--threads 5 "
                "--chrome-path $(which brave-browser) "
                "--db-location screenshots/gowitness.db "
                "--screenshot-path screenshots/"
            )
            os.system(cmd)

            # count screenshots taken
            ss_count = len(list(Path("screenshots").glob("*.png")))
            s.result(count=ss_count)
        except Exception as e:
            s.fail(str(e))

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    ui.summary(
        live_count=ui.count_lines("Live_Domains.txt"),
        ip_count=ui.count_lines("IPs.txt"),
        screenshot_count=len(list(Path("screenshots").glob("*.png"))) if Path("screenshots").exists() else 0,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 Final.py <target.com>")
        sys.exit(1)

    main(sys.argv[1])