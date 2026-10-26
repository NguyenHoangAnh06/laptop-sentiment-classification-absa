# P3 — Tóm tắt nhận định từ dữ liệu (insight)

P3 đã hoàn thành phân tích khám phá dữ liệu (EDA) trên bộ cố định gồm **30.000 bài đánh giá laptop**. Các số liệu dưới đây lấy từ kết quả P3 ngày 2026-10-09; phần trình bày được biên tập lại ngày 2026-10-20. Không chạy lại xử lý dữ liệu hoặc huấn luyện mô hình.

- **Nhãn mất cân bằng:** tích cực (positive) chiếm 63,70%, trung tính (neutral) chỉ 8,77%, còn tiêu cực (negative) là 27,53%. Nhãn được suy từ số sao, không phải nhãn cảm xúc do con người gán.
- **Độ dài khác nhau giữa các lớp:** trung vị (median, giá trị ở giữa khi sắp xếp) là 50/56/37 từ cho nhóm tiêu cực/trung tính/tích cực. Trung vị toàn bộ là 43 từ. Nhóm trung tính dài hơn trong mẫu này, nhưng không thể chỉ từ đó khẳng định nội dung thật sự trung tính.
- **Dấu hiệu khiếu nại:** stopped working (đã ngừng hoạt động) có trong 4,81% bài tiêu cực, so với 0,42% phần còn lại; to return (để trả lại) là 5,44% so với 0,93%; slow (chậm) là 11,21% so với 3,61%. Đây là căn cứ đặt giả thuyết về lỗi vận hành, trả hàng và hiệu năng.
- **Dấu hiệu thường gặp trong bài tích cực:** battery life (thời lượng pin) xuất hiện ở 11,03%, so với 4,34% phần còn lại; the price (giá) là 10,62%, so với 4,21%. Nhắc đến một khía cạnh trong bài tích cực không đồng nghĩa khen khía cạnh đó.
- **Chủ đề được nhắc nhiều:** hiệu năng 28,17%, màn hình 25,75%, giá 21,83%, theo từ điển gồm 9 nhóm giả thuyết. Một bài có thể thuộc nhiều nhóm. Đây chưa phải trích xuất khía cạnh hoặc phân loại cảm xúc theo khía cạnh (ABSA).
- **Thành phần mẫu thay đổi theo thời gian:** tỷ lệ nhãn tiêu cực năm 2014 là 19,49%, năm 2022 là 31,21%. Không đủ căn cứ kết luận chất lượng laptop giảm vì loại sản phẩm, tuổi bài và cách lấy mẫu cùng khác nhau; số bài không phải doanh số.
- **Giao dịch mua đã xác minh:** chiếm 87,83% số bài. Tỷ lệ tiêu cực ở nhóm này là 26,28%, so với 36,58% nhóm chưa xác minh; trung vị độ dài tương ứng 38 và 102 từ. Không thể dùng chênh lệch đó để kết luận nhóm chưa xác minh là bài giả.
- **Lượt hữu ích và độ dài có liên hệ:** hệ số tương quan thứ hạng Spearman là 0,3841. Bài dài có xu hướng nhận nhiều lượt đánh dấu hữu ích hơn trong mẫu, nhưng chưa kiểm soát tuổi bài, mức độ được xem hoặc độ phổ biến sản phẩm; không suy quan hệ nhân quả.
- **Dữ liệu tập trung và nhiều nhóm ít mẫu:** 5 nhóm thương hiệu dẫn đầu chiếm 79,46% số bài; 5.025/9.080 sản phẩm chỉ có một bài, chỉ 115 sản phẩm có ít nhất 30 bài. Không xếp hạng chất lượng hãng hoặc suy thị phần từ các thống kê này.
- **Kiểm tra chất lượng có giới hạn:** có bảng dữ liệu thiếu, thống kê trùng/ngắn và 12 ví dụ nghi nhiễu từ nhóm dành riêng. Không tự đổi nhãn, không tạo nhãn chuẩn thủ công và không ước lượng tỷ lệ nhiễu thật từ nhóm chẩn đoán có chủ đích.

Phương pháp và giới hạn chi tiết nằm trong `reports/p3_data_analysis_20261009.md`; 15 bảng và 7 biểu đồ gốc ở `reports/p3/20261009_verified/`. Báo cáo tổng hợp bổ sung nhận xét dưới từng bảng/biểu đồ; các nhận xét không thay thế việc con người gán nhãn độc lập.

**Giới hạn bắt buộc:** kết luận chỉ dành cho laptop; nhãn suy từ số sao có nhiễu; SemEval và Amazon khác nền tảng/phong cách trong cùng phạm vi laptop; bộ kiểm thử chuẩn thủ công (human gold test) dự kiến nhỏ và P10 hiện chưa có. Nguồn/giấy phép SemEval vẫn NOT_VERIFIED (chưa xác minh), được dùng theo ngoại lệ giáo dục của chủ dự án. Trạng thái triển khai hiện hành xem PLAN và bàn giao, không suy từ báo cáo lịch sử P3.
