# PHÂN TÍCH cảm xúc CỦA KHÁCH HÀNG CHO laptop review — KẾ HOẠCH THỰC HIỆN AI

Trạng thái khảo sát đầy đủ mới nhất (2026-10-08): Khảo sát điện tử đầy đủ chỉ dành cho laptop DONE, thoát 0. 43,886,944 review được quét; 408,740 khớp; Đã lưu 408,480 review hợp lệ; Các sản phẩm 28,161 có review hợp lệ. Cả phạm vi phủ sóng của EOF/source đều đúng; Tính nhất quán của checksums/output PASS; Các bài kiểm tra tính khả thi của 53 đã được thông qua. Bằng chứng: `reports/p1_full_laptop_survey.md` và `reports/tables/electronics_full_laptop_30k_verification.json`. 30K có tiềm năng số lượng lớn, KHÔNG phải là năng suất tiếng Anh sạch được đo lường. P1 chưa hoàn thiện: QA bộ lọc con người và SemEval train/test đang chờ gốc. Không có P2/training được ủy quyền. Các trình chặn approval/source-coverage trước đó dưới đây chỉ mang tính lịch sử.

Trạng thái thu nhận mới nhất (2026-10-08): được ủy quyền rõ ràng đầy đủ Điện tử review download/integrity DONE (6,474,438,619 byte, SHA256/manifest/size đã xác minh, 87m53s). Cả hai nguồn thô nén đều tồn tại. Phát trực tuyến khảo sát join/full laptop KHÔNG ĐƯỢC CẤP PHÉP và CHƯA CHẠY. Các trình chặn cấp phép tải xuống trước đó bên dưới đều mang tính lịch sử; P1 vẫn chưa hoàn thiện và số lượng tiếng Anh review sạch vẫn còn NOT_MEASURED. Bằng chứng: `reports/p1_reviews_full_acquisition.md`.

Trạng thái thực thi hiện tại (2026-10-08): được ủy quyền rõ ràng đầy đủ các hàng Điện tử siêu dữ liệu download/preflight DONE: 1,610,012 siêu dữ liệu, các sản phẩm 28,172 ứng viên laptop, EOF/coverage hoàn thành, không có lỗi ghi nào. Tải xuống review KHÔNG ĐƯỢC CẤP PHÉP. Bằng chứng: `reports/p1_metadata_full_preflight.md`. Các tuyên bố metadata-approval/absence trước đó dưới đây chỉ mang tính lịch sử; P1 vẫn chưa hoàn thiện.

Bản cập nhật mục tiêu hiện tại (2026-10-08): **30,000 sạch tiếng Anh laptop review**, đầy khát vọng. Bằng chứng P1 trước đó đề cập đến 50k vẫn còn mang tính lịch sử; dữ liệu đo được không thay đổi. siêu dữ liệu đầy đủ download/preflight yêu cầu phê duyệt rõ ràng mới; Tải xuống review không được tác vụ hiện tại cho phép. Trần tài nguyên, cấu trúc pha và các yêu cầu về ABSA không thay đổi.

> Tối ưu hóa cho trợ lý AI agents/coding. Tuân theo phạm vi, các phần phụ thuộc, ID nhiệm vụ, kết quả đầu ra và tiêu chí hoàn thành. Không mở rộng phạm vi vượt quá laptop trừ khi người dùng thay đổi rõ ràng phạm vi.

---

# 0. HỢP ĐỒNG DỰ ÁN

## PROJECT_ID

`customer-sentiment-laptop-reviews`

## MỤC TIÊU

Xây dựng dự án Phân tích cảm xúc lấy khách hàng làm trung tâm dữ liệu được giới hạn ở **laptop review** với:

1. Phân loại cảm xúc lớp 3 tổng thể.
2. Khám phá thông tin chi tiết chuyên sâu về dữ liệu + EDA + laptop.
3. Điểm chuẩn hồi quy logistic so với SVM tuyến tính so với cây quyết định so với BERT.
4. Trích xuất thuật ngữ khía cạnh cho các khía cạnh laptop.
5. Phân loại khía cạnh cảm xúc.
6. nhãn-nhiễu và phân tích mất cân bằng lớp.
7. thủ công Amazon laptop bộ kiểm thử gold.
8. Ứng dụng Streamlit đơn giản.
9. Kiến trúc đã sẵn sàng cho tiếng Việt + PhoBERT trong khi vẫn giữ laptop phạm vi.

## ranh giới phạm vi

- TRONG phạm vi: laptops/notebooks và văn bản review của chúng.
- NGOÀI phạm vi: điện thoại, tai nghe, máy tính bảng, đồng hồ thông minh, máy ảnh và các miền tiện ích khác.
- Không yêu cầu khái quát hóa nhiều tiện ích.
- Cho phép đánh giá SemEval→Amazon vì cả hai tập dữ liệu vẫn nằm trong laptop phạm vi; mô tả nó như là chuyển dataset/platform/style, không phải khái quát hóa tiện ích chéo phạm vi.

## Ràng buộc cố định

- Ngôn ngữ chính: tiếng Anh.
- Ngôn ngữ tương lai: tiếng Việt.
- nhãn: `positive`, `neutral`, `negative`.
- mục tiêu Amazon sạch bộ dữ liệu: khoảng `30,000` sạch tiếng Anh laptop review (cập nhật người dùng 2026-10-08; thay thế 50,000).
- Đây là mục tiêu mong muốn, không phải hạn ngạch cứng. Đánh giá nhóm 15,000–25,000 chất lượng cao bằng cách sử dụng tính đa dạng của lớp coverage/product và ghi lại kích thước thực tế. Các proxy đánh giá tổng thể không cung cấp ABSA nhãn cấp khía cạnh; không yêu cầu gán nhãn của tất cả 30,000 review.
- Nếu laptop dữ liệu hợp lệ nhỏ hơn, hãy giữ nguyên độ tinh khiết của phạm vi và ghi lại kích thước thực tế; không lấp đầy hạn ngạch bằng cách sử dụng các tiện ích không phải laptop.
- Quy mô đội: 1.
- Thời lượng: 6 tuần.
- Trọng số: dữ liệu 50%, xây dựng mô hình 40%, Ứng dụng 10%.
- ML cổ điển bắt buộc: Hồi quy logistic, SVM tuyến tính, Cây quyết định.
- Transformer bắt buộc: BERT.
- Yêu cầu ABSA: có.
- Ứng dụng: Streamlit, giao diện người dùng đơn giản.
- Không thêm CNN/LSTM/GRU/Word2Vec/FastText trừ khi phạm vi thay đổi.
- Không thêm Spark/Kafka/Airflow trừ khi quy mô thay đổi đáng kể.
- Không coi việc thu thập thông tin theo thời gian thực là một phần của MVP.

## NGUỒN dữ liệu

