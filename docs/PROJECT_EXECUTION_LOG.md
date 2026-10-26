# Lịch sử thực thi dự án

Ngày tái dựng: **2026-10-26, Asia/Saigon**. Đây là **canonical chronological execution history**; nguồn số liệu khoa học vẫn là artifact được dẫn. Log tổng hợp bằng chứng đã có, không phải chứng nhận rằng mọi lần chạy đã được quan sát lại.

## 1. Existing Log Audit — trước khi tạo log này

**Status: PARTIAL. Proposed Action: B — Existing log is partial; reconstruct missing history.** Chưa có một execution log chung đủ P0 → hiện tại; đã có nhiều lịch sử chuyên biệt. Đã tìm thực tế bằng `rg --files`, duyệt các thư mục dữ liệu/artifact cả phần bị Git ignore, tìm tên/nội dung history/log/manifest/acceptance/decision/preservation và kiểm Git. Không dùng tên dự kiến trong prompt làm bằng chứng file tồn tại.

| File/khu vực tìm thấy | Mục đích, phạm vi thời gian/pha | Chi tiết và khả năng tái dựng |
|---|---|---|
| `reports/p0_initialization.md`; `reports/p1_*.md`; `reports/tables/p1_*.json`; `reports/independent_qa/` | Khởi tạo, acquisition, filter, QA, phê duyệt 2026-10-08–09, P0/P1 | Có lệnh/count/limits/decision; không phải terminal history đầy đủ; riêng chúng không đủ P0 → hiện tại |
| `reports/p2_amazon_completion_20261009.md`; `data/interim/p2/*/manifest.json` | Cleaning, ledger và lần superseded/final P2, 2026-10-09 | Khá chi tiết, có conservation/config/source hash; thiếu wall-clock chronology mọi lần sửa |
| `reports/p3/`; `reports/p3_data_analysis_20261009.md`; `reports/p4*/` | EDA, split/tokenizer/semantic cache, 2026-10-09 và refactor 2026-10-24 | Có output/QA/acceptance; các bản `_final`/`_verified` phải đọc đúng; không tự giải thích toàn bộ quyết định model |
| `reports/p5/p5_20261015/`; `reports/p6/p6_20261015/`; completion reports | P5/P6 LEGACY, 2026-10-15 | Candidate/training history, selection locks, metrics/predictions, cost và metadata; không phải benchmark active |
| `reports/semantic_20261024/`; `reports/tabpfn_resources_20261024/`; `reports/tabpfn_smoke_20261024/` | Benchmark active local E00–E05, attempts và tài nguyên, 2026-10-24 | Lịch sử thí nghiệm khá mạnh; E03 phải theo `latest_attempt.json`; riêng root BLOCKED không phản ánh kết quả cuối |
| `artifacts/cloud_runs/tabpfn_full21k_20261024/`; `reports/tabpfn_kaggle_full21k_verification.*` | Cloud V3/V3_5 và import full21K, 2026-10-24 | Config/lock/environment/resource/metrics/predictions/hash; không fitted weights, không timestamp độc lập từng thao tác |
| `reports/history/tabpfn_before_kaggle_20261024/`; `reports/history/p7_before_human_20261025/` | Snapshot trước thay bảng cloud/trước human completion | Lưu trạng thái cũ có ý nghĩa; không phải log liên tục |
| `reports/p7_error_cause_analysis.*`; `reports/p7_human_*`; `data/manual/sentiment_diagnosis_20261024/` | Diagnosis tooling 2026-10-24, human confirmation 2026-10-25 | Có sampling/provenance/limits; human diagnosis không phải P10 gold |
| `reports/p8_20261026/`; `reports/p9_20261026/`; `reports/p9_exp01_deberta_20261026*/` | ATE, ASC BERT, DeBERTa, 2026-10-26 | Identity/history/lock/metrics/acceptance/preservation/logs; giữ cả invalid/interrupted attempts; chưa có index xuyên pha trước audit này |
| `artifacts/models/`; `artifacts/preprocessing/`; `data/processed/`; `configs/` | Model metadata/checkpoint, data manifests, config hiện hành và LEGACY | Tái lập identity tốt hơn narrative; config hiện tại không chứng minh mọi config lịch sử đã chạy |
| `docs/archive/20261024_before_cleanup/`; `reports/archive/p1_legacy_workflow/` | Snapshot PLAN/README/handoff/code trước cleanup hoặc refactor | Bổ sung lịch sử, có manifest; không đầy đủ mọi phiên bản P0–P9 |
| `PLAN_AI.md`, `PLAN_HUMAN.md`, `README.md`, `docs/PROJECT_INDEX.md`, `docs/CODEX_HANDOFF.md` | Yêu cầu, điều hướng, trạng thái mới nhất | PLAN không đồng nghĩa execution; handoff thay trạng thái cũ và giữ ít cập nhật, không phải archive |
| `.git/` | Git và snapshot nội bộ | Nhánh chưa có HEAD commit, index rỗng; không commit/tag/branch history để dựng chronology. Có 6 refs Codex trỏ đến 5 tree khác nhau, xem mục 3 |

Không phát hiện `CHANGELOG`, `HISTORY` hoặc thư mục `logs/` chung trong các khu vực dự án đã kiểm. Các `history.json` và `*_console.log` thực sự tồn tại dưới `reports/`. Inventory trước thay đổi: docs 17 file, reports 643, configs 21, data 252, artifacts 186, notebooks 2, app 1; đây là inventory audit, không phải số scientific artifacts được nghiệm thu.

**Gaps:** thiếu chronology xuyên pha, bảng thay canonical, index quyết định, ánh xạ failed attempts → recovery, command/time của một số tác vụ và commit execution history. Một số báo cáo đã được bổ sung tại chỗ nên không thể suy ra ngày từng đoạn từ nội dung hiện tại. Acceptance JSON có bằng chứng thực thi nhưng không khôi phục mọi prompt hoặc lý do đã không lưu.

## 2. Reconstruction Feasibility và Conversation Use

**Can reconstruct P0 → current: PARTIAL.** Độ tin cậy **HIGH** cho danh tính dữ liệu/split, các thí nghiệm hoàn tất và model được chọn khi có JSON/config/lock/predictions; **MEDIUM** cho narrative dựa nhiều tài liệu nhất quán. Không đủ để cam kết chronology chính xác đến từng thao tác. Có thể viết methodology/experimental setup/result analysis theo các mốc và giới hạn dưới đây; không thể coi đây là terminal transcript hoàn chỉnh.

Quy ước evidence:

- `VERIFIED`: lần audit này đọc trực tiếp repository artifact hoặc Git object; chỉ xác minh nội dung/tồn tại hoặc kiểm tra cụ thể được ghi, **không** hàm ý đã chạy lại training/test lịch sử. `historical execution: REPORTED_NOT_RERUN` áp dụng cho mọi nghiệm thu cũ.
- `DOCUMENTED`: diễn giải từ report/PLAN/handoff; `HIGH` chỉ dùng khi có artifact độc lập hỗ trợ, nếu chỉ tài liệu thì `MEDIUM`.
- `RECONSTRUCTED_FROM_CONVERSATION`: chỉ dùng cho thông tin chat không có repository confirmation. **Số entry loại này hiện tại: 0.** Phiên này không có quyền truy cập toàn bộ chat cũ; không tự tìm dữ liệu phiên riêng ngoài repository. Approval JSON lưu trong repo được dẫn như approval record, không giả đã đọc chat gốc.
- `date unknown`, `time unknown`, `ordering inferred from artifact dependencies` phân biệt với ngày ghi rõ trong report/acceptance. Ngày trong tên namespace là định danh; chỉ dùng làm ngày lịch sử khi report/metadata xác nhận. Không dùng filesystem mtime hoặc số trong ref Codex làm execution timestamp.

**Can old conversations reconstruct a standard log?** Có thể bổ sung narrative: ý định người dùng, lựa chọn bị bác bỏ, lý do đổi hướng, thời điểm yêu cầu model. Không đủ làm bằng chứng duy nhất cho metric/hash/count/config/test/timestamp. Mỗi chat-derived assertion cần nguồn/đoạn trích được cung cấp, nhãn reconstruction, confidence và đối chiếu file/lock/predictions tương ứng. Rủi ro: assistant claim chưa chạy, nhớ sai run, trộn local/cloud, nhầm canonical/baseline hoặc chat sau nghiệm thu được kể như quyết định trước test. Khi mâu thuẫn, ghi cả discrepancy và ưu tiên artifact khoa học có provenance; không dùng chat sửa score. Log chuẩn có thể chứa chat narrative có nhãn, nhưng scientific execution evidence phải dựa artifact.

## 3. Git evidence và chronology tổng quan

Đã chạy `git status --short`, `git rev-parse --verify HEAD`, `git log --all`, `git branch -a`, `git tag`, `git ls-files`, `git for-each-ref`, `git cat-file -t`, `git ls-tree` và `git show <tree>:docs/CODEX_HANDOFF.md`. HEAD verify thất bại vì nhánh chưa có commit; log/branches/tags/index không trả lịch sử dự án. Các ref nội bộ là **tree**, không phải commit, không có commit date/message/parent.

| Git tree đọc được | Nội dung snapshot xác nhận | Giới hạn |
|---|---|---|
| `1ce67d3a8cfb890bd0b52264fabfa71bd6fde329` | Handoff đề ngày 2026-10-24: 249tests, TabPFN local LIMITED, cloud PENDING | Chứng minh snapshot, không chứng minh giờ chạy |
| `62cec2c06e1982303b13940d5d92605222425a95` | Handoff 2026-10-24: cloud SUCCESS, 306tests, human diagnosis PENDING | Thứ tự nội dung khớp phụ thuộc cloud → diagnosis |
| `1e7434e1bfb0ce68e5feb90e7e17acc34a5bd13c` | Handoff 2026-10-26: P9 BERT DONE, 378tests | Không commit history P0–P8 |
| `8025546a42c544763f2575e3c2e3fce384f28f36` | Snapshot P9 BERT trước P9-EXP01, cùng nội dung trạng thái | Không coi hai snapshot là hai experiment |
| `780edc5da1c0612a119839ba146adca5c3c82741` | Handoff 2026-10-26: P9-EXP01 DeBERTa promoted, 380tests | Hai refs cùng tree; không suy số lần chạy từ số refs |

