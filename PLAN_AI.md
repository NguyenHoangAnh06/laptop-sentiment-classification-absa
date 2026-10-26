# Kế hoạch thực hiện AI — laptop sentiment và ABSA

Cập nhật 2026-10-26. Yêu cầu hiện hành, `AGENTS.md` và bằng chứng thực thi có thẩm quyền cao hơn kế hoạch lịch sử. Bản đầy đủ trước dọn dẹp nằm tại [kho lịch sử](docs/archive/20261024_before_cleanup/PLAN_AI.md); các mục đã thay thế không còn là lệnh chạy tiếp.

## Hợp đồng và trạng thái chung

- Chỉ laptop tiếng Anh; laptop 2-in-1 hợp lệ. Nhãn `negative/neutral/positive`, ID0/1/2. Tiếng Việt là ngôn ngữ trao đổi, chưa phải ngôn ngữ mô hình.
- Dữ liệu/EDA50%, mô hình/phân tích lỗi40%, ứng dụng10%; không mở rộng hạ tầng ngoài nhu cầu experiment.
- Amazon2023 review nối metadata; nhãn suy từ sao1–2/3/4–5 là proxy. Raw bất biến; không tạo gold giả, không đưa token/raw lớn vào Git.
- Dataset30000; split train21000/validation4500/test4500, seed42, product-disjoint theo audit đã lưu. Không acquisition/cleaning/resplit/regenerate cache hoặc rerun baseline nếu không có lỗi thực tế.
- Frozen MiniLM384 cho XGBoost/TabM/TabPFN; BERT nhận canonical title+body qua tokenizer riêng. Không TF-IDF/BoW/PCA/SVD hoặc metadata features trong benchmark hiện hành. Hợp đồng: `docs/MODEL_STACK_REFACTOR.md`.
- Chọn bằng validation macro F1; báo cáo accuracy/weighted F1/balanced accuracy/per-class precision/recall/F1/confusion matrix, runtime/RAM/GPU/artifact size. Không tune bằng test/gold.
- Test đã được xem trong LEGACY và benchmark local. Cloud full21K phải là experiment riêng, đóng băng thiết kế trước test và công bố test reuse; không gọi test hoàn toàn unseen.
- `[x]` chỉ nghiệm thu phạm vi ghi rõ; LIMITED không có nghĩa full-data. REPORTED là bằng chứng trước, VERIFIED là kiểm tra trong tác vụ; PENDING/NOT_MEASURED không phải kết quả đã chạy.

## Bảng trạng thái hiện hành

| Phạm vi | Trạng thái | Bằng chứng |
|---|---|---|
| P0–P4 | PASS/REUSED | báo cáo pha và cache semantic giữ nguyên |
| P5 E00/E01/E02 | PASS/REUSED | majority/XGBoost/TabM full21000 |
| P5 E03/E04 local | LIMITED | V3=10000, V3_5=1500; E03 WARNING RSS6,48GB |
| P6 | PASS | BERT canonical full21000, unweighted epoch3 |
| P7 local lịch sử | PASS trong giới hạn local P5 | snapshot giữ nguyên249tests ban đầu; import cloud291tests là lịch sử |
| P5-CLOUD và cập nhật P7 | PASS | V3/V3_5 full21000 Kaggle SUCCESS; metrics/IDs/hash verified,291tests PASS |
| P7 human diagnosis | DONE | 360 human-reviewed; integrity/proxy/human/sáu model PASS; reports/p0_p7_acceptance.json |
| P8 | DONE | SemEval laptop BIO/BERT ATE; entity test F1=0,804478;350tests PASS; reports/p8_20261026/acceptance.json |
| P9 | DONE | P9-EXP01 DeBERTa canonical: valmacro0,777467/testmacro0,780433; jointF10,660550;380tests PASS; reports/p9_exp01_deberta_20261026_v2/acceptance.json |
| P10–P13 | PENDING | Independent gold/domain shift/app chưa hoàn tất |

