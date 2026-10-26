# Kế hoạch dự án — cảm xúc và khía cạnh trong review laptop

Cập nhật 2026-10-26. Đọc [PLAN_AI](PLAN_AI.md) cho ID/DONE_WHEN, [AGENTS](AGENTS.md) cho ràng buộc và [báo cáo benchmark](reports/model_stack_refactor_completion.md) cho bằng chứng P0–P7; [P8](reports/p8_aspect_extraction.md) cho ATE, [P9 canonical](reports/p9_exp01_deberta_20261026_v2/report.md) cho ASC/joint ABSA. Kế hoạch đầy đủ trước dọn dẹp nằm trong [lịch sử](docs/archive/20261024_before_cleanup/PLAN_HUMAN.md), không phải danh sách lệnh chạy tiếp.

## Mục tiêu và cách đánh giá

Dự án6tuần/một người, laptop-only tiếng Anh; ưu tiên dữ liệu/EDA50%, mô hình40%, app10%. Dữ liệu Amazon2023 nối metadata; mục tiêu30K khi hợp lệ, không hạ chất lượng để đủ số lượng. SemEval laptop dành ABSA; gold300–500 review phải do người gán/xác minh và độc lập training. Tiếng Việt/PhoBERT là mở rộng tương lai.

Nhãn cố định negative/neutral/positive. Chọn model bằng validation macro F1; báo cáo neutral F1, balanced accuracy, accuracy, weighted F1, per-class precision/recall/F1, confusion matrix và compute. Proxy từ sao không phải human sentiment gold.

Dataset30000 đã hoàn tất; split21000/4500/4500 seed42 giữ nguyên. Không acquisition/cleaning/resplit/regenerate embeddings hoặc retrain baseline không có lỗi thực tế. Model hiện hành: majority sanity, XGBoost/TabM/TabPFN V3/V3_5 với frozen MiniLM384, BERT fine-tune canonical title+body. TF-IDF/LR/SVM/DT và BERT body-only là lịch sử.

# 3. CHẶNG 0 — Môi trường

- [x] Python/dependencies/CUDA/config/seed và phiên bản TabPFN explicit đã kiểm.

# 4. CHẶNG 1 — Nguồn và phạm vi dữ liệu

- [x] Reuse raw, metadata, schema và QA laptop; không tải lại. SemEval license/source vẫn NOT_VERIFIED theo ngoại lệ giáo dục đã ghi; QA sản phẩm không phải gold sentiment.

# 5. CHẶNG 2 — Làm sạch và nhãn

- [x] Dataset30K, mapping sao/proxy, duplicates/missingness/brand diversity có bằng chứng. Gold và các độ chính xác do người kiểm chưa có thì không tự suy ra.

# 6. CHẶNG 3 — EDA và readiness

- [x] Reuse EDA; đã bổ sung độ dài/truncation/neutral/resource risks. Không chạy lại phân tích chỉ để làm mới số liệu.

P3-REFINE-01 ngày2026-10-26 tinh gọn bản trình bày thành [EDA trọng tâm](reports/p3_refinement_20261026/report.md): 8bảng core/3hình, appendix và liên hệ P4/P6/P7/P8/P9; tách original observations với later confirmation. Các bảng/hình/report gốc, dữ liệu và kết quả modeling giữ nguyên; không mở pha mới.

# 7. CHẶNG 4 — Split và representation

- [x] Giữ split21K/4,5K/4,5K; canonical title+body, frozen embeddings384 đầy đủ30K và token BERT riêng; cache/hash/row alignment đã kiểm.

# 8. CHẶNG 5 — Benchmark frozen embeddings

- [x] Majority/XGBoost/TabM full21000 đã hoàn tất, reuse kết quả đã khóa.
- [x] TabPFN local LIMITED: V3 dùng10000, V3_5 dùng1500 mẫu phân tầng seed42. E03 RSS6,48GB vượt trần6GB; V3 n_estimators1 phủ tối đa200/384 chiều nội bộ. Cảnh báo được giữ trong báo cáo.
- [x] Chuẩn bị bundle Kaggle private local: `cloud/kaggle_tabpfn_full21k/`; runner/notebook/hash/alignment đã xác minh; cloud nay đã chạy và verified riêng.
- [x] Cloud full21000: người dùng đã chạy cả V3/V3_5 trên Kaggle Tesla T4; import và verify hash/ID/labels/metrics/lock PASS. Bảng chính thay hai dòng subsample, lịch sử giữ nguyên. Chi phí tiền chưa đo.

