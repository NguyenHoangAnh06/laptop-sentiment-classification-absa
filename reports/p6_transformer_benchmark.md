# P6 — Transformer canonical title + body

PASS: fine-tune end-to-end BERT trên đủ21000 mẫu train; không dùng frozen embeddings làm đầu vào. Reuse infrastructure và pretrained weights, không reuse fine-tuned BERT LEGACY hoặc test score cũ.

| model | train_samples | data_regime | representation | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 | runtime_seconds | peak_gpu_allocated_bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E05_transformer | 21000 | FULL | canonical raw text → BERT | 0.755382 | 0.886667 | 0.886262 | 0.756344 | 0.878571 | 0.436129 | 0.951446 | 2303.734281 | 2301708288 |

Follow-up TabPFN full21000 trên cloud: PENDING, chưa upload/thuê GPU/chạy job. Xem `docs/TABPFN_CLOUD_PLAN.md`; giữ kết quả local, output cloud riêng và công bố test reuse. Không rerun baseline/BERT chỉ để chuyển TabPFN lên cloud.

Config đầy đủ: `configs/transformer_benchmark.yaml`; model/tokenizer revision `86b5e0934494bd15c9632b12f734a8a67f723594`, google-bert/bert-base-uncased, canonical tokens max512. AdamW2e-5/weight_decay0.01, linear warmup0.1, batch8/accum4/fp16, seed42, tối đa3epochs/patience1. Hai loss cùng khởi tạo từ pretrained weights; weights nghịch tần số chỉ từ train. Selection chỉ validation macro F1, test một lần sau selection lock và reload parity. Confidence không hiệu chuẩn, không tạo điểm tin cậy.

| Loss | Epoch | Validation macro F1 | Neutral precision | Neutral recall | Neutral F1 | Epoch s |
|---|---:|---:|---:|---:|---:|---:|
| unweighted | 1 | 0.712574 | 0.448430 | 0.253165 | 0.323625 | 335.333 |
| unweighted | 2 | 0.742438 | 0.472789 | 0.351899 | 0.403483 | 338.039 |
| unweighted | 3 | 0.760338 | 0.440758 | 0.470886 | 0.455324 | 337.478 |
| balanced | 1 | 0.740707 | 0.341823 | 0.645570 | 0.446976 | 336.126 |
| balanced | 2 | 0.756596 | 0.372414 | 0.683544 | 0.482143 | 340.987 |
| balanced | 3 | 0.758344 | 0.381329 | 0.610127 | 0.469328 | 556.279 |

Chọn loss `unweighted`. Checkpoint tốt nhất, history/class weights, config, source hash, smoke forward/backward, prediction review_id, full metrics và independent validation nằm trong `reports/semantic_20261024/E05_transformer/`; trọng số ở `artifacts/models/semantic_20261024/E05_transformer/unweighted`.

Chỉ review laptop tiếng Anh. Các chỉ số đo dự đoán nhãn đại diện suy từ Amazon star rating (rating-derived sentiment proxy), có nhiễu; không phải độ chính xác so với human sentiment gold. Neutral8,77%; một seed42/search nhỏ; test đã dùng ở LEGACY nên không hoàn toàn unseen của toàn dự án. SemEval-to-Amazon platform/style shift trong laptop là giới hạn của phần ABSA tương lai, ngoài benchmark chỉ-Amazon này; bộ gold thủ công dự kiến nhỏ, hiện chưa có. Human-gold evaluation remains future work. Không triển khai ABSA hoặc mô hình tiếng Việt trong tác vụ này.
