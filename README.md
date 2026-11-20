# Kod Repo Asistanı

Yerel kod deposu için hibrit (BM25 + bge-m3 vektör, RRF) arama ve atıflı Türkçe soru-cevap. Python ve Markdown dosyalarını sembol bazlı parçalar (sınıf/metot/fonksiyon/başlık).

## Kurulum
```bash
uv sync                      # bağımlılıklar (torch cu132 dahil)
ollama pull qwen3.5:4b       # yalnız `ask` / arayüz için (LLM)
git clone --depth 1 https://github.com/encode/httpx data/repos/httpx   # eval için (commit 7cff5f7)
```

## Kullanım
```bash
uv run python -m src.cli index --repo ../KisiselNotArama
uv run python -m src.cli search "release_gpu ne yapar" --repo ../KisiselNotArama --mode hybrid --k 5
uv run python -m src.cli ask "release_gpu ne işe yarıyor?" --repo ../KisiselNotArama
uv run python -m src.cli eval            # = uv run python eval/run_eval.py [--set tuning]
uv run streamlit run app.py
uv run pytest
```
Modlar: `bm25`, `vector`, `hybrid` (varsayılan).

## Değerlendirme
`eval/questions.json` (59 soru, dondurulmuş), LLM kullanılmaz. Doğru sayılma: path aynı VE sembol eşleşmesi
(`#n`/`~n` ekleri atılır; markdown'da başlık yolunun son öğesi; "Sinif" beklenirse "Sinif" ya da "Sinif.metot" parçası).
Aynı sembolün bölünmüş parçaları tek hit sayılır. Ayrıntı: `eval/run_eval.py`, `tests/test_eval_match.py`.

| mod | repo | tür | n | hit@1 | hit@5 | MRR@10 |
|---|---|---|---|---|---|---|
| bm25 | httpx | name | 15 | 0.93 | 0.93 | 0.933 |
| bm25 | httpx | conceptual | 15 | 0.13 | 0.33 | 0.232 |
| bm25 | httpx | all | 30 | 0.53 | 0.63 | 0.583 |
| bm25 | kisiselnotarama | name | 15 | 0.67 | 0.87 | 0.756 |
| bm25 | kisiselnotarama | conceptual | 14 | 0.36 | 0.43 | 0.415 |
| bm25 | kisiselnotarama | all | 29 | 0.52 | 0.66 | 0.591 |
| bm25 | all | name | 30 | 0.80 | 0.90 | 0.844 |
| bm25 | all | conceptual | 29 | 0.24 | 0.38 | 0.320 |
| bm25 | all | all | 59 | 0.53 | 0.64 | 0.587 |
| vector | httpx | name | 15 | 0.87 | 0.93 | 0.889 |
| vector | httpx | conceptual | 15 | 0.47 | 0.73 | 0.585 |
| vector | httpx | all | 30 | 0.67 | 0.83 | 0.737 |
| vector | kisiselnotarama | name | 15 | 0.73 | 0.87 | 0.789 |
| vector | kisiselnotarama | conceptual | 14 | 0.43 | 0.64 | 0.530 |
| vector | kisiselnotarama | all | 29 | 0.59 | 0.76 | 0.664 |
| vector | all | name | 30 | 0.80 | 0.90 | 0.839 |
| vector | all | conceptual | 29 | 0.45 | 0.69 | 0.558 |
| vector | all | all | 59 | 0.63 | 0.80 | 0.701 |
| hybrid | httpx | name | 15 | 0.87 | 0.93 | 0.900 |
| hybrid | httpx | conceptual | 15 | 0.47 | 0.73 | 0.596 |
| hybrid | httpx | all | 30 | 0.67 | 0.83 | 0.748 |
| hybrid | kisiselnotarama | name | 15 | 0.73 | 0.87 | 0.789 |
| hybrid | kisiselnotarama | conceptual | 14 | 0.36 | 0.64 | 0.473 |
| hybrid | kisiselnotarama | all | 29 | 0.55 | 0.76 | 0.636 |
| hybrid | all | name | 30 | 0.80 | 0.90 | 0.844 |
| hybrid | all | conceptual | 29 | 0.41 | 0.69 | 0.537 |
| hybrid | all | all | 59 | 0.61 | 0.80 | 0.693 |

Hybrid ilk 10'da bulamadığı sorular: kna-01, kna-10, kna-24, kna-27, kna-28, kna-29, hx-13, hx-28, hx-29
