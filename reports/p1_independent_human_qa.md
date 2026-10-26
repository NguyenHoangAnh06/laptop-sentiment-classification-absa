# P1 — Đánh giá chất lượng con người và tính khả thi của dữ liệu

Ngày 2026-10-08 (Asia/Saigon). người gán nhãn: `human_reviewer_01`. **đánh giá hoàn tất; P1 chưa hoàn thành — BLOCKED / NEEDS review.**

## Xuất xứ và tập xác thực

Người dùng xác nhận tự kiểm tra và chấp thuận toàn bộ nhãn, bao gồm một số nhãn điều chỉnh sau gợi ý AI. nguồn gốc: `human_verified_after_ai_assistance`. Không mô tả toàn bộ quá trình là fully mù gán nhãn hoặc gold độc lập với AI. con người verification đã xác nhận; điều kiện nghiệm thu xác minh độc lập vẫn NEEDS review. Không biết số lượng/IDs từng được AI hỗ trợ; không tự suy đoán danh sách đó. CSV blinded ban đầu không chứng minh quá trình thực hiện sau này blind. thước đo có điều kiện theo nhãn hiện tại; AI anchoring/correlated lỗi nằm ngoài lấy mẫu uncertainty. Không truy cập hãng/retailer để xác minh thêm trong tác vụ này.

đã xác minh: 200 sản phẩm (153 laptop / 47 non_laptop), 400 review (251 laptop / 149 non_laptop), không blank/uncertain. lược đồ, IDs, bằng chứng presence, label/reason enums, nguồn fingerprints và sidecar checksum PASS; không product-nhãn conflicts. Phân bố toàn mẫu không phải population metrics. 403 bằng chứng cells `Amazon title + category` được chấp nhận theo yêu cầu hiện tại. 598 ghi chú trống không vi phạm validator. Không yêu cầu ngày kiểm tra; không sửa nhãn/evidence.

## lấy mẫu và phạm vi

hạt giống ngẫu nhiên 42, offsets/snapshot trong đã cố định kit bản kê và `docs/INDEPENDENT_HUMAN_QA.md`. sản phẩm ngẫu nhiên KEEP: SRS không hoàn lại trên unique products. review ngẫu nhiên KEEP: SRS trên valid saved records. ngẫu nhiên REJECT: ngẫu nhiên raw physical lines có điều kiện siêu dữ liệu-unselected. chẩn đoán có frame riêng, không gộp vào representative estimates. Join native `parent_asin`; review text/ rating không quyết định phạm vi. Survey mẫu 5.000 không phải QA frame.

| Tầng | Khung N | mẫu n | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|
| Sản phẩm ngẫu nhiên GIỮ | 28.172 | 150 | 150 | 0 | 0 | 0 |
| Chẩn đoán sản phẩm | 164.453 | 50 | 1 | 0 | 2 | 47 |
| review hợp lệ ngẫu nhiên GIỮ | 408.480 | 150 | 150 | 0 | 0 | 0 |
| review ngẫu nhiên siêu dữ liệu TỪ CHỐI | 43.478.204 | 150 | 0 | 0 | 1 | 149 |
| Chẩn đoán review, chỉ GIỮ | 80.721 | 100 | 100 | 0 | 0 | 0 |

laptop là positive; KEEP là predicted positive. sản phẩm chẩn đoán có 3 laptop / 47 non_laptop, 2 laptop bị REJECT. Không suy ra population độ bao phủ (recall) từ diagnostic. review chẩn đoán có 100 laptop, không FP; nhóm KEEP-only không chứng minh không còn FN. sản phẩm ngẫu nhiên KEEP chỉ hỗ trợ độ chính xác dự đoán (precision), không sản phẩm recall/F1.

## Số liệu và ma trận nhầm lẫn

sản phẩm ngẫu nhiên KEEP độ chính xác dự đoán (precision) **100% (150/150)**; review KEEP độ chính xác dự đoán (precision) cũng **100% (150/150)**. Không thấy accessory/desktop/tablet contamination trong ngẫu nhiên KEEP samples; không có nghĩa population contamination bằng zero.

review ngẫu nhiên confusion matrix, observed số lượng chưa weighting:

| Sự thật / đường dẫn con người | GIỮ | TỪ CHỐI |
|---|---:|---:|
| laptop | 150 | 1 |
| Không phải laptop | 0 | 149 |

Sample-only độ chính xác dự đoán (precision) 100%, độ bao phủ (recall) 99,3377%, F1 99,6678% mô tả mẫu 150/150, **không phải population-level recall/F1**.

Trọng lượng thiết kế: GIỮ `408480/150 = 2723.2`; TỪ CHỐI `43478204/150 = 289854.69333333336`. Tổng số ước tính = `sum_h count_h * N_h/n_h`; P = TP/(TP+FP), R = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). Trọng lượng lấy mẫu khác với trọng số lớp F1.

