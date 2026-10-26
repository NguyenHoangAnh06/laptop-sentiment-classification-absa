# Phân tích cảm xúc và khía cạnh trong review laptop

Dự án khoa học dữ liệu6tuần/một người, laptop-only tiếng Anh. Trọng tâm dữ liệu/EDA50%, mô hình40%, Streamlit10%. Tài liệu mới/trao đổi dùng tiếng Việt; mô hình tiếng Việt/PhoBERT chưa triển khai.

## Trạng thái hiện tại

**Benchmark chính đủ6model full21000: verified local+Kaggle.** Dataset30000/split21000/4500/4500 seed42 giữ nguyên. Hai TabPFN cloud đã import và tính lại metrics; local subsample được giữ trong lịch sử.

| Model | Train | Test macro F1 | Neutral F1 |
|---|---:|---:|---:|
| Majority sanity | 21000 | 0,259445 | 0,000000 |
| XGBoost | 21000 | 0,667752 | 0,321138 |
| TabM | 21000 | 0,689086 | 0,336673 |
| TabPFN-3 | 21000 Kaggle | 0,572971 | 0,039801 |
| TabPFN-3.5 | 21000 Kaggle | 0,614017 | 0,135747 |
| BERT canonical | 21000 | 0,755382 | 0,436129 |

Chọn bằng **validation macro F1**: BERT unweighted epoch3 vẫn best; TabM best frozen. TabPFN full21K cải thiện so với subsample nhưng vẫn thấp hơn BERT/TabM về Macro F1 và Neutral F1. V3 n_estimators1 còn giới hạn coverage nội bộ200/384chiều. [Xác minh cloud](reports/tabpfn_kaggle_full21k_verification.md) ghi nguồn/hash/metrics/resource và test reuse; [lịch sử local](reports/history/tabpfn_before_kaggle_20261024/p7_unified_benchmark.md) giữ cảnh báo RSS và subsample. ABSA/gold/app chưa hoàn tất.

**386tests PASS** (380 trước+6 P3-REFINE-01),0FAIL; kiểm hiện hành tại `reports/p3_refinement_20261026/validation.json`/`preservation.json`. Nghiệm thu P9-EXP01 trước đó380tests/381frozen files giữ nguyên tại `reports/p9_exp01_deberta_20261026_v2/validation.json`/`preservation.json`; không ghi lại snapshot cũ để đổi test count. Không retrain sentiment/P8 hoặc rerun embeddings/TabPFN.

**P8: DONE / FROZEN.** BERT Aspect Term Extraction trên SemEval laptop; train/validation/test=2587/458/800 câu, best epoch4/5 bằng validation entityF1=0,799401. Official test entity precision/recall/F1=**0,785714/0,824159/0,804478**. [Báo cáo P8](reports/p8_aspect_extraction.md), [nghiệm thu](reports/p8_20261026/acceptance.json) giữ nguyên. Có1natural duplicate giữa official train/test được giữ và công bố; train–validation không trùng normalized text. Nguồn/license SemEval vẫn NOT_VERIFIED theo ngoại lệ P1.

**P9-EXP01: COMPLETE — READY TO CONTINUE TO P10.** DeBERTa-v3-base unweighted epoch5/seed42 là canonical ASC mới, chọn bằng validation macroF1=**0,777467**, so với BERT0,714145. Giữ đúng1999/314/638examples, split, conflict exclusion và occurrence markers; chỉ thay backbone/tokenizer native. Official test macroF1/accuracy/weightedF1=**0,780433/0,815047/0,813232**; joint P/R/F1=**0,644776/0,677116/0,660550**, dùng frozen P8 spans. Seed43/44 chỉ validation; mean/std ba seed0,766691/0,011453 là stability riêng, không thay primary42. [Báo cáo canonical](reports/p9_exp01_deberta_20261026_v2/report.md), [nghiệm thu](reports/p9_exp01_deberta_20261026_v2/acceptance.json), selector `configs/p9_canonical.yaml`. [BERT previous canonical](reports/p9_aspect_sentiment.md) và toàn bộ artifacts/source snapshot vẫn giữ. Không triển khai P10/pseudo labels Amazon30K.

## Bắt đầu đọc

