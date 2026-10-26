# AGENTS.md — Thỏa thuận làm việc Codex

## 1. Mục tiêu và nguồn thông tin có thẩm quyền

Bạn là tác nhân lập trình cho dự án **Phân tích cảm xúc và khía cạnh trong đánh giá laptop** (`customer-sentiment-laptop-reviews`). Đây là dự án Khoa học dữ liệu **6 tuần, một người, lấy dữ liệu làm trọng tâm**. Ưu tiên xử lý dữ liệu có thể tái lập, thí nghiệm nghiêm ngặt và kết luận có căn cứ hơn việc bổ sung tính năng.

**Trước khi thay đổi quy mô pha**, hãy đọc phần có liên quan của `PLAN_AI.md`, kiểm tra các tệp mà tác vụ sẽ chạm vào và tuân theo các phần phụ thuộc của nó cũng như tiêu chí `DONE_WHEN`. Sử dụng `PLAN_HUMAN.md` cho ngữ cảnh giải thích khi cần thiết. Đừng đọc lại mọi tài liệu dự án để có một chỉnh sửa nhỏ, cục bộ.

Thứ tự ưu tiên khi có mâu thuẫn:
1. Yêu cầu rõ ràng hiện tại của người dùng.
2. `AGENTS.md` này và các hướng dẫn lồng nhau có thể áp dụng.
3. `PLAN_AI.md` cho phạm vi, yêu cầu về pha, tiêu chí chấp nhận và danh sách kiểm tra.
4. `PLAN_HUMAN.md`, sau đó là `README.md`, sau đó là chi tiết triển khai hiện có.

Nếu mâu thuẫn có thể thay đổi phạm vi, tính toàn vẹn dữ liệu hoặc tính hợp lệ của đánh giá, phải giải thích thay vì tự chọn trong im lặng. Không sửa hợp đồng chỉ để làm nhiệm vụ dễ hơn.

## 2. Ràng buộc dự án bất biến

- **phạm vi:** review chỉ của laptops/notebooks. Không trộn lẫn điện thoại, máy tính bảng, tai nghe, túi laptop, bộ sạc, đế cắm, bao đựng, chân đế hoặc các bộ phận thay thế.
- Không có khảo sát, mua lại Smartphone/Tablet, xây dựng mô hình hoặc dự phòng-phạm vi quy trình. Điện tử vẫn là loại nguồn; laptop là dự án phạm vi. Các sản phẩm thực sự laptop 2-in-1/convertible vẫn ở dạng phạm vi; chỉ từ ngữ trên máy tính bảng không phải là lý do để loại trừ chúng.
- **Ngôn ngữ:** tiếng Anh hiện nay; cấu trúc điểm mở rộng cho tiếng Việt và PhoBERT sau này. Không khẳng định tiếng Việt các mô hình hiện đang hoạt động cho đến khi được triển khai và thử nghiệm.
- **Tổng thể cảm xúc nhãn:** chính xác là `negative`, `neutral`, `positive` (ánh xạ nhất quán trên các tập dữ liệu, huấn luyện, số liệu, suy luận và giao diện người dùng).
- **các mô hình bắt buộc hiện hành (yêu cầu 2026-10-24):** majority chỉ sanity; XGBoost, TabM, TabPFN-3 (`ModelVersion.V3`) và TabPFN-3.5 (`ModelVersion.V3_5`) trên cùng frozen semantic embeddings; BERT fine-tune end-to-end trên canonical title + body. TF-IDF/LR/SVM/Decision Tree và BERT body-only giữ LEGACY, không rerun/xóa artifact chỉ vì refactor. Full21000 TabPFN cloud là follow-up PENDING tại `docs/TABPFN_CLOUD_PLAN.md`; local subsample phải ghi LIMITED.
- **ABSA bắt buộc:** trích xuất cụm từ khía cạnh tường minh bằng BERT và phân loại cảm xúc có điều kiện theo khía cạnh; tích hợp thành suy luận từ đầu đến cuối.
- **Chỉ số lựa chọn chính:** **macro F1**. Đồng thời báo cáo tỷ lệ dự đoán đúng (accuracy), F1 có trọng số precision/recall/F1, mỗi lớp và ma trận nhầm lẫn. Để so sánh mô hình, hãy báo cáo thời gian huấn luyện, độ trễ suy luận, kích thước tệp kết quả và tài nguyên sử dụng khi có thể đo lường được.
- **Điểm nhấn mạnh của dữ liệu:** ~50% dữ liệu quality/EDA/insights, ~40% xây dựng mô hình và phân tích lỗi, ứng dụng Streamlit ~10%. Giữ ứng dụng mỏng.
- **Tỷ lệ:** nhắm tới 30,000 sạch tiếng Anh Amazon laptop review **nếu tồn tại dữ liệu hợp lệ**; báo cáo kích thước thực tế nếu không. Nhóm 15,000–25,000 chất lượng cao có thể được đánh giá bằng cách sử dụng phạm vi phân loại và tính đa dạng của sản phẩm; không bao giờ bao gồm các sản phẩm không liên quan hoặc chất lượng thấp hơn để đạt được mục tiêu. Được cập nhật theo yêu cầu rõ ràng của người dùng trên 2026-10-08.
- **Tránh hiện tượng leo phạm vi:** không thu thập thông tin theo thời gian thực trong MVP; không có Spark, Kafka, Airflow, microservice, kiến ​​trúc thần kinh bổ sung React/FastAPI, hoặc cơ sở hạ tầng sản xuất không cần thiết.

