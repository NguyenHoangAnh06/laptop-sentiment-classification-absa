# P1 — Từ điển dữ liệu

## P2 đã xử lý bộ dữ liệu - 2026-10-09

`data/processed/laptop_reviews.parquet`:30k đã chọn laptop review, không phải tất cả các ứng viên hợp lệ. `raw_text` bảo tồn văn bản nguồn; `text` là tính năng dọn dẹp khoảng trắng HTML/entity/ bảo thủ. Các trường IDs/source_line/parent_asin/asin/metadata duy trì liên kết nguồn. Xếp hạng `sentiment`=negative/neutral/positive from1-2/3/4-5; `label_id`=0/1/2; `label_provenance`=`rating-derived proxy`. Không có con người cảm xúc nhãn. `brand_raw` và `brand_normalized` là loại siêu dữ liệu, chưa được nhà sản xuất xác minh. `quality_flags` là một danh sách chuỗi các phương pháp phỏng đoán cần thiết của review, không phải sự thật nhãn. `clean_text_sha256` băm văn bản được đóng hộp đã được làm sạch cho các bộ bảo vệ dedup/leakage chính xác. `language`=`en` là lựa chọn máy dò tự động, không phải nhãn chuẩn được xác thực con người; `language_detector_score` là điểm tương đối của Lingua được làm tròn 8 chữ số thập phân, không xác suất được hiệu chỉnh hoặc cảm xúc độ tin cậy. `near_duplicate_group_id` là null, để phân nhóm P4 sau này nếu tìm kiếm từ vựng gần đúng tìm thấy một cặp; lần chạy cuối cùng không có. Các phần bù ký tự raw/clean gốc không thể thay thế cho ABSA gán nhãn sau này. Các ứng viên 250 chẩn đoán nhiễu có `noise_candidate_reasons` và `annotation_status=UNANNOTATED_DIAGNOSTIC_NOT_GOLD`, được lưu riêng biệt với các hàng đã xử lý; chúng không phải là gold độc lập P10. Manifest/ledger/label và bảng nhãn hiệu: `reports/p2_amazon_completion_20261009.md`. Không có cột phân chia hoặc dự đoán được đào tạo.


## Kiểm tra QA và ứng viên hiện tại - 2026-10-09

Các lược đồ gán nhãn gốc không thay đổi. Canonical v2 sử dụng laptop/non_laptop trong khi CSV đã gửi vẫn giữ lại ACCEPT/REJECT; Cần có liên kết source/canonical SHA256 đã được phê duyệt để ghi đè người đánh giá. Hỗ trợ AI null có nghĩa là lịch sử không xác định, không phải không có hỗ trợ; Phê duyệt con người đã hoàn thành tách biệt với việc chấp nhận độc lập. human_is_laptop kế thừa và human_is_target_product khả thi là các lược đồ riêng biệt; Các hàng tiền tố trống 100-mô hình cơ sở là QA kế thừa tùy chọn, không phải đơn vị lấy mẫu v1/v2. Các cụm text_sha256 ứng viên là các khóa kiểm tra văn bản chuẩn hóa, không phải nguồn IDs/labels. Trùng lặp dư thừa=tổng(count-1), bị ảnh hưởng=tổng(đếm); nhóm dấu câu là ứng cử viên, không phải bằng chứng trùng lặp ngữ nghĩa. Sự chồng chéo QA cho thấy rủi ro cô lập trong tương lai; chưa có các tập đã chia nào tồn tại. Số lượng xếp hạng đại diện không phải là con người cảm xúc gold. Bằng chứng hiện tại: reports/p1_qa_v2_completion_20261009.md và reports/candidate_quality_preflight_20261009.md.

## con người QA (đã đánh giá; hỗ trợ AI được tiết lộ)

Bộ sản phẩm: `data/manual/independent_qa/p1_v1/`. Hướng dẫn: `docs/INDEPENDENT_HUMAN_QA.md`. nhãn hiện tại được `human_reviewer_01` cung cấp và xác minh sau một số đề xuất của AI; Codex không tạo ra con người nhãn trong nhiệm vụ đánh giá này. Đây là sản phẩm-phạm vi QA, không phải sentiment/ABSA gold.

