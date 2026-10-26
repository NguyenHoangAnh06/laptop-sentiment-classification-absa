# P1 — Nghiên cứu khả thi dữ liệu

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

## toàn bộ review raw available — cập nhật mới nhất (2026-10-08)

toàn bộ Electronics review **6,47 GB** đã download/verify SHA256, size và bản kê complete_source. Transfer 87 phút 53 giây, bình quân 1,23 MB/s, không vượt ceilings. Xem [acquisition report](p1_reviews_full_acquisition.md). Chưa parse/decompress/streaming join hoặc survey; total/valid/clean-English laptop review số lượng toàn nguồn **NOT_MEASURED**. siêu dữ liệu preflight 28.172 ứng viên sản phẩm vẫn là bằng chứng trước; không chạy lại. Không suy rộng prefixes hoặc xem raw Electronics là laptop bộ dữ liệu đã lọc.

BLOCKED: toàn bộ laptop-only review survey chưa được phê duyệt; con người QA/language/clean yield/SemEval các tập đã chia vẫn đang chờ. NEXT_ACTION: người dùng xác nhận survey riêng, tiếp tục giữ mục tiêu 30K và các guards; không P2/training/domain expansion. lịch sử download blockers bên dưới đã được supersede cho download chỉ, không phải bằng chứng feasibility hoàn tất.

## toàn bộ siêu dữ liệu bằng chứng — mới nhất (2026-10-08)

toàn bộ Electronics siêu dữ liệu đã tải/verify và scan EOF **1.610.012 records**, cho **28.172 ứng viên laptop sản phẩm** theo mô hình cơ sở siêu dữ liệu filter. Loại **1.581.840 record decisions**, gồm insufficient bằng chứng 830.326, excluded category 328.872, accessory/ambiguous title 422.642. Record errors/explicit cross-group ambiguity đều 0. Title ambiguity riêng chưa đo vì lý do gộp; filter vẫn **unvalidated** (QA 100 đang chờ).

Đây là toàn bộ siêu dữ liệu số lượng, không phải review count/clean-English yield. ứng viên review vẫn chỉ 17 laptop trên prefix cũ; Smartphone/Tablet không được khảo sát thêm. 30K feasibility chưa thể kết luận trước review và quality/language tập xác thực. Peak working set 71,16 MB, index estimate 38,00 MB, scan 212,962 s, read budgeted 6,56 GB. Xem [toàn bộ siêu dữ liệu report](p1_metadata_full_preflight.md) và `tables/electronics_metadata_full_30k.json`. lịch sử “siêu dữ liệu chưa có”/tài nguyên estimates bên dưới được thay thế bởi đã đo bằng chứng này.

BLOCKED: review chưa được phép tải; download thời gian giới hạn 60 phút có nguy cơ không đủ nếu review throughput giống siêu dữ liệu ~1 MB/s (~108 phút cho 6,47 GB). NEXT_ACTION: người dùng quyết định bước review và ngân sách, con người QA thực sự và SemEval access; không tự tăng tài nguyên ceilings, không P2/training/domain expansion.

## Mục tiêu 30K — cập nhật hiện hành (2026-10-08)

Mục tiêu hiện tại **30.000 sạch tiếng Anh laptop review**; ghi chú 50k và mọi thước đo bên dưới giữ làm lịch sử. Không có dữ liệu mới hoặc suy rộng prefix: vẫn 17 Laptop/3 Smartphone/9 Tablet valid các ứng viên, language/clean số lượng và bản gần trùng **NOT_MEASURED**, con người filter **unvalidated**.

Đủ ~30K chất lượng tốt -> ưu tiên laptop-only; 15K–25K không tự coi thất bại, đánh giá lớp coverage/imbalance và product/brand diversity rồi đề xuất quy mô. Nếu quá ít/chất lượng kém, tìm nguyên nhân coverage/filter/duplicates/language/ nhãn trước đề xuất nguồn laptop khác hoặc khảo sát dự phòng, không tự đổi nguồn/domain. 30K phục vụ EDA/overall cảm xúc; ABSA phải dùng khía cạnh spans/polarities từ SemEval hoặc con người Amazon gán nhãn riêng, rating/keyword heuristic không phải ABSA truth. Không yêu cầu con người khía cạnh gán nhãn cả 30K; gold 300–500 vẫn độc lập.

