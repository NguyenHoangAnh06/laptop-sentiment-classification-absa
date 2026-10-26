# P3 — Phân tích khám phá dữ liệu đánh giá laptop Amazon

Số liệu của giai đoạn P3 ngày 2026-10-09; biên tập ngôn ngữ và bổ sung nhận xét ngày 2026-10-20. P3-T01–T08 đã hoàn thành trên bộ dữ liệu P2 cố định, không chia tập, khớp mô hình hay huấn luyện trong P3. Các nhận xét là mô tả và giả thuyết từ dữ liệu, không phải nhãn con người hoặc kết quả ABSA (phân tích cảm xúc theo khía cạnh).

## 1. Nguồn và phương pháp

- Đầu vào EDA (phân tích khám phá dữ liệu): `data/processed/laptop_reviews.parquet`, SHA256 `611b73584a933645336784b13b7f004a17e8803758d1be8ac64708563eabb5ba`.
- Kết quả đã xác minh ở `reports/p3/20261009_verified/`: 15 bảng CSV và 7 biểu đồ, mỗi hình có PNG/SVG. Các thư mục `20261009` và `20261009_final` là lần thử trước, không phải bản cuối.
- Notebook nguồn: `notebooks/03_laptop_eda.ipynb`; bản đã chạy: `reports/p3/20261009_verified/03_laptop_eda.final.ipynb`. Mã xử lý tái sử dụng ở `src/data/eda.py`, lệnh phân tích ở `scripts/analyze_p3.py`.
- Bằng chứng chất lượng nhóm ứng viên và các bước xử lý P2 được tái sử dụng từ `reports/data_quality/candidate_pool_20261009/audit.json` cùng bản kê/kiểm tra P2. Không khảo sát lại nguồn, kiểm tra QA lại hoặc gán nhãn mới.
- Tần suất bài có từ (document frequency) chỉ đếm một lần cho mỗi từ/cụm từ trong một bài. N-gram là chuỗi từ liên tiếp: unigram gồm 1 từ, bigram 2 từ, trigram 3 từ. Không nối những từ vốn bị ngăn bởi từ dừng đã bỏ.
- Biểu thức chính quy, chuyển chữ thường và danh sách từ dừng chỉ phục vụ mô tả; giữ not/no (từ phủ định) và dạng viết tắt; không rút gọn từ gốc. Số ký tự, số từ tách bằng khoảng trắng và số token (đơn vị tách văn bản) là các thước đo khác nhau, không phải số token BERT.
- Ngưỡng số mẫu hỗ trợ (support) dùng trình bày: 30 bài cho từ vựng, 100 bài cho thương hiệu/thời gian, 30 bài cho sản phẩm. Vẫn lưu nhóm ít mẫu nhưng không xếp hạng chúng. Đây không phải điều kiện nghiệm thu mới.
- Chênh lệch tỷ lệ trong lớp so với ngoài lớp và tỷ số mức phổ biến đã làm trơn (smoothed lift) là thống kê khám phá, không phải kiểm định ý nghĩa thống kê. Không dùng thống kê toàn bộ dữ liệu để chọn đặc trưng có giám sát hoặc khớp mô hình ở giai đoạn sau.

## 2. Tổng quan, số sao và độ dài

Bộ dữ liệu có **30.000 bài, 9.080 sản phẩm và 181 nhóm thương hiệu từ siêu dữ liệu**. Không đồng nghĩa đã xác minh 181 nhà sản xuất. Parquet không có cột danh mục/thông số phần cứng có cấu trúc; không suy cấu hình phần cứng từ nội dung hoặc tiêu đề.

Có 5.025 sản phẩm chỉ có 1 bài, 115 sản phẩm có ít nhất 30 bài; tối đa 100 bài mỗi sản phẩm. Nhóm 100 sản phẩm nhiều bài nhất chiếm 19,34% số bài. Phân bố này chịu ảnh hưởng của làm sạch, lấy mẫu và các mẫu QA/chẩn đoán dành riêng.

| Số sao | Số bài | Tỷ lệ | Trung vị số từ |
|---|---:|---:|---:|
| 1 | 6.088 | 20,29% | 48 |
| 2 | 2.171 | 7,24% | 60 |
| 3 | 2.631 | 8,77% | 56 |
| 4 | 4.916 | 16,39% | 54 |
| 5 | 14.194 | 47,31% | 33 |

