# P7 — Đánh giá thống nhất

PASS: đủ6 mô hình, P5 TabPFN LIMITED/SUBSAMPLED; E03 có WARNING RSS. Đánh giá proxy-label sau khi khóa tất cả lựa chọn, không dùng phân tích lỗi để tune.

Follow-up TabPFN full21000 trên cloud: PENDING, chưa upload/thuê GPU/chạy job. Xem `docs/TABPFN_CLOUD_PLAN.md`; giữ kết quả local, output cloud riêng và công bố test reuse. Không rerun baseline/BERT chỉ để chuyển TabPFN lên cloud.

| model | train_samples | data_regime | representation | macro_f1 | accuracy | weighted_f1 | balanced_accuracy | negative_f1 | neutral_f1 | positive_f1 | runtime_seconds | peak_gpu_allocated_bytes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 21000 | FULL | N/A | 0.259445 | 0.637111 | 0.495886 | 0.333333 | 0.000000 | 0.000000 | 0.778336 | 0.082639 | 0 |
| E01_xgboost_embedding | 21000 | FULL | frozen MiniLM384 | 0.667752 | 0.799333 | 0.812327 | 0.687805 | 0.794650 | 0.321138 | 0.887468 | 211.907646 | 0 |
| E02_tabm_embedding | 21000 | FULL | frozen MiniLM384 | 0.689086 | 0.818444 | 0.832269 | 0.712587 | 0.828638 | 0.336673 | 0.901946 | 22.647173 | 226633216 |
| E03_tabpfn_v3_embedding | 10000 | SUBSAMPLED | frozen MiniLM384 | 0.562544 | 0.821111 | 0.785736 | 0.591434 | 0.777241 | 0.015075 | 0.895315 | 29.421082 | 6113728000 |
| E04_tabpfn_v35_embedding | 1500 | SUBSAMPLED | frozen MiniLM384 | 0.570952 | 0.823111 | 0.790340 | 0.592344 | 0.782144 | 0.032710 | 0.898000 | 29.682320 | 3415636480 |
| E05_transformer | 21000 | FULL | canonical raw text → BERT | 0.755382 | 0.886667 | 0.886262 | 0.756344 | 0.878571 | 0.436129 | 0.951446 | 2303.734281 | 2301708288 |

Mô hình chọn theo validation macro F1: **E05_transformer**; test macro F1=0.755382, neutral F1=0.436129. Không chọn theo accuracy hoặc chọn lại bằng test.

## Comparison A — Cùng frozen semantic representation

Best frozen theo validation: E02_tabm_embedding. XGBoost/TabM/TabPFN nhận cùng384 chiều frozen MiniLM. TabPFN dùng10000/1500 mẫu, còn XGBoost/TabM dùng21000: quy mô khác và V3 chỉ phủ tối đa200 chiều nội bộ với n_estimators1. Do đó bảng mô tả các cấu hình đã đo, không chứng minh thứ hạng architecture khi cùng số mẫu/hyperparameter budget. Macro/neutral F1 quan trọng hơn accuracy; TabPFN ở cấu hình này hầu như không dự đoán neutral.

## Comparison B — Frozen representation và NLP end-to-end

Đối chiếu best frozen với BERT fine-tune canonical text. Cả representation, context256/512 và training paradigm khác nhau; không diễn giải là so sánh architecture thuần túy. Không kiểm định nhiều seed hoặc khẳng định ý nghĩa thống kê.

## Computational Cost

CSV gốc `p7_unified_results.csv` có RSS, latency và artifact bytes, kèm artifact_file_bytes_actual tính lại từ tệp thực gồm metadata. Runtime là tổng experiment/search/reload/test được monitor, không đồng nhất với thời gian fit đơn lẻ. Fit-only được đo riêng trong resource assessment TabPFN; fit-only tách biệt cho campaign BERT/TabM/XGBoost NOT_MEASURED ở runner hiện tại. Epoch time BERT gồm validation. Encoder frozen dùng chung: train128 mẫu đo0.147678s sau load/warmup; không có phép đo thời gian toàn bộ30K đáng tin để phân bổ cho từng classifier (NOT_MEASURED). BERT có tokenizer riêng; thời gian tokenization toàn30K NOT_MEASURED. Không cộng tokenization vào training một cách giả định.

