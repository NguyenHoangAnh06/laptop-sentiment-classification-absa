# Quyết định nghiệm thu P1

## Quyết định của chủ sở hữu hiện tại — 2026-10-09

P1 **DONE**: C1-A/C2-A/C3-A đã được phê duyệt và SemEval Train/Test cộng với JSONL được chấp nhận theo ngoại lệ giáo dục được chủ sở hữu phê duyệt. Xác minh Source/license được miễn; **NOT_VERIFIED**, không bao giờ GIẤY PHÉP PASS/VERIFIED. Không cần tìm kiếm thêm nguồn, thu thập bằng chứng hoặc tải xuống lại. PASS kỹ thuật hiện có được sử dụng lại khi byte không thay đổi. Bảo quản partitions/spans/polarity/provenance gốc và P10 gold độc lập. P2 DONE; P3 bây giờ là DONE; hiện không thực thi P4/later. Bằng chứng P3: `reports/p3_data_analysis_20261009.md`. Bản ghi: `reports/tables/p1_semeval_owner_exception_20261009.json`.

Các tuyên bố gate/status trước đây sau đây là bằng chứng lịch sử, được thay thế bởi quyết định của chủ sở hữu hiện tại; họ không yêu cầu xác minh lại.

## Sự chấp thuận của chủ sở hữu được ghi lại

2026-10-09: C1-A, C2-A, C3-A và C4-B ĐƯỢC CHẤP THUẬN rõ ràng bởi chủ dự án. Scope/conditions: `tables/p1_owner_approval_20261009.json`. P1 KHÔNG phải là DONE vì P1-T03 được ủy quyền SemEval source/license vẫn là BLOCKED. P2 chỉ có trên Amazon hiện đã được ủy quyền; không có quyền P4 split/training/ABSA. Ngoại lệ C2 không làm thay đổi tính độc lập của P10 gold hoặc nguồn gốc AI lịch sử. Các câu lệnh proposal/UNAPPROVED bên dưới là gói tiền quyết định được giữ lại, được thay thế bằng bản ghi phê duyệt này.


Ngày 2026-10-09, Asia/Saigon. **Đề xuất đã chuẩn bị; chưa được phê duyệt. P1 NEEDS review; authorized SemEval nguồn/giấy phép BLOCKED.** Không đổi P0–P13, không chạy P2, không gán lại nhãn hoặc lặp survey/QA evaluation.

Khuyến nghị: chấp nhận coverage của **tập laptop được chọn**, chấp nhận lấy mẫu thương hiệu hiện có với monitoring trước/sau P2; nếu ưu tiên tiến độ, phê duyệt rõ ngoại lệ dùng con người-verified AI-assisted QA cho P1. Giữ nguyên độc lập bộ gold do con người gán nhãn P10 và nguồn gốc thực tế. SemEval vẫn cần bằng chứng authorized acquisition; phê duyệt quản lý không tạo ra quyền dùng dữ liệu.

## Tiêu chí thực sự trong PLAN

- `PLAN_AI.md` P1-T02: “Bộ lọc inspect/verify độc lập theo cách thủ công tập xác thực
  mẫu”; DONE_WHEN: “thủ công mẫu indicates the filtered tập ứng viên represents laptop sản phẩm with acceptable độ chính xác dự đoán (precision).” `PLAN_HUMAN.md` cũng yêu cầu human/source verification độc lập. Technical PASS/human nhãn phê duyệt chưa tự đóng yêu cầu này.
- `configs/acquisition.yaml`, `qa.required_precision=0.95` là ngưỡng độ chính xác dự đoán (precision)
  đã có. Không thấy đã phê duyệt recall/F1 cutoff hoặc yêu cầu numerical độ bao phủ (recall) lower bound.
- P1-T08 yêu cầu có thể tái lập laptop-only lấy mẫu, hạt giống ngẫu nhiên và preserve thương hiệu diversity
  nếu siêu dữ liệu hỗ trợ. Không quy định mọi thương hiệu phải có mặt, quota đều, market-share representativeness hoặc cutoff concentration. Những mức5% unknown/90% top5/2% largest-product trong báo cáo cũ chỉ là đề xuất chưa duyệt.
