"""Tổng hợp trạng thái thực của refactor, kể cả bị chặn; không chạy huấn luyện/test."""

import json

import pandas as pd

from scripts.train_modern import ORDER, latest_report
from src.config import PROJECT_ROOT
from src.preprocessing.semantic_cache import load_semantic_config


def main() -> None:
    root = PROJECT_ROOT
    if (root / 'reports/p7_completion.json').exists():
        from scripts.final_completion import main as final_report
        final_report()
        return
    cfg = load_semantic_config(root)
    results = {}
    for name in ORDER:
        report = latest_report(root / cfg['reports'] / name)
        path = report / 'result.json'
        results[name] = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'status': 'NOT STARTED'}
    benchmark = json.loads((root / 'reports/p4_encoder_benchmark.json').read_text(encoding='utf-8'))
    validation_path = root / 'reports/model_stack_validation.json'
    validation = json.loads(validation_path.read_text(encoding='utf-8')) if validation_path.exists() else {'status': 'PENDING'}
    rows = []
    for name, result in results.items():
        m = result.get('test_metrics', {})
        per_class = m.get('per_class', {})
        rows.append({'model': name, 'status': result['status'],
            'representation': 'majority sanity' if name == 'E00_majority' else 'frozen semantic embedding',
            'validation_macro_f1': result.get('validation_macro_f1'),
            'macro_f1': m.get('macro_f1'), 'accuracy': m.get('accuracy'), 'weighted_f1': m.get('weighted_f1'),
            'balanced_accuracy': m.get('balanced_accuracy'),
            **{f'{label}_f1': per_class.get(label, {}).get('f1') for label in ['negative', 'neutral', 'positive']},
            'runtime_seconds': result.get('runtime_seconds'),
            'peak_gpu_allocated_bytes': result.get('peak_gpu_allocated_bytes'),
            'peak_process_rss_bytes': result.get('peak_process_rss_bytes'),
            'artifact_bytes': result.get('artifact_bytes'),
            'inference_ms_per_review': result.get('inference_ms_per_review')})
    rows.append({'model': 'E05_transformer', 'status': 'NOT STARTED', 'representation': 'raw canonical text; end-to-end fine-tuning'})
    # Đây là bảng tiến độ P5, không phải tuyên bố đã hoàn thành P7.
    pd.DataFrame(rows).to_csv(root / 'reports/model_stack_partial_results.csv', index=False)
    header = ['| Model | Trạng thái | Representation | Val macro F1 | Test macro F1 | Accuracy | Weighted F1 | Balanced accuracy | Neg F1 | Neu F1 | Pos F1 | Runtime s | Peak VRAM byte |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    keys = ['model', 'status', 'representation', 'validation_macro_f1', 'macro_f1', 'accuracy', 'weighted_f1',
            'balanced_accuracy', 'negative_f1', 'neutral_f1', 'positive_f1', 'runtime_seconds', 'peak_gpu_allocated_bytes']
    def display(value):
        if value is None:
            return 'NOT_MEASURED'
        return f'{value:.6f}' if isinstance(value, float) else str(value)
    table = '\n'.join(header + ['| ' + ' | '.join(display(row.get(k)) for k in keys) + ' |' for row in rows])
    blockers = [f'BLOCKED: {name}: {result.get("error_type", "")}: {result.get("error", "").strip()}'
                for name, result in results.items() if result['status'] in ['BLOCKED', 'FAILED']]
    blocker_text = '\n\n'.join(blockers) if blockers else 'Không có blocker đã ghi.'
    next_action = ('NEXT_ACTION: chủ tài khoản chấp nhận giấy phép TabPFN-3/3.5 tại https://ux.priorlabs.ai, '
        'cấu hình TABPFN_TOKEN cục bộ; chạy `python -m scripts.train_modern E03_tabpfn_v3_embedding --attempt retry01`. '
        'Không gửi token trong chat/Git. Giữ nguyên attempt cũ; smoke và đo VRAM trước full21K. '
        'Sau E03 PASS mới E04, sau P5 PASS mới P6/P7. Không chạy lại test E00/E01/E02 đã khóa.')
    limits = ('Chỉ kết luận cho laptop. Nhãn đại diện suy từ số sao có nhiễu; neutral chỉ 8,77%. '
        'Frozen MiniLM/context256 khác Transformer end-to-end/context512; không quy mọi chênh lệch cho classifier. '
        'Test đã từng được đánh giá trong LEGACY; không phải test hoàn toàn chưa từng xem của toàn dự án. '
        'Một seed42, search nhỏ; không khẳng định ý nghĩa thống kê hay encoder tối ưu. '
        'TabPFN chưa tải trọng số nên chi phí/VRAM/full21K NOT_MEASURED, không phải OOM. '
        'Shift SemEval–Amazon trong cùng laptop; bộ gold thủ công nhỏ và hiện chưa có. Không triển khai ABSA hoặc tiếng Việt.')
    p5 = ['# P5 — benchmark tabular hiện đại', '', 'Trạng thái: BLOCKED; E00/E01/E02 PASS; E03 BLOCKED; E04 NOT STARTED.', '',
        'E00 chỉ sanity, không xếp model cạnh tranh. E01/E02 dùng chung ma trận 21K × 384, không rating/target/ID/metadata trong X. Selection trên validation macro F1, lock trước test, reload validation và independent recomputation PASS.', '', table, '',
        'XGBoost: CPU hist, 2 threads, 2 cấu hình × unweighted/weighted. TabM: CUDA, 3 blocks × width256 × ensemble32, tối đa25 epochs, patience5; hai loss, checkpoint tốt nhất theo validation. Mỗi epoch ghi loss/macro/per-class/runtime/GPU. Không SMOTE.', '',
        'E03 dùng explicit ModelVersion.V3; low_memory, memory_saving_mode=True, n_estimators=1, autocast, keep_cache_on_device=False. Smoke 24 mẫu thực (8/lớp) từ train dừng vì license trước inference; chưa thử full21K, không subsample full experiment.', '',
        'E04 explicit ModelVersion.V3_5 đã được kiểm tra resolve khác V3 tại P0, nhưng fit/predict chưa chạy do cổng tuần tự. Không thể coi cả bốn model đã attempt hợp lệ; P5 chưa đạt acceptance.', '',
        blocker_text, '', next_action, '',
        'Runtime là toàn bộ tuning + selection + final eval trong experiment, không phải chỉ fit checkpoint tốt nhất. XGBoost dùng CPU, TabM GPU nên không so tốc độ như cùng thiết bị. RSS là toàn process, gồm thư viện; VRAM là peak PyTorch cấp phát, không gồm mọi allocation ngoài Torch (XGBoost CPU có 0). Inference latency là thời gian final test batch chia số review, không phải interactive single-review hoặc benchmark lặp nhiều lần.', '',
        'Chi tiết: `reports/semantic_20261024/<experiment>/{config,candidates,selection_lock,result,validation_metrics,test_metrics,independent_validation}.json`, prediction NPY/parquet và confusion CSV. Artifact ở `artifacts/models/semantic_20261024/<experiment>/`. Một số tệp chỉ có khi PASS.', '',
        'Các kết quả đo mức đồng thuận với nhãn proxy suy từ sao, không phải độ chính xác trên human sentiment gold.', '', limits]
    (root / 'reports/p5_modern_tabular_models.md').write_text('\n'.join(p5) + '\n', encoding='utf-8')
    for phase, title in [('p6', 'transformer_benchmark'), ('p7', 'unified_benchmark')]:
        (root / f'reports/{phase}_{title}.md').write_text(
            f'# {phase.upper()} — trạng thái benchmark mới\n\nTrạng thái: NOT STARTED.\n\n'
            'BLOCKED: cổng P5 chưa PASS do E03 thiếu quyền tải checkpoint; E04 chưa chạy. Không dùng BERT body-only LEGACY thay cho E05 canonical title + body.\n\n'
            + next_action + '\n\nChưa có metrics, ranking đầy đủ hoặc error analysis mới của pha này.\n', encoding='utf-8')
    completion = ['# Báo cáo refactor bộ mô hình — 2026-10-24', '',
        '**Trạng thái tổng thể: BLOCKED; refactor chưa hoàn tất P0–P7.** Báo cáo phản ánh phần thực thi đã xác minh, không phải completion claim.', '',
        '## A. Trạng thái dự án', '',
        '| Pha | Trạng thái mới | Bằng chứng |', '|---|---|---|',
        '| P0 | PASS | p0_model_stack_refactor.md, environment JSON, 3 tests |',
        '| P1 | PASS / P1 REUSED AS-IS | hash raw/processed, metadata coverage, 47 tests |',
        '| P2 | PASS | đủ30K, labels/IDs/body/proxy mapping, whitelist; 40 tests |',
        '| P3 | PASS | readiness/length/truncation/storage/neutral/resource risks; 30 tests |',
        '| P4 | PASS | giữ split, frozen cache đủ30K, full BERT token reencode, isolation; 36 tests |',
        '| P5 | BLOCKED | E00/E01/E02 PASS; E03 license BLOCKED; E04 NOT STARTED |',
        '| P6 | NOT STARTED | chờ P5; BERT cũ body-only là LEGACY |',
        '| P7 | NOT STARTED | chờ P5/P6; không tạo ranking/error analysis giả |', '',
        '## B. Những gì giữ nguyên', '',
        'Hai raw nguồn Amazon (tổng ~7,79GB) được băm khớp manifest, không tải lại. Dataset30K/9080 sản phẩm; nhãn negative8259/neutral2631/positive19110. Split giữ seed42 và toàn bộ ô: train21000/6357 sản phẩm/5781-1842-13377; validation4500/1361/1239-395-2866; test4500/1362/1239-394-2867. Không cleaning/relabel/resplit, không dùng gold để train.', '',
        '53 model/metrics/prediction/config files lịch sử P5/P6 khớp output hashes (`model_stack_legacy_preservation.json`); không sửa lịch sử để hợp thức hóa code/document đã dịch.', '',
        '## C. Những gì thay đổi', '',
        'Danh sách active chuyển sang semantic benchmark trong configs/model.yaml. TF-IDF/LR/SVM/DT giữ LEGACY, không còn làm representation/model chính. Canonical title + body, frozen encoder pin revision, cache/mapping/labels/metadata/token riêng và whitelist fail closed. Bổ sung runner/validator cho P0/P1/P2/P3/P4/P5 và registry experiment E00–E05 trong semantic config. E05 mới được cấu hình nhưng chưa triển khai/chạy do cổng P5; không coi configuration là model hoàn chỉnh.', '',
        '## D. Dataset readiness', '',
        '30K tổng/21K train và đủ3lớp cho phép thử các model trên cùng dữ liệu; không bảo đảm chất lượng hoặc đủ VRAM cho TabPFN. Neutral1842 train, mất cân bằng cần so weighting trên validation. Title/body missingness và percentiles ở `p3_model_readiness.json`; gold sentiment độc lập hiện chưa có. Rating mapping là proxy, không sentiment gold.', '',
        '## E. Semantic encoder', '',
        f'Model: `{cfg["encoder"]["model"]}`, revision `{cfg["encoder"]["revision"]}`, dimension384, attention-mask mean pooling, L2 normalize, frozen FP32, batch32 CUDA, max_length256. Không dùng sentiment labels hoặc fine-tune encoder.', '',
        f'Mẫu train128 review: {benchmark["seconds"]:.6f}s; {benchmark["reviews_per_second"]:.2f} review/s; RSS peak {benchmark["peak_process_rss_bytes"]} byte; GPU allocated {benchmark["peak_gpu_allocated_bytes"]} byte, reserved {benchmark["peak_gpu_reserved_bytes"]} byte. Có warmup8; thời gian không gồm tải model. Đo một encoder, không phải cuộc thi nhiều encoder. Chọn vì nhỏ/gọn, 384chiều và chi phí sample phù hợp6GB. Truncation là giới hạn đã công bố.', '',
        '## F. Kết quả model thực đã chạy', '', table, '',
        'CSV đầy đủ gồm RAM/artifact size/latency: `model_stack_partial_results.csv`. NOT_MEASURED là chưa đo, không phải0. Majority chỉ sanity. Không đưa score BERT LEGACY vào bảng benchmark mới.', '',
        '## G. Model tốt nhất', '',
        'Chưa có best model của toàn benchmark. Trong hai model cạnh tranh đã hoàn tất, TabM được chọn bằng validation macro F1 cao hơn XGBoost; test macro/neutral F1 tương ứng có trong bảng. Đây là kết luận tạm cho hai model đã chạy, không kết luận TabM tốt hơn TabPFN/Transformer chưa được đánh giá. Runtime CPU XGBoost và GPU TabM khác thiết bị; xem tài nguyên đầy đủ trước quyết định triển khai.', '',
        '## H. Giới hạn và blocker', '', blocker_text, '', limits, '', next_action, '',
        '## I. Tệp thay đổi', '',
        'Tạo mới: `configs/semantic_benchmark.yaml`, `configs/modern_tabular.yaml`, bản sao `configs/model_legacy_20261024.yaml`; `src/preprocessing/{semantic,semantic_cache}.py`; `src/sentiment/{modern,tabpfn_versions}.py`; `scripts/{check_model_stack,revalidate_model_data,model_readiness,prepare_semantic,validate_semantic,train_modern,validate_modern,report_model_refactor}.py`; `tests/{test_semantic,test_semantic_cache,test_modern_smoke,test_model_stack_versions}.py`; `docs/MODEL_STACK_REFACTOR.md`; các báo cáo pha/completion, bằng chứng JSON/CSV và cache/model mới được tham chiếu.', '',
        'Sửa: `requirements.txt`, `configs/model.yaml`, `scripts/test_all.py`, `README.md`, `PLAN_AI.md`, `PLAN_HUMAN.md`, `docs/CODEX_HANDOFF.md`. Không xóa tệp. Legacy: configs/p4,p5,p6.yaml, scripts/train_p5,train_p6.py, model/preprocessing/metrics lịch sử giữ nguyên. Quan trọng không sửa: raw Amazon/SemEval, dataset sạch, split cũ, nhãn manual, model/dự đoán/metrics P5/P6 cũ.', '',
        'Repository ban đầu toàn bộ untracked; không dùng git reset/checkout và không tạo commit tự động. Danh sách thay đổi này ghi theo tác vụ, không giả là diff từ commit trước.', '',
        '## J. Kiểm thử và xác minh', '',
        f'Bằng chứng kiểm thử cuối: `{validation}`. Các lần chạy pha là tập con và có thể lặp lại, không cộng để thổi số tests.', '',
        '`python -m scripts.validate_semantic`: cache/hash/shape/finite/norm/order/label và token reencode đủ30K PASS. `python -m scripts.validate_modern E00_majority/E01_xgboost_embedding/E02_tabm_embedding`: artifact hashes/selection/metrics recomputation PASS, không predict test lại. XGBoost/TabM smoke fit/backward/reload thật trên fixture được đánh dấu rõ. TabPFN version resolution thật PASS; TabPFN inference smoke bị chặn bởi license, không thay bằng mock để tuyên bố PASS. Transformer smoke mới NOT STARTED; kiểm thử BERT legacy vẫn chạy riêng.', '',
        'Feature leakage tests từ chối rating/target/IDs/metadata; cache tests phát hiện corruption/reordering/config changes. Retry guard từ chối tái mở selection/test đã khóa và path traversal. Không chạy lại BERT legacy training/test prediction, không tạo human gold.', '',
        'Kết quả này đo mức đồng thuận với nhãn proxy suy từ sao, không phải độ chính xác trên human sentiment gold.']
    (root / 'reports/model_stack_refactor_completion.md').write_text('\n'.join(completion) + '\n', encoding='utf-8')
    print(json.dumps({'overall': 'BLOCKED', 'experiments': {k: v['status'] for k, v in results.items()}}, ensure_ascii=True))


if __name__ == '__main__':
    main()
