# Kod Repo Asistanı — Plan

## Amaç
Bir Git reposundaki kodu ve dokümantasyonu sınıf ve fonksiyon sınırlarını koruyarak parçalamak, BM25 ve vektör aramayı RRF ile birleştirmek, cevabı **dosya yolu ve satır aralığıyla** vermek. Katalogda `kod-repo-asistani` (Orta, 1-2 gün).

Öğrenme hedefleri, KisiselNotArama'da olmayan konular:
- Kod yapısına göre parçalama (code-aware chunking): `ast` ile fonksiyon, sınıf ve metot sınırlarından bölmek
- Hybrid search (BM25 + vektör) ve Reciprocal Rank Fusion (RRF)
- Metadata zenginleştirme: sembol adı, imza, dil, satır aralığı
- İsim sorgularıyla kavramsal sorguların ölçülerek karşılaştırılması

## Kapsam (v1)
- **Diller:** Python (`.py`, `ast` ile) ve Markdown (`.md`, başlıklara göre). JS ve C# v2'ye bırakıldı (tree-sitter gerekir).
- **Arayüz:** CLI (`index`, `ask`, `search`, `eval`) ve basit bir Streamlit sayfası.
- **Yerel çalışma:** Ollama (`qwen3.5:4b`) ve `BAAI/bge-m3`, KisiselNotArama'daki ayarlarla aynı.
- **Test repoları:** (1) KisiselNotArama'nın kendisi, (2) orta boy bir açık kaynak Python repo (ör. `httpx` ya da `rich`). Repo `data/repos/` altına klonlanır ve git'e eklenmez.

## Klasör yapısı
```
KodRepoAsistani/
  plan.md  README.md  pyproject.toml  app.py (Streamlit)
  src/
    config.py      # yollar, modeller, top_k, RRF k=60, dışlama kalıpları
    scanner.py     # repoyu tarar; .gitignore, test/lock/build/venv/__pycache__ dışlanır
    chunk_py.py    # ast: modül başı, sınıf, metot, fonksiyon -> CodeChunk
    chunk_md.py    # başlığa göre bölme
    chunk.py       # CodeChunk dataclass + dile göre yönlendirme
    embedder.py    # KisiselNotArama/src/embedder.py'den sadeleştirilerek kopyalanır
    vector_index.py# NumpyIndex (KisiselNotArama/src/index.py'den uyarlanır)
    bm25_index.py  # kod tokenizer'lı BM25 (rank-bm25)
    hybrid.py      # RRF birleştirme + aday havuzu
    generator.py   # prompt: dosya:satır atıflı cevap
    cli.py
  eval/
    questions.json # isim ve kavramsal sorular, beklenen dosya:sembol
    run_eval.py    # bm25 / vektör / hibrit karşılaştırması -> results.md
  tests/           # pytest: chunker, tokenizer, RRF, scanner
```
Projeler bağımsız kalsın diye KisiselNotArama'dan import yapılmaz; gereken küçük modüller kopyalanıp uyarlanır.

## Veri modeli
```python
@dataclass
class CodeChunk:
    id: str            # "src/index.py::NumpyIndex.search"
    path: str          # repo köküne göre
    lang: str          # "python" | "markdown"
    kind: str          # module | class | method | function | section
    symbol: str        # "NumpyIndex.search"
    signature: str     # "def search(self, qvec, k, sources=None)"
    start_line: int
    end_line: int
    text: str          # embedding'e giden metin: başlık satırı + kod
```
Embedding'e giden metin şöyle başlar: `# path :: symbol\n# signature\n<docstring>\n<kod>`. Bu başlık dosya yolu ve sembol bilgisini vektöre taşır.

