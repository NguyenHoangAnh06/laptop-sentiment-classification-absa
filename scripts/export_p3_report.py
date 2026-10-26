"""Gộp kết quả P3 đã lưu thành một báo cáo HTML độc lập, không phân tích lại dữ liệu."""

import argparse
import base64
import csv
import hashlib
import html
import json
import io
import os
from pathlib import Path
import re
import tempfile

from src.config import PROJECT_ROOT
from scripts.p3_report_content import COLUMNS, GLOSSARY, TERMS, VALUES, interpretations


TABLES = {
    'rating': 'Phân bố số sao', 'sentiment': 'Phân bố nhãn cảm xúc đại diện',
    'length_by_sentiment': 'Độ dài theo cảm xúc và số sao',
    'length_histogram': 'Phân bố độ dài', 'missing': 'Dữ liệu thiếu và chất lượng trường',
    'frequent_terms': 'Tần suất từ và cụm từ liên tiếp (n-gram)', 'lexical_by_class': 'Từ vựng theo lớp cảm xúc',
    'brands': 'Thương hiệu từ siêu dữ liệu', 'products': 'Phân tích theo sản phẩm',
    'months': 'Phân tích theo tháng', 'years': 'Phân tích theo năm',
    'verified': 'Giao dịch mua đã xác minh', 'themes': 'Chủ đề theo từ điển giả thuyết',
    'theme_contexts': 'Ngữ cảnh nhắc chủ đề', 'noise_examples': 'Ví dụ chẩn đoán nghi nhiễu nhãn',
}
FIGURES = {
    'rating_proxy': 'Số sao và nhãn cảm xúc suy từ số sao',
    'length': 'Độ dài bài đánh giá và khác biệt giữa các lớp',
    'distinctive_bigrams': 'Các cặp từ đặc trưng theo lớp',
    'brands': 'Phân bố thương hiệu và thành phần nhãn',
    'time': 'Phân bố theo thời gian',
    'verified_purchase': 'Giao dịch mua đã xác minh',
    'themes': 'Tỷ lệ nhắc các chủ đề giả thuyết',
}


def inline(text: str) -> str:
    """Hiển thị văn xuôi Markdown an toàn, không tạo phụ thuộc tệp ngoài."""
    parts = re.split(r'(`[^`]+`)', text)
    result = []
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            result.append('<code>' + html.escape(part[1:-1]) + '</code>')
        else:
            value = html.escape(part)
            value = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (<code>\2</code>)', value)
            value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
            result.append(value)
    return ''.join(result)


def count_label(value: int) -> str:
    """Định dạng số lượng theo quy ước tiếng Việt."""
    return f'{value:,}'.replace(',', '.')


def markdown(text: str) -> str:
    """Dựng các thành phần dùng trong báo cáo P3, giữ đủ văn bản nguồn."""
    lines = text.splitlines()
    output = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith('```'):
            block = []
            index += 1
            while index < len(lines) and not lines[index].startswith('```'):
                block.append(lines[index])
                index += 1
            output.append('<pre><code>' + html.escape('\n'.join(block)) + '</code></pre>')
        elif line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].startswith('|'):
                cells = lines[index].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', cell) for cell in cells):
                    tag = 'th' if not rows else 'td'
                    rows.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
                index += 1
            output.append('<div class="scroll"><table>' + ''.join(rows) + '</table></div>')
            continue
        elif re.match(r'^#{1,6} ', line):
            level = min(len(line) - len(line.lstrip('#')) + 1, 6)
            output.append(f'<h{level}>' + inline(line.lstrip('# ')) + f'</h{level}>')
        elif re.match(r'^[-*] ', line):
            items = []
            while index < len(lines) and re.match(r'^[-*] ', lines[index]):
                item = lines[index][2:]
                index += 1
                while index < len(lines) and lines[index].startswith('  '):
                    item += ' ' + lines[index].strip()
                    index += 1
                items.append('<li>' + inline(item) + '</li>')
            output.append('<ul>' + ''.join(items) + '</ul>')
            continue
        else:
            block = [line]
            index += 1
            while index < len(lines) and lines[index].strip() and not re.match(r'^(?:#|\||```|[-*] )', lines[index]):
                block.append(lines[index])
                index += 1
            output.append('<p>' + inline(' '.join(block)) + '</p>')
            continue
        index += 1
    return '\n'.join(output)


