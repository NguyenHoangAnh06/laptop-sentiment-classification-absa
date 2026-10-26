# P9 — Aspect Sentiment Classification và end-to-end ABSA cho laptop

**P9: DONE — READY FOR P10.** Standalone gold-aspect ASC là kết quả chính; joint ABSA dùng predicted spans P8 được báo riêng. Không triển khai P10.

## 1. Mục tiêu

Phân loại sentiment cho đúng một aspect occurrence trong sentence, không dùng label chung toàn câu. Gold-aspect ASC trả lời khi aspect đúng đã có thì classifier làm tốt đến đâu; joint metric đồng thời yêu cầu span và sentiment đúng. Không đặt target score nghiệm thu giả.

## 2. Dataset

SemEval-2014 Task4 **Laptop** từ XML/JSONL local đã có ở P1 và P8. Không dùng Restaurant/domain khác, Amazon30K proxy labels hoặc pseudo-aspect để train. Source/license vẫn NOT_VERIFIED theo ngoại lệ giáo dục P1; local hashes không chứng thực độc lập official origin. Không download/acquire thêm dữ liệu.

| split | source_sentences | original_aspect_entities | examples | excluded_conflict | max_sequence_length | truncated_examples |
|---|---|---|---|---|---|---|
| train | 2587 | 2039 | 1999 | 40 | 93 | 0 |
| validation | 458 | 319 | 314 | 5 | 62 | 0 |
| test | 800 | 654 | 638 | 16 | 92 | 0 |

Mỗi sample là một sentence+gold aspect/span, giữ original_aspect_index, raw polarity/xml_attributes, sentence ID/qualified UID và source_file. P9 kiểm raw XML+JSONL/P8 hashes, term/spans, polarity enum, missing/duplicates/overlap; không mặc nhiên coi P8 PASS là đủ.

## 3. Polarity distribution

| split | polarity | original_count | original_share | included_supervised |
|---|---|---|---|---|
| train | negative | 733 | 0.359490 | True |
| train | neutral | 399 | 0.195684 | True |
| train | positive | 867 | 0.425208 | True |
| train | conflict | 40 | 0.019617 | False |
| validation | negative | 133 | 0.416928 | True |
| validation | neutral | 61 | 0.191223 | True |
| validation | positive | 120 | 0.376176 | True |
| validation | conflict | 5 | 0.015674 | False |
| test | negative | 128 | 0.195719 | True |
| test | neutral | 169 | 0.258410 | True |
| test | positive | 341 | 0.521407 | True |
| test | conflict | 16 | 0.024465 | False |

Original share dùng mẫu số mọi aspects kể cả conflict; supervised class shares trong manifest dùng mẫu số chỉ3class. Neutral và các lớp khác có support khác nhau; test polarity mix khác train/validation được công bố, không dùng để đổi weights.

## 4. Conflict policy

PLAN/AGENTS yêu cầu đúng3nhãn negative/neutral/positive và resolve/exclude conflict có ghi chép. Đánh giá lựa chọn: giữ4class trái hợp đồng output hiện hành và conflict ít mẫu; map sang3class sẽ làm sai ý nghĩa mixed sentiment nếu không có căn cứ; **chọn exclude conflict** khỏi supervised/standalone target, giữ nguyên annotation trong nguồn và sidecar exclusions. Quyết định dựa trên PLAN và định nghĩa nhãn trước test, không chọn từ score test.

Conflict F1=N/A, model không được train để phát hiện conflict. Joint evaluation loại gold conflict khỏi recall denominator và ignore predicted entities có **exact cùng span conflict** chỉ lúc chấm điểm. Các predictions này vẫn được model infer, lưu và đếm raw; không dùng gold polarity để tạo input hoặc chặn predictions trước inference. Partial/overlapping conflict span khác ranh giới vẫn là FP nếu không khớp valid gold. Tổng excluded/ignored được công bố ở mục13. Đây là metric3class có điều kiện, không full4class ABSA.

## 5. Input representation