## Adımlar
1. **İskelet:** `uv init`, bağımlılıklar (sentence-transformers, numpy, ollama, rank-bm25, streamlit, pytest), config.
2. **Tarayıcı (scanner):** `.gitignore` kurallarına uyar (ya da `git ls-files`), `tests/`, `*.lock`, `build/`, `dist/`, `.venv/` dışlanır, büyük ve ikili dosyalar atlanır. Test: sahte bir repo ağacıyla dışlama kuralları kontrol edilir.
3. **Python parçalama:** `ast` ile `FunctionDef`, `AsyncFunctionDef` ve `ClassDef` bulunur. Decorator'lar parçaya dahil edilir (`decorator_list` ilk satırı). Sınıf çok uzunsa metotlarına bölünür, sınıf başı (docstring ve alanlar) ayrı parça olur. Modül seviyesindeki kalan kod "module" parçası olur. Bir parça N satırı aşarsa satır sınırından bölünür, imza başlığı korunur. Sözdizimi hatası olan dosyalarda satır bazlı bölmeye düşülür. Test: bilinen bir dosyada satır aralıkları kontrol edilir.
4. **Markdown parçalama:** başlıklara göre, satır numaralarıyla.
5. **Vektör indeksi:** NumpyIndex kullanılır; indeks adı model, repo hash'i ve commit kısa hash'inden oluşur.
6. **BM25 indeksi:** Kod tokenizer'ı `getUserById` adını `get user by id` ve `getuserbyid` olarak, `snake_case` adlarını parçalarına ayırarak ekler. Sembol ve yol alanları birkaç kez tekrarlanarak ağırlıklandırılır. Test: tokenizer çıktısı kontrol edilir.
7. **Hybrid search + RRF:** her yöntemden top-N (ör. 30) aday alınır, `score = Σ 1/(k + rank)` (k=60) ile birleştirilir, top-k döner. `search --mode bm25|vector|hybrid` ile hangi yöntemin seçildiği görülebilir. Test: RRF'nin hesaplanması elle hesaplanmış örnekle kontrol edilir.
8. **Cevap üretimi:** bağlam `### path:start-end (symbol)` biçimindeki bloklarla verilir. LLM her iddiayı `[path:satır]` biçiminde atıflar, kodda olmayanı uydurmaz ("Bu bilgi repoda yok"). CLI kaynakları dosya:satır listesi olarak gösterir.
9. **Eval:** her iki repo için yaklaşık 30 soru hazırlanır.
   - İsim sorguları (ör. "`chunk_by_heading` ne yapıyor?", "`NumpyIndex.search`")
   - Kavramsal sorgular (ör. "indeks bozulmasın diye ne yapılıyor?", "GPU belleği nerede boşaltılıyor?")
   - Metrikler: hit@1, hit@5, MRR. Sonuçlar bm25, vektör ve hibrit için **iki sorgu türüne ayrı ayrı** raporlanır.
   - Sorular baştan dondurulur. Ayar yapmak için ayrı bir küçük set kullanılır.
10. **Streamlit:** repo yolu, indeksleme düğmesi, soru kutusu, mod seçimi, kaynakların kod bloğu olarak dosya:satır başlığıyla gösterimi.
11. **README:** kurulum, kullanım, eval sonuç tablosu.

## Beklenen sonuç
`uv run python -m src.cli ask "retry mantığı nerede?" --repo data/repos/httpx` → kısa bir cevap, ardından `httpx/_transports/default.py:120-158 (HTTPTransport.handle_request)` biçiminde kaynaklar. Eval tablosunda isim sorgularında BM25'in, kavramsal sorgularda vektör aramanın güçlü olması, hibritin ise iki türde de en iyi ya da en iyiye yakın sonuç vermesi beklenir.

## Doğrulama
- `uv run pytest`: scanner, chunker satır aralıkları, tokenizer, RRF.
- `uv run python -m src.cli index --repo ../KisiselNotArama` hatasız çalışmalı ve parça sayısı ile tür dağılımı raporlanmalı.
- `uv run python eval/run_eval.py` → `eval/results.md` (mod × sorgu türü tablosu).
- Bir isim sorusu ve bir kavramsal soru için CLI'dan elle `ask` çalıştırılır; dosya:satır atıfları açılıp kontrol edilir.

## İş bölümü (uygulama sırasında)
- sonnet/medium: iskelet, scanner, md chunker, vektör indeksi, CLI, Streamlit, README
- opus/high: Python ast chunker ile BM25 tokenizer, RRF hattı (doğruluk kritik)
- sonnet/medium: eval sorularının hazırlanması (kodu yazandan farklı bir ajan)
- Ayrı bir reviewer ajanı: testler ve eval sonuçlarının kontrolü

## v2 fikirleri
- tree-sitter ile JS ve C#
- Cross-encoder reranking (sonraki katalog projesine köprü)
- Incremental indexing (git diff ile yalnızca değişen dosyalar)
- Çağrı grafiği: "X'i kim çağırıyor?" soruları