CSS = """
:root{color-scheme:light;--ink:#183029;--muted:#52635d;--accent:#12644d}
*{box-sizing:border-box}body{margin:0;background:#f3f5f1;color:var(--ink);font:16px/1.65 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:36px 24px 80px}header{padding:32px;background:#173e33;color:white;border-radius:16px}
h1{font-size:clamp(26px,4vw,40px);line-height:1.2;margin:12px 0}h2{margin-top:0;font-size:26px}h3{line-height:1.35}
header p{max-width:850px;color:#dfebe3}.eyebrow{letter-spacing:.12em;font-size:12px;font-weight:700}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}nav a,button{background:white;border:1px solid #c5d1ca;border-radius:8px;padding:8px 13px;color:var(--accent);text-decoration:none;cursor:pointer}
section{background:white;border:1px solid #dce2da;border-radius:14px;margin:24px 0;padding:26px;scroll-margin-top:20px}
.note{background:#f6f1de;border-left:4px solid #ae8236;padding:15px 18px;margin:18px 0}.small{font-size:13px;color:var(--muted)}
.interpretation{padding:16px 20px;background:#eef5ef;border-left:4px solid #287258;line-height:1.8;margin:16px 0;word-spacing:.04em}.interpretation strong{display:block;margin-bottom:5px}.column-key{display:block;font-size:11px;color:#52635d;font-weight:400;white-space:normal}th{min-width:145px;max-width:270px;white-space:normal!important}.glossary{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px 24px}.glossary dt{font-weight:700}.glossary dd{margin:0 0 12px;line-height:1.7}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}.stat{background:#ffffff15;padding:12px;border-radius:8px}.stat strong{display:block;font-size:25px}
figure{margin:24px 0 38px}img{display:block;max-width:100%;height:auto;border:1px solid #e5e7e1}figcaption{font-weight:650;margin:10px 0}
details{border-top:1px solid #dce2da;padding:16px 0}summary{cursor:pointer;font-size:18px;font-weight:650}.scroll{overflow:auto;max-height:600px;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.45}th,td{padding:9px 12px;border-bottom:1px solid #e0e6df;text-align:left;vertical-align:top}th{background:#edf3ed;position:sticky;top:0;white-space:nowrap}td{max-width:440px;min-width:90px;overflow-wrap:anywhere}tr:nth-child(even){background:#fafbf8}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:14px 0}.toolbar input{flex:1;min-width:200px;padding:10px;border:1px solid #c5d1ca;border-radius:6px}
button:disabled{opacity:.45;cursor:default}code{font-size:.86em;background:#eef2ec;padding:2px 4px;border-radius:3px;overflow-wrap:anywhere}pre{overflow:auto;background:#eef2ec;padding:18px;max-height:650px}pre code{padding:0}a{color:var(--accent)}
@media(max-width:650px){main{padding:16px 10px}.stats{grid-template-columns:repeat(2,1fr)}section,header{padding:18px}}
@media print{body{background:white}main{padding:0}section{break-before:page;border:0}nav,.toolbar{display:none}img{max-height:80vh;object-fit:contain}.scroll{max-height:none;overflow:visible}}
"""

