## Yönetici özeti

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


## 01. Proje tanımı ve kapsam

Kod Repo Asistanı, yerel bir Git reposunu sembol bazlı parçalayıp hibrit arama ve atıflı Türkçe soru-cevap sunan, 1789 satırlık Python projesidir (hesap: 897+252+579+61, kaynak: `rapor/facts.md`).

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
| Kütüphane ve CLI | `src/` | 13 Python dosyası, 897 satır: tarama, parçalama, indeks, hibrit arama, üretim |
| Arayüz | `app.py` | Streamlit sayfası, 61 satır |
| Değerlendirme | `eval/` | `run_eval.py`, `tune_rrf.py`; 59 soruluk ana set, 36 soruluk tuning seti |
| Eval sonuçları | `eval/results.md`, `eval/tuning_results.md` | Mod bazlı hit@1, hit@5, MRR@10; 36 kombinasyonlu ızgara |
| Test paketi | `tests/` | 9 dosya, 579 satır; 54 test geçti |
| Denetim raporu | `denetim/DENETIM-2026-11-21.md` | Çok boyutlu denetim, bulgu listesi (3 high, 13 medium, 13 low) |
| Plan ve kullanım | `plan.md`, `README.md` | Amaç, kapsam, kurulum, eval tablosu |

### Temel sayılar

| Ölçü | Değer | Kaynak |
|---|---|---|
| Git'e takipli dosya | 38 | `git ls-files \| wc -l` |
| Commit | 14 (2026-11-20 ile 2026-11-21) | `git rev-list --count HEAD` |
| `src/` | 13 dosya, 897 satır | `facts.md` |
| `eval/` | 2 dosya, 252 satır | `facts.md` |
| `tests/` | 9 dosya, 579 satır | `facts.md` |
| `app.py` | 61 satır | `wc -l app.py` |
| Python toplamı | 1789 satır | hesap: 897+252+579+61 |
| Test | 54 geçti, 1.49 sn | `uv run pytest -q` |
| Eval soru sayısı | 59 ana + 36 tuning | `eval/results.md`, `eval/tuning_results.md` |
| Hybrid, ana set | hit@5 0.92, MRR@10 0.796 | `eval/results.md` |

Not: 1.49 sn ve 54 test 2026-11-21 ölçümüdür; denetim anında test sayısı 36'ydı (kaynak: `denetim/DENETIM-2026-11-21.md`).


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
<text x="353.0" y="261" font-size="12" text-anchor="middle" fill="#1a1a1a">bm25.pkl</text>
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
| Tarayıcı | `src/scanner.py` | Repo dosyalarını listeler; dışlama ve boyut sınırı (300 000 bayt) | `config`, `git` |
| Parça modeli | `src/chunk.py` | `CodeChunk`, dile göre yönlendirme, gömme metni | `chunk_py`, `chunk_md` |
| Python parçalayıcı | `src/chunk_py.py` | `ast` ile sınıf, metot, fonksiyon parçaları; en çok 80 satır | `ast`, `config` |
| Markdown parçalayıcı | `src/chunk_md.py` | Başlığa göre bölme | `chunk` |
| Gömme | `src/embedder.py` | bge-m3 yükleme, cihaz seçimi (GPU/CPU), GPU bırakma | sentence-transformers, torch |
| Vektör indeksi | `src/vector_index.py` | `vecs.npy` + `chunks.json`; kosinüs arama; geçici dizinle atomik yazma | numpy |
| BM25 indeksi | `src/bm25_index.py` | Kod tokenizer'ı (büyük/küçük harf ve alt çizgi bölme), BM25 arama; `bm25.pkl` | rank-bm25, pickle |
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
| BM25 indeksi `pickle` ile | Basit, tokenlanmış corpus'u olduğu gibi saklar | Güvenilmeyen dosya yüklenirse risk; kaynak yerel yazım (denetimde low, M1) |
| Modüller kopyalanıp uyarlandı, ortak paket yok | Projeler bağımsız kalır (kaynak: `plan.md`) | Kod tekrarı |


## 03. Teknolojiler

Proje 6 çalışma zamanı ve 1 geliştirme bağımlılığı kullanır; sürümler `uv.lock` ile sabitlenmiştir (kaynak: `pyproject.toml`, `uv.lock`). Python ortamı 3.12.16'dır (kaynak: `uv run python -V`).

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
| Playwright | doğrulanmadı; depoda yok (`denetim/playwright` dalında, 8 test, oturum ölçümü) | E2E arayüz testi | Denetim sırasında kullanıldı, master'a birleştirilmedi |

### Standart kütüphane

`argparse`, `ast`, `json`, `pickle`, `hashlib`, `subprocess` (git çağrısı), `shutil`, `re`, `fnmatch` kullanılır (kaynak: `grep -n "^import" src/*.py`). Linter veya tip denetleyici `pyproject.toml`'da tanımlı değildir.


## 04. Geliştirme süreci

Proje 14 commit'te, iki takvim gününde (2026-11-20 ve 2026-11-21) beş aşamada geliştirildi (kaynak: `git log --format='%h %ad %s' --date=iso`; `facts.md`: commit sayısı 14). İlk commit 2500377 ("plan"), son commit 1f2b19a'dır. 10 commit ilk gün, 4 commit ikinci gün atıldı.

### Aşamalar

| Aşama | Dönem | Çıktı | Kilit karar |
|---|---|---|---|
| 0. Plan | 20 Kas 15:33 (1 commit: 2500377) | Plan commit'i | Yerel, bge-m3 + BM25 + Ollama kurgusu |
| 1. Faz 1: iskelet | 20 Kas 15:34-15:35 (2: 893f3c6, b980049) | `config`, `scanner`, `chunk`, `chunk_md`, `embedder`, `vector_index`; dondurulmuş `eval/questions.json` (59 soru) | Eval seti kod yazılmadan önce dondurulur, ayar için ayrı set kullanılır (`eval/README.md`) |
| 2. Faz 2: arama | 20 Kas 15:38 (1: 6dff6cb) | Python `ast` parçalama, kod BM25 tokenizer/indeksi, RRF hibrit arama + testler | Kod için özel tokenizer; sıralı birleştirme (RRF) |
| 3. Faz 3 ve ayar | 20 Kas 15:41-16:41 (6: 4fc30b8, 48ac9bc, 93dd096, dccbc70, b74b758, 756e4df) | Pipeline, generator, CLI, eval, `app.py`, README; tuning seti 36 soru; ağırlıklı RRF; `baslat.sh`/`durdur.sh` | RRF parametreleri yalnız tuning setiyle seçildi, ana sete bakılmadı (`eval/tuning_results.md`) |
| 4. Denetim ve düzeltme | 21 Kas 12:52-13:01 (4: 8f35f48, ba50a40, b010685, 1f2b19a) | Denetim raporu; H1, H2, H3 düzeltmeleri; Neon incelemesi sonrası düzeltme | Her düzeltme ayrı commit; Neon çapraz incelemesi (`denetim/DENETIM-2026-11-21.md`) |

### Zaman çizelgesi

