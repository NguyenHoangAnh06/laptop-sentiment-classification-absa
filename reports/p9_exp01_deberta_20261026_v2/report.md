# P9-EXP01 — DeBERTa-v3-base ASC

Trạng thái: VERIFIED. Dữ liệu P9 frozen, đổi backbone sang `microsoft/deberta-v3-base`; revision model/tokenizer `8ccc9b6f36199bec6961081d44eb72fb3f7353f3`.

## Protocol và nguồn tham khảo

Tái sử dụng processed P9:1999train/314validation/638official test. Giữ text, offsets, ID, labels, conflict sidecar, đúng occurrence, `[unused0]`/`[unused1]`, single sequence `[CLS] context_before [unused0] target [unused1] context_after [SEP]`, max128; không truncate. Tokenizer native DeBERTa thay WordPiece là thay đổi bắt buộc của backbone, marker IDs128001/128002, resize/save/reload vocabulary128003. Các trường thống kê split BERT kế thừa mô tả nguồn frozen; `marker_ids` và `token_lengths` mô tả cache DeBERTa thực tế (max94/59/87).

Repo https://github.com/ParhamVaryn/transformer-absa-semeval chỉ tham khảo model/range LR; xem `reference.json` có commit. Không lấy code, dataset, normalization, split, sentence pair, focal loss, marker TGT, early stopping hoặc best-of-seeds của repo đó.

Chọn bằng validation Macro F1, tie giữ candidate đầu/epoch sớm; official test chỉ một pass sau selection lock. P8 frozen, không dùng predicted aspects để chọn ASC. Unweighted/balanced như P9, LR3e-5,5epoch,seed42,AdamW,weight decay0.01,warmup0.1; physical batch4×accum4=effective16 so với BERT8×2. Eager attention do kiến trúc DeBERTa; FP32 parameters và FP16 autocast. Không search LR/epoch schedule khác BERT nên đây là so sánh primary config, không khẳng định backbone đã tối ưu toàn cục.

Giữ natural official train/test duplicate và train-only whitespace adjustment đã công bố ở P8/P9; không sửa raw hoặc resplit. Nguồn/license SemEval vẫn NOT_VERIFIED theo ngoại lệ P1, không tải dataset mới từ repo tham khảo. Split thống kê gốc vẫn seed42; seed43/44 chỉ thay khởi tạo/order training, không thay split.

Best: unweighted, epoch5; validation Macro F1=0.777467.

## Validation

| Metric | BERT | DeBERTa | Delta |
|---|---|---|---|
| Macro F1 | 0.714145 | 0.777467 | 0.063322 |
| Accuracy | 0.748408 | 0.808917 | 0.060510 |
| Weighted F1 | 0.753921 | 0.812973 | 0.059052 |
| negative precision | 0.820312 | 0.880952 | 0.060640 |
| negative recall | 0.789474 | 0.834586 | 0.045113 |
| negative f1 | 0.804598 | 0.857143 | 0.052545 |
| neutral precision | 0.479452 | 0.563380 | 0.083928 |
| neutral recall | 0.573770 | 0.655738 | 0.081967 |
| neutral f1 | 0.522388 | 0.606061 | 0.083673 |
| positive precision | 0.840708 | 0.880342 | 0.039634 |
| positive recall | 0.791667 | 0.858333 | 0.066667 |
| positive f1 | 0.815451 | 0.869198 | 0.053748 |

## Official test

| Metric | BERT | DeBERTa | Delta |
|---|---|---|---|
| Macro F1 | 0.748118 | 0.780433 | 0.032315 |
| Accuracy | 0.789969 | 0.815047 | 0.025078 |
| Weighted F1 | 0.785988 | 0.813232 | 0.027244 |
| negative precision | 0.630682 | 0.668571 | 0.037890 |
| negative recall | 0.867188 | 0.914062 | 0.046875 |
| negative f1 | 0.730263 | 0.772277 | 0.042014 |
| neutral precision | 0.758333 | 0.759398 | 0.001065 |
| neutral recall | 0.538462 | 0.597633 | 0.059172 |
| neutral f1 | 0.629758 | 0.668874 | 0.039116 |
| positive precision | 0.883041 | 0.915152 | 0.032111 |
| positive recall | 0.885630 | 0.885630 | 0.000000 |
| positive f1 | 0.884334 | 0.900149 | 0.015815 |

Confusion matrices: `validation_confusion_matrix.csv`, `test_confusion_matrix.csv`; hàng=gold,cột=prediction, thứ tự negative/neutral/positive.