JS = r"""
'use strict';
const tables=JSON.parse(document.getElementById('table-data').textContent);
const display=JSON.parse(document.getElementById('display-data').textContent);
const decimal=new Intl.NumberFormat('vi-VN',{maximumFractionDigits:4});
const percent=new Intl.NumberFormat('vi-VN',{style:'percent',maximumFractionDigits:2});
function displayValue(value,column){
 if(column==='verified_purchase')return value==='True'?'True (đã xác minh)':value==='False'?'False (chưa xác minh)':value;
 if(column==='sufficient_support')return value==='True'?'True (đạt ngưỡng)':value==='False'?'False (chưa đạt ngưỡng)':value;
 const meaning=display.values[value]||(column==='term'?display.terms[value]:null)||(column==='field'?display.columns[value]:null);
 if(meaning)return `${value} (${meaning})`;
 if(column==='noise_candidate_reasons'){
  try{return JSON.parse(value).map(v=>`${v} (${display.values[v]||'dấu hiệu cần kiểm tra'})`).join('; ')}catch{}
 }
 if(!['review_id','parent_asin','brand_normalized','term','text','snippet','month','year','bin'].includes(column)&&value.trim()!==''&&Number.isFinite(Number(value))){
  const number=Number(value);
  return column.endsWith('_share')||['share','prevalence','rest_prevalence','negative_ci_low','negative_ci_high','prevalence_difference'].includes(column)?percent.format(number):decimal.format(number);
 }
 return value;
}
for(const data of tables){
 const host=document.getElementById('table-'+data.name);let page=0,filter='',indices=null;
 const input=host.querySelector('input'),body=host.querySelector('tbody'),status=host.querySelector('.status');
 const previous=host.querySelector('.previous'),next=host.querySelector('.next');const size=50;
 function render(){
  const length=indices===null?data.rows.length:indices.length;
  page=Math.max(0,Math.min(page,Math.max(0,Math.ceil(length/size)-1)));body.replaceChildren();
  for(let j=page*size;j<Math.min((page+1)*size,length);j++){
   const row=data.rows[indices===null?j:indices[j]],tr=document.createElement('tr');
   for(let k=0;k<row.length;k++){const value=row[k],td=document.createElement('td');td.textContent=displayValue(value,data.columns[k]);td.title='Giá trị gốc: '+value;tr.append(td);}body.append(tr);
  }
  status.textContent=length===0?'Không có dòng phù hợp':`${page*size+1}–${Math.min((page+1)*size,length)} / ${length.toLocaleString('vi-VN')} dòng`;
  previous.disabled=page===0;next.disabled=(page+1)*size>=length;
 }
 input.addEventListener('input',()=>{filter=input.value.toLocaleLowerCase('vi');page=0;indices=filter?data.rows.map((r,i)=>r.some(v=>v.toLocaleLowerCase('vi').includes(filter)||(display.values[v]||display.terms[v]||display.columns[v]||'').toLocaleLowerCase('vi').includes(filter))?i:-1).filter(i=>i>=0):null;render();});
 previous.addEventListener('click',()=>{page--;render()});next.addEventListener('click',()=>{page++;render()});
 host.querySelector('.download').addEventListener('click',()=>{
  const quote=v=>'"'+v.replace(/"/g,'""')+'"';
  const csv='\uFEFF'+[data.columns,...data.rows].map(r=>r.map(quote).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=data.name+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });render();
}
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>document.querySelectorAll('#tables details').forEach(d=>d.open=b.dataset.open==='true')));
"""


