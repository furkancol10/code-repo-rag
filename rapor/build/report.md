## Yönetici özeti

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


## 01. Proje tanımı ve kapsam

Kod Repo Asistanı, yerel bir Git reposunu sembol bazlı parçalayıp hibrit arama ve atıflı Türkçe soru-cevap sunan, 1993 satırlık Python projesidir (hesap: 946+252+734+61, kaynak: `rapor/facts.md`).

### Problem ve çözüm

Kod depolarında soru sormak iki farklı arama türü gerektirir: isim sorguları (`release_gpu ne yapar`) ve kavramsal sorgular. Yalnız anahtar kelime araması kavramsal sorularda zayıf kalır: conceptual hit@5 bm25 için 0.45, vektör için 0.79 (kaynak: `eval/results.md`).

Çözüm, Python ve Markdown dosyalarını sınıf, metot, fonksiyon ve başlık sınırlarından parçalamaktır. BM25 ve `BAAI/bge-m3` vektör sonuçları ağırlıklı RRF ile birleştirilir. Yerel LLM (`qwen3.5:4b`), yalnız getirilen parçalara dayanarak dosya yolu ve satır aralığı atıflı cevap üretir (kaynak: `README.md`, `src/config.py`).

### Hedef kullanıcı

Kendi yerel kod deposunda, buluta kod göndermeden arama yapmak isteyen geliştirici. Her şey yerelde çalışır: gömme modeli sentence-transformers ile, LLM Ollama ile (kaynak: `src/config.py`, `src/embedder.py`).

### Kapsam

| Kapsam içi | Kapsam dışı |
|---|---|
| Python (`ast` ile) ve Markdown (başlığa göre) | JS, C# ve diğer diller (v2'ye bırakıldı; tree-sitter gerekir, kaynak: `plan.md`) |
| CLI: `index`, `search`, `ask`, `eval` | Çok kullanıcılı veya sunucu dağıtımı |
| Streamlit arayüzü (`app.py`) | Sürekli (artımlı) indeks güncelleme: doğrulanmadı, `src/pipeline.py` her seferinde tam kurar |
| BM25, vektör ve hibrit mod; eval ve RRF ayarı | Test dosyalarının indekslenmesi (`tests/`, `test_*.py` dışlanır, kaynak: `src/config.py`) |
| Atıf doğrulama ve düzeltme (`src/generator.py`) | Gömme modelinin ince ayarı |

### Çıktılar

| Çıktı | Konum | İçerik |
|---|---|---|
| Kütüphane ve CLI | `src/` | 13 Python dosyası, 946 satır: tarama, parçalama, indeks, hibrit arama, üretim |
| Arayüz | `app.py` | Streamlit sayfası, 61 satır |
| Değerlendirme | `eval/` | `run_eval.py`, `tune_rrf.py`; 59 soruluk ana set, 36 soruluk tuning seti |
| Eval sonuçları | `eval/results.md`, `eval/tuning_results.md` | Mod bazlı hit@1, hit@5, MRR@10; 36 kombinasyonlu ızgara |
| Test paketi | `tests/` | 10 dosya (`__init__.py` dahil), 734 satır; 65 test geçti |
| Denetim raporu | `denetim/DENETIM-2026-11-21.md` | Çok boyutlu denetim, bulgu listesi (3 high, 13 medium, 13 low) |
| E2E testleri | `e2e/app.spec.ts`, `playwright.config.ts` | Playwright, 8 `test(`; master'da (merge 77b5f78) |
| Plan ve kullanım | `plan.md`, `README.md` | Amaç, kapsam, kurulum, eval tablosu |

### Temel sayılar

| Ölçü | Değer | Kaynak |
|---|---|---|
| Git'e takipli dosya | 56 (rapor/ dahil) | `git ls-files \| wc -l` |
| Commit | 25 (2026-11-20 ile 2026-11-22) | `git rev-list --count HEAD` |
| `src/` | 13 dosya, 946 satır | `facts.md` |
| `eval/` | 2 dosya, 252 satır | `facts.md` |
| `tests/` | 10 dosya, 734 satır | `facts.md` |
| `app.py` | 61 satır | `wc -l app.py` |
| Python toplamı | 1993 satır | hesap: 946+252+734+61 |
| Test | 65 geçti, 1.12 sn | `uv run pytest -q` |
| Eval soru sayısı | 59 ana + 36 tuning | `eval/results.md`, `eval/tuning_results.md` |
| Hybrid, ana set | hit@5 0.92, MRR@10 0.796 | `eval/results.md` |

Not: 1.12 sn ve 65 test 2026-11-22 ölçümüdür; denetim anında test sayısı 36'ydı (kaynak: `denetim/DENETIM-2026-11-21.md`).


## 02. Mimari

Sistem 4 katmandan oluşur: tarama ve parçalama, indeksleme, arama, üretim; 13 Python dosyası (12 modül ve `__init__.py`) `src/` altındadır (kaynak: `src/`, `rapor/facts.md`). Modüller birbirine `config.py` üzerinden bağlanır; ayrı projelerden import yoktur (kaynak: `plan.md`).

### Uçtan uca veri akışı

İndeksleme: `scan_repo` dosyaları listeler, `chunk_file` her dosyayı `CodeChunk` listesine böler, `embed_passages` vektör üretir; `NumpyIndex` ve `BM25Index` aynı isimle kurulur (kaynak: `src/pipeline.py`). İndeks adı gömme modeli ve repo bilgisinden türetilir (`index_name`, `src/vector_index.py`).

Sorgu: `hybrid_search` BM25 ve vektör listelerinden 20 aday alır, ağırlıklı RRF ile birleştirir (w_bm25=0.3, w_vec=1, k=30). `ask` komutu ilk 5 parçayı `generator.answer` ile LLM'e verir; cevaptaki atıflar `fix_citations` ile getirilen parçalara göre düzeltilir (kaynak: `src/config.py`, `src/hybrid.py`, `src/generator.py`).

<figure>
<svg viewBox="0 0 720 424" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kod Repo Asistanı veri akışı" font-family="DejaVu Sans, sans-serif" style="max-width:100%;height:auto"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs><rect x="4" y="26" width="126" height="372" rx="8" fill="#eef2f8" stroke="#9aa7bd" stroke-width="1"/>
<text x="12" y="44" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Giriş</text>
<rect x="140" y="26" width="286" height="372" rx="8" fill="#eef6ee" stroke="#9aa7bd" stroke-width="1"/>
<text x="148" y="44" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">İndeksleme (src/pipeline.py)</text>
<rect x="438" y="26" width="122" height="372" rx="8" fill="#fbf3e6" stroke="#9aa7bd" stroke-width="1"/>
<text x="446" y="44" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Arama</text>
<rect x="572" y="26" width="144" height="372" rx="8" fill="#f6eef6" stroke="#9aa7bd" stroke-width="1"/>
<text x="580" y="44" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Üretim</text>
<rect x="10" y="56" width="114" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="67.0" y="74" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">Yerel repo</text>
<text x="67.0" y="89" font-size="12" text-anchor="middle" fill="#1a1a1a">(.py, .md)</text>
<rect x="10" y="160" width="114" height="57" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="67.0" y="178" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">src/cli.py</text>
<text x="67.0" y="193" font-size="12" text-anchor="middle" fill="#1a1a1a">index, search,</text>
<text x="67.0" y="208" font-size="12" text-anchor="middle" fill="#1a1a1a">ask, eval</text>
<rect x="10" y="264" width="114" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="67.0" y="282" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">app.py</text>
<text x="67.0" y="297" font-size="12" text-anchor="middle" fill="#1a1a1a">(Streamlit)</text>
<rect x="148" y="62" width="270" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="283.0" y="80" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">scanner.py</text>
<text x="283.0" y="95" font-size="12" text-anchor="middle" fill="#1a1a1a">dosya listesi</text>
<rect x="148" y="140" width="270" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="283.0" y="158" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">chunk.py, chunk_py.py,</text>
<text x="283.0" y="173" font-size="12" text-anchor="middle" fill="#1a1a1a">chunk_md.py: CodeChunk</text>
<rect x="148" y="228" width="130" height="57" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="213.0" y="246" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">embedder.py</text>
<text x="213.0" y="261" font-size="12" text-anchor="middle" fill="#1a1a1a">bge-m3</text>
<text x="213.0" y="276" font-size="12" text-anchor="middle" fill="#1a1a1a">vektörleri</text>
<rect x="288" y="228" width="130" height="58" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="353.0" y="246" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">bm25_index.py</text>
<text x="353.0" y="261" font-size="12" text-anchor="middle" fill="#1a1a1a">bm25.json</text>
<rect x="148" y="326" width="130" height="57" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="213.0" y="344" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">vector_index.py</text>
<text x="213.0" y="359" font-size="12" text-anchor="middle" fill="#1a1a1a">vecs.npy +</text>
<text x="213.0" y="374" font-size="12" text-anchor="middle" fill="#1a1a1a">chunks.json</text>
<rect x="444" y="205" width="110" height="72" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="499.0" y="223" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">hybrid.py</text>
<text x="499.0" y="238" font-size="12" text-anchor="middle" fill="#1a1a1a">ağırlıklı RRF</text>
<text x="499.0" y="253" font-size="12" text-anchor="middle" fill="#1a1a1a">20+20 aday</text>
<text x="499.0" y="268" font-size="12" text-anchor="middle" fill="#1a1a1a">çıktı: ilk 5</text>
<rect x="578" y="212" width="132" height="57" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="644.0" y="230" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">generator.py</text>
<text x="644.0" y="245" font-size="12" text-anchor="middle" fill="#1a1a1a">bağlam kurma,</text>
<text x="644.0" y="260" font-size="12" text-anchor="middle" fill="#1a1a1a">atıf düzeltme</text>
<rect x="578" y="336" width="132" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="644.0" y="354" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">Ollama</text>
<text x="644.0" y="369" font-size="12" text-anchor="middle" fill="#1a1a1a">qwen3.5:4b</text>
<path d="M124,86 L148,86" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<path d="M283,110 L283,140" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="290" y="129" font-size="12" text-anchor="start" fill="#1a1a1a">yollar</text>
<path d="M213,190 L213,228" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="220" y="214" font-size="12" text-anchor="start" fill="#1a1a1a">parça metni</text>
<path d="M353,190 L353,228" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="360" y="214" font-size="12" text-anchor="start" fill="#1a1a1a">token'lar</text>
<path d="M213,286 L213,326" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="220" y="311" font-size="12" text-anchor="start" fill="#1a1a1a">vektörler</text>
<path d="M418,257 L444,257" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<path d="M278,355 L500,355 L500,281" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<path d="M124,191 L134,191 L134,412 L534,412 L534,281" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<path d="M124,287 L134,287" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="150" y="407" font-size="12" text-anchor="start" fill="#1a1a1a">sorgu, mod (cli ve app)</text>
<text x="290" y="349" font-size="12" text-anchor="start" fill="#1a1a1a">20 aday</text>
<path d="M554,243 L578,243" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<path d="M612,274 L612,336" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="618" y="300" font-size="12" text-anchor="start" fill="#1a1a1a">prompt</text>
<path d="M676,336 L676,274" fill="none" stroke="#555" stroke-width="1.4" marker-end="url(#ah)"/>
<text x="670" y="322" font-size="12" text-anchor="end" fill="#1a1a1a">cevap</text></svg>
<figcaption>Şekil 1. Veri akışı: giriş, indeksleme, arama, üretim (soldan sağa). Yollar src/ modül adlarıdır; BM25 ve vektör aday listeleri hybrid.py'de birleşir.</figcaption>
</figure>

### Bileşenler

| Bileşen | Dosya | Sorumluluk | Bağımlılık |
|---|---|---|---|
| Ayarlar | `src/config.py` | Yollar, model adları, RRF parametreleri, dışlama kalıpları | yok |
| Tarayıcı | `src/scanner.py` | Repo dosyalarını listeler; dışlama, boyut sınırı (300 000 bayt), sembolik bağlantı bileşeni olan veya kök dışına çıkan yolları atlar | `config`, `git` |
| Parça modeli | `src/chunk.py` | `CodeChunk`, dile göre yönlendirme, gömme metni | `chunk_py`, `chunk_md` |
| Python parçalayıcı | `src/chunk_py.py` | `ast` ile sınıf, metot, fonksiyon parçaları; en çok 80 satır | `ast`, `config` |
| Markdown parçalayıcı | `src/chunk_md.py` | Başlığa göre bölme | `chunk` |
| Gömme | `src/embedder.py` | bge-m3 yükleme, cihaz seçimi (GPU/CPU), GPU bırakma | sentence-transformers, torch |
| Vektör indeksi | `src/vector_index.py` | `vecs.npy` + `chunks.json`; kosinüs arama (`argpartition`); bellek önbelleği, disk değişimini (mtime, inode, boyut) izler; geçici dizinle atomik yazma | numpy |
| BM25 indeksi | `src/bm25_index.py` | Kod tokenizer'ı (büyük/küçük harf ve alt çizgi bölme), BM25 arama; indeks `bm25.json` (JSON) olarak saklanır | rank-bm25, json |
| Hibrit arama | `src/hybrid.py` | RRF ve mod seçimi (`bm25`, `vector`, `hybrid`) | `embedder`, indeksler |
| Üretici | `src/generator.py` | Bağlam kurma, çit güvenliği, atıf denetimi ve düzeltme | ollama |
| Hat | `src/pipeline.py` | Tara, parçala, embed et, iki indeksi kur ve yükle | yukarıdakiler |
| CLI | `src/cli.py` | `index`, `search`, `ask`, `eval` | `pipeline`, `hybrid`, `generator` |
| Arayüz | `app.py` | Streamlit; indeks önbelleği, isteğe bağlı LLM cevabı | `pipeline`, `hybrid`, `generator` |
| Eval | `eval/run_eval.py`, `eval/tune_rrf.py` | Mod karşılaştırması; RRF ızgara taraması | `hybrid`, `pipeline` |