| Sự thật / đường dẫn con người | GIỮ, ước tính | TỪ CHỐI, ước tính |
|---|---:|---:|
| laptop | 408.480,000 | 289.854,693 |
| Không phải laptop | 0,000 | 43.188.349,307 |

**Design-weighted review độ chính xác dự đoán (precision) 100%; độ bao phủ (recall) 58,4934%; F1 73,8118%.** Weighted totals không phải thực tế corpus lỗi counts. Một ngẫu nhiên REJECT FN đại diện khoảng 289.855 records trong point estimate, không khẳng định có đúng số laptop bị bỏ sót đó. Đã tính lại thước đo độc lập từ strata số lượng, đối chiếu với tolerance floating-point; xem `statistical_summary.json`.

## Sự không chắc chắn về thống kê

95% Wilson score intervals cho laptop fraction: sản phẩm KEEP và review KEEP **97,5030–100%**; review REJECT **0,1178–3,6793%**, point estimate 0,6667%. Approximate binomial intervals cho SRS without replacement; bỏ finite-population correction vì lấy mẫu fractions ~0,5324%, 0,0367%, 0,000345%. Marginal, không simultaneous; không bao phủ gán nhãn errors/AI anchoring. Không có representative CI cho chẩn đoán samples. Với z=1.959963984540054, p=k/n: center=(p+z²/(2n))/(1+z²/n), halfwidth=z*sqrt(p*(1-p)/n+z²/(4n²))/(1+z²/n); clipped endpoints [0,1].

Không báo CI weighted recall/F1: chưa triển khai ratio interval estimation phù hợp rare-event REJECT. Sensitivity, **không phải đã đo lần chạy hoặc CI**: giữ KEEP và thay hypothetical REJECT FN bằng 0/1/2 cho độ bao phủ (recall) 100%/58,49%/41,34%. Chỉ FN=1 là quan sát thật. Cần mẫu REJECT bổ sung theo thiết kế định trước để kết luận độ bao phủ (recall) ổn định; không lựa chọn mẫu thuận lợi hậu nghiệm.

## phân tích lỗi

`errors.csv` có 3 FN, không FP. Cả ba thiếu `human_error_reason`, machine cause giữ `unclassified`. Bảng là phân tích kỹ thuật từ đã cố định metadata/rule, không phải nhãn con người mới. quy trình lý do cả ba: `insufficient_laptop_evidence`.

| tác vụ / tầng / sản phẩm | Nguyên nhân quan sát | Đề xuất, chưa thực hiện |
|---|---|---|
| Chẩn đoán sản phẩm / B08741LXZ8 | ASUS ROG Zephyrus Duo có laptop category/specs; title thiếu laptop/notebook/chromebook | Xem xét model/spec bằng chứng khi thiếu keyword, giữ accessory safeguards |
| Chẩn đoán sản phẩm / B071HYYB4M | Razer Blade Stealth có danh mục laptop; title dùng Ultrabook ngoài từ khóa whitelist | Xem xét Ultrabook + category, kiểm tra regression phụ kiện |
| review TỪ CHỐI ngẫu nhiên / B0BHF1HN6C | Acer Chromebook Spin CP311 có Chromebook trong title nhưng thiếu laptop category | Xem xét category-incomplete Chromebook/convertible bằng chứng, phân biệt tablet-only/bundle accessories |

Category/title đồng thời quá chặt có thể giảm coverage. thực sự Chromebook/ chuyển đổi vẫn in-phạm vi. Không phát hiện FP accessory/desktop/tablet; zero observed không bằng chứng xác nhận toàn corpus. Không definitive nhãn conflicts cùng product. siêu dữ liệu completeness chỉ nhận xét ở dòng lỗi, không ước lượng toàn corpus. Non-tiếng Anh rate **NOT_MEASURED**: language không thuộc phạm vi QA này.

## 260 bản ghi được chọn nhưng không hợp lệ và tính khả thi về số lượng

review frame 408.480 valid KEEP + 43.478.204 siêu dữ liệu REJECT = 43.886.684; raw corpus 43.886.944, chênh 260 selected-but-invalid. Chúng không nằm trong sample/ weighted estimates, chưa được audit domain/validity riêng. Không suy ra lỗi của chúng từ FP/FN hiện tại và không gọi thước đo là whole raw-to-clean quy trình độ bao phủ (recall). 11 được chọn sản phẩm không có valid review không được đánh giá review validity bằng sản phẩm độ chính xác dự đoán (precision).

REPORTED toàn bộ survey: 28.172 được chọn sản phẩm, 28.161 có valid review, 408.480 valid review; ratio so với 30K mục tiêu là 13,616x, cần retention 7,3443%. Quantity có tiềm năng; sạch tiếng Anh yield, duplicates/spam, nhãn đại diện nhiễu và cuối cùng class/product/brand coverage **NOT_MEASURED**. Không chạy lại survey/P2/training.

