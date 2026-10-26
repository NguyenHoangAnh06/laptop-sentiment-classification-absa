# Chỉ mục tài liệu và bằng chứng

Cập nhật 2026-10-26. P0–P8 đã khóa; P9 ASC và end-to-end ABSA DONE, READY FOR P10. Independent Amazon gold/domain-shift evaluation/app chưa hoàn tất. Dùng chỉ mục này thay vì đọc snapshot lịch sử như trạng thái hiện tại.

## Tài liệu hiện hành

| Tài liệu | Vai trò |
|---|---|
| [README](../README.md) | Bắt đầu, môi trường, bảng tóm tắt và lệnh xác minh |
| [AGENTS](../AGENTS.md) | Phạm vi/integrity/ngôn ngữ/cổng tài nguyên và bàn giao |
| [PLAN_HUMAN](../PLAN_HUMAN.md), [PLAN_AI](../PLAN_AI.md) | P0–P13 hiện hành, ID và tiêu chí nghiệm thu |
| [Bàn giao](CODEX_HANDOFF.md) | Trạng thái mới nhất và hành động tiếp |
| [Lịch sử thực thi](PROJECT_EXECUTION_LOG.md) | Canonical history P0–P9-EXP01: chronology, experiment/decision registry, canonical models, tests, failures và khoảng trống provenance |
| [Hợp đồng benchmark](MODEL_STACK_REFACTOR.md) | Representation, model/version và protocol local |
| [Cloud full21000](TABPFN_CLOUD_PLAN.md) | V3/V3_5 full21000 SUCCESS; hash/metrics/resources đã verified |
| [Từ điển dữ liệu](../data_dictionary.md) | Schema nguồn/processed; metadata không phải model features |

## P3 — EDA trọng tâm hiện hành

- [Báo cáo canonical](../reports/p3_refinement_20261026/report.md), [HTML tự chứa](../reports/p3_refinement_20261026/report.html): 8bảng core/3hình, Neutral/phrase effect sizes/context/concentration/proxy risk và traceability; 9mục appendix.
- [Audit từng artifact](../reports/p3_refinement_20261026/audit.md), [config/source/output hashes](../reports/p3_refinement_20261026/summary.json); tái dựng bằng `scripts.refine_p3` vào thư mục mới.
- `reports/p3_data_analysis_20261009.md`, `reports/p3_insight_summary_20261009.md`, `reports/p3/20261009_verified/`, notebook và HTML20261019 là lịch sử giữ nguyên. P4–P9 vẫn dùng manifests/hash cũ; không sửa scientific artifact để thay canonical trình bày.

## Kết quả benchmark local đã chạy

| Bằng chứng | Vai trò |
|---|---|
| [Completion A–M](../reports/model_stack_refactor_completion.md) | Trạng thái và giới hạn tổng thể |
| [P5](../reports/p5_modern_tabular_models.md), [P6](../reports/p6_transformer_benchmark.md), [P7](../reports/p7_unified_benchmark.md) | Báo cáo từng phần |
| [CSV cuối](../reports/p7_unified_results.csv) | Nguồn bảng sáu model, không làm tròn metrics gốc |
| [Final validation](../reports/model_stack_final_validation.json) | Snapshot249tests local;291cloud/321diagnosis/350P8/378P9/380P9-EXP01 là lịch sử; hiện386tests ở P3 refinement validation |
| [Bảo toàn legacy](../reports/model_stack_legacy_preservation_final.json) | 53tệp output lịch sử không đổi |
| [V3 resources](../reports/p5_e03_tabpfn_v3_resource_assessment.md), [V3.5 resources](../reports/p5_e04_tabpfn_v35_resource_assessment.md) | Đo local; không phải bằng chứng cloud |
| [Phiên bản TabPFN](../reports/tabpfn_version_verification.json) | Requested/resolved/checkpoint riêng biệt |

`reports/semantic_20261024/` giữ prediction/selection/metrics/hashes/candidate history; E03 đọc con trỏ `latest_attempt.json` tới `attempts/resource01`. Root E03 BLOCKED là lỗi license **lịch sử**, không phải trạng thái hiện hành. `reports/tabpfn_smoke_20261024/` và `reports/tabpfn_resources_20261024/` là bằng chứng cần giữ, gồm cả lỗi CPU và lần bị ngắt. P5 CSV là bảng riêng năm model; CSV P7 là bảng cuối sáu model, không cần bản sao tên `partial_results`.