Nội dung handoff trong tree vẫn là `DOCUMENTED`; tree identity/type/existence là `VERIFIED`. Không reset/checkout/commit hoặc phục hồi ghi đè file từ các tree. Companion JSON giữ refs/object IDs và SHA256 các handoff blobs đã đọc.

| Ngày/mốc | Sự kiện có căn cứ | Trạng thái thời gian |
|---|---|---|
| 2026-10-08 | P0; P1 prefix/probe → hardening → full Electronics scan → laptop-only cleanup | Ngày từ reports; giờ và thứ tự chi tiết không biết |
| 2026-10-09 | QA/acceptance exceptions; Amazon P2 final; P3; P4 final | Dependency order P1 approvals → P2 → P3 → P4; approval SemEval/P2 cùng ngày không khôi phục giờ |
| 2026-10-15 | P5 TF-IDF; P6 BERT body-only | P5 → P6 theo dependency; không có commit timestamps |
| 2026-10-19 | Việt hóa tài liệu/trao đổi | DOCUMENTED tại `docs/VIETNAMESE_TRANSLATION.md`; không model tiếng Việt |
| 2026-10-24 | Refactor P0–P7 semantic; local LIMITED → cloud preparation → Kaggle import; diagnosis tooling | Các bước có reports/snapshot; không có wall-clock transcript đầy đủ |
| 2026-10-25 | Human diagnosis hoàn tất; nghiệm thu P0–P7 | Acceptance/date/confirmation trong repo |
| 2026-10-26 | P8 ATE → P9 BERT ASC/joint → P9-EXP01 DeBERTa/recovery/stability/promotion | Dependency order; ngày nghiệm thu, không giờ promotion độc lập |
| 2026-10-26 | Audit và tái dựng log này | Thực hiện phiên này; không chạy thí nghiệm mới |

## 4. Project Metadata

- Dự án: `customer-sentiment-laptop-reviews`, Sentiment/ABSA **laptop-only**, model tiếng Anh; labels sentiment/ASC `negative/neutral/positive` = 0/1/2. Confidence chưa calibration: `null`.
- Started: **2026-10-08 là mốc khởi tạo sớm nhất được tài liệu repository xác nhận**; ngày bắt đầu ý tưởng trước đó `date unknown`.
- Current phase: P9-EXP01 COMPLETE, READY FOR P10; **P10–P13 chưa hoàn tất**, không tự mở P10 từ tác vụ log.
- Sentiment canonical: `E05_transformer`, BERT title + body, unweighted epoch3, `artifacts/models/semantic_20261024/E05_transformer/unweighted/`.
- ATE canonical: BERT token classifier epoch4, `artifacts/models/p8_20261026/best/`.
- ASC canonical: DeBERTa-v3-base seed42 unweighted epoch5, `configs/p9_canonical.yaml`; previous BERT vẫn giữ ở `artifacts/models/p9_20261026/unweighted/best/`.
- Amazon: P2 `20261009_final`, `data/processed/laptop_reviews.parquet`, 30.000 review/9.080 sản phẩm, SHA256 `611b73584a933645336784b13b7f004a17e8803758d1be8ac64708563eabb5ba`. Split `p4_20261009_final` = 21.000/4.500/4.500; cache `semantic_20261024`.
- SemEval laptop: official train 3.045/test 800 câu; P8 split train/validation/test 2.587/458/800; P9 non-conflict aspect examples 1.999/314/638. Không trộn Amazon proxy với SemEval gold.
- Evidence: [P0 report](../reports/p0_initialization.md), [P0–P7 acceptance](../reports/p0_p7_acceptance.json), [benchmark CSV](../reports/p7_unified_results.csv), [P8 manifest](../data/processed/p8_20261026/manifest.json), [P9 selector](../configs/p9_canonical.yaml). Nội dung artifact `VERIFIED`, lịch sử không rerun.

## 5. Timeline theo phase

### P0 — Khởi tạo, rồi cập nhật môi trường model stack

**Mốc:** 2026-10-08; bổ sung model stack 2026-10-24. **Objective/inputs:** repository và hợp đồng laptop-only/English, seed42, 3labels, macro F1; ban đầu chưa có dữ liệu.

**Tasks:** P0-T01–T04 tạo Git/ignore/venv/cấu trúc/config, registry/inference schema dùng chung single/batch, dành chỗ `vi` disabled. Python thực tế 3.13.12; không giả đã test 3.11. Model stack sau bổ sung Torch2.8.0+cu128/Transformers5.0.0 và TabPFN SDK/version checks; chi tiết dependencies ở artifact môi trường, không suy ngược pins P0 từ requirements hiện tại.

**Scripts/config/artifacts:** `configs/data.yaml`, `configs/model.yaml`, `configs/language.yaml`, `src/config.py`, `src/inference/schema.py`, `src/models/registry.py`, `requirements.txt`, `reports/p0_dependency_resolution.json`, `reports/p0_model_stack_environment.json`.

**Results/tests/acceptance:** P0 report ghi install/pip check/9passed; P0 stack nghiệm thu sau bằng version/checkpoint distinction. DONE_WHEN môi trường và config/schema có bằng chứng, không cần app/train. Initial blockers thiếu dữ liệu là lịch sử, không phải blocker hiện tại. **Evidence:** [khởi tạo](../reports/p0_initialization.md) `DOCUMENTED`; [resolution](../reports/p0_dependency_resolution.json), [stack](../reports/p0_model_stack_environment.json), [acceptance P0](../reports/p0_p7_acceptance.json) `VERIFIED`. Confidence HIGH cho artifact, MEDIUM cho chi tiết khởi tạo chỉ report.

### P1 — Nguồn, laptop filter, QA và quyết định nghiệm thu

**Mốc:** 2026-10-08–09. **Objective/inputs:** Amazon Reviews2023 Electronics review + metadata, join `parent_asin`; SemEval-2014 laptop giữ original partitions/spans/polarity. Không xác định laptop từ review/rating.

**Tasks:** acquisition có manifest/checksum/resource guards; kiểm schema/aliases; prefix đầu chỉ join được ít laptop, sau chuyển metadata-first streaming full scan, deterministic sampling và filter category/title/exclusion. Probe Smartphone/Tablet có trong archive lịch sử; **không phải dữ liệu/model thuộc dự án hiện hành**. Laptop-only cleanup có ledger, không xóa dấu vết quyết định cũ. T01–T08 chi tiết/convention cũ tra PLAN archive và báo cáo, không dựng task ID mới.

**Raw scale/results:** full scan 1.610.012 metadata + 43.886.944 review; chọn 28.172 sản phẩm; 408.740 matched = 408.480 valid + 260 invalid text. 28.161 sản phẩm có valid review; survey sample 5.000 là subset. Full source EOF không đồng nghĩa thu hồi mọi laptop. Raw/processed candidate khác nhau; P1 không chứng nhận clean-English yield.

**QA/decisions:** KEEP150review và150product đều laptop theo nhãn; REJECT pilot150 và complement868 hỗ trợ recall point89,0767%, joint95% CI55,4584–99,8455%, không ngưỡng recall đạt chắc chắn. C1-A chấp nhận selected-pool coverage; C2-A chấp nhận human-verified assisted QA giới hạn P1; C3-A giữ sampling/brand monitoring; C4-B cho Amazon-only P2 khi SemEval còn blocked. Sau đó owner exception riêng chấp nhận SemEval source/license **NOT_VERIFIED** cho dự án giáo dục, không biến thành quyền đã xác minh. Independent P10 gold vẫn bắt buộc. Cùng ngày, thứ tự approvals theo liên kết `previous_approval_record`, không giờ tự suy.

**Key scripts/configs:** `scripts.acquire_p1`, `survey_p1`, `audit_p1`, `src/data/loader.py`, `feasibility.py`, `laptop_filter.py`, `configs/acquisition.yaml`, `feasibility.yaml`. Report ghi command thực chạy full survey với `--source Electronics --groups laptop --run electronics_full_laptop_30k --mode scan --allow-large-scan`; command đầy đủ ở nguồn, không hướng dẫn chạy lại vào namespace cũ.

**Artifacts:** raw manifests `data/raw/amazon/`, `data/interim/feasibility/electronics_full_laptop_30k/`, `reports/tables/electronics_full_laptop_30k*.json`, `reports/independent_qa/`, `data/manual/independent_qa/`, SemEval XML/converted JSONL. **Tests:** các mốc 33/60/84/139 trong reports; 53passed survey-targeted không phải full suite. **Acceptance:** P1 DONE WITH LIMITATION theo owner decisions, không QA độc lập hoàn hảo hay license VERIFIED.

**Evidence:** [survey](../reports/p1_full_laptop_survey.md), [QA v2](../reports/p1_qa_v2_completion_20261009.md), [quyết định](../reports/p1_acceptance_decision_20261009.md) `DOCUMENTED`; [owner approvals](../reports/tables/p1_owner_approval_20261009.json), [SemEval exception](../reports/tables/p1_semeval_owner_exception_20261009.json), [cleanup](../reports/tables/p1_laptop_only_cleanup_inventory.json), [revalidation](../reports/p1_revalidation_for_new_models.json) `VERIFIED`. Confidence HIGH cho các counts/records, lý do ngoài văn bản đã lưu unknown.

### P2 — Cleaning, proxy labels và Amazon30K final

**Mốc:** 2026-10-09; phụ thuộc P1 candidate + approvals. **Tasks P2-T01–T09:** validate/quarantine, làm sạch HTML/entities/whitespace giữ phủ định/case/punctuation, exact normalized dedup, conflict-group quarantine, QA reservations, language gate, sampling/dataset/brand audit và noise worklist. Rating1–2→negative,3→neutral,4–5→positive; không human gold.