- [Tái lập từ GitHub](docs/GITHUB_REPRODUCTION.md): cấu trúc, dữ liệu cần tự lấy, pretrained/trained checkpoints, lệnh kiểm thử và ranh giới artifacts chỉ lưu local. Snapshot công khai qua P9 không bao gồm corpus, embeddings hoặc model weights.
- [P3 EDA trọng tâm](reports/p3_refinement_20261026/report.md) và [HTML tự chứa](reports/p3_refinement_20261026/report.html): 8bảng core/3hình, audit/appendix và traceability P4–P9. Chỉ tinh gọn phân tích/trình bày; EDA gốc và scientific artifacts giữ nguyên. Tái dựng vào thư mục mới bằng `.venv/Scripts/python.exe -X utf8 -m scripts.refine_p3 --output-dir reports/p3_refinement_REPRODUCTION`.
- [PLAN_HUMAN](PLAN_HUMAN.md): mục tiêu, phạm vi và tiến độ.
- [PLAN_AI](PLAN_AI.md): ID, phụ thuộc, DONE_WHEN; [AGENTS](AGENTS.md): ràng buộc làm việc.
- [Bàn giao](docs/CODEX_HANDOFF.md): tác vụ hiện tại, trạng thái và bước tiếp.
- [Chỉ mục tài liệu/bằng chứng](docs/PROJECT_INDEX.md): phân biệt active, lịch sử và dữ liệu cần giữ.
- [Báo cáo A–M](reports/model_stack_refactor_completion.md), [P5](reports/p5_modern_tabular_models.md), [P6](reports/p6_transformer_benchmark.md), [P7](reports/p7_unified_benchmark.md).
- [P8 ATE](reports/p8_aspect_extraction.md): BIO/offsets, training, strict span metrics, error analysis và API extraction.
- [P9 ASC/ABSA canonical](reports/p9_exp01_deberta_20261026_v2/report.md): so sánh BERT/DeBERTa, conflict, per-class/confusion, weighting, error pairs, stability và joint decomposition.

## Dữ liệu và pipeline hiện hành

Amazon2023 review nối metadata để xác định laptop; rating1–2→negative,3→neutral,4–5→positive. Dataset30000/9080parent_asin; negative8259/neutral2631/positive19110. Split product-disjoint theo audit đã lưu, không thay đổi.

Canonical text = review_title + newline + body (`text`), NFC/whitespace, giữ phủ định/dấu câu. Frozen MiniLM-L6-v2 revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41,384FP32/mask-mean/L2/max256 cho XGBoost/TabM/TabPFN. BERT checkpoint google-bert/bert-base-uncased revision86b5e0934494bd15c9632b12f734a8a67f723594, tokenizer riêng max512, fine-tune end-to-end. Không TF-IDF/PCA/SVD hoặc metadata features trong active benchmark.

Config: `configs/semantic_benchmark.yaml`, `configs/modern_tabular.yaml`, `configs/transformer_benchmark.yaml`; cache: `data/processed/features/semantic_20261024/`; models/reports: `artifacts/models/semantic_20261024/`, `reports/semantic_20261024/`. Loader kiểm hash/config/row alignment và từ chối cache hỏng.

## Môi trường và xác minh

Môi trường đã kiểm dùng `.venv/Scripts/python.exe`, Python3.13.12, PyTorch2.8.0+cu128, Transformers5.0.0, TabPFN9.2.0; RTX4050Laptop6GB/RAM16GB. Khi tạo môi trường mới, dùng Python tương thích requirements và CUDA của máy; không tự nâng dependency trong môi trường đã chạy benchmark.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -B -m scripts.finalize_p9_exp01 --run-checks
```

Hai lệnh đầu chỉ dành cho setup mới; không cài lại `.venv` đang dùng. Xác minh yêu cầu dữ liệu/artifacts local đã có, không tải chúng từ Git. `finalize_p9_exp01` tính lại metrics từ saved predictions, kiểm selection/model/source hashes và bảo toàn P0–P8/baseline P9; --run-checks chạy toàn suite/pip check/compile, không train hoặc predict test lại. `scripts.test_all` tách tests dữ liệu và Torch để giữ ngân sách bộ nhớ. Các finalizer cũ là công cụ lịch sử, không dùng ghi đè frozen evidence.

Các generator `benchmark_reports`/`finish_benchmark`/`final_completion`/`report_model_refactor` thuộc giai đoạn sentiment đã khóa. P9 dùng báo cáo namespace riêng; giữ P0–P8 reports như snapshots, không sinh lại chúng để cập nhật tiến độ. Hướng dẫn benchmark cũ tại [hợp đồng](docs/MODEL_STACK_REFACTOR.md); cloud verified tại báo cáo Kaggle.

## Giới hạn và công việc tiếp

Các score benchmark **sentiment P0–P7** đo rating-derived proxy trong laptop, không phải human-gold accuracy; P8/P9 dùng SemEval aspect annotations. Neutral sentiment train8,77%, một seed/search nhỏ; test đã được xem ở LEGACY/local. Không khẳng định thống kê, production hoặc khái quát sang loại thiết bị khác. Latency từ tokens/embeddings chưa gồm raw-text preprocessing; frozen-classifier artifact chưa gồm shared encoder. So sánh full-vs-subsample và CPU/GPU khác thiết bị phải giữ giới hạn này.

Independent human gold300–500review vẫn PENDING P10; QA bộ lọc/diagnosis360 không thay thế gold. SemEval-to-Amazon platform/style shift trong laptop chưa được đo. Streamlit chưa có UI hoàn chỉnh, chưa có lệnh chạy app được nghiệm thu; hợp đồng tương lai laptop/en với ba nhãn, confidence nullable và aspects rỗng khi không có khía cạnh.

**P7: DONE**, benchmark giữ nguyên. [Phân tích lỗi/proxy/mất cân bằng](reports/p7_error_cause_analysis.md) dùng360 human-reviewed sentiment diagnosis reviews và6model active gồm TabPFN cloud. Agreement292/360 (81,11%), disagreement68/360 (18,89%) chỉ mô tả mẫu gộp; SRS31/300 (10,33%) và enriched37/60 tách biệt, không suy rộng30K. BERT human macro F1 diagnosis0,674358 (gộp),0,691746 (SRS). [Kiểm P0–P7](reports/p0_p7_acceptance.json), [hướng dẫn diagnosis](docs/SENTIMENT_DIAGNOSIS.md). P8/P9 đã hoàn tất riêng; **dừng tại READY FOR P10**. Independent Amazon gold/domain-shift evaluation/app vẫn PENDING. TF-IDF/LR/SVM/DT, BERT body-only và kế hoạch Word cũ là lịch sử; không xóa artifacts.

## Dùng và xác minh Aspect Term Extraction

```powershell
.venv/Scripts/python.exe -B -m scripts.finalize_p9_exp01
```

Xác minh hiện hành P9-EXP01 đối chiếu hash frozen P8 và saved predictions, không retrain hoặc predict P8 test lại. P8 reports/350tests là evidence lịch sử; shared test driver đã mở rộng nên không dùng finalize_p8 để sinh lại snapshots đó. Lệnh train_p8 bị khóa với experiment đã selection/test, kể cả --resume.

```python
from pathlib import Path
from src.absa.extraction import AspectExtractor

