"""Chạy đúng full21K, khóa cấu hình sau validation và trước test."""
import contextlib
import csv
import io
import time
from pathlib import Path
import numpy as np
import yaml
from common import parser, verify, write, sha, environment, model_for, cleanup
from metrics import classification_metrics, ResourceMonitor
from redaction import safe_error


def evaluate(model, values, out, split, batch):
    import torch
    x,y,ids=values
    started=time.perf_counter()
    prediction=np.concatenate([model.predict(np.array(x[i:i+batch])) for i in range(0,len(x),batch)]).astype('int64')
    torch.cuda.synchronize()
    elapsed=time.perf_counter()-started
    metrics=classification_metrics(y,prediction)
    metrics['balanced_accuracy']=float(np.mean([v['recall'] for v in metrics['per_class'].values()]))
    metrics['neutral_f1']=metrics['per_class']['neutral']['f1']
    write(out/f'{split}_metrics.json',metrics)
    with (out/f'{split}_predictions.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['review_id','y_true','y_pred']); w.writerows(zip(ids,y,prediction))
    with (out/f'confusion_matrix_{split}.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['actual/predicted','negative','neutral','positive'])
        w.writerows([label,*row] for label,row in zip(['negative','neutral','positive'],metrics['confusion_matrix']))
    return elapsed


def run(args):
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=False)
    result={'status':'FULL21K_FAILED','experiment':'C-E03' if args.version=='v3' else 'C-E04',
            'requested_version':args.version,'seed':42,'train_count':21000,'data_regime':'FULL','test_reused':True}
    model=None
    monitor=None
    resource={}
    try:
        data,manifest=verify(args.data_root)
        config=yaml.safe_load((args.data_root/'config/cloud_experiment.yaml').read_text(encoding='utf-8'))
        settings=config['model']; batch=config['prediction_batch_size']
        write(out/'environment.json',environment())
        write(out/'config.json',config)
        result.update(source_split_hashes=manifest['source_split_hashes'],
                      source_embedding_hashes=manifest['source_embedding_hashes'],
                      bundle_manifest_sha256=sha(args.data_root/'metadata/bundle_manifest.json'))
        import torch
        torch.manual_seed(42); np.random.seed(42); torch.set_num_threads(2)
        torch.cuda.reset_peak_memory_stats()
        with ResourceMonitor() as monitor:
            # Không chuyển stdout/stderr SDK ra log để tránh thông tin xác thực trong lỗi.
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                model,resolution=model_for(args.version,settings)
                result.update(resolution)
                start=time.perf_counter()
                model.fit(np.array(data['train'][0]),data['train'][1])
                torch.cuda.synchronize()
                resource['fit_seconds']=time.perf_counter()-start
                resource['validation_inference_seconds']=evaluate(model,data['validation'],out,'validation',batch)
                lock={'settings':settings,'seed':42,'train_count':21000,'resolution':resolution,
                      'validation_metrics_sha256':sha(out/'validation_metrics.json'),
                      'policy':'Cấu hình duy nhất định trước; không tuning từ test; reused test'}
                write(out/'selection_lock.json',lock)
                result['selection_lock_sha256']=sha(out/'selection_lock.json')
                resource['test_inference_seconds']=evaluate(model,data['test'],out,'test',batch)
        result['status']='PASS'
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=safe_error(exc),
                      NEXT_ACTION='Kiểm tra lỗi/tài nguyên train-only; không subsample final hoặc tune theo test.')
    finally:
        if monitor is not None:
            resource.update(peak_process_rss_bytes=monitor.peak_rss_bytes,wall_seconds=getattr(monitor,'seconds',None))
        try:
            import torch
            resource.update(peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                            peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
        except Exception: pass
        del model
        cleanup()
        write(out/'resource_usage.json',resource)
        write(out/'run_metadata.json',result)
        (out/'run_summary.md').write_text('# Kết quả cloud\n\n'+result['status']+'\n\nFull21000; seed42; reused test; không cập nhật P7 tự động.\n',encoding='utf-8')
        write(out/'hashes.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='hashes.json'})
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(run(parser(__doc__).parse_args()))