**Row ledger:** 408.480 input = 8.406 QA reserved + 4Unicode quarantine + 4.621 label-conflict quarantine + 15.439 consistent duplicate excess + 380.010 eligible unique groups. Language-assess36.000 → 33.483 pass; 2.517 uncertain/non-English; 344.010 chưa assess. Chọn30.000 bằng seed42/hash rank, cap100/product, không rating/brand quota. Final8259negative/2631neutral/19110positive; 9.080product/181metadata brand categories. Noise queue250 **unannotated diagnostic**, reserved khỏi model dataset, không P10 gold.

**Implementation/config:** `src/data/{cleaning,labeling,near_duplicates,p2_pipeline}.py`, `scripts.prepare_p2_amazon`, `scripts.report_p2_amazon`, `configs/p2.yaml`; Lingua2.1.1, thresholds/margin/ASCII policy cấu hình. `data/interim/p2/20261009/` là superseded: floating-point detector variation và encoded-HTML residual sửa rồi chạy saved candidate thành `20261009_final`.

**Results/artifacts/tests:** parquet30K, final manifest, SQLite ledger, QA tables/label_distribution/brand_before_after; report ghi final86,4251s, peak441.520.128bytes, 161passed và targeted18. **Acceptance:** conservation/hash/label/negation/reservation/reload PASS. True language/spam/semantic-near/noise rates NOT_MEASURED; không suy heuristic = ground truth. **Evidence:** [completion](../reports/p2_amazon_completion_20261009.md) `DOCUMENTED`; [manifest](../data/interim/p2/20261009_final/manifest.json), [validation](../reports/tables/p2_amazon_20261009_final/validation.json), [revalidation](../reports/p2_revalidation_for_new_models.json) `VERIFIED`. Confidence HIGH cho saved final state; initial rerun wall-clock unknown.

### P3 — EDA, insights và readiness

**Mốc:** 2026-10-09; model readiness bổ sung trong refactor2026-10-24. **Inputs/objective:** cố định P2 parquet30K, mô tả dataset và giới hạn; không dùng cue để giả ABSA.

**Tasks/results:** rating/length/time/helpfulness/verified purchase/brand/product/vocabulary/quality analysis; 15tables/7PNG–SVG figure pairs, deterministic fresh-kernel notebook6code cells. Neutral8,77%, majority/minority7,2634 thúc đẩy macroF1/per-class/validation weighting comparison. Readiness canonical title+body có BERT lengths p50=61,p95≈403,max4159; những số này không phải token lengths của mọi encoder. Dense384/768 memory là ước lượng, không model fit peak đo được. Không rerun EDA cũ chỉ để refactor model.

**Code/config/artifacts:** `src/data/eda.py`, `scripts/analyze_p3.py`, `scripts/execute_p3_notebook.py`, source notebook `notebooks/03_laptop_eda.ipynb`, bản thực thi cuối `reports/p3/20261009_verified/03_laptop_eda.final.ipynb`, `reports/p3_model_readiness.*`. Các nhóm tác vụ EDA theo PLAN/archive; không khẳng định có log riêng mọi cell.

**Tests/acceptance:** saved task_validation169full-suite,8fixture tests,41protected checksums; notebook PASS. DONE_WHEN insight có bảng/hình, proxy-label limits công bố; resource feasibility từng model còn warning chờ phép đo. **Evidence:** [analysis](../reports/p3_data_analysis_20261009.md), [readiness](../reports/p3_model_readiness.md) `DOCUMENTED`; [task validation](../reports/p3/20261009_verified/task_validation.json), [summary](../reports/p3/20261009_verified/summary.json), [readiness JSON](../reports/p3_model_readiness.json) `VERIFIED`. Confidence HIGH cho output, MEDIUM cho narrative.

### P4 — Split chống leakage; LEGACY representation → semantic cache

**Mốc:** 2026-10-09, mở rộng representation2026-10-24. **Inputs:** P2 fixed30K/P3, không resplit khi refactor.

**Tasks P4-T01–T06/results:** connected grouping product/variant/normalized/preprocessed/lexical-near; seed42, deterministic class-balanced greedy. Final21K/4,5K/4,5K đạt exact class quotas,9.080groups,0excluded. Train classes5781/1842/13377; validation1239/395/2866; test1239/394/2867. Product-disjoint; checks IDs/parent/variant/groups/text/near overlaps. Lexical near search không chứng minh mọi semantic paraphrase đã sạch.

**LEGACY:** TF-IDF fit train-only; BERT body-only max512 từ trainp95=390. Lần `p4_20261009` dừng guard512MB khi tokenizer; giữ STATUS INCOMPLETE/SUPERSEDED, tối ưu bộ nhớ rồi `p4_20261009_final`, không âm thầm sửa manifest cũ.

