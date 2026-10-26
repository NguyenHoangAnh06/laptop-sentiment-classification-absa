# PHÂN TÍCH cảm xúc CỦA KHÁCH HÀNG CHO laptop review — KẾ HOẠCH DỰ ÁN

## Kế hoạch hiện hành — cập nhật 2026-10-24

Theo yêu cầu mới: so sánh gradient boosting (XGBoost), tabular deep learning (TabM), tabular foundation models (TabPFN-3 và TabPFN-3.5) trên cùng frozen semantic representation với Transformer fine-tune end-to-end; majority chỉ sanity. Loại TF-IDF/LR/SVM/DT khỏi benchmark active, giữ toàn bộ bằng chứng cũ là **LEGACY**. Không triển khai ABSA trong tác vụ này; các pha ABSA/gold/app dài hạn giữ nguyên ngoài phạm vi refactor.

- [x] P0: môi trường/CUDA/dependency và hai phiên bản TabPFN tường minh đã xác minh.
- [x] P1: nguồn Amazon/hash/metadata và QA được tái xác minh, không tải/lọc lại.
- [x] P2: giữ dataset 30K và nhãn proxy, kiểm tra toàn vẹn/whitelist feature.
- [x] P3: bổ sung readiness/neutral/độ dài/resource risks, không chạy lại EDA cũ.
- [x] P4: giữ split 21K/4,5K/4,5K; canonical title + body, embeddings frozen dùng chung, cache/mapping/labels riêng, token Transformer riêng; QA/leakage và re-encode 30K PASS.
- [x] P5: hoàn tất tuần tự với LIMITED/SUBSAMPLED TabPFN-3=10000/TabPFN-3.5=1500; WARNING RSS E03=6,48GB. Baseline reuse; resource/version/alignment/metrics xác minh; không tuyên bố TabPFN full-data.
- [x] P6: canonical BERT full21000 train, unweighted/balanced; chọn unweighted epoch3 bằng validation macro F1, reload và một lượt test PASS. Không reuse test result BERT body-only.
- [x] P7: benchmark đủ6model, comparison/cost/error analysis và giới hạn proxy; 249tests PASS. Tổng thể LIMITED do TabPFN subsampled/RSS warning; human gold/ABSA/app còn ngoài phạm vi.

Xem `docs/MODEL_STACK_REFACTOR.md`, đầu `PLAN_AI.md`, `reports/model_stack_refactor_completion.md` và `docs/CODEX_HANDOFF.md`. Chỉ đánh dấu DONE bằng kết quả thực đã kiểm tra. Không bỏ qua pha FAILED/BLOCKED; không resplit hoặc xóa artifact. Test cũ đã từng được đánh giá phải được công bố. Các mục DONE phía dưới là lịch sử **LEGACY** P0–P7, không phải nghiệm thu refactor.

---

## Thẩm quyền quy hoạch và cột mốc hiện tại - 2026-10-15

`PLAN_HUMAN.md` là kế hoạch chính thức dành cho con người, xác định phạm vi và thứ tự. `PLAN_AI.md` cụ thể hóa cùng các mốc P0-P13 bằng ID tác vụ và tiêu chí chấp nhận. Tuân theo yêu cầu mới nhất của người dùng và AGENTS; giữ các tiêu chí chi tiết hiện có. Báo cáo cung cấp bằng chứng; bàn giao cung cấp ngữ cảnh để tiếp tục. Kế hoạch Word và `reports/archive/p1_legacy_workflow/PLAN_*.md` là tài liệu lịch sử; mục tiêu 50K trong Word đã được thay bằng yêu cầu 30K ngày 2026-10-08. Không tạo mốc hoặc lộ trình mới.

**Thực thi mới nhất: P6 DONE (T01–T06); P0–P5 vẫn là DONE. P7 CHƯA BẮT ĐẦU.** Bằng chứng P6: `reports/p6_completion_20261015.md`, `reports/p6/p6_20261015/manifest.json`, `benchmark.csv`, `selection_lock.json`; cân bằng tốt nhất vòng huấn luyện3, kiểm thử macro F1=0.730204. Bằng chứng P5: `reports/p5_completion_20261015.md`, `reports/p5/p5_20261015/manifest.json`, `benchmark.csv`, `selection_lock.json`. Bằng chứng P4: `reports/p4_completion_20261009.md`, `reports/p4/p4_20261009_final/manifest.json` và `reload_validation.json`. Xác minh SemEval source/license ĐƯỢC MIỄN cho dự án giáo dục này; NOT_VERIFIED. Quyết định: `reports/tables/p1_semeval_owner_exception_20261009.json`. Train/Test hiện có và JSONL đã chuyển đổi có thể được sử dụng trong các giai đoạn ABSA có liên quan; giữ nguyên các phân vùng gốc. Không tải xuống lại bộ dữ liệu hoặc kiểm tra kỹ thuật lặp lại. P6 được hoàn thiện theo hướng dẫn sử dụng mới nhất; không thực thi P7/later. Phạm vi bảo hiểm nhóm được chọn C1-A, C2-A hỗ trợ con người QA cho P1 và lấy mẫu thương hiệu C3-A được PHÊ DUYỆT2026-10-09 với các giới hạn được tiết lộ. Giữ độ bao phủ (recall)89.0767%, CI 95% 55.4584-99.8455%, sai lệch lựa chọn và xuất xứ AI; không có yêu cầu full-coverage/blind. Cần có P10 gold độc lập. Đa dạng thương hiệu before/after P2 là bắt buộc, không có hạn ngạch ngang nhau. P4 cố định splits/preprocessing được bảo quản; Bộ phân loại cổ điển P5 được đánh giá, các giai đoạn sau đang chờ. Phê duyệt: `reports/tables/p1_owner_approval_20261009.json`; gói quyết định được giữ lại: `reports/p1_acceptance_decision_20261009.md`. Ngoại lệ chủ sở hữu chấp nhận cổng SemEval; quyền vẫn chưa được xác minh.

