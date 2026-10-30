# -*- coding: utf-8 -*-
"""Đường dẫn gốc. Mã chạy bằng python -m <lớp>.<tên> từ gen10k/."""
import os

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # gen10k/
ROOT = os.path.dirname(GOC)                                         # thư mục dự án (data/, sources/)
