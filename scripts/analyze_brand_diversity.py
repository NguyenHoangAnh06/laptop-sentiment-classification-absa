"""Mô tả sự đa dạng về thương hiệu ở các ứng viên laptop đã lưu, không cần dọn dẹp hay cân bằng."""
import argparse
import json
from pathlib import Path
from src.data.brand_diversity import analyze_brands


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,default=Path('data/interim/feasibility/electronics_full_laptop_30k'))
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(analyze_brands(args.run_dir,args.output_dir),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
