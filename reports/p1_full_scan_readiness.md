# P1 — Sẵn sàng quét toàn bộ thiết bị điện tử

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

## toàn bộ survey hoàn thành — trạng thái mới nhất (2026-10-08)

toàn bộ laptop-only survey đã được phê duyệt và hoàn tất: 43.886.944 Electronics review, 408.740 matched / 408.480 valid, 28.161 sản phẩm có valid review. Hai EOF và toàn bộ nguồn coverage true; outputs/checksums verified. 998,863 s, peak RAM 442,22 MB, budgeted read 35,65 GB, JSONL 430,75 MB; ceilings giữ nguyên. Xem [survey report](p1_full_laptop_survey.md). Filter QA/English/duplicates và gốc SemEval vẫn đang chờ; P1 chưa hoàn tất. Dừng sau survey, không P2/training. Các authorization/coverage blockers phía dưới là lịch sử đã được thay thế.

## review download hoàn thành — trạng thái mới nhất (2026-10-08)

Người dùng đã phê duyệt **download và integrity verification chỉ**, đã hoàn tất: **6.474.438.619 byte**, SHA256/manifest/size/complete_source verify, process exit 0. Transfer **87 phút 53 giây**, bình quân **1,23 MB/s**, trong ceilings 180 phút/6,6 GB. Disk còn **78,69 GB**, RAM khả dụng **4,22 GB**; không partial/failure, raw/QA cũ giữ nguyên. siêu dữ liệu full/preflight có sẵn được giữ nguyên; không preflight lại hoặc thay code/config.

Xem [toàn bộ review acquisition report](p1_reviews_full_acquisition.md). Hai toàn bộ raw các nguồn đã sẵn sàng cho bước tiếp theo; **streaming join/Laptop-only survey chưa được phê duyệt và chưa chạy**. CRC/JSONL/full-review counts/language/clean yield chưa đo. Các authorization/preparation statements phía dưới là lịch sử; phê duyệt download mới không đồng nghĩa phê duyệt survey. tài nguyên guards của survey và mục tiêu Laptop-only/30K giữ nguyên.

BLOCKED: chờ người dùng xác nhận streaming join/full laptop survey riêng. NEXT_ACTION: dừng tại acquisition results để người dùng quyết định survey; không P2/training.

## review acquisition preparation — trạng thái mới nhất (2026-10-08)

Theo yêu cầu mới, **chỉ chuẩn bị và kiểm thử**, chưa phê duyệt review download. `configs/acquisition.yaml` dùng source-specific full-download ceilings: siêu dữ liệu **3.600 s**, review **10.800 s (180 phút)**; `scripts/acquire_p1.py` chọn giới hạn bằng `args.source`. review byte giới hạn **6.600.000.000 byte** giữ nguyên; siêu dữ liệu byte giới hạn, prefix giới hạn tài nguyên, RAM/index/scan time/I/O/output limits không đổi. Downloader/resume architecture không thay đổi; mục tiêu vẫn Laptop-only/30K sạch tiếng Anh.

Kiểm chứng mới: **86 kiểm thử passed** (84 trước + 2 CLI dữ liệu mẫu cases xác nhận metadata/reviews thời gian và byte giới hạn tài nguyên). `pip check` không lỗi; `compileall` đạt. CLI kiểm thử mock acquisition, không network/download/raw writes. Không chạy lại toàn bộ siêu dữ liệu hash/preflight.

Local preparation check: disk free **86.874.882.048 byte (~86,9 GB)**; không có `Electronics.jsonl.gz`, một phần hoặc sidecars cùng tên. toàn bộ siêu dữ liệu **1.312.900.427 byte** có sẵn; file size/manifest/preflight SHA256 references khớp recorded đã xác minh SHA256. toàn bộ preflight bằng chứng vẫn **1.610.012 records / 28.172 laptop các ứng viên / EOF complete / 0 lỗi**. Đây là tái sử dụng bằng chứng, không kiểm tra hàm băm hoặc scan toàn bộ mới. bằng chứng preparation: `tables/p1_reviews_acquisition_readiness.json`. Chuẩn bị tối thiểu ~9 GB disk bổ sung (6,47 GB review + JSONL giới hạn 2 GB + margin); siêu dữ liệu đã lưu sẵn. một phần thất bại giữ lại có thể cần thêm disk trước một lượt tải mới.

