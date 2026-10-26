# PHÂN TÍCH cảm xúc CỦA KHÁCH HÀNG CHO laptop review — KẾ HOẠCH DỰ ÁN

Trạng thái khảo sát đầy đủ mới nhất (2026-10-08): Khảo sát điện tử đầy đủ chỉ dành cho laptop DONE, thoát 0. 43,886,944 review được quét; 408,740 khớp; Đã lưu 408,480 review hợp lệ; Các sản phẩm 28,161 có review hợp lệ. Cả phạm vi phủ sóng của EOF/source đều đúng; Tính nhất quán của checksums/output PASS; Các bài kiểm tra tính khả thi của 53 đã được thông qua. Bằng chứng: `reports/p1_full_laptop_survey.md` và `reports/tables/electronics_full_laptop_30k_verification.json`. 30K có tiềm năng số lượng lớn, KHÔNG phải là năng suất tiếng Anh sạch được đo lường. P1 chưa hoàn thiện: QA bộ lọc con người và SemEval train/test đang chờ gốc. Không có P2/training được ủy quyền. Các trình chặn approval/source-coverage trước đó dưới đây chỉ mang tính lịch sử.

## 1. Tổng quan

**Tên dự án:** Customer cảm xúc & khía cạnh Analysis for laptop review **Loại dự án:** Personal dữ liệu Science Project **Thời gian:** 6 tuần **Quy mô:** 1 người **Ngôn ngữ ban đầu:** tiếng Anh **Mở rộng tương lai:** tiếng Việt + PhoBERT **Tỷ trọng:** dữ liệu 50% — xây dựng mô hình 40% — Application 10%

### Phạm vi

Project chỉ tập trung vào **laptop review**. Các kết luận về cảm xúc, khía cạnh và hiệu năng mô hình chỉ được áp dụng trong phạm vi laptop; phone, headphone, smartwatch và các tech thiết bị khác nằm ngoài phạm vi hiện tại.

### Mục tiêu chính

- Phân loại overall cảm xúc thành 3 lớp: Positive / Neutral / Negative.
- Phân tích cảm xúc theo từng khía cạnh của laptop.
- Thực hiện dữ liệu chất lượng + EDA sâu và tìm insight.
- So sánh hồi quy logistic, SVM, Cây quyết định và BERT.
- Phân tích mất cân bằng lớp, nhiễu nhãn và lỗi mô hình.
- Xây dựng ABSA gồm khía cạnh Term Extraction + khía cạnh cảm xúc Classification.
- Xây dựng Streamlit app đơn giản cho single review và lô review.
- Thiết kế để có thể thêm tiếng Việt + PhoBERT sau này mà không thay đổi toàn bộ pipeline.

---

# 2. Quy ước trạng thái

- [ ] Chưa hoàn thành
- [x] Đã hoàn thành

Khi hoàn thành công việc, đổi `[ ]` thành `[x]`.

---

# 3. CHẶNG 0 — Khởi tạo dự án

## Mục tiêu

Tạo project có thể tái lập và khóa phạm vi laptop review.

## Công việc

- [x] Tạo Git repository.
- [x] Tạo Python environment.
- [x] Tạo `requirements.txt` hoặc `pyproject.toml`.
- [x] Tạo cấu trúc thư mục.
- [x] Viết README mô tả bài toán laptop cảm xúc + ABSA.
- [x] Chốt nhãn Positive / Neutral / Negative.
- [x] Chốt mô hình: Logistic Regression, Linear SVM, Decision Tree, BERT.
- [x] Chốt Macro F1 là thước đo chọn mô hình chính.
- [x] Chốt Amazon laptop review cho overall sentiment/EDA.
- [x] Chốt SemEval-2014 laptop cho ABSA.
- [x] Thiết kế language/model registry để thêm PhoBERT sau này.

## Có thể giao được

- [x] Kho lưu trữ.
- [x] README ban đầu.
- [x] Cấu trúc nguồn.
- [x] Cấu hình chung.

---

