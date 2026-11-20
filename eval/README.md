# Eval soru seti (dondurulmuş)
- `questions.json` (59 soru) dondurulmuştur; ayar için yalnız `tuning.json` (6 soru) kullanılır, ana sete bakılarak ayar yapılmaz.
- httpx commit: `7cff5f7` (data/repos/httpx, depth 1); diğer repo: KisiselNotArama (src/ + kök .py/.md, tests/ hariç).
- Şema: `{id, repo: kisiselnotarama|httpx, type: name|conceptual, question (TR), expected: [{path, symbol}]}`.
- path repo köküne göredir; symbol: `Sinif.metot`, fonksiyon adı veya markdown başlık metni. Birden fazla doğru cevap olabilir.
- Doğru sayılma: getirilen parçalardan biri expected listesindeki herhangi bir (path, symbol) ile eşleşirse.

## Değişiklik kaydı
- 2026-11-20: kna-28 expected'a `app.py:load_embed_model` eklendi. Neden: review'da soru app.py'deki load_embed_model ile de doğru cevaplanıyor.
- 2026-11-20: Eşleştirme kuralı değişti: (a) beklenen `Sinif.metot`, gelen chunk `Sinif` (kind=class) ve metot `def metot(` olarak chunk metninde geçiyorsa eşleşir; (b) markdown başlık sembolleri karşılaştırmadan önce normalize edilir (backtick silinir, `[x](url)` -> `x`, boşluklar sadeleşir).
