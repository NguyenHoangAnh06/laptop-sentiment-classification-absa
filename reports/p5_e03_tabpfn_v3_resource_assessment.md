# Đánh giá tài nguyên TabPFN V3

Chỉ dùng frozen embeddings train, 384 chiều float32; seed42, lấy mẫu phân tầng. Không dùng validation/test để chọn cấu hình tài nguyên. `tabpfn==9.2.0`, phiên bản explicit, n_estimators1, memory_saving_mode=True, keep_cache_on_device=False. Không PCA/SVD hoặc text preprocessing.

| Phép đo | Mẫu | Chế độ | Lô | Fit s | Predict s | RSS byte | GPU allocated byte | GPU reserved byte | Trạng thái |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| 10000_cuda_b16 | 10000 | low_memory | 16 | 0.3760388996452093 | 6.028907800093293 | 4969340928 | 6114071552 | 9183428608 | PASS |
| 10000_cuda_cache_b128 | 10000 | fit_with_cache | 128 | 6.337710800115019 | 0.18145549995824695 | 5816950784 | 6113728000 | 9229565952 | PASS |
| 1000_cuda_b16 | 1000 | low_memory | 16 | 0.4511064998805523 | 0.8895039004273713 | 2069786624 | 1189161472 | 1417674752 | PASS |
| 21000_cpu_auto | 21000 | fit_with_cache | 128 | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | ERROR |
| 21000_cpu_cache_b128 | 21000 | fit_with_cache | 128 | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | ERROR |
| 21000_cpu_cache_retry | 21000 | fit_with_cache | 128 | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | NOT_MEASURED | ERROR |
| 21000_cuda_b128 | 21000 | low_memory | 128 | 0.4956392999738455 | 16.87563359970227 | 6324076544 | 6223186944 | 9613344768 | PASS |
| 21000_cuda_b16 | 21000 | low_memory | 16 | 0.4715219000354409 | 14.500325900036842 | 5741682688 | 6221749248 | 9613344768 | PASS |
| 21000_cuda_cache_b128 | 21000 | fit_with_cache | 128 | 14.24581200024113 | 0.44217099994421005 | 6060224512 | 6221636608 | 9611247616 | PASS |
| 21000_cuda_cache_b32 | 21000 | fit_with_cache | 32 | 14.067206100095063 | 0.35633340012282133 | 6078504960 | 6221636608 | 9611247616 | PASS |
| 2500_cuda_b16 | 2500 | low_memory | 16 | 0.5023752995766699 | 1.2575508998706937 | 2077306880 | 2576870400 | 3414163456 | PASS |
| 5000_cuda_b16 | 5000 | low_memory | 16 | 0.36926940036937594 | 2.7015505000017583 | 3264700416 | 4880857088 | 6417285120 | PASS |
| 500_cuda_b16 | 500 | low_memory | 16 | 0.6552039002999663 | 1.3399990000762045 | 2083733504 | 725052416 | 1000341504 | PASS |

## Lỗi đã quan sát

- `21000_cpu_auto.json`: Running on CPU with more than 5000 samples is not allowed by default due to slow performance. To override this behavior, set the environment variable TABPFN_ALLOW_CPU_LARGE_DATASET=1 or set ignore_pretraining_limits=True. Alternatively, consider using a GPU or the tabpfn-client API: [URL]
- `21000_cpu_cache_retry.json`: You specified `inference_precision="autocast"`, however one or more of the selected devices (devices=(device(type='cpu'),)) does not support it. On CPU, autocast requires hardware-accelerated bfloat16 (Intel AMX / AVX512-BF16, AMD Zen 4+). Set `inference_precision="auto"` to fall back to full precision automatically.

## Quyết định trước experiment

```json
{
  "status": "PASS",
  "train_samples": 10000,
  "data_regime": "SUBSAMPLED",
  "fit_mode": "fit_with_cache",
  "prediction_batch_size": 128,
  "evidence": "10000_cuda_cache_b128.json",
  "reason": "Full21K cached RSS exceeds 6000000000 bytes; low_memory small batches exceed 1800 seconds projected; CPU default guard >5000 samples."
}
```

RSS là bộ nhớ toàn tiến trình lấy mẫu20ms, không phải giới hạn cứng của hệ điều hành. GPU allocated/reserved do PyTorch báo cáo có thể bao gồm bộ nhớ chia sẻ Windows; không diễn giải reserved là VRAM vật lý. Phép đo nằm trong tiến trình riêng, không phải RSS toàn máy.

V3: đủ21K đã thử với official memory-saving và nhiều lô; cached vượt trần RSS6GB, low_memory lô nhỏ có chi phí ngoại suy validation/reload/test vượt1800s. V3.5: dừng tăng mẫu sau phép đo5000 vì RSS9,14GB; full21K chưa đo, không tuyên bố OOM. Cả hai có thử CPU precision auto: guard thư viện chặn >5000 mẫu; không bỏ guard trên máy16GB. Quyết định riêng từng model được ghi ở JSON phía trên; dùng subsample train seed42, giữ tỷ lệ lớp, không giảm chiều embedding.

Đây là phép đo kỹ thuật; không phải kết quả chất lượng mô hình. Chỉ laptop, rating-derived proxy labels có nhiễu; không có human gold trong phép đo.

Follow-up full21000 trên cloud mới là PENDING: xem `docs/TABPFN_CLOUD_PLAN.md`. GPU24GB/RAM32GB hoặc A10040GB/RAM64GB chỉ là đề xuất đo mới, không phải cloud đã PASS. Không thay decision hoặc số liệu local trong báo cáo này.
