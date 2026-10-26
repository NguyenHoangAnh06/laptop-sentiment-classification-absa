# P8 — ABSA Aspect Term Extraction cho laptop

**P8: DONE — READY FOR P9.** Chỉ trích xuất aspect term tường minh; không triển khai aspect sentiment/P9.

## 1. Mục tiêu

Xây dựng pipeline SemEval laptop → WordPiece BIO → BERT token classifier → character spans, với metric entity nghiêm ngặt và artifacts tái lập. Không đặt ngưỡng F1 nghiệm thu giả; không sửa test hoặc tune sau test. Sentiment canonical P0–P7 và Amazon30K giữ nguyên.

## 2. Dataset

Dùng SemEval-2014 Task4 **Laptop**, XML do người dùng cung cấp từ P1 và JSONL chuẩn hóa hiện có. Đây là phân vùng train/test mang tên official trong bộ nguồn local; SHA256 xác nhận byte local, không chứng thực độc lập nguồn chính thức. Source/license vẫn NOT_VERIFIED theo ngoại lệ giáo dục của chủ sở hữu ở P1; không acquisition hoặc chấp nhận điều khoản mới. Không dùng Restaurant/domain khác/Amazon30K để train ATE.

| original_split | sentences | aspect_terms | no_aspect_sentences |
|---|---|---|---|
| train | 3045 | 2358 | 1557 |
| test | 800 | 654 | 378 |

| split | sentences | aspect_entities | unique_aspect_terms | aspects_per_sentence | sentences_without_aspects | no_aspect_share | multiple_aspect_sentences | multiple_aspect_share | max_sequence_length | unigram_entities | multiword_entities |
|---|---|---|---|---|---|---|---|---|---|---|---|
| train | 2587 | 2039 | 855 | 0.788172 | 1303 | 0.503672 | 485 | 0.187476 | 91 | 1308 | 731 |
| validation | 458 | 319 | 207 | 0.696507 | 254 | 0.554585 | 73 | 0.159389 | 60 | 185 | 134 |
| test | 800 | 654 | 393 | 0.817500 | 378 | 0.472500 | 156 | 0.195000 | 90 | 364 | 290 |

Phân phối độ dài entity theo whitespace words và WordPiece: `entity_lengths.csv`; top20 aspect terms mỗi split: `top_aspect_terms.csv`. Casefold chỉ phục vụ đếm term/nhóm split; không thay text hoặc offsets vào model. Câu không aspect được giữ với toàn O trên tokens không đặc biệt.

## 3. Parse SemEval và bảo toàn nguồn

Dùng lại `src/data/semeval.py` và schema P1: sentence_id, text, split, aspects(term/start/end/polarity/xml_attributes). So sánh JSONL với parser XML theo toàn bộ record, kiểm IDs/missing/duplicate/invalid spans/out-of-range/overlap/duplicate annotations. Polarity kể cả conflict giữ nguyên metadata; không map hoặc train polarity trong P8.

| split | xml | xml_sha256 | jsonl | jsonl_sha256 |
|---|---|---|---|---|
| train | data/raw/semeval/Laptop_Train_v2.xml | efec2ed73b4efb83b47c697114d800149c558118884afa80362a6e975ba7248c | data/interim/semeval/train_sentences.jsonl | 06abcd3f33eb256a73b40bcbcfe3217854346c54c40cc952843db0a16d89011b |
| test | data/raw/semeval/Laptops_Test_Gold.xml | aa3a30c9dd7e0eacf9b69e898eb4118a36c1b4f391a30a08dfc41a38d8b8745b | data/interim/semeval/test_sentences.jsonl | 42e17079730204223294e83c88ecfe961a225f5630347fe867d62c10e354de96 |

Mỗi BIO record giữ nguyên sentence_id, raw text và original aspects, thêm uid=original_split:sentence_id, source_file, original_split, split, extraction_aspects. Không sửa raw XML hoặc JSONL P1 in-place.

## 4. BIO conversion

Nhãn riêng ATE: O=0, B-ASP=1, I-ASP=2, không dùng ánh xạ nhãn sentiment. Với mỗi gold character span, token WordPiece đầu là B, toàn bộ WordPiece tiếp theo trong cùng span là I; các token khác O. CLS/SEP và padding dùng -100 trong loss. Không bỏ continuation subword. Căn chỉnh dùng offsets gốc, không text.find; repeated term giữ đúng occurrence.

## 5. Alignment validation