extractor = AspectExtractor(Path("artifacts/models/p8_20261026/best"), device="auto")
aspects = extractor.extract_aspects("The battery life is excellent.")
```

Đây là ví dụ gọi API, không phải kết quả dự đoán được khẳng định trước. Output term/start/end/score(null); không tạo sentiment, không có aspect trả[]. Chỉ hỗ trợ en, tối đa128tokens; câu quá dài bị từ chối rõ thay vì truncate. Model/tokenizer/config/optimizer nằm local; predictions có text giữ trong data/interim, không tự publish. Resume training ở ranh giới epoch được chuẩn bị nhưng chưa chạy thực tế trong lần train liền mạch này. Một seed và cảnh báo CUDA backward best-effort determinism được ghi trong báo cáo.

## Dùng và xác minh ASC / end-to-end ABSA

```powershell
.venv/Scripts/python.exe -B -m scripts.finalize_p9_exp01 --run-checks
```

Lệnh trên xác minh report từ saved artifacts, không rerun inference test. `scripts.p9_exp01 prepare`/`train` chỉ dành namespace mới; completed runs bị khóa. DeBERTa resume hiện không hỗ trợ do config vocab sau resize; xem lỗi và recovery minh bạch trong báo cáo. Inference/reload đã PASS. Không dùng finalizer BERT cũ trên source đã mở rộng; previous source11files được giữ đúng hash tại `reports/p9_exp01_deberta_20261026_v2/previous_canonical_source/`.

```python
from pathlib import Path
from src.absa.extraction import AspectExtractor
from src.absa.sentiment import AspectSentimentClassifier
from src.inference.absa import AspectAnalyzer
import yaml

extractor = AspectExtractor(Path("artifacts/models/p8_20261026/best"), device="auto")
selection = yaml.safe_load(Path("configs/p9_canonical.yaml").read_text(encoding="utf-8"))
classifier = AspectSentimentClassifier(Path(selection["model_directory"]), device="auto")
text = "The battery life is excellent but the keyboard feels cheap."
aspect_result = classifier.classify_aspect_sentiment(text, "battery life", 4, 16)
pipeline = AspectAnalyzer(extractor, classifier)
aspects_with_sentiment = pipeline.analyze_aspects(text)
```

Ví dụ chỉ gọi API, không khẳng định sẵn polarity của model. Repeated term bắt buộc start/end để chỉ đúng occurrence. ASC trả negative/neutral/positive và confidence=null; pipeline trả term/start/end/sentiment và hai score=null, không aspect trả[]. ASC cap128 tính cả markers; overlength/unsupported language được báo lỗi. Standalone SemEval dùng gold aspects; joint score dùng P8 predicted spans và ignore exact conflict-span predictions khi chấm, không thể dùng thay canonical ASC macroF1. Không triển khai P10 hoặc chạy ABSA pseudo labels trên Amazon30K.
