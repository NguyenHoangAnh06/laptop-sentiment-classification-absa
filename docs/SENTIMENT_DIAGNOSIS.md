# Chẩn đoán sentiment và tái lập human review

**P7: DONE**, nghiệm thu ngày2026-10-25; P8/P9 đã hoàn tất riêng tại [ATE](../reports/p8_aspect_extraction.md) và [ASC/ABSA](../reports/p9_aspect_sentiment.md). Bộ360 là **human-reviewed sentiment diagnosis set**, người dùng đã xác nhận toàn bộ nhãn/ambiguity/evidence. Reviewer convention `human_reviewer_01`, reviewed_at `2026-10-25`. Chỉ hai trường metadata trống được điền; mọi annotation còn lại giữ nguyên. Bằng chứng: `reports/p7_human_metadata_update.json`.

Báo cáo canonical: [p7_error_cause_analysis.md](../reports/p7_error_cause_analysis.md); số liệu đầy đủ: `reports/p7_human_audit_results.json`. Sáu model active lấy từ p7_completion.json, gồm TabPFN cloud full21K. Chỉ đọc saved predictions/history, không train/predict lại hoặc đổi benchmark/selection/splits.

## Tái lập

```powershell
.venv/Scripts/python.exe -B -m scripts.analyze_error_causes --evaluate-audit --confirm-human-review
.venv/Scripts/python.exe -B -m scripts.finalize_p7_acceptance
.venv/Scripts/python.exe -B -m scripts.test_all
```

Cờ confirm ghi nhận xác nhận human review của người dùng trong tác vụ này; không là chứng thực độc lập danh tính reviewer. Chỉ dùng khi annotation thực sự được con người xem và chấp nhận. Không tự tạo/sửa human_sentiment/ambiguity/evidence. Lệnh mặc định `scripts.analyze_error_causes` giữ kết luận human khi hash annotation không đổi; thay annotation sau xác nhận thì dừng và cần xác nhận mới.

CSV local `data/manual/sentiment_diagnosis_20261024/review_annotation.csv` có annotation_id/review_title/review_text và human_sentiment/ambiguity/evidence/reviewer_id/reviewed_at. Giữ nguyên IDs/title/body. Validator kiểm đúng360, nhãn chỉ negative/neutral/positive, không missing, evidence/reviewer/date đầy đủ; fingerprint/sidecar/source hashes/sampling/ID/rating/proxy/sáu predictions đều khớp. Phiếu hiện tại dùng ambiguity TRUE/FALSE; validator nhận cả boolean lẫn enum cũ clear/mixed/insufficient_context, không sửa file. Evaluator cũ vẫn hỗ trợ uncertain cho phiếu chưa quyết định; nghiệm thu360 hiện hành yêu cầu đúng ba nhãn, không tự chuyển uncertain thành neutral.

Manifest đã cập nhật trạng thái human-reviewed; private_reference.json và sampling bất biến. Tạo lại audit kit không ghi đè annotation người dùng. Full text và sidecar giữ local/data manual ignoreGit; mapping2160 review/model tại `data/interim/p7_diagnosis/human_attribution.parquet`, không publish review text tự động.

## Thiết kế lấy mẫu và mẫu số

- Representative:300 SRS không hoàn lại từ4500test, seed42, inclusion probability300/4500. Disagreement31/300=10,33%; exact hypergeometric95% [7,24%;14,20%] chỉ cho **test population4500** với nhãn người cố định và thiết kế SRS. Không suy rộng train/30K hoặc bao gồm sai số reviewer.
- Diagnostic enriched:60 ca rời nhau,20/proxy class, ưu tiên model cạnh tranh bất đồng proxy. Disagreement37/60=61,67%; không population inference hoặc CI.
- Gộp360: agreement292/360=81,11%, disagreement68/360=18,89%; chỉ mô tả diagnosis. Không dùng tỷ lệ này làm proxy error rate toàn30K. Đây là reused test, không phải independent P10 gold.

JSON/CSV tách ba scope all_360_descriptive_only/representative/diagnostic_enriched. Ranking và delta human−proxy phụ thuộc sampling; không dùng diagnosis để chọn lại mô hình. Canonical test4500 giữ nguyên.

## Quy chiếu lỗi

A=model=human khác proxy; B=model=proxy khác human; C=proxy=human khác model; D=model/proxy đều khác human **và khác nhau**; E=cả ba khớp. A–E rời nhau, cộng bằng support. D theo nghĩa rộng trong yêu cầu bao gồm B; xuất D_inclusive=B+D riêng để không đếm đôi. Human errors=B+C+D, proxy-evaluation errors=A+C+D. Count/share có mẫu số rõ theo scope/model. Đây là mô tả phù hợp nhãn, không chứng minh model đã học noise hoặc nguyên nhân từng lỗi.

## Artifacts và nghiệm thu

- `reports/p7_human_model_metrics.csv`: accuracy/macroF1/weightedF1 và delta, cả ba scope.
- `reports/p7_human_model_classes.csv`: per-class precision/recall/F1/support và deltaF1.
- `reports/p7_human_attribution.csv`: counts/shares A–E, D rộng, tổng lỗi human/proxy.
- `reports/p7_human_classes.csv`, `p7_human_ratings.csv`, `p7_human_ambiguity.csv`, `p7_human_proxy_confusion.csv`: bảng gộp mô tả; bảng tách nhóm và ma trận từng model trong JSON.
- `reports/p0_p7_acceptance.json`: từng pha DONE/DONE WITH LIMITATION, paths kiểm tồn tại, giới hạn REPORTED và hashes VERIFIED.
- `reports/p7_error_diagnosis_validation.json` và preservation cùng tiền tố: kiểm thử và bảo toàn scientific/model/legacy.
- `reports/history/p7_before_human_20261025/`: snapshot trước human review; trạng thái chờ annotation ở đó là lịch sử.

Imbalance neutral train8,77% đã đo; weighted validation sửa62/sai thêm7 neutral, FP236→391, macroF1 giảm0,001994. Human diagnosis chỉ test, không có paired human labels trên validation: không tuyên bố weighting sửa proxy noise hoặc định lượng causal fraction imbalance. Không cần retrain sentiment trước P8 theo bằng chứng hiện có.

Chỉ laptop tiếng Anh; proxy suy từ sao có nhiễu; SemEval-to-Amazon platform/style shift trong laptop; gold thủ công nhỏ là giới hạn P10 còn PENDING. Diagnosis360 không thay independent gold/ABSA. P8/P9 đã DONE; hiện dừng trước P10.
