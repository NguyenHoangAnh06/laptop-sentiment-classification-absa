"""Đóng gói allowlist artifacts; không thu gom cache/weights/secrets."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import zipfile
from common import ROOT, load, sha, secret_scan, write

RUN_FILES={'config.json','environment.json','run_metadata.json','validation_metrics.json','test_metrics.json',
'validation_predictions.csv','test_predictions.csv','confusion_matrix_validation.csv','confusion_matrix_test.csv',
'resource_usage.json','hashes.json','run_summary.md','selection_lock.json'}

def package(root, bundle):
    files=[]
    for version in ['v3','v35']:
        directory=root/f'tabpfn_{version}_full21k'
        if directory.exists():
            metadata=load(directory/'run_metadata.json')
            if metadata['status']=='PASS' and not all((directory/n).is_file() for n in RUN_FILES):
                raise ValueError('PASS thiếu artifacts: '+str(directory))
            if (directory/'hashes.json').exists():
                for name,digest in load(directory/'hashes.json').items():
                    if name not in RUN_FILES or sha(directory/name)!=digest:
                        raise ValueError('Result hash FAIL')
            files.extend(p for p in directory.glob('*') if p.name in RUN_FILES)
        probe=root/f'resource_probe_{version}.json'
        if probe.exists(): files.append(probe)
    if not files: raise ValueError('Không có kết quả/probe để đóng gói')
    for p in files:
        if p.suffix in {'.json','.md','.csv'}:
            # Scan từng file qua thư mục tạm chỉ chứa allowlist.
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as d:
                shutil.copyfile(p,Path(d)/p.name); secret_scan(Path(d))
    name='tabpfn_cloud_results_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.zip'
    out=root/name
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p,str(p.relative_to(root)))
        for name in ['bundle_manifest.json','hashes.json','label_mapping.json']:
            z.write(bundle/'metadata'/name,'bundle_metadata/'+name)
        z.writestr('archive_hashes.json',__import__('json').dumps({str(p.relative_to(root)):sha(p) for p in files},indent=2))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',type=Path,default=Path('/kaggle/working'))
    p.add_argument('--data-root',type=Path,default=ROOT); a=p.parse_args(); print(package(a.output_dir,a.data_root))
