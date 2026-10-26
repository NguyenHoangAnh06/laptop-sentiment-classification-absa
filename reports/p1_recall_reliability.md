# P1 — Độ tin cậy của độ bao phủ (recall) và QA TỪ CHỐI bổ sung

Ngày 2026-10-08 (Asia/Saigon). **Audit hoàn thành; kit v2 READY FOR con người.** **P1 chưa hoàn thành.** Không sửa v1 labels/predictions/manifests, filter hoặc source.

## Thiết kế kiểm toán và ước tính điểm

Đã đọc `src/data/independent_qa.py`, `feasibility.py`, bộ tải, filter, đã cố định kit và evaluation. ngẫu nhiên KEEP: N=408.480, n=150, probability=0,0003672150411, weight=2.723,2. ngẫu nhiên REJECT: N=43.478.204, n=150, probability=0,000003450004513, weight=289.854,693333. Không dùng chẩn đoán samples hoặc nhãn uncertain như negatives. Không có blank/uncertain/conflicts ở v1. Numeric nhãn có nguồn gốc `human_verified_after_ai_assistance`, không fully mù gán nhãn.

REJECT v1 là parent không thuộc selected-product index; không phải mọi failure của cleaning/validity. Raw SHA256, saved index và báo cáo cố định cho phép tái dựng đúng frame này. 408.740 matched + 43.478.204 REJECT = 43.886.944 raw records. Matched gồm 408.480 valid KEEP và 260 selected-but-invalid. 260 vẫn có được chọn parents và không vào REJECT. Frame suy luận 43.886.684; không whole-pipeline độ bao phủ (recall). Không recount mọi parent bằng một survey mới: tái sử dụng authoritative saved số lượng, checksum-preserved source/index; extraction kiểm tra raw physical count/EOF.

| Tế bào nhầm lẫn có trọng số | Tổng số ước tính |
|---|---:|
| TP | 408.480,000 |
| FP | 0,000 |
| FN | 289.854,693 |
| TN | 43.188.349,307 |

Totals = sum_h count_h * N_h/n_h. P=TP/(TP+FP), R=TP/(TP+FN), F1=2TP/(2TP+FP+FN). **P=100%, R=58,4934%, F1=73,8118%**. Đối chiếu independently recomputed counts/metrics với đánh giá v1 đạt PASS; **không phát hiện formula/weight bug**, không cần chạy lại hoặc sửa đánh giá v1. Tính float toàn bộ độ chính xác dự đoán (precision), chỉ round ở presentation; tolerance dùng khi đối chiếu.

Một FN ngẫu nhiên REJECT được weight ~289.855, vì population REJECT lớn hơn KEEP ~106,44 lần. TP estimated chỉ 408.480, nên độ bao phủ (recall) ~58,49% dù sample-only độ bao phủ (recall) 150/151=99,34%. Population estimates không dùng tỷ lệ KEEP/REJECT mẫu 50/50. Estimated totals không phải thực tế corpus counts.

## độ tin cậy interval phù hợp finite population

lấy mẫu SRS without replacement -> X_h ~ Hypergeometric(N_h,M_h,n_h), trong đó M_h là unknown number of laptop records. Dùng equal-tail kiểm thử inversion cho M_h integer: giữ các M có P_M(X>=x)>=alpha_h/2 và P_M(X<=x)>=alpha_h/2. Mỗi ngẫu nhiên stratum dùng alpha_h=0,025 (97,5% interval); Bonferroni cho joint coverage ít nhất 95%, không cần giả định independence để áp dụng union bound. Transform rectangle bounds theo monotonic ratios, không bootstrap từ một FN. PMF dùng C(M,x)C(N-M,n-x)/C(N,n), log-space, binary search M. Phân phối được mô tả trong [R statistics documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Hypergeometric.html).

| số lượng | Ước tính điểm | Khoảng khớp bảo tồn 95% |
|---|---:|---:|
| độ chính xác dự đoán (precision) | 100% | 97,12–100% |
| độ bao phủ (recall) | 58,49% | **17,92–99,12%** |
| F1 | 73,81% | 30,26–99,56% |

KEEP laptop total bounds: [396.722,408.480]; REJECT laptop total bounds: [3.646,1.816.710]. độ bao phủ (recall) lower = 396722/(396722+1816710); upper = 408480/(408480+3646). Bounds cố ý conservative, không claim tight interval. Coverage conditional on cố định correct nhãn, valid SRS, không đổi frames; không bao phủ AI anchoring, siêu dữ liệu lỗi, nonresponse hoặc nhãn mistakes. Không thể kết luận độ bao phủ (recall) thực tế thấp chính xác ở mức 58,49%.

Kish effective mẫu size (sum w)^2/sum(w²) = **152,82** cho 300 ngẫu nhiên review; descriptive weight mất cân bằng, không ratio-specific SE hay substitute cho design. Nonparametric bootstrap có khoảng (149/150)^150 ~36,67% REJECT resamples không FN, dẫn tới độ bao phủ (recall)=1; với một event bootstrap số mẫu hỗ trợ quá nghèo cho kết luận ổn định. Exact design interval tránh giả định normality/Wald cho suy luận hiện tại.

## Lựa chọn QA bổ sung

