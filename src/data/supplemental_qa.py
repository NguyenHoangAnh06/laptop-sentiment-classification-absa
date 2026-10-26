"""SRS bổ sung từ khung đã cố định siêu dữ liệu-REJECT, không có con người nhãn."""

import gzip
import json
import math
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.feasibility import check_memory, process_memory, source_info
from src.data.independent_qa import (REVIEW_COLUMNS, HUMAN_COLUMNS, LABELS, ERROR_REASONS,
                                     _strings, fixed_fingerprint, metadata_fields, read_csv, write_csv)
from src.data.laptop_filter import classify_product, parent_identifier
from src.data.loader import ScanStats, first_present, iter_jsonl, scan_jsonl
from src.data.validation import stable_key
from src.evaluation.sampling_uncertainty import review_estimates, success_total_interval


def candidate_lines(population: int, excluded: set[int], count: int, seed: int) -> list[int]:
    """Thống nhất ra lệnh cho các ứng cử viên tuyến đầu mà không phân bổ đầy đủ dân số."""
    if min(population, count) < 1 or any(not 1 <= x <= population for x in excluded):
        raise ValueError("Invalid source-line frame")
    if count > population-len(excluded):
        raise ValueError("Insufficient remaining raw lines")
    forbidden = sorted(excluded)
    result = []
    for index in random.Random(seed).sample(range(population-len(excluded)), count):
        line = index+1
        for skipped in forbidden:
            if line < skipped:
                break
            line += 1
        result.append(line)
    return result


def frozen_pilot(kit: Path, evaluation: Path) -> tuple[dict, dict, list[dict]]:
    """Yêu cầu nhãn gán và sidecar được đánh giá vẫn khớp với giá trị băm đã cố định của chúng."""
    manifest = json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
    result = json.loads(evaluation.read_text(encoding='utf-8'))
    if result['pending_or_uncertain'] or result['conflicting_product_labels']:
        raise ValueError('Pilot unresolved')
    for task in ('product', 'review'):
        if sha256_file(kit/f'{task}_annotation.csv') != result['annotation_sha256'][task]:
            raise ValueError('Pilot annotation changed since evaluation')
    if sha256_file(kit/'private_predictions.json') != manifest['files']['private_predictions.json']['sha256']:
        raise ValueError('Pilot predictions changed')
    _, rows = read_csv(kit/'review_annotation.csv')
    refs = {r['annotation_id']: r for r in json.loads((kit/'private_predictions.json').read_text(encoding='utf-8'))}
    if any(r['annotation_id'] not in refs or fixed_fingerprint(r)!=refs[r['annotation_id']]['fixed_fingerprint'] for r in rows):
        raise ValueError('Pilot source bindings changed')
    return manifest, result, rows


