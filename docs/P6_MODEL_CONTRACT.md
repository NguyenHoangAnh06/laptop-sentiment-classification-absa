> LEGACY: bằng chứng2026-10-15, Việt hóa2026-10-19. Tra [chỉ mục hiện hành](PROJECT_INDEX.md), [benchmark semantic](MODEL_STACK_REFACTOR.md) và [kế hoạch cloud](TABPFN_CLOUD_PLAN.md); không dùng trạng thái trong tài liệu này làm tiến độ mới.

# Hợp đồng mô hình BERT phân tích cảm xúc tổng thể P6

Phạm vi: chỉ P6-T01–T06. Không có pha P7, ABSA huấn luyện, phân chia mới, thu thập review, đào tạo lại P5 hoặc tạo bộ gold do con người gán nhãn. Cấu hình hiện tại: `configs/p6.yaml`. Chạy hiện tại DONE: vòng huấn luyện3 cân bằng, tập xác thực macro F1=0.7346463550, kiểm thử macro F1=0.7302042742; báo cáo `reports/p6_completion_20261015.md`.

## Đầu vào đã cố định và huấn luyện

P4 `p4_20261009_final` là phiên bản đầu vào duy nhất. Bộ điều hợp sử dụng các mảng token hiện có, duy trì riêng review IDs/labels đã đặt hàng và chỉ hiển thị `input_ids`, `attention_mask`, `token_type_ids`, `labels`. Các bản ghi đầy đủ được kiểm tra dựa trên các mục tiêu phân chia và được mã hóa lại bằng P4 bộ tách token không thay đổi. Kiểm tra cách ly phân chia và băm P4/P5 bản kê. Không khớp tokenizer trên tập dữ liệu hoặc thay chính sách tách token. Độ dài tối đa512 là lựa chọn bắt nguồn từ tập huấn luyện của P4; cắt ngắn bên phải, phần đệm bên phải động CLS101/SEP102/PAD0,. Phủ định và chấm câu vẫn còn nguyên.

Nguồn đã huấn luyện trước là `google-bert/bert-base-uncased`, cùng phiên bản P4 đã ghim `86b5e0934494bd15c9632b12f734a8a67f723594`, khai báo Apache2.0. Chỉ tải `model.safetensors` từ kho Hugging Face chính thức đã ghim; ghi SHA256. Tinh chỉnh toàn bộ tham số mạng nền và đầu phân loại 3 lớp mới. ID nhãn: negative0/neutral1/positive2. Không dùng mẫu SemEval cho huấn luyện cảm xúc tổng thể.

Hạt giống 42; AdamW với tốc độ học 2e-5, weight decay 0.01, lịch giảm/khởi động tuyến tính 10%, cắt chuẩn gradient 1.0; batch 8, tích lũy gradient 4, tối đa 3 vòng mỗi ứng viên, dừng sớm sau 1 vòng macro F1 validation không cải thiện. Mỗi vòng hoàn tất dùng đủ 21,000 mẫu train, không lấy mẫu lại/bỏ hàng. Chia nhóm độ dài chỉ trên train với hạt giống cố định để giảm đệm; xáo trộn nhóm/lô mỗi vòng. Nhóm tích lũy cuối dùng số microbatch thực tế. Trọng số là n_train/(3*class_count), không tính từ tập giữ lại. Hai ứng viên: CE không trọng số và CE cân bằng tính từng mẫu rồi lấy trung bình theo lô. Trọng số của phương án sau có kỳ vọng 1 dưới phân bố train gốc; không chuẩn hóa theo tổng trọng số mỗi microbatch. CE validation luôn không trọng số để so sánh được. AMP FP16 chỉ cho huấn luyện CUDA; validation/test/suy luận mô hình đã xuất dùng FP32. Gradient checkpointing giảm VRAM.