## 3. Nguồn dữ liệu bắt buộc và tính toàn vẹn khoa học

| Nguồn dữ liệu | Sử dụng chính | Bảo vệ cốt lõi |
|---|---|---|
| Amazon review 2023 **cộng với sản phẩm phù hợp siêu dữ liệu** | Phân tích tổng thể cảm xúc, quality/EDA, nhãn-nhiễu | Xác định các sản phẩm laptop bằng cách sử dụng liên kết review-to-siêu dữ liệu đã được xác minh |
| SemEval-2014 **laptop** | Trích xuất Train/evaluate khía cạnh và khía cạnh cảm xúc | Lưu giữ ID câu, khía cạnh vị trí cụm từ, thông tin phân chia gốc và chi tiết nhãn |
| 300–500 **do con người gán nhãn** Amazon laptop review | Đánh giá gold cho cảm xúc và ABSA tổng thể | Giữ độc lập với lựa chọn training/model; không bao giờ mạo danh con người gán nhãn |

### Lọc Amazon và nhãn

- Xác minh lược đồ nguồn thực tế và các khóa kết nối (ví dụ: số nhận dạng sản phẩm) **trước** các giả định mã hóa về tên trường. Không chỉ sử dụng văn bản hoặc xếp hạng sao review để xác định xem sản phẩm có phải là laptop hay không.
- Làm cho việc lọc các quy tắc inclusion/exclusion mang tính xác định, có thể định cấu hình và ghi lại. Thực hiện và báo cáo mẫu được kiểm tra thủ công về tình trạng nhiễm bẩn phụ kiện; nếu việc kiểm tra đó không xảy ra, bộ lọc nhãn **không được xác thực**.
- Giữ `data/raw/` không thay đổi. Lưu trữ các phép biến đổi dưới dạng tệp mới trong `data/interim/` hoặc `data/processed/`. Theo dõi số lượng bản ghi source/version,, bộ lọc và hạt giống ngẫu nhiên.
- Nếu nhãn phải đến từ xếp hạng: `1–2 -> negative`, `3 -> neutral`, `4–5 -> positive`. Lưu trữ xuất xứ nhãn dưới dạng **nhãn đại diện suy từ số sao**; không đánh đồng xếp hạng với con người nhãn chuẩn.
- Điều tra các bản sao dữ liệu, exact/near bị thiếu, short/empty review, các bản ghi giống thư rác, HTML các tệp kết quả, nhãn không cân bằng và các bất đồng về rating/text. Việc làm sạch phải bảo toàn ngôn ngữ phủ định và ngôn ngữ liên quan đến cảm xúc.
- Không bao giờ giả mạo review, gán nhãn, chạy thử nghiệm, kiểm tra thủ công, thống kê chất lượng dữ liệu hoặc kết quả đánh giá so sánh. Thiếu đầu vào dữ liệu phải được báo cáo là trở ngại, không được thay thế bằng bằng chứng tổng hợp.
- Trước khi tìm nạp tập dữ liệu của bên thứ ba, hãy kiểm tra các điều kiện của licensing/access, sử dụng nguồn dữ liệu được ủy quyền và tránh đưa dữ liệu thô có bản quyền hoặc nhạy cảm vào Git. Không đặt token hoặc thông tin đăng nhập vào kho lưu trữ.