| Cột mốc quan trọng | Tình trạng hiện tại | Bằng chứng / sản phẩm chưa hoàn thành |
|---|---|---|
| P0 | DONE | Trước khi thiết lập mới; các bài kiểm tra config/contract hiện tại; không có các mô hình |
| P1 | DONE | C1/C2/C3 đã được phê duyệt; Cổng SemEval được chủ sở hữu giáo dục chấp nhận ngoại lệ, giấy phép NOT_VERIFIED |
| P2 | DONE |30k tự động tiếng Anh đã chọn đại diện được gắn nhãn review, báo cáo quality/brand/imbalance và 250 ứng cử viên nhiễu dành riêng |
| P3 | DONE | P3-T01–T08 tables/7 figures/insights/report; Ô 6 kernel mới notebook PASS |
| P4 | DONE | hạt giống ngẫu nhiên42 product-disjoint21000/4500/4500; chỉ trên tập huấn luyện TF-IDF/BERT tiền xử lý và tải lại tập xác thực PASS |
| P5 | DONE | Lựa chọn 4 các mô hình, đã cố định tập xác thực, cố định kiểm thử benchmark/reload PASS; báo cáo20261015 |
| P6 | DONE | Toàn bộ chế độ BERT2×3 kỷ nguyên; kiểm thử macro0.730204; reload/independent tập xác thực PASS;181 đầu vào không thay đổi |
| P7 | CHƯA BẮT ĐẦU | Có chẩn đoán P5/P6 cơ bản; phân tích so sánh chi tiết P7 taxonomy/annotated đang chờ |
| P8 | CHƯA BẮT ĐẦU | P1 bảo tồn SemEval vị trí cụm từ; không có BIO/token alignment/model/evaluation |
| P9 | CHƯA BẮT ĐẦU | Không có khía cạnh dataset/model/end-to-end ABSA được điều hòa |
| P10 | CHƯA BẮT ĐẦU | phạm vi QA không phải là con người overall/aspect gold |
| P11 | CHƯA BẮT ĐẦU | Chưa lưu-mô hình single/batch Ứng dụng Streamlit |
| P12 | ĐANG TIẾN HÀNH | P0 routing/schema được tái sử dụng; preprocessing/loader/app sẵn sàng đầy đủ đang chờ |
| P13 | CHƯA BẮT ĐẦU | README/setup ban đầu không phải là reproducibility/report cuối cùng |

Bằng chứng của ứng viên: 408,480 review; 25,747 trùng lặp chính xác thô, 27,807 dư thừa được chuẩn hóa; Liên minh QA ID/text 8,406. Sản phẩm P2 output30k/9080; negative8259/neutral2631/positive19110; cặp từ vựng gần ngưỡng kiểm tra0. Đúng language/spam/semantic-duplicate/human tỷ lệ không đồng ý NOT_MEASURED. QA v2 FN1/TN867; kết hợp có điều kiện độ bao phủ (recall)89.0767%, khớp95% CI55.4584-99.8455%. Đây là những bằng chứng đã được lưu lại, không phải những cải tiến filtering/model mới được đo lường.

Bằng chứng kiểm toán và cổng: `reports/plan_progress_audit_20261009.md`; Đảm bảo chất lượng: `reports/p1_qa_v2_completion_20261009.md`; kiểm toán ứng viên: `reports/candidate_quality_preflight_20261009.md`. Bằng chứng P2 hiện tại: `reports/p2_amazon_completion_20261009.md` và `data/interim/p2/20261009_final/manifest.json`. P3 hoàn thành: `reports/p3_data_analysis_20261009.md`; P4 và P5 hiện là COMPLETE; bằng chứng đánh giá so sánh cổ điển ở trên. Các hộp kiểm chỉ ghi lại các nhiệm vụ phụ đã hoàn thành; các tác vụ không được kiểm tra có thể KHÔNG ĐƯỢC BẮT ĐẦU, ĐANG TIẾN HÀNH, CẦN review hoặc BLOCKED như được giải thích trong giai đoạn của chúng. Việc hoàn tất việc dọn dẹp được hỗ trợ bởi P2 các tệp kết quả ở trên.

## 1. Tổng quan

**Tên dự án:** Customer cảm xúc & khía cạnh Analysis for laptop review **Loại dự án:** Personal dữ liệu Science Project **Thời gian:** 6 tuần **Quy mô:** 1 người **Ngôn ngữ ban đầu:** tiếng Anh **Mở rộng tương lai:** tiếng Việt + PhoBERT **Tỷ trọng:** dữ liệu 50% — xây dựng mô hình 40% — Application 10%

### Phạm vi

Project chỉ tập trung vào **laptop review**. Các kết luận về cảm xúc, khía cạnh và hiệu năng mô hình chỉ được áp dụng trong phạm vi laptop; phone, headphone, smartwatch và các tech thiết bị khác nằm ngoài phạm vi hiện tại.

### Mục tiêu chính

- Phân loại overall cảm xúc thành 3 lớp: Positive / Neutral / Negative.
- Phân tích cảm xúc theo từng khía cạnh của laptop.
- Thực hiện dữ liệu chất lượng + EDA sâu và tìm insight.
- So sánh hồi quy logistic, SVM, Cây quyết định và BERT.
- Phân tích mất cân bằng lớp, nhiễu nhãn và lỗi mô hình.
- Xây dựng ABSA gồm khía cạnh Term Extraction + khía cạnh cảm xúc Classification.
- Xây dựng Streamlit app đơn giản cho single review và lô review.
- Thiết kế để có thể thêm tiếng Việt + PhoBERT sau này mà không thay đổi toàn bộ pipeline.

