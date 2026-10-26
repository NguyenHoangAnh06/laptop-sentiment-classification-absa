# P5 — mô hình huấn luyện cổ điển và đánh giá

Ngày 2026-10-15 (Asia/Saigon). **P5 hoàn thành**, theo nghiệm thu chính thức trong PLAN_AI §8 / PLAN_HUMAN chặng 5. BERT thuộc **P6**, không thực thi; yêu cầu có điều kiện về Transformer trong brief được giải quyết theo thứ tự giai đoạn chính thức. P0–P4 không chạy lại; không thay raw/P2/split/preprocessing hoặc nguồn siêu dữ liệu. Không SQLite/DuckDB, tải bộ dữ liệu, tạo nhãn gold, triển khai app/API hoặc ABSA.

## Nhiệm vụ và bằng chứng

| tác vụ ID chính thức | Công việc | Trạng thái | các tệp kết quả |
|---|---|---|---|
| P5-E00 | mô hình cơ sở thuộc loại đa số | DONE | Ma trận `majority/model.joblib`, metrics/confusion |
| P5-E01 | đã cố định TF-IDF + Hồi quy logistic; so sánh trọng số lớp | DONE | `logistic_regression/`, 4 ứng viên trong huấn luyện history |
| P5-E02 | đã cố định TF-IDF + SVM tuyến tính; convergence/weights | DONE | `linear_svm/`, 4 ứng viên, không warning |
| P5-E03 | đã cố định TF-IDF + Decision Tree; kiểm soát độ phức tạp/weights | DONE | `decision_tree/`, 4 ứng viên, bounded depth/leaf |

các mô hình: `artifacts/models/p5_20261015/`. bằng chứng: `reports/p5/p5_20261015/`. Contract/lệnh suy luận: `docs/P5_MODEL_CONTRACT.md`. P5 không có Txx trong PLAN; dùng đúng E00–E03, không tạo tác vụ ID giả. Required thước đo và giai đoạn đầu ra đều đủ.

## đầu vào và protocol đã xác minh

Đọc AGENTS/handoff, hai PLAN đúng phần liên quan, P4 report/contract/config/source/ bản kê và tests. Phiên bản hiện hành là `p4_20261009_final`; bản không `_final` vẫn superseded. Checksum-bind đầu ra P4, implementation và completed-input bản chụp trạng thái; 149 đầu vào paths giống trước và sau lần chạy, bao gồm raw/P2/P3 và tài nguyên BERT. Không tái làm các bước QA/EDA/acquisition hoặc chuẩn bị split/token đặc trưng.

| phân chia | review | Sản phẩm gốc | Tiêu cực | trung tính | tích cực |
|---|---:|---:|---:|---:|---:|
| tập huấn luyện | 21.000 | 6.357 | 5.781 | 1.842 | 13.377 |
| tập xác thực | 4.500 | 1.361 | 1.239 | 395 | 2.866 |
| kiểm thử | 4.500 | 1.362 | 1.239 | 394 | 2.867 |

Tổng 30.000/9.080 sản phẩm, nhãn 8.259/2.631/19.110, hạt giống ngẫu nhiên42, không trùng sản phẩm giữa các tập 70/15/15. Đọc trực tiếp phân chia parquet và ordered mục tiêu sidecars, so khớp toàn bộ hàng/nhãn. Tái kiểm tra giao nhau review ID, parent_asin, asin, component, văn bản và sạch hàm băm đều 0. Dùng lại gần trùng bằng chứng P4 có hàm băm, không tuyên bố semantic/exhaustive bằng chứng xác nhận hoặc chạy lại splitter. P3 trước đây đã xem descriptive EDA toàn corpus; không gọi kiểm thử là chưa từng được xem ở bất cứ bước nào.

TF-IDF CSR float32 30.000 chiều giữ nguyên: toàn bộ 3 matrices giống đã cố định văn bản transform; IDF tái tính từ document frequency tập huấn luyện khớp. P5 không gọi khớp mô hình trên vectorizer. Chỉ văn bản làm predictors; ratings/metadata/IDs không vào estimator. nhãn negative/neutral/positive = 0/1/2, **nhãn đại diện suy từ số sao**, không bộ gold do con người gán nhãn. SemEval không trộn vào overall cảm xúc và giữ nguyên bytes/provenance.

