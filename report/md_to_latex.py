"""Convert report.md into report.tex (LaTeX, for Overleaf or any TeX Live install).

Usage: python report/md_to_latex.py

Handles the Markdown subset report.md uses: the title block, ## and ### headings, paragraphs, "- " bullet
lists, pipe tables, figures with a caption <div>, **bold**, *italic*, `code` and URLs. Figures are not copied:
the .tex looks for them in ../figures (this repository) and in figures/ (an Overleaf upload of that folder).
Compile with pdfLaTeX (two passes for the figure numbers).
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE, TARGET = HERE / "report.md", HERE / "report.tex"

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
% Generated from report.md by report/md_to_latex.py. Edit report.md and regenerate, or edit this file directly
% once the team switches to LaTeX as the source.
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=18mm]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{xltabular}
\usepackage{caption}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{newunicodechar}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\usepackage{xurl}

\graphicspath{{../figures/}{figures/}}
\setlist[itemize]{itemsep=2pt, topsep=4pt, leftmargin=*}
\captionsetup{font=small, labelfont=bf}
\renewcommand{\arraystretch}{1.15}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}

% Characters used in the text that pdfLaTeX does not map by default
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{≤}{\ensuremath{\le}}
\newunicodechar{≥}{\ensuremath{\ge}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{·}{\textperiodcentered}
\newunicodechar{²}{\textsuperscript{2}}
\newunicodechar{±}{\ensuremath{\pm}}
\newunicodechar{ρ}{\ensuremath{\rho}}
\newunicodechar{Δ}{\ensuremath{\Delta}}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{≈}{\ensuremath{\approx}}
"""

LATEX_SPECIALS = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                  "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(ch, ch) for ch in text)


def code(text: str) -> str:
    # \texttt with line-break opportunities after underscores, so long identifiers wrap in narrow table cells
    return r"\texttt{" + escape(text).replace(r"\_", r"\_\allowbreak{}").replace("<", r"\textless{}").replace(">", r"\textgreater{}") + "}"


def inline(text: str) -> str:
    """Markdown inline markup to LaTeX: `code`, **bold**, *italic*, URLs; everything else escaped."""
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text).replace("\\|", "|")
    # Code spans and URLs become placeholders first, so **bold** around them pairs up across the whole string
    spans = []

    def keep(latex: str) -> str:
        spans.append(latex)
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]*)`", lambda m: keep(code(m.group(1))), text)
    text = re.sub(r"https?://\S+", lambda m: keep(r"\url{" + m.group(0) + "}"), text)
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", text)
    text = text.replace("\"", "''")
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


def table(lines: list) -> str:
    rows = [[cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]] for line in lines]
    header, spec_row, body = rows[0], rows[1], rows[2:]
    columns = []
    for cell in spec_row:
        if cell.startswith(":") and cell.endswith(":"):
            columns.append("c")
        elif cell.endswith(":"):
            columns.append("r")
        else:
            columns.append(r">{\raggedright\arraybackslash}X")
    if not any("X" in c for c in columns):
        columns[0] = r">{\raggedright\arraybackslash}X"
    out = [r"{\small", r"\begin{xltabular}{\linewidth}{" + "".join(columns) + "}", r"\toprule"]
    if any(header):
        out += [" & ".join(r"\textbf{" + inline(c) + "}" for c in header) + r" \\", r"\midrule", r"\endhead"]
    out += [" & ".join(inline(c) for c in row) + r" \\" for row in body]
    out += [r"\bottomrule", r"\end{xltabular}", "}"]
    return "\n".join(out)


def figure(image_line: str, caption_line: str) -> str:
    path = re.match(r"!\[[^\]]*\]\(([^)]+)\)", image_line).group(1)
    caption = re.sub(r"</?div[^>]*>", "", caption_line).strip()
    caption = re.sub(r"^Figure \d+\.\s*", "", caption)
    return "\n".join([r"\begin{figure}[htbp]", r"\centering", rf"\includegraphics[width=\linewidth,height=0.42\textheight,keepaspectratio]{{{Path(path).stem}}}",
                      rf"\caption{{{inline(caption)}}}", r"\end{figure}"])


def title_block(lines: list) -> str:
    text = "\n".join(lines)
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    subtitle = re.search(r'<div class="subtitle">(.*?)</div>', text).group(1)
    meta = re.search(r'<div class="meta">(.*?)</div>', text, re.S).group(1)
    fields = {m.group(1): m.group(2).strip() for m in re.finditer(r"<b>(.*?):</b>\s*(.*?)(?:<br>|$)", meta.strip(), re.M)}
    team, date = fields.pop("Team", ""), fields.pop("Date", "")
    meta_lines = [rf"\textbf{{{escape(k)}:}} {inline(v)}" for k, v in fields.items()]
    return "\n".join([rf"\title{{{inline(title)}\\[4pt]\large {inline(subtitle)}}}", r"\author{" + r" \and ".join(inline(member.strip()) for member in team.split(",")) + "}",
                      rf"\date{{{inline(date)}}}", r"\begin{document}", r"\maketitle", r"\begin{center}\small",
                      r" \\ ".join(meta_lines), r"\end{center}"])


def convert(markdown: str) -> str:
    lines = markdown.split("\n")
    first_section = next(i for i, line in enumerate(lines) if line.startswith("## "))
    out = [PREAMBLE, title_block(lines[:first_section])]
    i, paragraph, bullets = first_section, [], []

    def flush() -> None:
        if paragraph:
            out.append(inline(" ".join(paragraph)) + "\n")
            paragraph.clear()
        if bullets:
            out.append("\n".join([r"\begin{itemize}"] + [r"\item " + inline(b) for b in bullets] + [r"\end{itemize}"]) + "\n")
            bullets.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            flush()
            out.append(r"\section{" + inline(re.sub(r"^## (\d+\.\s*)?", "", line)) + "}\n")
        elif line.startswith("### "):
            flush()
            out.append(r"\subsection{" + inline(re.sub(r"^### (\d+\.\d+\s*)?", "", line)) + "}\n")
        elif line.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(table(block) + "\n")
            continue
        elif line.startswith("!["):
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            caption = lines[j] if j < len(lines) and lines[j].startswith('<div class="caption">') else ""
            out.append(figure(line, caption) + "\n")
            i = j + 1 if caption else i + 1
            continue
        elif line.startswith("- "):
            if paragraph:
                flush()
            bullets.append(line[2:])
        elif not line.strip():
            flush()
        else:
            if bullets:
                flush()
            paragraph.append(line.strip())
        i += 1
    flush()
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    TARGET.write_text(convert(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(HERE.parent)}")
