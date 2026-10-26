> LEGACY: ảnh chụp tại2026-10-19. Tra [chỉ mục hiện hành](PROJECT_INDEX.md), [benchmark semantic](MODEL_STACK_REFACTOR.md) và [kế hoạch cloud](TABPFN_CLOUD_PLAN.md); câu P7 chưa bắt đầu bên dưới chỉ là lịch sử.

# Việt hóa tài liệu và nội dung hiển thị

Ngày thực hiện: 2026-10-19 (Asia/Saigon), theo yêu cầu dịch toàn bộ tài liệu, chú thích mã và nội dung giao diện. Đây là thay đổi ngôn ngữ; không triển khai giai đoạn mô hình mới.

## Phạm vi

- 47 tệp Markdown hiện có: AGENTS, README, hai PLAN, từ điển dữ liệu, tài liệu trong `docs/`, báo cáo và tài liệu lịch sử trong `reports/`.
- 3 notebook: notebook nguồn P3 và các bản notebook trong báo cáo; dịch phần giải thích, giữ nội dung dữ liệu và kết quả thực thi đã lưu.
- 90 tệp Python trong `src/`, `scripts/`, `tests/`: chú thích, docstring, trợ giúp dòng lệnh; Việt hóa nhãn biểu đồ ở các hàm trình bày.
- `data/manual/independent_qa/p1_v2/annotation_guide.md`: hướng dẫn QA, không thay tệp gán nhãn.
- `customer_sentiment_analysis_plan.docx`: dịch nội dung và chân trang, giữ bảng và kế hoạch lịch sử. Mục tiêu 50K trong bản này đã bị thay thế bằng yêu cầu 30K ngày 2026-10-08; PLAN/README hiện hành có thẩm quyền.
- Ghi quy tắc tiếp tục dùng tiếng Việt trong `AGENTS.md` và làm mới bàn giao. Tài liệu tổng kết này được tạo mới.

Thư mục `app/` hiện chỉ có `.gitkeep`, chưa có giao diện Streamlit. Các nhãn biểu đồ mới được Việt hóa trong mã; hình, log và bằng chứng thực nghiệm đã lưu trước đây được giữ để bảo toàn lịch sử. Từ vựng tiếng Anh được thống kê từ review và tên lớp/mô hình vẫn giữ nguyên.

## Những nội dung giữ nguyên vì tương thích

Giữ tên tệp/đường dẫn, lệnh và tùy chọn CLI, định danh Python, khóa cấu hình/lược đồ, biểu thức chính quy, nhãn `negative/neutral/positive`, ánh xạ ID, mã trạng thái và ví dụ đầu vào tiếng Anh. Thông báo lỗi kiểm tra đầu vào và chuỗi kỹ thuật dùng trong hợp đồng/kiểm thử được giữ nguyên khi cần tương thích.

Không dịch dữ liệu review nguồn, nhãn CSV, mô hình, dự đoán, JSON/CSV thước đo hoặc bản kê SHA256 lịch sử. Giá trị cấu hình không thay đổi. Không thay danh sách công việc đã hoàn thành, chạy lại huấn luyện, tạo nhãn gold hay đánh giá test mới.

Bản dịch dài có hỗ trợ dịch tự động Google. Các tài liệu chính, thuật ngữ học máy, quy tắc QA và hợp đồng quan trọng đã được rà soát/chỉnh sửa thêm; không coi toàn bộ báo cáo lịch sử là bản dịch đã được con người kiểm duyệt từng câu. Chỉ gửi văn bản tài liệu/chú thích cần dịch; không tải dữ liệu review nguồn hoặc thông tin xác thực lên dịch vụ.

## Kiểm tra đã thực hiện

| Kiểm tra | Kết quả quan sát |
|---|---|
| `.venv/Scripts/python.exe -m scripts.test_all` | 195 đạt trong 8.58s; 12 đạt trong 8.91s; tổng 207, không lỗi |
| `.venv/Scripts/python.exe -m compileall -q src scripts tests` | Thành công |
| `.venv/Scripts/python.exe -m pip check` | Không có phụ thuộc hỏng |
| Đối chiếu checkbox hai PLAN | Thứ tự và trạng thái giữ nguyên |
| Đối chiếu tùy chọn CLI trong Markdown | Không mất tùy chọn gốc |
| Đối chiếu cấu trúc Python | Ngoài docstring/trợ giúp, bốn mô-đun biểu đồ có thay đổi chữ/ánh xạ hiển thị; không đổi phép tính dữ liệu hoặc huấn luyện |
| Kiểm tra Word | 3 trang, đã xuất PDF và xem PNG cả 3 trang; không thấy tràn/cắt nội dung |
| Kiểm tra biểu đồ P3 | Dựng 7 biểu đồ/14 PNG+SVG từ bảng có sẵn vào thư mục tạm, xem mẫu bố cục và dấu tiếng Việt |
| SHA256 parquet P2 | Khớp `611b73584a933645336784b13b7f004a17e8803758d1be8ac64708563eabb5ba` |

Renderer `render_docx.py` không chạy do máy thiếu LibreOffice; đã dùng Microsoft Word có sẵn để xuất PDF và pdf2image/Poppler dựng PNG. Không cài thêm thư viện. Tệp kiểm tra trung gian ở thư mục tạm ngoài kho mã.

**Lưu ý toàn vẹn lịch sử:** dịch tài liệu/docstring làm đổi byte và hàm băm tệp nguồn. Không sửa manifest/QA cũ để làm khớp bản dịch, không tuyên bố toàn bộ kiểm tra băm nghiệm thu P4–P6 đã được chạy lại hoặc vẫn khớp. Bằng chứng 2026-10-15 mô tả phiên bản tại thời điểm đó; kết quả kiểm thử phía trên mô tả phiên bản Việt hóa hiện tại.

## Trạng thái và bước tiếp theo

P7 chưa bắt đầu; P10 chưa có human gold; tiếng Việt/PhoBERT vẫn chưa triển khai. QA lọc sản phẩm không phải bộ kiểm thử cảm xúc/ABSA do con người gán nhãn. Bước tiếp theo theo kế hoạch là P7 phân tích lỗi bằng dự đoán đã lưu khi người dùng yêu cầu.

Giới hạn nghiên cứu giữ nguyên: chỉ laptop; nhiễu nhãn suy từ số sao; khác biệt nền tảng/phong cách SemEval–Amazon trong cùng phạm vi laptop; bộ gold thủ công nhỏ, hiện chưa có.
