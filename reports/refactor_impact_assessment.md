# Đánh giá tác động refactor — 2026-10-24

Trạng thái: WARNING — đã kiểm tra cấu trúc và số liệu thực tế; chưa nghiệm thu pipeline mới.

Yêu cầu trong tệp đính kèm ngày 2026-10-24 thay thế yêu cầu bộ mô hình cũ của AGENTS/PLAN: majority chỉ sanity baseline, XGBoost, TabM, TabPFN-3, TabPFN-3.5 và Transformer fine-tune. Không triển khai ABSA trong tác vụ này. Các tiêu chí không xung đột vẫn áp dụng.

## Trạng thái trước thay đổi

P0–P6 cũ được bàn giao là hoàn thành; P7 chưa bắt đầu. Đây là bằng chứng lịch sử, không phải kết quả benchmark mới. Repository hiện chưa theo dõi các tệp bằng Git (git status liệt kê các đường dẫn untracked); không dùng git reset/checkout để phục hồi hoặc ghi đè.

Đã đọc trực tiếp parquet bằng môi trường `.venv/Scripts/python.exe` trước khi sửa mã:

| Tập | Review | parent_asin | negative | neutral | positive |
|---|---:|---:|---:|---:|---:|
| Toàn bộ | 30000 | 9080 | 8259 | 2631 | 19110 |
| train | 21000 | 6357 | 5781 | 1842 | 13377 |
| validation | 4500 | 1361 | 1239 | 395 | 2866 |
| test | 4500 | 1362 | 1239 | 394 | 2867 |

Nguồn: `data/processed/laptop_reviews.parquet`, `data/processed/splits/p4_20261009_final/*.parquet`. Không có sai lệch số lượng so với yêu cầu. Schema thực có `review_title` và `text` (body), không có `review_text`. Label ID 0/1/2 tương ứng negative/neutral/positive. Phải kiểm tra lại cách ly trước khi tái sử dụng; không tạo split mới.

Môi trường ban đầu: Python 3.13.12, torch 2.8.0+cu128, CUDA 12.8, RTX 4050 Laptop GPU 6438780928 byte; transformers 5.0.0, sklearn 1.7.2. XGBoost/TabM/TabPFN/sentence-transformers chưa cài. `pip check`: PASS trước thay đổi.

## Phạm vi và rủi ro

- P0: kiểm tra resolver, pin/ghi phiên bản, import smoke, phân biệt explicit V3/V3_5; không thay đổi dữ liệu.
- P1/P2: tái xác minh bằng nguồn và QA đang có; không tải Amazon/crawl/lọc/làm sạch/gán nhãn lại.
- P3: bổ sung readiness; phân biệt ước lượng với số đo.
- P4: canonical title + body tối thiểu, frozen encoder dùng chung, cache có hash và mapping; nhánh tokenizer riêng. TF-IDF/SVD/PCA không thuộc pipeline mới.
- P5: benchmark vừa phải, unweighted/weighted khi hợp lý; khóa lựa chọn theo validation macro F1 trước test; explicit checkpoint TabPFN, thử tài nguyên trước full context.
- P6: reuse mã BERT nếu đáp ứng canonical text mới; experiment cũ chỉ được so sánh như legacy nếu đầu vào khác.
- P7: hợp nhất kết quả mới và phân tích lỗi; không dùng test đã xem để chọn mô hình.

Giữ nguyên các config, model, metrics, reports, EDA cũ để audit. Tái sử dụng `src/config.py`, `src/evaluation/classification.py`, ResourceMonitor, quy ước labels và test suite; không di chuyển hoặc xóa artifacts.

Rủi ro: tương thích Python 3.13 và các pin hiện tại; quyền truy cập/giấy phép checkpoint TabPFN; context 21K × embedding trên VRAM 6 GB; thời gian Transformer; test cũ đã được đánh giá nên phải công bố lịch sử phơi nhiễm. Không tự chấp nhận điều khoản tài khoản, dùng API trả phí hoặc giảm dữ liệu toàn benchmark.

## Cổng thực hiện

Theo thứ tự P0 → kiểm tra P0 → P1 … → P7. Sau mỗi pha lưu PASS/FAIL/WARNING và tests thực chạy. Nếu một pha FAILED/BLOCKED, giải quyết nguyên nhân trước; không tuyên bố các pha sau hoàn thành. Kết quả chưa đo là NOT_MEASURED.

Giới hạn giữ nguyên: chỉ laptop; nhãn đại diện suy từ sao có nhiễu; thay đổi nền tảng/phong cách SemEval–Amazon trong laptop; gold thủ công nhỏ và hiện chưa có.
