# Đánh giá QA con người độc lập

Trạng thái: ANNOTATION_COMPLETE_REVIEW_REQUIRED Chú thích: human_reviewer_01; xuất xứ: human_verified_after_ai_assistance

con người đã xác nhận review và phê duyệt sau khi có đề xuất của AI; không hoàn toàn mù gán nhãn. Cổng độc lập yêu cầu review riêng biệt.

| tầng | N | n | TP | FP | FN | TN | trống | không chắc chắn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sản phẩm:random_keep | 28172 | 150 | 150 | 0 | 0 | 0 | 0 | 0 |
| sản phẩm:chẩn đoán | 164453 | 50 | 1 | 0 | 2 | 47 | 0 | 0 |
| review:random_keep | 408480 | 150 | 150 | 0 | 0 | 0 | 0 | 0 |
| review:random_reject | 43478204 | 150 | 0 | 0 | 1 | 149 | 0 | 0 |
| review:chẩn đoán | 80721 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |

Số liệu có trọng số thiết kế review (null có nghĩa là chưa thể ước tính):

```json
{
  "confusion_matrix": {
    "TP": 408480.0,
    "FP": 0.0,
    "FN": 289854.69333333336,
    "TN": 43188349.306666665
  },
  "precision": 1.0,
  "recall": 0.5849344217028923,
  "f1": 0.7381181374992468
}
```

Sản phẩm ngẫu nhiên GIỮ độ chính xác dự đoán (precision): 1.0

Sản phẩm xung đột nhãn: []

Trong tầng review đại diện h, hãy sử dụng N_h/n_h cho mỗi bản ghi đã được giải quyết. Giữ lại tổng thể precision/recall/F1 cho đến khi tất cả các tầng ngẫu nhiên được giải quyết và không có sản phẩm xung đột nhãn. Hàng chẩn đoán không bao giờ nhập ước tính. Ước tính là ước tính điểm theo trọng số thiết kế, không phải số lượng quần thể chính xác hoặc khoảng độ tin cậy.

Khung sản phẩm ngẫu nhiên: sản phẩm KEEP đã lưu. Khung review suy luận: KEEP đã lưu hợp lệ cộng với tất cả các bản ghi nguồn TỪ CHỐI siêu dữ liệu không được chọn. Loại trừ các bản ghi đã chọn nhưng không hợp lệ; không ước tính độ bao phủ (recall) của toàn bộ quy trình có hiệu lực cuối cùng nguồn thô. Khung review chẩn đoán chỉ ở chế độ GIỮ; không phải là tìm kiếm negative sai.

FP = GIỮ dự đoán / con người non_laptop; FN = TỪ CHỐI dự đoán / con người laptop. Các hàng nhầm lẫn là sự thật con người, quyết định đường ống cột. Việc lấy mẫu chỉ GIỮ sản phẩm không thể ước tính recall/F1. Trống và không chắc chắn vẫn chưa được giải quyết; giới hạn cho các phân số tầng laptop nằm trong evaluation.json. Nguyên nhân lỗi đến từ human_error_reason; nguyên nhân không khớp không được giải quyết sẽ không được phân loại, không bao giờ được AI suy ra.

Việc chấp nhận P1 yêu cầu review có bằng chứng và phán quyết; không có danh sách kiểm tra nào được thay đổi tự động.

Hạn chế: Chỉ phát hiện được laptop; Amazon nhãn đại diện suy từ số sao-nhiễu nhãn (không được đánh giá ở đây); Sự thay đổi SemEval-to-Amazon platform/style trong laptop review (không được đánh giá ở đây); bộ dữ liệu gold được chú thích thủ công nhỏ (QA này không phải là sentiment/ABSA gold); Xuất xứ con người tự khai; chữ viết không thể chứng minh tính độc lập. Không có cổng kế hoạch tự động hoàn thành..
