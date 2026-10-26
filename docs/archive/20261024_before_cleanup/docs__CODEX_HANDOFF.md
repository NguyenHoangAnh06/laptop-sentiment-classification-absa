# Bàn giao Codex — 2026-10-24

## A. Tổng quan và thẩm quyền

Review laptop tiếng Anh; nhãn negative/neutral/positive, ID0/1/2. Tiếng Việt dùng trao đổi/tài liệu, chưa phải ngôn ngữ mô hình. Yêu cầu đính kèm mới nhất thay bộ model cũ bằng majority sanity + XGBoost/TabM/explicit TabPFN V3/V3_5 frozen embeddings + BERT canonical end-to-end. ABSA/gold/app ngoài tác vụ. AGENTS và đầu hai PLAN/docs/MODEL_STACK_REFACTOR.md giữ thẩm quyền; checklist bên dưới là LEGACY.

## B. Trạng thái

VERIFIED: P5–P7 nghiệm thu với tổng thể LIMITED, không phải mọi model full-data. E00/E01/E02 REUSED; E03/V3 SUBSAMPLED10000, E04/V3_5 SUBSAMPLED1500. Cả hai version/checkpoint khác nhau qua SDK, metrics/alignment/hash PASS. E03 WARNING RSS6,48GB vượt trần6GB và default n_estimators1 phủ tối đa200/384 chiều nội bộ; không rerun test. E05 BERT canonical full21000, unweighted epoch3 được chọn bằng validation macro0,760338; test macro0,755382/neutral0,436129. P7 đủ6model và phân tích lỗi/compute. Không tuyên bố toàn dự án hoàn tất.

REPORTED: P0–P4 PASS trước tác vụ; cache/source/split/config/hash/alignment đã kiểm lại PASS, không regenerate. P8–P13/gold/ABSA/app chưa hoàn tất. SemEval license cũ NOT_VERIFIED theo ngoại lệ giáo dục; không tải lại.

## C. Dữ liệu và artifacts

Dataset30000/9080 parent_asin, negative8259/neutral2631/positive19110; SHA256611b73584a933645336784b13b7f004a17e8803758d1be8ac64708563eabb5ba. Split giữ `data/processed/splits/p4_20261009_final/`:21000/4500/4500, seed42; không resplit/relabel. Raw bất biến, không acquisition/cleaning lại. Leakage actual audit trước REPORTED; hash/split giữ nguyên và leakage tests PASS.

Cache `data/processed/features/semantic_20261024/` đủ30K; embeddings/labels/mapping/token/metadata riêng, fail closed khi hash/config/alignment đổi. Artifacts/report trong `artifacts/models/semantic_20261024/` và `reports/semantic_20261024/`; E03 dùng `attempts/resource01`/latest_attempt, giữ nguyên root BLOCKED lịch sử. BERT chọn `E05_transformer/unweighted`; balanced giữ riêng. 53 tệp legacy (27P5+26P6) khớp hash, `reports/model_stack_legacy_preservation_final.json`.

## D. Mã và môi trường

`.venv/Scripts/python.exe`: Python3.13.12/torch2.8.0+cu128/CUDA12.8/transformers5.0.0/tabpfn9.2.0/xgboost3.4.1/tabm0.0.3/sklearn1.7.2; RTX4050Laptop6GB/RAM16GB. Requirements không đổi trong tác vụ tiếp tục.

Frozen MiniLM-L6-v2 revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41,384FP32/mask-mean/L2/max256. Canonical title+newline+body/NFC/whitespace/giữ phủ định. BERT checkpoint google-bert/bert-base-uncased revision86b5e0934494bd15c9632b12f734a8a67f723594/max512; dùng token canonical cache, không frozen embeddings.

`configs/transformer_benchmark.yaml`: AdamW2e-5,3epochs/patience1,batch8/accum4/fp16,seed42, hai loss; history/source hash/smoke/selection lock/reload/test1pass đã lưu. `scripts/train_modern.py` thêm decision/subsample/redaction/RSS guard trước test; `tabpfn_versions.py` pin9.2 và kiểm SDK resolved version. Không sửa legacy configs/p4,p5,p6.yaml/src/sentiment/bert.py.

## E. Thay đổi và xác minh gần đây

