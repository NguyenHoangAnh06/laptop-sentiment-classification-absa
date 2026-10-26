"""Phân tích lỗi/proxy/mất cân bằng từ artifact đã khóa; không train/predict."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT
from src.evaluation.error_diagnosis import file_hash,load_predictions,error_tables,imbalance_evidence,weighting_pairs
from src.evaluation.classification import classification_metrics
from src.evaluation.sentiment_audit import prepare_audit,evaluate_audit,read_annotations
from scripts.verify_kaggle_results import verify_package

KIT='data/manual/sentiment_diagnosis_20261024'
START='<!-- error_diagnosis:start -->'
END='<!-- error_diagnosis:end -->'


def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def table_md(frame,columns=None):
    columns=columns or list(frame.columns)
    lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
    for row in frame[columns].itertuples(index=False,name=None):
        lines.append('| '+' | '.join(f'{v:.6f}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(lines)


def attach_summary(root,summary):
    """Giữ phần chẩn đoán qua các lần sinh lại báo cáo benchmark."""
    block='\n'.join([START,'## Chẩn đoán lỗi, proxy rating và mất cân bằng','',
        'Đã phân tích saved predictions hiện hành của6model, gồm TabPFN cloud full21K. CSV p7_error_* và p7_class_diagnostics.csv hiện dùng provenance active; snapshot local cũ giữ riêng. Bất đồng với proxy không tự được tính là lỗi sentiment thật.',
        '',f"Neutral train {summary['neutral_train_count']}/{summary['train_count']} ({summary['neutral_train_share']:.2%}); đã tổng hợp weighted/unweighted BERT trên validation. Trọng số cải thiện recall neutral ở candidate tốt nhất từng mode nhưng macro F1 không tăng; chưa định lượng được phần lỗi do mất cân bằng.",
        '',f"Bộ audit đọc mù tại `{KIT}/review_annotation.csv`: {summary['audit']['representative_n']}mẫu đại diện+{summary['audit']['diagnostic_n']}ca chọn chủ đích. Chưa có human labels; không gọi đây là independent gold.",
        '', '**BLOCKED:** chưa có nhãn sentiment do người gán nên chưa đo được proxy–human disagreement hoặc tỷ lệ lỗi quy cho proxy. **NEXT_ACTION:** người dùng gán nhãn đọc mù, sau đó chạy evaluator được hướng dẫn trong `docs/SENTIMENT_DIAGNOSIS.md`.',
        '', 'Chi tiết: `reports/p7_error_cause_analysis.md`/`.json`. Phân tích mô tả và phần tooling hoàn tất; phân bổ nguyên nhân thực/human audit vẫn PENDING. Không retrain hoặc chọn lại bằng test.',END])
    for name in ['p7_unified_benchmark.md','model_stack_refactor_completion.md']:
        path=root/'reports'/name
        content=path.read_text(encoding='utf-8')
        if START in content:content=content[:content.index(START)]+block+content[content.index(END)+len(END):]
        else:content=content.rstrip()+'\n\n'+block+'\n'
        path.write_text(content,encoding='utf-8')
    p=root/'reports/p7_completion.json';completion=json.loads(p.read_text(encoding='utf-8'))
    completion.update(error_analysis_report='reports/p7_error_cause_analysis.md',
                      error_analysis_status='DESCRIPTIVE_COMPLETE_CURRENT_SIX_MODELS',
                      human_cause_attribution_status='PENDING_HUMAN_ANNOTATION',independent_gold_status='PENDING_NOT_CREATED')
    write_json(p,completion)


def analyze(root=PROJECT_ROOT, *, refresh_human=True):
    root=Path(root)
    human_path=root/'reports/p7_human_audit_results.json'
    if refresh_human and human_path.exists():
        previous=json.loads(human_path.read_text(encoding='utf-8'))
        if previous.get('status')=='HUMAN_REVIEWED_DIAGNOSIS_COMPLETE':
            if previous['integrity']['annotation_sha256']!=file_hash(root/KIT/'review_annotation.csv'):
                raise ValueError('Annotation thay đổi sau xác nhận human; cần evaluate lại có xác nhận')
    benchmark_hash=file_hash(root/'reports/p7_unified_results.csv')
    completion=json.loads((root/'reports/p7_completion.json').read_text(encoding='utf-8'))
    receipt=json.loads((root/'reports/tabpfn_kaggle_full21k_verification.json').read_text(encoding='utf-8'))
    verified=verify_package(root/receipt['artifact_directory'],root)
    if verified['integrity_status']!='PASS' or any(v['status']!='SUCCESS' for v in verified['models'].values()):raise ValueError('Cloud provenance chưa verified')
    frames={s:pd.read_parquet(root/'data/processed/splits/p4_20261009_final'/f'{s}.parquet') for s in ['train','validation','test']}
    predictions,provenance=load_predictions(root,frames['test'],completion)
    tables=error_tables(frames['test'],predictions)
    history_path=root/'reports/semantic_20261024/E05_transformer/history.json'
    history=json.loads(history_path.read_text(encoding='utf-8'))
    distribution,weighted=imbalance_evidence(frames,history)
    arrays={mode:np.load(history_path.parent/f'{mode}_validation.npy',allow_pickle=False)
            for mode in ['unweighted','balanced']}
    for mode,array in arrays.items():
        expected=weighted[(weighted['mode']==mode)&weighted.selected_within_mode_by_validation_macro_f1].iloc[0]
        actual=classification_metrics(frames['validation'].label_id,array)
        if not np.isclose(actual['macro_f1'],expected.validation_macro_f1,atol=1e-12,rtol=0):
            raise ValueError('Saved weighting predictions không khớp history')
    paired=weighting_pairs(frames['validation'].label_id,arrays['unweighted'],arrays['balanced'])
    paired.to_csv(root/'reports/p7_weighting_paired_validation.csv',index=False)
    names={'groups':'p7_error_groups.csv','transitions':'p7_error_transitions.csv','classes':'p7_class_diagnostics.csv',
           'ratings':'p7_error_by_rating.csv','examples':'p7_error_examples.csv','agreement':'p7_error_agreement.csv'}
    for key,name in names.items():tables[key].to_csv(root/'reports'/name,index=False)
    distribution.to_csv(root/'reports/p7_class_distribution.csv',index=False)
    weighted.to_csv(root/'reports/p7_weighting_validation.csv',index=False)
    interim=root/'data/interim/p7_diagnosis';interim.mkdir(parents=True,exist_ok=True)
    tables['review_predictions'].to_parquet(interim/'review_predictions.parquet',index=False)
    inputs={'split_sha256':{s:file_hash(root/'data/processed/splits/p4_20261009_final'/f'{s}.parquet') for s in frames},
            'prediction_sources':provenance,'bert_history_sha256':file_hash(history_path)}
    audit=prepare_audit(frames['test'],tables['review_predictions'],root/KIT,inputs)
    annotations,_,_=read_annotations(root/KIT,require_complete=False)
    neutral=distribution.query("split=='train' and `class`=='neutral'").iloc[0]
    neutral_pair=paired[paired['class']=='neutral'].iloc[0]
    best=weighted[weighted.selected_within_mode_by_validation_macro_f1]
    unweighted=best[best['mode']=='unweighted'].iloc[0];balanced=best[best['mode']=='balanced'].iloc[0]
    summary={'status':'DESCRIPTIVE_ANALYSIS_COMPLETE_HUMAN_ATTRIBUTION_PENDING','inputs':inputs,'model_count':len(predictions),
             'test_count':len(frames['test']),'train_count':len(frames['train']),
             'neutral_train_count':int(neutral['count']),'neutral_train_share':float(neutral['share']),
             'weighting_validation_macro_f1_delta':float(balanced.validation_macro_f1-unweighted.validation_macro_f1),
             'weighting_validation_neutral_recall_delta':float(balanced.neutral_recall-unweighted.neutral_recall),
             'weighting_validation_neutral_precision_delta':float(balanced.neutral_precision-unweighted.neutral_precision),
             'weighting_validation_neutral_f1_delta':float(balanced.neutral_f1-unweighted.neutral_f1),
             'weighting_pair_sources':{mode:file_hash(history_path.parent/f'{mode}_validation.npy') for mode in arrays},
             'audit':{**audit,'annotation_path':KIT+'/review_annotation.csv',
                      'nonempty_human_sentiments':int(annotations.human_sentiment.ne('').sum())},
             'causes':{'class_imbalance_presence':'MEASURED','class_imbalance_error_fraction':'NOT_IDENTIFIABLE',
                       'proxy_human_mismatch_rate':'NOT_MEASURED','model_vs_proxy_disagreement':'MEASURED',
                       'gold_evaluation':'PENDING_NOT_CREATED'},
             'benchmark_csv_sha256':benchmark_hash,
             'tests_evidence':'reports/p7_error_diagnosis_validation.json',
             'BLOCKED':'Chưa có human sentiment annotations; không định lượng nhiễu proxy hoặc phần lỗi causal.',
             'NEXT_ACTION':'Người đọc gán nhãn bộ audit; đánh giá riêng representative/enriched, không dùng để tuning.',
             'no_training_or_inference':True,'test_tuning':False,'benchmark_metrics_unchanged':True}
    write_json(root/'reports/p7_error_cause_analysis.json',summary)
    classes=tables['classes'];neutral_table=classes[classes['class']=='neutral']
    report=['# Chẩn đoán lỗi sentiment: model, proxy rating và mất cân bằng','',
            '**Hoàn tất phân tích mô tả và tooling; phân bổ nguyên nhân thực còn PENDING human audit.** Không train/predict lại, không đổi split/embeddings/nhãn hoặc selection. Đầu vào là6saved predictions hiện hành, cả V3/V3_5 full21K đã reverify. Hash nguồn và trạng thái đầy đủ trong JSON cùng tên.',
            '', '## 1. Phân biệt câu hỏi','',
            '| Câu hỏi | Bằng chứng hiện có | Kết luận cho phép |','|---|---|---|',
            '| Model bất đồng rating proxy ở đâu? | Predictions/IDs/y_true được đối chiếu, confusion/strata | Đo được bất đồng proxy, chưa phải lỗi với human gold |',
            '| Có mất cân bằng không? | Phân phối train/val/test và predicted shares | Có; mức đóng góp vào từng lỗi chưa xác định |',
            '| Weighted loss có giúp không? | BERT unweighted/balanced từ history validation đã khóa | Recall/precision/macro có trade-off, không giải thích toàn bộ lỗi |',
            '| Rating proxy có sai sentiment không? | Cần người đọc độc lập với rating/predictions | NOT_MEASURED tới khi có annotation hợp lệ |',
            '| Lỗi do mất cân bằng hay proxy bao nhiêu phần trăm? | Chưa có causal experiment/human evidence đủ | Không cộng/trừ hai nguyên nhân như hai tập loại trừ nhau |',
            '', '## 2. Phân phối lớp và mức dự đoán neutral','',table_md(distribution,['split','class','count','share','inverse_frequency_weight_train']),
            '', 'Trọng số inverse_frequency_weight_train chỉ tính từ train N/(3*n_class), không fit lại. Neutral ít là thực tế quan sát; điều này không chứng minh mọi neutral bị bỏ sót là do mất cân bằng.',
            '',table_md(neutral_table,['model','support','predicted_count','predicted_share','precision','recall','f1','proxy_disagreements','error_rate_within_class']),
            '', 'support và error_rate dùng mẫu số true proxy class. predicted_share dùng toàn4500test. Precision/recall theo proxy, không theo human gold; predicted neutral cực ít cũng có thể liên quan representation/priors/model/preprocessing/nhãn mơ hồ.',
            '', 'Cùng một test distribution nhưng mức dự đoán neutral rất khác: V3=8,V3_5=48,BERT=381 trên394proxy neutral. Mất cân bằng là điều kiện chung; các bảng này không đủ để coi nó là lời giải thích duy nhất cho khác biệt giữa các model.',
            '', '## 3. Bằng chứng weighted/unweighted hiện có','',table_md(weighted),
            '', 'Chọn epoch trong từng loss bằng validation macro F1, không chọn epoch chỉ vì neutral F1. Không rerun balanced test hoặc thay model đã chọn. Hai candidate tốt nhất:',
            '',table_md(best),
            '',f"Balanced trừ unweighted: macro F1={summary['weighting_validation_macro_f1_delta']:+.6f}; neutral precision={summary['weighting_validation_neutral_precision_delta']:+.6f}; recall={summary['weighting_validation_neutral_recall_delta']:+.6f}; F1={summary['weighting_validation_neutral_f1_delta']:+.6f}.",
            '', 'Weighted tăng neutral recall/F1 nhưng giảm precision và macro F1 ở candidate tốt nhất từng mode, nên giữ unweighted theo protocol. Đây là bằng chứng sensitivity đối với weighting trong một run/một seed; chưa phải ước lượng causal error fraction, không chứng minh imbalance là nguyên nhân duy nhất. Trọng số có thể khuếch đại cả noisy minority labels. Không suy diễn hiệu ứng cho TabPFN/XGBoost/TabM khi chưa có ablation tương ứng.',
            '',table_md(paired),
            '',f"Riêng neutral validation: balanced sửa được {int(neutral_pair.corrected_by_balanced)}ca unweighted bất đồng proxy, đồng thời làm sai thêm {int(neutral_pair.regressed_by_balanced)}ca; false positives neutral tăng từ{int(neutral_pair.unweighted_false_positives)} lên{int(neutral_pair.balanced_false_positives)}. Đây là trade-off quan sát được, không phải nhãn nguyên nhân của từng review.",
            '', 'Paired counts dùng hai mảng validation đã lưu của candidate tốt nhất từng mode; macro được tính lại và khớp history. Row order theo val_loader cố định trong runner; balanced không có một file ID riêng. Bốn cột both_correct/corrected/regressed/both_wrong cộng bằng support từng lớp. False positives có mẫu số là các review ngoài lớp đó; không cộng vào support lớp nguồn. Các thay đổi chưa chứng minh causal contribution của imbalance hoặc tỷ lệ noisy labels.',
            '', '## 4. Lỗi theo nhóm và agreement giữa model','',
            'Các CSV active mới: p7_error_groups.csv (all/short<=10/long>200/negation/mixed lexical/proxy_neutral), p7_error_transitions.csv (đủ3x3, có support và tỷ lệ theo lớp nguồn), p7_error_by_rating.csv, p7_class_diagnostics.csv và p7_error_agreement.csv. Nhóm lexical chồng lấn, không phải annotation semantic; không hardcode aspect findings.',
            '',table_md(tables['agreement']),
            '', 'Agreement chỉ dùng5model cạnh tranh, loại majority sanity. Ngay cả5model cùng bất đồng proxy vẫn chỉ là ca ưu tiên đọc, không phải bằng chứng proxy sai. Đồng thuận cũng có thể cùng sai. p7_error_examples.csv có excerpt đã lọc mẫu liên hệ phổ biến, confidence trống/human_verified=False, chỉ giữ local; chưa audit PII đầy đủ, không tự publish review text.',
            '', '## 5. Audit rating–text đọc mù và cách phân loại','',
            f"Đã tạo `{KIT}/review_annotation.csv`: {audit['representative_n']}SRS không hoàn lại từ4500test và{audit['diagnostic_n']}ca ưu tiên nhiều model bất đồng proxy (tối đa20mỗi lớp), rời nhau. Seed42, full text chỉ trong data/manual được ignoreGit. Phiếu không chứa rating/proxy/model/group; private_reference.json giữ mapping/selection/predictions và fingerprint nguồn. Chạy lại không overwrite trường người đã nhập.",
            '', 'Nhóm representative dùng để ước lượng bất đồng proxy–human trong **test population4500** sau khi annotation đầy đủ; không khái quát thẳng sang toàn30K. Nhóm enriched chỉ tìm kiểu lỗi, không dùng prevalence và không gộp tỷ lệ với representative. uncertain giữ riêng, không chuyển neutral. Có khoảng tin cậy exact hypergeometric95% khi representative đủ decisive labels; nếu uncertain thì báo tỷ lệ có điều kiện và cận mô tả trên mẫu, không tự điền nhãn.',
            '', '| Proxy so với human | Model so với human | Diễn giải có thể ghi |','|---|---|---|',
            '| Khớp | Khớp | Cả hai khớp human |','| Khớp | Không khớp | Model error theo human; chưa biết causal mechanism |',
            '| Không khớp | Khớp | Proxy–human mismatch; model khớp human |','| Không khớp | Không khớp | Cả proxy/model bất đồng human; không ép thành một nguyên nhân |',
            '', 'Cảm xúc mixed/insufficient_context được lưu riêng cùng bằng chứng và người gán/ngày. Đọc hướng dẫn `docs/SENTIMENT_DIAGNOSIS.md`; evaluator chỉ chạy khi người vận hành xác nhận human review. Validator không thể tự chứng minh danh tính người gán.',
            '', '**BLOCKED:** chưa có human sentiment annotations. **NEXT_ACTION:** người dùng hoàn thành phiếu đọc mù, sau đó chạy evaluator. Không có tỷ lệ nhiễu nhãn thật/human accuracy được tạo trong tác vụ này. Bộ này là audit chẩn đoán reused test, **không phải independent P10 gold**; P10 vẫn cần bộ gold sentiment+ABSA độc lập.',
            '', '## 6. Giới hạn và trạng thái','',
            'Phân tích test chỉ mô tả sau selection, không quay lại tune/relabel train hoặc đổi benchmark. Score và ranking chính giữ nguyên. Các nguyên nhân có thể cùng xuất hiện; không thể gán nhãn “do imbalance” cho từng review chỉ từ rating/prediction. Human audit hỗ trợ phân biệt model/proxy theo cách người đọc hiểu text, không chứng minh causal contribution của class imbalance.',
            '', 'Chỉ laptop tiếng Anh; noisy star-derived proxy; SemEval-to-Amazon platform/style shift thuộc ABSA; gold thủ công dự kiến nhỏ/chưa có. Không production/model tiếng Việt/statistical superiority. Snapshot local subsample vẫn giữ trong reports/history/tabpfn_before_kaggle_20261024; CSV p7_error_* hiện thay bằng phân tích active6model, không mất bản cũ.',
            '', '## Xác minh công cụ','',
            'Kết quả test/commands/source hashes mới nhất: `reports/p7_error_diagnosis_validation.json`; bảo toàn scientific files/legacy và xác nhận human fields trống trong `reports/p7_error_diagnosis_preservation.json`. Báo cáo import cloud giữ bằng chứng kiểm thử của tác vụ import, không thay cho kiểm thử chẩn đoán mới.']
    (root/'reports/p7_error_cause_analysis.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    attach_summary(root,summary)
    if refresh_human and human_path.exists():
        previous=json.loads(human_path.read_text(encoding='utf-8'))
        if previous.get('status')=='HUMAN_REVIEWED_DIAGNOSIS_COMPLETE':
            from src.evaluation.human_diagnosis import finalize_diagnosis
            finalize_diagnosis(root,confirmed_human_review=True)
            summary=json.loads((root/'reports/p7_error_cause_analysis.json').read_text(encoding='utf-8'))
    if file_hash(root/'reports/p7_unified_results.csv')!=benchmark_hash:raise ValueError('Không được sửa metric benchmark trong analysis')
    return summary


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluate-audit',action='store_true');p.add_argument('--confirm-human-review',action='store_true')
    p.add_argument('--kit',type=Path,default=PROJECT_ROOT/KIT)
    a=p.parse_args()
    if a.evaluate_audit:
        if a.kit.resolve()!=(PROJECT_ROOT/KIT).resolve():
            result=evaluate_audit(a.kit,confirmed_human_review=a.confirm_human_review)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return
        # Kiểm đầy đủ trước khi cập nhật report để không mất trạng thái khi input lỗi.
        from src.evaluation.human_diagnosis import validate_sources,finalize_diagnosis
        evaluate_audit(a.kit,confirmed_human_review=a.confirm_human_review)
        validate_sources(PROJECT_ROOT,a.kit)
        analyze(refresh_human=False)
        finalize_diagnosis(PROJECT_ROOT,confirmed_human_review=a.confirm_human_review)
        print('P7: DONE — READY FOR P8; không thay benchmark hoặc model.')
    else:
        result=analyze();print(result['status'])

if __name__=='__main__':main()