**Nhận xét:** gần một nửa số bài có 5 sao; nhóm 2–4 sao có trung vị độ dài lớn hơn nhóm 5 sao. Bài viết có ý kiến đan xen có thể cần giải thích dài hơn, nhưng số sao không xác định chắc chắn nội dung cảm xúc.

Ánh xạ nhãn đại diện (proxy label, nhãn suy từ số sao): 1–2 sao → negative (tiêu cực), 3 sao → neutral (trung tính), 4–5 sao → positive (tích cực). Tương ứng có 8.259 bài (27,53%), 2.631 bài (8,77%) và 19.110 bài (63,70%). Tích cực nhiều gấp khoảng 7,2634 lần trung tính. Vì mất cân bằng lớp, cần xem macro F1 (F1 trung bình đều giữa các lớp) và thước đo từng lớp khi so mô hình, không chỉ accuracy (tỷ lệ dự đoán đúng chung). P3 không chọn trọng số hoặc lấy mẫu lại để xử lý mất cân bằng.

Trung vị số từ của ba nhóm tiêu cực/trung tính/tích cực là 50/56/37; toàn bộ là 43 từ, p90 (mốc 90% bài không vượt quá) là 200 từ. Chênh lệch độ dài có thể ảnh hưởng việc so tần suất từ. Bảng `length_by_sentiment.csv` lưu phân vị theo ký tự, từ và đơn vị tách bằng biểu thức chính quy.

## 3. Thay đổi theo thời gian

Dấu thời gian theo UTC (giờ chuẩn quốc tế) từ 2001-10-23 đến 2023-09-07; không có lỗi đọc dấu thời gian trong bộ cuối. Tên nguồn Amazon Reviews 2023 không có nghĩa mọi bài được viết năm 2023. Bảng năm/tháng có số bài, số sao trung bình và phân bố nhãn; biểu đồ chỉ hiển thị tỷ lệ khi nhóm có ít nhất 100 bài.

Nhóm năm 2014 có 415/2.129 bài tiêu cực (19,49%); năm 2022 là 853/2.733 (31,21%); năm 2023 là 431/1.364 (31,60%). Thành phần mẫu thay đổi, nhưng chưa đủ căn cứ nói chất lượng laptop giảm: thế hệ sản phẩm, thương hiệu, tuổi bài, nguồn thu thập và cách làm sạch/lấy mẫu/giới hạn số bài đều có thể góp phần.

Chỉ những tháng có bài mới xuất hiện trên biểu đồ. Không coi khoảng trống tháng là doanh số bằng 0. Đầu/cuối giai đoạn, đặc biệt năm 2023, chỉ là dữ liệu một phần; không ngoại suy thành số liệu cả năm hoặc doanh số.

## 4. Từ vựng và giả thuyết khen/chê

| Từ/cụm từ và nhóm | Tỷ lệ trong nhóm | Tỷ lệ ngoài nhóm | Diễn giải có giới hạn |
|---|---:|---:|---|
| stopped working (đã ngừng hoạt động), tiêu cực | 397/8.259 = 4,81% | 92/21.741 = 0,42% | Gợi ý kiểm tra lỗi vận hành/vòng đời |
| to return (để trả lại), tiêu cực | 449/8.259 = 5,44% | 202/21.741 = 0,93% | Gợi ý kiểm tra trả hàng/dịch vụ |
| slow (chậm), tiêu cực | 926/8.259 = 11,21% | 784/21.741 = 3,61% | Gợi ý khiếu nại về hiệu năng |
| battery life (thời lượng pin), tích cực | 2.107/19.110 = 11,03% | 473/10.890 = 4,34% | Pin được nhắc nhiều, chưa suy cảm xúc riêng về pin |
| the price (giá), tích cực | 2.030/19.110 = 10,62% | 459/10.890 = 4,21% | Gợi ý chủ đề giá/giá trị |
| i guess (tôi đoán/tôi nghĩ), trung tính | 86/2.631 = 3,27% | 294/27.369 = 1,07% | Có thể là lối diễn đạt dè dặt, chưa xác nhận cảm xúc thật |

