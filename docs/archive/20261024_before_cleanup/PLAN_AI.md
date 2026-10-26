# PHÂN TÍCH cảm xúc CỦA KHÁCH HÀNG CHO laptop review — KẾ HOẠCH THỰC HIỆN AI

## Phạm vi hiện hành — refactor ngày 2026-10-24

Yêu cầu người dùng ngày 2026-10-24 thay thế bộ mô hình tổng thể trước đây; chi tiết và đường dẫn thực thi ở `docs/MODEL_STACK_REFACTOR.md`. Các mục DONE/checklist P0–P6 phía dưới ghi **LEGACY** (bằng chứng lịch sử), không nghiệm thu các tiêu chí mới sau đây. Giữ nguyên P8–P13 ngoài tác vụ; không triển khai ABSA trong refactor này.

- [x] P0: import/dependency/CUDA PASS; phân biệt explicit V3/V3_5, không dùng default; 3 tests PASS (`reports/p0_model_stack_refactor.md`).
- [x] P1: tái sử dụng dữ liệu; hash raw khớp manifest, metadata coverage/QA hiện có được kiểm tra; 47 tests PASS (`reports/p1_revalidation_for_new_models.md`).
- [x] P2: 30K, mapping/nhãn/missing/duplicates xác minh; không relabel; whitelist feature; 40 tests PASS (`reports/p2_revalidation_for_new_models.md`).
- [x] P3: Model Readiness Analysis, neutral/length/truncation/storage/resource risks; 30 tests PASS (`reports/p3_model_readiness.md`).
- [x] P4-T01–T06: giữ split, canonical text, frozen embeddings/cache/QA, nhánh tokenizer riêng, leakage checks; re-encode token đủ 30K và 36 tests PASS (`reports/p4_semantic_representation.md`).
- [x] P5-E00–E04: nghiệm thu benchmark với LIMITED/SUBSAMPLED cho TabPFN V3=10000/V3_5=1500, WARNING RSS E03=6,48GB; không phải full-data. E00/E01/E02 reuse; resource assessment, selection lock, alignment/metrics/hash và version distinction PASS (`reports/p5_modern_tabular_models.md`).
- [x] P6: BERT canonical title + body đủ21000 train, unweighted/balanced; chọn unweighted epoch3 bằng validation macro F1; reload, một lượt test và xác minh độc lập PASS (`reports/p6_transformer_benchmark.md`). BERT body-only cũ giữ LEGACY.
- [x] P7: đủ6 model, hai comparison, compute/error analysis/proxy limits; 249tests PASS, 53legacy files nguyên hash (`reports/p7_unified_benchmark.md`, `reports/model_stack_final_validation.json`). Tổng thể LIMITED vì giới hạn P5, không tuyên bố full TabPFN hoặc hoàn tất ABSA/gold/app.

**DONE_WHEN mới:** đủ bằng chứng thực thi và xác minh từng mục theo yêu cầu đính kèm; code-only không DONE. Thứ tự P0 → P1 → P2 → P3 → P4 → P5-E00/E01/E02/E03/E04 → P6 → P7; không bỏ qua FAILED/BLOCKED. `reports/model_stack_refactor_completion.md` và `docs/CODEX_HANDOFF.md` ghi trạng thái tiếp tục. Không tune bằng test/human gold; không TF-IDF/BoW/SVD/PCA hoặc metadata trong active feature pipeline. Phải giữ artifact cũ và công bố test đã được đánh giá trong LEGACY.

---

Phần dưới giữ nguyên kế hoạch/bằng chứng **LEGACY** cho P0–P7; các yêu cầu dài hạn không xung đột vẫn áp dụng.

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

> Tối ưu hóa cho trợ lý AI agents/coding. Tuân theo phạm vi, các phần phụ thuộc, ID nhiệm vụ, kết quả đầu ra và tiêu chí hoàn thành. Không mở rộng phạm vi vượt quá laptop trừ khi người dùng thay đổi rõ ràng phạm vi.

---

# 0. HỢP ĐỒNG DỰ ÁN

## PROJECT_ID

`customer-sentiment-laptop-reviews`

## MỤC TIÊU

Xây dựng dự án Phân tích cảm xúc lấy khách hàng làm trung tâm dữ liệu được giới hạn ở **laptop review** với:

1. Phân loại cảm xúc lớp 3 tổng thể.
2. Khám phá thông tin chi tiết chuyên sâu về dữ liệu + EDA + laptop.
3. Điểm chuẩn hồi quy logistic so với SVM tuyến tính so với cây quyết định so với BERT.
4. Trích xuất thuật ngữ khía cạnh cho các khía cạnh laptop.
5. Phân loại khía cạnh cảm xúc.
6. nhãn-nhiễu và phân tích mất cân bằng lớp.
7. thủ công Amazon laptop bộ kiểm thử gold.
8. Ứng dụng Streamlit đơn giản.
9. Kiến trúc đã sẵn sàng cho tiếng Việt + PhoBERT trong khi vẫn giữ laptop phạm vi.

## ranh giới phạm vi

- TRONG phạm vi: laptops/notebooks và văn bản review của chúng.
- NGOÀI phạm vi: điện thoại, tai nghe, máy tính bảng, đồng hồ thông minh, máy ảnh và các miền tiện ích khác.
- Không yêu cầu khái quát hóa nhiều tiện ích.
- Cho phép đánh giá SemEval→Amazon vì cả hai tập dữ liệu vẫn nằm trong laptop phạm vi; mô tả nó như là chuyển dataset/platform/style, không phải khái quát hóa tiện ích chéo phạm vi.

## Ràng buộc cố định

- Ngôn ngữ chính: tiếng Anh.
- Ngôn ngữ tương lai: tiếng Việt.
- nhãn: `positive`, `neutral`, `negative`.
- mục tiêu Amazon sạch bộ dữ liệu: khoảng `30,000` sạch tiếng Anh laptop review (cập nhật người dùng 2026-10-08; thay thế 50,000).
- Đây là mục tiêu mong muốn, không phải hạn ngạch cứng. Đánh giá nhóm 15,000–25,000 chất lượng cao bằng cách sử dụng tính đa dạng của lớp coverage/product và ghi lại kích thước thực tế. Các proxy đánh giá tổng thể không cung cấp ABSA nhãn cấp khía cạnh; không yêu cầu gán nhãn của tất cả 30,000 review.
- Nếu laptop dữ liệu hợp lệ nhỏ hơn, hãy giữ nguyên độ tinh khiết của phạm vi và ghi lại kích thước thực tế; không lấp đầy hạn ngạch bằng cách sử dụng các tiện ích không phải laptop.
- Quy mô đội: 1.
- Thời lượng: 6 tuần.
- Trọng số: dữ liệu 50%, xây dựng mô hình 40%, Ứng dụng 10%.
- ML cổ điển bắt buộc: Hồi quy logistic, SVM tuyến tính, Cây quyết định.
- Transformer bắt buộc: BERT.
- Yêu cầu ABSA: có.
- Ứng dụng: Streamlit, giao diện người dùng đơn giản.
- Không thêm CNN/LSTM/GRU/Word2Vec/FastText trừ khi phạm vi thay đổi.
- Không thêm Spark/Kafka/Airflow trừ khi quy mô thay đổi đáng kể.
- Không coi việc thu thập thông tin theo thời gian thực là một phần của MVP.

## NGUỒN dữ liệu

### Tổng thể cảm xúc / EDA / bộ kiểm thử gold

Amazon review 2023 + sản phẩm Amazon siêu dữ liệu, được lọc thành các sản phẩm laptop.

### ABSA benchmark/training

SemEval-2014 laptop review.

### Đánh giá thủ công

300–500 Amazon laptop review.

