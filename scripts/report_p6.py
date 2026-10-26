"""Tạo các đường cong P6 huấn luyện và đo đồng bằng chi phí chỉ từ bằng chứng đã lưu."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scripts.train_p5 import write_json
from src.config import PROJECT_ROOT
from src.evaluation.classification import LABELS


def report_p6(report: Path, root: Path = PROJECT_ROOT) -> dict:
    """Tạo chẩn đoán mới, không bao giờ tạo fit/select/re-predict từ kết quả kiểm thử."""
    config = json.loads((report / 'config.json').read_text(encoding='utf-8'))
    history = json.loads((report / 'training_history.json').read_text(encoding='utf-8'))
    benchmark = pd.read_csv(report / 'benchmark.csv').set_index('model')
    output = report.parent / f'{report.name}_analysis'
    if output.exists():
        raise FileExistsError('Analysis output exists; do not overwrite evidence')
    output.mkdir()
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
    for mode, color in [('unweighted', '#17649b'), ('balanced', '#d66d20')]:
        rows = [r for r in history if r['mode'] == mode]
        epochs = [r['epoch'] for r in rows]
        axes[0].plot(epochs, [r['train_loss'] for r in rows], 'o-', color=color, label=mode)
        axes[1].plot(epochs, [r['validation']['loss'] for r in rows], 'o-', color=color)
        axes[2].plot(epochs, [r['validation']['macro_f1'] for r in rows], 'o-', color=color)
    for ax, title in zip(axes, ['Hàm mục tiêu huấn luyện (khác trọng số)', 'Cross-entropy xác thực không trọng số', 'Macro F1 xác thực']):
        ax.set(title=title, xlabel='Vòng huấn luyện')
        ax.set_xticks(range(1, config['epochs'] + 1))
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    axes[2].axhline(benchmark.loc['logistic_regression', 'validation_macro_f1'], color='#555555', ls='--', lw=1)
    fig.savefig(output / 'training_curves.png', dpi=160)
    fig.savefig(output / 'training_curves.svg')
    plt.close(fig)
    bert = benchmark.loc['bert']
    deltas = []
    for model in ('majority', 'logistic_regression', 'linear_svm', 'decision_tree'):
        base = benchmark.loc[model]
        deltas.append({'baseline': model,
            'validation_macro_f1_delta': float(bert.validation_macro_f1 - base.validation_macro_f1),
            'test_macro_f1_delta': float(bert.macro_f1 - base.macro_f1),
            'accuracy_delta': float(bert.accuracy - base.accuracy),
            'neutral_f1_delta': float(bert.neutral_f1 - base.neutral_f1),
            'selected_fit_time_ratio': float(bert.training_seconds / base.training_seconds),
            'all_candidate_fit_time_ratio': float(bert.search_training_seconds / base.search_training_seconds),
            'observed_inference_latency_ratio': float(bert.inference_latency_ms_per_review / base.inference_latency_ms_per_review),
            'inference_artifact_size_ratio': float(bert.inference_artifact_bytes / base.inference_artifact_bytes)})
    pd.DataFrame(deltas).to_csv(output / 'cost_performance_deltas.csv', index=False)
    p4 = json.loads((root / config['p4_manifest']).read_text(encoding='utf-8'))
    frame = pd.read_parquet(root / p4['paths']['splits'] / 'test.parquet', columns=['review_id', 'text', 'label_id'])
    predictions = pd.read_parquet(root / 'artifacts/models' / config['output_suffix'] / 'test_predictions.parquet')
    if frame.review_id.tolist() != predictions.review_id.tolist():
        raise ValueError('Saved prediction IDs differ')
    lower = frame.text.str.lower()
    technical = lower.str.contains(r'\b(?:ram|ssd|ghz|processor|cpu|gpu|memory|storage|usb|hdmi)\b')
    emotion = lower.str.contains(r'\b(?:love|hate|great|excellent|terrible|disappointed|happy|good|bad)\b')
    mask = technical & ~emotion
    errors = predictions.label_id.ne(predictions.prediction_id)
    technical_slice = {'definition': 'technical lexical cue, no word from fixed emotion lexicon; heuristic only',
        'rows': int(mask.sum()), 'proxy_errors': int((mask & errors).sum()),
        'error_rate': float(errors[mask].mean()) if mask.any() else None,
        'human_verified': False}
    write_json(output / 'technical_slice.json', technical_slice)
    selected = json.loads((report / 'selection_lock.json').read_text(encoding='utf-8'))['selected']
    result = {'status': 'PASS', 'selected_mode': selected['mode'], 'best_epoch': selected['best_epoch'],
        'cost_ratios_caveat': 'Historical P5 CPU vs P6 device/workload; observed ratios, not architecture-only causality',
        'technical_slice': technical_slice, 'test_retuning': False, 'P7_phase_executed': False}
    write_json(output / 'summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=PROJECT_ROOT / 'reports/p6/p6_20261015')
    args = parser.parse_args()
    print(json.dumps(report_p6(args.report), indent=2))


if __name__ == '__main__':
    main()