### Tổng thể cảm xúc / EDA / bộ kiểm thử gold

Amazon review 2023 + sản phẩm Amazon siêu dữ liệu, được lọc thành các sản phẩm laptop.

### ABSA benchmark/training

SemEval-2014 laptop review.

### Đánh giá thủ công

300–500 Amazon laptop review.

## CHÍNH SÁCH LỌC AMAZON laptop

- Kết hợp các bản ghi review với sản phẩm siêu dữ liệu bằng mã nhận dạng sản phẩm thích hợp.
- Lọc các sản phẩm sử dụng các trường metadata/category/title đủ để xác định laptops/notebooks.
- Kiểm tra rõ ràng các kết quả dương tính giả như túi laptop, bộ sạc, chân đế, vỏ bọc, bộ phận thay thế và các phụ kiện khác.
- Ghi lại quy tắc lọc và một mẫu thủ công tập xác thực nhỏ.
- Giữ nguyên dữ liệu không thay đổi.

## CHÍNH SÁCH nhãn

Nếu Amazon cảm xúc nhãn không có sẵn:

```text
rating 1–2 -> negative
rating 3   -> neutral
rating 4–5 -> positive
```

Hãy coi cảm xúc bắt nguồn từ xếp hạng như một đại diện nhãn ồn ào, chưa bao giờ là nhãn chuẩn không thể nghi ngờ.

## CHỈ SỐ LỰA CHỌN mô hình CHÍNH

`Macro F1`

Các chỉ số phụ:
- tỷ lệ dự đoán đúng (accuracy)
- Precision/Recall/F1 mỗi lớp
- Trọng số F1
- Ma trận nhầm lẫn
- thời gian huấn luyện
- Độ trễ suy luận
- Kích thước mô hình
- RAM
- GPU/VRAM nếu có

---

# 1. QUY TẮC TÌNH TRẠNG

```text
- [ ] = NOT DONE
- [x] = DONE
```

Chỉ đánh dấu một nhiệm vụ `[x]` khi tiêu chí `DONE_WHEN` của nó được thỏa mãn.

Nếu bị chặn:

```text
BLOCKED: <reason>
NEXT_ACTION: <action>
```

---

# 2. CẤU TRÚC KHO LƯU TRỮ mục tiêu

```text
customer-sentiment-laptop/
├── README.md
├── requirements.txt
├── configs/
│   ├── data.yaml
│   ├── model.yaml
│   └── language.yaml
├── data/
│   ├── raw/
│   │   ├── amazon/
│   │   └── semeval/
│   ├── interim/
│   ├── processed/
│   └── manual/
├── notebooks/
│   ├── 01_dataset_overview.ipynb
│   ├── 02_data_quality.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_classical_ml.ipynb
│   ├── 05_bert.ipynb
│   └── 06_error_analysis.ipynb
├── src/
│   ├── data/
│   │   ├── loader.py
│   │   ├── laptop_filter.py
│   │   ├── validation.py
│   │   ├── cleaning.py
│   │   ├── labeling.py
│   │   └── split.py
│   ├── preprocessing/
│   │   ├── base.py
│   │   ├── english.py
│   │   └── vietnamese.py
│   ├── sentiment/
│   │   ├── classical/
│   │   └── transformer/
│   ├── absa/
│   │   ├── aspect_extraction/
│   │   └── aspect_sentiment/
│   ├── evaluation/
│   │   ├── metrics.py
│   │   ├── benchmark.py
│   │   └── error_analysis.py
│   ├── models/
│   │   └── registry.py
│   └── inference/
│       └── pipeline.py
├── app/
│   └── streamlit_app.py
├── reports/
│   ├── figures/
│   ├── tables/
│   └── final/
└── tests/
```

---

# 3. GIAI ĐOẠN P0 — KHỞI TẠO DỰ ÁN

## MỤC TIÊU

Tạo bộ khung có thể tái tạo và khóa laptop chỉ dành cho phạm vi.

### Thiết lập kho lưu trữ P0-T01
- [x] Tạo kho lưu trữ Git.
- [x] Tạo `.gitignore`.
- [x] Tạo môi trường Python.
- [x] Tạo tập tin phụ thuộc.

**DONE_WHEN:** Môi trường mới cài đặt các phần phụ thuộc cần thiết mà không gặp lỗi chưa được giải quyết.

### Cấu trúc thư mục P0-T02
- [x] Tạo cấu trúc kho lưu trữ mục tiêu.

**PHỤ THUỘC:** P0-T01 **DONE_WHEN:** Các thư mục cốt lõi tồn tại và trách nhiệm được tách biệt.

### P0-T03 Scope/config
- [x] Cấu hình nhãn.
- [x] Định cấu hình đường dẫn bộ dữ liệu.
- [x] Định cấu hình danh sách mô hình.
- [x] Định cấu hình số liệu.
- [x] Định cấu hình hạt giống ngẫu nhiên ngẫu nhiên.
- [x] Lưu trữ phạm vi=`laptop`.

**DONE_WHEN:** Core phạm vi được định hướng theo cấu hình và không bị trùng lặp trên notebook.

### Khả năng mở rộng ngôn ngữ P0-T04
- [x] Thêm cấu hình ngôn ngữ.
- [x] Bản đồ `en -> BERT`.
- [x] Dự trữ `vi -> PhoBERT`.
- [x] Xác định lược đồ suy luận độc lập với ngôn ngữ.

**DONE_WHEN:** Hỗ trợ tiếng Việt trong tương lai không yêu cầu thay đổi hợp đồng đầu ra ứng dụng.

## GIAI ĐOẠN ĐẦU RA
- [x] Kho lưu trữ được khởi tạo.
- [x] Đã khởi tạo cấu hình.
- [x] Tài liệu laptop chỉ có phạm vi.
- [x] Đã xác định mức độ trừu tượng English/Vietnamese.

---

Xác minh P0: xem `reports/p0_initialization.md` (2026-10-08): cài đặt môi trường mới, kiểm tra pip và 9 vượt qua các bài kiểm tra hợp đồng. Việc mua lại mô hình training/data không nằm trong quá trình hoàn tất này.

# 4. GIAI ĐOẠN P1 — laptop dữ liệu THU NHẬP VÀ HIỂU

## MỤC TIÊU

Mua Amazon laptop dữ liệu và SemEval laptop ABSA dữ liệu, sau đó hiểu các lược đồ trước mọi quá trình xử lý không thể đảo ngược.

### P1-T01 Mua lại Amazon review + siêu dữ liệu
- [x] Download/access Amazon review 2023 review dữ liệu.
- [x] Download/access tương ứng với sản phẩm siêu dữ liệu.
- [x] Bảo quản các tập tin thô không thay đổi.

** ĐẦU RA:** `data/raw/amazon/`

