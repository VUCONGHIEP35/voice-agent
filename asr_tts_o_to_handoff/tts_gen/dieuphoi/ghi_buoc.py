# -*- coding: utf-8 -*-
"""Tiện ích nhỏ cho chay_eval.sbatch (không cần GPU, chỉ thư viện chuẩn).

  python ghi_buoc.py ghi <run> <bước> <giây> <rc>     ghi thời gian: run_config.json["server_steps"] (nếu có run_config)
                                                      và logs/thoi_gian_asr.json (cộng dồn theo bước, như Colab)
  python ghi_buoc.py asr_xong <run> <tag>             thoát 0 nếu asr_<tag>.jsonl có đủ mọi utt_id của manifest
  python ghi_buoc.py diag_xong <run>                  thoát 0 nếu asr_diagnose.csv có cột hyp_c3 cho đủ utt_id
"""
import csv
import json
import os
import sys
import time


def utt_ids(run):
    with open(os.path.join(run, "manifest.jsonl"), encoding="utf-8") as f:
        return {json.loads(l)["utt_id"] for l in f if l.strip()}


def ghi(run, step, secs, rc):
    secs, rc = round(float(secs), 1), int(rc)
    cp = os.path.join(run, "run_config.json")
    if os.path.exists(cp):
        cfg = json.load(open(cp, encoding="utf-8"))
        cfg.setdefault("server_steps", []).append(dict(buoc=step, giay=secs, rc=rc, luc=time.strftime("%Y-%m-%d %H:%M:%S"),
                                                       may=os.uname().nodename, job=os.environ.get("SLURM_JOB_ID")))
        tmp = cp + ".tmp"
        json.dump(cfg, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, cp)
    if step.startswith(("asr_", "gate", "report")):
        tp = os.path.join(run, "logs", "thoi_gian_asr.json")
        os.makedirs(os.path.dirname(tp), exist_ok=True)
        t = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
        t[step] = round(t.get(step, 0) + secs, 1)
        json.dump(t, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def asr_xong(run, tag):
    p = os.path.join(run, f"asr_{tag}.jsonl")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-8") as f:
        have = {json.loads(l)["utt_id"] for l in f if l.strip()}
    return utt_ids(run) <= have


def diag_xong(run):
    p = os.path.join(run, "asr_diagnose.csv")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return bool(rows) and "hyp_c3" in rows[0] and utt_ids(run) <= {r["utt_id"] for r in rows}


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "ghi":
        ghi(*args)
    elif cmd == "asr_xong":
        raise SystemExit(0 if asr_xong(*args) else 1)
    elif cmd == "diag_xong":
        raise SystemExit(0 if diag_xong(*args) else 1)
    else:
        raise SystemExit(f"lệnh lạ: {cmd}")


if __name__ == "__main__":
    main()
