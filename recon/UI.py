"""
Terminal UI for the Recon pipeline.
Styled banner + per-step status + final summary table.
-h7n
"""

import time
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()
AUTHOR_TAG = "-h7n"


class StepResult:
    def __init__(self):
        self.count = None
        self.note = ""
        self.failed = False

    def result(self, count=None, note=""):
        self.count = count
        self.note = note

    def fail(self, note=""):
        self.failed = True
        self.note = note


class ReconUI:
    def __init__(self, target: str, tools=None):
        self.target = target
        self.tools = tools or []
        self.steps = []
        self.start_time = time.time()

    def banner(self):
        title = Text("R E C O N   S C A N N E R", style="bold cyan", justify="center")
        sub = Text(f"target: {self.target}", style="bold white", justify="center")

        body = Text()
        if self.tools:
            body.append("tools  ", style="dim")
            body.append(" • ".join(self.tools), style="green")

        content = Text()
        content.append_text(title)
        content.append("\n")
        content.append_text(sub)
        if self.tools:
            content.append("\n\n")
            content.append_text(body)

        console.print()
        console.print(Panel(Align.center(content), box=box.DOUBLE, border_style="cyan", padding=(1, 4)))
        console.print(Align.center(Text(AUTHOR_TAG, style="dim italic")))
        console.print()

    def section(self, name: str):
        console.print()
        console.rule(f"[bold magenta]{name}[/bold magenta]", style="magenta")

    @contextmanager
    def step(self, name: str):
        console.print(f"[bold yellow][*][/bold yellow] running [bold]{name}[/bold] ...")
        started = time.time()
        result = StepResult()
        try:
            yield result
        except Exception as e:
            result.failed = True
            result.note = str(e)
        finally:
            elapsed = time.time() - started
            self.steps.append((name, result, elapsed))
            if result.failed:
                console.print(f"[bold red][!][/bold red] {name} failed [dim]({elapsed:.1f}s)[/dim] — {result.note}")
            else:
                count_str = f", {result.count} results" if result.count is not None else ""
                note_str = f" — {result.note}" if result.note else ""
                console.print(f"[bold green][+][/bold green] {name} done [dim]({elapsed:.1f}s{count_str})[/dim]{note_str}")

    def summary(self, live_count=0, ip_count=0, screenshot_count=0):
        total = time.time() - self.start_time

        # per-step table
        table = Table(
            title=f"Scan Summary — {self.target}",
            box=box.SIMPLE_HEAVY,
            title_style="bold cyan",
            header_style="bold white",
        )
        table.add_column("Step", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Results", justify="right")
        table.add_column("Time", justify="right", style="dim")

        for name, result, elapsed in self.steps:
            status = "[bold red]FAILED[/bold red]" if result.failed else "[bold green]OK[/bold green]"
            results_str = str(result.count) if result.count is not None else "-"
            table.add_row(name, status, results_str, f"{elapsed:.1f}s")

        console.print()
        console.print(table)

        # final output summary
        output_table = Table(box=box.SIMPLE, header_style="bold cyan", title="Output Files", title_style="bold cyan")
        output_table.add_column("File", style="bold green")
        output_table.add_column("Contents", style="white")
        output_table.add_column("Count", justify="right", style="yellow")

        output_table.add_row("Live_Domains.txt", "Live subdomains (httpx verified)", str(live_count))
        output_table.add_row("IPs.txt", "Resolved IPs from all subdomains", str(ip_count))
        output_table.add_row("screenshots/", "Gowitness screenshots", str(screenshot_count))

        console.print()
        console.print(output_table)

        ok = sum(1 for _, r, _ in self.steps if not r.failed)
        failed = sum(1 for _, r, _ in self.steps if r.failed)

        footer = Text()
        footer.append(f"{ok} succeeded", style="green")
        if failed:
            footer.append("  •  ", style="dim")
            footer.append(f"{failed} failed", style="red")
        footer.append("  •  ", style="dim")
        footer.append(f"total {total:.1f}s", style="dim")

        console.print()
        console.print(Align.center(footer))
        console.print(Align.center(Text(AUTHOR_TAG, style="dim italic")))
        console.print()

    @staticmethod
    def count_lines(filepath: str) -> int:
        p = Path(filepath)
        if not p.exists():
            return 0
        return sum(1 for _ in p.open(errors="ignore"))