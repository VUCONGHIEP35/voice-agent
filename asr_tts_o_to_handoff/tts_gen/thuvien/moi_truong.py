# -*- coding: utf-8 -*-
"""Đặt thư mục tạm và cache vào tts_gen/.cache/ (ổ D:) cho tiến trình hiện tại, trước khi import torch/huggingface.

Ổ C: chỉ còn vài GB; TEMP mặc định của Windows và cache của pip/torch/CUDA đều nằm trên C:. Hàm này chỉ đổi biến môi
trường của tiến trình đang chạy (và tiến trình con), không sửa biến môi trường của Windows.
Dùng:  import tts_env; tts_env.setup()   (đặt ở đầu script, trước khi import torch)
"""
import os
import tempfile

from cauhinh.duong_dan import CACHE
DIRS = {
    "TEMP": "tmp", "TMP": "tmp", "PIP_CACHE_DIR": "pip", "TORCH_HOME": "torch", "CUDA_CACHE_PATH": "cuda",
    "HF_HOME": "hf",
}


def setup(force=True):
    """Đặt các biến trong DIRS (force=True ghi đè cả TEMP/TMP của Windows). Trả {biến: đường dẫn}."""
    out = {}
    for var, sub in DIRS.items():
        path = os.path.join(CACHE, sub)
        os.makedirs(path, exist_ok=True)
        if force or not os.environ.get(var):
            os.environ[var] = path
        out[var] = os.environ[var]
    tempfile.tempdir = None          # để tempfile đọc lại TEMP/TMP mới
    return out