---

# 2. Quy ước trạng thái

- [ ] Chưa hoàn thành
- [x] Đã hoàn thành

Khi hoàn thành công việc, đổi `[ ]` thành `[x]`.

Các trạng thái được đặt tên: KHÔNG BẮT ĐẦU = không có nhiệm vụ nào có thể thực hiện được bắt đầu; ĐANG TIẾN HÀNH = công việc một phần, bao gồm cả công việc ban đầu được ủy quyền rõ ràng; DONE = đáp ứng mọi tiêu chí hoàn thành hiện hành; CẦN review = evidence/acceptance yêu cầu review; BLOCKED = điều kiện tiên quyết bắt buộc không có sẵn. Các hộp kiểm vẫn ở dạng nhị phân: chỉ DONE là `[x]`. Một pha không phải là DONE chỉ vì một số nhiệm vụ con được kiểm tra. Sử dụng Trạng thái hiện tại và ghi chú theo từng giai đoạn, không phải báo cáo lịch sử, để tiếp tục công việc.


---

# 3. CHẶNG 0 — Khởi tạo dự án

## Mục tiêu

Tạo project có thể tái lập và khóa phạm vi laptop review.

## Công việc

- [x] Tạo Git repository.
- [x] Tạo Python environment.
- [x] Tạo `requirements.txt` hoặc `pyproject.toml`.
- [x] Tạo cấu trúc thư mục.
- [x] Viết README mô tả bài toán laptop cảm xúc + ABSA.
- [x] Chốt nhãn Positive / Neutral / Negative.
- [x] Chốt mô hình: Logistic Regression, Linear SVM, Decision Tree, BERT.
- [x] Chốt Macro F1 là thước đo chọn mô hình chính.
- [x] Chốt Amazon laptop review cho overall sentiment/EDA.
- [x] Chốt SemEval-2014 laptop cho ABSA.
- [x] Thiết kế language/model registry để thêm PhoBERT sau này.

## Có thể giao được

- [x] Kho lưu trữ.
- [x] README ban đầu.
- [x] Cấu trúc nguồn.
- [x] Cấu hình chung.

---

Xác minh P0: `reports/p0_initialization.md` (2026-10-08): cài đặt môi trường mới, kiểm tra pip, 9 vượt qua các bài kiểm tra. Cơ quan đăng ký chỉ cung cấp metadata/routing; chưa có các mô hình được đào tạo nào.

# 4. CHẶNG 1 — Thu thập và hiểu dữ liệu laptop

## Mục tiêu

Có hai nguồn dữ liệu cùng phạm vi laptop và hiểu rõ lược đồ trước khi cleaning/modeling.

## bộ dữ liệu A — Amazon laptop review

Use for:
- Tổng thể cảm xúc.
- EDA và cái nhìn sâu sắc về kinh doanh.
- Nghiên cứu nhãn-nhiễu.
- bộ kiểm thử gold thực tế cho overall cảm xúc và ABSA.

Mục tiêu hiện hành: **khoảng 30.000 sạch tiếng Anh laptop review**, thay 50.000 theo yêu cầu ngày 2026-10-08. Đây là mục tiêu mong muốn; nếu chỉ có 15.000–25.000 review chất lượng cao, đánh giá phân bố nhãn và đa dạng sản phẩm rồi báo cáo quy mô phù hợp, không hạ chất lượng hoặc trộn thiết bị để đạt quota. Dữ liệu ABSA cần khía cạnh-level nhãn riêng; không yêu cầu gán nhãn toàn bộ 30.000 review.

## bộ dữ liệu B — SemEval-2014 laptop review

Use for:
- Trích xuất thuật ngữ khía cạnh.
- Phân loại khía cạnh cảm xúc.
- đánh giá so sánh ABSA trong phạm vi laptop.

## Công việc

- [x] Tải/access Amazon review 2023.
- [x] Tải/access Amazon sản phẩm siêu dữ liệu tương ứng.
- [x] Join review với siêu dữ liệu qua sản phẩm identifier phù hợp.
- [x] Xác định rule lọc đúng sản phẩm laptop.
- [x] Audit đủ 100 AI-assisted, user-approved nhãn và báo cáo lỗi bộ lọc.
- [x] nghiệm thu QA P1 qua ngoại lệ C2-A đã được owner duyệt; không claim independent/blind, giữ P10 gold độc lập.
- [x] Kiểm tra official nguồn và mirror HF được chỉ định, revision/paths/terms; nguồn review đã có evidence.
- [x] Dùng XML/JSONL SemEval hiện có theo ngoại lệ học tập đã duyệt; nguồn/giấy phép NOT_VERIFIED, không yêu cầu authorized-acquisition verification.
- [x] Kiểm tra lược đồ Amazon review.
- [x] Kiểm tra lược đồ Amazon siêu dữ liệu.
- [x] Kiểm tra schema/annotation SemEval.
- [x] Xác định các cột cần dùng.
- [x] Tạo `data_dictionary.md`.
- [x] Kiểm tra số review laptop và số sản phẩm laptop: 408.480 valid review / 28.161 sản phẩm có valid review; toàn bộ survey.
- [x] Kiểm tra rating phân bố: đủ 1–5, xem `reports/p1_full_laptop_survey.md`.
- [x] Xác định lấy mẫu strategy; mục tiêu hiện hành ~30k review (thiết kế ban đầu ~50k).
- [x] Lưu raw dữ liệu không chỉnh sửa.

## Có thể giao được

- [x] `data/raw/amazon/` (tổng kiểm tra metadata/reviews, đầy đủ và đã xác minh EOF).
- [x] `data/raw/semeval/` (tập huấn luyện v2/Test gold do người dùng cung cấp; không thể thay đổi).
- [x] `data_dictionary.md`
- [x] Quy tắc lọc laptop được chấp nhận theo C1/C2; Các giới hạn được hỗ trợ-QA provenance/coverage được giữ lại.
- [x] bộ dữ liệu overview báo cáo (toàn bộ Electronics laptop-only survey; valid chưa phải sạch tiếng Anh).
- [x] Chiến lược lấy mẫu.