### Tách, rò rỉ dữ liệu và đánh giá

- Lưu các tập **train/validation/test 70/15/15** của Amazon với hạt giống ngẫu nhiên cố định khi khả thi; giải thích sai lệch do ràng buộc nhóm và độ bao phủ lớp.
- Kiểm tra rò rỉ dữ liệu trên các tập đã chia: identical/near-identical review, review ID, ID sản phẩm và `parent_asin` (nếu có). Xem xét việc phân chia nhận thức nhóm để đạt được hiệu suất kiểm thử trên các sản phẩm laptop chưa được nhìn thấy; ghi lại xem phân chia là không trùng review giữa các tập hay không trùng sản phẩm giữa các tập. phân chia nhận biết nhóm có thể thay thế phân tầng nghiêm ngặt khi cần để tránh rò rỉ dữ liệu.
- Bộ tạo vector văn bản khớp mô hình, bộ lấy mẫu lại, số liệu thống kê tập huấn luyện phụ thuộc tách token và lựa chọn mô hình chỉ sử dụng **huấn luyện dữ liệu**; điều chỉnh trên tập xác thực. Không sử dụng test/gold nhãn để dò hoặc chọn mô hình. Đánh giá các ứng cử viên được chọn cuối cùng trên bộ cố định kiểm thử chưa được xử lý và so sánh trong các điều kiện tương đương.
- Giữ riêng mọi phân vùng SemEval train/test ban đầu và đánh giá bộ Amazon bộ gold do con người gán nhãn dưới dạng dataset/platform/style-shift kiểm thử riêng biệt trong **cùng laptop phạm vi**.
- Benchmark hiện hành tách frozen encoder cho classifier và tokenizer BERT canonical; chuẩn hóa tối thiểu, giữ phủ định/dấu câu, không stemming/stopword removal. Không TF-IDF/BoW/PCA/SVD hoặc metadata features trong active pipeline. Quy trình TF-IDF cũ chỉ phục vụ tái lập LEGACY.
- So sánh với các đường cơ sở đơn giản mạnh mẽ trước khi khẳng định Transformer tốt hơn. Giải thích cả hiệu suất gain/loss và chi phí tính toán.
- Đối với sự mất cân bằng lớp, chỉ chọn trọng số hoặc biện pháp giảm thiểu khác sau khi ghi lại sự mất cân bằng và so sánh trên tập xác thực.

### Quy tắc cụ thể của ABSA

- Xử lý **khía cạnh thuật ngữ vị trí cụm từ** như nhãn chuẩn để chiết xuất. Giữ nguyên độ lệch ký tự và xác minh căn chỉnh khi chuyển đổi sang thẻ BIO và từ phụ token. Sử dụng entity/span-level độ chính xác dự đoán (precision), độ bao phủ (recall) và F1 để trích xuất; Chỉ riêng token tỷ lệ dự đoán đúng (accuracy) là không đủ.
- Các ví dụ khía cạnh cảm xúc phải dựa trên cả ngữ cảnh review/sentence và thuật ngữ khía cạnh cụ thể (và vị trí của nó khi có liên quan). Một review có thể chứa nhiều khía cạnh với các cực khác nhau.
- Chỉ bình thường hóa SemEval cảm xúc nhãn bằng chính sách được ghi lại. Xử lý rõ ràng `conflict`/nhãn không được hỗ trợ; không bao giờ âm thầm chuyển đổi chúng thành neutral.
- Phân biệt **các thuật ngữ được trích xuất rõ ràng** với các nhóm khía cạnh chuẩn dành cho doanh nghiệp tùy chọn sau này (pin, màn hình, bàn phím, hiệu suất, giá cả, v.v.). Không mã hóa cứng các phát hiện khía cạnh được coi là kết luận EDA.
- gold nhãn gán phải được thực hiện hoặc xác minh bởi con người. Codex có thể tạo mẫu gán nhãn, trình xác thực và tập lệnh lấy mẫu nhưng không được tự động tạo “con người” gold nhãn.
- Nếu các mô hình không cung cấp ước tính xác suất justified/calibrated, hãy trả về `null`/bỏ qua độ tin cậy thay vì tạo ra điểm số.

