> LEGACY: bằng chứng2026-10-15, Việt hóa2026-10-19. Tra [chỉ mục hiện hành](PROJECT_INDEX.md), [benchmark semantic](MODEL_STACK_REFACTOR.md) và [kế hoạch cloud](TABPFN_CLOUD_PLAN.md); không dùng trạng thái trong tài liệu này làm tiến độ mới.

# Hợp đồng dữ liệu và tiền xử lý cho các giai đoạn sau P4

Nguồn có thẩm quyền: PLAN/AGENTS hiện hành. Kết quả cố định đang dùng là `p4_20261009_final`. Parquet P2 gốc không đổi; giữ phân vùng và độ lệch ký tự gốc của SemEval. Đây là hợp đồng tại thời điểm P4; trạng thái các giai đoạn sau xem kế hoạch và bàn giao hiện hành.

## Các tập dữ liệu

`data/processed/splits/p4_20261009_final/{train,validation,test}.parquet` giữ mọi trường/giá trị P2, thêm `split` (train/validation/test) và SHA256 `split_group_id`. Mỗi ID review và mỗi hàng trong 30000 hàng nguồn xuất hiện đúng một lần. Sản phẩm cha, biến thể và các thành phần văn bản liên kết cùng thuộc một tập. Hàm băm nguồn, hạt giống 42, tỷ lệ 70-15-15 và thành viên từng tập nằm trong `reports/p4/p4_20261009_final/manifest.json`.

ID lớp: negative0/neutral1/positive2. Nhãn suy từ số sao; số sao/siêu dữ liệu chỉ là trường kiểm tra, không phải biến dự đoán. Train 21k/validation 4500/test 4500; số sản phẩm 6357/1361/1362. Lần chạy hiện hành không loại thêm mẫu.

## Đầu vào mô hình cổ điển

`artifacts/preprocessing/p4_20261009_final/{split}_tfidf.npz` là ma trận CSR float32 có 30000 cột. `{split}_feature_rows.parquet` chứa review_id theo đúng thứ tự, mục tiêu label_id và tên tập. Hàng i của ma trận PHẢI khớp hàng i của tệp phụ; không sắp xếp riêng.

`tfidf.joblib` là ClassicalPreprocessor đã cố định, chỉ khớp trên tập huấn luyện, chưa có bộ phân loại. Dùng `.transform(frame)` cho mọi dữ liệu giữ lại/suy luận, chỉ đọc frame.text. `.fit_train` chỉ chấp nhận tập huấn luyện và ghi ID dùng để khớp. Không khớp từ vựng/IDF trên toàn bộ dữ liệu; không lấy đặc trưng từ nhãn, số sao, thương hiệu, tiêu đề, ID sản phẩm, nguồn, cờ, lượt hữu ích hay giao dịch đã xác minh. Cấu hình/phiên bản tiền xử lý được cố định trong preprocessing.json. So sánh tham số P5 chỉ khớp train, chọn bằng validation, không dùng test cuối.

## Đầu vào BERT

`data/processed/features/p4_20261009_final/{split}_bert.parquet` lưu review_id, mục tiêu label_id, split và các danh sách số nguyên input_ids/attention_mask/token_type_ids. Chỉ ba mảng token là đầu vào mô hình; ID/nhãn/tên tập dùng quản lý hoặc làm mục tiêu.

Mỗi chuỗi có CLS101…SEP102, tối đa 512 token; lưu chưa đệm, mask1/typeID0. Phiên bản tokenizer, hàm băm tài nguyên và chính sách độ dài từ train nằm trong preprocessing.json; bert/tokenizer.json cục bộ tải lại từ vựng/cắt ngắn cố định. BertPreprocessor.encode(frame,padding=True) hỗ trợ đệm động theo chuỗi dài nhất trong lô bằng pad0 và attention mask.

Không rút gọn từ gốc/xóa từ dừng. Chuẩn hóa hoa thường/dấu do tokenizer uncased đã huấn luyện trước thực hiện; trước tokenizer, văn bản ngoài vẫn giữ hoa thường, dấu câu và phủ định. Train có p95=390, chọn 512; khoảng 3.1% vẫn bị cắt. P4 không tạo bộ chuyển đổi Torch, bộ gom lô, trọng số, điểm lưu hoặc bộ huấn luyện P6.

## Đánh giá và cách ly gold

Các tập cố định không trùng sản phẩm kiểm tra khả năng xử lý sản phẩm cha chưa thấy, không bảo đảm thương hiệu/người dùng chưa thấy. Giao nhau người dùng 35/37/6 đã được công bố. Loại ID/văn bản QA và 250 mẫu chẩn đoán dành riêng; sản phẩm QA phạm vi có thể giao nhau nhưng nhãn QA thủ công không bao giờ là nhãn huấn luyện cảm xúc.

P10 chưa có gold. Sau này lấy mẫu độc lập từ dữ liệu giữ lại/mới, cách ly với ID nguồn/văn bản/nhóm huấn luyện; không dùng gold để điều chỉnh. EDA toàn bộ dữ liệu P3 là lịch sử mô tả; không dùng lại từ theo lớp để chọn đặc trưng có giám sát. Từ P4, test dành cho đánh giá cuối. Tại thời điểm P4 chưa có dự đoán/hiệu năng mô hình hoặc confidence hiệu chuẩn.

## Toàn vẹn và tái sử dụng

Hàm băm đầu ra gắn với bản kê, bản chụp 121 đầu vào hoàn tất gồm 41 tệp được bảo vệ, validation/reload_validation và environment.json là bằng chứng tái lập tại thời điểm nghiệm thu P4. Báo cáo P4 không tự cho phép thực hiện P5. Nguồn/giấy phép SemEval NOT_VERIFIED theo ngoại lệ giáo dục của chủ dự án; tái sử dụng bằng chứng kỹ thuật PASS khi nội dung không đổi. P4 không tiền xử lý SemEval hoặc âm thầm đổi vị trí cụm từ. Báo cáo có ngày cũ là bản chụp lịch sử; PLAN/bàn giao/hợp đồng hiện hành xác định mức sẵn sàng cho giai đoạn sau.

Việt hóa ngày 2026-10-19 thay văn bản tài liệu/chú thích; không cập nhật lại hàm băm nghiệm thu lịch sử để che thay đổi. Dữ liệu và các kết quả mô hình giữ nguyên.

Giới hạn: kết luận chỉ cho laptop; nhiễu nhãn suy từ số sao; khác biệt phong cách SemEval–Amazon trong cùng phạm vi laptop; bộ gold thủ công nhỏ, hiện chưa được tạo. Tìm gần trùng từ vựng xấp xỉ không chứng minh đầy đủ về ngữ nghĩa; không khẳng định sẵn sàng vận hành thực tế.
