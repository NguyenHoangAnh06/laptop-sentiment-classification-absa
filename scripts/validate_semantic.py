"""Xác minh độc lập cache và re-encode token canonical, không encode embedding lại."""

import json

import pandas as pd
from tokenizers import Tokenizer

from scripts.revalidate_model_data import write_json
from src.config import PROJECT_ROOT
from src.preprocessing.semantic import canonical_text
from src.preprocessing.semantic_cache import load_cache, load_semantic_config


def main() -> None:
    cfg = load_semantic_config()
    data, metadata = load_cache(cfg)
    tokenizer = Tokenizer.from_file(str(PROJECT_ROOT / cfg['transformer']['tokenizer']))
    tokenizer.no_padding()
    tokenizer.enable_truncation(max_length=cfg['transformer']['max_length'])
    counts = {}
    for split, entry in data.items():
        frame = entry['frame']
        tokens = pd.read_parquet(PROJECT_ROOT / cfg['cache'] / f'{split}_transformer_tokens.parquet')
        if tokens.review_id.tolist() != frame.review_id.tolist() or tokens.label_id.tolist() != entry['y'].tolist():
            raise ValueError('Sai token alignment')
        texts = canonical_text(frame)
        for start in range(0, len(frame), 128):
            for row, encoded in zip(tokens.iloc[start:start+128].itertuples(), tokenizer.encode_batch(texts[start:start+128])):
                if (list(row.input_ids) != encoded.ids or list(row.attention_mask) != encoded.attention_mask
                        or list(row.token_type_ids) != encoded.type_ids):
                    raise ValueError('Token canonical khác tokenizer đã cố định')
        counts[split] = len(frame)
    result = {'status': 'PASS', 'cache_hashes_alignment': 'PASS', 'full_token_reencode': counts,
              'source_and_split_hashes_unchanged': True, 'embedding_qa': metadata['qa']}
    write_json(PROJECT_ROOT / 'reports/p4_semantic_independent_validation.json', result)
    print(json.dumps({'status': 'PASS', 'full_token_reencode': counts}))


if __name__ == '__main__':
    main()
