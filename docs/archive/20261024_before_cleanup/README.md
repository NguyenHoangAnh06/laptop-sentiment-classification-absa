# Phân tích cảm xúc và khía cạnh trong đánh giá laptop

> **Cập nhật 2026-10-24:** benchmark hiện hành chuyển sang majority sanity + XGBoost/TabM/TabPFN-3/TabPFN-3.5 trên frozen semantic embeddings + Transformer end-to-end. Các kết quả và lệnh TF-IDF/LR/SVM/DT/BERT body-only bên dưới là **LEGACY**. Xem [hợp đồng và lệnh mới](docs/MODEL_STACK_REFACTOR.md), [đánh giá tác động](reports/refactor_impact_assessment.md) và [trạng thái thực](reports/model_stack_refactor_completion.md). Không suy diễn trạng thái DONE cũ thành nghiệm thu benchmark mới.

> **Nghiệm thu benchmark mới:** P0–P7 đã thực thi; tổng thể **LIMITED** vì TabPFN dùng10000/1500 mẫu và E03 có cảnh báo RSS. BERT canonical được chọn bằng validation macro F1, test macro F1=0,755382/neutral F1=0,436129; TabM dẫn nhóm frozen (macro0,689086). 249tests PASS; không rerun P0–P4/XGBoost/TabM hoặc mở lại test để tune. Xem [bảng và phân tích P7](reports/p7_unified_benchmark.md). Chỉ laptop, nhãn suy từ sao có nhiễu; chưa có đánh giá human gold, không hàm ý ABSA/app hoặc mô hình tiếng Việt đã hoàn tất.

Dự án Khoa học dữ liệu cá nhân trong 6 tuần, **chỉ dành cho laptop**. Mô hình hiện xử lý tiếng Anh; tiếng Việt/PhoBERT là hướng mở rộng chưa triển khai. Trọng tâm: dữ liệu/EDA 50%, mô hình/phân tích lỗi 40%, Streamlit 10%. `Electronics` là danh mục nguồn, không phải phạm vi nghiên cứu. Laptop 2-in-1/convertible thực sự vẫn hợp lệ; không có quy trình hay phương án dự phòng cho loại thiết bị khác.

Từ ngày 2026-10-19, trao đổi, tài liệu mới, chú thích mã và nội dung giao diện dùng **tiếng Việt**. Giữ nguyên tên biến, đường dẫn, lệnh, khóa cấu hình và nhãn kỹ thuật.

## Trạng thái dự án — bằng chứng đến 2026-10-15

[PLAN_HUMAN](PLAN_HUMAN.md) xác định phạm vi và thứ tự; [PLAN_AI](PLAN_AI.md) quy định ID tác vụ và tiêu chí chấp nhận. Chủ dự án đã duyệt C1-A/C2-A/C3-A/C4-B; xem [hồ sơ quyết định](reports/p1_acceptance_decision_20261009.md).