tập xác thực macro F1 chọn vòng huấn luyện tốt nhất của từng ứng viên và sau đó là chế độ hàm mất mát chiến thắng. Nếu bằng điểm chính xác, giữ vòng huấn luyện/ứng viên xuất hiện trước. Tối đa một điểm lưu mô hình tốt nhất cho mỗi ứng viên được giữ lại. Trước bất kỳ dự đoán kiểm thử nào, khóa lựa chọn liên kết điểm lưu mô hình hash/config/choices. điểm lưu mô hình đã xuất được tải lại và kiểm tra lại trên tập xác thực; chỉ khi đó một lần vượt qua kiểm thử đầy đủ mới xảy ra. Các dự đoán đã lưu hỗ trợ tính toán lại số liệu mà không cần thực hiện lại kiểm thử suy luận. Không có điều chỉnh nào từ P5 kiểm thử hoặc P6 kiểm thử đã được đánh giá này. Đã kiểm tra tính xác định của suy luận; huấn luyện được gieo hạt là nỗ lực tốt nhất trên phần cứng được ghi chứ không phải đảm bảo bitwise trên nhiều thiết bị.

## Thực thi và giới hạn tài nguyên

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u -B -m scripts.train_p6
.\.venv\Scripts\python.exe -B -m scripts.validate_p6
.\.venv\Scripts\python.exe -B -m scripts.report_p6
.\.venv\Scripts\python.exe -m scripts.test_all
```

huấn luyện từ chối hậu tố model/report hiện có. Việc phát lại giao thức không thay đổi có chủ ý cần có bản sao cấu hình và output_suffix mới thông qua `--config`. Chạy một phần bảo toàn checkpoints/history/status; không ghi đè im lặng, tự động điều chỉnh lại hoặc cho rằng huấn luyện đã hoàn thành P6. Bản ghi trạng thái lỗi BLOCKED/NEXT_ACTION. Các tệp điểm lưu mô hình được thay thế thông qua các tệp tạm thời trên mỗi cải tiến tập xác thực; Trạng thái optimizer/RNG không được lưu, do đó huấn luyện bị gián đoạn yêu cầu chạy mới chứ không phải tiếp tục chính xác ở giữa vòng huấn luyện.

Bộ chạy kiểm thử dùng hai tiến trình pytest mới: tất cả các bài kiểm tra P0–P5, sau đó là các bài kiểm tra P6. Chỉ riêng việc import Torch làm tăng quy trình RSS vượt xa các bộ bảo vệ dữ liệu-phase512MB cũ hơn; bộ sưu tập nguyên khối gây ra 20 thất bại liên quan đến ngân sách. Việc cách ly giữ nguyên guards/tests cũ thay vì nâng trần tài nguyên hoặc thay đổi các xác nhận.

Nhật ký huấn luyện được ghi qua PowerShell `*>` chứa các báo cáo stderr đầu tác vụ đã huấn luyện trước dự kiến được gói dưới dạng NativeCommandError, mang lại exit1 trình bao bọc mặc dù có đường dẫn DONE/full bản kê. Bảo quản nhật ký đó; sử dụng tập xác thực (exit0) độc lập và bằng chứng epoch/checkpoint hoàn chỉnh để đánh giá hoạt động. Không tuyên bố trình bao bọc trả exit0.

Ngăn xếp Windows/Python3.13 đã ghi: torch2.8.0+cu128, Transformers5.0.0 với tokenizers0.22.1/HF Hub1.33.0 và sklearn1.7.2 hiện có. Các yêu cầu bao gồm chỉ mục bổ sung CUDA12.8 chính thức và các phần phụ thuộc bổ sung được ghim. Máy trạm mặc định Python không phải là môi trường này. Thiết bị tự động sử dụng CUDA khi khả dụng, nếu không thì CPU; CUDA không khả dụng rõ ràng sẽ gây ra lỗi. Độ chính xác hỗn hợp bị vô hiệu hóa trên CPU. Cấu hình budgets4hours/6GB đầu ra chạy RSS/4GB là kiểm tra mềm giữa các hoạt động, không phải giới hạn hệ điều hành cứng. Tải xuống mô hình và cài đặt môi trường là chi phí thiết lập riêng biệt. Không bao giờ âm thầm giảm độ dài dataset/max xuống khớp mô hình.

## Đang tải

```python
import json
import pandas as pd
from src.config import PROJECT_ROOT
from src.models.registry import load_sentiment

