"""SemEval laptop → WordPiece BIO, bảo toàn offsets/polarity/source và phân vùng gốc."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from tokenizers import Tokenizer
import yaml

from src.config import PROJECT_ROOT
from src.data.semeval import read_semeval_sentences, validate_semeval_sentences, write_semeval_jsonl
from src.evaluation.error_diagnosis import file_hash

LABELS = ('O','B-ASP','I-ASP')
LABEL_TO_ID = dict(zip(LABELS,range(3)))
FEATURES = ('input_ids','attention_mask','token_type_ids')


def load_p8_config(path: Path | None = None) -> dict:
    """Đọc contract một model ATE, không tái sử dụng sentiment checkpoint đã fine-tune."""
    cfg = yaml.safe_load((path or PROJECT_ROOT/'configs/p8_aspect_extraction.yaml').read_text(encoding='utf-8'))
    if cfg['labels'] != list(LABELS) or cfg['max_length'] < 4 or not 0 < cfg['validation_fraction'] < 1:
        raise ValueError('Config BIO/split không hợp lệ')
    if cfg['subword_policy'] != 'all_wordpieces_bio' or cfg['span_policy'] != 'trim_boundary_whitespace_preserve_original' or cfg['decode_policy'] != 'orphan_I_starts_entity':
        raise ValueError('Policy ATE chưa được hỗ trợ')
    return cfg


def load_tokenizer(path: Path) -> Tokenizer:
    """Dùng tokenizer đã pin; không padding/truncation ngầm."""
    tokenizer = Tokenizer.from_file(str(path))
    tokenizer.no_padding(); tokenizer.no_truncation()
    return tokenizer


def normalized_text(text: str) -> str:
    return ' '.join(text.casefold().split())


def split_train_validation(rows: list[dict], *, seed: int, fraction: float) -> dict[str,list[dict]]:
    """Nhóm text chuẩn hóa, chỉ lấy official train; không đưa test vào quyết định split."""
    if any(r['split']!='train' for r in rows) or len({r['sentence_id'] for r in rows}) != len(rows):
        raise ValueError('Split chỉ nhận official train với IDs duy nhất')
    rows = sorted(rows,key=lambda r:r['sentence_id'])
    groups = [normalized_text(r['text']) for r in rows]
    train, val = next(GroupShuffleSplit(n_splits=1,test_size=fraction,random_state=seed).split(rows,groups=groups))
    return {'train':[rows[i] for i in train], 'validation':[rows[i] for i in val]}


def canonical_aspects(row: dict) -> tuple[list[dict],list[dict]]:
    """Bỏ whitespace biên có căn cứ, lưu original aspects nguyên vẹn ở record nguồn."""
    if not row.get('sentence_id') or not isinstance(row.get('text'),str) or not row['text']:
        raise ValueError('Missing sentence ID/text')
    text = row['text']; result=[]; adjustments=[]
    for index,a in enumerate(row['aspects']):
        start,end = a['start'],a['end']
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or not a['term'] or text[start:end]!=a['term']:
            raise ValueError(f"Span không hợp lệ: {row['sentence_id']} aspect{index}")
        original_start,original_end = start,end
        while start < end and text[start].isspace(): start += 1
        while end > start and text[end-1].isspace(): end -= 1
        if start == end:
            raise ValueError('Aspect chỉ có whitespace')
        if any(max(start,b['start']) < min(end,b['end']) for b in result):
            raise ValueError('Overlapping/duplicate aspect annotations không thể biểu diễn BIO phẳng')
        aspect={'term':text[start:end],'start':start,'end':end,'original_aspect_index':index}
        result.append(aspect)
        if (start,end)!=(original_start,original_end):
            adjustments.append({'sentence_id':row['sentence_id'],'aspect_index':index,
                                'original_span':[original_start,original_end],'extraction_span':[start,end],
                                'reason':'trim_boundary_whitespace_only; original annotation preserved'})
    return sorted(result,key=lambda a:a['start']),adjustments


def validate_bio(labels: list[int]) -> None:
    previous = 0
    for label in labels:
        if label == -100:
            previous = 0
            continue
        if type(label) is not int or label not in range(3) or (label == 2 and previous not in (1,2)):
            raise ValueError('BIO transition/label không hợp lệ')
        previous=label


def decode_bio(text: str, offsets: list, labels: list[int], *, strict: bool = False) -> list[dict]:
    """Decode offsets, sửa orphan I thành B khi inference; không dùng text.find hoặc polarity."""
    if len(offsets)!=len(labels):
        raise ValueError('Offsets/labels không align')
    if strict: validate_bio(labels)
    result=[]; current=None; previous_end=0
    def flush():
        nonlocal current
        if current is not None:
            start,end=current
            result.append({'term':text[start:end],'start':start,'end':end,'score':None})
            current=None
    for (start,end),label in zip(offsets,labels):
        if type(label) is not int or label not in {-100,0,1,2}:
            raise ValueError('Nhãn decode ngoài enum')
        if (start,end)==(0,0):
            flush(); continue
        if not 0 <= start < end <= len(text) or start < previous_end:
            raise ValueError('Offset decode không hợp lệ')
        previous_end=end
        if label in {-100,0}: flush()
        elif label==1 or current is None:
            flush(); current=[start,end]
        else:
            current[1]=end
    flush()
    return result


def encode_sentence(row: dict, tokenizer: Tokenizer, *, split: str, max_length: int, source_file: str) -> tuple[dict,list]:
    aspects,adjustments = canonical_aspects(row)
    encoding=tokenizer.encode(row['text'])
    if len(encoding.ids)>max_length:
        raise ValueError(f"Câu vượt max_length; không truncate mất aspect: {row['sentence_id']}")
    labels=[-100 if a==b else 0 for a,b in encoding.offsets]
    for aspect in aspects:
        start,end=aspect['start'],aspect['end']
        hits=[i for i,(a,b) in enumerate(encoding.offsets) if max(a,start)<min(b,end)]
        if not hits or encoding.offsets[hits[0]][0]!=start or encoding.offsets[hits[-1]][1]!=end:
            raise ValueError(f"Unexplained token/span alignment: {row['sentence_id']} {start}:{end}")
        if hits!=list(range(hits[0],hits[-1]+1)):
            raise ValueError('Token span không liên tục')
        for j,i in enumerate(hits):
            if labels[i]!=0: raise ValueError('Overlapping BIO token spans')
            labels[i]=1 if j==0 else 2
    decoded=decode_bio(row['text'],encoding.offsets,labels,strict=True)
    if [(a['start'],a['end']) for a in decoded]!=[(a['start'],a['end']) for a in aspects]:
        raise ValueError('BIO round-trip không khớp character spans')
    record={**row,'original_split':row['split'],'split':split,
            'uid':f"{row['split']}:{row['sentence_id']}",'source_file':source_file,
            'tokens':encoding.tokens,'input_ids':encoding.ids,'attention_mask':encoding.attention_mask,
            'token_type_ids':encoding.type_ids,'offsets':[list(x) for x in encoding.offsets],
            'labels':labels,'bio_labels':[LABELS[l] if l!=-100 else 'IGNORE' for l in labels],
            'extraction_aspects':aspects}
    return record,adjustments


def describe_records(rows: list[dict]) -> dict:
    aspects=[a for r in rows for a in r['extraction_aspects']]
    terms=Counter(a['term'].casefold() for a in aspects)
    lengths=Counter(len(a['term'].split()) for a in aspects)
    subword_lengths=Counter()
    for row in rows:
        n=0
        for label in row['labels']+[0]:
            if label==2: n+=1
            else:
                if n: subword_lengths[n]+=1
                n=1 if label==1 else 0
    return {'sentences':len(rows),'aspect_entities':len(aspects),'unique_aspect_terms':len(terms),
            'aspects_per_sentence':len(aspects)/len(rows),'sentences_without_aspects':sum(not r['extraction_aspects'] for r in rows),
            'no_aspect_share':sum(not r['extraction_aspects'] for r in rows)/len(rows),
            'multiple_aspect_sentences':sum(len(r['extraction_aspects'])>1 for r in rows),
            'multiple_aspect_share':sum(len(r['extraction_aspects'])>1 for r in rows)/len(rows),
            'entity_word_length_counts':dict(sorted(lengths.items())),
            'entity_wordpiece_length_counts':dict(sorted(subword_lengths.items())),
            'max_sequence_length':max(len(r['input_ids']) for r in rows),
            'unigram_entities':sum(len(a['term'].split())==1 for a in aspects),
            'multiword_entities':sum(len(a['term'].split())>1 for a in aspects),
            'top_terms':terms.most_common(20)}


def prepare_p8(root: Path = PROJECT_ROOT, config_path: Path | None = None) -> dict:
    """Tái lập từ P1 XML+JSONL, từ chối ghi đè dataset/config khác và giữ official test."""
    cfg=load_p8_config(config_path)
    source={}; rows={}; source_audits={}
    for split in ['train','test']:
        xml=root/cfg['sources'][split+'_xml']; path=root/cfg['sources'][split+'_jsonl']
        parsed=read_semeval_sentences(xml,split)
        stored=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        if parsed!=stored or any(r['source']!='semeval2014_laptop' for r in parsed):
            raise ValueError('P1 JSONL không khớp XML/laptop provenance')
        audit=validate_semeval_sentences(parsed)
        if audit['duplicate_ids'] or any(d['kind']!='unsupported_or_missing_polarity' for d in audit['diagnostics']):
            raise ValueError('SemEval có lỗi span/ID chưa xử lý')
        rows[split]=parsed
        source_audits[split]={k:v for k,v in audit.items() if k not in {'duplicate_text_groups'}}
        source[split]={'xml':cfg['sources'][split+'_xml'],'xml_sha256':file_hash(xml),
                       'jsonl':cfg['sources'][split+'_jsonl'],'jsonl_sha256':file_hash(path)}
    splits=split_train_validation(rows['train'],seed=cfg['seed'],fraction=cfg['validation_fraction'])
    splits['test']=rows['test']
    tokenizer=load_tokenizer(root/cfg['tokenizer'])
    output=root/cfg['data_directory']; output.mkdir(parents=True,exist_ok=True)
    records={}; adjustments=[]
    for split,rs in splits.items():
        records[split]=[]
        for row in rs:
            record, changes=encode_sentence(row,tokenizer,split=split,max_length=cfg['max_length'],source_file=source[row['split']]['xml'])
            records[split].append(record)
            adjustments.extend({'uid':record['uid'],**c} for c in changes)
    if len(records['test'])!=len(rows['test']) or sum(len(r) for s,r in records.items() if s!='test')!=len(rows['train']):
        raise ValueError('Mất/thêm source sentences')
    train_texts={normalized_text(r['text']) for r in records['train']}
    val_texts={normalized_text(r['text']) for r in records['validation']}
    if train_texts & val_texts: raise ValueError('Duplicate text leakage train–validation')
    uid_sets={s:{r['uid'] for r in rs} for s,rs in records.items()}
    overlaps={a+'__'+b:sorted(uid_sets[a]&uid_sets[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}
    if any(overlaps.values()): raise ValueError('Qualified ID leakage')
    # Chỉ báo cáo overlap tự nhiên; không dùng test để sửa tập train hoặc chọn model.
    original_train_texts={normalized_text(r['text']) for r in rows['train']}
    overlap_rows=[{'test_uid':r['uid'],'original_sentence_id':r['sentence_id'],
                   'matching_train_uids':[q['uid'] for s in ['train','validation'] for q in records[s] if normalized_text(q['text'])==normalized_text(r['text'])]}
                  for r in records['test'] if normalized_text(r['text']) in original_train_texts]
    manifest={'status':'PASS','version':cfg['version'],'config':cfg,'sources':source,
              'tokenizer_sha256':file_hash(root/cfg['tokenizer']),'source_audits':source_audits,
              'alignment':{'status':'PASS','unexplained_failures':0,'explained_whitespace_adjustments':adjustments,
                           'sentences_over_max_length':0,'truncated_sentences':0},
              'splits':{s:describe_records(rs) for s,rs in records.items()},
              'split_ids':{s:[r['uid'] for r in rs] for s,rs in records.items()},
              'leakage':{'qualified_id_overlap':overlaps,'train_validation_normalized_text_overlap':0,
                         'raw_official_id_collisions':sorted({r['sentence_id'] for r in rows['train']}&{r['sentence_id'] for r in rows['test']}),
                         'official_cross_split_duplicate_texts':overlap_rows,
                         'policy':'Preserve official partitions and natural duplicate; IDs source-split-qualified; validation grouped by normalized train text; no test-driven deletion or tuning'},
              'polarity_policy':'preserve original including conflict; not a target; no mapping in P8',
              'metric_policy':'micro_exact_character_span_no_partial_credit; trim_boundary_whitespace_only; official test unchanged',
              'license_status':'NOT_VERIFIED; owner educational exception retained from P1; no new acquisition',
              'files':{}}
    existing=output/'manifest.json'
    for split,rs in records.items():
        write_semeval_jsonl(output/f'{split}.jsonl',rs)
        manifest['files'][split]={'path':(output/f'{split}.jsonl').relative_to(root).as_posix(),
                                  'sha256':file_hash(output/f'{split}.jsonl')}
    payload=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    if existing.exists() and existing.read_text(encoding='utf-8')!=payload:
        raise ValueError('Manifest/config hiện có khác; dùng namespace mới')
    existing.write_text(payload,encoding='utf-8')
    report=root/cfg['report_directory']; report.mkdir(parents=True,exist_ok=True)
    (report/'data_validation.json').write_text(payload,encoding='utf-8')
    return manifest


def load_records(root: Path, manifest: dict, split: str) -> list[dict]:
    """Hash check trước khi đọc từng split, test chỉ được runner mở sau selection lock."""
    file=manifest['files'][split]; path=root/file['path']
    if file_hash(path)!=file['sha256']: raise ValueError('Dataset BIO hash thay đổi')
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