## CHÍNH SÁCH LỌC AMAZON laptop

- Kết hợp các bản ghi review với sản phẩm siêu dữ liệu bằng mã nhận dạng sản phẩm thích hợp.
- Lọc các sản phẩm sử dụng các trường metadata/category/title đủ để xác định laptops/notebooks.
- Kiểm tra rõ ràng các kết quả dương tính giả như túi laptop, bộ sạc, chân đế, vỏ bọc, bộ phận thay thế và các phụ kiện khác.
- Ghi lại quy tắc lọc và một mẫu thủ công tập xác thực nhỏ.
- Giữ nguyên dữ liệu không thay đổi.

## CHÍNH SÁCH nhãn

Nếu Amazon cảm xúc nhãn không có sẵn:

```text
rating 1–2 -> negative
rating 3   -> neutral
rating 4–5 -> positive
```

Hãy coi cảm xúc bắt nguồn từ xếp hạng như một đại diện nhãn ồn ào, chưa bao giờ là nhãn chuẩn không thể nghi ngờ.

## CHỈ SỐ LỰA CHỌN mô hình CHÍNH

`Macro F1`

Các chỉ số phụ:
- tỷ lệ dự đoán đúng (accuracy)
- Precision/Recall/F1 mỗi lớp
- Trọng số F1
- Ma trận nhầm lẫn
- thời gian huấn luyện
- Độ trễ suy luận
- Kích thước mô hình
- RAM
- GPU/VRAM nếu có

---

# 1. QUY TẮC TÌNH TRẠNG

```text
- [ ] = NOT DONE
- [x] = DONE
```

Chỉ đánh dấu một nhiệm vụ `[x]` khi tiêu chí `DONE_WHEN` của nó được thỏa mãn.

Các trạng thái được đặt tên: KHÔNG BẮT ĐẦU = không có nhiệm vụ nào có thể thực hiện được bắt đầu; ĐANG TIẾN HÀNH = công việc một phần, bao gồm cả công việc ban đầu được ủy quyền rõ ràng; DONE = đáp ứng mọi tiêu chí hoàn thành hiện hành; CẦN review = evidence/acceptance yêu cầu review; BLOCKED = điều kiện tiên quyết bắt buộc không có sẵn. Các hộp kiểm vẫn ở dạng nhị phân: chỉ DONE là `[x]`. Một pha không phải là DONE chỉ vì một số nhiệm vụ con được kiểm tra. Sử dụng Trạng thái hiện tại và ghi chú theo từng giai đoạn, không phải báo cáo lịch sử, để tiếp tục công việc.


Nếu bị chặn:

```text
BLOCKED: <reason>
NEXT_ACTION: <action>
```

---

# 2. CẤU TRÚC KHO LƯU TRỮ mục tiêu

```text
customer-sentiment-laptop/
├── README.md
├── requirements.txt
├── configs/
│   ├── data.yaml
│   ├── model.yaml
│   └── language.yaml
├── data/
│   ├── raw/
│   │   ├── amazon/
│   │   └── semeval/
│   ├── interim/
│   ├── processed/
│   └── manual/
├── notebooks/
│   ├── 01_dataset_overview.ipynb
│   ├── 02_data_quality.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_classical_ml.ipynb
│   ├── 05_bert.ipynb
│   └── 06_error_analysis.ipynb
├── src/
│   ├── data/
│   │   ├── loader.py
│   │   ├── laptop_filter.py
│   │   ├── validation.py
│   │   ├── cleaning.py
│   │   ├── labeling.py
│   │   └── split.py
│   ├── preprocessing/
│   │   ├── base.py
│   │   ├── english.py
│   │   └── vietnamese.py
│   ├── sentiment/
│   │   ├── classical/
│   │   └── transformer/
│   ├── absa/
│   │   ├── aspect_extraction/
│   │   └── aspect_sentiment/
│   ├── evaluation/
│   │   ├── metrics.py
│   │   ├── benchmark.py
│   │   └── error_analysis.py
│   ├── models/
│   │   └── registry.py
│   └── inference/
│       └── pipeline.py
├── app/
│   └── streamlit_app.py
├── reports/
│   ├── figures/
│   ├── tables/
│   └── final/
└── tests/
```

---

# 3. GIAI ĐOẠN P0 — KHỞI TẠO DỰ ÁN

## MỤC TIÊU

Tạo bộ khung có thể tái tạo và khóa laptop chỉ dành cho phạm vi.

### Thiết lập kho lưu trữ P0-T01
- [x] Tạo kho lưu trữ Git.
- [x] Tạo `.gitignore`.
- [x] Tạo môi trường Python.
- [x] Tạo tập tin phụ thuộc.

**DONE_WHEN:** Môi trường mới cài đặt các phần phụ thuộc cần thiết mà không gặp lỗi chưa được giải quyết.

### Cấu trúc thư mục P0-T02
- [x] Tạo cấu trúc kho lưu trữ mục tiêu.

**PHỤ THUỘC:** P0-T01 **DONE_WHEN:** Các thư mục cốt lõi tồn tại và trách nhiệm được tách biệt.

### P0-T03 Scope/config
- [x] Cấu hình nhãn.
- [x] Định cấu hình đường dẫn bộ dữ liệu.
- [x] Định cấu hình danh sách mô hình.
- [x] Định cấu hình số liệu.
- [x] Định cấu hình hạt giống ngẫu nhiên ngẫu nhiên.
- [x] Lưu trữ phạm vi=`laptop`.

**DONE_WHEN:** Core phạm vi được định hướng theo cấu hình và không bị trùng lặp trên notebook.

### Khả năng mở rộng ngôn ngữ P0-T04
- [x] Thêm cấu hình ngôn ngữ.
- [x] Bản đồ `en -> BERT`.
- [x] Dự trữ `vi -> PhoBERT`.
- [x] Xác định lược đồ suy luận độc lập với ngôn ngữ.

**DONE_WHEN:** Hỗ trợ tiếng Việt trong tương lai không yêu cầu thay đổi hợp đồng đầu ra ứng dụng.

## GIAI ĐOẠN ĐẦU RA
- [x] Kho lưu trữ được khởi tạo.
- [x] Đã khởi tạo cấu hình.
- [x] Tài liệu laptop chỉ có phạm vi.
- [x] Đã xác định mức độ trừu tượng English/Vietnamese.

---

Xác minh P0: xem `reports/p0_initialization.md` (2026-10-08): cài đặt môi trường mới, kiểm tra pip và 9 vượt qua các bài kiểm tra hợp đồng. Việc mua lại mô hình training/data không nằm trong quá trình hoàn tất này.

# 4. GIAI ĐOẠN P1 — laptop dữ liệu THU NHẬP VÀ HIỂU

## MỤC TIÊU

Mua Amazon laptop dữ liệu và SemEval laptop ABSA dữ liệu, sau đó hiểu các lược đồ trước mọi quá trình xử lý không thể đảo ngược.

### P1-T01 Mua lại Amazon review + siêu dữ liệu
- [x] Download/access Amazon review 2023 review dữ liệu.
- [x] Download/access tương ứng với sản phẩm siêu dữ liệu.
- [x] Bảo quản các tập tin thô không thay đổi.

** ĐẦU RA:** `data/raw/amazon/`

**DONE_WHEN:** Cả hai bản ghi review và siêu dữ liệu đều có thể được tải lại.