## 4. Bản đồ kho lưu trữ và ranh giới trách nhiệm

Sử dụng cấu trúc kho lưu trữ được mô tả trong `PLAN_AI.md` làm tài liệu tham khảo, thích ứng với các đường dẫn **hiện có** thay vì sao chép các mô-đun. Ranh giới dự kiến:

```text
configs/          # Cài đặt data/model/language/seed
src/data/         # đang tải, lọc laptop, tập xác thực, làm sạch, nhãn, các tập đã chia
src/preprocessing/# per-language text processing
src/sentiment/    # các mô hình cổ điển và BERT tổng thể cảm xúc
src/absa/         # Trích xuất khía cạnh và khía cạnh cảm xúc
src/evaluation/   # số liệu, điểm chuẩn, phân tích lỗi
src/models/       # Đăng ký mô hình và tải mô hình
src/inference/    # dự đoán single/batch thống nhất
notebooks/        # phân tích thăm dò; logic có thể tái sử dụng thuộc về src/
app/              # Chỉ trình bày hợp lý
reports/          # số liệu, bảng biểu, văn bản phân tích
scripts/          # điểm vào CLI có thể tái tạo tùy chọn
tests/            # kiểm tra đơn vị, tích hợp và dựa trên lịch thi đấu nhanh
data/             # raw/interim/processed/manual (không phiên bản bộ dữ liệu lớn)
```

- Giữ các phép biến đổi, bộ dữ liệu, đánh giá và dự đoán có thể tái sử dụng trong các mô-đun Python có thể kiểm tra, **không chỉ các ô notebook**.
- Giữ tính xác định thực thi notebook từ kernel mới; sử dụng các đường dẫn tương đối di động và cấu hình dự án, không phải đường dẫn Windows tuyệt đối dành riêng cho người dùng.
- Không di chuyển huấn luyện sang Streamlit hoặc ghép nối trực tiếp các tiện ích UI với Transformer điểm lưu mô hình. Tải mô hình thuộc lớp registry/inference, tốt nhất nên được lưu vào bộ nhớ đệm ở cấp ứng dụng.
- Tách mô hình objects/checkpoints thực tế khỏi cấu hình mô hình và các bản tóm tắt đánh giá so sánh nhỏ.
- Ưu tiên một số lượng nhỏ các mô-đun tập trung và tránh sự trừu tượng vì lợi ích riêng của nó.

### Giao diện suy luận ổn định

Thiết kế lớp suy luận để các quy trình công việc đơn lẻ và lô chia sẻ một hợp đồng:

```json
{
  "domain": "laptop",
  "language": "en",
  "sentiment": "negative",
  "confidence": null,
  "aspects": [
    {"aspect": "battery life", "sentiment": "negative", "confidence": null}
  ]
}
```

Đầu ra phải dùng đúng ba nhãn hợp lệ. Không có khía cạnh thì trả danh sách rỗng, không tự tạo khía cạnh. `confidence` có thể là null. Xử lý rõ ngôn ngữ chưa hỗ trợ. Giữ định tuyến `en` và `vi` về sau có thể cấu hình mà không đổi hợp đồng. Không khẳng định giá trị ví dụ là dự đoán thực tế.

## 5. Quy ước về mã hóa và công cụ

