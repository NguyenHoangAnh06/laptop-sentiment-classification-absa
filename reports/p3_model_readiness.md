# P3 — Model Readiness Analysis

Trạng thái: PASS cho phân tích readiness; khả thi tài nguyên từng model còn WARNING.

Không chạy lại EDA cũ; giữ nguyên 15 bảng/7 hình và các nhận định lịch sử.

Có 30,000 review / 9,080 sản phẩm; nhãn: {'positive': 19110, 'negative': 8259, 'neutral': 2631}.

Neutral chỉ 8,77%; train có 1.842 neutral. Accuracy dễ che lỗi lớp này: chọn bằng macro F1, báo neutral F1 và đối chiếu weighted/unweighted trên validation. Không SMOTE.

Title/body thiếu hoặc trống: {'review_title': 0, 'text': 0}.

| Độ dài canonical text | p50 | p75 | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|
| characters | 256.0 | 543.0 | 1116.0 | 1723.05 | 3696.05 | 17400 |
| words | 48.0 | 101.0 | 207.0 | 318.0 | 679.0 | 3167 |
| bert_wordpiece_including_special_tokens | 61.0 | 127.0 | 262.0 | 403.0 | 863.01 | 4159 |

Tỷ lệ vượt 128/256/512 WordPiece: {'128': 0.2463, '256': 0.10286666666666666, '512': 0.03206666666666667}. Đây là số đếm bằng tokenizer BERT có special tokens; không giả là token count chính xác của mọi encoder.

Ước lượng dung lượng embeddings (byte, chưa gồm metadata): {'384': {'float32': 46080000, 'float16': 23040000}, '768': {'float32': 92160000, 'float16': 46080000}}.

| Model | Kết luận về dữ liệu | Ước lượng/rủi ro tài nguyên |
|---|---|---|
| XGBoost | 21K × dense features đủ để thử; không bảo đảm điểm số | Input 384 chiều float32 khoảng 32,26 MB; cây/histogram cần thêm RAM; CPU hist là lựa chọn an toàn ban đầu |
| TabM | 21K với ba lớp đủ để thử | Tham số/activation phụ thuộc width, k, batch; đo VRAM smoke trước full; weighted loss cần validation |
| TabPFN-3 | Dữ liệu số 384 chiều phù hợp API; chưa chứng minh full 21K khả thi | Context attention/cache có thể vượt 6 GB; dùng low_memory/memory_saving chính thức trước khi cân nhắc subsample riêng |
| TabPFN-3.5 | Dữ liệu như V3; checkpoint phải riêng | Không suy từ V3 rằng V3.5 vừa VRAM; đo riêng và giữ 21K cho các model khác |
| Transformer | 21K có thể fine-tune; neutral cần kiểm tra riêng | BERT ~110M tham số: riêng FP32 weights khoảng 440 MB, optimizer/gradient/activation lớn hơn; batch nhỏ + FP16 + accumulation + checkpointing; smoke trước full |

Các chi phí trong bảng là ước lượng cấu trúc, không phải peak RAM/VRAM đo được. Benchmark P4/P5/P6 sẽ quyết định tính khả thi thực tế; không hạ kích thước dataset để làm đẹp kết quả.

Full-data readiness chỉ mô tả, không dùng nhãn test chọn feature, max_length, hyperparameter hoặc model. Chính sách tokenizer mới sẽ cố định trước training; max_length 512 giữ từ P4 train-derived cũ.

Bằng chứng chi tiết: `p3_model_readiness.json`. Giới hạn: chỉ laptop; proxy labels nhiễu; shift SemEval–Amazon trong laptop; gold thủ công nhỏ, hiện chưa có.