### Temel tasarım kararları

| Karar | Gerekçe | Ödünleşim |
|---|---|---|
| `ast` ile sembol bazlı parçalama | Satır aralığı ve sembol adı atıf için gerekli (kaynak: `plan.md`) | Yalnız Python ve Markdown; diğer diller kapsam dışı |
| BM25 + vektör, RRF birleştirme | İsim sorgularında BM25, kavramsal sorgularda vektör güçlü | Hibritin vektöre üstünlüğü gürültü düzeyinde: hit@5 1 iyi / 0 kötü / 58 aynı (kaynak: `denetim/DENETIM-2026-11-21.md`, M9) |
| Ağırlıklı RRF, ayrı tuning setiyle seçim | Ana sette aşırı uyum riskini azaltır; skor 0.7880, varsayılan 0.7355 (kaynak: `eval/tuning_results.md`) | Tuning seti 36 soru; küçük örneklem |
| Tamamen yerel çalışma (bge-m3, Ollama) | Kod dışarı çıkmaz | Yaklaşık 4.1 GB RSS tepe, 1.67 GB VRAM tepe (oturum ölçümü, kaynak: `facts.md`); 4 milyar parametreli model zayıf atıf uyumu verdi (H2) |
| Atıf doğrulama kodda, prompt'ta değil | LLM atıfları denetim öncesi 21/96 geçersizdi (kaynak: `denetim/DENETIM-2026-11-21.md`, H2) | `fix_citations` yalnız getirilen parçalara göre düzeltir; atıfsız cevap kalabilir |
| Atomik indeks yazma (`.tmp` sonra `rename`) | Hata eski indeksi bozmaz (kaynak: `src/vector_index.py`) | İki indeksin birlikte atomikliği yok: sabit `.tmp`/`.old` dizinleri çakışabilir (L2) |
| BM25 indeksi JSON ile (önceden `pickle`) | Güvenilmeyen dosya yüklenirken kod çalıştırma riski yok (M1, 132f7d8) | Yüklemede BM25 yeniden kurulur; yükleme süresi ölçülmedi |
| Vektör indeksi bellek önbelleği | Her sorguda diskten okumayı önler (M6, 132f7d8, 8fb632d) | Önbellek yalnız tek süreçte geçerli; süre kazancı yeniden ölçülmedi |
| Modüller kopyalanıp uyarlandı, ortak paket yok | Projeler bağımsız kalır (kaynak: `plan.md`) | Kod tekrarı |


## 03. Teknolojiler

Proje Python tarafında çalışma zamanı bağımlılıkları ve pytest ile, E2E için ayrıca Node tarafında Playwright ile kullanır; Python sürümleri `uv.lock` ile sabitlenmiştir (kaynak: `pyproject.toml`, `uv.lock`). Python ortamı 3.12.16'dır (kaynak: `uv run python -V`).

### Çalışma zamanı

| Teknoloji | Sürüm (lockfile) | Rolü | Neden seçildi |
|---|---|---|---|
| Python | 3.12.16 (`>=3.12`) | Dil ve `ast` modülü | `ast` kod sınırlarını verir; ek bağımlılık gerekmez |
| sentence-transformers | 6.3.0 | bge-m3 gömme modelini çalıştırır | Yerel, tek satırda model yükleme; çok dilli model |
| BAAI/bge-m3 | model, lockfile dışı (`src/config.py:9`) | Parça ve sorgu vektörleri | Türkçe sorgu ve İngilizce kod için çok dilli; KisiselNotArama ile aynı ayar (kaynak: `plan.md`) |
| torch | 2.15.0+cu132 | GPU/CPU tensör altyapısı | sentence-transformers gerektirir; `cu132` indeksi `pyproject.toml`'da |
| numpy | 2.5.5 | Vektör depolama ve kosinüs arama | Binlerce parça için ayrı vektör veritabanı gereksiz |
| rank-bm25 | 0.2.2 | BM25 (`BM25Okapi`) | Küçük, bağımlılıksız sözcüksel arama |
| ollama (Python istemcisi) | 0.6.3 | Yerel LLM çağrısı | Veri dışarı çıkmaz |
| Ollama modeli qwen3.5:4b | 3.3 GB (kaynak: `ollama list`) | Atıflı cevap üretimi | Küçük, yerelde çalışır |
| streamlit | 1.67.0 | Web arayüzü (`app.py`) | Hızlı arayüz; denetimde E2E ile denendi |

### Geliştirme ve test

| Teknoloji | Sürüm (lockfile) | Rolü | Neden seçildi |
|---|---|---|---|
| uv | doğrulanmadı (`uv --version` ile doğrulanır) | Bağımlılık ve ortam yönetimi | Tek komutla `uv sync`, `uv.lock` ile tekrarlanabilirlik |
| pytest | 9.2.0 | Test çalıştırıcı (`uv run pytest -q`) | Standart, ek ayar yok (`pythonpath`, `testpaths` `pyproject.toml`'da) |
| Playwright (`@playwright/test`) | `^1.65.1` (kaynak: `package.json`; kesin sürüm `package-lock.json`) | E2E arayüz testi (`e2e/app.spec.ts`, 8 `test(`) | Streamlit arayüzünü gerçek tarayıcıda dener; master'da (merge 77b5f78) |

### Standart kütüphane

`argparse`, `ast`, `json`, `hashlib`, `os`, `subprocess` (git çağrısı), `shutil`, `re`, `fnmatch` kullanılır (kaynak: `grep -n "^import" src/*.py`). BM25 indeksi artık `pickle` yerine JSON saklar (`src/bm25_index.py`, 132f7d8). Linter veya tip denetleyici `pyproject.toml`'da tanımlı değildir.


## 04. Geliştirme süreci

Proje 25 commit'te, üç takvim gününde (2026-11-20, 21 ve 22) yedi aşamada geliştirildi (kaynak: `git log --format='%h %ad %s' --date=short`; `facts.md`: commit sayısı 25). İlk commit 2500377 ("plan"), son commit 8fb632d'dir. Günlere dağılım: 10, 6 ve 9 commit.

### Aşamalar

| Aşama | Dönem | Çıktı | Kilit karar |
|---|---|---|---|
| 0. Plan | 20 Kas 15:33 (1 commit: 2500377) | Plan commit'i | Yerel, bge-m3 + BM25 + Ollama kurgusu |
| 1. Faz 1: iskelet | 20 Kas 15:34-15:35 (2: 893f3c6, b980049) | `config`, `scanner`, `chunk`, `chunk_md`, `embedder`, `vector_index`; dondurulmuş `eval/questions.json` (59 soru) | Eval seti kod yazılmadan önce dondurulur, ayar için ayrı set kullanılır (`eval/README.md`) |
| 2. Faz 2: arama | 20 Kas 15:38 (1: 6dff6cb) | Python `ast` parçalama, kod BM25 tokenizer/indeksi, RRF hibrit arama + testler | Kod için özel tokenizer; sıralı birleştirme (RRF) |
| 3. Faz 3 ve ayar | 20 Kas 15:41-16:41 (6: 4fc30b8, 48ac9bc, 93dd096, dccbc70, b74b758, 756e4df) | Pipeline, generator, CLI, eval, `app.py`, README; tuning seti 36 soru; ağırlıklı RRF; `baslat.sh`/`durdur.sh` | RRF parametreleri yalnız tuning setiyle seçildi, ana sete bakılmadı (`eval/tuning_results.md`) |
| 4. Denetim ve 1. tur düzeltme | 21 Kas 12:52-13:01 (4: 8f35f48, ba50a40, b010685, 1f2b19a) | Denetim raporu; H1, H2, H3 düzeltmeleri; Neon incelemesi sonrası düzeltme | Her düzeltme ayrı commit; Neon çapraz incelemesi (`denetim/DENETIM-2026-11-21.md`) |
| 5. E2E ve belge | 21 Kas 12:35 (9b57b5d, `denetim/playwright` dalı) ve 13:10 (705d05a) | Playwright testleri (`e2e/app.spec.ts`); `eval/README` tuning notu | E2E ayrı dalda yazıldı, 22 Kas'ta merge edildi |
| 6. 2. tur düzeltme | 22 Kas 12:39-12:47 (9: 97df401, 77b5f78, 2edbf3c, 1bee4f4, 132f7d8, 333fd9a, 405bdb7, 5a8f7b9, 8fb632d) | M1 pickle yerine JSON, M2 symlink, M3 form feed, M4/M5 başlat/durdur, M6 önbellek, M9 README; eval sabitleme; Playwright merge (77b5f78) | Neon incelemesi 7 bulgu verdi; doğrulananlar 5a8f7b9 ve 8fb632d ile düzeltildi (oturum ölçümü); eval iki repoyu sabit commit'e bağladı |

### Zaman çizelgesi

<figure>
<svg viewBox="0 0 720 434" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Geliştirme zaman çizelgesi" font-family="DejaVu Sans, sans-serif" style="max-width:100%;height:auto"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs><rect x="4" y="6" width="714" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>
<text x="361.0" y="24" font-size="12" text-anchor="middle" fill="#1f3a68" font-weight="bold">20 Kasım 2026 (10 commit)</text>
<line x1="91.0" y1="74" x2="631.0" y2="74" stroke="#1f3a68" stroke-width="2.5"/>
<circle cx="91.0" cy="74" r="14" fill="#1f3a68"/>
<text x="91.0" y="78" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">1</text>
<line x1="91.0" y1="88" x2="91.0" y2="100" stroke="#9aa7bd"/>
<rect x="6" y="100" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="91.0" y="118" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">0. Plan</text>
<text x="91.0" y="133" font-size="12" text-anchor="middle" fill="#1a1a1a">20 Kas 15:33</text>
<text x="91.0" y="148" font-size="12" text-anchor="middle" fill="#1a1a1a">2500377</text>
<text x="91.0" y="163" font-size="12" text-anchor="middle" fill="#1a1a1a">"plan"</text>
<circle cx="271.0" cy="74" r="14" fill="#1f3a68"/>
<text x="271.0" y="78" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">2</text>
<line x1="271.0" y1="88" x2="271.0" y2="100" stroke="#9aa7bd"/>
<rect x="186" y="100" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="271.0" y="118" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">1. İskelet</text>
<text x="271.0" y="133" font-size="12" text-anchor="middle" fill="#1a1a1a">15:34-15:35</text>
<text x="271.0" y="148" font-size="12" text-anchor="middle" fill="#1a1a1a">b980049: soru</text>
<text x="271.0" y="163" font-size="12" text-anchor="middle" fill="#1a1a1a">seti donduruldu</text>
<circle cx="451.0" cy="74" r="14" fill="#1f3a68"/>
<text x="451.0" y="78" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">1</text>
<line x1="451.0" y1="88" x2="451.0" y2="100" stroke="#9aa7bd"/>
<rect x="366" y="100" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="451.0" y="118" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">2. Arama</text>
<text x="451.0" y="133" font-size="12" text-anchor="middle" fill="#1a1a1a">15:38</text>
<text x="451.0" y="148" font-size="12" text-anchor="middle" fill="#1a1a1a">6dff6cb:</text>
<text x="451.0" y="163" font-size="12" text-anchor="middle" fill="#1a1a1a">hibrit arama</text>
<circle cx="631.0" cy="74" r="14" fill="#1f3a68"/>
<text x="631.0" y="78" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">6</text>
<line x1="631.0" y1="88" x2="631.0" y2="100" stroke="#9aa7bd"/>
<rect x="546" y="100" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="631.0" y="118" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">3. Faz 3 ve ayar</text>
<text x="631.0" y="133" font-size="12" text-anchor="middle" fill="#1a1a1a">15:41-16:41</text>
<text x="631.0" y="148" font-size="12" text-anchor="middle" fill="#1a1a1a">dccbc70:</text>
<text x="631.0" y="163" font-size="12" text-anchor="middle" fill="#1a1a1a">ağırlıklı RRF</text>
<rect x="4" y="209" width="354" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>
<text x="181.0" y="227" font-size="12" text-anchor="middle" fill="#1f3a68" font-weight="bold">21 Kasım 2026 (6 commit)</text>
<rect x="364" y="209" width="174" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>
<text x="451.0" y="227" font-size="12" text-anchor="middle" fill="#1f3a68" font-weight="bold">22 Kasım (9 commit)</text>
<line x1="91.0" y1="277" x2="451.0" y2="277" stroke="#1f3a68" stroke-width="2.5"/>
<circle cx="91.0" cy="277" r="14" fill="#1f3a68"/>
<text x="91.0" y="281" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">4</text>
<line x1="91.0" y1="291" x2="91.0" y2="303" stroke="#9aa7bd"/>
<rect x="6" y="303" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="91.0" y="321" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">4. Denetim, 1. tur</text>
<text x="91.0" y="336" font-size="12" text-anchor="middle" fill="#1a1a1a">21 Kas 12:52-13:01</text>
<text x="91.0" y="351" font-size="12" text-anchor="middle" fill="#1a1a1a">1f2b19a: Neon</text>
<text x="91.0" y="366" font-size="12" text-anchor="middle" fill="#1a1a1a">düzeltmeleri</text>
<circle cx="271.0" cy="277" r="14" fill="#1f3a68"/>
<text x="271.0" y="281" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">2</text>
<line x1="271.0" y1="291" x2="271.0" y2="303" stroke="#9aa7bd"/>
<rect x="186" y="303" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="271.0" y="321" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">5. E2E ve belge</text>
<text x="271.0" y="336" font-size="12" text-anchor="middle" fill="#1a1a1a">21 Kas 12:35 ve 13:10</text>
<text x="271.0" y="351" font-size="12" text-anchor="middle" fill="#1a1a1a">9b57b5d: Playwright</text>
<text x="271.0" y="366" font-size="12" text-anchor="middle" fill="#1a1a1a">testleri</text>
<circle cx="451.0" cy="277" r="14" fill="#1f3a68"/>
<text x="451.0" y="281" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">9</text>
<line x1="451.0" y1="291" x2="451.0" y2="303" stroke="#9aa7bd"/>
<rect x="366" y="303" width="170" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="451.0" y="321" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">6. 2. tur düzeltme</text>
<text x="451.0" y="336" font-size="12" text-anchor="middle" fill="#1a1a1a">22 Kas 12:39-12:47</text>
<text x="451.0" y="351" font-size="12" text-anchor="middle" fill="#1a1a1a">77b5f78: master'a;</text>
<text x="451.0" y="366" font-size="12" text-anchor="middle" fill="#1a1a1a">8fb632d son commit</text>
<rect x="335.0" y="268" width="52" height="18" fill="#fff"/>
<path d="M353.0,286 L359.0,268 M363.0,286 L369.0,268" stroke="#c0392b" stroke-width="2" fill="none"/>
<text x="361.0" y="263" font-size="12" text-anchor="middle" fill="#c0392b" font-weight="bold">~23 sa boşluk</text>
<text x="6" y="408" font-size="12" text-anchor="start" fill="#555">Dairedeki sayı faz başına commit sayısıdır (toplam 25). Eksen ölçekli değildir; saatler commit zamanıdır.</text>
<text x="6" y="423" font-size="12" text-anchor="start" fill="#555">2. satır 1. satırın devamıdır (aralarında ~20 sa gece boşluğu).</text></svg>
<figcaption>Şekil 2. Geliştirme zaman çizelgesi: 25 commit, üç gün, yedi aşama. Aşama 0-3 aynı öğleden sonra 68 dakikada, denetim ve 1. tur düzeltme ertesi gün 9 dakikada, 2. tur düzeltme 22 Kasım'da 12:39-12:47 arasında commit'lendi.</figcaption>
</figure>

### Süreç notları

- Fazlar 0-3 aynı öğleden sonra 68 dakikada commit'lendi (15:33-16:41). Commit zamanları yazım süresini değil, toplu commit alışkanlığını yansıtıyor olabilir; gerçek çalışma süresi doğrulanmadı.
- Denetimden düzeltmelere 9 dakika geçti (12:52 -> 13:01); düzeltme commit'lerinin her biri yeni testlerle geldi. Test sayısı denetimde 36, bugün 65 (`facts.md`; artışın commit bazında dökümü doğrulanmadı).
- İkinci tur düzeltmeleri (22 Kas) 7 dakikada commit'lendi (12:40-12:47; 12:39'daki iki commit rapor ve merge). Geri alma doğrulamasının sonuçları (oturum ölçümü) bölüm 06'dadır.
- `denetim/playwright` dalı 77b5f78 merge'üyle master'a alındı; 8 E2E test (`e2e/app.spec.ts`) artık master'da (`git show --stat 77b5f78`). Dal yerelde hâlâ duruyor (`git branch -a`).