Nguồn kết quả: `reports/model_stack_refactor_completion.md`, `reports/p7_unified_results.csv`, `reports/model_stack_final_validation.json`. Local subsample giữ LIMITED trong lịch sử; kết quả chính mới dùng cloud full21K theo reports/tabpfn_kaggle_full21k_verification.md.

# 3. GIAI ĐOẠN P0 — Môi trường

- [x] P0-T01–T04: cấu trúc/config/language/seed/dependencies/CUDA đã kiểm; TabPFN pin9.2.0 và explicit V3/V3_5.

**DONE_WHEN:** môi trường và phân biệt checkpoint PASS. Bằng chứng `reports/p0_model_stack_refactor.md`; chi tiết tác vụ cũ lưu trong kế hoạch lịch sử. Không cài lại môi trường đang hợp lệ.

# 4. GIAI ĐOẠN P1 — Nguồn và phạm vi laptop

- [x] P1-T01–T08: reuse raw Amazon/metadata, schema/join/filter/QA và nguồn SemEval hiện có.

**DONE_WHEN:** nguồn/version/provenance, metadata coverage và quyết định QA được lưu. `reports/p1_revalidation_for_new_models.md` và `reports/p1_acceptance_decision_20261009.md` là bằng chứng. SemEval source/license vẫn NOT_VERIFIED theo ngoại lệ giáo dục đã ghi, không diễn giải thành quyền được xác minh. QA sản phẩm không phải sentiment gold.

# 5. GIAI ĐOẠN P2 — Cleaning và proxy labels

- [x] P2-T01–T09: 30K, rating mapping, chất lượng/duplicates/missingness, brand diversity và whitelist đã kiểm; không thay dữ liệu.

**DONE_WHEN:** dữ liệu tái lập và báo cáo QA có thật; các độ chính xác language/spam/noise chưa audit người phải ghi NOT_MEASURED. Bằng chứng `reports/p2_revalidation_for_new_models.md`, `reports/p2_amazon_completion_20261009.md`.

# 6. GIAI ĐOẠN P3 — EDA và readiness

- [x] P3-T01–T08: EDA cũ reuse, bổ sung length/truncation/imbalance/resource readiness.

**DONE_WHEN:** insight có bảng/biểu đồ và giới hạn nhãn; không tạo kết luận khía cạnh bằng từ khóa cố định. Canonical trình bày tinh gọn P3-REFINE-01: `reports/p3_refinement_20261026/report.md`, audit/summary cùng namespace; readiness `reports/p3_model_readiness.md`. Báo cáo gốc `reports/p3_data_analysis_20261009.md` và toàn bộ tables/figures/notebooks lịch sử giữ nguyên để tái lập downstream; refinement không thay dataset/split/model/benchmark hoặc tiêu chí nghiệm thu pha.

# 7. GIAI ĐOẠN P4 — Split và representation

- [x] P4-T01–T06: giữ split, canonical title+body, cache frozen384 đầy đủ30K, row mapping/labels/tokenizer/hash và leakage audit.

**DONE_WHEN:** cache/hash/config/alignment PASS; vectorizer/normalization phụ thuộc dữ liệu chỉ fit train. Encoder `sentence-transformers/all-MiniLM-L6-v2`, revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41, mask-mean/L2/FP32/max256. BERT revision86b5e0934494bd15c9632b12f734a8a67f723594/max512. `configs/semantic_benchmark.yaml`, `reports/p4_semantic_representation.md`; không đổi config để làm cache cũ giả hợp lệ.

# 8. GIAI ĐOẠN P5 — Benchmark frozen embeddings

