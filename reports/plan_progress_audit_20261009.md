# Audit kế hoạch và bằng chứng tiến độ

Ngày 2026-10-09, Asia/Saigon. **Milestone đang hoạt động: P1, review nghiệm thu còn thiếu.** Đã đồng bộ hai PLAN; không thay tên, thứ tự, mục tiêu hoặc deliverable P0–P13. Đây là báo cáo bằng chứng tại thời điểm audit, không phải roadmap hoặc danh sách kiểm tra tiến độ độc lập. Trạng thái hiện hành nằm trong hai PLAN.

## Nguồn kế hoạch và phạm vi kiểm tra

`PLAN_HUMAN.md` là kế hoạch chính cho người đọc, `PLAN_AI.md` là bản thực thi với tác vụ IDs và DONE_WHEN. Yêu cầu hiện tại ưu tiên cách phân vai này; các tiêu chí chi tiết đã có trong PLAN_AI được giữ nguyên. Không có xung đột thứ tự P0–P13 buộc người dùng lựa chọn lại PLAN. AGENTS và yêu cầu mới vẫn có ưu tiên cao hơn.

| Tài liệu | Vai trò |
|---|---|
| `PLAN_HUMAN.md` | phạm vi, mục tiêu, milestone, lịch sáu tuần và deliverable |
| `PLAN_AI.md` | Cùng milestone; tác vụ ID, nghiệm thu và quy tắc thực thi |
| `customer_sentiment_analysis_plan.docx` | Bản tổng quan lịch sử, cùng thứ tự quy trình; còn mục tiêu50k |
| `reports/archive/p1_legacy_workflow/PLAN_AI.md`, `PLAN_HUMAN.md` | bản chụp trạng thái lịch sử; README_ARCHIVE xác nhận không còn là quy trình hiện hành |
| `AGENTS.md` | Thỏa thuận làm việc, tính toàn vẹn khoa học và bàn giao |
| `docs/CODEX_HANDOFF.md` | Tóm tắt tiếp tục công việc, không định nghĩa nghiệm thu |
| Hướng dẫn `reports/*.md`, `data_dictionary.md`, QA | Bằng chứng/phương pháp/contracts; không thay phạm vi milestone |
| `data/manual/independent_qa/p1_v2/sample_size_planning.json` | Thiết kế cỡ mẫu QA, không phải kế hoạch dự án khác |

Đã tìm các tên PLAN/roadmap/progress/handoff trong repository, đọc hai PLAN hiện hành và bản chụp trạng thái lịch sử, trích nội dung bản từ, đối chiếu báo cáo cấp project, dictionary, cấu hình, registry/schema và inventory source/scripts/tests/artifacts. Không có nested AGENTS khác trong inventory. Audit JSON ghi hàm băm tài liệu và các tệp kết quả được kiểm tra; không hàm băm chính JSON đầu ra. Không sửa bản Word/history.

## Mâu thuẫn và cách xử lý

1. **mục tiêu Word50k khác mục tiêu hiện hành30k:** giữ từ làm lịch sử; hai PLAN và
   cấu hình đã có30k theo yêu cầu ngày2026-10-08. Không tái định nghĩa quy mô.
2. **phân chia bị gán P2 trong ghi chú:** sửa ghi chú để P2 sở hữu sạch bộ dữ liệu,
   P4 sở hữu70/15/15, rò rỉ dữ liệu analysis và tiền xử lý; không di chuyển tác vụ gốc.
3. **QA v2 vừa hoàn thành vừa chờ annotation/mapping:** loại các danh sách kiểm tra cập nhật
   lịch sử lặp ở cuối PLAN, thay bằng liên kết dated báo cáo; tiếp theo Action dùng canonical đánh giá hiện có, không yêu cầu gán lại868 nhãn hay xác nhận reviewer lần nữa. Các báo cáo lịch sử giữ nguyên số liệu/provenance.
4. **con người PLAN tick filtering rule deliverable trong khi AI PLAN chưa validated:**
   thống nhất deliverable validated còn unchecked; code/rule preparation đã hoàn thành.
5. **P2 tất cả unchecked dù preflight đã có:** credit các audit thực tế tại P2;
   làm sạch, tiếng Anh tập xác thực, loại trùng, cuối cùng labeling/dataset chưa hoàn thành.
6. **Ba ứng viên biểu đồ bị coi như P3 hoàn thành:** ghi P3 IN PROGRESS, làm sớm;
   clean-bộ dữ liệu EDA và nhận định vẫn đang chờ. Không tick whole-phase outputs.
