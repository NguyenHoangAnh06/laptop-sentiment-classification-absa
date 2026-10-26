# P1 — Từ điển dữ liệu

## Lược đồ đầu ra v4 cứng hơn

Valid/sample JSONL giữ thêm nullable `user_id` và `review_title` (alias nguồn `title/summary`), cùng `asin`, `parent_asin`, `timestamp`, `verified_purchase`, `helpful_vote`, `review_id`, `text`, `rating`, `product_title`, `brand`, `group`, `source`, `source_line`. thiếu optional các trường -> null, không tạo giá trị thay. văn bản nguyên gốc; `review_id` vẫn là nguồn gốc ID tạo từ nguồn SHA256+physical line, không phải ID review Amazon. Reviewer IDs chỉ nằm trong ignored dữ liệu files.

Scanner báo `eof_observed`, `oversized_records`, `malformed_records`, `truncated_records` (nghi JSON bị cắt cuối file), invalid totals và stop reason. EOF của local prefix không đủ nguồn coverage; siêu dữ liệu-only preflight không chứng nhận review coverage. Counts/schema profiles mới ở `*_hardening_v4.json`.

## Phạm vi khảo sát mới

Sau refactor có thêm Cell Phones and Accessories native nguồn probe: 5.000 siêu dữ liệu / 20.000 review. Parent join key và review keys khớp Electronics; profiles từng nguồn ở `reports/tables/electronics_refactor.json` và `cell_phones_refactor.json`. Không giả định mọi smartphone/tablet nằm trong Electronics. phạm vi project vẫn laptop; đầu ra `group` của feasibility không đổi suy luận contract.

các trường survey bổ sung: `group`, `source`, `source_line`, tổng hợp nguồn `review_id`, sản phẩm title/brand. `valid_reviews` chỉ yêu cầu mục tiêu siêu dữ liệu, lược đồ, rating và văn bản không rỗng; không hàm ý tiếng Anh, deduplicated hoặc con người cảm xúc labeled. `source_coverage_complete` chỉ true nếu nguồn có complete manifests và quét EOF. `not_in_selected_metadata_index` khác unmatched với mọi siêu dữ liệu: gồm ngoài group và parents không quan sát được. `human_is_target_product` là nhãn người kiểm tra trên new per-group QA CSV; các cột này đang trống. `human_is_laptop` cũ vẫn tồn tại trong mô hình cơ sở QA, không tự chuyển hoặc overwrite gán nhãn.

Các bảng dưới đây ghi missing/type số lượng của **Electronics prefix ban đầu**; không gán các tỷ lệ này cho Cell Phones hay toàn corpus.