**DONE_WHEN:** Cả hai bản ghi review và siêu dữ liệu đều có thể được tải lại.

### P1-T02 Xây dựng bộ lọc sản phẩm laptop
- [x] Xác định khóa nối giữa review và sản phẩm siêu dữ liệu.
- [x] Tham gia hoặc ánh xạ review tới sản phẩm siêu dữ liệu.
- [x] Xác định quy tắc bao gồm laptop/notebook.
- [x] Xác định quy tắc loại trừ phụ kiện.
- [ ] Kiểm tra thủ công mẫu tập xác thực.

**LOẠI TRỪ KHI ĐƯỢC XÁC ĐỊNH LÀ:** túi, bao đựng, chân đế, bộ sạc, đế cắm, bộ phận thay thế, miếng bảo vệ màn hình hoặc các phụ kiện không phải laptop khác.

**OUTPUT:** quy tắc lọc được ghi lại + `src/data/laptop_filter.py` hoặc tương đương.

**DONE_WHEN:** Mẫu thủ công cho biết nhóm được lọc đại diện cho các sản phẩm laptop có độ chính xác dự đoán (precision) được chấp nhận.

### P1-T03 Thu được SemEval laptop
- [ ] Download/access SemEval-2014 laptop review.
- [x] Giữ nguyên định dạng gán nhãn gốc.

** ĐẦU RA:** `data/raw/semeval/`

### Kiểm tra lược đồ Amazon P1-T04
- [x] Trường văn bản review.
- [x] Trường đánh giá.
- [x] ID sản phẩm/mã định danh gốc.
- [x] Dấu thời gian nếu có.
- [x] Các trường hữu ích nếu có.
- [x] Trường đã xác minh mua hàng nếu có.
- [x] Các trường siêu dữ liệu của sản phẩm hữu ích cho laptop identification/EDA.

### Kiểm tra lược đồ SemEval P1-T05
- [x] Trường Sentence/review.
- [x] khía cạnh terms/spans.
- [x] Phân cực khía cạnh.
- [x] Conflict/other nhãn.
- [x] Chính sách chuẩn hóa lớp 3.

### Từ điển P1-T06 dữ liệu
- [x] Tên trường.
- [x] Kiểu dữ liệu.
- [x] Ý nghĩa.
- [x] Ghi chú thiếu giá trị.
- [x] Mục đích sử dụng.

** ĐẦU RA:** `data_dictionary.md`

### Kiểm tra xếp hạng và kích thước nhóm P1-T07
- [x] Số lượng laptop review đã lọc: 408,740 khớp / 408,480 hợp lệ trong khảo sát Điện tử đầy đủ; không sạch tiếng Anh.
- [x] Đếm sản phẩm laptop: 28,172 ứng viên đầy đủ Điện tử siêu dữ liệu; Bộ lọc con người QA đang chờ.
- [x] Tính toán phân bố sao 1–5: toàn bộ số lượng nhóm hợp lệ trong `reports/p1_full_laptop_survey.md`.
- [ ] Ước tính kích thước bộ dữ liệu sạch có thể đạt được.

### Chiến lược lấy mẫu P1-T08
- [ ] mục tiêu ~30k sạch tiếng Anh laptop review; báo cáo kích thước và chất lượng thực tế nếu nhỏ hơn.
- [ ] Bảo tồn sự đa dạng xếp hạng.
- [ ] Bảo tồn sự đa dạng của sản phẩm.
- [ ] Duy trì sự đa dạng của thương hiệu nếu siêu dữ liệu hỗ trợ nó.
- [x] Lưu trữ ngẫu nhiên hạt giống ngẫu nhiên.
- [x] Không bao gồm các sản phẩm không phải laptop để đạt được số hàng cố định.

**DONE_WHEN:** Việc lấy mẫu có thể được sao chép và chỉ giữ lại laptop.

## GIAI ĐOẠN ĐẦU RA
- [x] Có sẵn Amazon review + siêu dữ liệu thô: nguồn đầy đủ, tổng kiểm tra đã được xác minh, cả hai luồng đều đạt EOF.
- [ ] Bộ lọc laptop được ghi lại và xác thực.
- [ ] SemEval thô có sẵn.
- [x] Từ điển dữ liệu có sẵn.
- [x] Chiến lược lấy mẫu được ghi lại.

---

P1 evidence/status: `reports/p1_data_acquisition.md`, `reports/tables/p1_audit.json`, `data_dictionary.md`. Các mục acquisition/schema đã kiểm tra chỉ đề cập đến tiền tố nguồn giới hạn và bản dùng thử laptop chính thức. P1 KHÔNG phải là COMPLETE: tính khả thi đầy đủ của nhóm laptop coverage/clean-size, bộ lọc QA SemEval train/test, và con người ban đầu vẫn mở.

BLOCKED: tiền tố nguồn độc lập chỉ mang lại ứng cử viên 17 laptop review; SemEval train/test ban đầu không có sẵn; không có bộ lọc QA con người. NEXT_ACTION: mở rộng phạm vi phủ sóng nguồn được ủy quyền, nhận SemEval laptop train/test chính thức theo điều khoản của nhà cung cấp và có con người review `data/manual/laptop_filter_qa.csv`.

### Nghiên cứu khả thi + công cụ tái cấu trúc P1 (2026-10-08)

Ngoại lệ phạm vi được ủy quyền bởi nhiệm vụ hiện tại: Smartphone/Tablet chỉ có thể được khảo sát riêng vì tính khả thi. Project/training/inference phạm vi vẫn là laptop. Không có P2 hoặc mô hình huấn luyện. Tiêu chí hoàn thành P1 ban đầu ở trên vẫn có hiệu lực.

- [x] Kiểm tra đường dẫn cũ và lỗi kết hợp tiền tố độc lập.
- [x] siêu dữ liệu-chỉ mục phát trực tuyến đầu tiên và review được kết hợp bởi parent_asin.
- [x] Bộ lọc Laptop/Smartphone/Tablet có thể định cấu hình với khả năng xử lý accessory/ambiguity.
- [x] Các mẫu và trình xác thực QA bị ràng buộc; Các cột con người vẫn trống.
- [x] Đầu dò source/schema/connection nhỏ dành cho Điện tử, Điện thoại di động và Phụ kiện.
- [x] Hợp lệ-review, chất lượng-đại diện, các phép đo trùng lặp và lấy mẫu trên các tập hợp con được phép.
- [x] Thiết kế Cleaning/language/sampling/leakage mà không triển khai P2.
- [x] Phát trực tuyến dựa trên tệp, ngân sách memory/I/O/time/output rõ ràng; không có cơ sở dữ liệu.
- [x] Bảo vệ Raw/manifest, tổng kiểm tra, chẩn đoán một phần và tái sử dụng xác định.
- [x] Các thử nghiệm đã thực hiện: 60 đã vượt qua, bao gồm các thử nghiệm mô hình cơ sở; toàn bộ đồ đạc chỉ quét nhánh.
- [x] Đã cập nhật báo cáo Feasibility/pipeline/acquisition và quan sát JSON/CSV.
- [x] Đề xuất khảo sát lớn cụ thể được chuẩn bị để người dùng phê duyệt; không chạy quét lớn.

