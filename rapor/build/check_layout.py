#!/usr/bin/env python3
"""Flag words beyond right margin and pages ending in a heading. Exit 1 on issues.
python check_layout.py report.pdf [--margin-mm 18] [--heading-size 11.5]
"""
import argparse, re, subprocess, sys, xml.etree.ElementTree as ET
ap = argparse.ArgumentParser(); ap.add_argument("pdf")
ap.add_argument("--margin-mm", type=float, default=18)
ap.add_argument("--ratio", type=float, default=1.2, help="last line taller than ratio*median line height => heading")
a = ap.parse_args()
xml = subprocess.run(["pdftotext", "-bbox-layout", a.pdf, "-"], capture_output=True, text=True, check=True).stdout
xml = re.sub(r'<!DOCTYPE[^>]*>', '', xml); xml = xml.replace('xmlns="http://www.w3.org/1999/xhtml"', '')
root = ET.fromstring(xml)
tol = 1.0; mpt = a.margin_mm * 72 / 25.4
import statistics
hs=[float(l.get("yMax"))-float(l.get("yMin")) for l in root.iter("line")]
med=statistics.median(hs) if hs else 10
issues = 0; pages = root.findall(".//page")
for i, pg in enumerate(pages, 1):
    w = float(pg.get("width")); limit = w - mpt + tol
    over = [x.text for x in pg.iter("word") if float(x.get("xMax")) > limit]
    if over and i > 1:
        issues += 1; print(f"p{i}: {len(over)} words beyond right margin, e.g. {over[:4]}")
    lines = list(pg.iter("line"))
    body = [l for l in lines if float(l.get("yMin")) > 60 and float(l.get("yMax")) < float(pg.get("height")) - 60]
    if body and i > 2:
        last = max(body, key=lambda l: float(l.get("yMax")))
        h = float(last.get("yMax")) - float(last.get("yMin"))
        if h >= a.ratio * med and len(list(last.iter("word"))) < 12:
            txt = " ".join(x.text for x in last.iter("word"))
            issues += 1; print(f"p{i}: page ends with heading? '{txt[:60]}'")
print(f"pages={len(pages)} issues={issues}")
sys.exit(1 if issues else 0)