**Active:** canonical title+newline+body minimal NFC/whitespace; MiniLM-L6-v2 revision`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, frozen384, mask-mean/L2/FP32/max256; sample128train kiểm tài nguyên/consistency, không chọn encoder bằng label score. Cache đủ30K, row mapping/hash/config/tokenizer; BERT canonical tokenizer riêng max512, revision`86b5e0934494bd15c9632b12f734a8a67f723594`. Không TF-IDF/BoW/PCA/SVD/metadata trong active input.

**Key files/artifacts:** `configs/p4.yaml`, `configs/semantic_benchmark.yaml`, `src/data/split.py`, `src/preprocessing/{english,bert,semantic,semantic_cache}.py`, `scripts.prepare_p4`, `scripts.prepare_semantic`; split `data/processed/splits/p4_20261009_final/`, legacy features/preprocessing giữ, new `data/processed/features/semantic_20261024/`.

**Tests/acceptance:** P4 historical180tests; reload/leakage/alignment/hash PASS; semantic split equality và independent cache validation PASS. Test đã được dùng ở LEGACY nên benchmark active không phải toàn dự án chưa từng xem test. **Evidence:** [P4 completion](../reports/p4_completion_20261009.md), [semantic](../reports/p4_semantic_representation.md) `DOCUMENTED`; [manifest](../reports/p4/p4_20261009_final/manifest.json), [initial status](../reports/p4/p4_20261009/STATUS.txt), [semantic split validation](../reports/p4_semantic_split_validation.json), [cache validation](../reports/p4_semantic_independent_validation.json) `VERIFIED`. Confidence HIGH cho dataset/cache identity, giờ thực thi unknown.

### P5 — LEGACY classical → frozen embeddings local → cloud full21K

**Mốc:** 2026-10-15 LEGACY; 2026-10-24 active/local/cloud. **Inputs:** cùng Amazon split; active384frozen features; validation macroF1 chọn, test sau lock.

**LEGACY tasks:** P5-E00majority/E01LR/E02LinearSVM/E03DecisionTree;13fits (1+4+4+4), LR/SVM C0,5/2 × weightsNone/balanced; DT depths10/25,leaf5 × weights. WinnerLR C0,5/balanced val0,693554/test0,683887;195tests. Đây là convention P5 cũ, **không đồng nhất P5-E03DecisionTree với active E03TabPFN**.

**Active tasks E00–E04:** majority sanity; XGBoost selected depth4/lr0,05/250trees/weighted; TabM selected weighted,3blocks/d256/k32/dropout0,1,lr0,001/batch256/max25/patience5. Resource probes train-only TabPFN phân biệt SDK `ModelVersion.V3` và `V3_5`; local E03 license BLOCKED ở root rồi retry hợp lệ tại `attempts/resource01`, selected10Ktrain; E04selected1500. Local LIMITED, V3RSS6,4828GB vượt trần6GB, n_estimators1coverage tối đa200/384; không đổi embedding dimension để che giới hạn.

**Cloud P5-C01–C06:** chuẩn bị bundle/hash/manifest/script/notebook, người dùng chạy Kaggle T4, Codex import ZIP và tính lại saved metrics. `C-E03` V3 và `C-E04` V3_5 fit đủ21K, validation/test4500mỗi; seed42, n_estimators1,fit_with_cache/memory saving/cacheCPU/autocast/batch16. Train-only probes tới21000 PASS riêng mỗi version. Cloud chỉ trả results, không fitted weights. Full rows không xóa hạn chế nội bộ V3 hoặc test reuse.

**Final results:** XGBoost val/test0,664566/0,667752; TabM0,680132/0,689086; cloudV3 0,580694/0,572971; cloudV3_5 0,614332/0,614017. Bảng local trước cloud giữ nguyên: V3test0,562544, V3_5test0,570952. Cloud fit7,968s/21,146s, wall80,047s/119,244s; hardware khác nên không quy chênh lệch trực tiếp cho model. Không tune theo test sau import.

**Files:** `configs/{p5,modern_tabular}.yaml`, `scripts/{train_p5,train_modern,prepare_kaggle_tabpfn,verify_kaggle_results,publish_kaggle_results}.py`, `src/sentiment/{classical,modern,tabpfn_versions}.py`; `reports/semantic_20261024/`, `reports/tabpfn_resources_20261024/`, `cloud/kaggle_tabpfn_full21k/`, `artifacts/cloud_runs/tabpfn_full21k_20261024/`. **Acceptance/tests:** local249tests, bundle276, import291; P5 DONE WITH LIMITATION sau full cloud verified, local giữ LIMITED lịch sử.

**Evidence:** [legacy](../reports/p5_completion_20261015.md), [local results](../reports/p5_modern_tabular_models.md), [cloud](TABPFN_CLOUD_PLAN.md) `DOCUMENTED`; [legacy manifest](../reports/p5/p5_20261015/manifest.json), [current CSV](../reports/p7_unified_results.csv), [local snapshot CSV](../reports/history/tabpfn_before_kaggle_20261024/p7_unified_results.csv), [import verification](../reports/tabpfn_kaggle_full21k_verification.json), [E03 pointer](../reports/semantic_20261024/E03_tabpfn_v3_embedding/latest_attempt.json) `VERIFIED`. Confidence HIGH cho saved metrics/protocol; không có independent attestation thời điểm cloud selection/test.

### P6 — BERT overall sentiment: body-only → canonical title + body

**Mốc:** 2026-10-15 và2026-10-24. **Inputs:** cùng21K/4,5K/4,5K,3proxy labels. Pretrained BERT base uncased revision`86b5e0934494bd15c9632b12f734a8a67f723594`; fine-tune toàn backbone, không frozen head-only.

**Tasks P6-T01–T06:** tokenizer/dataset/collator, smoke forward/backward, unweighted/balanced, epochs/history, checkpoint/selection lock/reload, một test inference sau lock. AdamW lr2e-5,weight_decay0,01,warmup0,1,physical8×accum4=32,max3epochs,seed42,max512,FP16autocast/GradScaler,eval16,gradient checkpointing. Weights chỉ train; chọn macroF1validation, không mặc định balanced.

**LEGACY:** body-only balancedepoch3 thắng val0,734646/test0,730204; giữ artifact/baseline và207tests(195+12). **Active E05:** canonical title+body unweightedepoch3 thắng val0,760338/test0,755382; accuracy0,886667,weightedF10,886262,neutralF10,436129. Đây là thay representation/model selection mới; không sửa score LEGACY hoặc diễn giải delta là tác động nhân quả riêng title.

**Artifacts/scripts:** `configs/{p6,transformer_benchmark}.yaml`, `src/sentiment/bert.py`, `scripts/{train_p6,train_transformer}.py`; `reports/p6/p6_20261015/`, `reports/semantic_20261024/E05_transformer/`; bestactive`artifacts/models/semantic_20261024/E05_transformer/unweighted/`. Runtimeactive2303,734s/RSS3,118GB/selected438.674.765bytes; từ saved result, không đo lại.

**Acceptance/limits:** đủ21K, pinned config/version/labels, selection+saved prediction verification PASS; một seed/search nhỏ, context/tokenization khác384encoder, testreuse, không significance/calibration/production claim. **Evidence:** [legacy report](../reports/p6_completion_20261015.md), [active report](../reports/p6_transformer_benchmark.md) `DOCUMENTED`; [legacy manifest](../reports/p6/p6_20261015/manifest.json), [active result](../reports/semantic_20261024/E05_transformer/result.json), [history](../reports/semantic_20261024/E05_transformer/history.json), [lock](../reports/semantic_20261024/E05_transformer/selection_lock.json) `VERIFIED`. Confidence HIGH cho result/identity.

### P7 — Unified evaluation, error analysis và human diagnosis

**Mốc:** 2026-10-24–25; phụ thuộc P5/P6, trước P8. **Tasks:** so6model cùnglabels/metrics/cost/ID-aligned predictions; thay hai dòng local bằng cloud provenance, snapshot bảng cũ; phân tích confusion/neutral/error agreement/weighting; chuẩn bị blinded human diagnosis và nghiệm thu sau người xác nhận.

**Results:** canonical sentiment vẫnBERT, bestfrozenTabM; accuracy cao không che neutralF1 thấp củaTabPFN. Diagnosis360review = 300SRS từ4500test +60enriched riêng; người dùng xác nhận human-reviewed2026-10-25, một reviewer. Proxy disagreement68/360 là mô tả mẫu gộp; SRS31/300 có CItest-population riêng; enriched37/60 không population inference. Không dùng nhãn diagnosis tune/relabel/rank lại model. BERT humanmacro0,674358gộp/0,691746SRS là diagnosis, không thay scorecanonical0,755382. Causal fraction do imbalance chưa xác định.

**Key files:** `scripts/{analyze_error_causes,finalize_p7_acceptance}.py` và công cụ human diagnosis được dẫn trong `docs/SENTIMENT_DIAGNOSIS.md`; logic`src/evaluation/{error_diagnosis,human_diagnosis}.py`; `data/manual/sentiment_diagnosis_20261024/`, `reports/p7_human_*`, `reports/p7_error_*`. Không nhầm QA sản phẩm P1 hoặc noise250P2 với human diagnosisP7/P10.

**Tests/acceptance:** tooling306tests rồi human completion321; preservation153scientific +53legacy và snapshot185 ghi trong acceptance. P0–P7PASS/DONE có giới hạn từng pha. **Evidence:** [benchmark](../reports/p7_unified_benchmark.md), [diagnosis](../reports/p7_error_cause_analysis.md) `DOCUMENTED`; [completion](../reports/p7_completion.json), [human result](../reports/p7_human_audit_results.json), [test validation](../reports/p7_error_diagnosis_validation.json), [acceptance](../reports/p0_p7_acceptance.json), [pre-human snapshot](../reports/history/p7_before_human_20261025/p7_error_diagnosis_validation.json) `VERIFIED`. Confidence HIGH cho saved outcome; human label correctness ngoài confirmation/annotation evidence chưa independent audit.

### P8 — BERT Aspect Term Extraction

**Mốc:** 2026-10-26, sau P7 acceptance. **Objective/inputs:** SemEval laptop gold character spans; explicit terms, không business taxonomy hoặc polarity ở extractor.

**Tasks P8-T01–T04:** parse giữ IDs/original offsets; BIO `O/B-ASP/I-ASP` trên mọi WordPiece, ignore special/pad; whitespace biên có provenance, orphan I bắt đầu entity khi decode; sentence-group split chỉ từ official train. Train/validation/test = 2.587/458/800 câu, gold entities2.039/319/654. `train:1436` original[44,54)→extraction[44,53) do NBSP biên, giữ original. Zero unexplained alignment failures/truncation. Natural official train/test duplicate ID227 giữ và công bố; qualified UID tránh ID collision; không test-driven deletion.

**Config/results:** BERT pinned như P6, AdamW lr3e-5, weight_decay0,01, warmup0,1, batch8×accum2=16, eval16, max128, 5epochs, seed42. Chọn **epoch4 bằng validation entity F1**. Validation P/R/F1=0,765043/0,836991/0,799401; official test một pass sau lock=0,785714/0,824159/0,804478; 539TP/147FP/115FN. Best model `artifacts/models/p8_20261026/best/`; runtime319,245s/selected436.311.903bytes.

**Code/artifacts/tests:** `configs/p8_aspect_extraction.yaml`, `src/absa/{extraction,extraction_data}.py`, `src/evaluation/aspect_extraction.py`, `scripts/{prepare_p8,train_p8,finalize_p8}.py`, processed/interim/reports namespace `p8_20261026`. 350tests/CPU smoke/metric recompute PASS;269protected files. **Acceptance:** spans/model/entity metrics/error analysis/reproducibility có thật, DONE/FROZEN. Giới hạn single seed, cap128, source/license NOT_VERIFIED, Amazon shift/gold PENDING.

**Evidence:** [report](../reports/p8_aspect_extraction.md) `DOCUMENTED`; [manifest](../data/processed/p8_20261026/manifest.json), [result](../reports/p8_20261026/result.json), [acceptance](../reports/p8_20261026/acceptance.json), [validation](../reports/p8_20261026/validation.json) `VERIFIED`. Confidence HIGH.

### P9 — Gold-aspect ASC BERT và end-to-end ABSA

**Mốc:** 2026-10-26, sau frozen P8. **Tasks P9-T01–T04:** context+specific aspect occurrence, exclude conflict giữ sidecars, train/eval3labels, nối P8 saved predicted spans→ASC; không dùng overall sentiment làm nhãn mọi aspect.

**Inputs/representation:** sentence IDs P8 cố định; aspects2039→1999train,319→314validation,654→638test sau exclude40/5/16conflict, không map neutral. `[CLS] context_before [unused0] target_occurrence [unused1] context_after [SEP]`, định vị bằng offset thay vì chỉ `text.find`; BERT markers IDs1/2,vocab30522. Max128/zero truncation; giữ source/spans/polarity.

**Config/results:** BERT pinned, lr3e-5,5epochs,batch8×accum2,seed42,AdamW/warmup như P8, loss unweighted/balanced. Unweighted epoch4 valmacro0,714145 thắng balanced epoch4=0,712292. Official gold-aspect test một pass sau lock: macro0,748118/accuracy0,789969/weightedF10,785988. Joint frozen P8 test F1=0,634557; joint exact span+polarity micro F1 khác standalone macro F1, không gộp mẫu số. Không infer P8 lại hoặc dùng predicted-aspect score chọn ASC.

**Code/artifacts/tests/acceptance:** `configs/p9_aspect_sentiment.yaml`, `src/absa/{sentiment,sentiment_data}.py`, `src/inference/absa.py`, `scripts/{prepare_p9,train_p9,evaluate_p9_end_to_end,finalize_p9}.py`; namespace `p9_20261026`, best `artifacts/models/p9_20261026/unweighted/best/`. 378tests/317protected files/CPU classifier+pipeline PASS; P9 DONE trước P10. BERT canonical tại mốc này, sau trở previous canonical.

**Evidence:** [report](../reports/p9_aspect_sentiment.md) `DOCUMENTED`; [manifest](../data/processed/p9_20261026/manifest.json), [lock](../reports/p9_20261026/selection_lock.json), [result](../reports/p9_20261026/result.json), [joint](../reports/p9_20261026/end_to_end_results.json), [acceptance](../reports/p9_20261026/acceptance.json) `VERIFIED`. Confidence HIGH.

### P9-EXP01 — DeBERTa, failed attempts, stability và promotion

**Mốc:** 2026-10-26. **Objective/inputs:** đổi backbone ASC, reuse đúng P9 dataset/protocol/P8 frozen. Nguồn tham khảo ngoài lưu ở `reference.json`; không lấy metric ngoài làm kết quả dự án.

**Primary config:** `microsoft/deberta-v3-base` revision`8ccc9b6f36199bec6961081d44eb72fb3f7353f3`; native tokenizer CLS/SEP,markers128001/128002,vocab128003,max128; token maximum train/validation/test94/59/87. Giữ1999/314/638examples, IDs/offsets/conflict/marker strings;lr3e-5,5epochs,AdamW,warmup0,1,unweighted/balanced,seed42. Physical batch4×accum4=16 so với BERT8×2; native tokenizer/eager attention là thay đổi kèm backbone, không khẳng định mọi điều kiện tính toán giống hệt.

**Failures/recovery:** namespace `p9_exp01_deberta_20261026` INVALID_FOR_COMPARISON: FP16 parameters/GradScaler failure, sau đó phát hiện conversion thiếu CLS/SEP, dừng trước selection/test. V2 sửa chuẩn tokens, restart pretrained; không dùng invalid scores. Seed43 interrupted epoch5; resume bị chặn vì pretrained vocab128100 khác checkpoint128003, chưa train/test thêm. Fresh restart `_seed43_restart01`, giữ attempt cũ. Resume NOT_SUPPORTED, không đồng nghĩa reload/inference lỗi. Report dẫn `attempts.json` nhưng file **không tồn tại**; bằng chứng còn là `attempt01_fp16_failure.log`, `invalid_attempt.json`, `resume_event.json` và console logs.

**Selection/results:** unweighted epoch5 valmacro0,777467 thắng balanced epoch4=0,765511 và BERT0,714145. `canonical_decision.json` ghi PROMOTED dựa validation, delta0,063322. Official test một pass sau lock: macro0,780433/accuracy0,815047/weightedF10,813232; F1negative/neutral/positive=0,772277/0,668874/0,900149. Paired fixed49/regressed33/both-correct471/both-wrong85. Joint frozen P8 P/R/F1=0,644776/0,677116/0,660550; exact-span sentiment errors108→91, extraction counts không đổi. Protocol records ghi test/joint chỉ báo cáo; không có independent timestamp attestation.

**Stability/cost:** seed43restart val0,767943epoch4;seed44val0,754664epoch3;seed42val0,777467epoch5. Mean0,766691/sample SD0,011453, validation only, không best-of-seeds/mean thay primary; BERT chưa multi-seed tương đương. Primary hai loss loops1861,358s/wall1956,263s/selected745.766.987bytes/RSS4,868GB/GPU allocated3,772GB. Controlled cùng314validation IDs,batch16,warmup1,3measured passes: median BERT1,016713 vs DeBERTa1,806148ms/aspect từ tokens. Original test7,912ms/aspect dùng batch8/điều kiện khác; giữ riêng và lưu initial contended timing. Tổng cost mọi failed/interrupted attempt NOT_MEASURED.

**Code/artifacts/tests/acceptance:** `configs/p9_exp01_deberta.yaml`, selector `configs/p9_canonical.yaml`, `scripts/{p9_exp01,finalize_p9_exp01}.py`, `src/absa/sentiment_backbone.py`, `src/evaluation/asc_comparison.py`; namespaces V2/stability. 380tests/0FAIL,381frozen files gồm P0–P8/baselineP9; previous11source/current20source hashed. COMPLETE/READY FOR P10, không mở gold/app. Confidence HIGH cho saved results/selection, MEDIUM cho wall-clock ordering.

**Evidence:** [report](../reports/p9_exp01_deberta_20261026_v2/report.md) `DOCUMENTED`; [decision](../reports/p9_exp01_deberta_20261026_v2/canonical_decision.json), [lock](../reports/p9_exp01_deberta_20261026_v2/selection_lock.json), [result](../reports/p9_exp01_deberta_20261026_v2/result.json), [stability](../reports/p9_exp01_deberta_20261026_v2/stability.json), [resume](../reports/p9_exp01_deberta_20261026_v2/resume_event.json), [latency](../reports/p9_exp01_deberta_20261026_v2/validation_latency.json), [acceptance](../reports/p9_exp01_deberta_20261026_v2/acceptance.json) `VERIFIED`.

### P10–P13 — PENDING

P10 independent human Amazon sentiment/ABSA gold300–500 và platform/style-shift evaluation; P11thin Streamlit single/batch; P12Vietnamese/PhoBERT extension; P13final report/reproducibility chưa đủ nghiệm thu. Không biến P7diagnosis360 thành P10gold hoặc planned tasks thành execution. Source: [PLAN_AI](../PLAN_AI.md), [PLAN_HUMAN](../PLAN_HUMAN.md).

## 6. Decision Log

DEC IDs là **ID của log mới**, không đổi experiment IDs cũ. Ngày theo documented stage, giờ unknown; lý do ngoài nguồn giữ unknown. Evidence paths đầy đủ và context trước/sau ở phase tương ứng.

| ID/mốc | Before → Decision | Reason được lưu | Impact/affected phases | Evidence/trust |
|---|---|---|---|---|
| DEC-001 / 2026-10-08 | Prefix/multi-group feasibility lịch sử → laptop-only full metadata-first | Prefix join thiếu coverage; giữ laptop/mục tiêu30K nếu hợp lệ | P1, probes khác domain archive | P1pipeline/cleanup inventory; DOCUMENTED/VERIFIED |
| DEC-002 / P0–P2 | Ratings → fixed3proxy labels | Rating làm proxy, chưa có human gold | Overall labels; giữ noise limits | P2manifest/config; VERIFIED; ngày quyết định ban đầu unknown |
| DEC-003 / 2026-10-09 | QA/coverage chưa đóng → C1-A/C2-A/C3-A; Amazon-onlyP2 C4-B | Chấp nhận selected pool/assisted QA/sampling có giới hạn | P1/P2; không nới P10independence | Owner approval JSON; VERIFIED record, không chat gốc |
| DEC-004 / 2026-10-09 | SemEval source/license BLOCKED → educational exception | Dùng existing train/test, waived source verification | P1/P8/P9; license vẫn NOT_VERIFIED | SemEval owner exception JSON; VERIFIED |
| DEC-005 / P2/P5/P6/P9 | Minority neutral → compare unweighted/balanced | Mất cân bằng quan sát; weighting không luôn thắng | Train-only weights, selection macroF1validation | Label table/selection locks; VERIFIED, không causal claim |
| DEC-006 / 2026-10-24 | TF-IDF/body-only → frozen384 XGB/TabM/V3/V3_5 + BERTtitle+body | Hợp đồng ghi yêu cầu người dùng; MiniLM phù hợp cost sample | P0–P7; LEGACY53outputs giữ, không resplit | Refactor contract/preservation; DOCUMENTED/VERIFIED; động cơ ngoài hợp đồng unknown |
| DEC-007 / 2026-10-24 | Local TabPFN LIMITED → cloud full21K riêng | Local RAM/VRAM limits; full train cùng384features | P5-C01–C06/P7, giữ local; cloud không weights | Cloud plan/import verification; VERIFIED outcome |
| DEC-008 / 2026-10-24–25 | Proxy-only errors → human diagnosis300SRS+60enriched | Phân biệt proxy disagreement/human errors | P7, giữ P10độc lập | Diagnosis guide/human result; DOCUMENTED/VERIFIED |
| DEC-009 / 2026-10-26 | Gold spans → BIO all WordPieces/exact entities | Bảo toàn offsets/partitions; metric cấp span | P8/P9, công bố duplicate/whitespace adjustment | P8manifest/acceptance; VERIFIED |
| DEC-010 / 2026-10-26 | Sentence+term → occurrence markers/exclude conflict sidecar | Term có thể lặp; labels3class không hỗ trợ conflict | P9standalone/joint, không map neutral | P9config/manifest/report; VERIFIED/DOCUMENTED |
| DEC-011 / 2026-10-26 | BERTASC → DeBERTa unweightedseed42epoch5 | Validation macroF1+0,063322, F1ba lớp tăng; stability riêng | P9selector/inference, giữ previous BERT | Decision/lock; VERIFIED, giờ promotion unknown |
| DEC-012 / 2026-10-26 | Invalid tokenization/failed resume → freshV2/seed43restart | Thiếu CLS/SEP/vocab mismatch | P9-EXP01, không dùng invalid scores/mở test seeds phụ | Invalid JSON/FP16log/resume_event; VERIFIED artifact |
| DEC-013 / 2026-10-26 / P3-REFINE-01 | P3 tổng hợp15bảng/7hình → canonical trình bày8bảng core/3hình,9appendix items | Ưu tiên insight/decision thay vì số lượng; chọn namespace mới thay cho ghi đè báo cáo P3 đã hash ở downstream | Chỉ analysis/report/ref links; P0–P2/P4–P9 và toàn bộ P3 gốc giữ nguyên | `reports/p3_refinement_20261026/audit.md`, `acceptance.json` cùng namespace; VERIFIED; không đổi model hoặc benchmark |

## 7. Experiment Registry

Mặc định metric là **macro F1 validation/test**, làm tròn6chữ số; ATE dùng **entity F1**, joint dùng **exact span+polarity micro F1**. Không so trực tiếp khác task/dataset/mẫu số. `namespace:mode` chỉ định vị candidate, không đặt experiment ID mới. REJECTED nghĩa không chọn bằng validation, không phải technical failure; không có test thì NOT_RUN.

| Experiment | Dataset/config/model | Val / test | Status/selected/reason | Evidence namespace |
|---|---|---|---|---|
| P5-E00 LEGACY | Amazon21K/4500/4500,`configs/p5.yaml`,majority | 0,259390 / 0,259445 | COMPLETE,sanity | `reports/p5/p5_20261015/` |
| P5-E01 LEGACY | Cùng split,TF-IDF+LR C0,5balanced | 0,693554 / 0,683887 | SELECTED best classical validation, nay LEGACY | Cùng P5namespace |
| P5-E02 LEGACY | TF-IDF+SVM C0,5balanced | 0,687509 / 0,678138 | COMPLETE, val thấp LR | Cùng P5namespace |
| P5-E03 LEGACY | TF-IDF+DT depth25/leaf5/unweighted | 0,527902 / 0,530962 | COMPLETE, không winner | Cùng P5namespace |
| p6_20261015:unweighted | Body-only BERT,`configs/p6.yaml`,epoch3 | 0,724805 / NOT_RUN | REJECTED, balanced val cao hơn | `reports/p6/p6_20261015/` |
| p6_20261015:balanced | Cùng data/config,epoch3 | 0,734646 / 0,730204 | Previous sentiment canonical, nay LEGACY | Cùng P6namespace |
| E00_majority | Full Amazon split,majority | 0,259390 / 0,259445 | COMPLETE,sanity | `reports/semantic_20261024/E00_majority/` |
| E01_xgboost_embedding | Full split/384,`configs/modern_tabular.yaml` | 0,664566 / 0,667752 | COMPLETE,weighted selected validation | `reports/semantic_20261024/E01_xgboost_embedding/` |
| E02_tabm_embedding | Cùng split/384/config | 0,680132 / 0,689086 | COMPLETE,weighted,best frozen validation | `reports/semantic_20261024/E02_tabm_embedding/` |
| E03_tabpfn_v3_embedding root | SDK V3/384 | NOT_AVAILABLE / NOT_RUN | Historical BLOCKED license, theo latest_attempt | Root result/latest_attempt |
| E03…/attempts/resource01 | 10Ktrain/4500/4500,resource config | 0,574185 / 0,562544 | COMPLETE LIMITED | `reports/semantic_20261024/E03_tabpfn_v3_embedding/attempts/resource01/` |
| E04_tabpfn_v35_embedding local | 1500train/4500/4500,V3_5/384 | 0,572939 / 0,570952 | COMPLETE LIMITED | `reports/semantic_20261024/E04_tabpfn_v35_embedding/` |
| C-E03 cloud | Full21K/4500/4500,V3,cloud config | 0,580694 / 0,572971 | SUCCESS,current row,không weights | `artifacts/cloud_runs/tabpfn_full21k_20261024/tabpfn_v3_full21k/` |
| C-E04 cloud | Cùng full split,V3_5,config riêng | 0,614332 / 0,614017 | SUCCESS,current row,không weights | `artifacts/cloud_runs/tabpfn_full21k_20261024/tabpfn_v35_full21k/` |
| E05_transformer:unweighted | Full split/title+body,`configs/transformer_benchmark.yaml`,epoch3 | 0,760338 / 0,755382 | SELECTED sentiment canonical validation | `reports/semantic_20261024/E05_transformer/` |
| E05_transformer:balanced | Cùng split/config | 0,758344 / NOT_RUN | REJECTED validation | E05lock/history |
| p8_20261026 ATE | SemEval2587/458/800,`configs/p8_aspect_extraction.yaml`,BERTepoch4 | entity0,799401 / 0,804478 | SELECTED ATE canonical | `reports/p8_20261026/` |
| p9_20261026:unweighted | SemEval1999/314/638,`configs/p9_aspect_sentiment.yaml`,BERTepoch4 | 0,714145 / 0,748118 | SELECTED tại P9,nay previous ASC | `reports/p9_20261026/` |
| p9_20261026:balanced | Cùng examples/config,epoch4 | 0,712292 / NOT_RUN | REJECTED validation | P9lock |
| P9joint BERT | Frozen P8spans,458/800sentences | joint0,589666 / 0,634557 | COMPLETE evaluation,không selection | P9end_to_end_results.json |
| P9-EXP01 invalid | Same P9examples,DeBERTa attempts | INVALID / NOT_RUN | INVALID_FOR_COMPARISON | `reports/p9_exp01_deberta_20261026/` |
| P9-EXP01 V2:unweighted | Same examples,`configs/p9_exp01_deberta.yaml`,seed42epoch5 | 0,777467 / 0,780433 | PROMOTED qua validation | `reports/p9_exp01_deberta_20261026_v2/` |
| P9-EXP01 V2:balanced | Same examples/config,epoch4 | 0,765511 / NOT_RUN | REJECTED validation | V2lock |
| P9-EXP01 V2seed43 | Same examples,seed43config | PARTIAL / NOT_RUN | INTERRUPTED/failed resume,không completed stability | `reports/p9_exp01_deberta_20261026_v2_seed43/` |
| P9-EXP01 seed43_restart01 | Same examples,seed43fresh config,epoch4 | 0,767943 / NOT_RUN | VALIDATION_ONLY_COMPLETE,không canonical | `reports/p9_exp01_deberta_20261026_v2_seed43_restart01/` |
| P9-EXP01 seed44 | Same examples,seed44config,epoch3 | 0,754664 / NOT_RUN | VALIDATION_ONLY_COMPLETE,không canonical | `reports/p9_exp01_deberta_20261026_v2_seed44/` |
| P9-EXP01 joint DeBERTa | Frozen P8spans,458/800sentences,locked42 | Xem joint JSON / 0,660550 | COMPLETE evaluation,không selection | V2end_to_end_results.json |

Mỗi namespace giữ `config.json` hoặc `training_identity.json`, candidate/history, lock/result/metrics. Xem đó để lấy full hyperparameters/epochs/weights/config hash, không suy từ config hiện tại. Companion trích exact metrics/config references từ saved artifacts; predictions có text chỉ giữ local, không chép review vào log.

## 8. Canonical Model History

| Date/stage | Task | Canonical model được bằng chứng chọn | Replaced/retained | Reason/evidence |
|---|---|---|---|---|
| 2026-10-15 P5 | Overall best classical | TF-IDF+LR balancedC0,5 | Majority sanity,SVM/DT non-winner | Validation winner,P5manifest; chưa evidence deployment |
| 2026-10-15 P6 | Overall sentiment | BERT body-only balancedepoch3 | LR baseline giữ | Val0,734646,P6manifest/lock |
| 2026-10-24 P6/P7refactor | Overall sentiment | BERT title+body unweightedepoch3 | Body-only/TF-IDF LEGACY giữ nguyên | Val0,760338,E05result/lock,contract mới |
| 2026-10-26 P8 | ATE | BERT token classifier epoch4 | Chưa có selected ATE trước được lưu | EntityF1val0,799401,P8lock |
| 2026-10-26 P9 | ASC | BERT unweightedepoch4 | First selected ASC trong repo evidence | Valmacro0,714145,P9lock |
| 2026-10-26 P9-EXP01 | ASC | DeBERTa-v3-base unweightedseed42epoch5 | BERT previous canonical giữ data/model/source | Valmacro0,777467,decision/selector |

Cloud chỉ thay TabPFN benchmark rows, **không thay sentiment canonical**. P9-EXP01 chỉ thay ASC, không thay ATE/overall sentiment. Không evidence app deployment trước P11.

## 9. Test History — lịch sử, không chạy lại trong audit

Mỗi số là scope suite tại mốc; không cộng tất cả milestone. VERIFIED artifact là đọc JSON/console, không rerun execution cũ. Nếu thiếu date metadata thì dùng stage.

| Mốc | Kết quả lưu | Evidence | Trust |
|---|---|---|---|
| P0 2026-10-08 | 9passed,pip check | `reports/p0_initialization.md` | DOCUMENTED |
| P1early→hardening | 33→60→84passed | `reports/p1_data_acquisition.md`,`reports/p1_pipeline_changes.md` | DOCUMENTED |
| P1remaining gates/QA | 139passed | `reports/tables/p1_recall_brand_validation.json` | VERIFIED artifact |
| P2final2026-10-09 | 161passed,targeted18 | `reports/p2_amazon_completion_20261009.md` | DOCUMENTED |
| P3 2026-10-09 | 169suite,8fixtures,notebook PASS | `reports/p3/20261009_verified/task_validation.json` | VERIFIED artifact |
| P4 2026-10-09 | 180passed | `reports/p4_completion_20261009.md` | DOCUMENTED |
| P5 2026-10-15 | 195passed,targeted15 | `reports/p5/p5_20261015_qa.json` | VERIFIED artifact |
| P6LEGACY2026-10-15 | 195+12=207passed,two process groups | `reports/p6/p6_20261015_qa.json` | VERIFIED artifact |
| Refactor initial2026-10-24 | 240passed,license BLOCKED snapshot | `reports/model_stack_validation.json` | VERIFIED artifact,không current |
| Refactor local/cleanup2026-10-24 | 249passed | `reports/model_stack_final_validation.json` | VERIFIED artifact |
| Cloud preparation2026-10-24 | 276passed | `reports/kaggle_tabpfn_full21k_preparation.json` | VERIFIED artifact |
| Cloud import2026-10-24 | 291passed | `reports/tabpfn_kaggle_full21k_verification.json` | VERIFIED artifact |
| P7diagnosis tooling | 306passed | `reports/history/p7_before_human_20261025/p7_error_diagnosis_validation.json` | VERIFIED artifact;tree62cec2c…cũng lưu306 |
| P7human2026-10-25 | 321passed | `reports/p7_error_diagnosis_validation.json` | VERIFIED artifact |
| P8 2026-10-26 | 350passed,0FAIL | `reports/p8_20261026/validation.json` | VERIFIED artifact |
| P9BERT2026-10-26 | 378passed,0FAIL | `reports/p9_20261026/validation.json` | VERIFIED artifact |
| P9-EXP01 2026-10-26 | 380passed,0FAIL | `reports/p9_exp01_deberta_20261026_v2/validation.json`,`test_console.log` | VERIFIED artifact |
| P3-REFINE-01 2026-10-26 | 386passed,0FAIL;380cũ+6mới;nhóm353/25/8 | `reports/p3_refinement_20261026/validation.json`,`test_console.log` | VERIFIED thực chạy; no regression, không ghi lại evidence P9 cũ |

Chỉ thêm test count có nguồn; không lấy ví dụ trong prompt làm lịch sử. SDK warnings/fixture failures rồi sửa không tự thành scientific run failure. Audit tài liệu kiểm provenance/links/metrics/preservation, không chạy full suite/finalizer ghi lại frozen reports.

## 10. Known Issues / Resolved Issues và failed attempts

ISSUE IDs là ID mới của log. Candidate không thắng validation không phải technical failure.

| ID | Problem/detected/impact | Resolution/status | Evidence |
|---|---|---|---|
| ISSUE-001 | Prefix join ít,17laptop không suy full yield | Metadata-first full scan; RESOLVED coverage hai file, chưa certify recall | P1pipeline/full survey |
| ISSUE-002 | Assisted QA/recall uncertainty,SemEval source chưa verified | ACCEPTED LIMITATION theo owner exception,không license PASS | Owner approval/exception,P1acceptance |
| ISSUE-003 | P2detector variation/encoded HTML residual | Round scores/sửa boundaries,final saved-pool rerun; RESOLVED | P2completion/final manifest/STATUS |
| ISSUE-004 | P4initial tokenizer vượt512MBguard | Tối ưu bộ nhớ,final namespace; RESOLVED | Initial STATUS/final manifest |
| ISSUE-005 | TabPFN initial license BLOCKED/local resource limits | Retry/cloud SUCCESS; local LIMITED/RSS warning giữ lịch sử | E03pointer/resource JSONs/cloud verification |
| ISSUE-006 | Neutral minority/proxy noise,human attribution thiếu lúc đầu | Diagnosis360completed; causal fraction NOT_MEASURED,P10PENDING | P7human result/acceptance |
| ISSUE-007 | P8cap128/API overlength,whitespace/official duplicate | Data hiện0truncation,một adjustment/duplicate công bố; ACCEPTED LIMITATION | P8manifest/acceptance |
| ISSUE-008 | P9conflict ngoài3labels/term lặp | Exclude sidecar/offset markers; RESOLVED protocol | P9manifest/config/report |
| ISSUE-009 | DeBERTa FP16/GradScaler,thiếuCLS/SEP | FP32 parameters/postprocessor V2fresh run; RESOLVED choV2,old INVALID | `reports/p9_exp01_deberta_20261026/attempt01_fp16_failure.log`,`invalid_attempt.json` |
| ISSUE-010 | Seed43interruption/resume vocab mismatch | Fresh restart COMPLETE; **OPEN: resume NOT_SUPPORTED**,total attempts cost NOT_MEASURED | V2resume_event/log/stability |
| ISSUE-011 | Latency contention/batch khác | Controlled validation314IDs/batch16 riêng; RESOLVED comparison,giữ initial timings | V2latency JSONs/logs |
| ISSUE-012 | SemEval→Amazon shift/P10gold chưa đo | OPEN/PENDINGP10,không suy production/tiếng Việt/khác thiết bị | PLAN/acceptance artifacts |
| ISSUE-013 | GITHUB-PUBLISH-01: HTTPS push bị GitHub từ chối `Invalid username or token`; gh CLI chưa cài, GCM không liệt kê account | OPEN; đăng nhập lại bằng `git credential-manager github login`, rồi push main/đối chiếu hash. Không gửi token trong chat | `reports/github_publication_20261026/publication.json`; commit snapshot local |

## 11. Discrepancies và chronology gaps

1. `AGENTS.md` và refactor contract còn cloud PENDING; cloud verification/currentP7CSV xác nhận SUCCESS. **Status drift** không hủy scientific/resource safeguards. Cloud plan câu P8–P13PENDING là snapshot trước P8/P9; nay có acceptance riêng2026-10-26. Không sửa hợp đồng/report cũ trong tác vụ này.
2. P1acceptance giữ proposal UNAPPROVED,C4-B/P1incomplete và educational exception/P1DONE trong cùng file. Hai approval JSON liên kết thể hiện chuyển trạng thái, không coi mọi đoạn hiện hành cùng lúc. P2report SemEval BLOCKED là trạng thái khi Amazon-onlyP2.
3. E03root BLOCKED→latest attempt PASS→cloud SUCCESS là các mốc khác nhau. Local10K/1500 và cloud21K giữ regime/source riêng, không metric corruption.
4. 249/291/321/350/378/380tests là snapshots tăng phạm vi. EXP01validation previous_tests350/new_tests30 đếm từP8; so P9BERT378 thì tăng2. Không sửa JSON cũ hoặc gọi350 là suite ngay trướcEXP01.
5. DeBERTa7,912ms test và1,806ms controlled validation khác batch/dataset/load; giữ cả điều kiện, không bỏ số cũ.
6. Report dẫn `attempts.json` nhưng file không tồn tại tại namespace được nhắc. Chỉ xác nhận failures qua FP16log/invalid_attempt/resume_event/report; không bịa nội dung hoặc sửa report cũ.
7. Không biết date/time/command/exit code mọi thao tác. Lệnh hướng dẫn không chứng minh actual execution; runtime không thay wall-clock start/end. Thiếu commit lineage/PLAN mọi version;5Codex trees chỉ vài mốc2026-10-24/26,không dùng ref epoch-like values/mtime làm execution time.
8. Giờ thay canonical/rejected alternatives/original chat motivations chưa lưu đầy đủ. Protocol records ghi validation selection trước test nhưng không independent timestamp attestation. Source hash kiểm identity không chứng minh mọi implementation cũ còn đủ bytes.

## 12. Recommended Logging Architecture và cập nhật tiếp

**Canonical:** `docs/PROJECT_EXECUTION_LOG.md`, các section registry/decision/canonical/test/issues tại đây, không tạo log cạnh tranh. **Companion:** `reports/project_execution_log.json` lưu inventory/hash nguồn,Git objects,exact metric extracts,link/preservation validation; không thay scientific result artifacts.

Đã kiểm writers `scripts/train_p8.py`, `train_p9.py`, `train_transformer.py`: có automatic **per-run** history/progress/identity/config/locks/predictions/metrics,finalizers có acceptance/preservation. **Chưa tìm thấy automatic append project history xuyên pha** trong source đã kiểm. Cách nhẹ nhất: Codex cập nhật log cùng handoff sau phase/experiment,dùng writer sẵn có; không framework/githook/background service mới. Tác vụ này đề xuất convention, chưa sửa generators/AGENTS để kích hoạt automation.

Append mốc vào phase đang làm hoặc thêm phase section; correction có ngày/source,giữ historical results:

```text
Ngày/giờ+timezone hoặc date/time unknown;phase/task/experiment ID hiện có
Objective;input version/hash;split IDs/counts;command thực chạy
Config snapshot;model/tokenizer revisions;seed;resource budget
Attempt ID;COMPLETE/FAILED/INTERRUPTED/LIMITED;resume/restart từ đâu
Validation selection+lock;test policy/results hoặc NOT_RUN
Metric/prediction/checkpoint/acceptance/preservation paths+hashes
Test command/exit code/result/scope;DEC/ISSUE mới nếu có
Limitations;evidence class/confidence;commit hash hoặc NO_COMMIT
```

Sau mốc, append registry/decision/canonical/test rows liên quan,lưu config/metrics/acceptance bằng runner hiện có. Ghi commit khi có,không tự commit để bù history; không rewrite scientific artifact cũ. Handoff giữ current status/linklog;PROJECT_INDEX dẫn log. Resource/authorization gates không đổi.

## 13. Log Reconstruction Result

- **Phases:** P0–P9/P9-EXP01,LEGACY/semantic/local/cloud/diagnosis;P10–P13PENDING,không dựng execution.
- **Experiments:** registry mục7 có selected/rejected/local/cloud/invalid/interrupted/stability/joint;resource attempts chi tiết dẫn về thư mục bằng chứng.
- **Decisions:**12DEC có nguồn;không tạo lý do thiếu bằng chứng.
- **Conversation-derived entries:**0. **Repository-verified entries:** JSON/config/lock/metric/Git tree records có provenance;doc-only narrative giữ DOCUMENTED,không đếm mọi câu là measurement đã verify.
- **Gaps:** mục11,nhất là giờ/lệnh mọi task,PLAN mọi version,original chat motivation,intra-day ordering,total failed-attempt cost.
- **Scientific Artifacts Changed: NO.** Chỉ log/companion/index/handoff;không sửa dataset/split/checkpoint/metric/prediction/acceptance/report cũ. Companion phân biệt content checks với metadata-only checks cho file lớn,không claim full raw/model rehash.
- **Final Assessment: PARTIAL.** Đủ hiểu mốc chính/làm căn cứ methodology,experimental setup,result analysis khi đối chiếu evidence;chưa đủ execution chronology đầy đủ theo giờ/lệnh.

**Kiểm tra thực hiện trong audit này — PASS:** lệnh PowerShell UTF-8 here-string qua `.venv/Scripts/python.exe -X utf8 -`; 73liên kết trong log tồn tại, sections1–13 và handoffA–H hợp lệ, 27dòng registry/12DEC/12ISSUE. Tính lại18bộ metric từ saved predictions: validation/test của6model benchmark hiện hành,2ASC BERT/DeBERTa và ATE; khớp metric JSON với tolerance1e-12, benchmark CSV cũng khớp. Dataset Amazon và3split hash khớp manifest;9evidence hashes của acceptance P9-EXP01 khớp. Bảo toàn1.262file cũ bằng SHA256;43file lớn bằng size/mtime, không full rehash nội dung. Hai tài liệu cũ được phép sửa là index/handoff; log/companion là file mới. Không chạy full test suite, training, inference, download hoặc finalizer. Số380tests vẫn là bằng chứng lịch sử, không phải kết quả chạy mới của audit này.

Giới hạn: **các phát hiện chỉ dành cho laptop**;**nhãn đại diện suy từ số sao có nhiễu nhãn**;**SemEval-to-Amazon platform/style shift trong laptop review chưa đánh giá độc lập**;**bộ gold do người chú thích nhỏ P10 vẫn PENDING**. Không khẳng định tiếng Việt,khái quát đa thiết bị hoặc production readiness.

## 14. 2026-10-26 — P3-REFINE-01: P3 EDA refinement

**Status:** DONE sau build/validation/preservation; ngày Asia/Saigon, giờ thực thi không ghi. Task documentation/analysis refinement, không experiment/model promotion. Quy tắc mandatory logging đã cài ở AGENTS mục11 được áp dụng cho task này.

**Objective:** giữ EDA có project impact, giảm biểu đồ/bảng trùng; phân biệt original P3 observations và later confirmation P7/P8/P9. **Inputs:** 15CSV/7figure pairs/summary đã khóa ở `reports/p3/20261009_verified/`, báo cáo/notebook P3 cũ, readiness JSON và P7 human diagnosis; dataset chỉ kiểm hash, không biến đổi review.

**Actions/Configuration:** audit từng artifact thành KEEP/APPENDIX/REMOVE FROM REPORT; giữ toàn bộ file gốc. Config `configs/p3_refinement.yaml`; logic tái sử dụng `src/data/eda_refinement.py`, CLI `scripts/refine_p3.py`. Top5bigrams/lớp theo prevalence difference, support trong lớp≥30, ties count giảm/term tăng; failure regex công khai chọn bigram/trigram theo cùng ranking. Tính rates từ số đếm và mẫu số trong/ngoài lớp, không chọn feature/hyperparameter. Gộp brand/product concentration, thêm failure slice/traceability; helpfulness xuống appendix. Không đưa context review text vào HTML mới.

**Results/Artifacts:** canonical presentation mới [Markdown](../reports/p3_refinement_20261026/report.md), [HTML tự chứa](../reports/p3_refinement_20261026/report.html), [audit](../reports/p3_refinement_20261026/audit.md), `tables/`, `figures/`, `summary.json` cùng namespace. Trước: generated15tables/7figures; MD3tables/0figures/9sections. Sau:8core tables/3figures/9appendix items,13core sections. Negative/neutral/positive median body words50/56/37, IQR76/93/72; negative failure phrase selection và positive aspect-like mentions có support/rates, không causal/aspect-polarity claims. Neutral mixed-language/factual/weak/mixed-sentiment mechanisms NOT_MEASURED. P7disagreement dùng cross-reference hồi cứu, không đưa thành tri thức P3 ban đầu.

**Decision/Reason:** DEC-013 — ACCEPT bản trình bày tinh gọn; KEEP CURRENT scientific protocol. Alternatives: giữ toàn bộ15bảng/7hình trong main report hoặc sửa trực tiếp report cũ; chọn8/3 ở namespace mới vì phù hợp insight density và bảo toàn downstream hashes. Canonical model history/experiment registry không đổi; đây không phải run sentiment/ABSA mới. Issue Registry NO CHANGE; giới hạn đã biết được giữ, không tạo issue khoa học từ chỉnh bố cục hình.

**Validation — VERIFIED:** `.venv/Scripts/python.exe -X utf8 -m scripts.refine_p3` build PASS; targeted6tests PASS, full `.venv/Scripts/python.exe -X utf8 -B -m scripts.test_all` **386PASS/0FAIL** (353+25+8), tăng6 từ380; Swig/SDK deprecation warnings có lưu. `pip check`/`compileall` PASS. Dựng độc lập từ bản copy input trong thư mục tạm:19outputs CSV/MD/HTML/PNG/SVG/summary byte-identical. Kiểm ba PNG, sửa shared legend tránh che points; report links/source/output hashes PASS. Before/after **full SHA256 1.302file cũ (~37,04GB), gồm raw/model weights, không mismatch**;7tài liệu điều hướng/log/plan/handoff được phép thay đổi. Không gọi metadata-only check là full checksum. Nguồn evidence: `reports/p3_refinement_20261026/{validation,preservation,acceptance}.json`, `test_console.log`.

**Impact on Existing Project:** dataset unchanged; split unchanged; model unchanged; canonical scientific metrics unchanged; historical P3 and P0–P2/P4–P9 artifacts preserved. **No canonical scientific artifacts changed.** Chỉ canonical presentation và README/PLAN/PROJECT_INDEX references cập nhật; các config/manifests downstream vẫn trỏ bằng chứng lịch sử. Bản nháp chart QA được giữ ngoài repository ở thư mục tạm; không scientific failed attempt hoặc canonical report thứ hai.

**Known Limitations/Next:** chỉ laptop/noisy star proxy, mention không phải aspect sentiment, chưa causal attribution; SemEval–Amazon shift và independent human gold nhỏ P10 vẫn PENDING. Dừng sau refinement; dùng bản mới để viết EDA/methodology, không tự mở P10. Không retrain hoặc infer ABSA trên Amazon30K.

## 15. 2026-10-26 — GITHUB-PUBLISH-01: snapshot công khai qua P9

**Status: BLOCKED — chuẩn bị/commit hoàn tất, push thất bại do authentication.** Ngày Asia/Saigon; tác vụ vận hành theo yêu cầu chủ sở hữu, không mở P10/P13 hoặc nghiệm thu toàn dự án.

**Objective/Inputs:** xuất bản source/config/tests/docs, báo cáo và metrics tổng hợp vào repository do người dùng cung cấp: `https://github.com/NguyenHoangAnh06/laptop-sentiment-classification-absa.git`. Đầu vào là project local hiện hành qua P9/P3-REFINE-01; dataset/split/version/model giữ nguyên. Git ban đầu đã init, nhánh master chưa có HEAD, index rỗng, không remote; `git ls-remote --symref <URL> HEAD` thành công và không có HEAD. Giữ nguyên các refs Codex kiểu tree, không push chúng.