**Nhận xét:** một số cụm về ngừng hoạt động, trả hàng và tốc độ phổ biến hơn trong lớp tiêu cực. Tuy nhiên đây là liên hệ giữa từ vựng với nhãn cả bài; một cụm có thể xuất hiện trong so sánh hoặc phủ định nên chưa thay thế mô hình cảm xúc theo khía cạnh.

Từ not (không; phủ định) có trong 11.170 bài (37,23%), củng cố việc giữ phủ định khi tiền xử lý. Bảng `frequent_terms.csv` chứa từ đơn và cụm 2–3 từ. Không coi số bài chứa từ là số khía cạnh được trích xuất.

Tất cả 9 chủ đề giả thuyết được kiểm tra bằng từ điển có phiên bản, không chỉ giữ chủ đề khớp kỳ vọng: hiệu năng 8.450 bài (28,17%), màn hình 7.725 (25,75%), giá 6.548 (21,83%), bàn phím 5.270 (17,57%), pin 4.655 (15,52%), tính di động 3.611 (12,04%), lưu trữ 3.225 (10,75%), nhiệt độ/tiếng ồn 2.414 (8,05%), kết cấu 1.568 (5,23%).

Một bài có thể nhắc nhiều chủ đề; tỷ lệ không cộng thành 100%. Các từ hot (nóng), keys (phím/chìa khóa), value (giá trị) có thể đa nghĩa; từ đồng nghĩa và khía cạnh ngầm có thể bị bỏ sót. Precision/recall (độ chính xác/độ bao phủ) của từ điển chưa được con người xác thực. Đây chưa phải ATE/ASC (trích xuất cụm từ khía cạnh/phân loại cảm xúc khía cạnh).

Các trích đoạn thực tế trong bảng giúp phân biệt cảm xúc cả bài và từng khía cạnh:

- Có bài tiêu cực nêu quảng cáo pin 8 giờ nhưng thực tế khoảng 1 giờ; ngữ cảnh hiệu năng có câu Very slow not a good value (rất chậm, không đáng tiền).
- Có bài tích cực vẫn viết The battery doesn't last long (pin không dùng được lâu) khi phát video, nhưng đủ cho viết/email; có bài tích cực so sánh với laptop cũ chạy chậm.
- Có bài nhãn trung tính khen giá nhưng phàn nàn Windows 10 S và giới hạn ứng dụng.

**Nhận xét:** một bài có thể vừa khen vừa chê. Không gán mọi khía cạnh theo số sao hoặc nhãn tổng thể; P9 cần phân loại có điều kiện theo khía cạnh. Việc đọc trích đoạn bằng máy không tạo nhãn con người hoặc ước lượng tỷ lệ nhiễu thật. Ví dụ được chọn theo ID để chẩn đoán, không đại diện cho tần suất khiếu nại.

## 5. Lượt hữu ích và giao dịch mua đã xác minh

Trung vị lượt đánh dấu hữu ích là 0, lớn nhất 1.398; 49,26% bài có ít nhất 1 lượt. Tương quan thứ hạng Spearman giữa lượt hữu ích và số từ là 0,3841. Lượt hữu ích trung bình theo lớp tiêu cực/trung tính/tích cực là 2,842/3,671/3,265; trung vị là 1/1/0. Bảng số sao cũng lưu trung bình và trung vị lượt hữu ích.

**Nhận xét:** bài dài có xu hướng nhận nhiều lượt hữu ích hơn trong mẫu, nhưng chưa kiểm soát thời gian tồn tại, mức độ được xem và độ phổ biến sản phẩm. Không coi lượt hữu ích là nhãn chất lượng do con người xác nhận.

Có 26.350 bài từ giao dịch mua đã xác minh (87,83%) và 3.650 bài chưa xác minh (12,17%). Tỷ lệ tiêu cực tương ứng 26,28% và 36,58%, chênh 10,30 điểm phần trăm; trung vị độ dài là 38 và 102 từ; lượt hữu ích trung bình là 2,873 và 5,428. Đây là liên hệ mô tả, không chứng minh bài chưa xác minh là giả hoặc xác minh giao dịch làm cảm xúc tích cực hơn. Không loại nhóm chưa xác minh sau EDA.

