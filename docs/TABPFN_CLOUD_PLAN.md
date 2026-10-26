# TabPFN cloud full21000 — nghiệm thu Kaggle 2026-10-24

**PASS: V3 và V3_5 full21000 đã import và verified.** Người dùng chạy Kaggle, Codex chỉ đọc ZIP/tính lại saved predictions; không upload/chạy lại model. Báo cáo có thẩm quyền: [xác minh](../reports/tabpfn_kaggle_full21k_verification.md), [P7 hiện hành](../reports/p7_unified_benchmark.md).

## Trạng thái P5-C01–C06

| ID | Kết quả |
|---|---|
| C01 | Kaggle Tesla T4,4CPU,RAM33658155008bytes; người dùng đã chạy. Chi phí tiền NOT_MEASURED |
| C02 | Bundle riêng giữ seed42/split/embeddings/labels/IDs; manifest cloud khớp local |
| C03 | Probe V3 train-only500→1000→2500→5000→10000→21000: tất cả PASS |
| C04 | C-E03 V3 full21000 SUCCESS; metrics/ID/version/selection lock verified |
| C05 | Probe và C-E04 V3_5 riêng full21000 SUCCESS; không suy tài nguyên từ V3 |
| C06 | Bảng chính P7 thay hai dòng bằng cloud full21K; local subsample giữ trong snapshot/history và artifacts gốc |

TabPFN9.2.0,ModelVersion.V3/V3_5 resolve thành checkpoint khác nhau. Fit nhận train21000; validation4500; lock chứa hash validation; test4500 là reused test. Config một candidate seed42/n_estimators1/fit_with_cache/memory_saving/cacheCPU/autocast/batch16. V3 coverage nội bộ vẫn tối đa200/384chiều, không đổi representation. Không dùng test chọn resource/hyperparameters và không giảm chiều.

## Kết quả chính

| Model | Test macro F1 | Neutral F1 | Fit s | Wall s | RSS GB | GPU allocated GB | GPU reserved GB |
|---|---:|---:|---:|---:|---:|---:|---:|
| V3 full21000 | 0,572971 | 0,039801 | 7,968 | 80,047 | 2,288 | 6,195 | 9,087 |
| V3_5 full21000 | 0,614017 | 0,135747 | 21,146 | 119,244 | 3,122 | 7,439 | 14,351 |

GB=10^9bytes. Full21K đã khả thi trên cấu hình thực này; đề xuất GPU24GB/A100 trước đây không phải yêu cầu bắt buộc và không phải phép đo. Không tự động cộng VRAM hai T4. Cả hai thấp hơn TabM/BERT về macro/neutralF1; không tiếp tục tune theo test.

## Bảo toàn và tái lập

Artifact nhập mới `artifacts/cloud_runs/tabpfn_full21k_20261024/`; source ZIP `cloud/results/tabpfn_cloud_results_20261024T134959209612Z.zip`. Local E03=10000/E04=1500 giữ nguyên, WARNING RSS local vẫn đúng lịch sử. Snapshot báo cáo trước cloud `reports/history/tabpfn_before_kaggle_20261024/` có hashes. Giữ raw/processed/cache và XGBoost/TabM/BERT bất biến.

Verifier `scripts.verify_kaggle_results` kiểm ZIP path/CRC/coverage/hash/manifest/version/train/split/embedding/IDs/labels/metrics/lock/probe/resources. Publisher reverify trước update và dùng provenance map trong p7_completion.json. Metrics local tính lại khớp cloud delta0, không inference. Evidence protocol dựa code được hash/config/metadata/lock; không có attestation độc lập hoặc log timestamp từng thao tác. Cloud chỉ trả result artifacts, không fitted weights.

Các generator finish_benchmark/final_completion khi cloud active sẽ dùng publisher để tránh ghi lại bảng subsample. Không chạy training runner vào thư mục đã khóa. Bất kỳ thí nghiệm mới nào cần namespace/output riêng, policy trước test và authorization compute tương ứng; cloud nghiệm thu này không cho phép tự chạy job mới.

Giới hạn: laptop-only/noisy star proxy; test reuse, một seed/hardware khác nhau; SemEval–Amazon shift thuộc ABSA, human gold dự kiến nhỏ/chưa có; không production/model tiếng Việt. Toàn dự án P8–P13 còn PENDING. Giữ token trong secrets, không lưu vào artifact/config/log hoặc Git.