13 lượt khớp mô hình: majority1, LR4, SVM4, DT4. LR/SVM thử C∈{0,5;2}, weights∈{None,balanced}; DT thử max_depth∈{10,25}, min_samples_leaf5, weights∈{None,balanced}. Không densify sparse matrix, không oversample/scaler. Positive/neutral tập huấn luyện ratio khoảng7,26 giải thích việc so sánh weights; giá trị balanced chỉ tính từ tập huấn luyện nhãn. Chọn theo tập xác thực macro F1, exact tie theo thứ tự cấu hình, convergence warning không đủ điều kiện. Không có warning trong 13 lượt khớp mô hình. Không mở rộng grid sau kiểm thử.

`selection_lock.json` lưu lựa chọn, tham số, thước đo tập xác thực và mô hình hàm băm **trước** kiểm thử prediction. Không refit tập huấn luyện+tập xác thực. Mỗi family đã chọn dự đoán kiểm thử đúng một lượt. `validate_p5` tính lại thước đo từ saved predictions, không chạy lại kiểm thử prediction; kiểm tra lựa chọn từ tập xác thực history và raw-text suy luận bằng tập xác thực. kiểm thử chỉ phục vụ cuối cùng comparison/diagnostics sau lock.

## Kết quả thực đo

| mô hình | tập xác thực macro F1 | kiểm thử macro F1 | kiểm thử tỷ lệ dự đoán đúng (accuracy) | kiểm thử có trọng số F1 | kiểm thử neutral F1 |
|---|---:|---:|---:|---:|---:|
| Đa số | 0,259390 | 0,259445 | 0,637111 | 0,495886 | 0,000000 |
| Hồi quy logistic | **0,693554** | **0,683887** | 0,807333 | 0,824430 | **0,350746** |
| SVM tuyến tính | 0,687509 | 0,678138 | **0,847556** | **0,841337** | 0,282014 |
| Cây quyết định | 0,527902 | 0,530962 | 0,736222 | 0,717325 | 0,127367 |

**Best classical: LR, C0,5, class_weight=balanced, lbfgs, max_iter1000, hạt giống ngẫu nhiên42.** Được chọn nhờ tập xác thực macro F1 cao nhất, không dựa kiểm thử. LR hơn SVM khoảng0,0060 tập xác thực macro F1, là chênh lệch điểm đo, chưa có significance claim. kiểm thử LR hơn SVM0,00575 macro F1 nhưng tỷ lệ dự đoán đúng (accuracy) thấp hơn0,04022. Macro F1 ưu tiên độ phủ ba lớp, đặc biệt neutral, nên không đổi winner vì SVM tỷ lệ dự đoán đúng (accuracy) cao hơn.

SVM chọn C0,5/balanced, dual=tự động, max_iter10000. DT chọn depth25/leaf5/None; balanced tăng neutral F1 nhưng giảm tập xác thực macro F1 nên không chọn. LR C0,5: dùng balanced tăng tập xác thực macro F1 từ0,593780 lên0,693554 và neutral F1 từ0,034314 lên0,366383. Mọi cặp weight được lưu, không mặc định weights tốt hơn.

Train/validation macro F1 của được chọn LR:0,84224/0,69355; SVM:0,97362/0,68751; DT:0,72213/0,52790. Các gap cho thấy nguy cơ overfit, rõ ở SVM; tăng C lên2 làm tập huấn luyện gần hoàn hảo nhưng không thắng tập xác thực ứng viên balanced C0,5. Depth25 DT hơn depth10 về tập xác thực nhưng vẫn kém linear các mô hình và còn gap train/val. Đây là quan sát, không chứng minh nguyên nhân độc lập với nhãn noise/product shift.

## Tính toán chi phí

| mô hình | (Các) khớp mô hình đã chọn | Tất cả họ lượt khớp mô hình (s) | Văn bản suy luận (ms/review) | byte mô hình | mô hình + byte TF-IDF được chia sẻ | RAM tối đa của quá trình lấy mẫu (MB) |
|---|---:|---:|---:|---:|---:|---:|
| Đa số | 0,0034 | 0,0034 | 0,3126 | 440 | 334.426 | 338,44 |
| LR | 3,0256 | 11,2844 | 0,3152 | 692.871 | 1.026.857 | 394,31 |
| SVM | 0,9820 | 4,9108 | 0,3202 | 692.674 | 1.026.660 | 407,01 |
| DT | 23,3157 | 62,9718 | 0,3387 | 40.506 | 374.492 | 353,44 |

