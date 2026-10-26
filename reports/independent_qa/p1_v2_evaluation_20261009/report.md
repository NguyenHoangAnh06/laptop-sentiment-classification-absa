# TỪ CHỐI bổ sung con người QA

Trạng thái: HUMAN_EVALUATION_REVIEW_REQUIRED

Người chú thích: human_reviewer_01; xuất xứ: không xác định

Các ước tính kết hợp sử dụng các đơn vị TỪ CHỐI thí điểm làm quan sát độ chắc chắn và trọng số SRS trên khung còn lại; không có sự tổng hợp ngây thơ.

```json
{
  "confusion_matrix": {
    "TP": 408480.0,
    "FP": 0.0,
    "FN": 50090.92396313364,
    "TN": 43428113.07603686
  },
  "precision": 1.0,
  "recall": 0.8907673353333656,
  "f1": 0.9422283944590278,
  "confidence_level": 0.95,
  "intervals": {
    "precision": [
      0.9712152369761066,
      1.0
    ],
    "recall": [
      0.5545836938789489,
      0.99845519075461
    ],
    "f1": [
      0.706017185858016,
      0.9992269983072242
    ]
  },
  "success_total_bounds": {
    "KEEP": [
      396722,
      408480
    ],
    "REJECT": [
      632,
      318629
    ]
  },
  "sampling_weights": {
    "KEEP": 2723.2,
    "REJECT_remaining": 50089.92396313364,
    "certainty": 1
  },
  "kish_effective_sample_size": 883.9410335567492,
  "method": "Equal-tail exact hypergeometric inversion per random stratum at alpha/2; Bonferroni joint bounds transformed monotonically to ratios. Conditional on fixed labels and valid SRS. Kish ESS is descriptive, not ratio-specific precision."
}
```

Thử nghiệm xác minh con người sau khi giữ lại đề xuất AI; review mới không làm cho v1 bị mù. Không hoàn thành cổng tự động. Chẩn đoán bị loại trừ; phạm vi QA không phải là sentiment/ABSA gold.