Bằng chứng: `reports/p1_pipeline_changes.md`, `reports/p1_data_feasibility.md`, `reports/tables/p1_feasibility_small.csv` và các báo cáo tái cấu trúc theo từng nguồn. Chỉ tập hợp con được đo: laptop 319 products/17 hợp lệ review, Điện thoại thông minh 25/3, Máy tính bảng 74/9. Tất cả các bộ lọc không được xác thực; language/clean tiếng Anh kích thước NOT_MEASURED.

BLOCKED: phạm vi phủ sóng toàn bộ nguồn, bộ lọc QA con người, SemEval laptop train/test và tính khả thi sạch của 50k vẫn chưa được giải quyết. NEXT_ACTION: review đề xuất mua lại Electronics 7.79 GB + ngân sách quét đầu tiên siêu dữ liệu; đang chờ ủy quyền rõ ràng, hãy lấy SemEval các tập đã chia và thực sự con người QA gốc.

### Bằng chứng làm cứng P1 (2026-10-08)

- [x] Cổng EOF/provenance siêu dữ liệu, chính sách bản ghi quá khổ có giới hạn và chẩn đoán lỗi đã được xác minh.
- [x] Đã triển khai các thử nghiệm QA review siêu dữ liệu, baseline/ambiguity/boundary QA không thể hủy và đèn chiếu trước siêu dữ liệu chỉ dành cho laptop.
- [x] Các bài kiểm tra 84 đã được thông qua; dependency/syntax kiểm tra và hai đầu dò cục bộ đã được xác minh, ứng cử viên 17/3/9 review không thay đổi.
- [x] sizes/resources chỉ có HEAD đã được kiểm tra lại và quét toàn bộ plan/criteria được ghi lại trong `reports/p1_full_scan_readiness.md`.
- [ ] Sự chấp thuận của người dùng mới, phạm vi phủ sóng metadata/index đầy đủ và quét laptop review đầy đủ.

BLOCKED: phạm vi phủ sóng toàn bộ nguồn, con người QA, SemEval các tập đã chia gốc và sản lượng tiếng Anh sạch vẫn không khả dụng. NEXT_ACTION: phê duyệt giai đoạn Điện tử siêu dữ liệu download/preflight sau đó khảo sát review download/laptop-only có điều kiện; không tăng trần nếu không có evidence/review. P1 vẫn chưa hoàn thiện; không có P2/training.

### Trạng thái thu nhận P1 30K (2026-10-08)

- [x] Danh sách kiểm tra target/config/acceptance đang hoạt động được cập nhật thành 30,000 sạch tiếng Anh laptop review; trần observations/technical lịch sử được bảo tồn.
- [x] Các bài kiểm tra 84 lại được thông qua; đã xác minh bốn tổng kiểm tra thô của Amazon và báo cáo tiền tố chỉ dành cho siêu dữ liệu hiện có.
- [x] Thiếu siêu dữ liệu đầy đủ; Chỉ HEAD xác nhận lại byte 1,312,900,427, trong giới hạn tải xuống 1.4 GB hiện có.
- [ ] Sự chấp thuận của người dùng mới đối với tải xuống đầy đủ siêu dữ liệu và đèn chiếu trước chỉ dành cho siêu dữ liệu.
- [ ] Thành công đầy đủ siêu dữ liệu EOF/index/provenance tập xác thực; chỉ chuẩn bị review sau đó.
- [ ] Sự chấp thuận riêng của người dùng đối với việc tải xuống review; rõ ràng là không được ủy quyền bởi nhiệm vụ hiện tại.

BLOCKED: không có tệp siêu dữ liệu đầy đủ hoặc phê duyệt tải xuống siêu dữ liệu rõ ràng; con người QA và SemEval các tập đã chia gốc vẫn là đang chờ. NEXT_ACTION: phê duyệt siêu dữ liệu chỉ acquisition/preflight, sau đó báo cáo kết quả đo được trước khi xin phê duyệt review riêng biệt. P1 chưa đầy đủ; không có P2/training.

### P1 đầy đủ bằng chứng thực thi siêu dữ liệu (2026-10-08)

- [x] Sự chấp thuận rõ ràng của người dùng chỉ áp dụng cho siêu dữ liệu download/preflight.
- [x] Bản đầy đủ siêu dữ liệu được tải xuống không thay đổi; SHA256/manifest và tính toàn vẹn của GZIP phát trực tuyến đã được xác minh.
- [x] Chuyến bay trước chỉ dành cho laptop đạt EOF: hàng 1,610,012, ứng cử viên 28,172, không có lỗi ghi; Trần tài nguyên không thay đổi và chưa đạt.
- [x] Bảo tồn hàng, ID được chọn duy nhất, dấu vân tay output/QA và năm tổng kiểm tra thô của Amazon đã được xác minh; Các bài kiểm tra 84 lại được thông qua.
- [ ] con người tập xác thực của QA sản phẩm 100 mới; SemEval các tập đã chia gốc.
- [ ] Phê duyệt review riêng biệt và tính khả thi đầy đủ của laptop review/clean-English.

BLOCKED: review không được ủy quyền; Thông lượng siêu dữ liệu cho thấy review có thể vượt quá mức trần tải xuống 60 mỗi phút hiện có. NEXT_ACTION: người dùng quyết định reviews/network/budget sau khi đo báo cáo siêu dữ liệu; không tăng trần tự động, P2 hoặc huấn luyện. P1 chưa hoàn thiện, mục tiêu 30K.

# 5. GIAI ĐOẠN P2 — dữ liệu CHẤT LƯỢNG, LÀM SẠCH, GHI NHÃN

## MỤC TIÊU

Tạo ra laptop review bộ dữ liệu sạch và định lượng các vấn đề về chất lượng dữ liệu.

### Thiếu P2-T01-Kiểm tra dữ liệu
- [ ] Thiếu tỷ lệ theo trường bắt buộc.
- [ ] Chính sách xử lý được ghi lại.

### Kiểm tra P2-T02 không hợp lệ-review
- [ ] Empty/whitespace review.
- [ ] review cực ngắn.
- [ ] Bản ghi không đúng định dạng.

### P2-T03 Kiểm toán trùng lặp
- [ ] Bản sao chính xác.
- [ ] Văn bản lặp lại trên laptop products/users nếu các trường tồn tại.
- [ ] Gần như trùng lặp nếu chất liệu.