---


### P1 còn thiếu và ranh giới với P2

- [x] Phân tích ứng viên thương hiệu diversity ở product/review levels, chuẩn hóa nguồn gốc và charts; C3-A đã phê duyệt; P2 trước/sau báo cáo available.

- [x] Chuẩn bị bộ độc lập con người QA: 150 ngẫu nhiên + 50 chẩn đoán sản phẩm;
  150 KEEP + 150 REJECT ngẫu nhiên review + 100 chẩn đoán review, blinded CSVs, hướng dẫn và weighted đánh giá CLI. Đã có con người-verified đánh giá sau AI assistance; không fully blind. Xem `docs/INDEPENDENT_HUMAN_QA.md`; C1/C2 nghiệm thu đã phê duyệt; không claim strict independence.

- [x] Tải xuống bản thô đầy đủ của Amazon, khảo sát và xác minh đầu ra chỉ dành cho laptop được liên kết với siêu dữ liệu.
- [x] Audit số lượng/rating/schema và mẫu có thể tái lập; quantity có tiềm năng đạt 30K.
- [x] Đánh giá QA user-approved và chỉ ra 4 trường hợp bỏ sót; giữ nguyên labels/dataset.
- [x] Chuẩn hóa quy trình thành laptop-only, lưu trữ lịch sử và dọn dependencies.
- [x] Owner-approved C2-A nghiệm thu exception; giữ nguyên AI nguồn gốc và độc lập P10 gold.
- [x] Lược đồ SemEval Train/Test cục bộ, vị trí cụm từ, kiểm tra phân cực và chồng chéo; JSONL đã được xác minh.
- [x] P1 DONE theo bằng chứng kỹ thuật và các ngoại lệ giới hạn được chủ sở hữu phê duyệt.

C1-A/C2-A/C3-A ĐƯỢC CHỦ SỞ HỮU2026-10-09; không có xác nhận đánh giá lặp đi lặp lại. independent/blind gán nhãn nghiêm ngặt không được yêu cầu; C2 là một ngoại lệ P1 bị chặn, P10 gold độc lập không thay đổi. Đã chấp nhận lấy mẫu thương hiệu, before/after P2 hiện đã được đo. P1 DONE: chủ sở hữu đã từ bỏ rõ ràng xác minh source/license cho SemEval Train/Test và JSONL hiện có trong dự án giáo dục này. License/source vẫn là NOT_VERIFIED; không có yêu cầu về quyền đã được xác minh. Bản ghi: `reports/tables/p1_semeval_owner_exception_20261009.json`. C4-B P2 và P3 chỉ có trên Amazon là COMPLETE. P4-P6 bây giờ là DONE; giai đoạn tiếp theo là P7, không được thực hiện ở đây. P2 sở hữu lựa chọn cleaning/labels/noise/clean; P4 sở hữu cố định các tập đã chia. Báo cáo P2 hiện tại: `reports/p2_amazon_completion_20261009.md`. Phân tích trước về thương hiệu ứng viên được giữ lại; Final181 sản phẩm siêu dữ liệu categories/9080, top5 review79.46%, unknown/ambiguous0.27%.

### Bằng chứng lịch sử

Các khảo sát prefix trước đây và repeated plan history đã được lưu bản chụp trạng thái tại `reports/archive/p1_legacy_workflow/`; không còn là tác vụ, blocker hoặc quyền chạy hiện hành. Báo cáo lịch sử vẫn giữ bằng chứng; dùng cleanup inventory để tìm đã lưu trữ run/QA paths.

# 5. CHẶNG 2 — dữ liệu chất lượng, làm sạch và Labeling

## Mục tiêu

Tạo bộ dữ liệu laptop sạch, đáng tin cậy và có nhãn overall cảm xúc.

**Trạng thái: DONE cho P2 chỉ Amazon theo C4-B; P1 hiện DONE nhờ các ngoại lệ được chủ dự án chấp nhận.** Bằng chứng: `reports/p2_amazon_completion_20261009.md`, `data/interim/p2/20261009_final/manifest.json` và `reports/tables/p2_amazon_20261009_final/validation.json`. Tái sử dụng kiểm tra thiếu dữ liệu/trùng hoàn toàn trước đó; áp dụng làm sạch HTML/khoảng trắng thận trọng, dành riêng mẫu QA, loại trùng sau chuẩn hóa/cách ly nhãn xung đột, chọn tiếng Anh tự động và ánh xạ nhãn từ số sao cố định. Có 30k hàng/9080 sản phẩm/3 lớp; dành riêng 250 mẫu chẩn đoán nhiễu. Có báo cáo thương hiệu trước/sau, không áp hạn ngạch thương hiệu. Tìm gần trùng là phép tìm từ vựng xấp xỉ trên văn bản được chọn và mẫu chẩn đoán, không chứng minh đầy đủ về ngữ nghĩa. Tỷ lệ sai ngôn ngữ/spam/nhãn con người thực tế NOT_MEASURED. P2 không tạo human gold, chia tập hoặc mô hình; chia tập cố định thuộc P4 đã hoàn thành. P3-P6 hiện hoàn thành; P7 không được thực hiện trong yêu cầu P6.

## Chất lượng dữ liệu

