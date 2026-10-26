"""Ngoại tuyến đã huấn luyện trước BERT bộ tách token; không có trọng lượng, bộ chuyển đổi mô hình hoặc tinh chỉnh."""

from pathlib import Path
import os

import numpy as np
import pandas as pd
from tokenizers import Tokenizer

from src.preprocessing.english import extract_review_text


def choose_max_length(train_lengths: list[int], *, quantile: float = .95,
                      candidates: tuple[int,...] = (128,256,384,512)) -> tuple[int,dict]:
    """Độ dài cố định từ các quan sát chỉ huấn luyện, được giới hạn bởi bối cảnh BERT512."""
    if not train_lengths or any(n<2 for n in train_lengths):
        raise ValueError('Nonempty special-token-inclusive training lengths required')
    if not 0<quantile<=1 or not candidates or sorted(set(candidates))!=list(candidates) or candidates[-1]>512:
        raise ValueError('Invalid BERT length policy')
    observed=float(np.quantile(train_lengths,quantile))
    chosen=next((n for n in candidates if n>=observed),candidates[-1])
    return chosen,{'selection_split':'train','quantile':quantile,'observed_quantile':observed,
                   'p50':float(np.quantile(train_lengths,.5)),
                   'p90':float(np.quantile(train_lengths,.9)),
                   'p95':float(np.quantile(train_lengths,.95)),
                   'p99':float(np.quantile(train_lengths,.99)),
                   'max_observed':max(train_lengths),'max_length':chosen,
                   'train_truncation_share':sum(n>chosen for n in train_lengths)/len(train_lengths),
                   'includes_cls_sep':True,'candidates':list(candidates)}


class BertPreprocessor:
    """Chuẩn hóa tối thiểu theo sau là cố định đã huấn luyện trước WordPiece."""

    def __init__(self, tokenizer_path: Path, max_length: int | None = None) -> None:
        # Tránh phân bổ riêng cho mỗi nhân viên không giới hạn trên các máy chủ Windows lớn.
        os.environ['TOKENIZERS_PARALLELISM']='false'
        self.tokenizer=Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.max_length=max_length
        if max_length is not None:
            if not 2<=max_length<=512:
                raise ValueError('BERT length must be2–512')
            self.tokenizer.enable_truncation(max_length=max_length,direction='right',strategy='longest_first')
        for token in ('[CLS]','[SEP]','[PAD]','[UNK]'):
            if self.tokenizer.token_to_id(token) is None:
                raise ValueError('Not a complete BERT tokenizer')

    def lengths(self, frame: pd.DataFrame) -> list[int]:
        """Đo độ dài không bị cắt bằng bản sao cố định-bộ tách token riêng biệt."""
        clone=Tokenizer.from_str(self.tokenizer.to_str())
        clone.no_truncation();clone.no_padding()
        texts=extract_review_text(frame)
        return [len(clone.encode(text,add_special_tokens=True).ids) for text in texts]

    def encode(self, frame: pd.DataFrame, *, padding: bool = False) -> list[dict]:
        """Chỉ trả về các trường đặc trưng; Phần đệm lô động có sẵn cho suy luận."""
        if self.max_length is None:
            raise ValueError('Freeze max length from train before encoding')
        clone=Tokenizer.from_str(self.tokenizer.to_str())
        if padding:
            clone.enable_padding(pad_id=clone.token_to_id('[PAD]'),pad_token='[PAD]',pad_type_id=0)
        else:
            clone.no_padding()
        return [{'input_ids':e.ids,'attention_mask':e.attention_mask,'token_type_ids':e.type_ids}
                for e in clone.encode_batch(extract_review_text(frame),add_special_tokens=True)]
