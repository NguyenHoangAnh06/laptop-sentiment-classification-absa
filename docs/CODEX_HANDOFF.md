# Bàn giao Codex — 2026-10-26

## A. Thẩm quyền và phạm vi

AGENTS/PLAN xác định yêu cầu, artifacts xác định kết quả. Laptop-only, model tiếng Anh, trao đổi/tài liệu tiếng Việt; labels negative/neutral/positive=0/1/2, confidence null. Yêu cầu mới nhất: **GITHUB-PUBLISH-01**, audit và publish snapshot qua P9 lên repository người dùng cung cấp; không corpus/model weights/secrets, không thay khoa học. Mandatory logging AGENTS mục11: Inspect → Execute → Validate → Update Log → Handoff. **Dừng trước P10.**

## B. Trạng thái

**VERIFIED: chuẩn bị GitHub PASS; commit/push PENDING.** Origin `https://github.com/NguyenHoangAnh06/laptop-sentiment-classification-absa.git`, nhánh main; ban đầu Git đã init/chưa HEAD/không remote, remote HEAD rỗng. Ignore bổ sung binary/corpus trong reports/notebook outputs/credentials; hướng dẫn `docs/GITHUB_REPRODUCTION.md`. Audit sau ignore không candidate blockers/secret scan PASS trong phạm vi công bố; inventory local không publish. Targeted6tests PASS/compile PASS, full suite NOT_RERUN. Full before/after SHA2561326files/37037489019bytes không mismatch;5tài liệu được phép đổi. Xem `reports/github_publication_20261026/` và execution log mục15/DEC-014. Không push Codex refs kiểu tree.

**VERIFIED: P3-REFINE-01 DONE.** Canonical trình bày P3 mới `reports/p3_refinement_20261026/report.md` và HTML tự chứa cùng namespace. Audit22items, từ15bảng/7hình generated xuống8bảng core/3hình/9appendix items;13core sections. Không xóa/sửa P3 gốc. README/PLAN_AI/PLAN_HUMAN/PROJECT_INDEX đã dẫn bản mới.

VERIFIED: full `.venv/Scripts/python.exe -X utf8 -B -m scripts.test_all` **386PASS/0FAIL**, nhóm353/25/8,380cũ+6mới; targeted6PASS; pip check/compileall PASS. Source/output/report links PASS, xem validation.json/test_console.log. Dựng lại độc lập từ input copy ở thư mục tạm:19outputs CSV/MD/HTML/PNG/SVG/summary byte-identical; kiểm trực quan3PNG và sửa legend. Full before/after SHA256 **1302file cũ/37036629523bytes**, gồm raw/model weights, không mismatch; preservation.json giữ danh sách. Chỉ7tài liệu điều hướng/log/plan/handoff cũ được phép đổi. Không retrain/model promotion hoặc infer ABSA Amazon.

REPORTED: P0–P9/P9-EXP01 hoàn tất theo từng acceptance; P9-EXP01 DeBERTa ASC canonical, P8 ATE và BERT overall giữ nguyên.380tests/381frozen files của P9-EXP01 là snapshot lịch sử; không ghi lại để nâng test count. P10 independent gold/domain shift/app/toàn dự án vẫn chưa hoàn tất.

## C. Dữ liệu và canonical artifacts

Amazon `data/processed/laptop_reviews.parquet`:30000reviews/9080products, SHA256611b73584a933645336784b13b7f004a17e8803758d1be8ac64708563eabb5ba. Split `data/processed/splits/p4_20261009_final/`21000/4500/4500,seed42; frozen384cache `data/processed/features/semantic_20261024/`. P3 gốc body-only EDA tại `reports/p3/20261009_verified/`, oldreports/notebooks/HTML giữ nguyên; P4 config vẫn trỏ summary cũ.

Canonical overall: `artifacts/models/semantic_20261024/E05_transformer/unweighted/`; ATE: `artifacts/models/p8_20261026/best/`; ASC selector `configs/p9_canonical.yaml`, model `artifacts/models/p9_exp01_deberta_20261026_v2/unweighted/best/`. Previous BERT ASC `artifacts/models/p9_20261026/unweighted/best/` giữ nguyên. SemEval P8 sentence split2587/458/800; P9 non-conflict examples1999/314/638, exclude40/5/16conflict giữ sidecars, không map neutral. Data/predictions có review text chỉ local.

## D. Mã và provenance

P3 mới: `src/data/eda_refinement.py`, `scripts/refine_p3.py`, `configs/p3_refinement.yaml`, `tests/test_eda_refinement.py`. Chỉ đọc saved CSV/summary/later P7 evidence, kiểm dataset hash; rates từ counts, support≥30, top5bigrams/lớp theo prevalence difference/count/term; failure regex công khai. Không hard-code phrase thắng hoặc tạo human labels. Writer từ chối overwrite và output ngoài reports. `summary.json` ghi43source hashes/18output hashes; validation.json thêm test/config/code hashes. Full project preservation riêng trong preservation.json; acceptance.json khóa7evidence hashes.

