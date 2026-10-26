"""Tái xác minh P1/P2 lần lượt; chỉ đọc dữ liệu và ghi báo cáo mới."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.labeling import LABEL_TO_ID, rating_label


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def p1(root: Path) -> dict:
    """Kiểm tra hash nguồn đã tải và join sản phẩm với metadata đã lưu."""
    result = {'status': 'PASS', 'phase': 'P1 REUSED AS-IS', 'raw_sources': {}}
    for name in ('Electronics.jsonl.gz', 'meta_Electronics.jsonl.gz'):
        path = root / 'data/raw/amazon' / name
        manifest = json.loads(path.with_name(path.name + '.manifest.json').read_text(encoding='utf-8'))
        actual = sha256_file(path)
        if actual != manifest['sha256']:
            raise ValueError(f'Hash nguồn không khớp: {name}')
        result['raw_sources'][name] = {'bytes': path.stat().st_size, 'sha256': actual,
                                       'manifest': manifest}
    source = root / 'data/processed/laptop_reviews.parquet'
    manifest = json.loads((root / 'data/interim/p2/20261009_final/manifest.json').read_text(encoding='utf-8'))
    if sha256_file(source) != manifest['clean_parquet_sha256']:
        raise ValueError('Hash dataset khác P2 manifest')
    frame = pd.read_parquet(source)
    metadata = pd.read_csv(root / 'reports/tables/p1_brand_diversity_v1/products.csv', keep_default_na=False)
    if not set(frame.parent_asin) <= set(metadata.product_id):
        raise ValueError('Sản phẩm thiếu metadata đã xác minh')
    qa = [root / 'reports/tables/p1_owner_approval_20261009.json',
          root / 'reports/p1_qa_v2_completion_20261009.md',
          root / 'reports/tables/p1_semeval_owner_exception_20261009.json']
    for path in qa:
        if not path.is_file():
            raise ValueError(f'Thiếu bằng chứng: {path.relative_to(root)}')
    result.update(dataset_sha256=sha256_file(source), rows=len(frame), products=frame.parent_asin.nunique(),
                  product_metadata_coverage='PASS', qa_artifacts=[str(p.relative_to(root)) for p in qa],
                  laptop_scope='REPORTED: QA được chủ dự án chấp nhận; không gán nhãn thủ công mới',
                  limitations='Giữ giới hạn QA hỗ trợ/thiên lệch chọn mẫu; SemEval license NOT_VERIFIED theo ngoại lệ cũ')
    return result


def p2(root: Path) -> dict:
    """Xác minh nhãn, missingness và duplicates; không sửa hoặc relabel."""
    prior = json.loads((root / 'reports/p1_revalidation_for_new_models.json').read_text(encoding='utf-8'))
    if prior['status'] != 'PASS':
        raise ValueError('P1 chưa PASS')
    source = root / 'data/processed/laptop_reviews.parquet'
    if sha256_file(source) != prior['dataset_sha256']:
        raise ValueError('Dataset thay đổi sau P1')
    frame = pd.read_parquet(source)
    expected = frame.rating.map(lambda v: rating_label(int(v)))
    checks = {'rows_30000': len(frame) == 30000,
              'valid_ratings': frame.rating.isin([1, 2, 3, 4, 5]).all(),
              'labels_match_rating': expected.equals(frame.sentiment),
              'label_ids': frame.sentiment.map(LABEL_TO_ID).equals(frame.label_id),
              'proxy_provenance': frame.label_provenance.eq('rating-derived proxy').all(),
              'unique_review_id': not frame.review_id.duplicated().any(),
              'unique_clean_body': not frame.text.duplicated().any(),
              'body_nonempty': frame.text.notna().all() and frame.text.str.strip().ne('').all(),
              'english': frame.language.eq('en').all()}
    result = {'status': 'PASS' if all(checks.values()) else 'FAILED',
              'checks': {k: bool(v) for k, v in checks.items()},
              'counts': {k: int(v) for k, v in frame.sentiment.value_counts().items()},
              'missing': {k: int(v) for k, v in frame.isna().sum().items()},
              'text_characters_min_max': [int(frame.text.str.len().min()), int(frame.text.str.len().max())],
              'dataset_sha256': sha256_file(source), 'relabelled': False, 'gold_used': False}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['p1', 'p2'])
    args = parser.parse_args()
    name = f'{args.phase}_revalidation_for_new_models'
    result = globals()[args.phase](PROJECT_ROOT)
    write_json(PROJECT_ROOT / f'reports/{name}.json', result)
    text = (f'# {args.phase.upper()} — tái xác minh dữ liệu\n\nTrạng thái: {result["status"]}\n\n'
            + ('P1 REUSED AS-IS. Không tải/lọc lại; hash hai nguồn khớp manifest và toàn bộ sản phẩm có trong metadata đã lưu.\n\n' if args.phase == 'p1' else
               'Nhãn đại diện suy từ số sao, không phải human sentiment gold. Không làm sạch/relabel lại.\n\n')
            + f'Bằng chứng: `{name}.json`.\n\n'
            + 'Các trường rating/stars/score/label/target và ID không được làm feature. Pipeline mới chỉ nhận văn bản title/body, rồi dense embedding; metadata lưu riêng.\n\n'
            + 'Giới hạn: chỉ laptop; nhiễu nhãn từ số sao; thay đổi nền tảng/phong cách SemEval–Amazon; gold thủ công nhỏ, hiện chưa có.\n')
    (PROJECT_ROOT / f'reports/{name}.md').write_text(text, encoding='utf-8')
    print(json.dumps({'phase': args.phase, 'status': result['status']}, ensure_ascii=True))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