- mục tiêu **Python 3.11+** trừ khi môi trường hiện tại được cố tình ghim vào một phiên bản tương thích khác. Ưu tiên `pathlib`, gợi ý kiểu về các hàm công khai, chuỗi tài liệu ngắn gọn và tập xác thực rõ ràng ở ranh giới dữ liệu.
- Sử dụng quản lý phụ thuộc hiện có (`requirements.txt` hoặc `pyproject.toml`); không giới thiệu một công cụ cạnh tranh hoặc bỏ ghim các phần phụ thuộc trùng lặp một cách không cần thiết.
- Dùng pandas/pyarrow cho dữ liệu bảng, scikit-learn cho quy trình/thước đo học máy cổ điển, Hugging Face Transformers + PyTorch cho BERT và Streamlit cho giao diện khi cần. Không cài thư viện không dùng.
- Duy trì các biểu hiện ngẫu nhiên các hạt giống ngẫu nhiên, bộ dữ liệu provenance/versions, phân chia, cấu hình mô hình, bản đồ nhãn, số liệu và vị trí tệp kết quả để có thể sao chép các thử nghiệm.
- Quy trình dữ liệu phải lặp lại an toàn: chạy lại với cùng đầu vào và cấu hình không được âm thầm thay đổi kết quả.
- Ưu tiên tải chunked/lazy hoặc chọn cột khi tệp nguồn lớn hơn RAM; không tải toàn bộ kho lưu trữ Amazon một cách không cần thiết.
- Không bao giờ mã hóa mật khẩu, khóa API, truy cập token, đường dẫn máy trạm hoặc bộ dữ liệu mẫu lớn. Sử dụng `.env`/biến môi trường cho các bí mật và bỏ qua chúng trong Git.
- Tôn trọng các quy ước đặt tên hiện có. Sử dụng `snake_case` cho mã định danh Python và `UPPER_CASE` cho hằng số. Các hàm nhỏ, có mục đích được ưu tiên hơn mã notebook trùng lặp.
- Trên Windows/VS Code, ưu tiên các lệnh di động như `python -m pip ...`, `python -m pytest ...`, `python -m streamlit ...`; đừng giả sử một shell Unix.

## 6. Cách thực hiện tác vụ Codex

1. **Hiểu phạm vi.** Xác định tác vụ được yêu cầu của người dùng, các tệp hiện tại, ID tác vụ và pha `P0`–`P13` có liên quan trong `PLAN_AI.md` và các phần phụ thuộc. Không thực hiện các giai đoạn không liên quan.
2. **Lập kế hoạch tương ứng.** Đối với công cụ tái cấu trúc theo từng giai đoạn hoặc nhiều tệp, hãy nêu ngắn gọn những gì sẽ thay đổi, ở đâu và cách thức xác minh thay đổi đó. Đối với một chỉnh sửa nhỏ, hãy tiến hành trực tiếp.
3. **Kiểm tra trước khi chỉnh sửa.** Sử dụng lại kho lưu trữ thực files/configuration,, kiểm tra các lược đồ dữ liệu và các thử nghiệm hiện có, đồng thời tránh ghi đè các thay đổi con người. Đừng cho rằng một tập tin theo kế hoạch đã tồn tại.
4. **Triển khai lát cắt dọc hoàn chỉnh nhỏ nhất.** Thích làm việc với scripts/functions và thử nghiệm tối thiểu đối với giàn giáo mở rộng hoặc mã giữ chỗ. Làm cho công việc tính toán tốn kém có thể cấu hình rõ ràng.
5. **Xác minh một cách trung thực.** Chạy các bài kiểm tra nhanh và kiểm tra khói có liên quan. Không khởi chạy BERT huấn luyện kéo dài nhiều giờ, tải xuống bộ dữ liệu khổng lồ, ghi đè các điểm kiểm tra đắt tiền hoặc sử dụng tài nguyên phải trả phí mà không có yêu cầu nhiệm vụ rõ ràng và ủy quyền thực tế. Nếu data/GPU/network không có sẵn, kiểm thử sử dụng **các bộ dữ liệu mẫu được đánh dấu rõ ràng** nhỏ và nêu chính xác những gì vẫn chưa được xác minh.
6. **Chỉ cập nhật kế hoạch khi có bằng chứng.** Kiểm tra `[x]` trong `PLAN_AI.md` và khớp các nhiệm vụ `PLAN_HUMAN.md` chỉ sau khi tiêu chí chấp nhận của chúng và các tệp kết quả thực sự được thỏa mãn. Không bao giờ đánh dấu giai đoạn hoàn thành đối với mã chỉ có khung.
7. **Báo cáo lại trong tiếng Việt.** Tóm tắt các thay đổi đã hoàn thành, các đường dẫn đã chạm, các yêu cầu bị chặn của kiểm thử commands/results, và một nhiệm vụ tiếp theo được đề xuất. Không báo cáo số liệu giả định dưới dạng kết quả đo được.

