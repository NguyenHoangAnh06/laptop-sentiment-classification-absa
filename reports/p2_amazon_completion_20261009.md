# Nhãn làm sạch chất lượng P2 Amazon dữ liệu

Ngày 2026-10-09, Asia/Saigon. **P2 Amazon-only deliverables COMPLETE theo ngoại lệ C4-B đã được owner phê duyệt. P1 chưa hoàn thành; authorized SemEval nguồn/giấy phép BLOCKED.** Không triển khai P3/P4/training; không tạo huấn luyện/xác thực/kiểm thử các tập đã chia hoặc bộ gold do con người gán nhãn. phạm vi vẫn được chọn laptop tập ứng viên, không đầy đủ laptop universe. độ bao phủ (recall)89.0767%, joint95% CI55.4584–99.8455%, lựa chọn bias và assisted-QA independence limits giữ nguyên.

## Phê duyệt và các tệp kết quả

C1-A/C2-A/C3-A/C4-B đã phê duyệt trong `tables/p1_owner_approval_20261009.json`. C2 chỉ chấp nhận assisted con người QA cho phạm vi filter P1, không thay đổi độc lập của gold P10. Không sửa nguồn nhãn, canonical mapping hoặc criteria/license SemEval.

- bộ dữ liệu: `data/processed/laptop_reviews.parquet`, **30,000 review**,15,767,926byte.
- Manifest/config/ledger: `data/interim/p2/20261009_final/manifest.json`,
  `candidate_ledger.sqlite` và `configs/p2.yaml`.
- nhãn-nhiễu worklist:250 **unannotated chẩn đoán các ứng viên** tại
  `data/interim/p2/20261009_final/label_noise_candidates.csv` và `.parquet`.
- Quality/brand/label tập xác thực: `tables/p2_amazon_20261009_final/validation.json`,
  `brand_before_after.csv`, `label_distribution.csv`.
- Các mô-đun có thể tái sử dụng: `src/data/cleaning.py`, `labeling.py`, `near_duplicates.py`,
  `p2_pipeline.py`; CLI `scripts/prepare_p2_amazon.py`, `report_p2_amazon.py`.

## Bằng chứng nhiệm vụ P2

| Nhiệm vụ | Trạng thái | Bằng chứng |
|---|---|---|
| Thiếu P2-T01 | DONE, nhóm hợp lệ đã lưu | tái sử dụng prior required/optional missing0 audit; handling policy below; không audit raw Amazon lần nữa |
| P2-T02 invalid/short | DONE | Bảo vệ type/rating/ID/metadata rõ ràng, cách ly trống; Số lượng before/after, các văn bản ngắn được giữ lại khi cổng ngôn ngữ đi qua |
| Bản sao P2-T03 | DONE, từ vựng phạm vi | Kiểm toán Exact/normalized được sử dụng lại; kiểm tra dedup/cross-product/user làm sạch lần cuối; tìm kiếm gần như trùng lặp được giới hạn được ghi lại bên dưới |
| Bộ lọc P2-T04 QA | DONE được chấp nhận C1/C2 | Tái sử dụng QA đã được xác minh con người: GIỮ ngẫu nhiên không có FP được quan sát; không có phụ kiện đi kèm nào được biết đến để loại bỏ, không loại bỏ chính sách phạm vi; không yêu cầu bồi thường không có ô nhiễm tử thi |
| Làm sạch P2-T05 | DONE | HTML/entities/word boundaries/whitespace; văn bản gốc được giữ lại; Các URL hiển thị trong văn bản được giữ lại; negation/case/punctuation được bảo quản |
| Proxy xếp hạng P2-T06 | DONE |1–2 negative/3 neutral/4–5 positive; ổn định IDs0/1/2, tải lại tập xác thực, counts/percentages |
| Ứng viên P2-T07 nhiễu | DONE | Đã lưu 250 thí sinh có lý do, không có con người nhãn; Đặt trước ID/text/near-cluster từ dữ liệu đã xử lý |
| Mất cân bằng P2-T08 | DONE | Tỷ lệ và chính sách cuối cùng: đảm bảo so sánh trọng lượng hạng sau, lựa chọn chỉ trên tập huấn luyện weights/validation; không có phụ kiện weights/resampling/model hiện tại |
| P2-T09 đã xử lý bộ dữ liệu | DONE |30k rows/9080 products/3classes, SHA256/row conservation/contract PASS; mục tiêu đã đáp ứng mà không cần thêm các sản phẩm không phải laptop |

