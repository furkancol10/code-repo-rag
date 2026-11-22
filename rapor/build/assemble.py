#!/usr/bin/env python3
"""parts/s01..s11.md + yönetici özeti + inline SVG şemaları -> build/report.md
Çalıştır: python3 assemble.py   (rapor/build içinden)
Şemalar parts içindeki `diagram-spec` bloklarının yerine geçer; parts dosyaları değişmez.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "parts"
FONT = "DejaVu Sans"
FS = 12  # viewBox 720 -> A4 içerik ~0.91 ölçek => 12 birim ~ 8.2 pt

try:
    from PIL import ImageFont
    _f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FS)
    _fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FS)
    def tw(s, bold=False): return (_fb if bold else _f).getlength(s)
except Exception:  # yaklaşık
    def tw(s, bold=False): return len(s) * FS * 0.62

WARN = []

def fit(s, w, bold=False, what=""):
    if tw(s, bold) > w:
        WARN.append(f"taşma: {what}{s!r} {tw(s,bold):.0f}>{w}")

def text(x, y, s, bold=False, anchor="start", fill="#1a1a1a", size=FS, halo=False):
    st = ""  # WeasyPrint paint-order desteklemez; halo kullanılmaz
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"'
            f'{" font-weight=\"bold\"" if bold else ""}{st}>{escape(s)}</text>')

def box(x, y, w, lines, fill="#fff", stroke="#1f3a68", head=True, h=None, what=""):
    lh = 15
    h = h or (len(lines) * lh + 12)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
    for i, ln in enumerate(lines):
        b = head and i == 0
        fit(ln, w - 10, b, what)
        out.append(text(x + w / 2, y + 6 + lh * (i + 1) - 3, ln, bold=b, anchor="middle"))
    return "\n".join(out), h

def arrow(pts, both=False):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    ms = ' marker-start="url(#ah)"' if both else ""
    return f'<path d="{d}" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"{ms}/>'

DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs>')

def svg(vb_w, vb_h, body, title):
    return (f'<svg viewBox="0 0 {vb_w} {vb_h}" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{escape(title)}" font-family="{FONT}, sans-serif" style="max-width:100%;height:auto">'
            f'{DEFS}' + "\n".join(body) + '</svg>')

def figure(svg_str, caption):
    return f'<figure>\n{svg_str}\n<figcaption>{escape(caption)}</figcaption>\n</figure>'

# ---------------------------------------------------------------- mimari
def diagram_architecture():
    b = []
    groups = [(4, 126, "Giriş", "#eef2f8"), (140, 286, "İndeksleme (src/pipeline.py)", "#eef6ee"),
              (438, 122, "Arama", "#fbf3e6"), (572, 144, "Üretim", "#f6eef6")]
    for gx, gw, gl, gf in groups:
        b.append(f'<rect x="{gx}" y="26" width="{gw}" height="372" rx="8" fill="{gf}" stroke="#9aa7bd" stroke-width="1"/>')
        b.append(text(gx + 8, 44, gl, bold=True, fill="#1f3a68"))
    def add(x, y, w, lines, **k):
        s, h = box(x, y, w, lines, what="mimari ", **k); b.append(s); return h
    add(10, 56, 114, ["Yerel repo", "(.py, .md)"])
    add(10, 160, 114, ["src/cli.py", "index, search,", "ask, eval"])
    add(10, 264, 114, ["app.py", "(Streamlit)"])
    add(148, 62, 270, ["scanner.py", "dosya listesi"])
    add(148, 140, 270, ["chunk.py, chunk_py.py,", "chunk_md.py: CodeChunk"])
    add(148, 228, 130, ["embedder.py", "bge-m3", "vektörleri"])
    add(288, 228, 130, ["bm25_index.py", "bm25.json"], h=58)
    add(148, 326, 130, ["vector_index.py", "vecs.npy +", "chunks.json"])
    add(444, 205, 110, ["hybrid.py", "ağırlıklı RRF", "20+20 aday", "çıktı: ilk 5"])
    add(578, 212, 132, ["generator.py", "bağlam kurma,", "atıf düzeltme"])
    add(578, 336, 132, ["Ollama", "qwen3.5:4b"])
    # oklar
    b.append(arrow([(124, 86), (148, 86)]))                       # repo -> scanner
    b.append(arrow([(283, 110), (283, 140)])); b.append(text(290, 129, "yollar"))
    b.append(arrow([(213, 190), (213, 228)])); b.append(text(220, 214, "parça metni"))
    b.append(arrow([(353, 190), (353, 228)])); b.append(text(360, 214, "token'lar"))
    b.append(arrow([(213, 286), (213, 326)])); b.append(text(220, 311, "vektörler"))
    b.append(arrow([(418, 257), (444, 257)]))                     # bm25 -> hybrid
    b.append(arrow([(278, 355), (500, 355), (500, 281)]))         # vec -> hybrid
    b.append(arrow([(124, 191), (134, 191), (134, 412), (534, 412), (534, 281)]))  # cli -> hybrid
    b.append(arrow([(124, 287), (134, 287)]))                     # app -> bus
    b.append(text(150, 407, "sorgu, mod (cli ve app)", halo=True))
    b.append(text(290, 349, "20 aday", halo=True))
    b.append(arrow([(554, 243), (578, 243)]))                     # hybrid -> generator
    b.append(arrow([(612, 274), (612, 336)])); b.append(text(618, 300, "prompt"))
    b.append(arrow([(676, 336), (676, 274)])); b.append(text(670, 322, "cevap", anchor="end"))
    return figure(svg(720, 424, b, "Kod Repo Asistanı veri akışı"),
                  "Şekil 1. Veri akışı: giriş, indeksleme, arama, üretim (soldan sağa). Yollar src/ modül adlarıdır; BM25 ve vektör aday listeleri hybrid.py'de birleşir.")

# ---------------------------------------------------------------- zaman çizelgesi
def diagram_timeline():
    b = []
    P = [
        ("0. Plan", ["20 Kas 15:33", "2500377", "\"plan\""], 1),
        ("1. İskelet", ["15:34-15:35", "b980049: soru", "seti donduruldu"], 2),
        ("2. Arama", ["15:38", "6dff6cb:", "hibrit arama"], 1),
        ("3. Faz 3 ve ayar", ["15:41-16:41", "dccbc70:", "ağırlıklı RRF"], 6),
        ("4. Denetim, 1. tur", ["21 Kas 12:52-13:01", "1f2b19a: Neon", "düzeltmeleri"], 4),
        ("5. E2E ve belge", ["21 Kas 12:35 ve 13:10", "9b57b5d: Playwright", "testleri"], 2),
        ("6. 2. tur düzeltme", ["22 Kas 12:39-12:47", "77b5f78: master'a;", "8fb632d son commit"], 9),
    ]
    cw, gap = 170, 10
    xs = [6 + i * (cw + gap) for i in range(4)]
    def band(x0, x1, label, y):
        b.append(f'<rect x="{x0}" y="{y}" width="{x1-x0}" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>')
        b.append(text((x0 + x1) / 2, y + 18, label, bold=True, anchor="middle", fill="#1f3a68"))
        fit(label, x1 - x0 - 8, True, "zaman ")
    def row(y0, items, xcols):
        ay = y0 + 36
        b.append(f'<line x1="{xcols[0]+cw/2}" y1="{ay}" x2="{xcols[-1]+cw/2}" y2="{ay}" stroke="#1f3a68" stroke-width="2.5"/>')
        for x, (head, lines, n) in zip(xcols, items):
            cx = x + cw / 2
            b.append(f'<circle cx="{cx}" cy="{ay}" r="14" fill="#1f3a68"/>')
            b.append(text(cx, ay + 4, str(n), bold=True, anchor="middle", fill="#fff"))
            b.append(f'<line x1="{cx}" y1="{ay+14}" x2="{cx}" y2="{ay+26}" stroke="#9aa7bd"/>')
            s, h = box(x, ay + 26, cw, [head] + lines, fill="#f4f6fa", what="zaman ")
            b.append(s)
        return ay + 26 + 87
    # 1. satır: 20 Kasım
    band(xs[0] - 2, xs[3] + cw + 2, "20 Kasım 2026 (10 commit)", 6)
    yb = 6 + 26 + 6
    row_end = row(yb, P[:4], xs)
    # 2. satır
    y2 = row_end + 22
    band(xs[0] - 2, xs[1] + cw + 2, "21 Kasım 2026 (6 commit)", y2)
    band(xs[2] - 2, xs[2] + cw + 2, "22 Kasım (9 commit)", y2)
    row_end2 = row(y2 + 26 + 6, P[4:], xs[:3])
    # kopuk eksen işaretleri: gece boşluğu (satır başı) ve gün arası boşluk
    ay2 = y2 + 26 + 6 + 36
    mid = (xs[1] + cw / 2 + xs[2] + cw / 2) / 2
    b.append(f'<rect x="{mid-26}" y="{ay2-9}" width="52" height="18" fill="#fff"/>')
    b.append(f'<path d="M{mid-8},{ay2+9} L{mid-2},{ay2-9} M{mid+2},{ay2+9} L{mid+8},{ay2-9}" stroke="#c0392b" stroke-width="2" fill="none"/>')
    b.append(text(mid, ay2 - 14, "~23 sa boşluk", anchor="middle", fill="#c0392b", bold=True))
    fit("~23 sa boşluk", 150, True, "zaman ")
    n1 = "Dairedeki sayı faz başına commit sayısıdır (toplam 25). Eksen ölçekli değildir; saatler commit zamanıdır."
    n2 = "2. satır 1. satırın devamıdır (aralarında ~20 sa gece boşluğu)."
    fit(n1, 700, False, "zaman "); fit(n2, 700, False, "zaman ")
    b.append(text(6, row_end2 + 18, n1, fill="#555")); b.append(text(6, row_end2 + 33, n2, fill="#555"))
    return figure(svg(720, row_end2 + 44, b, "Geliştirme zaman çizelgesi"),
                  "Şekil 2. Geliştirme zaman çizelgesi: 25 commit, üç gün, yedi aşama. Aşama 0-3 aynı öğleden sonra 68 dakikada, denetim ve 1. tur düzeltme ertesi gün 9 dakikada, 2. tur düzeltme 22 Kasım'da 12:39-12:47 arasında commit'lendi.")

# ---------------------------------------------------------------- yol haritası
def wrap(s, w, bold=False):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(t, bold) <= w: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur)
    return lines

def diagram_roadmap():
    b = []
    cols = ["Tamamlandı", "Şimdi", "Sonra", "Belki"]
    ccol = ["#2f6f4f", "#1f3a68", "#4a6fa5", "#7f8c9b"]
    lw, cg = 104, 6
    cw = (720 - 4 - lw - 4 - cg * 3) // 4
    cx = [lw + 8 + i * (cw + cg) for i in range(4)]
    lanes = [
        ("Test ve ölçüm", {0: ["Playwright birleşti (77b5f78)"],
                           1: ["#1 Atıf eval betiği kalıcı (M)", "#2 Entegrasyon testi: pipeline, cli, tune_rrf (M)", "#3 Playwright yeniden koş (S)"],
                           2: ["#5 Hibrit-vektör, yeni soru seti (M)"]}),
        ("Güvenlik", {0: ["pickle yerine JSON, symlink (132f7d8, 1bee4f4, 8fb632d)"],
                      2: ["#6 fsmonitor kapat, repo yolu doğrula (S)", "#9 İndeks adı + atomik yazım (M)"]}),
        ("Doğruluk (parçalama, atıf)", {0: ["Satır kayması M3 (1bee4f4, 333fd9a)"], 1: ["#4 md çit türü, L4 (S)"]}),
        ("Performans", {0: ["Vektör önbelleği M6, L7 (132f7d8)"], 2: ["#10 Model yükleme ve indeksleme, yeniden ölç (M)"], 3: ["#13 Incremental indexing (M)"]}),
        ("Bakım ve belge", {0: ["baslat/durdur, README, eval sabitleme (2edbf3c, 5a8f7b9, 405bdb7)"],
                            2: ["#7 embed_fn (S)", "#8 Hata yönetimi ve loglama (M)", "#11 ruff/mypy, sabit yol, expander başlığı (S)"]}),
        ("Erişim ve kapsam (v2)", {3: ["#12 Cross-encoder rerank (L)", "#14 tree-sitter JS/C# (L)", "#15 Çağrı grafiği (L)"]}),
    ]
    y = 8
    for i, c in enumerate(cols):
        b.append(f'<rect x="{cx[i]}" y="{y}" width="{cw}" height="24" rx="4" fill="{ccol[i]}"/>')
        b.append(text(cx[i] + cw / 2, y + 16, c, bold=True, anchor="middle", fill="#fff"))
        fit(c, cw - 8, True, "yol ")
    y = 40
    for li, (lane, cells) in enumerate(lanes):
        heights = {}
        for ci, items in cells.items():
            hs = [len(wrap(t, cw - 12)) * 15 + 10 for t in items]
            heights[ci] = sum(hs) + 6 * (len(hs) - 1)
        lane_lines = wrap(lane, lw - 10, True)
        rh = max(max(heights.values()), len(lane_lines) * 15 + 8) + 12
        b.append(f'<rect x="4" y="{y}" width="712" height="{rh}" rx="4" fill="{"#f4f6fa" if li%2==0 else "#fff"}" stroke="#d4d9e0"/>')
        for k, lns in enumerate(lane_lines):
            b.append(text(10, y + 20 + 15 * k, lns, bold=True, fill="#1f3a68"))
        for ci, items in cells.items():
            yy = y + 6
            for t in items:
                ls = wrap(t, cw - 12)
                s, h = box(cx[ci], yy, cw, ls, fill="#fff", stroke=ccol[ci], head=False, what="yol ")
                b.append(s); yy += h + 6
        y += rh + 4
    b.append(text(8, y + 14, "#n: yol haritası öncelik numarası (bölüm 09); (S/M/L): efor. 1-4 Şimdi, 5-11 Sonra, 12-15 Belki.", fill="#555"))
    fit("#n: yol haritası öncelik numarası (bölüm 09); (S/M/L): efor. 1-4 Şimdi, 5-11 Sonra, 12-15 Belki.", 700, False, "yol ")
    return figure(svg(720, y + 22, b, "Yol haritası"),
                  "Şekil 3. Yol haritası (Tamamlandı / Şimdi / Sonra / Belki), alana göre. Bağımlılıklar (önce → sonra): #1 → #5, #5 → #12, #2 → #8, #2 → #9, #9 → #13, #10 → #13. Önceliklendirme ve efor değerlendirmedir.")

DIAGRAMS = {"architecture": diagram_architecture, "timeline": diagram_timeline, "roadmap": diagram_roadmap}

def replace_specs(md):
    def r(m):
        t = re.search(r"^type:\s*(\w+)", m.group(1), re.M).group(1)
        return DIAGRAMS[t]()
    return re.sub(r"```diagram-spec\n(.*?)```", r, md, flags=re.S)

SUMMARY = """## Yönetici özeti

