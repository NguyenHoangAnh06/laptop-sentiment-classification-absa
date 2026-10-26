# P1 — Mua lại review điện tử đầy đủ

> BẰNG CHỨNG LỊCH SỬ - được giữ lại để tái tạo. Quyền trước đó,
> trình chặn và đầu dò không phải laptop không phải là quy trình hiện tại. Hiện tại chỉ có laptop
> trạng thái: `p1_full_laptop_survey.md`, `p1_laptop_filter_qa.md`, `p1_semeval_laptop.md`.
> Đường dẫn run/QA được thay thế: `tables/p1_laptop_only_cleanup_inventory.json`.

Ngày: 2026-10-08 (Asia/Saigon). **Download và integrity verification hoàn thành; streaming join/survey chưa chạy.** Phê duyệt hiện tại chỉ gồm toàn bộ review download + verification; mục tiêu vẫn Laptop-only/30K sạch tiếng Anh.

## Kết quả thực tế

| Hạng mục | Kết quả |
|---|---|
| Raw mới | `data/raw/amazon/Electronics.jsonl.gz` |
| Kích thước | **6.474.438.619 byte (~6,47 GB)** |
| SHA256 đọc lại | `17b2c5f3736d4c0cb874859076436ebd4513f4c2396c528440a63204084e6a28` |
| bản kê | `Electronics.jsonl.gz.manifest.json` |
| Dừng/hoàn thành | `source_eof` / `complete_source=true` / requested_limit=null |
| Đã truy xuất UTC | 2026-10-08T08:22:16.334136+00:00 (15:22:16 Asia/Saigon) |
| Thẻ ET | `"181e817db-62bdb26aa07c6"` |
| Sửa đổi lần cuối | Thứ năm, 16 tháng 1 2025 23:28:26 GMT |
| Kết nối/setup/transfer elapsed | **5.272,919 s — 87 phút 53 giây** |
| Tốc độ bình quân | **1.227.866 bytes/s (~1,23 MB/s)** |
| Integrity verification riêng | **5,607 s**, một SHA256 pass trên file đã finalized |
| Disk free sau xác minh | **78.694.182.912 byte (~78,69 GB)** |
| RAM khả dụng sau xác minh | **4.221.132.800 byte (~4,22 GB)** |
| Chẩn đoán một phần/lỗi | **Không có**, lượt tải thành công |

Nguồn: URL Amazon review 2023 Electronics review trong `configs/acquisition.yaml`, `https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Electronics.jsonl.gz`. nguồn URL/resolved URL, ETag, Last-Modified, timestamp và SHA256 giữ trong bản kê. Tổng compressed toàn bộ siêu dữ liệu + review hiện có: **7.787.339.046 byte (~7,79 GB)**; không bao gồm snapshots/sidecars cũ. Raw không tái phân phối/commit; access/license observations trước vẫn áp dụng.

Elapsed tính từ execution start tới bản kê retrieved timestamp, gồm setup/kết nối/transfer, không gồm checksum cuối của downloader hoặc verification riêng. Tốc độ = thực tế compressed byte / elapsed, không phải instant link speed. Disk/RAM là snapshots thực đo sau verification. bằng chứng đầy đủ: `tables/p1_reviews_download_execution.json`.

## Verification và bảo toàn dữ liệu

- Downloader hiện tại chạy đúng **10.800 s / 6.600.000.000 byte**. Không chạm ceilings,
  không sửa code/config hoặc tài nguyên guards. siêu dữ liệu timeout vẫn 3.600 s.
- Downloader xác nhận HTTP body size bằng Content-Length rồi hàm băm sau đóng file;
  process exit code 0. SHA256 đọc lại khớp bản kê, file size khớp **6.474.438.619 byte**, expected nguồn URL khớp, `complete_source=true`, `requested_limit=null`.
- GZIP magic header hợp lệ. **Không chạy toàn bộ GZIP CRC/decompression hoặc JSONL scan**
  trong nhiệm vụ này; transmission/file-hash verification không thay thế record/schema tập xác thực. bản kê `rows=null`, vì không đếm/parse review khi toàn bộ download.
- Trước/sau lượt tải, byte sizes và mtime_ns của mọi raw/QA files có sẵn không đổi.
  siêu dữ liệu, snapshots, manifests cũ và con người QA không bị overwrite/delete.
- Chỉ một lượt download; không tự retry/resume. Không có partial/failure sidecars của lượt này.
  New raw/manifest thuộc Git ignore. Không tạo uncompressed dump, database hoặc nhãn.

## Trạng thái P1 và bước tiếp theo

**hoàn thành:** hai toàn bộ compressed các nguồn đã có, review transmission/checksum/provenance verify; siêu dữ liệu preflight trước đó vẫn 1.610.012 records/28.172 candidates/EOF complete. Không chạy lại siêu dữ liệu preflight, không streaming join/survey/P2/training.

**NOT_MEASURED:** total/valid/clean-English laptop review số lượng toàn nguồn, review rating phân bố, product/brand review coverage, duplicates/language và khía cạnh-nhãn feasibility. 17 laptop ứng viên review từ prefix cũ vẫn là lịch sử, không cập nhật thành full-pool result. Raw Electronics chứa nhiều loại sản phẩm; đây là raw nguồn, không phải laptop bộ dữ liệu đã lọc. con người filter QA vẫn unvalidated; SemEval gốc splits/gold gán nhãn vẫn đang chờ.

BLOCKED: chưa được phê duyệt streaming join và laptop-only toàn bộ survey. NEXT_ACTION: người dùng xem acquisition/integrity results và xác nhận toàn bộ laptop survey riêng; giữ scan 50M records/4 giờ/60 GB read I/O/512 MB process working set và index ceilings hiện tại. Không tự tăng limits hoặc chuyển P2/training. P1 chưa hoàn tất; mục tiêu 30K còn cần evidence.

Giới hạn bắt buộc: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (hiện chưa có). Không claim cross-gadget generalization hoặc production readiness.