### P1-T02 Xây dựng bộ lọc sản phẩm laptop
- [x] Chuẩn bị bộ công cụ QA con người độc lập có thể tái tạo và các mẫu product/review gán nhãn mù; công cụ đánh giá đã được thử nghiệm. Đánh giá được xác minh con người sau khi hoàn thành hỗ trợ AI; Chấp nhận C2-A đã được phê duyệt; xuất xứ được hỗ trợ được giữ lại: `docs/INDEPENDENT_HUMAN_QA.md`.
- [x] Xác định khóa nối giữa review và sản phẩm siêu dữ liệu.
- [x] Tham gia hoặc ánh xạ review tới sản phẩm siêu dữ liệu.
- [x] Xác định quy tắc bao gồm laptop/notebook.
- [x] Xác định quy tắc loại trừ phụ kiện.
- [x] Kiểm tra tất cả 100 QA nhãn được AI hỗ trợ, được người dùng phê duyệt; Tiêu chí độ chính xác dự đoán (precision) đã đạt (không xác minh độc lập).
- [x] Lọc sự chấp nhận QA thông qua C2-A ngoại lệ2026-10-09: QA được hỗ trợ đã được xác minh bởi con người; tính độc lập nghiêm ngặt không được yêu cầu, P10 không thay đổi.

**LOẠI TRỪ KHI ĐƯỢC XÁC ĐỊNH LÀ:** túi, bao đựng, chân đế, bộ sạc, đế cắm, bộ phận thay thế, miếng bảo vệ màn hình hoặc các phụ kiện không phải laptop khác.

**OUTPUT:** quy tắc lọc được ghi lại + `src/data/laptop_filter.py` hoặc tương đương.

**DONE_WHEN:** Mẫu thủ công cho biết nhóm được lọc đại diện cho các sản phẩm laptop có độ chính xác dự đoán (precision) được chấp nhận.

### P1-T03 Thu được SemEval laptop
- [x] Nguồn chính thức của review và gương HF được chỉ định metadata/revision/terms (chỉ nguồn review).
- [x] Truy cập XML và JSONL SemEval tập huấn luyện v2/Test gold hiện có theo ngoại lệ giáo dục được chủ sở hữu phê duyệt; Đã miễn xác minh authorized-acquisition/source/license, NOT_VERIFIED.
- [x] Giữ nguyên định dạng gán nhãn gốc.

** ĐẦU RA:** `data/raw/semeval/`

### Kiểm tra lược đồ Amazon P1-T04
- [x] Trường văn bản review.
- [x] Trường đánh giá.
- [x] ID sản phẩm/mã định danh gốc.
- [x] Dấu thời gian nếu có.
- [x] Các trường hữu ích nếu có.
- [x] Trường đã xác minh mua hàng nếu có.
- [x] Các trường siêu dữ liệu của sản phẩm hữu ích cho laptop identification/EDA.

### Kiểm tra lược đồ SemEval P1-T05
- [x] Trường Sentence/review.
- [x] khía cạnh terms/spans.
- [x] Phân cực khía cạnh.
- [x] Conflict/other nhãn.
- [x] Chính sách chuẩn hóa lớp 3.

### Từ điển P1-T06 dữ liệu
- [x] Tên trường.
- [x] Kiểu dữ liệu.
- [x] Ý nghĩa.
- [x] Ghi chú thiếu giá trị.
- [x] Mục đích sử dụng.

** ĐẦU RA:** `data_dictionary.md`

### Kiểm tra xếp hạng và kích thước nhóm P1-T07
- [x] Số lượng laptop review đã lọc: 408,740 khớp / 408,480 hợp lệ trong khảo sát Điện tử đầy đủ; không sạch tiếng Anh.
- [x] Đếm sản phẩm laptop: ứng viên 28,172; 28,161 với review hợp lệ. Đã đánh giá QA hỗ trợ AI được xác minh bởi con người; Chấp nhận C2-A đã được phê duyệt; độc lập nghiêm ngặt không được tuyên bố.
- [x] Tính toán phân bố sao 1–5: toàn bộ số lượng nhóm hợp lệ trong `reports/p1_full_laptop_survey.md`.
- [x] Đánh giá tiềm năng số lượng: 408,480 hợp lệ / 30,000 mục tiêu = 13.616x; Cần giữ lại 7.3443%. P2 đã chọn hàng sạch 30,000; sản lượng sạch toàn nhóm vẫn là NOT_MEASURED vì đánh giá ngôn ngữ bị giới hạn.

### Chiến lược lấy mẫu P1-T08
- [x] Phân tích tính đa dạng của thương hiệu ứng viên từ nhóm metadata/valid đã lưu; số lượng, xuất xứ bình thường, nồng độ và năm biểu đồ: `reports/p1_brand_diversity.md`. Hiện đã có báo cáo bảo quản P2 before/after.
- [x] Tài liệu ~30K làm sạch tiếng Anh mục tiêu và chính sách đánh giá nhóm nhỏ hơn; sample/yield sạch cuối cùng thuộc về P2.
- [x] Chứng minh mẫu khảo sát hạt giống giữ lại tất cả năm xếp hạng; Lựa chọn clean-dữ liệu cuối cùng thuộc về P2.
- [x] Thể hiện sự đa dạng của mẫu khảo sát: sản phẩm 2,805, 68 reviews/product tối đa dưới giới hạn 100; lựa chọn cuối cùng thuộc về P2.
- [x] Chiến lược lấy mẫu P1 được chấp nhận theo C3-A; Hiện đã đo lường được mức độ bảo quản thương hiệu before/after P2; không có hạn ngạch ngang nhau.
- [x] Lưu trữ ngẫu nhiên hạt giống ngẫu nhiên.
- [x] Không bao gồm các sản phẩm không phải laptop để đạt được số hàng cố định.

**DONE_WHEN:** Việc lấy mẫu có thể được sao chép và chỉ giữ lại laptop.

## GIAI ĐOẠN ĐẦU RA
- [x] Có sẵn Amazon review + siêu dữ liệu thô: nguồn đầy đủ, tổng kiểm tra đã được xác minh, cả hai luồng đều đạt EOF.
- [x] Bộ lọc laptop được chấp nhận cho nhóm đã chọn trong C1/C2; giới hạn QA được hỗ trợ được tiết lộ.
- [x] SemEval thô có sẵn tại địa phương (máy nhân bản do người dùng cung cấp; giấy phép chưa được xác minh).
- [x] Từ điển dữ liệu có sẵn.
- [x] Chiến lược lấy mẫu được ghi lại.

---

## P1 Trạng thái hiện tại và Tiêu chí chấp nhận còn lại

- [x] Mua lại toàn bộ Amazon, tham gia siêu dữ liệu lần đầu tiên và xác minh nguồn EOF/checksum.
- [x] Kiểm tra pool/rating/schema đầy đủ và mẫu laptop giới hạn xác định.
- [x] Hoàn thành đánh giá QA được người dùng phê duyệt và phân tích negative sai.
- [x] workflow/config/CLI/tests hiện tại được chuẩn hóa thành chỉ laptop; bằng chứng lịch sử được lưu trữ
- [x] Sự chấp nhận P1-T02 được phê duyệt thông qua ngoại lệ C2-A bị giới hạn; nguồn gốc AI ban đầu được giữ lại.
- [x] Truy cập P1-T03 cục bộ tập huấn luyện v2/Test gold và kiểm tra phân chia schema/overlap gốc; Chủ sở hữu miễn xác minh source/license cho dự án giáo dục này; NOT_VERIFIED.
- [x] P1 hoàn chỉnh: bằng chứng kỹ thuật được sử dụng lại; C1/C2/C3 và ngoại lệ SemEval giáo dục đã được phê duyệt rõ ràng.