Kod Repo Asistanı, yerel bir Git reposundaki Python ve Markdown dosyalarını sembol bazlı parçalayıp BM25 + `BAAI/bge-m3` hibrit aramayla getiren ve yerel LLM'le `dosya:satır` atıflı Türkçe cevap üreten, tamamen yerel çalışan bir RAG projesidir. Rapor 25 commit'lik (2026-11-20 ile 2026-11-22) depoyu, 21 Kasım 2026 tarihli çok boyutlu denetimi ve denetimden sonraki iki düzeltme turunu (22 Kasım dahil) kapsar.

### Beş temel sayı

| Ölçü | Değer | Kaynak |
|---|---|---|
| Kod ve test | 1993 satır Python; 65 test geçti (1.12 sn); denetimde 36 testti | `facts.md`; `uv run pytest -q` |
| Retrieval (ana set, 59 soru) | hybrid hit@5 0.92, MRR@10 0.796; vektörden farkı gürültü düzeyinde | `eval/results.md` |
| RRF ayarı (ayrı 36 soruluk set) | skor 0.7355 → 0.7880 (+0.0526) | `eval/tuning_results.md` |
| Denetim bulguları | 29 bulgu (0 critical, 3 high, 13 medium, 13 low); iki turda 14'ü kapandı; 15 açık: 0 high, 4 medium, 11 low | `denetim/DENETIM-2026-11-21.md`; `facts.md` |
| Geçersiz atıf oranı | %21,9 → %0 (14 cevap; oturum ölçümü, depoda doğrulanmadı) | `facts.md` |

