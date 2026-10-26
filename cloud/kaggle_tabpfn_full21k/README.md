# Gói TabPFN full21K dành cho Kaggle

Chỉ chuẩn bị C-E03 (`ModelVersion.V3`) và C-E04 (`ModelVersion.V3_5`), `tabpfn==9.2.0`, seed42. Chưa chạy model/cloud. Bundle độc lập với repository, không chứa review text hoặc model weights. Dùng dataset **private** theo quyền nguồn Amazon hiện tại; chủ tài khoản tự hoàn tất điều kiện truy cập/giấy phép TabPFN. Không paste token vào notebook.

## Thao tác trên Kaggle

1. Tạo **private Kaggle Dataset** và upload toàn bộ nội dung thư mục bundle (giữ cấu trúc thư mục); có thể dùng ZIP bundle đã chuẩn bị.
2. Tạo Notebook bằng cách import `kaggle_notebook.ipynb`.
3. Attach Dataset vừa tạo. Chỉ attach một bundle; nếu nhiều bundle, đặt `DATA_ROOT` ở cell 3.
4. Bật GPU, chọn T4 x2 nếu tài khoản cung cấp; code dùng một GPU, hai T4 không cộng VRAM thành một GPU. Bật Internet để cài packages/tải checkpoint.
5. Thêm Kaggle Secret tên `TABPFN_TOKEN`, cấp quyền truy cập notebook. Không ghi giá trị vào code hoặc output.
6. Chạy **Run All**. Verify thất bại sẽ dừng; probe dùng train-only, mỗi mức 500/1000/2500/5000/10000/21000 ở subprocess mới. Mỗi mức timeout 3600 giây. Probe thất bại sẽ ghi `FULL21K_FAILED`, bỏ final của phiên bản đó và tiếp tục phiên bản kia.
7. Tải `/kaggle/working/tabpfn_cloud_results_*.zip`; giữ notebook outputs riêng nếu phiên bị kill do hết RAM/quota. Không tự coi subsample là kết quả full21K.

## Dữ liệu và integrity

Ba mảng embeddings `.npy` sao chép byte từ `data/processed/features/semantic_20261024/`; labels `.npy` giữ nguyên; IDs `.npy` Unicode không pickle được xuất theo đúng thứ tự mapping gốc. Train/validation/test: 21000/4500/4500, 384 chiều float32. Encoder `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, mask-mean/L2/max256. Nhãn `negative=0, neutral=1, positive=2`.

`metadata/bundle_manifest.json` lưu hash split nguồn, embeddings, mapping và toàn bộ payload. `config/expected_manifest.json` neo SHA256 manifest; giữ bản local để đối chiếu khi nhận kết quả. Hash không phải chữ ký chống tác nhân thay cả anchor lẫn payload. Export kiểm ID/row_index/labels trực tiếp với split gốc; verify trên Kaggle kiểm byte đã neo, shape, finite, zero rows, ba lớp, ID uniqueness và không overlap. Không thể suy ra semantic correspondence chỉ bằng matrix không có provenance; chứng cứ alignment là export so với mapping gốc và hash cố định.

Chạy độc lập: `python scripts/verify_bundle.py --data-root .` từ thư mục bundle. Runner: `python scripts/run_tabpfn_cloud.py --version v3 --data-root . --output-dir /kaggle/working/tabpfn_v3_full21k` (V3.5 dùng `v3_5`, output `tabpfn_v35_full21k`). Không chạy các lệnh training này trên máy local trong tác vụ chuẩn bị.

## Cấu hình và đánh giá

`config/cloud_experiment.yaml` cố định một candidate trước cloud: n_estimators1, fit_with_cache, memory_saving_mode true, cache CPU, autocast, batch16. Đây là cấu hình memory-safe chính thức đã dùng trong resource work local, không tự chọn theo score test. Không thay representation/giảm chiều hoặc fallback subsample. V3 n_estimators1 có giới hạn coverage nội bộ tối đa200/384 chiều; đầu vào vẫn384. Muốn đổi cấu hình phải làm trước test, probe lại train-only, dùng namespace mới và công bố thay đổi. Không retry vào output đã có.

Thứ tự: verify → fit full train → validation → selection_lock → test. Test này **reused test** đã được xem ở local/LEGACY, không phải holdout hoàn toàn mới. Mã metrics được sao nguyên từ `src/evaluation/classification.py`; balanced accuracy là trung bình recall ba lớp như runner local. Primary macro F1; accuracy, weighted F1, balanced accuracy, per-class precision/recall/F1, neutral F1 và confusion matrix đầy đủ. Predictions chứa review_id/y_true/y_pred với ID nhãn0/1/2; không lưu xác suất chưa calibration. RSS lấy mẫu20ms; GPU peak allocated/reserved từ PyTorch, không phải toàn GPU hay phép đo chi phí tiền. Không lưu weights. Môi trường Linux và CUDA được ghi thực tế, PyTorch dùng bản Kaggle hiện có; requirements không ép downgrade CUDA stack.

## Nhận lại kết quả local

1. Đặt ZIP dưới `artifacts/cloud_runs/`, giải nén vào thư mục mới; không overwrite artifacts subsample.
2. Đối chiếu `archive_hashes.json`, từng `hashes.json`, manifest SHA256 với bản bundle local và ba source split hashes.
3. Kiểm `run_metadata.json`: PASS, train_count21000/FULL, requested/resolved V3 hoặc V3_5, hai checkpoint khác nhau, tabpfn9.2.0, seed/config/selection lock. `FULL21K_FAILED` không được nhập như success.
4. Kiểm từng prediction có đủ4500 ID đúng thứ tự và y_true khớp bundle local; kiểm IDs không thiếu/thừa/trùng. Tính lại metrics bằng `src.evaluation.classification.classification_metrics` trên y_true/y_pred, cộng balanced_accuracy bằng mean per-class recall, so JSON và confusion CSV.
5. Kiểm lock tồn tại trước test, resource/environment/errors và tính đầy đủ artifact. Chỉ sau khi mọi kiểm tra PASS mới thực hiện tác vụ riêng cập nhật P7. Bundle không tự nhập hoặc sửa P7.

Giới hạn: chỉ laptop tiếng Anh; nhãn đại diện suy từ số sao có nhiễu; SemEval-to-Amazon platform/style shift trong laptop thuộc ABSA; bộ gold thủ công nhỏ dự kiến và chưa có. Không khẳng định production hoặc hỗ trợ tiếng Việt. Không đảm bảo GPU/RAM/quota Kaggle đủ full21K; khả năng chạy thực tế vẫn PENDING.