| Trường / tệp kết quả | loại | Ý nghĩa |
|---|---|---|
| `annotation_id` | chuỗi | ID tham gia xác định mờ đục cho sidecar riêng tư; giữ nguyên dưới dạng văn bản |
| `product_id` | chuỗi | Khóa tham gia `parent_asin` thực tế, không phải biến thể `asin` |
| `review_id` | chuỗi | Nguồn SHA256 + ID xuất xứ dòng vật lý thô, không phải ID gốc của Amazon |
| `title`, `review_title`, `review_text` | Chuỗi CSV | Tiêu đề sản phẩm gốc / Tiêu đề review / Văn bản review; không dọn dẹp |
| `categories`, `description`, `features`, `details` | JSON trong ô CSV/trống | siêu dữ liệu, null/missing được chọn ban đầu -> trống; không có thông số kỹ thuật bịa đặt |
| `source_evidence` | JSON trong ô CSV | Đã xác minh ảnh chụp nhanh nguồn hash/file/physical và liên kết; cha mẹ mất tích được ghi lại rõ ràng |
| `product_url` | chuỗi | Đã tạo gợi ý tra cứu, không phải bằng chứng trực tiếp visited/verified |
| `human_label` | trống / laptop / non_laptop / không chắc chắn | con người nhị phân được xem xét phạm vi nhãn, không phải cảm xúc; tiết lộ riêng hỗ trợ AI |
| `human_evidence`, `human_notes` | văn bản trống/tự do | Các nguồn và giải thích được kiểm tra bởi con người; bằng chứng cần thiết cho nhãn không trống |
| `human_error_reason` | enum trống/có tài liệu | Nguyên nhân do con người chọn, không được AI suy ra; không khớp mà không có lý do vẫn chưa được phân loại |
| `private_predictions.json` | danh sách JSON | Dấu vân tay hàng đã cố định task/stratum/prediction/reason/N/n/probability và cố định; không bao giờ mở trong gán nhãn |
| `manifest.json` | đối tượng JSON | Số lượng Source/output SHA256, rules/aliases/seed/version, frame/sample và bằng chứng tài nguyên |

Các tệp CSV con người không chứa các quyết định, lý do hoặc tầng lớp quy trình; xáo trộn một cách độc lập. Chỉ có thể chỉnh sửa bốn cột con người. CSV xác định; chỉ thư mục đầu ra mới. Khung sản phẩm ngẫu nhiên: 28,172 chọn lọc sản phẩm độc đáo. Khung review: 408,480 hợp lệ KEEP + 43,478,204 siêu dữ liệu-bản ghi TỪ CHỐI không được chọn; Đã loại trừ các bản ghi được chọn nhưng không hợp lệ của 260. Các tập hợp con chẩn đoán tách biệt với ước tính đại diện. Trọng số `N/n` trong tầng ước tính sự nhầm lẫn review totals/Precision/Recall/F1 chỉ sau khi tất cả nhãn ngẫu nhiên được giải quyết; blank/uncertain vẫn chưa được biết. Ước tính mẫu sản phẩm chỉ GIỮ độ chính xác dự đoán (precision) chứ không phải recall/F1. Mâu thuẫn nhãn đối với một sản phẩm cần được đánh giá. Tập lệnh không tự động chứng nhận tính độc lập của con người hoặc tự động thay đổi danh sách kiểm tra chấp nhận. Raw/pool/legacy QA không thay đổi.

## Lược đồ đầu ra v4 cứng hơn

Valid/sample JSONL giữ thêm nullable `user_id` và `review_title` (alias nguồn `title/summary`), cùng `asin`, `parent_asin`, `timestamp`, `verified_purchase`, `helpful_vote`, `review_id`, `text`, `rating`, `product_title`, `brand`, `group`, `source`, `source_line`. thiếu optional các trường -> null, không tạo giá trị thay. văn bản nguyên gốc; `review_id` vẫn là nguồn gốc ID tạo từ nguồn SHA256+physical line, không phải ID review Amazon. Reviewer IDs chỉ nằm trong ignored dữ liệu files.

Scanner báo `eof_observed`, `oversized_records`, `malformed_records`, `truncated_records` (nghi JSON bị cắt cuối file), invalid totals và stop reason. EOF của local prefix không đủ nguồn coverage; siêu dữ liệu-only preflight không chứng nhận review coverage. Counts/schema profiles mới ở `*_hardening_v4.json`.

## Phạm vi hiện hành — laptop-only

Electronics là danh mục nguồn; `group` trong survey chỉ có `laptop`. toàn bộ metadata/review lược đồ số lượng ở `reports/tables/electronics_full_laptop_30k.json`: 1.610.012 siêu dữ liệu / 43.886.944 review; cả hai EOF và nguồn coverage true. toàn bộ valid tập ứng viên 408.480 review là ứng viên tập ứng viên, chưa phải sạch English/deduplicated. Các lịch sử multi-phạm vi profiles chỉ là bằng chứng cũ, không quy trình hiện hành.

`source_coverage_complete`: complete-source manifests + observed EOF cả hai files. `not_in_selected_metadata_index`: gồm ngoài phạm vi và parents không trong được chọn index; không diễn giải thành thiếu siêu dữ liệu của toàn nguồn. `human_is_target_product`: QA sản phẩm nhãn, hỗ trợ True/False và cũ yes/no; blank/unsure là đang chờ. QA hiện hành có 100 AI-assisted, user-approved nhãn, không phải độc lập bộ gold do con người gán nhãn. `human_notes` giữ nguyên provenance/source evidence. mô hình cơ sở `human_is_laptop` cũ vẫn được hỗ trợ; không tự chuyển hoặc ghi đè nhãn.

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

## SemEval laptop XML? JSONL chuẩn hóa

