# -*- coding: utf-8 -*-
"""Dựng lại audio16/ từ audio48/ cho một lượt chạy (gói kết quả chỉ mang audio48 để nhẹ).

Chạy (từ tts_gen/):  python -m buoc.dung_audio16 runs/ket_qua_A/runs/eval1000_A
Cùng cách buoc/tts.py: soxr.resample(48 kHz -> 16 kHz) rồi run_pilot.write_flac (FLAC PCM_16, ghi tạm rồi đổi tên).
Chỉ ghi tệp audio16 còn thiếu, không ghi đè tệp đã có. In số tệp đã tạo / đã có / thiếu audio48.
"""
import argparse
import os
from thuvien.am_thanh import write_flac  # noqa: E402

from thuvien.manifest import load_manifest  # noqa: E402

SR16 = 16_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    a = ap.parse_args()
    import soundfile as sf
    import soxr
    made = have = lost = 0
    for m in load_manifest(a.run):
        p16 = os.path.join(a.run, m["audio16"])
        p48 = os.path.join(a.run, m["audio48"])
        if os.path.exists(p16):
            have += 1
            continue
        if not os.path.exists(p48):
            lost += 1
            continue
        w, sr = sf.read(p48, dtype="float32")
        os.makedirs(os.path.dirname(p16), exist_ok=True)
        write_flac(p16, soxr.resample(w, sr, SR16) if len(w) else w, SR16)
        made += 1
    print(f"{a.run}: tạo {made}, đã có {have}, thiếu audio48 {lost}")
    if lost:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