<figure>
<svg viewBox="0 0 720 244" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Geliştirme zaman çizelgesi" font-family="DejaVu Sans, sans-serif" style="max-width:100%;height:auto"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs><rect x="4" y="20" width="526" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>
<text x="267.0" y="38" font-size="12" text-anchor="middle" fill="#1f3a68" font-weight="bold">20 Kasım 2026 (10 commit)</text>
<rect x="564" y="20" width="124" height="26" rx="5" fill="#e6ebf3" stroke="#9aa7bd"/>
<text x="626.0" y="38" font-size="12" text-anchor="middle" fill="#1f3a68" font-weight="bold">21 Kasım 2026</text>
<line x1="66.0" y1="82" x2="468.0" y2="82" stroke="#1f3a68" stroke-width="2.5"/>
<line x1="626.0" y1="82" x2="626.0" y2="82" stroke="#1f3a68" stroke-width="2.5"/>
<line x1="468.0" y1="82" x2="539.0" y2="82" stroke="#1f3a68" stroke-width="2.5"/>
<line x1="555.0" y1="82" x2="626.0" y2="82" stroke="#1f3a68" stroke-width="2.5"/>
<path d="M539.0,90 L545.0,74 M549.0,90 L555.0,74" stroke="#c0392b" stroke-width="2" fill="none"/>
<text x="547.0" y="108" font-size="12" text-anchor="middle" fill="#c0392b" font-weight="bold">~20 sa</text>
<text x="547.0" y="123" font-size="12" text-anchor="middle" fill="#c0392b">boşluk</text>
<circle cx="66.0" cy="82" r="14" fill="#1f3a68"/>
<text x="66.0" y="86" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">1</text>
<line x1="66.0" y1="96" x2="66.0" y2="124" stroke="#9aa7bd"/>
<rect x="6" y="124" width="120" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="66.0" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">0. Plan</text>
<text x="66.0" y="157" font-size="12" text-anchor="middle" fill="#1a1a1a">15:33</text>
<text x="66.0" y="172" font-size="12" text-anchor="middle" fill="#1a1a1a">2500377</text>
<text x="66.0" y="187" font-size="12" text-anchor="middle" fill="#1a1a1a">"plan"</text>
<circle cx="200.0" cy="82" r="14" fill="#1f3a68"/>
<text x="200.0" y="86" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">2</text>
<line x1="200.0" y1="96" x2="200.0" y2="124" stroke="#9aa7bd"/>
<rect x="140" y="124" width="120" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="200.0" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">1. İskelet</text>
<text x="200.0" y="157" font-size="12" text-anchor="middle" fill="#1a1a1a">15:34-15:35</text>
<text x="200.0" y="172" font-size="12" text-anchor="middle" fill="#1a1a1a">b980049: soru</text>
<text x="200.0" y="187" font-size="12" text-anchor="middle" fill="#1a1a1a">seti donduruldu</text>
<circle cx="334.0" cy="82" r="14" fill="#1f3a68"/>
<text x="334.0" y="86" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">1</text>
<line x1="334.0" y1="96" x2="334.0" y2="124" stroke="#9aa7bd"/>
<rect x="274" y="124" width="120" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="334.0" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">2. Arama</text>
<text x="334.0" y="157" font-size="12" text-anchor="middle" fill="#1a1a1a">15:38</text>
<text x="334.0" y="172" font-size="12" text-anchor="middle" fill="#1a1a1a">6dff6cb:</text>
<text x="334.0" y="187" font-size="12" text-anchor="middle" fill="#1a1a1a">hibrit arama</text>
<circle cx="468.0" cy="82" r="14" fill="#1f3a68"/>
<text x="468.0" y="86" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">6</text>
<line x1="468.0" y1="96" x2="468.0" y2="124" stroke="#9aa7bd"/>
<rect x="408" y="124" width="120" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="468.0" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">3. Faz 3 + ayar</text>
<text x="468.0" y="157" font-size="12" text-anchor="middle" fill="#1a1a1a">15:41-16:41</text>
<text x="468.0" y="172" font-size="12" text-anchor="middle" fill="#1a1a1a">dccbc70:</text>
<text x="468.0" y="187" font-size="12" text-anchor="middle" fill="#1a1a1a">ağırlıklı RRF</text>
<circle cx="626.0" cy="82" r="14" fill="#1f3a68"/>
<text x="626.0" y="86" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">4</text>
<line x1="626.0" y1="96" x2="626.0" y2="124" stroke="#9aa7bd"/>
<rect x="566" y="124" width="120" height="72" rx="5" fill="#f4f6fa" stroke="#1f3a68" stroke-width="1.2"/>
<text x="626.0" y="142" font-size="12" text-anchor="middle" fill="#1a1a1a" font-weight="bold">4. Denetim</text>
<text x="626.0" y="157" font-size="12" text-anchor="middle" fill="#1a1a1a">12:52-13:01</text>
<text x="626.0" y="172" font-size="12" text-anchor="middle" fill="#1a1a1a">1f2b19a: Neon</text>
<text x="626.0" y="187" font-size="12" text-anchor="middle" fill="#1a1a1a">düzeltmeleri</text>
<text x="6" y="232" font-size="12" text-anchor="start" fill="#555">Dairedeki sayı faz başına commit sayısıdır (toplam 14). Eksen ölçekli değildir; saatler commit zamanıdır.</text></svg>
<figcaption>Şekil 2. Geliştirme zaman çizelgesi: 14 commit, iki gün, beş aşama; fazlar 1-3 aynı öğleden sonra 68 dakikada commit'lendi, denetim ve düzeltme ertesi gün 9 dakikada.</figcaption>
</figure>

### Süreç notları

- Fazlar 1-3 aynı öğleden sonra 68 dakikada commit'lendi (15:33-16:41). Commit zamanları yazım süresini değil, toplu commit alışkanlığını yansıtıyor olabilir; gerçek çalışma süresi doğrulanmadı.
- Denetimden düzeltmelere 9 dakika geçti (12:52 -> 13:01); düzeltme commit'lerinin her biri yeni testlerle geldi. Test sayısı denetimde 36, bugün 54 (`facts.md`; artışın commit bazında dökümü doğrulanmadı).
- Düzeltmelerin geri alma doğrulaması (oturum ölçümü) bölüm 06'da verilir.
- Denetim sonrası düzeltmeler `master`'da; `denetim/playwright` dalındaki 8 E2E test (commit 9b57b5d) birleştirilmedi (`facts.md`).


## 05. Değerlendirme ve testler

Test paketi 54 testten oluşuyor ve 54'ü geçiyor (`54 passed in 1.49s`; kaynak: `uv run pytest -q`, 2026-11-21). Retrieval ölçümü 59 soruluk dondurulmuş sette, ayar 36 soruluk ayrı sette yapıldı; üretim kalitesi depoda kalıcı olarak ölçülmüyor.

### Test paketi

Denetim anında paket 36 testti, kapsama %59 (750 ifade, 309 kaçırılan; kaynak: `denetim/DENETIM-2026-11-21.md`). Sonraki kapsama ölçülmedi; aşağıdaki kapsama sütunu denetim anına aittir.

| Test alanı | Test sayısı | Kapsam |
|---|---|---|
| `tests/test_generator.py` | 16 | Bağlam biçimi, çit taşması, atıf doğrulama/düzeltme; denetimde `generator` %78 |
| `tests/test_chunk_py.py` | 8 | Python `ast` parçalama; `chunk_py` %95 |
| `tests/test_eval_match.py` | 7 | Eval eşleştirme kuralı |
| `tests/test_tokenizer.py` | 7 | Kod BM25 tokenizer; `bm25_index` %94 |
| `tests/test_rrf.py` | 6 | RRF birleştirme; `hybrid` %100 |
| `tests/test_app.py` | 5 | `app.py` yardımcıları |
| `tests/test_chunk_md.py` | 3 | Markdown parçalama; `chunk_md` %95 |
| `tests/test_scanner.py` | 2 | Dosya tarama; `scanner` %91 |
| Toplam | 54 | Dosya başına `def test` sayımı (kaynak: `grep -c "def test" tests/*.py`) toplamı 54 ile uyumlu |

