"""Tạo các bảng, sơ đồ và xuất xứ mô tả P3 từ các đầu ra P2 bất biến."""

import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.eda import LABELS, STOPWORDS, THEMES, build_tables

COLORS = ['#b34b4b','#888888','#31816d']


def plot_tables(tables: dict, output: Path, *, explain_terms: bool = False) -> list[str]:
    """Lưu các biểu đồ có thể xuất độc lập với chú thích proxy/coverage rõ ràng."""
    paths=[]
    def save(fig,name):
        if explain_terms:
            from textwrap import fill
            from scripts.p3_report_content import TERMS, VALUES
            if name == 'distinctive_bigrams':
                fig.set_size_inches(19, 8)
            for ax in fig.axes:
                title = ax.get_title().replace('review', 'bài đánh giá')
                title = title.replace('negative', 'tiêu cực (negative)').replace('neutral', 'trung tính (neutral)').replace('positive', 'tích cực (positive)')
                ax.set_title(fill(title, 65), fontsize=11)
                ax.set_xlabel(ax.get_xlabel().replace('review', 'Số bài đánh giá').replace('UTC', 'UTC (giờ chuẩn quốc tế)'))
                ax.set_ylabel(ax.get_ylabel().replace('review', 'bài đánh giá').replace('negative', 'tiêu cực'))
                for direction in ('x', 'y'):
                    labels = getattr(ax, f'get_{direction}ticklabels')()
                    original = [label.get_text() for label in labels]
                    translated = []
                    for text in original:
                        meaning = TERMS.get(text) or VALUES.get(text)
                        if text in ('True', 'False') and name == 'verified_purchase':
                            meaning = 'đã xác minh' if text == 'True' else 'chưa xác minh'
                        translated.append(fill(f'{text} ({meaning})', 27) if meaning else text)
                    if original != translated:
                        ticks = getattr(ax, f'get_{direction}ticks')()
                        getattr(ax, f'set_{direction}ticks')(ticks, translated, fontsize=9)
                legend = ax.get_legend()
                if legend:
                    for text in legend.get_texts():
                        raw = text.get_text()
                        if raw in VALUES:
                            text.set_text(f'{raw} ({VALUES[raw]})')
                        text.set_fontsize(8)
                    legend.set_title('Nhãn suy từ số sao')
                    legend.get_title().set_fontsize(8)
                    if name == 'brands':
                        legend.set_loc('upper center')
                        legend.set_bbox_to_anchor((0.5, -0.16))
                    elif name == 'themes':
                        legend.set_loc('upper left')
                        legend.set_bbox_to_anchor((1.02, 1))
                if name == 'themes':
                    from matplotlib.ticker import PercentFormatter
                    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
                for text in ax.texts:
                    match = re.fullmatch(r'([\d,]+)\n(\d+\.\d+)%', text.get_text())
                    if match:
                        text.set_text(match[1].replace(',', '.') + '\n' + match[2].replace('.', ',') + '%')
        fig.tight_layout()
        for suffix in ('png','svg'):
            path=output/f'{name}.{suffix}'
            fig.savefig(path,dpi=160,bbox_inches='tight' if explain_terms else None,metadata={'Date':None} if suffix=='svg' else None)
            paths.append(path.name)
        plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    t=tables['rating'];axs[0].bar(t.rating,t.reviews,color='#466f9f');axs[0].set(title='Số sao của review laptop đã chọn',xlabel='Số sao',ylabel='review')
    t=tables['sentiment'].set_index('sentiment').reindex(LABELS)
    axs[1].bar(LABELS,t.reviews,color=COLORS);axs[1].set(title='Nhãn đại diện suy từ số sao',ylabel='review')
    for x,n in enumerate(t.reviews):axs[1].text(x,n+t.reviews.sum()/150,f'{n:,}\n{n/t.reviews.sum():.2%}',ha='center',fontsize=9)
    axs[1].set_ylim(0,max(t.reviews)*1.18);save(fig,'rating_proxy')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    t=tables['length_histogram'];axs[0].bar(t['bin'],t.reviews,color='#466f9f');axs[0].tick_params(axis='x',rotation=45)
    axs[0].set(title='Độ dài theo số từ; giữ phần đuôi dài',xlabel='từ',ylabel='review')
    t=tables['sentiment'].set_index('sentiment').reindex(LABELS)
    axs[1].bar(LABELS,t.median_words,color=COLORS);axs[1].set(title='Trung vị số từ theo nhãn đại diện',ylabel='từ');save(fig,'length')
    fig,axs=plt.subplots(1,2,figsize=(12,5))
    t=tables['brands'].sort_values('reviews',ascending=False).head(10).iloc[::-1]
    axs[0].barh(t.brand_normalized,t.reviews,color='#466f9f');axs[0].set(title='Các danh mục siêu dữ liệu hàng đầu theo số lượng review',xlabel='review')
    for label,color in zip(LABELS,COLORS):
        left=sum(t[x+'_share'] for x in LABELS[:LABELS.index(label)]) if label!=LABELS[0] else 0
        axs[1].barh(t.brand_normalized,t[label+'_share']*100,left=left*100,color=color,label=label)
    axs[1].set(title='Phân bố nhãn đại diện; mô tả, không xếp hạng thương hiệu',xlabel='Phần trăm',xlim=(0,100));axs[1].legend(loc='lower right');save(fig,'brands')
    t=tables['months'];fig,axs=plt.subplots(2,1,figsize=(11,6),sharex=True)
    axs[0].plot(range(len(t)),t.reviews,color='#466f9f');axs[0].set(ylabel='review',title='Phân bố mẫu đã chọn theo tháng (không phải doanh số)')
    supported=t.sufficient_support
    axs[1].plot(range(len(t)),t.negative_share.where(supported)*100,color=COLORS[0])
    axs[1].set(ylabel='Nhãn negative (%)',xlabel='tháng UTC; tỷ lệ chỉ hiển thị khi n >= 100')
    tick=range(0,len(t),max(1,len(t)//10));axs[1].set_xticks(list(tick),t.month.iloc[list(tick)],rotation=45);save(fig,'time')
    t=tables['themes'].pivot(index='theme',columns='sentiment',values='within_class_share').reindex(columns=LABELS)
    fig,ax=plt.subplots(figsize=(10,5));t.plot.bar(ax=ax,color=COLORS)
    theme_names = {'battery': 'Pin', 'build': 'Kết cấu', 'display': 'Màn hình',
        'keyboard': 'Bàn phím', 'performance': 'Hiệu năng', 'portability': 'Tính di động',
        'price': 'Giá', 'storage': 'Lưu trữ', 'thermals_noise': 'Nhiệt độ/tiếng ồn'}
    ax.set_xticklabels([theme_names.get(theme, theme) for theme in t.index])
    ax.set_xlabel('Chủ đề giả thuyết')
    ax.legend(title='Cảm xúc')
    ax.set(title='Tỷ lệ nhắc chủ đề theo từ điển giả thuyết và nhãn đại diện (không phải ABSA)',ylabel='Tỷ lệ review trong lớp');ax.tick_params(axis='x',rotation=35);save(fig,'themes')
    fig,axs=plt.subplots(1,3,figsize=(15,5))
    for ax,label,color in zip(axs,LABELS,COLORS):
        t=tables['lexical_by_class'];t=t[(t.sentiment==label)&(t.n==2)&(t.documents>=30)]
        t=t.sort_values(['prevalence_difference','documents','term'],ascending=[False,False,True]).head(10).iloc[::-1]
        ax.barh(t.term,t.prevalence_difference*100,color=color);ax.set(title=f'{label}: cặp từ liên tiếp',xlabel='Tỷ lệ trong lớp trừ tỷ lệ ngoài lớp (điểm %)')
    save(fig,'distinctive_bigrams')
    t=tables['verified'];fig,axs=plt.subplots(1,2,figsize=(10,4))
    axs[0].bar(t.verified_purchase.astype(str),t.reviews,color='#466f9f');axs[0].set(title='Trường mua hàng đã được xác minh',ylabel='review')
    axs[1].bar(t.verified_purchase.astype(str),t.negative_share*100,color=COLORS[0]);axs[1].set(title='Nhãn negative theo trạng thái xác minh mua hàng',ylabel='Phần trăm');save(fig,'verified_purchase')
    return paths


def analyze(output: Path) -> dict:
    output=output.resolve()
    if not output.is_relative_to((PROJECT_ROOT/'reports').resolve()):
        raise ValueError('Output must stay under reports')
    if output.exists():raise FileExistsError('Use a new output directory')
    source=PROJECT_ROOT/'data/processed/laptop_reviews.parquet'
    validation_path=PROJECT_ROOT/'reports/tables/p2_amazon_20261009_final/validation.json'
    validation=json.loads(validation_path.read_text(encoding='utf-8'))
    if sha256_file(source)!=validation['dataset_sha256']:raise ValueError('P2 bytes changed')
    protected=json.loads((PROJECT_ROOT/'reports/tables/p1_recall_brand_preservation.json').read_text(encoding='utf-8'))['files']
    # Chỉ ràng buộc tính toàn vẹn: không chạy lại bất kỳ cuộc kiểm tra P1/P2 schema/offset/filter nào.
    preserved={p:sha256_file(PROJECT_ROOT/p)==digest for p,digest in protected.items()}
    if not all(preserved.values()):raise ValueError('Protected input changed')
    d=pd.read_parquet(source)
    summary,tables=build_tables(d)
    noise=pd.read_csv(PROJECT_ROOT/'data/interim/p2/20261009_final/label_noise_candidates.csv',keep_default_na=False)
    safe_columns=[c for c in ['review_id','rating','sentiment','noise_candidate_reasons','text','annotation_status'] if c in noise]
    tables['noise_examples']=noise[safe_columns].head(12)
    output.mkdir(parents=True)
    for name,table in tables.items():table.to_csv(output/f'{name}.csv',index=False,encoding='utf-8',float_format='%.10g')
    figures=output/'figures';figures.mkdir();plot_paths=plot_tables(tables,figures)
    summary.update(source_sha256=validation['dataset_sha256'],seed=42,
                   lexical_min_document_support=30,brand_min_reviews=100,product_min_reviews=30,
                   time_min_reviews=100,stopwords=sorted(STOPWORDS),theme_patterns=THEMES,
                   table_files=[f'{name}.csv' for name in tables],figure_files=plot_paths,
                   protected_files=len(preserved),protected_integrity='PASS',
                   splits_created=False,models_trained=False,gold_labels_created=False,
                   license_status='OWNER_EXCEPTION_NOT_VERIFIED',
                   implementation_sha256={p:sha256_file(PROJECT_ROOT/p) for p in ['src/data/eda.py','scripts/analyze_p3.py']})
    summary['output_sha256']={str(p.relative_to(output)):sha256_file(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return summary


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path('reports/p3/20261009'))
    args=parser.parse_args()
    result=analyze(args.output_dir)
    print(json.dumps({k:result[k] for k in ['rows','products','time_min','time_max','protected_integrity']},indent=2))


if __name__=='__main__':main()