**Inspect/Execute:** inventory toàn workspace ngoài `.git/`, phân loại TRACK/IGNORE/REVIEW/LARGE FILE/SECRET RISK; kiểm nội dung first-party reports, JSON/CSV/notebook và đường dẫn máy cũ. Cập nhật `.gitignore` để loại binary ở mọi thư mục, corpus/trích đoạn review trong báo cáo QA/EDA, notebook có output, HTML P3 cũ, credentials/cache/ZIP và Word plan lịch sử. Không xóa/move scientific artifacts. Tạo `scripts/audit_public_snapshot.py`, fixture tests và `docs/GITHUB_REPRODUCTION.md`; thêm link README. Remote origin theo URL được cung cấp; nhánh xuất bản main. Không dùng LFS, không tải dữ liệu/train/evaluate lại.

**Results/Artifacts:** audit trước sửa phát hiện 46 candidate cần review (binary predictions/corpus/encoding); 3 cảnh báo tên credential nằm trong package venv (CA certificates/test key), không phải secret dự án và đều bị loại. Audit sau ignore: 844 candidates/40.050.662 bytes tại mốc quét, 50.523 ignored/45.428.263.511 bytes (bao gồm môi trường và inventory local); chưa tính các tệp log/audit bổ sung sau mốc này. 85files >10MB đều ignored (84 ban đầu và inventory local mới), từng đường dẫn/kích thước/ngưỡng có tại `reports/github_publication_20261026/large_files.csv`. Full inventories chỉ local ở `reports/github_publication_local/`; summary/publication/preservation trong `reports/github_publication_20261026/`. Số cuối cùng lấy từ index/commit, không đồng nhất số audit trung gian với snapshot cuối.

