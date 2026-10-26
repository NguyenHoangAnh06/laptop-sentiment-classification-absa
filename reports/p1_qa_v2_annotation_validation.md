# QA v2 — Kiểm tra gán nhãn ngày 2026-10-09

**BLOCKED_VALIDATION; P1 NEEDS review / NOT hoàn thành.** Không sửa gán nhãn, không chạy evaluator chính thức, không thay filter hoặc tạo huấn luyện bộ dữ liệu.

## Kết quả đã kiểm chứng

`data/manual/independent_qa/p1_v2/review_annotation.csv` đọc được bằng strict UTF-8, 868 dòng, lược đồ đúng; giữ ID và các trường CSV dưới dạng chuỗi. Không trùng lặp annotation/review IDs, khớp toàn bộ danh sách mẫu ban đầu. 868 fingerprint nguồn khớp sidecar; không trùng review v1. Sidecar, đã cố định pilot manifest/evaluation và lấy mẫu design PASS. Không có evidence/notes trống; 868 lỗi lý do trống được enum hiện hành cho phép, không phải lỗi bắt buộc.

Nhãn nộp: **ACCEPT 1, REJECT 867**. Cả 868 nằm ngoài enum hiện hành `laptop/non_laptop/uncertain`. Đây là số đếm chuỗi đã nộp, chưa phải số laptop được xác nhận hay confusion matrix. Không tự ánh xạ nhãn hoặc suy đoán từ filter. Danh sách cần xử lý: `independent_qa/p1_v2_validation_20261009/annotation_issues.csv`. tập xác thực JSON có thiếu số lượng, checks và SHA256 của gán nhãn đã nộp.

BLOCKED: cần xác nhận ACCEPT=laptop/REJECT=non_laptop, mã con người reviewer và quy trình có/không tham khảo AI. Yêu cầu xác nhận đã gửi trong phiên làm việc. NEXT_ACTION: khi được xác nhận, dùng bản dẫn xuất có mapping/provenance rõ ràng, giữ nguyên CSV nộp và kit gốc; chạy evaluator vào thư mục mới. Không giả lập con người xác nhận hoặc đóng độc lập nghiệm thu điều kiện nghiệm thu bằng sự có mặt của CSV.

## Lấy mẫu và so sánh v1/v2

đã xác minh v1 đã cố định bằng chứng: ngẫu nhiên KEEP 150 TP/0 FP; ngẫu nhiên REJECT 1 FN/149 TN. V1 weighted độ bao phủ (recall) 58,4934%, conservative joint 95% CI 17,9234–99,1153% theo `tables/p1_recall_reliability.json`; đây là kết quả v1, không phải kết quả v2. V1 nguồn gốc con người verification after AI suggestions vẫn giữ nguyên.

V2 là 868 SRS trên REJECT complement N=43.478.054, không giao nhau v1. Không gọi hai mẫu là hai SRS độc lập từ cùng frame: cỡ mẫu mới phụ thuộc pilot. Estimator kết hợp hợp lệ theo thiết kế có điều kiện: 150 REJECT pilot là known units weight 1; v2 weight 43.478.054/868; KEEP weight 408.480/150. Không dùng ACCEPT/868 làm độ bao phủ (recall) và không pooling N/(150+868). Recall/precision/F1 v2 và CI hiện **NOT_MEASURED** do validation/provenance đang chờ. 260 selected-but-invalid review ngoài frame đánh giá; không suy ra raw-to-clean độ bao phủ (recall).

## Dòng cần phân tích sau xác nhận

Dòng ACCEPT: gán nhãn `32bf11df68190815f34e517b`, sản phẩm `B0BB842RV1`. siêu dữ liệu title ghi GPD Pocket 3 / notebook laptop; category lưu `Tablets`. con người ghi chú mô tả complete clamshell pocket laptop và category misleading. Đây là ứng viên lỗi coverage do siêu dữ liệu category, **chưa kết luận FN chính thức** trước xác nhận ý nghĩa nhãn. Không truy cập nguồn hãng để xác minh độc lập trong lần này. Không tạo mới bằng chứng hay lỗi lý do của người gán nhãn. Nếu xác nhận, đánh giá quy tắc category kết hợp title/model/spec và độ chính xác dự đoán (precision) tradeoff trong một audit riêng; không điều chỉnh filter bằng QA trước chốt evaluation.

## Chấp nhận và lộ trình

thương hiệu analysis đã có đủ các tệp kết quả: 28.172 ứng viên products/408.480 valid review, top-five review share 79,77%, unknown/ambiguous review share khoảng 0,32%. Đây là saved candidate-pool analysis, chưa phải diversity của sạch huấn luyện dữ liệu. thương hiệu nghiệm thu vẫn NEEDS review; không có numeric recall/F1/brand cutoff được phê duyệt. hiện có KEEP độ chính xác dự đoán (precision) criterion 0,95 đạt có điều kiện theo nhãn v1; không tự hoàn tất independence/coverage/product QA gates.

Roadmap P0–P13 đã đối chiếu: P0 hoàn tất theo prior bằng chứng; P1 chưa hoàn tất; P2–P13 chưa có các tệp kết quả đáp ứng toàn bộ acceptance. Công việc tiếp theo an toàn đã thực hiện là revalidation quy trình SemEval hiện có, không BIO/training hoặc thay official train/test. huấn luyện/kiểm thử: 3.045/800 sentences, 2.358/654 vị trí cụm từ; schema/offset/polarity/round-trip/integrity PASS, conflict 45/16 giữ nguyên. tập huấn luyện có 12 duplicate-text groups; huấn luyện/kiểm thử có shared text/ID 227, cần chính sách đánh giá trước xây dựng mô hình. Licence/authorized nguồn gốc vẫn BLOCKED. Không có đủ phụ thuộc để xuất sạch huấn luyện bộ dữ liệu hay khởi động ML/DL.

## Tái hiện và bảo toàn

```powershell
.\.venv\Scripts\python.exe -B -m scripts.validate_supplemental_annotations --kit-dir data/manual/independent_qa/p1_v2 --output-dir reports/independent_qa/NEW_VALIDATION
.\.venv\Scripts\python.exe -B -m scripts.normalize_semeval_p1 --report reports/independent_qa/NEW_SEMEVAL_REPORT.json
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

đã xác minh: toàn bộ suite **140 passed in 3,94s**; targeted supplemental/SemEval **12 passed in 0,84s**. kiểm thử mới dùng tổng hợp dữ liệu mẫu để xác minh alias bị từ chối, đầu vào byte giữ nguyên và nguồn tampering được phát hiện; không bộ gold do con người gán nhãn. 41 files trong đã cố định bảo toàn mô hình cơ sở SHA256 **PASS**; đầu ra mới `independent_qa/p1_v2_validation_20261009/preservation.json`. Không sửa phụ thuộc hoặc được bảo vệ datasets/configs/v1 reports. SemEval JSONL identical được quy trình chấp nhận; revalidation báo cáo lưu riêng.

Giới hạn: laptop-only findings; nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong laptop phạm vi; small thủ công annotated sentiment/ABSA bộ dữ liệu gold vẫn chưa có. phạm vi QA không thay P10 gold.