Kaggle là lựa chọn thử miễn phí; Hugging Face Jobs/Modal cho phép chủ động compute có phí. Hai cấu hình đã chạy được trên Tesla T4/RAM khoảng33,66GB; không suy diễn cần A100 hoặc cộng VRAM haiGPU. RSS/GPU peaks cụ thể ở báo cáo xác minh. [Kế hoạch cloud](docs/TABPFN_CLOUD_PLAN.md) quy định cổng và giới hạn; không hứa F1 tăng khi dùng đủ dữ liệu.

# 9. CHẶNG 6 — Transformer end-to-end

- [x] BERT canonical full21000, hai loss từ cùng pretrained source; chọn unweighted epoch3 bằng validation macro F1. Test macro0,755382/neutral0,436129; reload/metrics/alignment PASS. Không reuse score BERT body-only.

# 10. CHẶNG 7 — Unified evaluation

- [x] Bảng local đủ6model, lỗi/compute/proxy limits. BERT best theo validation; TabM best frozen local (test macro0,689086/neutral0,336673). Bằng chứng cuối249tests PASS/53legacy hashes nguyên.
- [x] Cloud verified: bảng chính đủ6model full21000; lịch sử local có snapshot/hash. BERT vẫn best, TabM best frozen;291tests PASS.
- [x] Bổ sung chẩn đoán sáu model hiện hành và bằng chứng weighted/unweighted/paired validation; chỉ dùng saved predictions/history. Xem reports/p7_error_cause_analysis.md.
- [x] Chuẩn bị phiếu đọc mù360review (300mẫu đại diện test+60ca khó); có validator/evaluator, không điền nhãn người.
- [x] 360 review đã human-reviewed, integrity/source mapping PASS; hoàn tất proxy–human, rating, ambiguity và sáu model gồm TabPFN cloud. Agreement292/360, disagreement68/360; SRS31/300 và enriched37/60 tách biệt, không suy rộng toàn30K. Có attribution A–E; causal fraction của imbalance chưa xác định. Independent P10 gold vẫn riêng và PENDING. Bằng chứng: `reports/p7_human_audit_results.json` và `reports/p7_error_cause_analysis.md`.

**P7: DONE**, đã khóa trước P8. Kiểm nghiệm thu P0–P7: `reports/p0_p7_acceptance.json`. P8 triển khai riêng bên dưới, không retrain sentiment hoặc thay benchmark/dataset/splits/weights P0–P7.

**Benchmark hiện hành local+Kaggle: đủ6model full21000, verified.** Local TabPFN subsample vẫn LIMITED trong lịch sử; toàn dự án ABSA/gold/app chưa hoàn tất. Test cũ đã được xem, vì vậy experiment mới phải cố định thiết kế bằng train/validation trước test và công bố reuse. Không dùng test errors để quay lại tune.

## Phần dài hạn ngoài tác vụ hiện tại

Chặng8 và9 đã hoàn tất theo hai yêu cầu riêng ngày2026-10-26; các chặng10–13 giữ tiêu chí chưa hoàn tất. SemEval ABSA không đồng nghĩa hoàn tất independent Amazon gold/domain shift/app.

# 11. CHẶNG 8 — ABSA: khía cạnh Term Extraction

## Mục tiêu

Extract khía cạnh cụ thể trong laptop review.

Ví dụ:

`The screen is excellent but battery life is poor.`

→ `screen`, `battery life`

## Công việc

- [x] Hiểu gán nhãn SemEval laptop.
- [x] Chuyển đổi sang gắn thẻ BIO.
- [x] Xác thực căn chỉnh khía cạnh span/token.
- [x] Tinh chỉnh phân loại BERT token.
- [x] Evaluate trên SemEval kiểm thử.

