# -*- coding: utf-8 -*-
"""Đường dẫn gốc của tts_gen/ (mọi đường dẫn dữ liệu tính từ đây)."""
import os

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tts_gen/
CACHE = os.path.join(GOC, ".cache")
LEXICON_CHAM = os.path.join(GOC, "lexicon", "asr_bien_the.tsv")
LEXICON_DOC_TTS = os.path.join(GOC, "lexicon", "doc_tu_ngoai_tts.tsv")
