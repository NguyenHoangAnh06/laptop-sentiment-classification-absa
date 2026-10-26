# P0 — Khởi tạo dự án

Ngày kiểm chứng: 2026-10-08 (Asia/Saigon).

## Kết quả và bằng chứng

- P0-T01: `git init` thành công; `.gitignore` bảo vệ `.venv`, secrets, dữ liệu và mô hình các tệp kết quả.
  Tạo virtual môi trường mới bằng Python 3.13.12; cài phụ thuộc P0 thành công.
- P0-T02: đã tạo các thư mục chức năng theo kế hoạch, dùng `.gitkeep` cho thư mục
  chưa có implementation. Chưa tạo notebook hay script huấn luyện giả.
- P0-T03: ba YAML cấu hình chứa phạm vi laptop, hạt giống ngẫu nhiên 42, paths, rating nhãn đại diện,
  nhãn IDs 0/1/2, danh sách mô hình bắt buộc, macro F1 và thước đo phụ/chi phí.
- P0-T04: định tuyến `en -> BERT`, `vi -> PhoBERT` reserved/disabled; chung lược đồ
  cho đơn lẻ/hàng loạt có tập xác thực, độ tin cậy nullable và khía cạnh rỗng khi không có khía cạnh. Registry hiện chỉ cung cấp siêu dữ liệu, chưa load mô hình.
- README mô tả phạm vi, thiết lập thực thi được, phương pháp và các giới hạn.

## Kiểm tra đã chạy

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
git check-ignore .venv/pyvenv.cfg data/raw/amazon/example.jsonl artifacts/example.bin .env
```

Kết quả: cài đặt thành công; `No broken requirements found`; **9 passed**. Git ignore trả về cả bốn đường dẫn kiểm tra (chỉ là tên đường dẫn kiểm tra, không tạo dữ liệu mẫu). kiểm thử dùng object dữ liệu mẫu, không phải mô hình prediction. phụ thuộc trực tiếp và gián tiếp đã được khóa theo môi trường kiểm chứng.

## Chưa kiểm chứng và bước tiếp theo

P0 hoàn thành phần khởi tạo, chưa có bộ dữ liệu, huấn luyện, đánh giá so sánh hoặc app chạy được. Chưa kiểm chứng toàn bộ phụ thuộc xây dựng mô hình hay GPU, hoặc Python/platform khác.

BLOCKED: Chưa có Amazon review + siêu dữ liệu và SemEval để thực hiện dữ liệu audit ở P1. NEXT_ACTION: P1-T01/P1-T03 kiểm tra license/access và lấy dữ liệu từ nguồn được phép; tiếp đó audit schema/join key và xây dựng filter laptop có kiểm tra thủ công.

Các giới hạn cần giữ: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small do con người gán nhãn bộ dữ liệu gold (mục tiêu 300–500, hiện chưa thu thập/gán nhãn).
