# Eval soru seti (dondurulmuş)
- `questions.json` (59 soru) dondurulmuştur; ayar için yalnız `tuning.json` (36 soru; 2026-11-20 tarihinde 6 sorudan genişletildi) kullanılır, ana sete bakılarak ayar yapılmaz.
- İki repo da sabit commit'te: `kisiselnotarama` `1d45820` (data/repos/kisiselnotarama; src/ + kök .py/.md, tests/ hariç), httpx `7cff5f7` (data/repos/httpx, depth 1).
- Klonlama: `git clone ../KisiselNotArama data/repos/kisiselnotarama && git -C data/repos/kisiselnotarama checkout --detach 1d45820` (httpx: `git clone https://github.com/encode/httpx data/repos/httpx && git -C data/repos/httpx checkout --detach 7cff5f7`).
- Şema: `{id, repo: kisiselnotarama|httpx, type: name|conceptual, question (TR), expected: [{path, symbol}]}`.
- path repo köküne göredir; symbol: `Sinif.metot`, fonksiyon adı veya markdown başlık metni. Birden fazla doğru cevap olabilir.
- Doğru sayılma: getirilen parçalardan biri expected listesindeki herhangi bir (path, symbol) ile eşleşirse.

## Değişiklik kaydı
- 2026-11-20: kna-28 expected'a `app.py:load_embed_model` eklendi. Neden: review'da soru app.py'deki load_embed_model ile de doğru cevaplanıyor.
- 2026-11-20: Eşleştirme kuralı değişti: (a) beklenen `Sinif.metot`, gelen chunk `Sinif` (kind=class) ve metot `def metot(` olarak chunk metninde geçiyorsa eşleşir; (b) markdown başlık sembolleri karşılaştırmadan önce normalize edilir (backtick silinir, `[x](url)` -> `x`, boşluklar sadeleşir).
- 2026-11-22: kisiselnotarama repo yolu `../KisiselNotArama` yerine `data/repos/kisiselnotarama` (1d45820'e sabit klon). Neden: canlı repo değiştikçe dondurulmuş set sonuçları oynuyordu.

## Üretim kalitesi (gen_eval)
- `uv run python eval/gen_eval.py [--n 12] [--seed 0]` (Ollama gerekir): `questions.json`'dan name/conceptual dengeli, sabit seed'li alt küme + `gen_traps.json` (repoda olmayan tuzak sorular) için hibrit hit'lerle `generator.answer` çalıştırır; `eval/gen_results.md` yazar.
- Metrikler: geçersiz atıf oranı (`check_citations`), atıfsız cevap oranı, beklenen dosyaya atıf oranı, tuzaklarda "Bu bilgi repoda yok." oranı. Saf hesap `gen_metrics`, testi `tests/test_gen_eval.py`.