## 05. Değerlendirme ve testler

Test paketi 65 testten oluşuyor ve 65'i geçiyor (`65 passed in 1.12s`; kaynak: `uv run pytest -q`, 2026-11-22). Ayrıca `e2e/app.spec.ts` içinde 8 Playwright testi var. Retrieval ölçümü 59 soruluk dondurulmuş sette, ayar 36 soruluk ayrı sette yapıldı; üretim kalitesi depoda kalıcı olarak ölçülmüyor.

### Test paketi

Denetim anında paket 36 testti, kapsama %59 (750 ifade, 309 kaçırılan; kaynak: `denetim/DENETIM-2026-11-21.md`). Sonraki kapsama ölçülmedi (`uv run pytest --cov` çalıştırılmadı); aşağıdaki kapsama notları denetim anına aittir. `vector_index` ve `bm25_index` artık `tests/test_indexes.py` ile kısmen test ediliyor.

| Test alanı | Test sayısı | Kapsam |
|---|---|---|
| `tests/test_generator.py` | 16 | Bağlam biçimi, çit taşması, atıf doğrulama/düzeltme; denetimde `generator` %78 |
| `tests/test_chunk_py.py` | 9 | Python `ast` parçalama; `chunk_py` %95 |
| `tests/test_eval_match.py` | 7 | Eval eşleştirme kuralı |
| `tests/test_tokenizer.py` | 7 | Kod BM25 tokenizer; `bm25_index` %94 |
| `tests/test_rrf.py` | 6 | RRF birleştirme; `hybrid` %100 |
| `tests/test_app.py` | 5 | `app.py` yardımcıları |
| `tests/test_indexes.py` | 5 | JSON BM25 kaydet/yükle, vektör indeksi önbelleği (yeni) |
| `e2e/app.spec.ts` | 8 | Playwright E2E, pytest dışı (`grep -c "test("`) |
| `tests/test_chunk_md.py` | 4 | Markdown parçalama; `chunk_md` %95 |
| `tests/test_scanner.py` | 6 | Dosya tarama; `scanner` %91 |
| Toplam (pytest) | 65 | Dosya başına `def test` sayımı (kaynak: `grep -c "def test" tests/*.py`) toplamı 65 ile uyumlu; E2E hariç |

Denetimde kapsama %0 olan modüller: `cli`, `pipeline`, `vector_index` (şimdi kısmen test ediliyor), `eval/tune_rrf`; `embedder` %25 (kaynak: `denetim/DENETIM-2026-11-21.md`). Uçtan uca akış için pytest entegrasyon testi yok (bulgu M10, hâlâ açık).

### Retrieval değerlendirmesi: ana set

Dosya: `eval/results.md`. Set 59 soru: httpx 30 (15 name, 15 conceptual), kisiselnotarama 29 (15 name, 14 conceptual).

| Mod | hit@1 | hit@5 | MRR@10 |
|---|---|---|---|
| bm25 | 0.61 | 0.73 | 0.674 |
| vector | 0.71 | 0.90 | 0.794 |
| hybrid | 0.71 | 0.92 | 0.796 |

| Tür (n) | bm25 hit@5 / MRR | vector hit@5 / MRR | hybrid hit@5 / MRR |
|---|---|---|---|
| name (30) | 1.00 / 0.944 | 1.00 / 0.939 | 1.00 / 0.944 |
| conceptual (29) | 0.45 / 0.395 | 0.79 / 0.645 | 0.83 / 0.642 |

Hybrid ilk 10'da kna-23, kna-29 ve hx-17'yi bulamadı. Sonuçlar deterministik: 3 tekrar ve `eval/results.md` aynı md5'i verdi (kaynak: `denetim/DENETIM-2026-11-21.md`).

Eval artık iki repoyu da sabit commit'e bağlar: kisiselnotarama 1d45820 (`data/repos/kisiselnotarama`), httpx 7cff5f7 (`data/repos/httpx`) (kaynak: `eval/README.md`, commit 405bdb7). Sonuçlar sabitlemeden önceki tabloyla aynı kaldı; eval bu turda yeniden çalıştırılmadı, tablo dosyadan okundu.

Bu sayıların gösteremedikleri:
- Hibritin vektöre üstünlüğü kanıtlanmadı. Eşleştirilmiş karşılaştırmada hit@5: 1 iyi / 0 kötü / 58 aynı; RR farkı ortalama +0.0014 (n=59). Denetim "fark gürültü düzeyinde" yorumunu öneriyor (M9). Kisiselnotarama conceptual MRR'de hibrit 0.560, vektör 0.601.
- 59 soru küçük; tür/repo kırılımlarında n 14-15'e düşüyor, güven aralığı verilmedi (hesaplanmadı).
- Yalnız iki repo (httpx, KisiselNotArama) ve Türkçe sorular; başka dil/repo için genelleme doğrulanmadı.
- Üretilen cevabın doğruluğunu ölçmez, yalnız doğru parçanın getirilmesini ölçer.

### Retrieval değerlendirmesi: RRF ayarı

Dosya: `eval/tuning_results.md`. Tuning seti 36 soru (kaynak: `grep -c '"id"' eval/tuning.json` = 36). Tarama 36 kombinasyon: w_bm25 ∈ {0.3, 0.5, 0.7, 1.0}, k ∈ {10, 30, 60}, candidates ∈ {20, 30, 50}; w_vec=1. Skor = (name MRR@10 + conceptual MRR@10) / 2. Ana set taramada kullanılmadı.

| Yapılandırma | w_bm25 / k / candidates | Skor | name MRR | conceptual MRR |
|---|---|---|---|---|
| Seçilen | 0.3 / 30 / 20 | 0.7880 | 0.975 | 0.601 |
| Varsayılan | 1.0 / 60 / 30 | 0.7355 | n/a | n/a |
| Yalnız vektör | n/a | 0.7521 | 0.900 | 0.604 |

Kazanç +0.0526 skor. Sınırlar: kazanç tuning setinde ölçüldü; ayrı bir test setinde doğrulanmadı. Conceptual MRR vektörle neredeyse aynı (0.601 / 0.604); kazanç name sorularından geliyor.

### Üretim (cevap) kalitesi

Depoda kalıcı üretim ölçümü yok (M8: betik `eval/` içinde değil). Aşağıdakiler oturum ölçümüdür, depoda doğrulanmadı.

| Ölçüt | Denetim öncesi (12 soru x 3 tekrar) | Düzeltme sonrası (12 soru + 2 tuzak, 14 cevap) |
|---|---|---|
| Geçersiz atıf | 21/96 (%22); denetim raporunda 36 cevabın %25'i | %21,9 -> %0 (`fix_citations` sonrası; oturum ölçümü) |
| Atıfsız cevap | 15/36 | %35,7 -> %21,4 |
| Beklenen dosyaya atıf | 12/36 | %36,4 -> %72,7 |
| Tuzak sorular | 6/6 doğru reddedildi; gerçek sorularda yanlış red 0/36 | Ayrıca ölçülmedi |

Sınırlar: örnek çok küçük (14 cevap, 1 tekrar); önce/sonra farkı "doğrulanmadı" listesindedir. Doğrulamak için aynı 14 soruyla cevap üretim betiği yeniden çalıştırılmalı.

### Diğer ölçümler

| Alan | Sonuç | Durum |
|---|---|---|
| E2E (Playwright) | 8 test, `e2e/app.spec.ts` (103 satır); önceki koşuda 8/8 geçti (9b57b5d) | Dosyalar master'da (merge 77b5f78); 8/8 sonucu oturum ölçümü, bu turda yeniden koşulmadı; "İndeksle" başarı yolu test edilmedi (denetim) |
| Bağımlılık güvenliği | pip-audit: "No known vulnerabilities found" | Denetim raporu; torch+cu132 denetim dışı |
| Performans (httpx, 862 parça) | Sıcak arama medyanı: bm25 0.3 ms, vector 21.7 ms, hybrid 23.9 ms (p95 37 ms) | Oturum ölçümü; yeniden ölçülmedi |


## 06. Çok yönlü kalite değerlendirmesi (puanlı)

Ağırlıklı genel puan, denetim anı için 6.9/10; iki düzeltme turundan sonra yazarın yargısı 7.4/10 (yeniden denetim değil). Denetim puanları `denetim/DENETIM-2026-11-21.md` (2026-11-21, tam mod, kapsam commit 756e4df) üzerine kuruludur ve değiştirilmemiştir. Düzeltme sonrası değerlendirme ayrı bir tabloda, "değerlendirme" etiketiyle ve kanıtıyla verilir.

### Yöntem ve sınırlar

Denetim her boyutu ayrı alt ajana verdi; hata ve güvenlik bulguları ikinci modelle (Neon) çapraz kontrol edildi. Hakem olarak gpt-oss-120b-medium 2 çağrıda kullanıldı (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 5). Denetim kendi notunda şunu söyler: puanlar ajanların yargısıdır, kanıtlı bulgu puandan üstündür (bölüm 6).

- Denetimin 9 puanlı boyutu: test paketi, hatalar, güvenlik, Neon çapraz inceleme, kod kalitesi/mimari, E2E, erişilebilirlik, performans, LLM/RAG cevap kalitesi. Test stratejisi (senior-qa) React/Next.js'e özgü olduğu için puanlanmadı.
- Bu rapordaki 10 boyut denetimin boyutlarıyla birebir örtüşmez. Eşleme ve türetme kuralı aşağıdaki tabloda açıktır.
- "†" işaretli iki boyut (dokümantasyon, teslime hazırlık) denetimde puanlanmadı. Bunlar bu raporun yazarının değerlendirmesidir.

### Puan tablosu (denetim anı, değiştirilmemiş)

