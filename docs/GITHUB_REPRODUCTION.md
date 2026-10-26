# Tái lập từ snapshot GitHub qua P9

Snapshot này chứa source/config/tests, lịch sử thực thi, metrics tổng hợp và hình báo cáo. Đây là snapshot sau nhiều pha phát triển, không phải lịch sử commit từ ngày đầu. P10–P13 vẫn PENDING; xuất bản GitHub không phải nghiệm thu hoàn thành dự án.

## Cấu trúc và môi trường

`src/` chứa xử lý dữ liệu, tiền xử lý, sentiment, ABSA và đánh giá; `scripts/` là CLI; `configs/` là cấu hình; `tests/` là kiểm thử; `notebooks/` giữ notebook nguồn không output; `reports/` giữ báo cáo/metrics; `docs/` giữ hợp đồng và bàn giao. `app/` mới là vị trí dành cho ứng dụng.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -X utf8 -B -m scripts.test_all
```

Requirements là cấu hình môi trường của dự án; môi trường đã đo được nêu trong README. Chưa xác minh setup từ máy sạch trong tác vụ xuất bản. Một số kiểm thử tích hợp/acceptance cần dữ liệu và artifacts local, nên clone source không tương đương có đầy đủ đầu vào để chạy mọi kiểm tra. Không chạy finalizer ghi vào namespace frozen chỉ để thử cài đặt.

## Dữ liệu local và quyền truy cập

Không phân phối corpus Amazon/SemEval, dữ liệu xử lý có text, manual annotations, embeddings hoặc predictions theo từng review qua Git. Cả file nhỏ chứa trích đoạn trong reports và notebook đã thực thi cũng được loại. Metadata/manifest và hash trong báo cáo vẫn mô tả artifact local; đường dẫn đến file bị loại có thể không tồn tại sau clone. Đây là tham chiếu provenance, không phải liên kết tải công khai.

Amazon 2023: nguồn/version/schema/join/rules nằm ở `configs/acquisition.yaml`, `configs/data.yaml`, `reports/p1_data_acquisition.md`, `reports/p1_reviews_full_acquisition.md`, `reports/p2_amazon_completion_20261009.md` và `data_dictionary.md`. Người tái lập phải tự kiểm tra điều kiện sử dụng tại nguồn, tự tải Electronics reviews **và metadata** qua nguồn được phép. Không suy quyền redistribution từ việc tải công khai. CLI `python -m scripts.acquire_p1 --help` mô tả bounded/full download; full download cần cờ cho phép rõ ràng và dung lượng lớn, không chạy tự động khi clone.

SemEval-2014 Task 4 **laptop**: dùng quy trình truy cập/chấp thuận điều khoản của nhà cung cấp, giữ official train/test và spans gốc. `configs/acquisition.yaml` lưu URL và trạng thái quyền; source/license của bản local cũ vẫn **NOT_VERIFIED theo ngoại lệ giáo dục**, không được diễn giải thành quyền phân phối. Xem `reports/p1_semeval_laptop.md` và `configs/p8_aspect_extraction.yaml` để đối chiếu tên file/đường dẫn local. Không dùng corpus từ nhánh thiết bị khác.

Đặt dữ liệu theo các khóa đường dẫn trong cấu hình: `data/raw/` bất biến; các đầu ra trong `data/interim/`, `data/processed/`, `data/manual/`. Không upload annotations chứa review. Human gold P10 chưa tồn tại như một bộ nghiệm thu hoàn tất; Codex không tạo thay nhãn người.

## Pipeline và artifacts

Thứ tự phương pháp: P1 acquisition/join/filter/QA → P2 clean/proxy labels → P3 EDA → P4 split/preprocessing → P5/P6 benchmark → P7 error/label-noise analysis → P8 span extraction → P9 aspect-conditioned sentiment/joint ABSA. ID, dependencies và DONE_WHEN tại `PLAN_AI.md`; lệnh và bằng chứng đã thực hiện tại `docs/PROJECT_EXECUTION_LOG.md`.

Các entry point hiện có: `scripts.prepare_p2_amazon`, `scripts.analyze_p3`, `scripts.prepare_p4`, `scripts.prepare_semantic`, `scripts.train_modern`, `scripts.train_transformer`, `scripts.prepare_p8`, `scripts.train_p8`, `scripts.prepare_p9`, `scripts.p9_exp01`. Đọc module/config trước khi chạy; không phải mọi entry point đều có `--help` hoặc chế độ không ghi. Training/download có thể tốn nhiều giờ hoặc yêu cầu quyền riêng. Dùng namespace/config mới cho lần tái lập, giữ nguyên split/seed/protocol; không ghi đè artifacts frozen. Các script cũ LEGACY được giữ để giải thích lịch sử.

Pretrained sources/revisions được ghim trong `configs/semantic_benchmark.yaml`, `configs/transformer_benchmark.yaml`, `configs/p8_aspect_extraction.yaml`, `configs/p9_exp01_deberta.yaml`; credentials nếu cần phải đặt qua biến môi trường/cơ chế đăng nhập nhà cung cấp. **Pretrained backbone không phải trained checkpoint của dự án.** Không có public trained-model download được thiết lập trong lần xuất bản này. Muốn chạy inference phải có checkpoint local đúng manifest hoặc tự huấn luyện theo protocol vào namespace mới. Selector canonical ASC là `configs/p9_canonical.yaml`; ba vị trí canonical được ghi tại README/handoff. Không khẳng định inference chạy được ngay sau clone.

Riêng bản trình bày P3 tinh gọn dùng các CSV tổng hợp và bằng chứng liên quan: đọc `configs/p3_refinement.yaml`, `scripts/refine_p3.py` và `src/data/eda_refinement.py`. CLI vẫn kiểm SHA256 dataset local **và toàn bộ CSV P3 gốc**, kể cả `noise_examples.csv`/`theme_contexts.csv` không được publish. Vì vậy cần tự khôi phục/tái tạo đầy đủ đầu vào P3 local đúng manifest; chỉ clone và tải dataset là chưa đủ. Không bỏ kiểm checksum để chạy từ snapshot thiếu đầu vào:

```powershell
.venv/Scripts/python.exe -X utf8 -m scripts.refine_p3 --output-dir reports/p3_refinement_REPRODUCTION
```

## Ranh giới công khai và kiểm tra trước commit

`.gitignore` loại corpus, embeddings, checkpoints, model binary, ZIP, caches, môi trường, credentials và các báo cáo có payload gốc đã phát hiện. Không dùng Git LFS. `.gitattributes` tắt tự chuyển CRLF/LF để giữ nguyên byte và hash bằng chứng/source đã khóa, kể cả khi máy clone bật `core.autocrlf`. Các báo cáo/acceptance lịch sử có thể còn absolute path máy cũ: giữ nguyên để không đổi hash/bằng chứng, không dùng làm đường dẫn setup. README dùng project-relative paths. Không thêm giấy phép source/data khi chưa có quyết định của chủ sở hữu.

```powershell
.venv/Scripts/python.exe -X utf8 -B -m scripts.audit_public_snapshot --output reports/github_publication_local/audit.json
```

Audit phân loại TRACK/IGNORE/REVIEW/LARGE FILE/SECRET RISK, ghi danh sách >10MB/>50MB/≥100MB và chỉ ghi loại/vị trí secret. Phạm vi quét: text UTF-8 hoặc UTF-16 có BOM tối đa 10MB, gồm first-party reports bị ignore; data/, inventory local, môi trường/cache và dataset/model binary chỉ kiểm kê metadata. Đây là kiểm tra heuristic, không phải bảo đảm tuyệt đối không có secret; kiểm lại index và Git objects trước push. Inventory local không được publish.

Giới hạn khoa học giữ nguyên: **chỉ laptop**, **nhãn proxy suy từ sao có nhiễu**, **SemEval-to-Amazon platform/style shift chưa đánh giá độc lập**, **human-gold nhỏ P10 còn PENDING**. Model hiện chỉ hỗ trợ tiếng Anh; ứng dụng/production readiness chưa được nghiệm thu.