hoàn thành không có nghĩa đã đo true semantic bản trùng, true language error/spam hoặc rating-vs-con người disagreement. Những uncertainty đó được giữ như limitations; không lấy rule/cue score làm con người gán nhãn hoặc mô hình đánh giá so sánh.

## Báo cáo chất lượng dữ liệu và sổ cái đếm hàng

đầu vào saved408,480 các ứng viên đã có audit/hash; chỉ đọc saved tập ứng viên để transform, không download hoặc scan lại44million raw review. Required/optional missing0 là thông tin valid tập ứng viên, không toàn raw/260 selected-invalid records của P1. Invalid required/rating -> quarantine; rỗng cleaned -> quarantine; optional null giữ null; không xóa ngắn review chỉ theo từ count. Malformed JSON/duplicate ID fail rõ thay vì silently skip source. Unicode replacement văn bản quarantine có reason.

| Bố trí sân khấu độc quyền | Hàng |
|---|---:|
| Cụm QA ID/text được đặt trước |8,406 |
| Kiểm dịch thay thế Unicode |4 |
| Các nhóm văn bản nhãn đại diện xung đột đã được cách ly hoàn toàn |4,621 |
| Same-nhãn đại diện đã loại bỏ phần dư thừa trùng lặp được chuẩn hóa |15,439 |
| Các nhóm được làm sạch duy nhất đủ điều kiện |380,010 |
| **Tổng đầu vào** |**408,480** |

Sum đúng đầu vào; không cộng repeated flags vào ledger như exclusions. Grouping theo SHA256(cleaned văn bản casefolded), giữ first saved-source hàng khi cảm xúc đại diện consistent; nếu lớp conflict thì quarantine toàn group, không chọn rating thuận lợi hoặc tự sửa label.4/5 cùng positive và1/2 cùng negative không phải lớp conflict.3,066 consistent groups cross-product và2,537 cross-user được ghi trong bản kê; before-clean raw/normalized trùng lặp số lượng vẫn ở audit cũ.

162,648 texts thay đổi bởi normalization. làm sạch dùng HTMLParser cho recognized tags, giữ text/word boundaries, decode entities trước parse, giữ unknown tags/ comparisons thay vì broad regex xóa content. gốc `raw_text` luôn lưu riêng. Visible URLs giữ nguyên; anchor markup/href không trở thành review content. Không stemming, stopword deletion, lowercasing cuối cùng văn bản hoặc xóa negation. Không áp char độ lệch ký tự từ raw sang sạch; gán nhãn ABSA sau này phải chỉ rõ văn bản version và validate độ lệch ký tự trên version đó.

Spam-like audit:1,404 repeated-character flags,95 promotional-phrase flags, 1 low-lexical-diversity flag; heuristic flags không chứng minh spam. Quarantine chỉ áp composite suspicious patterns/script-style; thực tế đầu vào không có hàng thỏa composite rule. cuối cùng giữ123 repeated-character flags,8 promotional cues,1 low diversity flag và65 visible-URL review. Low-diversity case là repeated complaint warning về defective sản phẩm; machine inspection không biến nó thành con người nhãn. Giữ cảm xúc-bearing repetitions với flags; không cắt/xóa để làm review đẹp hơn. False-positive/false-negative rate của spam heuristics NOT_MEASURED.

siêu dữ liệu anomaly bằng chứng đã tái sử dụng:0 rỗng titles,664 metadata/title disagreement sản phẩm; UNKNOWN/AMBIGUOUS retained. Không fuzzy-merge, sửa manufacturer hoặc relabel laptop theo review/star. phạm vi filter không đổi, không restore rejected FN.

## Lựa chọn và lấy mẫu tiếng Anh

hạt giống ngẫu nhiên42 SHA256(review_id) rank, độc lập of rating/brand/model prediction, trên cleaned eligible unique groups. Assess **36,000**, trong đó33,483 passed tiếng Anh các điều kiện nghiệm thu,2,517 uncertain/non-English; **344,010 eligible groups chưa được language-assessed**. Không gọi2,517 là non-tiếng Anh prevalence toàn corpus hoặc 30k được chọn là thực tế sạch yield của tất cả408k review.