Xác minh P0: `reports/p0_initialization.md` (2026-10-08): cài đặt môi trường mới, kiểm tra pip, 9 vượt qua các bài kiểm tra. Cơ quan đăng ký chỉ cung cấp metadata/routing; chưa có các mô hình được đào tạo nào.

# 4. CHẶNG 1 — Thu thập và hiểu dữ liệu laptop

## Mục tiêu

Có hai nguồn dữ liệu cùng phạm vi laptop và hiểu rõ lược đồ trước khi cleaning/modeling.

## bộ dữ liệu A — Amazon laptop review

Use for:
- Tổng thể cảm xúc.
- EDA và cái nhìn sâu sắc về kinh doanh.
- Nghiên cứu nhãn-nhiễu.
- bộ kiểm thử gold thực tế cho overall cảm xúc và ABSA.

Mục tiêu hiện hành: **khoảng 30.000 sạch tiếng Anh laptop review**, thay 50.000 theo yêu cầu ngày 2026-10-08. Đây là mục tiêu mong muốn; nếu chỉ có 15.000–25.000 review chất lượng cao, đánh giá phân bố nhãn và đa dạng sản phẩm rồi báo cáo quy mô phù hợp, không hạ chất lượng hoặc trộn thiết bị để đạt quota. Dữ liệu ABSA cần khía cạnh-level nhãn riêng; không yêu cầu gán nhãn toàn bộ 30.000 review.

## bộ dữ liệu B — SemEval-2014 laptop review

Use for:
- Trích xuất thuật ngữ khía cạnh.
- Phân loại khía cạnh cảm xúc.
- đánh giá so sánh ABSA trong phạm vi laptop.

## Công việc

- [x] Tải/access Amazon review 2023.
- [x] Tải/access Amazon sản phẩm siêu dữ liệu tương ứng.
- [x] Join review với siêu dữ liệu qua sản phẩm identifier phù hợp.
- [x] Xác định rule lọc đúng sản phẩm laptop.
- [ ] Kiểm tra mẫu thủ công để loại phụ kiện không phải laptop nếu bị lẫn.
- [ ] Tải SemEval-2014 laptop review.
- [x] Kiểm tra lược đồ Amazon review.
- [x] Kiểm tra lược đồ Amazon siêu dữ liệu.
- [x] Kiểm tra schema/annotation SemEval.
- [x] Xác định các cột cần dùng.
- [x] Tạo `data_dictionary.md`.
- [x] Kiểm tra số review laptop và số sản phẩm laptop: 408.480 valid review / 28.161 sản phẩm có valid review; toàn bộ survey.
- [x] Kiểm tra rating phân bố: đủ 1–5, xem `reports/p1_full_laptop_survey.md`.
- [x] Xác định lấy mẫu strategy; mục tiêu hiện hành ~30k review (thiết kế ban đầu ~50k).
- [x] Lưu raw dữ liệu không chỉnh sửa.

## Có thể giao được

- [x] `data/raw/amazon/` (tổng kiểm tra metadata/reviews, đầy đủ và đã xác minh EOF).
- [ ] `data/raw/semeval/`
- [x] `data_dictionary.md`
- [x] laptop filtering rule (chưa được người xác thực).
- [x] bộ dữ liệu overview báo cáo (phạm vi nguồn prefixes).
- [x] Chiến lược lấy mẫu.

---


Bằng chứng P1: `reports/p1_data_acquisition.md`. Kiểm tra Acquisition/schema chỉ đề cập đến tiền tố nguồn bị chặn và bản dùng thử SemEval. P1 KHÔNG phải COMPLETE: Bộ lọc QA của con người, vùng phủ sóng nhóm laptop đầy đủ và SemEval train/test ban đầu là đang chờ.

BLOCKED: chỉ ứng cử viên 17 laptop review được liên kết trong tiền tố; Truy cập SemEval train/test và con người QA đang chờ. NEXT_ACTION: mở rộng việc mua lại được ủy quyền, lấy các tập đã chia, review bản gốc chính thức của bộ lọc hàng 100 QA CSV.

