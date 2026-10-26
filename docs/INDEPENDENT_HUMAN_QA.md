# Hướng dẫn độc lập con người QA — P1

Đây là QA xác minh **phạm vi sản phẩm laptop**, không phải gán cảm xúc hay ABSA. con người-verified đánh giá đã chạy; độc lập tập xác thực nghiệm thu vẫn NEEDS review. Nhãn cũ AI-assisted/user-approved không được sao chép sang bộ mẫu này.

## 1. Mở đúng hai file

- `data/manual/independent_qa/p1_v1/product_annotation.csv`: 150 sản phẩm độc đáo
  ngẫu nhiên từ KEEP và 50 sản phẩm gần ranh giới, trộn thứ tự.
- `data/manual/independent_qa/p1_v1/review_annotation.csv`: 150 review KEEP ngẫu
  nhiên, 150 review REJECT ngẫu nhiên và 100 review chẩn đoán riêng, trộn thứ tự.

Mở bằng Excel/LibreOffice hoặc trình sửa CSV giữ đúng encoding UTF-8 và dấu ngoặc cho các ô có nhiều dòng. Import các cột ID **dưới dạng văn bản**; không đổi ID, văn bản, siêu dữ liệu hoặc nguồn evidence. Không sắp xếp riêng một cột; có thể sắp xếp cả bảng. Lưu lại **CSV UTF-8**, không thay bằng `.xlsx`. Có thể giữ bản gốc và gán nhãn trên bản sao; CLI nhận đường dẫn bản sao bằng `--product-annotations` và `--review-annotations`.

Không mở `private_predictions.json` hoặc `manifest.json` trong lúc gán nhãn: chúng chứa prediction/tầng lấy mẫu dành cho đánh giá sau. File gán nhãn không chứa nhãn, quyết định, lý do lọc hoặc tên tầng của pipeline. Người gán nhãn không dùng AI nhãn, QA cũ hoặc kết quả filter để quyết định con người nhãn.

## 2. Chỉ điền bốn cột con người

| Cột | Cách điền |
|---|---|
| `human_label` | `laptop`, `non_laptop` hoặc `uncertain`; để trống nếu chưa xem |
| `human_evidence` | Bắt buộc với mọi nhãn đã điền, kể cả uncertain: bằng chứng không rỗng mô tả nguồn đã kiểm tra; chi tiết và ngày được khuyến nghị |
| `human_notes` | Giải thích quyết định, mâu thuẫn nguồn, model/variant, giới hạn bằng chứng |
| `human_error_reason` | Không bắt buộc; mã nguyên nhân nghi vấn dựa trên bằng chứng của bạn, không cần biết quy trình prediction |

Ví dụ **cách viết bằng chứng**, không phải nhãn cho bất kỳ dòng thật nào: `metadata SHA/line trong source_evidence; mô tả xác nhận thiết bị hoàn chỉnh có CPU/RAM/keyboard; trang hãng <URL> mục specifications, kiểm tra YYYY-MM-DD`. Nếu chỉ có siêu dữ liệu, ghi rõ `metadata-only`, trường/đoạn đã đọc và lý do đủ bằng chứng. Nếu không đủ, chọn `uncertain`, ghi nguồn đã thử và phần còn thiếu.

Mã `human_error_reason` hợp lệ: `accessory`, `tablet_only`, `desktop`, `other_non_laptop`, `convertible_2in1`, `model_only_title`, `missing_laptop_category`, `misleading_title_category`, `missing_metadata`, `incorrect_metadata`, `linkage_problem`, `insufficient_evidence`, `other` hoặc trống. Có thể ghi nhiều chi tiết trong ghi chú, nhưng chỉ một mã trong cột này. Sau đánh giá, mismatch không có mã sẽ được báo `unclassified`; script không tự suy đoán nguyên nhân bằng AI.

## 3. Tiêu chí phạm vi độc lập

- `laptop`: máy laptop/notebook/Chromebook hoàn chỉnh; thực sự laptop chuyển đổi
  hoặc 2-in-1 cũng thuộc phạm vi. Có chữ tablet không tự động đồng nghĩa ngoài phạm vi.
- `non_laptop`: phụ kiện (bag/sleeve/charger/dock/stand/adapter/parts...), tablet
  thuần, desktop hoặc sản phẩm khác. Một review nói “works with my laptop” về một charger vẫn là review của charger, không phải laptop.
- `uncertain`: không đủ bằng chứng để xác định đúng thiết bị/model/variant hoặc
  review–siêu dữ liệu linkage. Không ép nhãn để hoàn thành số lượng.

Đọc title, categories, description, đặc trưng và details; không chỉ tìm keyword laptop trong review. Với review, xác định sản phẩm thực sự được review theo `product_id`/metadata/evidence, đồng thời kiểm tra nội dung có mâu thuẫn rõ ràng hoặc lỗi liên kết không. Rating/sentiment và ngôn ngữ không phải tiêu chí QA phạm vi.