### Bộ lọc P2-T04 laptop QA
- [ ] Kiểm tra dương tính giả.
- [ ] Loại bỏ ô nhiễm accessory/non-laptop.
- [ ] Bộ lọc báo cáo QA sample/result.

### P2-T05 Làm sạch văn bản
- [ ] Chuẩn hóa HTML các tệp kết quả.
- [ ] Bình thường hóa khoảng trắng.
- [ ] Xử lý các URL khi thích hợp.
- [ ] Bảo toàn sự phủ định.
- [ ] Tránh làm sạch mạnh để phá hủy cảm xúc.

### P2-T06 nhãn có nguồn gốc từ xếp hạng
- [ ] Áp dụng 1–2 negative / 3 neutral / 4–5 positive.
- [ ] Xác thực các giá trị nhãn.
- [ ] Báo cáo số lớp và tỷ lệ phần trăm.

### Ứng viên P2-T07 nhãn-nhiễu
- [ ] Lưu các ví dụ có thể không đồng ý về văn bản xếp hạng cho thủ công review sau này.

### Kiểm tra mất cân bằng lớp P2-T08
- [ ] Tính tỉ số lớp.
- [ ] Quyết định xem trọng lượng có được bảo hành hay không.
- [ ] Lý do tài liệu.

### P2-T09 Làm sạch liên tục bộ dữ liệu
- [ ] Lưu `data/processed/laptop_reviews.parquet`.
- [ ] Ghi lại số lượng hàng before/after.
- [ ] Ghi lại số liệu thống kê cleaning/filtering.

**DONE_WHEN:** Chỉ tồn tại laptop sạch tiếng Anh bộ dữ liệu; mục tiêu ~30k nếu khả thi, nếu không thì kích thước thực tế và tính đầy đủ của lớp coverage/product sẽ được ghi lại mà không làm giảm chất lượng.

## GIAI ĐOẠN ĐẦU RA
- [ ] Làm sạch laptop bộ dữ liệu.
- [ ] Báo cáo chất lượng dữ liệu.
- [ ] Báo cáo phân phối nhãn.
- [ ] Báo cáo mất cân bằng lớp học.
- [ ] Mẫu ứng viên nhãn-nhiễu.

---

# 6. GIAI ĐOẠN P3 — laptop EDA VÀ CHI TIẾT

## MỤC TIÊU

Tạo ra những phân tích sâu sắc thay vì chỉ biểu đồ mô tả.

### Tổng quan về P3-T01 bộ dữ liệu
- [ ] Số lượng review.
- [ ] Số lượng Laptop/product.
- [ ] Số lượng Brand/category nếu đáng tin cậy.
- [ ] Phạm vi thời gian nếu có.

### Phân tích xếp hạng P3-T02
- [ ] Phân bổ xếp hạng.
- [ ] Đánh giá của laptop/product.
- [ ] Đánh giá theo thương hiệu nếu đáng tin cậy.
- [ ] Đánh giá theo thời gian nếu có ý nghĩa.

### Phân tích P3-T03 cảm xúc
- [ ] Phân phối tổng thể.
- [ ] cảm xúc bởi laptop/product.
- [ ] cảm xúc theo thương hiệu nếu đáng tin cậy.
- [ ] cảm xúc theo thời gian nếu có ý nghĩa.

### P3-T04 Phân tích độ dài văn bản
- [ ] Số ký tự.
- [ ] Số từ.
- [ ] token được tính khi hữu ích.
- [ ] Chiều dài bằng sentiment/rating.

### P3-T05 Phân tích từ vựng
- [ ] Các điều khoản thường xuyên.
- [ ] N-gram dương.
- [ ] N-gram trung tính.
- [ ] N-gram âm.

### Phân tích P3-T06 Helpfulness/metadata
- [ ] Tính hữu ích so với sentiment/rating/length nếu trường tồn tại.
- [ ] Phân tích mua hàng đã được xác minh nếu trường tồn tại.
- [ ] Chỉ phân tích Product/spec/brand khi chất lượng siêu dữ liệu hỗ trợ cho kết luận.

### Phân tích chất lượng P3-T07 dữ liệu
- [ ] Tỷ lệ trùng lặp.
- [ ] Tỷ lệ thiếu.
- [ ] Tỷ lệ review ngắn.
- [ ] Trực quan hóa sự mất cân bằng lớp học.
- [ ] Ví dụ nhãn-nhiễu.

### Trích xuất thông tin chuyên sâu dành riêng cho P3-T08 laptop
- [ ] Xác định các chủ đề laptop complaint/praise định kỳ từ bằng chứng.
- [ ] Điều tra các khía cạnh của ứng viên như pin, màn hình, bàn phím, hiệu suất, cấu trúc, giá cả, tính di động, bộ lưu trữ, thermals/noise.
- [ ] Không trình bày các khía cạnh của ứng viên dưới dạng dữ kiện thực tế cho đến khi data/ABSA hỗ trợ chúng.
- [ ] Tách biệt quan sát khỏi giải thích.

**DONE_WHEN:** EDA chứa nhận định từ dữ liệu đã được chứng minh bằng bằng chứng và không chỉ có các bản phân phối.

## GIAI ĐOẠN ĐẦU RA
- [ ] EDA notebook.
- [ ] Figures/tables.
- [ ] Tóm tắt cái nhìn sâu sắc.
- [ ] Báo cáo phân tích dữ liệu.

---

# 7. GIAI ĐOẠN P4 — dữ liệu TÁCH VÀ TIẾP XÚC

## MỤC TIÊU

Tạo bộ cố định kháng rò rỉ dữ liệu.

### P4-T01 cố định phân chia
- [ ] mục tiêu 70/15/15.
- [ ] Phân tầng cảm xúc.
- [ ] Sửa hạt giống ngẫu nhiên ngẫu nhiên.

### Phân tích P4-T02 rò rỉ dữ liệu
- [ ] Văn bản chính xác rò rỉ dữ liệu.
- [ ] Bản sao rò rỉ dữ liệu.
- [ ] Sản phẩm rò rỉ dữ liệu.
- [ ] Xem xét nhóm phân chia theo `product_id` / `parent_asin`.

### P4-T03 Kiên trì các tập đã chia
- [ ] Lưu tập huấn luyện.
- [ ] Lưu tập xác thực.
- [ ] Lưu kiểm thử.

### P4-T04 Tiền xử lý cổ điển
- [ ] Vệ sinh cơ bản.
- [ ] TF-IDF.
- [ ] Bảo toàn sự phủ định.
- [ ] khớp mô hình TF-IDF chỉ có trên tập huấn luyện.

### Tiền xử lý P4-T05 BERT
- [ ] Làm sạch tối thiểu.
- [ ] BERT bộ tách token.
- [ ] Không có gốc.
- [ ] Không loại bỏ từ dừng.
- [ ] Chọn độ dài chuỗi tối đa từ phân phối độ dài token được quan sát.