### Refactor và khảo sát khả thi P1 — 2026-10-08

- [x] Audit nguyên nhân join thấp và RAM của quy trình cũ.
- [x] Triển khai siêu dữ liệu-first index, streaming join/output và sampling/QA có giới hạn.
- [x] Khảo sát riêng laptop, Smartphone, Tablet ở Electronics và Cell Phones and Accessories.
- [x] Kiểm tra lược đồ, checksum, lỗi mạng/file, khả năng tái lập và bộ nhớ guards: 60 kiểm thử pass.
- [x] Báo cáo feasibility, thay đổi quy trình và phương án quét lớn chờ phê duyệt.

Đã đo trên subset: **17 laptop / 3 Smartphone / 9 Tablet valid ứng viên review**. phạm vi dự án vẫn laptop. Smartphone/Tablet chỉ là feasibility theo yêu cầu hiện tại. Language/clean size chưa đo, filter chưa con người QA; P1 chưa hoàn tất và chưa chuyển P2. Xem `reports/p1_data_feasibility.md` và `reports/p1_pipeline_changes.md`.

BLOCKED: cần toàn bộ nguồn coverage, con người filter QA, SemEval gốc huấn luyện/kiểm thử và bằng chứng 50k sạch feasibility. NEXT_ACTION: xem xét ngân sách Electronics ~7,79 GB tải và siêu dữ liệu-first scan, chờ cho phép trước thao tác lớn; đồng thời hoàn tất truy cập SemEval và QA do người kiểm tra.

### Mục tiêu 30K và acquisition điều kiện nghiệm thu — trạng thái mới nhất (2026-10-08)

- [x] Mục tiêu hiện hành/config/checklists đổi sang 30.000 sạch tiếng Anh laptop review; không đổi technical ceilings.
- [x] Chạy lại 84 kiểm thử; xác minh checksum 4 Amazon snapshots và tái sử dụng siêu dữ liệu-only prefix report.
- [x] Kiểm tra không có toàn bộ siêu dữ liệu; HEAD-only xác minh 1.312.900.427 compressed bytes.
- [ ] Người dùng phê duyệt riêng toàn bộ siêu dữ liệu download và siêu dữ liệu-only preflight.
- [ ] Sau preflight đạt, báo cáo và xin phép riêng review download; hiện chưa được phép.

BLOCKED: chưa có phê duyệt tải siêu dữ liệu lớn, toàn bộ siêu dữ liệu coverage, con người QA hoặc gốc SemEval các tập đã chia. NEXT_ACTION: phê duyệt siêu dữ liệu ~1,31 GB + siêu dữ liệu-only scan trong ceilings hiện có; dừng trước review. Những ghi chú 50k trong bằng chứng trước đó là lịch sử, không phải mục tiêu hiện hành.

### Hardening P1 — lịch sử kiểm chứng (2026-10-08)

- [x] Chặn toàn bộ review scan khi siêu dữ liệu thiếu EOF/provenance; báo lỗi/limits rõ ràng.
- [x] Xử lý oversized records có giới hạn, giữ siêu dữ liệu review và QA baseline/ambiguity.
- [x] 84 kiểm thử pass; hai probes giữ 17/3/9 review, integrity và dependency/syntax checks đạt.
- [x] HEAD/resources và kế hoạch từng bước ở `reports/p1_full_scan_readiness.md`.
- [ ] Người dùng phê duyệt mới và thực hiện toàn bộ coverage, con người QA, gốc SemEval access.

BLOCKED: chưa có nguồn đầy đủ hoặc bằng chứng sạch English/ABSA feasibility. NEXT_ACTION: phê duyệt siêu dữ liệu download/preflight rồi review download/survey có điều kiện; giữ laptop-only và P1 chưa hoàn tất.

### toàn bộ Electronics siêu dữ liệu — kết quả mới nhất (2026-10-08)

