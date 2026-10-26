# Chẩn đoán lỗi sentiment: model, proxy rating và mất cân bằng

**Hoàn tất phân tích mô tả và tooling; phân bổ nguyên nhân thực còn PENDING human audit.** Không train/predict lại, không đổi split/embeddings/nhãn hoặc selection. Đầu vào là6saved predictions hiện hành, cả V3/V3_5 full21K đã reverify. Hash nguồn và trạng thái đầy đủ trong JSON cùng tên.

## 1. Phân biệt câu hỏi

| Câu hỏi | Bằng chứng hiện có | Kết luận cho phép |
|---|---|---|
| Model bất đồng rating proxy ở đâu? | Predictions/IDs/y_true được đối chiếu, confusion/strata | Đo được bất đồng proxy, chưa phải lỗi với human gold |
| Có mất cân bằng không? | Phân phối train/val/test và predicted shares | Có; mức đóng góp vào từng lỗi chưa xác định |
| Weighted loss có giúp không? | BERT unweighted/balanced từ history validation đã khóa | Recall/precision/macro có trade-off, không giải thích toàn bộ lỗi |
| Rating proxy có sai sentiment không? | Cần người đọc độc lập với rating/predictions | NOT_MEASURED tới khi có annotation hợp lệ |
| Lỗi do mất cân bằng hay proxy bao nhiêu phần trăm? | Chưa có causal experiment/human evidence đủ | Không cộng/trừ hai nguyên nhân như hai tập loại trừ nhau |

## 2. Phân phối lớp và mức dự đoán neutral

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

Trọng số inverse_frequency_weight_train chỉ tính từ train N/(3*n_class), không fit lại. Neutral ít là thực tế quan sát; điều này không chứng minh mọi neutral bị bỏ sót là do mất cân bằng.

| model | support | predicted_count | predicted_share | precision | recall | f1 | proxy_disagreements | error_rate_within_class |
|---|---|---|---|---|---|---|---|---|
| E00_majority | 394 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 394 | 1.000000 |
| E01_xgboost_embedding | 394 | 590 | 0.131111 | 0.267797 | 0.401015 | 0.321138 | 236 | 0.598985 |
| E02_tabm_embedding | 394 | 604 | 0.134222 | 0.278146 | 0.426396 | 0.336673 | 226 | 0.573604 |
| E03_tabpfn_v3_embedding | 394 | 8 | 0.001778 | 1.000000 | 0.020305 | 0.039801 | 386 | 0.979695 |
| E04_tabpfn_v35_embedding | 394 | 48 | 0.010667 | 0.625000 | 0.076142 | 0.135747 | 364 | 0.923858 |
| E05_transformer | 394 | 381 | 0.084667 | 0.443570 | 0.428934 | 0.436129 | 225 | 0.571066 |

support và error_rate dùng mẫu số true proxy class. predicted_share dùng toàn4500test. Precision/recall theo proxy, không theo human gold; predicted neutral cực ít cũng có thể liên quan representation/priors/model/preprocessing/nhãn mơ hồ.

Cùng một test distribution nhưng mức dự đoán neutral rất khác: V3=8,V3_5=48,BERT=381 trên394proxy neutral. Mất cân bằng là điều kiện chung; các bảng này không đủ để coi nó là lời giải thích duy nhất cho khác biệt giữa các model.

## 3. Bằng chứng weighted/unweighted hiện có

| mode | epoch | validation_macro_f1 | neutral_precision | neutral_recall | neutral_f1 | negative_f1 | positive_f1 | selected_within_mode_by_validation_macro_f1 |
|---|---|---|---|---|---|---|---|---|
| unweighted | 1 | 0.712574 | 0.448430 | 0.253165 | 0.323625 | 0.867545 | 0.946552 | False |
| unweighted | 2 | 0.742438 | 0.472789 | 0.351899 | 0.403483 | 0.877125 | 0.946706 | False |
| unweighted | 3 | 0.760338 | 0.440758 | 0.470886 | 0.455324 | 0.880639 | 0.945051 | True |
| balanced | 1 | 0.740707 | 0.341823 | 0.645570 | 0.446976 | 0.846794 | 0.928349 | False |
| balanced | 2 | 0.756596 | 0.372414 | 0.683544 | 0.482143 | 0.848382 | 0.939262 | False |
| balanced | 3 | 0.758344 | 0.381329 | 0.610127 | 0.469328 | 0.866584 | 0.939121 | True |

