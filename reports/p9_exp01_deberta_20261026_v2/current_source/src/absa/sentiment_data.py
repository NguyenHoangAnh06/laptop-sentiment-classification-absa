"""Gold-aspect ASC dùng split SemEval P8; bảo toàn polarity và occurrence offsets."""
from collections import Counter
import json
from pathlib import Path
import re

from tokenizers import AddedToken,Tokenizer
import yaml

from src.absa.extraction_data import canonical_aspects,load_records as load_p8_records,load_tokenizer
from src.config import PROJECT_ROOT
from src.data.semeval import read_semeval_sentences,write_semeval_jsonl
from src.evaluation.classification import LABELS
from src.evaluation.error_diagnosis import file_hash

MARKERS=('[unused0]','[unused1]')
POLARITIES=(*LABELS,'conflict')


def load_p9_config(path: Path | None=None) -> dict:
    cfg=yaml.safe_load((path or PROJECT_ROOT/'configs/p9_aspect_sentiment.yaml').read_text(encoding='utf-8'))
    if (cfg['labels']!=list(LABELS) or cfg['conflict_policy']!='exclude_preserve_original'
            or cfg['representation']!='occurrence_markers_single_sequence' or cfg['markers']!=list(MARKERS)):
        raise ValueError('Contract ASC ba lớp/markers/conflict không được hỗ trợ')
    stability=(cfg.get('experiment')=='P9-EXP01-STABILITY' and cfg.get('validation_only') is True
               and cfg['training']['loss_candidates'] in (['unweighted'],['balanced']))
    if cfg['max_length']<8 or (cfg['training']['loss_candidates']!=['unweighted','balanced'] and not stability):
        raise ValueError('Config length/loss candidates không hợp lệ')
    return cfg


def asc_tokenizer(source: Path) -> Tokenizer:
    """Đăng ký marker bằng reserved IDs hiện có, không resize vocab hoặc sửa tokenizer P8."""
    tokenizer=load_tokenizer(source)
    before=tokenizer.get_vocab_size()
    if [tokenizer.token_to_id(m) for m in MARKERS]!=[1,2]:
        raise ValueError('Tokenizer không có reserved marker IDs1/2')
    tokenizer.add_special_tokens([AddedToken(m,special=True,normalized=False) for m in MARKERS])
    if tokenizer.get_vocab_size()!=before: raise ValueError('Không được tăng vocabulary ngầm')
    return tokenizer


def marked_input(text: str,aspect: str,start: int,end: int) -> str:
    """Chèn marker bằng character offsets; không tìm occurrence bằng text.find."""
    if (not isinstance(text,str) or not isinstance(aspect,str) or not aspect.strip()
            or type(start) is not int or type(end) is not int or not 0<=start<end<=len(text)
            or text[start:end]!=aspect):
        raise ValueError('Aspect term/span không khớp text')
    if any(m in text for m in MARKERS): raise ValueError('Text chứa marker dành riêng cho ASC')
    return text[:start]+MARKERS[0]+text[start:end]+MARKERS[1]+text[end:]


def resolve_aspect_span(text: str,aspect: str,start: int | None,end: int | None) -> tuple[int,int]:
    """API thiếu offsets chỉ nhận occurrence duy nhất; repeated term bắt buộc chỉ rõ span."""
    if (start is None)!=(end is None): raise ValueError('Cần cung cấp cả start và end')
    if start is None:
        if not isinstance(text,str) or not isinstance(aspect,str) or not aspect.strip():
            raise ValueError('Text/aspect không hợp lệ')
        hits=[m.start() for m in re.finditer('(?='+re.escape(aspect)+')',text)]
        if len(hits)!=1: raise ValueError('Aspect thiếu hoặc có nhiều occurrence; cần offsets rõ ràng')
        start=hits[0]; end=start+len(aspect)
    marked_input(text,aspect,start,end)
    return start,end


