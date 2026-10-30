# -*- coding: utf-8 -*-
"""Kiểm kỹ thuật một câu TTS để quyết định sinh lại (dùng chung cho run_pilot.py và asr_check.py).

Chỉ đo, không sửa âm thanh. Các ngưỡng là mốc ban đầu, chốt lại sau khi nghe:
  cat_dau      5 ms đầu đã ở mức tiếng nói (> −40 dBFS): âm thanh bắt đầu giữa âm vị, TTS cắt mất đầu câu
               (cùng cách tính với dau_bi_cat trong asr_diagnose.py)
  noi_lan_man  thời lượng có tiếng / số âm tiết > 0,6 s (như SEC_PER_SYL_MAX trong report_pilot.py)
  doc_thieu    thời lượng có tiếng / số âm tiết < 0,12 s (nhanh hơn ~8 âm tiết/giây; pilot100 nhanh nhất 6,3)
"""
import numpy as np

from cauhinh.nguong import HEAD_DB_MAX, HEAD_MS, SEC_PER_SYL_MAX, SEC_PER_SYL_MIN  # noqa: F401



def head_db(w, sr=16000):
    """Mức RMS (dBFS) của HEAD_MS đầu tiên."""
    head = np.asarray(w[: int(sr * HEAD_MS / 1000)], dtype=np.float64)
    return float(20 * np.log10(np.sqrt(np.mean(head ** 2)) + 1e-9)) if len(head) else -200.0


def check(w, n_syl, speech_s, sr=16000):
    """Trả (lý do, head_db); danh sách lý do rỗng là đạt. speech_s: giây có tiếng (measure() trong run_pilot.py)."""
    hd = head_db(w, sr)
    why = []
    if hd > HEAD_DB_MAX:
        why.append("cat_dau")
    if n_syl and speech_s is not None:
        sps = speech_s / n_syl
        if sps > SEC_PER_SYL_MAX:
            why.append("noi_lan_man")
        elif sps < SEC_PER_SYL_MIN:
            why.append("doc_thieu")
    return why, round(hd, 1)
