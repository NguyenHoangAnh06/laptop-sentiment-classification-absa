# P1 ? Nhập và chuẩn hóa SemEval-2014 laptop

## Quyết định của chủ sở hữu hiện tại — 2026-10-09

P1 **DONE**: C1-A/C2-A/C3-A đã được phê duyệt và SemEval Train/Test cộng với JSONL được chấp nhận theo ngoại lệ giáo dục được chủ sở hữu phê duyệt. Xác minh Source/license được miễn; **NOT_VERIFIED**, không bao giờ GIẤY PHÉP PASS/VERIFIED. Không cần tìm kiếm thêm nguồn, thu thập bằng chứng hoặc tải xuống lại. PASS kỹ thuật hiện có được sử dụng lại khi byte không thay đổi. Bảo quản partitions/spans/polarity/provenance gốc và P10 gold độc lập. P2 DONE; P3 bây giờ là DONE; hiện không thực thi P4/later. Bằng chứng P3: `reports/p3_data_analysis_20261009.md`. Bản ghi: `reports/tables/p1_semeval_owner_exception_20261009.json`.

Các tuyên bố gate/status trước đây sau đây là bằng chứng lịch sử, được thay thế bởi quyết định của chủ sở hữu hiện tại; họ không yêu cầu xác minh lại.

Đã xác minh 2026-10-08 (Asia/Saigon). Cả hai tệp XML do người dùng cung cấp đều phân tích cú pháp thành công; lược đồ, nhãn gán và ký tự chính xác vị trí cụm từ PASS. Không có acquisition/download nào được thực hiện trong nhiệm vụ này.

## Nguồn gốc và khả năng tái sản xuất

Các tệp nhân bản GitHub do người dùng cung cấp cho nghiên cứu cá nhân; Giấy phép bộ dữ liệu chưa được xác minh chính thức; SHA256 cục bộ không xác thực nguồn gốc chính thức.

Người dùng báo cáo xuất xứ nhân bản GitHub; bản sao chính xác URL/revision và nhận dạng byte chính thức là NOT_VERIFIED. Trước đó HF/official-access review là bằng chứng lịch sử, không phải bằng chứng của những tập tin này? nguồn gốc. Xác minh giấy phép vẫn là PENDING; quá trình nhập cục bộ đã hoàn tất. XML thô được giữ lại không thay đổi (tổng số byte 866,066), bị bỏ qua git, cần thiết để tái tạo JSONL và điều tra các vấn đề gán nhãn trong tương lai.

