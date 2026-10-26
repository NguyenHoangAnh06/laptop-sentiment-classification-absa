# Xác minh kết quả TabPFN Kaggle full21K — 2026-10-24

> Tiếp nối sau import: `reports/p7_error_cause_analysis.md` đã bổ sung phân tích lỗi6model active. CSV p7_error_* hiện nay đã gồm cloud; mô tả giữ CSV local dưới đây phản ánh trạng thái lúc import và bản local cũ còn trong snapshot history. Tests mới của chẩn đoán được ghi riêng, không thay bằng chứng import291tests.

## Nguồn và quyết định

ZIP nguồn: `cloud/results/tabpfn_cloud_results_20261024T134959209612Z.zip` (112402bytes). SHA256: `041e66d97c14c760a6cc5231ac8df4e8314c972a0835d21ac6bbfe25db6c9e3b`.

Import riêng: `artifacts/cloud_runs/tabpfn_full21k_20261024/`. ZIP CRC/members/path safety PASS; không overwrite artifact local. Archive hash coverage, từng run hashes và bundle metadata hashes PASS.

**V3: SUCCESS; V3.5: SUCCESS.** Cả hai đủ21000train; đã thay hai dòng subsample trong P7 bằng kết quả cloud. Không rerun model/P0–P7. Local subsample giữ nguyên artifact và snapshot `reports/history/tabpfn_before_kaggle_20261024/` có hash.

## Dữ liệu và protocol

Manifest cloud khớp nguyên byte manifest local (SHA25680a7ec0f80b4d8db7689448829fec97e4c505c4eed5af733ad88b1ec0a4bf82c). Source split/embedding hashes từng split được đối chiếu file local thật; labels/IDs bundle đối chiếu parquet gốc; đủ21000/4500/4500,384chiều,float32,negative0/neutral1/positive2. IDs unique/no overlap; cả4500validation và4500test predictions khớp toàn bộID đúng thứ tự và y_true. Không chỉ dựa tên folder.

Code bundle được hash, candidate config đơn định trước và selection lock/metadata cho thấy: fit nhận fulltrain21000 → validation4500 → ghi lock chứa hash validation metrics → test4500. Config cloud bằng config bundle đã đóng băng; seed42/fit_with_cache/cacheCPU/memory_saving/autocast/n_estimators1/batch16. Probe chỉ dùng train, tăng500/1000/2500/5000/10000/21000, tất cả PASS cho cả hai model. Không đổi embeddings, không TF-IDF/SVD/PCA và không tuning bằng test trong code đã đóng gói.

Giới hạn evidence: không có attestation độc lập, fitted estimator hay log timestamp từng thao tác; protocol được đối chiếu từ code/config/lock/hash/metadata, không chứng minh tuyệt đối lịch sử chạy nếu bên chạy cố ý sửa code ngoài bundle. Lock hash và validation hash khớp. Test này là reused test, không phải holdout mới; không dùng kết quả để tune lại.

## Trạng thái/version/train size

| Model | Status | Train metadata/lock/probe | Requested | Resolved | Package | Checkpoint |
|---|---|---:|---|---|---|---|
| v3 | SUCCESS | 21000 | V3 | V3 | 9.2.0 | tabpfn-v3-classifier-v3_default.ckpt |
| v35 | SUCCESS | 21000 | V3_5 | V3_5 | 9.2.0 | tabpfn-v3.5-20260909.safetensors |

Hai checkpoint khác nhau; tên version đối chiếu với resolver/candidate bundle đã kiểm SDK local trước khi xuất. Không tải checkpoint hoặc fit lại để verify.

## Metrics tính lại local

Dùng `src.evaluation.classification.classification_metrics`; balanced accuracy=mean recall ba lớp, đúng utility runner hiện tại. So toàn bộ JSON/per-class/support/confusion/order và confusion CSV; abs tolerance1e-12. **Max absolute delta cloud-vs-local =0 cho cả validation/test của cả hai model.**