## GIAI ĐOẠN ĐẦU RA
- [ ] cố định các tập đã chia.
- [ ] Báo cáo phân chia.
- [ ] Đường ống cổ điển
- [ ] đường ống BERT.

---

# 8. GIAI ĐOẠN P5 — ML CỔ ĐIỂN đánh giá so sánh

## MỤC TIÊU

Thiết lập đường cơ sở laptop cảm xúc mạnh mẽ.

### P5-E00 Đa số mô hình cơ sở
- [ ] Đánh giá mô hình cơ sở thuộc loại đa số.

### Hồi quy logistic P5-E01
- [ ] TF-IDF + Hồi quy logistic.
- [ ] Chỉ sử dụng trọng số lớp nếu hợp lý.

### SVM tuyến tính P5-E02
- [ ] TF-IDF + SVM tuyến tính.
- [ ] Chỉ sử dụng trọng số lớp nếu hợp lý.

### Cây quyết định P5-E03
- [ ] TF-IDF + Cây quyết định.
- [ ] Kiểm soát việc trang bị quá mức.
- [ ] Chỉ sử dụng trọng số lớp nếu hợp lý.

## CÁC CHỈ SỐ BẮT BUỘC
- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision) mỗi lớp.
- [ ] độ bao phủ (recall) mỗi lớp.
- [ ] F1 mỗi lớp.
- [ ] Macro F1.
- [ ] Trọng số F1.
- [ ] Ma trận nhầm lẫn.
- [ ] Thời gian huấn luyện.
- [ ] Độ trễ suy luận.
- [ ] Kích thước mô hình.
- [ ] RAM.

**DONE_WHEN:** Tất cả các mô hình đều được đánh giá trên cùng một bộ cố định kiểm thử và kết quả nằm trong một bảng có thể so sánh.

## GIAI ĐOẠN ĐẦU RA
- [ ] mô hình các tệp kết quả.
- [ ] Bảng đánh giá so sánh.
- [ ] Ma trận nhầm lẫn.
- [ ] Kết luận ML cổ điển tốt nhất.

---

# 9. GIAI ĐOẠN P6 — BERT TỔNG THỂ cảm xúc

## MỤC TIÊU

Tinh chỉnh BERT cho 3 lớp laptop cảm xúc.

### Bộ chuyển đổi P6-T01 bộ dữ liệu
- [ ] Tạo PyTorch/Hugging Face tương thích bộ dữ liệu.

### P6-T02 tách token
- [ ] BERT bộ tách token.
- [ ] Chính sách Truncation/padding.
- [ ] Ghi lại độ dài chuỗi tối đa.

### P6-T03 huấn luyện
- [ ] Tinh chỉnh BERT.
- [ ] Theo dõi tập huấn luyện hàm mất mát.
- [ ] Theo dõi tập xác thực hàm mất mát.
- [ ] Theo dõi Macro F1.
- [ ] Tiết kiệm điểm lưu mô hình tốt nhất.

### Xử lý mất cân bằng P6-T04
- [ ] Đánh giá nhu cầu hàm mất mát có trọng số.
- [ ] Trọng lượng lớp tài liệu nếu được sử dụng.

### Đánh giá P6-T05
- [ ] Số liệu phân loại tương tự như P5.
- [ ] Thời gian huấn luyện.
- [ ] Độ trễ suy luận.
- [ ] Kích thước mô hình.
- [ ] RAM.
- [ ] GPU/VRAM nếu có.

### So sánh P6-T06 Cost/performance
- [ ] BERT so với LR.
- [ ] BERT so với SVM.
- [ ] BERT vs DT.
- [ ] Định lượng mức tăng Macro-F1.
- [ ] Định lượng sự gia tăng chi phí tính toán.

## CÂU HỎI NGHIÊN CỨU CHÍNH

BERT cải thiện Macro F1 bao nhiêu so với TF-IDF + SVM tuyến tính trên laptop review và sự cải thiện đó đòi hỏi chi phí tính toán như thế nào?

## GIAI ĐOẠN ĐẦU RA
- [ ] BERT mô hình.
- [ ] Đánh giá BERT.
- [ ] Hợp nhất đánh giá so sánh.
- [ ] Phân tích Cost/performance.

---

# 10. GIAI ĐOẠN P7 — phân tích lỗi

## MỤC TIÊU

Đặc trưng các chế độ lỗi mô hình trong laptop review.

### PHÂN LOẠI LỖI
- [ ] Phủ định.
- [ ] Hỗn hợp cảm xúc.
- [ ] Sự mỉa mai.
- [ ] review rất ngắn.
- [ ] review dài.
- [ ] cảm xúc tiềm ẩn.
- [ ] Rating/text conflict.
- [ ] Multi-khía cạnh review.
- [ ] Thuật ngữ dành riêng cho laptop.

### SO SÁNH mô hình
- [ ] lỗi LR.
- [ ] lỗi SVM.
- [ ] lỗi DT.
- [ ] lỗi BERT.
- [ ] Các trường hợp BERT giải quyết được ML cổ điển bỏ sót.
- [ ] Các trường hợp tất cả các mô hình đều bị lỗi.

## GIAI ĐOẠN ĐẦU RA
- [ ] Phân loại lỗi.
- [ ] Các ví dụ có chú thích
- [ ] Phân tích lỗi cụ thể của mô hình.

---

# 11. GIAI ĐOẠN P8 — ABSA khía cạnh CHIẾT XUẤT CÓ HẠN

## MỤC TIÊU

Trích xuất các thuật ngữ laptop khía cạnh rõ ràng.

### P8-T01 Phân tích cú pháp SemEval laptop
- [ ] Bảo lưu ID câu.
- [ ] Bảo quản khía cạnh vị trí cụm từ.

### Chuyển đổi BIO P8-T02
- [ ] `B-ASP`.
- [ ] `I-ASP`.
- [ ] `O`.
- [ ] Xác thực căn chỉnh vị trí cụm từ.

### P8-T03 tập huấn luyện mô hình
- [ ] Tinh chỉnh phân loại BERT token.

### Đánh giá P8-T04
- [ ] Thực thể độ chính xác dự đoán (precision).
- [ ] Thực thể độ bao phủ (recall).
- [ ] Thực thể F1.

**DONE_WHEN:** khía cạnh vị trí cụm từ có thể được trích xuất từ các ví dụ SemEval laptop không nhìn thấy được với các chỉ số cấp vị trí cụm từ có thể tái tạo.

## GIAI ĐOẠN ĐẦU RA
- [ ] BIO bộ dữ liệu.
- [ ] Trích xuất khía cạnh mô hình.
- [ ] Đánh giá.

---

# 12. GIAI ĐOẠN P9 — ABSA khía cạnh cảm xúc PHÂN LOẠI

## MỤC TIÊU