- [x] Thực hiện phê duyệt siêu dữ liệu-only: tải 1,31 GB gzip, SHA256/manifest và GZIP integrity verify.
- [x] Preflight laptop-only EOF: 1.610.012 records, 28.172 các ứng viên, 0 record lỗi; không tăng ceilings.
- [x] Đo peak working set 71,16 MB, index estimate 38,00 MB, scan 212,962 s, budgeted read 6,56 GB.
- [x] Xác minh dấu vân tay Output/QA, ID conservation/unique hàng và tổng kiểm tra Amazon thô 5; Các bài kiểm tra 84 đã vượt qua.
- [ ] con người QA 100 sản phẩm mới, gốc SemEval các tập đã chia và quyết định review download riêng.

BLOCKED: review chưa được phê duyệt; nếu tốc độ giống siêu dữ liệu ~1 MB/s, review tải ~108 phút vượt giới hạn 60 phút hiện tại. NEXT_ACTION: xem `reports/p1_metadata_full_preflight.md`, quyết định reviews/ngân sách; không tự tăng limits hoặc chuyển P2/training. mục tiêu 30K và P1 chưa hoàn tất.

### toàn bộ Electronics review acquisition — trạng thái mới nhất (2026-10-08)

- [x] Phê duyệt download/integrity-only đã thực hiện: 6.474.438.619 byte, SHA256/manifest/size/complete_source verify.
- [x] Transfer 87 phút 53 giây / 1,23 MB/s, trong ceilings 180 phút/6,6 GB; raw/QA cũ giữ nguyên.
- [x] Cập nhật acquisition/feasibility/readiness và `reports/p1_reviews_full_acquisition.md` bằng bằng chứng thật.
- [ ] Phê duyệt riêng streaming join và toàn bộ laptop-only survey; chưa chạy.

BLOCKED: laptop review counts/clean tiếng Anh feasibility và con người QA/SemEval access chưa đủ; survey chưa được phê duyệt. NEXT_ACTION: người dùng quyết định survey sau khi xem acquisition results. Không preflight lại, không P2/training; mục tiêu 30K và P1 chưa hoàn tất.

# 5. CHẶNG 2 — dữ liệu chất lượng, làm sạch và Labeling

## Mục tiêu

Tạo bộ dữ liệu laptop sạch, đáng tin cậy và có nhãn overall cảm xúc.

## Chất lượng dữ liệu

- [ ] Kiểm tra thiếu values.
- [ ] Kiểm tra review rỗng/whitespace-only.
- [ ] Kiểm tra review quá ngắn.
- [ ] Kiểm tra exact duplicates.
- [ ] Kiểm tra repeated review giữa các laptop nếu có.
- [ ] Kiểm tra near-duplicates nếu đáng kể.
- [ ] Kiểm tra HTML/URL/ký tự bất thường.
- [ ] Kiểm tra spam-like review.
- [ ] Kiểm tra review length.
- [ ] Kiểm tra sản phẩm siêu dữ liệu bất thường.
- [ ] Kiểm tra lại false-positive trong bước lọc laptop.

## Ghi nhãn

Nếu Amazon không có cảm xúc nhãn trực tiếp:
- [ ] Xếp hạng 1–2 → Tiêu cực.
- [ ] Xếp hạng 3 → Trung tính.
- [ ] Xếp hạng 4–5 → Tích cực.
- [ ] Kiểm tra phân bố nhãn.
- [ ] Ghi rõ rating-derived nhãn là đại diện nhãn, không phải nhãn chuẩn tuyệt đối.

## nhiễu nhãn

- [ ] Lấy mẫu review để tìm rating-text disagreement.
- [ ] Lưu các case 5 sao nhưng văn bản tiêu cực/mixed.
- [ ] Lưu các case 1–2 sao nhưng văn bản tích cực/trung tính.
- [ ] Chuẩn bị ứng viên set cho thủ công gán nhãn ở Chặng 10.

## Có thể giao được

