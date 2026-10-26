"""Xác minh/comparison P9-EXP01 từ saved predictions; không mở lại inference test."""
from collections import Counter
import json
from pathlib import Path
import re

from scripts.finalize_p9 import assert_metrics,run_checks,table,verify_asc_predictions,verify_joint_predictions,write_json
from scripts.p9_exp01 import NAMESPACE
from src.absa.extraction_data import load_records as load_p8_records
from src.absa.sentiment_data import load_asc_records,load_p9_config
from src.config import PROJECT_ROOT
from src.evaluation.asc_comparison import paired_predictions
from src.evaluation.aspect_sentiment import asc_error_analysis
from src.evaluation.classification import LABELS,classification_metrics
from src.evaluation.error_diagnosis import file_hash


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_lines(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def finalize(root: Path=PROJECT_ROOT,*,checks: bool=False) -> dict:
    import pandas as pd
    cfg=load_p9_config(root/'configs/p9_exp01_deberta.yaml')
    report=root/cfg['report_directory']; local=root/cfg['prediction_directory']
    result=read_json(report/'result.json'); lock=read_json(report/'selection_lock.json')
    identity=read_json(report/'training_identity.json')
    manifest=read_json(root/cfg['data_directory']/'manifest.json')
    canonical=read_json(root/'data/processed/p9_20261026/manifest.json')
    if result['status']!='STANDALONE_ASC_COMPLETE' or result['test_prediction_passes']!=1 or result['test_tuning']:
        raise ValueError('Standalone chưa hoàn tất đúng protocol')
    if identity['config']!=cfg or manifest['config']!=cfg: raise ValueError('Config identity thay đổi')
    if file_hash(root/cfg['data_directory']/'manifest.json')!=identity['data_manifest_sha256']:
        raise ValueError('Manifest experiment thay đổi')
    if file_hash(root/'data/processed/p9_20261026/manifest.json')!=manifest['canonical_manifest_sha256']:
        raise ValueError('Manifest frozen P9 thay đổi')
    for p,h in identity['source_sha256'].items():
        if file_hash(root/p)!=h: raise ValueError('Source thay đổi sau training: '+p)
    for p,h in read_json(report/'extension_source.json').items():
        if p!='scripts/finalize_p9_exp01.py' and file_hash(root/p)!=h:
            raise ValueError('Source/config extension thay đổi: '+p)
    selected_directory=root/result['model_directory']
    for name in ['tokenizer.json','tokenizer_config.json']:
        if file_hash(selected_directory/name)!=file_hash(root/cfg['data_directory']/name):
            raise ValueError('Tokenizer reload không khớp: '+name)
    for name,digest in [('selection_lock.json',result['selection_lock_sha256']),
                        ('history.json',lock['history_sha256']),('training_identity.json',lock['training_identity_sha256'])]:
        if file_hash(report/name)!=digest: raise ValueError('Lock/history hash thay đổi')
    history=read_json(report/'history.json'); candidates=[]; loss_comparison=[]
    datasets={s:load_asc_records(root,manifest,s) for s in ['train','validation','test']}
    train_counts=Counter(r['aspect'].casefold() for r in datasets['train'])
    for split,expected in [('train',1999),('validation',314),('test',638)]:
        frozen=load_asc_records(root,canonical,split); rows=datasets[split]
        if len(rows)!=expected or len(frozen)!=expected: raise ValueError('Count sai')
        token_fields={'input_ids','attention_mask','token_type_ids','tokens','marker_ids'}
        for a,b in zip(frozen,rows):
            if {k:v for k,v in a.items() if k not in token_fields}!={k:v for k,v in b.items() if k not in token_fields}:
                raise ValueError('Dữ liệu/representation thay đổi ngoài tokenizer')
        item=canonical['excluded_files'][split]
        if file_hash(root/item['path'])!=item['sha256']: raise ValueError('Conflict metadata thay đổi')
    for mode in cfg['training']['loss_candidates']:
        best=max([h for h in history if h['mode']==mode],key=lambda h:h['validation']['macro_f1'])
        saved=read_json(report/f'{mode}_complete.json')
        if saved['epoch']!=best['epoch'] or saved['validation_macro_f1']!=best['validation']['macro_f1']:
            raise ValueError('Candidate không được chọn qua validation')
        path=root/cfg['model_directory']/mode/'best/model.safetensors'
        if file_hash(path)!=saved['model_sha256']: raise ValueError('Candidate checkpoint thay đổi')
        actual=verify_asc_predictions(datasets['validation'],read_json(local/f'{mode}_validation_predictions.json'))
        assert_metrics(actual,best['validation'])
        candidates.append(saved); loss_comparison.append({'mode':mode,'epoch':best['epoch'],**actual})
    selected=max(candidates,key=lambda c:c['validation_macro_f1'])
    if selected!=lock['selected'] or selected!=result['selected'] or lock['test_used_for_selection']:
        raise ValueError('Model selection không khớp')
    baseline=read_json(root/'reports/p9_20261026/result.json')
    comparison={}; paired={}; error_groups={}
    for split in ['validation','test']:
        predictions=read_lines(local/f'{split}_predictions.jsonl')
        actual=verify_asc_predictions(datasets[split],predictions); assert_metrics(actual,result[split])
        old=read_lines(root/f'data/interim/p9_20261026/{split}_predictions.jsonl')
        assert_metrics(verify_asc_predictions(load_asc_records(root,canonical,split),old),baseline[split])
        counts,examples=paired_predictions(old,predictions); paired[split]=counts
        (local/f'{split}_prediction_comparison.jsonl').write_text(
            ''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in examples),encoding='utf-8')
        analyses={key:asc_error_analysis(rows,train_counts) for key,rows in [('bert',old),('deberta',predictions)]}
        error_groups[split]={key:{k:v for k,v in analysis.items() if k!='error_examples'} for key,analysis in analyses.items()}
        write_json(local/f'{split}_error_examples.json',analyses['deberta']['error_examples'])
        metrics=[('Macro F1',baseline[split]['macro_f1'],actual['macro_f1']),
                 ('Accuracy',baseline[split]['accuracy'],actual['accuracy']),
                 ('Weighted F1',baseline[split]['weighted_f1'],actual['weighted_f1'])]
        for label in LABELS:
            for metric in ['precision','recall','f1']:
                metrics.append((f'{label} {metric}',baseline[split]['per_class'][label][metric],actual['per_class'][label][metric]))
        comparison[split]=[{'Metric':name,'BERT':a,'DeBERTa':b,'Delta':b-a} for name,a,b in metrics]
        pd.DataFrame(comparison[split]).to_csv(report/f'{split}_comparison.csv',index=False)
        pd.DataFrame(actual['confusion_matrix'],index=LABELS,columns=LABELS).to_csv(report/f'{split}_confusion_matrix.csv')
    write_json(report/'loss_comparison.json',loss_comparison)
    write_json(report/'error_comparison.json',error_groups)
    delta=result['validation']['macro_f1']-baseline['validation']['macro_f1']
    duplicate_uids={r['test_uid'] for r in canonical['leakage']['official_cross_split_duplicate_texts']}
    supplementary={}
    for name,path in [('bert',root/'data/interim/p9_20261026/test_predictions.jsonl'),
                      ('deberta',local/'test_predictions.jsonl')]:
        saved=read_lines(path); clean=[p for p in saved if p['sentence_uid'] not in duplicate_uids]
        supplementary[name]={'examples':len(clean),'excluded':len(saved)-len(clean),
                             'metrics':classification_metrics([p['label_id'] for p in clean],[p['predicted_label_id'] for p in clean])}
    e2e=None
    if (report/'end_to_end_results.json').exists():
        e2e=read_json(report/'end_to_end_results.json')
        if e2e['asc_selection_lock_sha256']!=result['selection_lock_sha256'] or e2e['p8_inference_rerun']:
            raise ValueError('Joint lock/P8 không khớp')
        p8=read_json(root/cfg['p8_manifest']); old_e2e=read_json(root/'reports/p9_20261026/end_to_end_results.json')
        for split in ['validation','test']:
            rows=load_p8_records(root,p8,split); path=root/cfg['p8_predictions']/f'{split}_predictions.jsonl'
            if file_hash(path)!=e2e['splits'][split]['p8_prediction_sha256']: raise ValueError('P8 predictions hash thay đổi')
            pred_path=local/f'{split}_end_to_end_predictions.jsonl'
            if file_hash(pred_path)!=e2e['splits'][split]['prediction_sha256']: raise ValueError('Joint predictions hash thay đổi')
            actual=verify_joint_predictions(rows,read_lines(path),read_lines(pred_path)); actual.pop('decomposition')
            assert_metrics(actual,e2e['splits'][split]['metrics'])
            for key in ['gold_entities','raw_predicted_entities','predicted_entities_scored','exact_extraction_matched_spans',
                        'extraction_missing_gold_spans','extraction_spurious_predicted_spans','boundary_gold_spans','boundary_predicted_spans']:
                if actual['counts'][key]!=old_e2e['splits'][split]['metrics']['counts'][key]:
                    raise ValueError('Extraction counts thay đổi: '+key)
    frozen=read_json(report/'preservation_before.json')
    changed=[p for p,h in frozen.items() if not (root/p).is_file() or file_hash(root/p)!=h]
    if changed: raise ValueError('Frozen artifacts thay đổi: '+str(changed))
    write_json(report/'preservation.json',{'status':'PASS','files_verified_unchanged':len(frozen),'mismatches':[]})
    previous_source=read_json(report/'previous_canonical_source/manifest.json')
    old_identity=read_json(root/'reports/p9_20261026/training_identity.json')
    for name,digest in previous_source['sha256'].items():
        if file_hash(report/'previous_canonical_source'/name)!=digest:
            raise ValueError('Snapshot source BERT sai hash: '+name)
    if any(previous_source['sha256'].get(p)!=h for p,h in old_identity['source_sha256'].items()):
        raise ValueError('Source snapshot không khớp BERT training identity')
    if checks: validation=run_checks(root,report)
    else: validation=read_json(report/'validation.json') if (report/'validation.json').exists() else {'status':'PENDING'}
    if validation['status']=='PASS' and any(file_hash(root/p)!=h for p,h in validation['source_sha256'].items()):
        raise ValueError('Source đổi sau checks; cần --run-checks')
    stability=read_json(report/'stability.json') if (report/'stability.json').exists() else None
    latency=read_json(report/'validation_latency.json') if (report/'validation_latency.json').exists() else None
    if latency and (latency['status']!='COMPLETE' or latency['test_opened']):
        raise ValueError('Latency benchmark không đúng validation-only')
    if latency:
        for name,sha in [('bert',baseline['selected']['model_sha256']),('deberta',selected['model_sha256'])]:
            if latency['results'][name]['model_sha256']!=sha or latency['results'][name]['examples']!=314:
                raise ValueError('Latency benchmark sai checkpoint/validation size')
    smoke=read_json(report/'inference_smoke.json')
    if smoke['status']!='PASS' or smoke['test_opened'] or smoke['source_split']!='validation':
        raise ValueError('CPU API smoke không PASS')
    if stability:
        if [s['seed'] for s in stability]!=[43,44]: raise ValueError('Thiếu stability seed43/44')
        for stable in stability:
            if stable['status']!='VALIDATION_ONLY_COMPLETE' or stable['test_opened']:
                raise ValueError('Stability không được mở test')
            namespace=Path(stable['model_directory']).parts[2]
            if not namespace.startswith(f"{NAMESPACE}_seed{stable['seed']}"):
                raise ValueError('Stability namespace không đúng seed')
            stable_cfg=load_p9_config(root/f'configs/{namespace}.yaml')
            stable_report=root/stable_cfg['report_directory']; stable_local=root/stable_cfg['prediction_directory']
            stable_identity=read_json(stable_report/'training_identity.json')
            stable_lock=read_json(stable_report/'selection_lock.json')
            if (stable_cfg['primary_selection_lock_sha256']!=result['selection_lock_sha256']
                    or stable_cfg['training']['loss_candidates']!=[selected['mode']]
                    or stable_cfg['training']!={**cfg['training'],'loss_candidates':[selected['mode']]}
                    or stable_identity['config']!=stable_cfg
                    or stable_lock['test_used_for_selection']
                    or stable['selection_lock_sha256']!=file_hash(stable_report/'selection_lock.json')):
                raise ValueError('Stability config/selection không khớp primary')
            if file_hash(root/stable_cfg['data_directory']/'manifest.json')!=stable_identity['data_manifest_sha256']:
                raise ValueError('Stability manifest thay đổi')
            if read_json(root/stable_cfg['data_directory']/'manifest.json')['files']!=manifest['files']:
                raise ValueError('Stability không reuse cache token primary')
            if stable_identity['source_sha256']!=identity['source_sha256']:
                raise ValueError('Stability code khác primary')
            if (stable_report/'test_metrics.json').exists() or (stable_local/'test_predictions.jsonl').exists():
                raise ValueError('Phát hiện official test artifact ở stability')
            if file_hash(root/stable['model_directory']/'model.safetensors')!=stable_lock['selected']['model_sha256']:
                raise ValueError('Stability checkpoint thay đổi')
            stable_actual=verify_asc_predictions(datasets['validation'],read_lines(stable_local/'validation_predictions.jsonl'))
            assert_metrics(stable_actual,stable['validation'])
            stable_best=max(read_json(stable_report/'history.json'),key=lambda h:h['validation']['macro_f1'])
            if (stable_best['epoch']!=stable['selected']['epoch']
                    or stable_best['validation']['macro_f1']!=stable['selected']['validation_macro_f1']):
                raise ValueError('Stability checkpoint rule khác primary')
    summary={'status':'VERIFIED' if validation['status']=='PASS' else 'PENDING_CHECKS','experiment':'P9-EXP01',
             'selected':selected,'validation_delta_macro_f1':delta,'validation_improved':delta>0,
             'comparison':comparison,'paired':paired,'result':result,'loss_comparison':loss_comparison,
             'supplementary_excluding_natural_duplicate':supplementary,
             'end_to_end':e2e,'stability':stability,'validation_latency':latency,'test_used_for_selection':False,'p8_retrained':False,'split_changed':False,'p10_implemented':False,
             'finalizer_sha256':file_hash(root/'scripts/finalize_p9_exp01.py'),
             'canonical_decision':read_json(report/'canonical_decision.json'),
             'inference_smoke':smoke,
             'frozen_files_verified':len(frozen),'tests':validation}
    write_json(report/'comparison.json',summary)
    lines=['# P9-EXP01 — DeBERTa-v3-base ASC',
           f"Trạng thái: {summary['status']}. Dữ liệu P9 frozen, đổi backbone sang `{cfg['pretrained_model']}`; revision model/tokenizer `{cfg['revision']}`.",
           '## Protocol và nguồn tham khảo',
           'Tái sử dụng processed P9:1999train/314validation/638official test. Giữ text, offsets, ID, labels, conflict sidecar, đúng occurrence, `[unused0]`/`[unused1]`, single sequence `[CLS] context_before [unused0] target [unused1] context_after [SEP]`, max128; không truncate. Tokenizer native DeBERTa thay WordPiece là thay đổi bắt buộc của backbone, marker IDs128001/128002, resize/save/reload vocabulary128003. Các trường thống kê split BERT kế thừa mô tả nguồn frozen; `marker_ids` và `token_lengths` mô tả cache DeBERTa thực tế (max94/59/87).',
           'Repo https://github.com/ParhamVaryn/transformer-absa-semeval chỉ tham khảo model/range LR; xem `reference.json` có commit. Không lấy code, dataset, normalization, split, sentence pair, focal loss, marker TGT, early stopping hoặc best-of-seeds của repo đó.',
           'Chọn bằng validation Macro F1, tie giữ candidate đầu/epoch sớm; official test chỉ một pass sau selection lock. P8 frozen, không dùng predicted aspects để chọn ASC. Unweighted/balanced như P9, LR3e-5,5epoch,seed42,AdamW,weight decay0.01,warmup0.1; physical batch4×accum4=effective16 so với BERT8×2. Eager attention do kiến trúc DeBERTa; FP32 parameters và FP16 autocast. Không search LR/epoch schedule khác BERT nên đây là so sánh primary config, không khẳng định backbone đã tối ưu toàn cục.',
           'Giữ natural official train/test duplicate và train-only whitespace adjustment đã công bố ở P8/P9; không sửa raw hoặc resplit. Nguồn/license SemEval vẫn NOT_VERIFIED theo ngoại lệ P1, không tải dataset mới từ repo tham khảo. Split thống kê gốc vẫn seed42; seed43/44 chỉ thay khởi tạo/order training, không thay split.',
           f"Best: {selected['mode']}, epoch{selected['epoch']}; validation Macro F1={selected['validation_macro_f1']:.6f}.",
           '## Validation',table(pd.DataFrame(comparison['validation'])),'## Official test',table(pd.DataFrame(comparison['test'])),
           'Confusion matrices: `validation_confusion_matrix.csv`, `test_confusion_matrix.csv`; hàng=gold,cột=prediction, thứ tự negative/neutral/positive.',
           'Supplementary loại natural duplicate, chỉ từ saved predictions; không chọn lại model hoặc thay score638mẫu canonical:',
           table(pd.DataFrame([{'Model':name,'Examples':s['examples'],'Excluded':s['excluded'],
                                **{k:s['metrics'][k] for k in ['macro_f1','accuracy','weighted_f1']}} for name,s in supplementary.items()])),
           '## Prediction/error comparison',table(pd.DataFrame([{'Split':s,**c} for s,c in paired.items()])),
           'Các file comparison/error_examples chứa review text ở data/interim, chỉ local. `error_comparison.json` dùng đúng taxonomy P9: neutral→negative/positive và đảo positive↔negative từ matrix; negation, mixed polarity, rare aspects, contrast cues, long context proxy. Implicit sentiment và long-distance cause vẫn NOT_MEASURED, không giả tạo human tags. Các nhóm chồng lấn, không coi cues là nguyên nhân xác minh.',
           '## Neutral và weighting']
    for split in ['validation','test']:
        a=baseline[split]['per_class']['neutral']; b=result[split]['per_class']['neutral']
        matrix=result[split]['confusion_matrix']
        contributions={l:(result[split]['per_class'][l]['f1']-baseline[split]['per_class'][l]['f1'])/3 for l in LABELS}
        lines.append(f"{split}: neutral recall {a['recall']:.6f}→{b['recall']:.6f}, F1 {a['f1']:.6f}→{b['f1']:.6f}; neutral→negative={matrix[1][0]}, neutral→positive={matrix[1][2]}. Đóng góp delta macro F1 (delta F1 lớp/3): {contributions}.")
    lines.extend([table(pd.DataFrame([{'Loss':c['mode'],'Epoch':c['epoch'],'Val Macro F1':c['macro_f1'],
                                     'Neutral F1':c['per_class']['neutral']['f1'],'Neutral recall':c['per_class']['neutral']['recall']} for c in loss_comparison])),
                  '## End-to-end'])
    if e2e:
        metrics=e2e['splits']['test']['metrics']; old=read_json(root/'reports/p9_20261026/end_to_end_results.json')['splits']['test']['metrics']
        lines.extend([table(pd.DataFrame([{'Metric':k,'BERT':old[k],'DeBERTa':metrics[k],'Delta':metrics[k]-old[k]} for k in ['precision','recall','f1']])),
                      table(pd.DataFrame([{'Count':k,'BERT':old['counts'][k],'DeBERTa':metrics['counts'][k]} for k in
                                          ['extraction_missing_gold_spans','boundary_gold_spans','boundary_predicted_spans',
                                           'sentiment_errors_on_exact_span','joint_wrong_span_and_polarity_pairs',
                                           'true_positive','false_positive','false_negative']])),
                      'Extraction counts được kiểm độc lập không đổi; xem counts/decomposition trong end_to_end_results.json và data/interim. FN=missing extraction+sentiment sai trên exact span; boundary/joint overlap không cộng thành causal fractions.'])
    else:
        lines.append('Chưa chạy. Nếu không thắng validation, không rerun canonical end-to-end.')
    lines.extend(['## Chi phí và sự cố',
                  table(pd.DataFrame([{'Measure':k,'BERT':baseline[k],'DeBERTa':result[k]} for k in
                                      ['training_seconds','runtime_seconds_including_checkpoint_io','artifact_bytes',
                                       'peak_process_rss_bytes_current_process','peak_gpu_allocated_bytes','peak_gpu_reserved_bytes',
                                       'inference_ms_per_gold_aspect_from_tokens']])),
                  'Train seconds là tổng loops hai loss×5epoch, không tính validation/checkpoint I/O. Latency là trung bình batched từ tokens (BERT eval batch16, DeBERTa8), không phải latency raw-text/single-request; không quy mọi khác biệt tốc độ cho backbone khi batch khác. Cùng máy GPU và stack Torch/Transformers, không đo tiền compute.',
                  f"Train loops {result['training_seconds']:.3f}s; wall {result['runtime_seconds_including_checkpoint_io']:.3f}s; selected artifact {result['artifact_bytes']}bytes; RSS {result['peak_process_rss_bytes_current_process']}bytes; peak GPU allocated/reserved {result['peak_gpu_allocated_bytes']}/{result['peak_gpu_reserved_bytes']}bytes; latency {result['inference_ms_per_gold_aspect_from_tokens']:.3f}ms/gold aspect từ tokens. Versions: {result['versions']}. GPU: {result['gpu_name']}. Tiền compute NOT_MEASURED.",
                  'Namespace cũ `p9_exp01_deberta_20261026` INVALID_FOR_COMPARISON, không dùng bất kỳ score nào: initial attempt dừng trước epoch hoàn tất/test do FP16 parameters không hợp GradScaler; sửa explicit float32 parameters. Sau đó phát hiện Transformers5 conversion thiếu CLS/SEP, dừng trước selection/test, giữ toàn bộ checkpoint/logs; tokenizer v2 khôi phục post_processor CLS/SEP chuẩn và restart pretrained. Không đổi representation P9 frozen. Xem attempts.json và invalid_attempt.json của namespace cũ. Tokenizer cần sentencepiece0.2.1/protobuf6.33.5, không đổi Transformers/PyTorch.',
                  'Seed43 bị turn interruption giữa epoch5. Resume bị chặn trước train/test vì nhánh resume lấy vocab128100 từ pretrained thay vì vocab128003 đã resize; không đổi trainer/source sau primary. Giữ attempt bị ngắt, chạy seed43 lại hoàn toàn từ pretrained trong namespace `_seed43_restart01`. Chỉ completed restart được dùng trong stability. Resume DeBERTa hiện NOT_SUPPORTED, fresh-run/reload đã xác minh; xem resume_event.json và logs. Tổng chi phí mọi attempt bị ngắt/lỗi NOT_MEASURED, không gộp giả vào primary/stability runtime.',
                  '## Quyết định canonical và giới hạn',
                  f"Validation delta Macro F1={delta:+.6f}; quyết định canonical ghi tại canonical_decision.json sau xem bằng chứng validation, không dùng official test hoặc joint F1 để chọn.",
                  f"Trạng thái quyết định: `{summary['canonical_decision']['status']}`. {summary['canonical_decision'].get('reason','Đang chờ stability/checks, chưa thay canonical.')}",
                  'Single-seed primary comparison; stability ghi riêng nếu có, không thay trực tiếp single-seed baseline bằng multi-seed mean. Không khẳng định ưu thế thống kê. Chỉ laptop tiếng Anh; nhãn Amazon đại diện suy từ số sao có nhiễu; SemEval-to-Amazon platform/style shift chưa đo; bộ gold người chú thích nhỏ P10 vẫn PENDING. Confidence null; chưa production/tiếng Việt. Không triển khai P10.',
                  '## Tái lập',
                  'Previous canonical BERT được giữ nguyên artifacts và có snapshot11source files tại previous_canonical_source/, khớp chính xác SHA256 validation/training identity frozen. Đây là archive provenance, không phải pipeline active thứ hai; snapshot được khôi phục bằng đảo các edit của tác vụ và chỉ chấp nhận bytes khớp hash frozen.',
                  'CPU classifier + raw P8→ASC pipeline smoke PASS trên validation (inference_smoke.json), kiểm labels/confidence/empty aspects/unsupported vi, không mở test. Latency bổ sung dùng benchmark_validation_latency.py; lượt đầu chồng CPU smoke được giữ riêng, số báo cáo là lượt chạy riêng sau khi cả hai process kết thúc.',
                  '`.venv/Scripts/python.exe -X utf8 -m scripts.p9_exp01 prepare` rồi `train` chỉ cho namespace chưa chạy; completed training bị khóa. Xác minh từ saved predictions: `.venv/Scripts/python.exe -X utf8 -m scripts.finalize_p9_exp01 --run-checks`. Không chạy finalizer P9 cũ để ghi đè frozen evidence.',
                  f"Tests: {validation.get('total_passed','PENDING')} PASS; frozen artifact checks: {len(frozen)} files giữ hash."])
    if stability:
        import statistics
        values=[result['validation']['macro_f1']]+[s['validation']['macro_f1'] for s in stability]
        stability_lines=['## Stability validation — tách khỏi canonical comparison',
                      table(pd.DataFrame([{'Seed':42,'Val Macro F1':values[0],'Epoch':selected['epoch']}]+
                                         [{'Seed':s['seed'],'Val Macro F1':s['validation']['macro_f1'],'Epoch':s['selected']['epoch']} for s in stability])),
                      f"Mean={statistics.mean(values):.6f}, sample std={statistics.stdev(values):.6f}. Cùng best loss/LR/max-epochs và checkpoint rule; không chọn seed tốt nhất, không thay seed42 bằng mean hoặc seed43/44, không mở official test của stability. BERT chưa có multi-seed tương đương nên đây không phải so sánh hai multi-seed means."]
        index=lines.index('## Quyết định canonical và giới hạn'); lines[index:index]=stability_lines
    if latency:
        index=lines.index('## Chi phí và sự cố')+1
        lines[index:index]=['So sánh latency bổ sung: cùng314validation IDs, CUDA, batch16, FP16, warmup1full pass và3passes đo, medianms/aspect từ tokens; không mở official test:',
                           table(pd.DataFrame([{'Model':name,'Median ms/aspect':v['median_ms_per_aspect_from_tokens'],
                                                'Predictions match saved':v['predictions_identical_to_saved']} for name,v in latency['results'].items()]))]
    (report/'report.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-checks',action='store_true')
    args=parser.parse_args(); result=finalize(checks=args.run_checks)
    print(json.dumps({k:result[k] for k in ['status','selected','validation_delta_macro_f1','paired']}),flush=True)
