# P2 — tái xác minh dữ liệu

Trạng thái: PASS

Nhãn đại diện suy từ số sao, không phải human sentiment gold. Không làm sạch/relabel lại.

Bằng chứng: `p2_revalidation_for_new_models.json`.

Các trường rating/stars/score/label/target và ID không được làm feature. Pipeline mới chỉ nhận văn bản title/body, rồi dense embedding; metadata lưu riêng.

Giới hạn: chỉ laptop; nhiễu nhãn từ số sao; thay đổi nền tảng/phong cách SemEval–Amazon; gold thủ công nhỏ, hiện chưa có.
