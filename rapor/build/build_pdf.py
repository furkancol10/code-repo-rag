#!/usr/bin/env python3
"""Markdown -> PDF (WeasyPrint). Raw inline SVG/HTML allowed. TOC from h2.
uv run --with weasyprint --with markdown python build_pdf.py report.md out.pdf --css report.css --title "T" [--subtitle S] [--meta M]
"""
import argparse, html, re, sys
from pathlib import Path
import markdown
from weasyprint import HTML

ap = argparse.ArgumentParser()
ap.add_argument("md"); ap.add_argument("pdf")
ap.add_argument("--css", required=True)
ap.add_argument("--title", required=True)
ap.add_argument("--subtitle", default=""); ap.add_argument("--meta", default="")
ap.add_argument("--no-toc", action="store_true")
a = ap.parse_args()

body = markdown.markdown(Path(a.md).read_text(encoding="utf-8"),
    extensions=["tables", "fenced_code", "sane_lists", "md_in_html"])
items = []
def add_id(m):
    n = len(items) + 1
    items.append((n, re.sub(r"<[^>]+>", "", m.group(1))))
    return f'<h2 id="sec{n}">{m.group(1)}</h2>'
body = re.sub(r"<h2>(.*?)</h2>", add_id, body)
toc = "" if a.no_toc else ('<section class="toc"><h2>İçindekiler</h2><ol>' + "".join(
    f'<li><a href="#sec{n}">{html.escape(t)}</a></li>' for n, t in items) + "</ol></section>")
hdr = html.escape(a.title).replace('"', '\\"')
doc = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>{html.escape(a.title)}</title>
<style>@page {{ @top-center {{ content: "{hdr}"; font: 8.5pt "DejaVu Sans","Noto Sans",sans-serif; color:#777; }} }}</style></head><body>
<section class="title-page"><h1>{html.escape(a.title)}</h1><div class="subtitle">{html.escape(a.subtitle)}</div><div class="meta">{html.escape(a.meta)}</div></section>
{toc}{body}</body></html>"""
HTML(string=doc, base_url=str(Path(a.md).resolve().parent)).write_pdf(a.pdf, stylesheets=[a.css])
print("ok", a.pdf, "sections:", len(items))