**Validation — VERIFIED:** `.venv/Scripts/python.exe -X utf8 -B -m pytest -q tests/test_public_snapshot.py`: **6 passed**, 0 fail; fixture tổng hợp kiểm token redaction, env access, corpus-vs-counts, notebook outputs, ignore/binary blockers và UTF-16 secret. `compileall` cho hai tệp mới PASS. Full scientific suite **NOT_RERUN**; 386PASS trước đó vẫn là evidence P3-REFINE-01. Audit sau ignore: 0 candidate blockers, secret scan PASS trong phạm vi UTF-8/UTF-16-BOM text ≤10MB; data/, inventory local, venv/cache/model/dataset binary chỉ kiểm kê metadata. Đây là heuristic scan, không phải chứng nhận không thể có secret. Corpus Amazon/SemEval/trích đoạn đã phát hiện EXCLUDED vì quyền redistribution chưa rõ; không thay đổi trạng thái license SemEval. Các absolute path bằng chứng lịch sử giữ nguyên, README/setup dùng relative paths. Kiểm full SHA256 trước/sau có báo cáo riêng; không suy preservation từ Git ignore.

**DEC-014:** chọn snapshot công khai có chọn lọc + hướng dẫn tự lấy/tái tạo artifacts. Alternatives: push mọi file; dùng LFS cho corpus/weights; chỉ source không báo cáo. Lý do: bảo vệ dữ liệu/quyền sử dụng và giữ bằng chứng methodology/metrics, không phá preservation. Canonical models/experiment registry **NO CHANGE**; Issue Registry **UPDATED: ISSUE-013 OPEN** cho authentication. Không thêm giấy phép phân phối khi chưa có quyết định của chủ sở hữu.