C1-A/C2-A/C3-A ĐƯỢC CHỦ SỞ HỮU2026-10-09; không có xác nhận đánh giá lặp đi lặp lại. independent/blind gán nhãn nghiêm ngặt không được yêu cầu; C2 là một ngoại lệ P1 bị chặn, P10 gold độc lập không thay đổi. Đã chấp nhận lấy mẫu thương hiệu, before/after P2 hiện đã được đo. P1 DONE: chủ sở hữu đã từ bỏ rõ ràng xác minh source/license cho SemEval Train/Test và JSONL hiện có trong dự án giáo dục này. License/source vẫn là NOT_VERIFIED; không có yêu cầu về quyền đã được xác minh. Bản ghi: `reports/tables/p1_semeval_owner_exception_20261009.json`. C4-B P2 và P3 chỉ có trên Amazon là COMPLETE. P4-P6 bây giờ là DONE; giai đoạn tiếp theo là P7, không được thực hiện ở đây. P2 sở hữu lựa chọn cleaning/labels/noise/clean; P4 sở hữu cố định các tập đã chia. Báo cáo P2 hiện tại: `reports/p2_amazon_completion_20261009.md`. Phân tích trước về thương hiệu ứng viên được giữ lại; Final181 sản phẩm siêu dữ liệu categories/9080, top5 review79.46%, unknown/ambiguous0.27%.

### Bằng chứng lịch sử (không phải quy trình hoặc ủy quyền hiện tại)

Bằng chứng acquisition/probe/full-scan trước đó vẫn còn trong `reports/` và các bảng của nó. Các vị trí run/QA được thay thế được ánh xạ trong `reports/tables/p1_laptop_only_cleanup_inventory.json`. Các phần kế hoạch lịch sử lặp lại ban đầu và v4 code/config được giữ lại trong `reports/archive/p1_legacy_workflow/`. Số lượng tiền tố nguồn cũ và trình chặn quyền không được hiểu là trạng thái khảo sát đầy đủ hiện tại.

# 5. GIAI ĐOẠN P2 — dữ liệu CHẤT LƯỢNG, LÀM SẠCH, GHI NHÃN

## MỤC TIÊU

Tạo ra laptop review bộ dữ liệu sạch và định lượng các vấn đề về chất lượng dữ liệu.

**Trạng thái: DONE cho P2 chỉ Amazon theo C4-B; P1 hiện DONE nhờ các ngoại lệ được chủ dự án chấp nhận.** Bằng chứng: `reports/p2_amazon_completion_20261009.md`, `data/interim/p2/20261009_final/manifest.json` và `reports/tables/p2_amazon_20261009_final/validation.json`. Tái sử dụng kiểm tra thiếu dữ liệu/trùng hoàn toàn trước đó; áp dụng làm sạch HTML/khoảng trắng thận trọng, dành riêng mẫu QA, loại trùng sau chuẩn hóa/cách ly nhãn xung đột, chọn tiếng Anh tự động và ánh xạ nhãn từ số sao cố định. Có 30k hàng/9080 sản phẩm/3 lớp; dành riêng 250 mẫu chẩn đoán nhiễu. Có báo cáo thương hiệu trước/sau, không áp hạn ngạch thương hiệu. Tìm gần trùng là phép tìm từ vựng xấp xỉ trên văn bản được chọn và mẫu chẩn đoán, không chứng minh đầy đủ về ngữ nghĩa. Tỷ lệ sai ngôn ngữ/spam/nhãn con người thực tế NOT_MEASURED. P2 không tạo human gold, chia tập hoặc mô hình; chia tập cố định thuộc P4 đã hoàn thành. P3-P6 hiện hoàn thành; P7 không được thực hiện trong yêu cầu P6.

### Thiếu P2-T01-Kiểm tra dữ liệu
- [x] Thiếu tỷ lệ theo trường bắt buộc (chỉ nhóm ứng viên hợp lệ đã lưu).
- [x] Chính sách xử lý được ghi lại (báo cáo trước chuyến bay của ứng viên).

### Kiểm tra P2-T02 không hợp lệ-review
- [x] Kiểm tra Empty/whitespace review (áp dụng làm sạch, giữ lại văn bản thô).
- [x] Kiểm tra review cực ngắn (không tự động xóa văn bản ngắn).
- [x] Bắt buộc phải kiểm tra bản ghi không đúng định dạng field/type/rating (chỉ nhóm ứng viên hợp lệ).

### P2-T03 Kiểm toán trùng lặp
- [x] Kiểm tra trùng lặp chính xác (áp dụng khấu trừ chuẩn hóa; lưu sổ cái hàng).
- [x] Văn bản lặp đi lặp lại trên các sản phẩm laptop đã được kiểm tra; số lượng người dùng chéo trong P2 bản kê.
- [x] Kiểm tra từ vựng gần như trùng lặp trên văn bản chẩn đoán + cuối cùng; các giới hạn gần đúng của scope/semantic được ghi lại.

### Bộ lọc P2-T04 laptop QA
- [x] Tái sử dụng C1/C2 đã được phê duyệt con người QA kiểm tra sai-positive; không có nhãn mới.
- [x] Loại bỏ ô nhiễm đã biết nếu có: không quan sát thấy trong KEEP QA ngẫu nhiên được chấp nhận; không yêu cầu loại bỏ quy tắc phạm vi hoặc yêu cầu về độ tinh khiết chung.
- [x] Bộ lọc báo cáo QA sample/result.

### P2-T05 Làm sạch văn bản
- [x] Chuẩn hóa HTML các tệp kết quả.
- [x] Bình thường hóa khoảng trắng.
- [x] Xử lý các URL khi thích hợp.
- [x] Bảo toàn sự phủ định.
- [x] Tránh làm sạch mạnh để phá hủy cảm xúc.

### P2-T06 nhãn có nguồn gốc từ xếp hạng
- [x] Áp dụng 1–2 negative / 3 neutral / 4–5 positive.
- [x] Xác thực các giá trị nhãn.
- [x] Báo cáo số lớp và tỷ lệ phần trăm.

### Ứng viên P2-T07 nhãn-nhiễu
- [x] Lưu các ví dụ có thể không đồng ý về văn bản xếp hạng cho thủ công review sau này.

### Kiểm tra mất cân bằng lớp P2-T08
- [x] Tính toán tỷ lệ và tỷ lệ phần trăm lớp đại diện được chọn cuối cùng.
- [x] Ghi lại rằng việc so sánh tập xác thực về trọng số lớp sẽ được đảm bảo sau này; không có toàn bộ bộ dữ liệu có trọng lượng khớp mô hình.
- [x] Lý do tài liệu.

### P2-T09 Làm sạch liên tục bộ dữ liệu
- [x] Lưu `data/processed/laptop_reviews.parquet`.
- [x] Ghi lại số lượng hàng before/after.
- [x] Ghi lại số liệu thống kê cleaning/filtering.

**DONE_WHEN:** Chỉ tồn tại laptop sạch tiếng Anh bộ dữ liệu; mục tiêu ~30k nếu khả thi, nếu không thì kích thước thực tế và tính đầy đủ của lớp coverage/product sẽ được ghi lại mà không làm giảm chất lượng.

## GIAI ĐOẠN ĐẦU RA
- [x] Làm sạch laptop bộ dữ liệu.
- [x] Báo cáo chất lượng dữ liệu.
- [x] Báo cáo phân phối nhãn.
- [x] Báo cáo mất cân bằng lớp học.
- [x] Mẫu ứng viên nhãn-nhiễu.

---

# 6. GIAI ĐOẠN P3 — laptop EDA VÀ CHI TIẾT

## MỤC TIÊU

Tạo ra những phân tích sâu sắc thay vì chỉ biểu đồ mô tả.

