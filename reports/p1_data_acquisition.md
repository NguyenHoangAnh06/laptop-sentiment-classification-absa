# P1 — Thu thập và hiểu dữ liệu

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

## toàn bộ Electronics review — kết quả mới nhất (2026-10-08)

Đã thực hiện phê duyệt **download/integrity chỉ**: review gzip **6.474.438.619 byte**, SHA256 đọc lại khớp bản kê, `source_eof`, `complete_source=true`, file size/source URL khớp. Transfer **5.272,919 s (87 phút 53 giây)**, bình quân **1,23 MB/s**; ceilings **10.800 s / 6,6 GB** giữ nguyên và không chạm. Không retry/resume; không có partial/failure. Disk còn **78,69 GB**, RAM khả dụng **4,22 GB** tại thời điểm verification.

Mọi raw/QA files có sẵn giữ nguyên sizes/mtime; siêu dữ liệu không overwrite/delete hoặc preflight lại. Code/config không đổi. **Chưa chạy streaming join, survey, P2 hoặc huấn luyện.** Chi tiết [p1_reviews_full_acquisition.md](p1_reviews_full_acquisition.md) và `tables/p1_reviews_download_execution.json`. GZIP header hợp lệ; toàn bộ CRC/JSONL scan chưa chạy. Các mục “review chưa tải/chưa được phép tải” bên dưới là lịch sử trước phê duyệt mới.

BLOCKED: streaming join/full laptop survey chưa được phê duyệt. NEXT_ACTION: người dùng xác nhận bước survey riêng sau khi xem acquisition results; chưa kết luận 30K sạch yield.

## review time-budget preparation — mới nhất (2026-10-08)

User yêu cầu tách full-download thời gian ceilings: siêu dữ liệu **3.600 s**, review **10.800 s (180 phút)**. cấu hình và CLI đã sửa tối thiểu, review byte giới hạn vẫn **6,6 GB**; không thay downloader/resume hoặc scan/RAM/index/I/O ceilings. Hai CLI dữ liệu mẫu kiểm thử mới xác nhận source-specific giới hạn tài nguyên; **86 kiểm thử pass**, dependency/syntax checks đạt. Chưa download review hoặc chạy lại toàn bộ siêu dữ liệu preflight.

Disk hiện **86.874.882.048 byte** trống; không có full/partial review Electronics. siêu dữ liệu toàn bộ có sẵn, size/manifest/SHA256 references khớp bằng chứng đã verify; preflight 1.610.012 records/28.172 candidates/EOF complete được tái sử dụng làm bằng chứng. Xem phần mới nhất của [mức sẵn sàng report](p1_full_scan_readiness.md) cho lệnh chuẩn bị, timeout mạng 30 giây, no-resume risks và budget. Các nhận xét giới hạn review 60 phút bên dưới là lịch sử, không phải cấu hình hiện hành.

BLOCKED: chưa được phép toàn bộ review download/survey. NEXT_ACTION: chờ người dùng phê duyệt download; giữ Laptop-only/30K, không P2 hoặc huấn luyện.

## toàn bộ Electronics siêu dữ liệu — kết quả mới nhất (2026-10-08)

Theo phê duyệt của người dùng, đã tải toàn bộ siêu dữ liệu **1.312.900.427 byte**, giữ gzip nguyên bản và bản kê; SHA256 đọc lại khớp. Transfer elapsed **1.312,77 s**. laptop-only preflight quét **1.610.012 records** đến EOF, **28.172 ứng viên sản phẩm**, **0 invalid/oversized records**, siêu dữ liệu coverage complete=true. Peak working set **71.163.904 byte**, index estimate **38.002.675 byte**, elapsed **212,962 s**, budgeted checksum+decoded read **6.559.044.561 byte**; không chạm ceilings.

Năm raw Amazon files/checksums và new output/QA fingerprints đều verify; 84 kiểm thử chạy lại đạt. Không code refactor/ceiling changes; không overwrite/delete raw. Chi tiết exclusions, GZIP integrity, QA và tài nguyên bằng chứng ở [p1_metadata_full_preflight.md](p1_metadata_full_preflight.md). Các mục “chưa có metadata/chờ phê duyệt siêu dữ liệu” bên dưới là lịch sử trước lượt tải này.