`[CLS] context_before [unused0] target_occurrence [unused1] context_after [SEP]`. Marker đặt bằng character offsets, không text.find trong SemEval. Chọn marker thay sentence+term pair thuần vì cùng term có thể xuất hiện nhiều lần với ngữ cảnh khác: pair thuần không chỉ ra occurrence. Hai reserved tokens IDs1/2 đã ở BERT vocab được đăng ký special trên **bản tokenizer P9 riêng**, vocab giữ30522, không resize embedding hoặc sửa tokenizer P8; serialization/reload có tests.

Sentence/raw original span giữ nguyên. Extraction span kế thừa policy P8 trim whitespace biên có giải thích cho1train annotation; không sửa polarity/annotation gốc. Toàn bộ context được giữ, không stemming/stopword removal. API không có offsets chỉ chấp nhận term xuất hiện đúng1lần; repeated/overlapping occurrence bắt buộc cung cấp start/end.

## 6. Train/validation/test integrity

Dùng đúng sentence-level splitIDs P8:2587train/458validation/800official test, seed42/group normalized text. Không tách aspect examples của cùng sentence qua train/validation. Câu0aspect không tạo ASC example nhưng vẫn thuộc split và có mặt trong end-to-end evaluation; không gán nhãn giả cho chúng. Official partitions giữ nguyên.

Exact ASC record overlap (text,start,end,label): {"train__validation": 0, "train__test": 1, "validation__test": 0}. Term overlap counts: {"train__validation": 102, "train__test": 146, "validation__test": 58}. Shared term tự nó không phải leakage.

Qualified sentence UID overlap0 và normalized text overlap train–validation0. Official raw ID/text227 trùng tự nhiên như P8 đã công bố; namespace tránh đụng khóa nhưng không xóa content overlap. Main test giữ nguyên; supplementary loại duplicate từ cùng saved predictions ở bảng8–9, không dùng để selection.

Standalone runner chỉ load train/validation cho model selection; test records được mở sau selection_lock. Chuẩn bị data có đọc test labels cho integrity/distribution, không dùng score test để quyết định conflict, preprocessing, weight hoặc epoch. P8 test đã được xem ở pha trước; không gọi đây là một holdout hoàn toàn mới.

## 7. Model configuration và imbalance

| setting | value |
|---|---|
| pretrained_model | google-bert/bert-base-uncased |
| revision | 86b5e0934494bd15c9632b12f734a8a67f723594 |
| max_length | 128 |
| seed | 42 |
| representation | occurrence_markers_single_sequence |
| device | cuda |
| threads | 2 |
| epochs | 5 |
| learning_rate | 0.000030 |
| batch_size | 8 |
| eval_batch_size | 16 |
| gradient_accumulation | 2 |
| weight_decay | 0.010000 |
| warmup_ratio | 0.100000 |
| max_grad_norm | 1.000000 |
| optimizer | AdamW |
| scheduler | linear_warmup_decay |
| loss_candidates | ['unweighted', 'balanced'] |
| evaluation_strategy | epoch |
| selection_metric | validation_macro_f1 |
| tie_break | first_candidate_then_earliest_epoch |
| gradient_checkpointing | True |
| mixed_precision | fp16 |
| max_seconds | 10800 |
| max_process_rss_bytes | 6000000000 |

Một BERT sequence classifier,2loss candidates unweighted/balanced cùng pretrained source, seed, batch order, optimizer/schedule. Không reuse P6/P8 fine-tuned weights. Balanced weights=N_train/(3*n_train_class): {"negative": 0.9090495679854479, "neutral": 1.6700083542188806, "positive": 0.7685505574778931}. Không dùng validation/test để tính weights.

