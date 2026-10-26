"""Viết báo cáo A–M sau P7 từ bằng chứng thực tế đã được xác minh."""

import importlib.metadata
import json

from scripts.benchmark_reports import collect, markdown_table, LIMITATIONS
from src.config import PROJECT_ROOT


def main():
    root = PROJECT_ROOT
    completion = json.loads((root / 'reports/p7_completion.json').read_text(encoding='utf-8'))
    assert completion['status'] == 'PASS'
    if completion.get('model_sources'):
        from scripts.publish_kaggle_results import publish
        publish(root)
        return
    results, table = collect(include_transformer=True)
    tests = json.loads((root / 'reports/model_stack_final_validation.json').read_text(encoding='utf-8'))
    assert tests['status'] == 'PASS'
    versions = {p: importlib.metadata.version(p) for p in ['torch', 'transformers', 'tabpfn', 'xgboost', 'tabm', 'numpy', 'scikit-learn']}
    text = ['# Báo cáo hoàn tất benchmark bộ mô hình — 2026-10-24', '',
        '**P0–P7 đã thực thi/nghiệm thu; tổng thể LIMITED vì TabPFN subsampled và WARNING RSS E03. Không tuyên bố tất cả model đã chạy full-data hoặc toàn dự án/ABSA/gold/app đã hoàn tất.**', '',
        '## A. Status', '', '| Pha | Trạng thái | Bằng chứng |', '|---|---|---|',
        '| P0–P4 | PASS/REUSED | báo cáo từng pha trước; cache/hash/config/alignment kiểm lại PASS trong tác vụ này |',
        '| P5-E00/E01/E02 | PASS/REUSED | không retrain hoặc chạy lại test; artifacts cũ giữ nguyên |',
        '| P5-E03 | LIMITED/SUBSAMPLED, WARNING RSS | V3 explicit,10000 mẫu, independent_validation PASS; RSS6,48GB |',
        '| P5-E04 | LIMITED/SUBSAMPLED | V3_5 explicit,1500 mẫu, independent_validation PASS |',
        '| P6 | PASS | canonical BERT unweighted/balanced, selection/reload/metrics PASS |',
        '| P7 | PASS | đủ6 model, thống nhất bảng/lỗi/compute; không tune test |', '',
        'Follow-up cloud full21000 cho V3/V3_5: **PENDING**, chỉ mới lập kế hoạch tại `docs/TABPFN_CLOUD_PLAN.md`; chưa upload, thuê GPU hoặc chạy job. Benchmark local/score trong báo cáo này giữ nguyên. Khả năng full-data không bị bác bỏ bởi trần local6GB.', '',
        '## B. Dataset', '',
        'Giữ dataset30000/9080 parent_asin, negative8259/neutral2631/positive19110. Train21000/validation4500/test4500; seed42 và split hash cố định ở metadata cache. Không acquisition, cleaning lại, resplit hoặc relabel. Dữ liệu raw/legacy giữ nguyên; `model_stack_legacy_preservation_final.json` kiểm lại hashes lịch sử. Kiểm tra cross-split cũ PASS, không đổi dữ liệu; leakage tests tiếp tục PASS.', '',
        '## C. Semantic representation', '',
        'Frozen sentence-transformers/all-MiniLM-L6-v2, revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41,384chiều FP32/mask-mean/L2/max256. Canonical review_title + newline + text, NFC/whitespace; giữ phủ định/dấu câu. Cache đủ30K được reuse và kiểm hash/row alignment; không TF-IDF/SVD/PCA/metadata features. BERT dùng canonical raw text qua tokenizer512, không nhận embeddings frozen.', '',
        '## D. Models', '',
        'Majority sanity; XGBoost/TabM học trên full21K frozen embeddings; TabPFN-3/V3 và TabPFN-3.5/V3_5 trên subsample train phân tầng seed42; BERT end-to-end canonical21K. TabPFN package9.2.0, requested/resolved/checkpoint khác nhau được kiểm tự động; `tabpfn_version_verification.json`. V3 n_estimators1 có giới hạn phủ tối đa200/384 chiều nội bộ theo cảnh báo SDK; representation đầu vào vẫn384. Không thay cấu hình sau test.', '',
        '## E. Validation protocol', '',
        'Validation macro F1 là lựa chọn chính, test chỉ sau selection lock. Hai loss BERT unweighted/balanced cùng pretrained initialization; class weights chỉ từ train. TabPFN cấu hình tài nguyên chọn trên train-only, không validation labels. Tất cả dự đoán có review_id alignment; metrics tính lại độc lập, không re-predict test để xác minh. Test legacy đã được dùng trước đây: không gọi test toàn dự án hoàn toàn unseen.', '',
        '## F. Final test table', '', markdown_table(table), '',
        'Bản CSV không làm tròn metrics gốc: `p7_unified_results.csv`; JSON metrics per-class precision/recall/F1, accuracy, weighted F1, balanced accuracy, confusion matrices trong từng report experiment.', '',
        '## G. Best model', '',
        f"Chọn bằng validation macro F1: **{completion['selected_by_validation']}**. Best frozen: **{completion['best_frozen_by_validation']}**. Test macro/neutral F1 và compute trong bảng; không ưu tiên accuracy đơn thuần. Xem hai comparison trong `p7_unified_benchmark.md`: cùng frozen representation có hạn chế khác số mẫu; frozen vs end-to-end khác representation/context/training paradigm, không so architecture thuần túy.", '',
        '## H. TabPFN resource findings', '',
        'V3 low_memory full21K chạy được: fit0,472s/predict16rows14,500s; cached21K fit~14s/predict32–128rows~0,36–0,44s nhưng RSS~6,06–6,08GB vượt trần6GB. Chọn cached10K dựa trên assessment5,82GB; experiment thực6,48GB vì overhead runner/serialization/reload. WARNING: trần là kiểm tra giữa bước, E03 chưa enforce RSS, đã bổ sung chặn trước test cho E04; không rerun test để che sự cố. V3.5 low_memory5K RSS9,14GB, cached2,5K RSS6,36GB; chọncached1,5K, actualRSS4,55GB. Không thửfull21K V3.5 sau ngưỡng này, không gọi là OOM. CPUprecisionauto được thử cả hai, SDKguard >5000; không dùng API trả phí. Hai report resource/JSON ghi đầy đủ số mẫu,features,dtype,fit/predict,RAM/GPU. Token được cấu hình cấp User nhưng process chưa kế thừa; cached checkpoint hợp lệ chạy được. Chỉ lưu presence boolean, không ghi token.', '',
        '## I. Error analysis', '',
        'Xem `p7_error_transitions.csv`, `p7_error_groups.csv`, `p7_error_examples.csv`: neutral→positive/negative, negative↔positive, short/long, negation, mixed cue, ambiguous cần người đọc. Cue là heuristic, chưa human verified. Star/text mismatch là câu hỏi review thủ công, không tự coi mọi bất đồng proxy là nhiễu nhãn. Confidence null, không bịa xác suất. Không dùng phân tích lỗi sau test để tune lại.', '',
        '## J. Limitations', '', LIMITATIONS, '',
        'Khác train size/full-vs-subsample, V3 feature coverage, context256/512, phần cứng16GB/RTX4050Laptop6GB và GPU shared memory Windows hạn chế diễn giải. Một seed/search nhỏ, không khẳng định superiority thống kê hoặc production readiness. Preprocessing cost toàn30K NOT_MEASURED; sample encoder có đo riêng. Runtime CPU/GPU không cùng điều kiện.', '',
        '## K. Reproducibility', '',
        'Seed42; configs semantic/modern_tabular/transformer_benchmark, cache/source/model hash và selection lock giữ lại. BERT google-bert/bert-base-uncased revision86b5e0934494bd15c9632b12f734a8a67f723594; pretrained weights nguồn được hash, checkpoint tốt nhất có hash/reload parity. Không pin mơ hồ TabPFN default. Môi trường Windows/Python3.13.12/RTX4050Laptop; phiên bản package:', '',
        '```json', json.dumps(versions, indent=2), '```', '',
        'Lệnh tiếp tục/xác minh: `python -m scripts.validate_modern E03_tabpfn_v3_embedding`, tương tự E04; `python -m scripts.validate_transformer`; `python -m scripts.test_all`. Không chạy lại runner vào thư mục đã có hoặc mở lại test đã khóa. `finish_benchmark` chỉ tổng hợp dự đoán đã lưu, không training/predict.', '',
        '## L. Tests', '', '```json', json.dumps(tests, ensure_ascii=False, indent=2), '```', '',
        'Xác minh alignment/metrics/hash/validation selection, hai TabPFN version khác nhau, no forbidden features và leakage tests PASS. Test token redaction dùng fixture giả, không token thật. Tổng tests không cộng các lần chạy lặp lại. Không fake human labels, smoke hoặc model results.', '',
        '## M. Files created/modified', '',
        'Mới: `scripts/assess_tabpfn.py`, `report_tabpfn_resources.py`, `benchmark_reports.py`, `train_transformer.py`, `validate_transformer.py`, `finish_benchmark.py`, `final_completion.py`; `src/evaluation/redaction.py`; `configs/transformer_benchmark.yaml`; `tests/test_resource_policy.py`, `test_final_benchmark.py`; resource/experiment reports, final comparison/error CSV/JSON, artifacts E03 attempt/E04/E05. Sửa `scripts/train_modern.py` (resource decision/subsample/error redaction/RSS guard/reload memory), reporting entrypoint, hai PLAN/README/docs/handoff. Legacy/raw/dataset/split/embedding files không sửa. Repository vẫn untracked từ đầu; không commit/reset/checkout.', '',
        'Bảo trì tài liệu sau benchmark: `docs/PROJECT_INDEX.md` phân biệt hiện hành/lịch sử; `docs/TABPFN_CLOUD_PLAN.md` chỉ lập follow-up PENDING. Hai PLAN/README cũ được snapshot kèm hash dưới `docs/archive/20261024_before_cleanup/`; tiêu chí P8–P12 giữ nguyên. Generator báo cáo không còn tạo CSV partial trùng hoặc template BLOCKED cũ. Danh sách dọn thực tế và kiểm tra nằm trong `reports/documentation_cleanup_20261024.json`/`.md`; không xóa bằng chứng/model/dataset.', '']
    (root / 'reports/model_stack_refactor_completion.md').write_text('\n'.join(text), encoding='utf-8')
    print(json.dumps({'overall': 'LIMITED', 'P6': 'PASS', 'P7': 'PASS', 'best_by_validation': completion['selected_by_validation']}))


if __name__ == '__main__':
    main()
