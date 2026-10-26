"""Kiểm tra P0 và lưu bằng chứng môi trường, không tải dữ liệu/trọng số."""

import importlib
import importlib.metadata
import json
import platform
import subprocess
import sys

from src.config import PROJECT_ROOT
from src.sentiment.tabpfn_versions import version_resolution


def main() -> None:
    packages = {'torch': 'torch', 'transformers': 'transformers', 'xgboost': 'xgboost',
                'tabm': 'tabm', 'tabpfn': 'tabpfn',
                'sentence-transformers': 'sentence_transformers', 'scikit-learn': 'sklearn'}
    result = {'python': sys.version, 'platform': platform.platform(), 'packages': {}}
    for distribution, module in packages.items():
        importlib.import_module(module)
        result['packages'][distribution] = importlib.metadata.version(distribution)
    import torch
    result['cuda'] = torch.version.cuda
    result['cuda_available'] = torch.cuda.is_available()
    if torch.cuda.is_available():
        result['gpu'] = torch.cuda.get_device_name(0)
        result['gpu_memory_bytes'] = torch.cuda.get_device_properties(0).total_memory
    result['tabpfn_checkpoints'] = version_resolution()
    check = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    result['pip_check'] = check.stdout.strip()
    result['status'] = 'PASS' if check.returncode == 0 else 'FAILED'
    path = PROJECT_ROOT / 'reports/p0_model_stack_environment.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if check.returncode:
        raise SystemExit(check.returncode)


if __name__ == '__main__':
    main()