Alignment **PASS**, unexplained failures=0; sentences truncated=0, overlength=0. BIO→character spans round-trip khớp extraction spans ở toàn bộ splits. Gold không có I sau O; boundary/overlap/token gaps được kiểm rõ.

| uid | sentence_id | aspect_index | original_span | extraction_span | reason |
|---|---|---|---|---|---|
| train:1436 | 1436 | 3 | [44, 54] | [44, 53] | trim_boundary_whitespace_only; original annotation preserved |

Một train annotation `uninstall` chứa NBSP ở cuối: original[44,54) được giữ nguyên, extraction span[44,53) bỏ whitespace biên bằng policy cố định cho mọi split. Không suy đoán sửa chữ hoặc dịch offsets. Official test không có adjustment nên strict test metric dùng đúng nguyên character boundaries nguồn. Hai term có ranh giới giữa cụm chữ không whitespace vẫn align được bằng WordPiece; không ép dùng regex word boundary.

## 6. Train/validation/test và leakage

GroupShuffleSplit seed42, validation fraction0.15; chỉ từ official train, grouping normalized text để duplicate train không sang validation. Actual train/validation=2587/458; tỷ lệ có thể lệch nhẹ do group. IDs cố định trong manifest. Official test giữ nguyên800 câu, không merge/resplit.

Qualified UID overlap=0 trên mọi cặp; normalized text overlap train–validation=0. Có **một duplicate tự nhiên `227`** giữa official train/test (cùng ID và text); source-split-qualified IDs tránh đụng khóa nhưng **không loại bỏ rò rỉ nội dung này**. Đã giữ nguyên benchmark gốc theo yêu cầu, không tự xóa test hoặc dùng test để quyết định train deletion. Bảng metric có cả official800 chính và supplementary loại đúng duplicate này (799 câu), dùng cùng saved predictions, không rerun/tune. Raw collision/duplicate được ghi đầy đủ trong data_validation.json; nghiệm thu có giới hạn này, không tuyên bố text-disjoint train–official test tuyệt đối.

Runner chỉ load train/validation trong training, ghi selection_lock trước khi load test records. Chuẩn bị data có kiểm hình thức spans/test để validation dữ liệu; không dùng metric test cho hyperparameters, epoch, checkpoint hoặc threshold.

## 7. Cấu hình model

| setting | value |
|---|---|
| pretrained_model | google-bert/bert-base-uncased |
| revision | 86b5e0934494bd15c9632b12f734a8a67f723594 |
| task | BertForTokenClassification |
| seed | 42 |
| max_length | 128 |
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
| evaluation_strategy | epoch |
| selection_metric | validation_entity_f1 |
| tie_break | earliest_epoch |
| gradient_checkpointing | True |
| mixed_precision | fp16 |
| max_seconds | 10800 |
| max_process_rss_bytes | 6000000000 |

Khởi tạo từ pretrained base local đã có; head token classifier mới, không reuse sentiment fine-tuned weights. Batch8×gradient accumulation2=effective16 (batch cuối nhỏ hơn); AdamW, linear warmup/decay, FP16, gradient checkpointing. Không search nhiều model hoặc class weighting. Max128 đủ vì official train tối đa91 tokens; official test chỉ kiểm không vượt cap (max90). API P8 từ chối input vượt cap, không truncate ngầm; windowing cho review dài chưa triển khai.

## 8. Kết quả huấn luyện

| epoch | train_sentences | mean_batch_loss | validation_precision | validation_recall | validation_f1 | training_seconds | validation_seconds |
|---|---|---|---|---|---|---|---|
| 1 | 2587 | 0.289894 | 0.710448 | 0.746082 | 0.727829 | 68.524465 | 1.130524 |
| 2 | 2587 | 0.054908 | 0.744986 | 0.815047 | 0.778443 | 70.064689 | 0.520712 |
| 3 | 2587 | 0.022493 | 0.786585 | 0.808777 | 0.797527 | 65.120984 | 1.152438 |
| 4 | 2587 | 0.010202 | 0.765043 | 0.836991 | 0.799401 | 59.182300 | 0.496802 |
| 5 | 2587 | 0.005541 | 0.760933 | 0.818182 | 0.788520 | 38.923479 | 0.693126 |

Đã chạy 5 epoch; best epoch=4 theo **validation entity F1**, tie chọn epoch sớm nhất. Training forward/backward/validation thực tế, không phải smoke. Reload best model tái lập nguyên validation predictions theo cùng chế độ/batch; selection lock và hashes đã đối chiếu độc lập. Last model + optimizer/scheduler/scaler/RNG/epoch được lưu để resume ở ranh giới epoch khi run chưa selection.