7. **README/handoff chỉ dẫn cũ:** cập nhật milestone, trạng thái QA và ranh giới
   phases. báo cáo không có quyền kéo dài authorization của yêu cầu trước.
8. **P0 schema/routing trùng một phần P12:** ghi nền tảng đã có ở P0; tái sử dụng trong
   P12, không tính thêm một mô hình registry có điểm lưu mô hình bộ tải hoặc PhoBERT hoạt động.

## Bằng chứng và trạng thái P1

| Nhiệm vụ | Trạng thái | Bằng chứng thực tế / phần còn thiếu |
|---|---|---|
| Mua lại P1-T01 | DONE | Raw manifests/full survey;41 được bảo vệ files đối chiếu checksum |
| Bộ lọc P1-T02 laptop | CẦN review | siêu dữ liệu-first linkage/rules/code; v1/v2 evaluations có; independent/coverage nghiệm thu thiếu |
| Mua lại SemEval P1-T03 | BLOCKED | gốc XML local và JSONL có; authorized source/licence bằng chứng thiếu |
| Lược đồ Amazon P1-T04 | DONE | Báo cáo khảo sát, từ điển Loader/validation, |
| Lược đồ SemEval P1-T05 | DONE | XML/offset/polarity chuẩn hóa báo cáo và bản kê; không chạy lại conversion |
| Từ điển P1-T06 | DONE | `data_dictionary.md` mô tả fields/types/provenance/usage |
| Kiểm toán P1-T07 size/rating | DONE | Saved408,480 valid các ứng viên;28,161 sản phẩm có valid review; không clean-tiếng Anh claim |
| Lấy mẫu P1-T08 | ĐANG TIẾN HÀNH/CẦN review | Seeded sample/product/rating bằng chứng và thương hiệu analysis; bảo toàn criterion chưa chốt |

QA v2 saved FN1/TN867, con người-approved canonical mapping; gốc ACCEPT/REJECT giữ nguyên. Conditional combined độ bao phủ (recall)89.0767%, joint95% CI55.4584–99.8455%. KEEP độ chính xác dự đoán (precision)100% trên mẫu và criterion0.95 đã PASS có điều kiện trên nhãn. Khoảng tin cậy không bao phủ AI anchoring/human nhãn error. v1 có AI assistance, v2 history unspecified; không khẳng định fully blind.100 mô hình cơ sở blanks không chặn QA v1/v2. Đánh giá đã hoàn thành; checksum verification không phải một đánh giá mới.

### nghiệm thu packet cho tác vụ tiếp theo của P1

| Hạng mục | bằng chứng đã có | Cần bổ sung theo điều kiện nghiệm thu hiện hành |
|---|---|---|
| tập xác thực độc lập | con người phê duyệt, nguồn/canonical bindings, v1/v2 lỗi | độc lập human/source verification với process bằng chứng; nếu thay bằng nghiệm thu của AI-assisted QA thì đó là thay đổi tiêu chí cần người dùng quyết định |
| Mức độ phù hợp | Recall/CI trên, rare-event lấy mẫu design,4 FN cases phân biệt random/diagnostic | Kết luận nghiệm thu có lý do về uncertainty; chưa có recall/F1 cutoff, không tự đặt cutoff hoặc tune filter từ evaluated QA |
| Tiêu chí lấy mẫu thương hiệu |369 loại strings/336 thô; top5 review chia sẻ79.77%; unknown/ambiguous0.32% review | Chốt cách chứng minh diversity trong lấy mẫu; ghi product/review denominators và unknown separately; không tự áp uniform thương hiệu quota |
| SemEval được ủy quyền | Chuyển đổi XML hashes/split preservation/lossless, nguồn trước review | Exact source/revision và acquisition/terms bằng chứng hoặc mirror permission được xác minh; code licence/global nhãn phê duyệt không đủ |

Khuyến nghị thương hiệu: dùng observed brand/product coverage và concentration trong lấy mẫu báo cáo, ghi rõ ảnh hưởng cap/dedup/cleaning đến phân bố; không loại thương hiệu nhỏ hoặc bù sản phẩm không phải laptop. Đây là đề xuất cho điều kiện nghiệm thu chưa chốt, không phải tiêu chí mới được tự phê duyệt. Final-clean bảo toàn thực thi trong P2, báo cáo ngược lại tác vụ lấy mẫu P1; không đếm như hai lần hoàn thành cùng công việc.

