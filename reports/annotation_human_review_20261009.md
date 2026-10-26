# Xác nhận con người review và chuẩn hóa gán nhãn — 2026-10-09

Tiếp tục hiện tại: [Hoàn thành QA](p1_qa_v2_completion_20261009.md) thay thế inventory/missing-path bên dưới và trạng thái chưa được đánh giá. Tệp khảo sát đầy đủ có nhãn100 tồn tại và khớp với SHA256 lịch sử; lược đồ bổ sung được hỗ trợ. Khoảng trống mô hình cơ sở100 là phụ trợ và không chặn đánh giá v1/v2 hợp lệ. Sự phê duyệt con người trước đó, hàm băm source/canonical và nguồn gốc AI lịch sử vẫn không thay đổi. Phần sau đây ghi lại nhiệm vụ chuẩn hóa trước đó; không có nhãn hoặc xác minh nào được lặp lại.

Project owner xác nhận đã trực tiếp kiểm tra toàn bộ gán nhãn, quyết định và chịu trách nhiệm về nhãn cuối cùng. con người verification **đã hoàn thành**, reviewer `human_reviewer_01` (định danh đã dùng trong guideline). Không yêu cầu xác nhận lại từng file. nhãn phê duyệt không đồng nghĩa QA/phase acceptance.

siêu dữ liệu xác nhận lưu tại `independent_qa/human_review_20261009/review_confirmation.json`, gắn với SHA256 của từng tệp. `reviewer_id` ánh xạ sang hiện có `annotator`; các trạng thái `human_verified=true`, `human_review_status=COMPLETED`, `review_status=APPROVED` lưu trong sidecar xác nhận, không thêm cột vào CSV hoặc sửa đã cố định bản kê.

| Tệp hiện có | Dòng | Nhãn hiện tại | con người review |
|---|---:|---|---|
| p1_v1/product_annotation.csv | 200 | 153 laptop / 47 non_laptop | ĐÃ HOÀN THÀNH |
| p1_v1/review_annotation.csv | 400 | 251 laptop / 149 non_laptop | ĐÃ HOÀN THÀNH |
| p1_v2/review_annotation.csv | 868 | 1 CHẤP NHẬN / 867 TỪ CHỐI | ĐÃ HOÀN THÀNH |
| laptop_filter_qa.csv | 100 | 100 ô human_is_laptop trống | ĐÃ HOÀN THÀNH; Thiếu giá trị nhãn |

Inventory quét các CSV thực có dưới `data/manual/`. Không có Amazon cảm xúc/ ABSA bộ gold do con người gán nhãn hiện có; không tạo gold từ xác nhận phạm vi QA. SemEval XML là third-party nhãn gán giữ nguyên nguồn gốc và bản gốc; xác nhận này không chứng minh nguồn chính thức, giấy phép, hay người dùng là tác giả nhãn SemEval.

## Chuẩn hóa

V1 đã dùng enum chuẩn nên giữ nguyên. V2 được chuẩn hóa theo quy ước phạm vi ACCEPT=laptop/REJECT=non_laptop trong yêu cầu chuẩn hóa của người dùng; không sử dụng prediction để quyết định nhãn. Bản dẫn xuất riêng: `data/interim/annotation_normalization/20261009/v2_review_annotation_canonical.csv`. Giữ nguyên cả 868 dòng/evidence/notes/error lý do và immutable nguồn các trường; chỉ chuyển biểu diễn nhãn. CSV nộp, sidecar, bản kê, v1 đánh giá không bị sửa. Canonical tập xác thực PASS: số lượng, fingerprint, label/reason enum, evidence.

BLOCKED: mô hình cơ sở `data/manual/laptop_filter_qa.csv` có100 nhãn trống, không thể biến thành cuối cùng nhãn. Báo cáo lịch sử về100 nhãn đầy đủ trỏ tới `data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv`, đường dẫn này không có trong inventory hiện tại. Không sao chép predictions/metrics để điền nhãn. NEXT_ACTION: tìm/khôi phục bản gán nhãn hoàn chỉnh đúng nguồn nếu cần dùng mô hình cơ sở này; không yêu cầu người dùng xác nhận lại con người verification.

## Xuất xứ và chấp nhận

V1 giữ `human_verified_after_ai_assistance`. V2 đã có cuối cùng con người xác nhận; lịch sử AI assistance cụ thể chưa được nêu trong declaration nên không tuyên bố fully blind/independent hoặc đổi lịch sử thành no-AI. Sidecar ghi unspecified cho lịch sử chưa xác định, kèm giải thích rõ. review phê duyệt không sửa lịch sử evaluation/provenance. Không chạy evaluator bằng flag gây claim independence sai.

P1 vẫn NOT DONE/NEEDS review; independence/coverage/brand criteria và authorized SemEval nguồn gốc không được duyệt qua chỉ dẫn này. Official v2 thước đo chưa chạy trong tác vụ ghi nhận/chuẩn hóa; các số1/867 là observed nhãn số lượng của canonical copy, không population độ bao phủ (recall). Không chỉnh filter/training/splits. Phần2 của yêu cầu bị cắt tại `Đọc lại: - \\`; đã yêu cầu gửi tiếp, không tự suy đoán những tác vụ bổ sung bị thiếu.

## Tái hiện và tập xác thực

```powershell
.\.venv\Scripts\python.exe -B -m scripts.record_annotation_review --confirm-human-review --annotator human_reviewer_01 --output-dir reports/independent_qa/NEW_REVIEW --canonical-output data/interim/annotation_normalization/NEW/v2_review_annotation_canonical.csv
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

Script chỉ được chạy theo thực tế declaration; từ chối overwrite. toàn bộ suite 140 passed in3.42s; canonical bộ dữ liệu tập xác thực PASS. gốc gán nhãn hàm băm được kiểm tra lại sau ghi nhận; preservation41-file mô hình cơ sở kiểm tra riêng. Không đổi dependencies. Limits: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small con người sentiment/ABSA bộ dữ liệu gold chưa có.