| Boyut | Ağırlık | Puan (/10) | Gerekçe (kanıt) | En büyük eksik |
|---|---|---|---|---|
| Doğruluk / kalite | %20 | 6.5 | Denetim "LLM/RAG cevap kalitesi" 6.5. Retrieval: ana sette hybrid hit@5 0.92, MRR@10 0.796 (`eval/results.md`). Tuzak sorular 6/6 reddedildi, yanlış red 0/36 | H2: 36 cevabın %25'inde geçersiz atıf, %42'si atıfsız. Hybridin vektöre üstünlüğü kanıtsız (M9) |
| Mimari | %8 | 7.5 | Denetim "kod kalitesi / mimari" 7.5. Bağımlılık yönü temiz (`config` → parçalayıcılar/indeksler → `hybrid`/`pipeline` → `cli`/`app`), döngü yok, ölü kod yok | İki indeksin yazımı atomik değil (L2). İndeks adı yalnız HEAD commit'ine bağlı (L1) |
| Kod kalitesi | %10 | 7.25 | Denetim "hatalar" 7 ile "kod kalitesi / mimari" 7.5'in ortalaması (türetme) | H1 enjeksiyon açığı; M3 satır numarası kayması; ruff/mypy yapılandırması yok (L11) |
| Test / ölçüm | %12 | 6 | Denetim "mevcut test paketi" 6: 36 geçti, kapsama %59 (750 ifade, 309 kaçırılan). Eval deterministik (3 tekrar aynı md5) | `cli`, `pipeline`, `vector_index`, `eval/tune_rrf` kapsamı %0; üretim kalitesi eval'de ölçülmüyor (M8, M10) |
| Dokümantasyon † | %6 | 7 | Değerlendirme: `README.md` (62 satır) kurulum, kullanım ve eval tablolarını içeriyor; `plan.md` (93 satır) kapsam ve v2 listesini veriyor | README'deki hibrit yorumu denetimde fazla iddialı bulundu (M9); denetim bu boyutu puanlamadı |
| Güvenlik / gizlilik | %12 | 8 | Denetim "güvenlik" 8. `shell=True`/`eval`/`exec` yok, yalnız localhost, git geçmişinde sır yok, `pip-audit` temiz. Neon 4/10 verdi; düşüklüğün ağırlıklı kısmı doğrulamada düşen önem seviyelerinden geliyor | M1: `pickle.load` (hakem: medium). M2: sembolik bağlantılar takip ediliyor (doğrulandı, test ile) |
| Performans | %8 | 7.5 | Denetim "performans" 7.5 (oturum ölçümü, httpx 862 parça): sıcak hybrid medyanı 23.9 ms, p95 37 ms; model yükleme 7.4 sn; RSS tepe ~4.1 GB | M6: `vector_index.search` her sorguda diskten okuyor (cProfile'da hybrid süresinin %26'sı). `ask` süresinin ~%99'u LLM |
| Kullanılabilirlik | %8 | 7 | Denetim E2E 7 (8/8 test geçti) ve erişilebilirlik 7 (render edilmiş DOM taraması) | H3: arama modunda da LLM çağrılıyor. WCAG: M13 (başlık atlaması), L13 (`lang="en"`, çerçeveden) |
| Bakım kolaylığı | %6 | 6.75 | Mimari 7.5 ile test paketi 6'nın ortalaması (türetme: yapı iyi, güvenlik ağı zayıf) | Test kapsamı %59; `hybrid.embed_query` monkeypatch'e bağlı (M11) |
| Teslime hazırlık † | %10 | 6 | Değerlendirme: denetim anında critical 0 ama high 3 açık; Playwright testleri o anda `master`'a birleştirilmemişti (`denetim/playwright`, 9b57b5d; sonradan 77b5f78 ile birleşti) | Denetim anında 3 high ve 13 medium bulgu açık; kurulum `torch` cu132 indeksine bağlı (`pyproject.toml`) |
| **Ağırlıklı genel puan** | **%100** | **6.9** | Σ(ağırlık × puan)/100 = 689/100 = 6.89 (hesap: bu bölümdeki tablo) | |

Kural: hiçbir boyut 8'in üzerine çıkmadı. 8 alan güvenlik puanı, denetimin ölçümlerine (`pip-audit`, kod incelemesi, test ile yeniden üretme) dayanıyor.

### Çapraz model doğrulama

Neon 8 bulgu verdi; 1 critical (pickle) doğrulamada düştü (doğrulayıcı: low, hakem: medium). Aşağıdaki tablo ayrışmaları özetler (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 2 ve 3).

| Bulgu | Neon | Doğrulayıcı (sonnet) | Hakem (gpt-oss) | Sonuç |
|---|---|---|---|---|
| H1 prompt injection | high | low | high | high |
| M1 `pickle.load` | critical | low | medium | medium |
| M2 sembolik bağlantı | high | medium (Claude güvenlik) | medium | medium (test ile doğrulandı) |
| L2 indeks yarışı | high | low | low | low |

Neon'un 4/10 güvenlik puanı bu önem farklarından doğar. Bu rapor güvenlik için denetimin 8'ini taşır ve Neon'un puanını ayrıca not eder.

### Denetimden sonra düzeltilenler (iki tur)

Denetimden sonra iki düzeltme turu 14 bulguyu kapattı: 3 high, 9 medium, 2 low (kaynak: `facts.md` "Denetim sonrası düzeltmeler" ve "Hâlâ açık denetim bulguları"; hesap: 29 - 15 açık = 14). Yeniden denetim yapılmadı. Test sayısı 36'dan 65'e çıktı (kaynak: `uv run pytest -q`, `65 passed in 1.12s`, 2026-11-22). Artışın commit bazında dökümü doğrulanmadı.

#### 1. tur

| Commit | Kapattığı bulgu | Kod kanıtı | Geri alma doğrulaması (oturum ölçümü) |
|---|---|---|---|
| ba50a40 | H3, M7, M13 | `app.py`: "LLM cevabı üret" onay kutusu, `st.cache_resource`, Kaynaklar h2 | 3 test kırıldı |
| b010685 | H1, H2, L3 | `src/generator.py`: `_fence`, `fix_citations`, `strip_images`, ters aralık | 4 düzeltme tek tek kapatıldı, her biri ≥1 test kırdı |
| 1f2b19a | Neon incelemesi: kod içinde atıf/boşluk dönüşümü, blok aralığı, önbellek anahtarı | `src/generator.py`, `app.py` | 6 test kırıldı |

#### 2. tur (2026-11-22)

Bu tur Neon incelemesinin doğrulanan bulgularını da içerir: Neon 7 bulgu verdi, doğrulananlar 5a8f7b9 ve 8fb632d ile düzeltildi (oturum ölçümü).

| Commit | Kapattığı bulgu | Kod kanıtı | Geri alma doğrulaması (oturum ölçümü) |
|---|---|---|---|
| 132f7d8 | M1, M6, L7 | `src/bm25_index.py` JSON, `src/vector_index.py` bellek önbelleği ve `argpartition`; `tests/test_indexes.py` | bm25: 3 test; vector: 1 test kırıldı |
| 1bee4f4 | M2, M3 (`chunk_py`) | `src/scanner.py` sembolik bağlantı; `src/chunk_py.py` form feed | scanner: 4 test; chunk_py: 1 test |
| 333fd9a | M3 (`chunk_md`) | `src/chunk_md.py` (`\x85` dahil) | ayrı sayı belirtilmedi (doğrulanmadı) |
| 8fb632d | Neon bulguları: M2 bileşen kontrolü, M6 önbellek | `src/scanner.py` symlink bileşenleri; `src/vector_index.py` disk değişimini izler | vector: 1 ek test kırıldı |
| 2edbf3c, 5a8f7b9 | M4, M5, M9 | `baslat.sh`, `durdur.sh` (PID doğrulama, port kontrolü, başlatma kilidi); `README.md` hibrit yorumu | kabuk betiği ve belge; Python geri alma kapsamı dışı |
| 405bdb7 | Eval sabitleme | `eval/README.md`, `eval/run_eval.py`: iki repo sabit commit'te (1d45820, 7cff5f7) | sonuçlar sabitlemeden önceki tabloyla aynı (oturum ölçümü; eval yeniden koşulmadı) |

Ek olarak Playwright dalı birleşti: `e2e/app.spec.ts` (8 `test(`), `playwright.config.ts`, merge 77b5f78. Önceki 8/8 geçti sonucu oturum ölçümüdür; bu turda yeniden koşulmadı.

- Geri alma sonuçları oturum ölçümüdür; depoda ölçüm çıktısı yok. Doğrulamak için her düzeltme geri alınıp `uv run pytest` tekrarlanmalı.
- Atıf kalitesi önce/sonra sayıları (oturum ölçümü, 14 cevap, geçersiz atıf %21,9 → %0) bölüm 05 "Üretim (cevap) kalitesi" tablosundadır; örneklem küçük ve tek koşulu.
- Hâlâ açık 15 bulgunun (4 medium, 11 low) listesi ve azaltma önerileri bölüm 07'dedir.

### Düzeltme sonrası değerlendirme (yazarın yargısı, iki tur)

Bu tablo denetim puanı değildir ve yeniden denetim sayılmamalıdır. Yalnız kodda, test ya da oturum ölçümünde kanıtı olan boyutlar değiştirildi; 8'in üzerine hiçbir puan çıkarılmadı (ölçülmüş destek yok). Denetim puanları yukarıdaki tabloda aynen duruyor.

| Boyut | Ağırlık | Denetim | Değerlendirme | Ağırlık × puan | Kanıt ve sınır |
|---|---|---|---|---|---|
| Doğruluk / kalite | %20 | 6.5 | 7.0 | 140 | Geçersiz atıf %21,9 → %0 (oturum ölçümü, 14 cevap, tek koşu). Retrieval değişmedi; M8 açık, ölçüm depoda yok, bu yüzden yalnız +0.5 |
| Mimari | %8 | 7.5 | 7.5 | 60 | Değişmedi: L1 ve L2 (indeks adı, atomik yazım) açık |
| Kod kalitesi | %10 | 7.25 | 7.75 | 77.5 | H1, M2, M3, L7 kapandı; her Python düzeltmesi geri alınınca ilgili test kırıldı (oturum ölçümü). L11 (lint/tip yok) açık |
| Test / ölçüm | %12 | 6 | 7.0 | 84 | 36 → 65 test (`uv run pytest -q`); düzeltmeler geri alma ile test ile bağlandı. Kapsama yeniden ölçülmedi; `pipeline`/`cli` testsiz (M10), M8 açık |
| Dokümantasyon † | %6 | 7 | 7.5 | 45 | M9 README yorumu düzeltildi (2edbf3c); `eval/README.md` sabitlemeyi anlatıyor (405bdb7) |
| Güvenlik / gizlilik | %12 | 8 | 8 | 96 | M1 (JSON) ve M2 (symlink) kapandı, ama puan 8'te tutuldu: L5, L6 açık, düzeltmeler yeniden denetlenmedi |
| Performans | %8 | 7.5 | 7.5 | 60 | M6 ve L7 kodda kapandı (132f7d8, 8fb632d); süre yeniden ölçülmedi, puan değişmedi |
| Kullanılabilirlik | %8 | 7 | 7.5 | 60 | H3, M13 kapalı; M4/M5 betikleri düzeltildi; Playwright birleşti ama yeniden koşulmadı. 7.5'te tutuldu (kabuk betiği düzeltmeleri test ile bağlı değil) |
| Bakım kolaylığı | %6 | 6.75 | 7.25 | 43.5 | Türetme: (Mimari 7.5 + Test 7.0) / 2 = 7.25 (denetimle aynı kural) |
| Teslime hazırlık † | %10 | 6 | 7.75 | 77.5 | High açık 0 (denetimde 3); medium açık 4/13; Playwright birleşti (77b5f78); eval sabitlendi. Açık: M8, M10-M12; `torch` cu132 bağımlılığı |
| **Ağırlıklı toplam** | **%100** | **6.9** | **7.4** | **743.5** | Σ(ağırlık × puan)/100 = 743.5/100 = 7.435, yani 7.4/10 |

Hesap: 140 + 60 + 77.5 + 84 + 45 + 96 + 60 + 60 + 43.5 + 77.5 = 743.5. Fark denetim anına göre +0.55 (7.435 - 6.89); ağırlıklı puan toplamındaki +54.5 farkın dökümü: teslime hazırlık +17.5, test +12, doğruluk +10, kod kalitesi +5, kullanılabilirlik +4, dokümantasyon +3, bakım +3. Bu rakam yazarın yargısıdır ve yeniden denetimle doğrulanmadı. Doğrulamak için `/denetmen` hızlı modu çalıştırılmalı ve atıf ölçümü aynı 14 soruyla tekrarlanmalı. Önceki (1. tur sonrası) yargı 7.2 idi; 2. tur +0.2 ekledi.

### Kontrol edilmeyenler

Denetim şunları kapsamadı: torch+cu132 bağımlılık taraması, görsel ekran görüntüsü incelemesi, kontrast aracı, yük testi, "İndeksle" başarı yolunun E2E testi, 12 soru dışındaki tüm cevap seti ve JS/C# desteği (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 4).


## 07. Sınırlamalar ve riskler

Denetimde 29 bulgu çıktı (0 critical, 3 high, 13 medium, 13 low); iki düzeltme turundan sonra 14'ü kapandı, 15'i açık: 0 high, 4 medium, 11 low (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 2; `facts.md` "Hâlâ açık denetim bulguları"). Kapanış commit'leri aşağıdaki "Kapatılanlar" tablosundadır. Olasılık ve etki sütunları değerlendirmedir; kanıt sütunu denetim bulgu numarasıdır. Açık listesi L4 dışında kodla yeniden doğrulanmadı.