**Impact:** dataset/split/model/canonical metrics/historical scientific artifacts unchanged. **No canonical scientific artifacts changed.** Chỉ thay chính sách Git, hướng dẫn, công cụ audit, tests và log/handoff. Local corpus/checkpoints vẫn tồn tại; clone công khai không có đủ đầu vào để kiểm toàn bộ acceptance/inference. Setup máy sạch và tái huấn luyện NOT_MEASURED. Giới hạn: chỉ laptop, star-proxy có nhiễu, SemEval-to-Amazon platform/style shift chưa đánh giá độc lập, bộ human-gold nhỏ P10 vẫn PENDING.

**Commit/Validate/Push — VERIFIED:** first public snapshot `02d75846d191615aa764d990c19ef40cd15fbd52`, message `Initial public project snapshot through P9`: **849files/40.307.269bytes**; từng index blob khớp byte worktree, secret/corpus/binary checks PASS; max blob5.708.731bytes. Reachable history chỉ1commit ở mốc snapshot, không chứa Codex trees. Máy bật `core.autocrlf=true`; thêm `.gitattributes` `* -text` giữ bytes/hash. Full preservation: **1326files/37.037.489.019bytes,0mismatch**, dataset/weights/raw gồm trong kiểm SHA256. `git diff --cached --check` và kiểm lại với `core.whitespace=cr-at-eol` báo whitespace lịch sử (lần sau37.079diagnostic lines); giữ nguyên formatting của scientific/source snapshots thay vì sửa checksum hàng loạt. Đây không phải test logic thất bại; targeted6tests vẫn PASS. Không tuyên bố whitespace-clean hoặc full-suite rerun.

`git push -u origin main` **FAILED**, GitHub trả `Invalid username or token. Password authentication is not supported for Git operations.` Không có branch remote để đối chiếu commit; `git ls-remote --heads origin` trả rỗng. Credential helper manager2.6.1 đã có nhưng `git credential-manager github list` rỗng; gh CLI NOT_INSTALLED. Không lấy/in secret, không xóa credentials hoặc tự cài công cụ. Commit ghi kết quả/log tiếp theo chỉ local; không gọi là push thành công.

**BLOCKED: GitHub HTTPS authentication không hợp lệ/chưa có account GCM. NEXT_ACTION:** người dùng đăng nhập trên máy bằng `git credential-manager github login` (không paste token vào chat), sau đó `git push -u origin main`; xác minh `git rev-parse HEAD` khớp `git ls-remote origin refs/heads/main`. Cập nhật ISSUE-013 thành RESOLVED và log/handoff sau khi quan sát push thành công. Không push Codex refs hoặc pha P10.