`source_evidence` là locator vào bản chụp trạng thái gốc: file, SHA256 và physical line. `product_url` chỉ là link tra cứu được tạo từ parent ID, **chưa được truy cập hoặc xác minh**, có thể không hoạt động hoặc chuyển sang variant khác. Có thể dùng trang hãng/model specifications hoặc nguồn đáng tin khác, ghi URL thực đã đọc. Không coi URL được tạo sẵn hay SHA256 là bằng chứng tự động chứng nhận laptop. Nếu cùng sản phẩm xuất hiện nhiều lần, kiểm tra cùng bằng chứng và giữ quyết định nhất quán; script sẽ báo các nhãn definitive trái ngược để bạn adjudicate.

## 4. Thiết kế lấy mẫu và giới hạn đánh giá

Nguồn thực là Amazon review 2023 **Electronics**, hai gzip native và báo cáo toàn bộ lần chạy tại `data/interim/feasibility/electronics_full_laptop_30k/report.json`. Join key là `parent_asin`, không dùng variant `asin` để fallback. Rule hiện hành `configs/acquisition.yaml` / `src/data/laptop_filter.py` yêu cầu category trong `Laptops/Traditional Laptops/Laptop Computers/Notebook Computers` và title chứa `laptop/notebook/chromebook`; accessory category/title bị loại trước. Description, đặc trưng, review văn bản và rating không tham gia sản phẩm classifier. KEEP được lưu còn qua kiểm tra văn bản không rỗng và rating 1–5 trong `src/data/feasibility.py`.

hạt giống ngẫu nhiên 42, các stream dùng hạt giống ngẫu nhiên độ lệch ký tự cố định:

- sản phẩm ngẫu nhiên: SRS không hoàn lại, 150 IDs từ danh sách sorted 28.172 KEEP
  sản phẩm; mỗi sản phẩm có xác suất như nhau, không weighting theo review count.
- sản phẩm boundary: reservoir 50 từ frame siêu dữ liệu có laptop/category/convertible
  hint nhưng bị REJECT, hoặc KEEP có chuyển đổi hint; loại 150 ngẫu nhiên sản phẩm IDs. Đây là subset chẩn đoán, không mẫu đại diện toàn Electronics.
- review KEEP: SRS 150 indices từ **408.480 valid saved records**, không lấy từ
  mẫu 5.000 có rating/product caps. Mỗi record có xác suất như nhau.
- review REJECT: chọn ngẫu nhiên không hoàn lại một danh sách raw physical lines,
  giữ 150 các ứng viên đầu theo thứ tự ngẫu nhiên có parent ngoài được chọn siêu dữ liệu index. Frame là **43.478.204 records**. Đây là SRS có điều kiện REJECT; không dùng 150 dòng đầu nguồn hoặc chỉ sản phẩm trong QA cũ. Gzip được đọc tuần tự để lấy các các ứng viên và kiểm tra EOF/CRC; không gọi lại toàn bộ Survey, không tạo lại pool.
- review chẩn đoán: reservoir 100 records từ phần KEEP còn lại, văn bản ngắn dưới
  5 normalized whitespace từ hoặc sản phẩm title có tablet/convertible/2-in-1/ detachable hint. lấy mẫu chỉ dùng tín hiệu để ưu tiên kiểm tra, không gán nhãn. Frame này **KEEP-only**, không đại diện và không phải một search đầy đủ false negatives. ngẫu nhiên REJECT là nguồn kiểm tra trường hợp bỏ sót đại diện đã chọn.

Hai nhóm review ngẫu nhiên tạo frame đánh giá gồm valid KEEP và siêu dữ liệu REJECT. **260 selected-but-invalid review không thuộc frame**. Vì thế các thước đo sau không được gọi là độ bao phủ (recall) của toàn bộ quy trình validity/cleaning trên 43.886.944 records. Việc này không thay đổi filter hoặc tiêu chí P1; nếu sau này cần audit validity failures, đó là một frame riêng cần thêm mẫu và nhãn.

Script không gộp chẩn đoán vào thước đo đại diện và không dùng confusion matrix 150/150 để giả định tỉ lệ KEEP/REJECT toàn corpus là 50/50. Với hai tầng review, ước lượng totals theo trọng số `N_h/n_h`, rồi tính độ chính xác dự đoán (precision), độ bao phủ (recall), F1. Đây là point estimates, không exact population counts. Assessment hiện tại có Wilson intervals cho từng ngẫu nhiên stratum; weighted recall/F1 intervals chưa triển khai. Khi không thấy FN trong 150 REJECT, không kết luận population độ bao phủ (recall) thực sự bằng 100%: lỗi laptop hiếm trong Electronics có thể chưa được bắt gặp. sản phẩm ngẫu nhiên KEEP chỉ cho độ chính xác dự đoán (precision); không đủ frame để tính recall/F1 sản phẩm.

Blank/uncertain được báo riêng, không đổi thành non_laptop và không điền tự động. Nếu một tầng ngẫu nhiên còn unresolved, thước đo quần thể review bị giữ `null`; báo cáo vẫn có confusion trên các dòng resolved và bounds của laptop fraction trong mỗi tầng. Các sản phẩm có definitive nhãn mâu thuẫn cũng chặn thước đo đại diện cho đến khi adjudicate. chẩn đoán còn uncertain vẫn không được dùng cho metrics. Không tự đánh dấu hai danh sách kiểm tra hoàn thành bằng script.