- P1-T03 yêu cầu authorized SemEval tập huấn luyện v2/Test gold. Week1 EXIT_CRITERIA yêu cầu
  validated filter, Amazon tập ứng viên và SemEval usable. **SemEval là điều kiện nghiệm thu đóng P1 theo PLAN hiện hành**, không chỉ là phụ thuộc mới ở P8.

Các reports/handoff không bổ sung threshold hoặc quyền bypass. Đây là decision packet dưới hai PLAN, không phải nguồn tiến độ hoặc roadmap mới.

## Coverage và độ tin cậy QA

Nguồn: `reports/p1_independent_human_qa.md` (v1 lịch sử), `reports/p1_recall_reliability.md` (thiết kế/interval), `reports/p1_qa_v2_completion_20261009.md` và saved canonical v2 evaluation. Không dùng NEXT_ACTION cũ trong các lịch sử báo cáo làm chỉ dẫn hiện hành.

| Hạng mục | Bằng chứng | Kết luận |
|---|---|---|
| GIỮ độ chính xác dự đoán (precision) |150/150 ngẫu nhiên review và150/150 sản phẩm ngẫu nhiên là laptop theo nhãn | Point100% đạt criterion0.95; review joint95% bounds97.12–100% cũng trên95%, conditional on nhãn |
| Kết hợp độ bao phủ (recall) |89.0767%; doanh95% CI55.4584–99.8455% | Point estimate có ích; không đủ chứng minh true độ bao phủ (recall)>=80% hoặc90% |
| quan sát FN | v1 ngẫu nhiên REJECT1/150; v2 TỪ CHỐI complement1/868 | Rare-event uncertainty còn lớn;2 chẩn đoán sản phẩm FN không vào population estimate |
| Phê duyệt nhãn | human_reviewer_01 cuối cùng verification đã xác nhận; canonical mapping đã phê duyệt | con người phê duyệt hoàn thành; không yêu cầu xác nhận lại reviewer/868 nhãn |
| gán nhãn độc lập | v1 con người được xác minh sau khi hỗ trợ AI; Lịch sử AI v2 không được chỉ định | Chưa đạt strict independent/blind điều kiện nghiệm thu; không được biến unknown thành no-AI |
| Chất lượng dữ liệu cuối cùng |Ứng viên hợp lệ 408,480; clean-English/spam/yield đang chờ P2 | Có đủ tiềm năng quantity; không certify cuối cùng sạch bộ dữ liệu |

**lấy mẫu design có cơ sở:** KEEP review SRS không hoàn lại trên saved valid records, ngẫu nhiên KEEP sản phẩm trên unique IDs. REJECT lấy ngẫu nhiên ordered raw-line các ứng viên, điều kiện parent ngoài được chọn index; v2 loại v1 nguồn lines và lấy 868 units trên complement43,478,054. mẫu size được chọn sau pilot nên old 150 REJECT là certainty units weight1; new units weight50,089.923963; KEEP weight2,723.2. Không naïvely pool1018 REJECT units hoặc dùng tỷ lệ868 accepted. Seed/frozen frames/fingerprints/checksums có evidence. chẩn đoán không góp estimates. Conditional design suy luận xử lý việc cỡ mẫu được chọn sau pilot; không chứng minh gán nhãn độc lập hoặc nhãn đúng. Similar reviews/shared sản phẩm không tự làm review-unit SRS sai khi coi population nhãn cố định; correlated con người mistakes vẫn ngoài interval và không suy ra product-level độ bao phủ (recall) từ review độ bao phủ (recall).

CI dùng exact finite-population stratum bounds và Bonferroni ratio transformation, conservative joint95%; không phải89.08% ± một sai số nhỏ. V2 làm interval hẹp hơn, không làm filter tốt hơn vì rules giữ nguyên. Frame loại260 selected-but-invalid; không gọi đây là whole raw-to-clean quy trình độ bao phủ (recall) hoặc coverage thị trường.