Original P3 observations khác later P7 confirmation; Neutral mixed-language/fact-like/weak/mixed mechanisms NOT_MEASURED. Mentions từ điển không phải aspect sentiment hoặc causal value drivers. Không sửa src/data/eda.py, legacy analyzers/exporters/model trainers/finalizers chỉ để đổi report.

## E. Kết quả và thay đổi gần đây

- 2026-10-26 GITHUB-PUBLISH-01: chuẩn bị snapshot chọn lọc, `.gitignore`, audit CLI/6fixture tests, README/reproduction guide, audit/preservation/log; scientific artifacts không đổi. Git main/origin đã cấu hình; commit/push đang chờ kiểm index.
- 2026-10-26 P3-REFINE-01:8core tables/3figures; length median negative/neutral/positive50/56/37words,IQR76/93/72; data-driven phrase rates, concentration, verified-group caveat, Neutral và ABSA motivation;386tests/full preservation PASS. DEC-013 và task entry mới trong execution log; không đổi experiment registry/model history.
- 2026-10-26: cài persistent Mandatory Execution Logging trong AGENTS mục11; áp dụng từ task sau cài đặt, tức task refinement này đã phải log.
- 2026-10-26: tái dựng canonical execution log P0–P9-EXP01/27experiment rows/12decisions tại thời điểm audit; chronology PARTIAL,0conversation-derived entries. Snapshot JSON cũ giữ provenance; task mới mở rộng tối thiểu.
- P9-EXP01: DeBERTa promoted bằng validation0,777467 so BERT0,714145; official testmacro0,780433/jointF10,660550 là REPORTED evidence, không chạy lại task này. Seeds43/44validation-only, BERT previous/source archives giữ nguyên.

## F. Nhiệm vụ hiện tại và bước tiếp

**NEXT_ACTION: kiểm index/commit object graph, tạo snapshot commit và push main; xác minh hash local/remote rồi hoàn tất log.** Người dùng đã cho phép commit/push sau audit PASS; không cần xin lại. P10 chỉ mở theo yêu cầu riêng; không annotate/pseudo-label Amazon, làm app hoặc retrain. Giữ canonical P3 report mới cho viết EDA/methodology khi được yêu cầu. Clone GitHub không có corpus/checkpoints/CSV chứa text; không gọi thiếu đầu vào là lỗi khoa học hoặc sửa frozen checks để chạy được.

## G. Failures và giới hạn

**BLOCKED: DeBERTa resume NOT_SUPPORTED** do vocab128003checkpoint vs128100pretrained; seed43 đã fresh restart riêng. NEXT_ACTION: nếu cần resume, sửa/kiểm trong namespace mới, không đổi identity completed runs. Invalid namespace thiếuCLS/SEP/FP16GradScaler giữ, không dùng scores. `attempts.json` report nhắc không tồn tại; FP16log/invalid_attempt/resume_event là evidence còn. Total failed/interrupted compute NOT_MEASURED.

Chronology giờ/lệnh/chat motivations còn thiếu; không suy từ mtime/Git tree refs. Cloud PENDING trong AGENTS/refactor contract là status cũ so full21K acceptance; discrepancies ở execution log. Không tái dựng lịch sử lần nữa nếu không có evidence mới.

Chỉ laptop/noisy star proxy; SemEval source/license NOT_VERIFIED theo owner exception,1official natural duplicate/1train whitespace adjustment giữ nguyên. SemEval–Amazon platform/style shift chưa đánh giá độc lập; gold người gán P10 dự kiến nhỏ và PENDING. Không production/Vietnamese/statistical-superiority claim. P3 complaint specificity và neutral mechanisms chưa human-validated.

## H. Hướng dẫn tiếp tục

Đọc AGENTS/handoff và phần source/evidence liên quan; không đọc toàn bộ project/history cho chỉnh sửa nhỏ. Dựng P3 vào thư mục mới: `.venv/Scripts/python.exe -X utf8 -m scripts.refine_p3 --output-dir reports/p3_refinement_REPRODUCTION`; không overwrite canonical đã nghiệm thu. Test suite dùng scripts.test_all để tách Torch/SDK khỏi data RSS guards.

Không chạy finalizers cũ để sinh lại frozen reports. Xác minh P9 khi cần chỉ dùng saved predictions/provenance theo report; fresh training cần namespace/authorization riêng. Không tự reset/commit/delete artifacts hoặc gán human gold. Execution log/companion ghi task mới, bảo toàn snapshot reconstruction cũ; cập nhật log không tự tạo vòng lặp logging.
