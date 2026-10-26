# Ảnh chụp nhanh cổng còn lại P1 - 2026-10-09

## Quyết định của chủ sở hữu hiện tại — 2026-10-09

P1 **DONE**: C1-A/C2-A/C3-A đã được phê duyệt và SemEval Train/Test cộng với JSONL được chấp nhận theo ngoại lệ giáo dục được chủ sở hữu phê duyệt. Xác minh Source/license được miễn; **NOT_VERIFIED**, không bao giờ GIẤY PHÉP PASS/VERIFIED. Không cần tìm kiếm thêm nguồn, thu thập bằng chứng hoặc tải xuống lại. PASS kỹ thuật hiện có được sử dụng lại khi byte không thay đổi. Bảo quản partitions/spans/polarity/provenance gốc và P10 gold độc lập. P2 DONE; P3 bây giờ là DONE; hiện không thực thi P4/later. Bằng chứng P3: `reports/p3_data_analysis_20261009.md`. Bản ghi: `reports/tables/p1_semeval_owner_exception_20261009.json`.

Các tuyên bố gate/status trước đây sau đây là bằng chứng lịch sử, được thay thế bởi quyết định của chủ sở hữu hiện tại; họ không yêu cầu xác minh lại.

Trạng thái có thẩm quyền: PLAN_HUMAN/PLAN_AI. Chủ dự án APPROVED C1-A/C2-A/C3-A/C4-B; ghi nhận ở `tables/p1_owner_approval_20261009.json`, hồ sơ quyết định tại [p1_acceptance_decision_20261009.md](p1_acceptance_decision_20261009.md). Tại thời điểm báo cáo này, P1 chưa DONE: nguồn/giấy phép SemEval được phép sử dụng còn BLOCKED ở P1-T03. Recall 89.0767%, khoảng tin cậy đồng thời 95% 55.4584–99.8455%; giữ các giới hạn chọn mẫu và QA có hỗ trợ. Human gold độc lập P10 vẫn bắt buộc. Các mẫu cơ sở trống cũ là tùy chọn. P2 chỉ Amazon COMPLETE theo C4-B: [báo cáo P2](p2_amazon_completion_20261009.md). Có 30k review/9080 sản phẩm, dành riêng 250 mẫu chẩn đoán nhiễu; đã đo phân bố thương hiệu trước/sau, không áp hạn ngạch đều. Không chia tập/huấn luyện/thực hiện P3 trong tác vụ này. NEXT_ACTION: xác minh nguồn/điều khoản SemEval để khép P1; giai đoạn tiếp theo theo PLAN là P3, nằm ngoài tác vụ P2 đã hoàn thành này. Không yêu cầu nghiệm thu QA P1 bổ sung.

Sau đây là ảnh chụp nhanh lịch sử2026-10-08 được giữ lại, không phải cổng hiện tại.

# P1 — Các cổng còn lại và chuyển giao cho con người QA v2

Ngày 2026-10-08 (Asia/Saigon). **P1 NOT hoàn thành; P2/training NOT_RUN.** Hoàn tất phần có thể tự động hóa; dừng trước annotation/evaluation v2 thực tế.

| Cổng/nhiệm vụ | Trạng thái | Bằng chứng | Hành động còn lại |
|---|---|---|---|
| Kiểm toán độ bao phủ (recall) formula/weights | DONE / PASS | `p1_recall_reliability.md`, JSON audit khớp v1 | Không cần chạy lại v1 |
| Chấp nhận độ tin cậy của độ bao phủ (recall) | CẦN review | Điểm58,49%, khớp95% CI17,92–99,12% | con người QA bổ sung; không kết luận độ bao phủ (recall) thấp chính xác |
| Chuẩn bị QA xác suất bổ sung | SẴN SÀNG CHO con người | `data/manual/independent_qa/p1_v2/`,868 trống-nhãn review | con người annotate, xác nhận process/annotator |
| Đánh giá Supplemental/combined | PENDING | Code và synthetic-fixture kiểm thử có sẵn | Không chạy official trước nhãn |
| Tiêu chí KEEP độ chính xác dự đoán (precision)95% hiện có | PASS có điều kiện trên nhãn | V1 ngẫu nhiên product/review KEEP150/150 | Không đồng nhất independent/coverage điều kiện nghiệm thu |
| thủ công product/filter QA độc lập | CẦN review | V1 con người review after AI suggestions, không fully mù | mù second reviewer hoặc documented nghiệm thu decision; chưa có bằng chứng hoàn thành |
| Phân tích đa dạng thương hiệu ứng viên | DONE | Bàn bida được lưu đầy đủ, biểu đồ 5 PNG+5 SVG | review siêu dữ liệu aliases/title bất đồng |
| Bảo tồn sự đa dạng/chấp nhận thương hiệu | CẦN review / PENDING | 5 sản phẩm hàng đầu76,32%, review79,77%; unknown/ambiguous1,11%/0,32% | Approve criteria; cuối cùng clean-dữ liệu bảo toàn thuộc P2 |
| SemEval được ủy quyền originals/provenance/licence | BLOCKED | Local manifests chỉ user-supplied mirror, official byte identity unverified | Authorized source/evidence of terms nghiệm thu hoặc đã xác minh mirror permission |
| Làm sạch tiếng Anh coverage/duplicates/proxy-noise | NOT_MEASURED, P2 hoạt động | ứng viên validity không chứng minh sạch tiếng Anh | Không tự chạy P2 |
| P1 hoàn thành | BLOCKED / CẦN review | Mandatory các điều kiện nghiệm thu còn mở | Không mark hoàn thành |