Denetimde kapsama %0 olan modüller: `cli`, `pipeline`, `vector_index`, `eval/tune_rrf`; `embedder` %25 (kaynak: `denetim/DENETIM-2026-11-21.md`). Uçtan uca akış için entegrasyon testi yok (bulgu M10).

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
| E2E (Playwright) | 8/8 geçti, dal `denetim/playwright` (9b57b5d) | Oturum ölçümü; master'a birleştirilmedi; "İndeksle" başarı yolu test edilmedi |
| Bağımlılık güvenliği | pip-audit: "No known vulnerabilities found" | Denetim raporu; torch+cu132 denetim dışı |
| Performans (httpx, 862 parça) | Sıcak arama medyanı: bm25 0.3 ms, vector 21.7 ms, hybrid 23.9 ms (p95 37 ms) | Oturum ölçümü; yeniden ölçülmedi |


## 06. Çok yönlü kalite değerlendirmesi (puanlı)

Ağırlıklı genel puan, denetim anı için 6.9/10; düzeltmeler sonrası yargıma dayalı tahmin 7.2/10. Puanlar `denetim/DENETIM-2026-11-21.md` (2026-11-21, tam mod, kapsam commit 756e4df) üzerine kuruludur. Denetim puanları değiştirilmemiştir. Düzeltme sonrası değerlendirme ayrı bir tabloda ve açıkça "değerlendirme" etiketiyle verilir.

### Yöntem ve sınırlar

Denetim her boyutu ayrı alt ajana verdi; hata ve güvenlik bulguları ikinci modelle (Neon) çapraz kontrol edildi. Hakem olarak gpt-oss-120b-medium 2 çağrıda kullanıldı (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 5). Denetim kendi notunda şunu söyler: puanlar ajanların yargısıdır, kanıtlı bulgu puandan üstündür (bölüm 6).

- Denetimin 9 puanlı boyutu: test paketi, hatalar, güvenlik, Neon çapraz inceleme, kod kalitesi/mimari, E2E, erişilebilirlik, performans, LLM/RAG cevap kalitesi. Test stratejisi (senior-qa) React/Next.js'e özgü olduğu için puanlanmadı.
- Bu rapordaki 10 boyut denetimin boyutlarıyla birebir örtüşmez. Eşleme ve türetme kuralı aşağıdaki tabloda açıktır.
- "†" işaretli iki boyut (dokümantasyon, teslime hazırlık) denetimde puanlanmadı. Bunlar bu raporun yazarının değerlendirmesidir.

### Puan tablosu (denetim anı)

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
| Teslime hazırlık † | %10 | 6 | Değerlendirme: denetim anında critical 0 ama high 3 açık; Playwright testleri `master`'a birleştirilmedi (`denetim/playwright`, 9b57b5d) | Denetim anında 3 high ve 13 medium bulgu açık; kurulum `torch` cu132 indeksine bağlı (`pyproject.toml`) |
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

### Denetimden sonra düzeltilenler

Denetim sonrası 3 commit yalnız `app.py` ve `src/generator.py` dosyalarını değiştirdi (kaynak: `git diff --stat 756e4df HEAD -- src app.py durdur.sh baslat.sh pyproject.toml`). Diğer bulgular kodda aynen duruyor.

| Commit | Kapattığı bulgu | Kod kanıtı | Geri alma doğrulaması (oturum ölçümü) |
|---|---|---|---|
| ba50a40 | H3, M7, M13 | `app.py`: "LLM cevabı üret" onay kutusu, `st.cache_resource` | 3 test kırıldı |
| b010685 | H1, H2, L3 | `src/generator.py`: `_fence`, `fix_citations`, `strip_images`, ters aralık | 4 düzeltme tek tek kapatıldı, her biri ≥1 test kırdı |
| 1f2b19a | Neon incelemesi: kod içinde atıf/boşluk dönüşümü, blok aralığı, önbellek anahtarı | `src/generator.py`, `app.py` | 6 test kırıldı |