- [x] Kiểm tra thiếu values trên saved valid ứng viên pool.
- [x] Kiểm tra review rỗng/whitespace-only; làm sạch đã áp dụng, giữ raw text.
- [x] Kiểm tra review quá ngắn; không tự xóa ngắn review.
- [x] Kiểm tra exact bản trùng; normalized loại trùng đã áp dụng, giữ ledger.
- [x] Kiểm tra repeated review giữa các laptop; dedup/quarantine có ledger.
- [x] Kiểm tra lexical near-duplicates trên cuối cùng+chẩn đoán texts; không bằng chứng xác nhận semantic duplicate-free.
- [x] Đếm ứng viên flags HTML/URL/ký tự bất thường; chưa xác minh/xử lý từng case.
- [x] Kiểm tra spam-like heuristic flags và policy; không tạo con người spam nhãn.
- [x] Kiểm tra ứng viên review độ dài; chưa có bộ tách token analysis.
- [x] Tái sử dụng metadata/title flags và kiểm tra rỗng title; không tự sửa manufacturer.
- [x] tái sử dụng C1/C2 đã phê duyệt QA: no observed ngẫu nhiên KEEP FP; không claim zero contamination.

## Ghi nhãn

Nếu Amazon không có cảm xúc nhãn trực tiếp:
- [x] Xếp hạng 1–2 → Tiêu cực.
- [x] Xếp hạng 3 → Trung tính.
- [x] Xếp hạng 4–5 → Tích cực.
- [x] Kiểm tra phân bố nhãn.
- [x] Ghi rõ rating-derived nhãn là đại diện nhãn, không phải nhãn chuẩn tuyệt đối.

## nhiễu nhãn

- [x] Lấy mẫu review để tìm rating-text disagreement.
- [x] Lưu các case 5 sao nhưng văn bản tiêu cực/mixed.
- [x] Lưu các case 1–2 sao nhưng văn bản tích cực/trung tính.
- [x] Chuẩn bị unannotated chẩn đoán ứng viên set, reserve khỏi đã xử lý dữ liệu; không thay độc lập P10 gold.

## Có thể giao được

- [x] `data/processed/laptop_reviews.parquet`
- [x] bộ dữ liệu sạch tiếng Anh hướng tới ~30k review; đánh giá quy mô nhỏ hơn theo chất lượng/phân bố nhãn/đa dạng sản phẩm.
- [x] Báo cáo chất lượng dữ liệu.
- [x] Báo cáo phân phối nhãn.
- [x] Mẫu ứng viên nhãn-nhiễu.

---

# 6. CHẶNG 3 — EDA và nhận định cho laptop review

## Mục tiêu

Đây là phần trọng tâm dữ liệu Science của dự án.

**Trạng thái: DONE (P3-T01–T08).** cố định P2 bộ dữ liệu chỉ đọc; không có P4/splits/fitting. Bằng chứng: `reports/p3_data_analysis_20261009.md`, `reports/p3_insight_summary_20261009.md`, `notebooks/03_laptop_eda.ipynb`, `reports/p3/20261009_verified/summary.json` và `notebook_validation.json`. Số liệu 15 tables/7 PNG+SVG; 6-cell notebook tính toán lại các bảng trong kernel mới. Danh mục thương hiệu là siêu dữ liệu, thông số kỹ thuật absent/not được suy ra. Các nhiệm vụ siêu dữ liệu có điều kiện đã hoàn thành ở chất lượng trường được hỗ trợ; giả thuyết từ vựng không phải là kết quả ATE/ASC. Hỗ trợ chẩn đoán mang tính mô tả, không phải là cổng chấp nhận mới. con người nhiễu nhãn thực sự và P10 gold độc lập vẫn còn unmeasured/pending. P4-P6 hiện đã hoàn tất; P7 không được thực thi.


## Phân tích tổng quan

- [x] Số review.
- [x] Số laptop/product.
- [x] Phân bố rating.
- [x] Phân bố cảm xúc.
- [x] Phân bố chiều dài review.
- [x] Số review theo product.
- [x] Temporal analysis nếu có timestamp.

## Phân tích văn bản

- [x] Tần số từ.
- [x] N-gram thường xuyên.
- [x] Terms đặc trưng Positive.
- [x] Terms đặc trưng Neutral.
- [x] Terms đặc trưng Negative.
- [x] Chiều dài review theo sentiment/rating.

## Phân tích siêu dữ liệu

- [x] Phiếu bầu hữu ích theo sentiment/rating.
- [x] đã xác minh purchase nếu dữ liệu có.
- [x] cảm xúc theo laptop/product.
- [x] Đánh giá theo laptop/product.
- [x] Phân tích metadata/spec/brand nếu đủ tin cậy và hữu ích.

## Phân tích chất lượng dữ liệu

- [x] Tỷ lệ trùng lặp.
- [x] Tỷ lệ thiếu.
- [x] Tỷ lệ review ngắn.
- [x] Mất cân bằng giai cấp.
- [x] Ví dụ nhãn-nhiễu.

## Cái nhìn sâu sắc dành riêng cho laptop

- [x] Tìm các nhóm vấn đề khách hàng thường đề cập.
- [x] Xác định điểm mạnh/yếu nổi bật của laptop từ review.
- [x] Xác định sản phẩm/brand có pattern cảm xúc khác nhau nếu dữ liệu hỗ trợ.
- [x] Chuẩn bị giả thuyết về khía cạnh phổ biến: battery, screen, keyboard, hiệu năng, build, price, portability, storage, thermal/noise... nhưng chỉ kết luận khi dữ liệu chứng minh.

## Có thể giao được

- [x] EDA notebook.
- [x] Figures/tables.
- [x] Tóm tắt cái nhìn sâu sắc.
- [x] Báo cáo phân tích dữ liệu.

---

# 7. CHẶNG 4 — Chuẩn bị dữ liệu cho xây dựng mô hình

## Mục tiêu

Tạo cố định phân chia đáng tin cậy và hạn chế rò rỉ dữ liệu.