**Trạng thái: DONE (P3-T01–T08).** cố định P2 bộ dữ liệu chỉ đọc; không có P4/splits/fitting. Bằng chứng: `reports/p3_data_analysis_20261009.md`, `reports/p3_insight_summary_20261009.md`, `notebooks/03_laptop_eda.ipynb`, `reports/p3/20261009_verified/summary.json` và `notebook_validation.json`. Số liệu 15 tables/7 PNG+SVG; 6-cell notebook tính toán lại các bảng trong kernel mới. Danh mục thương hiệu là siêu dữ liệu, thông số kỹ thuật absent/not được suy ra. Các nhiệm vụ siêu dữ liệu có điều kiện đã hoàn thành ở chất lượng trường được hỗ trợ; giả thuyết từ vựng không phải là kết quả ATE/ASC. Hỗ trợ chẩn đoán mang tính mô tả, không phải là cổng chấp nhận mới. con người nhiễu nhãn thực sự và P10 gold độc lập vẫn còn unmeasured/pending. P4-P6 hiện đã hoàn tất; P7 không được thực thi.


### Tổng quan về P3-T01 bộ dữ liệu
- [x] Số lượng review.
- [x] Số lượng Laptop/product.
- [x] Số lượng Brand/category nếu đáng tin cậy.
- [x] Phạm vi thời gian nếu có.

### Phân tích xếp hạng P3-T02
- [x] Phân bổ xếp hạng.
- [x] Đánh giá của laptop/product.
- [x] Đánh giá theo thương hiệu nếu đáng tin cậy.
- [x] Đánh giá theo thời gian nếu có ý nghĩa.

### Phân tích P3-T03 cảm xúc
- [x] Phân phối tổng thể.
- [x] cảm xúc bởi laptop/product.
- [x] cảm xúc theo thương hiệu nếu đáng tin cậy.
- [x] cảm xúc theo thời gian nếu có ý nghĩa.

### P3-T04 Phân tích độ dài văn bản
- [x] Số ký tự.
- [x] Số từ.
- [x] token được tính khi hữu ích.
- [x] Chiều dài bằng sentiment/rating.

### P3-T05 Phân tích từ vựng
- [x] Các điều khoản thường xuyên.
- [x] N-gram dương.
- [x] N-gram trung tính.
- [x] N-gram âm.

### Phân tích P3-T06 Helpfulness/metadata
- [x] Tính hữu ích so với sentiment/rating/length nếu trường tồn tại.
- [x] Phân tích mua hàng đã được xác minh nếu trường tồn tại.
- [x] Chỉ phân tích Product/spec/brand khi chất lượng siêu dữ liệu hỗ trợ cho kết luận.

### Phân tích chất lượng P3-T07 dữ liệu
- [x] Tỷ lệ trùng lặp.
- [x] Tỷ lệ thiếu.
- [x] Tỷ lệ review ngắn.
- [x] Trực quan hóa sự mất cân bằng lớp học.
- [x] Ví dụ nhãn-nhiễu.

### Trích xuất thông tin chuyên sâu dành riêng cho P3-T08 laptop
- [x] Xác định các chủ đề laptop complaint/praise định kỳ từ bằng chứng.
- [x] Điều tra các khía cạnh của ứng viên như pin, màn hình, bàn phím, hiệu suất, cấu trúc, giá cả, tính di động, bộ lưu trữ, thermals/noise.
- [x] Không trình bày các khía cạnh của ứng viên dưới dạng dữ kiện thực tế cho đến khi data/ABSA hỗ trợ chúng.
- [x] Tách biệt quan sát khỏi giải thích.

**DONE_WHEN:** EDA chứa nhận định từ dữ liệu đã được chứng minh bằng bằng chứng và không chỉ có các bản phân phối.

## GIAI ĐOẠN ĐẦU RA
- [x] EDA notebook.
- [x] Figures/tables.
- [x] Tóm tắt cái nhìn sâu sắc.
- [x] Báo cáo phân tích dữ liệu.

---

# 7. GIAI ĐOẠN P4 — dữ liệu TÁCH VÀ TIẾP XÚC

## MỤC TIÊU

Tạo bộ cố định kháng rò rỉ dữ liệu.

**Trạng thái: DONE (P4-T01–T05).** hạt giống ngẫu nhiên42, parent/variant/duplicate nhóm được kết nối, hạn ngạch số nguyên cân bằng lớp:21000/4500/4500; products6357/1361/1362; không có loại trừ. tập huấn luyện negative5781/neutral1842/positive13377; validation1239/395/2866; test1239/394/2867. Bằng chứng: `reports/p4_completion_20261009.md`, `docs/P4_DATA_CONTRACT.md`, `reports/p4/p4_20261009_final/{manifest,validation,reload_validation,task_validation}.json`. Các tính năng chỉ trên tập huấn luyện TF-IDF30000 thực tế; Bản sửa đổi cố định BERT bộ tách token, tập huấn luyện p95=390 chọn512token. Không có bộ phân loại weights/benchmark/ABSA huấn luyện hoặc các chỉnh sửa SemEval. 41 tổng kiểm tra được bảo vệ và 121 tổng số tệp ảnh chụp nhanh đầu vào không thay đổi; 180tests/pip kiểm tra PASS. Sàn gỗ All3split byte-replay/full đặc trưng tải lại PASS. Kiểm tra gần là từ vựng gần đúng; người dùng overlaps/QA phạm vi sản phẩm overlaps/truncation/gold vắng mặt được tiết lộ. Một phần p4_20261009/ được bảo vệ bộ nhớ ban đầu được thay thế; chỉ _final là hiện tại. NEXT_ACTION: Phân loại lỗi P7 theo một yêu cầu riêng; P5/P6 đã hoàn thành2026-10-15 mà không thay đổi P4.


### P4-T01 cố định phân chia
- [x] mục tiêu 70/15/15.
- [x] Phân tầng cảm xúc.
- [x] Sửa hạt giống ngẫu nhiên ngẫu nhiên.

### Phân tích P4-T02 rò rỉ dữ liệu
- [x] Văn bản chính xác rò rỉ dữ liệu.
- [x] Bản sao rò rỉ dữ liệu.
- [x] Sản phẩm rò rỉ dữ liệu.
- [x] Xem xét nhóm phân chia theo `product_id` / `parent_asin`.

### P4-T03 Kiên trì các tập đã chia
- [x] Lưu tập huấn luyện.
- [x] Lưu tập xác thực.
- [x] Lưu kiểm thử.

### P4-T04 Tiền xử lý cổ điển
- [x] Vệ sinh cơ bản.
- [x] TF-IDF.
- [x] Bảo toàn sự phủ định.
- [x] khớp mô hình TF-IDF chỉ có trên tập huấn luyện.

### Tiền xử lý P4-T05 BERT
- [x] Làm sạch tối thiểu.
- [x] BERT bộ tách token.
- [x] Không có gốc.
- [x] Không loại bỏ từ dừng.
- [x] Chọn độ dài chuỗi tối đa từ phân phối độ dài token được quan sát.

## GIAI ĐOẠN ĐẦU RA
- [x] cố định các tập đã chia.
- [x] Báo cáo phân chia.
- [x] Đường ống cổ điển
- [x] đường ống BERT.

---

# 8. GIAI ĐOẠN P5 — ML CỔ ĐIỂN đánh giá so sánh

**DONE 2026-10-15.** E00–E03, số liệu và đầu ra bắt buộc đã được xác minh: `reports/p5_completion_20261015.md`. LR C0.5/balanced được chọn trên macro tập xác thực F1=0.693554; Macro cố định-kiểm thử F1=0.683887. 195 bài kiểm tra PASS; trình xác nhận độc lập PASS;149 giá trị băm đầu vào không thay đổi. BERT là P6 và chưa được chạy.

## MỤC TIÊU

Thiết lập đường cơ sở laptop cảm xúc mạnh mẽ.

### P5-E00 Đa số mô hình cơ sở
- [x] Đánh giá mô hình cơ sở thuộc loại đa số.

