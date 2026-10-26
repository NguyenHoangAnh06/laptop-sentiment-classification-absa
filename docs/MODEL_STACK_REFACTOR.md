# Hợp đồng benchmark semantic — cập nhật2026-10-24

Phạm vi: laptop tiếng Anh, nhãn negative/neutral/positive. Model hiện hành majority sanity, XGBoost/TabM/explicit TabPFN V3/V3_5 trên frozen embeddings, BERT end-to-end canonical. Đây là thay đổi đã được người dùng yêu cầu; TF-IDF/LR/SVM/DT và BERT body-only giữ LEGACY. ABSA/gold/app ngoài refactor.

## Dữ liệu và representation

Giữ dataset30000, split `data/processed/splits/p4_20261009_final/`21000/4500/4500/seed42. Không resplit/relabel hoặc thêm non-laptop. Canonical review_title+newline+text, NFC/whitespace, bỏ phần null, fail khi cả hai rỗng; giữ phủ định/dấu câu. Chỉ đưa dense embedding hoặc token vào model, ID/rating/metadata là sidecar.

`configs/semantic_benchmark.yaml` pin MiniLM384/revision/pooling/L2/FP32/max256 và tokenizer BERT riêng/max512. Cache `data/processed/features/semantic_20261024/` có hash dataset/split/config/tokenizer/file, row mapping và labels; loader fail khi thay đổi/corruption. Không regenerate nếu hợp lệ. Không TF-IDF/BoW/PCA/SVD hoặc internal text preprocessing TabPFN; đầu vào TabPFN là ma trận số384 chiều.

## Model selection và artifact

Chọn validation macro F1; báo cáo đầy đủ3lớp và chi phí. Hai loss BERT cùng pretrained source, class weights chỉ train. TabPFN pin9.2.0, API `create_default_for_version` qua `make_tabpfn`, SDK kiểm requested/resolved/checkpoint khác nhau. Resource config chọn bằng train-only. Khóa config/checkpoint trước test; saved predictions phải khớp review_id/labels và metric được tính lại độc lập.

Output hiện tại dưới `artifacts/models/semantic_20261024/`, `reports/semantic_20261024/`; E03 latest attempt=`resource01`, giữ root BLOCKED lịch sử. Không overwrite hoặc dùng retry để mở lại selection/test đã khóa. Không lưu token vào source/log/config/report/Git; dùng environment/secrets, không auto-accept license.

## Kết quả và giới hạn local

P0–P4/E00/E01/E02 PASS/REUSED. E03/E04 kỹ thuật PASS nhưng LIMITED/SUBSAMPLED10000/1500; E03 RSS6,48GB vượt trần6GB và V3 n_estimators1 chỉ phủ tối đa200/384 đặc trưng nội bộ. P6 canonical full21000 chọn unweighted epoch3 bằng validation, P7 đủ6model. [Completion](../reports/model_stack_refactor_completion.md) và [P7](../reports/p7_unified_benchmark.md) là nguồn score; không coi TabPFN local là full-data.

Test từng được xem ở LEGACY/local; không gọi hoàn toàn unseen. Chỉ rating-derived proxy labels, không human gold. Khác train size/context/thiết bị và overhead phải công bố; latency/artifact classifier chưa bao gồm toàn bộ shared encoder/preprocessing. Tiếng Việt/PhoBERT/ABSA/gold/app chưa hoàn tất.

## Cloud follow-up

**PENDING** theo [kế hoạch cloud](TABPFN_CLOUD_PLAN.md): chưa chọn budget/khởi tạo job/upload. Cần runner/namespace/resource config cloud riêng trước khi chạy, giữ hash/384 chiều/split/seed và kết quả local. Mục tiêu full21000 V3 rồi V3_5; đo tài nguyên độc lập. GPU24GB/RAM32GB và A10040GB/RAM64GB là đề xuất, chưa PASS. Không tự nới trần local hoặc mở lại test để thử config liên tục.

## Lệnh hiện hành an toàn cho repository đã có artifacts

```powershell
.venv/Scripts/python.exe -m scripts.verify_benchmark
.venv/Scripts/python.exe -m scripts.benchmark_reports
.venv/Scripts/python.exe -m scripts.finish_benchmark
.venv/Scripts/python.exe -m scripts.final_completion
```

Các lệnh này chỉ verify/tổng hợp từ saved predictions, không train/predict test. `scripts.test_all` chạy tests fixture và nghiệm thu artifacts. Runner mới cần thư mục mới và protocol được cố định; không chạy lại acquisition/cleaning/P0–P4 hoặc training cũ chỉ theo lệnh trong kế hoạch lịch sử.

## LEGACY và bằng chứng giữ nguyên

Configs p4/p5/p6/model_legacy, preprocessing/feature/model/checkpoint/predictions lịch sử và báo cáo2026-10-15 được giữ nguyên. Hợp đồng cũ và Word plan vẫn có giá trị provenance, xem [chỉ mục](PROJECT_INDEX.md). Không sửa manifests cũ để làm khớp source/docs mới, không reset/checkout/commit tự động.