BLOCKED: chưa có authorized SemEval bằng chứng và P1 nghiệm thu chưa đóng. NEXT_ACTION: hoàn tất những evidence/decisions trong bảng này; giữ nguyên QA nhãn, không lặp mô hình cơ sở hoặc tự tuyên bố P1 hoàn thành. Đã hoàn thành phần tổng hợp review có thể làm ngay; các hành động cần human/source bằng chứng không được giả lập.

## Đối chiếu P2 và công việc làm sớm

Tái sử dụng `reports/data_quality/candidate_pool_20261009/audit.json`, đầu vào hàm băm và bound QA các nguồn; không chạy lại audit408,480 rows. Policy xử lý thiếu đã ghi ở ứng viên preflight: quarantine invalid required/rating, exclude normalized rỗng có ledger, giữ optional null, không tự xóa ngắn texts.

| Nhiệm vụ | Trạng thái | Đã có / chưa có |
|---|---|---|
| Thiếu P2-T01 | DONE cho nhóm ứng viên hợp lệ | Required/optional missing0 và policy; không suy ra thiếu toàn raw/260 excluded |
| P2-T02 review không hợp lệ | ĐANG TIẾN HÀNH | Empty0, ngắn<5 words38,419, required types/rating audit; chưa xử lý cuối cùng bộ dữ liệu |
| Bản sao P2-T03 | ĐANG TIẾN HÀNH | Exact excess25,747; normalized27,807;3,540 exact cross-product groups; semantic near-duplicates NOT_MEASURED; chưa loại trùng |
| Bộ lọc P2-T04 QA | CẦN review | P1 QA bằng chứng tái sử dụng; không có observed FP ở sampled KEEP, không bằng chứng xác nhận zero contamination; acceptance/removal đang chờ |
| Làm sạch P2-T05 | CHƯA BẮT ĐẦU | HTML/URL flags là audit, chưa strip/normalize bộ dữ liệu, chưa validate English/spam |
| P2-T06 nhãn | CHƯA BẮT ĐẦU | Rule/config và aggregate proxies có; chưa persist/validate cuối cùng per-row nhãn |
| Ứng viên P2-T07 nhiễu | CHƯA BẮT ĐẦU | Mixed-rating trùng lặp flags không phải con người văn bản disagreement; chưa có ứng viên review mẫu |
| Mất cân bằng P2-T08 | ĐANG TIẾN HÀNH | Số lượng ứng viên103,817 negative/32,685 neutral/271,978 positive; tỷ lệ8.32; lý do cuối cùng của counts/mitigation đang chờ |
| P2-T09 sạch bộ dữ liệu | CHƯA BẮT ĐẦU | `data/processed/laptop_reviews.parquet` absent; cuối cùng làm sạch ledger/yield/class-product adequacy chưa có |

QA ID/text union8,406 là isolation risk; sản phẩm matches65,983 chỉ là scenario. Không áp exclusion, không dùng QA nhãn làm cảm xúc huấn luyện nhãn. spam, language validity, semantic gần trùng rate, rating-text disagreement NOT_MEASURED. cuối cùng bộ dữ liệu phải đáp ứng laptop-only clean-tiếng Anh và ghi thực tế size/coverage; không lấy preflight làm bằng chứng xác nhận hoàn thành, không tạo split/training khi chưa đủ input.

## Những milestone còn lại và phụ thuộc

phụ thuộc dưới đây diễn giải pipeline/exit criteria đã có trong PLAN, không thêm điều kiện nghiệm thu hoặc roadmap. Chi tiết task/checklist vẫn ở PLAN_AI/PLAN_HUMAN.