## 5. Chạy đánh giá sau khi gán nhãn

Từ repository root, khi đã tự kiểm tra bằng chứng:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.evaluate_independent_qa `
  --kit-dir data/manual/independent_qa/p1_v1 `
  --annotator "TEN_HOAC_MA_NGUOI_GAN_NHAN" `
  --confirm-independent-human `
  --output-dir reports/independent_qa/p1_v1_evaluation
```

Thay người gán nhãn bằng tên hoặc mã của bạn. Flag là lời xác nhận bạn đã thực hiện độc lập human/source verification; chương trình không thể tự chứng minh ai đã gán nhãn. Nếu làm trên bản sao, thêm:

```powershell
--product-annotations path/to/product_annotation_completed.csv `
--review-annotations path/to/review_annotation_completed.csv
```

Mở `reports/independent_qa/p1_v1_evaluation/report.md`. Kèm theo có `evaluation.json` (metrics/bounds/provenance), `comparisons.csv` (từng dòng), `errors.csv` (FP/FN) và `strata.csv` (confusion/counts từng tầng). đầu ra phải là thư mục mới. Nếu sửa annotation/adjudicate, chạy với tên đầu ra khác, ví dụ `p1_v1_evaluation_round2`. gán nhãn và predictions không bị sửa. Chương trình từ chối duplicate/missing IDs, cột bằng chứng nguồn bị đổi, invalid nhãn, bằng chứng con người trống hoặc sidecar prediction bị sửa.

Sau đó yêu cầu review kết quả P1 và các dòng lỗi/uncertain; chỉ cập nhật danh sách kiểm tra khi thực tế thủ công bằng chứng và đánh giá đã được xem xét theo plan.

## 6. Tái tạo và kiểm thử

Không cần chạy lại bước chuẩn bị để gán nhãn. Khi thực sự cần một bộ mới:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.prepare_independent_qa `
  --run-dir data/interim/feasibility/electronics_full_laptop_30k `
  --output-dir data/manual/independent_qa/p1_v1_reproduced --seed 42
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

Lệnh chuẩn bị đọc raw nguồn lớn nhưng chỉ trích QA; dùng tài nguyên ceilings hiện hành, không download, không sửa raw/pool/QA cũ. Cùng snapshot/config/seed/code tạo cùng gán nhãn CSV; timestamps và tên đầu ra bản kê có thể khác. Predictions, lựa chọn frames, số lượng và SHA256 được lưu trong kit. Tất cả dataset/annotation nằm dưới `data/` đã git-ignore. Không có training/P2 hay con người nhãn tự tạo.

Giới hạn dự án: laptop-only findings; Amazon nhãn đại diện suy từ số sao-nhiễu nhãn; SemEval-to-Amazon platform/style shift trong cùng laptop phạm vi; small thủ công annotated bộ dữ liệu gold. Bộ QA phạm vi này không thay thế Amazon sentiment/ABSA bộ dữ liệu gold.

## đánh giá hiện tại — 2026-10-08
Người dùng xác nhận review/approval bởi `human_reviewer_01`, có một số nhãn được điều chỉnh sau gợi ý AI. CLI nhận `--ai-assisted-review` để xuất nguồn gốc `human_verified_after_ai_assistance`, không claim fully mù gán nhãn. Flag `--confirm-independent-human` xác nhận con người verification/approval để chạy tooling, không tự đóng độc lập nghiệm thu gate. Quy trình không AI-assisted vẫn theo hướng dẫn mù verification ở trên; không suy ra process từ template blinded.

bằng chứng `Amazon title + category` được chấp nhận khi schema/evidence presence và nguồn binding hợp lệ theo yêu cầu người dùng. Inspection date không phải hard bộ kiểm tra gate. Results: `reports/independent_qa/p1_v1_evaluation/`; readiness/uncertainty: `reports/p1_independent_human_qa.md`.

## Xác nhận cuối cùng của chủ dự án? 2026-10-09
Chủ dự án tuyên bố con người review/approval cuối cùng của tất cả các dự án nhãn gán hiện có. Sử dụng chú thích hiện có `human_reviewer_01`; không yêu cầu xác nhận lại cho mỗi tập tin. siêu dữ liệu ràng buộc SHA256 mới nhất: `reports/independent_qa/human_review_20261009/review_confirmation.json`. con người review HOÀN THÀNH chỉ áp dụng cho nhãn review; Việc chấp nhận independence/QA/phase vẫn riêng biệt. Lưu giữ lịch sử được AI hỗ trợ đã biết; lịch sử không xác định không có nghĩa là không có AI. CSV gốc schemas/manifests được giữ nguyên; đạo hàm chính tắc v2 và mô hình cơ sở nhãn bị thiếu được ghi lại trong `reports/annotation_human_review_20261009.md`. Các tuyên bố chờ đợi trước đó-con người là lịch sử.