### Bilinen sınırlar (açık, etkiye göre sıralı)

| Sıra | Risk | Olasılık | Etki | Kanıt | Azaltma |
|---|---|---|---|---|---|
| 1 | Üretim kalitesi kalıcı ölçülmüyor; atıf iyileşmesi (%21,9 → %0) yalnız oturum ölçümü, betik `eval/` içinde yok | Yüksek | Orta | M8; `facts.md` "Doğrulanmadı" | Atıf metriklerini `eval/` içine kalıcı betik olarak ekle |
| 2 | Hibritin vektöre üstünlüğü kanıtlanmamış: hit@5 1 iyi / 0 kötü / 58 aynı, RR farkı +0.0014 (n=59). README yorumu düzeltildi (2edbf3c), ölçüm sınırı duruyor | Yüksek | Orta | M9 (yorum kapandı), `eval/results.md` | Daha büyük, yeni soru seti |
| 3 | Entegrasyon testi yok: `pipeline`, `cli`, `eval/tune_rrf` testsiz; `vector_index` kısmen test ediliyor, kapsama yeniden ölçülmedi (denetim anı %59) | Yüksek | Orta | M10 | Sahte repo + sahte embedder ile pipeline testi |
| 4 | Hata yönetimi: sessiz `errors="replace"`, CLI'da ham traceback, loglama yalnız `embedder.py`'de | Orta | Düşük | M12 | Okunamayan dosyaları say; anlaşılır CLI hataları |
| 5 | `chunk_md` çit türünü eşlemiyor (`_FENCE`); farklı çit türüyle yanlış blok sınırı ve `# C#` kırpması denetimde doğrulandı | Düşük | Orta (yanlış parça sınırı) | L4 (kodda yeniden doğrulandı) | Çit türünü ve uzunluğunu eşle, test ekle |
| 6 | Güvenilmeyen repoda `git` komutları (`core.fsmonitor`) ve serbest repo yolu, boyut sınırı yok | Düşük | Orta | L5 (doğrulanmadı), L6 | `-c core.fsmonitor=`; yol ve boyut doğrulaması |
| 7 | `hybrid.embed_query` monkeypatch'e bağlı; lint/tip yapılandırması yok | Orta | Düşük | M11 (doğrulanmadı), L11 | `embed_fn` parametresi; ruff/mypy |
| 8 | İndeks adı yalnız HEAD commit'ine bağlı, bayat indeks mümkün; sabit `.tmp`/`.old` dizinleri çakışabilir | Düşük | Düşük | L1, L2 | Çalışma ağacı durumunu anahtara kat; benzersiz geçici dizin |
| 9 | Performans: CLI'da her çağrı ~9 sn (model yükleme 7.4 sn); indeksleme ~19 sn (embed 11 sn); RSS tepe ~4.1 GB. Değerler M6 düzeltmesinden önce ölçüldü | Yüksek | Düşük | L8, L9; oturum ölçümü | Uzun ömürlü süreç; batch büyüt; yeniden ölç |
| 10 | Erişilebilirlik: `<html lang="en">` Türkçe içerikte (çerçeveden düzeltilemez); ham expander başlığı | Yüksek | Düşük | L12, L13 (araç) | Başlık metnini düzelt; L13 için çerçeve kısıtı |
| 11 | `KisiselNotArama` yolu `app.py`/eval'de sabit kodlu | Orta | Düşük | L10 (doğrulanmadı) | Yolu `config`'e taşı |

### Kapatılanlar

Kapanan 14 bulgu (3 high, 9 medium, 2 low) ve kapanış commit'leri aşağıdadır. Kod kanıtı ve geri alma doğrulaması (oturum ölçümü) bölüm 06 "Denetimden sonra düzeltilenler" tablolarındadır.

