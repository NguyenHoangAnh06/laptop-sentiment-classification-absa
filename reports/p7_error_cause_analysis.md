# P7 — Chẩn đoán lỗi sentiment: proxy, human và mất cân bằng

**P7: DONE — READY FOR P8.** Human-reviewed diagnostic evaluation, không phải canonical test score. Không retrain, không đổi benchmark, split hoặc selection.

## 1. Mục tiêu

Định lượng bất đồng rating–human, tách lỗi theo human khỏi lỗi đánh giá proxy và xem xét imbalance/ambiguity bằng artifacts đã khóa. Không coi phân loại mô tả là chứng minh nhân quả.

## 2. Dữ liệu sử dụng

Amazon laptop tiếng Anh 30.000 review; split product-disjoint 21.000/4.500/4.500, seed42. Active models lấy từ p7_completion.json và provenance đã đối chiếu: E00_majority, E01_xgboost_embedding, E02_tabm_embedding, E03_tabpfn_v3_embedding, E04_tabpfn_v35_embedding, E05_transformer. TabPFN dùng cloud full21K, không dùng subsample lịch sử.

Phiếu `data/manual/sentiment_diagnosis_20261024/review_annotation.csv`: 300 SRS không hoàn lại từ 4.500 test (seed42, inclusion_probability=300/4500) và 60 enriched rời nhau, tối đa20/proxy class, ưu tiên nhiều model cạnh tranh bất đồng proxy. Đã tái lập chính xác sampling từ source. Tỷ lệ gộp360 chỉ mô tả diagnosis; không có CI hoặc population estimate cho tập gộp/enriched/toàn30K.

## 3. Trạng thái human review

360/360 là **human-reviewed sentiment diagnosis set**, được người dùng xác nhận toàn bộ ngày 2026-10-25; reviewer convention human_reviewer_01. Chỉ điền reviewer_id/reviewed_at còn trống theo yêu cầu; nhãn, ambiguity, evidence, ID, title/body giữ nguyên. Boolean TRUE/FALSE được đọc trực tiếp, không thay nội dung phiếu. Một reviewer; chưa đo agreement liên người. Đây là reused-test diagnosis, không phải independent P10 gold.

## 4. Kiểm tra integrity

| check | result |
|---|---|
| status | PASS |
| rows | 360 |
| unique_annotation_ids | True |
| unique_review_ids | True |
| no_missing_human_labels | True |
| three_labels_only | True |
| fixed_fingerprints_match | True |
| title_body_match_source | True |
| sampling_reproduced | True |
| rating_proxy_match_source | True |
| six_model_predictions_match_source | True |
| source_hashes_match | True |
| duplicate_title_body_pairs | 0 |
| encoding | UTF-8 CSV |
| annotation_sha256 | 69a7cd3e58b5b997a69005fcb5524b84bc46b6369d43458a05032145d9233cc8 |
| private_reference_sha256 | 157f4f43a0b2e53d7729ba05a2ca95d1947cdd936511692fbcb9a5cdc345498d |

Đối chiếu từng ID/text/title/rating/proxy/prediction với source và fingerprint; không mất/thêm review, không duplicate bất thường. Hash nguồn/split/history/sidecar khớp manifest. Chi tiết đường dẫn/hash trong JSON; mapping 2.160 review/model chỉ lưu local `data/interim/p7_diagnosis/human_attribution.parquet`.

## 5. Proxy so với human

Agreement 292/360 (81.11%); disagreement 68/360 (18.89%); Cohen kappa=0.668486. Đây là chỉ số của mẫu gộp, có enrichment.

| human_class | count | agreement | disagreement | disagreement_rate |
|---|---|---|---|---|
| negative | 136 | 95 | 41 | 0.301471 |
| neutral | 35 | 11 | 24 | 0.685714 |
| positive | 189 | 186 | 3 | 0.015873 |

Ma trận: hàng=human, cột=proxy; thứ tự negative/neutral/positive.

| human | negative | neutral | positive |
|---|---|---|---|
| negative | 95 | 31 | 10 |
| neutral | 6 | 11 | 18 |
| positive | 0 | 3 | 186 |

