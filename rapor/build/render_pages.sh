#!/usr/bin/env bash
# usage: render_pages.sh report.pdf outdir page [page...]   (<=60 DPI PNGs)
set -e
pdf=$1; out=$2; shift 2; mkdir -p "$out"
for p in "$@"; do pdftoppm -r 60 -f "$p" -l "$p" -png "$pdf" "$out/p$p"; done
ls "$out"
