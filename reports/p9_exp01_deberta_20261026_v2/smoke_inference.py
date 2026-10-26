"""Smoke CPU từ một câu validation; không phải đo official test hay tạo gold mới."""
from collections import defaultdict
import json
from pathlib import Path

import torch

from src.absa.extraction import AspectExtractor
from src.absa.sentiment import AspectSentimentClassifier
from src.inference.absa import AspectAnalyzer

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).parent
torch.set_num_threads(2)
result=json.loads((REPORT/'result.json').read_text(encoding='utf-8'))
rows=[json.loads(line) for line in (ROOT/'data/processed/p9_exp01_deberta_20261026_v2/validation.jsonl').read_text(encoding='utf-8').splitlines()]
groups=defaultdict(list)
for row in rows: groups[row['sentence_uid']].append(row)
examples=next(part for part in groups.values() if len({r['label'] for r in part})>1)
text=examples[0]['text']
classifier=AspectSentimentClassifier(ROOT/result['model_directory'],device='cpu')
pred=classifier.classify_many(text,[{'term':r['aspect'],'start':r['start'],'end':r['end']} for r in examples])
assert len(pred)==len(examples) and all(p['sentiment'] in ['negative','neutral','positive'] and p['confidence'] is None for p in pred)
assert classifier.classify_many(text,[])==[]
try:
    classifier.classify_many(text,[],language='vi')
except ValueError:
    unsupported=True
else:
    raise ValueError('Không được âm thầm nhận language=vi')
p8=json.loads((ROOT/'reports/p8_20261026/result.json').read_text(encoding='utf-8'))
extractor=AspectExtractor(ROOT/p8['model_directory'],device='cpu')
aspects=AspectAnalyzer(extractor,classifier).analyze_aspects(text)
assert all(a['term']==text[a['start']:a['end']] and a['sentiment'] in ['negative','neutral','positive']
           and a['aspect_score'] is None and a['sentiment_score'] is None for a in aspects)
payload={'status':'PASS','device':'cpu','source_split':'validation','sentence_uid':examples[0]['sentence_uid'],
         'gold_aspect_inputs':len(examples),'gold_aspect_output_labels':[p['sentiment'] for p in pred],
         'pipeline_aspects':len(aspects),'confidence_null':True,'empty_aspects_pass':True,
         'unsupported_vi_rejected':unsupported,'p8_retrained':False,'test_opened':False}
(REPORT/'inference_smoke.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(payload),flush=True)
