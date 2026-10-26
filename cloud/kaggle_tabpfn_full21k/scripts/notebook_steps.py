"""Điều phối notebook; failure của một phiên bản không ngăn đóng gói phiên bản kia."""
from pathlib import Path
import subprocess
import sys
from common import load, write, sha


def full_after_probe(bundle, working, version):
    slug='v3' if version=='v3' else 'v35'
    probe=load(working/f'resource_probe_{slug}.json')
    out=working/f'tabpfn_{slug}_full21k'
    if out.exists(): raise ValueError('Output đã tồn tại; tạo phiên Kaggle mới để tránh ghi đè')
    if probe['status']!='PASS':
        out.mkdir()
        write(out/'run_metadata.json',{'status':'FULL21K_FAILED','requested_version':version,
              'reason':'Probe train-only thất bại; không chạy final/subsample.', 'test_evaluated':False})
        write(out/'hashes.json',{'run_metadata.json':sha(out/'run_metadata.json')})
        print(version+': FULL21K_FAILED (probe)')
        return
    result=subprocess.run([sys.executable,str(bundle/'scripts/run_tabpfn_cloud.py'),'--version',version,
                           '--data-root',str(bundle),'--output-dir',str(out)],capture_output=True)
    if not (out/'run_metadata.json').exists():
        out.mkdir(exist_ok=True)
        write(out/'run_metadata.json',{'status':'FULL21K_FAILED','requested_version':version,
              'reason':'Tiến trình kết thúc trước khi lưu metadata','exit_code':result.returncode})
    print(version+': '+load(out/'run_metadata.json')['status'])
