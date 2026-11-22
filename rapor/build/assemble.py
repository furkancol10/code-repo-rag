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
    add(288, 228, 130, ["bm25_index.py", "bm25.pkl"], h=58)
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
    cols = [
        ("0. Plan", ["15:33", "2500377", "\"plan\""], 1),
        ("1. İskelet", ["15:34-15:35", "b980049: soru", "seti donduruldu"], 2),
        ("2. Arama", ["15:38", "6dff6cb:", "hibrit arama"], 1),
        ("3. Faz 3 + ayar", ["15:41-16:41", "dccbc70:", "ağırlıklı RRF"], 6),
        ("4. Denetim", ["12:52-13:01", "1f2b19a: Neon", "düzeltmeleri"], 4),
    ]
    cw, gap = 120, 14
    xs = [6 + i * (cw + gap) for i in range(5)]
    xs[4] += 24  # gece boşluğu için ek boşluk
    # gün çerçeveleri
    b.append(f'<rect x="{xs[0]-2}" y="20" width="{xs[3]+cw-xs[0]+4}" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>')
    b.append(text((xs[0] + xs[3] + cw) / 2, 38, "20 Kasım 2026 (10 commit)", bold=True, anchor="middle", fill="#1f3a68"))
    b.append(f'<rect x="{xs[4]-2}" y="20" width="{cw+4}" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>')
    b.append(text(xs[4] + cw / 2, 38, "21 Kasım 2026", bold=True, anchor="middle", fill="#1f3a68"))
    ay = 82
    b.append(f'<line x1="{xs[0]+cw/2}" y1="{ay}" x2="{xs[3]+cw/2}" y2="{ay}" stroke="#1f3a68" stroke-width="2.5"/>')
    b.append(f'<line x1="{xs[4]+cw/2}" y1="{ay}" x2="{xs[4]+cw/2}" y2="{ay}" stroke="#1f3a68" stroke-width="2.5"/>')
    # kırık eksen
    bx = (xs[3] + cw + xs[4]) / 2
    b.append(f'<line x1="{xs[3]+cw/2}" y1="{ay}" x2="{bx-8}" y2="{ay}" stroke="#1f3a68" stroke-width="2.5"/>')
    b.append(f'<line x1="{bx+8}" y1="{ay}" x2="{xs[4]+cw/2}" y2="{ay}" stroke="#1f3a68" stroke-width="2.5"/>')
    b.append(f'<path d="M{bx-8},{ay+8} L{bx-2},{ay-8} M{bx+2},{ay+8} L{bx+8},{ay-8}" stroke="#c0392b" stroke-width="2" fill="none"/>')
    b.append(text(bx, ay + 26, "~20 sa", anchor="middle", fill="#c0392b", bold=True))
    b.append(text(bx, ay + 41, "boşluk", anchor="middle", fill="#c0392b"))
    for i, (head, lines, n) in enumerate(cols):
        cx = xs[i] + cw / 2
        b.append(f'<circle cx="{cx}" cy="{ay}" r="14" fill="#1f3a68"/>')
        b.append(text(cx, ay + 4, str(n), bold=True, anchor="middle", fill="#fff"))
        b.append(f'<line x1="{cx}" y1="{ay+14}" x2="{cx}" y2="124" stroke="#9aa7bd"/>')
        s, h = box(xs[i], 124, cw, [head] + lines, fill="#f4f6fa", what="zaman ")
        b.append(s)
    b.append(text(6, 232, "Dairedeki sayı faz başına commit sayısıdır (toplam 14). Eksen ölçekli değildir; saatler commit zamanıdır.", fill="#555"))
    return figure(svg(720, 244, b, "Geliştirme zaman çizelgesi"),
                  "Şekil 2. Geliştirme zaman çizelgesi: 14 commit, iki gün, beş aşama; fazlar 1-3 aynı öğleden sonra 68 dakikada commit'lendi, denetim ve düzeltme ertesi gün 9 dakikada.")

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
    cols = ["Şimdi", "Sonra", "Belki"]
    ccol = ["#1f3a68", "#4a6fa5", "#7f8c9b"]
    lw, cw, cg = 112, 188, 8
    cx = [lw + 8 + i * (cw + cg) for i in range(3)]
    lanes = [
        ("Test ve ölçüm", {0: ["#1 Playwright dalını birleştir (S)", "#2 Atıf eval betiği kalıcı (M)", "#3 Entegrasyon testleri (M)"], 1: ["#8 Hibrit-vektör, yeni soru seti (M)"]}),
        ("Güvenlik", {0: ["#4 pickle yerine JSON/npz (S)", "#5 symlink atla, fsmonitor kapat (S)"], 1: ["#13 İndeks adı + atomik yazım (M)"]}),
        ("Doğruluk (parçalama, atıf)", {0: ["#6 splitlines ve md çit düzeltmesi (S)"]}),
        ("Performans", {1: ["#9-10 Önbellek + embed hızı (S/M)"], 2: ["#16 Incremental indexing (M)"]}),
        ("Bakım ve belge", {0: ["#7 baslat/durdur eşleşmesi (S)"], 1: ["#11, 12, 14 embed_fn, hata yönetimi, ruff/mypy (S/M)"]}),
        ("Erişim ve kapsam (v2)", {2: ["#15 Cross-encoder rerank (L)", "#17 tree-sitter JS/C# (L)", "#18 Çağrı grafiği (L)"]}),
    ]
    y = 8
    for i, c in enumerate(cols):
        b.append(f'<rect x="{cx[i]}" y="{y}" width="{cw}" height="24" rx="4" fill="{ccol[i]}"/>')
        b.append(text(cx[i] + cw / 2, y + 16, c, bold=True, anchor="middle", fill="#fff"))
    y = 40
    for li, (lane, cells) in enumerate(lanes):
        # satır yüksekliği
        heights = {}
        for ci, items in cells.items():
            hs = [len(wrap(t, cw - 12)) * 15 + 10 for t in items]
            heights[ci] = sum(hs) + 6 * (len(hs) - 1)
        rh = max(heights.values()) + 12
        b.append(f'<rect x="4" y="{y}" width="712" height="{rh}" rx="4" fill="{"#f4f6fa" if li%2==0 else "#fff"}" stroke="#d4d9e0"/>')
        for lns, ly in zip(wrap(lane, lw - 10, True), range(y + 20, y + 200, 15)):
            b.append(text(10, ly, lns, bold=True, fill="#1f3a68"))
        for ci, items in cells.items():
            yy = y + 6
            for t in items:
                ls = wrap(t, cw - 12)
                s, h = box(cx[ci], yy, cw, ls, fill="#fff", stroke=ccol[ci], head=False, what="yol ")
                b.append(s); yy += h + 6
        y += rh + 4
    b.append(text(8, y + 14, "Etiket: #n yol haritası madde numarası; (S/M/L) efor. Madde 1-7 Şimdi, 8-14 Sonra, 15-18 Belki.", fill="#555"))
    return figure(svg(720, y + 22, b, "Yol haritası"),
                  "Şekil 3. Yol haritası (Şimdi / Sonra / Belki), alana göre. Bağımlılıklar (önce → sonra): #2 → #8, #8 → #15, #13 → #16, #3 → #4, #3 → #9, #1 → #3.")

