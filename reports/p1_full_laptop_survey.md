# P1 — Khảo sát điện tử đầy đủ chỉ dành cho laptop

Ngày 2026-10-08 (Asia/Saigon). **hoàn thành: toàn bộ survey, exit 0, toàn bộ nguồn coverage.** P1 chưa hoàn tất: con người filter QA và gốc SemEval laptop huấn luyện/kiểm thử vẫn thiếu. Không chạy P2, huấn luyện, dashboard, download lại hoặc siêu dữ liệu-only preflight riêng. Raw, QA và kết quả cũ được giữ nguyên; pipeline/config/ceilings không thay đổi.

## Phương pháp và phạm vi

Chạy đúng CLI đã kiểm tra bằng `--help`, với phê duyệt của người dùng:

```powershell
.\.venv\Scripts\python.exe -m scripts.survey_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --reviews data/raw/amazon/Electronics.jsonl.gz --groups laptop --run electronics_full_laptop_30k --mode scan --allow-large-scan
```

quy trình hàm băm hai đầu vào, kiểm tra manifests, stream siêu dữ liệu dựng index rồi join review theo `parent_asin`. Chỉ giữ sản phẩm qua laptop metadata/title rules; review văn bản hoặc rating không quyết định phạm vi. Scan không dừng tại 30K. Valid nghĩa là siêu dữ liệu-linked ứng viên, văn bản không rỗng sau survey chuẩn hóa, rating thuộc 1–5 và aliases nhất quán; **không đồng nghĩa sạch tiếng Anh**. văn bản nguồn được giữ trong JSONL; chuẩn hóa chỉ phục vụ thống kê.

## Số lượng và coverage

| Chỉ số | Kết quả |
|---|---:|
| Bản ghi siêu dữ liệu | 1.610.012 |
| Sản phẩm ứng cử viên laptop | 28.172 |
| Tổng Electronics review quét | 43.886.944 |
| Phù hợp laptop review | 408.740 |
| Valid laptop review / số lưu trong `laptop_valid.jsonl` | 408.480 |
| Invalid matched review (empty/invalid text) | 260 |
| sản phẩm có ít nhất một **valid** review | 28.161 |
| ứng viên sản phẩm không có valid review | 11 |
| Deterministic mẫu review (subset, không cộng vào tập ứng viên) | 5.000 |

Số sản phẩm có bất kỳ matched review kể cả invalid-only không được đo riêng; 28.161 là số sản phẩm có valid review được xác minh từ output. 43.478.204 review không trong được chọn index: gộp out-of-phạm vi và thiếu matching được chọn siêu dữ liệu, không phải tỷ lệ thiếu siêu dữ liệu của toàn Electronics.

siêu dữ liệu và review đều `eof_observed=true`, `stop_reason=source_eof`; `metadata_coverage_complete=true`, `source_coverage_complete=true`, mẫu stop `completed`. Không malformed/oversized/truncated records hoặc gzip errors. EOF của gzip đã kiểm tra trailer/CRC khi đọc hết bằng quy trình hiện tại. Manifests full-source và URLs khớp nguồn cấu hình. toàn bộ nguồn coverage là quét hết hai nguồn Electronics đã tải; không chứng minh filter thu hồi mọi laptop trên Amazon.

Bảo tồn PASS: 43.886.944 = 43.478.204 + 408.740; 408.740 = 408.480 + 260. Số lượng Rating/length và tập hợp con mẫu cũng PASS.

## Đánh giá và tổng thể cảm xúc đại diện

Mẫu số mọi phân bố dưới đây: **408.480 valid review**.

| Đánh giá | review |
|---|---:|
| 1 | 75.626 |
| 2 | 28.191 |
| 3 | 32.685 |
| 4 | 64.764 |
| 5 | 207.214 |

| nhãn đại diện suy từ số sao | review |
|---|---:|
| negative (1–2) | 103.817 |
| neutral (3) | 32.685 |
| positive (4–5) | 271.978 |

Đây là đại diện cho overall cảm xúc, không phải con người nhãn chuẩn hoặc khía cạnh polarity. Positive chiếm khoảng 66,58%, neutral 8,00%, negative 25,42%; mất cân bằng cần đánh giá trong bước tiếp theo, chưa chọn lớp weights hay bất kỳ mô hình nào.

## Chất lượng và khía cạnh heuristic

- Độ dài trung bình: **78,7923 từ / 424,5171 chars**, trên văn bản đã decode HTML,
  bỏ HTML tags và collapse whitespace; từ số lượng dùng whitespace phân chia.
- Thùng từ: 0–4 **38.424**, 5–19 **97.915**, 20–99 **183.922**, 100+ **88.219**.
  review dưới 5 từ **9,4066%**; đây là chất lượng flag, chưa loại tự động.
- Không absent/null ở các các trường kiểm tra trên matched review: văn bản, rating,
  timestamp, helpful_vote, verified_purchase, user_id, review_title, asin. rỗng strings không phải absent/null; 260 empty/invalid văn bản đã bị loại.
- thương hiệu siêu dữ liệu thiếu trên **1.156 valid review**; **369** thương hiệu strings có mặt,
  chưa canonicalize hoặc con người-validate. Largest sản phẩm share **1,2527%**.
- Exact normalized-text bản trùng **NOT_MEASURED** cho toàn bộ tập ứng viên: vượt giới hạn 100K
  unique văn bản hàm băm nên quy trình vô hiệu hóa metric. bản gần trùng **NOT_MEASURED**.
