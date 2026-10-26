"""Dựng P3 tinh gọn từ các bảng bất biến; không chạy lại pipeline hoặc model."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from src.config import PROJECT_ROOT
from src.data.eda import LABELS
from src.data.eda_refinement import compact_tables
from scripts.export_p3_report import markdown

COLORS = ['#a84144', '#737c87', '#287b69']
AUDIT = [
    ('sentiment.csv', 'table', 'KEEP', 'Neutral8,77%; macro/per-class F1', 'P5–P7'),
    ('length_by_sentiment.csv', 'table', 'KEEP', 'Median/IQR theo lớp; giữ đuôi dài', 'P4/P6'),
    ('lexical_by_class.csv', 'table', 'KEEP', 'Tỷ lệ trong/ngoài lớp; hỗ trợ và effect size', 'P7/P8/P9'),
    ('themes.csv', 'table', 'KEEP', 'Mention rates có từ điển, không polarity', 'P8/P9'),
    ('brands.csv', 'table', 'KEEP', 'Chỉ giữ concentration, không xếp hạng hãng', 'P4/P7'),
    ('products.csv', 'table', 'KEEP', 'Nhóm sản phẩm lặp và singleton; split', 'P4'),
    ('verified.csv', 'table', 'KEEP', 'Chênh negative10,30điểm%; confounded bởi độ dài', 'P7'),
    ('rating.csv', 'table', 'APPENDIX', 'Tra mapping sao; trùng class snapshot', 'P2/P7'),
    ('years.csv', 'table', 'APPENDIX', 'Audit thời gian, chưa quyết định model', 'Tham khảo'),
    ('months.csv', 'table', 'APPENDIX', 'Audit coverage, không doanh số', 'Tham khảo'),
    ('missing.csv', 'table', 'APPENDIX', 'Null/empty audit; P2 có báo cáo riêng', 'P2'),
    ('theme_contexts.csv', 'table', 'APPENDIX', 'Ngữ cảnh chưa human-verified; giữ local', 'P8/P9'),
    ('noise_examples.csv', 'table', 'APPENDIX', 'Worklist riêng, không noise prevalence', 'P7'),
    ('frequent_terms.csv', 'table', 'REMOVE FROM REPORT', 'Tần suất chung không phân biệt lớp', 'Không thêm quyết định'),
    ('length_histogram.csv', 'table', 'REMOVE FROM REPORT', 'Trùng độ dài; thiếu class conditioning', 'Không thêm quyết định'),
    ('figures/rating_proxy.png', 'figure', 'KEEP', 'Chỉ giữ panel class; bỏ panel sao lặp', 'P5–P7'),
    ('figures/length.png', 'figure', 'KEEP', 'Thay median bars bằng median/IQR', 'P4/P6'),
    ('figures/distinctive_bigrams.png', 'figure', 'KEEP', 'Top5/lớp; within vs outside rates', 'P7'),
    ('figures/brands.png', 'figure', 'APPENDIX', 'Concentration table đủ cho core', 'P4/P7'),
    ('figures/time.png', 'figure', 'APPENDIX', 'Coverage tham khảo', 'Tham khảo'),
    ('figures/themes.png', 'figure', 'REMOVE FROM REPORT', 'Lặp bảng mention rates', 'P8/P9 dùng bảng'),
    ('figures/verified_purchase.png', 'figure', 'REMOVE FROM REPORT', 'Bảng ngắn đủ và nêu confounders', 'P7 dùng bảng'),
]
TRACE = [
    ('Neutral minority', 'P5/P6/P7', 'Macro F1 và per-class/neutral F1; thử weights chỉ train/validation', 'Quan sát cũ; không chứng minh causal imbalance'),
    ('Median/IQR và đuôi dài', 'P4/P6', 'Giữ context/negation; đối chiếu tokenizer max length đã khóa', 'Không đổi max_length bằng full-data EDA'),
    ('Product/brand concentration', 'P4', 'Product/variant-aware split; kiểm ID/text/near overlap', 'P4 đã thực hiện; EDA không chứng minh zero semantic leakage'),
    ('Phrase phân biệt theo lớp', 'P7', 'Ngữ cảnh chẩn đoán phủ định, failure, mixed wording', 'Không dùng full-data phrases làm selected features'),
    ('Rating là proxy', 'P7/P10', 'Human diagnosis; giữ independent gold riêng', 'P7 là xác nhận về sau, không thông tin P3 đã biết'),
    ('Aspect-like language đa chủ đề', 'P8/P9', 'ATE span-level + ASC theo occurrence', 'Động lực, không gold ABSA từ keyword'),
    ('Verified-group khác cả độ dài', 'P7', 'Nêu giới hạn composition; không metadata feature hoặc lọc lại', 'Liên hệ mô tả, không causal quality label'),
]


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def md_table(rows: list[list], headers: list[str]) -> str:
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(v).replace('|', '/') for v in row) + ' |' for row in rows])


def number(value: float, places: int = 2) -> str:
    return f'{value:,.{places}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def four(observation: str, evidence: str, interpretation: str, impact: str) -> str:
    return '\n\n'.join([f'**{label}:** {text}' for label, text in [
        ('Observation', observation), ('Evidence', evidence),
        ('Interpretation', interpretation), ('Project Impact', impact)]])


def plots(core: dict, output: Path) -> None:
    """Ba hình có mục đích riêng; không histogram/word cloud hoặc chart trùng bảng."""
    plt.rcParams.update({'svg.hashsalt': 'p3_refinement_v1', 'font.family': 'DejaVu Sans', 'font.size': 10})
    output.mkdir()

    def save(fig, name, rect=None):
        fig.tight_layout(rect=rect)
        fig.savefig(output / f'{name}.png', dpi=160)
        fig.savefig(output / f'{name}.svg', metadata={'Date': None})
        plt.close(fig)

    data = core['snapshot'].set_index('sentiment').reindex(LABELS)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(LABELS, data.reviews, color=COLORS)
    for i, row in enumerate(data.itertuples()):
        ax.text(i, row.reviews + 500, f'{number(row.reviews, 0)}\n{number(row.review_share * 100)}%', ha='center')
    ax.set(ylabel='Số bài', title='Neutral là lớp thiểu số theo nhãn suy từ sao', ylim=(0, 23000))
    save(fig, 'class_distribution')

    data = core['length'].set_index('sentiment').reindex(LABELS)
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, (label, row) in enumerate(data.iterrows()):
        ax.plot([row.q25_words, row.q75_words], [i, i], lw=8, color=COLORS[i], alpha=.5)
        ax.scatter(row.median_words, i, color=COLORS[i], s=70, zorder=3)
        ax.text(row.q75_words + 3, i, f'{row.q25_words:g} / {row.median_words:g} / {row.q75_words:g}', va='center')
    ax.set(yticks=range(3), yticklabels=LABELS, xlim=(0, 155), ylim=(-.6, 2.6),
           xlabel='Số từ trong body; đoạn = Q25–Q75, điểm = median', title='Phân vị theo lớp, không chỉ trung bình')
    save(fig, 'length_iqr')

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharex=True)
    for ax, label, color in zip(axes, LABELS, COLORS):
        rows = core['phrases'].query('sentiment == @label').iloc[::-1]
        for i, row in enumerate(rows.itertuples()):
            ax.plot([row.rest_prevalence * 100, row.prevalence * 100], [i, i], color=color, lw=2)
        ax.scatter(rows.rest_prevalence * 100, range(len(rows)), marker='x', color='#737c87', label='Ngoài lớp')
        ax.scatter(rows.prevalence * 100, range(len(rows)), color=color, label='Trong lớp')
        ax.set(yticks=range(len(rows)), yticklabels=rows.term, xlabel='% bài chứa phrase', title=label)
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=2)
    save(fig, 'phrase_comparison', rect=(0, 0, 1, .9))


def report(core: dict, summary: dict, readiness: dict, human: dict, cfg: dict) -> str:
    """Nội dung hiện hành, phân biệt rõ quan sát gốc và xác nhận downstream."""
    labels = core['snapshot'].set_index('sentiment')
    phrases = core['phrases']
    failure = core['failure_phrases']
    verified = core['verified'].set_index('verified_purchase')
    delta = float(verified.loc[False, 'negative_share'] - verified.loc[True, 'negative_share']) * 100
    ratio = labels.loc['positive', 'reviews'] / labels.loc['neutral', 'reviews']
    lexical_rows = [[r.sentiment, r.term, f'{r.documents}/{r.class_documents}', number(r.prevalence * 100),
                     f'{r.outside_documents}/{r.outside_class_documents}', number(r.rest_prevalence * 100),
                     number(r.prevalence_difference * 100), number(r.smoothed_lift)] for r in phrases.itertuples()]
    failure_rows = [[r.term, f'{r.documents}/{r.class_documents}', number(r.prevalence * 100),
                     f'{r.outside_documents}/{r.outside_class_documents}', number(r.rest_prevalence * 100),
                     number(r.prevalence_difference * 100), number(r.smoothed_lift)] for r in failure.itertuples()]
    themes = core['theme_rates']
    theme_rows = [[r.theme, int(r.negative), number(r.negative_rate * 100), int(r.neutral),
                   number(r.neutral_rate * 100), int(r.positive), number(r.positive_rate * 100)] for r in themes.itertuples()]
    concentration = [[r.scope, r.indicator, int(r.numerator), '—' if pd.isna(r.denominator) else int(r.denominator),
                       '—' if pd.isna(r.share) else number(r.share * 100)] for r in core['concentration'].itertuples()]
    all_h = human['all_360_descriptive_only']
    srs = human['groups']['representative']
    enriched = human['groups']['diagnostic_enriched']
    text = [
        '# P3 — EDA trọng tâm cho sentiment và ABSA laptop',
        f'Bản tinh gọn {cfg["date"]}, task `{cfg["task_id"]}`. Quan sát gốc từ P3 ngày2026-10-09; các liên hệ P4–P9 bên dưới được bổ sung hồi cứu, không viết lại điều P3 đã biết. Bộ bảng/hình gốc và báo cáo cũ giữ nguyên. Dataset/split/model/benchmark không đổi.',
        '## 1. Mục tiêu và phạm vi',
        'Giữ EDA giúp hiểu class imbalance, text/context, dấu hiệu từ vựng, concentration và proxy-label risk. Đây là phân tích mô tả toàn bộ30K đã khóa, không chọn đặc trưng/hyperparameters từ test. Không huấn luyện, chạy ABSA Amazon hoặc sinh nhãn người. Không dùng p-value để phóng đại chênh lệch nhỏ.',
        '## 2. Dataset snapshot',
        four(f'{summary["rows"]:,} review laptop, {summary["products"]:,} sản phẩm; ba nhãn suy từ sao.',
             'Bảng1 trích `sentiment.csv`; số sản phẩm từ `summary.json`.',
             'Counts là mẫu đã qua lọc/sampling, không đại diện thị trường; số sản phẩm theo từng lớp có thể giao nhau.',
             'Giữ negative/neutral/positive=0/1/2 và cùng mẫu số xuyên P4–P7; không relabel sau EDA.'),
        md_table([[r.sentiment, r.reviews, number(r.review_share * 100)] for r in core['snapshot'].itertuples()], ['Nhãn proxy', 'Review', 'Tỷ lệ %']),
        '## 3. Class imbalance và lựa chọn metric',
        four(f'Neutral chỉ{number(labels.loc["neutral", "review_share"] * 100)}%; positive nhiều gấp{number(ratio)} lần neutral.',
             'Bảng1 và Hình1; đây là quan sát P3 gốc.',
             'Accuracy chịu ảnh hưởng lớp lớn; macro F1/per-class F1 cần để nhìn minority. Imbalance là challenge có khả năng ảnh hưởng, chưa chứng minh nguyên nhân của lỗi.',
             'P5/P6 so unweighted/balanced bằng validation; P7 báo neutral F1. Later confirmation: BERT overall chọn unweighted; P7 weighted validation macro F1 giảm, nên không mặc định weights giải quyết mọi lỗi.'),
        '![Hình1 — class distribution](figures/class_distribution.png)',
        '## 4. Review length và độ phức tạp biểu diễn',
        four('Median body words negative/neutral/positive=50/56/37; IQR tương ứng76/93/72. Negative/neutral thường dài hơn ở trung tâm, nhưng IQR chồng lấn mạnh.',
             'Bảng2/Hình2 từ `length_by_sentiment.csv`, chỉ lấy word_count; Q25/median/Q75, không suy BERT tokens từ từ tách whitespace.',
             'Chênh median13/19từ so positive đáng lưu ý về context; không đủ kết luận model sai vì review dài. Positive vẫn có đuôi rất dài; median không phản ánh truncation tail.',
             f'Later measurement: readiness canonical title+body có{number(readiness["above_token_limit_share"]["256"] * 100)}% vượt256 và{number(readiness["above_token_limit_share"]["512"] * 100)}% vượt512 BERT WordPiece. MiniLM256/BERT512 là context budgets khác; P4 đã chốt protocol, không đổi bằng EDA mới. Body median43 và canonical median48 không mâu thuẫn vì khác văn bản.'),
        md_table([[r.sentiment, int(r.reviews), r.q25_words, r.median_words, r.q75_words, r.iqr_words] for r in core['length'].itertuples()], ['Lớp', 'n', 'Q25 từ', 'Median từ', 'Q75 từ', 'IQR từ']),
        '![Hình2 — median và IQR](figures/length_iqr.png)',
        '## 5. Discriminative language — phrase có mẫu số',
        four('Phủ định/return nổi lên ở negative; các cụm khen và pin/giá nổi lên ở positive. Neutral không đồng nghĩa không có ngôn ngữ đánh giá.',
             'Bảng3/Hình3: top5bigrams mỗi lớp theo chênh prevalence trong–ngoài lớp, support trong lớp≥30; tie theo count giảm rồi term tăng. Không cố định phrase thắng.',
             'Mỗi phrase đếm tối đa một lần/review, có mẫu số trong/ngoài lớp. Lift=(k+1)/(n+2) chia tỷ lệ ngoài lớp làm trơn tương tự; effect size là điểm %. Phrase có thể chồng lấn/ngữ cảnh phủ định; không causal hoặc feature importance.',
             'Giữ negation/punctuation trong pipeline; dùng EDA để giải thích error patterns P7, không biến full-data lexical ranking thành chọn features có giám sát. Các phrase là body n-grams; không artifact ATE hoặc nhãn aspect.'),
        md_table(lexical_rows, ['Lớp', 'Phrase', 'Trong lớp k/n', 'Trong %', 'Ngoài lớp k/n', 'Ngoài %', 'Δ điểm %', 'Lift làm trơn']),
        '![Hình3 — within và outside class](figures/phrase_comparison.png)',
        '## 6. Negative failure signals',
        four('Top failure phrases theo quy tắc hiện tại chủ yếu là trả hàng và ngừng hoạt động; không có căn cứ buộc mọi nhóm overheating/software/keyboard đều nổi bật.',
             'Bảng4 lọc bigram/trigram theo regex failure trong config rồi xếp cùng effect-size/support. Ví dụ “to return” và “stopped working” được dữ liệu chọn; full regex và ngưỡng lưu trong config snapshot.',
             'Đây là mention của dấu hiệu lexical, không đếm số sự cố đã xác minh. “to return” có thể nói trả hàng dự định, “not broken” có thể phủ định; các hàng overlap, không cộng thành prevalence complaint category.',
             'P7 có thể tra context khi phân tích failure/return; chưa có human cause labels cho tổng thể. Không khái quát thành tỷ lệ hỏng laptop hoặc lọc dữ liệu/model theo complaint.'),
        md_table(failure_rows, ['Phrase', 'Negative k/n', 'Negative %', 'Ngoài k/n', 'Ngoài %', 'Δ điểm %', 'Lift làm trơn']),
        '## 7. Positive value signals và aspect-like mentions',
        four('Trong positive, các chủ đề giá, tính di động và hiệu năng được nhắc với tỷ lệ cao hơn negative; battery life/the price cũng có effect size dương ở bảng phrase.',
             'Bảng5 giữ đủ9chủ đề của từ điển P3, không bỏ hàng không hợp kỳ vọng. Counts nêu mẫu số8259/2631/19110 ở bảng1; một review có thể nhắc nhiều chủ đề.',
             'Đây là ứng viên để hỏi người dùng hài lòng về khía cạnh nào, chưa trả lời chắc “hài lòng vì gì”. Mention trong positive không đồng nghĩa aspect được khen: có thể có complaint hoặc so sánh bên trong. Không dùng keyword làm sentiment hoặc causal value driver.',
             'Motivation cho P8/P9: cần trích span rồi phân loại có điều kiện theo aspect occurrence. Giữ kết luận ở mức lexical evidence đến khi có aspect-level gold/validation.'),
        md_table(theme_rows, ['Chủ đề từ điển', 'Neg count', 'Neg %', 'Neu count', 'Neu %', 'Pos count', 'Pos %']),
        '## 8. Neutral-class characteristics',
        four('Neutral là2631review, tất cả rating3 do mapping; median56từ/IQR93, rộng hơn hai lớp còn lại. Top phrase gồm “is not”, “a good” cùng các cụm nhắc battery/keyboard.',
             'Bảng1–3/5: support và rates ở cùng dataset, không thêm annotation. Rating3 là định nghĩa proxy class, không phát hiện độc lập về cảm xúc.',
             'Cả dấu hiệu khen/phủ định ở cấp lớp không chứng minh cùng một review chứa cả hai. Mixed-language rate, fact-like statements, weak sentiment, comparison và praise+complaint co-occurrence chưa được định lượng có nhãn; ghi NOT_MEASURED, không gán nhãn bằng trực giác.',
             'Neutral cần per-class metrics và P7 human diagnosis. Later confirmation P7 cho thấy proxy–human mismatch; không quy toàn bộ khó khăn cho imbalance. Neutral ASC P9 thuộc SemEval aspect-level, khác Amazon overall neutral, không nhập hai population.'),
        '## 9. Concentration và khác biệt nhóm metadata',
        four('5025/9080sản phẩm chỉ có1review; top100sản phẩm chứa5802/30000review; top5brand categories chứa23837/30000review.',
             'Bảng6 tổng hợp products/brands, không nhúng9080product rows hoặc xếp hạng theo sentiment.',
             'Repeated products tạo dependence tiềm năng giữa review; singleton nhiều làm subgroup estimates không ổn định. Top5≈79,46% là selected-pool concentration, không market share hoặc bias đã đo theo hiệu năng.',
             'P4 dùng product/variant/text groups và leakage audit. P2/P4 duplicate checks đã có: exact residual0 không đồng nghĩa semantic near-duplicate-free. Không sửa split hoặc brand quotas.'),
        md_table(concentration, ['Scope', 'Chỉ báo', 'Tử số/giá trị', 'Mẫu số', 'Tỷ lệ %']),
        four(f'Non-verified negative rate cao hơn verified{number(delta)}điểm%; median words102so38.',
             'Bảng7 có counts/mẫu số, cả neutral và độ dài; đây là chênh đáng lưu ý về composition, không chỉ chart trạng thái mua hàng.',
             'Product mix/tuổi review/độ dài/exposure chưa kiểm soát; không kết luận non-verified giả hoặc xác minh làm sentiment tích cực hơn.',
             'Giữ cả hai nhóm, không metadata feature trong active benchmark. Kết quả là caveat về selection/composition khi diễn giải P7, không đưa ra filter/model mới.'),
        md_table([[r.verified_purchase, r.reviews, r.negative_count, number(r.negative_share * 100), r.neutral_count,
                   number(r.neutral_share * 100), r.median_words] for r in core['verified'].itertuples()], ['Verified', 'n', 'Negative n', 'Negative %', 'Neutral n', 'Neutral %', 'Median từ']),
        '## 10. Rating–text tension: quan sát gốc và xác nhận về sau',
        four('Original P3: nhãn suy từ sao và ví dụ context có thể khen/chê đan xen; chưa có human noise estimate đại diện.',
             f'Later confirmation P7 ngày2026-10-25: disagreement{all_h["disagreement"]}/{all_h["n"]} chỉ mô tả mẫu gộp. SRS={srs["disagreement"]}/{srs["n"]}; enriched={enriched["disagreement"]}/{enriched["n"]}, phải tách scope. Nguồn `reports/p7_human_audit_results.json`, báo cáo P7 bên dưới.',
             'P7 đo reused-test diagnosis, không whole30K noise rate và không independent P10gold. Khoảng tin cậy SRS trong P7 chỉ cho test population4500 và phụ thuộc nhãn người; không dùng pooled360 suy population.',
             'Giữ provenance proxy trong mọi score; P7 phân biệt lỗi proxy và lỗi model; P10 vẫn cần independent human sentiment/ABSA gold. Không sửa rating/labels sau kết quả P7.'),
        '[P7 human diagnosis](../p7_error_cause_analysis.md); [P7 artifact](../p7_human_audit_results.json).',
        '## 11. Motivation for downstream ABSA',
        four('Các phrase/aspect-like mentions phân biệt theo nhãn overall, nhưng một review có thể nhắc nhiều chủ đề và polarity khác nhau.',
             'Bảng3–5 là original lexical evidence. P3 context examples giữ ở appendix có status chưa aspect-labeled; không dùng kết quả model P8/P9 làm phát hiện P3 ban đầu.',
             'Overall classification không xác định span hay sentiment của từng occurrence; từ điển chưa có precision/recall do người xác minh.',
             'P8 cần span-level entity evaluation; P9 cần gold-aspect ASC và joint predicted spans riêng, policy conflict rõ. Không infer ABSA trên Amazon trong refinement này.'),
        '## 12. Bảy kết luận chính',
        '- Neutral8,77% đòi hỏi macro F1/per-class F1; weighting phải chọn validation, không mặc định.',
        '- Negative/neutral có median body dài hơn positive, nhưng IQR chồng lấn; không gán nguyên nhân lỗi model.',
        '- Phrase failure/return có concentration trong negative, đo bằng tỷ lệ trong/ngoài lớp và support.',
        '- Positive có lexical signals về pin/giá/di động/hiệu năng; chưa phải aspect sentiment hoặc causal value drivers.',
        '- Neutral có wording đa dạng; rating3 không đảm bảo neutral theo text. Mixed/weak/factual causes vẫn chưa đo.',
        '- Product/brand concentration và metadata-group differences giới hạn diễn giải, hỗ trợ group split thay vì brand ranking.',
        '- P7 xác nhận proxy–human tension về sau; aspect-like evidence tạo động lực cho ATE+ASC, không thay human gold.',
        '## 13. Cross-phase traceability',
        md_table([list(r) for r in TRACE], ['P3 finding', 'Phase sau', 'Decision/diễn giải', 'Giới hạn thời gian và suy luận']),
        'P4: `reports/p4/p4_20261009_final/leakage_report.json`; P6: `reports/p6_transformer_benchmark.md`; P7: `reports/p7_error_cause_analysis.md`; P8: `reports/p8_aspect_extraction.md`; P9: `reports/p9_exp01_deberta_20261026_v2/report.md`. Đây là traceability hồi cứu, không xác nhận EDA gây ra mọi quyết định. Dataset/split/context budgets và model selection đã khóa vẫn giữ nguyên.',
        '## Appendix — audit tham khảo, không core findings',
        'Sáu bảng được demote và hai hình gốc giữ nguyên trong `../p3/20261009_verified/`:',
    ]
    for name, kind, rec, reason, phase in AUDIT:
        if rec == 'APPENDIX':
            text.append(f'- [{name}](../p3/20261009_verified/{name}) — {reason}; {phase}.')
    text += [
        '### A9. Helpfulness — chưa đủ giải thích complaint cụ thể',
        f'Tỷ lệ helpful_vote>0 toàn mẫu={number(summary["helpful_nonzero_share"] * 100)}%, median0, max{summary["helpful_max"]}. Spearman words–helpful={number(summary["helpful_words_spearman"], 4)}. Field không hoàn toàn sparse nhưng right-skew; không có denominator exposure/tuổi review hoặc nhãn complaint specificity. Không kết luận helpful reviews chứa complaint cụ thể hơn.',
        md_table([[r.sentiment, r.reviews, number(r.helpful_mean, 3), r.helpful_median,
                   number(r.helpful_nonzero_share * 100)] for r in core['helpfulness'].itertuples()], ['Lớp', 'n', 'Mean votes', 'Median votes', 'Votes>0 %']),
        'Negative helpful mean không cao hơn positive trong bảng gốc; mean/median và zero-share cho góc nhìn khác nhau. Đây là mô tả appendix, không nhãn chất lượng hoặc feature được đưa vào model.',
        '### Phương pháp, tái lập và provenance',
        'Tám core tables và ba figures; appendix9items (6bảng,2hình tham chiếu,1helpfulness summary). `audit.md` liệt kê từng artifact/cột/figure, mục đích/insight/downstream và quyết định giữ/bỏ. `summary.json` lưu config/source/output hashes. Không xóa15CSV/7hình hoặc báo cáo/notebook gốc. CSV core dùng số đếm để tính lại rates; float gốc đã làm tròn không được coi là exact count.',
        '```powershell\n.venv/Scripts/python.exe -X utf8 -m scripts.refine_p3 --output-dir reports/p3_refinement_REPRODUCTION\n```',
        'Chọn thư mục mới chưa tồn tại; runner từ chối overwrite hoặc output ngoài reports. Chỉ đọc saved tables/summary và later evidence, không parse raw corpus, không tokenize lại hay train/infer.',
        '**Giới hạn:** chỉ laptop; proxy labels từ sao có nhiễu; SemEval–Amazon platform/style shift chưa đánh giá độc lập; independent human gold P10 dự kiến nhỏ/chưa có. Language/spam accuracy, mixed-sentiment prevalence, complaint specificity và tác động nhân quả đều chưa được đo. SemEval source/license NOT_VERIFIED theo owner exception. Không production/Vietnamese/general-device claim.',
    ]
    return '\n\n'.join(text) + '\n'


def build(output: Path, config: Path = Path('configs/p3_refinement.yaml'), root: Path = PROJECT_ROOT) -> dict:
    """Dựng báo cáo mới có manifest, không overwrite bất kỳ artifact nào."""
    root = root.resolve()
    output = (root / output).resolve() if not output.is_absolute() else output.resolve()
    if not output.is_relative_to(root / 'reports') or output == root / 'reports':
        raise ValueError('Output phải là thư mục con mới trong reports')
    if output.exists():
        raise FileExistsError('Không ghi đè report/artifact đã tồn tại')
    config = root / config
    cfg = yaml.safe_load(config.read_text(encoding='utf-8'))
    source = root / cfg['source_directory']
    summary = load_json(source / 'summary.json')
    dataset = root / 'data/processed/laptop_reviews.parquet'
    if sha(dataset) != summary['source_sha256']:
        raise ValueError('Dataset khác P3 đã khóa')
    for name in summary['table_files']:
        if sha(source / name) != summary['output_sha256'][name]:
            raise ValueError(f'Bảng gốc đổi checksum: {name}')
    paths = list(source.rglob('*')) + [config, dataset,
        root / 'reports/p3_model_readiness.json', root / 'reports/p7_human_audit_results.json',
        root / 'reports/p3_data_analysis_20261009.md', root / 'reports/p3_insight_summary_20261009.md',
        root / 'notebooks/03_laptop_eda.ipynb', root / 'scripts/refine_p3.py', root / 'src/data/eda_refinement.py']
    before = {p.relative_to(root).as_posix(): sha(p) for p in paths if p.is_file()}
    tables = {p.stem: pd.read_csv(p) for p in source.glob('*.csv') if p.stem not in ['noise_examples', 'theme_contexts']}
    core = compact_tables(tables, cfg)
    core['traceability'] = pd.DataFrame(TRACE, columns=['finding', 'later_phase', 'decision', 'limits'])
    core['helpfulness'] = tables['sentiment'][['sentiment', 'reviews', 'helpful_mean', 'helpful_median', 'helpful_nonzero_share']]
    readiness = load_json(root / 'reports/p3_model_readiness.json')
    human = load_json(root / 'reports/p7_human_audit_results.json')
    output.mkdir(parents=True)
    (output / 'tables').mkdir()
    for name, frame in core.items():
        frame.to_csv(output / 'tables' / f'{name}.csv', index=False, float_format='%.12g')
    plots(core, output / 'figures')
    md = report(core, summary, readiness, human, cfg)
    (output / 'report.md').write_text(md, encoding='utf-8')
    audit = '# Current P3 Audit — P3-REFINE-01\n\n' + md_table(
        [[n, t, reason, phase, rec] for n, t, rec, reason, phase in AUDIT],
        ['Item', 'Type', 'Purpose / insight', 'Later phase', 'Recommendation'])
    audit += '\n\nNguồn cũ:15tables/7figures; Markdown3bảng/0embedded figures/9sections; HTML tổng hợp nhúng15tables/7figures. Đề xuất7table KEEP/6APPENDIX/2REMOVE;3figure KEEP/2APPENDIX/2REMOVE. Hai concentration tables gộp; thêm failure slice và traceability: bản mới8core tables/3figures/9appendix items. Không xóa file cũ. Helpfulness chỉ appendix do thiếu exposure và complaint-specificity labels.\n'
    audit += '\nArtifacts ngoài bảng: reports/p3/20261009 và _final là superseded; _verified là nguồn. Summary/task_validation/notebook_validation là acceptance lịch sử, giữ nguyên. Source notebook và executed/final notebook, hai báo cáo MD, HTML20261019, scripts analyze_p3/export_p3_report/p3_report_content/execute_p3_notebook, src/data/eda.py giữ nguyên. Config P4 trỏ P3 summary cũ để tái lập; config mới chỉ chọn presentation, không thay pipeline. README/PLAN/PROJECT_INDEX dẫn canonical mới; downstream manifests giữ references/hash lịch sử.\n'
    (output / 'audit.md').write_text(audit, encoding='utf-8')
    pieces = re.split(r'(!\[[^\]]*\]\(figures/[^)]+\.png\))', md)
    body = []
    for part in pieces:
        match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', part)
        if match:
            image = base64.b64encode((output / match[2]).read_bytes()).decode()
            body.append(f'<figure><img alt="{match[1]}" src="data:image/png;base64,{image}"><figcaption>{match[1]}</figcaption></figure>')
        else:
            rendered = markdown(part)
            body.append(re.sub(r'<(/?)h([2-6])>', lambda m: f'<{m[1]}h{int(m[2])-1}>', rendered))
    css = 'body{font:16px/1.65 system-ui;color:#24332f;background:#f4f6f4;margin:0}main{max-width:1100px;margin:auto;background:white;padding:36px}h1,h2{color:#205c50}h2{margin-top:42px}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:8px;border:1px solid #d9e0dc;text-align:left}th{background:#eaf1ed}.scroll{overflow:auto}img{max-width:100%;height:auto}figure{margin:28px 0}code,pre{background:#f1f3f1}pre{padding:18px;overflow:auto}@media print{main{padding:0}table,figure{break-inside:avoid}}'
    (output / 'report.html').write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P3 — EDA trọng tâm</title><style>' + css + '</style><main>' + '\n'.join(body) + '</main></html>', encoding='utf-8')
    after = {p: sha(root / p) for p in before}
    if before != after:
        raise ValueError('Nguồn đã thay đổi trong khi dựng report')
    result = {'status': 'REPORT_BUILD_COMPLETE', 'task_id': cfg['task_id'], 'date': cfg['date'],
              'before': {'generated_tables': 15, 'generated_figures': 7, 'markdown_sections': 9, 'markdown_tables': 3, 'markdown_figures': 0},
              'after': {'core_tables': 8, 'core_figures': 3, 'appendix_items': 9},
              'audit': [dict(zip(['path', 'type', 'recommendation', 'insight', 'later_phase'], r)) for r in AUDIT],
              'configuration': cfg, 'source_sha256': before, 'source_preservation': 'PASS',
              'integrity': cfg['policy'], 'dataset_sha256': summary['source_sha256'],
              'core_table_files': [f'tables/{n}.csv' for n in core if n != 'helpfulness'],
              'appendix_table_files': ['tables/helpfulness.csv'],
              'output_sha256': {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('reports/p3_refinement_20261026'))
    parser.add_argument('--config', type=Path, default=Path('configs/p3_refinement.yaml'))
    args = parser.parse_args()
    result = build(args.output_dir, args.config)
    print(json.dumps({'status': result['status'], 'task_id': result['task_id'], 'after': result['after']}))


if __name__ == '__main__':
    main()
