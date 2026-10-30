# -*- coding: utf-8 -*-
"""Cắt đoạn nghe nhiễu GIỮ ĐỘ TO THẬT trong mỗi nhóm (bản đầu của phantich/do_nhieu.py đưa từng đoạn về −26 dBFS nên
người nghe mất manh mối "to hay nhỏ"). Chạy trên cụm (venv_rir), từ tts_gen/:
  python -m phantich.cat_doan_nghe --ds runs/nhieu_v1/do/doan_nghe.tsv --nhieu ~/asr_tts_o_to/nhieu --out runs/nhieu_v1/do/nghe2
doan_nghe.tsv (tab): nhom, ten, tep (tương đối so với --nhieu), bat_dau_s (−1 = giữa tệp), dai_s (0 = cả tệp).
Mỗi nhóm dùng MỘT hệ số khuếch đại: đoạn to nhất có RMS −20 dBFS, rồi hạ cả nhóm nếu có đỉnh vượt −1 dBFS. Kênh 1.
Ghi <out>/<nhom>/<ten>.flac và <out>/muc.tsv (mức RMS gốc và sau khuếch đại của từng đoạn).
"""
import argparse
import csv
import os

import numpy as np
import soundfile as sf

from thuvien.am_thanh import write_flac


def cat(path, bat_dau_s, dai_s):
    info = sf.info(path)
    n = int(dai_s * info.samplerate) if dai_s > 0 else info.frames
    s = (info.frames - n) // 2 if bat_dau_s < 0 else int(bat_dau_s * info.samplerate)
    x, sr = sf.read(path, start=max(0, s), frames=min(n, info.frames), dtype="float64", always_2d=True)
    return x[:, 0] - x[:, 0].mean(), sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", required=True)
    ap.add_argument("--nhieu", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    goc = os.path.expanduser(a.nhieu)
    nhom = {}
    for r in csv.DictReader(open(a.ds, encoding="utf-8"), delimiter="\t"):
        x, sr = cat(os.path.join(goc, r["tep"]), float(r["bat_dau_s"]), float(r["dai_s"]))
        nhom.setdefault(r["nhom"], []).append((r["ten"], x, sr))
    dong = ["nhom\tten\trms_goc_db\trms_ra_db"]
    for g, ds in nhom.items():
        rms = [20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12) for _, x, _ in ds]
        k = -20 - max(rms)
        pk = max(20 * np.log10(np.max(np.abs(x)) + 1e-12) for _, x, _ in ds) + k
        k -= max(0.0, pk + 1)
        os.makedirs(os.path.join(a.out, g), exist_ok=True)
        for (ten, x, sr), r in zip(ds, rms):
            write_flac(os.path.join(a.out, g, f"{ten}.flac"), (x * 10 ** (k / 20)).astype(np.float32), sr)
            dong.append(f"{g}\t{ten}\t{r:.1f}\t{r + k:.1f}")
        print(f"{g}: {len(ds)} đoạn, khuếch đại chung {k:+.1f} dB, RMS ra {min(rms) + k:.1f} … {max(rms) + k:.1f} dBFS")
    with open(os.path.join(a.out, "muc.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(dong) + "\n")


if __name__ == "__main__":
    main()