## 6. Thương hiệu và sản phẩm

Năm nhóm HP/ASUS/Acer/Lenovo/Dell chiếm 79,46% số bài; 18 nhóm có ít nhất 100 bài. Trong mẫu này, tỷ lệ tiêu cực của Dell là 1.150/3.573 (32,19%), Acer 934/4.197 (22,25%), HP 1.888/6.141 (30,74%), ASUS 1.623/6.038 (26,88%), Lenovo 1.136/3.888 (29,22%).

**Nhận xét:** dữ liệu tập trung vào vài nhóm thương hiệu. Chênh lệch nhãn có thể liên quan tới dòng máy, máy cũ/tân trang, tuổi bài và cách chọn mẫu; không phải thị phần, đánh giá công bằng giữa hãng hoặc xếp hạng chất lượng nhà sản xuất. Phân bố thương hiệu trước/sau P2 đã được đo riêng; không áp hạn ngạch mới.

Sản phẩm B00N3ODBBA có 16/30 bài tiêu cực (53,33%), khoảng tin cậy Wilson 95% là 36,14–69,77%; B01JLCKP1Q có 24/46 (52,17%), khoảng 38,14–65,88%. Không xếp hạng cả 9.080 sản phẩm khi phần lớn nhóm quá nhỏ. Khoảng tin cậy giả định các quan sát nhị thức độc lập; chưa điều chỉnh nhóm sản phẩm/người dùng, so sánh nhiều nhóm, thiên lệch chọn mẫu hoặc nhiễu nhãn. Đây không phải confidence (độ tin cậy) được hiệu chuẩn của mô hình và khác khoảng tin cậy theo thiết kế QA ở P1.

Giới hạn siêu dữ liệu được tái sử dụng: 70 giá trị thương hiệu thô bị thiếu (0,23%); 80 giá trị chuẩn hóa chưa xác định/mơ hồ (0,27%). Có 664 sản phẩm từng được gắn cờ siêu dữ liệu/tiêu đề trước P2, không đồng nghĩa 664 sản phẩm đã xác nhận lọc sai. Không xác minh lại hãng/thông số hoặc khẳng định hiệu năng phần cứng từ dữ liệu chưa có.

## 7. Chất lượng dữ liệu và nhãn nghi nhiễu

| Thước đo | Nhóm ứng viên | Bộ cuối P2 | Giới hạn so sánh |
|---|---:|---:|---|
| Hàng dư do trùng hoàn toàn ở dữ liệu thô | 25.747/408.480 = 6,30% | Không tính lại cùng phép đo | Bằng chứng kiểm tra trước được giữ nguyên |
| Hàng dư do trùng sau chuẩn hóa trước | 27.807/408.480 = 6,81% | 0 hàng dư theo hàm băm văn bản sạch/30.000 | Khác chuẩn hóa/phạm vi, không phải cùng một ước lượng |
| Bài dưới 5 từ | 38.419/408.480 = 9,41% | 424/30.000 = 1,41% | Loại trùng/chọn mẫu làm thay đổi phân bố; vẫn giữ bài ngắn hợp lệ |
| Thiếu trường bắt buộc | 0 trong nhóm hợp lệ | 0 ở trường bắt buộc của bộ cuối | Bản ghi nguồn sai định dạng nằm ngoài nhóm hợp lệ |
| Thiếu mã nhóm gần trùng | Không áp dụng | 30.000/30.000 | Chưa gán nhóm, không phải lỗi nối siêu dữ liệu |

**Nhận xét:** bộ cuối không có ID hoặc hàm băm văn bản sạch bị trùng dư và vẫn còn bài ngắn hợp lệ. Không được so các tỷ lệ trước/sau như cùng một phép đo khi mẫu số và chuẩn hóa khác nhau; cũng chưa chứng minh đã hết gần trùng về ngữ nghĩa.

Bảng dữ liệu thiếu kiểm tra mọi cột và phân biệt null (giá trị thiếu) với chuỗi rỗng, không khẳng định mọi siêu dữ liệu đều đầy đủ. Kiểm tra gần trùng từ vựng xấp xỉ của P2 có 34 cặp ứng viên được so, không có cặp đạt Jaccard ≥ 0,9; bỏ qua văn bản dưới 10 từ. Không chứng minh tìm kiếm ngữ nghĩa toàn diện. Giữ nguyên cờ P2, không làm sạch hoặc loại hàng sau khi xem EDA.