- [x] E00 majority sanity, E01 XGBoost và E02 TabM full21000; baseline/model selection/test đã khóa, không retrain.
- [x] E03 explicit V3 local: LIMITED/SUBSAMPLED10000, metrics/hash/alignment PASS. RSS6,48GB vượt trần6GB; n_estimators1 chỉ phủ tối đa200/384 chiều nội bộ. Giữ cảnh báo, không sửa score sau test.
- [x] E04 explicit V3_5 local: LIMITED/SUBSAMPLED1500, metrics/hash/alignment PASS. Full21K local V3.5 NOT_MEASURED; cloud mới SUCCESS, không sửa bằng chứng local thành OOM.
- [x] Resource train-only, SDK version distinction, validation selection, lock và saved predictions đủ bằng chứng local.
- [x] P5-C01: người dùng đã chạy Kaggle Tesla T4; environment/resources có evidence. Chi phí tiền NOT_MEASURED; không khởi tạo job mới trong tác vụ import.
- [x] P5-C02: gói Kaggle đã export và người dùng chạy cloud; hash/alignment/secret scan PASS tại `cloud/kaggle_tabpfn_full21k/`. Xem `reports/kaggle_tabpfn_full21k_preparation.md`.
- [x] P5-C03: resource assessment V3 full21000 trên cloud, official memory/cache/batching; ghi RAM/GPU/time/hardware, không validation/test tuning tài nguyên.
- [x] P5-C04: experiment V3 full21000 với cấu hình cố định; verify metrics/alignment/version/selection, output mới, không overwrite local.
- [x] P5-C05: lặp resource assessment và experiment riêng V3_5 full21000; không suy từ V3.
- [x] P5-C06: bổ sung comparison full-data và compute cloud vào P7; giữ bảng local lịch sử, công bố test reuse và khác thiết bị.

**Phân tích nguyên nhân:** đã hoàn tất human-reviewed diagnosis360, tách SRS300/enriched60; có proxy–human và model–human metrics. Không xác định causal fraction của imbalance hoặc suy rộng nhiễu toàn30K; independent P10 gold vẫn PENDING.

**DONE_WHEN local:** `reports/p5_modern_tabular_models.md` phản ánh LIMITED và artifacts xác minh. **DONE_WHEN cloud:** cả hai có kết quả full21000 được kiểm hoặc giới hạn mới có bằng chứng; không đánh dấu hoàn tất từ kế hoạch. Chi tiết phụ thuộc/cổng: [kế hoạch cloud](docs/TABPFN_CLOUD_PLAN.md). Không dùng `--attempt` để mở lại experiment đã selection/test; cần tên/thư mục experiment cloud riêng và hỗ trợ runner trước khi chạy.

# 9. GIAI ĐOẠN P6 — BERT canonical end-to-end

- [x] P6-T01–T06: tokenizer/dataset canonical, smoke forward/backward, unweighted/balanced, validation history, checkpoint hash/reload và một lượt test.

**DONE_WHEN:** đủ21000 train, lựa chọn validation macro F1, output aligned và metrics độc lập PASS. Chọn unweighted epoch3; test macro0,755382/neutral0,436129. `reports/p6_transformer_benchmark.md`, `configs/transformer_benchmark.yaml`. Không cần chạy lại BERT để chỉ chuyển hai TabPFN lên cloud.

# 10. GIAI ĐOẠN P7 — Unified evaluation và phân tích lỗi

- [x] Local: đủ6model, bảng metric/cost, confusion matrices, nhóm lỗi/transition và ví dụ chưa human verified.
- [x] Tách comparison cùng frozen representation và best frozen vs BERT; nêu train size/context/thiết bị khác nhau.
- [x] Test suite249PASS và53legacy hashes nguyên theo bằng chứng cuối; confidence null khi chưa có xác suất justified/calibrated.
- [x] Sau P5-C06: bảng chính dùng TabPFN full21000 cloud verified; snapshot subsample giữ ở reports/history/tabpfn_before_kaggle_20261024. Không chọn lại model từ test.
- [x] Xác minh chẩn đoán:321tests PASS (306 trước+15 human diagnosis),53legacy hashes nguyên; báo cáo reports/p7_error_diagnosis_validation.json.
- [x] P7-D01: phân tích bất đồng proxy cho6model active, bao gồm cloud; strata/confusion/ID alignment/predicted class shares/consensus có mẫu số rõ. `reports/p7_error_cause_analysis.md`.
- [x] P7-D02: tổng hợp BERT unweighted/balanced đã lưu trên validation, chọn epoch bằng macro F1, paired corrected/regressed/false positives; không chạy lại model hoặc tuning test.
- [x] P7-D03: audit kit đọc mù300SRS test+60ca enriched rời nhau,seed42; validator/evaluator tách hai nhóm, không tạo human labels hoặc independent gold. `docs/SENTIMENT_DIAGNOSIS.md`.
- [x] P7-H01: người dùng xác nhận toàn bộ360 nhãn human-reviewed ngày2026-10-25; integrity/source mapping PASS. Đã đo agreement/disagreement/kappa/rating/ambiguity/sáu model, A–E rời nhau và D rộng riêng. SRS300 và enriched60 tách biệt; CI chỉ cho test4500, không toàn30K. `reports/p7_human_audit_results.json`, `reports/p7_error_cause_analysis.md`. Không tuyên bố causal error fraction của imbalance; independent P10 gold vẫn PENDING.

