# Dọn dẹp chỉ laptop và trạng thái hiện tại của P1

Ngày 2026-10-08. Đã thực hiện phạm vi cleanup; không chạy P2, huấn luyện, download hoặc rescan Amazon. bộ dữ liệu laptop toàn bộ Survey và nhãn gán user-approved được giữ nguyên.

## GIỮ

- Toàn bộ `data/raw/amazon/`, manifests/checksums và `data/raw/semeval/`.
  lịch sử raw Cell Phones prefixes cũng giữ: raw deletion cần phê duyệt riêng.
- `data/interim/feasibility/electronics_full_laptop_30k/` và
  `electronics_metadata_full_30k/`, tất cả products/valid/sample/report outputs.
- QA hiện tại `Electronics_laptop_3aeb96dfe815.csv` và full-siêu dữ liệu QA
  `Electronics_laptop_8a3c1eaf1583.csv`. hiện tại file 54 True/46 false không bị sửa.
- `data/processed/` (chưa có finished bộ dữ liệu), model/artifact placeholders,
  code/config/tests, hiện tại đang hoạt động plans/README/dictionary/AGENTS/handoff.
- báo cáo và small thước đo bảng chứa khả năng tái lập evidence. lịch sử báo cáo
  có banner phân biệt với quy trình hiện hành; không loại bằng chứng duy nhất.

## lưu trữ đã thực hiện

Chín old lần chạy directories chuyển từ `data/interim/feasibility/` sang `data/interim/archive/feasibility/`, giữ nguyên nội dung:

- `cell_phones_feasibility_small`, `cell_phones_hardening_v4`,
  `cell_phones_probe_v2`, `cell_phones_refactor`.
- `electronics_feasibility_small`, `electronics_hardening_v4`,
  `electronics_metadata_preflight_probe_v4`, `electronics_probe_v2`, `electronics_refactor`.

**25 blank QA CSV** chuyển từ `data/manual/feasibility/` sang `data/manual/archive/feasibility/`: 12 Cell Phones (kể cả laptop negative samples), 8 Electronics Smartphone/Tablet, 5 old Electronics laptop prefix/preflight QA. Tất cả 25 files có blank nhãn và ghi chú trước di chuyển; không xóa con người nhãn gán. Chọn lưu trữ để giữ lịch sử hashes/dependencies thay vì xóa generated evidence.

**22 files bản chụp trạng thái** trước chỉnh sửa ở `reports/archive/p1_legacy_workflow/`: gốc plans/README/dictionary, v4 cấu hình, relevant code/CLIs/tests/requirements. bản chụp trạng thái giữ old full-run settings/code; không được import hoặc execute như hiện tại quy trình. History được rút gọn khỏi hiện tại plans; gốc wording vẫn nằm trong snapshot.

**8 bytecode/test cache directories** chuyển sang `reports/archive/regenerable_caches/` bằng đã xác minh reversible moves. Chi tiết ở `reports/tables/p1_laptop_only_cache_cleanup.json`. tự động phê duyệt review chặn lệnh xóa đệ quy (`blocked by policy`, không có lý do chi tiết hơn); không cache deletion nào được thực hiện. lưu trữ thay thế đã thành công.

Exact file/directory disposition và mapping: `reports/tables/p1_laptop_only_cleanup_inventory.json`. lịch sử tables/report references có thể dùng old paths: tra mapping trong ledger; không đổi các immutable lịch sử fingerprint records để giả vờ paths chưa di chuyển.

## DELETE đã thực hiện

- Active `src/data/product_filter.py`: obsolete multi-phạm vi classifier đã được
  bản chụp trạng thái trước xóa; không còn active imports. laptop filter chuyển về shared `classify_product`, không xóa reusable streaming/survey/QA logic.
- Không xóa raw, model/checkpoint, QA nhãn, datasets hoặc unique báo cáo evidence.

## Code/config/CLI thay đổi

- `configs/feasibility.yaml`: chỉ Electronics nguồn, laptop group/keywords;
  bỏ Smartphone/Tablet rules/source và unused native-source probe settings. Version v5/purpose cập nhật; **tài nguyên ceilings giữ nguyên**.