| measurement | value |
|---|---|
| selected_epoch | 4 |
| epochs_run | 5 |
| test_prediction_passes | 1 |
| test_tuning | False |
| reload_validation_predictions_identical | True |
| selection_lock_sha256 | 81e148053278acd7bf603e6068e974a265712cecd6f5b8314fdc7e3a3ecc8f33 |
| validation_seconds | 0.764859 |
| test_seconds | 1.248248 |
| inference_ms_per_sentence_from_tokens | 1.560311 |
| model_directory | artifacts/models/p8_20261026/best |
| artifact_bytes | 436311903 |
| runtime_seconds_including_checkpoint_io | 319.245483 |
| training_seconds | 301.815918 |
| peak_process_rss_bytes_current_process | 3021422592 |
| peak_gpu_allocated_bytes | 2252350976 |
| peak_gpu_reserved_bytes | 2476736512 |
| device | cuda |
| gpu_name | NVIDIA GeForce RTX 4050 Laptop GPU |

Runtime wall gồm checkpoint I/O; training_seconds chỉ vòng train cộng theo epoch; validation/test seconds tính từ token có sẵn và gồm decode/metrics, không là raw-text latency. Peak RSS là cả tiến trình, GPU allocated/reserved theo PyTorch, không toàn VRAM vật lý; tiền compute NOT_MEASURED. Model artifact bytes gồm best model/tokenizer/config, không gồm optimizer/last checkpoints.

Phiên bản: {"python": "3.13.12", "torch": "2.8.0+cu128", "transformers": "5.0.0"}. Seed được cố định; đã quan sát cảnh báo CUDA memory-efficient attention backward không bảo đảm bitwise determinism (warn_only). Không khẳng định retrain sẽ cho cùng trọng số/score từng bit. Split/BIO/metric từ saved predictions đã kiểm tái lập.

## 9. Entity-level evaluation

| split | sentences | gold_entities | predicted_entities | true_positive | false_positive | false_negative | entity_precision | entity_recall | entity_f1 |
|---|---|---|---|---|---|---|---|---|---|
| validation | 458 | 319 | 349 | 267 | 82 | 52 | 0.765043 | 0.836991 | 0.799401 |
| test | 800 | 654 | 686 | 539 | 147 | 115 | 0.785714 | 0.824159 | 0.804478 |
| test_excluding_natural_duplicate_supplementary_only | 799 | 653 | 685 | 538 | 147 | 115 | 0.785401 | 0.823890 | 0.804185 |

Metric chính: micro exact **character-span** P/R/F1; phải khớp toàn [start,end), `battery` không được partial credit cho `battery life`. Tự triển khai tập span theo câu và kiểm số học bằng fixtures; không thêm seqeval vì không cần dependency để đếm exact character spans. Không gọi đây là kết quả chạy official SemEval scorer. Gold BIO strict; prediction orphan I sau O được decode như bắt đầu entity (policy công bố), số lần sửa trong metrics JSON.

Token accuracy bổ trợ: validation=0.977764, test=0.974381; không dùng nghiệm thu. Saved predictions chứa sentence ID/text/gold/predicted aspects và character spans, chỉ lưu local để tránh tự publish dataset.

## 10. Error analysis

| split | boundary_pairs | boundary_gold_entities | boundary_predicted_entities | missed_without_overlap | false_positive_without_overlap | multiword_gold | multiword_missed | rare_gold | rare_missed | long_phrase_gold | long_phrase_missed | generic_gold | generic_missed | multiple_aspect_sentences | multiple_aspect_sentences_with_error | sentences_with_error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| validation | 20 | 19 | 20 | 33 | 62 | 134 | 23 | 137 | 39 | 32 | 9 | 1 | 1 | 73 | 31 | 92 |
| test | 97 | 69 | 97 | 46 | 50 | 290 | 77 | 345 | 104 | 75 | 44 | 3 | 0 | 156 | 62 | 137 |

Official test: 77/290 multi-word entities bị miss (26.55%), so với 38/364 unigram (10.44%). Rare/unseen terms miss 104/345 (30.14%), frequent terms miss 11/309 (3.56%). Boundary errors chạm 69/115 gold FN và 97/147 predicted FP. Câu nhiều aspect có lỗi 62/156; long phrases miss 44/75. Các nhóm này có thể chồng lấn và có liên hệ với độ khó, không phải các nguyên nhân nhân quả độc lập.