Human neutral chuyển thành proxy negative 6, positive 18, giữ neutral 11/35. Human negative bị proxy positive che khuất 10/136; human positive bị proxy negative 0/189. Không đồng nhất neutral/mixed hoặc coi mọi rating3 là neutral theo text.

SRS300: disagreement 31/300 (10.33%); khoảng95% exact hypergeometric cho **test population4500** [7.24%, 14.20%]. Có điều kiện thiết kế SRS và nhãn người cố định; không bao gồm sai số reviewer hoặc suy rộng sang train/30K. Enriched60: 37/60 (61.67%), không population inference.

## 6. Rating so với human

| rating | total | negative | neutral | positive | negative_share | neutral_share | positive_share |
|---|---|---|---|---|---|---|---|
| 1 | 65 | 65 | 0 | 0 | 1.000000 | 0.000000 | 0.000000 |
| 2 | 36 | 30 | 6 | 0 | 0.833333 | 0.166667 | 0.000000 |
| 3 | 45 | 31 | 11 | 3 | 0.688889 | 0.244444 | 0.066667 |
| 4 | 62 | 8 | 13 | 41 | 0.129032 | 0.209677 | 0.661290 |
| 5 | 152 | 2 | 5 | 145 | 0.013158 | 0.032895 | 0.953947 |

Rating vẫn là proxy hữu ích để duy trì benchmark nhất quán, nhưng sai ở cấp review; các phân phối theo sao trên là mô tả mẫu diagnosis có enrichment. Không suy ra độ chính xác toàn30K hoặc kết luận rating hoàn toàn tốt/xấu. Giữ provenance star-derived proxy và không tự relabel dataset.

## 7. Ambiguity

| ambiguity | count | share | disagreement | disagreement_rate |
|---|---|---|---|---|
| False | 188 | 0.522222 | 25 | 0.132979 |
| True | 172 | 0.477778 | 43 | 0.250000 |

TRUE là annotation mơ hồ/mixed do người dùng xác nhận; không tự suy ra kiểu semantic cụ thể. So sánh trên có liên hệ mô tả, chịu selection và reviewer bias, không chứng minh ambiguity gây mismatch. Số lượng từng nhóm hiển thị để đánh giá độ ổn định; nhóm con theo lớp nhỏ cần thận trọng.

## 8. Hiệu suất human diagnostic từng model

| model | n | proxy_accuracy | proxy_macro_f1 | proxy_weighted_f1 | human_accuracy | human_macro_f1 | human_weighted_f1 | delta_accuracy | delta_macro_f1 | delta_weighted_f1 |
|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 360 | 0.594444 | 0.248548 | 0.443244 | 0.525000 | 0.229508 | 0.361475 | -0.069444 | -0.019040 | -0.081769 |
| E01_xgboost_embedding | 360 | 0.675000 | 0.554692 | 0.687578 | 0.713889 | 0.594782 | 0.726228 | 0.038889 | 0.040089 | 0.038649 |
| E02_tabm_embedding | 360 | 0.672222 | 0.563462 | 0.690822 | 0.733333 | 0.631756 | 0.751272 | 0.061111 | 0.068295 | 0.060450 |
| E03_tabpfn_v3_embedding | 360 | 0.683333 | 0.471504 | 0.640653 | 0.738889 | 0.524561 | 0.699125 | 0.055556 | 0.053056 | 0.058472 |
| E04_tabpfn_v35_embedding | 360 | 0.691667 | 0.491660 | 0.655846 | 0.744444 | 0.545962 | 0.710939 | 0.052778 | 0.054302 | 0.055093 |
| E05_transformer | 360 | 0.716667 | 0.568910 | 0.724319 | 0.800000 | 0.674358 | 0.807726 | 0.083333 | 0.105448 | 0.083407 |

CSV p7_human_model_classes.csv chứa precision/recall/F1/support từng lớp theo cả human/proxy. JSON chứa confusion matrices từng model. Các bảng tách SRS/enriched nằm trong cùng CSV và JSON, không dùng ranking gộp để chọn model.

