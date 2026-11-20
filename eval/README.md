# Eval soru seti (dondurulmuş)
- `questions.json` (59 soru) dondurulmuştur; ayar için yalnız `tuning.json` (6 soru) kullanılır, ana sete bakılarak ayar yapılmaz.
- httpx commit: `7cff5f7` (data/repos/httpx, depth 1); diğer repo: KisiselNotArama (src/ + kök .py/.md, tests/ hariç).
- Şema: `{id, repo: kisiselnotarama|httpx, type: name|conceptual, question (TR), expected: [{path, symbol}]}`.
- path repo köküne göredir; symbol: `Sinif.metot`, fonksiyon adı veya markdown başlık metni. Birden fazla doğru cevap olabilir.
- Doğru sayılma: getirilen parçalardan biri expected listesindeki herhangi bir (path, symbol) ile eşleşirse.
