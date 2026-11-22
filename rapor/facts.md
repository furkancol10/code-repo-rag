# Gerçekler (facts.md) — KodRepoAsistani

Biçim: `- gerçek: değer (kaynak: dosya | komut)`. Yollar proje köküne göredir.

## Depo istatistikleri
- Git'e takipli dosya sayısı: 38 (kaynak: `git ls-files | wc -l`)
- Commit sayısı: 14 (kaynak: `git rev-list --count HEAD`)
- İlk commit: 2500377, 2026-11-20, "plan" (kaynak: `git log --date=short`)
- Son commit: 1f2b19a, 2026-11-21, "fix: kod içinde atıf/boşluk dönüşümü yok, blok aralığı, önbellek anahtarı (Neon incelemesi)" (kaynak: `git log --date=short`)
- `src/`: Python, 13 dosya, 897 satır (kaynak: `find src -name '*.py'` + `cat | wc -l`)
- `eval/`: Python, 2 dosya, 252 satır (`eval/run_eval.py`, `eval/tune_rrf.py`) (kaynak: aynı komut)
- `tests/`: Python, 9 dosya (`__init__.py` dahil), 579 satır (kaynak: aynı komut)
- `app.py`: Python, 61 satır (kaynak: `wc -l app.py`)
- Python toplamı (src + eval + tests + app.py): 1789 satır (hesap: 897+252+579+61)
- `eval/questions.json`: 765 satır, `eval/tuning.json`: 445 satır (kaynak: `wc -l`)
- Gömme modeli: BAAI/bge-m3 (kaynak: `src/config.py:9`)

## Test
- Test sayısı: 54 geçti, 1.49 sn. Komut: `uv run pytest -q`; çıktı satırı: `54 passed in 1.49s` (kaynak: komut, 2026-11-21)
- Denetim anındaki sayı: 36/36 geçti, "36 passed in 0.85s", kapsama %59 (750 ifade, 309 kaçırılan) (kaynak: `denetim/DENETIM-2026-11-21.md`, "Mevcut test paketi")
- Kapsama (denetim anı): %100 `hybrid`, `chunk`, `config`; `chunk_py` %95, `chunk_md` %95, `bm25_index` %94, `scanner` %91, `generator` %78, `eval/run_eval` %51, `embedder` %25; %0 `cli`, `pipeline`, `vector_index`, `eval/tune_rrf` (kaynak: `denetim/DENETIM-2026-11-21.md`)

## Sürümler
- Python (uv ortamı): 3.12.16 (kaynak: `uv run python -V`); gereksinim `>=3.12` (kaynak: `pyproject.toml`, `uv.lock`)
- sentence-transformers: 6.3.0 (kaynak: `uv.lock`)
- torch: 2.15.0+cu132 (kaynak: `uv.lock`)
- numpy: 2.5.5 (kaynak: `uv.lock`)
- rank-bm25: 0.2.2 (kaynak: `uv.lock`)
- streamlit: 1.67.0 (kaynak: `uv.lock`)
- ollama (Python istemcisi): 0.6.3 (kaynak: `uv.lock`)
- Yerel Ollama modeli: qwen3.5:4b, 3.3 GB (kaynak: `ollama list`)

