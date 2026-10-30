# -*- coding: utf-8 -*-
"""Đổi giọng cho câu vẫn lỗi kỹ thuật sau khi buoc/tts.py đã sinh lại tối đa --max-retry lần (việc T4).

Chạy (từ tts_gen/):
  .venv/Scripts/python -m buoc.doi_giong runs/eval1000_A                  # chỉ ghi <run>/fallback_input.jsonl
  .venv/Scripts/python -m buoc.doi_giong runs/eval1000_A --run-tts        # ghi rồi chạy buoc/tts.py vào cùng thư mục
Chọn câu: dòng hiện hành (eval_common.active_rows) có tts_check khác "dat" và chưa từng đổi giọng (chỉ 1 vòng).
Chọn giọng mới: cùng vùng, cùng giới, khác giọng cũ; ưu tiên giọng không có câu bị cắt đầu trong lượt này, rồi giọng
đang có ít câu nhất trong phần, hòa thì theo băm. Miền Trung không có giọng cùng giới: lấy giọng còn lại, doi_gioi=true.
Dòng ghi ra giữ mọi trường của dòng gốc trong tệp đầu vào của lượt chạy, đổi voice/voice_* và thêm voice_fallback_from.
buoc/tts.py ghi thêm dòng mới vào manifest; dòng cũ (lỗi) vẫn giữ. Không ghi đè fallback_input.jsonl đã có.
"""
import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from thuvien.manifest import active_rows, load_jsonl, load_manifest  # noqa: E402
from cauhinh.giong import VOICES, VOICE_SUB_REGION  # noqa: E402

SEED = 20261020


def h(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()


def rows_to_fallback(manifest):
    """Dòng hiện hành còn lỗi kỹ thuật và chưa đổi giọng lần nào."""
    switched = {m["sample_id"] for m in manifest if m.get("voice_fallback_from")}
    return [m for m in active_rows(manifest) if m.get("tts_check", "dat") != "dat" and m["sample_id"] not in switched]


def pick_voice(old, sample_id, voices, counts, cut_flagged):
    """(giọng mới, doi_gioi) hoặc (None, None) nếu vùng không còn giọng nào khác."""
    reg, gen = voices[old][0], voices[old][1]
    cands = [v for v, m in voices.items() if m[0] == reg and m[1] == gen and v != old]
    doi_gioi = False
    if not cands:
        cands = [v for v, m in voices.items() if m[0] == reg and v != old]
        doi_gioi = True
    if not cands:
        return None, None
    return min(cands, key=lambda v: (v in cut_flagged, counts.get(v, 0), h(SEED, sample_id, v))), doi_gioi


def build(manifest, plan_rows, voices=VOICES):
    """Danh sách dòng đầu vào mới cho buoc/tts.py."""
    act = active_rows(manifest)
    counts = collections.Counter(m["voice"] for m in act)
    cut_flagged = {m["voice"] for m in act if "cat_dau" in m.get("tts_check", "")}
    plan = {r["sample_id"]: r for r in plan_rows}
    out = []
    for m in rows_to_fallback(manifest):
        new, doi_gioi = pick_voice(m["voice"], m["sample_id"], voices, counts, cut_flagged)
        if new is None:
            print(f"{m['sample_id']}: vùng {voices[m['voice']][0]} không còn giọng khác, bỏ qua")
            continue
        counts[new] += 1
        reg, gen, style, _ = voices[new]
        src = plan[m["sample_id"]]
        r = dict(src, voice=new, voice_fallback_from=m["voice"], doi_gioi=doi_gioi, voice_gender=gen,
                 voice_style=style, voice_region=reg, voice_sub_region=VOICE_SUB_REGION.get(new, ""))
        if reg == "Trung" and src.get("residence") == "Quê":
            r["giong_khop_tieu_vung"] = src.get("sub_region") == VOICE_SUB_REGION.get(new)
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--plan", default=None, help="tệp đầu vào của lượt chạy (mặc định: 'input' trong run_config.json)")
    ap.add_argument("--run-tts", action="store_true", help="chạy buoc/tts.py với tệp vừa ghi, cùng --out")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--pilot-args", default="", help="tham số thêm cho buoc/tts.py (vd \"--dtype float32 --backbone-repo ...\"), "
                    "phải trùng cấu hình của lượt chính")
    a = ap.parse_args()
    out_p = os.path.join(a.run, "fallback_input.jsonl")
    if os.path.exists(out_p) and os.path.getsize(out_p):
        raise SystemExit(f"{out_p} đã có (chỉ đổi giọng 1 vòng); xóa tay nếu thật sự muốn làm lại")
    plan_p = a.plan
    if not plan_p:
        with open(os.path.join(a.run, "run_config.json"), encoding="utf-8") as f:
            inp = json.load(f)["input"]
        plan_p = inp if os.path.isabs(inp) else os.path.join(HERE, inp)
    manifest = load_manifest(a.run)
    rows = build(manifest, load_jsonl(plan_p))
    with open(out_p, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} câu đổi giọng -> {out_p}")
    for r in rows:
        print(f"  {r['sample_id']}: {r['voice_fallback_from']} -> {r['voice']}{' (đổi giới)' if r['doi_gioi'] else ''}")
    if a.run_tts and rows:
        import shlex
        cmd = [sys.executable, "-m", "buoc.tts", "--input", out_p, "--out", a.run, "--batch", str(a.batch)]
        cmd += shlex.split(a.pilot_args)
        print("Chạy:", " ".join(cmd), flush=True)
        raise SystemExit(subprocess.call(cmd, cwd=HERE))


if __name__ == "__main__":
    main()
