# -*- coding: utf-8 -*-
"""Bảng gán nhiễu giai đoạn 1 cho từng bản đã chèn vang (docs/ke_hoach_nhieu_v1.md). Chưa trộn gì; chỉ thư viện chuẩn.

Chạy (từ tts_gen/):
  python -m buoc.nhieu_gan --vang runs/rir_v2/aug_v1/_reverb/manifest.jsonl --kho runs/nhieu_v1/kho --out runs/nhieu_v1/gan
Mỗi bản của manifest vang (bước RIR):
  preset  bốc theo (câu gốc, bản): TY_LE_THEO_SHEET bốc trong preset mà cột "Case dùng" ghi cho case (giao PRESET_GD1),
          còn lại bốc đều trong PRESET_GD1. Câu ghép lời gọi vì vậy cùng preset với câu gốc.
  tệp, kênh, điểm bắt đầu, SNR  bốc theo (sample_id, bản): tệp trong kho cùng preset và cùng split (train: 3 xe; dev:
          Golf); kênh đúng vị trí micro của bản (MICRO_DO; trần -> kênh 7/8 phân tán; bản không RIR -> kênh bất kỳ).
          Không có tệp nào có kênh đúng vị trí thì lấy kênh bất kỳ và ghi kenh_khop = false. SNR đều trong nhóm của preset.
Ghi trường preset_moi_truong (KHÔNG dùng factors_covered: đó là mã yếu tố nội dung của sheet Yeu_to).
Ghi <out>/assign_train.jsonl, assign_dev.jsonl, phan_bo.json, gan_config.json. Trượt kiểm thì dừng mã 3.
"""
import argparse
import collections
import hashlib
import json
import os
import random

import cauhinh.nhieu as N
import cauhinh.tang_cuong as C
from thuvien.chon_cau import h32


def kenh_cho(micro, xe, cau_hinh):
    """Các kênh (1–8) của tệp CAVEMOVE ứng với vị trí micro; [] nếu cấu hình không có micro đó."""
    if not micro:
        return list(range(1, 9))
    if micro == "tran":
        return list(N.KENH_TRAN) if cau_hinh == "distributed" else []
    m = C.MICRO_DO.get(("cavemove", xe, cau_hinh)) or C.MICRO_DO.get(("cavemove", "*", cau_hinh)) or {}
    return sorted(k for k, v in m.items() if v == micro)


def chon_preset(goc, ban, case_id, seed=N.SEED):
    r = random.Random(h32("preset", goc, ban, seed))
    theo_sheet = [p for p in N.PRESET_GD1 if case_id in N.CASE_PRESET[p]]
    if r.random() < N.TY_LE_THEO_SHEET and theo_sheet:
        return r.choice(theo_sheet), "sheet"
    return r.choice(N.PRESET_GD1), "ngau_nhien"


def chon_doan(kho, preset, split, micro, khoa, dai_ban, seed=N.SEED):
    """Tệp, kênh, điểm bắt đầu cho một đoạn nhiễu; khoa là chuỗi băm riêng của bản (hoặc của ô lưới)."""
    r = random.Random(h32("nhieu", *khoa, seed))
    cands = sorted((t for t in kho if t["preset"] == preset and t["split"] == split), key=lambda t: t["nhieu_id"])
    if not cands:
        raise SystemExit(f"kho không có tệp {preset}/{split}")
    co_kenh = [t for t in cands if kenh_cho(micro, t["xe"], t["cau_hinh"])]
    t = r.choice(co_kenh or cands)
    kenh = r.choice(kenh_cho(micro, t["xe"], t["cau_hinh"]) or list(range(1, t["so_kenh"] + 1)))
    du = t["dai_s"] - 2 * N.CAT_BIEN_S - dai_ban
    bat_dau = N.CAT_BIEN_S + r.random() * du if du > 0 else N.CAT_BIEN_S
    return dict(nhieu_id=t["nhieu_id"], nhieu_tep=t["tep"], nhieu_xe=t["xe"], nhieu_cau_hinh=t["cau_hinh"],
                kenh=kenh, kenh_khop=bool(co_kenh), bat_dau_s=round(bat_dau, 4), nhieu_dai_s=t["dai_s"]), r


