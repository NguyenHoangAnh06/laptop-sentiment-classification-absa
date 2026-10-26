> LEGACY: bằng chứng2026-10-15, Việt hóa2026-10-19. Tra [chỉ mục hiện hành](PROJECT_INDEX.md), [benchmark semantic](MODEL_STACK_REFACTOR.md) và [kế hoạch cloud](TABPFN_CLOUD_PLAN.md); không dùng trạng thái trong tài liệu này làm tiến độ mới.

# Hợp đồng tệp mô hình cảm xúc cổ điển P5

P5 phụ trách majority/LR/Linear SVM/Decision Tree; BERT thuộc P6. Lần chạy hiện hành: `artifacts/models/p5_20261015/`; bằng chứng ở `reports/p5/p5_20261015/`. Dùng `.venv` đã ghim scikit-learn 1.7.2, không dùng Python mặc định của máy.

## Tái lập và đánh giá

```powershell
.\.venv\Scripts\python.exe -B -m scripts.train_p5
.\.venv\Scripts\python.exe -B -m scripts.validate_p5
```

Huấn luyện từ chối mọi thư mục đầu ra đã tồn tại. Muốn chủ động chạy lại, sao chép `configs/p5.yaml`, chỉ đổi `output_suffix` sang giá trị mới và truyền `--config`. Đây là chạy lại giao thức cố định; không dùng kết quả test để thay tham số/lưới tìm kiếm. Không tải dữ liệu, chạy lại chuẩn bị P0–P4, khớp lại tiền xử lý hoặc huấn luyện BERT.

Ma trận CSR P4 cố định được đối chiếu với phép biến đổi văn bản và tệp phụ mục tiêu theo đúng thứ tự. Từ vựng/IDF vẫn chỉ được khớp trên 21,000 review train gốc. Mọi ứng viên chỉ khớp train; macro F1 validation chọn mô hình mỗi họ và mô hình thắng chung. Nếu bằng điểm chính xác, theo thứ tự lưới/họ đã khai báo. Ứng viên không hội tụ không đủ điều kiện. Trọng số lớp chỉ tính từ mục tiêu train. Không khớp lại trên train+validation. `selection_lock.json` ghi lựa chọn và hàm băm mô hình trước lượt dự đoán test duy nhất của mỗi họ được chọn.

`training_history.json` lưu tham số, thước đo train/validation, cảnh báo, thời gian khớp và RAM tiến trình lấy mẫu của mọi ứng viên. `benchmark.csv` so sánh các mô hình được chọn trên cùng 4,500 hàng test. Thước đo từng lớp và ma trận nhầm lẫn (hàng là nhãn thật, cột là dự đoán; thứ tự negative/neutral/positive) ở `metrics.json` và các CSV tương ứng. Có thể tính lại độc lập từ dự đoán test đã lưu mà không dự đoán test lần nữa.

Các cột thời gian phân biệt thời gian khớp mô hình được chọn, tổng thời gian khớp mọi ứng viên, dự đoán test theo lô và suy luận văn bản từ đầu đến cuối. Đo suy luận trên lô validation cố định 128 mẫu, khởi động một lần, lặp năm lần; lấy **trung vị** thời gian lô chia số review. Phép đo gồm chuẩn hóa/TF-IDF/phân loại, không gồm tải đĩa; đây là độ trễ bình quân theo lô, không phải độ trễ yêu cầu đơn lẻ.

RAM là RSS toàn tiến trình, lấy mẫu mỗi 20 ms, gồm đầu vào dùng chung/cấp phát trước; không phải bộ nhớ riêng của bộ phân loại. Giới hạn là kiểm tra mềm giữa các thao tác có giới hạn, không phải trần hệ điều hành cưỡng chế. GPU VRAM không áp dụng cho mô hình CPU này. Kích thước tệp mô hình không gồm tiền xử lý dùng chung; `inference_artifact_bytes` có tính phần đó.

## Tải mô hình để suy luận

```python
from pathlib import Path
import pandas as pd
from src.config import PROJECT_ROOT
from src.sentiment.classical import load_classical

artifact = load_classical(
    PROJECT_ROOT / "artifacts/models/p5_20261015/logistic_regression", PROJECT_ROOT
)
predictions = artifact.predict(pd.DataFrame({
    "text": ["The battery does not last long."], "language": ["en"]
}))
```

Ví dụ thực thi mô hình, không khẳng định sẵn nhãn hay điểm số đầu ra. Chỉ `text` là biến dự đoán. Ngôn ngữ tùy chọn phải là `en`; thiếu/rỗng văn bản sẽ báo lỗi. Nhãn đúng ba giá trị negative/neutral/positive. Confidence null vì chưa hiệu chuẩn. Aspects rỗng vì P5 chỉ có cảm xúc tổng thể; ABSA được tích hợp trong giai đoạn riêng. Đơn lẻ/hàng loạt dùng cùng `predict(frame)`; không thêm huấn luyện vào Streamlit/ứng dụng.

Mỗi thư mục họ có `model.joblib` và `metadata.json`. Siêu dữ liệu gắn nội dung mô hình, ID nhãn, mã băm ID train, tham số, hạt giống, phiên bản sklearn và đường dẫn/hàm băm `tfidf.joblib` P4 gốc. Khi chuyển dự án phải giữ tệp dùng chung đó; không tạo bản sao bộ vector hóa dư thừa. Chỉ tải joblib đáng tin trong môi trường phụ thuộc đã ghi. Cấu hình, môi trường, nguồn gốc và hàm băm lưu riêng với đối tượng mô hình.

## Diễn giải

Chẩn đoán lỗi diễn ra sau lựa chọn đã cố định. Cờ từ vựng và nhóm độ dài cố định là chỉ báo mô tả, không phải nhãn con người, bộ nhận diện mỉa mai đã xác thực hoặc bất đồng số sao–văn bản đã xác nhận. Tệp cục bộ bị Git bỏ qua `error_review_queue.parquet` chứa văn bản chẩn đoán lấy mẫu tái lập, không phải dữ liệu huấn luyện/human gold. Không dùng để điều chỉnh lại lần chạy đã đánh giá. Phân tích P7 chi tiết vẫn là giai đoạn riêng về sau.

Giới hạn: **kết luận chỉ cho laptop**, **nhiễu nhãn suy từ số sao**, **khác biệt nền tảng/phong cách SemEval–Amazon trong review laptop**, **bộ gold thủ công nhỏ, P10 độc lập hiện chưa có**. Không trùng sản phẩm không đồng nghĩa chưa thấy thương hiệu/người dùng hoặc đại diện thị phần. Đồng thuận với nhãn suy từ số sao không xác lập accuracy cảm xúc thật theo con người. Giữ nguyên ngoại lệ giấy phép SemEval và nguồn gốc hiện có. Không khẳng định sẵn sàng vận hành thực tế hoặc khái quát sang thiết bị khác.
