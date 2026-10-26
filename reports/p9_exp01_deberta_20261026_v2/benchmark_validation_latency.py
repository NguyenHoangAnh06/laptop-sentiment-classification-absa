"""Đo latency hai checkpoint trên cùng validation/batch; tuyệt đối không đọc test."""
import gc
import json
from pathlib import Path
import statistics
import time

import torch
from transformers import AutoModelForSequenceClassification

from src.absa.sentiment import predict_asc
from src.absa.sentiment_data import load_asc_records
from src.evaluation.error_diagnosis import file_hash

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).parent
torch.set_num_threads(2)
device=torch.device('cuda')
results={}; ids=None
for name,namespace in [('bert','p9_20261026'),('deberta','p9_exp01_deberta_20261026_v2')]:
    saved=json.loads((ROOT/f'reports/{namespace}/result.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/f'data/processed/{namespace}/manifest.json').read_text(encoding='utf-8'))
    rows=load_asc_records(ROOT,manifest,'validation')
    current=[r['example_id'] for r in rows]
    if ids is not None and ids!=current: raise ValueError('Validation IDs/order khác nhau')
    ids=current
    model=AutoModelForSequenceClassification.from_pretrained(ROOT/saved['model_directory'],local_files_only=True).to(device)
    predict_asc(model,rows,device,batch_size=16,amp=True)
    seconds=[]
    for _ in range(3):
        torch.cuda.synchronize(); tick=time.perf_counter()
        predictions=predict_asc(model,rows,device,batch_size=16,amp=True)
        torch.cuda.synchronize(); seconds.append(time.perf_counter()-tick)
    expected=[json.loads(line)['predicted_label_id'] for line in
              (ROOT/f'data/interim/{namespace}/validation_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    results[name]={'examples':len(rows),'batch_size':16,'warmup_full_passes':1,'measured_full_passes':3,
                   'seconds':seconds,'median_ms_per_aspect_from_tokens':statistics.median(seconds)/len(rows)*1000,
                   'predictions_identical_to_saved':predictions==expected,
                   'model_sha256':file_hash(ROOT/saved['model_directory']/'model.safetensors')}
    del model; gc.collect(); torch.cuda.empty_cache()
payload={'status':'COMPLETE','dataset':'validation_only_same314IDs','test_opened':False,
         'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,'fp16_autocast':True,'threads':2,
         'note':'Batched từ cached tokens, gồm collate/transfer/forward; không raw-text hoặc single-request latency',
         'results':results,'source_sha256':file_hash(Path(__file__))}
(REPORT/'validation_latency.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(payload),flush=True)