**P7: DONE**, đã khóa trước P8. Proxy–human disagreement68/360 chỉ mô tả mẫu; SRS31/300 và enriched37/60. BERT diagnosis human macro0,674358 (gộp) và0,691746 (SRS); không thay canonical score/ranking. Không retrain sentiment khi triển khai P8. Kiểm P0–P7/giới hạn ở `reports/p0_p7_acceptance.json`; P8 được nghiệm thu riêng bên dưới.

**DONE_WHEN local:** `reports/p7_unified_benchmark.md` và `reports/p7_completion.json` PASS trong giới hạn công bố. Best model theo validation là BERT; best frozen local là TabM. Không suy diễn human sentiment accuracy.

## Các pha dài hạn giữ nguyên tiêu chí

P8 và P9 đã triển khai theo hai yêu cầu riêng ngày2026-10-26. P10–P13 vẫn PENDING; giữ ID và yêu cầu independent gold/domain shift/app. Nghiệm thu P9 không tự cho phép triển khai P10.

# 11. GIAI ĐOẠN P8 — ABSA khía cạnh CHIẾT XUẤT CÓ HẠN

## MỤC TIÊU

Trích xuất các thuật ngữ laptop khía cạnh rõ ràng.

### P8-T01 Phân tích cú pháp SemEval laptop
- [x] Bảo lưu ID câu.
- [x] Bảo quản khía cạnh vị trí cụm từ.

### Chuyển đổi BIO P8-T02
- [x] `B-ASP`.
- [x] `I-ASP`.
- [x] `O`.
- [x] Xác thực căn chỉnh vị trí cụm từ.

### P8-T03 tập huấn luyện mô hình
- [x] Tinh chỉnh phân loại BERT token.

### Đánh giá P8-T04
- [x] Thực thể độ chính xác dự đoán (precision).
- [x] Thực thể độ bao phủ (recall).
- [x] Thực thể F1.

**DONE_WHEN:** khía cạnh vị trí cụm từ có thể được trích xuất từ các ví dụ SemEval laptop không nhìn thấy được với các chỉ số cấp vị trí cụm từ có thể tái tạo.

## GIAI ĐOẠN ĐẦU RA
- [x] BIO bộ dữ liệu.
- [x] Trích xuất khía cạnh mô hình.
- [x] Đánh giá.

**P8: DONE**, đã khóa trước P9. `reports/p8_aspect_extraction.md`; nghiệm thu `reports/p8_20261026/acceptance.json`. Train/validation/test=2587/458/800 câu,2039/319/654 entities. WordPiece BIO toàn subword;0unexplained alignment failures,1train-only whitespace adjustment giữ original span. Group split seed42 chỉ từ official train,train–validation không trùng normalized text; official train/test có1natural duplicate được giữ và công bố, raw ID227 dùng qualified UID. BERT base pin revision,5epoch,best4 theo validation entityF1=0,799401; official test P/R/F1=0,785714/0,824159/0,804478 sau selection lock. Predictions/metrics/error analysis/reload/CPU API và350tests PASS tại thời điểm P8;269files P0–P7/raw giữ nguyên. P9 không retrain P8 hoặc thay sentiment benchmark. Chi tiết config/giới hạn source-license và GPU determinism trong báo cáo frozen.