CPU, 1 native thread. Python3.13.12/Windows, đã ghim phiên bản .venv sklearn1.7.2; default workstation sklearn1.8.0 không dùng để train/load. Không cần phụ thuộc mới. Whole run115,7853s, peak RSS408.522.752bytes, tổng ứng viên khớp mô hình79,1703s. đầu ra trước bản kê1.580.739bytes. Giới hạn config900s/1GB RSS/100MB đầu ra; đạt yêu cầu, không tăng ngân sách trong run. GPU/VRAM không áp dụng cho P5.

RAM là process RSS lấy mẫu20ms, bao gồm shared đầu vào và allocations trước đó, không phải RAM riêng từng estimator. Limits kiểm tra giữa operations, không là hard OS kiểm tra giới hạn. khớp mô hình thời gian có overhead monitor nhỏ. độ trễ là median5 lần trên 128 tập xác thực review sau1 warmup, gồm cleaning/TF-IDF/predict, chia số review; không tính load disk và không là độ trễ một request riêng. CSV còn có thời gian dự đoán toàn kiểm thử. Các số nhỏ không đủ để xếp hạng tốc độ triển khai thực tế. Shared P4 vectorizer333.986bytes, không copy bốn lần; suy luận bộ tải kiểm hash.

## phân tích lỗi sau khóa chọn

LR:867/4.500 sai so với đại diện (19,27%). Confusion matrix, true rows/predicted columns:

| Đúng → Dự đoán | Tiêu cực | trung tính | tích cực |
|---|---:|---:|---:|
| Tiêu cực | 985 | 195 | 59 |
| trung tính | 122 | 188 | 84 |
| tích cực | 112 | 295 | 2.460 |

Neutral độ bao phủ (recall)47,72%, độ chính xác dự đoán (precision)27,73%; **số mẫu hỗ trợ kiểm thử là394**, tập xác thực là395. 188neutral đúng trên394; 678neutral predictions gồm 195negative và295positive bị kéo về neutral. Positive→neutral295 lớn hơn positive→negative112; negative→neutral195 lớn hơn negative→positive59. Đây là trade-off lớp weighting, không xác nhận review thực sự neutral.

| Slice cố định | Hàng | Lỗi đại diện | Tỷ lệ lỗi |
|---|---:|---:|---:|
| Có dấu hiệu phủ định từ vựng | 2.603 | 601 | 23,09% |
| Có cả positive/negative lexical cues | 216 | 58 | 26,85% |
| Từ 5 | 143 | 12 | 8,39% |
| >Từ 200 | 431 | 98 | 22,74% |

Flags có thể giao nhau; không cộng các denominators hoặc coi là semantic nhãn. Không đổi thresholds sau khi xem kiểm thử. Script tạo41 chẩn đoán examples có hạt giống ngẫu nhiên42, tối đa5 mỗi confusion cell và3 mỗi flagged slice, deduplicate IDs. Queue local ở `artifacts/models/p5_20261015/error_review_queue.parquet`, không commit văn bản lớn.

Codex đã đọc12 examples (2 mỗi off-diagonal cell); đây là **AI qualitative review**, không phải con người gán nhãn, không tính gold/noise tỷ lệ dự đoán đúng (accuracy). Dẫn chiếu suffix source-line của review_id để tái tìm, không sao chép dài review vào báo cáo:

- Negative→positive: `1102980` có lời chê laptop đang đánh giá và lời khen máy
  thay thế; `14059595` có đoạn khen ban đầu rồi update trải nghiệm xấu. Bag-of-ngrams có thể nhầm target/thứ tự thời gian; cần con người adjudication để phân loại nguyên nhân.
- Negative→neutral: `15152348` chứa nhiều từ biểu đạt mức tạm chấp nhận cùng
  phàn nàn hình ảnh; `38240845` rất ngắn và có replacement character, thiếu context.
- Neutral→negative: `18404098` mô tả thất vọng phần mềm; `28298419` pha vấn đề
  máy/warranty với hậu mãi tích cực. Một overall đại diện không thể hiện mọi khía cạnh.
- Neutral→positive: `4657699` thiên lời khen dù rating3; `10004175` vừa khen
  tốc độ/touch/battery vừa chê hạn chế phần mềm. Chỉ là các ứng viên nhãn mismatch/ mixed cảm xúc, không sửa nhãn hoặc khẳng định mô hình đúng thực tế.
- Positive→negative: `26007322` dùng negation để nói không cần gaming/work;
  `3680091` nêu vấn đề vệ sinh/hỗ trợ rồi kết luận hài lòng.