BLOCKED: chưa phê duyệt review download/scan; con người QA và gốc SemEval các tập đã chia đang chờ. NEXT_ACTION: quyết định review sau khi xem siêu dữ liệu results; throughput siêu dữ liệu ~1 MB/s gợi ý review có thể cần ~108 phút nếu tốc độ tương tự, vượt download giới hạn 60 phút. Không tăng giới hạn hoặc tiếp tục review tự động. P1 chưa hoàn tất; mục tiêu 30K giữ nguyên.

## Mục tiêu 30K — trạng thái hiện hành (2026-10-08)

Mục tiêu mới **30.000 sạch tiếng Anh laptop review**, thay 50.000; không phải quota bắt buộc. tập ứng viên 15.000–25.000 chất lượng cao cần đánh giá class/product diversity, không hạ chất lượng hoặc trộn phạm vi. Những số 50k phía dưới là lịch sử; raw/observations/manifests và báo cáo bảng cũ giữ nguyên.

Đã xác minh thực tế: **chưa có `meta_Electronics.jsonl.gz` đầy đủ**. Có 4 Amazon prefix JSONL, tổng 170.085.365 byte, checksum đều MATCH; siêu dữ liệu manifests partial. tái sử dụng siêu dữ liệu-only prefix báo cáo đã verify source/output/QA fingerprints: 20.000 siêu dữ liệu records, 319 ứng viên laptop sản phẩm, stop `record_limit`, `eof_observed=false`, coverage false, review `not_started`. Không gọi đây là toàn bộ preflight. số lượng review trước đó vẫn 17 Laptop/3 Smartphone/9 Tablet; không chạy scan review mới.

HEAD-only kiểm tra lại siêu dữ liệu **1.312.900.427 byte**, không tải body. Disk hiện **75.439.374.336 byte** trống. Chạy lại `.venv\Scripts\python.exe -m pytest -q`: **84 passed, 0 failed**. Không refactor quy trình hoặc tăng tài nguyên ceilings; siêu dữ liệu-only báo cáo bổ sung các counters filtering/baseline/join đã được tính sẵn để toàn bộ preflight báo lý do loại/ambiguity/invalid identifiers; kiểm thử preflight hiện có kiểm tra các trường này. tóm tắt CLI dùng bộ dữ liệu mục tiêu từ cấu hình thay vì hard-code 50k. bằng chứng mới: `tables/p1_30k_acquisition_status.json`, `p1_feasibility_30k_status.json/.csv`; tóm tắt mới tái sử dụng observations cũ, không phải phép đo mới/full-source evidence.

BLOCKED: thiếu phê duyệt mới cho toàn bộ siêu dữ liệu ~1,31 GB + siêu dữ liệu-only scan. NEXT_ACTION: người dùng phê duyệt hai thao tác siêu dữ liệu ở mức sẵn sàng báo cáo; giữ gzip/raw bất biến, dùng downloader/checksum/manifests hiện có. Chưa tải toàn bộ siêu dữ liệu, chưa toàn bộ scan, review download không được phép. Sau preflight đạt sẽ báo counts/resources và xin phê duyệt riêng review; P1 chưa hoàn tất, chưa P2/training.

## quy trình hardening — bằng chứng mới nhất (2026-10-08)

**84 kiểm thử passed** trong `.venv`; dependency/syntax checks đạt. Chạy lại hai local snapshots, số lượng giữ **17 laptop / 3 Smartphone / 9 Tablet**; 5 raw checksums khớp manifests, đầu ra JSON/checksums và QA fingerprints hợp lệ. Không tải thêm bộ dữ liệu. Các mục 60/33 kiểm thử bên dưới là lịch sử, không thay thế kết quả mới này.

HEAD-only xác minh lại Electronics siêu dữ liệu **1.312.900.427** và review **6.474.438.619 byte**, tổng **7.787.339.046 byte**. `scan` nay chặn review scan nếu siêu dữ liệu chưa EOF/provenance đầy đủ hoặc có lỗi. CLI có `--metadata-only` để kiểm siêu dữ liệu trước tải review và `--groups laptop` cho toàn bộ laptop survey.