- [ ] `data/processed/laptop_reviews.parquet`
- [ ] bộ dữ liệu sạch tiếng Anh hướng tới ~30k review; đánh giá quy mô nhỏ hơn theo chất lượng/phân bố nhãn/đa dạng sản phẩm.
- [ ] Báo cáo chất lượng dữ liệu.
- [ ] Báo cáo phân phối nhãn.
- [ ] Mẫu ứng viên nhãn-nhiễu.

---

# 6. CHẶNG 3 — EDA và nhận định cho laptop review

## Mục tiêu

Đây là phần trọng tâm dữ liệu Science của dự án.

## Phân tích tổng quan

- [ ] Số review.
- [ ] Số laptop/product.
- [ ] Phân bố rating.
- [ ] Phân bố cảm xúc.
- [ ] Phân bố chiều dài review.
- [ ] Số review theo product.
- [ ] Temporal analysis nếu có timestamp.

## Phân tích văn bản

- [ ] Tần số từ.
- [ ] N-gram thường xuyên.
- [ ] Terms đặc trưng Positive.
- [ ] Terms đặc trưng Neutral.
- [ ] Terms đặc trưng Negative.
- [ ] Chiều dài review theo sentiment/rating.

## Phân tích siêu dữ liệu

- [ ] Phiếu bầu hữu ích theo sentiment/rating.
- [ ] đã xác minh purchase nếu dữ liệu có.
- [ ] cảm xúc theo laptop/product.
- [ ] Đánh giá theo laptop/product.
- [ ] Phân tích metadata/spec/brand nếu đủ tin cậy và hữu ích.

## Phân tích chất lượng dữ liệu

- [ ] Tỷ lệ trùng lặp.
- [ ] Tỷ lệ thiếu.
- [ ] Tỷ lệ review ngắn.
- [ ] Mất cân bằng giai cấp.
- [ ] Ví dụ nhãn-nhiễu.

## Cái nhìn sâu sắc dành riêng cho laptop

- [ ] Tìm các nhóm vấn đề khách hàng thường đề cập.
- [ ] Xác định điểm mạnh/yếu nổi bật của laptop từ review.
- [ ] Xác định sản phẩm/brand có pattern cảm xúc khác nhau nếu dữ liệu hỗ trợ.
- [ ] Chuẩn bị giả thuyết về khía cạnh phổ biến: battery, screen, keyboard, hiệu năng, build, price, portability, storage, thermal/noise... nhưng chỉ kết luận khi dữ liệu chứng minh.

## Có thể giao được

- [ ] EDA notebook.
- [ ] Figures/tables.
- [ ] Tóm tắt cái nhìn sâu sắc.
- [ ] Báo cáo phân tích dữ liệu.

---

# 7. CHẶNG 4 — Chuẩn bị dữ liệu cho xây dựng mô hình

## Mục tiêu

Tạo cố định phân chia đáng tin cậy và hạn chế rò rỉ dữ liệu.

## Công việc

- [ ] Chia tập huấn luyện / tập xác thực / kiểm thử, mục tiêu 70/15/15.
- [ ] Phân tầng theo cảm xúc.
- [ ] Kiểm tra trùng lặp rò rỉ dữ liệu.
- [ ] Kiểm tra sản phẩm rò rỉ dữ liệu.
- [ ] Xem xét Group phân chia theo `product_id` / `parent_asin`.
- [ ] Lưu cố định phân chia và ngẫu nhiên hạt giống ngẫu nhiên.
- [ ] Tạo tiền xử lý riêng cho Classical ML.
- [ ] Tạo tiền xử lý riêng cho BERT.
- [ ] khớp mô hình TF-IDF chỉ trên tập huấn luyện.
- [ ] Giữ negation như `not`, `never`, `don't`.
- [ ] Không stemming/stopword removal cho BERT.

## Có thể giao được

- [ ] tập huấn luyện / tập xác thực / kiểm thử.
- [ ] Báo cáo phân chia.
- [ ] Đường ống tiền xử lý cổ điển.
- [ ] Đường ống tiền xử lý BERT.

