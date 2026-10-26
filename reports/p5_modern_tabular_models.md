> Bằng chứng benchmark **local lịch sử**. Bảng chính hiện hành dùng TabPFN full21000 Kaggle đã verified tại `reports/tabpfn_kaggle_full21k_verification.md`; score/local resource dưới đây giữ nguyên.

# P5 — So sánh các mô hình bảng

Trạng thái: PASS về thực thi/metrics; LIMITED về dữ liệu TabPFN, WARNING về RSS E03. Không phải tất cả mô hình dùng full train. Các baseline E00/E01/E02 được reuse, không retrain hoặc predict test lại.

| model | train_samples | data_regime | representation | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 | runtime_seconds | peak_gpu_allocated_bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 21000 | FULL | N/A | 0.259445 | 0.637111 | 0.495886 | 0.333333 | 0.000000 | 0.000000 | 0.778336 | 0.082639 | 0 |
| E01_xgboost_embedding | 21000 | FULL | frozen MiniLM384 | 0.667752 | 0.799333 | 0.812327 | 0.687805 | 0.794650 | 0.321138 | 0.887468 | 211.907646 | 0 |
| E02_tabm_embedding | 21000 | FULL | frozen MiniLM384 | 0.689086 | 0.818444 | 0.832269 | 0.712587 | 0.828638 | 0.336673 | 0.901946 | 22.647173 | 226633216 |
| E03_tabpfn_v3_embedding | 10000 | SUBSAMPLED | frozen MiniLM384 | 0.562544 | 0.821111 | 0.785736 | 0.591434 | 0.777241 | 0.015075 | 0.895315 | 29.421082 | 6113728000 |
| E04_tabpfn_v35_embedding | 1500 | SUBSAMPLED | frozen MiniLM384 | 0.570952 | 0.823111 | 0.790340 | 0.592344 | 0.782144 | 0.032710 | 0.898000 | 29.682320 | 3415636480 |

Follow-up TabPFN full21000 trên cloud: PENDING, chưa upload/thuê GPU/chạy job. Xem `docs/TABPFN_CLOUD_PLAN.md`; giữ kết quả local, output cloud riêng và công bố test reuse. Không rerun baseline/BERT chỉ để chuyển TabPFN lên cloud.

Selection dựa trên validation macro F1; cấu hình/checkpoint được khóa trước test. Artifact, prediction review_id, per-class precision/recall/F1 và confusion matrix nằm trong `reports/semantic_20261024/`, E03 dưới `attempts/resource01`. Các independent_validation.json đã tính lại metrics và kiểm tra thứ tự ID. Token không được lưu.

TabPFN-3 dùng10000 mẫu, TabPFN-3.5 dùng1500 mẫu phân tầng seed42; cùng embedding384, không PCA/SVD. Quyết định theo đo train-only, không dựa trên test. Xem hai `p5_e0*_resource_assessment.md` và JSON thô. V3 nhận384 chiều nhưng default n_estimators1 chỉ phủ tối đa200 chiều bên trong model theo cảnh báo thư viện; không được diễn giải là so sánh classifier hoàn toàn kiểm soát. Không sửa sau khi xem test.

WARNING: E03 RSS thực6482808832byte vượt trần cấu hình6GB; phép đo riêng10K là5816950784byte nên không dự báo đầy đủ overhead runner/serialization/reload. Bộ monitor lúc E03 chỉ ghi nhận, chưa enforce RSS; đã thêm chặn trước test cho E04. Không chạy lại test E03 để che giới hạn. E03 không OOM; không khẳng định full21K không thể chạy ở mọi cấu hình/máy. Guard mới có thể từ chối retry10K nếu RSS vượt6GB ở máy/lần chạy khác; cần đo lại train-only và suffix mới, không mở lại test đã khóa.

Hai version/checkpoint phân biệt thực qua API đã kiểm tra tại `tabpfn_version_verification.json`. Chi phí TabPFN là pretrained foundation model + fit/in-context inference, không phải huấn luyện từ đầu như TabM/XGBoost.

Chỉ review laptop tiếng Anh. Các chỉ số đo dự đoán nhãn đại diện suy từ Amazon star rating (rating-derived sentiment proxy), có nhiễu; không phải độ chính xác so với human sentiment gold. Neutral8,77%; một seed42/search nhỏ; test đã dùng ở LEGACY nên không hoàn toàn unseen của toàn dự án. SemEval-to-Amazon platform/style shift trong laptop là giới hạn của phần ABSA tương lai, ngoài benchmark chỉ-Amazon này; bộ gold thủ công dự kiến nhỏ, hiện chưa có. Human-gold evaluation remains future work. Không triển khai ABSA hoặc mô hình tiếng Việt trong tác vụ này.
