# Chuẩn bị TabPFN full21K trên Kaggle — 2026-10-24

## A. Status

**READY FOR KAGGLE**. Bundle độc lập đã xuất/verify local và ZIP giải nén ngoài repository đã verify PASS. Chưa upload/deploy/chạy cloud hoặc TabPFN full21K local. Trạng thái này chỉ nghiệm thu chuẩn bị, không đảm bảo Kaggle đủ tài nguyên.

## B. Data

| Split | Shape | Dtype |
|---|---|---|
| train | (21000, 384) | float32 |
| validation | (4500, 384) | float32 |
| test | (4500, 384) | float32 |

Nguồn thật: `data/processed/features/semantic_20261024/{split}_embeddings.npy`, `{split}_labels.npy`, `{split}_mapping.parquet`; split `data/processed/splits/p4_20261009_final/{split}.parquet`. Embeddings/labels copy nguyên byte; IDs Unicode NPY giữ nguyên thứ tự mapping. Không shuffle/recompute/resplit. Encoder MiniLM revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41,mask-mean/L2/max256; negative0/neutral1/positive2.

## C. Bundle

`cloud/kaggle_tabpfn_full21k/`,27files,khoảng56,45MB. ZIP `cloud/kaggle_tabpfn_full21k.zip`,khoảng42,96MB. **Số byte và ZIP SHA256 cuối chính xác ở `reports/kaggle_tabpfn_full21k_preparation.json`.** Không weights/raw/text/cache hoặc duplicated embeddings.

Các file lớn nhất: train embeddings32256128bytes,train IDs7056128bytes,test embeddings6912128bytes,validation embeddings6912128bytes,test IDs1512128bytes. IDs giữ chuỗi đầy đủ không pickle; không phải embeddings trùng lặp.

## D. Integrity

PASS shape/dtype/finite/nonzero/labels/ID uniqueness/no overlap/SHA256/manifest anchor/secret scan. Export đối chiếu mapping.review_id/row_index và labels trực tiếp với split gốc trước copy. Kaggle kiểm hash payload đã neo để bảo toàn alignment; không suy diễn semantic alignment chỉ từ matrix. Giữ anchor local: hash không chống việc thay cả payload và anchor.

Split SHA256:

- Train: `3b3a1a92d6019659510c6282a92e1ce47b15f24e4857770d3b65deff964fe41b`.
- Validation: `80e706247adb3daca99580d31ba618bb10b784fa4af9aa5fd15123320d6ce7a0`.
- Test: `f2a621178b8d7e76c385d3e336f66fdb8041a2c2c9ee07e89ca281cc82a1e097`.

Source embedding/mapping và mọi payload hashes nằm trong `metadata/bundle_manifest.json`; hash index và expected manifest tách riêng tránh tự tham chiếu. Bảo toàn155scientific files và53legacy files(27+26): PASS,0mismatch; xem `reports/kaggle_tabpfn_preservation.json`. P7 CSV/report giữ nguyên. Secret scan toàn văn bản và byte arrays PASS; notebook outputs rỗng. Không đọc token thật khi chuẩn bị.

## E. Models

C-E03 explicit `ModelVersion.V3`; C-E04 explicit `ModelVersion.V3_5`; pin tabpfn9.2.0. SDK local xác minh hai checkpoint khác nhau, không fit:

- `tabpfn-v3-classifier-v3_default.ckpt`.
- `tabpfn-v3.5-20260909.safetensors`.

Resolver kiểm requested/resolved/checkpoint thực tế, từ chối trùng hoặc sai version. Metrics utility copy nguyên byte từ `src/evaluation/classification.py`; balanced accuracy bằng mean recall như runner local. Macro F1 chính, có accuracy/weighted F1/balanced accuracy/per-class precision/recall/F1/neutral F1/confusion matrix.

