"""Xác minh ASC/joint từ saved predictions và bảo toàn P0–P8, không train hoặc rerun test."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

from src.absa.extraction_data import load_records as load_p8_records
from src.absa.sentiment_data import load_asc_records,load_p9_config,prepare_p9
from src.config import PROJECT_ROOT
from src.evaluation.aspect_sentiment import asc_error_analysis,joint_metrics
from src.evaluation.classification import LABELS,classification_metrics
from src.evaluation.error_diagnosis import file_hash,weighting_pairs


def write_json(path: Path,value) -> None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def table(frame: pd.DataFrame) -> str:
    def cell(v): return f'{v:.6f}' if isinstance(v,float) else str(v)
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(cell(v) for v in r)+' |' for r in frame.itertuples(index=False,name=None)])


def assert_metrics(actual: dict,expected: dict) -> None:
    """So sánh cả matrix/per-class với tolerance nhỏ, không chỉ macroF1."""
    for key,value in actual.items():
        other=expected[key]
        if isinstance(value,dict): assert_metrics(value,other)
        elif isinstance(value,(int,float)) and not isinstance(value,bool):
            if abs(value-other)>1e-12: raise ValueError('Metric không khớp: '+key)
        elif value!=other: raise ValueError('Metric/matrix không khớp: '+key)


def verify_asc_predictions(rows: list[dict],predictions: list[dict]) -> dict:
    if [r['example_id'] for r in rows]!=[p['example_id'] for p in predictions]: raise ValueError('ASC prediction ID/order không khớp')
    fields=['sentence_uid','sentence_id','original_split','split','source_file','text','aspect','start','end',
            'original_aspect_index','original_polarity','label','label_id']
    for row,pred in zip(rows,predictions):
        if any(row[k]!=pred[k] for k in fields): raise ValueError('ASC prediction gold/source metadata thay đổi')
        label=pred['predicted_label_id']
        if type(label) is not int or label not in range(3) or pred['predicted_sentiment']!=LABELS[label]: raise ValueError('ASC prediction label mapping không hợp lệ')
        if pred['correct']!=(label==row['label_id']) or pred['confidence'] is not None: raise ValueError('ASC correct/confidence không khớp contract')
    return classification_metrics([r['label_id'] for r in rows],[p['predicted_label_id'] for p in predictions])


def verify_joint_predictions(rows: list[dict],p8: list[dict],predictions: list[dict]) -> dict:
    if [r['uid'] for r in rows]!=[p['uid'] for p in predictions] or [r['uid'] for r in rows]!=[p['uid'] for p in p8]:
        raise ValueError('Joint UID/order không khớp')
    for row,extracted,pred in zip(rows,p8,predictions):
        gold=[{**a,'polarity':row['aspects'][a['original_aspect_index']]['polarity']} for a in row['extraction_aspects']]
        if pred['gold_aspects']!=gold or pred['text']!=row['text'] or pred['sentence_id']!=row['sentence_id']:
            raise ValueError('Joint gold/source bị thay đổi')
        actual=[(a['term'],a['start'],a['end']) for a in pred['predicted_aspects']]
        expected=[(a['term'],a['start'],a['end']) for a in extracted['predicted_aspects']]
        if actual!=expected: raise ValueError('Joint đã thay P8 predicted spans hoặc bỏ aspect trước inference')
        if any(a['aspect_score'] is not None or a['sentiment_score'] is not None for a in pred['predicted_aspects']):
            raise ValueError('Joint confidence phải null')
    return joint_metrics(predictions)


def run_checks(root: Path,report: Path) -> dict:
    logs=[]; commands=[]
    for args in [['-B','-m','scripts.test_all'],['-m','pip','check'],['-m','compileall','-q','src','scripts','tests']]:
        p=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(p.stdout+p.stderr); commands.append({'command':'.venv/Scripts/python.exe '+' '.join(args),'exit_code':p.returncode})
        (report/'test_console.log').write_text('\n'.join(logs),encoding='utf-8');print(json.dumps(commands[-1]),flush=True)
        if p.returncode:
            write_json(report/'validation.json',{'status':'FAIL','commands':commands,'BLOCKED':'Tests/checks fail; xem log',
                       'NEXT_ACTION':'Sửa lỗi, chạy lại --run-checks; không đánh dấu P9 DONE'})
            raise RuntimeError('P9 checks thất bại')
    counts=[int(x) for x in re.findall(r'(\d+) passed',logs[0])]
    if len(counts)!=3 or sum(counts)<350: raise ValueError('Không quan sát đủ suite cũ và mới')
    paths=['scripts/test_all.py','scripts/prepare_p9.py','scripts/train_p9.py','scripts/evaluate_p9_end_to_end.py',
           'scripts/finalize_p9.py','src/absa/sentiment_data.py','src/absa/sentiment.py','src/evaluation/aspect_sentiment.py',
           'src/inference/absa.py','tests/test_p9_data.py','tests/test_p9_model.py']
    result={'status':'PASS','total_passed':sum(counts),'failed':0,'groups':counts,'previous_tests':350,
            'new_tests':sum(counts)-350,'commands':commands,'pip_check':'PASS','compileall':'PASS',
            'source_sha256':{p:file_hash(root/p) for p in paths},'console_log':(report/'test_console.log').relative_to(root).as_posix()}
    write_json(report/'validation.json',result);return result


def finalize(root: Path=PROJECT_ROOT,*,checks: bool=False) -> dict:
    cfg=load_p9_config(root/'configs/p9_aspect_sentiment.yaml'); report=root/cfg['report_directory']; local=root/cfg['prediction_directory']
    result=json.loads((report/'result.json').read_text(encoding='utf-8'))
    if result['status']!='STANDALONE_ASC_COMPLETE': raise ValueError('Standalone ASC chưa hoàn tất')
    manifest=prepare_p9(root,root/'configs/p9_aspect_sentiment.yaml')
    identity=json.loads((report/'training_identity.json').read_text(encoding='utf-8'))
    if identity['config']!=cfg or identity['data_manifest_sha256']!=file_hash(root/cfg['data_directory']/'manifest.json'):
        raise ValueError('ASC config/data đã thay đổi')
    if any(file_hash(root/p)!=h for p,h in identity['source_sha256'].items()): raise ValueError('ASC training/evaluation code đã thay đổi sau run')
    lock=json.loads((report/'selection_lock.json').read_text(encoding='utf-8'))
    history=json.loads((report/'history.json').read_text(encoding='utf-8'))
    candidates=[]; weighting=[]; candidate_predictions={}
    datasets={s:load_asc_records(root,manifest,s) for s in ['train','validation','test']}
    for mode in cfg['training']['loss_candidates']:
        best=max([h for h in history if h['mode']==mode],key=lambda r:r['validation']['macro_f1'])
        source=root/cfg['model_directory']/mode/'best/model.safetensors'
        completed=json.loads((report/f'{mode}_complete.json').read_text(encoding='utf-8'))
        if completed['epoch']!=best['epoch'] or completed['validation_macro_f1']!=best['validation']['macro_f1'] or completed['model_sha256']!=file_hash(source):
            raise ValueError('ASC candidate selection/checkpoint không khớp')
        pred=json.loads((local/f'{mode}_validation_predictions.json').read_text(encoding='utf-8'))
        actual=verify_asc_predictions(datasets['validation'],pred);assert_metrics(actual,best['validation'])
        candidate_predictions[mode]=[p['predicted_label_id'] for p in pred]
        candidates.append(completed)
        weighting.append({'mode':mode,'epoch':best['epoch'],'validation_macro_f1':actual['macro_f1'],
                          'accuracy':actual['accuracy'],'weighted_f1':actual['weighted_f1'],
                          **{f'{l}_{k}':actual['per_class'][l][k] for l in LABELS for k in ['precision','recall','f1']}})
    selected=max(candidates,key=lambda r:r['validation_macro_f1'])
    if selected!=lock['selected'] or result['selected']!=selected or lock['test_used_for_selection'] or not lock['selection_complete_before_test']:
        raise ValueError('ASC validation selection lock không khớp')
    for path,sha in [('selection_lock.json',result['selection_lock_sha256']),('history.json',lock['history_sha256']),
                     ('training_identity.json',lock['training_identity_sha256'])]:
        if file_hash(report/path)!=sha: raise ValueError('ASC history/selection hash thay đổi')
    if file_hash(root/result['model_directory']/'model.safetensors')!=selected['model_sha256']: raise ValueError('ASC selected model hash thay đổi')
    train_counts=Counter(r['aspect'].casefold() for r in datasets['train'])
    predictions={}; independent={}; errors={}; classes=[]; transitions=[]
    for split in ['validation','test']:
        predictions[split]=[json.loads(line) for line in (local/f'{split}_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
        actual=verify_asc_predictions(datasets[split],predictions[split]);assert_metrics(actual,result[split])
        independent[split]=actual
        analysis=asc_error_analysis(predictions[split],train_counts)
        write_json(local/f'{split}_error_examples.json',analysis['error_examples'])
        errors[split]={k:v for k,v in analysis.items() if k!='error_examples'}
        for label,metric in actual['per_class'].items(): classes.append({'split':split,'class':label,**metric})
        for i,source in enumerate(LABELS):
            for j,target in enumerate(LABELS):
                transitions.append({'split':split,'gold':source,'prediction':target,'count':actual['confusion_matrix'][i][j]})
    pd.DataFrame(classes).to_csv(report/'per_class_metrics.csv',index=False)
    pd.DataFrame(transitions).to_csv(report/'confusion_matrix.csv',index=False)
    pd.DataFrame([{'split':s,**g} for s,a in errors.items() for g in a['groups']]).to_csv(report/'error_groups.csv',index=False)
    write_json(report/'error_summary.json',errors)
    pd.DataFrame(weighting).to_csv(report/'weighting_validation.csv',index=False)
    paired=weighting_pairs([r['label_id'] for r in datasets['validation']],candidate_predictions['unweighted'],candidate_predictions['balanced'])
    paired.to_csv(report/'weighting_paired_validation.csv',index=False)
    distributions=[]
    for split,stats in manifest['splits'].items():
        for label in (*LABELS,'conflict'):
            distributions.append({'split':split,'polarity':label,'original_count':stats['original_polarity_counts'][label],
                                  'original_share':stats['original_polarity_shares'][label],
                                  'included_supervised':label!='conflict'})
    pd.DataFrame(distributions).to_csv(report/'polarity_distribution.csv',index=False)
    e2e=json.loads((report/'end_to_end_results.json').read_text(encoding='utf-8'))
    if e2e['status']!='COMPLETE' or e2e['asc_selection_lock_sha256']!=result['selection_lock_sha256'] or e2e['p8_inference_rerun']:
        raise ValueError('End-to-end chưa hoàn tất đúng locked model')
    p8=json.loads((root/cfg['p8_manifest']).read_text(encoding='utf-8')); joint={}
    for split in ['validation','test']:
        rows=load_p8_records(root,p8,split)
        path=root/cfg['p8_predictions']/f'{split}_predictions.jsonl'
        if file_hash(path)!=e2e['splits'][split]['p8_prediction_sha256']: raise ValueError('P8 predictions nguồn bị thay đổi')
        p8pred=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        path=local/f'{split}_end_to_end_predictions.jsonl'
        if file_hash(path)!=e2e['splits'][split]['prediction_sha256']: raise ValueError('Joint prediction hash thay đổi')
        pred=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        actual=verify_joint_predictions(rows,p8pred,pred);actual.pop('decomposition')
        assert_metrics(actual,e2e['splits'][split]['metrics']);joint[split]=actual
    # Natural duplicate chỉ supplementary, không thay canonical score hoặc chọn lại model.
    duplicate_uids={r['test_uid'] for r in manifest['leakage']['official_cross_split_duplicate_texts']}
    clean=[p for p in predictions['test'] if p['sentence_uid'] not in duplicate_uids]
    independent['test_excluding_natural_duplicate_supplementary']=classification_metrics([p['label_id'] for p in clean],[p['predicted_label_id'] for p in clean])
    exact_sets={s:{(r['text'],r['start'],r['end'],r['label']) for r in rows} for s,rows in datasets.items()}
    record_overlaps={a+'__'+b:len(exact_sets[a]&exact_sets[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}
    if record_overlaps['train__validation']: raise ValueError('Exact ASC record leakage train–validation')
    baseline=json.loads((root/'reports/p9_preservation_before.json').read_text(encoding='utf-8'))
    changed=[p for p,h in baseline.items() if not (root/p).is_file() or file_hash(root/p)!=h]
    if changed: raise ValueError('P0–P8 frozen files thay đổi: '+str(changed))
    preservation={'status':'PASS','files_verified_unchanged':len(baseline),'mismatches':[],
                  'p8_canonical_test_entity_f1':json.loads((root/cfg['p8_result']).read_text(encoding='utf-8'))['test']['entity_f1'],
                  'p8_model_sha256':manifest['p8_model_sha256'],'sentiment_benchmark_sha256':file_hash(root/'reports/p7_unified_results.csv')}
    write_json(report/'preservation.json',preservation)
    independent_report={'status':'PASS','standalone_gold_aspect_metrics':independent,'joint_predicted_aspect_metrics':joint,
                        'selected_model_sha256':selected['model_sha256'],'model_selection_verified':True,'predictions_rerun':False,
                        'exact_record_overlap_counts':record_overlaps,
                        'prediction_sha256':{s:file_hash(local/f'{s}_predictions.jsonl') for s in predictions}}
    write_json(report/'independent_evaluation.json',independent_report)
    if checks: validation=run_checks(root,report)
    else: validation=json.loads((report/'validation.json').read_text(encoding='utf-8')) if (report/'validation.json').exists() else {'status':'PENDING'}
    if validation['status']=='PASS' and any(file_hash(root/p)!=h for p,h in validation['source_sha256'].items()): raise ValueError('P9 source đổi sau tests, cần --run-checks')
    smoke_path=report/'inference_smoke.json'
    if not smoke_path.exists():
        import torch
        from src.absa.extraction import AspectExtractor
        from src.absa.sentiment import AspectSentimentClassifier
        from src.inference.absa import AspectAnalyzer
        torch.set_num_threads(2)
        classifier=AspectSentimentClassifier(root/result['model_directory'],device='cpu')
        p8_val=[json.loads(line) for line in (root/cfg['p8_predictions']/'validation_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
        multiple={p['uid'] for p in p8_val if len(p['predicted_aspects'])>1}
        sample=next((r for r in datasets['validation'] if r['sentence_uid'] in multiple),datasets['validation'][0])
        answer=classifier.classify_aspect_sentiment(sample['text'],sample['aspect'],sample['start'],sample['end'])
        extractor=AspectExtractor(root/json.loads((root/cfg['p8_result']).read_text(encoding='utf-8'))['model_directory'],device='cpu')
        pipeline=AspectAnalyzer(extractor,classifier)
        aspects=pipeline.analyze_aspects(sample['text'])
        if answer['sentiment'] not in LABELS or answer['confidence'] is not None: raise ValueError('ASC API contract lỗi')
        if any(a['sentiment'] not in LABELS or a['term']!=sample['text'][a['start']:a['end']] for a in aspects): raise ValueError('ABSA API contract lỗi')
        write_json(smoke_path,{'status':'PASS','device':'cpu','validation_example_id':sample['example_id'],
                   'gold_aspect_prediction':answer,'pipeline_aspect_count':len(aspects),'official_test_inference':False,
                   'model_sha256':selected['model_sha256']})
    smoke=json.loads(smoke_path.read_text(encoding='utf-8'))
    if smoke['status']!='PASS' or smoke['model_sha256']!=selected['model_sha256']: raise ValueError('ASC smoke artifact không khớp')
    acceptance={'status':'DONE' if validation['status']=='PASS' else 'NOT_DONE_PENDING_TESTS',
                'readiness':'READY FOR P10' if validation['status']=='PASS' else 'NOT_READY','date':'2026-10-26',
                'tasks':{t:'PASS' for t in ['P9-T01','P9-T02','P9-T03','P9-T04']},
                'standalone_validation':independent['validation'],'standalone_official_test':independent['test'],
                'end_to_end':joint,'conflict_policy':cfg['conflict_policy'],'selection':selected,
                'canonical_artifacts_p0_p8_changed':False,'p8_retrained':False,'amazon_dataset_changed':False,
                'official_test_used_for_tuning':False,'p10_implemented':False,'tests':validation,'preservation':preservation,
                'mandatory_blockers_before_p10':[] if validation['status']=='PASS' else ['PENDING_TESTS'],
                'limitations':['SemEval license/source NOT_VERIFIED with owner educational exception',
                  'three-class conditional evaluation excludes conflict; end-to-end ignores exact conflict-span predictions',
                  'one natural official train/test duplicate retained','single seed and best-effort CUDA backward determinism',
                  'SemEval-to-Amazon platform/style shift not measured; independent small P10 gold pending',
                  'uncalibrated confidence null; API rejects overlength context'],
                'NEXT_ACTION':'Dừng tại READY FOR P10; không triển khai independent gold/app hoặc pseudo-label Amazon.'}
    write_json(report/'acceptance.json',acceptance)
    write_report(root,cfg,manifest,result,history,independent_report,errors,weighting,paired,validation,preservation,acceptance)
    return acceptance


def write_report(root: Path,cfg: dict,manifest: dict,result: dict,history: list,independent: dict,
                 errors: dict,weighting: list,paired: pd.DataFrame,validation: dict,
                 preservation: dict,acceptance: dict) -> None:
    report=root/cfg['report_directory']; tc=cfg['training']
    distribution=pd.read_csv(report/'polarity_distribution.csv')
    classes=pd.read_csv(report/'per_class_metrics.csv')
    confusion=pd.read_csv(report/'confusion_matrix.csv')
    standalone=independent['standalone_gold_aspect_metrics']; joint=independent['joint_predicted_aspect_metrics']
    performance=pd.DataFrame([{'split':s,'examples':sum(p['support'] for p in m['per_class'].values()),
                              **{k:m[k] for k in ['macro_f1','accuracy','weighted_f1']}} for s,m in standalone.items()])
    history_table=pd.DataFrame([{'mode':h['mode'],'epoch':h['epoch'],'validation_macro_f1':h['validation']['macro_f1'],
                'accuracy':h['validation']['accuracy'],'weighted_f1':h['validation']['weighted_f1'],
                'neutral_precision':h['validation']['per_class']['neutral']['precision'],
                'neutral_recall':h['validation']['per_class']['neutral']['recall'],
                'neutral_f1':h['validation']['per_class']['neutral']['f1'],'training_seconds':h['training_seconds']} for h in history])
    weight_frame=pd.DataFrame(weighting).set_index('mode')
    deltas={k:float(weight_frame.loc['balanced',k]-weight_frame.loc['unweighted',k])
            for k in ['validation_macro_f1','accuracy','weighted_f1','neutral_precision','neutral_recall','neutral_f1']}
    joint_table=pd.DataFrame([{'split':s,'precision':m['precision'],'recall':m['recall'],'f1':m['f1'],**m['counts']} for s,m in joint.items()])
    test=standalone['test']; cm=test['confusion_matrix']
    off_diagonal=[(cm[i][j],LABELS[i],LABELS[j]) for i in range(3) for j in range(3) if i!=j]
    most=max(off_diagonal)
    artifact_paths={
        'ASC data/tokenizer/config/split provenance':cfg['data_directory']+'/manifest.json',
        'Conflict exclusions giữ metadata':cfg['data_directory']+'/{train,validation,test}_conflict_excluded.jsonl',
        'Selected model/tokenizer/metadata':result['model_directory'],
        'Loss candidates best/last/optimizer/RNG':cfg['model_directory']+'/{unweighted,balanced}/',
        'Training identity/history/selection lock':cfg['report_directory']+'/{training_identity,history,selection_lock}.json',
        'Canonical standalone metrics':cfg['report_directory']+'/{validation,test}_metrics.json',
        'Gold-aspect predictions có text local':cfg['prediction_directory']+'/{validation,test}_predictions.jsonl',
        'End-to-end predictions có text local':cfg['prediction_directory']+'/{validation,test}_end_to_end_predictions.jsonl',
        'Joint metrics/decomposition':cfg['report_directory']+'/end_to_end_results.json',
        'Per-class/confusion/strata/weighting CSV':cfg['report_directory']+'/',
        'Independent verification':cfg['report_directory']+'/independent_evaluation.json',
        'Tests/preservation/CPU API smoke':cfg['report_directory']+'/{validation,preservation,inference_smoke}.json',
        'Acceptance':cfg['report_directory']+'/acceptance.json'}
    lines=['# P9 — Aspect Sentiment Classification và end-to-end ABSA cho laptop','',
           f"**P9: {acceptance['status']} — {acceptance['readiness']}.** Standalone gold-aspect ASC là kết quả chính; joint ABSA dùng predicted spans P8 được báo riêng. Không triển khai P10.",'',
           '## 1. Mục tiêu','',
           'Phân loại sentiment cho đúng một aspect occurrence trong sentence, không dùng label chung toàn câu. Gold-aspect ASC trả lời khi aspect đúng đã có thì classifier làm tốt đến đâu; joint metric đồng thời yêu cầu span và sentiment đúng. Không đặt target score nghiệm thu giả.','',
           '## 2. Dataset','',
           'SemEval-2014 Task4 **Laptop** từ XML/JSONL local đã có ở P1 và P8. Không dùng Restaurant/domain khác, Amazon30K proxy labels hoặc pseudo-aspect để train. Source/license vẫn NOT_VERIFIED theo ngoại lệ giáo dục P1; local hashes không chứng thực độc lập official origin. Không download/acquire thêm dữ liệu.','',
           table(pd.DataFrame([{'split':s,**{k:m[k] for k in ['source_sentences','original_aspect_entities','examples','excluded_conflict','max_sequence_length','truncated_examples']}}
                               for s,m in manifest['splits'].items()])), '',
           'Mỗi sample là một sentence+gold aspect/span, giữ original_aspect_index, raw polarity/xml_attributes, sentence ID/qualified UID và source_file. P9 kiểm raw XML+JSONL/P8 hashes, term/spans, polarity enum, missing/duplicates/overlap; không mặc nhiên coi P8 PASS là đủ.','',
           '## 3. Polarity distribution','',table(distribution),'',
           'Original share dùng mẫu số mọi aspects kể cả conflict; supervised class shares trong manifest dùng mẫu số chỉ3class. Neutral và các lớp khác có support khác nhau; test polarity mix khác train/validation được công bố, không dùng để đổi weights.','',
           '## 4. Conflict policy','',
           'PLAN/AGENTS yêu cầu đúng3nhãn negative/neutral/positive và resolve/exclude conflict có ghi chép. Đánh giá lựa chọn: giữ4class trái hợp đồng output hiện hành và conflict ít mẫu; map sang3class sẽ làm sai ý nghĩa mixed sentiment nếu không có căn cứ; **chọn exclude conflict** khỏi supervised/standalone target, giữ nguyên annotation trong nguồn và sidecar exclusions. Quyết định dựa trên PLAN và định nghĩa nhãn trước test, không chọn từ score test.','',
           'Conflict F1=N/A, model không được train để phát hiện conflict. Joint evaluation loại gold conflict khỏi recall denominator và ignore predicted entities có **exact cùng span conflict** chỉ lúc chấm điểm. Các predictions này vẫn được model infer, lưu và đếm raw; không dùng gold polarity để tạo input hoặc chặn predictions trước inference. Partial/overlapping conflict span khác ranh giới vẫn là FP nếu không khớp valid gold. Tổng excluded/ignored được công bố ở mục13. Đây là metric3class có điều kiện, không full4class ABSA.','',
           '## 5. Input representation','',
           '`[CLS] context_before [unused0] target_occurrence [unused1] context_after [SEP]`. Marker đặt bằng character offsets, không text.find trong SemEval. Chọn marker thay sentence+term pair thuần vì cùng term có thể xuất hiện nhiều lần với ngữ cảnh khác: pair thuần không chỉ ra occurrence. Hai reserved tokens IDs1/2 đã ở BERT vocab được đăng ký special trên **bản tokenizer P9 riêng**, vocab giữ30522, không resize embedding hoặc sửa tokenizer P8; serialization/reload có tests.','',
           'Sentence/raw original span giữ nguyên. Extraction span kế thừa policy P8 trim whitespace biên có giải thích cho1train annotation; không sửa polarity/annotation gốc. Toàn bộ context được giữ, không stemming/stopword removal. API không có offsets chỉ chấp nhận term xuất hiện đúng1lần; repeated/overlapping occurrence bắt buộc cung cấp start/end.','',
           '## 6. Train/validation/test integrity','',
           'Dùng đúng sentence-level splitIDs P8:2587train/458validation/800official test, seed42/group normalized text. Không tách aspect examples của cùng sentence qua train/validation. Câu0aspect không tạo ASC example nhưng vẫn thuộc split và có mặt trong end-to-end evaluation; không gán nhãn giả cho chúng. Official partitions giữ nguyên.','',
           'Exact ASC record overlap (text,start,end,label): '+json.dumps(independent['exact_record_overlap_counts'],ensure_ascii=False)+'. Term overlap counts: '+json.dumps(manifest['leakage']['asc_term_overlap_counts'],ensure_ascii=False)+'. Shared term tự nó không phải leakage.','',
           'Qualified sentence UID overlap0 và normalized text overlap train–validation0. Official raw ID/text227 trùng tự nhiên như P8 đã công bố; namespace tránh đụng khóa nhưng không xóa content overlap. Main test giữ nguyên; supplementary loại duplicate từ cùng saved predictions ở bảng8–9, không dùng để selection.','',
           'Standalone runner chỉ load train/validation cho model selection; test records được mở sau selection_lock. Chuẩn bị data có đọc test labels cho integrity/distribution, không dùng score test để quyết định conflict, preprocessing, weight hoặc epoch. P8 test đã được xem ở pha trước; không gọi đây là một holdout hoàn toàn mới.','',
           '## 7. Model configuration và imbalance','',
           table(pd.DataFrame([{'setting':k,'value':v} for k,v in {'pretrained_model':cfg['pretrained_model'],'revision':cfg['revision'],
                   'max_length':cfg['max_length'],'seed':cfg['seed'],'representation':cfg['representation'],**tc}.items()])), '',
           'Một BERT sequence classifier,2loss candidates unweighted/balanced cùng pretrained source, seed, batch order, optimizer/schedule. Không reuse P6/P8 fine-tuned weights. Balanced weights=N_train/(3*n_train_class): '+json.dumps(manifest['balanced_weights_train_only'],ensure_ascii=False)+'. Không dùng validation/test để tính weights.','',
           table(history_table),'',table(pd.DataFrame(weighting)),'',
           'Balanced−unweighted ở checkpoint tốt nhất mỗi mode: '+json.dumps(deltas,ensure_ascii=False)+'. Không chọn weighted chỉ vì neutral recall tăng; selection dùng validation macroF1.','',table(paired),'',
           'Paired rows dùng cùng validation examples/IDs; corrected/regressed là thay đổi so gold polarity, FP có mẫu số ngoài lớp. Một seed, không causal superiority claim. Không evaluate test cho candidate không được chọn.','',
           '## 8. Standalone validation results','',
           table(performance[performance['split']=='validation']),'',
           '## 9. Standalone official test results','',table(performance[performance['split']!='validation']),'',
           f"Selected mode={result['selected']['mode']}, epoch={result['selected']['epoch']} bằng validation macroF1, tie theo candidate order rồi epoch sớm nhất. Official gold-aspect test inference{result['test_prediction_passes']}pass sau lock, không tuning. Reload selected checkpoint tái lập nguyên validation predictions theo cùng batch/precision. Confidence=null vì chưa calibration; không gọi raw softmax là xác suất tin cậy.",'',
           '## 10. Per-class results','',table(classes),'',
           'Nhãn/ma trận cố định theo negative,neutral,positive. Conflict bị loại có provenance, không có Conflict F1 giả. MacroF1 là trung bình F1 ba lớp; accuracy/weightedF1 đi kèm để không che minority behavior.','',
           '## 11. Confusion matrices','',
           'Hàng=gold, cột=prediction. CSV confusion_matrix.csv đủ9ô/split.','',
           *sum(([f'### {s}', '',table(pd.DataFrame(m['confusion_matrix'],index=LABELS,columns=LABELS).rename_axis('gold').reset_index()),'']
                  for s,m in standalone.items() if s in {'validation','test'}),[]),
           '## 12. Error analysis','',
           table(pd.read_csv(report/'error_groups.csv')),'',
           f"Test confusion lớn nhất: {most[1]}→{most[2]}={most[0]}; positive→negative={cm[2][0]}, negative→positive={cm[0][2]}. Neutral→negative={cm[1][0]}, neutral→positive={cm[1][2]} trên{test['per_class']['neutral']['support']}gold neutral. Per-class P/R/F1 giúp phân biệt giảm recall với tăng false positives.",'',
           'Nhóm negation/contrast/comparison chỉ lexical cues, group có thể chồng lấn; support và accuracy dùng mẫu số **aspect examples**, kèm số sentence riêng. Multi-aspect và mixed-polarity sentence lấy từ gold annotations3class cùng câu; không dùng một label chung cho cả câu. Rare<=1lần trong train ASC đã exclude conflict. Long context>30words chỉ proxy cấu trúc, không đo trực tiếp khoảng cách opinion–aspect.','',
           'Implicit sentiment, long-distance expression và mixed sentiment trong cùng một aspect chưa có human cause/opinion-span tags; không ép gán taxonomy hoặc gọi cue absence là implicit sentiment. Conflict rows giữ riêng để P10/task khác có thể xem xét, không tự tạo nhãn mới. Full wrong examples có ID/text/term/span/gold/pred/cue groups tại local `{validation,test}_error_examples.json`.','',
           '## 13. End-to-end results','',table(joint_table),'',
           'PLAN P9-T04 yêu cầu nối ATE→ASC: dùng **P8 predicted spans đã lưu** trên toàn458validation/800test, không chạy lại P8 test hoặc dùng gold aspect để thay input. P9 selected classifier infer trên mọi predicted spans, rồi chấm exact span+sentiment. Span sai ranh giới hoặc polarity sai đều không full credit. Standalone macroF1 và joint microP/R/F1 là hai bài toán/mẫu số khác nhau, không thay thế nhau.','',
           '## 14. End-to-end error decomposition','',
           'FN_joint=extraction_missing_gold_spans+sentiment_errors_on_exact_span; FP_joint=extraction_spurious_predicted_spans+sentiment_errors_on_exact_span. Boundary gold/pred là các unmatched spans có giao ký tự, là subset của extraction errors. Joint_wrong_span_and_polarity_pairs là quan hệ overlap vừa sai span vừa sai polarity, có thể nhiều-nhiều; không cộng như taxonomy rời nhau hoặc tự gán classifier sai cho FP không có gold polarity. Counts và denominator ở bảng13, details mỗi sentence ở local decomposition JSON.','',
           '## 15. Limitations','',
           'Chỉ laptop tiếng Anh. P6 sentiment dùng Amazon reviews với nhãn đại diện suy từ số sao có nhiễu; P8/P9 dùng SemEval aspect annotations. Cùng laptop nhưng nguồn/thời kỳ/annotation scheme/style khác; **SemEval-to-Amazon platform/style shift chưa được đo**. Independent P10 human gold nhỏ vẫn PENDING; diagnosis360 không thay ABSA gold.','',
           'Source/license NOT_VERIFIED theo ngoại lệ P1; natural duplicate official splits;3class evaluation không cover conflict; một seed/search nhỏ, không statistical superiority/production hoặc tiếng Việt. GPU memory-efficient attention backward có cảnh báo nondeterministic với warn_only; split/data/saved-pred metrics tái lập, không cam kết retrain bitwise-identical. API ASC cap128 tính cả markers, P8 cap128 riêng; pipeline từ chối overlength rõ thay vì silent truncate. SemEval max lengths thực tế trong bảng2 đều dưới cap,0truncated.','',
           'Actual runtime/compute (versions và peak là số đo đã quan sát):','',
           table(pd.DataFrame([{'measurement':k,'value':v} for k,v in result.items() if k not in {'status','validation','test','selected','versions'}])), '',
           'Versions: '+json.dumps(result['versions'],ensure_ascii=False)+'. Training time cộng2candidate loops; wall gồm checkpoint I/O. Inference từ token có sẵn, không raw-text end-to-end latency. RSS cả tiến trình/GPU allocated/reserved không toàn VRAM vật lý; artifact_bytes chỉ selected model/tokenizer/metadata, không optimizer/last/candidate khác. Tiền compute NOT_MEASURED. Resume artifacts được lưu theo epoch; actual resume NOT_MEASURED vì run liền mạch.','',
           '## 16. Acceptance decision','',
           f"**P9: {acceptance['status']} — {acceptance['readiness']}.** T01–T04 có artifacts thật, standalone gold-aspect ASC và joint tách biệt, conflict policy minh bạch, model selected từ validation, official test không tuning. Tests {validation.get('total_passed','PENDING')}PASS/{validation.get('failed','PENDING')}FAIL, pip/compile checks và CPU reload/API smoke được lưu. {preservation['files_verified_unchanged']}files frozen P0–P8/raw giữ hash; không retrain P8 hoặc sửa Amazon/canonical scores. Chưa triển khai P10; dừng tại readiness đã ghi.",'',
           '## 17. Artifacts','',table(pd.DataFrame([{'artifact':k,'path':v} for k,v in artifact_paths.items()])),'',
           'API: `AspectSentimentClassifier(directory).classify_aspect_sentiment(text,aspect,start,end)` và `AspectAnalyzer(extractor,classifier).analyze_aspects(text)`. Confidence/aspect_score/sentiment_score null; không có aspect trả[]. Language en, unsupported language báo lỗi. Không chạy pseudo labels Amazon30K, không annotation P10 hoặc UI/deployment.','',
           '## 18. Reproduction instructions','',
           '```powershell','.venv/Scripts/python.exe -B -m scripts.prepare_p9','.venv/Scripts/python.exe -B -m scripts.train_p9',
           '.venv/Scripts/python.exe -B -m scripts.evaluate_p9_end_to_end','.venv/Scripts/python.exe -B -m scripts.finalize_p9 --run-checks','```','',
           'Train/evaluate_end_to_end chỉ dành namespace chưa có output, không chạy lại completed run. Resume trước selection bằng --resume, identity/config/source phải khớp. Xác minh run hiện tại chỉ dùng prepare_p9 và finalize_p9 (không flag dùng tests evidence còn đúng source; --run-checks chạy lại suite). Không chạy lại P8 finalizer để sửa các báo cáo frozen:350tests P8 là evidence lịch sử, shared test driver đã mở rộng cho P9; P9 preservation xác nhận nguyên bytes. Muốn retrain tái lập độc lập phải đặt namespace mới trước khi chạy và giữ thiết kế cố định, không chọn run theo test.','']
    (root/'reports/p9_aspect_sentiment.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-checks',action='store_true')
    args=parser.parse_args();result=finalize(checks=args.run_checks)
    print(result['status']+' — '+result['readiness'])
