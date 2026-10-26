# Phân tích cảm xúc & khía cạnh của khách hàng cho laptop review

Dự án dữ liệu Science cá nhân 6 tuần, chỉ dành cho review laptop/notebook. Trọng tâm: chất lượng dữ liệu/EDA 50%, xây dựng mô hình và phân tích lỗi 40%, Streamlit 10%.

## Hiện trạng

Mục tiêu hiện hành **30K sạch tiếng Anh laptop review**. toàn bộ Electronics siêu dữ liệu đã tải **1,31 GB**, checksum/manifest verify; laptop-only preflight đạt EOF với **1.610.012 records / 28.172 ứng viên sản phẩm**, không record errors. 84 kiểm thử chạy lại đạt. review **6,47 GB đã tải và verify SHA256/manifest/size** theo phê duyệt download-only; streaming join/Laptop-only toàn bộ survey chưa được phê duyệt hoặc chạy. con người filter QA vẫn unvalidated, sạch yield chưa đo. Xem `reports/p1_metadata_full_preflight.md` và `reports/p1_reviews_full_acquisition.md` cho bằng chứng và bước tiếp theo.

Chặng P0 đã hoàn thành. P1 đã refactor siêu dữ liệu-first: compact sản phẩm index, streaming review join, bounded QA/sampling và feasibility thước đo với tài nguyên guards. Khảo sát nhỏ Electronics + Cell Phones có 17 laptop / 3 Smartphone / 9 Tablet valid ứng viên review; Smartphone/Tablet chỉ là feasibility, phạm vi dự án vẫn laptop. SemEval laptop hiện chỉ có trial. Không dùng các prefixes như bộ dữ liệu cuối. P1 chưa hoàn thành: cần mở rộng độ phủ dữ liệu, gốc SemEval huấn luyện/kiểm thử và con người filter QA. Chưa có mô hình đã tập huấn luyện, quy trình dự đoán hoặc ứng dụng Streamlit. `en -> BERT` là cấu hình dự kiến; `vi -> PhoBERT` được dành chỗ và bị từ chối rõ ràng khi sử dụng.

## Cài đặt và kiểm tra

Python 3.11+; P0 được kiểm tra trên Python 3.13.12 ở Windows. Chạy tại thư mục gốc trong PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

phụ thuộc hiện chỉ gồm PyYAML và pytest, được khóa phiên bản. Pandas/pyarrow, scikit-learn, Transformers/PyTorch và Streamlit sẽ được thêm và kiểm tra tương thích ở chặng sử dụng chúng; chưa kiểm chứng GPU hoặc huấn luyện.

## Cấu trúc và cấu hình

- `configs/data.yaml`: phạm vi, hạt giống ngẫu nhiên, nguồn dữ liệu, đường dẫn, nhãn rating và tỷ lệ phân chia.
- `configs/model.yaml`: nhãn IDs cố định, danh sách mô hình, thước đo và chi phí cần đo.
- `configs/language.yaml`: tiếng Anh hiện tại và điểm mở rộng Vietnamese/PhoBERT.
- `configs/acquisition.yaml`: URL nguồn, ngân sách thu thập, lược đồ aliases, laptop filter và QA criteria.
- `configs/feasibility.yaml`: hai nguồn khảo sát, group rules và scan/RAM/output giới hạn tài nguyên; không đổi phạm vi huấn luyện.
- `src/config.py`: đọc cấu hình và giải quyết đường dẫn theo root dự án.
- `src/data/`, `src/preprocessing/`: xử lý dữ liệu và tiền xử lý theo ngôn ngữ.
- `src/sentiment/`, `src/absa/`, `src/evaluation/`: xây dựng mô hình, ABSA và đánh giá ở các chặng sau.
- `src/models/registry.py`: routing ngôn ngữ; `src/inference/schema.py`: đầu ra chung cho single/batch.
- `data/raw/`, `data/interim/`, `data/processed/`, `data/manual/`: dữ liệu không đưa vào Git.
- `artifacts/`: checkpoint/model không đưa vào Git; `reports/`: báo cáo và bằng chứng.
- `notebooks/`, `scripts/`, `app/`, `tests/`: EDA, CLI, UI và kiểm tra.

Không tạo notebook/model/pipeline rỗng để thay cho phần triển khai ở chặng sau.

## Phương pháp đã chốt

Amazon review 2023 phải đi kèm siêu dữ liệu và xác minh join key để lọc laptop, loại phụ kiện; filter hiện **unvalidated**. Mục tiêu hiện hành khoảng **30.000 sạch tiếng Anh laptop review**, thay 50.000 theo yêu cầu ngày 2026-10-08. Đây là mục tiêu mong muốn; tập ứng viên 15.000–25.000 chất lượng cao vẫn cần đánh giá độ bao phủ lớp và đa dạng sản phẩm, không hạ chất lượng để đạt quota. Raw bất biến. Rating 1–2/3/4–5 lần lượt là `negative`/`neutral`/`positive`, với nguồn gốc **nhãn đại diện suy từ số sao**.

phân chia mục tiêu 70/15/15 với hạt giống ngẫu nhiên 42, kiểm tra duplicate/product rò rỉ dữ liệu và cân nhắc group phân chia. khớp mô hình TF-IDF chỉ trên tập huấn luyện, chọn mô hình theo tập xác thực macro F1; kiểm thử cố định và bộ gold do con người gán nhãn không được dùng để tuning. đánh giá so sánh majority, TF-IDF + LR/Linear SVM/Decision Tree và BERT kèm compute cost.

ABSA dùng SemEval-2014 laptop: giữ ID, phân chia và character vị trí cụm từ; đánh giá extraction theo entity/span F1; cảm xúc phải điều kiện hóa theo từng khía cạnh. Chính sách `conflict` phải được quyết định và ghi rõ khi xử lý dữ liệu. gold Amazon 300–500 review phải do người gán nhãn, độc lập với train/model selection. 30K phục vụ EDA/overall cảm xúc; ABSA cần khía cạnh-level nhãn riêng từ SemEval hoặc con người Amazon gán nhãn, không suy từ rating và không phải gán nhãn cả 30K.

đầu ra chung gồm `domain`, `language`, `sentiment`, `confidence`, `aspects`. Không có khía cạnh thì trả `[]`; độ tin cậy mặc định `null`, chỉ được cung cấp khi có cơ sở xác suất phù hợp. lược đồ tạo object dữ liệu, không sinh dự đoán.

## Giới hạn và bước tiếp theo

Chỉ kết luận trong phạm vi laptop; nhãn rating có nhiễu; SemEval và Amazon có platform/style shift trong cùng phạm vi; gold do người gán nhãn có quy mô nhỏ. Chưa có bằng chứng thực nghiệm hoặc tuyên bố production readiness. Tiếp theo là hoàn tất blockers P1 trước P2. Xem `reports/p1_data_acquisition.md` để chạy acquisition/audit/QA, `data_dictionary.md` cho lược đồ đã quan sát và `reports/p1_data_feasibility.md` cho kết quả nhỏ, cleaning/sampling design và phương án tải/quét lớn đang chờ phê duyệt. `reports/p1_pipeline_changes.md` ghi logic cũ/mới và kiểm chứng. `reports/tables/p1_feasibility_small.csv` chứa bảng thước đo; `p1_audit.json` là cũ prefix diagnostic. Xem `PLAN_AI.md` và `PLAN_HUMAN.md` cho checklist.