| ID giai đoạn/nhiệm vụ | Trạng thái | đầu vào cần có → deliverable / hoàn thành bằng chứng còn thiếu |
|---|---|---|
| P0-T01–T04 | DONE | Prior mới môi trường bằng chứng, configs/schema/registry kiểm thử; mới install không chạy lại |
| P3-T01–T08 | ĐANG TIẾN HÀNH, chỉ là số liệu ban đầu | P2 sạch dữ liệu → overview/text/metadata/quality/insight notebook/report;3 preliminary biểu đồ không đáp ứng nhận định criterion |
| P4-T01–T05 | CHƯA BẮT ĐẦU | P2 làm sạch các quan sát input/P3 → cố định các tập đã chia, báo cáo rò rỉ dữ liệu, đường ống chỉ trên tập huấn luyện classical/BERT |
| P5-E00–E03 | CHƯA BẮT ĐẦU | P4 cố định dữ liệu → majority/LR/SVM/DT các tệp kết quả và cùng bảng cố định-kiểm thử benchmark/cost |
| P6-T01–T06 | CHƯA BẮT ĐẦU | P4 + đường cơ sở P5 mạnh mẽ → So sánh BERT checkpoint/metrics/cost |
| P7 taxonomy/comparison | CHƯA BẮT ĐẦU | P5/P6 predictions → mô hình-specific phân tích lỗi; filter FN báo cáo không thay mô hình lỗi |
| P8-T01–T04 | CHƯA BẮT ĐẦU | Authorized P1 SemEval → BIO/subword alignment/ATE checkpoint/span thước đo; P1 parse tái sử dụng không chứng minh trained ATE |
| P9-T01–T04 | CHƯA BẮT ĐẦU | Trích xuất khía cạnh-ngữ cảnh dữ liệu + P8 được ủy quyền → Số liệu ASC checkpoint/conflict policy/end-to-end |
| P10 sampling/annotation/evaluation | CHƯA BẮT ĐẦU | Amazon laptop holdout/human nhãn độc lập và đánh giá các mô hình →300–500 gold/overall+ABSA/noise/shift |
| Các chế độ P11 single/batch | CHƯA BẮT ĐẦU | Đã lưu suy luận các mô hình → Tinh giản mà không cần đào tạo lại, đã thử nghiệm mẫu số input/aggregate |
| Nhiệm vụ sẵn sàng P12 | ĐANG TIẾN HÀNH, chỉ có nền tảng | Tích hợp P0 schema/routing + inference/app → tiền xử lý interfaces/real loading/extension sẵn sàng; vi vẫn bị vô hiệu hóa |
| P13-T01–T05 | CHƯA BẮT ĐẦU | Các mốc quan trọng trước đó → phân tích tổng hợp, báo cáo setup/data/inference/app evidence/final mới chạy |

Milestone active vẫn P1. điều kiện nghiệm thu tuần1 yêu cầu validated filter và usable Amazon/ SemEval; PLAN không có waiver hiện hành cho toàn bộ P2 sau khi điều kiện nghiệm thu chưa đạt. Vì yêu cầu mới chỉ cho làm milestone hiện tại và cấm tiếp tục sớm vì thuận tiện, lần này không triển khai cleaning/English/dedup/label-noise mới. Nếu P1 được đóng, tác vụ kế tiếp là P2-T02/T03 xử lý audit còn thiếu và P2-T04 đầu vào QA, rồi P2-T05 cleaning/P2-T06 labeling theo PLAN; P4 các tập đã chia giữ nguyên thứ tự sau P3.

## tập xác thực và thay đổi

Chỉnh `PLAN_HUMAN.md`, `PLAN_AI.md`, `README.md`, hiện tại header của `reports/p1_remaining_gates.md` và `docs/CODEX_HANDOFF.md`. Tạo báo cáo này và `scripts/audit_plan_progress.py`; bản chụp trạng thái machine bằng chứng tại `reports/tables/plan_progress_audit_20261009.json`. Script chỉ đối chiếu14 giai đoạn IDs, protected/source/annotation hàm băm, saved QA consistency, đại diện denominator và tệp kết quả presence; không chạy lại survey/QA. Chạy lại với đầu ra mới để tránh overwrite.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m scripts.audit_plan_progress --output reports/tables/plan_progress_audit_20261009.json
```

đã xác minh: toàn bộ suite143 passed in3.88s trong lần này; hai PLAN giữ nguyên đủ14 milestones, không có nested AGENTS khác, training/app/artifact directories chỉ có placeholders. mới môi trường install và các experiments trước là REPORTED, không chạy lại. đã xác minh:41 được bảo vệ SHA256 checks PASS; saved candidate/QA nguồn bindings, đại diện denominator and giai đoạn sequence PASS. No được bảo vệ đầu vào changed. Giới hạn: laptop-only findings, nhãn đại diện suy từ số sao-nhiễu nhãn, SemEval-to-Amazon platform/style shift trong laptop review và small thủ công annotated bộ dữ liệu gold (sentiment/ABSA gold hiện chưa có). Không có mô hình thước đo hoặc production-readiness claims; acceptance/license chưa được phê duyệt trong audit.
