# Eval sonuçları (main, 59 soru)

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
| hybrid | httpx | name | 15 | 0.93 | 1.00 | 0.967 |
| hybrid | httpx | conceptual | 15 | 0.53 | 0.87 | 0.696 |
| hybrid | httpx | all | 30 | 0.73 | 0.93 | 0.831 |
| hybrid | kisiselnotarama | name | 15 | 0.87 | 1.00 | 0.922 |
| hybrid | kisiselnotarama | conceptual | 14 | 0.43 | 0.71 | 0.544 |
| hybrid | kisiselnotarama | all | 29 | 0.66 | 0.86 | 0.740 |
| hybrid | all | name | 30 | 0.90 | 1.00 | 0.944 |
| hybrid | all | conceptual | 29 | 0.48 | 0.79 | 0.623 |
| hybrid | all | all | 59 | 0.69 | 0.90 | 0.786 |

Hybrid ilk 10'da bulamadığı sorular: kna-24, kna-27, kna-29