def prepare_supplemental_qa(run: Path, raw: Path, pilot_kit: Path, pilot_evaluation: Path,
                            output: Path, acquisition: dict, limits: dict,
                            *, sample_size: int, seed: int = 20261008) -> dict:
    """Trích xuất SRS TỪ CHỐI mới bằng cách sử dụng chỉ mục đã lưu; truyền trực tiếp nguyên bản sang EOF.

    Chỉ các dòng ứng viên thống nhất mới được giải mã JSON. n lần từ chối đủ điều kiện đầu tiên của họ là SRS của khung bổ sung có điều kiện đối với phi công; sự thiếu hụt không thành công.
    """
    if output.exists():
        raise FileExistsError('Use a new supplemental kit directory')
    for protected in (run, raw, pilot_kit, pilot_evaluation.parent):
        a, b = output.resolve(), protected.resolve()
        if a == b or a in b.parents or b in a.parents:
            raise ValueError('Output must be separate from protected sources')
    if sample_size < 1:
        raise ValueError('Sample size must be positive')
    started = time.monotonic()
    deadline = started+limits['max_scan_seconds']
    pilot, evaluated, old_rows = frozen_pilot(pilot_kit, pilot_evaluation)
    report_path=run/'report.json'
    report=json.loads(report_path.read_text(encoding='utf-8'))
    if not report['source_coverage_complete'] or report['source']!='Electronics':
        raise ValueError('Complete Electronics snapshot required')
    if sha256_file(report_path)!=pilot['run_report_sha256']:
        raise ValueError('Run report differs from pilot')
    if stable_key(acquisition['filter'],0)!=pilot['rules_sha256'] or acquisition['schema']!=pilot['schema_aliases']:
        raise ValueError('Rules/schema differ from pilot')
    inputs={}
    for kind, info in report['inputs'].items():
        path=raw/info['name']; checked=source_info(path)
        if checked['sha256']!=info['sha256'] or not checked['complete_source']:
            raise ValueError('Source checksum/completeness mismatch')
        if checked['manifest']['source_url']!=acquisition['amazon'][f'{kind}_url']:
            raise ValueError('Source URL mismatch')
        inputs[kind]={'path':path.as_posix(),'sha256':checked['sha256']}
    if sha256_file(run/'products.jsonl')!=report['output_sha256']['products.jsonl']:
        raise ValueError('KEEP index checksum mismatch')
    products={}
    for _, row in iter_jsonl(run/'products.jsonl'):
        parent=parent_identifier(row,acquisition['schema']['metadata_id'])
        if parent in products or not classify_product(row,acquisition['filter']).include:
            raise ValueError('Invalid/stale selected index')
        products[parent]=row
    group=report['groups']['laptop']; nr=report['join_counts']['not_in_selected_metadata_index']
    if len(products)!=group['candidate_products'] or nr!=pilot['populations']['reviews_metadata_reject']:
        raise ValueError('Population differs from pilot')
    if (report['review_scan']['invalid_records'] or report.get('counts',{}).get('invalid_review_identifier',0)
            or nr+group['matched_reviews']!=report['review_scan']['rows']):
        raise ValueError('Index complement cannot reconstruct original REJECT frame')
    pilot_reject=evaluated['strata']['review:random_reject']['sample_size']
    if sum(row['product_id'] not in products for row in old_rows)!=pilot_reject:
        raise ValueError('Excluded v1 reviews include additional REJECT units; complement design invalid')
    n_remaining=nr-pilot_reject
    if sample_size>n_remaining:
        raise ValueError('Insufficient REJECT complement')
    excluded={json.loads(row['source_evidence'])['review_line'] for row in old_rows}
    n_raw=report['review_scan']['rows']
    candidates=candidate_lines(n_raw,excluded,min(n_raw-len(excluded),3*sample_size),seed)
    wanted=set(candidates); found={}; decoded=0; line=0
    source=Path(inputs['reviews']['path']); opener=gzip.open if source.suffix=='.gz' else open
    with opener(source,'rb') as handle:
        while payload := handle.readline(limits['max_record_bytes']+1):
            line += 1
            decoded+=len(payload)
            if len(payload)>limits['max_record_bytes'] or decoded>limits['max_scan_read_bytes']:
                raise ValueError('Read/record budget exceeded')
            if line in wanted:
                found[line]=json.loads(payload)
            if line%1000000==0:
                check_memory(limits['max_process_working_set_bytes'])
                if time.monotonic()>deadline:
                    raise TimeoutError('Supplemental extraction deadline exceeded')
                print(f'Supplemental extraction {line:,}/{n_raw:,}',flush=True)
    if line!=n_raw or len(found)!=len(wanted):
        raise ValueError('Source EOF/line count mismatch')
    selected=[]
    for line in candidates:
        row=found[line]; parent=parent_identifier(row,acquisition['schema']['review_parent_id'])
        if parent not in products:
            selected.append({'product_id':parent,'review_id':f"amazon2023:{inputs['reviews']['sha256']}:{line}",
                             'review_title':first_present(row,acquisition['schema']['review_title']),
                             'review_text':first_present(row,acquisition['schema']['review_text']),
                             'source_line':line})
        if len(selected)==sample_size:
            break
    if len(selected)!=sample_size:
        raise ValueError('Insufficient random REJECT candidates; no kit written')
    needed={r['product_id'] for r in selected}; enriched={}; stats=ScanStats()
    for line,row in scan_jsonl(Path(inputs['metadata']['path']),stats,
                              max_rows=limits['scan_metadata_records'],
                              max_bytes=limits['max_scan_read_bytes']-decoded,
                              deadline=deadline,max_record_bytes=limits['max_record_bytes']):
        parent=parent_identifier(row,acquisition['schema']['metadata_id'])
        if parent in needed:
            if parent in enriched or classify_product(row,acquisition['filter']).include:
                raise ValueError('Ambiguous metadata or index/decision contradiction')
            evidence={'dataset':'Amazon Reviews 2023 Electronics','metadata_file':inputs['metadata']['path'],
                      'metadata_sha256':inputs['metadata']['sha256'],'metadata_line':line,
                      'join_key':'parent_asin','external_url_status':'lookup_hint_not_verified'}
            enriched[parent]=metadata_fields(row,evidence)
        if line%10000==0:
            check_memory(limits['max_process_working_set_bytes'])
    if not stats.eof_observed or stats.invalid_records or stats.rows!=report['metadata_scan']['rows']:
        raise ValueError('Incomplete/invalid metadata scan')
    human,sidecar=[],[]
    for row in selected:
        metadata=enriched.get(row['product_id']) or metadata_fields(None,{
            'metadata_status':'no_matching_parent_in_complete_source','metadata_sha256':inputs['metadata']['sha256']})
        item={**metadata,**row,'annotation_id':stable_key({'review_id':row['review_id']},seed+1)[:24],
              'product_url':f"https://www.amazon.com/dp/{row['product_id']}"}
        item['source_evidence']={**metadata['source_evidence'],'review_file':inputs['reviews']['path'],
                                 'review_sha256':inputs['reviews']['sha256'],'review_line':row['source_line']}
        item.update({k:'' for k in HUMAN_COLUMNS}); csv_row=_strings(item,REVIEW_COLUMNS)
        human.append(csv_row)
        sidecar.append({'annotation_id':item['annotation_id'],'review_id':row['review_id'],
                        'task':'review','stratum':'random_reject_complement','prediction':False,
                        'frame_population':n_remaining,'sample_size':sample_size,
                        'inclusion_probability':sample_size/n_remaining,
                        'sampling_weight':n_remaining/sample_size,'fixed_fingerprint':fixed_fingerprint(csv_row)})
    human.sort(key=lambda r:stable_key({'annotation_id':r['annotation_id']},seed+2))
    if len({r['review_id'] for r in human})!=sample_size or {r['review_id'] for r in human}&{r['review_id'] for r in old_rows}:
        raise ValueError('Sample duplicate/overlap')
    output.mkdir(parents=True)
    write_csv(output/'review_annotation.csv',REVIEW_COLUMNS,human)
    (output/'annotation_guide.md').write_text(
        (PROJECT_ROOT/'docs/SUPPLEMENTAL_REJECT_QA.md').read_text(encoding='utf-8'),encoding='utf-8')
    (output/'private_predictions.json').write_text(json.dumps(sidecar,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'version':'supplemental_reject_v2','status':'READY_FOR_HUMAN','seed':seed,
            'pilot_kit':pilot_kit.as_posix(),'pilot_evaluation':pilot_evaluation.as_posix(),
            'pilot_evaluation_sha256':sha256_file(pilot_evaluation),
            'pilot_manifest_sha256':sha256_file(pilot_kit/'manifest.json'),
            'pilot_annotation_sha256':evaluated['annotation_sha256'],
            'sources':inputs,'run_report':report_path.as_posix(),'run_report_sha256':sha256_file(report_path),
            'index_sha256':sha256_file(run/'products.jsonl'),'rules_sha256':pilot['rules_sha256'],
            'populations':{'raw_reviews':n_raw,'valid_keep':group['valid_reviews'],'original_reject':nr,
                           'pilot_reject_certainty':pilot_reject,'reject_complement':n_remaining,
                           'excluded_selected_but_invalid':group['matched_reviews']-group['valid_reviews']},
            'sample_size':sample_size,'inclusion_probability':sample_size/n_remaining,
            'sampling_weight':n_remaining/sample_size,'diagnostic_samples':0,
            'sampling':'Uniform ordered raw-line candidate SRS excluding all v1 review lines; first n metadata-unselected candidates. Conditional SRS of REJECT complement. Stream to EOF/CRC; candidate shortage fails without output.',
            'combined_estimator':'Old random REJECT 150 fixed known units weight1; new sample weights (N_REJECT-150)/n_new. KEEP uses v1 N_KEEP/150. Pilot-dependent size: do not naively pool old/new as SRS.',
            'resources':{'elapsed_seconds':time.monotonic()-started,'decoded_read_bytes':decoded+stats.decoded_bytes,
                         'review_candidates_decoded':len(found),'metadata_rows_read':stats.rows,**process_memory()},
            'files':{p.name:{'sha256':sha256_file(p),'bytes':p.stat().st_size} for p in output.iterdir()}}
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def evaluate_supplemental_qa(kit: Path, *, annotator: str, confirm_human: bool,
                             ai_assisted_review: bool | None = False,
                             review_annotations: Path | None = None,
                             review_confirmation: Path | None = None) -> dict:
    """Chỉ đánh giá trong tương lai sau khi xác minh con người thực tế; không bao giờ đổ lỗi cho khoảng trống."""
    if not confirm_human or not annotator.strip():
        raise ValueError('Explicit human confirmation and annotator required')
    m=json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
    if sha256_file(kit/'private_predictions.json')!=m['files']['private_predictions.json']['sha256']:
        raise ValueError('Supplemental sidecar changed')
    pilot_kit=Path(m['pilot_kit']); pilot_eval=Path(m['pilot_evaluation'])
    if sha256_file(pilot_eval)!=m['pilot_evaluation_sha256'] or sha256_file(pilot_kit/'manifest.json')!=m['pilot_manifest_sha256']:
        raise ValueError('Pilot evidence changed')
    _,old,_=frozen_pilot(pilot_kit,pilot_eval)
    annotation_path=review_annotations or kit/'review_annotation.csv'
    normalization=None
    if review_annotations is not None:
        if review_confirmation is None:
            raise ValueError('Canonical override requires frozen human review confirmation')
        approval=json.loads(review_confirmation.read_text(encoding='utf-8'))
        binding=approval['canonical_v2']
        source=kit/'review_annotation.csv'
        if (Path(binding['source']).resolve()!=source.resolve()
                or Path(binding['path']).resolve()!=annotation_path.resolve()
                or sha256_file(source)!=binding['source_sha256']
                or sha256_file(annotation_path)!=binding['sha256']):
            raise ValueError('Canonical source/hash binding changed')
        declarations=[r for r in approval['annotations'] if Path(r['path']).resolve()==source.resolve()]
        if (len(declarations)!=1 or declarations[0]['annotator']!=annotator
                or declarations[0]['sha256']!=binding['source_sha256']
                or declarations[0]['human_verified'] is not True
                or declarations[0]['human_review_status']!='COMPLETED'
                or declarations[0]['review_status']!='APPROVED'):
            raise ValueError('Missing matching final human approval')
        _,original=read_csv(source)
        _,normalized=read_csv(annotation_path)
        originals={r['annotation_id']:r for r in original}
        if len(originals)!=len(original) or len(normalized)!=len(original):
            raise ValueError('Canonical source membership changed')
        for row in normalized:
            if row['annotation_id'] not in originals:
                raise ValueError('Canonical source membership changed')
            expected=dict(originals[row['annotation_id']])
            expected['human_label']=binding['mapping'].get(expected['human_label'].strip(),expected['human_label'].strip())
            if row!=expected:
                raise ValueError('Canonical conversion changed more than approved label representation')
        normalization={'confirmation_path':review_confirmation.as_posix(),
                       'confirmation_sha256':sha256_file(review_confirmation),**binding}
    columns,rows=read_csv(annotation_path)
    refs=json.loads((kit/'private_predictions.json').read_text(encoding='utf-8'))
    by_id={r['annotation_id']:r for r in refs}
    if (set(columns)!=set(REVIEW_COLUMNS) or len(by_id)!=len(refs) or len(rows)!=len(by_id)
            or len({r['review_id'] for r in rows})!=len(rows)
            or {r['annotation_id'] for r in rows}!=set(by_id)):
        raise ValueError('Invalid annotation schema/IDs')
    n=m['sample_size']; population=m['populations']['reject_complement']
    pilot_reject=old['strata']['review:random_reject']
    if (population!=pilot_reject['frame_population']-pilot_reject['sample_size']
            or m['populations']['valid_keep']!=old['strata']['review:random_keep']['frame_population']):
        raise ValueError('Complement frame differs from pilot')
    if len(rows)!=n or any(r['prediction'] is not False or r['stratum']!='random_reject_complement'
                          or r['frame_population']!=population or r['sample_size']!=n
                          or not math.isclose(r['inclusion_probability'],n/population)
                          or not math.isclose(r['sampling_weight'],population/n) for r in refs):
        raise ValueError('Invalid sampling metadata')
    counts=Counter(); comparisons=[]; labels=defaultdict(set)
    for row in old['comparisons']:
        if row['human_label'] in ('laptop','non_laptop'):
            labels[row['product_id']].add(row['human_label'])
    for row in rows:
        if fixed_fingerprint(row)!=by_id[row['annotation_id']]['fixed_fingerprint']:
            raise ValueError('Immutable annotation fields changed')
        label=row['human_label'].strip().lower()
        if label not in LABELS or row['human_error_reason'].strip() not in ERROR_REASONS:
            raise ValueError('Invalid human label/reason')
        if label and not row['human_evidence'].strip():
            raise ValueError('Missing human evidence')
        outcome='FN' if label=='laptop' else 'TN' if label=='non_laptop' else 'blank' if not label else 'uncertain'
        counts[outcome]+=1
        if label in ('laptop','non_laptop'):
            labels[row['product_id']].add(label)
        comparisons.append({**row,'stratum':'random_reject_complement','outcome':outcome,
                            'error_reason':row['human_error_reason'] or ('unclassified' if outcome=='FN' else '')})
    conflicts=sorted(p for p,v in labels.items() if len(v)>1)
    unresolved=counts['blank']+counts['uncertain']; combined=None
    keep=old['strata']['review:random_keep']; reject=old['strata']['review:random_reject']
    if not unresolved and not conflicts:
        combined=review_estimates(keep['frame_population'],keep['sample_size'],keep['counts'].get('TP',0),
                                  population,n,counts['FN'],known_reject_laptops=reject['counts'].get('FN',0),
                                  known_reject_non_laptops=reject['counts'].get('TN',0))
    prevalence_interval=None
    if not unresolved and not conflicts:
        prevalence_interval=[x/population for x in success_total_interval(counts['FN'],n,population)]
    return {'status':'PENDING_ANNOTATION_OR_ADJUDICATION' if unresolved or conflicts else 'HUMAN_EVALUATION_REVIEW_REQUIRED',
            'annotator':annotator,'label_provenance':('unspecified' if ai_assisted_review is None else
                'human_verified_after_ai_assistance' if ai_assisted_review else 'independent_human_declared'),
            'human_verified':True,'human_review_status':'COMPLETED','review_status':'APPROVED',
            'review_status_scope':'Final label approval only; QA/phase acceptance requires separate review',
            'ai_assistance':ai_assisted_review,
            'annotation_process':('Final human approval declared; AI-assistance history unspecified; independence not asserted.'
                if ai_assisted_review is None else 'Human-approved labels; prior assistance history retained.'),
            'annotation_sha256':sha256_file(annotation_path),'annotation_path':annotation_path.as_posix(),
            'normalization_binding':normalization,
            'pending_or_uncertain':unresolved,'conflicting_product_labels':conflicts,'counts':dict(counts),
            'supplemental_laptop_prevalence':counts['FN']/n if not unresolved and not conflicts else None,
            'supplemental_laptop_prevalence_95_interval':prevalence_interval,
            'pilot_laptop_prevalence':reject['counts'].get('FN',0)/reject['sample_size'],
            'combined_weighted_estimates':combined,'pilot_weighted_estimates':old['review_weighted_estimates'],
            'comparisons':comparisons,'population_scope':f"valid KEEP plus metadata REJECT; selected-but-invalid{m['populations']['excluded_selected_but_invalid']} excluded",
            'limitations':'Pilot human verification after AI suggestions retained; new review does not retroactively make v1 blind. No automatic gate completion. Diagnostics excluded; domain QA is not sentiment/ABSA gold.'}