## Quyết định về tính sẵn sàng và danh sách kiểm tra của P1

Ngưỡng đã tồn tại: `configs/acquisition.yaml:qa.required_precision = 0.95`. Nhận định preflight trước rằng không có numeric threshold được đính chính. Point độ chính xác dự đoán (precision) đạt 95%; Wilson lower bound 97,50% cũng vượt 95%, dù plan không bắt buộc CI lower bound. Không đã phê duyệt recall/F1 cutoff; không tự đặt ngưỡng rồi dùng để kết luận PASS/FAIL.

| Cổng | Trạng thái | Quyết định |
|---|---|---|
| Schema/bindings, con người đã được đánh giá evaluation/report | PASS | Thêm danh sách kiểm tra đánh giá hoàn thành, disclosed AI assistance |
| Product/review GIỮ độ chính xác dự đoán (precision) >=95% | PASS, điều kiện số trên nhãn | · Hiệu lực gate/whole-pipeline độc lập |
| Độ đầy đủ của Recall/F1 | CẦN review | Rare FN uncertainty, chưa đã phê duyệt cutoff |
| Mẫu thủ công độc lập tập xác thực | CẦN review | con người review confirmed; AI influence disclosed, không tự đóng điều kiện nghiệm thu |
| Bộ lọc laptop được ghi lại và xác nhận, chấp nhận tổng thể | CẦN review | độ chính xác dự đoán (precision) đạt, provenance/coverage cần quyết định; checkbox mở |
| SemEval được ủy quyền source/licence | BLOCKED | Local files/normalization không chứng minh authorized originals |
| Preserve thương hiệu diversity nếu siêu dữ liệu hỗ trợ | PENDING | Raw thương hiệu strings chưa phải cuối cùng canonical thương hiệu coverage |
| P1 hoàn thành | BLOCKED / CẦN review | Mandatory checklists còn mở |

Không thay filtering policy. Có cơ sở đề xuất cải thiện FN coverage; cần audit riêng và độ chính xác dự đoán (precision) tradeoff trước áp dụng. Không khẳng định có sạch bộ dữ liệu đủ cho P2. Có thể cân nhắc Amazon P2 sau quyết định của người dùng về QA/coverage; **chưa phê duyệt hoặc chạy P2**, P1 tổng thể chưa hoàn thành. NEXT_ACTION: review provenance/coverage nghiệm thu và supplemental QA design, đồng thời giải quyết authorized SemEval provenance/licence. Nếu P2 được cho phép: language/validity audit và negation-preserving làm sạch; exact/near trùng lặp, spam/short review, đại diện-nhiễu audit; cuối cùng class/product/ thương hiệu coverage và lấy mẫu; persist rò rỉ dữ liệu-resistant 70/15/15 các tập đã chia, ghi rõ group constraints. Không tune bằng test/gold.

## Nhân giống, thử nghiệm và bảo quản

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_independent_qa --kit-dir data/manual/independent_qa/p1_v1 --annotator human_reviewer_01 --confirm-independent-human --ai-assisted-review --output-dir reports/independent_qa/p1_v1_evaluation
.\.venv\Scripts\python.exe -B -m pytest tests/test_independent_qa.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

đầu ra đã tồn tại; chạy lại dùng directory mới. Relevant kiểm thử **19 passed in 0.40s**; toàn bộ suite **120 passed in 1.58s**. Một kiểm thử mới kiểm tra AI-assisted nguồn gốc trong JSON/Markdown, thước đo không đổi và đầu vào byte nguyên vẹn. Code chỉ thêm nguồn gốc option; sampling/filter/weighting/dependencies/configs không đổi.

đã xác minh SHA256: hai raw Amazon, ba full-survey JSONL, hai SemEval XML và hai normalized JSONL khớp đã cố định manifests; gán nhãn khớp preflight, sidecar khớp kit bản kê. Kit bản kê hàm băm được capture và kiểm tra lại cuối task. Chi tiết `integrity.json`; không ghi nguồn/human labels/predictions. Preparation: `reports/tables/p1_independent_qa_preparation.json`. Preflight JSON giữ declaration trạng thái cũ như lịch sử, không hiện tại evaluation. đầu ra: `evaluation.json`, `report.md`, `comparisons.csv`, `errors.csv`, `strata.csv`, `statistical_summary.json`, `integrity.json`, `assessment.md`.

Giới hạn: **laptop-only findings**, **nhãn đại diện suy từ số sao-nhiễu nhãn** chưa đánh giá, **SemEval-to-Amazon platform/style shift trong cùng laptop phạm vi**, **small thủ công annotated bộ dữ liệu gold** chưa có sentiment/ABSA gold; phạm vi QA này không thay thế gold. Không mô hình metrics/production-readiness claim.