FN=mọi gold entity không exact-match; FP=mọi predicted entity không exact-match. Boundary pair là một cặp FN/FP có giao ký tự, có thể nhiều-nhiều; không cộng/trừ như taxonomy rời nhau. missed_without_overlap và false_positive_without_overlap tách trường hợp không giao gold/pred nào.

Multi-word dùng >1 whitespace word; rare terminology có frequency<=1 trong **train thực tế2587**, gồm unseen; long_phrase>=3 words chỉ proxy cấu trúc cho cụm phức tạp, không tự xác nhận compound/technical noun phrase bằng người. Multiple-aspect errors dùng mẫu số số câu >1 aspect. Generic nouns system/machine/thing chỉ mô tả nếu có gold; không gán mọi lỗi vào taxonomy hoặc suy ra nguyên nhân semantic. Error examples đầy đủ ở local `{validation,test}_errors.json`, chứa IDs/gold/pred/boundary pairs để truy nguồn.

## 11. Giới hạn

Các phát hiện chỉ dành laptop tiếng Anh. Nhãn đại diện suy từ số sao-nhiễu nhãn vẫn là giới hạn của sentiment P0–P7; **ATE dùng span labels SemEval, không dùng rating proxy**. SemEval-to-Amazon platform/style shift trong laptop review chưa được đo bằng P8. Bộ gold thủ công nhỏ/independent P10 vẫn PENDING; không dùng diagnosis360 để thay ABSA gold.

Giới hạn thêm: nguồn/license NOT_VERIFIED theo ngoại lệ P1; một natural duplicate train/test; whitespace adjustment train có ghi rõ; một seed/một BERT; GPU training best-effort determinism; không đánh giá polarity hoặc end-to-end ABSA. Confidence trả null; API chỉ en và cap128, chưa windowing. Không khẳng định production hoặc tiếng Việt.

## 12. Quyết định nghiệm thu

**P8: DONE — READY FOR P9.** T01–T04 có artifact thật; alignment không lỗi chưa giải thích; validation group-disjoint và official partitions nguyên vẹn với duplicate đã công bố; model fine-tuned/selected từ validation; official test đã đánh giá một lần; metric/error analysis/checkpoint/provenance đầy đủ.

Tests: 350 PASS, 0 FAIL. P0–P7/raw bảo toàn 269 files; canonical metrics/Amazon dataset không đổi. P9 chưa triển khai; dừng tại readiness đã ghi. Chi tiết gates: acceptance.json, independent_evaluation.json, preservation.json, validation.json.

## 13. Artifacts

| artifact | path |
|---|---|
| BIO và split IDs | data/processed/p8_20261026/manifest.json |
| Model/tokenizer/config tốt nhất | artifacts/models/p8_20261026/best/ |
| Last model/optimizer/RNG để resume | artifacts/models/p8_20261026/training_state.pt |
| Config/source identity | reports/p8_20261026/training_identity.json |
| History | reports/p8_20261026/history.json |
| Selection lock | reports/p8_20261026/selection_lock.json |
| Validation/test metrics | reports/p8_20261026/{validation,test}_metrics.json |
| Predictions và full error examples local | data/interim/p8_20261026/{validation,test}_predictions.jsonl |
| Xác minh độc lập | reports/p8_20261026/independent_evaluation.json |
| Bằng chứng test | reports/p8_20261026/validation.json |
| Bảo toàn P0–P7 | reports/p8_20261026/preservation.json |
| Nghiệm thu | reports/p8_20261026/acceptance.json |

Inference API: `from src.absa.extraction import AspectExtractor`; tải thư mục best một lần rồi gọi `extract_aspects(text)`. Output là danh sách term/start/end/score(null); không có aspect trả [], không tạo polarity. CPU inference smoke trên validation đã PASS, không thêm lượt test prediction.

## 14. Tái lập

```powershell
.venv/Scripts/python.exe -B -m scripts.prepare_p8
.venv/Scripts/python.exe -B -m scripts.train_p8
.venv/Scripts/python.exe -B -m scripts.finalize_p8 --run-checks
```

Lệnh train ở trên chỉ dùng khi output chưa tồn tại, **không chạy lại run đã khóa**. Resume run chưa selection bằng `scripts.train_p8 --resume`; identity/config/data/source phải khớp. Sau selection, runner từ chối mở lại test. Để xác minh kết quả hiện tại chỉ chạy prepare_p8 và finalize_p8 (không flag để dùng tests evidence còn khớp source; --run-checks để kiểm suite lại). Để tái tạo training độc lập cần namespace mới trong config trước khi chạy, giữ nguyên hyperparameters/split/seed, công bố best-effort GPU determinism; không overwrite hoặc chọn run theo test.