Error transitions/groups là mô tả proxy; `reports/p7_error_examples.csv` giữ cục bộ/.gitignore vì chứa trích đoạn review, không human verified và không publish tự động. Không xóa raw/source/split/cache/checkpoint/model/dự đoán hoặc nhãn manual để dọn tài liệu.

## Lịch sử và phạm vi LEGACY

- [Snapshot trước dọn dẹp](archive/20261024_before_cleanup/manifest.json): hai PLAN, README, bàn giao và generator cũ với hash kiểm tra. Dùng để tra quyết định trước, không chạy lệnh huấn luyện từ snapshot vào output đã có.
- [P4 contract](P4_DATA_CONTRACT.md), [P5 contract](P5_MODEL_CONTRACT.md), [P6 contract](P6_MODEL_CONTRACT.md): mô tả TF-IDF/BERT body-only2026-10-15; vẫn cần cho tái lập artifacts cũ, không thay hợp đồng semantic mới.
- [Việt hóa2026-10-19](VIETNAMESE_TRANSLATION.md): báo cáo ngôn ngữ ở thời điểm đó; câu P7 chưa bắt đầu là lịch sử.
- `reports/p5/p5_20261015/`, `reports/p6/p6_20261015/`, báo cáo completion2026-10-15 và các bản kê hashes: bất biến; không sửa kết quả lịch sử để khớp docs mới.
- `reports/model_stack_validation.json`: snapshot240tests/license BLOCKED trước khi tiếp tục; thay cho trạng thái hiện hành phải đọc `model_stack_final_validation.json`. Bản preservation không có hậu tố `_final` cũng là snapshot cũ.
- `reports/continuation_implementation_sha256.json`: snapshot source sau benchmark local, trước cleanup; không phải checksum của source đã sửa sau đó. Checksum các generator sau cleanup được ghi riêng trong `reports/documentation_cleanup_20261024.json`.
- `customer_sentiment_analysis_plan.docx`: kế hoạch Word lịch sử, mục tiêu50K đã được thay bằng30K; không là tài liệu điều khiển hiện tại. Giữ đường dẫn cho provenance/tài liệu tham chiếu.
- `scripts/audit_plan_progress.py`, `train_p5`/`train_p6`, `verify_benchmark`: công cụ các pha trước; không dùng để sinh lại artifacts frozen hoặc đánh dấu P9. Xác minh hiện hành: `scripts.finalize_p9_exp01 --run-checks`.

## Ghi chú về công việc còn lại

Kaggle full21K V3/V3_5 verified; [xác minh](../reports/tabpfn_kaggle_full21k_verification.md) giữ evidence import, [snapshot local](../reports/history/tabpfn_before_kaggle_20261024/p7_unified_benchmark.md) giữ subsample/RSS. p7_completion.json chứa cloud provenance. P8/P9 nay hoàn tất riêng; tiếp P10 chỉ khi có yêu cầu, không tự tạo human gold. Chỉ laptop/noisy sentiment proxy; independent gold nhỏ và SemEval–Amazon shift chưa đánh giá.

## Chẩn đoán sentiment hiện hành

- [Phân tích lỗi, proxy rating và mất cân bằng](../reports/p7_error_cause_analysis.md):6model active; CSV p7_error_* hiện hành đã gồm cloud. Snapshot CSV local trước cloud vẫn ở history.
- [Hướng dẫn audit đọc mù](SENTIMENT_DIAGNOSIS.md):360 human-reviewed hoàn tất ngày2026-10-25;300SRS test+60enriched, không trộn population inference và không phải independent gold.
- `reports/p7_error_diagnosis_validation.json`: bằng chứng tests/preservation cho tác vụ chẩn đoán; số291ở báo cáo import cloud là lịch sử import.

**P7: DONE.** Human–proxy/model diagnosis: `reports/p7_human_audit_results.json`; P0–P7 acceptance: `reports/p0_p7_acceptance.json`. Causal contribution của imbalance chưa xác định, không phải blocker P7. Independent P10 gold vẫn PENDING. Bản trước human review là lịch sử tại `reports/history/p7_before_human_20261025/`.

