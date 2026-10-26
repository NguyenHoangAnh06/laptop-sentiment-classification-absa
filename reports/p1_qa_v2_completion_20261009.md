# P1 — QA v2 và chấp nhận, 2026-10-09

**con người review đã hoàn thành; v2 đánh giá COMPLETE; P1 NEEDS review / NOT hoàn thành.** Reviewer `human_reviewer_01` đã có global cuối cùng phê duyệt; không cần xác nhận lại. Nhãn gốc/canonical/frozen sidecar không thay đổi trong tác vụ này. Trạng thái duyệt nhãn khác với phê duyệt independence, quality/coverage hoặc giai đoạn acceptance.

## 100 nhãn trống

`data/manual/laptop_filter_qa.csv` là template cũ từ `scripts/audit_p1.py:audit_legacy_prefix`, sampled50 include/50 exclude từ20.000 siêu dữ liệu-prefix records, hạt giống ngẫu nhiên42. Tái hiện membership/order và100 source-line bindings (ID/title/category/brand/store/rule) PASS. Schema/IDs hợp lệ,100 nhãn trống. Mẫu này không phải150 KEEP/150 REJECT/100 chẩn đoán review hay200 sản phẩm của độc lập QA v1, cũng không phải868 supplemental v2.

Trong100 sản phẩm,1 ID `B0C2ZMJW53` có con người nhãn laptop trong v1 review gán nhãn `bd520abe231e1c2f8d7346a5`; common title/category fingerprint khớp. Không tự chuyển nhãn sang mô hình cơ sở hoặc dùng review lấy mẫu unit như sản phẩm lấy mẫu unit. 99 IDs không có reference nhãn trong các bộ hiện hành đã kiểm tra. Toàn bộ100 blank hàng được lưu riêng tại `data/interim/annotation_validation/20261009/legacy_baseline_pending.csv`; đây là worklist tùy chọn nếu cần sử dụng lại mô hình cơ sở, không blocker QA hiện hành.

Đính chính báo cáo trước: file `data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv` thực sự tồn tại; 100 nhãn54 True/46 false dùng lược đồ `human_is_target_product`, SHA256 `9c0b1594b6207fb1d29066e4baa483ebc9b2ea9f3b82051c9399a505e6206f83` khớp lịch sử. Inventory trước bỏ sót lược đồ này; script đã sửa, không tái tạo labels/results. Mẫu feasibility còn lại `Electronics_laptop_8a3c1eaf1583.csv` có100 blank nhãn, không dùng cho official evaluation. đã lưu trữ non-project workflows không được khôi phục. Inventory hiện hành có6 nguồn CSVs +1 canonical derivative, không duplicate/missing IDs hoặc invalid vocabulary theo từng schema.

bằng chứng: `independent_qa/annotation_inventory_20261009/inventory.json` và `baseline_references.csv`. Xác nhận review ở mức file giữ nguyên; ô nhãn trống không phải cuối cùng nhãn và không được tự tạo nhãn/human evidence.

## tập xác thực và thiết kế lấy mẫu

V1200 product/400 review nhãn, fingerprints và evaluated hàm băm khớp đã cố định pilot; không unresolved/conflicting nhãn. V2 canonical868 unique IDs,1 laptop/ 867 non_laptop; nguồn CSV ACCEPT/REJECT và canonical mapping khớp từng dòng, chỉ khác biểu diễn `human_label`. Evidence/reason enum/source fingerprints PASS. Evaluator mới nhận canonical override chỉ cùng review-confirmation sidecar có đã phê duyệt source/canonical hashes/reviewer; từ chối changed ghi chú hoặc membership.

review IDs v1/v2 không overlap. sản phẩm IDs có thể lặp: lấy mẫu unit là review, không yêu cầu không trùng sản phẩm giữa các tập và không claim độc lập gán nhãn theo product. V2 SRS có điều kiện trên REJECT complement N=43.478.054; không coi v1/v2 là hai SRS cùng frame có thể pooling tự do. Cỡ mẫu mới được chọn sau pilot.