def gan_ban(v, kho, seed=N.SEED):
    if "factors_covered" in v:
        raise SystemExit("manifest vang có factors_covered: không trộn trường này với preset")
    preset, nguon = chon_preset(v["cau_goc"], v["ban"], v["case_id"], seed)
    d, r = chon_doan(kho, preset, v["split"], v["micro"], (v["sample_id"], v["ban"]), v["dai_s"], seed)
    lo, hi = N.nhom_snr(preset)
    return dict(v, preset_moi_truong=preset, nguon_preset=nguon, snr_db=round(r.uniform(lo, hi), 2), **d)


def ty_le(c):
    n = sum(c.values()) or 1
    return {k: round(v / n, 4) for k, v in sorted(c.items())}


def tom_tat(rows):
    t = {}
    for sp in ("train", "dev"):
        rs = [r for r in rows if r["split"] == sp]
        t[sp] = dict(so_ban=len(rs), preset=ty_le(collections.Counter(r["preset_moi_truong"] for r in rs)),
                     nguon_preset=ty_le(collections.Counter(r["nguon_preset"] for r in rs)),
                     xe=ty_le(collections.Counter(r["nhieu_xe"] for r in rs)),
                     kenh_khop=round(sum(r["kenh_khop"] for r in rs) / max(len(rs), 1), 4),
                     preset_theo_case={c: dict(collections.Counter(r["preset_moi_truong"] for r in rs if r["case_id"] == c))
                                       for c in sorted({r["case_id"] for r in rs})},
                     snr_theo_preset={p: [round(min(x), 1), round(max(x), 1)] for p in N.PRESET_GD1
                                      if (x := [r["snr_db"] for r in rs if r["preset_moi_truong"] == p])},
                     vung=ty_le(collections.Counter(r["vung"] for r in rs)))
    goc = {(r["cau_goc"], r["ban"]): r["preset_moi_truong"] for r in rows if r["phan"] == "thuong"}
    ghep = [r for r in rows if r["phan"] == "ghep"]
    t["kiem"] = dict(
        dev_chi_golf=all(r["nhieu_xe"] == "Volkswagen_Golf" for r in rows if r["split"] == "dev"),
        train_khong_golf=all(r["nhieu_xe"] != "Volkswagen_Golf" for r in rows if r["split"] == "train"),
        ghep_cung_preset=all(goc.get((r["cau_goc"], r["ban"]), r["preset_moi_truong"]) == r["preset_moi_truong"] for r in ghep),
        preset_hop_le=all(r["preset_moi_truong"] in N.PRESET_GD1 for r in rows),
        snr_trong_nhom=all(N.nhom_snr(r["preset_moi_truong"])[0] <= r["snr_db"] <= N.nhom_snr(r["preset_moi_truong"])[1]
                           for r in rows),
        khong_factors_covered=not any("factors_covered" in r for r in rows),
        so_ban_ghep=len(ghep))
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vang", required=True, help="manifest.jsonl của bộ vang (buoc.rir_chap)")
    ap.add_argument("--kho", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=N.SEED)
    a = ap.parse_args()
    with open(os.path.join(a.kho, "kho_nhieu.jsonl"), encoding="utf-8") as f:
        kho = [json.loads(x) for x in f if x.strip()]
    with open(a.vang, encoding="utf-8") as f:
        vang = [json.loads(x) for x in f if x.strip()]
    rows = [gan_ban(v, kho, a.seed) for v in vang]
    os.makedirs(a.out, exist_ok=True)
    for sp in ("train", "dev"):
        with open(os.path.join(a.out, f"assign_{sp}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                if r["split"] == sp:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    t = tom_tat(rows)
    with open(os.path.join(a.out, "phan_bo.json"), "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
    sha = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in (a.vang, os.path.join(a.kho, "kho_nhieu.jsonl"))}
    with open(os.path.join(a.out, "gan_config.json"), "w", encoding="utf-8") as f:
        json.dump(dict(seed=a.seed, vang=a.vang, kho=a.kho, sha256=sha, preset=N.PRESET_GD1, ty_le_theo_sheet=N.TY_LE_THEO_SHEET,
                       case_preset=N.CASE_PRESET, snr_theo_nhom=N.SNR_THEO_NHOM, xe=N.XE_NHIEU), f, ensure_ascii=False, indent=1)
    for sp in ("train", "dev"):
        s = t[sp]
        print(f"{sp}: {s['so_ban']} bản; preset {s['preset']}; theo sheet {s['nguon_preset']}; xe {s['xe']}; "
              f"kênh đúng vị trí {s['kenh_khop']:.1%}")
    print("Kiểm:", t["kiem"])
    if not all(v for v in t["kiem"].values() if isinstance(v, bool)):
        raise SystemExit(3)


if __name__ == "__main__":
    main()