**Khi bị chặn:** ghi `BLOCKED: <reason>` và `NEXT_ACTION: <concrete action>` vào status/report có liên quan thay vì ẩn giới hạn. Cần có các quyết định của người dùng đối với thay đổi về nội dung phạm vi hoặc đánh giá, chứ không phải các chi tiết triển khai thông thường.

## 7. Cổng chất lượng theo loại thay đổi

- **dữ liệu ingestion/filtering:** kiểm tra đơn vị về bí danh lược đồ, số nhận dạng bị thiếu, ví dụ về laptop-so với phụ kiện, lấy mẫu xác định và xác nhận số hàng; lưu báo cáo QA lọc.
- **Cleaning/labels/splitting:** kiểm tra văn bản trống, bảo toàn phủ định, ranh giới xếp hạng 1/2/3/4/5, ID nhãn ổn định, loại bỏ trùng lặp, độ rời rạc của phân chia và kiểm tra rò rỉ dữ liệu.
- **classifier frozen embeddings:** fixture fit/validate/reload, whitelist embedding và row alignment, seed/version/config cố định, saved predictions/metrics/selection lock. TabPFN phải phân biệt V3/V3_5 bằng SDK, đo tài nguyên train-only; full/subsample và coverage nội bộ phải công bố. Kiểm tra TF-IDF pipeline cũ chỉ dành LEGACY.
- **BERT cảm xúc:** Kiểm thử bộ gom lô tokenizer/dataset,, ánh xạ nhãn, chuyển tiếp, reload/inference, và dự phòng thiết bị mà không yêu cầu chạy huấn luyện đầy đủ.
- **Trích xuất khía cạnh:** kiểm tra độ lệch ký tự, chuyển tiếp BIO, căn chỉnh từ phụ và đánh giá cấp thực thể; bảo quản khía cạnh text/spans. gốc
- **khía cạnh sentiment/end-to-end:** kiểm thử hai khía cạnh phân cực đối lập trong một review, các khía cạnh còn thiếu, xử lý chính sách conflict và lược đồ đầu ra.
- **Streamlit/batch:** ứng dụng phải sử dụng các mô hình đã lưu mà không cần đào tạo lại; xác thực các trường CSV đầu vào, tệp empty/malformed và kích thước lô; cung cấp dự đoán trên mỗi review và tổng hợp tỷ lệ phần trăm sentiment/aspect bằng cách sử dụng mẫu số chính xác.
- **Tài liệu:** hướng dẫn thiết lập và chạy thực thi phải khớp với mã hiện tại. Bao gồm phương pháp và những hạn chế thay vì chỉ chụp ảnh màn hình.

