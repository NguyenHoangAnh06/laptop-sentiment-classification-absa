# P4 — cố định phân chia, rò rỉ dữ liệu và Báo cáo tiền xử lý

Ngày2026-10-09. **P4 hoàn thành: P4-T01–T05.** đầu vào P2 cố định30.000 review/ 9.080products; P0–P3 không chạy lại hoặc thay các tệp kết quả. P5 trở đi NOT RUN. P1 vẫn hoàn thành bằng phê duyệt/ngoại lệ; SemEval nguồn/giấy phép **NOT_VERIFIED** theo ngoại lệ dự án học tập. Không tải lại/re-audit SemEval, không biến ngoại lệ thành giấy phép PASS.

## PLAN, phụ thuộc và phạm vi

Đã đọc đầy đủ AGENTS, hai PLAN, handoff, P2/P3 bằng chứng và dữ liệu contracts. P4 nguyên văn quy định70/15/15, stratify cảm xúc, cố định hạt giống ngẫu nhiên, duplicate/product rò rỉ dữ liệu, group phân chia, TF-IDF chỉ trên tập huấn luyện, minimal BERT cleaning/tokenizer và observed độ dài policy. hiện có configs/data.yaml chốt hạt giống ngẫu nhiên42 và tỷ lệ. Group-aware có thể ưu tiên trên strict stratification khi cần chống rò rỉ dữ liệu theo AGENTS; ở bộ dữ liệu hiện tại đạt **đồng thời grouping và integer lớp targets**, không cần ngoại lệ mới.

Thứ tự thực thi: bind input/holdouts → leakage/group constraints → seeded assignment → validation/persist/replay → TF-IDF tập huấn luyện fit/frozen transforms → đã huấn luyện trước bộ tách token → chỉ trên tập huấn luyện độ dài rule → token đặc trưng persistence/reload → checksum/report. Chỉ TF-IDF/vocabulary/IDF học từ tập huấn luyện. Không classifier, mô hình lựa chọn, resampler, lớp weights, scaler, đặc trưng lựa chọn, PyTorch dataset/collator hoặc huấn luyện run.

| Nhiệm vụ theo PLAN | Trạng thái | Bằng chứng |
|---|---|---|
| P4-T01 fixed70/15/15 + stratification/seed | DONE |21.000/4.500/4.500; hạn ngạch lớp số nguyên, hạt giống ngẫu nhiên42 trong bản kê |
| Phân tích P4-T02 leakage/group | DONE, từ vựng giới hạn phạm vi | Exact/normalized/classical-text/parent/asin/components overlap0; QA/noise guards; near limits dưới đây |
| P4-T03 vẫn tồn tại train/validation/test | DONE |Tệp sàn gỗ 3 + băm assignments.csv + manifest/source/output; phát lại giống hệt byte |
| P4-T04 cổ điển preprocessing/TF-IDF | DONE |Bộ vector hóa được trang bị chỉ trên tập huấn luyện thực tế, ma trận thưa thớt 3, tải lại đã cố định + kiểm tra IDF số độc lập |
| P4-T05 tối thiểu BERT/tokenizer/length | DONE |Chính sách đã huấn luyện trước bộ tách token, tập huấn luyện p95 được ghim thực tế, sàn gỗ đặc trưng được mã hóa 3, mã hóa lại mảng đã lưu đầy đủ PASS |

## Chiến lược phân chia, sự đánh đổi và tính toán

`src/data/split.py`: connected grouping theo parent_asin/variant asin, exact, normalized, classical-preprocessed văn bản và accepted gần trùng edges; không chia component sang nhiều tập. Group ID là SHA256(sorted nguồn IDs). Sort groups size-descending + hạt giống ngẫu nhiên42 hàm băm; greedy weighted squared class-mục tiêu deficits, không search nhiều seeds/đánh giá các mô hình. Integer quotas dùng largest remainder và giữ cả total/class margins. chạy lại đảo đầu vào order cho cùng membership.

9.080components, largest100reviews;0capacity fallback groups,0exclusions. Các near/variant edges không nối thêm parent groups ở thực tế bộ dữ liệu. Tất cả30k hàng được phân bổ đúng một tập, không thêm nguồn ngoài P2. Không sửa P2 hoặc nhãn đại diện.

| phân chia | review | Sản phẩm | Tiêu cực | trung tính | tích cực |
|---|---:|---:|---:|---:|---:|
| tập huấn luyện |21.000 |6.357 |5.781(27,529%) |1.842(8,771%) |13.377(63,700%) |
| tập xác thực |4.500 |1.361 |1.239(27,533%) |395(8,778%) |2.866(63,689%) |
| kiểm thử |4.500 |1.362 |1.239(27,533%) |394(8,756%) |2.867(63,711%) |

