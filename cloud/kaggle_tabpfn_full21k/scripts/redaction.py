"""Ẩn thông tin xác thực trước khi lưu lỗi thí nghiệm."""

import os
import re


def safe_error(exc: Exception) -> str:
    """Loại giá trị token môi trường và URL khỏi thông báo lỗi."""
    message = str(exc)
    for key in ('TABPFN_TOKEN', 'HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN'):
        token = os.environ.get(key, '')
        if token:
            message = message.replace(token, '[REDACTED]')
    return re.sub(r'https?://\S+', '[URL]', message)