### Puanlar

Denetim anı genel puanı 6.9/10'dur (değerlendirme): denetimin boyut puanlarından türetilen ağırlıklı toplam, değiştirilmemiştir; hesap bölüm 06'dadır. İki düzeltme turundan sonra yazarın yargısı 7.4/10'dur. Bu ikinci rakam yeniden denetim değildir, yazarın yargısıdır ve yeniden denetimle doğrulanmamıştır; genel denetim puanı olarak kullanılmaz.

### En büyük 3 risk

1. **Üretim kalitesi kalıcı ölçülmüyor.** Atıf iyileşmesi yalnız oturum ölçümüdür; ölçüm betiği `eval/` içinde yok (M8).
2. **Hibritin üstünlüğü kanıtsız.** Vektöre göre hit@5 farkı 1 iyi / 0 kötü / 58 aynı, RR farkı +0.0014 (M9); README yorumu düzeltildi, ölçüm sınırı duruyor.
3. **Entegrasyon testi yok.** `pipeline`, `cli` ve `eval/tune_rrf` testsiz; `vector_index` kısmen test ediliyor, kapsama yeniden ölçülmedi (denetim anı %59) (M10).

### Sonraki adım

Yol haritasının ilk üç işi (bölüm 09): atıf ölçümünü `eval/` içinde kalıcı betiğe çevirmek, `pipeline`/`cli`/`eval/tune_rrf` için entegrasyon testi yazmak, Playwright testlerini `master`'da yeniden çalıştırmak. Ardından `chunk_md` çit türü eşlemesi (L4) düzeltilir.
"""

def main():
    parts = [SUMMARY]
    for p in sorted(PARTS.glob("s[0-9][0-9].md")):
        parts.append(replace_specs(p.read_text(encoding="utf-8")).strip() + "\n")
    out = "\n\n".join(parts)
    assert "diagram-spec" not in out
    (ROOT / "build" / "report.md").write_text(out, encoding="utf-8")
    # şemaların bağımsız kopyaları
    (ROOT / "assets").mkdir(exist_ok=True)
    for name, fn in DIAGRAMS.items():
        (ROOT / "assets" / f"{name}.svg").write_text(re.search(r"<svg.*</svg>", fn(), re.S).group(0), encoding="utf-8")
    print("report.md", len(out), "bayt;", "uyarı:" if WARN else "uyarı yok")
    for w in sorted(set(WARN)): print("  ", w)

if __name__ == "__main__":
    main()
