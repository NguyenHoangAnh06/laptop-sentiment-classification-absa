# Báo cáo hoàn tất benchmark bộ mô hình — cập nhật Kaggle 2026-10-24

Benchmark chính đủ6model full21000; hai TabPFN cloud SUCCESS. Đây không phải toàn dự án DONE. Báo cáo local A–M nguyên bản được giữ trong thư mục lịch sử để bảo toàn provenance.

## A. Status

P0–P4/P6 và majority/XGBoost/TabM/BERT: REUSED, không retrain. C-E03/C-E04: SUCCESS/FULL21000, Kaggle Tesla T4. P7 cập nhật chỉ sau verify saved predictions. ABSA/gold/app còn PENDING.

## B. Dataset và split

Giữ dataset30000 và split21000/4500/4500/seed42. Hash/row order/label mapping đã đối chiếu nguồn thật; không resplit/relabel/regenerate embeddings.

## C. Representation

Frozen MiniLM384FP32/L2 cho classifier; BERT canonical title+body end-to-end. Không dùng thêm biểu diễn giảm chiều hoặc features metadata.

## D. Models

TabPFN9.2.0 explicit V3/V3_5 với checkpoint khác nhau và train_count21000 được đối chiếu metadata/lock/probe. Model artifacts local giữ nguyên.

## E. Protocol

Validation macro F1 lựa chọn chính; cấu hình cloud đơn định trước, train-only probe, lock trước reused test theo code bundle và metadata; không test tuning.

## F. Final table

| model | train_samples | data_regime | validation_macro_f1 | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 21000 | FULL | 0.259390 | 0.259445 | 0.637111 | 0.495886 | 0.333333 | 0.000000 | 0.000000 | 0.778336 |
| E01_xgboost_embedding | 21000 | FULL | 0.664566 | 0.667752 | 0.799333 | 0.812327 | 0.687805 | 0.794650 | 0.321138 | 0.887468 |
| E02_tabm_embedding | 21000 | FULL | 0.680132 | 0.689086 | 0.818444 | 0.832269 | 0.712587 | 0.828638 | 0.336673 | 0.901946 |
| E03_tabpfn_v3_embedding | 21000 | FULL | 0.580694 | 0.572971 | 0.826667 | 0.790161 | 0.587601 | 0.782539 | 0.039801 | 0.896574 |
| E04_tabpfn_v35_embedding | 21000 | FULL | 0.614332 | 0.614017 | 0.837556 | 0.809843 | 0.621268 | 0.799242 | 0.135747 | 0.907063 |
| E05_transformer | 21000 | FULL | 0.760338 | 0.755382 | 0.886667 | 0.886262 | 0.756344 | 0.878571 | 0.436129 | 0.951446 |

## G. Best model

Chọn theo validation macro F1: **E05_transformer**; best frozen: **E02_tabm_embedding**. Thứ hạng test Macro F1 chỉ mô tả kết quả đã khóa: E05_transformer > E02_tabm_embedding > E01_xgboost_embedding > E04_tabpfn_v35_embedding > E03_tabpfn_v3_embedding > E00_majority. Neutral F1 cao nhất vẫn BERT; TabM đứng sau. Cả hai TabPFN full21K cải thiện so với subsample nhưng vẫn thấp hơn BERT/TabM về Macro F1 và Neutral F1; không điều chỉnh sau test.

## H. Resource findings

| Model | Fit s | Val s | Test s | Wall s | RSS GB | GPU allocated GB | GPU reserved GB | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| E03_tabpfn_v3_embedding | 7.968 | 35.431 | 35.344 | 80.047 | 2.288 | 6.195 | 9.087 | Tesla T4 |
| E04_tabpfn_v35_embedding | 21.146 | 48.591 | 48.270 | 119.244 | 3.122 | 7.439 | 14.351 | Tesla T4 |