Global đại diện distribution27,53%/8,77%/63,70%; largest deviation do integer rounding khoảng0,01445 percentage point. Không undersample/oversample hoặc cân quota brand. Grouping cho đánh giá trên unseen parent sản phẩm, chặt hơn không trùng review giữa các tập ngẫu nhiên phân chia. Đổi lại kiểm thử không đại diện market share/chronological deployment/brand-fairness; không trùng sản phẩm giữa các tập không đồng nghĩa brand-disjoint hoặc user-disjoint. Nếu dữ liệu khác không khớp mô hình lớp capacities, splitter báo thực tế deviations; rỗng phân chia hoặc độ bao phủ lớp failure sẽ fail tập xác thực, không giả hoàn thành. dữ liệu mẫu kiểm tra những cases đó.

## Báo cáo rò rỉ dữ liệu

`reports/p4/p4_20261009_final/validation.json` và `reload_validation.json`:

- ID review, `text` chính xác, hàm băm đã được làm sạch, văn bản HTML/whitespace/casefold được chuẩn hóa,
  văn bản được xử lý trước cổ điển: chồng chéo phân chia0.
- parent_asin, asin và split_group_id được kết nối: chéo phân chia chồng chéo0.
- Near phạm vi mới P4:30k nguồn +1.518 QA/diagnostic holdout texts; tái sử dụng hiện có
  `src/data/near_duplicates.py`/P2-approved32MinHash,8bands×4, shingle Jaccard>=.90. 36candidate comparisons,0pairs, comparison cap100k không reached. Không semantic/ exhaustive gần trùng bằng chứng xác nhận; ngắn<10word texts bị skip, LSH có thể miss pairs. Nếu có pair withinP2 thì cùng connected group; holdout-connected văn bản clusters sẽ bị exclude khỏi derived các tập đã chia có lý do, không mutate P2.
- Nguồn QA IDs/text0, dành riêng250chẩn đoán cặp IDs/text0, giữ-gần0.
  con người QA labels/private predictions không được dùng làm cảm xúc huấn luyện targets.
- QA sản phẩm overlaps177train/40validation/39test được ghi **chẩn đoán**, không0:
  P1 product-phạm vi QA khác sentiment/ABSA gold; reserve actualQA IDs/text clusters nhưng không blanket-remove mọi review cùng QA product. Chính sách P2 giữ nguyên.
- User giao nhau tập huấn luyện–validation35/train–test37/validation–kiểm thử6. User IDs không là
  predictor, user-disjoint không là hiện tại nghiệm thu rule; future unseen-user claims không được hỗ trợ. Không coi những số lượng này là sản phẩm rò rỉ dữ liệu PASS tuyệt đối.
- P10 con người sentiment/ABSA gold **chưa tồn tại**. Không claim gold contamination
  đã measured0; future gold phải lấy độc lập held-out/new review, disjoint huấn luyện IDs/text/components. Không tạo sample/annotation P10 ở P4.
- Xếp hạng, ID sentiment/label bắt nguồn từ xếp hạng, nguồn IDs/line, product/brand/title,
  helpfulness, verified_purchase, độ dài flags và siêu dữ liệu **không là predictor**. đặc trưng allowlist chỉ `text`; label_id lưu riêng làm mục tiêu. văn bản có mô tả star rating tự nhiên không bị sửa, nhãn đại diện nhiễu vẫn còn.
- TF-IDF vocabulary/IDF khớp mô hình đúng21k tập huấn luyện IDs; độc lập bộ kiểm tra reconstructs
  smooth IDF=`log((1+n_train)/(1+train_df))+1` từ huấn luyện document frequencies. Validation/test chỉ transform bằng tệp kết quả đã đã cố định. Không khớp mô hình scaler/resampler.
- bộ tách token là cố định đã huấn luyện trước WordPiece, không học vocab từ corpus dự án. độ dài
  được chọn từ tập huấn luyện IDs/distribution rồi đã cố định trước heldout tách token. Các heldout truncation stats chỉ chẩn đoán, không dùng đổi threshold/model/max_length.
- P3 đã descriptive EDA toàn corpus trước splitting; kiểm thử không được gọi là văn bản
  chưa từng được xem. Từ P4 onward kiểm thử bị cố định cho cuối cùng đánh giá, không dùng EDA lexical tables/test nhãn để supervised đặc trưng selection/tuning/model choice.