- **P1 hoàn thành:** chủ dự án chấp nhận ngoại lệ giáo dục cho bước xác minh nguồn/giấy phép SemEval. Nguồn và giấy phép vẫn `NOT_VERIFIED`; dùng XML/JSONL hiện có, giữ phân vùng và vị trí cụm từ gốc. Quyết định: `reports/tables/p1_semeval_owner_exception_20261009.json`. Recall trong nhóm được chọn là 89,08%; khoảng tin cậy đồng thời 95%: 55,46–99,85%. Vẫn có thiên lệch chọn mẫu và giới hạn QA có hỗ trợ. Gold độc lập ở P10 vẫn bắt buộc.
- **P2 hoàn thành, chỉ Amazon:** 30.000 review được chọn tiếng Anh tự động, 9.080 sản phẩm, 181 danh mục siêu dữ liệu. Nhãn suy từ số sao: `negative` 8.259 (27,53%), `neutral` 2.631 (8,77%), `positive` 19.110 (63,70%). Dành riêng 250 mẫu nghi nhiễu chưa được gán nhãn. [Báo cáo P2](reports/p2_amazon_completion_20261009.md) có phân bố thương hiệu trước/sau, nhật ký làm sạch/loại trùng và kiểm tra toàn vẹn. Độ chính xác thực về ngôn ngữ/spam/nhiễu theo con người và mức trùng ngữ nghĩa toàn diện chưa được đo.
- **P3 hoàn thành:** EDA mô tả, 15 bảng, 7 biểu đồ PNG+SVG và notebook 6 ô chạy từ kernel mới. Xem [báo cáo](reports/p3_data_analysis_20261009.md) và [notebook](notebooks/03_laptop_eda.ipynb).
- **P4 hoàn thành:** cố định 21.000/4.500/4.500 mẫu, hạt giống 42, không trùng sản phẩm giữa các tập. Chỉ khớp TF-IDF 30.000 đặc trưng trên tập huấn luyện; bộ tách token BERT được ghim phiên bản, độ dài tối đa 512. Xem [báo cáo](reports/p4_completion_20261009.md) và [hợp đồng dữ liệu](docs/P4_DATA_CONTRACT.md). P4 ghi nhận 180 kiểm thử đạt; đến P5 có 195 kiểm thử đạt và 149 hàm băm đầu vào không đổi. `vi` vẫn bị tắt.
- **P5 hoàn thành:** majority/LR/Linear SVM/Decision Tree, 13 lượt khớp trên đặc trưng P4 cố định. LR `C=0,5`, `balanced` được chọn bằng macro F1 xác thực 0,693554; macro F1 kiểm thử 0,683887; accuracy 0,807333; F1 lớp `neutral` 0,350746. Mỗi họ mô hình được chọn đánh giá test một lần; tính lại kết quả và tải lại độc lập đều đạt. Xem [báo cáo](reports/p5_completion_20261015.md) và [hợp đồng mô hình](docs/P5_MODEL_CONTRACT.md).
- **P6 hoàn thành:** hai chế độ hàm mất mát, mỗi chế độ 3 vòng huấn luyện đầy đủ. Chọn BERT `balanced` vòng 3: macro F1 xác thực 0,734646; macro F1 kiểm thử 0,730204; accuracy 0,852889; F1 `neutral` 0,404883. 181 đầu vào được bảo vệ không đổi tại thời điểm nghiệm thu. Kiểm tra độc lập, cập nhật mạng nền và tải lại trên CPU đều đạt. Bộ chạy tách tiến trình ghi nhận 195+12=207 kiểm thử đạt. Xem [báo cáo](reports/p6_completion_20261015.md) và [hợp đồng mô hình](docs/P6_MODEL_CONTRACT.md).

**P7 chưa bắt đầu; ABSA, human gold và ứng dụng còn chờ.** QA bộ lọc không phải human gold. [Bàn giao](docs/CODEX_HANDOFF.md) ghi đường dẫn và giới hạn hiện tại. Việc Việt hóa tài liệu/chú thích ngày 2026-10-19 không phải lần chạy lại hay nghiệm thu mô hình mới; hàm băm văn bản nguồn đã dịch có thể khác bằng chứng lịch sử.

## Cài đặt và kiểm tra

Môi trường đã kiểm tra: Python 3.13.12, Windows PowerShell. SciPy 1.18.1 được ghim ở P4 yêu cầu Python >=3.12; chưa xác minh cài mới bằng Python 3.11 với bộ phụ thuộc hiện tại.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m scripts.test_all
.\.venv\Scripts\python.exe -m compileall -q src scripts
```

P5 dùng lại môi trường dữ liệu/tokenizer/scikit-learn đã ghim. P6 bổ sung PyTorch CUDA/Transformers; Streamlit thuộc giai đoạn sau. Dùng `scripts.test_all` để tách kiểm thử Torch khỏi kiểm thử dữ liệu có giới hạn RAM. Chạy chung trong một tiến trình pytest sẽ vượt giới hạn 512 MB cũ; không tăng giới hạn để né kiểm tra.

## Lệnh P1 hiện hành

Đánh giá QA, không sửa nhãn:

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_filter_qa --path data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv --label-provenance ai_assisted_user_approved
```

Đã có XML train/test SemEval và JSONL chuyển đổi; tái sử dụng bằng chứng kiểm tra lược đồ, vị trí ký tự, cảm xúc và tương đương XML–JSONL. Không tải/kiểm tra lại khi nội dung không đổi. Ngoại lệ giáo dục cho phép dùng tệp hiện có trong các giai đoạn ABSA, nhưng không xác minh nguồn/giấy phép. Giữ phân vùng gốc, ID câu, vị trí cụm từ và nhãn `conflict`.