**Rủi ro FP:** zero observed không chứng minh zero accessories. Joint lower độ chính xác dự đoán (precision) 97.12% tương thích với contamination tới khoảng2.88% trong KEEP dưới giả định nhãn/ lấy mẫu; đây là bound, không số contamination đo được. AI anchoring có thể làm độ chính xác dự đoán (precision) thực thấp hơn conditional suy luận. P2 filter QA vẫn phải giữ trong PLAN. **Rủi ro FN:** làm mất nhóm model-only/category-misclassified Chromebook/convertible/ pocket-laptop;4 observed cases cho thấy cơ chế có hệ thống, chưa đo tỷ lệ mỗi nhóm. FN giảm diversity/khả năng khái quát và làm EDA mô tả được chọn tập ứng viên, không toàn bộ laptop universe. Không tự phục hồi FN/tune rule từ evaluated QA.

| Phương án coverage | Lợi ích | Rủi ro / công sức / tiến độ |
|---|---|---|
| **C1-A: chấp nhận selected-pool coverage với CI và giới hạn, không numerical độ bao phủ (recall) cutoff** | Phù hợp mục tiêu30k sạch nếu có, ưu tiên laptop purity; không thêm workload | Không certify coverage cao của laptop universe; báo cáo scope/selection bias; công sức thấp |
| C1-B: đề xuất point độ bao phủ (recall)>=80% | Dễ quản lý; point hiện89.08% sẽ đáp ứng nếu duyệt |80% chỉ minh họa, chưa đã phê duyệt; không chứng minh true độ bao phủ (recall)>=80%; dễ đánh giá quá tự tin |
| C1-C: đề xuất joint95% lower độ bao phủ (recall)>=80% | Bảo thủ, kết luận coverage mạnh hơn | bằng chứng hiện55.46% chưa đạt; cần thiết kế/budget probability QA bổ sung, có thể kéo dài đáng kể; chưa chứng minh cần cho mục tiêu dự án |

Khuyến nghị **C1-A**. Không tạo thêm REJECT nhãn gán chỉ để interval trông đẹp hơn khi chưa có yêu cầu suy luận cụ thể. Nếu chọn C1-C, duyệt mục tiêu/budget trước, không tự lấy thêm mẫu hoặc dừng tùy kết quả đến khi vượt cutoff.

### Independence: quyết định tách biệt với coverage

**C2-A (đề xuất nếu ưu tiên tiến độ):** chấp nhận quy trình con người-verified after AI assistance làm tập xác thực cho **P1 phạm vi filter**, với nguồn gốc giữ nguyên; đây là **ngoại lệ có giới hạn đối với tiêu chí independence hiện hành**, cần người dùng phê duyệt rõ. Không sửa con người nhãn, không tuyên bố fully mù, không coi QA này là sentiment/ABSA gold, không nới độc lập holdout/human gán nhãn P10. Rủi ro còn lại: human/AI anchoring chưa được đo; conditional CI không khắc phục nó.

C2-B: giữ strict điều kiện nghiệm thu; độc lập reviewer/source bằng chứng trên tập xác thực mẫu đã có, không nhất thiết tạo corpus/sample mới. Lợi ích là kiểm tra anchoring/domain judgments thực tế; effort trung bình/cao phụ thuộc nguồn bằng chứng, thêm phụ thuộc con người. Chỉ review4 FN hoặc các case khó **không** thay độc lập ngẫu nhiên KEEP QA. Không thực hiện thêm review này trước khi người phụ trách chọn strict option.

phê duyệt cũ cho nhãn không phải C2-A approval. C2-A cũng không tự thỏa C1/brand/license.

## Chấp nhận thương hiệu

Nguồn: `reports/p1_brand_diversity.md`, saved tables/summary. Denominators: 28,172 được chọn sản phẩm (11 không có valid review) và408,480 valid review. 369 raw strings ->336 siêu dữ liệu categories, **không phải336 đã xác minh manufacturers**.

| Thương hiệu | Sản phẩm | review | Chia sẻ sản phẩm | Chia sẻ review |
|---|---:|---:|---:|---:|
| HP |7,964 |84,121 |28.27% |20.59% |
| ASUS |2,792 |79,393 |9.91% |19.44% |
| Acer |2,148 |63,161 |7.62% |15.46% |
| Lenovo |4,940 |52,182 |17.54% |12.77% |
| Dell |3,656 |47,000 |12.98% |11.51% |
| KHÔNG XÁC ĐỊNH |300 |1,237 |1.0649% |0.3028% |
| mơ hồ |13 |68 |0.0461% |0.0166% |

