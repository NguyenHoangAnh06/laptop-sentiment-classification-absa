"""Chạy thử nghiệm ngân sách dữ liệu và thử nghiệm Torch trong các quy trình Python mới riêng biệt.

Nhập Torch trong quá trình thu thập pytest vượt quá trần RSS của quy trình pha dữ liệu trước đó. Sự cô lập duy trì những biện pháp bảo vệ và kiểm tra đó mà không cần tăng ngân sách.
"""

import subprocess
import sys

from src.config import PROJECT_ROOT


def main() -> None:
    for args in (['tests', '--ignore=tests/test_p6.py', '--ignore=tests/test_model_stack_versions.py',
                  '--ignore=tests/test_modern_smoke.py', '--ignore=tests/test_p8_model.py',
                  '--ignore=tests/test_p9_model.py'],
                 ['tests/test_p6.py', 'tests/test_p8_model.py', 'tests/test_p9_model.py'],
                 ['tests/test_model_stack_versions.py', 'tests/test_modern_smoke.py']):
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', *args], cwd=PROJECT_ROOT, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
