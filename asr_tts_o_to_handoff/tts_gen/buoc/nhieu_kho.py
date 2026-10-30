# -*- coding: utf-8 -*-
"""Kho nhiễu giai đoạn 1: chỉ mục các tệp CAVEMOVE có nhãn theo preset (cauhinh/nhieu.py: NGUON_PRESET, XE_NHIEU).

Chạy (từ tts_gen/):
  python -m buoc.nhieu_kho --nhieu ~/asr_tts_o_to/nhieu --out runs/nhieu_v1/kho              # trên cụm (đọc tệp)
  python -m buoc.nhieu_kho --tu-csv runs/nhieu_v1/do/cavemove.csv --out runs/nhieu_v1/kho    # laptop (từ số đo sẵn)
Mỗi tệp <xe>/<cấu hình>/{noise,ventilation}/<tên>.wav khớp luật của một preset thành một dòng kho_nhieu.jsonl:
nhieu_id, preset, split (theo xe), xe, cau_hinh, loai, ten, tep (tương đối so với --nhieu), dai_s, so_kenh, thay_the.
Xe không có tệp nào khớp luật chính thì dùng luật thay_the (E01 của Golf: quạt mức 1, đứng yên). Thiếu preset nào ở
split nào thì dừng (mã 3). Ghi thêm kho_config.json và in tóm tắt số tệp, số phút theo preset × split.
"""
import argparse
import collections
import csv
import glob
import json
import os
import re

import cauhinh.nhieu as N

GOC_CM = os.path.join("cavemove", "giai_nen", "cavemove_dataset")


def nhan(loai, ten):
    """(tốc độ hoặc mức quạt, kính, nhám) từ tên tệp; None nếu không đọc được."""
    m = re.match(r"s(\d+)_w(\d)(.*)$", ten) if loai == "noise" else re.match(r"v(\d)_w(\d)(.*)$", ten)
    return (int(m.group(1)), int(m.group(2)), "coarse" in m.group(3)) if m else None


def khop(luat, loai, ten, quat_max):
    n = nhan(loai, ten)
    if n is None or loai != luat["loai"] or n[1] not in luat["kinh"]:
        return False
    if loai == "noise":
        return luat["toc_do"][0] <= n[0] <= luat["toc_do"][1] and n[2] == luat["nham"]
    return n[0] == (quat_max if luat["quat"] == "max" else luat["quat"])


def chon(tep):
    """tep: [(xe, cau_hinh, loai, ten, dai_s, so_kenh)] -> [dòng kho]."""
    quat_max = collections.defaultdict(int)
    for xe, _, loai, ten, *_ in tep:
        if loai == "ventilation" and nhan(loai, ten):
            quat_max[xe] = max(quat_max[xe], nhan(loai, ten)[0])
    out = []
    for p, luat in N.NGUON_PRESET.items():
        for xe in sorted(N.XE_NHIEU):
            ds = [t for t in tep if t[0] == xe and khop(luat, t[2], t[3], quat_max[xe])]
            thay = not ds and "thay_the" in luat
            if thay:
                ds = [t for t in tep if t[0] == xe and khop(luat["thay_the"], t[2], t[3], quat_max[xe])]
            for xe_, ch, loai, ten, dai, so_kenh in sorted(ds):
                out.append(dict(nhieu_id=f"{p}_{xe_}_{ch}_{ten}", preset=p, split=N.XE_NHIEU[xe_], xe=xe_, cau_hinh=ch,
                                loai=loai, ten=ten, tep="/".join((GOC_CM.replace(os.sep, "/"), xe_, ch, loai, ten + ".wav")),
                                dai_s=round(dai, 3), so_kenh=so_kenh, thay_the=thay))
    return out


def doc_tep(nhieu):
    import soundfile as sf
    out = []
    for p in sorted(glob.glob(os.path.join(os.path.expanduser(nhieu), GOC_CM, "*", "*", "*", "*.wav"))):
        xe, ch, loai, ten = p.replace("\\", "/").split("/")[-4:]
        if xe in N.XE_NHIEU and ch in N.CAU_HINH_NHIEU and loai in ("noise", "ventilation"):
            i = sf.info(p)
            if i.samplerate != 16000:
                raise SystemExit(f"{p}: {i.samplerate} Hz")
            out.append((xe, ch, loai, ten[:-4], i.duration, i.channels))
    return out


def doc_csv(path):
    with open(path, encoding="utf-8") as f:
        return [(r["xe"], r["cau_hinh"], r["loai"], r["tep"], float(r["dai_s"]), 8) for r in csv.DictReader(f)
                if r["xe"] in N.XE_NHIEU and r["cau_hinh"] in N.CAU_HINH_NHIEU and r["loai"] in ("noise", "ventilation")]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--nhieu", help="thư mục đích của buoc.nhieu_tai (có cavemove/giai_nen)")
    g.add_argument("--tu-csv", help="cavemove.csv của phantich.do_nhieu (laptop, không cần tệp âm thanh)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = chon(doc_tep(a.nhieu) if a.nhieu else doc_csv(a.tu_csv))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "kho_nhieu.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tom = collections.defaultdict(lambda: [0, 0.0, set()])
    for r in rows:
        t = tom[(r["preset"], r["split"])]
        t[0] += 1
        t[1] += r["dai_s"]
        t[2].add(r["xe"] + ("*" if r["thay_the"] else ""))
    thieu = [(p, s) for p in N.PRESET_GD1 for s in ("train", "dev") if (p, s) not in tom]
    with open(os.path.join(a.out, "kho_config.json"), "w", encoding="utf-8") as f:
        json.dump(dict(nguon=N.NGUON_NHIEU["cavemove"], nguon_preset=N.NGUON_PRESET, xe=N.XE_NHIEU,
                       cau_hinh=N.CAU_HINH_NHIEU, tu=a.nhieu or a.tu_csv,
                       tom_tat={f"{p}|{s}": dict(so_tep=v[0], phut=round(v[1] / 60, 1), xe=sorted(v[2]))
                                for (p, s), v in sorted(tom.items())}), f, ensure_ascii=False, indent=1)
    print(f"{len(rows)} tệp -> {a.out}/kho_nhieu.jsonl (* = luật thay thế)")
    for (p, s), (n, d, xe) in sorted(tom.items()):
        print(f"  {p} {s:5s} {n:3d} tệp {d / 60:5.1f} phút  {sorted(xe)}")
    if thieu:
        raise SystemExit(f"Thiếu nguồn cho {thieu}")


if __name__ == "__main__":
    main()