Supplementary loại natural duplicate, chỉ từ saved predictions; không chọn lại model hoặc thay score638mẫu canonical:

| Model | Examples | Excluded | macro_f1 | accuracy | weighted_f1 |
|---|---|---|---|---|---|
| bert | 637 | 1 | 0.747258 | 0.789639 | 0.785553 |
| deberta | 637 | 1 | 0.779698 | 0.814757 | 0.812876 |

## Prediction/error comparison

| Split | fixed | regressed | both_correct | both_wrong |
|---|---|---|---|---|
| validation | 36 | 17 | 218 | 43 |
| test | 49 | 33 | 471 | 85 |

Các file comparison/error_examples chứa review text ở data/interim, chỉ local. `error_comparison.json` dùng đúng taxonomy P9: neutral→negative/positive và đảo positive↔negative từ matrix; negation, mixed polarity, rare aspects, contrast cues, long context proxy. Implicit sentiment và long-distance cause vẫn NOT_MEASURED, không giả tạo human tags. Các nhóm chồng lấn, không coi cues là nguyên nhân xác minh.

## Neutral và weighting

validation: neutral recall 0.573770→0.655738, F1 0.522388→0.606061; neutral→negative=9, neutral→positive=12. Đóng góp delta macro F1 (delta F1 lớp/3): {'negative': 0.0175150519978106, 'neutral': 0.027890848786371197, 'positive': 0.01791588948648763}.

test: neutral recall 0.538462→0.597633, F1 0.629758→0.668874; neutral→negative=43, neutral→positive=25. Đóng góp delta macro F1 (delta F1 lớp/3): {'negative': 0.014004689942678486, 'neutral': 0.013038795572767473, 'positive': 0.005271736640097058}.

| Loss | Epoch | Val Macro F1 | Neutral F1 | Neutral recall |
|---|---|---|---|---|
| unweighted | 5 | 0.777467 | 0.606061 | 0.655738 |
| balanced | 4 | 0.765511 | 0.605263 | 0.754098 |

## End-to-end

| Metric | BERT | DeBERTa | Delta |
|---|---|---|---|
| precision | 0.619403 | 0.644776 | 0.025373 |
| recall | 0.650470 | 0.677116 | 0.026646 |
| f1 | 0.634557 | 0.660550 | 0.025994 |

| Count | BERT | DeBERTa |
|---|---|---|
| extraction_missing_gold_spans | 115 | 115 |
| boundary_gold_spans | 69 | 69 |
| boundary_predicted_spans | 97 | 97 |
| sentiment_errors_on_exact_span | 108 | 91 |
| joint_wrong_span_and_polarity_pairs | 25 | 18 |
| true_positive | 415 | 432 |
| false_positive | 255 | 238 |
| false_negative | 223 | 206 |

Extraction counts được kiểm độc lập không đổi; xem counts/decomposition trong end_to_end_results.json và data/interim. FN=missing extraction+sentiment sai trên exact span; boundary/joint overlap không cộng thành causal fractions.

## Chi phí và sự cố

So sánh latency bổ sung: cùng314validation IDs, CUDA, batch16, FP16, warmup1full pass và3passes đo, medianms/aspect từ tokens; không mở official test:

| Model | Median ms/aspect | Predictions match saved |
|---|---|---|
| bert | 1.016713 | True |
| deberta | 1.806148 | True |

| Measure | BERT | DeBERTa |
|---|---|---|
| training_seconds | 324.129151 | 1861.358178 |
| runtime_seconds_including_checkpoint_io | 346.843756 | 1956.263389 |
| artifact_bytes | 438705553.000000 | 745766987.000000 |
| peak_process_rss_bytes_current_process | 3060903936.000000 | 4868427776.000000 |
| peak_gpu_allocated_bytes | 2264303104.000000 | 3772422144.000000 |
| peak_gpu_reserved_bytes | 2497708032.000000 | 4001366016.000000 |
| inference_ms_per_gold_aspect_from_tokens | 1.064507 | 7.912041 |

Train seconds là tổng loops hai loss×5epoch, không tính validation/checkpoint I/O. Latency là trung bình batched từ tokens (BERT eval batch16, DeBERTa8), không phải latency raw-text/single-request; không quy mọi khác biệt tốc độ cho backbone khi batch khác. Cùng máy GPU và stack Torch/Transformers, không đo tiền compute.