| mode | epoch | validation_macro_f1 | accuracy | weighted_f1 | neutral_precision | neutral_recall | neutral_f1 | training_seconds |
|---|---|---|---|---|---|---|---|---|
| unweighted | 1 | 0.694972 | 0.754777 | 0.738989 | 0.733333 | 0.360656 | 0.483516 | 31.081996 |
| unweighted | 2 | 0.698448 | 0.754777 | 0.742915 | 0.631579 | 0.393443 | 0.484848 | 30.565712 |
| unweighted | 3 | 0.697646 | 0.738854 | 0.740909 | 0.469697 | 0.508197 | 0.488189 | 38.147517 |
| unweighted | 4 | 0.714145 | 0.748408 | 0.753921 | 0.479452 | 0.573770 | 0.522388 | 35.165720 |
| unweighted | 5 | 0.704768 | 0.742038 | 0.745804 | 0.478261 | 0.540984 | 0.507692 | 38.256846 |
| balanced | 1 | 0.660749 | 0.710191 | 0.701379 | 0.571429 | 0.393443 | 0.466019 | 30.737711 |
| balanced | 2 | 0.700374 | 0.757962 | 0.746843 | 0.615385 | 0.393443 | 0.480000 | 29.993126 |
| balanced | 3 | 0.686903 | 0.707006 | 0.722797 | 0.410000 | 0.672131 | 0.509317 | 29.893573 |
| balanced | 4 | 0.712292 | 0.735669 | 0.749240 | 0.440860 | 0.672131 | 0.532468 | 30.265024 |
| balanced | 5 | 0.705353 | 0.745223 | 0.748169 | 0.477612 | 0.524590 | 0.500000 | 30.021927 |

| mode | epoch | validation_macro_f1 | accuracy | weighted_f1 | negative_precision | negative_recall | negative_f1 | neutral_precision | neutral_recall | neutral_f1 | positive_precision | positive_recall | positive_f1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| unweighted | 4 | 0.714145 | 0.748408 | 0.753921 | 0.820312 | 0.789474 | 0.804598 | 0.479452 | 0.573770 | 0.522388 | 0.840708 | 0.791667 | 0.815451 |
| balanced | 4 | 0.712292 | 0.735669 | 0.749240 | 0.858407 | 0.729323 | 0.788618 | 0.440860 | 0.672131 | 0.532468 | 0.861111 | 0.775000 | 0.815789 |

Balanced−unweighted ở checkpoint tốt nhất mỗi mode: {"validation_macro_f1": -0.0018538374323791018, "accuracy": -0.01273885350318471, "weighted_f1": -0.004680917081115066, "neutral_precision": -0.03859183974075708, "neutral_recall": 0.09836065573770492, "neutral_f1": 0.010079472766039932}. Không chọn weighted chỉ vì neutral recall tăng; selection dùng validation macroF1.

| class | support | both_correct | corrected_by_balanced | regressed_by_balanced | both_wrong | unweighted_false_positives | balanced_false_positives |
|---|---|---|---|---|---|---|---|
| negative | 133 | 94 | 3 | 11 | 25 | 23 | 16 |
| neutral | 61 | 33 | 8 | 2 | 18 | 38 | 52 |
| positive | 120 | 88 | 5 | 7 | 20 | 18 | 15 |

Paired rows dùng cùng validation examples/IDs; corrected/regressed là thay đổi so gold polarity, FP có mẫu số ngoài lớp. Một seed, không causal superiority claim. Không evaluate test cho candidate không được chọn.

## 8. Standalone validation results

| split | examples | macro_f1 | accuracy | weighted_f1 |
|---|---|---|---|---|
| validation | 314 | 0.714145 | 0.748408 | 0.753921 |

## 9. Standalone official test results

| split | examples | macro_f1 | accuracy | weighted_f1 |
|---|---|---|---|---|
| test | 638 | 0.748118 | 0.789969 | 0.785988 |
| test_excluding_natural_duplicate_supplementary | 637 | 0.747258 | 0.789639 | 0.785553 |

Selected mode=unweighted, epoch=4 bằng validation macroF1, tie theo candidate order rồi epoch sớm nhất. Official gold-aspect test inference1pass sau lock, không tuning. Reload selected checkpoint tái lập nguyên validation predictions theo cùng batch/precision. Confidence=null vì chưa calibration; không gọi raw softmax là xác suất tin cậy.

