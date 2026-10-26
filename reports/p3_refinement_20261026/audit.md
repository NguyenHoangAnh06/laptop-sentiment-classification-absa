# Current P3 Audit — P3-REFINE-01

| Item | Type | Purpose / insight | Later phase | Recommendation |
| --- | --- | --- | --- | --- |
| sentiment.csv | table | Neutral8,77%; macro/per-class F1 | P5–P7 | KEEP |
| length_by_sentiment.csv | table | Median/IQR theo lớp; giữ đuôi dài | P4/P6 | KEEP |
| lexical_by_class.csv | table | Tỷ lệ trong/ngoài lớp; hỗ trợ và effect size | P7/P8/P9 | KEEP |
| themes.csv | table | Mention rates có từ điển, không polarity | P8/P9 | KEEP |
| brands.csv | table | Chỉ giữ concentration, không xếp hạng hãng | P4/P7 | KEEP |
| products.csv | table | Nhóm sản phẩm lặp và singleton; split | P4 | KEEP |
| verified.csv | table | Chênh negative10,30điểm%; confounded bởi độ dài | P7 | KEEP |
| rating.csv | table | Tra mapping sao; trùng class snapshot | P2/P7 | APPENDIX |
| years.csv | table | Audit thời gian, chưa quyết định model | Tham khảo | APPENDIX |
| months.csv | table | Audit coverage, không doanh số | Tham khảo | APPENDIX |
| missing.csv | table | Null/empty audit; P2 có báo cáo riêng | P2 | APPENDIX |
| theme_contexts.csv | table | Ngữ cảnh chưa human-verified; giữ local | P8/P9 | APPENDIX |
| noise_examples.csv | table | Worklist riêng, không noise prevalence | P7 | APPENDIX |
| frequent_terms.csv | table | Tần suất chung không phân biệt lớp | Không thêm quyết định | REMOVE FROM REPORT |
| length_histogram.csv | table | Trùng độ dài; thiếu class conditioning | Không thêm quyết định | REMOVE FROM REPORT |
| figures/rating_proxy.png | figure | Chỉ giữ panel class; bỏ panel sao lặp | P5–P7 | KEEP |
| figures/length.png | figure | Thay median bars bằng median/IQR | P4/P6 | KEEP |
| figures/distinctive_bigrams.png | figure | Top5/lớp; within vs outside rates | P7 | KEEP |
| figures/brands.png | figure | Concentration table đủ cho core | P4/P7 | APPENDIX |
| figures/time.png | figure | Coverage tham khảo | Tham khảo | APPENDIX |
| figures/themes.png | figure | Lặp bảng mention rates | P8/P9 dùng bảng | REMOVE FROM REPORT |
| figures/verified_purchase.png | figure | Bảng ngắn đủ và nêu confounders | P7 dùng bảng | REMOVE FROM REPORT |

Nguồn cũ:15tables/7figures; Markdown3bảng/0embedded figures/9sections; HTML tổng hợp nhúng15tables/7figures. Đề xuất7table KEEP/6APPENDIX/2REMOVE;3figure KEEP/2APPENDIX/2REMOVE. Hai concentration tables gộp; thêm failure slice và traceability: bản mới8core tables/3figures/9appendix items. Không xóa file cũ. Helpfulness chỉ appendix do thiếu exposure và complaint-specificity labels.

Artifacts ngoài bảng: reports/p3/20261009 và _final là superseded; _verified là nguồn. Summary/task_validation/notebook_validation là acceptance lịch sử, giữ nguyên. Source notebook và executed/final notebook, hai báo cáo MD, HTML20261019, scripts analyze_p3/export_p3_report/p3_report_content/execute_p3_notebook, src/data/eda.py giữ nguyên. Config P4 trỏ P3 summary cũ để tái lập; config mới chỉ chọn presentation, không thay pipeline. README/PLAN/PROJECT_INDEX dẫn canonical mới; downstream manifests giữ references/hash lịch sử.