| Bulgu | Commit |
|---|---|
| H1, H2, L3 | b010685 |
| H3, M7, M13 | ba50a40 |
| 1. tur Neon bulguları | 1f2b19a |
| M1 (pickle → JSON) | 132f7d8 |
| M2 (symlink kaçışı) | 1bee4f4, 8fb632d |
| M3 (form feed satır kayması) | 1bee4f4 (`chunk_py`), 333fd9a (`chunk_md`) |
| M4, M5 (başlat/durdur) | 2edbf3c, 5a8f7b9 |
| M6, L7 (vektör önbelleği, `argpartition`) | 132f7d8, 8fb632d |
| M9 (README hibrit yorumu; ölçüm sınırı bilinen sınırlar sırasında 2'de kalır) | 2edbf3c |
| 2. tur Neon bulguları (7 bulgudan doğrulananlar) | 5a8f7b9, 8fb632d |

Ek olarak Playwright dalı `master`'a birleşti (77b5f78) ve eval iki repoyu sabit commit'e sabitledi (405bdb7); bu iki risk de kapandı.

### Olası riskler (doğrulanmamış)

| Risk | Olasılık | Etki | Kanıt | Azaltma |
|---|---|---|---|---|
| Küçük soru seti (59) nedeniyle sonuçların başka repolara genellenmemesi | Orta | Yüksek | Yalnız iki repo; JS/C# v2 kapsamında, denetlenmedi | Farklı repolardan soru ekle |
| Düzeltmeler bağımsız yeniden denetimden geçmedi; kapatılan bulgular kodda ve geri alma testiyle doğrulandı, ama kapsama ve performans yeniden ölçülmedi | Orta | Orta | `facts.md` "Doğrulanmadı" | `/denetmen` hızlı modu; kapsama ve performans yeniden ölçümü |
| Ayar kazancının (+0.0526) tuning seti dışında geçmemesi | Orta | Orta | Ayrı test seti yok | Üçüncü, dondurulmuş set |
| `fix_citations` geçersiz atıfı temizler ama cevabın doğruluğunu garanti etmez | Orta | Orta | Yalnız atıf biçimi ölçüldü | Cevap doğruluğu için ayrı değerlendirme |
| Küçük yerel model (`qwen3.5:4b`) bağlam dışı bilgi üretebilir | Orta | Orta | Tuzak sorular 6/6 reddedildi (küçük örnek) | Daha büyük tuzak seti |
| E2E testleri birleşti ama merge sonrası yeniden koşulmadı; arayüz regresyonu fark edilmeyebilir | Düşük | Düşük | `e2e/app.spec.ts` 8 `test(`; önceki 8/8 oturum ölçümü | Master'da Playwright'ı çalıştır |
| `torch+cu132` bağımlılık açıkları denetlenmedi | Düşük | Orta | pip-audit kapsamı dışı | Ayrı denetim |


## 08. Alternatif teknolojiler

Projenin 6 ana teknoloji seçimi için alternatifler aşağıda; hiçbirinde şu an geçiş gerekçesi yok. Seçilen seçenek her tabloda **kalın** yazılıdır. Alternatiflerin artı/eksileri genel bilgidir ve bu projede ölçülmedi; "doğrulanmadı" denen yerde neyin ölçüleceği belirtilmiştir. Geçiş koşulu olarak verilen eşikler yazarın önerisidir, depodan gelmez.

### 1. Gömme modeli

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **BAAI/bge-m3 (yerel)** | Çok dilli; Türkçe soru ve İngilizce kod birlikte çalışır. Yerelde çalışır, veri dışarı çıkmaz. Ana sette vector hit@5 0.90 (`eval/results.md`) | torch + CUDA bağımlılığı; model yükleme 7.4 sn, RSS tepe ~4.1 GB (oturum ölçümü) | Veri yerel kalmalı, Türkçe sorgu var |
| Daha küçük yerel model (örn. e5-small sınıfı) | Daha az bellek, daha hızlı yükleme | Çok dilli kod aramada kalite bu projede ölçülmedi | Bellek ya da yükleme süresi darboğaz olursa |
| Bulut gömme API'si | Yerel GPU ve torch gerekmez | Kod dışarı gider; ağ ve maliyet bağımlılığı | Yerel donanım yoksa ve kod gizli değilse |

Geçiş gerekçesi yok. Doğrulamak için: aynı `eval/questions.json` (59 soru) ile aday modeli çalıştırıp hit@5 ve MRR@10'u kıyaslamak gerekir; bu yapılmadı (doğrulanmadı).

### 2. Vektör deposu

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **numpy `vecs.npy` + kaba kuvvet (float16)** | Ek bağımlılık yok, deterministik, indeks tek dosya (`src/vector_index.py`). 862 parçada vector arama medyanı 21.7 ms, embed ~10 ms dahil (oturum ölçümü) | Arama süresi parça sayısıyla doğrusal artar. İndeks bellek önbelleğinde tutulur ve disk değişimini izler (M6 kapandı, 132f7d8 ve 8fb632d; süre yeniden ölçülmedi) | Küçük ve orta repo, tek kullanıcı |
| FAISS | Büyük koleksiyonda hızlı yaklaşık arama | Ek bağımlılık; küçük koleksiyonda kazanç yok | Parça sayısı on binlere çıkarsa |
| Chroma / Qdrant | Meta veri filtresi, kalıcı sunucu, çok kullanıcı | Süreç yönetimi ve bağımlılık ağırlığı | Çok repo ve filtreli arama gerekirse |

Geçiş şimdi gerekçesiz: `search` payı ~7 ms (oturum ölçümü, M6 düzeltmesinden önce) ve darboğaz depolama motoru değildi; diskten tekrar okuma önbellekle giderildi, düzeltme sonrası süre ölçülmedi. Geçiş koşulu (öneri): sıcak vector arama medyanı 100 ms'yi aşarsa.

### 3. Sözcük (lexical) arama

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **rank-bm25 0.2.2 + özel kod tokenizer'ı** | Saf Python, sıcak arama medyanı 0.3 ms (oturum ölçümü). name sorularında MRR 0.944 (`eval/results.md`) | Büyük koleksiyonda bellek içi; indeks JSON saklanır, yüklemede yeniden kurulur (M1 kapandı, 132f7d8) | Küçük repo, kod sembol adı araması |
| SQLite FTS5 | Disk tabanlı, sorgu başına tüm indeksi belleğe yüklemez | Kod tokenizer'ı (`camelCase`, `snake_case` bölme) ayrıca uyarlanmalı | İndeks belleğe sığmayacak kadar büyürse |
| Tantivy / Elasticsearch | Ölçeklenebilir, zengin sorgu | Kurulum ve işletme ağırlığı | Çok büyük depo ya da paylaşımlı sunucu |

Geçiş gerekçesi yok; BM25 hızı ve name kalitesi yeterli. M1 için denetimin önerdiği önlem uygulandı: token listeleri JSON saklanıyor, BM25 yüklemede yeniden kuruluyor (132f7d8); FTS5'e geçmeye gerek kalmadı.

### 4. Kod parçalama

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **Python `ast` + Markdown başlıkları** | Standart kütüphane, sınıf/metot/fonksiyon sınırı doğru. `chunk_py` kapsamı %95 (denetim anı) | Yalnız `.py` ve `.md`; JS/C# desteği yok (`src/config.py` `EXTENSIONS`) | Python ağırlıklı depolar |
| tree-sitter | Çok dilli sözdizimi ağacı | Dil başına gramer ve ek bağımlılık | JS/C# gerekince; `plan.md` bunu v2'ye bırakıyor |
| Sabit boyutlu / satır kayan pencere | Dil bağımsız, basit | Sembol sınırını keser; atıfta sembol adı kaybolur | Sözdizimi çözümlenemeyen dosyalarda yedek olarak |

Geçiş: yeni dil istenene kadar gerekçe yok. Koşul: ikinci bir dil desteği talebi.

### 5. Üretici model (LLM)

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **Ollama + qwen3.5:4b (yerel, 3.3 GB)** | Kod makineden çıkmaz, anahtar ve ücret yok. Tuzak soruların 6/6'sı reddedildi, yanlış red 0/36 (denetim) | `ask` süresinin ~%99'u LLM; sıcakken ~8 sn. Atıf uyumu zayıftı (H2) | Gizlilik ve çevrimdışı çalışma öncelikse |
| Daha büyük yerel model | Daha iyi atıf ve akıl yürütme beklenir | VRAM sınırı: indeksleme tepesi 1.67 GB (oturum ölçümü); büyük model bu bütçeyi aşabilir | Donanım yeterliyse ve atıf kalitesi yetmezse |
| Bulut LLM API | Yüksek kalite, düşük gecikme | Kod parçaları dışarı gider; maliyet | Repo gizli değilse ve kalite kritikse |

Geçiş şimdilik gerekçesiz: H2 atıf sorunu model değiştirmeden, `fix_citations` ile geçersiz atıfı %21,9'dan %0'a indirdi (oturum ölçümü). Koşul: düzeltme sonrası da atıfsız cevap oranı kabul edilemezse (şu an %21,4, oturum ölçümü) daha büyük model denenmeli.

### 6. Arayüz ve sıralama katmanı

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **Streamlit 1.67.0 + CLI** | `app.py` 61 satır; tek tıkla `baslat.sh`. Yalnız localhost | `lang="en"` ve bazı İngilizce etiketler çerçeveden gelir ve değiştirilemez (L13) | Kişisel araç, hızlı prototip |
| FastAPI + React | Tam arayüz ve erişilebilirlik denetimi, çok kullanıcı | Çok daha fazla kod ve bakım | Ekip kullanımı, kimlik doğrulama gerekirse |
| **RRF (ağırlıklı) ile birleştirme** | Ek model yok; tuning setinde skor 0.7880, varsayılan 0.7355 (`eval/tuning_results.md`) | Ana sette vektör karşısındaki fark gürültü düzeyinde: RR farkı ort. +0.0014, n=59 (M9) | Hafif, açıklanabilir birleştirme |
| Cross-encoder reranker | Genelde üst sıra kalitesini artırır | Ek model, gecikme; bu projede ölçülmedi | Kavramsal sorularda iyileşme gerekirse; `plan.md` v2 listesinde |

Streamlit için geçiş gerekçesi yok. Reranker için koşul: kavramsal sorularda hybrid hit@5'in 0.83 (`eval/results.md`) seviyesinin yetersiz kaldığı ayrı bir soru setiyle gösterilirse denenmeli; ölçülmeden eklenmemeli.


## 09. Yol haritası

Denetimde açık kalan 15 bulgunun 14'ü (L13 hariç) ve `plan.md`'deki 4 v2 fikri 15 işe indirildi; "Şimdi" grubundaki 4 iş ölçü ve test boşluklarını kapatır. Sayım: 29 bulgudan iki düzeltme turunda 14'ü kapandı, 15'i açık (4 medium, 11 low); L13 Streamlit çerçevesine bağlı olduğu için kapsam dışıdır, kalan 14 bulgu (M8, M10-M12, L1, L2, L4-L6, L8-L12) 11 işe, 4 v2 fikri 4 işe dağılır (kaynak: `facts.md` "Hâlâ açık denetim bulguları").

### Kapsam ve durum

Denetimden sonra iki tur düzeltme geldi; 2026-11-21 tarihli ilk taslaktaki "Şimdi" maddelerinin çoğu tamamlandı. Bulgu kimlikleri bölüm 06 (puan gerekçeleri) ve bölüm 07 (riskler) ile aynıdır.

Tamamlanan işlerin commit listesi bölüm 07 "Kapatılanlar" tablosundadır; 1. taslaktaki Playwright birleştirme, `pickle` → JSON, symlink, satır kayması, `baslat.sh`/`durdur.sh`, vektör önbelleği, README yorumu ve eval sabitleme bu listede yer alır. Aşağıdaki şemada "Tamamlandı" sütunu bunların özetidir.

| Durum | Bulgular | Kaynak |
|---|---|---|
| Açık, bu yol haritasında | M8, M10, M11, M12, L1, L2, L4, L5, L6, L8, L9, L10, L11, L12 | `facts.md` |
| Açık, kapsam dışı | L13 (`<html lang="en">`, Streamlit çerçevesi) | `denetim/DENETIM-2026-11-21.md`, L13 |

Not: açık bulguların hepsi kodda yeniden doğrulanmadı (yalnız L4 yeniden doğrulandı). "Doğrulanmadı" etiketli bulgular (M11, M12, L5, L6, L10, L11) için önce basit bir yeniden üretme adımı gerekir.

### Şimdi

Şimdi grubu, kalan değişikliklerin ölçüsünü ve güvenlik ağını koyan işleri içerir.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 1 | Atıf kalitesi ölçümünü `eval/` içine kalıcı betik yap | "%21,9 → %0" iddiası yeniden üretilebilir olur | M | Çalışan Ollama; aynı 14 soru | Betik depoda; geçersiz atıf oranı betik çıktısında raporlanıyor | M8, H2 |
| 2 | `pipeline`, `cli`, `eval/tune_rrf` için sahte repo + sahte embedder ile entegrasyon testi; kapsamayı yeniden ölç | Bu modüller testsiz kalmaz; kapsama denetimdeki %59 ile karşılaştırılır | M | Embedder ve Ollama için mock | Üç modül kapsamı > %0; tarama-parçalama-indeks-arama akışı tek testte | M10 |
| 3 | Playwright'ı `master`'da yeniden çalıştır, komutu `README.md`'ye yaz | Merge sonrası E2E güvencesi doğrulanır | S | Çalışan Streamlit + Ollama | `e2e/app.spec.ts` 8 `test(` geçiyor; `uv run pytest -q` etkilenmiyor | Bölüm 07 olası risk (E2E) |
| 4 | `chunk_md` çit türü eşlemesini düzelt | Atıflardaki satır aralıkları doğru kalır | S | Farklı çit türü içeren test girdisi | Yeni test geçer, düzeltme geri alınınca kırılır | L4 |

Efor ölçeği: S = bir oturumdan kısa, M = bir-iki oturum, L = çok oturum. Bu bir değerlendirme olup ölçüm değildir.

### Sonra

Sonra grubu, düşük etkili açık bulguları ve ölçümün gücünü artıran işleri içerir.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 5 | Hibrit-vektör karşılaştırmasını daha büyük, yeni bir soru setiyle tekrarla | "Hibrit daha iyi" iddiası ya kanıtlanır ya bırakılır | M | Dondurulmuş yeni set (ayar setiyle çakışmayan) | Eşleştirilmiş fark ve güven aralığı raporlanır; mevcut fark +0.0014 (n=59) | M9 (ölçüm sınırı) |
| 6 | `git` çağrılarında `core.fsmonitor` kapat; repo yolu ve boyut doğrulaması | Güvenilmeyen repoda komut çalıştırma riski azalır | S | L5 için yeniden üretme adımı | Sahte `fsmonitor` ayarlı repoda komut çalışmıyor; aşırı büyük yol reddediliyor | L5, L6 |
| 7 | `hybrid_search`'e `embed_fn` parametresi ekle; `monkeypatch`'i kaldır | `eval/run_eval.py` ve `eval/tune_rrf.py` kırılgan bağdan kurtulur | S | Yok | Eval çıktıları (`eval/results.md`) değişmez (md5 aynı) | M11 |
| 8 | Hata yönetimi ve loglama: sessiz `errors="replace"`, ham traceback, geniş `except` | Hatalar kullanıcıya anlaşılır çıkar | M | Madde 2 (CLI testi) | CLI'da bilinen hata girdileri traceback yerine mesaj verir | M12 |
| 9 | İndeks adına çalışma ağacı durumunu kat; eski indeksleri temizle; yazımı atomik yap | Bayat indeks ve çakışma riski azalır | M | Madde 2 | Kirli ağaçta indeks adı değişir; eşzamanlı build testi | L1, L2 |
| 10 | Model yükleme ve indeksleme süresini kısalt; M6 sonrası gecikmeyi yeniden ölç | CLI çağrısı ~9 sn, indeksleme ~19 sn; M6 kazancı ölçülür | M | GPU belleği payı (VRAM tepe 1.67 GB) | Sıcak hibrit medyanı 23.9 ms'nin altında (yeniden ölçülmüş); indeksleme 19 sn'nin altında, sonuçlar aynı | L8, L9, M6 |
| 11 | `ruff`/`mypy` yapılandırması; sabit `KisiselNotArama` yolunu `config`'e taşı; kaynak expander başlığını düzelt | Bakım kolaylığı ve erişilebilirlik | S | Yok | Yapılandırma depoda; `app.py` ve `eval/run_eval.py` yolu `config`'ten okur | L10, L11, L12 |

### Belki (v2 fikirleri)

Bu grup `plan.md` "v2 fikirleri" bölümünden gelir ve hiçbiri bir denetim bulgusuyla zorunlu kılınmamıştır.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 12 | Cross-encoder reranking | Kavramsal sorularda sıralama iyileşebilir (hibrit conceptual MRR 0.642; ilk 10'da bulunamayanlar: kna-23, kna-29, hx-17) | L | Madde 5'teki yeni set; ayar için ayrı set | Yeni sette conceptual MRR@10, rerank olmadan hibritten yüksek; gecikme ölçülü | Bölüm 05 (conceptual sonuçlar); M9 |
| 13 | Incremental indexing (git diff ile yalnız değişen dosyalar) | Yeniden indeksleme ~19 sn yerine değişen dosya sayısıyla orantılı | M | Madde 9 (indeks adı/atomik yazım) | Tek dosya değişiminde süre, tam indekslemenin bir kesri; sonuçlar tam indeksle aynı | L1, L9 |
| 14 | tree-sitter ile JS ve C# desteği | Kapsam genişler (şimdi yalnız `.py`, `.md`) | L | Yeni dillerde dondurulmuş eval seti | Yeni dil için isim/kavramsal soru seti ve hit@5 raporu | Bölüm 01 kapsam dışı |
| 15 | Çağrı grafiği ("X'i kim çağırıyor?") | Yeni soru türü | L | Çağrı çözümlemesi tasarımı; yeni eval türü | Soru türü için ayrı set ve metrik | Bağlı bulgu yok (yeni özellik) |

### Yol haritası şeması

<figure>
<svg viewBox="0 0 720 748" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Yol haritası" font-family="DejaVu Sans, sans-serif" style="max-width:100%;height:auto"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs><rect x="112" y="8" width="147" height="24" rx="4" fill="#2f6f4f"/>
<text x="185.5" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Tamamlandı</text>
<rect x="265" y="8" width="147" height="24" rx="4" fill="#1f3a68"/>
<text x="338.5" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Şimdi</text>
<rect x="418" y="8" width="147" height="24" rx="4" fill="#4a6fa5"/>
<text x="491.5" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Sonra</text>
<rect x="571" y="8" width="147" height="24" rx="4" fill="#7f8c9b"/>
<text x="644.5" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Belki</text>
<rect x="4" y="40" width="712" height="159" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="60" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Test ve ölçüm</text>
<rect x="112" y="46" width="147" height="42" rx="5" fill="#fff" stroke="#2f6f4f" stroke-width="1.2"/>
<text x="185.5" y="64" font-size="12" text-anchor="middle" fill="#1a1a1a">Playwright birleşti</text>
<text x="185.5" y="79" font-size="12" text-anchor="middle" fill="#1a1a1a">(77b5f78)</text>
<rect x="265" y="46" width="147" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="338.5" y="64" font-size="12" text-anchor="middle" fill="#1a1a1a">#1 Atıf eval betiği</text>
<text x="338.5" y="79" font-size="12" text-anchor="middle" fill="#1a1a1a">kalıcı (M)</text>
<rect x="265" y="94" width="147" height="57" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="338.5" y="112" font-size="12" text-anchor="middle" fill="#1a1a1a">#2 Entegrasyon testi:</text>
<text x="338.5" y="127" font-size="12" text-anchor="middle" fill="#1a1a1a">pipeline, cli, tune_rrf</text>
<text x="338.5" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a">(M)</text>
<rect x="265" y="157" width="147" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="338.5" y="175" font-size="12" text-anchor="middle" fill="#1a1a1a">#3 Playwright</text>
<text x="338.5" y="190" font-size="12" text-anchor="middle" fill="#1a1a1a">yeniden koş (S)</text>
<rect x="418" y="46" width="147" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="64" font-size="12" text-anchor="middle" fill="#1a1a1a">#5 Hibrit-vektör, yeni</text>
<text x="491.5" y="79" font-size="12" text-anchor="middle" fill="#1a1a1a">soru seti (M)</text>
<rect x="4" y="203" width="712" height="98" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="223" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Güvenlik</text>
<rect x="112" y="209" width="147" height="57" rx="5" fill="#fff" stroke="#2f6f4f" stroke-width="1.2"/>
<text x="185.5" y="227" font-size="12" text-anchor="middle" fill="#1a1a1a">pickle yerine JSON,</text>
<text x="185.5" y="242" font-size="12" text-anchor="middle" fill="#1a1a1a">symlink (132f7d8,</text>
<text x="185.5" y="257" font-size="12" text-anchor="middle" fill="#1a1a1a">1bee4f4, 8fb632d)</text>
<rect x="418" y="209" width="147" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="227" font-size="12" text-anchor="middle" fill="#1a1a1a">#6 fsmonitor kapat,</text>
<text x="491.5" y="242" font-size="12" text-anchor="middle" fill="#1a1a1a">repo yolu doğrula (S)</text>
<rect x="418" y="257" width="147" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="275" font-size="12" text-anchor="middle" fill="#1a1a1a">#9 İndeks adı +</text>
<text x="491.5" y="290" font-size="12" text-anchor="middle" fill="#1a1a1a">atomik yazım (M)</text>
<rect x="4" y="305" width="712" height="65" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="325" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Doğruluk</text>
<text x="10" y="340" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">(parçalama,</text>
<text x="10" y="355" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">atıf)</text>
<rect x="112" y="311" width="147" height="42" rx="5" fill="#fff" stroke="#2f6f4f" stroke-width="1.2"/>
<text x="185.5" y="329" font-size="12" text-anchor="middle" fill="#1a1a1a">Satır kayması M3</text>
<text x="185.5" y="344" font-size="12" text-anchor="middle" fill="#1a1a1a">(1bee4f4, 333fd9a)</text>
<rect x="265" y="311" width="147" height="27" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="338.5" y="329" font-size="12" text-anchor="middle" fill="#1a1a1a">#4 md çit türü, L4 (S)</text>
<rect x="4" y="374" width="712" height="67" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="394" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Performans</text>
<rect x="112" y="380" width="147" height="42" rx="5" fill="#fff" stroke="#2f6f4f" stroke-width="1.2"/>
<text x="185.5" y="398" font-size="12" text-anchor="middle" fill="#1a1a1a">Vektör önbelleği M6,</text>
<text x="185.5" y="413" font-size="12" text-anchor="middle" fill="#1a1a1a">L7 (132f7d8)</text>
<rect x="418" y="380" width="147" height="57" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="398" font-size="12" text-anchor="middle" fill="#1a1a1a">#10 Model yükleme</text>
<text x="491.5" y="413" font-size="12" text-anchor="middle" fill="#1a1a1a">ve indeksleme,</text>
<text x="491.5" y="428" font-size="12" text-anchor="middle" fill="#1a1a1a">yeniden ölç (M)</text>
<rect x="571" y="380" width="147" height="42" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="644.5" y="398" font-size="12" text-anchor="middle" fill="#1a1a1a">#13 Incremental</text>
<text x="644.5" y="413" font-size="12" text-anchor="middle" fill="#1a1a1a">indexing (M)</text>
<rect x="4" y="445" width="712" height="144" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="465" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Bakım ve</text>
<text x="10" y="480" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">belge</text>
<rect x="112" y="451" width="147" height="72" rx="5" fill="#fff" stroke="#2f6f4f" stroke-width="1.2"/>
<text x="185.5" y="469" font-size="12" text-anchor="middle" fill="#1a1a1a">baslat/durdur,</text>
<text x="185.5" y="484" font-size="12" text-anchor="middle" fill="#1a1a1a">README, eval</text>
<text x="185.5" y="499" font-size="12" text-anchor="middle" fill="#1a1a1a">sabitleme (2edbf3c,</text>
<text x="185.5" y="514" font-size="12" text-anchor="middle" fill="#1a1a1a">5a8f7b9, 405bdb7)</text>
<rect x="418" y="451" width="147" height="27" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="469" font-size="12" text-anchor="middle" fill="#1a1a1a">#7 embed_fn (S)</text>
<rect x="418" y="484" width="147" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="502" font-size="12" text-anchor="middle" fill="#1a1a1a">#8 Hata yönetimi ve</text>
<text x="491.5" y="517" font-size="12" text-anchor="middle" fill="#1a1a1a">loglama (M)</text>
<rect x="418" y="532" width="147" height="57" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="491.5" y="550" font-size="12" text-anchor="middle" fill="#1a1a1a">#11 ruff/mypy, sabit</text>
<text x="491.5" y="565" font-size="12" text-anchor="middle" fill="#1a1a1a">yol, expander başlığı</text>
<text x="491.5" y="580" font-size="12" text-anchor="middle" fill="#1a1a1a">(S)</text>
<rect x="4" y="593" width="712" height="129" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="613" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Erişim ve</text>
<text x="10" y="628" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">kapsam (v2)</text>
<rect x="571" y="599" width="147" height="42" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="644.5" y="617" font-size="12" text-anchor="middle" fill="#1a1a1a">#12 Cross-encoder</text>
<text x="644.5" y="632" font-size="12" text-anchor="middle" fill="#1a1a1a">rerank (L)</text>
<rect x="571" y="647" width="147" height="42" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="644.5" y="665" font-size="12" text-anchor="middle" fill="#1a1a1a">#14 tree-sitter JS/C#</text>
<text x="644.5" y="680" font-size="12" text-anchor="middle" fill="#1a1a1a">(L)</text>
<rect x="571" y="695" width="147" height="27" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="644.5" y="713" font-size="12" text-anchor="middle" fill="#1a1a1a">#15 Çağrı grafiği (L)</text>
<text x="8" y="740" font-size="12" text-anchor="start" fill="#555">#n: yol haritası öncelik numarası (bölüm 09); (S/M/L): efor. 1-4 Şimdi, 5-11 Sonra, 12-15 Belki.</text></svg>
<figcaption>Şekil 3. Yol haritası (Tamamlandı / Şimdi / Sonra / Belki), alana göre. Bağımlılıklar (önce → sonra): #1 → #5, #5 → #12, #2 → #8, #2 → #9, #9 → #13, #10 → #13. Önceliklendirme ve efor değerlendirmedir.</figcaption>
</figure>

### Değerlendirme

Sıralama gerekçesi: önce ölçü ve test (madde 1-3), çünkü sonraki değişikliklerin geri alma doğrulaması bunlara dayanıyor; iki düzeltme turunda aynı yöntem kullanıldı (oturum ölçümü, `facts.md`). Hibrit≈vektör bulgusu için iddia README'de düzeltildi, ölçüm işi (madde 5) "Sonra" grubunda kaldı. Bu sıra bir değerlendirmedir; kesin etki hesabı yapılmamıştır.


## 10. CV ve portföy değeri

Proje, 3 takvim gününde (2026-11-20 → 2026-11-22) 25 commit ile üretilmiş, 1993 satırlık Python kodu (`src` 946, `eval` 252, `tests` 734, `app.py` 61), 65 testi ve iki ayrı eval setiyle ölçülmüş yerel bir RAG sistemidir; denetim sonrası iki düzeltme turu 29 bulgunun 14'ünü kapattı (kaynak: facts.md "Depo istatistikleri", "Test", "Hâlâ açık denetim bulguları"). Aşağıdaki iddialar yalnız facts.md ve depo dosyalarına dayanır; "oturum ölçümü" etiketli olanlar öyle belirtilmiştir.

### Beceri kanıt tablosu

| Beceri | Kanıt (dosya/sayı) | CV cümlesi |
|---|---|---|
| Hibrit arama (BM25 + vektör, RRF) | `src/hybrid.py`, `src/bm25_index.py`, `src/vector_index.py`; gömme modeli `BAAI/bge-m3` (`src/config.py:9`) | BM25 ve yoğun vektör aramayı ağırlıklı RRF ile birleştiren yerel kod arama motoru geliştirdim. |
| Kod bilgili parçalama | `src/chunk_py.py` (`ast`), `src/chunk_md.py`; httpx'te 862 parça (oturum ölçümü) | Python kodunu `ast` ile sembol bazında (sınıf, metot, fonksiyon) parçalayan ve satır aralığı veren bir hat yazdım. |
| Değerlendirme tasarımı | `eval/questions.json` (59 soru, dondurulmuş), `eval/tuning.json` (36 soru), `eval/run_eval.py`; hit@1, hit@5, MRR@10 | Ayar ve test setlerini ayırıp ölçüt tabanlı retrieval değerlendirmesi kurdum; sonuçlar deterministik (3 tekrar, aynı md5). |
| Parametre ayarı ve aşırı uyum kontrolü | `eval/tune_rrf.py`: 36 kombinasyon; skor 0.7355 → 0.7880 (+0.0526) yalnız ayar setinde | RRF parametrelerini ayrı bir sette taradım; ana seti ayar için kullanmadım. |
| Test yazma | 65 test, `65 passed in 1.12s` (`uv run pytest -q`); `tests/` 734 satır, 10 dosya | Chunker, tokenizer, RRF, tarayıcı, indeksler, üretici ve eval eşleştirme için 65 test yazdım. |
| E2E test | `e2e/app.spec.ts` (8 `test(`), `playwright.config.ts`; merge 77b5f78; önceki 8/8 geçti oturum ölçümü | Streamlit arayüzü için 8 Playwright E2E testi ekledim ve ana dala birleştirdim. |
| Güvenlik/kalite denetimi yapma ve düzeltme | `denetim/DENETIM-2026-11-21.md`: 29 bulgu (3 high, 13 medium, 13 low); iki turda 14'ü kapandı: H1-H3, M1-M7, M9, M13, L3, L7 (`ba50a40`, `b010685`, `132f7d8`, `1bee4f4`, `333fd9a`, `2edbf3c`, `5a8f7b9`, `8fb632d`) | Projeyi çok boyutlu denetleyip 3 high ve 9 medium dahil 14 bulguyu düzelttim: prompt injection, atıf uyumu, pickle yerine JSON, sembolik bağlantı kaçışı. |
| LLM üretim güvenliği | `src/generator.py`: çit taşması/enjeksiyon, `fix_citations`, `strip_images`; tuzak sorular 6/6 reddedildi, yanlış red 0/36 (denetim) | Bağlam enjeksiyonuna karşı çitleme ve atıf doğrulaması ekledim; tuzak sorularda 6/6 doğru red gözlendi (denetim ölçümü). |
| Doğrulama disiplini | İki düzeltme turu; Neon çapraz incelemesi (2. turda 7 bulgu, doğrulananlar 5a8f7b9 ve 8fb632d ile düzeltildi); her Python düzeltmesi geri alınınca test kırıldı (1. tur 3/4 düzeltme/6; 2. tur scanner 4, chunk_py 1, bm25 3, vector 1+1) (hepsi oturum ölçümü) | Düzeltmeleri başka modelin incelemesinden geçirip geri alarak testlerin kırıldığını gösterdim. |
| Tekrarlanabilir eval | `eval/README.md`, `eval/run_eval.py`: iki repo sabit commit'e (1d45820, 7cff5f7) sabitlendi, 405bdb7; sonuçlar sabitlemeden önceki tabloyla aynı (oturum ölçümü; eval yeniden koşulmadı) | Eval'i iki repoyu sabit commit'e sabitleyerek tekrarlanabilir yaptım. |
| Yerel LLM ve arayüz | Ollama `qwen3.5:4b` (3.3 GB), Streamlit 1.67.0, `baslat.sh`/`durdur.sh` | Bulut kullanmadan Ollama ve Streamlit ile çalışan, tek tıkla açılan arayüz kurdum. |

### Hazır CV maddeleri

1. Python/Markdown depoları için BM25 + bge-m3 vektör aramayı ağırlıklı RRF ile birleştiren yerel RAG asistanı geliştirdim; 59 soruluk dondurulmuş sette hit@5 0.92, MRR@10 0.796 ölçtüm (kaynak: `eval/results.md`).
2. RRF parametrelerini ayrı 36 soruluk sette taradım (36 kombinasyon); ayar skorunu 0.7355'ten 0.7880'e çıkardım ve ana seti ayara karıştırmadım (kaynak: `eval/tuning_results.md`).
3. Projeyi 9 puanlı boyutta (test paketi, hatalar, güvenlik, çapraz inceleme, kod kalitesi, E2E, erişilebilirlik, performans, RAG) denetleyip iki turda 29 bulgunun 14'ünü kapattım (3 high, 9 medium dahil); her düzeltmeyi çapraz model incelemesi ve geri alma ile doğruladım; test sayısı 36'dan 65'e çıktı (kaynak: `denetim/DENETIM-2026-11-21.md`; `facts.md` "Denetim sonrası düzeltmeler"; `uv run pytest -q`). Geri alma sonuçları oturum ölçümüdür.

Not: denetim tablosunda 10 satır vardır; senior-qa satırı puanlanmadı (React/Next.js'e özgü), bu yüzden 9 puanlı boyut yazıldı. Düzeltme sonrası kapsama yüzdesi ve yeniden denetim puanı yoktur; CV'ye yazılmamalıdır. Bölüm 06'daki 7.4/10 yazarın yargısıdır, denetim puanı olarak sunulmamalıdır.

### Portföy özeti (2 cümle)

Kod Repo Asistanı, Python ve Markdown depolarında sembol bazlı parçalama, BM25 + bge-m3 hibrit arama ve atıflı Türkçe cevap üreten, tamamen yerel çalışan bir RAG sistemidir. Hibrit sıralama ve cevap kalitesi, sabit commit'lere bağlı soru setleri ve çok boyutlu bir denetimle ölçülmüş; iki düzeltme turu çapraz model incelemesi ve geri alma doğrulamalı testlerle yapılmış, hibritin vektörden belirgin üstün olmadığı ile 15 açık bulgu dürüstçe raporlanmıştır.

### Görüşme konuşma noktaları

| Konu | Anlatılacak olgu | Kanıt |
|---|---|---|
| Neden hibrit? | İsim sorularında BM25 güçlü (MRR 0.944), kavramsal sorularda vektör güçlü (hit@5 0.79 vs BM25 0.45) | `eval/results.md` |
| Hibrit gerçekten daha mı iyi? | Dürüst cevap: ana sette hibrit ve vektör neredeyse aynı (MRR@10 0.796 / 0.794; hit@5 için 1 iyi / 0 kötü / 58 aynı) | `denetim/DENETIM-2026-11-21.md` M9 |
| Aşırı uyum | Tuning ayrı sette; ana set ayar için kullanılmadı; fark ayar setinde +0.0526 | `eval/tuning_results.md` |
| Ölçüm bulduğu hata | Denetimde 36 cevabın %25'inde geçersiz atıf; `fix_citations` sonrası %0 (12 soru + 2 tuzak, oturum ölçümü) | denetim H2; facts.md "Oturum ölçümleri" |
| Güvenlik | Prompt injection (H1) bulundu ve düzeltildi; Neon'un "critical" pickle bulgusu doğrulayıcıda low, hakemde medium oldu (M1) ve sonra JSON'a çevrildi (132f7d8); sembolik bağlantı kaçışı da kapandı (M2) | denetim bölüm 3; facts.md |
| Neden iki model çapraz inceleme? | Aynı modelin kendi çıktısını onaylama riski; Neon farklı bulgular getirdi, biri doğrulamada elendi | denetim bölüm 3 ve 5 |
| Ajanlarla geliştirme | Süreç şeffaf anlatılmalı: planda iş bölümü ajanlara ayrılmış; kodu yazan ve inceleyen ayrı ajanlar | `plan.md` "İş bölümü"; denetim bölüm 5 |
| Düzeltmeleri nasıl doğruladın? | Test yaz, düzeltmeyi geri al, testin kırıldığını gör; Neon'a ayrı inceleme yaptır. Sayılar oturum ölçümü | facts.md "Denetim sonrası düzeltmeler" |
| Ne yapardın? | Yol haritasının ilk maddeleri: atıf eval'ini kalıcı yap, `pipeline`/`cli` entegrasyon testi, Playwright'ı yeniden koş; ardından hibrit-vektör için yeni soru seti | bölüm 09 |

### Bu proje neyi kanıtlamaz

Aşağıdaki sınırlar CV'de abartı yapılmasını önler ve görüşmede sorulursa açıkça söylenmelidir.

| İddia | Neden kanıtlanmıyor | Kaynak |
|---|---|---|
| "Hibrit vektörden iyidir" | Fark gürültü düzeyinde: RR farkı ort. +0.0014 (n=59); KisiselNotArama kavramsalda hibrit MRR 0.560, vektör 0.601. README yorumu düzeltildi (2edbf3c) ama ölçüm sınırı duruyor | denetim M9; `README.md` |
| "Genel retrieval kalitesi yüksek" | Yalnız 2 repo, 59 soru; yeni repo veya dil için ölçüm yok | `eval/results.md` |
| "Cevap kalitesi ölçüldü" | Üretim ölçümü 12 soruluk alt küme; atıf önce/sonra ölçümü depoda kalıcı değil (doğrulanmadı) | denetim bölüm 4; facts.md "Doğrulanmadı" |
| "Üretime hazır" | Tek kullanıcı, localhost, yük testi yok, web API yok | denetim bölüm 4 |
| "Kapsama yüksek" | Denetim anında %59; `pipeline`, `cli`, `vector_index` %0. 65 teste çıkıldı ama kapsama yeniden ölçülmedi; `pipeline`, `cli`, `eval/tune_rrf` hâlâ testsiz (M10) | denetim "Mevcut test paketi"; facts.md |
| "Çok dilli kod desteği" | Yalnız `.py` ve `.md` (`src/config.py` `EXTENSIONS`) | `src/config.py` |
| "Geliştirmeyi tek başıma yazdım" | Geliştirme ajan ekibiyle yapıldı; kişisel katkı (tasarım kararları, kabul, denetim yönlendirmesi) ayrıca belirtilmeli | `plan.md` "İş bölümü" |
| "Performans ölçüldü" | Değerler denetimde tek makinede ölçüldü, bu çalışmada yeniden ölçülmedi | facts.md "Doğrulanmadı" |
| "Test sayısı 36'dan 65'e artışı hep yeni özellik" | Artışın dökümü commit bazında ayrıştırılmadı | facts.md "Doğrulanmadı" |
| "Düzeltmeler bağımsız olarak yeniden denetlendi" | Yeniden denetim yapılmadı; bölüm 06'daki 7.4/10 yazarın yargısı, geri alma sayıları oturum ölçümü | bölüm 06; facts.md "Doğrulanmadı" |
| "Tüm bulgular kapandı" | 15 bulgu açık: M8, M10, M11, M12, L1, L2, L4, L5, L6, L8-L13 | facts.md "Hâlâ açık denetim bulguları" |

Bu bölümdeki puan veya genel nitelemeler "değerlendirme" niteliğindedir; sayılar yukarıdaki kaynaklardan alınmıştır.


## 11. Ekler

Bu ek, 56 takipli dosyanın haritasını, kurulum ve çalıştırma komutlarını, sözlüğü, eval şemasını ve olgu kaynaklarını toplar (kaynak: `git ls-files | wc -l` çıktısı 56, facts.md). Yollar proje köküne görelidir.

### Dosya haritası

| Yol | Amaç |
|---|---|
| `plan.md` | Tasarım planı: kapsam, klasör yapısı, veri modeli, adımlar, v2 fikirleri |
| `README.md` | Kurulum, kullanım, eval sonuç tablosu |
| `pyproject.toml`, `uv.lock` | Bağımlılıklar ve kilit dosyası (Python `>=3.12`) |
| `app.py` | Streamlit arayüzü (repo yolu, indeksleme, soru, mod seçimi, kaynaklar) |
| `baslat.sh`, `durdur.sh` | Ollama + Streamlit'i başlat (8501-8510 arası boş port) ve yalnız bu projenin Streamlit'ini kapat; süreç kimliği `data/streamlit.pid` dosyasında |
| `e2e/app.spec.ts`, `playwright.config.ts` | Playwright E2E testleri (8 test) ve yapılandırma |
| `package.json`, `package-lock.json`, `tsconfig.json` | Playwright (Node) bağımlılıkları |
| `src/config.py` | Yollar, model adları, arama parametreleri, dışlama kalıpları |
| `src/scanner.py` | Repoyu tarar; dışlama kuralları, dosya boyutu sınırı |
| `src/chunk.py`, `src/chunk_py.py`, `src/chunk_md.py` | `CodeChunk` ve dile göre yönlendirme; Python (`ast`) ve Markdown parçalama |
| `src/embedder.py` | bge-m3 gömme (GPU/CPU) |
| `src/vector_index.py` | Numpy vektör indeksi (bellek önbelleği) |
| `src/bm25_index.py` | Kod tokenizer'lı BM25 indeksi (JSON olarak saklanır) |
| `src/hybrid.py` | Ağırlıklı RRF ve aday havuzu |
| `src/pipeline.py` | İndeks oluşturma ve yükleme |
| `src/generator.py` | Bağlam, prompt, atıf doğrulama ve düzeltme (Ollama) |
| `src/cli.py` | `index`, `search`, `ask`, `eval` komutları |
| `eval/questions.json` | Ana eval seti: 59 soru, dondurulmuş |
| `eval/tuning.json` | Ayar seti: 36 soru |
| `eval/run_eval.py`, `eval/tune_rrf.py` | Eval çalıştırıcı ve RRF ızgara taraması |
| `eval/results.md`, `eval/tuning_results.md` | Üretilmiş sonuç tabloları |
| `eval/README.md` | Eval şeması ve değişiklik kaydı |
| `tests/test_*.py` | 65 test: app, chunk_md, chunk_py, eval_match, generator, indexes, rrf, scanner, tokenizer |
| `denetim/DENETIM-2026-11-21.md` | Çok boyutlu denetim raporu |
| `.gitignore` | `data/`, `.venv/` vb. dışlama |

Git'e takipli olmayan yerler: `data/` (indeksler, `data/repos/kisiselnotarama` ve `data/repos/httpx` klonları, `data/streamlit.pid`, günlükler). `rapor/` ve `denetim/` takiplidir (`git ls-files`; 56 dosyaya dahil). E2E testleri master'dadır (merge 77b5f78); `denetim/playwright` dalı yerelde durur (kaynak: `git branch -a`).

### Komutlar

Tüm komutlar proje kökünden çalıştırılır (kaynak: `README.md`, `baslat.sh`, `durdur.sh`).

| Amaç | Komut |
|---|---|
| Kurulum | `uv sync` |
| LLM modeli (yalnız `ask` ve arayüz için) | `ollama pull qwen3.5:4b` |
| Eval reposu: httpx (commit `7cff5f7`) | `git clone https://github.com/encode/httpx data/repos/httpx && git -C data/repos/httpx checkout --detach 7cff5f7` |
| Eval reposu: kisiselnotarama (commit `1d45820`) | `git clone ../KisiselNotArama data/repos/kisiselnotarama && git -C data/repos/kisiselnotarama checkout --detach 1d45820` |
| Playwright kurulumu (E2E için) | `npm install` ve `npx playwright install chromium` (doğrulanmadı; `package.json` ve `playwright.config.ts` ile uyumlu) |
| E2E testi | `npx playwright test` (doğrulanmadı; bu turda koşulmadı) |
| İndeksle | `uv run python -m src.cli index --repo <repo-yolu>` |
| Ara | `uv run python -m src.cli search "<sorgu>" --repo <repo-yolu> --mode hybrid --k 5` |
| Cevap üret | `uv run python -m src.cli ask "<soru>" --repo <repo-yolu>` |
| Arayüz (elle) | `uv run streamlit run app.py` |
| Arayüz (tek tık) | `./baslat.sh` (Ollama ve Streamlit'i başlatır, boş portu seçer; varsayılan `http://localhost:8501`) |
| Arayüzü kapat | `./durdur.sh` (`data/streamlit.pid` ile doğrulanan Streamlit süreci; Ollama'ya dokunmaz) |
| Test | `uv run pytest -q` (çıktı: `65 passed in 1.12s`) |
| Ana eval | `uv run python -m src.cli eval` veya `uv run python eval/run_eval.py` (sonuç: `eval/results.md`) |
| Ayar seti eval | `uv run python eval/run_eval.py --set tuning` |
| RRF taraması | `uv run python eval/tune_rrf.py` (yalnız `eval/tuning.json`) |

Modlar: `bm25`, `vector`, `hybrid` (varsayılan). Eval LLM kullanmaz. Eval çalıştırmak için `data/repos/httpx` ve `data/repos/kisiselnotarama` klonları, ilgili commit'lere sabitlenmiş olarak gerekir (kaynak: `eval/README.md`); KisiselNotArama yolu kodda sabittir (denetim L10, açık).

### Eval şeması

Her soru `eval/questions.json` ve `eval/tuning.json` içinde bir JSON nesnesidir (kaynak: `eval/README.md`).

| Alan | Tür | Anlam |
|---|---|---|
| `id` | metin | Örn. `kna-01`, `hx-17`, `tune-01` |
| `repo` | `kisiselnotarama` veya `httpx` | Sorunun ait olduğu depo |
| `type` | `name` veya `conceptual` | İsim sorusu veya kavramsal soru |
| `question` | metin (Türkçe) | Soru metni |
| `expected` | liste | Her öğe `{path, symbol}`; `path` repo köküne göre, `symbol` `Sinif.metot`, fonksiyon adı veya Markdown başlığı |

Doğru sayılma: getirilen parçalardan biri `expected` içindeki herhangi bir `(path, symbol)` ile eşleşirse. Metrikler hit@1, hit@5 ve MRR@10'dur; ayrıntı `eval/run_eval.py` ve `tests/test_eval_match.py` içindedir.

### Sözlük

| Terim | Anlam |
|---|---|
| RAG | Retrieval-Augmented Generation: önce ilgili parçaları bul, sonra LLM bu parçalara dayanarak cevap versin |
| BM25 | Sözcük eşleşmesine dayalı klasik sıralama; burada kod adlarını bölen özel tokenizer ile |
| Vektör (yoğun) arama | Metni gömme modeliyle (`BAAI/bge-m3`) sayı vektörüne çevirip benzerlik arama |
| Hibrit arama | BM25 ve vektör sıralamalarının birleştirilmesi |
| RRF | Reciprocal Rank Fusion: `score = Σ w_i/(k+rank)`; seçilen `w_bm25=0.3`, `w_vec=1`, `k=30`, `candidates=20` |
| Parça (chunk) | Dosyanın sınıf, metot, fonksiyon veya Markdown başlığı gibi tek birimi (`CodeChunk`) |
| Atıf | Cevapta `[yol:başlangıç-bitiş]` biçiminde kaynak gösterimi |
| hit@k | İlk k sonuçtan en az biri doğruysa 1 |
| MRR@10 | İlk doğru sonucun sırasının tersinin ortalaması, ilk 10 içinde |
| name / conceptual | Sembol adıyla sorulan soru / davranışı anlatan soru |
| Tuzak soru | Depoda cevabı olmayan soru; doğru davranış reddetmek |
| Prompt injection | Bağlam metninin içine gömülü talimatın modeli yönlendirmesi (H1) |
| Neon | Denetimde çapraz inceleme yapan Gemini modeli (`gemini-4-neon-high`) |
| Dondurulmuş set | Ayar için kullanılmayan, değiştirilmeyen ana soru seti |

### Kaynak ve olgu listesi

Rapordaki her sayı ilgili bölümde kaynağıyla birlikte verilir (özet: bölüm 01 "Temel sayılar"). Çelişki durumunda `rapor/facts.md` geçerlidir.

### Doğrulanmadı listesi

| Madde | Neyle doğrulanır |
|---|---|
| Atıf önce/sonra sayıları (%21,9 → %0; %35,7 → %21,4; %36,4 → %72,7) | Aynı 14 soruyla cevap üretim betiğini yeniden çalıştırmak (betik `eval/` içinde yok, M8) |
| Geri alma testlerinde kırılan test sayıları (1. tur: 3, 4 düzeltme, 6; 2. tur: scanner 4, chunk_py 1, bm25 3, vector 1+1) | Her düzeltmeyi geri alıp `uv run pytest` çalıştırmak |
| GitHub deposunun `code-repo-rag` adı ve public olması | Ağdan kontrol (yapılmadı) |
| Performans değerleri (0.3 / 21.7 / 23.9 ms, 7.4 sn, ~19 sn, RSS ~4.1 GB, VRAM 1.67 GB) | Ölçümü yeniden yapmak (bu çalışmada yapılmadı) |
| 36 → 65 test artışının dökümü | Denetim sonrası commit'lerde `git diff --stat tests/` ile ayrıştırmak |
| Düzeltme sonrası kapsama yüzdesi | `uv run pytest --cov` (bu çalışmada çalıştırılmadı) |
| `e2e/app.spec.ts` testlerinin güncel master ile geçmesi (8/8 eski sonuç) | `npx playwright test` çalıştırmak (bu turda koşulmadı) |
| Eval sonuçlarının sabitleme sonrası aynılığı | `uv run python -m src.cli eval` ile yeniden koşup `eval/results.md` farkına bakmak (bu turda yeniden koşulmadı) |
| Denetim etiketi "doğrulanmadı" olan bulgular (H3 önceki durumu, M5, M11, M12, L5, L6, L10, L11) | Tek tek yeniden üretme adımı |