## 10. Per-class results

| split | class | precision | recall | f1 | support |
|---|---|---|---|---|---|
| validation | negative | 0.820312 | 0.789474 | 0.804598 | 133 |
| validation | neutral | 0.479452 | 0.573770 | 0.522388 | 61 |
| validation | positive | 0.840708 | 0.791667 | 0.815451 | 120 |
| test | negative | 0.630682 | 0.867188 | 0.730263 | 128 |
| test | neutral | 0.758333 | 0.538462 | 0.629758 | 169 |
| test | positive | 0.883041 | 0.885630 | 0.884334 | 341 |

Nhãn/ma trận cố định theo negative,neutral,positive. Conflict bị loại có provenance, không có Conflict F1 giả. MacroF1 là trung bình F1 ba lớp; accuracy/weightedF1 đi kèm để không che minority behavior.

## 11. Confusion matrices

Hàng=gold, cột=prediction. CSV confusion_matrix.csv đủ9ô/split.

### validation

| gold | negative | neutral | positive |
|---|---|---|---|
| negative | 105 | 21 | 7 |
| neutral | 15 | 35 | 11 |
| positive | 8 | 17 | 95 |

### test

| gold | negative | neutral | positive |
|---|---|---|---|
| negative | 111 | 10 | 7 |
| neutral | 45 | 91 | 33 |
| positive | 20 | 19 | 302 |

## 12. Error analysis

| split | group | examples | sentences | errors | accuracy |
|---|---|---|---|---|---|
| validation | all | 314 | 202 | 79 | 0.748408 |
| validation | negation_cue | 84 | 50 | 29 | 0.654762 |
| validation | contrast_cue | 32 | 23 | 7 | 0.781250 |
| validation | comparison_cue | 15 | 12 | 1 | 0.933333 |
| validation | long_context_gt30_words | 42 | 18 | 18 | 0.571429 |
| validation | multi_aspect_sentence | 183 | 71 | 57 | 0.688525 |
| validation | mixed_polarity_sentence | 50 | 19 | 22 | 0.560000 |
| validation | rare_aspect_train_frequency_le1 | 136 | 103 | 32 | 0.764706 |
| test | all | 638 | 411 | 134 | 0.789969 |
| test | negation_cue | 134 | 89 | 51 | 0.619403 |
| test | contrast_cue | 70 | 46 | 23 | 0.671429 |
| test | comparison_cue | 33 | 15 | 15 | 0.545455 |
| test | long_context_gt30_words | 57 | 21 | 20 | 0.649123 |
| test | multi_aspect_sentence | 379 | 152 | 80 | 0.788918 |
| test | mixed_polarity_sentence | 103 | 38 | 42 | 0.592233 |
| test | rare_aspect_train_frequency_le1 | 342 | 256 | 86 | 0.748538 |

Test confusion lớn nhất: neutral→negative=45; positive→negative=20, negative→positive=7. Neutral→negative=45, neutral→positive=33 trên169gold neutral. Per-class P/R/F1 giúp phân biệt giảm recall với tăng false positives.

Nhóm negation/contrast/comparison chỉ lexical cues, group có thể chồng lấn; support và accuracy dùng mẫu số **aspect examples**, kèm số sentence riêng. Multi-aspect và mixed-polarity sentence lấy từ gold annotations3class cùng câu; không dùng một label chung cho cả câu. Rare<=1lần trong train ASC đã exclude conflict. Long context>30words chỉ proxy cấu trúc, không đo trực tiếp khoảng cách opinion–aspect.

Implicit sentiment, long-distance expression và mixed sentiment trong cùng một aspect chưa có human cause/opinion-span tags; không ép gán taxonomy hoặc gọi cue absence là implicit sentiment. Conflict rows giữ riêng để P10/task khác có thể xem xét, không tự tạo nhãn mới. Full wrong examples có ID/text/term/span/gold/pred/cue groups tại local `{validation,test}_error_examples.json`.