Một candidate định trước: seed42,n_estimators1,fit_with_cache,memory_saving_mode true,cacheCPU,autocast,batch16. V3 coverage nội bộ vẫn tối đa200/384chiều với n_estimators1; đầu vào384chiều không đổi. Không thay representation hoặc tự fallback subsample. Probe chỉ train, mỗi mức subprocess riêng/timeout3600s; final fit→validation→selection_lock→test. Test được công bố reused test. RSS sampled20ms, GPU peak theo PyTorch; tiền cloud chưa đo. Failure là FULL21K_FAILED.

## F. Kaggle instructions

1. Tạo Dataset **private**, upload ZIP/nội dung bundle giữ cấu trúc.
2. Import `kaggle_notebook.ipynb` để tạo Notebook.
3. Attach Dataset; chỉ attach một bundle hoặc đặt DATA_ROOT.
4. Bật GPU T4x2 nếu có và Internet ON; code dùng một GPU, không cộng VRAM hai T4.
5. Thêm/cấp quyền Kaggle Secret TABPFN_TOKEN, không paste giá trị vào code.
6. Run All; verify fail sẽ dừng, probe fail bỏ final phiên bản đó và tiếp tục phiên bản kia.
7. Tải `tabpfn_cloud_results_*.zip`. Xem README để nhập vào artifacts/cloud_runs, kiểm hash/version/IDs/y_true và tính lại metrics trước tác vụ riêng cập nhật P7.

PENDING: GPU/RAM/quota/access thực, Linux/Kaggle execution và full21K V3/V3_5. Probe16train rows không bảo đảm final4500rows; nếu kernel bị kill có thể mất artifact chưa flush, cần giữ notebook logs. Không tuning resource/config từ test.

## G. Tests

- `.venv/Scripts/python.exe -m scripts.test_all`: **276PASS**,0FAIL(256+12+8), gồm249test hiện có+27test mới. Có10SDKDeprecationWarnings trong nhóm cũ.
- `.venv/Scripts/python.exe -B -m pytest -q tests/test_kaggle_bundle.py`: **27PASS** sau chỉnh sửa cuối.
- `.venv/Scripts/python.exe -B -m pip check`: PASS.
- Bundle syntax và11notebook code cells compile: PASS; CLI help4scripts từ cwd ngoài repo PASS; ZIP giải nén ngoài repo verify real data PASS.
- Test count/dtype/NaN/Inf/zero/labels/IDs/overlap/hash/secret fixtures, explicit versions/no ambiguous default, lock trước test, output schema, package allowlist và probe failure không chạy final: PASS.

Bốn CLI smoke ban đầu fail vì stdout encoding Windows khi pipe tiếng Việt; đã sửa UTF-8 và rerun PASS. Rà soát cuối sửa các chuỗi tài liệu bị mất dấu qua pipe PowerShell. Fixture tổng hợp chỉ kiểm giao thức, không báo như score benchmark. Không cài lại dependency local/tải dataset hoặc checkpoint/chạy full21K để xác minh bundle.

## H. Files created

Bundle27files: README/requirements/notebook,config cloud+expected manifest,9data NPY,3metadata JSON,output/.gitkeep và9scripts(common/metrics/versions/redaction/verify/resource_probe/run/package/notebook_steps). Danh sách từng path trong preparation JSON.

Ngoài bundle: `scripts/prepare_kaggle_tabpfn.py`, `tests/test_kaggle_bundle.py`,ZIP upload,preparation MD/JSON,preservation JSON. Cập nhật `.gitignore`,PLAN_AI/PLAN_HUMAN chỉ nghiệm thu gói local C02,docs/TABPFN_CLOUD_PLAN.md và CODEX_HANDOFF.md. C03–C06 vẫn PENDING.

## I. Important warning

Cloud chỉ nhằm thay hai kết quả TabPFN subsample sau khi kết quả thực được mang về và verified. Task này không thay official scores,dataset,split,embeddings,XGBoost,TabM,BERT,legacy hoặc P7 artifacts.

Các phát hiện chỉ dành cho laptop; nhãn đại diện suy từ số sao có nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review còn thuộc ABSA; bộ dữ liệu gold được chú thích thủ công dự kiến nhỏ, hiện chưa có. Không suy diễn production readiness hoặc hỗ trợ mô hình tiếng Việt.