---

# 8. CHẶNG 5 — Classical Machine Learning

## Đường ống

`Laptop Review → Basic Cleaning → TF-IDF → Classifier`

## Thí nghiệm

- [ ] Lớp đa số mô hình cơ sở.
- [ ] TF-IDF + Hồi quy logistic.
- [ ] TF-IDF + SVM tuyến tính.
- [ ] TF-IDF + Cây quyết định.
- [ ] Dùng lớp weighting khi mất cân bằng đủ lớn và có lý do.

## thước đo bắt buộc

- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision) từng class.
- [ ] độ bao phủ (recall) từng class.
- [ ] F1 từng class.
- [ ] Macro F1.
- [ ] Trọng số F1.
- [ ] Ma trận nhầm lẫn.
- [ ] Thời gian huấn luyện.
- [ ] Thời gian suy luận.
- [ ] Kích thước mô hình.
- [ ] Việc sử dụng RAM.

## Có thể giao được

- [ ] 3 ML cổ điển các mô hình.
- [ ] Bảng đánh giá so sánh thống nhất.
- [ ] Ma trận nhầm lẫn.
- [ ] Kết luận mô hình Classical ML tốt nhất.

---

# 9. CHẶNG 6 — BERT Overall cảm xúc

## Mục tiêu

Fine-tune BERT cho laptop review 3 lớp và so sánh với Classical ML.

## Công việc

- [ ] Chuẩn bị tokenizer/dataset.
- [ ] Chọn max sequence độ dài từ phân bố token thực tế.
- [ ] Tinh chỉnh BERT.
- [ ] Theo dõi train/validation hàm mất mát.
- [ ] Theo dõi Macro F1.
- [ ] Kiểm tra overfitting.
- [ ] Dùng weighted hàm mất mát nếu mất cân bằng đáng kể.
- [ ] Tiết kiệm điểm lưu mô hình tốt nhất.

## Đánh giá

- [ ] Đầy đủ thước đo giống Classical ML.
- [ ] Thời gian huấn luyện.
- [ ] Độ trễ suy luận.
- [ ] Kích thước mô hình.
- [ ] RAM/GPU/VRAM nếu có.
- [ ] BERT so với LR/SVM/DT.
- [ ] Định lượng mức tăng hiệu suất và chi phí tính toán.

## Câu hỏi nghiên cứu chính

**BERT cải thiện Macro F1 bao nhiêu so với TF-IDF + Linear SVM trên laptop review và chi phí tính toán tăng bao nhiêu?**

## Có thể giao được

- [ ] BERT mô hình.
- [ ] ML-vs-BERT đánh giá so sánh.
- [ ] Phân tích Cost/performance.

---

# 10. CHẶNG 7 — phân tích lỗi

## Nhóm lỗi cần kiểm tra

- [ ] Phủ định.
- [ ] Hỗn hợp cảm xúc.
- [ ] Sự mỉa mai.
- [ ] review rất ngắn.
- [ ] review dài.
- [ ] cảm xúc tiềm ẩn.
- [ ] Văn bản đánh giá conflict.
- [ ] Multi-khía cạnh review.
- [ ] Thuật ngữ dành riêng cho laptop.

## So sánh mô hình

- [ ] LR sai loại nào.
- [ ] SVM sai loại nào.
- [ ] DT sai loại nào.
- [ ] BERT sửa được lỗi nào.
- [ ] Lỗi nào tất cả mô hình vẫn thất bại.

## Có thể giao được

- [ ] Báo cáo phân tích lỗi.
- [ ] Các ví dụ có chú thích
- [ ] Kết luận mô hình strengths/weaknesses.

---

# 11. CHẶNG 8 — ABSA: khía cạnh Term Extraction

## Mục tiêu

Extract khía cạnh cụ thể trong laptop review.

Ví dụ:

`The screen is excellent but battery life is poor.`

→ `screen`, `battery life`

## Công việc