84 kiểm thử chạy lại đạt. siêu dữ liệu-only prefix báo cáo được reuse/verify, không scan toàn bộ: 319 sản phẩm, EOF chưa quan sát/record_limit, coverage false; không có toàn bộ siêu dữ liệu file. `tables/p1_feasibility_30k_status.*` chỉ cập nhật mục tiêu context cho observations cũ.

BLOCKED: toàn bộ siêu dữ liệu chưa có/phê duyệt download còn thiếu; con người QA, SemEval các tập đã chia và sạch yield chưa đủ. NEXT_ACTION: phê duyệt siêu dữ liệu-only download/preflight trong ceilings hiện có; chỉ chuẩn bị review sau preflight đạt rồi xin phép riêng. Không P2/training.

## Hardening tập xác thực mới nhất (2026-10-08)

số lượng không đổi: **319/25/74 ứng viên sản phẩm**, **17/3/9 valid review** theo Laptop/Smartphone/Tablet. báo cáo mới: `tables/electronics_hardening_v4.json`, `cell_phones_hardening_v4.json`, `p1_feasibility_hardening.json/.csv`. Electronics 5,692 s / peak 30.601.216 byte / JSONL 197.040 byte; Cell Phones 1,103 s / peak 28.737.536 byte / JSONL 12.979 bytes. đầu ra tăng vì thêm `user_id`, `review_title`; review văn bản và join/rating số lượng giữ nguyên.

**84 kiểm thử passed**; local siêu dữ liệu-only probe trả PENDING/coverage false/reviews not_started đúng thiết kế. toàn bộ scan có điều kiện nghiệm thu bắt buộc siêu dữ liệu EOF + nguồn gốc nguồn phù hợp trước review scan; nguồn prefixes không đại diện và không được dùng kết luận 50k. Chưa con người QA, language tập xác thực, làm sạch hay ABSA nhãn.

[mức sẵn sàng report](p1_full_scan_readiness.md) thay thế kế hoạch full-scan cũ bên dưới: HEAD sizes đã xác minh lại; disk/RAM đo thực tế, ceilings, thời gian scenarios, metadata-only/laptop-only commands và quantity/quality/ABSA/scope criteria có đủ. Phần observations cũ bên dưới được giữ làm mô hình cơ sở so sánh; chưa tải/scan lớn.

Ngày khảo sát: 2026-10-08. **Refactor có kiểm chứng nhỏ; P1 chưa hoàn tất.** Smartphone/Tablet chỉ được khảo sát theo yêu cầu, không mở rộng phạm vi huấn luyện.

## Nguồn và độ phủ