KEEP giữ N408.480/n150, weight2723,2. Old ngẫu nhiên REJECT150 units trở thành known units weight1; v2 weight43.478.054/868=50.089,923963. chẩn đoán lỗi không vào population estimates.260 selected-but-invalid review ngoài frame đánh giá. mẫu lựa chọn không phụ thuộc con người nhãn v2; không điều chỉnh filter sau nhãn.

## Quan sát và ước lượng

| Bộ / tầng | Quan sát laptop/non-laptop | Ý nghĩa |
|---|---:|---|
| V1 ngẫu nhiên GIỮ review | 150 / 0 | 150 TP,0 FP |
| V1 TỪ CHỐI ngẫu nhiên review | 1 / 149 | 1 FN,149 TN |
| V2 TỪ CHỐI bổ sung | 1 / 867 | 1 FN,867 TN |

V2 laptop fraction trong REJECT mẫu là0,115207%, exact marginal95% CI 0,002919–0,640201%. Không phải độ bao phủ (recall). Pilot REJECT fraction0,666667%; thay đổi point estimate không chứng minh filter cải thiện vì rules/dataset không đổi.

| Chỉ số dân số review | điểm V1 | Khớp V1KTC 95% | Điểm kết hợp có điều kiện | Khớp kết hợp CI 95% |
|---|---:|---:|---:|---:|
| độ chính xác dự đoán (precision) | 100% | 97,12–100% | 100% | 97,12–100% |
| độ bao phủ (recall) | 58,4934% | 17,9234–99,1153% | **89,0767%** | **55,4584–99,8455%** |
| F1 | 73,8118% | 30,2620–99,5557% | 94,2228% | 70,6017–99,9227% |

Combined estimated TP408.480, FP0, FN50.090,923963, TN43.428.113,076037 là weighted totals, không thực tế corpus lỗi counts. Known old1 FN cộng với1 new FN nhân complement weight. Không dùng868 nghiệm thu fraction hoặc N/(150+868). Kish ESS883,94 mô tả weights, không phải độ chính xác dự đoán (precision) của độ bao phủ (recall) estimator.

Intervals: equal-tail exact finite-population hypergeometric inversion, mỗi ngẫu nhiên stratum97,5%, Bonferroni simultaneous bounds>=95%, monotone ratio bounds. V1 formulas/intervals reproduced đúng đã cố định audit; canonical v2 đánh giá chạy lại in-memory khớp toàn bộ saved result. Không overwrite v1 hoặc chạy lại acquisition.

độ bao phủ (recall) uncertainty hẹp hơn sau supplemental review nhưng vẫn rộng vì1 FN hiếm. lấy mẫu CI có điều kiện trên nhãn đúng và thiết kế hợp lệ; không bao phủ con người classification lỗi, AI anchoring hoặc correlated gán nhãn decisions. V1 giữ human_verified_after_ai_assistance; v2 con người-approved nhưng AI history unspecified, không claim fully blind/independent. `ai_assistance=null` chỉ unknown history.

## Âm tính giả

| Round/task | sản phẩm | siêu dữ liệu và nguyên nhân rule | Diễn giải |
|---|---|---|---|
| Sản phẩm chẩn đoán V1 | B08741LXZ8 | ASUS ROG Zephyrus Duo; laptop category nhưng title mô hình-only | Keyword whitelist thiếu bằng chứng model/spec; chẩn đoán, không population độ bao phủ (recall) |
| Sản phẩm chẩn đoán V1 | B071HYYB4M | Razer Blade Stealth/Ultrabook; Danh mục laptop | Tiêu đề Ultrabook/model-only; chẩn đoán |
| TỪ CHỐI review ngẫu nhiên V1 | B0BHF1HN6C | Acer Chromebook Spin CP311; thiếu laptop category | `insufficient_laptop_evidence` |
| TỪ CHỐI review ngẫu nhiên V2 | B0BB842RV1 | Tiêu đề GPD Pocket3, notebook laptop, thông số kỹ thuật CPU/RAM/storage/display, danh mục Máy tính bảng | `excluded_category`; category veto chạy trước title/category inclusion |

