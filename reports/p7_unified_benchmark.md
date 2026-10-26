# P7 — Đánh giá thống nhất sau xác minh Kaggle

PASS: hai TabPFN full21000 đã verified; bảng chính dùng cloud thay subsample, giữ local lịch sử. Không rerun P0–P7/model; chỉ tính lại saved predictions và cập nhật báo cáo.

| model | train_samples | data_regime | validation_macro_f1 | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 21000 | FULL | 0.259390 | 0.259445 | 0.637111 | 0.495886 | 0.333333 | 0.000000 | 0.000000 | 0.778336 |
| E01_xgboost_embedding | 21000 | FULL | 0.664566 | 0.667752 | 0.799333 | 0.812327 | 0.687805 | 0.794650 | 0.321138 | 0.887468 |
| E02_tabm_embedding | 21000 | FULL | 0.680132 | 0.689086 | 0.818444 | 0.832269 | 0.712587 | 0.828638 | 0.336673 | 0.901946 |
| E03_tabpfn_v3_embedding | 21000 | FULL | 0.580694 | 0.572971 | 0.826667 | 0.790161 | 0.587601 | 0.782539 | 0.039801 | 0.896574 |
| E04_tabpfn_v35_embedding | 21000 | FULL | 0.614332 | 0.614017 | 0.837556 | 0.809843 | 0.621268 | 0.799242 | 0.135747 | 0.907063 |
| E05_transformer | 21000 | FULL | 0.760338 | 0.755382 | 0.886667 | 0.886262 | 0.756344 | 0.878571 | 0.436129 | 0.951446 |

Chọn theo validation macro F1: **E05_transformer**; best frozen: **E02_tabm_embedding**. Thứ hạng test Macro F1 chỉ mô tả kết quả đã khóa: E05_transformer > E02_tabm_embedding > E01_xgboost_embedding > E04_tabpfn_v35_embedding > E03_tabpfn_v3_embedding > E00_majority. Neutral F1 cao nhất vẫn BERT; TabM đứng sau. Cả hai TabPFN full21K cải thiện so với subsample nhưng vẫn thấp hơn BERT/TabM về Macro F1 và Neutral F1; không điều chỉnh sau test.

## Tài nguyên và khả năng so sánh

| Model | Fit s | Val s | Test s | Wall s | RSS GB | GPU allocated GB | GPU reserved GB | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| E03_tabpfn_v3_embedding | 7.968 | 35.431 | 35.344 | 80.047 | 2.288 | 6.195 | 9.087 | Tesla T4 |
| E04_tabpfn_v35_embedding | 21.146 | 48.591 | 48.270 | 119.244 | 3.122 | 7.439 | 14.351 | Tesla T4 |

Đơn vị GB=10^9bytes. RSS sampled20ms; allocated/reserved theo PyTorch, không phải toàn VRAM vật lý. Wall cloud gồm setup model/fit/validation/test trong monitor, không gồm probe; local runtime có search/reload. Không so runtime như cùng điều kiện. Latency từ embedding/token có sẵn, không phải raw-text end-to-end. Tiền compute NOT_MEASURED. Cloud không trả model weights: artifact_bytes để trống; artifact_file_bytes_actual chỉ là gói kết quả, không so với kích thước fitted model local.

## Protocol và provenance

Dataset/split/hash/ID/labels/embeddings giữ nguyên. Candidate seed42/n_estimators1/fit_with_cache/cacheCPU/autocast/batch16 cố định trước cloud; probe chỉ train. Fit train21000 → validation4500 → selection lock → test4500. Hash manifest cloud khớp local; predictions align toàn4500ID và nhãn, mọi metric/ma trận tính lại khớp abs tolerance1e-12, max delta0. Evidence là code bundle được hash/config/lock/metadata, không có attestation độc lập hoặc timestamp log để chứng minh tuyệt đối lịch sử thực thi. Test reuse được công bố.

## Lịch sử và phân tích lỗi

Bảng local trước cloud: `reports/history/tabpfn_before_kaggle_20261024/p7_unified_results.csv`; báo cáo/metrics/artifacts subsample10000/1500 không bị xóa. Resource local V3 RSS6,48GB vượt trần6GB và V3.5 dùng1500 vẫn là bằng chứng lịch sử. Các CSV lỗi local trước cloud được bảo toàn trong `reports/history/tabpfn_before_kaggle_20261024`. CSV p7_error_* hiện hành được sinh lại từ6model active, gồm TabPFN cloud; không dùng subsample để diễn giải cloud.

| model | train_samples | data_regime | validation_macro_f1 | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| E03_tabpfn_v3_embedding | 10000 | SUBSAMPLED | 0.574185 | 0.562544 | 0.821111 | 0.785736 | 0.591434 | 0.777241 | 0.015075 | 0.895315 |
| E04_tabpfn_v35_embedding | 1500 | SUBSAMPLED | 0.572939 | 0.570952 | 0.823111 | 0.790340 | 0.592344 | 0.782144 | 0.032710 | 0.898000 |

## Giới hạn

Chỉ review laptop tiếng Anh; nhãn đại diện suy từ sao có nhiễu, không phải human sentiment gold. Test đã xem ở LEGACY/local/cloud, không gọi unseen mới. Một seed42, không kết luận ưu thế thống kê. SemEval-to-Amazon platform/style shift trong laptop còn thuộc ABSA; bộ gold thủ công dự kiến nhỏ, chưa có. V3 n_estimators1 vẫn giới hạn coverage nội bộ tối đa200/384chiều; không thay embeddings384. Context MiniLM256/BERT512 và paradigm frozen/end-to-end khác nhau; không khẳng định production hoặc hỗ trợ tiếng Việt.

Bằng chứng: `reports/tabpfn_kaggle_full21k_verification.md`/`.json`; provenance map trong `reports/p7_completion.json`. Toàn dự án ABSA/gold/app vẫn PENDING.

<!-- error_diagnosis:start -->
## Chẩn đoán sentiment đã hoàn tất

**P7: DONE — READY FOR P8.** 360 human-reviewed sentiment diagnosis reviews; agreement 292/360 (81.11%), disagreement 68/360 (18.89%). Sáu model gồm TabPFN cloud full21K đã đối chiếu human/proxy.

360 là mẫu chẩn đoán gồm 300 SRS test + 60 enriched; tỷ lệ gộp chỉ mô tả mẫu, không ước lượng toàn 30K. Independent P10 gold vẫn PENDING. Causal fraction của imbalance chưa xác định, không là blocker P7. Benchmark/selection/splits/weights giữ nguyên; không cần retrain trước P8.

Bằng chứng: `reports/p7_error_cause_analysis.md`, `reports/p7_human_audit_results.json`, `reports/p0_p7_acceptance.json`. Dừng tại READY FOR P8, chưa triển khai P8.
<!-- error_diagnosis:end -->