- Positive→neutral: `730371` kể cải thiện sau update; `32077794` pha chê tốc độ/
  wifi với nhận xét máy vẫn hoạt động. Temporal/mixed context chưa được mô hình hóa.

Sarcasm **NOT_MEASURED**; lexical cues không xác nhận sarcasm, mixed meaning hoặc rating/text disagreement. Không có tỷ lệ nhiễu nhãn được con người xác nhận ở P5. Phân biệt: đại diện lỗi là số đo; true mô hình error/label nhiễu là các giả thuyết cần bộ gold do con người gán nhãn. không trùng sản phẩm giữa các tập đo unseen sản phẩm, không brand/user/time-disjoint; source/brand bias và lựa chọn bias vẫn có. Detailed P7 chưa hoàn thành bởi diagnostics này.

## Xác minh và các tệp kết quả

- `.venv/Scripts/python.exe -m pytest -q`: **195 PASS**,14,47s (180 cũ+15 P5).
- Sau thêm independent-validator assertion vào integration kiểm thử:
  `-m pytest -q tests/test_p5.py`: **15 PASS**,2,87s.
- Regression cuối sau cập nhật: `-m pytest -q`: **195 PASS**,9,62s; không FAIL.
- `.venv/Scripts/python.exe -m pip check`: **Không tìm thấy yêu cầu nào bị hỏng**.
- `.venv/Scripts/python.exe -m compileall -q src scripts`: thoát0.
- `-B -m scripts.train_p5`: exit0, DONE,13 lượt khớp mô hình thực tế,0cảnh báo.
- `-B -m scripts.validate_p5`: exit0, **PASS**,4models,4.500 dự đoán đã lưu;
  metrics/confusions/CSV và tập xác thực-based lựa chọn khớp,149input hàm băm đã xác minh, không predict kiểm thử lại. Mỗi mô hình tải lại từ văn bản tập xác thực khớp saved TF-IDF prediction.
- Hồ sơ kiểm toán độc lập cuối cùng: `reports/p5/p5_20261015_qa.json` PASS, kèm theo hàm băm
  validator/tests và kết quả commands. Cả hai danh sách kiểm tra P5 không còn unchecked; handoff đủ A–H. Audit không sửa đã hoàn thành lần chạy hoặc chạy lại kiểm thử predictions.

kiểm thử gồm thước đo zero-division/mapping/shape; seeded sparse fit/reload; tie và convergence exclusion; mục tiêu order; phân chia sản phẩm giao nhau; tree bounds; end-to-end dữ liệu mẫu khớp mô hình train-only/no tiền xử lý refit; immutable đầu ra refusal; tệp kết quả tamper; language/empty text/output contract; zero-error queue. dữ liệu mẫu scores không được dùng làm đánh giá so sánh. Không thay kiểm thử cũ để PASS.

Các file tạo: `configs/p5.yaml`, `src/sentiment/classical.py`, `src/evaluation/classification.py`, `scripts/train_p5.py`, `scripts/validate_p5.py`, `tests/test_p5.py`, `docs/P5_MODEL_CONTRACT.md`, báo cáo này và lần chạy outputs. Sửa `PLAN_AI.md`, `PLAN_HUMAN.md`, `README.md`, `docs/CODEX_HANDOFF.md` để cập nhật evidence/state. Không xóa file, đổi kiến trúc, sửa phụ thuộc hoặc các tệp kết quả cũ. Chi tiết params/env/hashes trong config/environment/history/selection_lock/manifest; các mô hình và predictions nằm ở ignored các tệp kết quả, reusable văn bản suy luận đã tải lại PASS.

## Nghiệm thu và bước tiếp theo

**DONE_WHEN đạt:** cả4models được đánh giá trên cùng cố định kiểm thử, một comparable bảng, tất cả required metrics/costs, artifacts/confusions và best classical conclusion. Không còn BLOCKED ở P5. bộ gold do con người gán nhãn chưa có không bị giả thành P5 đánh giá so sánh. NEXT_ACTION: P6-T01 bộ dữ liệu adapter, theo một yêu cầu riêng; không khởi động P6.

Giới hạn bắt buộc: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (P10 hiện chưa có). SemEval nguồn/giấy phép vẫn NOT_VERIFIED theo owner educational exception; P5 không xác minh lại hoặc đổi provenance. Không claim cross-gadget generalization, BERT superiority, calibrated độ tin cậy hoặc production readiness.