Đã xác minh hai nguồn được [McAuley Lab công bố](https://amazon-reviews-2023.github.io/): Electronics và Cell Phones and Accessories, cả review lẫn siêu dữ liệu. HEAD/schema probe ở `reports/tables/p1_source_probe.json`; gốc manifests giữ provenance. Join key cả hai nguồn là `parent_asin`, không phải variant `asin`.

- Electronics: tái sử dụng 20.000 siêu dữ liệu + 100.000 review nguồn đang có.
- Cell Phones and Accessories: mới lấy 5.000 siêu dữ liệu / **17.952.345 byte**,
  20.000 review / **11.680.327 byte**, giữ nguyên nguồn lines và checksum.
- Tổng raw probe Amazon hiện có: 25.000 siêu dữ liệu + 120.000 review, **170.085.365 byte**.
  Đây không phải 120.000 review sản phẩm mục tiêu; đa số là ngoài target/không có parent trong được chọn index. Không tải toàn bộ nguồn trong nhiệm vụ này.

Snapshots là **prefix có thiên lệch thứ tự**. New quy trình xử lý siêu dữ liệu trước review; nguồn completeness vẫn false vì nguồn gốc bản chụp trạng thái partial. Không thể dùng số lượng nhỏ này để suy ra Amazon thiếu laptop/smartphone/tablet.

## Observations trên subset thực tế

Các nhóm có review hiện nằm ở nguồn riêng trong hai probe: Laptop/Tablet ở Electronics, Smartphone ở Cell Phones. Không có tuyên bố loại trùng toàn hai corpus.

| Số liệu | laptop | điện thoại thông minh | Máy tính bảng |
|---|---:|---:|---:|
| Sản phẩm ứng viên | 319 | 25 | 74 |
| Matched review với được chọn index | 17 | 3 | 9 |
| Valid review theo lược đồ, văn bản không rỗng, rating 1–5 | 17 | 3 | 9 |
| Unique products with review | 11 | 1 | 6 |
| Average normalized review length (words) | 110,65 | 93,00 | 130,33 |
| Tỷ lệ trùng lặp chính xác được chuẩn hóa | 0% | 0% | 0% |
| Số lượng đánh giá 1/2/3/4/5 | 1/0/1/3/12 | 0/1/0/0/2 | 1/0/1/3/4 |
| Phân phối ngôn ngữ | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| khía cạnh coverage heuristic | 52,94% | 33,33% | 55,56% |
| review dưới 5 từ | 0% | 0% | 0% |
| Known brands có review | 6 | 1 | 6 |
| thương hiệu thiếu trên valid review | 0 | 0 | 0 |
| Thị phần sản phẩm lớn nhất | 35,29% | 100% | 33,33% |
| Clean tiếng Anh review count | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| Tỷ lệ gần trùng lặp | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |
| con người filter precision/recall | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED |

trùng lặp là extra occurrence của normalized/casefolded **văn bản**, chia valid review count. Không đồng nghĩa unique users, gần trùng hoặc đã loại trùng bộ dữ liệu. khía cạnh heuristic = review >=10 từ và chứa ít nhất một keyword cấu hình; đây là đại diện “potentially useful for ABSA”, **không phải extracted vị trí cụm từ hoặc cảm xúc nhãn**. Language chưa chạy detector phù hợp; không gọi valid review là sạch tiếng Anh.

Rating đại diện lớp số lượng: laptop negative/neutral/positive **1/1/15**, Smartphone **1/0/2**, Tablet **1/1/7**. Đây là subset bias, không dùng chọn lớp weights hoặc cân bằng huấn luyện. Rating overall không gán nhãn mọi khía cạnh.

độ dài bins (từ): laptop 5–19/20–99/100+ = **5/7/5**; Smartphone = **1/0/2**; Tablet = **3/3/3**. Trong các matched records này chưa thấy thiếu required text/rating hoặc invalid rating; null/absent số lượng toàn nguồn nằm ở JSON profiles.

Electronics: 26 mục tiêu-index matches (17 laptop + 9 Tablet), 99.974 không thuộc được chọn index. Cell Phones: 3 mục tiêu matches, 19.997 không thuộc được chọn index. Không diễn giải nhóm còn lại là siêu dữ liệu thiếu: nhóm này còn gồm accessories và sản phẩm không được chọn. Số 3.726 cũ join là join **mọi siêu dữ liệu của prefix**, không cùng denominator với mục tiêu-index matches.

CSV/JSON chi tiết: `reports/tables/p1_feasibility_small.*`, `electronics_refactor.json`, `cell_phones_refactor.json`. Mọi thước đo vắng mặt được ghi NOT_MEASURED thay vì estimate như số thực đo.

## thời gian, bộ nhớ và I/O thực đo

| Đầu dò nguồn | Đã qua | Bộ làm việc cao điểm | Ước tính tải trọng chỉ mục đã chọn | Đọc I/O |
|---|---:|---:|---:|---:|
| Điện tử | 5,414 s | byte 30.871.552 | byte 523.860 | Băm 140.452.693 + byte được giải mã 140.452.693 |
| Điện thoại di động | 1,097 s | byte 29.429.760 | byte 28.174 | Băm 29.632.672 + byte được giải mã 29.632.672 |

Thời gian gồm checksum, scan và đầu ra, chưa gồm acquisition qua mạng. Working set gồm Python process/modules, không phải chỉ index. Không có RAM/time đánh giá so sánh cho cũ quy trình hoặc toàn bộ corpus. Một checksum pass + một siêu dữ liệu pass + một review pass; gzip decoding là streaming. đầu ra JSONL tổng: 192.342 và 12.391 byte, gồm sản phẩm, valid và mẫu; QA/JSON báo cáo có thêm overhead nhỏ.

## Khả năng đạt 50.000 và lựa chọn phạm vi

**Chưa thể kết luận đủ hoặc thiếu 50.000 sạch tiếng Anh laptop review.** Hiện chỉ có 17 valid ứng viên laptop. Giới hạn nằm ở độ phủ nguồn, filter chưa validated, language/cleaning/dedup chưa hoàn tất; không phải bằng chứng laptop tập ứng viên toàn Amazon nhỏ.

Đề xuất hiện tại: **giữ laptop-only**. Khảo sát Smartphone/Tablet không đủ để chứng minh lợi ích mở rộng, nhất là Smartphone chỉ 1 product. Mở rộng thật sẽ thay scientific contract/ABSA benchmark/gold gán nhãn; cần quyết định riêng sau full-pool evidence. Không gộp ba nhóm để lấp quota.

## Thiết kế làm sạch và lấy mẫu ở bước sau

1. **Raw**: nguồn bytes/manifests bất biến, review IDs nguồn và parent links.
2. **Valid**: schema/identifier, rating 1–5, văn bản không rỗng. P1 chỉ lưu tầng này.
3. **sạch tiếng Anh**: chuẩn hóa HTML/whitespace có bảo toàn negation; exact normalized
   trùng lặp audit theo product/users; language identification có policy cho mixed/ uncertain language; con người mẫu để kiểm tra. Near-duplicates cần thử threshold trên mẫu, group bản trùng trước splitting. Chưa có detector/threshold được validate.
4. **Overall labeled**: thêm rating đại diện mapping 1–2/3/4–5, nguồn gốc và nhãn-nhiễu
   study; giữ gold do người gán nhãn độc lập, không mô hình-select trên gold.
5. **khía cạnh labeled**: chỉ gốc SemEval spans/polarities hoặc con người Amazon gán nhãn;
   không suy ra từ star rating hay keyword coverage.

mẫu P1 hiện giữ 17/3/9, hạt giống ngẫu nhiên 42, sản phẩm giới hạn 100; max thực tế 6/3/3 reviews/product. Với tập ứng viên lớn: bounded hàm băm reservoir dùng cho survey, không trực tiếp hứa cho cuối cùng 50k. Thiết kế cuối cùng mẫu nên audit sản phẩm concentration, proportional rating quotas (giữ lớp hiếm khi khả thi), sản phẩm giới hạn có lý do, thương hiệu coverage khi siêu dữ liệu đủ tin cậy. Nếu reservoir không đủ diversity sau giới hạn, cần nhiều lượt file xử lý để tăng reservoir/per-product coverage, ghi rõ số lượt và I/O giới hạn tài nguyên; không tự oversample kiểm thử hoặc thay distribution. Lưu full-pool/sample phân bố và nguồn IDs.

phân chia proposal vẫn 70/15/15 hạt giống ngẫu nhiên-controlled, ưu tiên product/parent-disjoint khi đánh giá unseen laptops; group near-duplicates và kiểm tra độ bao phủ lớp, ghi rõ deviation từ stratification. gold phải dành riêng trước training/model selection. Trong nhiệm vụ này chưa tạo các tập đã chia, chưa chuyển P2 hoặc huấn luyện.

## Phương án lớn chờ phê duyệt

NGÀY 2026-10-08:

| Nguồn | gzip siêu dữ liệu | gzip review | Tổng số lượt tải xuống |
|---|---:|---:|---:|
| Điện tử | 1.312.900.427 | 6.474.438.619 | 7.787.339.046 byte (~7,79 GB) |
| Điện thoại di động và phụ kiện | 857.990.660 | 2.532.539.010 | 3.390.529.670 byte (~3,39 GB) |
| Cả hai | | | 11.177.868.716 byte (~11,18 GB) |

Đề xuất ưu tiên **Electronics trước**: siêu dữ liệu đầy đủ -> compact laptop/tablet index -> review đầy đủ -> số lượng và QA. Đây khắc phục coverage/join bằng kiểm tra toàn siêu dữ liệu trước, không chỉ tăng hai prefix. Cell Phones toàn bộ là lựa chọn khảo sát bổ sung riêng, không bắt buộc cho laptop-only.

Ngân sách đề xuất Electronics: **12 GB free disk**, gồm 7,79 GB gzip nguyên bản, đầu ra giới hạn 2 GB và margin. Cả hai các nguồn: **18 GB free disk** (11,18 GB raw + hai đầu ra ceilings 4 GB + margin). Không giải nén thành dump khổng lồ. RAM kiểm tra giới hạn 512 MB; index estimated giới hạn 128 MB; reserve khoảng **1 GB RAM available** cho process/system overhead. Nếu vượt kiểm tra giới hạn thì dừng, chưa có partition fallback tự động.

thời gian **estimate, chưa đo toàn bộ**: giả định network 10–30 MB/s, download Electronics khoảng 4,3–13 phút (chưa tính overhead/retry). Dự trù scan **20–90 phút/source**; đây là planning scenario, không benchmark/extrapolation về số laptop. Scan kiểm tra giới hạn 4 giờ/source và 60 GB tổng checksum + decoded read I/O; decoded toàn bộ byte nguồn **NOT_MEASURED**, có thể cần đổi giới hạn tài nguyên với phê duyệt nếu limit bị chạm.

Mục tiêu: đã đo mục tiêu product/review số lượng, rating/length/duplicate/brand phân bố và filter QA đủ để đánh giá quota. 50k clean-size/yield vẫn cần English/quality tập xác thực; chưa biết phải quét thêm **bao nhiêu review** để đạt nó. HTTP resume chưa triển khai; một phần có hash/failure record và không append.

Lệnh đã chuẩn bị, **CHƯA CHẠY**:

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata --category Electronics --full --allow-large-download
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews --category Electronics --full --allow-large-download
.\.venv\Scripts\python.exe -m scripts.audit_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --reviews data/raw/amazon/Electronics.jsonl.gz --run electronics_full --mode scan --allow-large-scan
```

hiện tại user tác vụ §7/§13 yêu cầu dừng trước download/scan lớn để xin phép.

BLOCKED: chưa có toàn bộ metadata/review nguồn coverage hoặc con người filter QA. NEXT_ACTION: người dùng xem ngân sách Electronics ở trên, cho phép nếu phù hợp; đồng thời điền QA CSV được liệt kê trong `qa_rule_sha256` của báo cáo mới.

BLOCKED: gốc SemEval laptop huấn luyện/kiểm thử chưa có; language và sạch yield chưa đo. NEXT_ACTION: lấy gốc các tập đã chia qua quyền truy cập hợp lệ; sau khi đủ P1 bằng chứng mới triển khai cleaning/language tập xác thực ở P2. Giữ gold 300–500 review cho người gán nhãn.

Giới hạn: laptop-only findings; rating nhãn đại diện nhiễu; SemEval-to-Amazon platform/ style shift trong laptop review; small bộ gold do con người gán nhãn set. Không claim cross-gadget generalization, Transformer hiệu năng hoặc production readiness.