Kế hoạch/lệnh/tài nguyên/authorization điều kiện nghiệm thu mới nhất ở [p1_full_scan_readiness.md](p1_full_scan_readiness.md). toàn bộ download/large scan **CHƯA CHẠY**; chưa đổi ceiling/domain hoặc chuyển P2. P1 vẫn BLOCKED vì coverage, con người QA và gốc SemEval các tập đã chia. NEXT_ACTION: xem và phê duyệt kế hoạch có điều kiện.

## Cập nhật sau refactor feasibility (2026-10-08)

quy trình hiện tại dùng siêu dữ liệu-first compact index -> streaming join -> JSONL từng group -> bounded sampling/QA. `scripts/audit_p1.py` mặc định chạy quy trình mới; code prefix audit cũ chỉ dùng `--legacy-prefix` cho diagnostics, không làm bộ dữ liệu cuối. phạm vi training/inference vẫn laptop; smartphone/tablet nằm ở survey cấu hình riêng.

Dữ liệu mới thu thập nhỏ từ Cell Phones and Accessories: **5.000 siêu dữ liệu, 20.000 review**, 29.632.672 byte decoded giữ nguyên nguồn lines trong `data/raw/amazon/Cell_Phones_and_Accessories_*_probe_*.jsonl`, kèm nguồn URL, ETag, Last-Modified, SHA256 và `complete_source: false`. Electronics và SemEval raw hiện có được tái sử dụng, không overwrite/xóa; corrected sidecars cũ cũng giữ nguyên. Không toàn bộ download/scan lớn hoặc database.

Kết quả nhỏ mới: **laptop 17, Smartphone 3, Tablet 9 valid ứng viên review**; không gọi chúng là sạch English/gold cảm xúc dữ liệu. Filter cả ba nhóm unvalidated. Schema/HEAD probe cả review và siêu dữ liệu của hai nguồn đã chạy; nguồn sizes và ETags trong `reports/tables/p1_source_probe.json`. License/access observations trong phần lịch sử bên dưới vẫn áp dụng: chưa có giấy phép Amazon rõ ràng được xác minh; không tái phân phối raw, không dùng SemEval mirror chưa xác minh.

Kiểm chứng hiện tại: **60 kiểm thử pass**; dữ liệu mẫu full-scan branch, checksum/malformed data/network body thiếu, lấy mẫu và bộ nhớ guards đều có tests. Hai local small studies đã đo thời gian/RAM thật; xem `p1_data_feasibility.md` và `p1_pipeline_changes.md`. Large scan mới có kiểm tra giới hạn `--mode scan --allow-large-scan`; toàn bộ acquisition cần `--full --allow-large-download`, vẫn phải được người dùng cho phép trước.

