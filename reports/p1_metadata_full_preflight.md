# P1 — Mua lại siêu dữ liệu điện tử đầy đủ & Preflight chỉ dành cho laptop

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

Ngày: 2026-10-08 (Asia/Saigon). **siêu dữ liệu acquisition và preflight hoàn thành. P1 chưa hoàn tất.** Người dùng đã phê duyệt tải ~1,31 GB siêu dữ liệu và siêu dữ liệu-only scan; **chưa phê duyệt review**. Mục tiêu hiện hành vẫn 30.000 sạch tiếng Anh laptop review, có thể đánh giá tập ứng viên chất lượng nhỏ hơn.

## Thu thập và toàn vẹn nguồn

Downloader hiện tại đã tải nguyên compressed byte từ URL Electronics siêu dữ liệu được cấu hình, không giải nén ra dump, không overwrite/delete raw, không thay đổi code hoặc ceilings.

| Hạng mục | Kết quả thực đo |
|---|---|
| Raw mới | `data/raw/amazon/meta_Electronics.jsonl.gz` |
| Kích thước | **1.312.900.427 byte** |
| SHA256 | `a4a196a1c8e443e0942d8a5c79b5a5d2d68e29d483f2badec1126690b4b2790d` |
| bản kê | `meta_Electronics.jsonl.gz.manifest.json` |
| Trạng thái tải xuống | `source_eof`, `complete_source=true`, requested_limit=null |
| Đã truy xuất UTC | 2026-10-08T06:27:38.891086+00:00 (13:27:38 Asia/Saigon) |
| Thẻ ET | `"4e41454b-62bda3bbc47f3"` |
| Connection/setup/transfer đã trôi qua | **1.312,77 s (~21 phút 53 giây)** |

Elapsed được tính từ process StartTime tới bản kê retrieved timestamp; gồm setup/connection/transfer, không gồm checksum cuối. Downloader đã kiểm tra toàn bộ body với HTTP Content-Length, hàm băm sau đóng file; SHA256 đọc lại khớp trước preflight, trong preflight và sau preflight. Năm raw Amazon files (bốn prefixes cũ và toàn bộ siêu dữ liệu mới) đều khớp manifests. Không có partial/failure file của lượt tải thành công. GZIP được đọc đến EOF trong preflight, không báo CRC/decompression/JSON errors. Đây là kiểm tra integrity local/source nguồn gốc; không gọi SHA256 tự tính là checksum độc lập do upstream công bố. Nguồn public research theo access observations hiện có; không commit/tái phân phối raw.

Bằng chứng thực hiện: `tables/p1_metadata_download_execution.json`, `tables/electronics_metadata_full_30k.json`, `tables/p1_metadata_full_integrity.json`.

## Kết quả preflight laptop-only

| Chỉ số | Kết quả |
|---|---:|
| Tổng siêu dữ liệu records đã quét | **1.610.012** |
| Sản phẩm laptop ứng viên / parent_asin được chọn duy nhất | **28.172** |
| siêu dữ liệu records bị loại bởi filter | **1.581.840** |
| Số nhận dạng siêu dữ liệu không hợp lệ | **0** |
| Bản ghi không hợp lệ/quá khổ/không đúng định dạng/cắt ngắn | **0 / 0 / 0 / 0** |
| Quyết định `ambiguous_multiple_groups` rõ ràng | **0** |
| EOF được quan sát | **đúng** |
| Lý do dừng lại | **source_eof** |
| Hoàn thành bảo hiểm siêu dữ liệu | **đúng** |
| review được quét | **0 — not_started** |
| Toàn bộ vùng phủ sóng nguồn siêu dữ liệu+review | **false**, vì review chưa quét |

Số loại là **record decisions**, không khẳng định mọi parent ID bị loại đều unique. 28.172 được chọn IDs đã kiểm tra không trùng lặp, tất cả `group=laptop`; hàng conservation PASS.

| Quyết định lọc | Bản ghi siêu dữ liệu |
|---|---:|
| `insufficient_laptop_evidence` | 830.326 |
| `excluded_category` | 328.872 |
| `accessory_or_ambiguous_title` | 422.642 |
| `laptop_category_and_title` (đã bao gồm) | 28.172 |
| Tổng | **1.610.012** |

mô hình cơ sở và group-filter decisions bằng nhau trên nguồn này. Cross-group category ambiguity kiểm tra giới hạn vẫn hoạt động dù chỉ xuất laptop; `ambiguous_multiple_groups` có số lượng 0. Title lý do `accessory_or_ambiguous_title` gộp accessories và title mơ hồ, **chưa đo riêng số title ambiguous**. Không suy 422.642 là toàn bộ ambiguous sản phẩm hay chỉ accessories. Category/title thiếu laptop keywords vẫn có nguy cơ false negative; mô hình cơ sở không thay đổi để tăng counts.

## RAM, thời gian, I/O và ceilings