Chạy từ kho lưu trữ gốc:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.normalize_semeval_p1
# Rerun: use --report reports/tables/semeval_rerun.json (new path).
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
```

JSONL giống hệt hiện có được chấp nhận; đầu ra khác nhau và đường dẫn báo cáo hiện tại bị từ chối. Lỗi XML parse/schema không thành công rõ ràng. Các điểm bất thường của gán nhãn được giữ lại bằng chẩn đoán, các thuộc tính XML repaired/dropped. không bao giờ được giữ lại để bảo toàn các chuỗi bù gốc. Không có bản sao kho văn bản tạm thời nào được tạo ra.

## Tổng quan về bộ dữ liệu được đo

| Số liệu | tập huấn luyện | kiểm thử |
|---|---:|---:|
| câu | 3045 | 800 |
| Điều khoản khía cạnh | 2358 | 654 |
| Với những khía cạnh | 1488 | 422 |
| Không có khía cạnh | 1557 | 378 |
| Nhiều khía cạnh | 558 | 156 |
| Ký tự trung bình | 78.01576354679803 | 67.57125 |
| Các từ có khoảng trắng nghĩa | 14.862725779967159 | 12.905 |
| Các khía cạnh của positive | 987 | 341 |
| Các khía cạnh của negative | 866 | 128 |
| Các khía cạnh của neutral | 460 | 169 |
| Các khía cạnh của conflict | 45 | 16 |

ID trùng lặp: 0 trong mỗi phân chia. tập huấn luyện có các nhóm văn bản trùng lặp 12/các lần xuất hiện bổ sung 12; kiểm thử bằng không. Chồng chéo chính xác và whitespace/casefold Train/Test: một câu kiểm thử, ID `227`; ID chia sẻ `227`. Các phân vùng ban đầu không thay đổi. xây dựng mô hình trong tương lai phải ghi lại rõ ràng sự nhiễm trùng chồng chéo và mọi phân tích độ nhạy riêng biệt mà không âm thầm thay đổi kiểm thử chính thức.

Các cực của Invalid/misaligned vị trí cụm từ, missing/unsupported, văn bản trống, các khía cạnh chồng chéo và các chẩn đoán gán nhãn khác: không ở cả các tập đã chia. Lược đồ chỉ chứa sentences/text/aspectTerms/aspectTerm và các thuộc tính dự kiến. Không có nhãn gán nào được thay đổi.

## Đầu ra và tính toàn vẹn

| phân chia | đầu vào | đầu ra | Trạng thái |
|---|---|---|---|
| tập huấn luyện | `data/raw/semeval/Laptop_Train_v2.xml` | `data/interim/semeval/train_sentences.jsonl` | PASS |

Đầu vào tập huấn luyện: byte 687312; bản ghi 3045; SHA256 `efec2ed73b4efb83b47c697114d800149c558118884afa80362a6e975ba7248c`.

Đầu ra tập huấn luyện: byte 858815; bản ghi 3045; SHA256 `06abcd3f33eb256a73b40bcbcfe3217854346c54c40cc952843db0a16d89011b`.
| kiểm thử | `data/raw/semeval/Laptops_Test_Gold.xml` | `data/interim/semeval/test_sentences.jsonl` | PASS |

Đầu vào kiểm thử: byte 178754; bản ghi 800; SHA256 `aa3a30c9dd7e0eacf9b69e898eb4118a36c1b4f391a30a08dfc41a38d8b8745b`.

Đầu ra kiểm thử: byte 223295; bản ghi 800; SHA256 `42e17079730204223294e83c88ecfe961a225f5630347fe867d62c10e354de96`.

Chẩn đoán trùng lặp Manifest/statistics/complete: `reports/tables/p1_semeval_normalization.json`. Mỗi input/output bao gồm tên tệp, byte, số lượng SHA256, sentence/aspect, trạng thái, dấu thời gian xử lý UTC, xuất xứ và phiên bản biến đổi `semeval_sentences_v1`. Chuyến đi khứ hồi JSONL tương đương với các bản ghi có nguồn gốc từ XML được phân tích cú pháp, bao gồm văn bản, ID, thứ tự khía cạnh, độ lệch và phân cực. Giá trị băm đầu vào không thay đổi. Bảo quản Split/order/count PASS.

## Sẵn sàng ATE/ASC

ATE: vị trí cụm từ chính xác sẵn sàng cho việc căn chỉnh BIO sau này; giữ lại câu 1,557/378 no-khía cạnh. Các câu trùng lặp và chồng chéo train/test yêu cầu xử lý đánh giá bằng tài liệu. Căn chỉnh Token/subword là NOT_MEASURED; không có BIO/tokenization được tạo.

ASC: bối cảnh + thuật ngữ + vị trí + phân cực ban đầu có sẵn. Tất cả 61 conflict nhãn gán được giữ lại. bộ dữ liệu ba lớp trong tương lai phải xác định rõ ràng đánh giá conflict exclusion/separate; không bao giờ ánh xạ conflict tới neutral. Không có ví dụ ASC nào, điều chỉnh tập xác thực phân chia, huấn luyện hoặc kiểm thử được tạo.

## Trạng thái tập xác thực và P1

Các bài kiểm tra 101 đã đạt trong 1.29 bằng cách sử dụng lệnh `.venv` ở trên. Năm thử nghiệm lịch thi đấu mới bao gồm chuyển đổi không mất dữ liệu, các khía cạnh no/empty/multiple, conflict, chuỗi ID, chẩn đoán, ID trùng lặp, cách ly phân chia, chạy lại xác định, tính toàn vẹn JSONL/count và malformed/unsupported XML. Hệ thống mặc định Python thiếu pytest; môi trường dự án trôi qua.

Kiểm tra lược đồ SemEval acquisition/access, gốc-phân chia cục bộ, JSONL được chuẩn hóa và tổng quan hoàn tất; Việc thu thập nguồn authorized/licence-verified không được chứng nhận. P1 KHÔNG phải DONE: vẫn cần có QA sản phẩm con người độc lập. NEXT_ACTION: QA sản phẩm độc lập cộng với xác minh xuất xứ gương licence/source. Các giai đoạn ABSA sau này tạo ra các ví dụ được điều chỉnh BIO và khía cạnh chỉ sử dụng tập huấn luyện, giữ cho kiểm thử gold độc lập.

Hạn chế: Chỉ phát hiện được laptop; Amazon nhãn đại diện suy từ số sao-nhiễu nhãn; Sự thay đổi SemEval-sang-Amazon platform/style trong laptop review; do con người gán nhãn nhỏ Amazon bộ dữ liệu gold (hiện không có). Không có số liệu mô hình hoặc xác nhận quyền sở hữu production/generalization.
