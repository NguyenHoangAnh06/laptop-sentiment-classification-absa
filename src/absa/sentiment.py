"""BERT ASC theo đúng aspect occurrence; standalone gold-aspect và API batch dùng chung."""
from contextlib import nullcontext
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader,Dataset
from transformers import AutoModelForSequenceClassification,AutoTokenizer,BertForSequenceClassification

from src.absa.extraction_data import FEATURES
from src.absa.sentiment_data import MARKERS,asc_tokenizer,encode_aspect,resolve_aspect_span
from src.evaluation.classification import LABELS,classification_metrics
from src.evaluation.error_diagnosis import file_hash
from src.sentiment.bert import collate_tokens,resolve_device


class AspectSentimentDataset(Dataset):
    """Một sample=sentence+target span; metadata/polarity gốc không đi vào model."""
    def __init__(self,records: list[dict],split: str):
        if not records or any(r['split']!=split for r in records): raise ValueError('ASC split/dataset không hợp lệ')
        if len({r['example_id'] for r in records})!=len(records): raise ValueError('Duplicate ASC example ID')
        labeled=[r.get('label_id') is not None for r in records]
        if any(labeled) and not all(labeled): raise ValueError('Không trộn labeled/unlabeled ASC')
        for r in records:
            if any(len(r[k])!=len(r['input_ids']) for k in FEATURES): raise ValueError('Token alignment ASC không hợp lệ')
            opening,closing=r.get('marker_ids',(1,2))
            if opening==closing or r['input_ids'].count(opening)!=1 or r['input_ids'].count(closing)!=1: raise ValueError('Thiếu/duplicate aspect markers')
            if r['input_ids'].index(opening)>=r['input_ids'].index(closing): raise ValueError('Aspect marker order không hợp lệ')
            if r.get('label_id') is not None and (type(r['label_id']) is not int or r['label_id'] not in range(3)):
                raise ValueError('ASC chỉ nhận label IDs0/1/2')
        self.records=records; self.split=split; self.lengths=[len(r['input_ids']) for r in records]

    def __len__(self): return len(self.records)

    def __getitem__(self,index):
        row=self.records[index]
        result={k:list(row[k]) for k in FEATURES}
        if row.get('label_id') is not None: result['labels']=row['label_id']
        return result


def predict_asc(model,records: list[dict],device: torch.device,*,batch_size: int,amp: bool=False) -> list[int]:
    if not records: return []
    dataset=AspectSentimentDataset(records,records[0]['split'])
    loader=DataLoader(dataset,batch_size=batch_size,shuffle=False,collate_fn=collate_tokens)
    predicted=[]; model.eval()
    with torch.inference_mode():
        for batch in loader:
            batch.pop('labels',None)
            context=torch.autocast('cuda',dtype=torch.float16) if amp and device.type=='cuda' else nullcontext()
            with context: logits=model(**{k:v.to(device) for k,v in batch.items()}).logits
            if not torch.isfinite(logits).all(): raise ValueError('ASC logits không hữu hạn')
            predicted.extend(logits.argmax(-1).cpu().tolist())
    return predicted


def evaluate_asc(model,records: list[dict],device: torch.device,*,batch_size: int,amp: bool=False) -> tuple[dict,list[dict]]:
    predicted=predict_asc(model,records,device,batch_size=batch_size,amp=amp)
    metrics=classification_metrics([r['label_id'] for r in records],predicted)
    saved=[]
    fields=('example_id','sentence_uid','sentence_id','original_split','split','source_file','text',
            'aspect','start','end','original_aspect_index','original_polarity','label','label_id')
    for row,label in zip(records,predicted):
        saved.append({**{k:row[k] for k in fields},'predicted_label_id':label,'predicted_sentiment':LABELS[label],
                      'confidence':None,'correct':label==row['label_id']})
    return metrics,saved


class AspectSentimentClassifier:
    """Tải ASC artifact; không giả tạo confidence từ logits chưa calibration."""
    def __init__(self,directory: Path,*,device: str='auto'):
        directory=Path(directory)
        self.metadata=json.loads((directory/'asc_metadata.json').read_text(encoding='utf-8'))
        if self.metadata['labels']!=list(LABELS) or self.metadata['markers']!=list(MARKERS):
            raise ValueError('Artifact không đúng contract ASC')
        if file_hash(directory/'tokenizer.json')!=self.metadata['tokenizer_sha256']: raise ValueError('ASC tokenizer hash không khớp')
        self.generic=self.metadata.get('tokenizer_backend')=='huggingface_auto'
        self.tokenizer=AutoTokenizer.from_pretrained(directory,local_files_only=True) if self.generic else asc_tokenizer(directory/'tokenizer.json')
        self.device=resolve_device(device)
        model_class=AutoModelForSequenceClassification if self.generic else BertForSequenceClassification
        self.model=model_class.from_pretrained(directory,local_files_only=True).to(self.device).eval()
        if self.model.config.id2label!=dict(enumerate(LABELS)): raise ValueError('ASC label mapping không đúng')

    def classify_many(self,text: str,aspects: list[dict],*,language: str='en') -> list[dict]:
        if language!='en': raise ValueError('ASC hiện chỉ hỗ trợ language=en')
        if not isinstance(text,str): raise ValueError('text phải là chuỗi')
        records=[]
        for index,a in enumerate(aspects):
            term=a['term']; start,end=resolve_aspect_span(text,term,a.get('start'),a.get('end'))
            if self.generic:
                from src.absa.sentiment_backbone import encode_record
                encoded=encode_record({'text':text,'aspect':term,'start':start,'end':end},self.tokenizer,self.metadata['max_length'])
            else:
                encoded=encode_aspect(text,term,start,end,self.tokenizer,self.metadata['max_length'])
            records.append({**encoded,'example_id':str(index),'split':'inference','label_id':None})
        labels=predict_asc(self.model,records,self.device,batch_size=16)
        return [{'aspect':a['term'],'sentiment':LABELS[label],'confidence':None} for a,label in zip(aspects,labels)]

    def classify_aspect_sentiment(self,text: str,aspect: str,start: int | None=None,end: int | None=None,*,language: str='en') -> dict:
        return self.classify_many(text,[{'term':aspect,'start':start,'end':end}],language=language)[0]