- Test sayısı 36'dan 54'e çıktı (kaynak: `uv run pytest -q`, `54 passed in 1.49s`). `def test` sayımı da 54 (kaynak: `grep -c "^def test" tests/*.py`). Artışın commit bazında dökümü doğrulanmadı.
- Geri alma sonuçları oturum ölçümüdür; depoda ölçüm çıktısı yok. Doğrulamak için düzeltme geri alınıp `uv run pytest` tekrarlanmalı.
- Atıf kalitesi önce/sonra sayıları (oturum ölçümü, 14 cevap) bölüm 05 "Üretim (cevap) kalitesi" tablosundadır; örneklem küçük ve tek koşulu.
- Hâlâ açık (kodda doğrulandı): M1 (`src/bm25_index.py:122` `pickle.load`), M2 (`src/scanner.py` `is_file()` sembolik bağlantıyı izler), M3 (`src/chunk_py.py:105` `splitlines()`), M4 (`durdur.sh:4` geniş `pgrep`). M8 (eval'de üretim metriği yok) ve M10 (`pipeline`/`cli` testi yok): `eval/` altında üretim betiği yok, `tests/` altında `test_pipeline` ya da `test_cli` yok.

### Düzeltme sonrası değerlendirme (yazarın yargısı)

Bu tablo denetim puanı değildir. Yalnız kodda ya da oturum ölçümünde kanıtı olan boyutlar değiştirildi; yeniden denetim yapılmadı.

| Boyut | Denetim | Değerlendirme | Kanıt ve sınır |
|---|---|---|---|
| Doğruluk / kalite | 6.5 | 7.0 | Oturum ölçümü: geçersiz atıf %21,9 → %0. 14 cevaplık tek koşu; retrieval değişmedi, depoda ölçüm yok, bu yüzden yalnız +0.5 |
| Test / ölçüm | 6 | 6.5 | 36 → 54 test, düzeltmeler geri alınarak test ile bağlandı (oturum ölçümü). Kapsama yeniden ölçülmedi; `pipeline`/`cli`/`vector_index` hâlâ test dosyasız |
| Kullanılabilirlik | 7 | 7.5 | H3 ve M13 kodda kapalı (`app.py`), `tests/test_app.py` 5 test. E2E ve a11y taraması yeniden çalıştırılmadı |
| Teslime hazırlık † | 6 | 7 | H1, H2, H3 kapandı (kod + oturum ölçümü). Playwright dalı hâlâ birleşmedi; M1, M2 açık |
| Güvenlik, performans, mimari, kod, dok., bakım | değişmedi | değişmedi | H1 kapandı ama M1/M2/L5 açık; M6 kodda duruyor; M7 kapandı ama yeniden ölçülmedi |

Ağırlıklı toplam değerlendirmesi: 719/100 = 7.19, yani 7.2/10 (hesap: ağırlıklar yukarıdaki tablodan). Bu rakam "oturum ölçümü" ve yazarın yargısına dayanır; yeniden denetimle doğrulanmadı. Doğrulamak için `/denetmen` hızlı modu ya da aynı 14 soruluk üretim ölçümü tekrarlanmalı.

### Kontrol edilmeyenler

Denetim şunları kapsamadı: torch+cu132 bağımlılık taraması, görsel ekran görüntüsü incelemesi, kontrast aracı, yük testi, "İndeksle" başarı yolunun E2E testi, 12 soru dışındaki tüm cevap seti ve JS/C# desteği (kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 4).


## 07. Sınırlamalar ve riskler

Denetimde 29 bulgu çıktı (0 critical, 3 high, 13 medium, 13 low; kaynak: `denetim/DENETIM-2026-11-21.md`, bölüm 2). Denetimden sonra H1, H2, H3, M7, M13, L3 ve Neon takip düzeltmeleri kapatıldı (`facts.md`); aşağıda yalnızca açık kalanlar var. Olasılık ve etki sütunları değerlendirmedir; kanıt sütunu denetim bulgu numarasıdır.

### Bilinen sınırlar (doğrulanmış)

Etkiye göre sıralı.

| Risk | Olasılık | Etki | Kanıt | Azaltma |
|---|---|---|---|---|
| Hibritin vektöre üstünlüğü kanıtlanmamış: hit@5 1/0/58, RR farkı +0.0014 | Yüksek | Orta (yanlış iddia riski) | M9, `eval/results.md` | README yorumunu "gürültü düzeyinde" yap; daha büyük soru seti |
| Üretim kalitesi kalıcı ölçülmüyor; atıf iyileşmesi yalnız oturum ölçümü | Yüksek | Orta | M8; `facts.md` "Doğrulanmadı" | Atıf metriklerini `eval/` içine kalıcı betik olarak ekle |
| Entegrasyon testi yok; `cli`, `pipeline`, `vector_index`, `eval/tune_rrf` kapsama %0 (denetim anı) | Yüksek | Orta | M10 | Sahte repo + sahte embedder ile pipeline testi |
| Sembolik bağlantılar takip ediliyor; güvenilmeyen repodaki dosya indekslenip arayüze gidebilir (yerel Ollama, dışarı çıkış yok) | Düşük | Orta | M2 (test ile doğrulandı) | `is_symlink()` atla veya `resolve().is_relative_to(root)` |
| `pickle.load` ile BM25 indeksi; `data/` değiştirilirse kod çalışabilir (saldırgan yolu yok) | Düşük | Orta | M1 (hakem: medium) | JSON/`np.savez` ile sakla |
| `splitlines()` form feed vb. karakterlerde satır numarasını kaydırıyor | Düşük | Orta (yanlış atıf satırı) | M3 (yeniden üretildi) | `split("\n")` kullan, test ekle |
| `vector_index.search` her sorguda diskten okuyor (hibrit süresinin %26'sı, cProfile) | Yüksek | Düşük | M6 (ölçüldü) | `load()` önbelleği |
| Hata yönetimi: sessiz `errors="replace"`, CLI'da ham traceback, loglama yalnız `embedder.py`'de | Orta | Düşük | M12 | Okunamayan dosyaları say; anlaşılır CLI hataları |
| Ek test ve araç boşlukları: `durdur.sh` tüm `streamlit run app.py` süreçlerini eşliyor (M4); `hybrid.embed_query` monkeypatch (M11); lint/tip yapılandırması yok (L11) | Orta | Düşük | M4, M11, L11 | Proje yoluyla daralt; `embed_fn` parametresi; ruff/mypy |
| İndeks adı yalnız HEAD commit'ine bağlı, bayat indeks mümkün (L1); sabit `.tmp`/`.old` dizinleri çakışabilir (L2) | Düşük | Düşük | L1, L2 | Çalışma ağacı durumunu anahtara kat; benzersiz geçici dizin |
| Performans: CLI'da her çağrı ~9 sn (model yükleme 7.4 sn); indeksleme ~19 sn (embed 11 sn); RSS tepe ~4.1 GB | Yüksek | Düşük | L8, L9; oturum ölçümü | Uzun ömürlü süreç; batch büyüt |
| Erişilebilirlik: `<html lang="en">` Türkçe içerikte (L13, çerçeveden düzeltilemez); ham expander başlığı (L12) | Yüksek | Düşük | L12, L13 (araç) | Başlık metnini düzelt; L13 için çerçeve kısıtı |

### Diğer açık bulgular

Düşük etkili, aşağıdakiler kısaca açık: M5 (`baslat.sh` 8501 portunu yanlış algılar, doğrulanmadı), L4 (`chunk_md` çit türü eşleşmesi, `# C#` kırpması; doğrulandı), L5 (`git` `core.fsmonitor`, doğrulanmadı), L6 (serbest repo yolu, boyut sınırı yok), L7 (`argsort`), L10 (`KisiselNotArama` yolu sabit kodlu).

### Kapatılanlar

Kapatılan bulgular, commit'leri ve geri alma doğrulaması bölüm 06 "Denetimden sonra düzeltilenler" tablosundadır.

### Olası riskler (doğrulanmamış)

| Risk | Olasılık | Etki | Kanıt | Azaltma |
|---|---|---|---|---|
| Küçük soru seti (59) nedeniyle sonuçların başka repolara genellenmemesi | Orta | Yüksek | Yalnız iki repo; JS/C# v2 kapsamında, denetlenmedi | Farklı repolardan soru ekle |
| Ayar kazancının (+0.0526) tuning seti dışında geçmemesi | Orta | Orta | Ayrı test seti yok | Üçüncü, dondurulmuş set |
| `fix_citations` geçersiz atıfı temizler ama cevabın doğruluğunu garanti etmez | Orta | Orta | Yalnız atıf biçimi ölçüldü | Cevap doğruluğu için ayrı değerlendirme |
| Küçük yerel model (`qwen3.5:4b`) bağlam dışı bilgi üretebilir | Orta | Orta | Tuzak sorular 6/6 reddedildi (küçük örnek) | Daha büyük tuzak seti |
| Güvenilmeyen repoda `git` komutları (L5) | Düşük | Orta | Doğrulanmadı | `-c core.fsmonitor=` |
| `torch+cu132` bağımlılık açıkları denetlenmedi | Düşük | Orta | pip-audit kapsamı dışı | Ayrı denetim |
| E2E testleri `master`'da yok; arayüz regresyonu fark edilmez | Orta | Düşük | `denetim/playwright` dalı birleştirilmedi | Dalı birleştir |


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
| **numpy `vecs.npy` + kaba kuvvet (float16)** | Ek bağımlılık yok, deterministik, indeks tek dosya (`src/vector_index.py`). 862 parçada vector arama medyanı 21.7 ms, embed ~10 ms dahil (oturum ölçümü) | Arama süresi parça sayısıyla doğrusal artar. Şu an her sorguda diskten okuyor (M6) | Küçük ve orta repo, tek kullanıcı |
| FAISS | Büyük koleksiyonda hızlı yaklaşık arama | Ek bağımlılık; küçük koleksiyonda kazanç yok | Parça sayısı on binlere çıkarsa |
| Chroma / Qdrant | Meta veri filtresi, kalıcı sunucu, çok kullanıcı | Süreç yönetimi ve bağımlılık ağırlığı | Çok repo ve filtreli arama gerekirse |

Geçiş şimdi gerekçesiz: `search` payı ~7 ms ve darboğaz diskten tekrar okumadır, depolama motoru değil. Önce M6'nın önbellek düzeltmesi yapılmalı. Geçiş koşulu (öneri): sıcak vector arama medyanı 100 ms'yi aşarsa.

### 3. Sözcük (lexical) arama

| Seçenek | Artı | Eksi | Ne zaman tercih edilir |
|---|---|---|---|
| **rank-bm25 0.2.2 + özel kod tokenizer'ı** | Saf Python, sıcak arama medyanı 0.3 ms (oturum ölçümü). name sorularında MRR 0.944 (`eval/results.md`) | İndeks `pickle` ile saklanıyor (M1). Büyük koleksiyonda bellek içi | Küçük repo, kod sembol adı araması |
| SQLite FTS5 | Disk tabanlı, `pickle` gerektirmez | Kod tokenizer'ı (`camelCase`, `snake_case` bölme) ayrıca uyarlanmalı | `pickle` riski kaldırılacaksa |
| Tantivy / Elasticsearch | Ölçeklenebilir, zengin sorgu | Kurulum ve işletme ağırlığı | Çok büyük depo ya da paylaşımlı sunucu |

Geçiş gerekçesi yok; BM25 hızı ve name kalitesi yeterli. M1 için ayrı bir önlem yeter: token listelerini JSON/`np.savez` ile saklayıp BM25'i yüklemede yeniden kurmak (denetim önerisi).

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

Denetimde açık kalan 22 bulgu ve `plan.md`'deki 4 v2 fikri 18 işe indirildi; "Şimdi" grubundaki 7 iş küçük veya orta eforla güvenlik, test ve doğrulanabilirlik boşluklarını kapatır. Sayım: `denetim/DENETIM-2026-11-21.md` bölüm 2'de M1-M13 ve L1-L13 toplam 26 bulgudur; bunlardan düzeltilen M7, M13, L3 (3) ve Streamlit çerçevesine bağlı L13 (1) çıkınca 22 kalır. H1-H3 de düzeltildiği için sayıma girmez.

### Kapsam ve durum

Denetimden sonra üç commit gelen bulguları kapattı: `ba50a40` (H3, M7, M13), `b010685` (H1, H2, L3) ve `1f2b19a` (Neon incelemesi sonrası üç düzeltme) (kaynak: `git log`). Aşağıdaki liste bunların dışında kalan bulguları ve `plan.md` "v2 fikirleri" bölümünü kapsar. Bulgu kimlikleri bölüm 06 (puan gerekçeleri) ve bölüm 07 (riskler) ile aynıdır.

| Durum | Bulgular | Kaynak |
|---|---|---|
| Düzeltildi | H1, H2, H3, M7, M13, L3 (+ Neon takip düzeltmeleri) | `git log`; `denetim/DENETIM-2026-11-21.md` |
| Açık, bu yol haritasında | M1-M6, M8-M12, L1, L2, L4-L12 | aynı rapor, bölüm 2 |
| Açık, kapsam dışı | L13 (`<html lang="en">`, Streamlit çerçevesi) | aynı rapor, L13 |
| Birleştirilmemiş iş | `denetim/playwright` dalı (8 test, commit `9b57b5d`) | `git branch -a` |

Not: bu çalışmada açık bulguların hepsi kodda yeniden doğrulanmadı. Doğrulama etiketi "doğrulanmadı" olan bulgular (M5, M11, M12, L5, L6, L10, L11) için önce basit bir yeniden üretme adımı gerekir (kaynak: denetim raporu etiketleri).

### Şimdi

Şimdi grubu, kodu değiştirmeden önce ölçü koyan veya tek dosyalık güvenlik düzeltmeleri yapan işleri içerir.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 1 | `denetim/playwright` dalını master'a birleştir | E2E regresyon güvencesi (8 test) | S | Dal, `ba50a40` sonrası `app.py` ile (onay kutusu, Kaynaklar h2) çakışmayacak biçimde güncellenmeli | 8/8 geçiyor; `uv run pytest -q` etkilenmiyor | Denetim "E2E 7/10"; "Kontrol EDİLMEYENLER": E2E kapsamı |
| 2 | Atıf kalitesi ölçümünü `eval/` içine kalıcı betik yap | "%21,9 → %0" iddiası yeniden üretilebilir olur | M | Çalışan Ollama; aynı 14 soru | Betik depoda; geçersiz atıf oranı betik çıktısında raporlanıyor | M8, H2 |
| 3 | `pipeline`, `cli`, `vector_index` için sahte repo + sahte embedder ile entegrasyon testi | Bu modüllerin kapsaması %0'dan çıkar | M | Embedder ve Ollama için mock | Üç modülün kapsaması > %0; tarama-parçalama-indeks-arama akışı tek testte | M10 |
| 4 | BM25 indeksini `pickle` yerine JSON/npz ile sakla | Yüklemede kod çalıştırma yolu kapanır | S | Yok | `src/bm25_index.py` içinde `pickle` kalmaz; yükleme testi geçer | M1 |
| 5 | Tarayıcıda sembolik bağlantıları atla; `git` çağrılarında `core.fsmonitor` kapat | Güvenilmeyen repoda sızıntı ve komut çalıştırma riski azalır | S | Yok | Sembolik bağlantılı sahte repo testi: dosya indekslenmez | M2, L5 |
| 6 | `chunk_py` satır bölmeyi `ast` ile uyumlu yap; `chunk_md` çit türü eşlemesini düzelt | Atıflardaki satır numaraları doğru kalır | S | Form feed ve `~~~` içeren test girdisi | Her iki girdi için yeni test geçer, geri alınca kırılır | M3, L4 |
| 7 | `durdur.sh` ve `baslat.sh` eşleşmesini proje yolu/PID dosyasıyla daralt | Başka Streamlit uygulamasını kapatma ve yanlış sayfa açma ortadan kalkar | S | 8501 portunda başka uygulama ile elle deneme | Başka bir `streamlit run app.py` açıkken `durdur.sh` onu kapatmıyor | M4, M5 |

Efor ölçeği: S = bir oturumdan kısa, M = bir-iki oturum, L = çok oturum. Bu bir değerlendirme olup ölçüm değildir.

### Sonra

Sonra grubu, ölçülmüş ama düşük etkili sorunları ve ölçümün gücünü artıran işleri içerir.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 8 | Hibrit-vektör karşılaştırmasını daha büyük, yeni bir soru setiyle tekrarla | "Hibrit daha iyi" iddiası ya kanıtlanır ya bırakılır | M | Dondurulmuş yeni set (ayar setiyle çakışmayan) | Eşleştirilmiş fark ve güven aralığı raporlanır; mevcut fark +0.0014 (n=59) | M9 |
| 9 | `vector_index.search` içinde `vecs.npy` ve `chunks.json`'u önbellekle | Sıcak aramada gecikme azalır | S | Yok | httpx'te hibrit medyanı 23.9 ms'nin altına iner (oturum ölçümü; yeniden ölçülmeli) | M6, L7 |
| 10 | Model yükleme ve indeksleme süresini kısalt (batch büyüt/uzunluğa göre sırala) | CLI çağrısı ~9 sn, indeksleme ~19 sn | M | GPU belleği payı (VRAM tepe 1.67 GB) | Aynı repo için indeksleme süresi 19 sn'nin altında, sonuçlar aynı | L8, L9 |
| 11 | `hybrid_search`'e `embed_fn` parametresi ekle; `monkeypatch`'i kaldır | `eval/run_eval.py` ve `eval/tune_rrf.py` kırılgan bağdan kurtulur | S | Yok | Eval çıktıları (`eval/results.md`) değişmez (md5 aynı) | M11 |
| 12 | Hata yönetimi ve loglama: sessiz `errors="replace"`, ham traceback, geniş `except` | Hatalar kullanıcıya anlaşılır çıkar | M | Yok | CLI'da bilinen hata girdileri traceback yerine mesaj verir | M12 |
| 13 | İndeks adına çalışma ağacı durumunu kat; eski indeksleri temizle; yazımı atomik yap | Bayat indeks ve çakışma riski azalır | M | Yok | Kirli ağaçta indeks adı değişir; eşzamanlı build testi | L1, L2 |
| 14 | `ruff`/`mypy` yapılandırması ve sabit `KisiselNotArama` yolunu `config`'e taşı; kaynak expander başlığını düzelt | Bakım kolaylığı ve erişilebilirlik | S | Yok | Yapılandırma depoda; `app.py` ve `eval/run_eval.py` yolu `config`'ten okur | L10, L11, L12, L6 |

### Belki (v2 fikirleri)

Bu grup `plan.md` "v2 fikirleri" bölümünden gelir ve hiçbiri bir denetim bulgusuyla zorunlu kılınmamıştır.

| Öncelik | İş | Kazanım | Efor | Önkoşul | Ölçüt | Bağlı bulgu |
|---|---|---|---|---|---|---|
| 15 | Cross-encoder reranking | Kavramsal sorularda sıralama iyileşebilir (hibrit conceptual MRR 0.642; ilk 10'da bulunamayanlar: kna-23, kna-29, hx-17) | L | Madde 8'deki yeni set; ayar için ayrı set | Yeni sette conceptual MRR@10, rerank olmadan hibritten yüksek; gecikme ölçülü | Bölüm 05 (conceptual sonuçlar); M9 |
| 16 | Incremental indexing (git diff ile yalnız değişen dosyalar) | Yeniden indeksleme ~19 sn yerine değişen dosya sayısıyla orantılı | M | Madde 13 (indeks adı/atomik yazım) | Tek dosya değişiminde süre, tam indekslemenin bir kesri; sonuçlar tam indeksle aynı | L1, L9 |
| 17 | tree-sitter ile JS ve C# desteği | Kapsam genişler (şimdi yalnız `.py`, `.md`) | L | Yeni dillerde dondurulmuş eval seti | Yeni dil için isim/kavramsal soru seti ve hit@5 raporu | Bölüm 01 kapsam dışı |
| 18 | Çağrı grafiği ("X'i kim çağırıyor?") | Yeni soru türü | L | Çağrı çözümlemesi tasarımı; yeni eval türü | Soru türü için ayrı set ve metrik | Bağlı bulgu yok (yeni özellik) |

### Yol haritası şeması

<figure>
<svg viewBox="0 0 720 568" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Yol haritası" font-family="DejaVu Sans, sans-serif" style="max-width:100%;height:auto"><defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs><rect x="120" y="8" width="188" height="24" rx="4" fill="#1f3a68"/>
<text x="214.0" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Şimdi</text>
<rect x="316" y="8" width="188" height="24" rx="4" fill="#4a6fa5"/>
<text x="410.0" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Sonra</text>
<rect x="512" y="8" width="188" height="24" rx="4" fill="#7f8c9b"/>
<text x="606.0" y="24" font-size="12" text-anchor="middle" fill="#fff" font-weight="bold">Belki</text>
<rect x="4" y="40" width="712" height="114" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="60" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Test ve ölçüm</text>
<rect x="120" y="46" width="188" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="64" font-size="12" text-anchor="middle" fill="#1a1a1a">#1 Playwright dalını birleştir</text>
<text x="214.0" y="79" font-size="12" text-anchor="middle" fill="#1a1a1a">(S)</text>
<rect x="120" y="94" width="188" height="27" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="112" font-size="12" text-anchor="middle" fill="#1a1a1a">#2 Atıf eval betiği kalıcı (M)</text>
<rect x="120" y="127" width="188" height="27" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="145" font-size="12" text-anchor="middle" fill="#1a1a1a">#3 Entegrasyon testleri (M)</text>
<rect x="316" y="46" width="188" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="410.0" y="64" font-size="12" text-anchor="middle" fill="#1a1a1a">#8 Hibrit-vektör, yeni soru</text>
<text x="410.0" y="79" font-size="12" text-anchor="middle" fill="#1a1a1a">seti (M)</text>
<rect x="4" y="158" width="712" height="98" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="178" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Güvenlik</text>
<rect x="120" y="164" width="188" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="182" font-size="12" text-anchor="middle" fill="#1a1a1a">#4 pickle yerine JSON/npz</text>
<text x="214.0" y="197" font-size="12" text-anchor="middle" fill="#1a1a1a">(S)</text>
<rect x="120" y="212" width="188" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="230" font-size="12" text-anchor="middle" fill="#1a1a1a">#5 symlink atla, fsmonitor</text>
<text x="214.0" y="245" font-size="12" text-anchor="middle" fill="#1a1a1a">kapat (S)</text>
<rect x="316" y="164" width="188" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="410.0" y="182" font-size="12" text-anchor="middle" fill="#1a1a1a">#13 İndeks adı + atomik</text>
<text x="410.0" y="197" font-size="12" text-anchor="middle" fill="#1a1a1a">yazım (M)</text>
<rect x="4" y="260" width="712" height="52" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="280" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Doğruluk</text>
<text x="10" y="295" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">(parçalama,</text>
<text x="10" y="310" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">atıf)</text>
<rect x="120" y="266" width="188" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="284" font-size="12" text-anchor="middle" fill="#1a1a1a">#6 splitlines ve md çit</text>
<text x="214.0" y="299" font-size="12" text-anchor="middle" fill="#1a1a1a">düzeltmesi (S)</text>
<rect x="4" y="316" width="712" height="52" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="336" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Performans</text>
<rect x="316" y="322" width="188" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="410.0" y="340" font-size="12" text-anchor="middle" fill="#1a1a1a">#9-10 Önbellek + embed</text>
<text x="410.0" y="355" font-size="12" text-anchor="middle" fill="#1a1a1a">hızı (S/M)</text>
<rect x="512" y="322" width="188" height="42" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="606.0" y="340" font-size="12" text-anchor="middle" fill="#1a1a1a">#16 Incremental indexing</text>
<text x="606.0" y="355" font-size="12" text-anchor="middle" fill="#1a1a1a">(M)</text>
<rect x="4" y="372" width="712" height="52" rx="4" fill="#f4f6fa" stroke="#d4d9e0"/>
<text x="10" y="392" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Bakım ve</text>
<text x="10" y="407" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">belge</text>
<rect x="120" y="378" width="188" height="42" rx="5" fill="#fff" stroke="#1f3a68" stroke-width="1.2"/>
<text x="214.0" y="396" font-size="12" text-anchor="middle" fill="#1a1a1a">#7 baslat/durdur eşleşmesi</text>
<text x="214.0" y="411" font-size="12" text-anchor="middle" fill="#1a1a1a">(S)</text>
<rect x="316" y="378" width="188" height="42" rx="5" fill="#fff" stroke="#4a6fa5" stroke-width="1.2"/>
<text x="410.0" y="396" font-size="12" text-anchor="middle" fill="#1a1a1a">#11, 12, 14 embed_fn, hata</text>
<text x="410.0" y="411" font-size="12" text-anchor="middle" fill="#1a1a1a">yönetimi, ruff/mypy (S/M)</text>
<rect x="4" y="428" width="712" height="114" rx="4" fill="#fff" stroke="#d4d9e0"/>
<text x="10" y="448" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">Erişim ve</text>
<text x="10" y="463" font-size="12" text-anchor="start" fill="#1f3a68" font-weight="bold">kapsam (v2)</text>
<rect x="512" y="434" width="188" height="42" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="606.0" y="452" font-size="12" text-anchor="middle" fill="#1a1a1a">#15 Cross-encoder rerank</text>
<text x="606.0" y="467" font-size="12" text-anchor="middle" fill="#1a1a1a">(L)</text>
<rect x="512" y="482" width="188" height="27" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="606.0" y="500" font-size="12" text-anchor="middle" fill="#1a1a1a">#17 tree-sitter JS/C# (L)</text>
<rect x="512" y="515" width="188" height="27" rx="5" fill="#fff" stroke="#7f8c9b" stroke-width="1.2"/>
<text x="606.0" y="533" font-size="12" text-anchor="middle" fill="#1a1a1a">#18 Çağrı grafiği (L)</text>
<text x="8" y="560" font-size="12" text-anchor="start" fill="#555">Etiket: #n yol haritası madde numarası; (S/M/L) efor. Madde 1-7 Şimdi, 8-14 Sonra, 15-18 Belki.</text></svg>
<figcaption>Şekil 3. Yol haritası (Şimdi / Sonra / Belki), alana göre. Bağımlılıklar (önce → sonra): #2 → #8, #8 → #15, #13 → #16, #3 → #4, #3 → #9, #1 → #3.</figcaption>
</figure>

### Değerlendirme

Sıralama gerekçesi: önce ölçü ve test (madde 1-3), çünkü sonraki değişikliklerin geri alma doğrulaması bunlara dayanıyor; denetim sonrası düzeltmelerde aynı yöntem kullanıldı (oturum ölçümü, facts.md). Bu sıra bir değerlendirmedir; kesin etki hesabı yapılmamıştır.


## 10. CV ve portföy değeri

Proje, 2 günde (2026-11-20 ve 2026-11-21) 14 commit ile üretilmiş, 1789 satırlık Python kodu, 54 testi ve iki ayrı eval setiyle ölçülmüş yerel bir RAG sistemidir (kaynak: facts.md "Depo istatistikleri", "Test"). Aşağıdaki iddialar yalnız facts.md ve depo dosyalarına dayanır; "oturum ölçümü" etiketli olanlar öyle belirtilmiştir.

### Beceri kanıt tablosu

| Beceri | Kanıt (dosya/sayı) | CV cümlesi |
|---|---|---|
| Hibrit arama (BM25 + vektör, RRF) | `src/hybrid.py`, `src/bm25_index.py`, `src/vector_index.py`; gömme modeli `BAAI/bge-m3` (`src/config.py:9`) | BM25 ve yoğun vektör aramayı ağırlıklı RRF ile birleştiren yerel kod arama motoru geliştirdim. |
| Kod bilgili parçalama | `src/chunk_py.py` (`ast`), `src/chunk_md.py`; httpx'te 862 parça (oturum ölçümü) | Python kodunu `ast` ile sembol bazında (sınıf, metot, fonksiyon) parçalayan ve satır aralığı veren bir hat yazdım. |
| Değerlendirme tasarımı | `eval/questions.json` (59 soru, dondurulmuş), `eval/tuning.json` (36 soru), `eval/run_eval.py`; hit@1, hit@5, MRR@10 | Ayar ve test setlerini ayırıp ölçüt tabanlı retrieval değerlendirmesi kurdum; sonuçlar deterministik (3 tekrar, aynı md5). |
| Parametre ayarı ve aşırı uyum kontrolü | `eval/tune_rrf.py`: 36 kombinasyon; skor 0.7355 → 0.7880 (+0.0526) yalnız ayar setinde | RRF parametrelerini ayrı bir sette taradım; ana seti ayar için kullanmadım. |
| Test yazma | 54 test, `54 passed in 1.49s` (`uv run pytest -q`); `tests/` 579 satır | Chunker, tokenizer, RRF, tarayıcı, üretici ve eval eşleştirme için 54 birim testi yazdım. |
| Güvenlik/kalite denetimi yapma ve düzeltme | `denetim/DENETIM-2026-11-21.md`: 3 high bulgu (H1-H3), H1-H3 düzeltildi (`ba50a40`, `b010685`) | Projeyi çok boyutlu denetleyip 3 high bulguyu (prompt injection, atıf uyumu, gereksiz LLM çağrısı) düzelttim. |
| LLM üretim güvenliği | `src/generator.py`: çit taşması/enjeksiyon, `fix_citations`, `strip_images`; tuzak sorular 6/6 reddedildi, yanlış red 0/36 (denetim) | Bağlam enjeksiyonuna karşı çitleme ve atıf doğrulaması ekledim; tuzak sorularda 6/6 doğru red gözlendi (denetim ölçümü). |
| Doğrulama disiplini | Her düzeltme için ayrı ajanla geri alma testi (3, 4 ve 6 test kırıldı; oturum ölçümü) | Düzeltmeleri geri alıp testlerin kırıldığını göstererek doğruladım. |
| Yerel LLM ve arayüz | Ollama `qwen3.5:4b` (3.3 GB), Streamlit 1.67.0, `baslat.sh`/`durdur.sh` | Bulut kullanmadan Ollama ve Streamlit ile çalışan, tek tıkla açılan arayüz kurdum. |

### Hazır CV maddeleri

1. Python/Markdown depoları için BM25 + bge-m3 vektör aramayı ağırlıklı RRF ile birleştiren yerel RAG asistanı geliştirdim; 59 soruluk dondurulmuş sette hit@5 0.92, MRR@10 0.796 ölçtüm (kaynak: `eval/results.md`).
2. RRF parametrelerini ayrı 36 soruluk sette taradım (36 kombinasyon); ayar skorunu 0.7355'ten 0.7880'e çıkardım ve ana seti ayara karıştırmadım (kaynak: `eval/tuning_results.md`).
3. Projeyi 9 puanlı boyutta (test paketi, hatalar, güvenlik, çapraz inceleme, kod kalitesi, E2E, erişilebilirlik, performans, RAG) denetleyip 3 high bulguyu düzelttim; test sayısı 36'dan 54'e çıktı (kaynak: `denetim/DENETIM-2026-11-21.md` bölüm 1; `uv run pytest -q`).

Not: denetim tablosunda 10 satır vardır; senior-qa satırı puanlanmadı (React/Next.js'e özgü), bu yüzden 9 puanlı boyut yazıldı. Düzeltme sonrası kapsama yüzdesi ölçülmedi, CV'ye yazılmamalıdır.

### Portföy özeti (2 cümle)

Kod Repo Asistanı, Python ve Markdown depolarında sembol bazlı parçalama, BM25 + bge-m3 hibrit arama ve atıflı Türkçe cevap üreten, tamamen yerel çalışan bir RAG sistemidir. Hibrit sıralama ve cevap kalitesi, dondurulmuş soru setleri ve çok boyutlu bir denetimle ölçülmüş; bulgular ve açık kalan işler dürüstçe raporlanmıştır.

### Görüşme konuşma noktaları

| Konu | Anlatılacak olgu | Kanıt |
|---|---|---|
| Neden hibrit? | İsim sorularında BM25 güçlü (MRR 0.944), kavramsal sorularda vektör güçlü (hit@5 0.79 vs BM25 0.45) | `eval/results.md` |
| Hibrit gerçekten daha mı iyi? | Dürüst cevap: ana sette hibrit ve vektör neredeyse aynı (MRR@10 0.796 / 0.794; hit@5 için 1 iyi / 0 kötü / 58 aynı) | `denetim/DENETIM-2026-11-21.md` M9 |
| Aşırı uyum | Tuning ayrı sette; ana set ayar için kullanılmadı; fark ayar setinde +0.0526 | `eval/tuning_results.md` |
| Ölçüm bulduğu hata | Denetimde 36 cevabın %25'inde geçersiz atıf; `fix_citations` sonrası %0 (12 soru + 2 tuzak, oturum ölçümü) | denetim H2; facts.md "Oturum ölçümleri" |
| Güvenlik | Prompt injection (H1) bulundu ve düzeltildi; Neon'un "critical" pickle bulgusu doğrulayıcıda low, hakemde medium oldu (M1) | denetim bölüm 3 |
| Neden iki model çapraz inceleme? | Aynı modelin kendi çıktısını onaylama riski; Neon farklı bulgular getirdi, biri doğrulamada elendi | denetim bölüm 3 ve 5 |
| Ajanlarla geliştirme | Süreç şeffaf anlatılmalı: planda iş bölümü ajanlara ayrılmış; kodu yazan ve inceleyen ayrı ajanlar | `plan.md` "İş bölümü"; denetim bölüm 5 |
| Ne yapardın? | Yol haritasının ilk 3 maddesi: E2E dalını birleştir, atıf eval'ini kalıcı yap, entegrasyon testi | bölüm 09 |

### Bu proje neyi kanıtlamaz

Aşağıdaki sınırlar CV'de abartı yapılmasını önler ve görüşmede sorulursa açıkça söylenmelidir.

| İddia | Neden kanıtlanmıyor | Kaynak |
|---|---|---|
| "Hibrit vektörden iyidir" | Fark gürültü düzeyinde: RR farkı ort. +0.0014 (n=59); KisiselNotArama kavramsalda hibrit MRR 0.560, vektör 0.601 | denetim M9; `README.md` |
| "Genel retrieval kalitesi yüksek" | Yalnız 2 repo, 59 soru; yeni repo veya dil için ölçüm yok | `eval/results.md` |
| "Cevap kalitesi ölçüldü" | Üretim ölçümü 12 soruluk alt küme; atıf önce/sonra ölçümü depoda kalıcı değil (doğrulanmadı) | denetim bölüm 4; facts.md "Doğrulanmadı" |
| "Üretime hazır" | Tek kullanıcı, localhost, yük testi yok, web API yok | denetim bölüm 4 |
| "Kapsama yüksek" | Denetim anında %59; `pipeline`, `cli`, `vector_index` %0. Düzeltme sonrası değer ölçülmedi | denetim "Mevcut test paketi" |
| "Çok dilli kod desteği" | Yalnız `.py` ve `.md` (`src/config.py` `EXTENSIONS`) | `src/config.py` |
| "Geliştirmeyi tek başıma yazdım" | Geliştirme ajan ekibiyle yapıldı; kişisel katkı (tasarım kararları, kabul, denetim yönlendirmesi) ayrıca belirtilmeli | `plan.md` "İş bölümü" |
| "Performans ölçüldü" | Değerler denetimde tek makinede ölçüldü, bu çalışmada yeniden ölçülmedi | facts.md "Doğrulanmadı" |
| "Test sayısı 54 artışı hep yeni özellik" | Denetim sonrası 36 → 54 artışının dökümü commit bazında ayrıştırılmadı | facts.md "Doğrulanmadı" |

Bu bölümdeki puan veya genel nitelemeler "değerlendirme" niteliğindedir; sayılar yukarıdaki kaynaklardan alınmıştır.


## 11. Ekler

Bu ek, 38 takipli dosyanın haritasını, kurulum ve çalıştırma komutlarını, sözlüğü, eval şemasını ve olgu kaynaklarını toplar (kaynak: `git ls-files | wc -l` çıktısı 38, facts.md). Yollar proje köküne görelidir.

### Dosya haritası

| Yol | Amaç |
|---|---|
| `plan.md` | Tasarım planı: kapsam, klasör yapısı, veri modeli, adımlar, v2 fikirleri |
| `README.md` | Kurulum, kullanım, eval sonuç tablosu |
| `pyproject.toml`, `uv.lock` | Bağımlılıklar ve kilit dosyası (Python `>=3.12`) |
| `app.py` | Streamlit arayüzü (repo yolu, indeksleme, soru, mod seçimi, kaynaklar) |
| `baslat.sh`, `durdur.sh` | Ollama + Streamlit'i başlat (8501) ve Streamlit'i kapat |
| `src/config.py` | Yollar, model adları, arama parametreleri, dışlama kalıpları |
| `src/scanner.py` | Repoyu tarar; dışlama kuralları, dosya boyutu sınırı |
| `src/chunk.py`, `src/chunk_py.py`, `src/chunk_md.py` | `CodeChunk` ve dile göre yönlendirme; Python (`ast`) ve Markdown parçalama |
| `src/embedder.py` | bge-m3 gömme (GPU/CPU) |
| `src/vector_index.py` | Numpy vektör indeksi |
| `src/bm25_index.py` | Kod tokenizer'lı BM25 indeksi |
| `src/hybrid.py` | Ağırlıklı RRF ve aday havuzu |
| `src/pipeline.py` | İndeks oluşturma ve yükleme |
| `src/generator.py` | Bağlam, prompt, atıf doğrulama ve düzeltme (Ollama) |
| `src/cli.py` | `index`, `search`, `ask`, `eval` komutları |
| `eval/questions.json` | Ana eval seti: 59 soru, dondurulmuş |
| `eval/tuning.json` | Ayar seti: 36 soru |
| `eval/run_eval.py`, `eval/tune_rrf.py` | Eval çalıştırıcı ve RRF ızgara taraması |
| `eval/results.md`, `eval/tuning_results.md` | Üretilmiş sonuç tabloları |
| `eval/README.md` | Eval şeması ve değişiklik kaydı |
| `tests/test_*.py` | 54 test: app, chunk_md, chunk_py, eval_match, generator, rrf, scanner, tokenizer |
| `denetim/DENETIM-2026-11-21.md` | Çok boyutlu denetim raporu |
| `.gitignore` | `data/`, `.venv/` vb. dışlama |

Git'e takipli olmayan yerler: `data/` (indeksler, klonlanmış repolar, günlükler) ve `rapor/` (bu rapor). `denetim/playwright` dalında 8 E2E test bulunur ve master'a birleştirilmemiştir (kaynak: `git branch -a`).

### Komutlar

Tüm komutlar proje kökünden çalıştırılır (kaynak: `README.md`, `baslat.sh`, `durdur.sh`).

| Amaç | Komut |
|---|---|
| Kurulum | `uv sync` |
| LLM modeli (yalnız `ask` ve arayüz için) | `ollama pull qwen3.5:4b` |
| Eval reposu (httpx, commit `7cff5f7`) | `git clone --depth 1 https://github.com/encode/httpx data/repos/httpx` |
| İndeksle | `uv run python -m src.cli index --repo <repo-yolu>` |
| Ara | `uv run python -m src.cli search "<sorgu>" --repo <repo-yolu> --mode hybrid --k 5` |
| Cevap üret | `uv run python -m src.cli ask "<soru>" --repo <repo-yolu>` |
| Arayüz (elle) | `uv run streamlit run app.py` |
| Arayüz (tek tık) | `./baslat.sh` (Ollama ve Streamlit'i başlatır, `http://localhost:8501` açar) |
| Arayüzü kapat | `./durdur.sh` (yalnız Streamlit; Ollama'ya dokunmaz) |
| Test | `uv run pytest -q` (çıktı: `54 passed in 1.49s`) |
| Ana eval | `uv run python -m src.cli eval` veya `uv run python eval/run_eval.py` (sonuç: `eval/results.md`) |
| Ayar seti eval | `uv run python eval/run_eval.py --set tuning` |
| RRF taraması | `uv run python eval/tune_rrf.py` (yalnız `eval/tuning.json`) |

Modlar: `bm25`, `vector`, `hybrid` (varsayılan). Eval LLM kullanmaz. Eval çalıştırmak için `data/repos/httpx` klonu ve `KisiselNotArama` yolu gerekir (kaynak: `eval/README.md`, `eval/run_eval.py`); KisiselNotArama yolu kodda sabittir (denetim L10).

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
| Geri alma testlerinde kırılan test sayıları (3, 4 düzeltme, 6) | Her düzeltmeyi geri alıp `uv run pytest` çalıştırmak |
| GitHub deposunun `code-repo-rag` adı ve public olması | Ağdan kontrol (yapılmadı) |
| Performans değerleri (0.3 / 21.7 / 23.9 ms, 7.4 sn, ~19 sn, RSS ~4.1 GB, VRAM 1.67 GB) | Ölçümü yeniden yapmak (bu çalışmada yapılmadı) |
| 36 → 54 test artışının dökümü | Denetim sonrası üç commit'te `git diff --stat tests/` ile ayrıştırmak |
| Düzeltme sonrası kapsama yüzdesi | `uv run pytest --cov` (bu çalışmada çalıştırılmadı) |
| `denetim/playwright` testlerinin güncel master ile geçmesi | Dalı güncelleyip testleri çalıştırmak |
| Denetim etiketi "doğrulanmadı" olan bulgular (H3 önceki durumu, M5, M11, M12, L5, L6, L10, L11) | Tek tek yeniden üretme adımı |