XGBoost học cây trên CPU2threads; TabM học neural parameters bằng GPU, retrain cần optimizer/epochs. TabPFN sử dụng pretrained weights và ngữ cảnh train; fit_with_cache tạo cache KV trên CPU, suy luận dựa trên ngữ cảnh, không gradient-train foundation weights. Artifact joblib chứa fitted state/cache; số byte checkpoint và chi phí tạo cache khác artifact nhỏ của majority/XGBoost. BERT cập nhật toàn backbone, retrain tốn hơn và cần lại optimizer/epochs. GPU không bắt buộc về mặt API nhưng CPU large TabPFN bị guard; các experiment neural đo trên RTX4050Laptop6GB, không so runtime CPU/GPU như cùng thiết bị. GPU allocated/reserved Windows có thể gồm shared memory, không đồng nhất VRAM vật lý.

Artifact classifier không gồm shared encoder MiniLM, tokenizer và cache embeddings; triển khai model frozen vẫn cần encoder. Latency tabular trong CSV chỉ tính predict trên embedding đã có; BERT chỉ tính forward trên token đã có. Cả hai chưa gồm tiền xử lý text/tokenization; không gọi đây là độ trễ end-to-end từ raw text. Sample encoder cost được báo riêng, không dùng để giả định chi phí toàn bộ30K.

## Phân tích lỗi sau benchmark

`p7_error_transitions.csv`: Neutral→Positive/Negative, Negative→Positive, Positive→Negative cho từng model. `p7_error_groups.csv`: số mẫu/lỗi theo short<=10word, long>200word, negation, mixed lexical cues, neutral ambiguous. Nhóm có thể chồng lấn; mẫu số là support từng nhóm. Không tuyên bố cue lexical là human annotation hoặc đánh giá semantic gold.

`p7_error_examples.csv`: mẫu lỗi theo thứ tự nguồn, excerpt đã lọc mẫu liên hệ/số phổ biến, proxy label/prediction/model/category; confidence null vì chưa lưu/xác minh xác suất. human_verified=False. Mixed/ambiguous và star/text mismatch cần người đọc lại: không tự đồng nhất bất đồng với nhãn sao thành lỗi nhãn. Không có manual audit PII đầy đủ; không publish mẫu review tự động. Không tune sau phân tích lỗi.

Đếm các chuyển nhãn của mô hình được chọn:

| Proxy → Prediction | Số mẫu |
|---|---:|
| neutral → positive | 91 |
| neutral → negative | 134 |
| negative → positive | 33 |
| positive → negative | 40 |

| Nhóm mô tả | Support | Bất đồng proxy | Tỷ lệ |
|---|---:|---:|---:|
| short_10_words | 302 | 12 | 0.0397 |
| long_200_words | 451 | 68 | 0.1508 |
| negation_cue | 2710 | 380 | 0.1402 |
| mixed_cues_heuristic | 333 | 70 | 0.2102 |
| ambiguous_requires_human_review | 394 | 225 | 0.5711 |

Nhận xét từ mẫu do Codex đọc, không phải adjudication/human gold: các phàn nàn ngắn về pin hỏng, máy chậm hoặc cấu hình khác mô tả mang proxy neutral nhưng BERT dự đoán negative. Điều này cho thấy không thể đồng nhất sao3 với văn bản trung tính; chưa đủ bằng chứng khẳng định từng nhãn sao sai. Có review dài trộn khen tốc độ với phàn nàn tính năng, hoặc khen laptop trước khi nói thất vọng về tuổi thọ: dự đoán có thể bỏ sót sự chuyển cực và phạm vi phủ định. Cue phủ định cũng xuất hiện trong lời tự giới thiệu không liên quan đánh giá sản phẩm, nên chỉ đếm từ phủ định không giải thích được đúng/sai sentiment. Không thay mô hình sau khi đọc các lỗi này.


Chỉ review laptop tiếng Anh. Các chỉ số đo dự đoán nhãn đại diện suy từ Amazon star rating (rating-derived sentiment proxy), có nhiễu; không phải độ chính xác so với human sentiment gold. Neutral8,77%; một seed42/search nhỏ; test đã dùng ở LEGACY nên không hoàn toàn unseen của toàn dự án. SemEval-to-Amazon platform/style shift trong laptop là giới hạn của phần ABSA tương lai, ngoài benchmark chỉ-Amazon này; bộ gold thủ công dự kiến nhỏ, hiện chưa có. Human-gold evaluation remains future work. Không triển khai ABSA hoặc mô hình tiếng Việt trong tác vụ này.