V2 con người ghi chú xác nhận complete clamshell pocket laptop; review nói về thiết bị và lỗi unit/dịch vụ. Không manufacturer/source verification mới được thực hiện. siêu dữ liệu có bất nhất thông số (RAM1GB so với8GB title/spec; RAM/graphics strings), không tự sửa facts hoặc nhãn. con người lỗi lý do để trống giữ nguyên; machine lý do tách riêng trong tóm tắt, không giả thành con người gán nhãn.

Khuyến nghị audit riêng model/spec bằng chứng và category-misclassified thực sự laptops, có accessory/tablet-only safeguards và độ chính xác dự đoán (precision) tradeoff. Chưa sửa filter, whitelist hoặc ứng viên tập ứng viên; QA records chưa dùng train/tune.

## nghiệm thu và tiếp tục roadmap

| Hạng mục | Trạng thái |
|---|---|
| Acquisition/schema/source linkage/EOF | DONE theo các tệp kết quả đã lưu, giá trị băm không thay đổi |
| con người review / phê duyệt nhãn hợp lệ | ĐÃ HOÀN THÀNH; khoảng trống kế thừa tùy chọn bị loại trừ |
| Đánh giá v1/v2 chính thức + khả năng tái tạo | DONE; thống kê có điều kiện, tiết lộ xuất xứ |
| Hiện có GIỮ độ chính xác dự đoán (precision)>=0,95 | PASS conditional on nhãn; zero observed FP không bằng chứng xác nhận zero contamination |
| Coverage/recall đầy đủ, chấp nhận độc lập | NEEDS review; không đã phê duyệt recall/F1 cutoff hoặc độc lập process nghiệm thu |
| Phân tích thương hiệu | DONE; bảo quản tiêu chí diversity/approved sạch cuối cùng PENDING |
| SemEval được ủy quyền original/source/licence | BLOCKED; global con người phê duyệt không giải quyết licence |
| Sạch-tiếng Anh dataset/splits/training | đang chờ; candidate-quality preflight mới hoàn tất, không cuối cùng huấn luyện các tệp kết quả |
| P1 tổng thể | KHÔNG DONE / CẦN review |

Đã tiếp tục công việc độc lập: toàn bộ ứng viên missing/length/duplicates/QA-leakage mức sẵn sàng audit và preliminary EDA, `data_quality/candidate_pool_20261009/`. Không lặp lại thương hiệu analysis/SemEval conversion đã PASS. P0 complete theo prior bằng chứng; P2/P3 mới có ứng viên preflight, P4 các tập đã chia absent, P5–P9 các mô hình absent, P10 sentiment/ABSA bộ gold do con người gán nhãn absent, P11–P13 chưa đáp ứng milestones. NEXT_ACTION: review coverage/independence và thương hiệu nghiệm thu, giải quyết SemEval authorized nguồn gốc; dùng chất lượng audit để chốt English/HTML/dedup/QA exclusion policy trước cuối cùng sạch tập ứng viên và rò rỉ dữ liệu-resistant phân chia. Không cần gán lại mô hình cơ sở cũ để thực hiện các công việc hiện hành.

## Tái hiện

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_supplemental_qa --kit-dir data/manual/independent_qa/p1_v2 --annotator human_reviewer_01 --confirm-human-review --ai-history-unspecified --review-annotations data/interim/annotation_normalization/20261009/v2_review_annotation_canonical.csv --review-confirmation reports/independent_qa/human_review_20261009/review_confirmation.json --output-dir reports/independent_qa/NEW_V2_EVALUATION
.\.venv\Scripts\python.exe -B -m scripts.summarize_qa_continuation --evaluation-dir reports/independent_qa/NEW_V2_EVALUATION --output-dir reports/independent_qa/NEW_SUMMARY
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

đã xác minh full143 kiểm thử passed in3,65s; targeted7 passed in1,15s. 41 được bảo vệ SHA256 PASS; original/current canonical/confirmation hàm băm tracked in `independent_qa/p1_v2_summary_20261009/summary.json`. New reports/evaluation directories chỉ; no nguồn annotations/checkpoints/configs overwritten. Giới hạn bắt buộc: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop review; small thủ công annotated sentiment/ABSA bộ dữ liệu gold hiện chưa có. phạm vi QA không thay gold hoặc chứng minh production readiness.
