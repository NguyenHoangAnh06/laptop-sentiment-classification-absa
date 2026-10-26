# P1 refactor — Thay đổi quy trình

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

## quy trình hardening v4 — mới nhất (2026-10-08)

- `loader.py`: thêm observed EOF; oversized physical lines được drain bounded
  64 KiB rồi skip/count, giữ đúng line IDs. Phân biệt malformed/final suspected truncated JSON, oversized và corrupt GZIP; byte/time guards vẫn áp dụng khi drain.
- `feasibility.py`: siêu dữ liệu coverage/provenance điều kiện nghiệm thu ở scan; failures có JSON
  diagnostics và standard stop lý do; bộ nhớ checks đầu scan và mỗi 1.000 dòng. siêu dữ liệu-only preflight, output/raw/QA path separation, nullable user/title các trường, mô hình cơ sở laptop counters, boundary QA cho model-only/ambiguous sản phẩm và mẫu output-limit status. Không đổi laptop mô hình cơ sở regex hoặc làm sạch review text.
- `product_filter.py`: category ambiguity kiểm tra mọi group đã cấu hình kể cả
  đầu ra chỉ chọn laptop. `survey_p1.py`: `--metadata-only`, `--groups laptop`; `summarize_p1.py`: chọn runs/output để giữ bằng chứng lịch sử.
- cấu hình thêm title/summary alias, version v4; **tài nguyên ceilings không đổi**.
- kiểm thử: **84 passed** (60 cũ + 24 mới), `pip check` và `compileall` đạt. Full-source
  behavior chỉ dữ liệu mẫu nhỏ. Hai local probes giữ số lượng, manifests/raw/QA cũ giữ nguyên.

Chi tiết policy, paths, nguồn, đo tài nguyên, feasibility criteria và lệnh **chưa chạy**: [p1_full_scan_readiness.md](p1_full_scan_readiness.md). toàn bộ download/large scan đang chờ phê duyệt mới theo yêu cầu người dùng; P1 chưa hoàn tất, chưa P2/training. Phần 60-tests/refactor dưới đây là lịch sử mô hình cơ sở.

Ngày: 2026-10-08. Refactor phục vụ feasibility study; **phạm vi dự án vẫn laptop**.

## Audit trước khi sửa

- Downloader đã giữ raw, SHA256, ETag, Last-Modified và giới hạn byte/time.
  bộ tải streaming, alias tập xác thực, `parent_asin`, SemEval vị trí cụm từ tập xác thực và policy conflict là các phần tái sử dụng được. Hai bản kê sửa hàm băm cũ được giữ nguyên.
- Nút thắt: hai prefix độc lập. 100.000 review chỉ join được 3.726 siêu dữ liệu
  thuộc prefix 20.000; 17 laptop review không phải bằng chứng thiếu laptop trên Amazon.
- `audit_p1.py` cũ giữ `all_ids`, toàn bộ `qa`, toàn bộ `filtered` và các bản copy
  của `sample_reviews`. Đây là RAM tăng theo kích thước corpus, dù reader là streaming.
- Filter laptop cũ ưu tiên độ chính xác dự đoán (precision) nhưng có false-negative risk với bundle/title
  thiếu từ khóa. Chưa được người xác thực; không được tự tuyên bố precision/recall.
- nguồn path/file names cố định Electronics; không có multi-group classification,
  generic QA hoặc chất lượng đại diện survey. toàn bộ acquisition có byte/time kiểm tra giới hạn nhưng chưa check HTTP body thiếu so với Content-Length, chưa có diagnostics cho partial.

## Logic mới

1. Đọc siêu dữ liệu từng record. Phân loại bằng category + title, loại phụ kiện và
   siêu dữ liệu mâu thuẫn giữa nhóm. Giữ index **chỉ các ứng viên sản phẩm** gồm parent ID, title, categories, thương hiệu và group; ghi `products.jsonl`.
2. Stream review, lookup `parent_asin` trong index đã chọn; validate text/rating/
   aliases và ghi JSONL riêng từng group. Không giữ toàn bộ filtered review.
3. Báo cáo số lần quét, hồ sơ không hợp lệ, trường bị thiếu, bảo tồn hàng,
   stop lý do và observed schema. `not_in_selected_metadata_index` gồm cả ngoài mục tiêu và siêu dữ liệu chưa được quan sát; không gọi tất cả là thiếu siêu dữ liệu.
4. QA là bottom-hash lấy mẫu hữu hạn: included, excluded gần boundary,
   excluded khác. con người columns để trống; rule columns có fingerprint.
5. Mẫu review là bể chứa băm đáy có giới hạn (5.000/group), sản phẩm áp dụng
   giới hạn 100 trên reservoir. Full/sample rating phân bố đều được ghi để nhìn lấy mẫu distortion. sản phẩm giới hạn có thể làm mẫu nhỏ hơn mục tiêu; không đảm bảo rating quota của toàn bộ tập ứng viên hoặc giữ mọi sản phẩm sau khi reservoir đầy.
6. Số lượng trùng lặp được chuẩn hóa chính xác, số liệu length/rating/brand và phương pháp phỏng đoán
   keyword khía cạnh coverage là khảo sát. Language, sạch tiếng Anh size, bản gần trùng và ground-truth khía cạnh nhãn không được giả định.