## Eval sonuçları — `eval/results.md` (main set, 59 soru)
- Soru dağılımı: httpx 30 (15 name, 15 conceptual), kisiselnotarama 29 (15 name, 14 conceptual) (kaynak: `eval/results.md`)
- bm25, tümü: hit@1 0.61, hit@5 0.73, MRR@10 0.674 (kaynak: `eval/results.md`)
- vector, tümü: hit@1 0.71, hit@5 0.90, MRR@10 0.794 (kaynak: `eval/results.md`)
- hybrid, tümü: hit@1 0.71, hit@5 0.92, MRR@10 0.796 (kaynak: `eval/results.md`)
- name soruları (n=30): bm25 MRR 0.944, vector 0.939, hybrid 0.944; hit@5 üçünde 1.00 (kaynak: `eval/results.md`)
- conceptual soruları (n=29): bm25 hit@5 0.45 / MRR 0.395; vector 0.79 / 0.645; hybrid 0.83 / 0.642 (kaynak: `eval/results.md`)
- Hybrid ilk 10'da bulamadığı sorular: kna-23, kna-29, hx-17 (kaynak: `eval/results.md`)
- Hibrit vs vektör eşleştirilmiş karşılaştırma: hit@5 1 iyi / 0 kötü / 58 aynı, RR farkı ort. +0.0014 (n=59); denetim "fark gürültü düzeyinde" yorumunu öneriyor (kaynak: `denetim/DENETIM-2026-11-21.md`, M9)

## Tuning — `eval/tuning_results.md` (36 soru)
- Tarama: 36 kombinasyon (w_bm25 ∈ {0.3, 0.5, 0.7, 1.0} × k ∈ {10, 30, 60} × candidates ∈ {20, 30, 50}); w_vec=1 (kaynak: `eval/tuning_results.md`, tablo satır sayımı)
- Skor = (name MRR@10 + conceptual MRR@10) / 2 (kaynak: `eval/tuning_results.md`)
- Seçilen: w_bm25=0.3, k=30, candidates=20, skor 0.7880 (name MRR 0.975, conceptual MRR 0.601, conceptual hit@5 0.81) (kaynak: `eval/tuning_results.md`)
- Varsayılan: w_bm25=1.0, k=60, candidates=30, skor 0.7355; fark +0.0526 (kaynak: `eval/tuning_results.md`)
- Yalnız vektör referansı: name MRR 0.900, conceptual MRR 0.604, skor 0.7521 (kaynak: `eval/tuning_results.md`)
- Ana set tuning taramasında kullanılmadı (kaynak: `eval/tuning_results.md`)

## Denetim — `denetim/DENETIM-2026-11-21.md` (2026-11-21, tam mod, kapsam commit 756e4df)
- Puan, mevcut test paketi: 6/10 (kaynak: `denetim/DENETIM-2026-11-21.md`)
- Puan, hatalar (code-review): 7/10 (aynı)
- Puan, güvenlik: 8/10 (aynı)
- Puan, bağımsız çapraz inceleme (Neon): hata 6/10, güvenlik 4/10 (aynı)
- Puan, kod kalitesi/mimari: 7.5/10 (aynı)
- Puan, E2E (Playwright): 7/10 (aynı)
- Puan, erişilebilirlik: 7/10 (aynı)
- Puan, performans: 7.5/10 (aynı)
- Puan, LLM/RAG cevap kalitesi: 6.5/10 (aynı)
- Test stratejisi (senior-qa): puanlanmadı, atlandı (React/Next.js'e özgü) (aynı)
- Bulgu sayıları (düzeltme listesi): critical 0, high 3 (H1-H3), medium 13 (M1-M13), low 13 (L1-L13) (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 2; satır sayımı)
- High bulgular: H1 prompt injection / kod bloğu taşması; H2 zayıf atıf uyumu; H3 arama modunda bile LLM çağrısı (aynı)
- Neon'un 8 bulgusu; 1 critical (pickle) doğrulamada düştü: doğrulayıcı low (M1) (aynı, bölüm 3 ve M1)
- Doğrulama etiketleri (örnekler): "doğrulandı" (M2, M3, L4), "ölçüldü" (M6, M9, M10, L7-L9), "doğrulanmadı" (H3, M5, M7, M11, M12, L5, L6, L10, L11), "iki model" (M4, L1, L3), "araç" (M13, L12, L13) (aynı)
- Araç/model: doğrulayıcı 2 × sonnet/low; hakem gpt-oss-120b-medium (2 çağrı); toplam Gem çağrısı 4/12 (aynı, bölüm 5)
- Denetim bulguları: H2 36 cevabın %25'inde geçersiz atıf (atıfların 21/96'sı), %42 atıfsız, beklenen dosya hit'lerin %92'sinde ama cevapların %33'ünde atıflı (aynı, H2)
- Tuzak sorular 6/6 doğru reddedildi; gerçek sorularda yanlış red 0/36 (aynı)
- pip-audit: "No known vulnerabilities found"; torch+cu132 denetim dışı (aynı)
- Eval deterministik: 3 tekrar ve `eval/results.md` aynı md5 (aynı)