Chạy lại hiện tại:

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata --category Cell_Phones_and_Accessories
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews --category Cell_Phones_and_Accessories
.\.venv\Scripts\python.exe -m scripts.audit_p1 --source Electronics --metadata data/raw/amazon/metadata_prefix_20000.jsonl --reviews data/raw/amazon/reviews_prefix_100000.jsonl --run electronics_refactor
.\.venv\Scripts\python.exe -m scripts.audit_p1 --source Cell_Phones_and_Accessories --metadata data/raw/amazon/Cell_Phones_and_Accessories_metadata_probe_5000.jsonl --reviews data/raw/amazon/Cell_Phones_and_Accessories_reviews_probe_20000.jsonl --run cell_phones_refactor
.\.venv\Scripts\python.exe -m scripts.summarize_p1
.\.venv\Scripts\python.exe -m scripts.validate_filter_qa
```

New per-group QA CSV ở `data/manual/feasibility/`, tên chính xác nằm trong `qa_rule_sha256` của `electronics_refactor.json` và `cell_phones_refactor.json`. Điền `human_is_target_product` = yes/no/unsure và `human_notes`, rồi chạy `python -m scripts.validate_filter_qa --path <CSV>`. Rule columns có fingerprint, không sửa source/parent ID/rule_include để khiến độ chính xác dự đoán (precision) cao lên. Không điền nhãn tự động. gốc laptop QA CSV vẫn được giữ riêng.

Đã kiểm tra sáu QA files mới của cuối cùng lần chạy: **407 hàng**, tất cả đang đang chờ, validators đều trả unvalidated. Smartphone included mẫu chỉ 25 sản phẩm nên chưa đủ minimum 50 để nâng trạng thái dù có người điền hết. Không suy ra population độ bao phủ (recall). Đã đọc lại và verify SHA256 của năm raw JSONL/XML nguồn hiện có: đều khớp manifests tương ứng; `pip check` không lỗi. Full-download CLI đã smoke-check: thiếu explicit authorization flag bị từ chối trước network/file mutation.

BLOCKED: full-pool coverage/50k feasibility, con người QA, SemEval huấn luyện/kiểm thử chưa đủ. NEXT_ACTION: xem phương án Electronics ~7,79 GB download, 12 GB free disk và RAM/time/I/O ceilings trong `p1_data_feasibility.md`; chờ người dùng cho phép scan lớn.

## Lịch sử P1 trước refactor

Phần bên dưới ghi lại bản chụp trạng thái và 33 kiểm thử ở thời điểm triển khai đầu tiên. Lệnh audit không arguments trong phần lịch sử nay cần `--legacy-prefix`; lệnh toàn bộ acquisition phải thêm `--allow-large-download` sau phê duyệt.

Ngày kiểm chứng: 2026-10-08 (Asia/Saigon). **P1 chưa hoàn thành.**

## Nguồn và điều kiện truy cập

- Amazon: review và siêu dữ liệu Electronics từ endpoint công khai của
  [McAuley Lab](https://amazon-reviews-2023.github.io/), release Amazon review 2023. bộ dữ liệu card chính chủ trên [Hugging Face](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023) không có trường giấy phép rõ ràng khi kiểm tra; không gán một giấy phép tự suy đoán. Truy cập nguồn public cho dự án nghiên cứu này; không tái phân phối raw hoặc suy ra quyền sử dụng thương mại. Chưa dùng remote bộ dữ liệu loading code.
- SemEval: lấy laptop trial XML từ [website tổ chức](https://alt.qcri.org/semeval2014/task4/index.php?id=data-and-tools).
  Trang nguồn nêu fair use và điều kiện của dữ liệu providers. META-SHARE ELDA [index](http://metashare.elda.org/repository/search/?q=semeval+2014) liệt kê academic/non-commercial, no redistribution. [Trao đổi của organizer](https://groups.google.com/g/semeval-absa/c/O-h1lBOK2gI) cũng chỉ về META-SHARE và lưu ý hạn chế redistribution. Không tải bản huấn luyện/kiểm thử từ mirror cộng đồng khi chưa xác minh quyền phân phối.
- siêu dữ liệu HF revision đã kiểm tra: `2b6d039ed471f2ba5fd2acb718bf33b0a7e5598e`.
  byte dữ liệu thực tế lấy từ UCSD native gzip, có URL, ETag, Last-Modified, thời điểm UTC, byte/record số lượng và SHA256 trong bản kê riêng.

## Phạm vi thu thập thực tế

Downloader có giới hạn số dòng, 150 MB uncompressed/file và 180 giây/file; không tải toàn bộ Electronics. Các JSONL bản chụp trạng thái giữ nguyên byte từng nguồn line sau giải nén, chưa lọc hay viết lại vào raw. XML giữ nguyên byte file.

| tệp kết quả | Bản ghi/byte |
|---|---:|
| `data/raw/amazon/metadata_prefix_20000.jsonl` | 20.000 / 73.240.352 |
| `data/raw/amazon/reviews_prefix_100000.jsonl` | 100.000 / 67.212.341 |
| `data/raw/semeval/laptops-trial.xml` | Câu 100/18.547 |

Đây là **nguồn prefixes có thiên lệch thứ tự**, không phải ngẫu nhiên mẫu toàn corpus và không được dùng để ước lượng tổng laptop pool. Mỗi bản kê Amazon ghi `complete_source: false`; hạt giống ngẫu nhiên 42 dùng cho QA/sampling, không cho prefix.

Lỗi checksum ban đầu được kiểm thử bắt: downloader hàm băm trước khi đóng đầu ra buffer. Đã sửa để hàm băm sau khi đóng file. Hai bản kê gốc vẫn được giữ; bản kê `.verified.manifest.json` ghi checksum của file finalized, hàm băm cũ và lý do đính chính. nguồn raw không bị ghi đè. SemEval bản kê khớp checksum ngay từ đầu.

## Tham gia và lọc laptop

lược đồ đã quan sát trước khi code filter. Join `review.parent_asin` với `metadata.parent_asin`; không fallback variant `asin`. trùng lặp siêu dữ liệu ID bị báo lỗi thay vì tạo join many-to-many. quy trình có row-count conservation assertions.

Quy tắc `laptop_metadata_v1` trong `configs/acquisition.yaml`:

1. Identifier, title và categories phải hợp lệ.
2. Category node phải chỉ laptop, không phải chỉ Electronics/Computers.
3. Tên sản phẩm có laptop/notebook/chromebook.
4. Loại accessory categories và accessory/ambiguous titles theo regex cấu hình.
   Node `Computers & Accessories` là ancestor hợp lệ, không tự loại laptop.
5. Không dùng review văn bản hay rating để xác định laptop.

Filter cố ý ưu tiên độ chính xác dự đoán (precision), có thể bỏ laptop title không có từ khóa hoặc bundle title có accessory keywords. Không khẳng định độ bao phủ (recall) trên toàn pool.

| Chỉ số thực đo trong hai prefix | Kết quả |
|---|---:|
| Sản phẩm laptop ứng viên | 319 |
| review join được với siêu dữ liệu | 3.726 |
| review không có siêu dữ liệu trong prefix | 96.274 |
| review join được nhưng sản phẩm không qua filter | 3.709 |
| Ứng viên laptop review | 17 |
| Sản phẩm có ứng cử viên review | 11 |

Rating số lượng của 17 ứng viên review: **1★: 1, 2★: 0, 3★: 1, 4★: 3, 5★: 12**. Đây chưa phải cleaned bộ dữ liệu hoặc cảm xúc nhãn chuẩn. Tỷ lệ join thấp phản ánh hai prefix độc lập; không suy ra thiếu siêu dữ liệu toàn nguồn. Chưa ước lượng sạch size; phải mở rộng độ phủ, con người QA và thực hiện P2 trước.

## Mẫu QA dành cho người kiểm tra

`data/manual/laptop_filter_qa.csv`: 50 included + 50 excluded sản phẩm, hàm băm lấy mẫu hạt giống ngẫu nhiên 42; giữ title/categories và lý do rule để kiểm tra. `human_is_laptop` và `human_notes` **để trống**. Đây là QA filter, không phải gold cảm xúc bộ dữ liệu ở P10. Điền `yes/no/unsure` theo sản phẩm thực sự là laptop; ghi chú false positive, false negative hoặc thiếu bằng chứng.

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_filter_qa
```