### Lệnh tiếp theo — CHƯA CHẠY, chờ người dùng phê duyệt

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews --category Electronics --full --allow-large-download

# Chỉ sau download thành công, trong bước survey được phép:
.\.venv\Scripts\python.exe -m scripts.survey_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --reviews data/raw/amazon/Electronics.jsonl.gz --groups laptop --run electronics_full_laptop_30k --mode scan --allow-large-scan
```

Main survey dựng/xác minh index từ siêu dữ liệu trong quy trình hiện có; không chạy siêu dữ liệu-only preflight riêng. Dùng lần chạy directory mới để bảo toàn raw/QA/evidence. cấu hình thời gian mapping mới làm settings fingerprint thay đổi; không chạy lại old cached lần chạy với cấu hình mới.

### Rủi ro còn lại

- nguồn size theo HEAD bằng chứng trước **6.474.438.619 byte (~6,47 GB)**; chưa tải hoặc
  network-check lại ở lượt chuẩn bị này. Nếu nguồn thay đổi vượt byte giới hạn, downloader dừng.
- siêu dữ liệu transfer trước ~1 MB/s cho scenario review ~108 phút, nằm trong giới hạn mới
  180 phút; **không đảm bảo review thực đạt tốc độ đó**. Cần bình quân >~0,60 MB/s để transfer hoàn tất trong ba giờ, còn setup/overhead cần margin.
- `urllib.request.urlopen(..., timeout=30)` vẫn **30 giây cho network blocking operations**;
  tăng tổng thời gian giới hạn không tăng socket timeout. Kết nối/read stall có thể fail sớm.
- **Chưa hỗ trợ resume/retry tự động**. Partial/failure sidecar giữ nguyên; không append,
  delete hoặc overwrite. hiện có một phần cần kiểm tra/quyết định riêng trước tải lại.
- thời gian giới hạn được kiểm tra giữa read blocks; không phải hard process deadline cho
  mọi blocking operation/hash. byte kiểm tra giới hạn và HTTP body Content-Length check vẫn áp dụng.
- review decoded I/O/scan time/output yield chưa đo. Scan giữ 50M review / 4 giờ /
  60 GB budgeted read / 512 MB working set. Vượt kiểm tra giới hạn thì dừng, không tự nâng giới hạn.
- Filter vẫn unvalidated (100 QA đang chờ); 28.172 sản phẩm không chứng minh đủ 30K
  sạch tiếng Anh review hoặc khía cạnh-level ABSA nhãn. con người QA/SemEval access vẫn đang chờ.

BLOCKED: toàn bộ review download/survey chưa được người dùng phê duyệt. NEXT_ACTION: người dùng phê duyệt toàn bộ review download sau khi xem ngân sách/rủi ro; chỉ chạy survey sau download thành công và trong phạm vi được phép. Không P2/training/domain expansion. Các ghi chú giới hạn review 60 phút phía dưới là lịch sử trước điều chỉnh được yêu cầu này.

## toàn bộ siêu dữ liệu preflight hoàn thành — trạng thái mới nhất (2026-10-08)

Người dùng đã phê duyệt siêu dữ liệu download/preflight và đã thực hiện thành công: **1,31 GB gzip**, SHA256/manifest verify; **1.610.012 records**, **28.172 ứng viên laptop sản phẩm**, **0 record lỗi**, EOF/source_eof, siêu dữ liệu coverage=true. Peak process **71,16 MB**, index estimate **38,00 MB**, preflight **212,962 s**, budgeted read **6,56 GB**. đầu ra index **9.639.464 byte**, unique được chọn parent IDs và fingerprints verify. Không tăng ceilings, không refactor hoặc overwrite/delete raw. 84 kiểm thử chạy lại đạt.

Chi tiết [p1_metadata_full_preflight.md](p1_metadata_full_preflight.md). siêu dữ liệu authorization/preparation sections phía dưới là lịch sử trước phê duyệt; siêu dữ liệu điều kiện nghiệm thu nay đã đạt. Whole siêu dữ liệu+review coverage vẫn false; review chưa chạy.

**review ~6,47 GB chưa được phê duyệt.** siêu dữ liệu transfer mất 1.312,77 s (~1 MB/s): nếu review có throughput tương tự, tải ~108 phút, vượt giới hạn hiện tại 3.600 s. Tốc độ review thực NOT_MEASURED; cần >~1,80 MB/s để hoàn tất trong giới hạn một giờ. Không tự tăng thời gian budget. Main laptop survey nếu được phép vẫn hash/read siêu dữ liệu lại, chỉ join laptop parents và giữ scan/RAM/I/O/output ceilings hiện tại.

BLOCKED: chờ quyết định review download/scan và đánh giá thời gian giới hạn tài nguyên; con người QA unvalidated. NEXT_ACTION: người dùng xem đã đo siêu dữ liệu results rồi quyết định review; dừng trước review, P2 và huấn luyện. mục tiêu vẫn 30.000 sạch tiếng Anh laptop review, chưa đo sạch yield.

## Mục tiêu 30K và siêu dữ liệu-only authorization — hiện hành (2026-10-08)

Mục tiêu đổi từ 50K thành **30.000 sạch tiếng Anh laptop review** theo yêu cầu mới; có thể đánh giá tập ứng viên 15.000–25.000 chất lượng tốt bằng lớp coverage/product diversity. Không đổi phạm vi, số scan records, mẫu reservoir, index/RAM/time/I/O/output ceilings. Metrics/resource observations cũ bên dưới giữ nguyên; toàn bộ download vẫn chưa chạy. review ~6,47 GB **không được phép tải trong nhiệm vụ hiện tại**. Kế hoạch bốn bước bên dưới chỉ là phương án tương lai; hiện chỉ xin phê duyệt **hai bước siêu dữ liệu**.

### Chuẩn bị đã hoàn tất

- Config/active plans/checklists/README áp dụng 30K, ABSA cần nhãn riêng; không quota bằng mọi giá.
- Chạy lại **84 kiểm thử passed**; 4 raw Amazon bản chụp trạng thái checksums MATCH. tóm tắt dùng mục tiêu config.
- Không có toàn bộ siêu dữ liệu để reuse. hiện có siêu dữ liệu-only prefix báo cáo được verify/reuse:
  20.000 hàng, 319 laptop sản phẩm, EOF false, record_limit, coverage false, review not_started. Đây là kết quả scan cũ, không thời gian/RAM đo mới; toàn bộ siêu dữ liệu statistics **NOT_MEASURED**.
- HEAD-only reconfirm: siêu dữ liệu **1.312.900.427 byte (~1,31 GB)**; disk hiện
  **75.439.374.336 byte** trống. bằng chứng `tables/p1_30k_acquisition_status.json`.

### Hai thao tác cần phê duyệt — CHƯA CHẠY

```powershell
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata --category Electronics --full --allow-large-download
.\.venv\Scripts\python.exe -m scripts.survey_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --metadata-only --groups laptop --run electronics_metadata_full_30k --mode scan --allow-large-scan
```

siêu dữ liệu-only báo cáo mới xuất thêm filtering/baseline/join counters đã tính sẵn; hiện có cached prefix báo cáo giữ nguyên, không có các các trường mới được tạo hồi tố. kiểm thử preflight hiện có kiểm tra counters, không refactor pipeline.

Chi phí siêu dữ liệu: lưu **1,31 GB gzip** (không giải nén dump), download kiểm tra giới hạn **1,4 GB / 3.600 giây**; đề xuất >=4 GB disk trống cho raw, đầu ra giới hạn và margin. Ở giả định 10–30 MB/s, tải khoảng **44–131 giây** chưa overhead/retry; tốc độ thực **NOT_MEASURED**. siêu dữ liệu preflight giữ ceilings **2M records**, index **100k sản phẩm / 128 MB estimated**, working set **512 MB**, read giới hạn tài nguyên **60 GB**, thời gian **4 giờ**, JSONL **2 GB**. Đề xuất >=1 GB RAM khả dụng trước chạy; toàn bộ siêu dữ liệu decoded size/scan thời gian chưa đo. Read I/O gồm một gzip checksum pass + một decoded streaming pass. Nếu EOF/index/resource điều kiện nghiệm thu không đạt, ghi failure.json và dừng; không tự tăng limits hoặc tiếp tục review. HTTP resume chưa implement; một phần failure được giữ nguyên để kiểm tra.

BLOCKED: chưa có phê duyệt rõ ràng cho siêu dữ liệu download ~1,31 GB và siêu dữ liệu-only preflight. NEXT_ACTION: người dùng xác nhận hai thao tác trên; sau toàn bộ preflight mới báo số sản phẩm, exclusions/ambiguity/errors, EOF/provenance và RAM/time/I/O thực đo. Chỉ khi preflight đạt mới chuẩn bị review ~6,47 GB và xin phê duyệt riêng. P1 chưa hoàn tất; chưa P2/training.

Ngày: 2026-10-08 (Asia/Saigon). **Code đã kiểm chứng nhỏ; toàn bộ download/scan đang chờ phê duyệt. P1 chưa hoàn tất.**

## Trạng thái và bằng chứng

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| siêu dữ liệu EOF/provenance điều kiện nghiệm thu trước review scan | DONE | Fixture complete/incomplete, Giới hạn record/byte/time, URL nguồn không khớp |
| Stop lý do và báo cáo lỗi | DONE | `source_eof`, `record_limit`, `byte_limit`, `time_limit`, `memory_limit`, `output_limit`, `corrupt_source`; `not_started` cho review chưa chạy |
| Chính sách Oversized/JSON/GZIP | DONE | kiểm thử bounded drainage, malformed/final truncated JSON, GZIP hỏng |
| Lược đồ review siêu dữ liệu và baseline/filter QA | DONE | Kiểm tra các trường có thể rỗng, văn bản gốc, phụ kiện, sự mơ hồ và các tiêu đề chỉ dành cho mô hình |
| Kiểm chứng toàn bộ | DONE | `.venv\Scripts\python.exe -m pytest -q`: **84 passed**; pip check và compileall đạt |
| Hải thăm dò địa phương và toàn vẹn | DONE | `tables/*_hardening_v4.json`, `p1_hardening_integrity.json`; 5 raw checksums MATCH, đầu ra JSON/checksums và QA fingerprints hợp lệ |
| CLI ánh sáng trước chỉ dành cho siêu dữ liệu | DONE | Lịch thi đấu hoàn tất; tiền tố cục bộ PENDING, 319 laptop ứng viên, review `not_started` |
| Bảo hiểm đầy đủ metadata/reviews | BLOCKED | Chưa có file đầy đủ; chưa được phép download/scan lớn |
| con người filter precision/recall | NOT_MEASURED | QA chưa có nhãn người kiểm tra; không công bố precision/recall |
| Năng suất tiếng Anh sạch / gần trùng lặp / ABSA nhãn chuẩn | NOT_MEASURED | P2 và gán nhãn chưa thực hiện |
| SemEval gốc train/test | BLOCKED | Hiện chỉ có trial; cần truy cập hợp lệ |

Python mặc định (`python -m pytest -q`) chưa có pytest; dùng môi trường `.venv` của dự án, không cài thêm dependency. Các full-scan kiểm thử dùng **dữ liệu mẫu tổng hợp nhỏ**, không phải bằng chứng hiệu năng toàn Electronics. Code thay đổi ở bộ tải, feasibility, product-filter ambiguity kiểm tra giới hạn, survey/summarize CLI, acquisition/feasibility cấu hình và tests. Không viết lại quy trình, không database, không training/P2, không mở rộng phạm vi.

## Chính sách đọc và chặn kết luận sai

- `eof_observed` chỉ true khi scanner thực sự nhận EOF. Chạm đúng giới hạn record/byte
  vẫn được ghi limit nếu chưa quan sát EOF; không suy đoán hoàn tất từ kích thước file.
- Độ phủ nguồn yêu cầu EOF **cả hai files** và manifests có SHA256 khớp, complete-source
  flag và URL nguồn cấu hình khớp. Local file EOF không chứng minh toàn nguồn remote.
- `scan` dừng trước review scan nếu siêu dữ liệu thiếu EOF/provenance, có record lỗi hoặc
  identifier không hợp lệ. `failure.json` ghi stage, stats, lý do, BLOCKED/NEXT_ACTION. Không tạo review JSONL để bị nhầm thành kết quả full-pool. `probe` vẫn xử lý subset.
- Oversized record bị loại, không chuẩn hóa hoặc viết lại raw. Drain đến newline bằng
  chunks tối đa 64 KiB, có byte/time giới hạn tài nguyên; tail không được parse như record mới. Các bộ đếm `oversized_records`, `malformed_records`, `truncated_records`, lỗi lines hữu hạn (20) ghi tổn thất. JSON cuối file thiếu newline nhưng hợp lệ vẫn được nhận; JSON không hợp lệ ở đó là **nghi bị cắt**, không thể chứng minh nguyên nhân chỉ từ bytes. GZIP hỏng dừng `corrupt_source`, lưu chẩn đoán và raise lỗi.
- Index/product, process bộ nhớ và đầu ra guards giữ nguyên ceilings; không tự partition.
  Vượt tài nguyên giới hạn tài nguyên thì dừng an toàn. `sample_stop_reason` ghi riêng mẫu đầu ra limit.
- laptop mô hình cơ sở `laptop_metadata_v1` và regex giữ nguyên. Category laptop nhưng thiếu
  laptop/notebook/chromebook trong title vẫn excluded, nay được lấy vào boundary QA. Ambiguous category groups bị loại kể cả với `--groups laptop`; có counts/QA và `baseline_laptop_filter_decisions` để đối chiếu. Chưa có population precision/recall.
- Các các trường mới `user_id`, `review_title` (title/summary alias) giữ giá trị nguồn hoặc
  null, cùng asin/parent_asin/timestamp/verified_purchase/helpful_vote và các trường hiện có. review văn bản nguyên gốc; review_id là ID nguồn gốc SHA256+line, không giả Amazon ID.
- đầu ra directories không được chồng raw đầu vào hoặc QA directory. chạy lại chỉ tái sử dụng khi
  source/output/QA fingerprints khớp; nhãn con người được bảo toàn. lần chạy lỗi dùng directory mới.

## tập xác thực cục bộ

| Nguồn | Sản phẩm ứng viên Laptop/Smartphone/Tablet | review Laptop/Smartphone/Tablet hợp lệ | Thời gian | Bộ làm việc cao điểm | byte JSONL |
|---|---|---|---:|---:|---:|
| Điện tử | 319 / 0 / 74 | 17 / 0 / 9 | 5,692 s | 30.601.216 | 197.040 |
| Điện thoại di động và phụ kiện | 0 / 25 / 0 | 0 / 3 / 0 | 1,103 s | 28.737.536 | 12.979 |

số lượng bằng mô hình cơ sở 319/25/74 sản phẩm và 17/3/9 review. đầu ra tăng 4.698 và 588 byte so với lần chạy cũ do thêm user_id/review_title vào valid/sample JSONL; text/rating không thay đổi. được chọn index estimates giữ 523.860/28.174 bytes. Read I/O checksum
+ decoded tương ứng 280.905.386 / 59.265.344 bytes. Không có record lỗi/oversized trong
hai probes; metadata/review records chạm giới hạn hoặc chỉ là một phần nguồn prefixes, `source_coverage_complete=false`. Các số này **không đại diện toàn Amazon**.

siêu dữ liệu-only laptop probe: 20.000 records, 319 sản phẩm, 432.728 estimated index byte, 2,545 s, peak 28.979.200 byte; siêu dữ liệu stop `record_limit`, nguồn gốc một phần, review 0/`not_started`, trạng thái đang chờ. Đây là kiểm chứng CLI, không toàn bộ scan.

## Nguồn và ngân sách

HEAD-only ngày 2026-10-08, không tải body; bằng chứng `tables/p1_full_scan_resource_check.json`. Nguồn được công bố bởi [McAuley Lab](https://amazon-reviews-2023.github.io/), bộ dữ liệu card [Amazon review 2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023). Chưa xác minh giấy phép rõ ràng; giữ raw riêng, không redistribution/commit dữ liệu.

| Nguồn Electronics | Byte nén | Download giới hạn hiện tại |
|---|---:|---:|
| siêu dữ liệu JSONL.GZ | 1.312.900.427 | 1.400.000.000 |
| review JSONL.GZ | 6.474.438.619 | 6.600.000.000 |
| Tổng | **7.787.339.046 (~7,79 GB / 7,25 GiB)** | |

ETag/Last-Modified/Content-Length đã kiểm tra lại; sizes bằng báo cáo cũ. HEAD chỉ xác minh kích thước compressed, không cho biết số siêu dữ liệu hàng hoặc decoded bytes. Website chính chủ ghi ~43,9M Electronics ratings và ~1,6M items, nhưng ghi rõ items được đếm từ review, **không phải siêu dữ liệu hàng**; không dùng 1,6M làm EOF evidence.

- Disk: đề xuất **ít nhất 12 GB trống** (7,79 GB raw + 2 GB JSONL giới hạn + margin).
  Giữ gzip, không tạo uncompressed dump. Hiện đo **77.582.667.776 byte** trống. một phần download thất bại có thể cần thêm disk nếu giữ một phần và tải bản mới.
- RAM: xử lý kiểm tra giới hạn **512.000.000 byte**, chỉ số ước tính **128.000.000 byte**,
  tối đa 100.000 products. Đề xuất >=1 GB RAM khả dụng trước chạy. Máy đo tổng 16.849.264.640 byte, khả dụng **2.152.431.616 byte**, biến động theo ứng dụng khác. laptop-only toàn bộ lần chạy tránh giữ Smartphone/Tablet ứng viên index/output.
- Download thời gian **estimate, NOT_MEASURED**: ở 10–30 MB/s, 7,79 GB cần khoảng
  **4,3–13 phút** chưa overhead/retry. giới hạn 3.600 s/file; review cần trung bình >1,80 MB/s để hoàn tất trong một giờ. Không có tốc độ tải bộ dữ liệu đo thực tế.
- Scan thời gian **estimate, NOT_MEASURED**: giả sử decoded byte 20–50 GB và tốc độ
  5–25 MB/s thì riêng streaming khoảng **13–167 phút**; thêm checksum/I/O overhead. Đây là scenario planning, không extrapolate prefix thành đánh giá so sánh full. kiểm tra giới hạn **4 giờ/run** bao gồm checksum; decoded nguồn size/speed chưa đo.
- I/O: main toàn bộ lần chạy giới hạn **60 GB** = compressed checksum 7,79 GB + tối đa
  khoảng **52,21 GB decoded**; không phải dung lượng disk cần lưu. siêu dữ liệu preflight thêm một checksum + một decoded siêu dữ liệu pass, có giới hạn tài nguyên riêng và đo riêng. Main lần chạy đọc siêu dữ liệu lần nữa để xác minh nguồn/index trước review.
- Record ceilings: **2.000.000 siêu dữ liệu / 50.000.000 review**. Chưa chứng minh
  siêu dữ liệu hàng <=2M, decoded I/O <=60GB hoặc được chọn index <=100k/128MB. Nếu nguồn/working set vượt giới hạn: BLOCKED; trình người dùng số thực đo và đề xuất tăng giới hạn tài nguyên có lý do trước chạy lại, không tăng tự động.
- Interrupted downloads: server có Accept-Ranges, nhưng client **chưa implement resume**.
  Partial/failure manifests được giữ, không append/overwrite. Không có tự động fallback database.

## Lệnh dự kiến — CHƯA CHẠY toàn bộ

Thực hiện từng bước sau phê duyệt, kiểm tra kết quả trước bước tiếp theo.

```powershell
# 1. Tải metadata đầy đủ
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source metadata --category Electronics --full --allow-large-download

# 2. Metadata-only preflight, không cần review file
.\.venv\Scripts\python.exe -m scripts.survey_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --metadata-only --groups laptop --run electronics_metadata_full_v4 --mode scan --allow-large-scan

# 3. CHỈ sau metadata_coverage_complete=true, không lỗi/index over-budget: tải reviews
.\.venv\Scripts\python.exe -m scripts.acquire_p1 --source reviews --category Electronics --full --allow-large-download

# 4. Laptop-only survey; metadata gate được kiểm tra lại
.\.venv\Scripts\python.exe -m scripts.survey_p1 --source Electronics --metadata data/raw/amazon/meta_Electronics.jsonl.gz --reviews data/raw/amazon/Electronics.jsonl.gz --groups laptop --run electronics_full_laptop_v4 --mode scan --allow-large-scan
```

Nếu preflight dừng, không tiếp tục bước 3/4. Các flags chỉ là software điều kiện nghiệm thu, không thay thế xác nhận mới của người dùng. Không toàn bộ Cell Phones download theo đề xuất này.

## laptop feasibility decision criteria

Chỉ quyết định sau khi coverage đầy đủ, filter con người QA và P2 bằng chứng có thật:

1. **Quantity:** matched/valid/clean-English số lượng theo tầng; mục tiêu hiện hành ~30.000
   sạch tiếng Anh review. Nếu nhỏ hơn (ví dụ 15.000–25.000 chất lượng cao), ghi thực tế size và đánh giá lớp coverage/product diversity với người dùng, không hạ chất lượng. Báo cáo sản phẩm có review, largest-product share/top-product concentration, rating/class coverage và thương hiệu diversity; không cộng Smartphone/Tablet để đạt quota.
2. **Chất lượng:** kiểm tra văn bản missing/invalid, empty/short, bản sao exact/near,
   language/mixed/uncertain phân bố và con người language mẫu, length/rating/brand distributions. con người QA included/excluded/ambiguous/model-only titles; threshold hiện tại mẫu độ chính xác dự đoán (precision) >=95%, >=50 included, hết pending/unsure. Đây là mẫu criterion, không population độ bao phủ (recall). Không chọn weights/model bằng subset này.
3. **ABSA:** keyword-hit rate chỉ heuristic. review rating chỉ overall đại diện,
   không khía cạnh nhãn. Tần suất/đa dạng explicit vị trí cụm từ và nhiều cực tính cảm xúc phải kiểm chứng qua gốc SemEval laptop và con người Amazon gán nhãn; giữ gold 300–500 do người gán nhãn độc lập, không dùng làm train/model selection. Chưa có ngưỡng ABSA sufficiency đo thực tế; ghi NOT_MEASURED thay vì áp số liệu keyword như truth.
4. **phạm vi:** đủ laptop -> ưu tiên laptop-only. Nếu thiếu, phân biệt thiếu nguồn,
   filter quá chặt, chất lượng/language/duplicates, mất cân bằng hay thiếu ABSA nhãn trước đề xuất khảo sát Smartphone/Tablet riêng. Nếu đề xuất multi-phạm vi vì lợi ích nghiên cứu, phải nêu gain/generalization cần kiểm chứng, khía cạnh chuẩn hóa, annotation/model/dashboard costs và thời gian. Contract hiện 6 tuần; scenario 7–8 tuần trong yêu cầu không tự thay lịch. Quyết định mở rộng thuộc người dùng.

Giới hạn bắt buộc: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (hiện chưa có). Không claim cross-gadget/production readiness.

BLOCKED: chưa có phê duyệt mới cho ~7,79 GB toàn bộ download và large scans; siêu dữ liệu EOF/index/decompressed giới hạn tài nguyên chưa được xác minh trên toàn bộ source. NEXT_ACTION: người dùng phê duyệt ngân sách và các bước siêu dữ liệu download/preflight, sau đó review download/laptop survey có điều kiện. Giữ nguyên ceilings hiện tại; bất kỳ đề xuất tăng giới hạn nào cần xem dữ liệu/resource thực đo trước khi chạy.

BLOCKED: con người filter QA, gốc SemEval huấn luyện/kiểm thử và sạch English/ABSA bằng chứng chưa đủ. NEXT_ACTION: kiểm tra QA thật, hoàn tất truy cập SemEval hợp lệ; chỉ chuyển P2 khi P1 điều kiện nghiệm thu đủ.