DIAGRAMS = {"architecture": diagram_architecture, "timeline": diagram_timeline, "roadmap": diagram_roadmap}

def replace_specs(md):
    def r(m):
        t = re.search(r"^type:\s*(\w+)", m.group(1), re.M).group(1)
        return DIAGRAMS[t]()
    return re.sub(r"```diagram-spec\n(.*?)```", r, md, flags=re.S)

SUMMARY = """## Yönetici özeti

Kod Repo Asistanı, yerel bir Git reposundaki Python ve Markdown dosyalarını sembol bazlı parçalayıp BM25 + `BAAI/bge-m3` hibrit aramayla getiren ve yerel LLM'le `dosya:satır` atıflı Türkçe cevap üreten, tamamen yerel çalışan bir RAG projesidir. Rapor 14 commit'lik (2026-11-20 ve 2026-11-21) depoyu, 21 Kasım 2026 tarihli çok boyutlu denetimi ve denetim sonrası düzeltmeleri kapsar.

### Beş temel sayı

| Ölçü | Değer | Kaynak |
|---|---|---|
| Kod ve test | 1789 satır Python; 54 test geçti (1.49 sn) | `facts.md`; `uv run pytest -q` |
| Retrieval (ana set, 59 soru) | hybrid hit@5 0.92, MRR@10 0.796 | `eval/results.md` |
| RRF ayarı (ayrı 36 soruluk set) | skor 0.7355 → 0.7880 (+0.0526) | `eval/tuning_results.md` |
| Denetim bulguları | 29 bulgu: 0 critical, 3 high, 13 medium, 13 low; 3 high kapatıldı | `denetim/DENETIM-2026-11-21.md` |
| Geçersiz atıf oranı | %21,9 → %0 (14 cevap; oturum ölçümü, depoda doğrulanmadı) | `facts.md` |

### Genel puan

Genel puan 6.9/10'dur (değerlendirme): denetimin boyut puanlarından türetilen ağırlıklı toplam, hesap bölüm 06'dadır. Denetim sonrası düzeltmeler için yazarın yargısı 7.2/10'dur; bu rakam yeniden denetimle doğrulanmamıştır ve genel puan olarak kullanılmaz.

### En büyük 3 risk

1. **Hibritin üstünlüğü kanıtsız.** Vektöre göre hit@5 farkı 1 iyi / 0 kötü / 58 aynı, RR farkı +0.0014 (M9); fark gürültü düzeyindedir.
2. **Üretim kalitesi kalıcı ölçülmüyor.** Atıf iyileşmesi yalnız oturum ölçümüdür; depoda ölçüm betiği yok (M8).
3. **Test güvencesi eksik.** Denetim anında kapsama %59, `cli`, `pipeline`, `vector_index` %0 (M10); `pickle.load` (M1) ve sembolik bağlantılar (M2) açık.

### Sonraki adım

Yol haritasının ilk üç işi (bölüm 09): `denetim/playwright` dalını birleştirmek, atıf ölçümünü `eval/` içinde kalıcı betiğe çevirmek, `pipeline`/`cli`/`vector_index` için entegrasyon testi yazmak.
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
