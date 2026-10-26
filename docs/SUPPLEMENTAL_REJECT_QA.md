# Cập nhật đánh giá hiện hành — 2026-10-09

`human_reviewer_01` đã hoàn tất đánh giá/phê duyệt thủ công cuối cùng; không yêu cầu xác nhận lại. Giữ nguyên CSV ACCEPT/REJECT được nộp và bản dẫn xuất chuẩn hóa. Đánh giá chính thức đã hoàn thành tại `reports/independent_qa/p1_v2_evaluation_20261009/`: recall kết hợp 89.0767%, khoảng tin cậy đồng thời 95% 55.4584–99.8455%. Không tự động nghiệm thu; lịch sử AI của v2 chưa được chỉ rõ.

Bộ đánh giá nhận `--review-annotations` gắn với `--review-confirmation` và `--ai-history-unspecified` để không khẳng định lịch sử đánh giá độc lập/mù. Cách tái lập xem `reports/p1_qa_v2_completion_20261009.md`. Hướng dẫn chuẩn bị dưới đây là tài liệu lịch sử của bộ đã hoàn thành; không tạo lại nhãn.

# P1 v2 — QA thủ công bổ sung trên nhóm REJECT

**SẴN SÀNG CHO CON NGƯỜI GÁN NHÃN: 868 review mới. Không có nhãn con người nào được tạo tự động.** Đây là hướng dẫn chuẩn bị lịch sử; trạng thái đánh giá hiện hành xem `docs/SUPPLEMENTAL_REJECT_QA.md` và `reports/p1_qa_v2_completion_20261009.md`. Không tạo lại bộ đã hoàn thành.

Chỉ mở `data/manual/independent_qa/p1_v2/review_annotation.csv` để gán nhãn. Không mở `private_predictions.json` hoặc `manifest.json` trong lúc gán nhãn; không xem nhãn v1 hoặc dùng AI để quyết định nhãn mới. Nếu cần nguồn, tự đọc siêu dữ liệu trong CSV và nguồn hãng/mẫu máy đáng tin cậy; ghi đúng nguồn đã xem. Mọi URL sản phẩm chỉ là gợi ý tra cứu chưa xác minh, không phải bằng chứng xác nhận loại sản phẩm.

## Cách điền

Giữ UTF-8, đọc ID dưới dạng văn bản. Chỉ sửa bốn cột `human_label`, `human_evidence`, `human_notes`, `human_error_reason`. Giữ nguyên ID, nội dung, siêu dữ liệu và trường nguồn; không sắp xếp riêng một cột. Nhãn hợp lệ: `laptop`, `non_laptop`, `uncertain`. Không đủ bằng chứng thì dùng `uncertain`; không ép thành `non_laptop`.

Mọi nhãn đã điền **bắt buộc có bằng chứng không rỗng**. Khuyến nghị ghi ngày/ghi chú, nhưng đây không phải điều kiện kiểm tra bắt buộc. Chỉ dùng bằng chứng `Amazon title + category` khi thực sự tự kiểm tra và đủ căn cứ. Mã lý do và tiêu chí chi tiết theo `docs/INDEPENDENT_HUMAN_QA.md`.

Laptop/notebook/Chromebook hoàn chỉnh và laptop chuyển đổi/2-in-1 thực sự thuộc phạm vi. Phụ kiện, máy tính để bàn và thiết bị chỉ là máy tính bảng nằm ngoài phạm vi. Nội dung nói dùng với laptop không chứng minh sản phẩm được đánh giá là laptop. Không dùng số sao/ngôn ngữ làm nhãn phạm vi. Nếu thiếu siêu dữ liệu hoặc liên kết review–sản phẩm không rõ, ghi giới hạn hoặc `uncertain`. Đây là QA phạm vi sản phẩm, không phải gán nhãn cảm xúc hay ABSA.

## Thiết kế lấy mẫu và tính độc lập

868 bản ghi được lấy mẫu ngẫu nhiên đơn từ phần còn lại của REJECT sau khi loại 150 mẫu REJECT ngẫu nhiên v1; N=43.478.054. Không trùng bất kỳ review v1 nào. Không có mẫu chẩn đoán mới. Tệp phụ lưu xác suất/trọng số; CSV không hiển thị dự đoán hoặc tầng lấy mẫu.

Việc tất cả mẫu thuộc REJECT là thông tin đã biết của thiết kế, nên không mô tả bộ này như kiểm thử KEEP/REJECT trộn hoàn toàn mù. Khuyến nghị người đánh giá thứ hai chưa xem gợi ý AI/nhãn v1; việc này chưa được thực hiện, không giả lập công việc con người. Nhãn v1 vẫn có nguồn gốc là con người xác minh sau gợi ý AI. V2 không tự làm v1 thành đánh giá mù và không tự hoàn tất điều kiện QA sản phẩm độc lập.

868 là phương án dung hòa ngân sách có tính toán, không bảo đảm đạt mục tiêu precision/recall. Xem khoảng tin cậy 95% và giả định lập kế hoạch trong `reports/p1_recall_reliability.md`.

## Sau khi hoàn thành và xác nhận đánh giá thủ công

Không chạy lệnh dưới trước khi có nhãn thật và xác nhận của người đánh giá:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_supplemental_qa --kit-dir data/manual/independent_qa/p1_v2 --annotator TEN_HOAC_MA_HUMAN --confirm-human-review --output-dir reports/independent_qa/p1_v2_evaluation
```

Nếu đã tham khảo AI, phải thêm `--ai-assisted-review`, không che giấu nguồn gốc. Mỗi lần chạy lại cần thư mục đầu ra mới. Không ghi đè bộ nguồn v1/v2 hoặc kết quả đánh giá hiện có. Tập lệnh kiểm tra bằng chứng v1 đã cố định, dấu nhận dạng nguồn v2, nhãn/bằng chứng, ID trùng và nhãn sản phẩm mâu thuẫn. Nhãn trống/không chắc chắn/xung đột khiến ước lượng kết hợp giữ null; không tự điền suy diễn.

Ước lượng kết hợp giữ 150 mẫu REJECT v1 làm đơn vị chắc chắn có trọng số 1; mẫu v2 dùng `43.478.054/868`. KEEP giữ `408.480/150`. Không nối CSV rồi dùng N/(150+868), vì cỡ mẫu v2 được chọn sau khi thấy mẫu thăm dò. Dùng khoảng tin cậy siêu bội trên KEEP ngẫu nhiên và phần REJECT còn lại; kết hợp cận đồng thời Bonferroni rồi tính tỷ số, cộng đúng FN/TN cũ đã biết. Nếu v2 chưa tìm thấy laptop, độ bất định vẫn không bằng 0.

Xuất tỷ lệ laptop và khoảng tin cậy bổ sung, P/R/F1 kết hợp cùng khoảng tin cậy, so sánh thăm dò và lỗi. Không tự cập nhật điều kiện nghiệm thu. Không chạy P2 hoặc huấn luyện.