### Hồi quy logistic P5-E01
- [x] TF-IDF + Hồi quy logistic.
- [x] Chỉ sử dụng trọng số lớp nếu hợp lý (mất cân bằng tập huấn luyện; so sánh tập xác thực).

### SVM tuyến tính P5-E02
- [x] TF-IDF + SVM tuyến tính.
- [x] Chỉ sử dụng trọng số lớp nếu hợp lý (mất cân bằng tập huấn luyện; so sánh tập xác thực).

### Cây quyết định P5-E03
- [x] TF-IDF + Cây quyết định.
- [x] Kiểm soát quá mức (đã báo cáo các khoảng trống depth10/25, leaf5; train/validation).
- [x] Chỉ sử dụng trọng số lớp nếu hợp lý (so sánh loại bỏ cân bằng để có DT tốt nhất).

## CÁC CHỈ SỐ BẮT BUỘC
- [x] tỷ lệ dự đoán đúng (accuracy).
- [x] độ chính xác dự đoán (precision) mỗi lớp.
- [x] độ bao phủ (recall) mỗi lớp.
- [x] F1 mỗi lớp.
- [x] Macro F1.
- [x] Trọng số F1.
- [x] Ma trận nhầm lẫn.
- [x] Thời gian huấn luyện.
- [x] Độ trễ suy luận.
- [x] Kích thước mô hình.
- [x] RAM (RSS quy trình lấy mẫu, ghi lại các giới hạn đo lường).

**DONE_WHEN:** Tất cả các mô hình đều được đánh giá trên cùng một bộ cố định kiểm thử và kết quả nằm trong một bảng có thể so sánh.

## GIAI ĐOẠN ĐẦU RA
- [x] mô hình các tệp kết quả.
- [x] Bảng đánh giá so sánh.
- [x] Ma trận nhầm lẫn.
- [x] Kết luận ML cổ điển tốt nhất.

---

# 9. GIAI ĐOẠN P6 — BERT TỔNG THỂ cảm xúc

**DONE 2026-10-15 (T01–T06).** `reports/p6_completion_20261015.md` và `reports/p6/p6_20261015/`: chế độ mất full21k×3epochs×2, cân bằng vòng huấn luyện3 được chọn bởi tập xác thực macro0.734646, kiểm thử macro0.730204. 181 đầu vào được bảo vệ không thay đổi; trình xác nhận độc lập PASS,207kiểm tra PASS thông qua trình chạy bị cô lập. Không thực thi P7.

## MỤC TIÊU

Tinh chỉnh BERT cho 3 lớp laptop cảm xúc.

### Bộ chuyển đổi P6-T01 bộ dữ liệu
- [x] Tạo PyTorch/Hugging Face tương thích bộ dữ liệu (kiểm tra adapter/collator và căn chỉnh full30k PASS).

### P6-T02 tách token
- [x] BERT bộ tách token (tái sử dụng đã cố định P4, tất cả các mảng token đã được xác minh).
- [x] Chính sách Truncation/padding (cắt ngắn bên phải, đệm bên phải động).
- [x] Ghi lại độ dài chuỗi tối đa (P4 tập huấn luyện-có nguồn gốc512, không thay đổi).

### P6-T03 huấn luyện
- [x] Tinh chỉnh BERT (mạng nền đầy đủ, 2 chế độ × 3 đầy đủ vòng huấn luyện).
- [x] Theo dõi tập huấn luyện hàm mất mát.
- [x] Theo dõi tập xác thực hàm mất mát.
- [x] Theo dõi Macro F1.
- [x] Tiết kiệm tốt nhất điểm lưu mô hình (cân bằng vòng huấn luyện3, tập xác thực được chọn trước kiểm thử).

### Xử lý mất cân bằng P6-T04
- [x] Đánh giá nhu cầu hàm mất mát có trọng số (so sánh đầy đủ unweighted/balanced).
- [x] Trọng lượng lớp tài liệu nếu được sử dụng (tập huấn luyện n/(3*count), report/history).

### Đánh giá P6-T05
- [x] Số liệu phân loại tương tự như P5.
- [x] Thời gian huấn luyện.
- [x] Độ trễ suy luận.
- [x] Kích thước mô hình.
- [x] RAM (quy trình lấy mẫu RSS, tài liệu báo trước).
- [x] GPU/VRAM nếu có (Đỉnh đuốc allocated/reserved).

### So sánh P6-T06 Cost/performance
- [x] BERT so với LR.
- [x] BERT so với SVM.
- [x] BERT vs DT.
- [x] Định lượng mức tăng Macro-F1 (kiểm thử+0.046317LR/+0.052066SVM).
- [x] Định lượng mức tăng chi phí tính toán (fit/latency/size, CPU/GPU hãy cẩn thận).

## CÂU HỎI NGHIÊN CỨU CHÍNH

BERT cải thiện Macro F1 bao nhiêu so với TF-IDF + SVM tuyến tính trên laptop review và sự cải thiện đó đòi hỏi chi phí tính toán như thế nào?

## GIAI ĐOẠN ĐẦU RA
- [x] BERT mô hình.
- [x] Đánh giá BERT.
- [x] Hợp nhất đánh giá so sánh.
- [x] Phân tích Cost/performance.

---

# 10. GIAI ĐOẠN P7 — phân tích lỗi

## MỤC TIÊU

Đặc trưng các chế độ lỗi mô hình trong laptop review.

### PHÂN LOẠI LỖI
- [ ] Phủ định.
- [ ] Hỗn hợp cảm xúc.
- [ ] Sự mỉa mai.
- [ ] review rất ngắn.
- [ ] review dài.
- [ ] cảm xúc tiềm ẩn.
- [ ] Rating/text conflict.
- [ ] Multi-khía cạnh review.
- [ ] Thuật ngữ dành riêng cho laptop.

### SO SÁNH mô hình
- [ ] lỗi LR.
- [ ] lỗi SVM.
- [ ] lỗi DT.
- [ ] lỗi BERT.
- [ ] Các trường hợp BERT giải quyết được ML cổ điển bỏ sót.
- [ ] Các trường hợp tất cả các mô hình đều bị lỗi.

## GIAI ĐOẠN ĐẦU RA
- [ ] Phân loại lỗi.
- [ ] Các ví dụ có chú thích
- [ ] Phân tích lỗi cụ thể của mô hình.

---

# 11. GIAI ĐOẠN P8 — ABSA khía cạnh CHIẾT XUẤT CÓ HẠN

## MỤC TIÊU

Trích xuất các thuật ngữ laptop khía cạnh rõ ràng.

### P8-T01 Phân tích cú pháp SemEval laptop
- [ ] Bảo lưu ID câu.
- [ ] Bảo quản khía cạnh vị trí cụm từ.

### Chuyển đổi BIO P8-T02
- [ ] `B-ASP`.
- [ ] `I-ASP`.
- [ ] `O`.
- [ ] Xác thực căn chỉnh vị trí cụm từ.

### P8-T03 tập huấn luyện mô hình
- [ ] Tinh chỉnh phân loại BERT token.

### Đánh giá P8-T04
- [ ] Thực thể độ chính xác dự đoán (precision).
- [ ] Thực thể độ bao phủ (recall).
- [ ] Thực thể F1.

**DONE_WHEN:** khía cạnh vị trí cụm từ có thể được trích xuất từ các ví dụ SemEval laptop không nhìn thấy được với các chỉ số cấp vị trí cụm từ có thể tái tạo.

## GIAI ĐOẠN ĐẦU RA
- [ ] BIO bộ dữ liệu.
- [ ] Trích xuất khía cạnh mô hình.
- [ ] Đánh giá.

---