Train loops 1861.358s; wall 1956.263s; selected artifact 745766987bytes; RSS 4868427776bytes; peak GPU allocated/reserved 3772422144/4001366016bytes; latency 7.912ms/gold aspect từ tokens. Versions: {'python': '3.13.12', 'torch': '2.8.0+cu128', 'transformers': '5.0.0'}. GPU: NVIDIA GeForce RTX 4050 Laptop GPU. Tiền compute NOT_MEASURED.

Namespace cũ `p9_exp01_deberta_20261026` INVALID_FOR_COMPARISON, không dùng bất kỳ score nào: initial attempt dừng trước epoch hoàn tất/test do FP16 parameters không hợp GradScaler; sửa explicit float32 parameters. Sau đó phát hiện Transformers5 conversion thiếu CLS/SEP, dừng trước selection/test, giữ toàn bộ checkpoint/logs; tokenizer v2 khôi phục post_processor CLS/SEP chuẩn và restart pretrained. Không đổi representation P9 frozen. Xem attempts.json và invalid_attempt.json của namespace cũ. Tokenizer cần sentencepiece0.2.1/protobuf6.33.5, không đổi Transformers/PyTorch.

Seed43 bị turn interruption giữa epoch5. Resume bị chặn trước train/test vì nhánh resume lấy vocab128100 từ pretrained thay vì vocab128003 đã resize; không đổi trainer/source sau primary. Giữ attempt bị ngắt, chạy seed43 lại hoàn toàn từ pretrained trong namespace `_seed43_restart01`. Chỉ completed restart được dùng trong stability. Resume DeBERTa hiện NOT_SUPPORTED, fresh-run/reload đã xác minh; xem resume_event.json và logs. Tổng chi phí mọi attempt bị ngắt/lỗi NOT_MEASURED, không gộp giả vào primary/stability runtime.

## Stability validation — tách khỏi canonical comparison

| Seed | Val Macro F1 | Epoch |
|---|---|---|
| 42 | 0.777467 | 5 |
| 43 | 0.767943 | 4 |
| 44 | 0.754664 | 3 |

Mean=0.766691, sample std=0.011453. Cùng best loss/LR/max-epochs và checkpoint rule; không chọn seed tốt nhất, không thay seed42 bằng mean hoặc seed43/44, không mở official test của stability. BERT chưa có multi-seed tương đương nên đây không phải so sánh hai multi-seed means.

## Quyết định canonical và giới hạn

Validation delta Macro F1=+0.063322; quyết định canonical ghi tại canonical_decision.json sau xem bằng chứng validation, không dùng official test hoặc joint F1 để chọn.

Trạng thái quyết định: `PROMOTED`. Validation Macro F1 tăng0,063322; F1 cả3lớp validation tăng, neutralF1 tăng0,083673. Seed43/44 hỗ trợ độ ổn định; giữ primary seed42, không chọn theo test/joint hoặc best seed.

Single-seed primary comparison; stability ghi riêng nếu có, không thay trực tiếp single-seed baseline bằng multi-seed mean. Không khẳng định ưu thế thống kê. Chỉ laptop tiếng Anh; nhãn Amazon đại diện suy từ số sao có nhiễu; SemEval-to-Amazon platform/style shift chưa đo; bộ gold người chú thích nhỏ P10 vẫn PENDING. Confidence null; chưa production/tiếng Việt. Không triển khai P10.

## Tái lập

Previous canonical BERT được giữ nguyên artifacts và có snapshot11source files tại previous_canonical_source/, khớp chính xác SHA256 validation/training identity frozen. Đây là archive provenance, không phải pipeline active thứ hai; snapshot được khôi phục bằng đảo các edit của tác vụ và chỉ chấp nhận bytes khớp hash frozen.

CPU classifier + raw P8→ASC pipeline smoke PASS trên validation (inference_smoke.json), kiểm labels/confidence/empty aspects/unsupported vi, không mở test. Latency bổ sung dùng benchmark_validation_latency.py; lượt đầu chồng CPU smoke được giữ riêng, số báo cáo là lượt chạy riêng sau khi cả hai process kết thúc.

`.venv/Scripts/python.exe -X utf8 -m scripts.p9_exp01 prepare` rồi `train` chỉ cho namespace chưa chạy; completed training bị khóa. Xác minh từ saved predictions: `.venv/Scripts/python.exe -X utf8 -m scripts.finalize_p9_exp01 --run-checks`. Không chạy finalizer P9 cũ để ghi đè frozen evidence.

Tests: 380 PASS; frozen artifact checks: 381 files giữ hash.