Top5 products76.32%, review79.77%; unknown+ambiguous products1.11%, review0.3195%. 664 sản phẩm metadata/title disagreement (2.36%) là flags, chưa bằng chứng xác nhận siêu dữ liệu sai. Largest product1.2527% review; top100 products22.83%. HHI products0.14689, review0.13762; effective category numbers12.76/11.06. Không có market comparator để gọi đây là thị phần hoặc chứng minh population representativeness.

**Bổ sung cần thiết, nhỏ:** đối chiếu thương hiệu trên hiện có saved5000-review survey mẫu với products.csv, không đọc/khảo sát lại corpus. VERIFIED5000 unique IDs, 2805 sản phẩm,94 siêu dữ liệu categories, max68 reviews/product, đủ ratings1–5; zero raw-brand discrepancies so với saved sản phẩm mapping. Top5 review share79.88% (pool79.77%), unknown/ambiguous13 review0.26%,11 products0.3922%.242 categories vắng mẫu chứa3188 ứng viên review,0.7805% pool. Không đo final30k coverage; không chứng minh mọi long-tail group được preserve. Evidence/counts/hashes: `reports/tables/p1_acceptance_decision_20261009.json`.

**Overall cảm xúc:** review-heavy brands/products có thể chi phối vocabulary, huấn luyện số mẫu hỗ trợ và aggregate thước đo; macro F1 cân bằng cảm xúc lớp, không cân bằng brands. Đây là risk, chưa có mô hình bias measurement. thương hiệu siêu dữ liệu không cần làm đặc trưng; không drop valid review chỉ vì thương hiệu UNKNOWN. **ABSA:** SemEval huấn luyện không dùng thương hiệu map Amazon; concentration ảnh hưởng Amazon khía cạnh mix/gold coverage/transfer evaluation. thương hiệu correction không tạo khía cạnh nhãn hoặc giải quyết SemEval-to-Amazon shift. gold300–500 nhỏ nên không hứa thước đo ổn định cho từng thương hiệu hiếm.

| Phương án thương hiệu | Lợi ích | Rủi ro, công sức và tiến độ |
|---|---|---|
| **C3-A: accept hiện tại ứng viên metadata/sampling với giới hạn; không uniform quotas** | Pool/sample bằng chứng supports major-brand coverage; giữ nguyên domain/raw nguồn gốc; workload thấp | Long tail có thể thiếu số mẫu hỗ trợ; requires trước/sau brand/product/rating ledger tại P2, báo cả absent/unknown groups; chưa certify final-clean diversity |
| C3-B: cải thiện siêu dữ liệu trước nghiệm thu | Có thể giảm alias/reseller/model ambiguity, tăng độ tin cậy thương hiệu nhận định từ dữ liệu | review664 flags/313 unknown-ambiguous sản phẩm cần nguồn bằng chứng; chưa đo benefit; effort trung bình/cao, trì hoãn P1; không chắc cải thiện cảm xúc nhãn |
| C3-C: targeted tập xác thực nếu cần manufacturer-level claims | bằng chứng tập trung vào outliers có ảnh hưởng hoặc thương hiệu cần báo cáo riêng | Targeted mẫu không chứng minh toàn336 categories đúng; effort vừa tùy subset; chỉ justified nếu claims/độ nhạy kết quả yêu cầu |

Khuyến nghị **C3-A**. Tiêu chí qualitative đề nghị phê duyệt: lấy mẫu không giới hạn vào whitelist leading thương hiệu, giữ siêu dữ liệu provenance/UNKNOWN riêng, không loại review hợp lệ vì thương hiệu nhỏ, báo brand/product/class phân bố và long-tail hàm mất mát trước/sau cuối cùng selection. Không đặt uniform thương hiệu quotas hoặc dùng các heuristic5%/90%/2% như scientific nghiệm thu đã phê duyệt. P1 approve **ứng viên lấy mẫu strategy**; cuối cùng sạch bảo toàn phải có bằng chứng ở P2, không tick cuối cùng bộ dữ liệu hoặc đánh dấu mọi thương hiệu đã có support.

## SemEval: điều kiện nghiệm thu milestone và phụ thuộc kỹ thuật

