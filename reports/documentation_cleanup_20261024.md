# Cập nhật và dọn tài liệu — 2026-10-24

Trạng thái benchmark local giữ **LIMITED**, cloud full21000 **PENDING**. Đây là tác vụ tài liệu/báo cáo, không training, upload, thuê GPU hoặc đánh giá test mới.

## Nội dung đã thống nhất

README, AGENTS, PLAN_AI/PLAN_HUMAN và hợp đồng semantic dùng cùng bộ model/representation hiện hành. Hai PLAN đã bỏ phần hướng dẫn TF-IDF/BERT body-only khỏi luồng active, giữ bản đầy đủ trước sửa với hash trong `docs/archive/20261024_before_cleanup/`. P8–P12 được đối chiếu giữ nguyên; P13 chỉ thay model list cũ. Không xóa yêu cầu ABSA/gold/app hoặc nới tiêu chí khoa học.

Thêm `docs/PROJECT_INDEX.md` để phân biệt active/history và `docs/TABPFN_CLOUD_PLAN.md` cho follow-up21K. Kế hoạch cloud chưa chọn nền tảng/ngân sách, chưa có runner cloud hoàn chỉnh hoặc kết quả cloud. Các đề xuất GPU/RAM không được ghi thành phép đo đã PASS. Test reuse, secrets, namespace riêng và giới hạn local được công bố.

P5, E03/E04, P6, P7, resource và completion A–M được sinh lại từ cùng artifacts/saved predictions; score không đổi. Metadata P7 ghi scope local và cloud PENDING. Script báo cáo cũ chỉ alias tới báo cáo cuối; không phục hồi template license BLOCKED hoặc tạo lại CSV partial trùng. Lỗi trong resource report chuyển xuống phần riêng để bảng Markdown liên tục.

## Dọn thực tế

- Xóa `reports/model_stack_partial_results.csv` sau khi so byte bằng `reports/p7_unified_results.csv`. CSV P7 là nguồn bảng cuối; P5 CSV vẫn cần vì chỉ có5model.
- Dọn cache Python/pytest tái tạo được trong workspace, loại trừ `.venv`, data, artifacts và thư mục lịch sử. Số lượng/path/byte thực tế nằm trong JSON cùng tên.
- Giữ raw/processed/split/embeddings, model/checkpoint, nhãn manual, prediction/metrics, smoke/resource/error/attempt và53legacy outputs. Giữ Word plan lịch sử tại đường dẫn cũ để không làm mất provenance.
- Các contracts2026-10-15 và báo cáo Việt hóa2026-10-19 chỉ thêm nhãn LEGACY/chỉ dẫn hiện hành; không sửa kết quả khoa học lịch sử.

## Xác minh

`python -m scripts.verify_benchmark`:249tests PASS (229+12+8),0FAIL; sáu validators/pip check/compileall PASS;53legacy output hashes không đổi. Không re-predict test để verify.

Kiểm tra đường dẫn Markdown, snapshot hashes,14phase headings mỗi PLAN và nội dung P8–P12 PASS; chi tiết cuối trong `reports/documentation_cleanup_20261024.json`. Bản kê archive giữ nguyên bytes trước cleanup. Caches có thể được Python tạo lại khi chạy lệnh mới, không phải artifact khoa học cần bảo toàn.

Giới hạn nghiên cứu giữ nguyên: laptop-only, noisy star proxy, SemEval–Amazon style shift thuộc ABSA, gold người dự kiến nhỏ chưa có. Bước tiếp là chọn compute/ngân sách và chuẩn bị cloud theo kế hoạch, không tự khởi tạo job trả phí.