## Classical tiền xử lý thực tế

`src/preprocessing/english.py`: tái sử dụng P2 conservative HTML/entities/whitespace làm sạch, retain raw text/case/punctuation/negation trước mô hình-specific transform. Idempotent trên thực tế P2 đầu vào; source/split văn bản và raw_text luôn nguyên giá trị. Classical thêm lowercasing và curly-apostrophe chuẩn hóa cố định; không stopword deletion/stemming/lemmatization. token regex giữ contractions, punctuation và emoji; `not`, `never`, `no`, `don't`, `!` có tests. Mọi inference/validation/test đi qua cùng text-only selector/normalizer/frozen vectorizer.

thực tế TF-IDF: unigram+bigram,min_df2,max_features30k,sublinear_tf=true,smooth_idf, float32, vocabulary **30.000**. cấu hình ban đầu để P5 so sánh, không tối ưu theo kiểm thử. tập huấn luyện matrix21000×30000,nnz2523532; tập xác thực4500×30000,nnz533343; kiểm thử4500×30000,nnz529003. tệp kết quả `tfidf.joblib` là tiền xử lý, **không classifier**. tải lại và full-dữ liệu retransform bằng saved tệp kết quả khớp tất cả matrices. khớp mô hình wrapper từ chối mixed/validation/test frames hoặc refit sau đã cố định; khớp mô hình ID hàm băm lưu trong preprocessing.json. P5 có thể tune tiền xử lý trên train/validation đúng PLAN, không refit trên tập huấn luyện+validation/test trước cuối cùng cố định-kiểm thử comparison.

## BERT tiền xử lý thực tế