def encode_aspect(text: str,aspect: str,start: int,end: int,tokenizer: Tokenizer,max_length: int) -> dict:
    marked=marked_input(text,aspect,start,end)
    encoded=tokenizer.encode(marked)
    if len(encoded.ids)>max_length: raise ValueError('ASC vượt max_length; không truncate aspect/context ngầm')
    if encoded.ids.count(1)!=1 or encoded.ids.count(2)!=1 or encoded.ids.index(1)>=encoded.ids.index(2):
        raise ValueError('Marker occurrence/tokenizer alignment không hợp lệ')
    return {'input_ids':encoded.ids,'attention_mask':encoded.attention_mask,'token_type_ids':encoded.type_ids,
            'tokens':encoded.tokens,'marked_text':marked}


def build_asc_samples(rows: list[dict],tokenizer: Tokenizer,max_length: int) -> tuple[list[dict],list[dict],dict]:
    examples=[]; excluded=[]; distribution=Counter(); seen=set(); lengths=[]
    for row in rows:
        if not row.get('sentence_id') or row['uid']!=f"{row['original_split']}:{row['sentence_id']}":
            raise ValueError('Sentence ID/UID không hợp lệ')
        aspects,_=canonical_aspects(row)
        by_index={a['original_aspect_index']:a for a in aspects}
        for index,original in enumerate(row['aspects']):
            polarity=original.get('polarity')
            if polarity not in POLARITIES: raise ValueError('Polarity thiếu/ngoài enum')
            aspect=by_index[index]
            aid=f"{row['uid']}:aspect:{index}"
            if aid in seen: raise ValueError('Duplicate annotation ID')
            seen.add(aid); distribution[polarity]+=1
            sample={'example_id':aid,'sentence_uid':row['uid'],'sentence_id':row['sentence_id'],
                    'original_split':row['original_split'],'split':row['split'],'source_file':row['source_file'],
                    'text':row['text'],'aspect':aspect['term'],'start':aspect['start'],'end':aspect['end'],
                    'original_aspect_index':index,'original_aspect':original,'original_polarity':polarity}
            if polarity=='conflict':
                excluded.append({**sample,'exclusion_reason':'conflict_not_in_three_class_contract; original retained'})
                continue
            encoded=encode_aspect(row['text'],aspect['term'],aspect['start'],aspect['end'],tokenizer,max_length)
            examples.append({**sample,**encoded,'label':polarity,'label_id':LABELS.index(polarity)})
            lengths.append(len(encoded['input_ids']))
    if not examples: raise ValueError('Không có gold-aspect ASC examples hợp lệ')
    return examples,excluded,{'source_sentences':len(rows),'original_aspect_entities':sum(distribution.values()),
                'original_polarity_counts':{p:distribution[p] for p in POLARITIES},
                'original_polarity_shares':{p:distribution[p]/sum(distribution.values()) for p in POLARITIES},
                'examples':len(examples),'excluded_conflict':len(excluded),
                'class_counts':{p:distribution[p] for p in LABELS},
                'class_shares':{p:distribution[p]/len(examples) for p in LABELS},
                'max_sequence_length':max(lengths),'truncated_examples':0,'integrity':'PASS'}


