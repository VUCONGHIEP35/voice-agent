# -*- coding: utf-8 -*-
"""So kho RIR mô phỏng với kho RIR đo thật theo loại xe × nhóm ghế × dải octave (hiệu chỉnh vật liệu, ke_hoach_RIR_v3).

Chạy (từ tts_gen/):
  python -m phantich.so_kho_rir --mo-phong runs/rir_v2/thu/kho --do runs/rir_v2/kho_do [--out so_sanh.json]
Mục tiêu (đặt từ kho đo, chỉ dùng RIR đạt):
  EDT từng dải (250 Hz–4 kHz), ghế lái và ghế sau: trung vị của mỗi loại mô phỏng nằm trong [min, max] trung vị
      các xe đo, nới ±NOI_EDT;
  DRR ghế sau: trung vị mỗi loại trong ±NOI_DRR dB quanh trung vị các xe CAVEMOVE (micro phía trước; V-Class đo
      bằng micro trần, nên không lấy làm tâm).
Chỉ xem trung vị: ray tracing không tất định (EDT dao động ±0,01–0,02 s giữa các lần chạy).
"""
import argparse
import collections
import json
import os

import numpy as np

import cauhinh.tang_cuong as C

NOI_EDT = 0.25
NOI_DRR = 3.0
NHOM = {"lai": "lai", "phu": "phu", "sau_trai": "sau", "sau_phai": "sau"}


def doc(kho):
    with open(os.path.join(kho, "rir_manifest.jsonl"), encoding="utf-8") as f:
        return [r for r in map(json.loads, f) if r.get("dat", True)]


def trung_vi(rows):
    """{dải: trung vị EDT, 'drr': ..., 't20': ..., 'n': ...} của một nhóm RIR."""
    out = {b: float(np.median(v)) if (v := [r["edt_bang"][str(b)] for r in rows if r["edt_bang"].get(str(b)) is not None])
           else None for b in C.EDT_BANG}
    out.update(drr=float(np.median([r["drr_db"] for r in rows])),
               t20=float(np.median([r["t20_s"] for r in rows if r.get("t20_s")] or [np.nan])), n=len(rows))
    return out


def theo_nhom(rows, khoa):
    g = collections.defaultdict(list)
    for r in rows:
        g[(r[khoa], NHOM[r["ghe"]])].append(r)
    return {k: trung_vi(v) for k, v in g.items()}


def muc_tieu(do):
    """Từ trung vị từng xe đo: dải EDT cho phép theo (nhóm ghế, dải) và tâm DRR ghế sau."""
    xe = theo_nhom(do, "khoang")
    mt = {}
    for nh in ("lai", "sau"):
        for b in C.EDT_BANG:
            v = [m[b] for (k, n), m in xe.items() if n == nh and m[b] is not None]
            mt[(nh, b)] = (min(v) * (1 - NOI_EDT), max(v) * (1 + NOI_EDT))
    cave = {r["khoang"] for r in do if r.get("bo") == "cavemove"}
    tam = float(np.median([m["drr"] for (k, n), m in xe.items() if n == "sau" and k in cave]))
    mt[("sau", "drr")] = (tam - NOI_DRR, tam + NOI_DRR)
    return xe, mt


def danh_gia(sim, mt):
    """[(loại, nhóm ghế, chỉ số, giá trị, dải đích, đạt)] cho mọi loại mô phỏng."""
    out = []
    for (lo, nh), m in sorted(theo_nhom(sim, "loai_xe").items()):
        if nh == "phu":
            continue
        for b in C.EDT_BANG:
            a, z = mt[(nh, b)]
            out.append((lo, nh, f"edt_{b}", m[b], (a, z), m[b] is not None and a <= m[b] <= z))
        if nh == "sau":
            a, z = mt[("sau", "drr")]
            out.append((lo, nh, "drr", m["drr"], (a, z), a <= m["drr"] <= z))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mo-phong", required=True, nargs="+")
    ap.add_argument("--do", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    do = doc(a.do)
    sim = [r for k in a.mo_phong for r in doc(k)]
    xe, mt = muc_tieu(do)
    kq = danh_gia(sim, mt)

    print("Xe đo (trung vị):  nhóm  " + "  ".join(f"{b:>5}" for b in C.EDT_BANG) + "    DRR    T20")
    for (k, nh), m in sorted(xe.items()):
        print(f"  {k:10s} {nh:4s} " + "  ".join(f"{m[b]:.3f}" if m[b] else "  -  " for b in C.EDT_BANG)
              + f"  {m['drr']:5.1f}  {m['t20']:.3f}  (n={m['n']})")
    print("\nMô phỏng (trung vị):")
    for (lo, nh), m in sorted(theo_nhom(sim, "loai_xe").items()):
        print(f"  {lo:10s} {nh:4s} " + "  ".join(f"{m[b]:.3f}" if m[b] else "  -  " for b in C.EDT_BANG)
              + f"  {m['drr']:5.1f}  {m['t20']:.3f}  (n={m['n']})")
    truot = [x for x in kq if not x[5]]
    print(f"\nĐạt {len(kq) - len(truot)}/{len(kq)} mục tiêu (EDT nới ±{NOI_EDT:.0%}, DRR sau ±{NOI_DRR} dB).")
    for lo, nh, ten, v, (lo_, hi), _ in truot:
        print(f"  TRƯỢT {lo:8s} {nh:4s} {ten:9s} {v if v is None else round(v, 3)} ngoài [{lo_:.3f}, {hi:.3f}]")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(dict(muc_tieu={f"{k[0]}|{k[1]}": v for k, v in mt.items()},
                           xe_do={f"{k[0]}|{k[1]}": v for k, v in xe.items()},
                           mo_phong={f"{k[0]}|{k[1]}": v for k, v in theo_nhom(sim, "loai_xe").items()},
                           ket_qua=[dict(loai=x[0], ghe=x[1], chi_so=x[2], gia_tri=x[3], dich=x[4], dat=x[5]) for x in kq]),
                      f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