Phân loại cảm xúc theo từng laptop khía cạnh.

## ĐẦU VÀO

`review_text + aspect_term`

## ĐẦU RA

`positive | neutral | negative`

### Chuẩn bị P9-T01 bộ dữ liệu
- [ ] Xây dựng các ví dụ về ngữ cảnh khía cạnh.
- [ ] Chuẩn hóa các lớp mục tiêu nhãn thành 3.
- [ ] Resolve/exclude không được hỗ trợ conflict nhãn và chính sách tài liệu.

### P9-T02 tập huấn luyện
- [ ] Tinh chỉnh BERT cho khía cạnh cảm xúc.

### Đánh giá P9-T03
- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision).
- [ ] độ bao phủ (recall).
- [ ] Macro F1.
- [ ] Ma trận nhầm lẫn.

### P9-T04 ABSA đầu cuối
- [ ] Kết nối trích xuất khía cạnh với khía cạnh cảm xúc.
- [ ] Tạo đường ống `review -> aspect spans -> aspect sentiment`.

## GIAI ĐOẠN ĐẦU RA
- [ ] khía cạnh cảm xúc mô hình.
- [ ] Đường ống ABSA từ đầu đến cuối.
- [ ] Chỉ số ABSA

---

# 13. GIAI ĐOẠN P10 — AMAZON laptop thủ công bộ kiểm thử gold

## MỤC TIÊU

Đánh giá Amazon laptop review thực tế và định lượng hai vấn đề:
1. nhiễu nhãn có nguồn gốc từ xếp hạng;
2. SemEval→Amazon dataset/platform/style thay đổi trong cùng một laptop phạm vi.

## KÍCH THƯỚC mục tiêu

`300–500 Amazon Laptop reviews`

## LẤY MẪU
- [ ] Trên các xếp hạng.
- [ ] Trên toàn chiều dài review.
- [ ] Trên khắp laptop products/brands khi có sẵn.
- [ ] Bao gồm các trường hợp mixed/difficult.

## TRƯỜNG gán nhãn

```text
review_id
product_id
review_text
rating
rating_derived_sentiment
human_overall_sentiment
aspect_term
human_aspect_sentiment
notes
```

## NHIỆM VỤ
- [ ] con người chú thích tổng thể cảm xúc.
- [ ] con người chú thích các thuật ngữ khía cạnh.
- [ ] con người chú thích khía cạnh cảm xúc.
- [ ] Các trường hợp không rõ ràng của review.
- [ ] Đo đánh giá-vs-con người agreement/disagreement.
- [ ] Đánh giá tổng thể cảm xúc các mô hình trên bộ kiểm thử gold.
- [ ] Đánh giá ABSA được đào tạo SemEval trên Amazon laptop bộ kiểm thử gold.
- [ ] So sánh hiệu suất SemEval kiểm thử với Amazon gold-kiểm thử.

## QUY TẮC GIẢI GIẢI

Sự sụt giảm hiệu suất từ SemEval xuống Amazon phải được mô tả là **sự thay đổi dataset/platform/style trong laptop review**, chứ không phải bằng chứng về sự khái quát hóa tiện ích công nghệ phone/headphone/general.

## GIAI ĐOẠN ĐẦU RA
- [ ] `data/manual/amazon_laptop_gold_test.csv`
- [ ] Đánh giá gold-kiểm thử.
- [ ] Phân tích nhãn-nhiễu.
- [ ] SemEval→Phân tích chuyển giao của Amazon.

---

# 14. GIAI ĐOẠN P11 — ỨNG DỤNG STREAMLIT

## MỤC TIÊU

Phân tích laptop review đơn giản dành cho người dùng cuối; không có sự phức tạp không cần thiết ở lối vào.

### CHẾ ĐỘ A — laptop review đơn
- [ ] Nhập văn bản.
- [ ] Tổng thể cảm xúc.
- [ ] độ tin cậy nếu có.
- [ ] Trích xuất khía cạnh.
- [ ] khía cạnh cảm xúc.

### CHẾ ĐỘ B — lô laptop review
- [ ] Tải lên CSV.
- [ ] lô suy luận.
- [ ] Tỷ lệ phần trăm Positive/Neutral/Negative.
- [ ] Tần số đề cập đến khía cạnh.
- [ ] Phân phối cảm xúc bởi khía cạnh.
- [ ] Các khía cạnh positive/negative laptop hàng đầu.

## Lược đồ đầu ra

```json
{
  "domain": "laptop",
  "language": "en",
  "sentiment": "negative",
  "confidence": 0.91,
  "aspects": [
    {
      "aspect": "battery",
      "sentiment": "negative",
      "confidence": 0.94
    }
  ]
}
```

**DONE_WHEN:** Ứng dụng thực hiện suy luận từ các mô hình đã lưu mà không cần đào tạo lại.

## GIAI ĐOẠN ĐẦU RA
- [ ] `app/streamlit_app.py`
- [ ] Chế độ đơn review.
- [ ] Chế độ lô-review.

---

# 15. GIAI ĐOẠN P12 — tiếng Việt SẴN SÀNG MỞ RỘNG

## MỤC TIÊU

Giữ laptop phạm vi cố định trong khi thực hiện tiện ích mở rộng ngôn ngữ sau này với chi phí thấp.

## NHIỆM VỤ
- [ ] Giao diện tiền xử lý cơ bản.
- [ ] Mô-đun tiền xử lý tiếng Anh.
- [ ] Giao diện tiếng Việt placeholder/module.
- [ ] Đăng ký mô hình.
- [ ] `en -> BERT`.
- [ ] Dự trữ `vi -> PhoBERT`.
- [ ] Lược đồ đầu ra độc lập với ngôn ngữ.
- [ ] Giữ logic dành riêng cho mô hình bên ngoài giao diện người dùng Streamlit.

**DONE_WHEN:** Thêm PhoBERT yêu cầu thay đổi implementation/config, không thiết kế lại hợp đồng ứng dụng.

---

# 16. GIAI ĐOẠN P13 — HOÀN THÀNH

### Hợp nhất P13-T01 đánh giá so sánh
- [ ] LR.
- [ ] SVM.
- [ ] DT.
- [ ] BERT.
- [ ] Bảng chỉ số.
- [ ] Bảng chi phí.

### Hợp nhất phân tích P13-T02
- [ ] EDA.
- [ ] Mất cân bằng.
- [ ] nhiễu nhãn.
- [ ] phân tích lỗi.
- [ ] ABSA.
- [ ] SemEval→Chuyển laptop của Amazon.

### Tài liệu P13-T03
- [ ] README.
- [ ] Cài đặt.
- [ ] Chuẩn bị dữ liệu.
- [ ] huấn luyện.
- [ ] suy luận.
- [ ] Sử dụng ứng dụng.