Local/cloud khác hardware và runtime scope; không suy diễn tốc độ thuần model. Weights cloud không được xuất, artifact results không đại diện model size.

## I. Error analysis

Bảng local trước cloud: `reports/history/tabpfn_before_kaggle_20261024/p7_unified_results.csv`; báo cáo/metrics/artifacts subsample10000/1500 không bị xóa. Resource local V3 RSS6,48GB vượt trần6GB và V3.5 dùng1500 vẫn là bằng chứng lịch sử. Các CSV lỗi local trước cloud được bảo toàn trong `reports/history/tabpfn_before_kaggle_20261024`. CSV p7_error_* hiện hành được sinh lại từ6model active, gồm TabPFN cloud; không dùng subsample để diễn giải cloud.

## J. Limitations

Chỉ review laptop tiếng Anh; nhãn đại diện suy từ sao có nhiễu, không phải human sentiment gold. Test đã xem ở LEGACY/local/cloud, không gọi unseen mới. Một seed42, không kết luận ưu thế thống kê. SemEval-to-Amazon platform/style shift trong laptop còn thuộc ABSA; bộ gold thủ công dự kiến nhỏ, chưa có. V3 n_estimators1 vẫn giới hạn coverage nội bộ tối đa200/384chiều; không thay embeddings384. Context MiniLM256/BERT512 và paradigm frozen/end-to-end khác nhau; không khẳng định production hoặc hỗ trợ tiếng Việt.

## K. Reproducibility

Source ZIP, SHA256, môi trường Linux/Python3.13.15/torch2.11.0+cu128/sklearn1.7.2, local recomputed metrics đầy đủ và protocol evidence nằm ở verification report. Manifest/prediction/selection_lock hashes được lưu nguyên.

## L. Tests

Bằng chứng lúc import cloud ở `reports/tabpfn_kaggle_full21k_verification.json`; kiểm thử tác vụ chẩn đoán mới ở `reports/p7_error_diagnosis_validation.json`. Dùng `python -m scripts.test_all`, không chạy model benchmark để verify.

## M. Files và lịch sử

Bảng local trước cloud: `reports/history/tabpfn_before_kaggle_20261024/p7_unified_results.csv`; báo cáo/metrics/artifacts subsample10000/1500 không bị xóa. Resource local V3 RSS6,48GB vượt trần6GB và V3.5 dùng1500 vẫn là bằng chứng lịch sử. Các CSV lỗi local trước cloud được bảo toàn trong `reports/history/tabpfn_before_kaggle_20261024`. CSV p7_error_* hiện hành được sinh lại từ6model active, gồm TabPFN cloud; không dùng subsample để diễn giải cloud.

Báo cáo cập nhật: p7_unified_results.csv/p7_unified_benchmark.md/p7_completion.json và báo cáo này. Không sửa raw/processed/cache/local model/saved predictions. Công cụ `scripts.publish_kaggle_results` reverify trước publish; không nhập bằng tên folder đơn thuần.

<!-- error_diagnosis:start -->
## Chẩn đoán sentiment đã hoàn tất

**P7: DONE — READY FOR P8.** 360 human-reviewed sentiment diagnosis reviews; agreement 292/360 (81.11%), disagreement 68/360 (18.89%). Sáu model gồm TabPFN cloud full21K đã đối chiếu human/proxy.

360 là mẫu chẩn đoán gồm 300 SRS test + 60 enriched; tỷ lệ gộp chỉ mô tả mẫu, không ước lượng toàn 30K. Independent P10 gold vẫn PENDING. Causal fraction của imbalance chưa xác định, không là blocker P7. Benchmark/selection/splits/weights giữ nguyên; không cần retrain trước P8.

Bằng chứng: `reports/p7_error_cause_analysis.md`, `reports/p7_human_audit_results.json`, `reports/p0_p7_acceptance.json`. Dừng tại READY FOR P8, chưa triển khai P8.
<!-- error_diagnosis:end -->