def export_report(output: Path, root: Path = PROJECT_ROOT, *, replace: bool = False) -> dict:
    """Nhúng dữ liệu gốc và bản trình bày tiếng Việt; chỉ thay HTML khi yêu cầu rõ."""
    if output.suffix.lower() != '.html':
        raise ValueError('Đầu ra phải là tệp HTML.')
    if output.exists() and not replace:
        raise FileExistsError('Tệp tổng hợp đã tồn tại; dùng đường dẫn mới.')
    source = root / 'reports/p3/20261009_verified'
    actual = {p.stem for p in source.glob('*.csv')}
    if actual != set(TABLES):
        raise ValueError(f'Danh sách bảng khác dự kiến: {actual ^ set(TABLES)}')
    before = {}
    def read(path: Path) -> bytes:
        raw = path.read_bytes()
        before[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
        return raw
    summary = json.loads(read(source / 'summary.json'))
    tables = []
    table_dicts = {}
    for name in TABLES:
        records = list(csv.reader(io.StringIO(read(source / f'{name}.csv').decode('utf-8-sig'), newline='')))
        columns, rows = records[0], records[1:]
        if any(len(row) != len(columns) for row in rows):
            raise ValueError(f'Số cột không hợp lệ: {name}')
        if set(columns) - COLUMNS.keys():
            raise ValueError(f'Thiếu chú giải cột: {set(columns) - COLUMNS.keys()}')
        tables.append({'name': name, 'columns': columns, 'rows': rows})
        table_dicts[name] = [dict(zip(columns, row)) for row in rows]
    table_notes, figure_notes = interpretations(table_dicts, summary)
    # Dựng lại phần trình bày từ CSV; không đọc dữ liệu thô hoặc chạy lại EDA.
    import pandas as pd
    from scripts.analyze_p3 import plot_tables
    with tempfile.TemporaryDirectory(prefix='p3_vietnamese_figures_') as temporary:
        folder = Path(temporary)
        plot_tables({name: pd.read_csv(source / f'{name}.csv') for name in TABLES}, folder, explain_terms=True)
        images = {name: (folder / f'{name}.png').read_bytes() for name in FIGURES}
    parts = ['<!doctype html><html lang="vi"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>P3 — Tổng hợp EDA dữ liệu laptop</title><style>' + CSS + '</style><main>',
        '<header><span class="eyebrow">P3 · PHÂN TÍCH KHÁM PHÁ DỮ LIỆU</span>',
        '<h1>Toàn bộ bảng, biểu đồ và nhận định về dữ liệu laptop</h1>',
        '<p>Kết quả P3 ngày 2026-10-09; trình bày và diễn giải cập nhật ngày 2026-10-20. Mở bằng trình duyệt, không cần mạng hoặc tệp đi kèm.</p>',
        f'<div class="stats"><div class="stat"><strong>{count_label(summary["rows"])}</strong>bài đánh giá laptop</div>',
        f'<div class="stat"><strong>{count_label(summary["products"])}</strong>sản phẩm</div>',
        '<div class="stat"><strong>15</strong>bảng đầy đủ</div><div class="stat"><strong>7</strong>biểu đồ</div></div></header>',
        '<nav><a href="#insights">Tóm tắt nhận định</a><a href="#glossary">Giải thích thuật ngữ</a><a href="#figures">7 biểu đồ</a><a href="#tables">15 bảng</a><a href="#analysis">Phân tích đầy đủ</a><a href="#provenance">Nguồn và toàn vẹn</a></nav>',
        '<div class="note">Nhãn cảm xúc suy từ số sao, không phải nhãn chuẩn con người. Chủ đề từ điển là giả thuyết khám phá, chưa phải kết quả ABSA. Các trạng thái “P4 chưa bắt đầu” trong tài liệu gốc phản ánh thời điểm P3, không phải trạng thái dự án hiện nay.</div>']
    for target, title, path in [
        ('insights', 'Tóm tắt nhận định từ dữ liệu', root / 'reports/p3_insight_summary_20261009.md'),
        ('analysis', 'Báo cáo phân tích đầy đủ P3', root / 'reports/p3_data_analysis_20261009.md'),
    ]:
        text = read(path).decode('utf-8-sig')
        section = f'<section id="{target}"><h2>{title}</h2>' + markdown(text)
        section += '<details><summary>Xem nguyên văn Markdown</summary><pre>' + html.escape(text) + '</pre></details></section>'
        if target == 'insights':
            parts.append(section)
        else:
            analysis = section
    parts.append('<section id="glossary"><h2>Giải thích thuật ngữ</h2><dl class="glossary">' + ''.join(f'<div><dt>{html.escape(term)}</dt><dd>({html.escape(meaning)})</dd></div>' for term, meaning in GLOSSARY) + '</dl><p>Bảng hiển thị số theo quy ước tiếng Việt: dấu chấm tách hàng nghìn, dấu phẩy tách thập phân. Tỷ lệ được đổi sang % để dễ đọc; chênh lệch tỷ lệ dùng điểm phần trăm. Di chuột lên ô để xem giá trị gốc; tải CSV vẫn giữ giá trị gốc.</p><p>Văn bản đánh giá, trích đoạn và từ vựng tiếng Anh là dữ liệu gốc. Chú giải được thêm cho các cụm thông dụng; không tự dịch hoặc thay thế toàn bộ dữ liệu nghiên cứu.</p></section>')
    parts.append('<section id="figures"><h2>Toàn bộ 7 biểu đồ P3</h2><p class="small">Dựng bản trình bày tiếng Việt có chú giải từ các bảng P3 đã lưu; không thay số liệu hoặc hình gốc trong thư mục đã xác minh.</p>')
    for number, (name, title) in enumerate(FIGURES.items(), 1):
        read(source / f'figures/{name}.png')
        raw = images[name]
        parts.append(f'<figure><figcaption>Hình {number}. {title}</figcaption><img alt="{html.escape(title)}" src="data:image/png;base64,{base64.b64encode(raw).decode()}"><div class="interpretation" data-analysis="figure-{name}"><strong>Nhận xét từ biểu đồ</strong>{html.escape(figure_notes[name])}</div><p class="small">Số liệu: các bảng P3 đã xác minh; bản tham chiếu lịch sử: figures/{name}.png</p></figure>')
    parts.append('</section><section id="tables"><h2>Toàn bộ 15 bảng phân tích</h2><p>Mỗi bảng chứa đủ các hàng gốc, hiển thị 50 hàng mỗi trang để mở nhanh. Tên cột có nghĩa tiếng Việt và mã gốc trong ngoặc. Tìm kiếm áp dụng trên toàn bộ bảng; nút tải CSV xuất toàn bộ dữ liệu gốc, kể cả khi đang lọc. Số trên màn hình được định dạng và làm tròn để dễ đọc; dữ liệu tải về giữ đầy đủ độ chính xác.</p><div class="toolbar"><button data-open="true">Mở tất cả bảng</button><button data-open="false">Thu gọn tất cả</button></div><noscript>Cần bật JavaScript để xem và tìm kiếm các bảng đầy đủ được nhúng trong tệp này.</noscript>')
    for number, data in enumerate(tables, 1):
        name, columns, rows = data['name'], data['columns'], data['rows']
        title = TABLES[name]
        parts.append(f'<details id="table-{name}" {"open" if number <= 2 else ""}><summary>{number}. {title} — {count_label(len(rows))} hàng</summary><p class="small">Nguồn: {name}.csv · {len(columns)} cột</p><div class="toolbar"><input aria-label="Tìm trong bảng {html.escape(title)}" placeholder="Tìm bằng tiếng Việt hoặc từ gốc…"><button class="previous">← Trước</button><span class="status"></span><button class="next">Sau →</button><button class="download">Tải toàn bộ CSV gốc</button></div><div class="scroll"><table><thead><tr>' + ''.join('<th>' + html.escape(COLUMNS[col]) + '<span class="column-key">(' + html.escape(col) + ')</span></th>' for col in columns) + '</tr></thead><tbody></tbody></table></div><div class="interpretation" data-analysis="table-' + name + '"><strong>Nhận xét từ bảng</strong>' + html.escape(table_notes[name]) + '</div></details>')
    parts.append('</section>' + analysis)
    parts.append('<section id="provenance"><h2>Nguồn, phương pháp và giới hạn</h2><p>Đọc các kết quả đã xác minh trong reports/p3/20261009_verified và hai báo cáo P3; không chạy lại EDA, làm sạch, gán nhãn hoặc huấn luyện. Không thay bảng hay hình nguồn. Nhúng đủ mọi hàng của 15 CSV và 7 biểu đồ dựng lại chỉ phần trình bày tiếng Việt từ các bảng đó. Bản kê dưới đây ghi hàm băm của nguồn tham chiếu, gồm cả hình gốc.</p><p><strong>Giới hạn:</strong> kết luận chỉ cho laptop; nhiễu nhãn suy từ số sao; khác biệt nền tảng/phong cách SemEval–Amazon trong cùng phạm vi laptop; bộ kiểm thử chuẩn thủ công dự kiến nhỏ, hiện chưa có. Không suy quan hệ nhân quả, chất lượng thương hiệu hoặc nhãn cảm xúc khía cạnh từ tần suất từ.</p><details><summary>Toàn bộ thống kê nguồn (summary.json)</summary><pre>' + html.escape(json.dumps(summary, ensure_ascii=False, indent=2)) + '</pre></details><details><summary>SHA256 (hàm băm kiểm tra toàn vẹn) các nguồn tham chiếu</summary><pre>' + html.escape(json.dumps(before, ensure_ascii=False, indent=2)) + '</pre></details></section></main>')
    payload = json.dumps(tables, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    display = json.dumps({'columns': COLUMNS, 'values': VALUES, 'terms': TERMS}, ensure_ascii=False).replace('<', '\\u003c')
    parts.append('<script type="application/json" id="table-data">' + payload + '</script><script type="application/json" id="display-data">' + display + '</script><script>' + JS + '</script></html>')
    for relative, digest in before.items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Nguồn thay đổi khi xuất: {relative}')
    output.parent.mkdir(parents=True, exist_ok=True)
    if replace:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent, suffix='.tmp', delete=False) as handle:
            handle.write('\n'.join(parts))
            temporary_output = Path(handle.name)
        try:
            os.replace(temporary_output, output)
        finally:
            temporary_output.unlink(missing_ok=True)
    else:
        with output.open('x', encoding='utf-8') as handle:
            handle.write('\n'.join(parts))
    return {'output': str(output), 'tables': len(tables), 'table_rows': sum(len(t['rows']) for t in tables),
        'figures': len(FIGURES), 'interpretations': len(table_notes) + len(figure_notes),
        'sources_unchanged': len(before), 'bytes': output.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=PROJECT_ROOT / 'reports/p3/P3_tong_hop_20261019.html', help='Tệp HTML mới, không ghi đè tệp đã có.')
    parser.add_argument('--replace', action='store_true', help='Chủ động cập nhật tệp HTML đã có; không sửa bảng/hình nguồn.')
    args = parser.parse_args()
    print(json.dumps(export_report(args.output.resolve(), replace=args.replace), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