### Khả năng tái tạo P13-T04
- [ ] Thiết lập môi trường trong lành.
- [ ] Đường ống dữ liệu thực thi.
- [ ] mô hình suy luận thực thi.
- [ ] Ứng dụng thực thi.

### P13-T05 Báo cáo cuối cùng
- [ ] Tuyên bố vấn đề.
- [ ] Ranh giới laptop-phạm vi.
- [ ] dữ liệu và phương pháp lọc.
- [ ] dữ liệu Quality/EDA.
- [ ] Tổng thể cảm xúc xây dựng mô hình.
- [ ] So sánh mô hình.
- [ ] phân tích lỗi.
- [ ] ABSA.
- [ ] Amazon laptop bộ kiểm thử gold.
- [ ] Ứng dụng.
- [ ] Hạn chế.
- [ ] Công việc tương lai.

## GIỚI HẠN BẮT BUỘC
- [ ] Không yêu cầu khái quát hóa ngoài laptop review.
- [ ] Đánh giá nhãn là nhãn đại diện ồn ào.
- [ ] SemEval và Amazon có thể khác nhau trong cách viết style/platform ngay cả trong laptop phạm vi.
- [ ] thủ công bộ dữ liệu gold tương đối nhỏ.

---

# 17. BẢN ĐỒ THỰC HIỆN TUẦN

## TUẦN 1
- [x] P0 đã hoàn thành.
- [ ] P1 đã hoàn thành.

**EXIT_CRITERIA:** Bộ lọc laptop là defined/validated; Có thể sử dụng được nhóm Amazon laptop và SemEval; schema/sampling được ghi lại.

## TUẦN 2
- [ ] P2 đã hoàn thành.
- [ ] P3 đã hoàn thành.

**EXIT_CRITERIA:** tồn tại laptop bộ dữ liệu sạch và EDA sâu.

## TUẦN 3
- [ ] P4 đã hoàn thành.
- [ ] P5 đã hoàn thành.

**EXIT_CRITERIA:** cố định các tập đã chia và ML cổ điển đánh giá so sánh tồn tại.

## TUẦN 4
- [ ] P6 đã hoàn thành.
- [ ] P7 đã hoàn thành.

**EXIT_CRITERIA:** BERT đánh giá so sánh, so sánh chi phí và phân tích lỗi tồn tại.

## TUẦN 5
- [ ] P8 đã hoàn thành.
- [ ] P9 đã hoàn thành.
- [ ] P10 về cơ bản đã hoàn thiện.

**EXIT_CRITERIA:** ABSA toàn diện hoạt động và Amazon laptop bộ kiểm thử gold tồn tại.

## TUẦN 6
- [ ] P11 đã hoàn thành.
- [ ] P12 đã hoàn thành.
- [ ] P13 đã hoàn thành.

**EXIT_CRITERIA:** Ứng dụng, tài liệu, khả năng tái tạo và báo cáo cuối cùng đã hoàn tất.

---

# 18. ĐỊNH NGHĨA TOÀN CẦU CỦA DONE

## dữ liệu
- [ ] laptop chỉ làm sạch tiếng Anh đã xử lý bộ dữ liệu, mục tiêu ~30k nếu khả thi; assess/document bể bơi chất lượng cao nhỏ hơn.
- [ ] Bộ lọc laptop có thể tái tạo.
- [ ] EDA sâu.
- [ ] Phân tích sự mất cân bằng giai cấp.
- [ ] Phân tích nhãn-nhiễu.

## TỔNG THỂ cảm xúc
- [ ] Hồi quy logistic.
- [ ] SVM tuyến tính.
- [ ] Cây quyết định.
- [ ] BERT.
- [ ] Hợp nhất đánh giá so sánh.
- [ ] phân tích lỗi.

## ABSA
- [ ] Trích xuất thuật ngữ khía cạnh.
- [ ] Phân loại khía cạnh cảm xúc.
- [ ] ABSA đầu cuối.
- [ ] Đánh giá SemEval.

## thủ công kiểm thử
- [ ] 300–500 được chú thích thủ công Amazon laptop review.
- [ ] Phân tích xếp hạng-vs-con người.
- [ ] Đánh giá tổng thể cảm xúc gold-kiểm thử.
- [ ] SemEval→Đánh giá ABSA của Amazon laptop.

## ỨNG DỤNG
- [ ] Phân tích laptop review đơn lẻ.
- [ ] Phân tích lô laptop review.
- [ ] Tóm tắt tổng thể cảm xúc.
- [ ] Tóm tắt khía cạnh.

## KỸ THUẬT
- [ ] Kho lưu trữ có thể tái tạo.
- [ ] Đã lưu các mô hình.
- [ ] Lựa chọn language/model dựa trên cấu hình.
- [ ] Điểm mở rộng Vietnamese/PhoBERT.

## TÀI LIỆU
- [ ] README.
- [ ] Báo cáo cuối cùng.
- [ ] Hạn chế.
- [ ] Công việc tương lai.

---

# 19. QUY TẮC HOẠT ĐỘNG AI

1. Không bao giờ mở rộng phạm vi ra ngoài máy tính xách tay mà không có hướng dẫn rõ ràng cho người dùng.
2. Không bao giờ đánh dấu `[x]` mà không có bằng chứng cho thấy đáp ứng tiêu chí hoàn thành.
3. Làm việc theo thứ tự phụ thuộc trừ khi có sự song song an toàn rõ ràng.
4. Không bao giờ sửa đổi dữ liệu thô tại chỗ.
5. Ghi ngẫu nhiên các hạt giống ngẫu nhiên để lọc mẫu, lấy mẫu và tách mẫu.
6. Xác thực lọc laptop; nhiễm bẩn phụ kiện là lỗi chất lượng dữ liệu.
7. khớp mô hình preprocessing/vectorizers chỉ có trên huấn luyện dữ liệu.
8. Ngăn chặn duplicate/product rò rỉ dữ liệu trước khi báo cáo hiệu suất.
9. Sử dụng Macro F1 làm chỉ số lựa chọn chính.
10. Hãy coi cảm xúc có nguồn gốc từ xếp hạng là nhãn đại diện nhiễu.
11. Sử dụng quy trình tiền xử lý thích hợp riêng biệt cho ML và BERT cổ điển.
12. So sánh các mô hình trên cùng một bộ cố định kiểm thử.
13. Lưu các tệp kết quả cần thiết để tiếp tục công việc.
14. SemEval→Sự thay đổi hiệu suất của Amazon phải được mô tả giống như sự thay đổi phạm vi dataset/platform/style.
15. Không yêu cầu khái quát hóa tiện ích phone/headphone/other.
16. Cập nhật tệp này khi trạng thái tác vụ thay đổi.
17. Nếu dự án phạm vi thay đổi, trước tiên hãy cập nhật HỢP ĐỒNG DỰ ÁN.