Chọn epoch trong từng loss bằng validation macro F1, không chọn epoch chỉ vì neutral F1. Không rerun balanced test hoặc thay model đã chọn. Hai candidate tốt nhất:

| mode | epoch | validation_macro_f1 | neutral_precision | neutral_recall | neutral_f1 | negative_f1 | positive_f1 | selected_within_mode_by_validation_macro_f1 |
|---|---|---|---|---|---|---|---|---|
| unweighted | 3 | 0.760338 | 0.440758 | 0.470886 | 0.455324 | 0.880639 | 0.945051 | True |
| balanced | 3 | 0.758344 | 0.381329 | 0.610127 | 0.469328 | 0.866584 | 0.939121 | True |

Balanced trừ unweighted: macro F1=-0.001994; neutral precision=-0.059429; recall=+0.139241; F1=+0.014004.

Weighted tăng neutral recall/F1 nhưng giảm precision và macro F1 ở candidate tốt nhất từng mode, nên giữ unweighted theo protocol. Đây là bằng chứng sensitivity đối với weighting trong một run/một seed; chưa phải ước lượng causal error fraction, không chứng minh imbalance là nguyên nhân duy nhất. Trọng số có thể khuếch đại cả noisy minority labels. Không suy diễn hiệu ứng cho TabPFN/XGBoost/TabM khi chưa có ablation tương ứng.

| class | support | both_correct | corrected_by_balanced | regressed_by_balanced | both_wrong | unweighted_false_positives | balanced_false_positives |
|---|---|---|---|---|---|---|---|
| negative | 1239 | 1045 | 4 | 58 | 132 | 163 | 133 |
| neutral | 395 | 179 | 62 | 7 | 147 | 236 | 391 |
| positive | 2866 | 2601 | 6 | 82 | 177 | 129 | 79 |

Riêng neutral validation: balanced sửa được 62ca unweighted bất đồng proxy, đồng thời làm sai thêm 7ca; false positives neutral tăng từ236 lên391. Đây là trade-off quan sát được, không phải nhãn nguyên nhân của từng review.

Paired counts dùng hai mảng validation đã lưu của candidate tốt nhất từng mode; macro được tính lại và khớp history. Row order theo val_loader cố định trong runner; balanced không có một file ID riêng. Bốn cột both_correct/corrected/regressed/both_wrong cộng bằng support từng lớp. False positives có mẫu số là các review ngoài lớp đó; không cộng vào support lớp nguồn. Các thay đổi chưa chứng minh causal contribution của imbalance hoặc tỷ lệ noisy labels.

## 4. Lỗi theo nhóm và agreement giữa model

Các CSV active mới: p7_error_groups.csv (all/short<=10/long>200/negation/mixed lexical/proxy_neutral), p7_error_transitions.csv (đủ3x3, có support và tỷ lệ theo lớp nguồn), p7_error_by_rating.csv, p7_class_diagnostics.csv và p7_error_agreement.csv. Nhóm lexical chồng lấn, không phải annotation semantic; không hardcode aspect findings.

| proxy_class | competitive_models_disagreeing_with_proxy | support | human_cause_status |
|---|---|---|---|
| negative | 0 | 839 | NOT_MEASURED |
| neutral | 0 | 5 | NOT_MEASURED |
| positive | 0 | 2294 | NOT_MEASURED |
| negative | 1 | 150 | NOT_MEASURED |
| neutral | 1 | 13 | NOT_MEASURED |
| positive | 1 | 211 | NOT_MEASURED |
| negative | 2 | 70 | NOT_MEASURED |
| neutral | 2 | 67 | NOT_MEASURED |
| positive | 2 | 151 | NOT_MEASURED |
| negative | 3 | 68 | NOT_MEASURED |
| neutral | 3 | 79 | NOT_MEASURED |
| positive | 3 | 86 | NOT_MEASURED |
| negative | 4 | 67 | NOT_MEASURED |
| neutral | 4 | 97 | NOT_MEASURED |
| positive | 4 | 79 | NOT_MEASURED |
| negative | 5 | 45 | NOT_MEASURED |
| neutral | 5 | 133 | NOT_MEASURED |
| positive | 5 | 46 | NOT_MEASURED |

