"""Khôi phục snapshot source BERT trước extension; chỉ nhận bytes khớp SHA256 frozen."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=Path(__file__).parent/'previous_canonical_source'
expected=json.loads((ROOT/'reports/p9_20261026/validation.json').read_text(encoding='utf-8'))['source_sha256']


def replace(text,old,new):
    if old not in text: raise ValueError('Không tìm thấy đoạn extension cần đảo: '+old[:100])
    return text.replace(old,new,1)


def restore(name,text):
    if name=='src/absa/sentiment_data.py':
        text=replace(text,"    stability=(cfg.get('experiment')=='P9-EXP01-STABILITY' and cfg.get('validation_only') is True\n               and cfg['training']['loss_candidates'] in (['unweighted'],['balanced']))\n    if cfg['max_length']<8 or (cfg['training']['loss_candidates']!=['unweighted','balanced'] and not stability):",
                     "    if cfg['max_length']<8 or cfg['training']['loss_candidates']!=['unweighted','balanced']:")
    elif name=='src/absa/sentiment.py':
        text=replace(text,'from transformers import AutoModelForSequenceClassification,AutoTokenizer,BertForSequenceClassification','from transformers import BertForSequenceClassification')
        text=replace(text,"            opening,closing=r.get('marker_ids',(1,2))\n            if opening==closing or r['input_ids'].count(opening)!=1 or r['input_ids'].count(closing)!=1: raise ValueError('Thiếu/duplicate aspect markers')\n            if r['input_ids'].index(opening)>=r['input_ids'].index(closing): raise ValueError('Aspect marker order không hợp lệ')",
                     "            if r['input_ids'].count(1)!=1 or r['input_ids'].count(2)!=1: raise ValueError('Thiếu/duplicate aspect markers')\n            if r['input_ids'].index(1)>=r['input_ids'].index(2): raise ValueError('Aspect marker order không hợp lệ')")
        text=replace(text,"        self.generic=self.metadata.get('tokenizer_backend')=='huggingface_auto'\n        self.tokenizer=AutoTokenizer.from_pretrained(directory,local_files_only=True) if self.generic else asc_tokenizer(directory/'tokenizer.json')\n        self.device=resolve_device(device)\n        model_class=AutoModelForSequenceClassification if self.generic else BertForSequenceClassification\n        self.model=model_class.from_pretrained(directory,local_files_only=True).to(self.device).eval()",
                     "        self.tokenizer=asc_tokenizer(directory/'tokenizer.json'); self.device=resolve_device(device)\n        self.model=BertForSequenceClassification.from_pretrained(directory,local_files_only=True).to(self.device).eval()")
        text=replace(text,"            if self.generic:\n                from src.absa.sentiment_backbone import encode_record\n                encoded=encode_record({'text':text,'aspect':term,'start':start,'end':end},self.tokenizer,self.metadata['max_length'])\n            else:\n                encoded=encode_aspect(text,term,start,end,self.tokenizer,self.metadata['max_length'])",
                     "            encoded=encode_aspect(text,term,start,end,self.tokenizer,self.metadata['max_length'])")
    elif name=='scripts/evaluate_p9_end_to_end.py':
        text=replace(text,'from transformers import AutoModelForSequenceClassification,AutoTokenizer,BertForSequenceClassification','from transformers import BertForSequenceClassification')
        text=replace(text,'tokenizer,max_length: int,*,encoder=encode_aspect)','tokenizer,max_length: int)')
        text=replace(text,"            encoded=encoder(row['text']","            encoded=encode_aspect(row['text']")
        text=replace(text,"def evaluate_end_to_end(root: Path=PROJECT_ROOT,*,config_path: Path | None=None) -> dict:\n    cfg=load_p9_config(config_path or root/'configs/p9_aspect_sentiment.yaml')",
                     "def evaluate_end_to_end(root: Path=PROJECT_ROOT) -> dict:\n    cfg=load_p9_config(root/'configs/p9_aspect_sentiment.yaml')")
        begin=text.index('    encoder=encode_aspect\n'); end=text.index('    summary=',begin)
        text=text[:begin]+"    tokenizer=asc_tokenizer(chosen/'tokenizer.json')\n    model=BertForSequenceClassification.from_pretrained(chosen,local_files_only=True).to(device)\n"+text[end:]
        text=replace(text,",cfg['max_length'],encoder=encoder)",",cfg['max_length'])")
    elif name=='scripts/train_p9.py':
        text=replace(text,'from transformers import AutoConfig,AutoModelForSequenceClassification,BertConfig,BertForSequenceClassification,get_linear_schedule_with_warmup','from transformers import BertConfig,BertForSequenceClassification,get_linear_schedule_with_warmup')
        text=replace(text,"    if cfg.get('experiment'):\n        shutil.copy2(tokenizer.parent/'tokenizer_config.json',directory/'tokenizer_config.json')\n",'')
        text=replace(text,"'confidence':'null_uncalibrated',\n               **({'backbone':cfg['pretrained_model'],'revision':cfg['revision'],\n                   'tokenizer_revision':cfg['tokenizer_revision'],'tokenizer_backend':'huggingface_auto'} if cfg.get('experiment') else {})})",
                     "'confidence':'null_uncalibrated'})")
        text=replace(text,"def run(*,resume: bool=False,root: Path=PROJECT_ROOT,config_path: Path | None=None) -> dict:\n    cfg=load_p9_config(config_path or root/'configs/p9_aspect_sentiment.yaml'); tc=cfg['training']\n    model_class=AutoModelForSequenceClassification if cfg.get('experiment') else BertForSequenceClassification\n    config_class=AutoConfig if cfg.get('experiment') else BertConfig",
                     "def run(*,resume: bool=False,root: Path=PROJECT_ROOT) -> dict:\n    cfg=load_p9_config(root/'configs/p9_aspect_sentiment.yaml'); tc=cfg['training']")
        text=replace(text,"cfg.get('pretrained_filename','model.safetensors')","'model.safetensors'")
        text=replace(text,'mc=config_class.from_pretrained','mc=BertConfig.from_pretrained')
        begin=text.index('            model=model_class.from_pretrained('); end=text.index("            if tc['gradient_checkpointing']",begin)
        text=text[:begin]+"            model=BertForSequenceClassification.from_pretrained(mode_out/'last' if resume_mode else source.parent,\n                  config=mc,local_files_only=True,attn_implementation='sdpa').to(device)\n"+text[end:]
        text=replace(text,'        model=model_class.from_pretrained(chosen','        model=BertForSequenceClassification.from_pretrained(chosen')
        begin=text.index("        if cfg.get('validation_only'):\n"); end=text.index("        test=load_asc_records",begin)
        text=text[:begin]+text[end:]
    elif name=='tests/test_p9_data.py':
        text=text[:text.index('\ndef test_paired_backbone_predictions_require_same_gold_and_ids():')]
    elif name=='tests/test_p9_model.py':
        text=text[:text.index('\ndef test_deberta_occurrence_markers_forward_reload_cpu(tmp_path):')]
    return text


manifest={}
for name,digest in expected.items():
    raw=(ROOT/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest:
        text=restore(name,raw.decode('utf-8').replace('\r\n','\n'))
        candidates=[]
        for suffix in ['', '\n', '\n\n', '\n\n\n']:
            candidate=text.rstrip('\n')+suffix
            candidates.extend([candidate.encode('utf-8'),candidate.replace('\n','\r\n').encode('utf-8')])
        raw=next((c for c in candidates if hashlib.sha256(c).hexdigest()==digest),None)
        if raw is None: raise ValueError('Không tái lập đúng hash frozen: '+name)
    target=OUTPUT/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    manifest[name]=digest
(OUTPUT/'manifest.json').write_text(json.dumps({'status':'VERIFIED_EXACT_FROZEN_SOURCE','sha256':manifest,
    'method':'Đảo chỉ các chỉnh sửa của tác vụ hiện tại; chỉ lưu bytes nếu SHA256 khớp validation BERT frozen, không tạo lịch sử giả'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_files':len(manifest),'status':'PASS'}))
