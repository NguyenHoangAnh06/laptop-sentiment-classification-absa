"""Kiểm nghiệm thu P0–P7 từ bằng chứng đã có và hashes, không chạy model."""
import json

from src.config import PROJECT_ROOT
from src.evaluation.error_diagnosis import file_hash
from src.evaluation.human_diagnosis import KIT, validate_sources


def acceptance(root=PROJECT_ROOT) -> dict:
    """Phân biệt bằng chứng cũ REPORTED và kiểm tra hiện tại VERIFIED."""
    rows, integrity=validate_sources(root,root/KIT)
    historical=json.loads((root/'reports/kaggle_tabpfn_preservation.json').read_text(encoding='utf-8'))
    # Hai báo cáo P7 đã được cập nhật khi import; chỉ 153 scientific files bất biến.
    scientific={p:h for p,h in historical['files'].items()
                if p not in {'reports/p7_unified_results.csv','reports/p7_unified_benchmark.md'}}
    before=json.loads((root/'data/interim/p7_diagnosis/before_human_finalization.json').read_text(encoding='utf-8'))
    def differences(mapping):
        return [p for p,h in mapping.items() if not (root/p).is_file() or file_hash(root/p)!=h]
    mismatches=differences(scientific)
    task_mismatches=differences(before)
    legacy={}
    for phase in ['p5','p6']:
        manifest=json.loads((root/f'reports/{phase}/{phase}_20261015/manifest.json').read_text(encoding='utf-8'))
        mapping=manifest['output_sha256']
        legacy[phase]={'files':len(mapping),'mismatches':differences(mapping)}
    if mismatches or task_mismatches or any(v['mismatches'] for v in legacy.values()):
        raise ValueError('Scientific/model/legacy artifacts thay đổi; không nghiệm thu')
    metric_sha=file_hash(root/'reports/p7_unified_results.csv')
    if metric_sha!='260068014d210a8549d09156e79eadd4ae0b8546f0dda64b51e361b664753f54':
        raise ValueError('Canonical metric CSV thay đổi; dừng, không sửa benchmark')
    paths={
        'P0':['reports/p0_model_stack_refactor.md','reports/p0_model_stack_environment.json','requirements.txt'],
        'P1':['reports/p1_revalidation_for_new_models.json','reports/p1_acceptance_decision_20261009.md',
              'reports/tables/p1_semeval_owner_exception_20261009.json','data/raw/amazon/Electronics.jsonl.gz'],
        'P2':['reports/p2_revalidation_for_new_models.json','reports/p2_amazon_completion_20261009.md','data/processed/laptop_reviews.parquet'],
        'P3':['reports/p3_model_readiness.json','reports/p3_data_analysis_20261009.md','reports/p3/20261009_verified/task_validation.json'],
        'P4':['reports/p4_semantic_representation.md','reports/p4_semantic_independent_validation.json',
              'reports/p4_semantic_split_validation.json','configs/semantic_benchmark.yaml'],
        'P5':['reports/p5_modern_tabular_models.md','reports/tabpfn_kaggle_full21k_verification.json','configs/modern_tabular.yaml'],
        'P6':['reports/p6_transformer_benchmark.md','reports/semantic_20261024/E05_transformer/history.json','configs/transformer_benchmark.yaml'],
        'P7':['reports/p7_completion.json','reports/p7_unified_results.csv','reports/p7_human_audit_results.json',
              'reports/p7_error_cause_analysis.md','reports/p7_human_model_metrics.csv','reports/p7_human_attribution.csv']}
    # Đường dẫn raw lấy từ repository hiện có, không dựa trên tên dự kiến nếu layout khác.
    raw=list((root/'data/raw').rglob('Electronics.jsonl.gz'))
    if len(raw)!=1:
        raise ValueError('Không xác định duy nhất raw source Amazon')
    paths['P1'][-1]=raw[0].relative_to(root).as_posix()
    limits={
        'P0':'Môi trường đã xác minh trước; không cài lại hoặc nâng dependency.',
        'P1':'DONE WITH LIMITATION: ngoại lệ giáo dục của chủ sở hữu; SemEval source/license NOT_VERIFIED, không gọi quyền truy cập đã xác minh.',
        'P2':'Nhãn suy từ sao; audit360 chỉ diagnosis, không xác nhận độ sạch ngôn ngữ/spam toàn30K.',
        'P3':'EDA mô tả trên laptop; cue/keyword không phải gold ABSA.',
        'P4':'MiniLM256/BERT512, giữ split/product leakage audit đã khóa; không re-encode.',
        'P5':'DONE WITH LIMITATION: cloud full21K SUCCESS; V3 coverage nội bộ200/384, khác hardware/runtime, cloud không xuất weights. Local subsample giữ LIMITED lịch sử.',
        'P6':'DONE WITH LIMITATION: một seed/search nhỏ và test reuse; không thống kê ưu thế.',
        'P7':'360 human-reviewed,300SRS+60enriched; causal fraction imbalance không xác định, independent P10 gold vẫn PENDING.'}
    phases={}
    for phase,names in paths.items():
        missing=[p for p in names if not (root/p).is_file()]
        if missing:
            raise ValueError(f'{phase} thiếu artifacts: {missing}')
        phases[phase]={'status':'DONE WITH LIMITATION' if phase in {'P1','P5','P6'} else 'DONE',
                       'artifact_existence':'VERIFIED', 'previous_phase_execution':'REPORTED_NOT_RERUN',
                       'evidence':names, 'limitations':limits[phase]}
    # Các báo cáo máy đọc được phải giữ PASS từ lần thực thi đã chấp nhận.
    for p in ['reports/p1_revalidation_for_new_models.json','reports/p2_revalidation_for_new_models.json',
              'reports/p3_model_readiness.json','reports/p4_semantic_independent_validation.json']:
        if json.loads((root/p).read_text(encoding='utf-8'))['status']!='PASS':
            raise ValueError('Evidence pha không PASS: '+p)
    completion=json.loads((root/'reports/p7_completion.json').read_text(encoding='utf-8'))
    if completion['p7_status']!='DONE' or completion['cloud_full_train_status']!='PASS':
        raise ValueError('Chưa hoàn tất P7/cloud')
    preservation={'status':'PASS','scientific_files_unchanged':len(scientific),'mismatches':mismatches,
                  'task_snapshot_files_unchanged':len(before),'task_snapshot_mismatches':task_mismatches,
                  'legacy':legacy,'benchmark_csv_sha256':metric_sha,'manual_rows':len(rows),
                  'human_fields_nonempty':360,'annotation_file_sha256':integrity['annotation_sha256'],
                  'private_sidecar_sha256':integrity['private_reference_sha256']}
    result={'status':'PASS','date':'2026-10-25','phases':phases,'p7_status':'DONE','readiness':'READY FOR P8',
            'mandatory_blockers_before_p8':[],'no_p8_implementation':True,'canonical_metrics_changed':False,
            'models_retrained':False,'dataset_splits_changed':False,'preservation':preservation,
            'tests_evidence':'reports/p7_error_diagnosis_validation.json',
            'NEXT_ACTION':'Dừng tại READY FOR P8; P8 chỉ thực hiện trong tác vụ tiếp theo.'}
    (root/'reports/p7_error_diagnosis_preservation.json').write_text(json.dumps(preservation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'reports/p0_p7_acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    result=acceptance()
    print(result['readiness'])