Thứ hạng macro F1 diagnosis theo proxy: E05_transformer > E02_tabm_embedding > E01_xgboost_embedding > E04_tabpfn_v35_embedding > E03_tabpfn_v3_embedding > E00_majority. Theo human: E05_transformer > E02_tabm_embedding > E01_xgboost_embedding > E04_tabpfn_v35_embedding > E03_tabpfn_v3_embedding > E00_majority. Thay đổi thứ hạng trên mẫu chỉ mô tả, chưa có kiểm định ưu thế và không thay ranking canonical.

So sánh riêng SRS300 (tránh diễn giải mức tăng trên mẫu enriched như hiệu quả đại diện):

| model | proxy_accuracy | human_accuracy | proxy_macro_f1 | human_macro_f1 | delta_macro_f1 |
|---|---|---|---|---|---|
| E00_majority | 0.646667 | 0.606667 | 0.261808 | 0.251729 | -0.010079 |
| E01_xgboost_embedding | 0.810000 | 0.776667 | 0.684472 | 0.619550 | -0.064922 |
| E02_tabm_embedding | 0.806667 | 0.793333 | 0.693570 | 0.665490 | -0.028080 |
| E03_tabpfn_v3_embedding | 0.820000 | 0.820000 | 0.575243 | 0.584858 | 0.009615 |
| E04_tabpfn_v35_embedding | 0.830000 | 0.820000 | 0.606165 | 0.584581 | -0.021584 |
| E05_transformer | 0.860000 | 0.870000 | 0.704326 | 0.691746 | -0.012580 |

Trên SRS, delta macro F1 có thể âm trong khi mẫu gộp tăng; enrichment chọn ca model sai proxy làm thay đổi hướng so sánh. BERT/TabM vẫn đứng đầu hai nhóm tương ứng trong SRS. TabPFN3 và3.5 đổi thứ tự nhẹ theo human SRS, không đủ chứng minh khác biệt thống kê.

## 9. Quy chiếu lỗi proxy/model

A: model=human≠proxy; B: model=proxy≠human; C: proxy=human≠model; D: cả model/proxy sai human **và model khác proxy**; E: cả ba khớp. Định nghĩa D rộng trong yêu cầu chồng B; D_inclusive=B+D được báo riêng. Năm nhóm A–E ở đây rời nhau, tổng360. Share dùng mẫu số360, human_errors=B+C+D; proxy_errors=A+C+D. A là ca benchmark proxy phạt dự đoán phù hợp human; B phù hợp giả thuyết bám proxy noise nhưng không chứng minh quá trình học.

| model | n | A | B | C | D | E | A_share | B_share | C_share | D_share | E_share | D_inclusive | human_errors | proxy_errors |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E00_majority | 360 | 3 | 28 | 106 | 37 | 186 | 0.008333 | 0.077778 | 0.294444 | 0.102778 | 0.516667 | 65 | 171 | 146 |
| E01_xgboost_embedding | 360 | 31 | 17 | 66 | 20 | 226 | 0.086111 | 0.047222 | 0.183333 | 0.055556 | 0.627778 | 37 | 103 | 117 |
| E02_tabm_embedding | 360 | 37 | 15 | 65 | 16 | 227 | 0.102778 | 0.041667 | 0.180556 | 0.044444 | 0.630556 | 31 | 96 | 118 |
| E03_tabpfn_v3_embedding | 360 | 30 | 10 | 56 | 28 | 236 | 0.083333 | 0.027778 | 0.155556 | 0.077778 | 0.655556 | 38 | 94 | 114 |
| E04_tabpfn_v35_embedding | 360 | 31 | 12 | 55 | 25 | 237 | 0.086111 | 0.033333 | 0.152778 | 0.069444 | 0.658333 | 37 | 92 | 111 |
| E05_transformer | 360 | 42 | 12 | 46 | 14 | 246 | 0.116667 | 0.033333 | 0.127778 | 0.038889 | 0.683333 | 26 | 72 | 102 |

Tệp local có case từng review/model; không ép gán nguyên nhân imbalance cho từng review. D_inclusive không cộng thêm vào A–E.

## 10. Bằng chứng mất cân bằng

