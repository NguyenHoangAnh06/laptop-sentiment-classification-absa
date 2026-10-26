> Bằng chứng benchmark **local lịch sử**. Bảng chính hiện hành dùng TabPFN full21000 Kaggle đã verified tại `reports/tabpfn_kaggle_full21k_verification.md`; score/local resource dưới đây giữ nguyên.

# E04_tabpfn_v35_embedding

| model | train_samples | data_regime | representation | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 | runtime_seconds | peak_gpu_allocated_bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E04_tabpfn_v35_embedding | 1500 | SUBSAMPLED | frozen MiniLM384 | 0.570952 | 0.823111 | 0.790340 | 0.592344 | 0.782144 | 0.032710 | 0.898000 | 29.682320 | 3415636480 |

Trạng thái LIMITED/SUBSAMPLED; experiment kỹ thuật PASS. Chi tiết config/version/seed/provenance, predictions, full metrics, confusion matrix, selection lock và resource usage trong thư mục report experiment. Xem báo cáo P5 chung và resource assessment về giới hạn, đặc biệt RSS E03 và feature coverage V3. Không test tuning.

Follow-up TabPFN full21000 trên cloud: PENDING, chưa upload/thuê GPU/chạy job. Xem `docs/TABPFN_CLOUD_PLAN.md`; giữ kết quả local, output cloud riêng và công bố test reuse. Không rerun baseline/BERT chỉ để chuyển TabPFN lên cloud.

Chỉ review laptop tiếng Anh. Các chỉ số đo dự đoán nhãn đại diện suy từ Amazon star rating (rating-derived sentiment proxy), có nhiễu; không phải độ chính xác so với human sentiment gold. Neutral8,77%; một seed42/search nhỏ; test đã dùng ở LEGACY nên không hoàn toàn unseen của toàn dự án. SemEval-to-Amazon platform/style shift trong laptop là giới hạn của phần ABSA tương lai, ngoài benchmark chỉ-Amazon này; bộ gold thủ công dự kiến nhỏ, hiện chưa có. Human-gold evaluation remains future work. Không triển khai ABSA hoặc mô hình tiếng Việt trong tác vụ này.
