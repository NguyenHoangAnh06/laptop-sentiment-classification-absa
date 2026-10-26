"""Thực thi P3 notebook trong một dự án mới-Python kernel, không cần đăng ký toàn cầu."""

import argparse
import json
from pathlib import Path
import sys
import tempfile

from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient
import nbformat

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('reports/p3/20261009_verified/03_laptop_eda.executed.ipynb'))
    args=parser.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to((PROJECT_ROOT/'reports').resolve()):
        raise ValueError('Notebook output must stay under reports')
    if output.exists():raise FileExistsError('Refuse to overwrite executed notebook')
    source=PROJECT_ROOT/'notebooks/03_laptop_eda.ipynb'
    nb=nbformat.read(source,as_version=4)
    with tempfile.TemporaryDirectory(prefix='laptop_p3_kernel_') as temporary:
        task_temp=Path(temporary).resolve()
        assert task_temp.parent==Path(tempfile.gettempdir()).resolve()
        spec=task_temp/'project-p3';spec.mkdir()
        (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                                  'display_name':'Project P3','language':'python'}),encoding='utf-8')
        manager=KernelManager(kernel_name='project-p3',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(task_temp)]))
        NotebookClient(nb,km=manager,timeout=180,resources={'metadata':{'path':str(PROJECT_ROOT)}}).execute()
    nbformat.validate(nb)
    output.parent.mkdir(parents=True,exist_ok=True)
    nbformat.write(nb,output)
    check={'notebook_execution':'PASS','fresh_project_kernel':True,
           'code_cells':sum(c.cell_type=='code' for c in nb.cells),
           'input_sha256':sha256_file(source),'executed_sha256':sha256_file(output),
           'splits_created':False,'models_trained':False}
    (output.parent/'notebook_validation.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(check,indent=2))


if __name__=='__main__':main()
