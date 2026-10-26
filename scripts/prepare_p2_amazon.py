"""Chạy P2 chỉ được Amazon phê duyệt mà không có phân chia hoặc mô hình huấn luyện."""

import json
from pathlib import Path

from src.config import PROJECT_ROOT, load_config
from src.data.p2_pipeline import run_p2


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('configs/p2.yaml'))
    args = parser.parse_args()
    import yaml
    with args.config.open(encoding='utf-8') as handle:
        config = yaml.safe_load(handle)
    result = run_p2(config, load_config('data'), root=PROJECT_ROOT)
    print(json.dumps({k:result[k] for k in ('selection','proxy_counts','elapsed_seconds','resources')},indent=2))


if __name__ == '__main__':
    main()
