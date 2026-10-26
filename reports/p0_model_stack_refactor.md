# P0 — môi trường benchmark mới

Trạng thái: PASS cho import, dependency resolver, CUDA và explicit model version. Không sửa dữ liệu.

Python 3.13.12, CUDA 12.8, RTX 4050 Laptop GPU (6438780928 byte). Phiên bản: torch 2.8.0+cu128, transformers 5.0.0, xgboost 3.4.1, tabm 0.0.3, tabpfn 9.2.0, sentence-transformers 6.2.0, scikit-learn 1.7.2. Các phụ thuộc mới và transitive đã được ghim trong requirements hiện có; không thay pin lịch sử.

Đã chạy resolver dry-run trước install, sau đó install thật thành công. `python -m scripts.check_model_stack`: PASS; import đủ bảy package; `pip check`: No broken requirements found. Bằng chứng máy đọc được: `p0_dependency_resolution.json`, `p0_installed_dependencies.json`, `p0_model_stack_environment.json`.

Factory chính thức resolve riêng:
- E03: ModelVersion.V3 → tabpfn-v3-classifier-v3_default.ckpt.
- E04: ModelVersion.V3_5 → tabpfn-v3.5-20260909.safetensors.

`src/sentiment/tabpfn_versions.py` từ chối tên mơ hồ và override model_path; kiểm tra checkpoint khác nhau. P0 chỉ tạo object, không tải hoặc chạy checkpoint. Smoke fit/predict và VRAM thuộc P5, chưa được đo. Không coi import PASS là benchmark PASS.

Nguồn API/điều kiện truy cập: [TabPFN chính thức](https://github.com/PriorLabs/TabPFN), [TabM chính thức](https://github.com/yandex-research/tabm). Trọng số TabPFN có giấy phép riêng; không tự thay phiên bản, chấp nhận điều khoản tài khoản hoặc chuyển sang API trả phí.
