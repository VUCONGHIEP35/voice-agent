# -*- coding: utf-8 -*-
"""Kiểm một lượt sinh so với tệp đầu vào (bản script của hàm check_run trong notebook Colab).

Chạy (từ tts_gen/):  python -m buoc.kiem_luot runs/eval1000_B eval1000_tts/shard_B.jsonl [--max-retry-rate 0.25]
Kiểm: đủ sample_id (theo eval_common.active_rows), không thừa, không trùng utt_id, đủ tệp audio48/audio16, tts_text được
dùng (tts_input == tts_text), tỷ lệ câu phải sinh lại, không có giọng bị loại (Minh Triết). In JSON kết quả.
Mã thoát: 0 đạt; 2 gặp điểm dừng (mất/trùng câu, thiếu tệp, tts_text không dùng, sinh lại quá ngưỡng).
"""
import argparse
import json
import os
from cauhinh.nguong import SINH_LAI_MAX  # noqa: E402

from thuvien.manifest import active_rows, load_jsonl, load_manifest  # noqa: E402

EXCLUDED = {"Minh Triết"}


def check(run, plan, max_retry_rate=SINH_LAI_MAX):
    man = load_manifest(run)
    act = active_rows(man)
    want = {r["sample_id"]: r for r in load_jsonl(plan)}
    utt = [m["utt_id"] for m in man]
    have = {m["sample_id"] for m in act}
    missing_files = [m["utt_id"] for m in man for k in ("audio48", "audio16")
                     if not os.path.exists(os.path.join(run, m[k]))]
    tts_bad = [m["sample_id"] for m in man if want.get(m["sample_id"], {}).get("tts_text")
               and m.get("tts_input") != want[m["sample_id"]]["tts_text"]]
    retried = len({m["sample_id"] for m in man if m.get("retries")})
    res = dict(dong_manifest=len(man), sample_id_duy_nhat=len(have), ke_hoach=len(want),
               thieu=sorted(set(want) - have)[:10], so_thieu=len(set(want) - have),
               thua=sorted(have - set(want))[:10], utt_id_trung=len(utt) - len(set(utt)),
               thieu_tep=missing_files[:10], tts_text_khong_dung=tts_bad[:10],
               co_sinh_lai=retried, ty_le_sinh_lai=round(retried / max(len(act), 1), 3),
               con_loi_ky_thuat=sum(m.get("tts_check", "dat") != "dat" for m in act),
               doi_giong=sum(bool(m.get("voice_fallback_from")) for m in act),
               giong_bi_loai=sorted({m["voice"] for m in man if m["voice"] in EXCLUDED}))
    stop = []
    if res["so_thieu"] or res["thua"] or res["utt_id_trung"] or res["thieu_tep"]:
        stop.append("mất hoặc trùng câu / thiếu tệp")
    if res["tts_text_khong_dung"]:
        stop.append("tts_text không được dùng")
    if res["ty_le_sinh_lai"] > max_retry_rate:
        stop.append(f"quá {max_retry_rate:.0%} số câu phải sinh lại")
    if res["giong_bi_loai"]:
        stop.append("có giọng bị loại")
    return res, stop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("plan")
    ap.add_argument("--max-retry-rate", type=float, default=SINH_LAI_MAX)
    a = ap.parse_args()
    res, stop = check(a.run, a.plan, a.max_retry_rate)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if stop:
        print("*** ĐIỂM DỪNG:", "; ".join(stop), "***")
        raise SystemExit(2)
    print("check_run: ĐẠT")


if __name__ == "__main__":
    main()
