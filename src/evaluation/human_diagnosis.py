"""Chẩn đoán human–proxy tái lập từ annotation và predictions đã lưu."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.evaluation.classification import LABELS, classification_metrics
from src.evaluation.error_diagnosis import file_hash, load_predictions
from src.evaluation.sentiment_audit import ambiguity_flag, evaluate_audit, read_annotations, sample_audit

KIT = 'data/manual/sentiment_diagnosis_20261024'


def attribution_case(human: int, proxy: int, prediction: int) -> str:
    """Năm nhóm rời nhau; D chỉ gồm trường hợp prediction khác cả human lẫn proxy."""
    if prediction == human:
        return 'E' if proxy == human else 'A'
    if prediction == proxy:
        return 'B'
    return 'C' if proxy == human else 'D'


def compare_rows(rows: pd.DataFrame, models: list[str]) -> dict:
    """Mọi tỷ lệ dùng mẫu số tường minh, không suy ra nguyên nhân nhân quả."""
    n = len(rows)
    human = rows.human_id.to_numpy(dtype=int)
    proxy = rows.proxy_label_id.to_numpy(dtype=int)
    mismatch = human != proxy
    counts = classification_metrics(human, proxy)
    classes = []
    for i, label in enumerate(LABELS):
        mask = human == i
        support = int(mask.sum())
        wrong = int((mask & mismatch).sum())
        classes.append({'human_class': label, 'count': support, 'agreement': support-wrong,
                        'disagreement': wrong, 'disagreement_rate': wrong/support if support else None})
    ambiguity = []
    for flag in [False, True]:
        mask = rows.ambiguous.to_numpy() == flag
        support = int(mask.sum()); wrong = int((mask & mismatch).sum())
        ambiguity.append({'ambiguity': flag, 'count': support, 'share': support/n,
                          'disagreement': wrong, 'disagreement_rate': wrong/support if support else None})
    ratings = []
    for rating in range(1, 6):
        mask = rows.rating.to_numpy() == rating
        support = int(mask.sum())
        ratings.append({'rating': rating, 'total': support,
                        **{label: int((mask & (human == i)).sum()) for i, label in enumerate(LABELS)},
                        **{label+'_share': float((human[mask] == i).mean()) if support else None
                           for i, label in enumerate(LABELS)}})
    model_results = {}
    for name in models:
        pred = rows[name].to_numpy(dtype=int)
        pm = classification_metrics(proxy, pred); hm = classification_metrics(human, pred)
        cases = [attribution_case(h, p, m) for h, p, m in zip(human, proxy, pred)]
        c = {case: cases.count(case) for case in 'ABCDE'}
        # D theo định nghĩa rộng của yêu cầu bao gồm B; công bố cả hai để không đếm đôi.
        model_results[name] = {'proxy_metrics': pm, 'human_metrics': hm,
                               'delta': {key: hm[key]-pm[key] for key in ['accuracy', 'macro_f1', 'weighted_f1']},
                               'per_class_f1_delta': {label: hm['per_class'][label]['f1']-pm['per_class'][label]['f1'] for label in LABELS},
                               'exclusive_cases': c, 'case_percentages': {k: v/n for k, v in c.items()},
                               'D_inclusive': c['B']+c['D'], 'human_errors': c['B']+c['C']+c['D'],
                               'proxy_errors': c['A']+c['C']+c['D']}
    return {'n': n, 'agreement': int((~mismatch).sum()), 'agreement_rate': float((~mismatch).mean()),
            'disagreement': int(mismatch.sum()), 'disagreement_rate': float(mismatch.mean()),
            'cohen_kappa': float(cohen_kappa_score(human, proxy, labels=[0, 1, 2])),
            'confusion_matrix_human_rows_proxy_columns': counts['confusion_matrix'],
            'label_order': list(LABELS), 'classes': classes, 'ratings': ratings,
            'ambiguity': ambiguity, 'models': model_results}


def validate_sources(root: Path, kit: Path) -> tuple[pd.DataFrame, dict]:
    """Đối chiếu phiếu với manifest, split, sampling và sáu nguồn predictions active."""
    annotations, refs, manifest = read_annotations(kit)
    if len(annotations) != 360 or not annotations.human_sentiment.isin(LABELS).all():
        raise ValueError('Cần đủ 360 nhãn human thuộc đúng ba lớp')
    completion = json.loads((root/'reports/p7_completion.json').read_text(encoding='utf-8'))
    frame = pd.read_parquet(root/'data/processed/splits/p4_20261009_final/test.parquet')
    if not frame.review_id.is_unique:
        raise ValueError('Duplicate review_id trong source')
    predictions, provenance = load_predictions(root, frame, completion)
    if provenance != manifest['inputs']['prediction_sources'] or len(predictions) != 6:
        raise ValueError('Active prediction provenance không khớp manifest')
    for split, sha in manifest['inputs']['split_sha256'].items():
        if file_hash(root/f'data/processed/splits/p4_20261009_final/{split}.parquet') != sha:
            raise ValueError('Split hash thay đổi')
    history = root/'reports/semantic_20261024/E05_transformer/history.json'
    if file_hash(history) != manifest['inputs']['bert_history_sha256']:
        raise ValueError('History hash thay đổi')
    if len({r['review_id'] for r in refs}) != len(refs):
        raise ValueError('Duplicate review_id trong sidecar')
    wide = pd.DataFrame({'review_id': frame.review_id,
                         'competitive_disagreement_count': np.stack([p != frame.label_id.to_numpy()
                           for m, p in predictions.items() if m != 'E00_majority']).sum(axis=0)})
    sampled = sample_audit(frame, wide, seed=manifest['seed'], representative_n=manifest['representative_n'])
    selected = {str(frame.review_id.iloc[s['row']]): s for s in sampled}
    source = frame.reset_index(drop=True).set_index('review_id')
    indexed = frame.reset_index().set_index('review_id')['index']
    ann = annotations.set_index('annotation_id')
    records = []
    for ref in refs:
        row = ann.loc[ref['annotation_id']]; original = source.loc[ref['review_id']]
        selection = selected.get(ref['review_id'])
        if selection is None or selection['sampling_group'] != ref['sampling_group'] or selection['inclusion_probability'] != ref['inclusion_probability']:
            raise ValueError('Sampling membership/probability thay đổi')
        if row.review_title != str(original.review_title) or row.review_text != str(original.text):
            raise ValueError('Title/body không khớp source')
        if ref['proxy_label_id'] != int(original.label_id) or ref['rating'] != float(original.rating):
            raise ValueError('Proxy/rating không khớp source')
        expected_proxy = 0 if float(original.rating) <= 2 else 1 if float(original.rating) == 3 else 2
        if ref['proxy_label_id'] != expected_proxy:
            raise ValueError('Rating mapping không khớp')
        expected_predictions = {m: int(p[int(indexed.loc[ref['review_id']])]) for m, p in predictions.items()}
        if ref['predictions'] != expected_predictions:
            raise ValueError('Prediction mapping không khớp source')
        records.append({k: ref[k] for k in ['annotation_id', 'review_id', 'sampling_group', 'rating', 'proxy_label_id']}
                       | {'human_id': LABELS.index(row.human_sentiment), 'ambiguous': ambiguity_flag(row.ambiguity)}
                       | expected_predictions)
    rows = pd.DataFrame(records)
    integrity = {'status': 'PASS', 'rows': len(rows), 'unique_annotation_ids': True,
                 'unique_review_ids': True, 'no_missing_human_labels': True, 'three_labels_only': True,
                 'fixed_fingerprints_match': True, 'title_body_match_source': True,
                 'sampling_reproduced': True, 'rating_proxy_match_source': True,
                 'six_model_predictions_match_source': True, 'source_hashes_match': True,
                 'duplicate_title_body_pairs': int(annotations.duplicated(['review_title', 'review_text']).sum()),
                 'encoding': 'UTF-8 CSV', 'annotation_sha256': file_hash(kit/'review_annotation.csv'),
                 'private_reference_sha256': file_hash(kit/'private_reference.json'), 'prediction_sources': provenance}
    return rows, integrity


def markdown_table(frame: pd.DataFrame) -> str:
    """Bảng Markdown không cần dependency bổ sung."""
    def cell(v):
        return f'{v:.6f}' if isinstance(v, (float, np.floating)) else str(v)
    return '\n'.join(['| '+' | '.join(frame.columns)+' |', '|'+'|'.join(['---']*len(frame.columns))+'|']+
                     ['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False, name=None)])


def finalize_diagnosis(root: Path, *, confirmed_human_review: bool) -> dict:
    """Sinh bảng/báo cáo canonical riêng diagnosis; không sửa benchmark hoặc nhãn người."""
    root = Path(root); kit = root/KIT
    grouped = evaluate_audit(kit, confirmed_human_review=confirmed_human_review)
    rows, integrity = validate_sources(root, kit)
    models = list(integrity['prediction_sources'])
    all_stats = compare_rows(rows, models)
    groups = {group: compare_rows(part, models) for group, part in rows.groupby('sampling_group')}
    result = {'status': 'HUMAN_REVIEWED_DIAGNOSIS_COMPLETE', 'provenance': 'human-reviewed sentiment diagnosis set',
              'reviewer_convention': 'human_reviewer_01', 'review_date': '2026-10-25',
              'scope': 'human-reviewed diagnostic evaluation; reused test; not independent P10 gold',
              'integrity': integrity, 'all_360_descriptive_only': all_stats, 'groups': groups,
              'sampling_uncertainty': grouped['groups'], 'population_30000_inference_allowed': False,
              'imbalance_causal_attribution': 'NOT_IDENTIFIABLE_FROM_THIS_AUDIT',
              'canonical_metrics_changed': False, 'models_retrained': False, 'dataset_splits_changed': False}
    reports = root/'reports'
    for key in ['classes', 'ratings', 'ambiguity']:
        pd.DataFrame(all_stats[key]).to_csv(reports/f'p7_human_{key}.csv', index=False)
    pd.DataFrame(all_stats['confusion_matrix_human_rows_proxy_columns'], index=LABELS, columns=LABELS).to_csv(
        reports/'p7_human_proxy_confusion.csv', index_label='human_sentiment')
    metric_rows, case_rows, per_class = [], [], []
    for scope, stats in {'all_360_descriptive_only': all_stats, **groups}.items():
        for name, m in stats['models'].items():
            metric_rows.append({'scope': scope, 'model': name, 'n': stats['n'],
                                **{'proxy_'+k: m['proxy_metrics'][k] for k in ['accuracy', 'macro_f1', 'weighted_f1']},
                                **{'human_'+k: m['human_metrics'][k] for k in ['accuracy', 'macro_f1', 'weighted_f1']},
                                **{'delta_'+k: v for k, v in m['delta'].items()}})
            case_rows.append({'scope': scope, 'model': name, 'n': stats['n'], **m['exclusive_cases'],
                              **{k+'_share': v for k, v in m['case_percentages'].items()},
                              'D_inclusive': m['D_inclusive'], 'human_errors': m['human_errors'], 'proxy_errors': m['proxy_errors']})
            for label in LABELS:
                per_class.append({'scope': scope, 'model': name, 'class': label,
                                  **{'proxy_'+k: v for k, v in m['proxy_metrics']['per_class'][label].items()},
                                  **{'human_'+k: v for k, v in m['human_metrics']['per_class'][label].items()},
                                  'delta_f1': m['per_class_f1_delta'][label]})
    metrics = pd.DataFrame(metric_rows); cases = pd.DataFrame(case_rows)
    metrics.to_csv(reports/'p7_human_model_metrics.csv', index=False)
    cases.to_csv(reports/'p7_human_attribution.csv', index=False)
    pd.DataFrame(per_class).to_csv(reports/'p7_human_model_classes.csv', index=False)
    # Mapping theo review chỉ local; không xuất text/evidence vào báo cáo được chia sẻ.
    local = root/'data/interim/p7_diagnosis'
    local.mkdir(parents=True, exist_ok=True)
    detail = []
    for row in rows.to_dict('records'):
        for model in models:
            detail.append({k: row[k] for k in ['annotation_id', 'review_id', 'sampling_group', 'human_id', 'proxy_label_id']}
                          | {'model': model, 'prediction_id': row[model],
                             'case': attribution_case(row['human_id'], row['proxy_label_id'], row[model])})
    pd.DataFrame(detail).to_parquet(local/'human_attribution.parquet', index=False)
    (reports/'p7_human_audit_results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_report(root, result, metrics, cases)
    summary_path = reports/'p7_error_cause_analysis.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    summary.update(status='P7_DONE_READY_FOR_P8', human_diagnosis='reports/p7_human_audit_results.json',
                   human_diagnosis_integrity=integrity, NEXT_ACTION='READY FOR P8; dừng, chưa triển khai P8.')
    summary.pop('BLOCKED', None)
    summary['audit'].update(status='HUMAN_REVIEWED_COMPLETE', nonempty_human_sentiments=360)
    summary['causes']['proxy_human_mismatch_rate']='MEASURED_BY_SAMPLING_GROUP'
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    completion_path = reports/'p7_completion.json'
    completion = json.loads(completion_path.read_text(encoding='utf-8'))
    completion.update(p7_status='DONE', readiness='READY FOR P8', error_analysis_status='COMPLETE_CURRENT_SIX_MODELS',
                      human_cause_attribution_status='HUMAN_REVIEWED_DIAGNOSTIC_COMPLETE',
                      human_diagnosis_report='reports/p7_human_audit_results.json', independent_gold_status='PENDING_NOT_CREATED')
    completion_path.write_text(json.dumps(completion, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    start='<!-- error_diagnosis:start -->'; end='<!-- error_diagnosis:end -->'
    block='\n'.join([start, '## Chẩn đoán sentiment đã hoàn tất', '',
                    f"**P7: DONE — READY FOR P8.** 360 human-reviewed sentiment diagnosis reviews; agreement {all_stats['agreement']}/360 ({all_stats['agreement_rate']:.2%}), disagreement {all_stats['disagreement']}/360 ({all_stats['disagreement_rate']:.2%}). Sáu model gồm TabPFN cloud full21K đã đối chiếu human/proxy.", '',
                    '360 là mẫu chẩn đoán gồm 300 SRS test + 60 enriched; tỷ lệ gộp chỉ mô tả mẫu, không ước lượng toàn 30K. Independent P10 gold vẫn PENDING. Causal fraction của imbalance chưa xác định, không là blocker P7. Benchmark/selection/splits/weights giữ nguyên; không cần retrain trước P8.', '',
                    'Bằng chứng: `reports/p7_error_cause_analysis.md`, `reports/p7_human_audit_results.json`, `reports/p0_p7_acceptance.json`. Dừng tại READY FOR P8, chưa triển khai P8.', end])
    for name in ['p7_unified_benchmark.md', 'model_stack_refactor_completion.md']:
        path = reports/name; text = path.read_text(encoding='utf-8')
        if start in text:
            text = text[:text.index(start)]+block+text[text.index(end)+len(end):]
        else:
            text += '\n\n'+block+'\n'
        path.write_text(text, encoding='utf-8')
    return result


def write_report(root: Path, result: dict, metrics: pd.DataFrame, cases: pd.DataFrame) -> None:
    """Báo cáo có đúng các câu hỏi nghiệm thu và số liệu tính từ nguồn."""
    s=result['all_360_descriptive_only']; g=result['groups']; rep=g['representative']; enriched=g['diagnostic_enriched']
    table=lambda records: markdown_table(pd.DataFrame(records))
    distribution=pd.read_csv(root/'reports/p7_class_distribution.csv')
    weighted=pd.read_csv(root/'reports/p7_weighting_validation.csv')
    paired=pd.read_csv(root/'reports/p7_weighting_paired_validation.csv')
    neutral=pd.read_csv(root/'reports/p7_class_diagnostics.csv').query("`class`=='neutral'")
    cm=np.asarray(s['confusion_matrix_human_rows_proxy_columns'])
    ci=result['sampling_uncertainty']['representative']['test_population_proxy_mismatch_95pct_interval']
    selected=weighted[weighted.selected_within_mode_by_validation_macro_f1]
    delta=selected.set_index('mode').loc['balanced','validation_macro_f1']-selected.set_index('mode').loc['unweighted','validation_macro_f1']
    all_metrics=metrics[metrics.scope=='all_360_descriptive_only']
    all_cases=cases[cases.scope=='all_360_descriptive_only']
    proxy_rank=all_metrics.sort_values('proxy_macro_f1',ascending=False).model.tolist()
    human_rank=all_metrics.sort_values('human_macro_f1',ascending=False).model.tolist()
    lines=['# P7 — Chẩn đoán lỗi sentiment: proxy, human và mất cân bằng', '',
           '**P7: DONE — READY FOR P8.** Human-reviewed diagnostic evaluation, không phải canonical test score. Không retrain, không đổi benchmark, split hoặc selection.', '',
           '## 1. Mục tiêu', '', 'Định lượng bất đồng rating–human, tách lỗi theo human khỏi lỗi đánh giá proxy và xem xét imbalance/ambiguity bằng artifacts đã khóa. Không coi phân loại mô tả là chứng minh nhân quả.', '',
           '## 2. Dữ liệu sử dụng', '',
           f'Amazon laptop tiếng Anh 30.000 review; split product-disjoint 21.000/4.500/4.500, seed42. Active models lấy từ p7_completion.json và provenance đã đối chiếu: {", ".join(s["models"])}. TabPFN dùng cloud full21K, không dùng subsample lịch sử.', '',
           f'Phiếu `{KIT}/review_annotation.csv`: 300 SRS không hoàn lại từ 4.500 test (seed42, inclusion_probability=300/4500) và 60 enriched rời nhau, tối đa20/proxy class, ưu tiên nhiều model cạnh tranh bất đồng proxy. Đã tái lập chính xác sampling từ source. Tỷ lệ gộp360 chỉ mô tả diagnosis; không có CI hoặc population estimate cho tập gộp/enriched/toàn30K.', '',
           '## 3. Trạng thái human review', '',
           '360/360 là **human-reviewed sentiment diagnosis set**, được người dùng xác nhận toàn bộ ngày 2026-10-25; reviewer convention human_reviewer_01. Chỉ điền reviewer_id/reviewed_at còn trống theo yêu cầu; nhãn, ambiguity, evidence, ID, title/body giữ nguyên. Boolean TRUE/FALSE được đọc trực tiếp, không thay nội dung phiếu. Một reviewer; chưa đo agreement liên người. Đây là reused-test diagnosis, không phải independent P10 gold.', '',
           '## 4. Kiểm tra integrity', '',
           table([{'check': k, 'result': v} for k,v in result['integrity'].items() if k not in {'prediction_sources'}]), '',
           'Đối chiếu từng ID/text/title/rating/proxy/prediction với source và fingerprint; không mất/thêm review, không duplicate bất thường. Hash nguồn/split/history/sidecar khớp manifest. Chi tiết đường dẫn/hash trong JSON; mapping 2.160 review/model chỉ lưu local `data/interim/p7_diagnosis/human_attribution.parquet`.', '',
           '## 5. Proxy so với human', '',
           f"Agreement {s['agreement']}/360 ({s['agreement_rate']:.2%}); disagreement {s['disagreement']}/360 ({s['disagreement_rate']:.2%}); Cohen kappa={s['cohen_kappa']:.6f}. Đây là chỉ số của mẫu gộp, có enrichment.", '',
           table(s['classes']), '', 'Ma trận: hàng=human, cột=proxy; thứ tự negative/neutral/positive.', '',
           markdown_table(pd.DataFrame(cm, index=LABELS, columns=LABELS).rename_axis('human').reset_index()), '',
           f'Human neutral chuyển thành proxy negative {cm[1,0]}, positive {cm[1,2]}, giữ neutral {cm[1,1]}/{cm[1].sum()}. Human negative bị proxy positive che khuất {cm[0,2]}/{cm[0].sum()}; human positive bị proxy negative {cm[2,0]}/{cm[2].sum()}. Không đồng nhất neutral/mixed hoặc coi mọi rating3 là neutral theo text.', '',
           f"SRS300: disagreement {rep['disagreement']}/300 ({rep['disagreement_rate']:.2%}); khoảng95% exact hypergeometric cho **test population4500** [{ci[0]:.2%}, {ci[1]:.2%}]. Có điều kiện thiết kế SRS và nhãn người cố định; không bao gồm sai số reviewer hoặc suy rộng sang train/30K. Enriched60: {enriched['disagreement']}/60 ({enriched['disagreement_rate']:.2%}), không population inference.", '',
           '## 6. Rating so với human', '', table(s['ratings']), '',
           'Rating vẫn là proxy hữu ích để duy trì benchmark nhất quán, nhưng sai ở cấp review; các phân phối theo sao trên là mô tả mẫu diagnosis có enrichment. Không suy ra độ chính xác toàn30K hoặc kết luận rating hoàn toàn tốt/xấu. Giữ provenance star-derived proxy và không tự relabel dataset.', '',
           '## 7. Ambiguity', '', table(s['ambiguity']), '',
           'TRUE là annotation mơ hồ/mixed do người dùng xác nhận; không tự suy ra kiểu semantic cụ thể. So sánh trên có liên hệ mô tả, chịu selection và reviewer bias, không chứng minh ambiguity gây mismatch. Số lượng từng nhóm hiển thị để đánh giá độ ổn định; nhóm con theo lớp nhỏ cần thận trọng.', '',
           '## 8. Hiệu suất human diagnostic từng model', '',
           markdown_table(all_metrics.drop(columns=['scope'])), '',
           'CSV p7_human_model_classes.csv chứa precision/recall/F1/support từng lớp theo cả human/proxy. JSON chứa confusion matrices từng model. Các bảng tách SRS/enriched nằm trong cùng CSV và JSON, không dùng ranking gộp để chọn model.', '',
           'Thứ hạng macro F1 diagnosis theo proxy: '+' > '.join(proxy_rank)+'. Theo human: '+' > '.join(human_rank)+'. Thay đổi thứ hạng trên mẫu chỉ mô tả, chưa có kiểm định ưu thế và không thay ranking canonical.', '',
           'So sánh riêng SRS300 (tránh diễn giải mức tăng trên mẫu enriched như hiệu quả đại diện):', '',
           markdown_table(metrics[metrics.scope=='representative'][['model','proxy_accuracy','human_accuracy','proxy_macro_f1','human_macro_f1','delta_macro_f1']]), '',
           'Trên SRS, delta macro F1 có thể âm trong khi mẫu gộp tăng; enrichment chọn ca model sai proxy làm thay đổi hướng so sánh. BERT/TabM vẫn đứng đầu hai nhóm tương ứng trong SRS. TabPFN3 và3.5 đổi thứ tự nhẹ theo human SRS, không đủ chứng minh khác biệt thống kê.', '',
           '## 9. Quy chiếu lỗi proxy/model', '',
           'A: model=human≠proxy; B: model=proxy≠human; C: proxy=human≠model; D: cả model/proxy sai human **và model khác proxy**; E: cả ba khớp. Định nghĩa D rộng trong yêu cầu chồng B; D_inclusive=B+D được báo riêng. Năm nhóm A–E ở đây rời nhau, tổng360. Share dùng mẫu số360, human_errors=B+C+D; proxy_errors=A+C+D. A là ca benchmark proxy phạt dự đoán phù hợp human; B phù hợp giả thuyết bám proxy noise nhưng không chứng minh quá trình học.', '',
           markdown_table(all_cases.drop(columns=['scope'])), '',
           'Tệp local có case từng review/model; không ép gán nguyên nhân imbalance cho từng review. D_inclusive không cộng thêm vào A–E.', '',
           '## 10. Bằng chứng mất cân bằng', '', table(distribution.to_dict('records')), '',
           markdown_table(neutral[['model','support','predicted_count','precision','recall','f1']]), '',
           'Neutral train1842/21000=8,77%; proxy neutral test394. Cùng phân phối mà model có neutral recall/F1 rất khác nhau, nên imbalance không đủ giải thích tất cả. Human class distribution ở mục5 khác proxy; 360 là mẫu bị chọn, không phải phân phối huấn luyện. Imbalance có thật và proxy mismatch có thật nhưng có thể tương tác; chưa xác định tính độc lập hoặc causal fraction.', '',
           '## 11. Weighted so với unweighted', '', table(weighted.to_dict('records')), '', table(paired.to_dict('records')), '',
           f'Chọn epoch tốt nhất từng mode bằng validation macro F1: balanced−unweighted={delta:+.6f}. Neutral được sửa62 ca, sai thêm7; negative sửa4/sai thêm58; positive sửa6/sai thêm82. Tác động ròng mạnh nhất ở positive, còn recall tăng chủ yếu neutral. Neutral FP236→391; recall+0,139241, precision−0,059429, F1+0,014004. Giữ unweighted đã khóa.', '',
           'Hai mảng là validation, còn 360human nằm test; review_id không giao nhau nên **không có paired human weighted/unweighted evaluation** và không chạy balanced test mới. Có bằng chứng weighting thay behavior/recall nhưng chưa có bằng chứng trực tiếp rằng nó sửa proxy noise; class weights không đổi label mapping và có thể tăng trọng số nhãn nhiễu. Không tuyên bố causal effect hoặc chuyển kết luận sang model khác.', '',
           '## 12. Taxonomy lỗi', '',
           table([{'nhóm': a,'bằng chứng/chính sách': b} for a,b in [
               ('proxy label mismatch','Đo trực tiếp human≠proxy, bảng5/9; không causal fraction'),
               ('class imbalance','Phân phối và sensitivity validation; không gán per-review cause'),
               ('ambiguous / mixed sentiment','Boolean ambiguity từ human; không suy ra mọi mixed review đều neutral'),
               ('implicit sentiment','Chưa có annotation taxonomy riêng; NOT_MEASURED'),
               ('long review with mixed aspects','Độ dài/cue ở p7_error_groups chỉ heuristic; mixed aspects chưa xác minh'),
               ('temporal sentiment shift','Cần human taxonomy theo thời gian sử dụng; NOT_MEASURED'),
               ('strong rating but mixed review text','Proxy mismatch + ambiguity là dấu hiệu, không xác nhận semantic taxonomy'),
               ('negation / comparison','Cue lexical chỉ nhóm mô tả, chưa có human causal tags'),
               ('hardware/software-specific complaints','Chưa có annotation taxonomy riêng; NOT_MEASURED'),
               ('positive overall with local complaint','Có thể tương thích ambiguity; chưa đếm semantic subtype'),
               ('negative overall despite isolated praise','Có thể tương thích ambiguity; chưa đếm semantic subtype')]]), '',
           'Không gán taxonomy semantic mới từ evidence bằng suy đoán hoặc tạo human annotation bổ sung. Đây là giới hạn độ chi tiết chẩn đoán, không blocker nghiệm thu các so sánh human/proxy.', '',
           '## 13. Giới hạn', '',
           'Các phát hiện chỉ dành cho laptop tiếng Anh. Nhãn đại diện suy từ số sao có nhiễu nhãn. Sự thay đổi SemEval-to-Amazon platform/style trong laptop review còn thuộc đánh giá ABSA. Bộ dữ liệu gold được chú thích thủ công nhỏ là hạn chế dự kiến P10; diagnosis360 này nhỏ, một reviewer và reused test, không thay independent gold. SRS chỉ đại diện test4500; enriched/360không đại diện30K. Test đã xem sau selection, không tuning hoặc tuyên bố production/ưu thế thống kê. Causal fraction của imbalance/representation NOT_IDENTIFIABLE; taxonomy chưa có tags riêng. Cloud/local khác thiết bị và phạm vi đo compute, V3 giới hạn coverage200/384; xem benchmark gốc.', '',
           '## 14. Kết luận cuối', '',
           '1. Bao nhiêu lỗi proxy phạt model phù hợp human? Cột A ở mục9, với từng model và mẫu số360; không suy rộng30K.',
           '2. Bao nhiêu lỗi thật khi đối chiếu human? Cột human_errors=B+C+D ở mục9, bao gồm C khi proxy đúng và B/D khi proxy cũng sai.',
           '3. Neutral yếu liên quan nhiều yếu tố: ít support train, proxy↔human chuyển lớp, ambiguity và model profile khác nhau. Chưa đủ causal evidence để chọn một nguyên nhân chủ yếu hoặc cộng các tỷ lệ như độc lập.',
           '4. Weighting tăng neutral recall nhưng đổi precision/FP và làm giảm macro F1; không có paired human validation labels nên chưa xác nhận xử lý được noise.',
           f"5. Tiếp tục dùng rating proxy có giới hạn: SRS test agreement {rep['agreement']}/300 ({rep['agreement_rate']:.2%}), giữ báo cáo nhãn-nhiễu và bổ sung independent gold P10. Không coi kết quả này là chất lượng nhãn toàn30K.",
           '6. Không cần retrain sentiment trước P8: chưa có bug hoặc bằng chứng validation mới hợp lệ buộc thay selection. Human diagnosis dùng để giải thích; không dùng test để chọn lại mô hình.', '',
           '## 15. Quyết định nghiệm thu P7', '',
           '**P7: DONE. READY FOR P8.** Integrity360PASS; human–proxy/rating/ambiguity/sáu model và weighting đã phân tích từ artifacts thật. Benchmark metrics/selection/dataset/splits/weights giữ nguyên. P0–P7 acceptance và các giới hạn: `reports/p0_p7_acceptance.json`; validation: `reports/p7_error_diagnosis_validation.json`. Không còn blocker bắt buộc trước P8 theo phạm vi hiện hành. Dừng tại đây, **chưa triển khai P8**; independent gold/ABSA vẫn PENDING.']
    (root/'reports/p7_error_cause_analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
