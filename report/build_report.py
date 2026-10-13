"""Build report.pdf from report.md.

Usage: python report/build_report.py
Needs the `markdown` and `Pillow` packages and Google Chrome (set the CHROME environment variable if it is not in a usual place).
Figures are read from ../figures and downsized into report/.build/ so the PDF stays small.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from PIL import Image

HERE = Path(__file__).resolve().parent
FIGURES = HERE.parent / "figures"
BUILD = HERE / ".build"
MAX_WIDTH_PX = 1800

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; @bottom-center { content: counter(page); font: 9pt Helvetica, Arial, sans-serif; color: #666; } }
body { font: 10.3pt/1.42 Helvetica, Arial, sans-serif; color: #15151E; }
h1 { font-size: 24pt; margin: 0 0 2pt; }
.subtitle { font-size: 12pt; color: #555; margin-bottom: 10pt; }
.meta { font-size: 9.5pt; border-left: 3pt solid #E10600; padding: 2pt 0 2pt 9pt; margin-bottom: 14pt; line-height: 1.5; }
h2 { font-size: 15pt; margin: 20pt 0 6pt; padding-bottom: 3pt; border-bottom: 1.2pt solid #E10600; break-after: avoid; }
h3 { font-size: 11.8pt; margin: 14pt 0 4pt; break-after: avoid; }
p { margin: 5pt 0; }
p:has(+ table), p:has(+ .figure), p:has(+ ul) { break-after: avoid; }
ul { margin: 4pt 0 6pt; padding-left: 15pt; }
li { margin: 2.5pt 0; }
code { font: 8.8pt Menlo, Consolas, monospace; background: #F2F2F5; padding: 0 2pt; border-radius: 2pt; }
table { border-collapse: collapse; width: 100%; margin: 7pt 0 10pt; font-size: 8.8pt; break-inside: avoid; }
table.long { break-inside: auto; }
table.registry { table-layout: fixed; font-size: 8.3pt; }
table.registry td { overflow-wrap: anywhere; }
table.registry td:first-child { overflow-wrap: normal; }
table.registry code { font-size: 7.2pt; white-space: nowrap; }
table.registry th:nth-child(1), table.registry td:nth-child(1) { width: 11%; }
table.registry th:nth-child(2), table.registry td:nth-child(2) { width: 30%; }
table.registry th:nth-child(3), table.registry td:nth-child(3) { width: 13%; }
table.registry th:nth-child(4), table.registry td:nth-child(4) { width: 26%; }
table.registry th:nth-child(5), table.registry td:nth-child(5) { width: 20%; }
tr { break-inside: avoid; }
th { background: #15151E; color: #fff; text-align: left; padding: 3.5pt 5pt; font-weight: 600; }
td { padding: 3pt 5pt; border-bottom: 0.5pt solid #D5D5DC; vertical-align: top; }
thead:not(:has(th:not(:empty))) { display: none; }
.figure { break-inside: avoid; margin: 9pt 0 11pt; text-align: center; }
.figure img { max-width: 100%; max-height: 108mm; }
.figure.tall img { max-height: 150mm; }
.caption { font-size: 8.8pt; color: #444; margin-top: 3pt; text-align: left; }
"""
TALL = {"xai_shap_beeswarm.png", "de_q1_front_row_conversion.png", "de_q3_mechanical_retirements.png", "feat_univariate_auc.png"}
LONG_TABLE_MARKERS = ("Why it is known before the race", "Precision")   # tables allowed to run over a page break


def find_chrome() -> str:
    candidates = [os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"),
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("Google Chrome not found. Set the CHROME environment variable to its path.")


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    text = (HERE / "report.md").read_text(encoding="utf-8")

    def figure(match: re.Match) -> str:
        alt, name, caption = match.group(1), match.group(2), match.group(3)
        image = Image.open(FIGURES / name)
        if image.width > MAX_WIDTH_PX:
            image = image.resize((MAX_WIDTH_PX, round(image.height * MAX_WIDTH_PX / image.width)), Image.LANCZOS)
        image.save(BUILD / name, optimize=True)
        tall = " tall" if name in TALL else ""
        return f'<div class="figure{tall}"><img src="{name}" alt="{alt}"><div class="caption">{caption}</div></div>'

    text = re.sub(r'!\[(.*?)\]\((.*?)\)\n<div class="caption">(.*?)</div>', figure, text)
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = re.sub(r"<table>(?=(?:(?!</table>).)*?(?:%s))" % "|".join(LONG_TABLE_MARKERS), '<table class="long">', body, flags=re.S)
    body = re.sub(r'<table class="long">(?=(?:(?!</table>).)*?Why it is known before the race)', '<table class="long registry">', body, flags=re.S)
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Formula 1 Podium Prediction</title><style>{CSS}</style></head><body>{body}</body></html>'
    (BUILD / "report.html").write_text(html, encoding="utf-8")

    pdf = HERE / "report.pdf"
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", (BUILD / "report.html").as_uri()], check=True, capture_output=True)
    print(f"Wrote {pdf} ({pdf.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