| Model | Split | Macro F1 | Accuracy | Weighted F1 | Balanced accuracy | Neutral F1 | Max delta |
|---|---|---:|---:|---:|---:|---:|---:|
| v3 | validation | 0.580693833 | 0.822000000 | 0.787721293 | 0.586338276 | 0.076923077 | 0.0 |
| v3 | test | 0.572971458 | 0.826666667 | 0.790161351 | 0.587600852 | 0.039800995 | 0.0 |
| v35 | validation | 0.614332485 | 0.838666667 | 0.810180260 | 0.621930717 | 0.132420091 | 0.0 |
| v35 | test | 0.614017409 | 0.837555556 | 0.809843492 | 0.621268495 | 0.135746606 | 0.0 |

| Model | Test class | Precision | Recall | F1 | Support |
|---|---|---:|---:|---:|---:|
| v3 | negative | 0.776629571 | 0.788539144 | 0.782539047 | 1239 |
| v3 | neutral | 1.000000000 | 0.020304569 | 0.039800995 | 394 |
| v3 | positive | 0.845701917 | 0.953958842 | 0.896574332 | 2867 |
| v35 | negative | 0.753033547 | 0.851493140 | 0.799242424 | 1239 |
| v35 | neutral | 0.625000000 | 0.076142132 | 0.135746606 | 394 |
| v35 | positive | 0.879711570 | 0.936170213 | 0.907063197 | 2867 |

Confusion matrices test, thứ tự negative/neutral/positive (hàng=true,cột=pred):

`v3`:
```json
[[977, 0, 262], [149, 8, 237], [132, 0, 2735]]
```

`v35`:
```json
[[1055, 7, 177], [174, 30, 190], [172, 11, 2684]]
```

## Cloud full21K so với local subsample

| Model | Local train | Local macro F1 | Cloud macro F1 | Delta macro | Local neutral F1 | Cloud neutral F1 |
|---|---:|---:|---:|---:|---:|---:|
| v3 | 10000 | 0.562543798 | 0.572971458 | +0.010427660 | 0.015075377 | 0.039800995 |
| v35 | 1500 | 0.570951612 | 0.614017409 | +0.043065797 | 0.032710280 | 0.135746606 |

BERT vẫn best theo validation/test Macro F1 và Neutral F1; TabM best frozen. Thứ hạng test macro F1: BERT0,755382 > TabM0,689086 > XGBoost0,667752 > V3.5 full0,614017 > V3 full0,572971 > majority0,259445. V3 balanced accuracy giảm từ0,591434 local xuống0,587601 cloud dù macro F1 tăng; không gọi mọi metric đều cải thiện. Không kết luận causal gain chỉ do train size vì hardware/môi trường thay đổi.

## Tài nguyên và environment

| Model | Fit s | Validation s | Test s | Wall s | Peak RSS bytes | GPU allocated bytes | GPU reserved bytes | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v3 | 7.968203 | 35.430766 | 35.343691 | 80.046892 | 2287575040 | 6195194880 | 9086959616 | Tesla T4 |
| v35 | 21.145939 | 48.590992 | 48.269700 | 119.244243 | 3121553408 | 7439429120 | 14350811136 | Tesla T4 |

Cả hai: Kaggle Linux,Python3.13.15,torch2.11.0+cu128,CUDA12.8,numpy2.2.6,sklearn1.7.2,tabpfn9.2.0,4CPU,RAM total33658155008bytes. Final peak RSS2,288/3,122GB; allocated6,195/7,439GB; reserved9,087/14,351GB (GB=10^9bytes). Probe full21K peakRSS2,281/3,140GB; probe/final đo riêng. RSS sampled20ms; CUDA peak allocated/reserved không phải toànGPU. Wall chưa gồm toàn bộprobe/cài đặt; chi phí tiền NOT_MEASURED. Local V3 dùng10K với RSS6,48GB và V3.5 dùng1,5K với RSS4,55GB, không trực tiếp so tốc độ do khác máy/runner.

