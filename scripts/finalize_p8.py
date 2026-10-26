"""Xác minh độc lập P8, tạo báo cáo và nghiệm thu sau toàn bộ kiểm thử; không train/predict test."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

from src.absa.extraction_data import decode_bio,load_p8_config,load_records,prepare_p8
from src.config import PROJECT_ROOT
from src.evaluation.aspect_extraction import entity_metrics,error_analysis
from src.evaluation.error_diagnosis import file_hash


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def table(frame: pd.DataFrame) -> str:
    def cell(v): return f'{v:.6f}' if isinstance(v,float) else str(v)
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(cell(v) for v in r)+' |' for r in frame.itertuples(index=False,name=None)])


def verify_predictions(rows: list[dict], predictions: list[dict]) -> dict:
    """Nguồn gold/order/text và BIO predicted phải khớp; metric không nhận label từ file lạ."""
    if [r['uid'] for r in rows]!=[r['uid'] for r in predictions]:
        raise ValueError('Prediction UID/order không khớp dataset')
    token_correct=token_n=0
    for row,pred in zip(rows,predictions):
        if any(row[k]!=pred[k] for k in ['sentence_id','original_split','split','text','source_file']):
            raise ValueError('Prediction metadata/text không khớp source')
        if row['extraction_aspects']!=pred['gold_aspects']:
            raise ValueError('Prediction gold bị thay đổi')
        if len(pred['predicted_label_ids'])!=len(row['input_ids']):
            raise ValueError('Prediction labels không align')
        if decode_bio(row['text'],row['offsets'],pred['predicted_label_ids'])!=pred['predicted_aspects']:
            raise ValueError('Prediction spans không khớp decode từ labels')
        for gold,label in zip(row['labels'],pred['predicted_label_ids']):
            if gold!=-100:
                token_n+=1; token_correct+=gold==label
    return {**entity_metrics(predictions),'token_accuracy':token_correct/token_n,'labeled_wordpieces':token_n}


def run_checks(root: Path, report: Path) -> dict:
    """Quan sát suite thực tế; tách tiến trình Torch để giữ các trần RSS cũ."""
    logs=[]; commands=[]
    for args in [['-B','-m','scripts.test_all'],['-m','pip','check'],['-m','compileall','-q','src','scripts','tests']]:
        proc=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(proc.stdout+proc.stderr)
        commands.append({'command':'.venv/Scripts/python.exe '+' '.join(args),'exit_code':proc.returncode})
        (report/'test_console.log').write_text('\n'.join(logs),encoding='utf-8')
        print(json.dumps(commands[-1]),flush=True)
        if proc.returncode:
            write_json(report/'validation.json',{'status':'FAIL','commands':commands,
                       'BLOCKED':'Kiểm thử/check thất bại; xem test_console.log','NEXT_ACTION':'Sửa lỗi rồi chạy lại checks; không nghiệm thu P8.'})
            raise RuntimeError('Kiểm thử P8 thất bại')
    counts=[int(n) for n in re.findall(r'(\d+) passed',logs[0])]
    if len(counts)!=3 or sum(counts)<321:
        raise ValueError('Không quan sát đủ các nhóm test cũ và P8')
    paths=['src/absa/extraction.py','src/absa/extraction_data.py','src/evaluation/aspect_extraction.py',
           'scripts/prepare_p8.py','scripts/train_p8.py','scripts/finalize_p8.py','scripts/test_all.py',
           'tests/test_p8_data.py','tests/test_p8_model.py']
    result={'status':'PASS','total_passed':sum(counts),'failed':0,'groups':counts,'previous_tests':321,
            'new_tests':sum(counts)-321,'commands':commands,'pip_check':'PASS','compileall':'PASS',
            'source_sha256':{p:file_hash(root/p) for p in paths},
            'console_log':(report/'test_console.log').relative_to(root).as_posix()}
    write_json(report/'validation.json',result)
    return result


def finalize(root: Path=PROJECT_ROOT, *, checks: bool=False) -> dict:
    cfg=load_p8_config(root/'configs/p8_aspect_extraction.yaml')
    report=root/cfg['report_directory']; out=root/cfg['model_directory']; local=root/cfg['prediction_directory']
    result=json.loads((report/'result.json').read_text(encoding='utf-8'))
    if result['status']!='TRAINING_AND_EVALUATION_COMPLETE': raise ValueError('Chưa có training/evaluation hoàn tất')
    # Tái lập data, đồng thời đối chiếu raw/XML/JSONL với BIO và manifest đã khóa.
    manifest=prepare_p8(root,root/'configs/p8_aspect_extraction.yaml')
    identity=json.loads((report/'training_identity.json').read_text(encoding='utf-8'))
    if identity['config']!=cfg or identity['data_manifest_sha256']!=file_hash(root/cfg['data_directory']/'manifest.json'):
        raise ValueError('Config/data thay đổi sau training')
    if any(file_hash(root/p)!=h for p,h in identity['source_sha256'].items()):
        raise ValueError('Training implementation thay đổi sau run')
    lock=json.loads((report/'selection_lock.json').read_text(encoding='utf-8'))
    history=json.loads((report/'history.json').read_text(encoding='utf-8'))
    chosen=max(history,key=lambda r:r['validation']['entity_f1'])
    if (chosen['epoch']!=lock['selected_epoch'] or lock['test_used_for_selection']
            or lock['selected_value']!=chosen['validation']['entity_f1'] or not lock['selection_complete_before_test']):
        raise ValueError('Model selection không khớp validation history')
    if (file_hash(out/'best/model.safetensors')!=lock['model_sha256']
            or file_hash(report/'selection_lock.json')!=result['selection_lock_sha256']
            or file_hash(report/'history.json')!=lock['history_sha256']
            or file_hash(report/'training_identity.json')!=lock['training_identity_sha256']):
        raise ValueError('Checkpoint/selection/history identity hash thay đổi')
    datasets={s:load_records(root,manifest,s) for s in ['train','validation','test']}
    train_terms=Counter(a['term'].casefold() for r in datasets['train'] for a in r['extraction_aspects'])
    independent={}; errors={}; predictions={}
    for split in ['validation','test']:
        predictions[split]=[json.loads(line) for line in (local/f'{split}_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
        metrics=verify_predictions(datasets[split],predictions[split])
        if any(abs(value-result[split][key])>1e-12 for key,value in metrics.items() if isinstance(value,(int,float))):
            raise ValueError('Metric độc lập không khớp result')
        if split=='validation' and metrics['entity_f1']!=chosen['validation']['entity_f1']:
            raise ValueError('Validation score không khớp checkpoint đã chọn')
        independent[split]=metrics
        analysis=error_analysis(predictions[split],train_terms)
        # Full examples chỉ nằm local, không đưa review text vào report có thể chia sẻ.
        write_json(local/f'{split}_errors.json',analysis)
        errors[split]={k:v for k,v in analysis.items() if k!='examples'}
    duplicate_ids={r['test_uid'] for r in manifest['leakage']['official_cross_split_duplicate_texts']}
    clean=[r for r in predictions['test'] if r['uid'] not in duplicate_ids]
    independent['test_excluding_natural_duplicate_supplementary_only']=entity_metrics(clean)
    stats=[]; term_rows=[]; length_rows=[]
    for split,values in manifest['splits'].items():
        stats.append({'split':split,**{k:v for k,v in values.items() if not isinstance(v,(dict,list))}})
        term_rows.extend({'split':split,'term':t,'count':n} for t,n in values['top_terms'])
        for kind in ['entity_word_length_counts','entity_wordpiece_length_counts']:
            length_rows.extend({'split':split,'unit':kind,'length':int(k),'count':v} for k,v in values[kind].items())
    pd.DataFrame(stats).to_csv(report/'aspect_statistics.csv',index=False)
    pd.DataFrame(term_rows).to_csv(report/'top_aspect_terms.csv',index=False)
    pd.DataFrame(length_rows).to_csv(report/'entity_lengths.csv',index=False)
    pd.DataFrame([{'split':s,**a['counts']} for s,a in errors.items()]).to_csv(report/'error_counts.csv',index=False)
    write_json(report/'error_summary.json',errors)
    # Giữ nguyên toàn bộ artifact khoa học P0–P7; chỉ PLAN/README/HANDOFF được đổi trạng thái.
    preserved=json.loads((root/'reports/p8_preservation_before.json').read_text(encoding='utf-8'))
    changed=[p for p,h in preserved.items() if not (root/p).is_file() or file_hash(root/p)!=h]
    if changed: raise ValueError('P0–P7/raw artifacts thay đổi: '+str(changed))
    preservation={'status':'PASS','files_verified_unchanged':len(preserved),'mismatches':[],
                  'canonical_metric_csv_sha256':file_hash(root/'reports/p7_unified_results.csv')}
    write_json(report/'preservation.json',preservation)
    write_json(report/'independent_evaluation.json',{'status':'PASS','metrics':independent,
               'predictions_rerun':False,'selection_verified':True,'reload_verified_by_runner':result['reload_validation_predictions_identical'],
               'model_sha256':lock['model_sha256'],'prediction_sha256':{s:file_hash(local/f'{s}_predictions.jsonl') for s in predictions}})
    if checks: validation=run_checks(root,report)
    else: validation=json.loads((report/'validation.json').read_text(encoding='utf-8')) if (report/'validation.json').exists() else {'status':'PENDING'}
    if validation['status']=='PASS' and any(file_hash(root/p)!=h for p,h in validation['source_sha256'].items()):
        raise ValueError('Source thay đổi sau tests, cần chạy lại --run-checks')
    # Smoke API trên validation bằng CPU, không mở thêm một lượt official test inference.
    smoke_path=report/'inference_smoke.json'
    if not smoke_path.exists():
        import torch
        from src.absa.extraction import AspectExtractor
        torch.set_num_threads(2)
        extractor=AspectExtractor(out/'best',device='cpu')
        sample=next(r for r in datasets['validation'] if r['extraction_aspects'])
        extracted=extractor.extract_aspects(sample['text'])
        if any(a['term']!=sample['text'][a['start']:a['end']] or a['score'] is not None for a in extracted):
            raise ValueError('API extraction contract không hợp lệ')
        write_json(smoke_path,{'status':'PASS','device':'cpu','validation_uid':sample['uid'],
                   'aspect_count':len(extracted),'span_text_roundtrip':True,'score_is_null':True,
                   'official_test_inference':False,'checkpoint_sha256':lock['model_sha256']})
    smoke=json.loads(smoke_path.read_text(encoding='utf-8'))
    if smoke['status']!='PASS' or smoke['checkpoint_sha256']!=lock['model_sha256']:
        raise ValueError('Smoke artifact không khớp model')
    acceptance={'status':'DONE' if validation['status']=='PASS' else 'NOT_DONE_PENDING_TESTS',
                'readiness':'READY FOR P9' if validation['status']=='PASS' else 'NOT_READY',
                'date':'2026-10-26','tasks':{t:'PASS' for t in ['P8-T01','P8-T02','P8-T03','P8-T04']},
                'alignment':manifest['alignment'],'natural_official_overlap_disclosed':manifest['leakage'],
                'validation':independent['validation'],'official_test':independent['test'],
                'test_used_for_tuning':False,'canonical_metrics_changed':False,'amazon_dataset_changed':False,
                'p9_implemented':False,'tests':validation,'preservation':preservation,
                'limitations':['SemEval license/source NOT_VERIFIED with owner exception',
                               'one natural official train/test duplicate retained',
                               'one train-only whitespace-boundary adjustment, original preserved',
                               'single seed; CUDA attention backward not guaranteed bitwise deterministic',
                               'SemEval-to-Amazon shift; small independent P10 human gold remains pending',
                               'no calibrated confidence; API rejects overlength sentences'],
                'NEXT_ACTION':'Dừng tại READY FOR P9; không train ASC hoặc nối end-to-end ABSA.'}
    write_json(report/'acceptance.json',acceptance)
    write_report(root,cfg,manifest,result,history,independent,errors,validation,preservation,acceptance)
    return acceptance


def write_report(root: Path,cfg: dict,manifest: dict,result: dict,history: list,
                 metrics: dict,errors: dict,validation: dict,preservation: dict,acceptance: dict) -> None:
    """Báo cáo canonical từ artifacts thật; không hard-code kết quả train/test."""
    report=root/cfg['report_directory']; tc=cfg['training']
    data=pd.read_csv(report/'aspect_statistics.csv')
    performance=pd.DataFrame([{'split':s,**{k:m[k] for k in ['sentences','gold_entities','predicted_entities',
                                'true_positive','false_positive','false_negative','entity_precision','entity_recall','entity_f1']}}
                              for s,m in metrics.items()])
    history_table=pd.DataFrame([{'epoch':r['epoch'],'train_sentences':r['train_sentences'],
                                 'mean_batch_loss':r['mean_batch_loss'],'validation_precision':r['validation']['entity_precision'],
                                 'validation_recall':r['validation']['entity_recall'],'validation_f1':r['validation']['entity_f1'],
                                 'training_seconds':r['training_seconds'],'validation_seconds':r['validation_seconds']} for r in history])
    error_table=pd.DataFrame([{'split':s,**v['counts']} for s,v in errors.items()])
    counts=errors['test']['counts']; test=metrics['test']
    missed_single=test['false_negative']-counts['multiword_missed']
    single_n=test['gold_entities']-counts['multiword_gold']
    missed_frequent=test['false_negative']-counts['rare_missed']
    frequent_n=test['gold_entities']-counts['rare_gold']
    insights=(f"Official test: {counts['multiword_missed']}/{counts['multiword_gold']} multi-word entities bị miss "
              f"({counts['multiword_missed']/counts['multiword_gold']:.2%}), so với {missed_single}/{single_n} unigram "
              f"({missed_single/single_n:.2%}). Rare/unseen terms miss {counts['rare_missed']}/{counts['rare_gold']} "
              f"({counts['rare_missed']/counts['rare_gold']:.2%}), frequent terms miss {missed_frequent}/{frequent_n} "
              f"({missed_frequent/frequent_n:.2%}). Boundary errors chạm {counts['boundary_gold_entities']}/{test['false_negative']} "
              f"gold FN và {counts['boundary_predicted_entities']}/{test['false_positive']} predicted FP. "
              f"Câu nhiều aspect có lỗi {counts['multiple_aspect_sentences_with_error']}/{counts['multiple_aspect_sentences']}; "
              f"long phrases miss {counts['long_phrase_missed']}/{counts['long_phrase_gold']}. "
              "Các nhóm này có thể chồng lấn và có liên hệ với độ khó, không phải các nguyên nhân nhân quả độc lập.")
    paths={
        'BIO và split IDs':cfg['data_directory']+'/manifest.json',
        'Model/tokenizer/config tốt nhất':cfg['model_directory']+'/best/',
        'Last model/optimizer/RNG để resume':cfg['model_directory']+'/training_state.pt',
        'Config/source identity':cfg['report_directory']+'/training_identity.json',
        'History':cfg['report_directory']+'/history.json',
        'Selection lock':cfg['report_directory']+'/selection_lock.json',
        'Validation/test metrics':cfg['report_directory']+'/{validation,test}_metrics.json',
        'Predictions và full error examples local':cfg['prediction_directory']+'/{validation,test}_predictions.jsonl',
        'Xác minh độc lập':cfg['report_directory']+'/independent_evaluation.json',
        'Bằng chứng test':cfg['report_directory']+'/validation.json',
        'Bảo toàn P0–P7':cfg['report_directory']+'/preservation.json',
        'Nghiệm thu':cfg['report_directory']+'/acceptance.json'}
    lines=['# P8 — ABSA Aspect Term Extraction cho laptop','',
           f"**P8: {acceptance['status']} — {acceptance['readiness']}.** Chỉ trích xuất aspect term tường minh; không triển khai aspect sentiment/P9.",'',
           '## 1. Mục tiêu','',
           'Xây dựng pipeline SemEval laptop → WordPiece BIO → BERT token classifier → character spans, với metric entity nghiêm ngặt và artifacts tái lập. Không đặt ngưỡng F1 nghiệm thu giả; không sửa test hoặc tune sau test. Sentiment canonical P0–P7 và Amazon30K giữ nguyên.','',
           '## 2. Dataset','',
           'Dùng SemEval-2014 Task4 **Laptop**, XML do người dùng cung cấp từ P1 và JSONL chuẩn hóa hiện có. Đây là phân vùng train/test mang tên official trong bộ nguồn local; SHA256 xác nhận byte local, không chứng thực độc lập nguồn chính thức. Source/license vẫn NOT_VERIFIED theo ngoại lệ giáo dục của chủ sở hữu ở P1; không acquisition hoặc chấp nhận điều khoản mới. Không dùng Restaurant/domain khác/Amazon30K để train ATE.','',
           table(pd.DataFrame([{'original_split':s,'sentences':a['sentences'],'aspect_terms':a['aspect_terms'],
                               'no_aspect_sentences':a['sentences_without_aspects']} for s,a in manifest['source_audits'].items()])), '',
           table(data),'',
           'Phân phối độ dài entity theo whitespace words và WordPiece: `entity_lengths.csv`; top20 aspect terms mỗi split: `top_aspect_terms.csv`. Casefold chỉ phục vụ đếm term/nhóm split; không thay text hoặc offsets vào model. Câu không aspect được giữ với toàn O trên tokens không đặc biệt.','',
           '## 3. Parse SemEval và bảo toàn nguồn','',
           'Dùng lại `src/data/semeval.py` và schema P1: sentence_id, text, split, aspects(term/start/end/polarity/xml_attributes). So sánh JSONL với parser XML theo toàn bộ record, kiểm IDs/missing/duplicate/invalid spans/out-of-range/overlap/duplicate annotations. Polarity kể cả conflict giữ nguyên metadata; không map hoặc train polarity trong P8.','',
           table(pd.DataFrame([{'split':s,**v} for s,v in manifest['sources'].items()])), '',
           'Mỗi BIO record giữ nguyên sentence_id, raw text và original aspects, thêm uid=original_split:sentence_id, source_file, original_split, split, extraction_aspects. Không sửa raw XML hoặc JSONL P1 in-place.','',
           '## 4. BIO conversion','',
           'Nhãn riêng ATE: O=0, B-ASP=1, I-ASP=2, không dùng ánh xạ nhãn sentiment. Với mỗi gold character span, token WordPiece đầu là B, toàn bộ WordPiece tiếp theo trong cùng span là I; các token khác O. CLS/SEP và padding dùng -100 trong loss. Không bỏ continuation subword. Căn chỉnh dùng offsets gốc, không text.find; repeated term giữ đúng occurrence.','',
           '## 5. Alignment validation','',
           f"Alignment **{manifest['alignment']['status']}**, unexplained failures={manifest['alignment']['unexplained_failures']}; sentences truncated=0, overlength=0. BIO→character spans round-trip khớp extraction spans ở toàn bộ splits. Gold không có I sau O; boundary/overlap/token gaps được kiểm rõ.",'',
           table(pd.DataFrame(manifest['alignment']['explained_whitespace_adjustments'])),'',
           'Một train annotation `uninstall` chứa NBSP ở cuối: original[44,54) được giữ nguyên, extraction span[44,53) bỏ whitespace biên bằng policy cố định cho mọi split. Không suy đoán sửa chữ hoặc dịch offsets. Official test không có adjustment nên strict test metric dùng đúng nguyên character boundaries nguồn. Hai term có ranh giới giữa cụm chữ không whitespace vẫn align được bằng WordPiece; không ép dùng regex word boundary.','',
           '## 6. Train/validation/test và leakage','',
           f"GroupShuffleSplit seed{cfg['seed']}, validation fraction{cfg['validation_fraction']}; chỉ từ official train, grouping normalized text để duplicate train không sang validation. Actual train/validation={manifest['splits']['train']['sentences']}/{manifest['splits']['validation']['sentences']}; tỷ lệ có thể lệch nhẹ do group. IDs cố định trong manifest. Official test giữ nguyên800 câu, không merge/resplit.",'',
           'Qualified UID overlap=0 trên mọi cặp; normalized text overlap train–validation=0. Có **một duplicate tự nhiên `227`** giữa official train/test (cùng ID và text); source-split-qualified IDs tránh đụng khóa nhưng **không loại bỏ rò rỉ nội dung này**. Đã giữ nguyên benchmark gốc theo yêu cầu, không tự xóa test hoặc dùng test để quyết định train deletion. Bảng metric có cả official800 chính và supplementary loại đúng duplicate này (799 câu), dùng cùng saved predictions, không rerun/tune. Raw collision/duplicate được ghi đầy đủ trong data_validation.json; nghiệm thu có giới hạn này, không tuyên bố text-disjoint train–official test tuyệt đối.','',
           'Runner chỉ load train/validation trong training, ghi selection_lock trước khi load test records. Chuẩn bị data có kiểm hình thức spans/test để validation dữ liệu; không dùng metric test cho hyperparameters, epoch, checkpoint hoặc threshold.','',
           '## 7. Cấu hình model','',
           table(pd.DataFrame([{'setting':k,'value':v} for k,v in {
               'pretrained_model':cfg['pretrained_model'],'revision':cfg['revision'],'task':'BertForTokenClassification',
               'seed':cfg['seed'],'max_length':cfg['max_length'],**tc}.items()])), '',
           'Khởi tạo từ pretrained base local đã có; head token classifier mới, không reuse sentiment fine-tuned weights. Batch8×gradient accumulation2=effective16 (batch cuối nhỏ hơn); AdamW, linear warmup/decay, FP16, gradient checkpointing. Không search nhiều model hoặc class weighting. Max128 đủ vì official train tối đa91 tokens; official test chỉ kiểm không vượt cap (max90). API P8 từ chối input vượt cap, không truncate ngầm; windowing cho review dài chưa triển khai.','',
           '## 8. Kết quả huấn luyện','',table(history_table),'',
           f"Đã chạy {result['epochs_run']} epoch; best epoch={result['selected_epoch']} theo **validation entity F1**, tie chọn epoch sớm nhất. Training forward/backward/validation thực tế, không phải smoke. Reload best model tái lập nguyên validation predictions theo cùng chế độ/batch; selection lock và hashes đã đối chiếu độc lập. Last model + optimizer/scheduler/scaler/RNG/epoch được lưu để resume ở ranh giới epoch khi run chưa selection.",'',
           table(pd.DataFrame([{'measurement':k,'value':v} for k,v in result.items() if k not in {'validation','test','versions','status'}])), '',
           'Runtime wall gồm checkpoint I/O; training_seconds chỉ vòng train cộng theo epoch; validation/test seconds tính từ token có sẵn và gồm decode/metrics, không là raw-text latency. Peak RSS là cả tiến trình, GPU allocated/reserved theo PyTorch, không toàn VRAM vật lý; tiền compute NOT_MEASURED. Model artifact bytes gồm best model/tokenizer/config, không gồm optimizer/last checkpoints.','',
           'Phiên bản: '+json.dumps(result['versions'],ensure_ascii=False)+'. Seed được cố định; đã quan sát cảnh báo CUDA memory-efficient attention backward không bảo đảm bitwise determinism (warn_only). Không khẳng định retrain sẽ cho cùng trọng số/score từng bit. Split/BIO/metric từ saved predictions đã kiểm tái lập.','',
           '## 9. Entity-level evaluation','',table(performance),'',
           'Metric chính: micro exact **character-span** P/R/F1; phải khớp toàn [start,end), `battery` không được partial credit cho `battery life`. Tự triển khai tập span theo câu và kiểm số học bằng fixtures; không thêm seqeval vì không cần dependency để đếm exact character spans. Không gọi đây là kết quả chạy official SemEval scorer. Gold BIO strict; prediction orphan I sau O được decode như bắt đầu entity (policy công bố), số lần sửa trong metrics JSON.','',
           f"Token accuracy bổ trợ: validation={result['validation']['token_accuracy']:.6f}, test={result['test']['token_accuracy']:.6f}; không dùng nghiệm thu. Saved predictions chứa sentence ID/text/gold/predicted aspects và character spans, chỉ lưu local để tránh tự publish dataset.",'',
           '## 10. Error analysis','',table(error_table),'',
           insights,'',
           'FN=mọi gold entity không exact-match; FP=mọi predicted entity không exact-match. Boundary pair là một cặp FN/FP có giao ký tự, có thể nhiều-nhiều; không cộng/trừ như taxonomy rời nhau. missed_without_overlap và false_positive_without_overlap tách trường hợp không giao gold/pred nào.','',
           'Multi-word dùng >1 whitespace word; rare terminology có frequency<=1 trong **train thực tế2587**, gồm unseen; long_phrase>=3 words chỉ proxy cấu trúc cho cụm phức tạp, không tự xác nhận compound/technical noun phrase bằng người. Multiple-aspect errors dùng mẫu số số câu >1 aspect. Generic nouns system/machine/thing chỉ mô tả nếu có gold; không gán mọi lỗi vào taxonomy hoặc suy ra nguyên nhân semantic. Error examples đầy đủ ở local `{validation,test}_errors.json`, chứa IDs/gold/pred/boundary pairs để truy nguồn.','',
           '## 11. Giới hạn','',
           'Các phát hiện chỉ dành laptop tiếng Anh. Nhãn đại diện suy từ số sao-nhiễu nhãn vẫn là giới hạn của sentiment P0–P7; **ATE dùng span labels SemEval, không dùng rating proxy**. SemEval-to-Amazon platform/style shift trong laptop review chưa được đo bằng P8. Bộ gold thủ công nhỏ/independent P10 vẫn PENDING; không dùng diagnosis360 để thay ABSA gold.','',
           'Giới hạn thêm: nguồn/license NOT_VERIFIED theo ngoại lệ P1; một natural duplicate train/test; whitespace adjustment train có ghi rõ; một seed/một BERT; GPU training best-effort determinism; không đánh giá polarity hoặc end-to-end ABSA. Confidence trả null; API chỉ en và cap128, chưa windowing. Không khẳng định production hoặc tiếng Việt.','',
           '## 12. Quyết định nghiệm thu','',
           f"**P8: {acceptance['status']} — {acceptance['readiness']}.** T01–T04 có artifact thật; alignment không lỗi chưa giải thích; validation group-disjoint và official partitions nguyên vẹn với duplicate đã công bố; model fine-tuned/selected từ validation; official test đã đánh giá một lần; metric/error analysis/checkpoint/provenance đầy đủ.",'',
           f"Tests: {validation.get('total_passed','PENDING')} PASS, {validation.get('failed','PENDING')} FAIL. P0–P7/raw bảo toàn {preservation['files_verified_unchanged']} files; canonical metrics/Amazon dataset không đổi. P9 chưa triển khai; dừng tại readiness đã ghi. Chi tiết gates: acceptance.json, independent_evaluation.json, preservation.json, validation.json.",'',
           '## 13. Artifacts','',table(pd.DataFrame([{'artifact':k,'path':v} for k,v in paths.items()])),'',
           'Inference API: `from src.absa.extraction import AspectExtractor`; tải thư mục best một lần rồi gọi `extract_aspects(text)`. Output là danh sách term/start/end/score(null); không có aspect trả [], không tạo polarity. CPU inference smoke trên validation đã PASS, không thêm lượt test prediction.','',
           '## 14. Tái lập','',
           '```powershell','.venv/Scripts/python.exe -B -m scripts.prepare_p8',
           '.venv/Scripts/python.exe -B -m scripts.train_p8',
           '.venv/Scripts/python.exe -B -m scripts.finalize_p8 --run-checks','```','',
           'Lệnh train ở trên chỉ dùng khi output chưa tồn tại, **không chạy lại run đã khóa**. Resume run chưa selection bằng `scripts.train_p8 --resume`; identity/config/data/source phải khớp. Sau selection, runner từ chối mở lại test. Để xác minh kết quả hiện tại chỉ chạy prepare_p8 và finalize_p8 (không flag để dùng tests evidence còn khớp source; --run-checks để kiểm suite lại). Để tái tạo training độc lập cần namespace mới trong config trước khi chạy, giữ nguyên hyperparameters/split/seed, công bố best-effort GPU determinism; không overwrite hoặc chọn run theo test.','']
    (root/'reports/p8_aspect_extraction.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-checks',action='store_true')
    args=parser.parse_args()
    result=finalize(checks=args.run_checks)
    print(result['status']+' — '+result['readiness'])