| split | class | count | share | inverse_frequency_weight_train |
|---|---|---|---|---|
| train | negative | 5781 | 0.275286 | 1.210863 |
| train | neutral | 1842 | 0.087714 | 3.800217 |
| train | positive | 13377 | 0.637000 | 0.523286 |
| validation | negative | 1239 | 0.275333 | 1.210863 |
| validation | neutral | 395 | 0.087778 | 3.800217 |
| validation | positive | 2866 | 0.636889 | 0.523286 |
| test | negative | 1239 | 0.275333 | 1.210863 |
| test | neutral | 394 | 0.087556 | 3.800217 |
| test | positive | 2867 | 0.637111 | 0.523286 |

| model | support | predicted_count | precision | recall | f1 |
|---|---|---|---|---|---|
| E00_majority | 394 | 0 | 0.000000 | 0.000000 | 0.000000 |
| E01_xgboost_embedding | 394 | 590 | 0.267797 | 0.401015 | 0.321138 |
| E02_tabm_embedding | 394 | 604 | 0.278146 | 0.426396 | 0.336673 |
| E03_tabpfn_v3_embedding | 394 | 8 | 1.000000 | 0.020305 | 0.039801 |
| E04_tabpfn_v35_embedding | 394 | 48 | 0.625000 | 0.076142 | 0.135747 |
| E05_transformer | 394 | 381 | 0.443570 | 0.428934 | 0.436129 |

Neutral train1842/21000=8,77%; proxy neutral test394. Cùng phân phối mà model có neutral recall/F1 rất khác nhau, nên imbalance không đủ giải thích tất cả. Human class distribution ở mục5 khác proxy; 360 là mẫu bị chọn, không phải phân phối huấn luyện. Imbalance có thật và proxy mismatch có thật nhưng có thể tương tác; chưa xác định tính độc lập hoặc causal fraction.

## 11. Weighted so với unweighted

| mode | epoch | validation_macro_f1 | neutral_precision | neutral_recall | neutral_f1 | negative_f1 | positive_f1 | selected_within_mode_by_validation_macro_f1 |
|---|---|---|---|---|---|---|---|---|
| unweighted | 1 | 0.712574 | 0.448430 | 0.253165 | 0.323625 | 0.867545 | 0.946552 | False |
| unweighted | 2 | 0.742438 | 0.472789 | 0.351899 | 0.403483 | 0.877125 | 0.946706 | False |
| unweighted | 3 | 0.760338 | 0.440758 | 0.470886 | 0.455324 | 0.880639 | 0.945051 | True |
| balanced | 1 | 0.740707 | 0.341823 | 0.645570 | 0.446976 | 0.846794 | 0.928349 | False |
| balanced | 2 | 0.756596 | 0.372414 | 0.683544 | 0.482143 | 0.848382 | 0.939262 | False |
| balanced | 3 | 0.758344 | 0.381329 | 0.610127 | 0.469328 | 0.866584 | 0.939121 | True |

| class | support | both_correct | corrected_by_balanced | regressed_by_balanced | both_wrong | unweighted_false_positives | balanced_false_positives |
|---|---|---|---|---|---|---|---|
| negative | 1239 | 1045 | 4 | 58 | 132 | 163 | 133 |
| neutral | 395 | 179 | 62 | 7 | 147 | 236 | 391 |
| positive | 2866 | 2601 | 6 | 82 | 177 | 129 | 79 |

Chọn epoch tốt nhất từng mode bằng validation macro F1: balanced−unweighted=-0.001994. Neutral được sửa62 ca, sai thêm7; negative sửa4/sai thêm58; positive sửa6/sai thêm82. Tác động ròng mạnh nhất ở positive, còn recall tăng chủ yếu neutral. Neutral FP236→391; recall+0,139241, precision−0,059429, F1+0,014004. Giữ unweighted đã khóa.

Hai mảng là validation, còn 360human nằm test; review_id không giao nhau nên **không có paired human weighted/unweighted evaluation** và không chạy balanced test mới. Có bằng chứng weighting thay behavior/recall nhưng chưa có bằng chứng trực tiếp rằng nó sửa proxy noise; class weights không đổi label mapping và có thể tăng trọng số nhãn nhiễu. Không tuyên bố causal effect hoặc chuyển kết luận sang model khác.

## 12. Taxonomy lỗi