| tài nguyên | Thực đo | giới hạn giữ nguyên |
|---|---:|---:|
| Bản ghi siêu dữ liệu | 1.610.012 | 2.000.000 |
| Sản phẩm được chọn | 28.172 | 100.000 |
| Chỉ số trong bộ nhớ ước tính | **38.002.675 byte** | 128.000.000 |
| Bộ làm việc quy trình đỉnh | **71.163.904 byte (~71,16 MB)** | 512.000.000 |
| Preflight elapsed (gồm checksum) | **212,962 s (~3 phút 33 giây)** | 14.400 s |
| Đọc tổng kiểm tra nén | **1.312.900.427 byte** | |
| Đọc logic được giải mã | **5.246.144.134 byte** | |
| Tổng kiểm tra ngân sách + đọc được giải mã | **6.559.044.561 byte (~6,56 GB)** | 60.000.000.000 |
| Sản phẩm JSONL trên đĩa | **9.639.464 byte** | 2.000.000.000 JSONL byte |

Decoded byte là logical scanner I/O, không phải lượng disk cần lưu hoặc physical disk traffic. Preflight có một compressed checksum pass + một streaming GZIP pass; các lần integrity hàm băm ngoài preflight là I/O bổ sung, không nằm trong elapsed/budgeted read của báo cáo preflight. Raw gzip giữ compressed, không có uncompressed dump. Mọi ceilings đều không bị chạm. Không có lỗi thực sự cần sửa/refactor; nguồn code/config ceilings không thay đổi trong lượt này.

## Đầu ra và con người QA

- Chỉ số nhỏ gọn: `data/interim/feasibility/electronics_metadata_full_30k/products.jsonl`.
- lần chạy báo cáo: cùng directory, `report.json`; bản JSON bằng chứng ở `reports/tables/electronics_metadata_full_30k.json`.
- đầu ra SHA256: `8c359dbc575980fd31066de83c484110e7c5908fb590aeb5f44b2d757748912e`, đã verify.
- QA mới: `data/manual/feasibility/Electronics_laptop_8a3c1eaf1583.csv`.
  **100 hàng**, gồm 50 included, 25 excluded_near_boundary và 25 excluded_other; con người nhãn vẫn để trống. bộ kiểm tra: 100 đang chờ, `unvalidated`, độ chính xác dự đoán (precision) null, population độ bao phủ (recall) NOT_MEASURED. Immutable QA rule fingerprint đã verify.
- Xác minh nhanh: `.venv\Scripts\python.exe -m pytest -q`: **84 đã đạt, 0 không thành công**.
  Các unit kiểm thử dùng dữ liệu mẫu; counts/resource measurements ở đây là toàn bộ siêu dữ liệu thật.

## Ý nghĩa và bước tiếp theo

**toàn bộ siêu dữ liệu preflight đạt**, có thể chuẩn bị laptop review join bằng parent_asin. 28.172 là ứng viên sản phẩm, **không phải review số lượng** và chưa được người xác minh filter. Không thể kết luận đủ 30K sạch tiếng Anh review trước khi có reviews/language/quality evidence. 17 laptop ứng viên review của prefixes cũ vẫn là số lịch sử; không chạy survey review mới. ABSA vẫn cần explicit spans/aspect cảm xúc nhãn từ SemEval/human Amazon gán nhãn; rating overall và siêu dữ liệu không cung cấp nhãn đó.

review Electronics theo HEAD bằng chứng trước: **6.474.438.619 byte (~6,47 GB)**. Download giới hạn hiện tại **6.600.000.000 byte / 3.600 s**. siêu dữ liệu lần này có throughput bình quân khoảng **1,00 MB/s** (gồm connection/setup); nếu review có throughput tương tự, tải cần khoảng **108 phút**, vượt giới hạn 60 phút. Đây là **scenario dựa trên lượt siêu dữ liệu**, không phải phép đo tốc độ review. Cần >~1,80 MB/s để review hoàn tất trong một giờ. Không tự tăng giới hạn; người dùng cần cân nhắc mạng nhanh hơn hoặc quyết định giới hạn tài nguyên riêng.

Nếu được phê duyệt sau này, laptop review scan giữ 50M review records, process 512 MB, read 60 GB và thời gian 4 giờ. Main survey sẽ hash/read lại siêu dữ liệu để dựng và xác minh index; siêu dữ liệu đã đo giúp tính giới hạn tài nguyên nhưng decoded review bytes/time vẫn NOT_MEASURED. Có index laptop không có nghĩa chỉ tải/đọc 30.000 review đầu nguồn là đủ.

BLOCKED: review download/scan chưa được phê duyệt; tốc độ siêu dữ liệu vừa đo cho thấy nguy cơ vượt review download thời gian giới hạn hiện tại. con người QA và gốc SemEval các tập đã chia vẫn đang chờ. NEXT_ACTION: người dùng xem đã đo siêu dữ liệu results và quyết định bước reviews/ngân sách; hoàn tất con người QA song song. Dừng tại đây, không tải review, không P2/training/domain expansion.

Giới hạn bắt buộc: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (hiện chưa có). Không claim cross-gadget generalization hoặc production readiness.
