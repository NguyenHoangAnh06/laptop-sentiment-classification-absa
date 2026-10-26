"""BERT token classifier và API trích xuất aspect tường minh cho P9 sử dụng sau."""
from contextlib import nullcontext
import json
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertForTokenClassification

from src.absa.extraction_data import FEATURES, LABELS, decode_bio, load_tokenizer, validate_bio
from src.evaluation.aspect_extraction import entity_metrics
from src.evaluation.error_diagnosis import file_hash
from src.sentiment.bert import resolve_device


class AspectDataset(Dataset):
    """Chỉ đưa token/labels vào model, không đưa polarity/ID/metadata."""

    def __init__(self, records: list[dict], split: str):
        if not records or split not in {'train','validation','test'}:
            raise ValueError('Cần split không rỗng')
        self.records=records; self.split=split
        self.lengths=[len(r['input_ids']) for r in records]
        if len({r['uid'] for r in records})!=len(records): raise ValueError('Duplicate UID')
        for row in records:
            if row['split']!=split or any(len(row[key])!=len(row['labels']) for key in FEATURES):
                raise ValueError('Dataset token/split alignment không hợp lệ')
            validate_bio(row['labels'])
            if any(l!=-100 for l,o in zip(row['labels'],row['offsets']) if o[0]==o[1]):
                raise ValueError('Special token phải được ignore trong loss')

    def __len__(self): return len(self.records)

    def __getitem__(self,index):
        return {key:list(self.records[index][key]) for key in (*FEATURES,'labels')}


def collate_ate(rows: list[dict]) -> dict[str,torch.Tensor]:
    """Dynamic right-padding; padding và special tokens không đóng góp loss."""
    if not rows: raise ValueError('Empty batch')
    width=max(len(r['input_ids']) for r in rows)
    return {key:torch.tensor([r[key]+[(-100 if key=='labels' else 0)]*(width-len(r[key]))
                              for r in rows],dtype=torch.long) for key in (*FEATURES,'labels')}


def evaluate_ate(model, records: list[dict], device: torch.device, *, batch_size: int, amp: bool=False) -> tuple[dict,list[dict]]:
    """Suy luận theo thứ tự records rồi tính entity chính xác; token accuracy chỉ bổ trợ."""
    dataset=AspectDataset(records,records[0]['split'])
    loader=DataLoader(dataset,batch_size=batch_size,collate_fn=collate_ate,shuffle=False)
    predictions=[]; correct=token_n=0; orphan_count=0; cursor=0
    model.eval()
    with torch.inference_mode():
        for batch in loader:
            labels=batch.pop('labels')
            context=torch.autocast('cuda',dtype=torch.float16) if amp and device.type=='cuda' else nullcontext()
            with context:
                logits=model(**{k:v.to(device) for k,v in batch.items()}).logits
            output=logits.argmax(-1).cpu()
            mask=labels!=-100
            correct+=int(((output==labels)&mask).sum()); token_n+=int(mask.sum())
            for tags in output.tolist():
                row=records[cursor]; cursor+=1
                tags=tags[:len(row['input_ids'])]
                previous=0
                for tag,offset in zip(tags,row['offsets']):
                    if offset[0]==offset[1]: previous=0; continue
                    orphan_count+=tag==2 and previous not in (1,2)
                    previous=tag
                aspects=decode_bio(row['text'],row['offsets'],tags)
                predictions.append({'uid':row['uid'],'sentence_id':row['sentence_id'],
                                    'original_split':row['original_split'],'split':row['split'],
                                    'source_file':row['source_file'],'text':row['text'],
                                    'gold_aspects':row['extraction_aspects'],'predicted_aspects':aspects,
                                    'predicted_label_ids':tags})
    metrics={**entity_metrics(predictions),'token_accuracy':correct/token_n if token_n else 0.,
             'labeled_wordpieces':token_n,'orphan_I_predictions_repaired':orphan_count}
    return metrics,predictions


class AspectExtractor:
    """Tải artifact P8 một lần; confidence null vì chưa calibration."""

    def __init__(self, directory: Path, *, device: str='auto'):
        directory=Path(directory)
        self.metadata=json.loads((directory/'extraction_metadata.json').read_text(encoding='utf-8'))
        if self.metadata['labels']!=list(LABELS) or self.metadata['decode_policy']!='orphan_I_starts_entity':
            raise ValueError('Artifact không đúng contract ATE')
        tokenizer_path=directory/'tokenizer.json'
        if file_hash(tokenizer_path)!=self.metadata['tokenizer_sha256']:
            raise ValueError('Tokenizer hash không khớp artifact')
        self.tokenizer=load_tokenizer(tokenizer_path)
        self.device=resolve_device(device)
        self.model=BertForTokenClassification.from_pretrained(directory,local_files_only=True).to(self.device).eval()
        if self.model.config.id2label!=dict(enumerate(LABELS)):
            raise ValueError('Label mapping của model không đúng BIO')

    def extract_aspects(self, text: str, *, language: str='en') -> list[dict]:
        """Trả term/start/end/score=null; từ chối câu quá dài thay vì truncate ngầm."""
        if language!='en': raise ValueError('Chỉ hỗ trợ language=en trong P8')
        if not isinstance(text,str): raise ValueError('text phải là chuỗi')
        if not text.strip(): return []
        encoded=self.tokenizer.encode(text)
        if len(encoded.ids)>self.metadata['max_length']:
            raise ValueError('Câu vượt max_length ATE; chưa hỗ trợ window trong API P8')
        inputs={key:torch.tensor([values],device=self.device) for key,values in
                zip(FEATURES,[encoded.ids,encoded.attention_mask,encoded.type_ids])}
        with torch.inference_mode(): tags=self.model(**inputs).logits.argmax(-1)[0].tolist()
        return decode_bio(text,encoded.offsets,tags)