siêu dữ liệu phải quét đầy đủ **trước** review trong khảo sát corpus thực sự. Probe trên snapshots vẫn một phần, luôn `exploratory_subset_not_final_dataset`. `source_coverage_complete` yêu cầu EOF cả hai scan **và** complete-source manifests. Ngay cả khi nguồn đầy đủ, đầu ra vẫn là ứng viên tập ứng viên cần con người QA/language tập xác thực.

## File thay đổi

| tập tin | Vai trò |
|---|---|
| `src/data/acquisition.py` | Validate giới hạn tài nguyên, Content-Length, một phần failure checksum; không resume giả |
| `scripts/acquire_p1.py` | Hai category, small probe riêng, toàn bộ cần explicit flag |
| `src/data/loader.py` | Bounded tolerant scanner, lỗi JSON/UTF-8/gzip và stop lý do |
| `src/data/product_filter.py` | laptop mô hình cơ sở + Smartphone/Tablet có thể định cấu hình; bác bỏ sự mơ hồ |
| `src/data/feasibility.py` | Chỉ mục nhỏ gọn, phát trực tiếp dấu vân tay join/output, QA, tài nguyên guards/provenance |
| `src/data/survey.py` | Chuẩn hóa đại diện, trùng lặp, lấy mẫu giới hạn, các trường measured/NOT_MEASURED |
| `src/data/filter_qa.py` | Trình xác nhận tương thích nhóm chung QA và mô hình cơ sở |
| `scripts/audit_p1.py` | Default siêu dữ liệu-first CLI; diagnostics cũ chỉ qua `--legacy-prefix` |
| `scripts/survey_p1.py`, `scripts/summarize_p1.py` | Chạy survey và xuất JSON/CSV observations |
| `scripts/validate_filter_qa.py` | `--path` cho QA mới; không có path giữ mô hình cơ sở laptop |
| `configs/feasibility.yaml`, `src/config.py` | Nguồn/rules/budgets survey và cấu hình loading |
| `tests/test_p1_feasibility.py` | Kiểm tra cố định cho bộ tái cấu trúc và chế độ lỗi |
| README, từ điển, hai kế hoạch, ba báo cáo P1, `reports/tables/` | Bằng chứng và phạm vi thực tế |

Không thay nhãn/model/inference phạm vi trong `configs/data.yaml` hay contract. `laptop_filter.py` giữ mô hình cơ sở logic; modules P0/SemEval/tests cũ vẫn dùng được. Không thêm phụ thuộc hoặc database. Chưa chạy P2/training.

## Giới hạn tài nguyên và an toàn dữ liệu

- Probe: 320 MB tổng checksum + decoded read I/O, 20k metadata/100k review,
  90 giây; đầu ra JSONL tối đa 16 MB. Cell nguồn acquisition nhỏ riêng: 5k/20k, tối đa 25 MB decoded/file, 60 giây/file.
- Scan: explicit authorization, tối đa 2m metadata/50m review, 60 GB read I/O,
  4 giờ/source, JSONL đầu ra tối đa 2 GB/source. Đây là **giới hạn**, không phải dự báo cần chạy 4 giờ hay xác nhận nguồn đã được quét hết.
- Chỉ mục: Tải trọng ước tính 100k products/128 MB; mẫu ước tính 5k/group/16 MB
  payload. Exact văn bản hàm băm set 100k/group; vượt giới hạn -> trùng lặp thước đo NOT_MEASURED.
- Windows working set kiểm tra giới hạn 512 MB, kiểm tra mỗi 1.000 records; thực tế working
  set/peak được ghi. Platform không hỗ trợ trả NOT_MEASURED, vẫn có payload caps.
- Dừng khi index/RAM thiếu; không dùng database fallback. Hash-partition được chọn
  siêu dữ liệu rồi scan review theo từng shard là phương án file-based cho trường hợp vượt giới hạn; cần ngân sách I/O nhiều lượt và implementation bổ sung trước khi chạy.
- Resume HTTP **chưa triển khai**. HEAD có Accept-Ranges không chứng minh gzip
  prefix hoặc filter state resume được. một phần có failure sidecar/hash; giữ lại, không append hoặc overwrite. Chọn destination/run mới sau khi kiểm tra nguyên nhân.
- lần chạy hoàn tất được tái sử dụng sau kiểm tra nguồn, đầu ra và immutable QA columns.
  con người notes/labels có thể chỉnh mà không bị overwrite. lần chạy chưa hoàn tất không được coi là đã hoàn thành điểm lưu mô hình; cần directory mới. Không xóa raw/annotation cũ.

## Kiểm chứng

`python -m pytest -q`: **60 passed** (gồm 33 kiểm thử cũ). Bao phủ filtering các nhóm, ambiguous/accessory cases, streaming join, hàng conservation, JSONL/gzip lỗi, network body thiếu, một phần checksum, alias conflicts, trùng lặp giới hạn, mẫu giới hạn, khả năng tái lập, source/output tampering, con người ghi chú bảo toàn, scan điều kiện nghiệm thu và working-set kiểm tra giới hạn. Full-source branch chỉ kiểm thử trên **dữ liệu mẫu nhỏ**.

Hai survey thật dùng bản chụp trạng thái nhỏ, nguồn schema/HEAD được probe. Kết quả và memory/time ở `reports/p1_data_feasibility.md`. Chưa đánh giá so sánh network/scan lớn.

Giới hạn bắt buộc: laptop-only findings, rating đại diện nhiễu, SemEval-to-Amazon platform/style shift trong laptop review và small bộ gold do con người gán nhãn set (chưa tạo).