Số liệu thống kê và xuất xứ Train/Test địa phương đã được xác minh: `reports/p1_semeval_laptop.md`; bảng kê khai input/output đầy đủ: `reports/tables/p1_semeval_normalization.json`. Gương GitHub do người dùng cung cấp để nghiên cứu cá nhân; Giấy phép bộ dữ liệu và nhận dạng byte chính thức chưa được xác minh.

| trường | loại | Ý nghĩa/chính sách còn thiếu |
|---|---|---|
| `source` | str | `semeval2014_laptop` |
| `split` | str | `train` hoặc `test` gốc, không bao giờ kết hợp |
| `sentence_id` | str / null | ID XML gốc, các số 0 đứng đầu được giữ nguyên; bị thiếu gắn cờ |
| `text` | str | Văn bản gốc được giải mã XML, không chuẩn hóa; lược đồ văn bản bị thiếu bị từ chối, được gắn cờ trống |
| `aspects` | danh sách | Đặt hàng các điều khoản ban đầu; danh sách trống được giữ lại |
| `aspects[].term` | str / null | Thuật ngữ rõ ràng, không chuẩn hóa; bị thiếu được gắn cờ bởi kiểm tra vị trí cụm từ |
| `aspects[].start/end` | int / str / null | Ký tự Python nửa mở vị trí cụm từ; bản gốc không đúng định dạng được giữ lại và gắn cờ |
| `aspects[].polarity` | str / null | positive/negative/neutral/conflict gốc; missing/unknown được gắn cờ |
| `aspects[].xml_attributes` | dict[str,str] | Các thuộc tính gốc bao gồm các chuỗi từ vựng from/to, được bảo tồn mà không cần sửa chữa |

Không có trường ánh xạ cảm xúc hoặc trường đủ điều kiện huấn luyện trong JSONL được chuẩn hóa. Xung đột vẫn còn conflict; Chính sách ASC ba lớp trong tương lai phải rõ ràng. `parse_semeval` kế thừa vẫn nghiêm ngặt và hiển thị bản đồ cảm xúc lịch sử của nó; bình thường hóa không sử dụng nó. XML elements/attributes/hierarchy không mong đợi thay vì mất nhãn gán một cách âm thầm. Giá trị chênh lệch đề cập đến văn bản được giải mã XML, không phải chính tả thực thể XML thô hoặc giá trị bù byte. Đầu ra: `data/interim/semeval/{train,test}_sentences.jsonl`, UTF-8 xác định; biến đổi `semeval_sentences_v1`. XML thô được giữ lại không thay đổi. Xác minh đầy đủ round-trip/count/order PASS. Các bản ghi được chuẩn hóa là nền tảng ATE/ASC, không phải bộ dữ liệu BIO/training.


Xuất xứ đánh giá: `human_verified_after_ai_assistance` khi CLI `--ai-assisted-review` được cung cấp; `annotation_process` ghi lại con người review không mù hoàn toàn. Legacy `independent_human_declared` là bản tự tuyên bố dành cho các hoạt động không tiết lộ thông tin đó, không có mã chứng nhận độc lập. Không tự động đóng cổng chấp nhận dự án. Bằng chứng date/notes được khuyến nghị, không yêu cầu lược đồ cứng; bằng chứng ngắn không trống được chấp nhận theo hướng dẫn mới nhất của người dùng. Các phép đo hiện tại và thống kê phạm vi: `reports/p1_independent_human_qa.md`.


## Bổ sung REJECT QA v2 và lược đồ phân tích thương hiệu

Kit `data/manual/independent_qa/p1_v2/` tái dùng REVIEW_COLUMNS và bốn con người các trường; không thêm prediction/stratum vào gán nhãn CSV. Sidecar chứa `random_reject_complement`, N43.478.054, n868, `inclusion_probability=n/N`, `sampling_weight=N/n`; v1 ngẫu nhiên REJECT150 là certainty units khi kết hợp. bản kê binds v1 evaluation/annotations, source/index hàm băm, hạt giống ngẫu nhiên và populations; 260 selected-but-invalid vẫn ngoài suy luận frame. All v2 nhãn currently blank. Future đầu ra `combined_weighted_estimates` chứa design totals, P/R/F1 và joint95% hypergeometric/Bonferroni intervals; pending/uncertain/conflicts -> null.

thương hiệu bảng `reports/tables/p1_brand_diversity_v1/`: sản phẩm records giữ `brand_raw`, `brand_normalized`, `brand_status`, `title_brand_hint`, `title_hint_ambiguous`, `metadata_title_disagreement`, `review_count`. Raw thương hiệu là siêu dữ liệu details.Brand, không store. Exact aliases và Unicode/case chuẩn hóa; missing/generic=UNKNOWN, multi-brand delimiters=AMBIGUOUS; title hints không thay siêu dữ liệu. Other siêu dữ liệu categories không chứng minh đã xác minh manufacturers. `brands.csv` có product/review counts/shares và review-minus-product share; denominators28.172 products/408.480 valid review, chưa sạch tiếng Anh. Methods/gates: độ bao phủ (recall)-reliability và brand-diversity báo cáo; không có mô hình scores.
