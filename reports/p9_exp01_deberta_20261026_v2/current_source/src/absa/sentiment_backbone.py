"""Mã hóa occurrence P9 với tokenizer của backbone bổ sung, không đổi dữ liệu."""
from src.absa.sentiment_data import MARKERS,marked_input


def encode_record(row: dict,tokenizer,max_length: int=128) -> dict:
    """Giữ text/offsets/labels và marker logic P9; từ chối truncation ngầm."""
    marked=marked_input(row['text'],row['aspect'],row['start'],row['end'])
    if row.get('marked_text',marked)!=marked:
        raise ValueError('Representation không khớp P9 frozen')
    encoded=tokenizer(marked,truncation=False,return_token_type_ids=True)
    ids=encoded['input_ids']; markers=tokenizer.convert_tokens_to_ids(list(MARKERS))
    if (not ids or ids[0]!=tokenizer.cls_token_id or ids[-1]!=tokenizer.sep_token_id
            or len(ids)>max_length or any(ids.count(m)!=1 for m in markers)
            or ids.index(markers[0])>=ids.index(markers[1])):
        raise ValueError('DeBERTa length/marker alignment không hợp lệ; không truncate ngầm')
    return {**row,**encoded,'tokens':tokenizer.convert_ids_to_tokens(ids),'marker_ids':markers,'marked_text':marked}