def prepare_p9(root: Path=PROJECT_ROOT,config_path: Path | None=None) -> dict:
    cfg=load_p9_config(config_path)
    p8_path=root/cfg['p8_manifest']; p8=json.loads(p8_path.read_text(encoding='utf-8'))
    p8_result=json.loads((root/cfg['p8_result']).read_text(encoding='utf-8'))
    if p8_result['status']!='TRAINING_AND_EVALUATION_COMPLETE' or p8['alignment']['unexplained_failures']:
        raise ValueError('P8 chưa accepted/validated')
    original={}
    for split,source in p8['sources'].items():
        if file_hash(root/source['xml'])!=source['xml_sha256'] or file_hash(root/source['jsonl'])!=source['jsonl_sha256']:
            raise ValueError('SemEval P1 source hash thay đổi')
        original[split]={r['sentence_id']:r for r in read_semeval_sentences(root/source['xml'],split)}
    tokenizer=asc_tokenizer(root/cfg['tokenizer_source'])
    output=root/cfg['data_directory']; output.mkdir(parents=True,exist_ok=True)
    token_path=output/'tokenizer.json'; payload=tokenizer.to_str(pretty=True)
    if token_path.exists() and token_path.read_text(encoding='utf-8')!=payload: raise ValueError('P9 tokenizer đã có khác config')
    token_path.write_text(payload,encoding='utf-8')
    manifest={'status':'PASS','version':cfg['version'],'config':cfg,'p8_manifest_sha256':file_hash(p8_path),
              'tokenizer_source_sha256':file_hash(root/cfg['tokenizer_source']),'tokenizer_sha256':file_hash(token_path),
              'p8_model_sha256':file_hash(root/p8_result['model_directory']/'model.safetensors'),
              'sources':p8['sources'],'files':{},'splits':{},'excluded_files':{},'sentence_split_ids':p8['split_ids'],
              'conflict_policy':'exclude supervised/standalone; preserve original metadata; never map to neutral',
              'representation':'[CLS] context_before [unused0] target_occurrence [unused1] context_after [SEP]; reserved IDs1/2, vocab unchanged',
              'leakage':{**p8['leakage'],'aspect_term_overlap_is_not_itself_leakage':True},
              'end_to_end_conflict_policy':cfg['end_to_end']['conflict_policy']}
    loaded={}; term_sets={}
    for split in ['train','validation','test']:
        rows=load_p8_records(root,p8,split); loaded[split]=rows
        for r in rows:
            raw=original[r['original_split']][r['sentence_id']]
            if r['text']!=raw['text'] or r['aspects']!=raw['aspects']:
                raise ValueError('P9 aspect source không khớp XML')
        samples,excluded,stats=build_asc_samples(rows,tokenizer,cfg['max_length'])
        manifest['splits'][split]=stats
        write_semeval_jsonl(output/f'{split}.jsonl',samples)
        write_semeval_jsonl(output/f'{split}_conflict_excluded.jsonl',excluded)
        manifest['files'][split]={'path':(output/f'{split}.jsonl').relative_to(root).as_posix(),'sha256':file_hash(output/f'{split}.jsonl')}
        manifest['excluded_files'][split]={'path':(output/f'{split}_conflict_excluded.jsonl').relative_to(root).as_posix(),'sha256':file_hash(output/f'{split}_conflict_excluded.jsonl')}
        term_sets[split]={r['aspect'].casefold() for r in samples}
    texts={s:{' '.join(r['text'].casefold().split()) for r in rows} for s,rows in loaded.items()}
    if texts['train']&texts['validation']: raise ValueError('Text leakage train–validation')
    manifest['leakage']['asc_term_overlap_counts']={a+'__'+b:len(term_sets[a]&term_sets[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}
    counts=manifest['splits']['train']['class_counts']; n=sum(counts.values())
    if not all(counts.values()): raise ValueError('Thiếu class trong train ASC')
    manifest['balanced_weights_train_only']={p:n/(len(LABELS)*counts[p]) for p in LABELS}
    path=output/'manifest.json'; payload=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')!=payload: raise ValueError('P9 manifest/config khác run cũ; dùng namespace mới')
    path.write_text(payload,encoding='utf-8')
    report=root/cfg['report_directory']; report.mkdir(parents=True,exist_ok=True)
    (report/'data_validation.json').write_text(payload,encoding='utf-8')
    return manifest


def load_asc_records(root: Path,manifest: dict,split: str) -> list[dict]:
    item=manifest['files'][split]; path=root/item['path']
    if file_hash(path)!=item['sha256']: raise ValueError('ASC dataset hash thay đổi')
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