- [ ] Hiểu gán nhãn SemEval laptop.
- [ ] Chuyển đổi sang gắn thẻ BIO.
- [ ] Xác thực căn chỉnh khía cạnh span/token.
- [ ] Tinh chỉnh phân loại BERT token.
- [ ] Evaluate trên SemEval kiểm thử.

## Số liệu

- [ ] Thực thể độ chính xác dự đoán (precision).
- [ ] Thực thể độ bao phủ (recall).
- [ ] Thực thể F1.

## Có thể giao được

- [ ] BIO bộ dữ liệu.
- [ ] Trích xuất khía cạnh mô hình.
- [ ] Báo cáo đánh giá.

---

# 12. CHẶNG 9 — ABSA: khía cạnh cảm xúc Classification

## Mục tiêu

Với mỗi khía cạnh laptop, phân loại Positive / Neutral / Negative.

## Công việc

- [ ] Chuẩn bị `(review, aspect, sentiment)` examples từ SemEval.
- [ ] Chuẩn hóa về 3 cảm xúc classes.
- [ ] Xử lý/loại unsupported conflict nhãn có ghi chú.
- [ ] Tinh chỉnh bộ phân loại BERT khía cạnh cảm xúc.
- [ ] Đánh giá bộ phân loại
- [ ] Nối khía cạnh Extraction → khía cạnh cảm xúc thành end-to-end ABSA.

## Số liệu

- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision).
- [ ] độ bao phủ (recall).
- [ ] Macro F1.
- [ ] Ma trận nhầm lẫn.

## Có thể giao được

- [ ] khía cạnh cảm xúc mô hình.
- [ ] Đường ống ABSA từ đầu đến cuối.
- [ ] Báo cáo đánh giá ABSA.

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
- [ ] Hoàn thiện đánh giá so sánh LR/SVM/DT/BERT.
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

# 17. Kế hoạch 6 tuần

| Tuần | Chặng | Kết quả cần đạt |
|---|---|---|
| 1 | 0–1 | Kho lưu trữ + Từ điển laptop thô của Amazon dữ liệu + SemEval + dữ liệu |
| 2 | 2–3 | Làm sạch laptop bộ dữ liệu + EDA + hiểu biết sâu sắc |
| 3 | 4–5 | cố định phân chia + LR/SVM/DT đánh giá so sánh |
| 4 | 6–7 | So sánh BERT + mô hình + phân tích lỗi |
| 5 | 8–10 | ABSA + thủ công Amazon laptop bộ kiểm thử gold |
| 6 | 11–13 | Streamlit + tích hợp + báo cáo cuối cùng |

---

# 18. Định nghĩa xong

Dự án hoàn thành khi:

- [ ] Có bộ dữ liệu laptop sạch tiếng Anh, mục tiêu khoảng 30k review; ghi rõ quy mô thực tế nếu nhỏ hơn.
- [ ] Có EDA và nhận định đủ sâu trong phạm vi laptop.
- [ ] Có tổng thể lớp 3 cảm xúc.
- [ ] Có hồi quy logistic, SVM, Cây quyết định và BERT đánh giá so sánh.
- [ ] Có tỷ lệ dự đoán đúng (accuracy) / độ chính xác dự đoán (precision) / độ bao phủ (recall) / F1 / Macro F1 / F1 có trọng số.
- [ ] Có so sánh training/inference/model-size/resource.
- [ ] Có phân tích mất cân bằng lớp.
- [ ] Có phân tích nhãn-nhiễu.
- [ ] Có phân tích lỗi.
- [ ] Có trích xuất thuật ngữ khía cạnh.
- [ ] Có phân loại khía cạnh cảm xúc.
- [ ] Có 300–500 Amazon laptop review được thủ công gán nhãn.
- [ ] Có đánh giá SemEval laptop → Amazon laptop.
- [ ] Có ứng dụng Streamlit.
- [ ] Có kiến trúc mở rộng Vietnamese/PhoBERT.
- [ ] Có báo cáo cuối cùng và kho lưu trữ có thể tái tạo.