Kiểm tra cục bộ điển hình (chỉ chạy khi files/dependencies tồn tại):

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app/streamlit_app.py
```

Không bao giờ tuyên bố các thử nghiệm, tải xuống, tinh chỉnh hoặc đánh giá đã thành công trừ khi thực sự được thực thi và quan sát.

## 8. Định nghĩa dự án đã hoàn thành

Dự án chỉ kết thúc khi danh sách kiểm tra dựa trên bằng chứng trong `PLAN_AI.md` hoàn tất: laptop-only data/EDA/nhãn-nhiễu, split chống leakage; benchmark majority/XGBoost/TabM/explicit TabPFN V3/V3_5/BERT canonical với giới hạn full/subsample công bố; phân tích lỗi và chi phí; span-level extraction và aspect-conditioned sentiment/ABSA end-to-end; Amazon gold độc lập do người gán; Streamlit single/batch; setup tái lập và điểm mở rộng Vietnamese/PhoBERT. Nghiệm thu benchmark local LIMITED không đồng nghĩa cloud full21000 hoặc toàn dự án đã hoàn tất.

Luôn nêu rõ những hạn chế này trong báo cáo: **Các phát hiện chỉ dành cho laptop**, **nhãn đại diện suy từ số sao-nhiễu nhãn**, **Sự thay đổi SemEval-to-Amazon platform/style trong laptop review** và **bộ dữ liệu gold được chú thích thủ công nhỏ**. Không bao giờ tuyên bố khái quát sang nhiều loại thiết bị hoặc sự sẵn sàng sản xuất mà không có bằng chứng.

## 9. Bối cảnh liên tục và chuyển giao tự động

Khi bắt đầu mỗi cửa sổ session/context mới (kể cả sau khi nén), hãy đọc `AGENTS.md`, sau đó là `docs/CODEX_HANDOFF.md`. Xác định nhiệm vụ hiện tại, hành động tiếp theo và các ràng buộc. Chỉ đọc các phần source/config/document có liên quan trực tiếp đến nhiệm vụ đó; không tự động đọc lại kho lưu trữ, tất cả các báo cáo hoặc lịch sử dự án. Chỉ mở rộng việc đọc đối với thông tin còn thiếu, mâu thuẫn hoặc nhu cầu nhiệm vụ thực tế. Kiểm tra files/artifacts có liên quan trước khi chỉnh sửa; bàn giao là một bản tóm tắt, không phải bằng chứng thay thế mã. Các yêu cầu thay đổi quy mô giai đoạn hiện tại vẫn được áp dụng.

Sau mỗi tác vụ thay đổi mã, cấu hình, kiểm tra, kiến trúc, tập dữ liệu, báo cáo, kế hoạch hoặc trạng thái dự án, Codex PHẢI cập nhật `docs/CODEX_HANDOFF.md` trước phản hồi cuối cùng mà không cần nhắc nhở người dùng: hoàn thành tác vụ, chạy tập xác thực thích hợp, xác định các thay đổi thực tế, làm mới trạng thái bị ảnh hưởng, Tác vụ hiện tại và Hành động tiếp theo, sau đó thêm mục nhập Thay đổi gần đây ngắn gọn. Đồng thời ghi lại failures/blockers khi chúng ảnh hưởng đến việc nối lại, sử dụng `BLOCKED:` và `NEXT_ACTION:`. Các tác vụ chỉ đọc không có thay đổi trạng thái thì không cần cập nhật. Việc chỉnh sửa bản chuyển giao không kích hoạt một chu kỳ cập nhật khác.

Giữ các phần cố định A–H, tốt nhất là 1,000–2,000 token. Thay thế trạng thái cũ thay vì nối thêm vô thời hạn; giữ lại nhiều nhất các bản cập nhật quan trọng gần đây của 5–10. Đường dẫn tham chiếu thay vì sao chép source/reports/history; bỏ qua các lỗi không liên quan đã được giải quyết và các chi tiết trùng lặp. Phân biệt VERIFIED (đã kiểm tra nhiệm vụ này), REPORTED (bằng chứng trước, không chạy lại), PENDING, BLOCKED và NOT_MEASURED. Bao gồm các lệnh tập xác thực, kết quả quan sát được và các giới hạn còn lại; không bao giờ phát minh ra lịch sử hoặc đo lường.

Đối với xung đột, hãy làm theo yêu cầu mới nhất của người dùng và hướng dẫn hiện hành. Sử dụng repository/artifacts thực tế để thiết lập trạng thái thực tế; sử dụng thỏa thuận này và configs/plans có liên quan để thiết lập các yêu cầu. Việc chuyển giao phụ thuộc vào cả hai, không bao giờ là một hợp đồng mới. Giải thích chênh lệch đáng kể. Hành động tiếp theo không cho phép các hoạt động tốn kém hoặc phá hoại: duy trì các cổng ủy quyền hiện có, trần tài nguyên và các biện pháp bảo vệ tính toàn vẹn của dữ liệu.

## 10. Ngôn ngữ làm việc

Theo yêu cầu người dùng ngày 2026-10-19, từ nay trao đổi, tài liệu mới, chú thích mã và nội dung giao diện dùng **tiếng Việt**. Giữ nguyên định danh, tên tệp/đường dẫn, lệnh, khóa cấu hình, nhãn và mã trạng thái cần cho tương thích kỹ thuật. Yêu cầu này không đồng nghĩa mô hình đã hỗ trợ dữ liệu tiếng Việt.

## 11. Mandatory Execution Logging

Quy tắc bắt buộc được thiết lập ngày **2026-10-26**, áp dụng **từ task tiếp theo sau tác vụ thiết lập này**, không tái dựng lại lịch sử P0–P9.

- Mọi công việc có ý nghĩa khoa học hoặc vận hành phải theo lifecycle **Inspect → Execute → Validate → Update Log → Handoff**. Sau validation, cập nhật canonical `docs/PROJECT_EXECUTION_LOG.md` và đồng bộ `reports/project_execution_log.json`; mở rộng schema tối thiểu, tương thích ngược khi cần. Task chưa hoàn tất nếu log liên quan chưa được đồng bộ. Miễn log cho typo, whitespace, format/comment nhỏ không ảnh hưởng logic và thao tác terminal không có giá trị lịch sử.
- Entry tối thiểu: ngày đáng tin, phase/task ID hiện có, objective, inputs/version/split, actions, config hoặc đường dẫn, results, decision/reason, artifacts, validation, impact lên dataset/split/canonical model/metrics/artifacts cũ/downstream, limitations liên quan và evidence. Không có thay đổi khoa học thì ghi `No canonical scientific artifacts changed.` Không ghi `DONE` trước khi execution/validation hoàn tất, artifacts tồn tại và metrics liên quan được xác minh; dở dang ghi đúng `FAILED`, `PARTIAL`, `BLOCKED` hoặc `ABORTED`.
- Append đúng chronology, giữ các attempts thất bại có ý nghĩa. Chỉ sửa entry lịch sử khi có factual correction/bằng chứng mới hoặc thay đổi canonical chính thức; ghi `Historical correction` cùng lý do, giữ quyết định/model trước. Không bịa command, timestamp, metric, test count hoặc preservation; chỉ claim checksum đã kiểm.
- Experiment phải cập nhật registry với experiment/phase/model-method/dataset/validation/test/status/decision. Đổi canonical phải ghi previous/new model, ngày/stage, validation evidence và reason. Quyết định quan trọng phải có context/alternatives/decision/evidence/impact. Issue phải có problem/detected-in/impact/resolution/status (`OPEN`, `RESOLVED`, `ACCEPTED LIMITATION`, `DEFERRED`); sửa xong giữ entry và chuyển `RESOLVED`. Test count thay đổi chỉ thêm mốc sau khi thực chạy, ghi task/số mới/failures/regression status.
- Ưu tiên evidence: artifacts thực tế → metrics/predictions → config → acceptance → test output → current code → documentation. Conversation chỉ bổ sung intent/context/rationale có provenance, không thay artifact khoa học. Log tập trung facts + decisions + provenance, không terminal transcript.
- Cập nhật `docs/CODEX_HANDOFF.md` theo mục 9 khi trạng thái/model/artifact/result/decision/blocker/next step thay đổi; sửa README/PLAN/PROJECT_INDEX chỉ khi thực sự outdated. Việc cập nhật log/handoff không tạo vòng lặp tự ghi log; không thay scientific artifacts chỉ để đồng bộ tài liệu.
- Final response của mọi task phải có **Project Log Update**: `PROJECT_EXECUTION_LOG.md`, `project_execution_log.json`, `CODEX_HANDOFF.md` = `UPDATED`/`NOT REQUIRED` (nêu lý do nếu không cập nhật); Decision Log, Experiment Registry, Issue Registry = `UPDATED`/`NO CHANGE`. Nếu execution xong nhưng không cập nhật được log, báo **`TASK COMPLETE — LOGGING BLOCKED`**, nêu blocker và không coi task hoàn tất hoàn toàn.
