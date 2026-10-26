"""Tiện ích độc lập cho gói Kaggle; không đọc dữ liệu ngoài bundle."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import sys

# CLI tiếng Việt hoạt động cả khi stdout Windows được pipe.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ('train', 'validation', 'test')
COUNTS = (21000, 4500, 4500)
LABELS = {'negative': 0, 'neutral': 1, 'positive': 2}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def secret_scan(root):
    patterns = [r'TABPFN_TOKEN\s*=\s*["\x27]?[A-Za-z0-9_-]{12,}',
                r'(?i)bearer\s+[A-Za-z0-9._-]{12,}', r'\bhf_[A-Za-z0-9]{20,}',
                r'\bsk-[A-Za-z0-9_-]{20,}', r'(?i)(?:api[_-]?key|authorization)\s*[:=]\s*["\x27][A-Za-z0-9_-]{16,}']
    for path in Path(root).rglob('*'):
        if path.is_file() and path.suffix not in ('.zip', '.pyc'):
            content = path.read_bytes().decode('utf-8', errors='ignore')
            if any(re.search(p, content) for p in patterns):
                raise ValueError('Secret scan FAIL: '+str(path.relative_to(root)))

def verify(root):
    root = Path(root)
    manifest = load(root/'metadata/bundle_manifest.json')
    expected = load(root/'config/expected_manifest.json')
    if sha(root/'metadata/bundle_manifest.json') != expected['manifest_sha256']:
        raise ValueError('Manifest không khớp anchor')
    if load(root/'metadata/hashes.json') != manifest['bundle_file_hashes']:
        raise ValueError('Hash index không khớp manifest')
    if manifest['label_mapping'] != LABELS: raise ValueError('Sai label mapping')
    if load(root/'metadata/label_mapping.json') != LABELS: raise ValueError('Sai mapping file')
    for name, digest in manifest['bundle_file_hashes'].items():
        path = root/name
        if not path.resolve().is_relative_to(root.resolve()) or sha(path) != digest:
            raise ValueError('Hash FAIL: '+name)
    data, seen = {}, set()
    for split, count in zip(SPLITS, COUNTS):
        x=np.load(root/f'data/embeddings/{split}.npy', allow_pickle=False, mmap_mode='r')
        y=np.load(root/f'data/labels/{split}.npy', allow_pickle=False)
        ids=np.load(root/f'data/ids/{split}.npy', allow_pickle=False)
        if x.shape != (count, manifest['embedding_dimension']) or str(x.dtype) != manifest['embedding_dtype']:
            raise ValueError('Shape/dtype FAIL: '+split)
        if not np.isfinite(x).all() or not np.any(x) or np.any(np.linalg.norm(x,axis=1)==0):
            raise ValueError('Embedding không hợp lệ')
        if y.shape != (count,) or y.dtype.kind not in 'iu' or ids.shape != (count,) or ids.dtype.kind != 'U' or set(y.tolist()) != {0,1,2}:
            raise ValueError('Label/ID shape FAIL')
        current=set(ids.tolist())
        if len(current)!=count or seen & current or any(not i.strip() for i in current):
            raise ValueError('ID trùng/rỗng/overlap')
        seen.update(current)
        # Hash ba mảng cố định và chứng cứ export từ mapping gốc bảo toàn alignment.
        if manifest['splits'][split]['alignment_verified'] is not True: raise ValueError('Thiếu alignment')
        data[split]=(x,y,ids)
    secret_scan(root)
    return data, manifest

def parser(description):
    p=argparse.ArgumentParser(description=description)
    p.add_argument('--data-root',type=Path,default=ROOT)
    p.add_argument('--version',choices=['v3','v3_5'],required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    return p

def environment():
    import psutil, torch
    return {'python':platform.python_version(), 'packages':{n:importlib.metadata.version(n) for n in ['torch','tabpfn','numpy','scikit-learn']},
            'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'cpu_count':os.cpu_count(),'ram_total_bytes':psutil.virtual_memory().total}

def model_for(version, settings):
    import torch
    from versions import make_tabpfn, version_resolution
    if not os.environ.get('TABPFN_TOKEN','').strip(): raise RuntimeError('Thiếu Kaggle Secret TABPFN_TOKEN')
    if not torch.cuda.is_available(): raise RuntimeError('Cần bật GPU trước khi chạy')
    names={'v3':'E03_tabpfn_v3_embedding','v3_5':'E04_tabpfn_v35_embedding'}
    paths=version_resolution()
    model=make_tabpfn(names[version],device='cuda',random_state=42,**settings)
    if Path(model.model_path).name != Path(paths[names[version]]).name:
        raise ValueError('Checkpoint thực tế không khớp requested version')
    resolution={'requested_version': 'V3' if version=='v3' else 'V3_5',
                'resolved_version':'V3' if version=='v3' else 'V3_5',
                'checkpoint':Path(paths[names[version]]).name,'tabpfn_package_version':'9.2.0'}
    return model,resolution

def cleanup():
    import gc, torch
    gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()