Không chạy lại khảo sát đầy đủ: kết quả v4 nằm ở `data/interim/feasibility/electronics_full_laptop_30k/`. Cấu hình v5 có dấu nhận dạng khác; không dùng để ghi đè hoặc coi kết quả v4 là lượt quét mới. Quy trình lịch sử nằm ở `reports/archive/p1_legacy_workflow/`; báo cáo dọn dẹp có bảng ánh xạ đường dẫn.

## Cấu trúc, phương pháp và giới hạn

`configs/` chứa phạm vi, hạt giống, nhãn, ngôn ngữ, lược đồ và giới hạn tài nguyên. `src/data/` chứa đọc dữ liệu theo luồng, lọc laptop, QA và kiểm tra SemEval. `scripts/` là các lệnh; logic tái sử dụng nằm trong `src/`. Dữ liệu thô ở `data/raw/` bất biến; kết quả trung gian ở `data/interim/`; nhãn thủ công ở `data/manual/`. Tệp `data/processed/laptop_reviews.parquet` có 30.000 review qua bộ chọn tiếng Anh tự động. Không đưa dữ liệu thô/tệp lớn vào Git. Các lần thử và mẫu QA trống đã lưu trữ không thuộc quy trình hiện hành; xem báo cáo dọn dẹp.

Số sao 1–2/3/4–5 ánh xạ sang `negative`/`neutral`/`positive` là **nhãn đại diện suy từ số sao**, không phải nhãn chuẩn con người. Chọn mô hình bằng macro F1; chia 70/15/15 chống rò rỉ, khớp TF-IDF chỉ trên train, điều chỉnh trên validation, giữ test riêng và cần bộ gold Amazon 300–500 review do con người gán nhãn độc lập.

Bắt buộc có majority/LR/Linear SVM/Decision Tree/BERT, trích xuất cụm từ khía cạnh bằng BERT và cảm xúc có điều kiện theo khía cạnh. Từ khóa/số sao không tạo nhãn chuẩn ABSA. Giữ vị trí `conflict` cho trích xuất, loại khỏi phân loại cảm xúc ba lớp theo chính sách.

Hợp đồng suy luận: `laptop/en`, ba nhãn, `confidence` có thể null, danh sách `aspects` rỗng khi không có khía cạnh. Tách định tuyến tiếng Anh/tiếng Việt. Đã có dự đoán cảm xúc tổng thể thực từ P5/P6; confidence null; ABSA chưa triển khai.

Giới hạn: **kết luận chỉ cho laptop**, **nhiễu nhãn suy từ số sao**, **khác biệt nền tảng/phong cách SemEval–Amazon trong cùng phạm vi laptop**, **bộ gold thủ công nhỏ, hiện chưa có**. Không tuyên bố sẵn sàng vận hành thực tế.

## Lệnh P2

```powershell
.\.venv\Scripts\python.exe -B -m scripts.prepare_p2_amazon
.\.venv\Scripts\python.exe -B -m scripts.report_p2_amazon --output-dir reports/tables/NEW_P2_REPORT
```

Lệnh chuẩn bị từ chối đầu ra đã tồn tại. Muốn chạy lại, dùng bản sao tách biệt với đường dẫn mới. Lệnh báo cáo kiểm tra kết quả đã lưu, không xử lý lại nguồn. Bản kê hiện hành: `data/interim/p2/20261009_final/manifest.json`; kết quả ban đầu ở `20261009/` đã được thay thế. Không ghi đè dữ liệu thô, QA hoặc kết quả tốn kém được bảo vệ.

## Lệnh P3

```powershell
.\.venv\Scripts\python.exe -B -m scripts.analyze_p3 --output-dir reports/p3/NEW_RUN
.\.venv\Scripts\python.exe -B -m scripts.execute_p3_notebook --output reports/p3/NEW_EXECUTED.ipynb
```

Phải dùng đường dẫn đầu ra mới. Notebook đọc bảng ở `20261009_verified`; muốn so sánh lần chạy khác thì đổi ô cấu hình thư mục đầu ra. Giữ nguyên văn bản/dữ liệu nguồn. P5-E00–E03 và P6-T01–T06 đã hoàn thành; giai đoạn tiếp theo là P7. SemEval vẫn có ngoại lệ xác minh của chủ dự án và trạng thái `NOT_VERIFIED`; phải giữ cách ly train/test gốc.

## Lệnh P4 và đầu vào cố định