[HF mô hình card](https://huggingface.co/google-bert/bert-base-uncased) công bố Apache-2.0; chỉ tải tokenizer.json/config.json ở revision `86b5e0934494bd15c9632b12f734a8a67f723594`, lưu URL/bytes/SHA256. Không mô hình weights/PyTorch/Transformer trainer hoặc tinh chỉnh. Đây không là tìm lại SemEval license. Sử dụng [Tokenizers API](https://huggingface.co/docs/tokenizers/api/tokenizer) để encode/reload tệp kết quả locally; không tập huấn luyện bộ tách token từ laptop corpus.

External làm sạch minimal, không lowercase trước bộ tách token, không stemming/stopword removal. BERT **uncased đã huấn luyện trước normalizer** tự lowercase/strip accent/handle controls theo bộ tách token gốc; cấu hình nguyên bản ghi trong preprocessing.json. Không tuyên bố case/accents còn nguyên trong token IDs. Punctuation/negation không bị xóa bởi external cleaner. CLS/SEP/type IDs/masks và lengths được validate.

tập huấn luyện token lengths (gồmCLS/SEP): p50=54,p90=255,p95=390,p99≈834,01,max4154. Rule: nhỏ nhất trong128/256/384/512 cover p95, bounded mô hình context512 → **512**. 384 chưa cover390;512 có compute chi phí cao hơn256/384, nhưng đạt rulecoverage đã chọn từ tập huấn luyện mà không xem validation/test performance. Right truncation; saved đặc trưng không padding, môi trường chạy dynamic longest-in-lô padding có API/tests.

| phân chia | review bị cắt ngắn | Tỷ lệ | Đã lưu token |
|---|---:|---:|---:|
| tập huấn luyện |654 |3,114% |2.099.010 |
| tập xác thực |141 |3,133% |446.227 |
| kiểm thử |137 |3,044% |438.424 |

Truncation có thể bỏ late mixed opinions/aspects; P6 phải giữ policy và báo impact, không giả định toàn review đã được mô hình đọc. Không xử lý/chuyển độ lệch ký tự SemEval ở P4; raw/XML/JSONL/original huấn luyện/kiểm thử không đổi. Future P8 cần span/subword căn chỉnh, P9 cần khía cạnh-context adapters; token đặc trưng P4 là Amazon **overall cảm xúc**.

## các tệp kết quả và khả năng tái tạo

- `data/processed/splits/p4_20261009_final/{train,validation,test}.parquet`:
  toàn bộ các trường P2 +split/split_group_id; nguồn đầy đủ equality/schema tập xác thực PASS.
- `reports/p4/p4_20261009_final/`: bản kê, bài tập, loại trừ (sổ cái lý do trống),
  label_distribution,near_pairs,leakage_report,tập xác thực,reload_validation,input_preservation, environment/task_validation. bản kê binds source/version/config/implementation/ phân chia+đặc trưng hàm băm; hạt giống ngẫu nhiên42, role/fit IDs và bounds lưu rõ.
- Ma trận `artifacts/preprocessing/p4_20261009_final/`: tfidf.joblib,3NPZ,
  đã đặt hàng xe sidecar đặc trưng-hàng mục tiêu,preprocessing.json,bert original/configured tokenizer/config.
- `data/processed/features/p4_20261009_final/{train,validation,test}_bert.parquet`:
  review_id/label_id/split +input_ids/attention_mask/token_type_ids. Chỉ3arrays là BERT mô hình đầu vào; review_id/split/label_id là bookkeeping/target.
- New downstream contract: `docs/P4_DATA_CONTRACT.md`. Không sửa đã hoàn thành dictionary,
  P2/P3 reports/notebook/provenance; dated báo cáo là state snapshots của chặng đó.

Membership chạy lại từ đầu vào reversed PASS;3split parquet **byte-identical**. Ordered đặc trưng-row căn chỉnh và all TF-IDF values/BERT arrays reloaded/recomputed PASS. P4 đầu ra footprint48.127.680bytes (bản kê-bound files, chưa tính report/env extensions). Runtime107,1615s; peak459.124.736bytes <512.000.000. Initial một phần lần chạy chạm working-set giới hạn trong BERT stage; giữ tại p4_20261009/ với trạng thái INCOMPLETE/SUPERSEDED, không có đã hoàn thành bản kê. Đã bỏ references không cần, bộ tách token nativeparallelism false và lengths sequential; cuối cùng mới lần chạy dưới ceiling. Không tăng RAM/time giới hạn tài nguyên, không tải lại Amazon/SemEval hoặc rerunP1/P2/P3 transformations/annotations.

## Kiểm tra và chấp nhận

**180tests passed in10.29s**, gồm11P4synthetic dữ liệu mẫu kiểm thử; `pip check` PASS. dữ liệu mẫu kiểm tra exact quotas/margins, input-order khả năng tái lập, product/variant/ normalized/near components, infeasible grouping/empty-split failures, foreign hàng, holdout propagation, raw văn bản equality, negation/punctuation/OOV, chỉ trên tập huấn luyện TF-IDF, IDF frozen/reload, bộ tách token padding/truncation/CLSSEP/length policy. Không giả con người gán nhãn, classifier đánh giá hoặc đánh giá so sánh bằng fixtures.

Production độc lập tập xác thực PASS: schema/30kconservation/labels, zero required thiếu, đã cố định assignment/hash chạy lại, group isolation, QA/noise contamination, train-ID/IDF audit, every đặc trưng record căn chỉnh, all TF-IDF/BERT retransform, **41protected checksums PASS**; bản chụp trạng thái tổng121completed-input hàm băm unchanged. 121 là total bản chụp trạng thái gồm41, không phải121+41. License/source remains NOT_VERIFIED.

P4 nghiệm thu: **hoàn thành**, không thiếu tác vụ hoặc BLOCKED hiện hành. Statistical limits không được đổi thành đã đo chất lượng rates: approximate near search, đại diện nhiễu, coverage89,08%/joint95%CI55,46–99,85%, assisted-QA independence/selection bias, user giao nhau, truncation và gold absent được công bố, không tạo gate/threshold mới. Giữ **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (P10 con người sentiment/ABSA gold chưa có).

NEXT_ACTION đúng PLAN: **P5-E00 majority mô hình cơ sở rồi P5-E01 LR/P5-E02 LinearSVM/ P5-E03 DecisionTree**, tập huấn luyện bằng đã cố định train/features, tunevalidation, fixedtest cuối cùng metrics/compute comparison. **P5 NOT STARTED** trong tác vụ P4-only hiện tại.

```powershell
.\.venv\Scripts\python.exe -B -m scripts.prepare_p4
.\.venv\Scripts\python.exe -B -m scripts.validate_p4 --output reports/p4/p4_20261009_final/NEW_VALIDATION.json
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
```

Prepare refuses hiện có đầu ra; chạy lại phải dùng cấu hình copy có output_suffix mới. tập xác thực chỉ đọc hiện có các tệp kết quả, không fit/split lại vào dữ liệu files. đã ghim phiên bản P4 SciPy1.18.1 yêu cầuPython>=3.12; thực tế environmentPython3.13.12/Windows được verify, chưa claim mới Python3.11setup. Classifier/model hiệu năng NOT_MEASURED.