- VERIFIED: `.venv/Scripts/python.exe -m scripts.verify_benchmark` exit0; 249tests PASS=229+12+8,0FAIL;10 upstream deprecation warnings. Pip check/compileall và sáu independent validators PASS. JSON/log: `reports/model_stack_final_validation*`. Không predict test lại để xác minh.
- VERIFIED: E03/E04 đã test suite sau từng bước; P6 sau training245PASS/4SKIP (bốn nghiệm thu P7 chưa tồn tại), sau P7 toàn249PASS/không skip. Không cộng các lần lặp để tăng số tests.
- VERIFIED: V3 progressive500→21K low_memory, cached21K RSS6,06–6,08GB vượt6GB; chọn10K assessment5,82GB nhưng actual6,48GB vì overhead runner/reload. E03 monitor khi đó chưa enforce RSS; đã thêm guard cho E04. V3.5 low_memory5K RSS9,14GB, dừng tăng mẫu (10K INTERRUPTED, không OOM), cached2,5K6,36GB; chọn1,5K actual4,55GB. CPU auto cả hai bị SDKguard >5000. JSON/decision và báo cáo resource đầy đủ; không suy diễn full21K V3.5 đã chạy.
- VERIFIED: token presence Process=false/User=true/Machine=false; chỉ boolean trong `reports/tabpfn_environment_presence.json`, không in/lưu giá trị. Cached checkpoint chạy được, không dùng paid API/auto-accept license. Smoke24fit/3predict trước đó giữ nguyên.

## F. Nhiệm vụ hiện tại và hành động tiếp theo

Tác vụ tiếp tục E03→E04→P6→P7 đã hoàn tất trong giới hạn đã báo. `reports/model_stack_refactor_completion.md` có A–M; `p5_modern_tabular_models.md`, `p6_transformer_benchmark.md`, `p7_unified_benchmark.md`, CSV/error/validation là nguồn kết quả. TabM best frozen (test macro0,689086/neutral0,336673); XGBoost0,667752/0,321138; V3=0,562544/0,015075; V3.5=0,570952/0,032710. Không dùng test để chọn lại model.

NEXT_ACTION: người dùng review báo cáo/giới hạn; đánh giá human-gold độc lập là việc tương lai cần nhãn người, không tự tạo hoặc dùng gold train. Không khởi chạy benchmark mới, nới trần hoặc mở lại test chỉ để cải thiện score. Tác vụ sửa IDE trước là lịch sử ngoài phạm vi, không tiếp tục trong benchmark này.

## G. Giới hạn và lỗi cần biết

Chỉ laptop; nhãn sao là proxy có nhiễu, neutral8,77%; chưa có human gold (dự kiến bộ nhỏ). SemEval-to-Amazon platform/style shift thuộc ABSA tương lai, không phải benchmark Amazon hiện tại. Frozen context256 khác end-to-end512; một seed/search nhỏ, test đã dùng LEGACY; không claim statistical superiority/production. TabPFN khác số mẫu và V3 feature coverage hạn chế; E03 RSS WARNING. GPU allocated/reserved Windows có thể gồm shared memory, không đồng nhất VRAM vật lý.

Fit-only riêng campaign BERT/TabM/XGBoost và preprocessing toàn30K NOT_MEASURED; runtime/epoch gồm validation/reload/search theo runner. Latency chỉ predict trên embedding/token sẵn có, không raw-text end-to-end. Artifact bytes classifier chưa gồm shared MiniLM/cache. Các mẫu mixed/ambiguous/star-text mismatch chưa human verified; confidence null. `reports/p7_error_examples.csv` chứa excerpt đã lọc mẫu PII phổ biến, giữ cục bộ/.gitignore, không publish tự động.

## H. Hướng dẫn tiếp tục

Đọc AGENTS/bàn giao và chỉ source/report cần cho tác vụ mới. Để xác minh dùng `scripts.verify_benchmark` (không train/predict test); tổng hợp từ saved predictions bằng `finish_benchmark`/`final_completion`. Không chạy `report_model_refactor` cũ để hồi quy trạng thái: entrypoint đã chuyển báo cáo cuối khi có P7. Không acquisition/regen/resplit/retrain legacy, không overwrite outputs hoặc reset/checkout/commit; repository vẫn untracked từ đầu. Handoff là tóm tắt, artifacts mới là bằng chứng.
