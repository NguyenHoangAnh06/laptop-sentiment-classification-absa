"""Probe chỉ train; mỗi mức là một subprocess, dừng khi failure/timeout."""
import contextlib
import io
import subprocess
import sys
import time
import numpy as np
import yaml
from common import parser, verify, write, load, model_for, cleanup, environment
from metrics import ResourceMonitor
from redaction import safe_error


def worker(args):
    import torch, psutil
    result={'status':'FAIL','sample_count':args.samples,'requested_version':args.version,'split':'train'}
    model=None; monitor=None; started=time.perf_counter()
    try:
        data,_=verify(args.data_root)
        x,y,_=data['train']
        from sklearn.model_selection import train_test_split
        idx=np.arange(len(y))
        if args.samples<len(y): idx=np.sort(train_test_split(idx,train_size=args.samples,stratify=y,random_state=42)[0])
        config=yaml.safe_load((args.data_root/'config/cloud_experiment.yaml').read_text(encoding='utf-8'))
        torch.manual_seed(42); np.random.seed(42); torch.set_num_threads(2)
        torch.cuda.reset_peak_memory_stats()
        result.update(feature_dimension=x.shape[1],dtype=str(x.dtype),environment=environment())
        with ResourceMonitor() as monitor:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                model,resolution=model_for(args.version,config['model'])
                result.update(resolution)
                start=time.perf_counter(); model.fit(np.array(x[idx]),y[idx]); torch.cuda.synchronize()
                result['fit_seconds']=time.perf_counter()-start
                start=time.perf_counter(); model.predict(np.array(x[:config['prediction_batch_size']])); torch.cuda.synchronize()
                result['inference_seconds']=time.perf_counter()-start
        result['status']='PASS'
    except Exception as exc:
        result.update(exception_class=type(exc).__name__,exception_message=safe_error(exc))
    finally:
        result['elapsed_seconds']=time.perf_counter()-started
        result['process_rss_bytes']=psutil.Process().memory_info().rss
        result['peak_process_rss_bytes']=monitor.peak_rss_bytes if monitor else None
        if torch.cuda.is_available():
            result.update(gpu_allocated_bytes=torch.cuda.memory_allocated(),gpu_reserved_bytes=torch.cuda.memory_reserved(),
                          max_gpu_memory_bytes=torch.cuda.max_memory_allocated())
        del model; cleanup(); write(args.output_dir,result)
    return 0 if result['status']=='PASS' else 1


def main():
    p=parser(__doc__); p.add_argument('--samples',type=int,choices=[500,1000,2500,5000,10000,21000])
    p.add_argument('--timeout',type=int,default=3600)
    args=p.parse_args()
    if args.samples: return worker(args)
    verify(args.data_root)
    if args.output_dir.exists(): raise ValueError('Không ghi đè probe đã có')
    args.output_dir.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    for size in [500,1000,2500,5000,10000,21000]:
        part=args.output_dir.with_name(args.output_dir.stem+f'_{size}.json')
        try:
            process=subprocess.run([sys.executable,__file__,'--version',args.version,'--data-root',str(args.data_root),
                                   '--output-dir',str(part),'--samples',str(size)],capture_output=True,timeout=args.timeout)
            row=load(part) if part.exists() else {'status':'FAIL','sample_count':size,'exception_class':'WorkerExit','exit_code':process.returncode}
        except subprocess.TimeoutExpired:
            row={'status':'FAIL','sample_count':size,'exception_class':'TimeoutExpired'}
        results.append(row)
        write(args.output_dir,{'version':args.version,'status':'PASS' if size==21000 and row['status']=='PASS' else 'FULL21K_FAILED',
                              'train_only':True,'results':results})
        if part.exists(): part.unlink()
        if row['status']!='PASS': break
    # Failure được ghi; notebook vẫn có thể chạy phiên bản còn lại và đóng gói.
    return 0

if __name__=='__main__': raise SystemExit(main())