Lingua2.1.1 offline, all75 languages, low-tỷ lệ dự đoán đúng (accuracy) mode; tiếng Anh detector score>=0.90, top language margin>=0.20, ASCII-letter share>=0.98. Đây là conservative configurable lựa chọn heuristics, không đã phê duyệt QA tỷ lệ dự đoán đúng (accuracy) threshold hoặc calibrated probability. Mixed-language/technical jargon/short-text lỗi vẫn có thể xảy ra; true language lỗi rate NOT_MEASURED. Detector scores canonical round8decimals để tránh variation floating-point parallel reductions. Không fine-tune/train một mô hình language/sentiment. Implementation/version/seed/source hàm băm và policy được lưu để tái lập. Primary library documentation: [Lingua v2.1.1](https://github.com/pemistahl/lingua-py/blob/v2.1.1/README.md).

Reserve chẩn đoán các ứng viên trước cuối cùng lựa chọn; cap100 reviews/product được tái sử dụng từ lấy mẫu policy;1,412 giới hạn skips trước đạt mục tiêu. Không quota brand/rating, không bù quota bằng review không qua chất lượng gate. cuối cùng có9,080 sản phẩm, 181 siêu dữ liệu thương hiệu categories;424 review dưới5 whitespace từ vẫn giữ. Không thiết lập max BERT length/tokenizer statistics hoặc vectorizer trong P2.

## Sẵn sàng rò rỉ dữ liệu trùng lặp

Normalized cuối cùng hàm băm và review IDs unique; QA ID/text overlap0 và nhiễu chẩn đoán ID/text overlap0. Chỉ reserve QA IDs/text clusters, không xóa65,983 sản phẩm matches của conservative không trùng sản phẩm giữa các tập scenario trước. Không sử dụng QA con người nhãn làm cảm xúc huấn luyện nhãn. sản phẩm giao nhau với QA không được gọi là phân chia rò rỉ dữ liệu vì chưa có các tập đã chia và phạm vi QA khác cảm xúc gold.

Lexical near audit trên30k cuối cùng +250 dành riêng chẩn đoán:32 stable uint64 MinHash components,8 bands x4, exact hashed word-triple Jaccard>=0.90;34 ứng viên comparisons, 0 đã xác minh threshold pairs, không chạm comparison cap. ngắn<10word skipped; approximate search có thể bỏ sót, không bằng chứng xác nhận semantic duplicate-free. Không tự xóa pair khác sentiment/negation; nếu pair có, retain group IDs cho P4. Punctuation ứng viên clusters từ toàn bộ preflight không bị coi là semantic evidence. Không tạo train/validation/test. P4 vẫn phải thực hiện leakage/group checks riêng.

## Báo cáo mất cân bằng phân phối và lớp nhãn

| đại diện cảm xúc | ID | review | Tỷ lệ phần trăm |
|---|---:|---:|---:|
| negative |0 |8,259 |27.53% |
| neutral |1 |2,631 |8.77% |
| positive |2 |19,110 |63.70% |

Nhãn là **nhãn đại diện suy từ số sao**, không con người nhãn chuẩn. Largest/minority ratio7.2634, trước pool8.32. Neutral có2631 hàng và9080 sản phẩm tổng thể, đủ cơ sở tiếp tục đánh giá dưới phạm vi được chọn tập ứng viên; chưa hứa độ bao phủ lớp của future không trùng sản phẩm giữa các tập các tập đã chia. Không cân bằng artificial hoặc lọc theo mô hình outputs. mất cân bằng đủ lớn để so sánh unweighted/class-weighted baselines ở P5 và weighted hàm mất mát ở P6. Weights chỉ khớp mô hình trên tập huấn luyện khi P4 tồn tại, chọn trên tập xác thực, macro F1 primary; không khớp mô hình resampler/vectorizer/train statistics trên whole đã xử lý dữ liệu.

## Danh sách công việc nhiễu nhãn

250 unique chẩn đoán các ứng viên, không phải gold hoặc đã đo nhiễu rate. lý do counts100 five-star negative/mixed cues,103 low-star positive/mixed cues, 51 low-star neutral cues; sum254 vì một số hàng có nhiều reason. Phrase/negation cues có thể false positive; mixed review có thể hợp lý ở bất kỳ rating. Không overwrite ratings/proxy nhãn. Worklist lưu nguồn ID/raw/clean văn bản, rating/proxy/reasons và `UNANNOTATED_DIAGNOSTIC_NOT_GOLD`, không sinh con người nhãn. Các các ứng viên đã được reserve khỏi đã xử lý bộ dữ liệu; near cluster overlap0. Đây là chẩn đoán queue cho annotation/noise analysis sau này, không representative 300–500 P10 gold. P10 độc lập sampling/blinding/human verification vẫn bắt buộc; không dùng worklist có rating/proxy hiển thị để giả danh mù gold. true rating-text disagreement/agreement rate NOT_MEASURED.

## thương hiệu diversity trước và sau P2

| Đo lường | Ứng viên trước | Được chọn sau |
|---|---:|---:|
| review |408,480 |30,000 |
| Sản phẩm |28,172 đã chọn /28,161 với review hợp lệ |9,080 |
| Danh mục siêu dữ liệu |336 |181 |
| Chia sẻ Top5 review |79.7731% |79.4567% |
| Chia sẻ UNKNOWN/AMBIGUOUS review |0.3195% |0.2667% |

155 absent categories chứa693 ứng viên review, **0.1697%** tập ứng viên, không bằng 46% review lost: category số lượng và population share khác nhau. thương hiệu names là siêu dữ liệu categories, không đã xác minh manufacturers. No equal quota/leading-brand whitelist. UNKNOWN/AMBIGUOUS không bị loại riêng vì thiếu brand. ASUS share tăng0.69pp; Acer giảm1.47pp; HP giảm0.12pp; Samsung giảm0.80pp. Chênh lệch do tổng hợp cleaning/quarantine/QA reservations/language/sample/product cap/diagnostic reservations, **không quy hết cho làm sạch**. Đây không phải market representativeness hoặc đã đo mô hình fairness/brand bias. Long-tail subgroup thước đo cần số mẫu hỗ trợ checks sau này; macro F1 lớp không tự cân bằng brands. Full336-category trước/sau review và sản phẩm bảng tại `brand_before_after.csv`.

## tập xác thực và giới hạn

đã xác minh toàn bộ suite **161 passed in4.67s (cuối cùng check after documentation/config updates)**; targeted18 kiểm thử PASS. dữ liệu mẫu integration thực thi offline detector, nguồn ledger, parquet tải lại và hai lần chạy byte-identical; kiểm thử cover rating1–5/bool rejection/negation/HTML boundaries/encoded tags/QA/dedup/ mixed labels/diagnostic reservations/near groups/no-overwrite. tổng hợp dữ liệu mẫu không là thực tế reviews/human nhãn. `pip check` PASS.

Production verification:41 được bảo vệ checksums PASS; raw/annotations/configs acquisition/ feasibility unchanged. đầu vào byte không đổi, hàng conservation, parquet unique IDs/ văn bản hàm băm, cố định nhãn IDs, negation-preserving raw-to-clean match, no QA/noise giao nhau, no residual recognized HTML tags PASS. cuối cùng bộ dữ liệu hash/implementation fingerprints/manifest links được lưu. New config/dependencies chỉ for P2, no ML stack.

đã đo cuối cùng run86.4251s; peak working set441,520,128bytes (<512,000,000). SQLite ledger1,074,966,528bytes, below2GB đầu ra giới hạn; ledger plus đầu ra remains under per-run2GB. Initial tập xác thực lần chạy phát hiện tiny floating-point score variation và one encoded-HTML residual; corrected implementation tested, saved ứng viên tập ứng viên reprocessed to verify corrections. Initial tệp kết quả được giữ tại `data/interim/p2/20261009/` nhưng superseded; chỉ `20261009_final` là hiện tại run. Không chạy lại nguồn acquisition/full44million survey hoặc P1 QA evaluation.

```powershell
.\.venv\Scripts\python.exe -B -m scripts.prepare_p2_amazon
.\.venv\Scripts\python.exe -B -m scripts.report_p2_amazon --output-dir reports/tables/NEW_P2_REPORT
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
```

hiện có đầu ra không overwrite; để chạy lại, copy cấu hình sang path khác, đổi interim đầu ra và sạch path trong isolated checkout/config. báo cáo command chỉ đọc saved đầu ra, không tái xử lý source. hiện tại CLI không tự chia tập hoặc tập huấn luyện.

Remaining limits: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **SemEval-to-Amazon platform/style shift within laptop review**, **small thủ công annotated bộ dữ liệu gold** (con người sentiment/ABSA gold chưa có). true language/spam/semantic near-duplicate/noise lỗi rates chưa có con người estimates. C1/C2 limits vẫn áp dụng. BLOCKED: authorized SemEval nguồn/giấy phép cho đóng P1 và SemEval-dependent ABSA. NEXT_ACTION: review hiện tại P2 report/artifacts; công việc kế tiếp theo PLAN là P3, nhưng chưa triển khai P3 trong tác vụ chỉ được phép Amazon-only P2 này. P4 phân chia và mọi huấn luyện vẫn NOT RUN.