Pilot REJECT prevalence 1/150=0,6667%; marginal exact 95% interval 0,01688–3,65831%. SRS direct cho equal probability/weights và toàn bộ REJECT coverage. Stratified ngẫu nhiên risk groups có thể hiệu quả hơn nhưng cần đầy đủ frame số lượng theo risk và xác suất từng tầng; chưa có saved index toàn bộ rejected products. Risk-based chẩn đoán tìm lỗi tốt nhưng không estimate độ bao phủ (recall) khi không biết probabilities. Không bổ sung chẩn đoán hàng vào probability mẫu; v1 chẩn đoán lỗi chỉ định hướng đề xuất policy, không thành ngẫu nhiên observations.

Planning conventional n0=z²(1-p)/(p*r²), finite correction n=ceil(N*n0/(N+n0-1)); đây là giới hạn tài nguyên scenarios theo uncertain pilot rate, không đã phê duyệt nghiệm thu threshold hoặc guarantee. Bảng total-review-budget subtract 150 records đã review để chọn workload mới:

| Nửa chiều rộng tương đối danh nghĩa trong kế hoạch tổng ngân sách thông thường | Tổng ngân sách | review mới | Dự kiến FN mới theo phi công | Giờ nếu 30s/review |
|---|---:|---:|---:|---:|
| 100% | 573 | 423 | 2,82 | 3,53 |
| 75% | 1.018 | **868** | 5,79 | 7,23 |
| 50% | 2.290 | 2.140 | 14,27 | 17,83 |
| 25% | 9.157 | 9.007 | 60,05 | 75,06 |

Chọn 868 là scenario ngân sách trung bình, không chọn số tròn tùy ý. Vì combined estimator đúng xem pilot là certainty units, thực tế nominal relative half-width trên remaining frame với n_new=868 là **81,2%, không 75%**. Nếu muốn nominal 75% riêng remaining frame cần khoảng 1.018 new review. Đây là tradeoff được nêu rõ, không tự claim mục tiêu độ chính xác dự đoán (precision) đạt. Planning Wald chỉ heuristic ở rare events; suy luận sau gán nhãn dùng exact hypergeometric, không Wald. Theo pilot rate, 448 new cho chance ít nhất một FN ~95%; 868 cho ~99,70%. Tại lower bound marginal pilot prevalence, 868 chỉ cho ~13,63% detection. Các expected/detection/cost là giả định planning, không results thực tế mới.

## Kit thực tế và estimator cho round sau

`data/manual/independent_qa/p1_v2/review_annotation.csv`: **868 unique review**, all con người các trường blank, không giao nhau bất cứ review v1. N_REJECT remaining =43.478.204−150=43.478.054. hạt giống ngẫu nhiên20261008; raw ứng viên lines được chọn uniformly không replacement, loại mọi nguồn lines v1; first 868 eligible siêu dữ liệu-unselected các ứng viên là conditional SRS trên complement. ứng viên shortage -> fail, không xuất một phần kit. Không dùng review keyword để chọn nhãn hoặc samples. review text/rating validity không tham gia membership của REJECT frame.

Sidecar cố định IDs, stratum, prediction, N/n, inclusion probability và weight; CSV không chứa prediction/stratum. bản kê ghi bản chụp trạng thái hashes/index/report, hàng fingerprints, old evaluation/annotation bindings, seed/resources. Guide: `docs/SUPPLEMENTAL_REJECT_QA.md`, bản copy `annotation_guide.md` trong kit. Chỉ đọc sequential gzip tới EOF/CRC, JSON-decode2.604 review các ứng viên; siêu dữ liệu đọc1.610.012 hàng để enrich, không regenerate survey hoặc saved pools. Elapsed148,151s; decoded read27.862.377.786 byte; peak working set87.216.128 bytes. Decoded read không gồm checksum I/O, không gọi là total physical I/O.

Vì n_v2 được chọn sau pilot, không naive pool150+868 với weightN/1018. Conditional unbiased REJECT total = known_v1_laptop_count + (N_REJECT−150)*FN_v2/868; old ngẫu nhiên REJECT units weight1, complement mẫu weight50.089,92396. KEEP vẫn N_KEEP/150; old chẩn đoán không góp estimates. Combined exact intervals: ngẫu nhiên KEEP M bounds + complement M bounds, cộng known v1 FN/TN rồi Bonferroni transform. Đây là interval conditional on observed pilot, không giả định adaptive pooled mẫu là SRS. New-only prevalence/CI và pilot comparison được đầu ra; uncertainty/conflicts làm thước đo null, không imputations.

**Không chạy supplemental/combined đánh giá trên nhãn thật: chưa có nhãn v2.** Pipeline/threshold không đổi. mù second reviewer chưa xem AI/v1 được khuyến nghị; v2 không tự biến v1 thành fully mù hoặc đóng sản phẩm QA independence.

## Sinh sản và giới hạn

```powershell
.\.venv\Scripts\python.exe -B -m scripts.audit_recall_reliability --output reports/tables/NEW_recall_audit.json
.\.venv\Scripts\python.exe -B -m scripts.prepare_supplemental_qa --output-dir data/manual/independent_qa/NEW_KIT
```

Machine-readable audit: `reports/tables/p1_recall_reliability.json`. Không overwrite outputs. Future đánh giá command trong gán nhãn guide chỉ chạy sau con người nhãn và explicit reviewer confirmation. Tests/remaining các điều kiện nghiệm thu: `reports/p1_remaining_gates.md`. Limits: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift within laptop review; small thủ công annotated cảm xúc/ ABSA bộ dữ liệu gold chưa có, phạm vi QA không thay thế gold. P2/training NOT_RUN.
