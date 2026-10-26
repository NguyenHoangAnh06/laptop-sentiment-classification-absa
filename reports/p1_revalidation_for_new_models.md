# P1 — tái xác minh dữ liệu

Trạng thái: PASS

P1 REUSED AS-IS. Không tải/lọc lại; hash hai nguồn khớp manifest và toàn bộ sản phẩm có trong metadata đã lưu.

Bằng chứng: `p1_revalidation_for_new_models.json`.

Các trường rating/stars/score/label/target và ID không được làm feature. Pipeline mới chỉ nhận văn bản title/body, rồi dense embedding; metadata lưu riêng.

Giới hạn: chỉ laptop; nhiễu nhãn từ số sao; thay đổi nền tảng/phong cách SemEval–Amazon; gold thủ công nhỏ, hiện chưa có.