Local XML/schema/offset/lossless chuẩn hóa PASS đã có; nguồn user-supplied mirror/revision/authorized terms bằng chứng chưa đủ. Không thực hiện web/source review lại, download/login/terms nghiệm thu hoặc tuyên bố licence đã giải quyết.

| Công việc | Phụ thuộc SemEval? | Hệ quả |
|---|---|---|
| Đóng toàn bộ P1/P1-T03/week1 exit | Có theo PLAN | BLOCKED đến khi có authorized source/terms bằng chứng; phê duyệt quản lý không thay bằng chứng |
| P2 Amazon quality/cleaning/rating nhãn; P3 Amazon EDA | Không về kỹ thuật | dữ liệu đầu vào Amazon có; vẫn chờ gate/explicit scheduling authorization hiện hành |
| P4 Amazon các tập đã chia; P5/P6/P7 tổng thể models/errors | Không về dữ liệu SemEval | Vẫn phụ thuộc clean/splits và đúng phase/resource authorization; không được tự triển khai sớm |
| Các bài kiểm tra P8/P9 ATE/ASC/SemEval | Có | Không tokenize/train/derive huấn luyện dữ liệu từ nguồn chưa authorized |
| P10 Amazon sampling/human cảm xúc+khía cạnh gán nhãn | Không cần SemEval để annotate | Thuộc P10 theo PLAN; đánh giá SemEval-trained ABSA phụ thuộc authorized models/data |
| P11 hoàn thành dự án ABSA app/P13 hoàn thành | Có đầu ra ABSA | Overall-only subset không bằng hoàn thành toàn bộ app/project |

**C4-A:** giữ điều kiện nghiệm thu, cung cấp exact acquisition source/revision và bằng chứng quyền truy cập/terms cho gốc XML hoặc mirror permission được xác minh; nếu phải thay byte, cần provenance/integrity mới, không silent overwrite. Ưu tiên nếu đã có bằng chứng có thể cung cấp. Không yêu cầu người dùng chỉ “approve giấy phép”.

**C4-B (đề xuất để tránh đình trệ nếu bằng chứng chưa có):** phê duyệt rõ ngoại lệ phụ thuộc **cho Amazon-only P2** sau khi C1/C2/C3 được quyết định. Giữ P1 NEEDS review, P1-T03 BLOCKED, không dời tác vụ sang giai đoạn khác hoặc giảm requirement authorized SemEval; không mở P3/training/ABSA bằng quyết định này. Đây là scheduling exception cần phê duyệt, không có sẵn trong PLAN và **chưa được áp dụng**. Nếu không duyệt, không triển khai toàn bộ P2 dù Amazon không phụ thuộc kỹ thuật vào SemEval.

## Bảng quyết định cuối cùng