bộ kiểm tra yêu cầu toàn bộ mẫu hết pending/unsure, ít nhất 50 included đã kiểm tra và observed mẫu độ chính xác dự đoán (precision) >= 95%. Threshold là tiêu chí QA đề xuất được ghi trong cấu hình, không phải kết quả đã đo hay đảm bảo độ chính xác dự đoán (precision) quần thể. Hiện **filter unvalidated**. chạy lại không ghi đè gán nhãn của con người.

## Lấy mẫu và kiểm tra SemEval

`data/interim/amazon_laptop_candidates.jsonl`: 17 records qua filter, chưa clean. `amazon_laptop_sample.jsonl`: giữ cả 17 vì nhỏ hơn 50.000. lấy mẫu tổng quát: proportional rating quotas (largest remainder), hàm băm hạt giống ngẫu nhiên 42, round-robin sản phẩm trong từng rating để tăng sản phẩm diversity. thương hiệu lấy từ `details.Brand` khi có; không suy diễn store là brand. Không stratify thương hiệu vì thương hiệu chưa được xác thực; báo cáo độ phủ thương hiệu thay vì hứa cân bằng brand. lấy mẫu có thể đổi sản phẩm phân bố, cần báo cáo khi dùng ở tập ứng viên lớn.

SemEval trial: **100 sentences, 49 vị trí cụm từ** đã căn chỉnh validate; polarities positive 29, negative 16, neutral 4. Chưa thấy conflict trong trial; policy vẫn được kiểm thử bằng dữ liệu mẫu: giữ vị trí cụm từ và cực tính cảm xúc gốc, exclude conflict khỏi ASC 3 lớp, không đổi sang neutral. huấn luyện/kiểm thử nguyên bản được giữ riêng khi có dữ liệu.

