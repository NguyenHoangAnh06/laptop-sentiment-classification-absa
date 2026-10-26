"""Cập nhật bảng/báo cáo từ cloud đã verified; không huấn luyện hoặc dự đoán."""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
from src.config import PROJECT_ROOT
from scripts.verify_kaggle_results import read,write,sha,verify_package,require,VERSIONS

HISTORY='reports/history/tabpfn_before_kaggle_20261024'
SNAPSHOTS=['p7_unified_results.csv','p7_unified_benchmark.md','p7_completion.json','model_stack_refactor_completion.md',
           'p7_error_groups.csv','p7_error_transitions.csv','p7_error_examples.csv']


def table_md(frame):
    columns=['model','train_samples','data_regime','validation_macro_f1','macro_f1','accuracy','weighted_f1','balanced_accuracy','negative_f1','neutral_f1','positive_f1']
    lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
    for _,row in frame.iterrows():lines.append('| '+' | '.join(f'{row[c]:.6f}' if isinstance(row[c],float) else str(row[c]) for c in columns)+' |')
    return '\n'.join(lines)


def publish(root=PROJECT_ROOT):
    root=Path(root)
    receipt=read(root/'reports/tabpfn_kaggle_full21k_verification.json')
    verified=verify_package(root/receipt['artifact_directory'],root)
    require(verified['integrity_status']=='PASS','Không publish package integrity FAIL')
    passed={k:v for k,v in verified['models'].items() if v['status']=='SUCCESS'}
    require(bool(passed),'Không có model SUCCESS để cập nhật')
    history=root/HISTORY
    if not history.exists():
        history.mkdir(parents=True)
        for name in SNAPSHOTS:shutil.copyfile(root/'reports'/name,history/name)
        write(history/'hashes.json',{n:sha(history/n) for n in SNAPSHOTS})
    for name,digest in read(history/'hashes.json').items():require(sha(history/name)==digest,'Historical snapshot hash FAIL')
    frame=pd.read_csv(history/'p7_unified_results.csv')
    frame['execution_environment']='local Windows RTX4050Laptop/CPU'
    frame['artifact_kind']='fitted_model'
    sources={}
    resources=[]
    for slug,v in passed.items():
        name=VERSIONS[slug][1];i=frame.index[frame.model.eq(name)][0]
        m=v['metrics']['test'];resource=v['resource'];folder=root/v['artifact_directory']
        count=sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
        updates={'train_samples':21000,'data_regime':'FULL','validation_macro_f1':v['metrics']['validation']['macro_f1'],
                 **{k:m[k] for k in ['macro_f1','accuracy','weighted_f1','balanced_accuracy']},
                 **{f'{label}_f1':m['per_class'][label]['f1'] for label in ['negative','neutral','positive']},
                 'runtime_seconds':resource['wall_seconds'],'peak_gpu_allocated_bytes':resource['peak_gpu_allocated_bytes'],
                 'peak_process_rss_bytes':resource['peak_process_rss_bytes'],'artifact_bytes':np.nan,
                 'artifact_file_bytes_actual':count,'inference_ms_per_review':resource['test_inference_seconds']/4500*1000,
                 'execution_environment':'Kaggle Linux Tesla T4','artifact_kind':'results_only_no_weights'}
        for key,value in updates.items():frame.at[i,key]=value
        sources[name]={'kind':'kaggle_csv','directory':v['artifact_directory'],'verification':'reports/tabpfn_kaggle_full21k_verification.json','status':'SUCCESS'}
        resources.append(f"| {name} | {resource['fit_seconds']:.3f} | {resource['validation_inference_seconds']:.3f} | {resource['test_inference_seconds']:.3f} | {resource['wall_seconds']:.3f} | {resource['peak_process_rss_bytes']/1e9:.3f} | {resource['peak_gpu_allocated_bytes']/1e9:.3f} | {resource['peak_gpu_reserved_bytes']/1e9:.3f} | Tesla T4 |")
    output = frame.astype(object)
    original = pd.read_csv(history/'p7_unified_results.csv', dtype=str, keep_default_na=False)
    for i,row in original.iterrows():
        if row['model'] not in sources:
            for key,value in row.items():output.at[i,key]=value
    output.to_csv(root/'reports/p7_unified_results.csv',index=False)
    best=frame.loc[frame.validation_macro_f1.idxmax(),'model']
    frozen=frame[frame.model.str.contains('embedding')]
    best_frozen=frozen.loc[frozen.validation_macro_f1.idxmax(),'model']
    test_rank=frame.sort_values('macro_f1',ascending=False).model.tolist()
    completion=read(history/'p7_completion.json')
    completion.update(scope='verified_local_and_kaggle_proxy_benchmark',cloud_full_train_status='PASS' if len(passed)==2 else 'PARTIAL',
                      selected_by_validation=best,best_frozen_by_validation=best_frozen,model_sources=sources,
                      test_macro_f1_ranking_descriptive=test_rank,historical_local_directory=HISTORY,
                      verification_report='reports/tabpfn_kaggle_full21k_verification.json',
                      limitations=['reused test','V3 internal feature coverage','proxy labels','different hardware/runtime scopes','human gold future work'])
    write(root/'reports/p7_completion.json',completion)
    notes=('Chọn theo validation macro F1: **'+best+'**; best frozen: **'+best_frozen+'**. '
           'Thứ hạng test Macro F1 chỉ mô tả kết quả đã khóa: '+ ' > '.join(test_rank)+'. '
           'Neutral F1 cao nhất vẫn BERT; TabM đứng sau. Cả hai TabPFN full21K cải thiện so với subsample nhưng vẫn thấp hơn BERT/TabM về Macro F1 và Neutral F1; không điều chỉnh sau test.')
    resource_text='\n'.join(['| Model | Fit s | Val s | Test s | Wall s | RSS GB | GPU allocated GB | GPU reserved GB | GPU |',
                             '|---|---:|---:|---:|---:|---:|---:|---:|---|',*resources])
    limitations=('Chỉ review laptop tiếng Anh; nhãn đại diện suy từ sao có nhiễu, không phải human sentiment gold. '
                 'Test đã xem ở LEGACY/local/cloud, không gọi unseen mới. Một seed42, không kết luận ưu thế thống kê. '
                 'SemEval-to-Amazon platform/style shift trong laptop còn thuộc ABSA; bộ gold thủ công dự kiến nhỏ, chưa có. '
                 'V3 n_estimators1 vẫn giới hạn coverage nội bộ tối đa200/384chiều; không thay embeddings384. '
                 'Context MiniLM256/BERT512 và paradigm frozen/end-to-end khác nhau; không khẳng định production hoặc hỗ trợ tiếng Việt.')
    history_text=(f'Bảng local trước cloud: `{HISTORY}/p7_unified_results.csv`; báo cáo/metrics/artifacts subsample10000/1500 không bị xóa. '
                  'Resource local V3 RSS6,48GB vượt trần6GB và V3.5 dùng1500 vẫn là bằng chứng lịch sử. '
                  f'Các CSV lỗi local trước cloud được bảo toàn trong `{HISTORY}`. '
                  'CSV p7_error_* hiện hành được sinh lại từ6model active, gồm TabPFN cloud; không dùng subsample để diễn giải cloud.')
    text=['# P7 — Đánh giá thống nhất sau xác minh Kaggle','',
          'PASS: hai TabPFN full21000 đã verified; bảng chính dùng cloud thay subsample, giữ local lịch sử. Không rerun P0–P7/model; chỉ tính lại saved predictions và cập nhật báo cáo.',
          '',table_md(frame),'',notes,'','## Tài nguyên và khả năng so sánh','',resource_text,'',
          'Đơn vị GB=10^9bytes. RSS sampled20ms; allocated/reserved theo PyTorch, không phải toàn VRAM vật lý. Wall cloud gồm setup model/fit/validation/test trong monitor, không gồm probe; local runtime có search/reload. Không so runtime như cùng điều kiện. Latency từ embedding/token có sẵn, không phải raw-text end-to-end. Tiền compute NOT_MEASURED. Cloud không trả model weights: artifact_bytes để trống; artifact_file_bytes_actual chỉ là gói kết quả, không so với kích thước fitted model local.',
          '','## Protocol và provenance','',
          'Dataset/split/hash/ID/labels/embeddings giữ nguyên. Candidate seed42/n_estimators1/fit_with_cache/cacheCPU/autocast/batch16 cố định trước cloud; probe chỉ train. Fit train21000 → validation4500 → selection lock → test4500. Hash manifest cloud khớp local; predictions align toàn4500ID và nhãn, mọi metric/ma trận tính lại khớp abs tolerance1e-12, max delta0. Evidence là code bundle được hash/config/lock/metadata, không có attestation độc lập hoặc timestamp log để chứng minh tuyệt đối lịch sử thực thi. Test reuse được công bố.',
          '','## Lịch sử và phân tích lỗi','',history_text,'',table_md(pd.read_csv(history/'p7_unified_results.csv').query("model.str.contains('tabpfn')",engine='python')),
          '','## Giới hạn','',limitations,'',
          'Bằng chứng: `reports/tabpfn_kaggle_full21k_verification.md`/`.json`; provenance map trong `reports/p7_completion.json`. Toàn dự án ABSA/gold/app vẫn PENDING.']
    (root/'reports/p7_unified_benchmark.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    summary=['# Báo cáo hoàn tất benchmark bộ mô hình — cập nhật Kaggle 2026-10-24','',
             'Benchmark chính đủ6model full21000; hai TabPFN cloud SUCCESS. Đây không phải toàn dự án DONE. Báo cáo local A–M nguyên bản được giữ trong thư mục lịch sử để bảo toàn provenance.',
             '','## A. Status','', 'P0–P4/P6 và majority/XGBoost/TabM/BERT: REUSED, không retrain. C-E03/C-E04: SUCCESS/FULL21000, Kaggle Tesla T4. P7 cập nhật chỉ sau verify saved predictions. ABSA/gold/app còn PENDING.',
             '','## B. Dataset và split','', 'Giữ dataset30000 và split21000/4500/4500/seed42. Hash/row order/label mapping đã đối chiếu nguồn thật; không resplit/relabel/regenerate embeddings.',
             '','## C. Representation','', 'Frozen MiniLM384FP32/L2 cho classifier; BERT canonical title+body end-to-end. Không dùng thêm biểu diễn giảm chiều hoặc features metadata.',
             '','## D. Models','', 'TabPFN9.2.0 explicit V3/V3_5 với checkpoint khác nhau và train_count21000 được đối chiếu metadata/lock/probe. Model artifacts local giữ nguyên.',
             '','## E. Protocol','', 'Validation macro F1 lựa chọn chính; cấu hình cloud đơn định trước, train-only probe, lock trước reused test theo code bundle và metadata; không test tuning.',
             '','## F. Final table','',table_md(frame),'','## G. Best model','',notes,
             '','## H. Resource findings','',resource_text,'','Local/cloud khác hardware và runtime scope; không suy diễn tốc độ thuần model. Weights cloud không được xuất, artifact results không đại diện model size.',
             '','## I. Error analysis','',history_text,'','## J. Limitations','',limitations,
             '','## K. Reproducibility','', 'Source ZIP, SHA256, môi trường Linux/Python3.13.15/torch2.11.0+cu128/sklearn1.7.2, local recomputed metrics đầy đủ và protocol evidence nằm ở verification report. Manifest/prediction/selection_lock hashes được lưu nguyên.',
             '','## L. Tests','', 'Bằng chứng lúc import cloud ở `reports/tabpfn_kaggle_full21k_verification.json`; kiểm thử tác vụ chẩn đoán mới ở `reports/p7_error_diagnosis_validation.json`. Dùng `python -m scripts.test_all`, không chạy model benchmark để verify.',
             '','## M. Files và lịch sử','',history_text,'', 'Báo cáo cập nhật: p7_unified_results.csv/p7_unified_benchmark.md/p7_completion.json và báo cáo này. Không sửa raw/processed/cache/local model/saved predictions. Công cụ `scripts.publish_kaggle_results` reverify trước publish; không nhập bằng tên folder đơn thuần.']
    (root/'reports/model_stack_refactor_completion.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    from scripts.analyze_error_causes import analyze
    analyze(root)
    return read(root/'reports/p7_completion.json')

if __name__=='__main__':publish()