report = PROJECT_ROOT / "reports/p6/p6_20261015"
lock = json.loads((report / "selection_lock.json").read_text(encoding="utf-8"))
model_dir = PROJECT_ROOT / "artifacts/models/p6_20261015" / lock["selected"]["mode"]
artifact = load_sentiment(model_dir, family="bert", language="en", device="auto")
predictions = artifact.predict(pd.DataFrame({
    "text": ["The keyboard is comfortable."], "language": ["en"]
}))
```

Đây là cách sử dụng có thể thực thi được, không có ví dụ nhãn hoặc điểm số nào được xác nhận. Trọng lượng mô hình, cấu hình mô hình và bộ tách token độc lập trong thư mục đã chọn; siêu dữ liệu liên kết tổng kiểm tra của họ và ID nhãn chính xác. Chỉ nhập văn bản, ngôn ngữ tùy chọn phải là en; Đầu vào invalid/empty không thành công. Đầu ra tuân theo laptop/en/three labels/confidence null/aspects trống. độ tin cậy không được hiệu chỉnh; P6 chỉ có tổng thể không tạo ra các dự đoán khía cạnh. `predict(frame)` phục vụ đơn hoặc lô, giữ thứ tự hàng, chạy chế độ eval/inference và có thể tải trên CPU hoặc CUDA.

## Bằng chứng và giải thích

Chạy các đầu ra trong `reports/p6/<suffix>/`, models/predictions trong `artifacts/models/<suffix>/` bị bỏ qua. Config/environment/source/loading/smoke/input tập xác thực, training_history/progress, selection_lock, metrics/confusion matrices/benchmark, error_analysis/validation và bản kê lưu giữ bằng chứng thí nghiệm. Các hàng đánh giá so sánh P5 sử dụng lại các hàng metrics/times đã lưu lịch sử; Hàng BERT sử dụng lần chạy này. Độ trễ P5 là CPU, BERT có thể là GPU; tỷ lệ là chi phí quan sát được trên các thiết bị được chỉ định, không phải là so sánh tốc độ chỉ dành cho kiến ​​trúc được kiểm soát. Số lần lặp/lắp lưới tối đa của P5 và lựa chọn BERT epoch/checkpoint cũng thể hiện các ngân sách khác nhau.

Báo cáo thời gian khớp mô hình của ứng viên đã chọn, tổng thời gian tìm kiếm khớp mô hình và toàn bộ lần chạy riêng biệt. suy luận sử dụng review xác thực đầu tiên128, một lần khởi động và năm lần lặp lại, duration/row từ đầu đến cuối trung bình với đồng bộ hóa CUDA, không bao gồm tải đĩa. BERT các đợt nội bộ16; đây là các phép đo thông lượng theo đợt được khấu hao, không phải độ trễ của một yêu cầu riêng biệt. RSS quy trình được lấy mẫu20ms và bao gồm inputs/runtime/allocations; Đỉnh CUDA allocated/reserved đến từ Torch và loại trừ các phân bổ GPU apps/driver khác. Các byte mô hình so với tổng số byte thư mục suy luận được phân biệt. Không ngụ ý sự bình đẳng của các số liệu CPU/GPU tài nguyên.

Chẩn đoán lỗi sau khóa cơ bản được yêu cầu cho P6 so sánh các lỗi BERT/LR đại diện đã lưu và các lát cố định lexical/length. Hàng đợi văn bản chẩn đoán không phải là bộ gold do con người gán nhãn; các tín hiệu từ vựng không tạo ra sự bất đồng về xếp hạng thực sự hoặc sentiment/sarcasm hỗn hợp. Danh sách kiểm tra giai đoạn chi tiết của P7 vẫn riêng biệt và không được kiểm tra.

Giới hạn: Chỉ phát hiện laptop; nhãn đại diện suy từ số sao-nhiễu nhãn; Sự thay đổi SemEval-to-Amazon platform/style trong laptop review; bộ dữ liệu gold được chú thích thủ công nhỏ (P10 gold độc lập hiện không có). không trùng sản phẩm giữa các tập không phải là brand/user/time- rời rạc. Không có tuyên bố về tính ưu việt của Transformer trong quá trình sản xuất, đa tiện ích hoặc tự động.