## Cách chạy lại

Tại root dự án, phụ thuộc P0 hiện đủ cho streaming P1; chưa cần pandas/pyarrow cho JSONL/XML audit. Không cài thêm thư viện chưa dùng.

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source trial
.\.venv\Scripts\python.exe -m scripts.audit_p1
.\.venv\Scripts\python.exe -m scripts.validate_filter_qa
.\.venv\Scripts\python.exe -m pytest -q
```

Downloader tái sử dụng file có checksum/source/limit khớp; không overwrite raw hoặc một phần files. Đổi giới hạn tạo filename mới; không âm thầm thay mẫu nguồn. Để audit SemEval được cấp quyền, đặt gốc laptop files vào `data/raw/semeval/Laptop_Train_v2.xml` và `Laptops_Test_Gold.xml`, giữ tài liệu license/access kèm provenance. Script audit hỗ trợ hai tên này và giữ gốc phân chia.

## Trạng thái và blockers

Kiểm chứng đã chạy: `python -m pytest -q` **33 passed**; `pip check` không có phụ thuộc lỗi. Chạy lại cả ba lệnh acquisition thành công bằng tái sử dụng và kiểm tra checksum; chạy lại audit giữ số dòng/kết quả như cũ và không ghi đè QA. bộ kiểm tra trên CSV thực tế trả `unvalidated`, 100 đang chờ, độ chính xác dự đoán (precision) `null`. Git ignore đã kiểm tra đối với raw, interim và thủ công CSV. kiểm thử dùng dữ liệu mẫu tổng hợp được ghi rõ; thống kê báo cáo lấy từ nguồn thực tế, không lấy từ fixture.

P1-T04/T06 đã audit lược đồ prefix và có dữ liệu dictionary. P1-T02 đã implement filter và QA template, chưa có con người QA. P1-T05 chỉ audit trial; chưa đủ gốc train/test. P1-T07 có số lượng prefix, chưa tổng pool/clean size. P1-T08 có lấy mẫu tái lập trên tập ứng viên ứng viên, chưa có laptop-only tập xác thực của con người.

BLOCKED: Cần review/metadata có độ phủ đủ để kiểm tra mục tiêu ~50k; prefixes hiện chỉ liên kết 17 laptop ứng viên review. NEXT_ACTION: Chọn ngân sách tải/stream lớn hơn hoặc cung cấp nguồn files hợp lệ đã có; dùng cùng join/filter và audit lại số lượng, không trộn non-laptop.

HEAD thực tế của nguồn: siêu dữ liệu gzip **1.312.900.427 byte**, review gzip **6.474.438.619 byte**, tổng **7.787.339.046 byte (~7,79 GB)**. Chưa tải các file đầy đủ. `--full` đã được chuẩn bị để giữ compressed nguồn nguyên bản, có byte/time giới hạn tài nguyên riêng và bản kê; chỉ chạy sau khi được phép tải lớn:

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata --full
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews --full
```

Full-download mode mới được kiểm tra bằng dữ liệu mẫu; chưa đo tốc độ/thời gian tải thực. Audit hiện chạy prefixes; khi có toàn bộ các nguồn cần chuyển đầu vào và giữ bộ nhớ bounds phù hợp trước khi audit toàn pool. toàn bộ các nguồn không tự giải quyết con người QA hoặc SemEval access. Không đánh dấu toàn bộ acquisition hoàn thành.

BLOCKED: SemEval laptop huấn luyện/kiểm thử gold chưa được truy cập từ nguồn có quyền. NEXT_ACTION: Lấy gốc files qua META-SHARE với điều kiện academic/non-commercial/no redistribution; không thay bằng trial hoặc mirror chưa xác minh.

BLOCKED: Chưa có người điền và kiểm tra 100-row filter QA sample. NEXT_ACTION: Người dùng kiểm tra `data/manual/laptop_filter_qa.csv`, rồi chạy bộ kiểm tra và rà soát báo cáo trước khi nâng filter thành validated.

Giới hạn: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small do con người gán nhãn bộ dữ liệu gold (300–500 mục tiêu, hiện chưa có). Chưa có đánh giá so sánh hoặc production claim.