# 12. GIAI ĐOẠN P9 — ABSA khía cạnh cảm xúc PHÂN LOẠI

## MỤC TIÊU

Phân loại cảm xúc theo từng laptop khía cạnh.

## ĐẦU VÀO

`review_text + aspect_term`

## ĐẦU RA

`positive | neutral | negative`

### Chuẩn bị P9-T01 bộ dữ liệu
- [ ] Xây dựng các ví dụ về ngữ cảnh khía cạnh.
- [ ] Chuẩn hóa các lớp mục tiêu nhãn thành 3.
- [ ] Resolve/exclude không được hỗ trợ conflict nhãn và chính sách tài liệu.

### P9-T02 tập huấn luyện
- [ ] Tinh chỉnh BERT cho khía cạnh cảm xúc.

### Đánh giá P9-T03
- [ ] tỷ lệ dự đoán đúng (accuracy).
- [ ] độ chính xác dự đoán (precision).
- [ ] độ bao phủ (recall).
- [ ] Macro F1.
- [ ] Ma trận nhầm lẫn.

### P9-T04 ABSA đầu cuối
- [ ] Kết nối trích xuất khía cạnh với khía cạnh cảm xúc.
- [ ] Tạo đường ống `review -> aspect spans -> aspect sentiment`.

## GIAI ĐOẠN ĐẦU RA
- [ ] khía cạnh cảm xúc mô hình.
- [ ] Đường ống ABSA từ đầu đến cuối.
- [ ] Chỉ số ABSA

---

# 13. GIAI ĐOẠN P10 — AMAZON laptop thủ công bộ kiểm thử gold

## MỤC TIÊU

Đánh giá Amazon laptop review thực tế và định lượng hai vấn đề:
1. nhiễu nhãn có nguồn gốc từ xếp hạng;
2. SemEval→Amazon dataset/platform/style thay đổi trong cùng một laptop phạm vi.

## KÍCH THƯỚC mục tiêu

`300–500 Amazon Laptop reviews`

## LẤY MẪU
- [ ] Trên các xếp hạng.
- [ ] Trên toàn chiều dài review.
- [ ] Trên khắp laptop products/brands khi có sẵn.
- [ ] Bao gồm các trường hợp mixed/difficult.

## TRƯỜNG gán nhãn

```text
review_id
product_id
review_text
rating
rating_derived_sentiment
human_overall_sentiment
aspect_term
human_aspect_sentiment
notes
```

## NHIỆM VỤ
- [ ] con người chú thích tổng thể cảm xúc.
- [ ] con người chú thích các thuật ngữ khía cạnh.
- [ ] con người chú thích khía cạnh cảm xúc.
- [ ] Các trường hợp không rõ ràng của review.
- [ ] Đo đánh giá-vs-con người agreement/disagreement.
- [ ] Đánh giá tổng thể cảm xúc các mô hình trên bộ kiểm thử gold.
- [ ] Đánh giá ABSA được đào tạo SemEval trên Amazon laptop bộ kiểm thử gold.
- [ ] So sánh hiệu suất SemEval kiểm thử với Amazon gold-kiểm thử.

## QUY TẮC GIẢI GIẢI

Sự sụt giảm hiệu suất từ SemEval xuống Amazon phải được mô tả là **sự thay đổi dataset/platform/style trong laptop review**, chứ không phải bằng chứng về sự khái quát hóa tiện ích công nghệ phone/headphone/general.

## GIAI ĐOẠN ĐẦU RA
- [ ] `data/manual/amazon_laptop_gold_test.csv`
- [ ] Đánh giá gold-kiểm thử.
- [ ] Phân tích nhãn-nhiễu.
- [ ] SemEval→Phân tích chuyển giao của Amazon.

---

# 14. GIAI ĐOẠN P11 — ỨNG DỤNG STREAMLIT

## MỤC TIÊU

Phân tích laptop review đơn giản dành cho người dùng cuối; không có sự phức tạp không cần thiết ở lối vào.

### CHẾ ĐỘ A — laptop review đơn
- [ ] Nhập văn bản.
- [ ] Tổng thể cảm xúc.
- [ ] độ tin cậy nếu có.
- [ ] Trích xuất khía cạnh.
- [ ] khía cạnh cảm xúc.

### CHẾ ĐỘ B — lô laptop review
- [ ] Tải lên CSV.
- [ ] lô suy luận.
- [ ] Tỷ lệ phần trăm Positive/Neutral/Negative.
- [ ] Tần số đề cập đến khía cạnh.
- [ ] Phân phối cảm xúc bởi khía cạnh.
- [ ] Các khía cạnh positive/negative laptop hàng đầu.

## Lược đồ đầu ra

```json
{
  "domain": "laptop",
  "language": "en",
  "sentiment": "negative",
  "confidence": 0.91,
  "aspects": [
    {
      "aspect": "battery",
      "sentiment": "negative",
      "confidence": 0.94
    }
  ]
}
```

**DONE_WHEN:** Ứng dụng thực hiện suy luận từ các mô hình đã lưu mà không cần đào tạo lại.

## GIAI ĐOẠN ĐẦU RA
- [ ] `app/streamlit_app.py`
- [ ] Chế độ đơn review.
- [ ] Chế độ lô-review.

---

# 15. GIAI ĐOẠN P12 — tiếng Việt SẴN SÀNG MỞ RỘNG

## MỤC TIÊU

Giữ laptop phạm vi cố định trong khi thực hiện tiện ích mở rộng ngôn ngữ sau này với chi phí thấp.

## NHIỆM VỤ
- [ ] Giao diện tiền xử lý cơ bản.
- [ ] Mô-đun tiền xử lý tiếng Anh.
- [ ] Giao diện tiếng Việt placeholder/module.
- [ ] Đăng ký mô hình.
- [ ] `en -> BERT`.
- [ ] Dự trữ `vi -> PhoBERT`.
- [ ] Lược đồ đầu ra độc lập với ngôn ngữ.
- [ ] Giữ logic dành riêng cho mô hình bên ngoài giao diện người dùng Streamlit.

**DONE_WHEN:** Thêm PhoBERT yêu cầu thay đổi implementation/config, không thiết kế lại hợp đồng ứng dụng.

---

# 16. GIAI ĐOẠN P13 — HOÀN THÀNH

### Hợp nhất P13-T01 đánh giá so sánh
- [ ] LR.
- [ ] SVM.
- [ ] DT.
- [ ] BERT.
- [ ] Bảng chỉ số.
- [ ] Bảng chi phí.

### Hợp nhất phân tích P13-T02
- [ ] EDA.
- [ ] Mất cân bằng.
- [ ] nhiễu nhãn.
- [ ] phân tích lỗi.
- [ ] ABSA.
- [ ] SemEval→Chuyển laptop của Amazon.

### Tài liệu P13-T03
- [ ] README.
- [ ] Cài đặt.
- [ ] Chuẩn bị dữ liệu.
- [ ] huấn luyện.
- [ ] suy luận.
- [ ] Sử dụng ứng dụng.

### Khả năng tái tạo P13-T04
- [ ] Thiết lập môi trường trong lành.
- [ ] Đường ống dữ liệu thực thi.
- [ ] mô hình suy luận thực thi.
- [ ] Ứng dụng thực thi.

### P13-T05 Báo cáo cuối cùng
- [ ] Tuyên bố vấn đề.
- [ ] Ranh giới laptop-phạm vi.
- [ ] dữ liệu và phương pháp lọc.
- [ ] dữ liệu Quality/EDA.
- [ ] Tổng thể cảm xúc xây dựng mô hình.
- [ ] So sánh mô hình.
- [ ] phân tích lỗi.
- [ ] ABSA.
- [ ] Amazon laptop bộ kiểm thử gold.
- [ ] Ứng dụng.
- [ ] Hạn chế.
- [ ] Công việc tương lai.