**Trạng thái: DONE (P4-T01–T05).** hạt giống ngẫu nhiên42, parent/variant/duplicate nhóm được kết nối, hạn ngạch số nguyên cân bằng lớp:21000/4500/4500; products6357/1361/1362; không có loại trừ. tập huấn luyện negative5781/neutral1842/positive13377; validation1239/395/2866; test1239/394/2867. Bằng chứng: `reports/p4_completion_20261009.md`, `docs/P4_DATA_CONTRACT.md`, `reports/p4/p4_20261009_final/{manifest,validation,reload_validation,task_validation}.json`. Các tính năng chỉ trên tập huấn luyện TF-IDF30000 thực tế; Bản sửa đổi cố định BERT bộ tách token, tập huấn luyện p95=390 chọn512token. Không có bộ phân loại weights/benchmark/ABSA huấn luyện hoặc các chỉnh sửa SemEval. 41 tổng kiểm tra được bảo vệ và 121 tổng số tệp ảnh chụp nhanh đầu vào không thay đổi; 180tests/pip kiểm tra PASS. Sàn gỗ All3split byte-replay/full đặc trưng tải lại PASS. Kiểm tra gần là từ vựng gần đúng; người dùng overlaps/QA phạm vi sản phẩm overlaps/truncation/gold vắng mặt được tiết lộ. Một phần p4_20261009/ được bảo vệ bộ nhớ ban đầu được thay thế; chỉ _final là hiện tại. NEXT_ACTION: Phân loại lỗi P7 theo một yêu cầu riêng; P5/P6 đã hoàn thành2026-10-15 mà không thay đổi P4.


## Công việc

- [x] Chia tập huấn luyện / tập xác thực / kiểm thử, mục tiêu 70/15/15.
- [x] Phân tầng theo cảm xúc.
- [x] Kiểm tra trùng lặp rò rỉ dữ liệu.
- [x] Kiểm tra sản phẩm rò rỉ dữ liệu.
- [x] Xem xét Group phân chia theo `product_id` / `parent_asin`.
- [x] Lưu cố định phân chia và ngẫu nhiên hạt giống ngẫu nhiên.
- [x] Tạo tiền xử lý riêng cho Classical ML.
- [x] Tạo tiền xử lý riêng cho BERT.
- [x] khớp mô hình TF-IDF chỉ trên tập huấn luyện.
- [x] Giữ negation như `not`, `never`, `don't`.
- [x] Không stemming/stopword removal cho BERT.

## Có thể giao được

- [x] tập huấn luyện / tập xác thực / kiểm thử.
- [x] Báo cáo phân chia.
- [x] Đường ống tiền xử lý cổ điển.
- [x] Đường ống tiền xử lý BERT.

---

# 8. CHẶNG 5 — Classical Machine Learning

**hoàn thành 2026-10-15 (P5-E00–E03).** Báo cáo `reports/p5_completion_20261015.md`; 4models trên cùng4.500test hàng, tập xác thực-đã cố định lựa chọn, đủ metrics/costs, reload/independent tập xác thực PASS,149input hàm băm giữ nguyên. LR C0,5/balanced: tập xác thực macro F1=0,693554; kiểm thử macro F1=0,683887. BERT thuộc P6, chưa chạy.

## Đường ống

`Laptop Review → Basic Cleaning → TF-IDF → Classifier`

## Thí nghiệm

- [x] Lớp đa số mô hình cơ sở.
- [x] TF-IDF + Hồi quy logistic.
- [x] TF-IDF + SVM tuyến tính.
- [x] TF-IDF + Cây quyết định.
- [x] Dùng lớp weighting khi mất cân bằng đủ lớn và có lý do (so sánh tập xác thực, chọn LR/SVM balanced; DT None).

## thước đo bắt buộc

- [x] tỷ lệ dự đoán đúng (accuracy).
- [x] độ chính xác dự đoán (precision) từng class.
- [x] độ bao phủ (recall) từng class.
- [x] F1 từng class.
- [x] Macro F1.
- [x] Trọng số F1.
- [x] Ma trận nhầm lẫn.
- [x] Thời gian huấn luyện.
- [x] Thời gian suy luận.
- [x] Kích thước mô hình.
- [x] RAM usage (sampled process RSS; có giới hạn phương pháp đo).

## Có thể giao được

- [x] 3 ML cổ điển các mô hình.
- [x] Bảng đánh giá so sánh thống nhất.
- [x] Ma trận nhầm lẫn.
- [x] Kết luận mô hình Classical ML tốt nhất.

---

# 9. CHẶNG 6 — BERT Overall cảm xúc

**hoàn thành 2026-10-15 (T01–T06).** `reports/p6_completion_20261015.md` và `reports/p6/p6_20261015/`:2loss modes×3full vòng huấn luyện, balanced vòng huấn luyện3 được chọn bằng tập xác thực macro0,734646; kiểm thử macro0,730204. 181inputs giữ nguyên, độc lập tập xác thực PASS,207tests PASS qua isolated runner. Không thực thi P7.

## Mục tiêu

Fine-tune BERT cho laptop review 3 lớp và so sánh với Classical ML.

## Công việc

- [x] Chuẩn bị tokenizer/dataset (adapter/collator và toàn bộ token căn chỉnh PASS).
- [x] Chọn max sequence độ dài từ phân bố token thực tế (tái sử dụng P4 tập huấn luyện-derived512).
- [x] Tinh chỉnh BERT (2modes×3full vòng huấn luyện, toàn mạng nền).
- [x] Theo dõi train/validation hàm mất mát.
- [x] Theo dõi Macro F1.
- [x] Kiểm tra overfitting (tập huấn luyện objective giảm/validation CE tăng; limitations ghi trong báo cáo).
- [x] Dùng weighted hàm mất mát nếu mất cân bằng đáng kể (so sánh tập xác thực, chỉ trên tập huấn luyện weights).
- [x] Tiết kiệm điểm lưu mô hình tốt nhất.