## P8 — Aspect Term Extraction hiện hành

- [Báo cáo P8](../reports/p8_aspect_extraction.md): SemEval laptop/BIO/BERT token classification, strict entity P/R/F1, lỗi và giới hạn.
- [Nghiệm thu](../reports/p8_20261026/acceptance.json), [xác minh metric](../reports/p8_20261026/independent_evaluation.json), [350tests](../reports/p8_20261026/validation.json), [269files bảo toàn](../reports/p8_20261026/preservation.json).
- `configs/p8_aspect_extraction.yaml`: seed42/5epoch/lr3e-5/batch8×accum2/max128; chọn epoch4 bằng validation entityF1.
- BIO/split IDs/provenance: `data/processed/p8_20261026/`; best model/tokenizer/metadata: `artifacts/models/p8_20261026/best/`; predictions/error examples có text chỉ local: `data/interim/p8_20261026/`.
- API `src.absa.extraction.AspectExtractor.extract_aspects`, score=null, không polarity; CPU smoke đã PASS. Tái lập/xác minh bằng `scripts.prepare_p8` và `scripts.finalize_p8`; không mở lại run train đã selection.

**P8: DONE / FROZEN.** Giữ1official natural duplicate và1train whitespace-boundary adjustment có công bố;0unexplained alignment failures. P9 reuse model/predictions, không retrain hoặc sửa test score P8. Các report/350tests P8 là snapshots; shared test driver đã mở rộng nên dùng cổng P9 cho xác minh hiện tại, giữ nguyên evidence cũ.

## P9 — ASC và joint ABSA hiện hành

- [Báo cáo DeBERTa canonical](../reports/p9_exp01_deberta_20261026_v2/report.md), [nghiệm thu](../reports/p9_exp01_deberta_20261026_v2/acceptance.json), [quyết định validation](../reports/p9_exp01_deberta_20261026_v2/canonical_decision.json), [380tests](../reports/p9_exp01_deberta_20261026_v2/validation.json), [381files frozen](../reports/p9_exp01_deberta_20261026_v2/preservation.json).
- Selector `configs/p9_canonical.yaml`; config experiment `configs/p9_exp01_deberta.yaml`: microsoft/deberta-v3-base pinned, unweighted epoch5/seed42, lr3e-5,physical4×accum4,5epochs/loss. Validation macroF1=0,777467 so với BERT0,714145; seed43/44 validation-only, không chọn best seed.
- Giữ1999/314/638examples, split/text/offsets/labels/conflict và marker strings; native tokenizer CLS/SEP + marker IDs128001/128002, max128/zero truncation. Original dataset/conflict metadata tại `data/processed/p9_20261026/`; token cache mới `data/processed/p9_exp01_deberta_20261026_v2/`.
- Selected checkpoint `artifacts/models/p9_exp01_deberta_20261026_v2/unweighted/best/`. Predictions/error pairs chỉ local `data/interim/p9_exp01_deberta_20261026_v2/`. [BERT previous canonical](../reports/p9_aspect_sentiment.md) và namespace `p9_20261026` giữ nguyên; source snapshot11files khớp hash tại report mới.
- API classifier/pipeline giữ hợp đồng en/3labels/confidence=null; CPU smoke PASS. Fresh-run/reload hợp lệ; resume DeBERTa NOT_SUPPORTED do vocab mismatch, attempt seed43 bị ngắt đã restart pretrained riêng. Attempts thiếu CLS/SEP bị loại trước test, không dùng score trong comparison.
- Xác minh hiện hành: `scripts.finalize_p9_exp01 --run-checks`, không predict test lại. `comparison.json` kiểm độc lập metrics, paired errors, native cache, selection/stability và frozen P8 spans. `validation_latency.json` so sánh cùng314validation/batch16; không raw-text latency.

**P9-EXP01 COMPLETE — READY TO CONTINUE TO P10.** Gold-aspect test macroF1=0,780433; joint test P/R/F1=0,644776/0,677116/0,660550. Không triển khai P10, pseudo-label Amazon30K hoặc retrain P0–P8.