lược đồ quan sát từ **20.000 siêu dữ liệu** và **100.000 review** đầu nguồn Electronics Amazon review 2023; không đại diện toàn bộ corpus. Nguồn: [McAuley Lab](https://amazon-reviews-2023.github.io/). Thống kê type/null/absent thực tế nằm trong `reports/tables/p1_audit.json`.

## Amazon review

| trường nguồn | Type quan sát | Ý nghĩa / sử dụng | Thiếu tiền tố |
|---|---|---|---|
| `text` | str | Body review; giữ nguyên ở P1 | 0 null/absent; chưa audit rỗng |
| `title` | str | Tiêu đề review, khác sản phẩm title | 0 null/absent |
| `rating` | phao | Rating 1–5; P2 mới tạo nhãn đại diện | 0 null/absent |
| `asin` | str | Variant ID; không dùng thay parent join key | 0 null/absent |
| `parent_asin` | str | Join với siêu dữ liệu và group rò rỉ dữ liệu audit | 0 null/absent |
| `user_id` | str | ID reviewer; giữ riêng trong dữ liệu, không đưa lên Git | 0 null/absent |
| `timestamp` | int | Unix timestamp; giá trị nguồn dùng millisecond | 0 null/absent |
| `helpful_vote` | int | Số phiếu bầu hữu ích | 0 null/absent |
| `verified_purchase` | bool | Đã xác nhận giao dịch mua siêu dữ liệu | 0 null/absent |
| `images` | danh sách | Media; không tải ảnh | 0 null/absent |

Alias khai báo: `text/reviewText`, `rating/overall`, `timestamp/sort_timestamp`, `helpful_vote/helpful_votes`. Prefix thực tế chỉ thấy tên đầu mỗi cặp. Alias không cho phép tự fallback `asin` sang `parent_asin`; conflicting values bị từ chối. Nguồn không có review ID riêng. `review_id` ở interim là **ID nguồn tự tạo** từ SHA256 của bản chụp trạng thái + line number, không phải Amazon review ID và không dùng để khẳng định review đã deduplicate giữa các bản chụp trạng thái có độ dài khác nhau.

## Amazon siêu dữ liệu

| trường | Type quan sát | Ý nghĩa / sử dụng | Thiếu tiền tố |
|---|---|---|---|
| `parent_asin` | str | ID gốc của sản phẩm/khóa tham gia | 0 null/absent |
| `title` | str | Tiêu đề sản phẩm; Bộ lọc laptop | 0 null/absent |
| `categories` | danh sách | Phân cấp danh mục; Bộ lọc laptop | 0 null/absent |
| `main_category` | str / null | Category lớn, không đủ chứng minh laptop | 222 null |
| `details` | mệnh lệnh | Bản ghi tùy chọn Brand/specs; use `Brand` khi có | 0 null/absent ở cấp object |
| `store` | str / null | Store; **không tự coi là thương hiệu** | 108 null |
| `features`, `description` | danh sách | Thông tin sản phẩm, chưa dùng làm filter | 0 null/absent |
| `average_rating` | phao | Rating sản phẩm; không phải rating review | 0 null/absent |
| `rating_number` | int | Số rating sản phẩm; không thay số review đã quan sát | 0 null/absent |
| `price` | nổi / vô giá trị | Giá crawl, thiếu nhiều | 11.363 null |
| `images`, `videos` | danh sách | Không tải media | 0 null/absent |
| `bought_together` | vô giá trị | Không dùng trong MVP | 20.000 null |
| `author`, `subtitle` | tùy chọn | siêu dữ liệu khác; không dùng trong MVP | Mỗi trường absent 19.990 |

Hugging Face có thể serialize `details` thành JSON string và `price` thành string; quy trình đọc nguồn gzip native, không giả định lược đồ của bản HF giống byte nguồn.

## SemEval laptop XML

Nguồn trial: [SemEval tác vụ 4](https://alt.qcri.org/semeval2014/task4/index.php?id=data-and-tools). Đã audit **trial**: 100 sentences, 49 aspects. Chưa có huấn luyện/kiểm thử được cấp quyền truy cập.

| trường | Gõ sau phân tích | Ý nghĩa / quy tắc |
|---|---|---|
| `sentence/@id` | str | Giữ gốc ID; reject missing/duplicate trong file |
| `text` | str | Giữ văn bản gốc, không chuẩn hóa trước kiểm tra vị trí cụm từ |
| `aspectTerm/@term` | str | Explicit term gốc, không canonicalize |
| `@from`, `@to` | int | Độ lệch ký tự `[from,to)`; `text[from:to] == term` |
| `@polarity` | str | Giữ gốc `positive/negative/neutral/conflict` |
| `original_split` | str | `train/test/trial` theo file nguồn; không trộn trial vào đánh giá so sánh |
| `sentiment` | str / null | Bản đồ nhận dạng lớp cho ba; conflict -> null, loại trừ ASC |
| `use_for_sentiment` | bool | false cho conflict; khía cạnh vị trí cụm từ vẫn dùng cho extraction |

Sentence không có khía cạnh giữ `aspects: []`. Unsupported cực tính cảm xúc hoặc lệch vị trí cụm từ bị báo lỗi. Policy conflict bảo toàn dữ liệu gốc; không đổi conflict thành neutral.