## Đánh giá

- [x] Đầy đủ thước đo giống Classical ML.
- [x] Thời gian huấn luyện.
- [x] Độ trễ suy luận.
- [x] Kích thước mô hình.
- [x] RAM/GPU/VRAM nếu có.
- [x] BERT so với LR/SVM/DT.
- [x] Định lượng mức tăng hiệu suất và chi phí tính toán (có cảnh báo đo lường CPU/GPU).

## Câu hỏi nghiên cứu chính

**BERT cải thiện Macro F1 bao nhiêu so với TF-IDF + Linear SVM trên laptop review và chi phí tính toán tăng bao nhiêu?**

## Có thể giao được

- [x] BERT mô hình.
- [x] ML-vs-BERT đánh giá so sánh.
- [x] Phân tích Cost/performance.

---

# 10. CHẶNG 7 — phân tích lỗi

## Nhóm lỗi cần kiểm tra

- [ ] Phủ định.
- [ ] Hỗn hợp cảm xúc.
- [ ] Sự mỉa mai.
- [ ] review rất ngắn.
- [ ] review dài.
- [ ] cảm xúc tiềm ẩn.
- [ ] Văn bản đánh giá conflict.
- [ ] Multi-khía cạnh review.
- [ ] Thuật ngữ dành riêng cho laptop.

## So sánh mô hình

- [ ] LR sai loại nào.
- [ ] SVM sai loại nào.
- [ ] DT sai loại nào.
- [ ] BERT sửa được lỗi nào.
- [ ] Lỗi nào tất cả mô hình vẫn thất bại.

## Có thể giao được

- [ ] Báo cáo phân tích lỗi.
- [ ] Các ví dụ có chú thích
- [ ] Kết luận mô hình strengths/weaknesses.

---

# 11. CHẶNG 8 — ABSA: khía cạnh Term Extraction

## Mục tiêu

Extract khía cạnh cụ thể trong laptop review.

Ví dụ:

`The screen is excellent but battery life is poor.`

→ `screen`, `battery life`

## Công việc

- [ ] Hiểu gán nhãn SemEval laptop.
- [ ] Chuyển đổi sang gắn thẻ BIO.
- [ ] Xác thực căn chỉnh khía cạnh span/token.
- [ ] Tinh chỉnh phân loại BERT token.
- [ ] Evaluate trên SemEval kiểm thử.

## Số liệu

- [ ] Thực thể độ chính xác dự đoán (precision).
- [ ] Thực thể độ bao phủ (recall).
- [ ] Thực thể F1.

## Có thể giao được

- [ ] BIO bộ dữ liệu.
- [ ] Trích xuất khía cạnh mô hình.
- [ ] Báo cáo đánh giá.

---

# 12. CHẶNG 9 — ABSA: khía cạnh cảm xúc Classification

## Mục tiêu

Với mỗi khía cạnh laptop, phân loại Positive / Neutral / Negative.

## Công việc

- [ ] Chuẩn bị `(review, aspect, sentiment)` examples từ SemEval.
- [ ] Chuẩn hóa về 3 cảm xúc classes.
- [ ] Xử lý/loại unsupported conflict nhãn có ghi chú.
- [ ] Tinh chỉnh bộ phân loại BERT khía cạnh cảm xúc.
- [ ] Đánh giá bộ phân loại
- [ ] Nối khía cạnh Extraction → khía cạnh cảm xúc thành end-to-end ABSA.

## Số liệu

- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision).
- [ ] độ bao phủ (recall).
- [ ] Macro F1.
- [ ] Ma trận nhầm lẫn.

## Có thể giao được

- [ ] khía cạnh cảm xúc mô hình.
- [ ] Đường ống ABSA từ đầu đến cuối.
- [ ] Báo cáo đánh giá ABSA.

---

# 13. CHẶNG 10 — thủ công gán nhãn và Amazon laptop bộ kiểm thử gold

## Mục tiêu

Kiểm tra mô hình tập huấn luyện trên SemEval laptop có hoạt động tốt trên Amazon laptop review thực tế hay không, đồng thời đánh giá nhiễu của rating-derived nhãn.

## Quy mô

**300–500 Amazon laptop review**.

## Lấy mẫu

- [ ] Cân đối theo rating.
- [ ] Cân đối theo review length.
- [ ] Cân đối theo nhiều laptop/product/brand nếu có.
- [ ] Bao gồm mixed-cảm xúc và difficult cases.

## gán nhãn

- [ ] con người tổng thể cảm xúc.
- [ ] Điều khoản khía cạnh.
- [ ] khía cạnh cảm xúc.
- [ ] Lưu ý cho những trường hợp mơ hồ.

## Phân tích

- [ ] cảm xúc có nguồn gốc từ xếp hạng so với con người cảm xúc.
- [ ] Tỷ lệ Agreement/disagreement.
- [ ] Overall cảm xúc các mô hình trên bộ kiểm thử gold.
- [ ] SemEval-trained ABSA trên Amazon laptop bộ kiểm thử gold.
- [ ] Phân tích **bộ dữ liệu shift SemEval → Amazon trong cùng laptop phạm vi**.

## Có thể giao được

- [ ] `data/manual/amazon_laptop_gold_test.csv`
- [ ] Báo cáo bộ kiểm thử gold.
- [ ] Báo cáo nhiễu nhãn.
- [ ] SemEval→Đánh giá chuyển giao của Amazon.

---

# 14. CHẶNG 11 — Ứng dụng Streamlit

## review đơn

- [ ] Nhập laptop review.
- [ ] Dự đoán tổng thể cảm xúc.
- [ ] Hiển thị độ tin cậy nếu mô hình hỗ trợ.
- [ ] Trích xuất các khía cạnh
- [ ] Predict cảm xúc từng khía cạnh.