## 13. End-to-end results

| split | precision | recall | f1 | gold_entities | raw_predicted_entities | predicted_entities_scored | conflict_gold_excluded | predictions_ignored_exact_conflict | true_positive | false_negative | false_positive | extraction_missing_gold_spans | extraction_spurious_predicted_spans | exact_extraction_matched_spans | sentiment_errors_on_exact_span | boundary_gold_spans | boundary_predicted_spans | boundary_pairs | joint_wrong_span_and_polarity_pairs | missed_without_predicted_overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| validation | 0.563953 | 0.617834 | 0.589666 | 314 | 349 | 344 | 5 | 5 | 194 | 120 | 150 | 52 | 82 | 262 | 68 | 19 | 20 | 20 | 6 | 33 |
| test | 0.619403 | 0.650470 | 0.634557 | 638 | 686 | 670 | 16 | 16 | 415 | 223 | 255 | 115 | 147 | 523 | 108 | 69 | 97 | 97 | 25 | 46 |

PLAN P9-T04 yêu cầu nối ATE→ASC: dùng **P8 predicted spans đã lưu** trên toàn458validation/800test, không chạy lại P8 test hoặc dùng gold aspect để thay input. P9 selected classifier infer trên mọi predicted spans, rồi chấm exact span+sentiment. Span sai ranh giới hoặc polarity sai đều không full credit. Standalone macroF1 và joint microP/R/F1 là hai bài toán/mẫu số khác nhau, không thay thế nhau.

## 14. End-to-end error decomposition

FN_joint=extraction_missing_gold_spans+sentiment_errors_on_exact_span; FP_joint=extraction_spurious_predicted_spans+sentiment_errors_on_exact_span. Boundary gold/pred là các unmatched spans có giao ký tự, là subset của extraction errors. Joint_wrong_span_and_polarity_pairs là quan hệ overlap vừa sai span vừa sai polarity, có thể nhiều-nhiều; không cộng như taxonomy rời nhau hoặc tự gán classifier sai cho FP không có gold polarity. Counts và denominator ở bảng13, details mỗi sentence ở local decomposition JSON.

## 15. Limitations

Chỉ laptop tiếng Anh. P6 sentiment dùng Amazon reviews với nhãn đại diện suy từ số sao có nhiễu; P8/P9 dùng SemEval aspect annotations. Cùng laptop nhưng nguồn/thời kỳ/annotation scheme/style khác; **SemEval-to-Amazon platform/style shift chưa được đo**. Independent P10 human gold nhỏ vẫn PENDING; diagnosis360 không thay ABSA gold.

Source/license NOT_VERIFIED theo ngoại lệ P1; natural duplicate official splits;3class evaluation không cover conflict; một seed/search nhỏ, không statistical superiority/production hoặc tiếng Việt. GPU memory-efficient attention backward có cảnh báo nondeterministic với warn_only; split/data/saved-pred metrics tái lập, không cam kết retrain bitwise-identical. API ASC cap128 tính cả markers, P8 cap128 riêng; pipeline từ chối overlength rõ thay vì silent truncate. SemEval max lengths thực tế trong bảng2 đều dưới cap,0truncated.

Actual runtime/compute (versions và peak là số đo đã quan sát):

| measurement | value |
|---|---|
| model_directory | artifacts/models/p9_20261026/unweighted/best |
| selection_lock_sha256 | c893eef0cb4c92fed396119673d008b39853650d40f23863ac7589967251d473 |
| reload_validation_predictions_identical | True |
| test_prediction_passes | 1 |
| test_tuning | False |
| training_seconds | 324.129151 |
| validation_seconds | 0.537002 |
| test_seconds | 0.679156 |
| inference_ms_per_gold_aspect_from_tokens | 1.064507 |
| runtime_seconds_including_checkpoint_io | 346.843756 |
| peak_process_rss_bytes_current_process | 3060903936 |
| peak_gpu_allocated_bytes | 2264303104 |
| peak_gpu_reserved_bytes | 2497708032 |
| artifact_bytes | 438705553 |
| gpu_name | NVIDIA GeForce RTX 4050 Laptop GPU |