## Oturum ölçümleri (oturum ölçümü; depoda doğrulanmadı)
- Denetim sonrası düzeltmeler (oturum ölçümü): ba50a40 (`app.py`: "LLM cevabı üret" onay kutusu, indeks önbelleği, Kaynaklar h2); b010685 (generator: çit taşması/enjeksiyon, strip_images, fix_citations, ters aralık); 1f2b19a (Neon incelemesi sonrası: kod içinde atıf/boşluk dönüşümü yok, blok aralığı n. hit'e göre, önbellek anahtarı indeks adı içerir). Commit mesajları `git log` ile de görülüyor.
- Düzeltmelerin geri alma doğrulaması (oturum ölçümü): her düzeltme için ayrı ajan geri aldı; ba50a40: 3 test kırıldı; b010685: 4 düzeltme tek tek kapatıldı, her biri ≥1 test kırdı; 1f2b19a: 6 test kırıldı
- Atıf kalitesi önce/sonra (oturum ölçümü; 12 soru + 2 tuzak, 14 cevap, 1 tekrar, temperature 0): geçersiz atıf %21,9 → %0 (fix_citations sonrası); atıfsız cevap %35,7 → %21,4; beklenen dosyaya atıf %36,4 → %72,7
- Denetim öncesi cevap kalitesi (oturum ölçümü; 12 soru × 3 tekrar): geçersiz atıf 21/96 (%22), atıfsız 15/36, beklenen dosyaya atıf 12/36; tuzak sorular 6/6 reddedildi
- Performans (oturum ölçümü; httpx, 862 parça): sıcak arama medyanı bm25 0.3 ms, vector 21.7 ms, hybrid 23.9 ms (p95 37 ms); model yükleme 7.4 sn; indeksleme ~19 sn (embed 11 sn); RSS tepe ~4.1 GB; VRAM tepe 1.67 GB (aynı değerler `denetim/DENETIM-2026-11-21.md` Performans bölümünde de var)
- E2E (oturum ölçümü): Playwright 8 test, 8/8 geçti, `denetim/playwright` dalı (commit 9b57b5d), master'a birleştirilmedi (denetim raporunda da yazıyor) (dal `denetim/playwright` ve commit 9b57b5d depoda mevcut: `git branch -a`, `git cat-file -t`)
- Ağırlıklı RRF seçimi tuning setiyle (oturum ölçümü): w_bm25=0.3, w_vec=1, k=30, candidates=20; skor 0.7880 vs varsayılan 0.7355 (`eval/tuning_results.md` ile uyumlu)
- GitHub (oturum ölçümü): public repo `code-repo-rag`

## Doğrulanmadı
- Atıf önce/sonra sayıları (%21,9 → %0 vb.): depoda ölçüm çıktısı yok; yalnız oturum ölçümü. Doğrulamak için aynı 14 soruyla cevap üretim betiği yeniden çalıştırılmalı (M8: bu betik `eval/` içinde kalıcı değil).
- Geri alma testlerinde kırılan test sayıları (3, 4 düzeltme, 6): oturum ölçümü; her düzeltme geri alınıp `uv run pytest` ile tekrarlanarak doğrulanabilir.
- GitHub reposunun public olması ve adı: ağdan kontrol edilmedi.
- Performans değerleri bu çalışmada yeniden ölçülmedi.
- Denetim sonrası 54 testin 36'dan artış dökümü: commit bazında ayrıştırılmadı.
