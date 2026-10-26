"""Chạy kiểm tra cuối và lưu số test quan sát được, không predict test lại."""

import json
import re
import subprocess
import sys

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file


def main():
    root = PROJECT_ROOT
    logs, commands = [], []
    for experiment in ['E00_majority', 'E01_xgboost_embedding', 'E02_tabm_embedding',
                       'E03_tabpfn_v3_embedding', 'E04_tabpfn_v35_embedding']:
        commands.append([sys.executable, '-m', 'scripts.validate_modern', experiment])
    commands.extend([[sys.executable, '-m', 'scripts.validate_transformer'],
                     [sys.executable, '-m', 'scripts.test_all'],
                     [sys.executable, '-m', 'pip', 'check'],
                     [sys.executable, '-m', 'compileall', '-q', 'src', 'scripts', 'tests']])
    for command in commands:
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace')
        output = proc.stdout + proc.stderr
        logs.append(output)
        print(json.dumps({'command': ' '.join(command[1:]), 'exit_code': proc.returncode}), flush=True)
        if proc.returncode:
            (root / 'reports/model_stack_final_validation_console.log').write_text('\n'.join(logs), encoding='utf-8')
            raise RuntimeError('Kiểm tra cuối thất bại; xem console log, không đánh dấu DONE')
    counts = [int(n) for n in re.findall(r'(\d+) passed', '\n'.join(logs))]
    assert len(counts) == 3
    preservation = {}
    for suffix, phase in [('p5_20261015', 'p5'), ('p6_20261015', 'p6')]:
        manifest = json.loads((root / f'reports/{phase}/{suffix}/manifest.json').read_text(encoding='utf-8'))
        mapping = manifest['output_sha256']
        mismatches = [name for name, digest in mapping.items() if sha256_file(root / name) != digest]
        assert not mismatches
        preservation[phase] = {'files': len(mapping), 'mismatches': mismatches}
    (root / 'reports/model_stack_legacy_preservation_final.json').write_text(json.dumps(preservation, indent=2), encoding='utf-8')
    (root / 'reports/model_stack_final_validation_console.log').write_text('\n'.join(logs), encoding='utf-8')
    summary = {'status': 'PASS', 'total_passed': sum(counts), 'groups': counts, 'failed': 0,
        'commands': [' '.join(c[1:]) for c in commands], 'legacy_preservation': preservation,
        'independent_metrics_alignment_selection': 'PASS', 'pip_check': 'PASS', 'compileall': 'PASS',
        'test_predictions_rerun': False, 'gold_created': False}
    (root / 'reports/model_stack_final_validation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