| nhóm | bằng chứng/chính sách |
|---|---|
| proxy label mismatch | Đo trực tiếp human≠proxy, bảng5/9; không causal fraction |
| class imbalance | Phân phối và sensitivity validation; không gán per-review cause |
| ambiguous / mixed sentiment | Boolean ambiguity từ human; không suy ra mọi mixed review đều neutral |
| implicit sentiment | Chưa có annotation taxonomy riêng; NOT_MEASURED |
| long review with mixed aspects | Độ dài/cue ở p7_error_groups chỉ heuristic; mixed aspects chưa xác minh |
| temporal sentiment shift | Cần human taxonomy theo thời gian sử dụng; NOT_MEASURED |
| strong rating but mixed review text | Proxy mismatch + ambiguity là dấu hiệu, không xác nhận semantic taxonomy |
| negation / comparison | Cue lexical chỉ nhóm mô tả, chưa có human causal tags |
| hardware/software-specific complaints | Chưa có annotation taxonomy riêng; NOT_MEASURED |
| positive overall with local complaint | Có thể tương thích ambiguity; chưa đếm semantic subtype |
| negative overall despite isolated praise | Có thể tương thích ambiguity; chưa đếm semantic subtype |

Không gán taxonomy semantic mới từ evidence bằng suy đoán hoặc tạo human annotation bổ sung. Đây là giới hạn độ chi tiết chẩn đoán, không blocker nghiệm thu các so sánh human/proxy.

## 13. Giới hạn

Các phát hiện chỉ dành cho laptop tiếng Anh. Nhãn đại diện suy từ số sao có nhiễu nhãn. Sự thay đổi SemEval-to-Amazon platform/style trong laptop review còn thuộc đánh giá ABSA. Bộ dữ liệu gold được chú thích thủ công nhỏ là hạn chế dự kiến P10; diagnosis360 này nhỏ, một reviewer và reused test, không thay independent gold. SRS chỉ đại diện test4500; enriched/360không đại diện30K. Test đã xem sau selection, không tuning hoặc tuyên bố production/ưu thế thống kê. Causal fraction của imbalance/representation NOT_IDENTIFIABLE; taxonomy chưa có tags riêng. Cloud/local khác thiết bị và phạm vi đo compute, V3 giới hạn coverage200/384; xem benchmark gốc.

## 14. Kết luận cuối

1. Bao nhiêu lỗi proxy phạt model phù hợp human? Cột A ở mục9, với từng model và mẫu số360; không suy rộng30K.
2. Bao nhiêu lỗi thật khi đối chiếu human? Cột human_errors=B+C+D ở mục9, bao gồm C khi proxy đúng và B/D khi proxy cũng sai.
3. Neutral yếu liên quan nhiều yếu tố: ít support train, proxy↔human chuyển lớp, ambiguity và model profile khác nhau. Chưa đủ causal evidence để chọn một nguyên nhân chủ yếu hoặc cộng các tỷ lệ như độc lập.
4. Weighting tăng neutral recall nhưng đổi precision/FP và làm giảm macro F1; không có paired human validation labels nên chưa xác nhận xử lý được noise.
5. Tiếp tục dùng rating proxy có giới hạn: SRS test agreement 269/300 (89.67%), giữ báo cáo nhãn-nhiễu và bổ sung independent gold P10. Không coi kết quả này là chất lượng nhãn toàn30K.
6. Không cần retrain sentiment trước P8: chưa có bug hoặc bằng chứng validation mới hợp lệ buộc thay selection. Human diagnosis dùng để giải thích; không dùng test để chọn lại mô hình.

## 15. Quyết định nghiệm thu P7

**P7: DONE. READY FOR P8.** Integrity360PASS; human–proxy/rating/ambiguity/sáu model và weighting đã phân tích từ artifacts thật. Benchmark metrics/selection/dataset/splits/weights giữ nguyên. P0–P7 acceptance và các giới hạn: `reports/p0_p7_acceptance.json`; validation: `reports/p7_error_diagnosis_validation.json`. Không còn blocker bắt buộc trước P8 theo phạm vi hiện hành. Dừng tại đây, **chưa triển khai P8**; independent gold/ABSA vẫn PENDING.