Versions: {"python": "3.13.12", "torch": "2.8.0+cu128", "transformers": "5.0.0"}. Training time cộng2candidate loops; wall gồm checkpoint I/O. Inference từ token có sẵn, không raw-text end-to-end latency. RSS cả tiến trình/GPU allocated/reserved không toàn VRAM vật lý; artifact_bytes chỉ selected model/tokenizer/metadata, không optimizer/last/candidate khác. Tiền compute NOT_MEASURED. Resume artifacts được lưu theo epoch; actual resume NOT_MEASURED vì run liền mạch.

## 16. Acceptance decision

**P9: DONE — READY FOR P10.** T01–T04 có artifacts thật, standalone gold-aspect ASC và joint tách biệt, conflict policy minh bạch, model selected từ validation, official test không tuning. Tests 378PASS/0FAIL, pip/compile checks và CPU reload/API smoke được lưu. 317files frozen P0–P8/raw giữ hash; không retrain P8 hoặc sửa Amazon/canonical scores. Chưa triển khai P10; dừng tại readiness đã ghi.

## 17. Artifacts

| artifact | path |
|---|---|
| ASC data/tokenizer/config/split provenance | data/processed/p9_20261026/manifest.json |
| Conflict exclusions giữ metadata | data/processed/p9_20261026/{train,validation,test}_conflict_excluded.jsonl |
| Selected model/tokenizer/metadata | artifacts/models/p9_20261026/unweighted/best |
| Loss candidates best/last/optimizer/RNG | artifacts/models/p9_20261026/{unweighted,balanced}/ |
| Training identity/history/selection lock | reports/p9_20261026/{training_identity,history,selection_lock}.json |
| Canonical standalone metrics | reports/p9_20261026/{validation,test}_metrics.json |
| Gold-aspect predictions có text local | data/interim/p9_20261026/{validation,test}_predictions.jsonl |
| End-to-end predictions có text local | data/interim/p9_20261026/{validation,test}_end_to_end_predictions.jsonl |
| Joint metrics/decomposition | reports/p9_20261026/end_to_end_results.json |
| Per-class/confusion/strata/weighting CSV | reports/p9_20261026/ |
| Independent verification | reports/p9_20261026/independent_evaluation.json |
| Tests/preservation/CPU API smoke | reports/p9_20261026/{validation,preservation,inference_smoke}.json |
| Acceptance | reports/p9_20261026/acceptance.json |

API: `AspectSentimentClassifier(directory).classify_aspect_sentiment(text,aspect,start,end)` và `AspectAnalyzer(extractor,classifier).analyze_aspects(text)`. Confidence/aspect_score/sentiment_score null; không có aspect trả[]. Language en, unsupported language báo lỗi. Không chạy pseudo labels Amazon30K, không annotation P10 hoặc UI/deployment.

## 18. Reproduction instructions

```powershell
.venv/Scripts/python.exe -B -m scripts.prepare_p9
.venv/Scripts/python.exe -B -m scripts.train_p9
.venv/Scripts/python.exe -B -m scripts.evaluate_p9_end_to_end
.venv/Scripts/python.exe -B -m scripts.finalize_p9 --run-checks
```

Train/evaluate_end_to_end chỉ dành namespace chưa có output, không chạy lại completed run. Resume trước selection bằng --resume, identity/config/source phải khớp. Xác minh run hiện tại chỉ dùng prepare_p9 và finalize_p9 (không flag dùng tests evidence còn đúng source; --run-checks chạy lại suite). Không chạy lại P8 finalizer để sửa các báo cáo frozen:350tests P8 là evidence lịch sử, shared test driver đã mở rộng cho P9; P9 preservation xác nhận nguyên bytes. Muốn retrain tái lập độc lập phải đặt namespace mới trước khi chạy và giữ thiết kế cố định, không chọn run theo test.