## lô review

- [ ] Tải lên CSV.
- [ ] lô suy luận.
- [ ] % Tích cực / Trung tính / Tiêu cực.
- [ ] Tần số đề cập đến khía cạnh.
- [ ] Phân phối cảm xúc theo khía cạnh.
- [ ] Các khía cạnh positive / negative laptop hàng đầu.

## Có thể giao được

- [ ] Ứng dụng Streamlit.
- [ ] Chế độ đơn review.
- [ ] Chế độ lô-review.
- [ ] Bảng điều khiển phân tích cơ bản.

---

# 15. CHẶNG 12 — Chuẩn bị mở rộng tiếng Việt

## Mục tiêu

phạm vi vẫn là laptop nhưng có thể thay tiếng Anh bằng tiếng Việt sau này.

## Công việc

- [ ] Tách tiền xử lý theo ngôn ngữ.
- [ ] Không hard-code BERT trong UI/business logic.
- [ ] Tạo mô hình registry.
- [ ] `en → BERT`.
- [ ] Dự trữ `vi → PhoBERT`.
- [ ] Chuẩn hóa suy luận output.
- [ ] Tạo interface cho tiếng Việt preprocessing.

## Có thể giao được

- [ ] Giao diện suy luận không phụ thuộc vào ngôn ngữ.
- [ ] Đăng ký mô hình.
- [ ] Điểm mở rộng Vietnamese/PhoBERT.

---

# 16. CHẶNG 13 — Tổng hợp và hoàn thiện

## Công việc

- [ ] Hoàn thiện EDA/insight.
- [ ] Hoàn thiện đánh giá so sánh LR/SVM/DT/BERT.
- [ ] Hoàn thiện phân tích lỗi.
- [ ] Hoàn thiện mất cân bằng lớp analysis.
- [ ] Hoàn thiện nhãn-nhiễu analysis.
- [ ] Hoàn thiện ABSA evaluation.
- [ ] Hoàn thiện SemEval→Amazon laptop transfer evaluation.
- [ ] Hoàn thiện Streamlit.
- [ ] Hoàn thiện README/hướng dẫn chạy.
- [ ] Kiểm tra reproducibility.
- [ ] Viết limitation.
- [ ] Viết future work.

## Limitation bắt buộc phải ghi rõ

- [ ] Project chỉ đánh giá phạm vi laptop review.
- [ ] Không kết luận mô hình generalize sang phone/headphone/tech gadgets khác.
- [ ] cảm xúc bắt nguồn từ xếp hạng có nhiễu nhãn.
- [ ] SemEval và Amazon có thể có dataset/style shift dù cùng phạm vi laptop.

---

# 17. Kế hoạch 6 tuần

| Tuần | Chặng | Kết quả cần đạt |
|---|---|---|
| 1 | 0–1 | Kho lưu trữ + Từ điển laptop thô của Amazon dữ liệu + SemEval + dữ liệu |
| 2 | 2–3 | Làm sạch laptop bộ dữ liệu + EDA + hiểu biết sâu sắc |
| 3 | 4–5 | cố định phân chia + LR/SVM/DT đánh giá so sánh |
| 4 | 6–7 | So sánh BERT + mô hình + phân tích lỗi |
| 5 | 8–10 | ABSA + thủ công Amazon laptop bộ kiểm thử gold |
| 6 | 11–13 | Streamlit + tích hợp + báo cáo cuối cùng |

---

# 18. Định nghĩa xong

Dự án hoàn thành khi:

- [x] Có laptop30k được xử lý bộ dữ liệu qua cổng tiếng Anh tự động; ghi các giới hạn trong báo cáo P2.
- [x] Có EDA và nhận định trong phạm vi laptop; evidence/limits ở P3 báo cáo và notebook.
- [x] Có lớp 3 tổng thể cảm xúc (P5/P6 đã lưu suy luận).
- [x] Có Logistic Regression, SVM, Decision Tree và BERT đánh giá so sánh (bảng P6 thống nhất cố định-kiểm thử).
- [x] Có tỷ lệ dự đoán đúng (accuracy) / độ chính xác dự đoán (precision) / độ bao phủ (recall) / F1 / Macro F1 / F1 có trọng số.
- [x] Có so sánh training/inference/model-size/resource (báo cáo P6; hãy cẩn thận với device/measurement).
- [x] Có mất cân bằng lớp analysis P2; P5/P6 mitigation đã so sánh bằng tập xác thực.
- [ ] Có phân tích nhãn-nhiễu.
- [ ] Có phân tích lỗi.
- [ ] Có trích xuất thuật ngữ khía cạnh.
- [ ] Có phân loại khía cạnh cảm xúc.
- [ ] Có 300–500 Amazon laptop review được thủ công gán nhãn.
- [ ] Có đánh giá SemEval laptop → Amazon laptop.
- [ ] Có ứng dụng Streamlit.
- [ ] Có kiến trúc mở rộng Vietnamese/PhoBERT.
- [ ] Có báo cáo cuối cùng và kho lưu trữ có thể tái tạo.

## Lịch sử bằng chứng

Các sự kiện acquisition/QA/normalization lịch sử vẫn còn trong báo cáo ghi ngày của chúng chứ không phải là danh sách kiểm tra hoạt động trùng lặp. Xem `reports/p1_semeval_laptop.md`, `reports/p1_independent_human_qa.md`, `reports/p1_recall_reliability.md`, `reports/p1_qa_v2_annotation_validation.md`, `reports/annotation_human_review_20261009.md`, `reports/p1_qa_v2_completion_20261009.md` và `reports/candidate_quality_preflight_20261009.md`. Ánh xạ v2 đã giải quyết và các khoảng trống kế thừa tùy chọn không phải là các công cụ chặn hiện tại.