- Survey/acquisition CLIs không nhận other domain/source options. Direct quy trình
  rejects non-laptop groups trước nguồn access. `Electronics` nguồn được giữ.
- Bỏ cross-phạm vi category ambiguity classification; laptop category/title/accessory
  rules v1 **không đổi**. chuyển đổi có tablet-mode wording vẫn được include nếu có laptop title/category bằng chứng; known CF-19 keyword miss được báo cáo, chưa sửa.
- QA bộ kiểm tra nhận booleans/legacy yes-no, kiểm tra malformed CSV/unique IDs,
  confusion matrix/strata/provenance và không viết nhãn. New báo cáo đầu ra dùng exclusive creation; không giả độc lập con người tập xác thực.
- tóm tắt default toàn bộ laptop lần chạy, chỉ xuất laptop observations và không ghi đè
  summaries cũ. SemEval local audit CLI kiểm tra split/schema/spans/overlap, không download.
- tiếng Anh → Vietnamese/PhoBERT config/interface không đổi, chưa claim tiếng Việt hoạt động.
- `pytest.ini` giới hạn kiểm thử discovery trong active `tests/`, không collect lưu trữ snapshot.

## review REQUIRED — không xóa hoặc di chuyển

`customer_sentiment_analysis_plan.docx`: gốc user document, nội dung/phụ thuộc chưa được audit. Chỉ đề xuất người dùng xem liệu còn cần; giữ nguyên đến quyết định riêng. lịch sử raw non-laptop prefixes: được bảo vệ raw, không xóa theo phạm vi cleanup này. Không có unresolved phụ thuộc buộc phải xóa thêm file.

## tập xác thực

- toàn bộ suite: **96 passed** (`python -m pytest -q`). dữ liệu mẫu scan vẫn stream/join
  và bảo toàn counts/guards/provenance trong laptop-only phạm vi; không scan toàn bộ raw.
- `python -m compileall -q src scripts`: PASS; `python -m pip check`: PASS.
- CLI help/rejected cũ options và active references được kiểm tra.
- Trước/sau: 25 được bảo vệ paths size/mtime khớp; small files hàm băm khớp. toàn bộ survey
  JSONL đầu ra hàm băm rechecked PASS. Không raw multi-GB rehash/decompression lần nữa.
- hiện tại QA whole-file SHA256, immutable rule fingerprint và 100 decisions khớp PASS.
  đã lưu trữ nine lần chạy output/QA fingerprints cũng PASS; tài nguyên ceilings/filter v1 không đổi.
- Bằng chứng: `p1_laptop_only_preservation_before.json` /
  `p1_laptop_only_preservation_after.json` trong `reports/tables/`.

Initial kiểm thử discovery collected đã lưu trữ kiểm thử; cố định by active `testpaths`. Index-budget kiểm thử dữ liệu mẫu được đổi sang hai laptop sản phẩm để tiếp tục kiểm tra kiểm tra giới hạn sau khi bỏ non-laptop các ứng viên; cuối cùng suite PASS, không tắt tài nguyên tests.

## P1 và các hành động tiếp theo

QA đánh giá hoàn thành ở mức **AI-assisted, user-approved**; mẫu độ chính xác dự đoán (precision) PASS, độc lập thủ công filter nghiệm thu chưa đạt. gốc SemEval huấn luyện/kiểm thử BLOCKED do anonymous download redirects to login và restricted-use licence. **P1 chưa hoàn thành**. hiện tại plans đã check QA đánh giá, toàn bộ acquisition/survey/pool/rating/quantity feasibility và demonstrated mẫu rating/product diversity; các các điều kiện nghiệm thu còn thiếu giữ unchecked.

NEXT_ACTION: độc lập sản phẩm QA và authorized gốc SemEval laptop XML, schema/overlap audit. thực tế sạch English/language/dedup/noise/final sampling/splits thuộc **P2**, chưa chạy. Không tự tái tạo bộ dữ liệu hoặc chạy scan lớn khi filter thay đổi.

Giới hạn: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small thủ công annotated bộ dữ liệu gold (chưa có). Không claim cross-gadget hoặc production readiness.