| Cổng | Tiêu chí quy định | Bằng chứng | Trạng thái | Đề xuất | Rủi ro còn lại | Quyết định cần phê duyệt |
|---|---|---|---|---|---|---|
| Độ tinh khiết Precision/domain | P1-T02 chấp nhận được độ chính xác dự đoán (precision); config0.95 | ngẫu nhiên KEEP150/150 review và các sản phẩm; có điều kiện review thấp hơn97.12% | Technical/numerical PASS; chấp nhận tổng thể đang chờ | Giữ filter; chấp nhận sampled purity cùng limitations | Conditional nhãn; zero FP không bằng chứng xác nhận zero contamination | Xác nhận chấp nhận ứng viên tập ứng viên làm đầu vào P2, không cuối cùng sạch certification |
| Bảo hiểm | QA/sampling adequacy; không độ bao phủ (recall) cutoff đã phê duyệt | độ bao phủ (recall)89.08%, CI55.46–99.85%;4 FN cases phân biệt strata | Điểm có sẵn; độ chắc chắn độ bao phủ (recall) cao KHÔNG CÓ KẾT LUẬN | **C1-A** selected-pool phạm vi, không additional large QA | Lựa chọn bias/FN groups/rare-event không chắc chắn | Chấp nhận phạm vi và uncertainty; hoặc chọn C1-B/C với mục tiêu rõ |
| Độc lập | Xác minh manual/source độc lập | con người review DONE cuối cùng; v1 AI-assisted/v2 không xác định | Tính độc lập nghiêm ngặt KHÔNG ĐÁP ỨNG | **C2-A** bounded exception P1 chỉ nếu ưu tiên tiến độ | Lỗi Anchoring/label ngoài CI | Duyệt ngoại lệ cụ thể; hoặc chọn C2-B giữ strict điều kiện nghiệm thu và độc lập review |
| Đa dạng thương hiệu | Có thể tái tạo đa dạng laptop chỉ có sampling/preserve nếu được hỗ trợ | Danh mục Pool336, không xác định0.32% review; mẫu94 categories/top5 79.88% | Analysis/sample tập xác thực PASS; chấp nhận đang chờ | **C3-A** tiêu chí định tính + sổ cái before/after P2 | Tổn thất support/metadata validity/final-selection đuôi dài | Duyệt hiện tại ứng viên lấy mẫu strategy/monitoring; không certify final30k |
| giá trị | XML được ủy quyền P1-T03; nguồn có thể sử dụng được trong tuần 1 | Tính toàn vẹn kỹ thuật cục bộ PASS; Không có bằng chứng rights/source | BLOCKED | **C4-A** bằng chứng; nếu unavailable xét C4-B | Giấy phép chưa được giải quyết, ABSA không thể tiếp tục | Cung cấp authorized bằng chứng; hoặc chỉ duyệt scheduling exception Amazon P2 |
| Khởi động P1 completion/P2 | Các cổng P1 hiện hành đã được đáp ứng hoặc được sửa đổi rõ ràng; trạng thái pha trung thực | Chưa có approvals/evidence bổ sung | P1 CẦN review; đầy đủ P2 KHÔNG ĐƯỢC ỦY QUYỀN | Không tick hoàn thành | phê duyệt nghiệm thu khác bằng chứng xác nhận nguồn quyền sử dụng | C1–C3 + C4-A bằng chứng để đóng P1; hoặc C1–C3 + C4-B để P2 Amazon tiến hành nhưng P1 vẫn mở |

**Technical tập xác thực PASS** = schema/formula/source bindings có evidence. **Statistical độ tin cậy** = CI conditional on labels/design, độ bao phủ (recall) vẫn không chắc. **con người phê duyệt** = nhãn đã đã phê duyệt, không bằng process independence hoặc nguồn rights. **dữ liệu-quality nghiệm thu** = owner chọn mức risk/scope cho ứng viên đầu vào; chưa phải cuối cùng clean-tiếng Anh dữ liệu. **Milestone completion** = các điều kiện nghiệm thu thực sự satisfied hoặc criterion/scheduling exception được phê duyệt rõ, không suy ra từ tests/label approval.

## Verification, thay đổi và bước tiếp theo

Tạo báo cáo này và machine bằng chứng JSON; cập nhật liên kết decision packet trong hai PLAN, remaining-gates header và handoff. Giữ nguyên giai đoạn IDs/titles/objectives/ checkbox acceptance. Không đổi code/config/filter/raw/annotations/QA calculations. Previous143 kiểm thử passed/41 được bảo vệ hàm băm PASS là REPORTED, không tính là kiểm thử lần chạy mới. New saved-sample checks ở trên đã xác minh bằng JSON/CSV số lượng và assertions; nguồn hàm băm bindings/phase sequence/document links được kiểm tra cho tác vụ này. đã xác minh hiện tại tác vụ:41 được bảo vệ SHA256 checks PASS;5 decision-evidence nguồn hàm băm PASS;P0–P13 sequence/shared hiện tại trạng thái PASS. No được bảo vệ data/config/annotation changed; no new pytest/evaluation/training run.

BLOCKED: authorized SemEval bằng chứng; strict độc lập QA chưa đạt khi chưa có đã phê duyệt exception. NEXT_ACTION: owner chọn C1/C2/C3 và C4-A bằng chứng hoặc C4-B scheduling exception. Không cần thêm audit/annotation tốn công để đưa ra quyết định. Chưa có quyết định phê duyệt trong tác vụ này, nên P1 vẫn NEEDS review và P2 chưa chạy.

Giới hạn bắt buộc: laptop-only findings, nhãn đại diện suy từ số sao-nhiễu nhãn, SemEval-to-Amazon platform/style shift trong laptop review, small bộ gold do con người gán nhãn set (sentiment/ABSA gold hiện chưa có). Không claim market coverage/production readiness.