## GIỚI HẠN BẮT BUỘC
- [ ] Không yêu cầu khái quát hóa ngoài laptop review.
- [ ] Đánh giá nhãn là nhãn đại diện ồn ào.
- [ ] SemEval và Amazon có thể khác nhau trong cách viết style/platform ngay cả trong laptop phạm vi.
- [ ] thủ công bộ dữ liệu gold tương đối nhỏ.

---

# 17. BẢN ĐỒ THỰC HIỆN TUẦN

## TUẦN 1
- [x] P0 đã hoàn thành.
- [x] P1 đã hoàn thành (ngoại lệ SemEval giáo dục được chủ sở hữu phê duyệt; giấy phép NOT_VERIFIED).

**EXIT_CRITERIA:** Bộ lọc laptop là defined/validated; Có thể sử dụng được nhóm Amazon laptop và SemEval; schema/sampling được ghi lại.

## TUẦN 2
- [x] P2 hoàn chỉnh (chỉ dành cho Amazon, C4-B).
- [x] P3 hoàn chỉnh (EDA mô tả dựa trên bằng chứng; kernel mới notebook PASS).

**EXIT_CRITERIA:** tồn tại laptop bộ dữ liệu sạch và EDA sâu.

## TUẦN 3
- [x] P4 hoàn thành (cố định không trùng sản phẩm giữa các tập các tập đã chia, chỉ trên tập huấn luyện tiền xử lý, tập xác thực PASS).
- [x] P5 đã hoàn thành (E00–E03, cố định kiểm thử, tương đương đánh giá so sánh và tải lại tập xác thực).

**EXIT_CRITERIA:** cố định các tập đã chia và ML cổ điển đánh giá so sánh tồn tại.

## TUẦN 4
- [x] P6 đã hoàn thành (T01–T06, fine-tuning/test/benchmark/reload/independent QA thực sự đầy đủ).
- [ ] P7 đã hoàn thành.

**EXIT_CRITERIA:** BERT đánh giá so sánh, so sánh chi phí và phân tích lỗi tồn tại.

## TUẦN 5
- [ ] P8 đã hoàn thành.
- [ ] P9 đã hoàn thành.
- [ ] P10 về cơ bản đã hoàn thiện.

**EXIT_CRITERIA:** ABSA toàn diện hoạt động và Amazon laptop bộ kiểm thử gold tồn tại.

## TUẦN 6
- [ ] P11 đã hoàn thành.
- [ ] P12 đã hoàn thành.
- [ ] P13 đã hoàn thành.

**EXIT_CRITERIA:** Ứng dụng, tài liệu, khả năng tái tạo và báo cáo cuối cùng đã hoàn tất.

---

# 18. ĐỊNH NGHĨA TOÀN CẦU CỦA DONE

## dữ liệu
- [x] Đã chọn laptop30k đã xử lý bộ dữ liệu với cổng tiếng Anh tự động; Các giới hạn của scope/quality được ghi lại.
- [x] Bộ lọc laptop có thể tái tạo được chấp nhận theo xuất xứ ban đầu của C1/C2, được giữ lại.
- [x] EDA sâu (P3 report/insights/notebook; đã tiết lộ các giới hạn suy luận).
- [x] Phân tích mất cân bằng lớp (hoàn tất so sánh trọng số P2; P5/P6 chỉ trên tập huấn luyện).
- [ ] Phân tích nhãn-nhiễu.

## TỔNG THỂ cảm xúc
- [x] Hồi quy logistic (P5).
- [x] SVM tuyến tính (P5).
- [x] Cây quyết định (P5).
- [x] BERT (P6).
- [x] đánh giá so sánh hợp nhất (P6, cố định kiểm thử; device/cost đã ghi lại cảnh báo).
- [ ] phân tích lỗi.

## ABSA
- [ ] Trích xuất thuật ngữ khía cạnh.
- [ ] Phân loại khía cạnh cảm xúc.
- [ ] ABSA đầu cuối.
- [ ] Đánh giá SemEval.

## thủ công kiểm thử
- [ ] 300–500 được chú thích thủ công Amazon laptop review.
- [ ] Phân tích xếp hạng-vs-con người.
- [ ] Đánh giá tổng thể cảm xúc gold-kiểm thử.
- [ ] SemEval→Đánh giá ABSA của Amazon laptop.

## ỨNG DỤNG
- [ ] Phân tích laptop review đơn lẻ.
- [ ] Phân tích lô laptop review.
- [ ] Tóm tắt tổng thể cảm xúc.
- [ ] Tóm tắt khía cạnh.

## KỸ THUẬT
- [ ] Kho lưu trữ có thể tái tạo.
- [ ] Đã lưu các mô hình.
- [ ] Lựa chọn language/model dựa trên cấu hình.
- [ ] Điểm mở rộng Vietnamese/PhoBERT.

## TÀI LIỆU
- [ ] README.
- [ ] Báo cáo cuối cùng.
- [ ] Hạn chế.
- [ ] Công việc tương lai.

---

# 19. QUY TẮC HOẠT ĐỘNG AI

1. Không bao giờ mở rộng phạm vi ra ngoài máy tính xách tay mà không có hướng dẫn rõ ràng cho người dùng.
2. Không bao giờ đánh dấu `[x]` mà không có bằng chứng cho thấy đáp ứng tiêu chí hoàn thành.
3. Làm việc theo thứ tự phụ thuộc trừ khi có sự song song an toàn rõ ràng.
4. Không bao giờ sửa đổi dữ liệu thô tại chỗ.
5. Ghi ngẫu nhiên các hạt giống ngẫu nhiên để lọc mẫu, lấy mẫu và tách mẫu.
6. Xác thực lọc laptop; nhiễm bẩn phụ kiện là lỗi chất lượng dữ liệu.
7. khớp mô hình preprocessing/vectorizers chỉ có trên huấn luyện dữ liệu.
8. Ngăn chặn duplicate/product rò rỉ dữ liệu trước khi báo cáo hiệu suất.
9. Sử dụng Macro F1 làm chỉ số lựa chọn chính.
10. Hãy coi cảm xúc có nguồn gốc từ xếp hạng là nhãn đại diện nhiễu.
11. Sử dụng quy trình tiền xử lý thích hợp riêng biệt cho ML và BERT cổ điển.
12. So sánh các mô hình trên cùng một bộ cố định kiểm thử.
13. Lưu các tệp kết quả cần thiết để tiếp tục công việc.
14. SemEval→Sự thay đổi hiệu suất của Amazon phải được mô tả giống như sự thay đổi phạm vi dataset/platform/style.
15. Không yêu cầu khái quát hóa tiện ích phone/headphone/other.
16. Cập nhật tệp này khi trạng thái tác vụ thay đổi.
17. Nếu dự án phạm vi thay đổi, trước tiên hãy cập nhật HỢP ĐỒNG DỰ ÁN.

## Lịch sử bằng chứng

Các sự kiện acquisition/QA/normalization lịch sử vẫn còn trong báo cáo ghi ngày của chúng chứ không phải là danh sách kiểm tra hoạt động trùng lặp. Xem `reports/p1_semeval_laptop.md`, `reports/p1_independent_human_qa.md`, `reports/p1_recall_reliability.md`, `reports/p1_qa_v2_annotation_validation.md`, `reports/annotation_human_review_20261009.md`, `reports/p1_qa_v2_completion_20261009.md` và `reports/candidate_quality_preflight_20261009.md`. Ánh xạ v2 đã giải quyết và các khoảng trống kế thừa tùy chọn không phải là các công cụ chặn hiện tại.