## gán nhãn độc lập

Người dùng đã xác nhận human_reviewer_01 tự kiểm tra/chấp thuận nhãn v1 sau một số gợi ý AI. Không yêu cầu lặp lại identity/confirmation. Không đổi nhãn v1 hoặc retroactively claim fully blind. V2 CSV không có predictions nhưng gồm REJECT frame, không được quảng cáo mixed fully mù kiểm thử. Đề xuất second reviewer chưa xem v1/AI; có thể cần second review cho sản phẩm điều kiện nghiệm thu riêng, không chỉ review v2. Không suy đoán chất lượng con người work từ template bằng chứng ngắn; bằng chứng đã được user chấp nhận theo schema. Supplemental kit không tự satisfy độc lập gate.

## Giá trị provenance/licence review

đã xác minh local bằng chứng inspected: `reports/tables/p1_semeval_normalization.json`, mirror nguồn review và download access reports. XML hàm băm,gốc partitions và lossless JSONL không chứng minh nguồn official hoặc quyền mirror redistribution. Saved access bằng chứng ghi MS-NC-NoReD academic/noncommercial/no-redistribution và login redirect; đó là prior tài nguyên-page bằng chứng, không chứng nhận người dùng đã chấp thuận điều khoản. Exact user-supplied GitHub URL/revision và official byte identity vẫn unverified. bộ tải Apache header không phải bộ dữ liệu licence.

đã xác minh hiện tại web read: [official tác vụ dữ liệu and Tools](https://alt.qcri.org/semeval2014/task4/index.php?id=data-and-tools) trỏ tập huấn luyện V2.0 và kiểm thử phases tới META-SHARE. tài nguyên links không resolve được qua web tool trong lần kiểm tra này; không suy ra provider offline hoặc licence đã đổi. Không tải XML, login, accept licence, thay local datasets hoặc tự chứng nhận authorized acquisition. Public landing page không cấp quyền cho mirror cụ thể. BLOCKED: chưa có provenance/terms-acceptance bằng chứng cho files đang dùng. NEXT_ACTION: người dùng cung cấp exact source/revision và authorized acquisition/ terms bằng chứng, hoặc xác minh quyền mirror theo nguồn chính thức. Không lấy giấy phép từ GitHub/code header để đóng checklist.

## tập xác thực và bảo quản

kiểm thử mới: exact hypergeometric CDF so với combinatorial small populations, coverage>=95%, zero events, census, weighted ratios và complement-vs-pooled; uniform ứng viên sampling/reproducibility/exclusion, dữ liệu mẫu kit blank con người các trường, trùng lặp prevention, nguồn tamper, bản kê weights, gán nhãn-bound future đánh giá; thương hiệu chuẩn hóa, Unicode/aliases/unknown/ambiguity, title-hint separation, full-count denominators và chart exports. dữ liệu mẫu nhãn là tổng hợp kiểm thử-only, không real bộ gold do con người gán nhãn.

Các lệnh đã dùng:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_sampling_uncertainty.py tests/test_supplemental_qa.py tests/test_brand_diversity.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
```

đã xác minh cuối cùng: new tests19 passed in2.71s, toàn bộ suite139 passed in3.14s, pip check PASS. phụ thuộc được ghim phiên bản với Requires-Python hỗ trợ3.11; môi trường chạy kiểm thử trên existing3.13.12, chưa tạo/test interpreter3.11 riêng. Source/pool/v1/SemEval/config bảo toàn: `reports/tables/p1_recall_brand_preservation.json`, 41 được bảo vệ files SHA256 không đổi PASS; v2 blank con người fields/no overlap/probabilities/fingerprints/counts PASS trong `reports/tables/p1_recall_brand_validation.json`. QA v2 integrity checks riêng không con người evaluation. Không overwrite v1 hoặc các đầu ra quan trọng trước tác vụ; v2/report các tệp kết quả mới được hoàn thiện trong task. P1 independent/brand-preservation/SemEval/DONE các điều kiện nghiệm thu giữ unchecked; chỉ thêm hoàn thành analysis/preparation tác vụ có evidence.

## Hành động tiếp theo

Người dùng gán nhãn868 review trong `data/manual/independent_qa/p1_v2/review_annotation.csv`, theo `docs/SUPPLEMENTAL_REJECT_QA.md`. Không mở sidecar hoặc dùng AI tạo nhãn chuẩn. Sau gán nhãn và explicit reviewer declaration, chạy evaluator vào đầu ra mới, review combined độ tin cậy intervals/errors rồi quyết định QA/coverage acceptance. Giải quyết SemEval nguồn gốc riêng; chưa bắt đầu P2 hoặc huấn luyện.

Limits: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift within laptop review; small annotated sentiment/ABSA gold chưa có. phạm vi QA này không phải P10 gold hoặc production-readiness evidence.
