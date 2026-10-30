# -*- coding: utf-8 -*-
"""Hàm dùng chung cho đánh giá 1.000 câu (make_fallback.py, gate_union.py, report_eval.py).

active_rows(manifest): một dòng cho mỗi sample_id. Manifest có thể có nhiều dòng cùng sample_id (đổi giọng bằng
make_fallback.py ghi thêm dòng mới). Lấy dòng CUỐI có tts_check == "dat"; nếu không có dòng nào đạt thì lấy dòng cuối.
"""
import json
import math
import os


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_manifest(run):
    return load_jsonl(os.path.join(run, "manifest.jsonl"))


def active_rows(manifest):
    """[dòng] theo thứ tự xuất hiện đầu tiên của sample_id; mỗi sample_id lấy dòng cuối đạt, không có thì dòng cuối."""
    last, last_ok, order = {}, {}, []
    for m in manifest:
        sid = m["sample_id"]
        if sid not in last:
            order.append(sid)
        last[sid] = m
        if m.get("tts_check", "dat") == "dat":
            last_ok[sid] = m
    return [last_ok.get(s, last[s]) for s in order]


def wilson(k, n, z=1.96):
    """Khoảng tin cậy Wilson 95 % cho tỷ lệ k/n. Trả (thấp, cao); n = 0 thì (0, 1)."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - r) / d), min(1.0, (c + r) / d)