## Số liệu

- [x] Thực thể độ chính xác dự đoán (precision).
- [x] Thực thể độ bao phủ (recall).
- [x] Thực thể F1.

## Có thể giao được

- [x] BIO bộ dữ liệu.
- [x] Trích xuất khía cạnh mô hình.
- [x] Báo cáo đánh giá.

**P8: DONE**, đã khóa trước P9. SemEval laptop nguồn local P1:3045official train/800test; group split2587train/458validation, seed42. WordPiece BIO giữ offsets/polarity;1whitespace adjustment train được giải thích,0lỗi chưa giải thích. Có1duplicate tự nhiên giữa official splits được công bố và giữ nguyên; không text leakage train–validation. BERT ATE5epoch,best4 theo validation entityF1=0,799401; test entity precision0,785714/recall0,824159/F1=0,804478.350tests PASS tại P8,269P0–P7/raw files giữ hash. [Báo cáo P8](reports/p8_aspect_extraction.md), `reports/p8_20261026/acceptance.json`; P9 reuse artifacts, không retrain P8.

---

# 12. CHẶNG 9 — ABSA: khía cạnh cảm xúc Classification

## Mục tiêu

Với mỗi khía cạnh laptop, phân loại Positive / Neutral / Negative.

## Công việc

- [x] Chuẩn bị `(review, aspect, sentiment)` examples từ SemEval.
- [x] Chuẩn hóa về 3 cảm xúc classes.
- [x] Xử lý/loại unsupported conflict nhãn có ghi chú.
- [x] Tinh chỉnh bộ phân loại BERT khía cạnh cảm xúc.
- [x] Đánh giá bộ phân loại
- [x] Nối khía cạnh Extraction → khía cạnh cảm xúc thành end-to-end ABSA.

## Số liệu

- [x] tỷ lệ dự đoán đúng (accuracy).
- [x] độ chính xác dự đoán (precision).
- [x] độ bao phủ (recall).
- [x] Macro F1.
- [x] Ma trận nhầm lẫn.

## Có thể giao được

- [x] khía cạnh cảm xúc mô hình.
- [x] Đường ống ABSA từ đầu đến cuối.
- [x] Báo cáo đánh giá ABSA.

**P9-EXP01 COMPLETE — READY TO CONTINUE TO P10.** DeBERTa-v3-base unweighted epoch5/seed42 trở thành canonical ASC nhờ validation macroF1=0,777467, so với BERT0,714145; không chọn bằng test. Giữ nguyên1999/314/638examples, split, occurrence markers, conflict metadata và evaluation protocol. Native tokenizer có CLS/SEP, zero truncation. Seed43/44 chỉ validation0,767943/0,754664; stability không thay primary42. Official test macroF1/accuracy/weightedF1=0,780433/0,815047/0,813232; joint frozen P8 P/R/F1=0,644776/0,677116/0,660550, extraction counts giữ nguyên.380tests PASS,381files P0–P8/baseline P9 giữ checksum; BERT previous canonical cùng source snapshot11files vẫn giữ. [Báo cáo canonical](reports/p9_exp01_deberta_20261026_v2/report.md), [nghiệm thu](reports/p9_exp01_deberta_20261026_v2/acceptance.json), selector `configs/p9_canonical.yaml`. Những attempts lỗi tokenizer/resume và chi phí được công bố; resume DeBERTa hiện không hỗ trợ, inference/reload PASS. SemEval–Amazon style shift/gold độc lập vẫn PENDING; không retrain P8/pseudo labels hoặc triển khai P10.

---

# 13. CHẶNG 10 — thủ công gán nhãn và Amazon laptop bộ kiểm thử gold

## Mục tiêu

Kiểm tra mô hình tập huấn luyện trên SemEval laptop có hoạt động tốt trên Amazon laptop review thực tế hay không, đồng thời đánh giá nhiễu của rating-derived nhãn.

## Quy mô

**300–500 Amazon laptop review**.

## Lấy mẫu

- [ ] Cân đối theo rating.
- [ ] Cân đối theo review length.
- [ ] Cân đối theo nhiều laptop/product/brand nếu có.
- [ ] Bao gồm mixed-cảm xúc và difficult cases.