Cloud ZIP chỉ có kết quả, không weights. Bảng chính artifact_bytes để trống, artifact_file_bytes_actual là dung lượng run result813992/814014bytes; không so với model checkpoint local.

## Update decision và bảo toàn

Đã cập nhật P7 CSV/report/completion, model_stack_refactor_completion, README, PLAN files và trạng thái cloud/handoff. Snapshot local trước update gồm7tệp+hashes trong reports/history/tabpfn_before_kaggle_20261024. Mọi artifact model subsample giữ nguyên. P7 error CSV local giữ nguyên và được gắn ngữ cảnh lịch sử trong báo cáo mới; không giả phân tích lỗi cloud.

Bảo toàn153scientific inputs/local outputs ngoài2P7file được phép cập nhật: PASS.53legacy output hashes(27+26): PASS. Giá trị và chuỗi CSV của majority/XGBoost/TabM/BERT giữ nguyên. Các generator finish_benchmark/final_completion chuyển tới publisher có reverify khi cloud đang active, tránh khôi phục nhầm subsample. Không sửa weights/dataset/split/cache hoặc inference outputs cũ.

## Tests

**291PASS,0FAIL**:271+12+8 qua `.venv/Scripts/python.exe -B -m scripts.test_all`. Gồm276test hiện có và15test mới; hai test P7 cũ cập nhật để kiểm provenance cloud đầy đủ thay hardcode SUBSAMPLED, vẫn giữ fallback local. Có10DeprecationWarnings SDK ở nhóm cũ.

Targeted verifier/P7:19PASS. Kiểm dữ liệu thật, metrics tolerance/NaN, ZIP unsafe path/không overwrite, metadata train/version/ID/lock/metric bị sửa có rehash, thiếu artifact/failure, và bảo toàn model rows local. Hai lỗi fixture ban đầu (Windows zipfile normalize backslash và NaN CSV comparison) đã sửa trước full suite. Lỗi verifier ban đầu do đường dẫn relative đã chuẩn hóa resolve, reverify SUCCESS trước publish; không có data failure bị bỏ qua.

## Files modified

- `scripts/verify_kaggle_results.py`
- `scripts/publish_kaggle_results.py`
- `scripts/finish_benchmark.py`
- `scripts/final_completion.py`
- `tests/test_kaggle_results.py`
- `tests/test_final_benchmark.py`
- `reports/p7_unified_results.csv`
- `reports/p7_unified_benchmark.md`
- `reports/p7_completion.json`
- `reports/model_stack_refactor_completion.md`
- `reports/tabpfn_kaggle_full21k_verification.md`
- `reports/tabpfn_kaggle_full21k_verification.json`
- `PLAN_AI.md`
- `PLAN_HUMAN.md`
- `README.md`
- `docs/PROJECT_INDEX.md`
- `docs/TABPFN_CLOUD_PLAN.md`
- `docs/CODEX_HANDOFF.md`
- `.gitignore`

- `scripts/benchmark_reports.py`
- `reports/p5_modern_tabular_models.md`
- `reports/p5_e03_tabpfn_v3.md`
- `reports/p5_e04_tabpfn_v35.md`

Artifact nhập mới: `artifacts/cloud_runs/tabpfn_full21k_20261024/`; source ZIP giữ nguyên. Snapshot lịch sử giữ bản trước update với hashes.

## Giới hạn nghiên cứu

Các phát hiện chỉ dành laptop tiếng Anh; nhãn đại diện suy từ số sao có nhiễu; SemEval-to-Amazon platform/style shift trong laptop còn thuộc ABSA; bộ gold gán nhãn thủ công dự kiến nhỏ, hiện chưa có. Không khẳng định production/model tiếng Việt hoặc toàn dự án đã hoàn tất. Bước tiếp là xem xét pha P8 theo PLAN; tác vụ này không tự khởi chạy pha/model mới.