```powershell
.\.venv\Scripts\python.exe -B -m scripts.prepare_p4
.\.venv\Scripts\python.exe -B -m scripts.validate_p4 --output reports/p4/p4_20261009_final/NEW_VALIDATION.json
```

Lệnh chuẩn bị từ chối đầu ra đã tồn tại. Chạy lại cần bản sao cấu hình có `output_suffix` mới; parquet P2 và kết quả P0–P3 giữ bất biến. Các tập ở `data/processed/splits/p4_20261009_final/`, tiền xử lý ở `artifacts/preprocessing/p4_20261009_final/`, đặc trưng token ở `data/processed/features/p4_20261009_final/`. Báo cáo/bản kê/kiểm tra tải lại ở `reports/p4/p4_20261009_final/`. Lần chạy ban đầu `p4_20261009/` chưa hoàn chỉnh và đã được thay thế.

Đặc trưng chỉ từ văn bản. Số sao/siêu dữ liệu dùng kiểm tra, `label_id` là mục tiêu riêng. `ClassicalPreprocessor` dùng từ vựng/IDF huấn luyện đã cố định cho tập giữ lại và suy luận. `BertPreprocessor` dùng tokenizer/độ dài cố định, không khớp tokenizer hoặc trọng số cục bộ. Không khớp lại trên validation/test hoặc dùng từ phân theo lớp của P3 để chọn đặc trưng có giám sát. Dự đoán/kết quả P5 lưu riêng.

## Lệnh P5 và mô hình đã lưu

```powershell
.\.venv\Scripts\python.exe -B -m scripts.train_p5
.\.venv\Scripts\python.exe -B -m scripts.validate_p5
.\.venv\Scripts\python.exe -m pytest -q tests/test_p5.py
```

Không ghi đè hậu tố đã hoàn thành `p5_20261015`. Muốn chạy lại đúng giao thức, sao chép `configs/p5.yaml`, đặt `output_suffix` mới và truyền `--config`. Không dùng kết quả test để điều chỉnh mới. Mô hình/siêu dữ liệu ở `artifacts/models/p5_20261015/{majority,logistic_regression,linear_svm,decision_tree}/`; thước đo, chi phí, ma trận nhầm lẫn, lịch sử và khóa lựa chọn ở `reports/p5/p5_20261015/`. Cần tệp TF-IDF P4 dùng chung `tfidf.joblib`; dùng sklearn 1.7.2 trong `.venv`. Cách dùng `load_classical` và `predict(frame)` nằm trong hợp đồng mô hình. Bộ kiểm tra tính lại thước đo test đã lưu và chạy suy luận validation mà không huấn luyện lại; confidence null và chưa có ABSA.

## Lệnh P6 và mô hình đã lưu

Chi phí P5 trên CPU và P6 trên GPU khác thiết bị/khối lượng xử lý; xem báo cáo về giới hạn so sánh và precision yếu của lớp `neutral`.

P6 đã hoàn thành theo yêu cầu ngày 2026-10-15, tinh chỉnh đầy đủ trên RTX4050 Laptop 6 GB bằng đầu vào P4 cố định, lựa chọn chỉ trên validation trước một lượt test. Mô hình tốt nhất: `artifacts/models/p6_20261015/balanced/`. Macro F1 test tăng 0,046317 so với LR và 0,052066 so với SVM. Tổng thời gian 52,27 phút; mô hình được chọn cùng tokenizer 438,68 MB; độ trễ văn bản theo lô GPU quan sát được 20,15 ms/review.

```powershell
.\.venv\Scripts\python.exe -u -B -m scripts.train_p6
.\.venv\Scripts\python.exe -B -m scripts.validate_p6
.\.venv\Scripts\python.exe -B -m scripts.report_p6
.\.venv\Scripts\python.exe -m scripts.test_all
```

Hậu tố `p6_20261015` được bảo vệ. Lệnh huấn luyện/phân tích từ chối đầu ra đã có; không khởi động lại hoặc ghi đè lần chạy tốn kém đã hoàn thành. Đọc `manifest.json`, `selection_lock.json`, `training_history.json`. Cấu hình mặc định so sánh `unweighted`/`balanced` trên toàn tập huấn luyện, tối đa 3 vòng mỗi chế độ, batch 8/tích lũy 4/độ dài 512. Huấn luyện GPU FP16; đánh giá/suy luận FP32; có dự phòng CPU. P6 không triển khai P7, ABSA hoặc tạo human gold mới.