## gán nhãn

- [ ] con người tổng thể cảm xúc.
- [ ] Điều khoản khía cạnh.
- [ ] khía cạnh cảm xúc.
- [ ] Lưu ý cho những trường hợp mơ hồ.

## Phân tích

- [ ] cảm xúc có nguồn gốc từ xếp hạng so với con người cảm xúc.
- [ ] Tỷ lệ Agreement/disagreement.
- [ ] Overall cảm xúc các mô hình trên bộ kiểm thử gold.
- [ ] SemEval-trained ABSA trên Amazon laptop bộ kiểm thử gold.
- [ ] Phân tích **bộ dữ liệu shift SemEval → Amazon trong cùng laptop phạm vi**.

## Có thể giao được

- [ ] `data/manual/amazon_laptop_gold_test.csv`
- [ ] Báo cáo bộ kiểm thử gold.
- [ ] Báo cáo nhiễu nhãn.
- [ ] SemEval→Đánh giá chuyển giao của Amazon.

---

# 14. CHẶNG 11 — Ứng dụng Streamlit

## review đơn

- [ ] Nhập laptop review.
- [ ] Dự đoán tổng thể cảm xúc.
- [ ] Hiển thị độ tin cậy nếu mô hình hỗ trợ.
- [ ] Trích xuất các khía cạnh
- [ ] Predict cảm xúc từng khía cạnh.

## lô review

- [ ] Tải lên CSV.
- [ ] lô suy luận.
- [ ] % Tích cực / Trung tính / Tiêu cực.
- [ ] Tần số đề cập đến khía cạnh.
- [ ] Phân phối cảm xúc theo khía cạnh.
- [ ] Các khía cạnh positive / negative laptop hàng đầu.

## Có thể giao được

- [ ] Ứng dụng Streamlit.
- [ ] Chế độ đơn review.
- [ ] Chế độ lô-review.
- [ ] Bảng điều khiển phân tích cơ bản.

---

# 15. CHẶNG 12 — Chuẩn bị mở rộng tiếng Việt

## Mục tiêu

phạm vi vẫn là laptop nhưng có thể thay tiếng Anh bằng tiếng Việt sau này.

## Công việc

- [ ] Tách tiền xử lý theo ngôn ngữ.
- [ ] Không hard-code BERT trong UI/business logic.
- [ ] Tạo mô hình registry.
- [ ] `en → BERT`.
- [ ] Dự trữ `vi → PhoBERT`.
- [ ] Chuẩn hóa suy luận output.
- [ ] Tạo interface cho tiếng Việt preprocessing.

## Có thể giao được

- [ ] Giao diện suy luận không phụ thuộc vào ngôn ngữ.
- [ ] Đăng ký mô hình.
- [ ] Điểm mở rộng Vietnamese/PhoBERT.

---

# 16. CHẶNG 13 — Tổng hợp và hoàn thiện

## Công việc

- [ ] Hoàn thiện EDA/insight.
- [ ] Hoàn thiện đánh giá so sánh majority/XGBoost/TabM/TabPFN V3/V3_5/BERT canonical.
- [ ] Hoàn thiện phân tích lỗi.
- [ ] Hoàn thiện mất cân bằng lớp analysis.
- [ ] Hoàn thiện nhãn-nhiễu analysis.
- [ ] Hoàn thiện ABSA evaluation.
- [ ] Hoàn thiện SemEval→Amazon laptop transfer evaluation.
- [ ] Hoàn thiện Streamlit.
- [ ] Hoàn thiện README/hướng dẫn chạy.
- [ ] Kiểm tra reproducibility.
- [ ] Viết limitation.
- [ ] Viết future work.

## Limitation bắt buộc phải ghi rõ

- [ ] Project chỉ đánh giá phạm vi laptop review.
- [ ] Không kết luận mô hình generalize sang phone/headphone/tech gadgets khác.
- [ ] cảm xúc bắt nguồn từ xếp hạng có nhiễu nhãn.
- [ ] SemEval và Amazon có thể có dataset/style shift dù cùng phạm vi laptop.

---

