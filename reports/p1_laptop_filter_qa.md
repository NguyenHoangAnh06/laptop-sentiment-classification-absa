# P1 — Bộ lọc laptop QA

Ngày 2026-10-08. Đã đánh giá đủ **100 sản phẩm**, không sửa nhãn hoặc filter rules. nhãn là **AI-assisted, user-approved**, không phải độc lập con người-verified nhãn hay độc lập bộ gold do con người gán nhãn standard. Nguồn là QA toàn bộ survey `data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv`.

## Kiểm tra dữ liệu

CSV đúng lược đồ, 100 parent IDs duy nhất, đủ 100 valid boolean nhãn: **54 true / 46 false**, không pending/unsure hoặc malformed rows. Các cột metadata/rule/stratum có fingerprint khớp toàn bộ survey gốc; thay đổi trước tác vụ này chỉ nằm ở con người labels/notes do người dùng cung cấp. File SHA256 trước/sau tác vụ: `9c0b1594b6207fb1d29066e4baa483ebc9b2ea9f3b82051c9399a505e6206f83`. Immutable rule SHA256: `5454e6e8d591f646c4c239b99ca1941df3a5f8b90125ee9e19fb3e4ac9336062`.

## Confusion matrix trên mẫu phân tầng

Hàng là quyết định rule; cột là nhãn user-approved.

| quy tắc | nhãn laptop Đúng | nhãn laptop Sai |
|---|---:|---:|
| Bao gồm Đúng | TP 50 | FP 0 |
| Đã loại trừ Sai | FN 4 | TN 46 |

**4 lỗi / 100 sampled sản phẩm**, tất cả trường hợp bỏ sót theo nhãn được chấp thuận. mẫu độ chính xác dự đoán (precision) = TP/(TP+FP) = **50/50 = 100%**, đạt criterion 95% với >=50 included. False-positive fraction trong included = **0/50 = 0%**. False-negative fraction trong excluded = **4/50 = 8%**; mẫu số là excluded hàng, không phải công thức FN/(TP+FN) hoặc population miss rate.

| tầng | Hàng | TP / FP / FN / TN | Tỷ lệ lỗi trong stratum |
|---|---:|---|---:|
| bao gồm | 50 | 50 / 0 / 0 / 0 | FP 0% |
| excluded_near_boundary | 25 | 0 / 0 / 4 / 21 | FN 16% |
| excluded_other | 25 | 0 / 0 / 0 / 25 | FN 0% |

Đây là mẫu 50/25/25 theo tầng, không đại diện ngẫu nhiên toàn Electronics/Amazon. Không suy population độ bao phủ (recall) hoặc overall tỷ lệ dự đoán đúng (accuracy) từ matrix; cả hai **NOT_MEASURED**. độ chính xác dự đoán (precision) 100% là agreement với user-approved nhãn trong 50 included hàng, không bảo đảm 100% độ chính xác dự đoán (precision) trên toàn 408.480 review.

## Bốn trường hợp bỏ sót và nguyên nhân

| parent_asin | Sản phẩm theo siêu dữ liệu và nhãn được chấp thuận | Nguyên nhân rule |
|---|---|---|
| B07FYPFHHZ | MSI GL73 8RD-282 Chơi game laptop | Title có laptop, categories chỉ đến Computers & Tablets; thiếu laptop category |
| B0027JVI30 | Máy tính xách tay Panasonic CF-19 chuyển đổi | Categories có Laptops/Traditional Laptops, title dùng Tablet PC/model CF19, thiếu laptop/notebook/chromebook keyword |
| B0872V1HHF | HP 14 laptop, Athlon 3050U được đổi mới | Title có laptop, categories quá chung; thiếu laptop category |
| B098BNXYGR | HP Pavilion x360 2-in-1 laptop | Title có laptop, categories rỗng |

Tất cả `rule_reason=insufficient_laptop_evidence`; nguyên nhân được kiểm tra từ CSV categories/title và rule hiện có. sản phẩm identity ở đây dựa trên labels/notes được người dùng cung cấp; Codex không tuyên bố đã independently verify manufacturer links. toàn bộ laptop tập ứng viên là conservative subset có thể bỏ sót sản phẩm thật. Không biết có bao nhiêu review của bốn sản phẩm bị bỏ hoặc population độ bao phủ (recall); không scan lại raw.

## Khuyến nghị và trạng thái điều kiện nghiệm thu

Giữ filter v1 và bộ dữ liệu hiện tại. tập ứng viên lớn, included mẫu không có FP theo nhãn này; chưa có căn cứ để nới rule đại trà hoặc tăng quota bằng sản phẩm không rõ phạm vi. Trước thay đổi filter, cần review độc lập các boundary cases và trường hợp nhận nhầm; thử nghiệm một đường xác minh siêu dữ liệu bổ sung cho category thiếu, cùng manufacturer/ mô hình bằng chứng cho chuyển đổi mô hình-only titles. Không đổi thành title-only inclusion, không loại tablet-mode laptop chỉ vì từ tablet. thực sự 2-in-1/convertible vẫn in phạm vi.

Việc bỏ cũ multi-phạm vi ambiguity classifier không sửa các category/title rules của laptop v1. laptop dữ liệu mẫu xác minh chuyển đổi title có laptop và laptop category vẫn được include. CF-19 mô hình-only case được ghi rõ là known limitation, chưa sửa. Mọi filter correction/dataset regeneration cần phạm vi riêng; không chạy lại toàn bộ survey.

**Đã hoàn thành đánh giá user-approved QA**, mẫu độ chính xác dự đoán (precision) criterion PASS. **độc lập thủ công filter tập xác thực còn đang chờ**; không đánh dấu P1-T02 thủ công inspection hoàn thành chỉ dựa vào AI nhãn được chấp thuận chung. Đây cũng không phải gold Amazon sentiment/ABSA gán nhãn của P10.

Tái tạo:

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_filter_qa --path data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv --label-provenance ai_assisted_user_approved
```

Machine results: `reports/tables/p1_laptop_filter_qa.json`. NEXT_ACTION: người dùng kiểm tra từng sản phẩm bằng metadata/source bằng chứng để xác minh độc lập, ghi nguồn gốc riêng; không tự thay nhãn đã được chấp thuận.

Giới hạn dự án: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small bộ gold do con người gán nhãn set (chưa có). QA sản phẩm không đo chất lượng cảm xúc hoặc khía cạnh nhãn gán.