- Số lượng Language/clean-English, ngôn ngữ hỗn hợp, tỷ lệ giống thư rác, mức độ phổ biến của HTML và
  rating/text disagreement **NOT_MEASURED**; chưa triển khai làm sạch ở lượt này.
- khía cạnh keyword đại diện: **171.998 / 408.480 = 42,1068%**, có ít nhất một keyword
  battery/screen/display/keyboard/performance/price/fan/touchpad/storage và >=10 words. Không phải extraction vị trí cụm từ, khía cạnh cảm xúc, gán nhãn hoặc ABSA sufficiency.
- Filter **unvalidated**. QA mới gồm 100 hàng (50 included/25 boundary/25 other),
  tất cả con người nhãn còn trống. QA cũ không ghi đè; Codex không gán nhãn thay người.

## Tài nguyên thực đo

| Chỉ số | Thực đo | giới hạn hiện tại |
|---|---:|---:|
| Survey elapsed (bao gồm nguồn hashing, đến trước cuối cùng đầu ra hashing/report write) | 998,8633 s (~16m39s) | 14.400 s |
| Bộ làm việc quy trình đỉnh | 442.224.640 byte (~442,22 MB) | 512.000.000 |
| Chỉ số được chọn ước tính | byte 38.002.675 | 128.000.000 |
| Sản phẩm được lập chỉ mục | 28.172 | 100.000 |
| Đọc đầu vào tổng kiểm tra | byte 7.787.339.046 | được bao gồm trong ngân sách I/O |
| Đọc đầu vào được giải mã | byte 27.862.377.786 | được bao gồm trong ngân sách I/O |
| Budgeted read tổng | byte 35.649.716.832 | 60.000.000.000 |
| Các byte JSONL được ghi | byte 430.753.519 | 2.000.000.000 |

Read accounting của quy trình là compressed checksum byte + decoded byte, không phải OS physical disk I/O/cache traffic. đầu ra hàm băm reads, độc lập verification reads và báo cáo byte nằm ngoài counter này; physical I/O **NOT_MEASURED**. đầu ra hashing/report-write tail không có timer riêng; không coi 998,8633 s là thời gian end-to-end chính xác đến process exit. Verification riêng **24,5920 s**. Không đạt tài nguyên limit. Peak working set còn khoảng 69,8 MB tới ceiling.

## các tệp kết quả và kiểm chứng

Chạy thư mục: `data/interim/feasibility/electronics_full_laptop_30k/`.

| tập tin | Hàng | Byte |
|---|---:|---:|
| `products.jsonl` | 28.172 | 9.639.464 |
| `laptop_valid.jsonl` | 408.480 | 416.018.817 |
| `laptop_sample.jsonl` | 5.000 | 5.095.238 |
| `report.json` | báo cáo khảo sát đầy đủ | 10.451 |

Machine báo cáo: `reports/tables/electronics_full_laptop_30k.json` (bằng lần chạy báo cáo). Verification: `reports/tables/electronics_full_laptop_30k_verification.json`. QA mới: `data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv`.

nguồn SHA256, đã hàm băm thực trong survey và khớp manifests:

- siêu dữ liệu: `a4a196a1c8e443e0942d8a5c79b5a5d2d68e29d483f2badec1126690b4b2790d`.
- review: `17b2c5f3736d4c0cb874859076436ebd4513f4c2396c528440a63204084e6a28`.

độc lập đầu ra checksums/line số lượng, siêu dữ liệu liên kết, monotonic nguồn gốc source_line, settings fingerprint, thước đo tính lại, 5.000 exact mẫu subset hàng, immutable QA fingerprint và hàng conservation đều **PASS**. Không hash/scan raw lần hai. `python -m pytest -q tests/test_p1_feasibility.py`: **53 passed in 1,33 s**. Không sửa code nên không chạy broad kiểm thử suite hoặc mô hình.

## Khả năng đạt mục tiêu và bước tiếp theo

tập ứng viên valid lớn gấp **13,616 lần** mục tiêu 30K; giữ được khoảng **7,3443%** tập ứng viên là đủ về số lượng. Đây là phép tính feasibility, không phải đã đo sạch yield. laptop-only **có tiềm năng mạnh về số lượng**, chưa xác nhận 30K sạch tiếng Anh. Phải xác thực phạm vi độ chính xác dự đoán (precision), tiếng Anh, loại trùng, spam/short review, nhiễu nhãn và class/product coverage trước quyết định bộ dữ liệu cuối. Không broaden phạm vi.

BLOCKED: P1 completion còn thiếu con người filter QA và authorized gốc SemEval laptop huấn luyện/kiểm thử; sạch tiếng Anh yield chưa đo (bước dữ liệu Quality/P2 chưa chạy). NEXT_ACTION: người dùng xem survey, hoàn tất QA thật và SemEval gốc các tập đã chia; sau đó phê duyệt bước dữ liệu Quality/P2: language audit, empty/short/spam/HTML checks, exact/near loại trùng, rating-text nhiễu, diversity và rò rỉ dữ liệu-resistant phân chia. Giữ gold 300–500 review độc lập do người gán nhãn; chưa có bộ dữ liệu gold.

Giới hạn: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (hiện chưa có). Không claim cross-gadget/production readiness. Survey xong thì dừng để người dùng xem kết quả; không tự chuyển P2.
