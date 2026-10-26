# P4 — semantic representation

Trạng thái: PASS.

Split cũ được giữ nguyên; toàn bộ ô nguồn so bằng nhau, không resplit. Kiểm tra ID/parent/variant/group/body/canonical text và lexical near-duplicate cross-split PASS.

Encoder frozen: {'model': 'sentence-transformers/all-MiniLM-L6-v2', 'revision': '1110a243fdf4706b3f48f1d95db1a4f5529b4d41', 'dimension': 384, 'pooling': 'attention_mask_mean', 'normalize_embeddings': True, 'max_length': 256, 'batch_size': 32, 'device': 'cuda', 'dtype': 'float32'}. Không fit theo nhãn, không TF-IDF/BoW/SVD/PCA.

Sample train 128 review: {'rows': 128, 'seconds': 0.1476782001554966, 'reviews_per_second': 866.749458384673, 'peak_process_rss_bytes': 1382313984, 'peak_gpu_allocated_bytes': 265123328, 'peak_gpu_reserved_bytes': 367001600, 'deterministic_sample': True, 'duplicate_consistency': True, 'selected_encoder': {'model': 'sentence-transformers/all-MiniLM-L6-v2', 'revision': '1110a243fdf4706b3f48f1d95db1a4f5529b4d41', 'dimension': 384, 'pooling': 'attention_mask_mean', 'normalize_embeddings': True, 'max_length': 256, 'batch_size': 32, 'device': 'cuda', 'dtype': 'float32'}, 'reason': 'MiniLM 6 lớp, 384 chiều và sample đo trực tiếp phù hợp VRAM 6GB; không chọn dựa trên nhãn hoặc test score', 'limits': 'Một encoder được đo; không khẳng định tối ưu hơn các encoder chưa thử; max_length256 có truncation'}.

Chọn MiniLM vì kích thước 384 và chi phí đo trên GPU hiện có phù hợp. Không khẳng định encoder tốt nhất về sentiment; không dùng validation/test labels để chọn encoder. Giới hạn: review dài bị cắt ở 256 WordPiece; Transformer dùng tối đa 512 nên so sánh hai kiến trúc bao gồm khác biệt representation/context.

Cache: `data/processed/features/semantic_20261024`; embedding/labels/mapping/metadata/token BERT lưu riêng. BERT nhận canonical text qua tokenizer riêng, không dùng embedding.

Cache identity gồm hash dataset, split, config, tokenizer. Loader kiểm tra hash từng tệp, row order, label và text hash. Config/dataset/split thay đổi sẽ bị từ chối; không âm thầm encode/overwrite.

QA từng split: {'train': {'shape': [21000, 384], 'dtype': 'float32', 'norm_min': 0.9999998807907104, 'norm_max': 1.0000001192092896, 'finite': True, 'seconds': 18.533025099895895, 'peak_process_rss_bytes': 1571921920, 'peak_gpu_allocated_bytes': 278148608, 'ordered_ids_hash': '10ebaba1aaf26076ac652b0933ac7195847a3b85e3c6e5e07cb4e4b246e5e533'}, 'validation': {'shape': [4500, 384], 'dtype': 'float32', 'norm_min': 0.9999998807907104, 'norm_max': 1.0000001192092896, 'finite': True, 'seconds': 4.323343399912119, 'peak_process_rss_bytes': 1702555648, 'peak_gpu_allocated_bytes': 277952000, 'ordered_ids_hash': '8b4019a679d155c6fd3cc313aa40486c92bd7edfc460baf1509665fa15237024'}, 'test': {'shape': [4500, 384], 'dtype': 'float32', 'norm_min': 0.9999998807907104, 'norm_max': 1.0000001192092896, 'finite': True, 'seconds': 3.9811856001615524, 'peak_process_rss_bytes': 1482510336, 'peak_gpu_allocated_bytes': 277952000, 'ordered_ids_hash': 'ebbbfc08b872c13d62893e9e74c51b8ebff865fb6663f869d8d0719ac7b8e03f'}}. Sample replay và duplicate consistency PASS.

Bằng chứng: `p4_semantic_split_validation.json`, `p4_encoder_benchmark.json` và cache metadata. Kiểm tra gần trùng là xấp xỉ từ vựng, không bảo đảm mọi paraphrase. Test cũ đã được đánh giá trong benchmark LEGACY; benchmark mới không phải test hoàn toàn chưa từng xem của toàn dự án.

Giới hạn: chỉ laptop; proxy labels nhiễu; shift SemEval–Amazon trong laptop; gold thủ công nhỏ, hiện chưa có.
