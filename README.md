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
| bm25 | httpx | name | 15 | 1.00 | 1.00 | 1.000 |
| bm25 | httpx | conceptual | 15 | 0.20 | 0.40 | 0.310 |
| bm25 | httpx | all | 30 | 0.60 | 0.70 | 0.655 |
| bm25 | kisiselnotarama | name | 15 | 0.80 | 1.00 | 0.889 |
| bm25 | kisiselnotarama | conceptual | 14 | 0.43 | 0.50 | 0.486 |
| bm25 | kisiselnotarama | all | 29 | 0.62 | 0.76 | 0.695 |
| bm25 | all | name | 30 | 0.90 | 1.00 | 0.944 |
| bm25 | all | conceptual | 29 | 0.31 | 0.45 | 0.395 |
| bm25 | all | all | 59 | 0.61 | 0.73 | 0.674 |
| vector | httpx | name | 15 | 0.93 | 1.00 | 0.956 |
| vector | httpx | conceptual | 15 | 0.53 | 0.87 | 0.685 |
| vector | httpx | all | 30 | 0.73 | 0.93 | 0.820 |
| vector | kisiselnotarama | name | 15 | 0.87 | 1.00 | 0.922 |
| vector | kisiselnotarama | conceptual | 14 | 0.50 | 0.71 | 0.601 |
| vector | kisiselnotarama | all | 29 | 0.69 | 0.86 | 0.767 |
| vector | all | name | 30 | 0.90 | 1.00 | 0.939 |
| vector | all | conceptual | 29 | 0.52 | 0.79 | 0.645 |
| vector | all | all | 59 | 0.71 | 0.90 | 0.794 |
| hybrid | httpx | name | 15 | 0.93 | 1.00 | 0.956 |
| hybrid | httpx | conceptual | 15 | 0.60 | 0.87 | 0.719 |
| hybrid | httpx | all | 30 | 0.77 | 0.93 | 0.837 |
| hybrid | kisiselnotarama | name | 15 | 0.87 | 1.00 | 0.933 |
| hybrid | kisiselnotarama | conceptual | 14 | 0.43 | 0.79 | 0.560 |
| hybrid | kisiselnotarama | all | 29 | 0.66 | 0.90 | 0.753 |
| hybrid | all | name | 30 | 0.90 | 1.00 | 0.944 |
| hybrid | all | conceptual | 29 | 0.52 | 0.83 | 0.642 |
| hybrid | all | all | 59 | 0.71 | 0.92 | 0.796 |

Hybrid ilk 10'da bulamadığı sorular: kna-23, kna-29, hx-17

Hibrit, ağırlıklı RRF kullanır (`score = Σ w_i/(k+rank)`): w_bm25=0.3, w_vec=1, k=30, candidates=20.
Bu değerler yalnız ayrı tuning setinde (`eval/tuning.json`, 36 soru) `eval/tune_rrf.py` ızgarasıyla seçildi; ana set yalnız sonda bir kez çalıştırıldı (`eval/tuning_results.md`).
Ana sette hibrit, conceptual hit@5'te vektörü geçiyor (0.83 / 0.79, yani 1 soru) ama conceptual MRR'de hâlâ çok az geride (0.642 / 0.645); genel MRR'de fark ihmal edilebilir (0.796 / 0.794).
