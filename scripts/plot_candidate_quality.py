"""Sơ đồ chất lượng ứng viên đã được đo lường sẵn; không có lựa chọn hoặc lọc bộ dữ liệu mới."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Use a new figure directory')
    result=json.loads(args.audit.read_text(encoding='utf-8'))
    args.output_dir.mkdir(parents=True)
    n=result['rows']
    labels=['negative','neutral','positive']
    counts=[result['rating_proxy_class_counts'].get(label,0) for label in labels]
    fig,ax=plt.subplots(figsize=(7,4.5))
    bars=ax.bar(labels,counts,color=['#b44949','#858585','#37806b'])
    for bar,count in zip(bars,counts):
        ax.text(bar.get_x()+bar.get_width()/2,count+n*.013,f'{count:,}\n{count/n:.2%}',ha='center',fontsize=10)
    ax.set_ylim(0,max(counts)*1.2)
    ax.set_ylabel('Số review ứng viên')
    ax.set_title('Nhãn suy từ số sao; chưa phải nhãn cảm xúc gold thủ công')
    fig.tight_layout();fig.savefig(args.output_dir/'proxy_class_balance.png',dpi=150);plt.close(fig)
    hist={int(k):v for k,v in result['word_length_distribution'].items()}
    edges=[0,5,10,25,50,100,200,500,1000,float('inf')]
    bins=[sum(v for k,v in hist.items() if low<=k<high) for low,high in zip(edges,edges[1:])]
    names=['0–4','5–9','10–24','25–49','50–99','100–199','200–499','500–999','1000+']
    fig,ax=plt.subplots(figsize=(9,4.5));ax.bar(names,bins,color='#466f9f')
    ax.set_ylabel('Số review ứng viên');ax.set_xlabel('Số từ tách bằng khoảng trắng sau giải mã HTML')
    ax.set_title(f'Độ dài review; trung vị {result["word_length_quantiles"]["p50"]} từ')
    fig.tight_layout();fig.savefig(args.output_dir/'review_length.png',dpi=150);plt.close(fig)
    names=['Trùng hoàn toàn ở dữ liệu thô','Trùng sau chuẩn hóa','Ngắn (<5 từ)','Trùng ID/văn bản QA']
    values=[result['raw_exact_duplicates']['duplicate_excess_rows'],
            result['normalized_duplicates']['duplicate_excess_rows'],
            result['flags']['short_under_5_words'],result['flags']['qa_id_or_text_rows']]
    fig,ax=plt.subplots(figsize=(9,4.5));bars=ax.barh(names,[v/n*100 for v in values],color='#99764d')
    for bar,value in zip(bars,values):
        ax.text(bar.get_width()+.15,bar.get_y()+bar.get_height()/2,f'{value:,} ({value/n:.2%})',va='center')
    ax.set_xlim(0,max(values)/n*100+5)
    ax.set_xlabel(f'Tỷ lệ trong {n:,} mẫu ứng viên đã lưu (%)')
    ax.set_title('Các cờ có thể giao nhau; cờ trùng đếm số hàng dư')
    fig.tight_layout();fig.savefig(args.output_dir/'quality_flags.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    main()
