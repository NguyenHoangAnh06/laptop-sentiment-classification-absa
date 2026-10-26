# Đánh giá tài nguyên TabPFN V3_5

Chỉ dùng frozen embeddings train, 384 chiều float32; seed42, lấy mẫu phân tầng. Không dùng validation/test để chọn cấu hình tài nguyên. `tabpfn==9.2.0`, phiên bản explicit, n_estimators1, memory_saving_mode=True, keep_cache_on_device=False. Không PCA/SVD hoặc text preprocessing.

| Phép đo | Mẫu | Chế độ | Lô | Fit s | Predict s | RSS byte | GPU allocated byte | GPU reserved byte | Trạng thái |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 10000_interrupted | 10000 | NOT_MEASURED | None | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | INTERRUPTED |
| 1000_cuda_b16 | 1000 | low_memory | 16 | 0.9460196997970343 | 1.1174739999696612 | 3170308096 | 2470191616 | 3336568832 | PASS |
| 1500_cuda_cache_b128 | 1500 | fit_with_cache | 128 | 1.9967508995905519 | 0.19805630017071962 | 3206238208 | 3415636480 | 5362417664 | PASS |
| 21000_cpu_auto | 21000 | fit_with_cache | 128 | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | ERROR |
| 2500_cuda_b16 | 2500 | low_memory | 16 | 0.9859342002309859 | 2.6034880001097918 | 4951830528 | 4767912960 | 7386169344 | PASS |
| 2500_cuda_cache_b128 | 2500 | fit_with_cache | 128 | 6.654454299714416 | 0.2749540996737778 | 6356471808 | 5026346496 | 8835301376 | PASS |
| 5000_cuda_b16 | 5000 | low_memory | 16 | 0.7173203998245299 | 10.852365299593657 | 9138573312 | 7276806144 | 13050576896 | PASS |
| 500_cuda_b16 | 500 | low_memory | 16 | 3.4591962001286447 | 1.2044395003467798 | 3106009088 | 1710684672 | 2187329536 | PASS |

## Lỗi đã quan sát

- `21000_cpu_auto.json`: Running on CPU with more than 5000 samples is not allowed by default due to slow performance. To override this behavior, set the environment variable TABPFN_ALLOW_CPU_LARGE_DATASET=1 or set ignore_pretraining_limits=True. Alternatively, consider using a GPU or the tabpfn-client API: [URL]

## Quyết định trước experiment

```json
{
  "status": "PASS",
  "train_samples": 1500,
  "data_regime": "SUBSAMPLED",
  "fit_mode": "fit_with_cache",
  "prediction_batch_size": 128,
  "evidence": "1500_cuda_cache_b128.json",
  "reason": "5000 low_memory RSS 9.14GB, 2500 cached RSS 6.36GB exceeds 6GB; CPU guard >5000. Full21K not measured after safe stop."
}
```

RSS là bộ nhớ toàn tiến trình lấy mẫu20ms, không phải giới hạn cứng của hệ điều hành. GPU allocated/reserved do PyTorch báo cáo có thể bao gồm bộ nhớ chia sẻ Windows; không diễn giải reserved là VRAM vật lý. Phép đo nằm trong tiến trình riêng, không phải RSS toàn máy.

V3: đủ21K đã thử với official memory-saving và nhiều lô; cached vượt trần RSS6GB, low_memory lô nhỏ có chi phí ngoại suy validation/reload/test vượt1800s. V3.5: dừng tăng mẫu sau phép đo5000 vì RSS9,14GB; full21K chưa đo, không tuyên bố OOM. Cả hai có thử CPU precision auto: guard thư viện chặn >5000 mẫu; không bỏ guard trên máy16GB. Quyết định riêng từng model được ghi ở JSON phía trên; dùng subsample train seed42, giữ tỷ lệ lớp, không giảm chiều embedding.

Đây là phép đo kỹ thuật; không phải kết quả chất lượng mô hình. Chỉ laptop, rating-derived proxy labels có nhiễu; không có human gold trong phép đo.

Follow-up full21000 trên cloud mới là PENDING: xem `docs/TABPFN_CLOUD_PLAN.md`. GPU24GB/RAM32GB hoặc A10040GB/RAM64GB chỉ là đề xuất đo mới, không phải cloud đã PASS. Không thay decision hoặc số liệu local trong báo cáo này.