Agreement chỉ dùng5model cạnh tranh, loại majority sanity. Ngay cả5model cùng bất đồng proxy vẫn chỉ là ca ưu tiên đọc, không phải bằng chứng proxy sai. Đồng thuận cũng có thể cùng sai. p7_error_examples.csv có excerpt đã lọc mẫu liên hệ phổ biến, confidence trống/human_verified=False, chỉ giữ local; chưa audit PII đầy đủ, không tự publish review text.

## 5. Audit rating–text đọc mù và cách phân loại

Đã tạo `data/manual/sentiment_diagnosis_20261024/review_annotation.csv`: 300SRS không hoàn lại từ4500test và60ca ưu tiên nhiều model bất đồng proxy (tối đa20mỗi lớp), rời nhau. Seed42, full text chỉ trong data/manual được ignoreGit. Phiếu không chứa rating/proxy/model/group; private_reference.json giữ mapping/selection/predictions và fingerprint nguồn. Chạy lại không overwrite trường người đã nhập.

Nhóm representative dùng để ước lượng bất đồng proxy–human trong **test population4500** sau khi annotation đầy đủ; không khái quát thẳng sang toàn30K. Nhóm enriched chỉ tìm kiểu lỗi, không dùng prevalence và không gộp tỷ lệ với representative. uncertain giữ riêng, không chuyển neutral. Có khoảng tin cậy exact hypergeometric95% khi representative đủ decisive labels; nếu uncertain thì báo tỷ lệ có điều kiện và cận mô tả trên mẫu, không tự điền nhãn.

| Proxy so với human | Model so với human | Diễn giải có thể ghi |
|---|---|---|
| Khớp | Khớp | Cả hai khớp human |
| Khớp | Không khớp | Model error theo human; chưa biết causal mechanism |
| Không khớp | Khớp | Proxy–human mismatch; model khớp human |
| Không khớp | Không khớp | Cả proxy/model bất đồng human; không ép thành một nguyên nhân |

Cảm xúc mixed/insufficient_context được lưu riêng cùng bằng chứng và người gán/ngày. Đọc hướng dẫn `docs/SENTIMENT_DIAGNOSIS.md`; evaluator chỉ chạy khi người vận hành xác nhận human review. Validator không thể tự chứng minh danh tính người gán.

**BLOCKED:** chưa có human sentiment annotations. **NEXT_ACTION:** người dùng hoàn thành phiếu đọc mù, sau đó chạy evaluator. Không có tỷ lệ nhiễu nhãn thật/human accuracy được tạo trong tác vụ này. Bộ này là audit chẩn đoán reused test, **không phải independent P10 gold**; P10 vẫn cần bộ gold sentiment+ABSA độc lập.

## 6. Giới hạn và trạng thái

Phân tích test chỉ mô tả sau selection, không quay lại tune/relabel train hoặc đổi benchmark. Score và ranking chính giữ nguyên. Các nguyên nhân có thể cùng xuất hiện; không thể gán nhãn “do imbalance” cho từng review chỉ từ rating/prediction. Human audit hỗ trợ phân biệt model/proxy theo cách người đọc hiểu text, không chứng minh causal contribution của class imbalance.

Chỉ laptop tiếng Anh; noisy star-derived proxy; SemEval-to-Amazon platform/style shift thuộc ABSA; gold thủ công dự kiến nhỏ/chưa có. Không production/model tiếng Việt/statistical superiority. Snapshot local subsample vẫn giữ trong reports/history/tabpfn_before_kaggle_20261024; CSV p7_error_* hiện thay bằng phân tích active6model, không mất bản cũ.

## Xác minh công cụ

Kết quả test/commands/source hashes mới nhất: `reports/p7_error_diagnosis_validation.json`; bảo toàn scientific files/legacy và xác nhận human fields trống trong `reports/p7_error_diagnosis_preservation.json`. Báo cáo import cloud giữ bằng chứng kiểm thử của tác vụ import, không thay cho kiểm thử chẩn đoán mới.