---

# 12. GIAI ĐOẠN P9 — ABSA khía cạnh cảm xúc PHÂN LOẠI

## MỤC TIÊU

Phân loại cảm xúc theo từng laptop khía cạnh.

## ĐẦU VÀO

`review_text + aspect_term`

## ĐẦU RA

`positive | neutral | negative`

### Chuẩn bị P9-T01 bộ dữ liệu
- [x] Xây dựng các ví dụ về ngữ cảnh khía cạnh.
- [x] Chuẩn hóa các lớp mục tiêu nhãn thành 3.
- [x] Resolve/exclude không được hỗ trợ conflict nhãn và chính sách tài liệu.

### P9-T02 tập huấn luyện
- [x] Tinh chỉnh BERT cho khía cạnh cảm xúc.

### Đánh giá P9-T03
- [x] tỷ lệ dự đoán đúng (accuracy).
- [x] độ chính xác dự đoán (precision).
- [x] độ bao phủ (recall).
- [x] Macro F1.
- [x] Ma trận nhầm lẫn.

### P9-T04 ABSA đầu cuối
- [x] Kết nối trích xuất khía cạnh với khía cạnh cảm xúc.
- [x] Tạo đường ống `review -> aspect spans -> aspect sentiment`.

## GIAI ĐOẠN ĐẦU RA
- [x] khía cạnh cảm xúc mô hình.
- [x] Đường ống ABSA từ đầu đến cuối.
- [x] Chỉ số ABSA

**P9-EXP01 COMPLETE — READY TO CONTINUE TO P10.** Canonical ASC mới là `microsoft/deberta-v3-base`, revision8ccc9b6f36199bec6961081d44eb72fb3f7353f3; selector `configs/p9_canonical.yaml`, [báo cáo](reports/p9_exp01_deberta_20261026_v2/report.md), [nghiệm thu](reports/p9_exp01_deberta_20261026_v2/acceptance.json). Giữ đúng1999/314/638examples, split/P9 preprocessing/conflict/markers và evaluation code; native tokenizer có CLS/SEP và marker IDs128001/128002, zero truncation. Unweighted epoch5/seed42 thắng validation macroF1=0,777467 so với BERT0,714145; balanced best0,765511. Seed43/44 chỉ validation0,767943/0,754664, không chọn seed tốt nhất hoặc dùng mean thay single-seed baseline. Official test1pass sau lock: macroF1/accuracy/weightedF1=0,780433/0,815047/0,813232; joint frozen P8 P/R/F1=0,644776/0,677116/0,660550, extraction counts không đổi.380tests PASS,381frozen files P0–P8/baseline P9 giữ hash. BERT previous canonical và source11files giữ đúng provenance tại namespace cũ/snapshot mới; không xóa/retrain P8 hoặc sentiment. Attempts thiếu CLS/SEP bị loại trước test; resume DeBERTa bị chặn do vocab mismatch, seed43 đã restart pretrained riêng, ghi rõ trong report. Confidence null, SemEval→Amazon shift và independent P10 gold vẫn PENDING. Dừng, không triển khai P10.

---

# 13. GIAI ĐOẠN P10 — AMAZON laptop thủ công bộ kiểm thử gold

## MỤC TIÊU

Đánh giá Amazon laptop review thực tế và định lượng hai vấn đề:
1. nhiễu nhãn có nguồn gốc từ xếp hạng;
2. SemEval→Amazon dataset/platform/style thay đổi trong cùng một laptop phạm vi.

## KÍCH THƯỚC mục tiêu

`300–500 Amazon Laptop reviews`

Audit chẩn đoán reused-test360review ở P7-D03 là bộ riêng, không thay independent P10 gold. Tooling đã chuẩn bị không đồng nghĩa human annotation/gold evaluation hoàn tất; các checkbox P10 dưới đây vẫn chờ bằng chứng người thật.

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
- [ ] Majority sanity.
- [ ] XGBoost.
- [ ] TabM.
- [ ] TabPFN V3/V3_5.
- [ ] BERT canonical.
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