`noise_examples.csv` có 12 ví dụ từ 250 ứng viên nghi nhiễu chưa gán nhãn, được dành riêng và không nằm trong bộ cuối 30.000 bài. Có bài 5 sao vẫn chê RAM, lưu trữ hoặc pin; dấu hiệu từ vựng không phân biệt chắc chắn ý kiến đan xen với số sao sai. Không tự đổi nhãn, suy ma trận nhầm lẫn hoặc tỷ lệ nhiễu từ nhóm này. Một bài nhắc điện thoại, máy tính bảng hay phụ kiện không tự thay phạm vi laptop đã nối với sản phẩm.

## 8. Bằng chứng kiểm tra và khả năng tái lập

P3-T01–T08 được nghiệm thu trong phạm vi mô tả dữ liệu. Bằng chứng lịch sử tại `notebook_validation.json` ghi notebook 6 ô mã chạy từ kernel mới, đối chiếu bảng với CSV và kiểm tra hàm băm nguồn/đầu ra; 41 tệp được bảo vệ và parquet không đổi tại thời điểm đó. Không sửa dữ liệu thô/XML/JSONL, nhãn hoặc nguồn gốc nhãn; không thực hiện mô hình/chia tập/gold trong P3. Kiểm tra kỹ thuật SemEval được tái sử dụng khi nội dung không đổi.

Bằng chứng cũ tại `reports/p3/20261009_verified/task_validation.json` ghi 169 kiểm thử đạt trong 6,40 giây, gồm 8 kiểm thử P3 bằng dữ liệu mẫu; kiểm tra phụ thuộc đạt. Đây là kết quả lúc nghiệm thu P3, không phải tuyên bố chạy lại trong lần biên tập báo cáo này. Sửa văn bản/chú thích về sau có thể đổi hàm băm tệp nguồn; không ghi lại bản kê cũ để che thay đổi.

Nếu chủ động tái lập P3, dùng thư mục đầu ra mới, không ghi đè:

```powershell
.venv\Scripts\python.exe -B -m scripts.analyze_p3 --output-dir reports/p3/NEW_RUN
.venv\Scripts\python.exe -B -m scripts.execute_p3_notebook --output reports/p3/NEW_EXECUTED.ipynb
```

Notebook hiện đọc thư mục bảng đã xác minh; đổi đường dẫn đầu ra trong ô cấu hình nếu so với lần chạy mới. Không cần tải lại nguồn hoặc làm QA lại chỉ để đọc báo cáo.

## 9. Giới hạn và trạng thái

Kết luận chỉ dành cho laptop; nhãn suy từ số sao có nhiễu; SemEval và Amazon khác nền tảng/phong cách trong cùng phạm vi laptop; bộ kiểm thử chuẩn thủ công dự kiến nhỏ và P10 hiện chưa có. Độ chính xác thật của nhận diện ngôn ngữ, spam, nhiễu cảm xúc và mức gần trùng ngữ nghĩa toàn diện chưa được đo.

Recall (độ bao phủ) QA được báo cáo là 89,08%, khoảng tin cậy đồng thời 95% là 55,46–99,85%; vẫn có thiên lệch chọn mẫu và giới hạn đánh giá có AI hỗ trợ. Nguồn/giấy phép SemEval chưa được xác minh (NOT_VERIFIED), được dùng theo ngoại lệ giáo dục của chủ dự án; không phải xác nhận giấy phép hợp lệ.

Tại thời điểm P3, bước tiếp theo là P4 chia tập/kiểm tra rò rỉ và tiền xử lý riêng cho mô hình cổ điển/BERT. Trạng thái hiện hành phải xem PLAN và bàn giao: không suy rằng P4 vẫn chưa bắt đầu chỉ vì đọc báo cáo P3. Giữ phân vùng SemEval gốc, thông tin 227 ID câu giao nhau và 12 nhóm trùng trong tập huấn luyện đã được ghi nhận trước đó; không kiểm tra lại chúng trong lần biên tập này.
