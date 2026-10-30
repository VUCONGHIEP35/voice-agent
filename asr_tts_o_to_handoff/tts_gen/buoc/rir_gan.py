# -*- coding: utf-8 -*-
"""Bảng gán RIR cho từng bản trộn (giai đoạn 3 của docs/RIR.md, sửa theo docs/ke_hoach_RIR_v1.md). Chưa chập gì.

Chạy (từ tts_gen/; chỉ cần thư viện chuẩn):
  python -m buoc.rir_gan --kho runs/rir_v2/kho runs/rir_v2/kho_do --out runs/rir_v2/gan      # mô phỏng + đo thật
  python -m buoc.rir_gan --kho ... --out ... --runs-goc runs/ket_qua_full10k/runs     # trên laptop
Đầu vào (luật v1): mỗi lượt full10k_p01..p10 lấy câu có ket_qua = dat trong gate_hop_v1.csv; full10k_wake lấy thêm điều
kiện kiểu ghép thuộc GHEP_GIU (đủ cụm, cắt đúng ranh giới). Âm thanh là audio16 của lượt đó (không lấy mẫu lại).
Vùng (trường vung) = vùng của giọng đã đọc (voice_region; câu đổi giọng có thể khác speaker_region).
Mỗi câu (câu gốc = sample_id bỏ đuôi "#w"):
  split   dev nếu băm(nhóm chia) < TY_LE_DEV_CAU, không thì train. Nhóm chia = câu gốc (mặc định), hoặc lõi câu
          (core) / khung (frame_id) của câu gốc trong NHAN_CAU (--chia-theo, CHIA_DEV_THEO). Câu ghép cùng split với
          câu gốc.
  số bản  SO_BAN[split] (train 2, dev 1).
Mỗi bản b:
  - nguồn, khoang, ghế, micro: bốc theo hạt giống (câu gốc, b). Câu ghép vì vậy cùng xe, ghế, micro với bản b của câu
    gốc (cùng người, cùng xe). Ghế 70/20/5/5, micro đều 4 vị trí (đặc tả gốc). Nguồn: ưu tiên RIR ĐO THẬT với xác suất
    P_RIR_DO (người dùng chọn 28/10); xe đo của split không có ghế + micro đó thì dùng mô phỏng. Khoang (xe) bốc đều
    trong các khoang của nguồn đó có RIR đạt cho ghế + micro; các bản của cùng câu khác khoang, nên không dùng chung RIR.
  - có RIR hay không (P_RIR) và RIR cụ thể trong khoang (vị trí đầu; với RIR đo: biến thể vị trí/hướng/kính, kênh):
    hạt giống riêng của bản = h32(sample_id, b, SEED).
  Không gán preset (preset mã E gán ở bước cộng nhiễu).
Thêm hay bớt file không đổi bản trộn của file khác: mọi lựa chọn chỉ phụ thuộc mã của chính câu đó và kho RIR.
Ghi <out>/assign_train.jsonl, assign_dev.jsonl, phan_bo.json (để người dùng xem trước khi chập), gan_config.json.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import random
import time

import cauhinh.tang_cuong as C
from cauhinh.duong_dan import GOC
from thuvien.chon_cau import h32
from thuvien.manifest import load_manifest

GIU_TU_MANIFEST = ("sample_id", "case_id", "speaker_region", "voice", "voice_region", "length_class", "n_syllables",
                   "duration_s", "clipped", "text_raw", "audio16", "wake_type", "wake_cat", "parent_utt_id")


def doc_dau_vao(runs_goc, luot_thuong=C.LUOT_THUONG, luot_ghep=C.LUOT_GHEP):
    """[dòng đầu vào]: mỗi file đạt luật v1 một dòng, kèm run và các trường manifest cần cho gán và chập."""
    out = []
    for run in list(luot_thuong) + [luot_ghep]:
        d = os.path.join(runs_goc, run)
        man = {m["utt_id"]: m for m in load_manifest(d)}
        with open(os.path.join(d, C.CHAM_DAU_VAO), encoding="utf-8-sig") as f:
            for g in csv.DictReader(f):
                if g["ket_qua"] not in C.KET_QUA_DAU_VAO:
                    continue
                m = man[g["utt_id"]]
                if run == luot_ghep and (m.get("wake_type"), m.get("wake_cat") or "") not in C.GHEP_GIU:
                    continue
                out.append(dict(utt_id=m["utt_id"], run=run, phan="ghep" if run == luot_ghep else "thuong",
                                vung=m.get("voice_region") or m["speaker_region"], **{k: m.get(k) for k in GIU_TU_MANIFEST}))
    return out


def cau_goc(sample_id):
    return sample_id.split("#", 1)[0]


def gan_nhom_chia(inp, theo, nhan_path):
    """Thêm trường nhom_chia (giá trị đem băm để chia train/dev) vào mỗi dòng đầu vào."""
    if theo == "cau_goc":
        for f in inp:
            f["nhom_chia"] = cau_goc(f["sample_id"])
        return
    with open(nhan_path, encoding="utf-8") as fh:
        nhan = {d["sample_id"]: d[theo] for d in (json.loads(x) for x in fh if x.strip())}
    for f in inp:
        f["nhom_chia"] = f"{theo}:{nhan[cau_goc(f['sample_id'])]}"


def chia(goc, seed=C.SEED):
    return "dev" if h32("split", goc, seed) / 2 ** 32 < C.TY_LE_DEV_CAU else "train"


def chi_muc_kho(rir_rows):
    """Từ các RIR đạt (kho mô phỏng và/hoặc kho đo): ({(khoang, ghế, micro): [rir_id]}, {split: {nguồn: [khoang]}},
    {khoang: loại xe}, {rir_id: dòng}). Nguồn = "mo_phong" hoặc "do"."""
    idx, cab, loai, meta = collections.defaultdict(list), {}, {}, {}
    for r in rir_rows:
        if r.get("dat", True):
            idx[(r["khoang"], r["ghe"], r["micro"])].append(r["rir_id"])
            cab.setdefault(r["split"], {}).setdefault(r.get("nguon", "mo_phong"), set()).add(r["khoang"])
            loai[r["khoang"]] = r["loai_xe"]
            meta[r["rir_id"]] = r
    return ({k: sorted(v) for k, v in idx.items()}, {sp: {n: sorted(v) for n, v in d.items()} for sp, d in cab.items()},
            loai, meta)


def boc_trong_so(rng, w):
    keys = list(w)
    return rng.choices(keys, weights=[w[k] for k in keys])[0]


def gan_file(f, idx, cabins, loai, meta, seed=C.SEED, p_do=C.P_RIR_DO):
    """Các bản trộn của một file đầu vào. Nguồn RIR: ưu tiên kho đo với xác suất p_do (bốc theo câu gốc + bản, nên
    câu ghép đi cùng câu gốc); kho đo của split không có xe nào cho ghế + micro đã bốc, hoặc xe đo đã dùng cho bản khác
    của câu, thì dùng kho mô phỏng. Không có kho đo thì kết quả giống hệt bản chỉ có mô phỏng."""
    goc = cau_goc(f["sample_id"])
    split = chia(f.get("nhom_chia") or goc, seed)
    rows, dung = [], []
    for b in range(C.SO_BAN[split]):
        rc = random.Random(h32("cau", goc, b, seed))
        ghe = boc_trong_so(rc, C.TRONG_SO_GHE)
        mic = boc_trong_so(rc, C.TRONG_SO_MICRO)
        thu_tu = ["do", "mo_phong"] if random.Random(h32("nguon", goc, b, seed)).random() < p_do else ["mo_phong"]
        khoang = None
        for ng in thu_tu:
            cands = [k for k in cabins.get(split, {}).get(ng, []) if (k, ghe, mic) in idx]
            rc.shuffle(cands)
            khoang = next((k for k in cands if k not in dung), None)
            if khoang is not None:
                break
        if khoang is None:
            raise SystemExit(f"{f['utt_id']} bản {b}: không còn khoang {split} nào có RIR đạt cho {ghe}/{mic}")
        dung.append(khoang)
        s = h32(f["sample_id"], b, seed)
        rb = random.Random(s)
        co = rb.random() < C.P_RIR
        rid = rb.choice(idx[(khoang, ghe, mic)])
        m = meta[rid]
        rows.append(dict(ban_id=f"{f['utt_id']}__r{b}", utt_id=f["utt_id"], sample_id=f["sample_id"], cau_goc=goc,
                         run=f["run"], phan=f["phan"], split=split, ban=b, seed=s, co_rir=co,
                         rir_id=rid if co else "", khoang=khoang if co else "", loai_xe=loai[khoang] if co else "",
                         ghe=ghe if co else "", micro=mic if co else "", dau=m["dau"] if co else None,
                         nguon_rir=m.get("nguon", "mo_phong") if co else "", vung=f["vung"],
                         nhom_chia=f.get("nhom_chia") or goc,
                         **{k: f.get(k) for k in GIU_TU_MANIFEST if k != "sample_id"}))
    return rows


def ty_le(c):
    n = sum(c.values())
    return {k: round(v / n, 4) for k, v in sorted(c.items())} if n else {}


def tom_tat(inp, rows):
    """Phân bố và các kiểm tra của bảng gán (in ra và ghi phan_bo.json)."""
    out = dict(dau_vao=dict(so_file=len(inp), theo_phan=dict(collections.Counter(f["phan"] for f in inp)),
                            theo_vung=dict(collections.Counter(f["vung"] for f in inp))))
    vung_vao = ty_le(collections.Counter(f["vung"] for f in inp))
    for sp in ("train", "dev"):
        rs = [r for r in rows if r["split"] == sp]
        co = [r for r in rs if r["co_rir"]]
        vung = ty_le(collections.Counter(r["vung"] for r in rs))
        out[sp] = dict(
            so_cau=len({r["utt_id"] for r in rs}), so_ban=len(rs), ty_le_co_rir=round(len(co) / max(len(rs), 1), 4),
            vung=vung, vung_lech_diem=max((abs(vung.get(k, 0) - v) * 100 for k, v in vung_vao.items()), default=0),
            loai_xe=ty_le(collections.Counter(r["loai_xe"] for r in co)), ghe=ty_le(collections.Counter(r["ghe"] for r in co)),
            micro=ty_le(collections.Counter(r["micro"] for r in co)),
            nguon_rir=ty_le(collections.Counter(r["nguon_rir"] for r in co)),
            nguon_theo_micro={m: ty_le(collections.Counter(r["nguon_rir"] for r in co if r["micro"] == m))
                              for m in sorted({r["micro"] for r in co})},
            xe_do=ty_le(collections.Counter(r["khoang"] for r in co if r["nguon_rir"] == "do")),
            so_khoang_dung=len({r["khoang"] for r in co}), so_rir_dung=len({r["rir_id"] for r in co}),
            ghe_theo_case={c: ty_le(collections.Counter(r["ghe"] for r in co if r["case_id"] == c))
                           for c in sorted({r["case_id"] for r in co})},
            loai_xe_theo_vung={v: ty_le(collections.Counter(r["loai_xe"] for r in co if r["vung"] == v))
                               for v in sorted({r["vung"] for r in co})},
            co_rir_theo_phan={p: round(sum(r["co_rir"] for r in rs if r["phan"] == p) / max(sum(r["phan"] == p for r in rs), 1), 4)
                              for p in ("thuong", "ghep")})
    rir_train = {r["rir_id"] for r in rows if r["split"] == "train" and r["co_rir"]}
    kh_train = {r["khoang"] for r in rows if r["split"] == "train" and r["co_rir"]}
    by_utt = collections.defaultdict(list)
    for r in rows:
        by_utt[r["utt_id"]].append(r)
    hai_ban = all(len({(r["khoang"], r["ghe"], r["micro"], r["dau"]) for r in v if r["co_rir"]}) == sum(r["co_rir"] for r in v)
                  for v in by_utt.values())
    goc_of = {}
    for r in rows:
        if r["phan"] == "thuong":
            goc_of[(r["sample_id"], r["ban"])] = r
    ghep_ok, ghep_co_goc = True, 0
    for r in rows:
        if r["phan"] == "ghep":
            p = goc_of.get((r["cau_goc"], r["ban"]))
            if p is not None:
                ghep_co_goc += 1
                # cùng split luôn; cùng khoang/ghế/micro khi cả hai có RIR
                if p["split"] != r["split"] or (p["co_rir"] and r["co_rir"] and
                                                (p["khoang"], p["ghe"], p["micro"]) != (r["khoang"], r["ghe"], r["micro"])):
                    ghep_ok = False
    out["kiem"] = dict(
        dev_khong_dung_rir_train=not any(r["rir_id"] in rir_train for r in rows if r["split"] == "dev" and r["co_rir"]),
        dev_khong_dung_khoang_train=not any(r["khoang"] in kh_train for r in rows if r["split"] == "dev" and r["co_rir"]),
        hai_ban_khac_rir=hai_ban, ghep_cung_split_khoang_ghe_micro=ghep_ok, so_ban_ghep_co_cau_goc=ghep_co_goc,
        cau_goc_nhieu_split=sum(len({r["split"] for r in v}) > 1 for v in
                                _nhom(rows, "cau_goc").values()))
    return out


def _nhom(rows, key):
    d = collections.defaultdict(list)
    for r in rows:
        d[r[key]].append(r)
    return d


def in_tom_tat(t):
    print(f"Đầu vào {t['dau_vao']['so_file']} file {t['dau_vao']['theo_phan']}, vùng {t['dau_vao']['theo_vung']}")
    for sp in ("train", "dev"):
        s = t[sp]
        print(f"\n{sp}: {s['so_cau']} câu, {s['so_ban']} bản, có RIR {s['ty_le_co_rir']:.3f} "
              f"(thường {s['co_rir_theo_phan']['thuong']:.3f}, ghép {s['co_rir_theo_phan']['ghep']:.3f}); "
              f"{s['so_khoang_dung']} khoang, {s['so_rir_dung']} RIR khác nhau")
        print(f"  vùng {s['vung']} (lệch tối đa {s['vung_lech_diem']:.2f} điểm so với đầu vào)")
        for k in ("nguon_rir", "xe_do", "loai_xe", "ghe", "micro"):
            print(f"  {k:8s} {s[k]}")
    print("\nKiểm:", t["kiem"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kho", nargs="+", required=True, help="một hoặc nhiều thư mục kho (rir_manifest.jsonl): mô phỏng, đo")
    ap.add_argument("--p-do", type=float, default=C.P_RIR_DO, help="xác suất ưu tiên RIR đo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs-goc", default=os.path.join(GOC, "runs"), help="thư mục chứa full10k_p01..p10, full10k_wake")
    ap.add_argument("--seed", type=int, default=C.SEED)
    ap.add_argument("--chia-theo", choices=["cau_goc", "core", "frame_id"], default=C.CHIA_DEV_THEO)
    a = ap.parse_args()
    rir, kho_sha = [], {}
    for d in a.kho:
        mp = os.path.join(d, "rir_manifest.jsonl")
        with open(mp, "rb") as f:
            kho_sha[d] = hashlib.sha256(f.read()).hexdigest()
        with open(mp, encoding="utf-8") as f:
            rir += [json.loads(x) for x in f if x.strip()]
    if len({r["rir_id"] for r in rir}) != len(rir):
        raise SystemExit("rir_id trùng giữa các kho")
    idx, cabins, loai, meta = chi_muc_kho(rir)
    inp = doc_dau_vao(a.runs_goc)
    gan_nhom_chia(inp, a.chia_theo, os.path.join(GOC, C.NHAN_CAU))
    rows = [r for f in inp for r in gan_file(f, idx, cabins, loai, meta, a.seed, a.p_do)]
    os.makedirs(a.out, exist_ok=True)
    for sp in ("train", "dev"):
        with open(os.path.join(a.out, f"assign_{sp}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                if r["split"] == sp:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    t = tom_tat(inp, rows)
    with open(os.path.join(a.out, "phan_bo.json"), "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "gan_config.json"), "w", encoding="utf-8") as f:
        json.dump(dict(seed=a.seed, runs_goc=a.runs_goc, kho=a.kho, rir_manifest_sha256=kho_sha, p_rir_do=a.p_do, cham=C.CHAM_DAU_VAO,
                       ket_qua=C.KET_QUA_DAU_VAO, ghep_giu=sorted(C.GHEP_GIU), p_rir=C.P_RIR, so_ban=C.SO_BAN,
                       ty_le_dev_cau=C.TY_LE_DEV_CAU, chia_theo=a.chia_theo, trong_so_ghe=C.TRONG_SO_GHE, trong_so_micro=C.TRONG_SO_MICRO,
                       so_khoang={sp: {n: len(v) for n, v in d.items()} for sp, d in cabins.items()},
                       trich_dan_rir_do=sorted({r["trich_dan"] for r in rir if r.get("nguon") == "do"}),
                       ghi_luc=time.strftime("%F %T")),
                  f, ensure_ascii=False, indent=1)
    in_tom_tat(t)
    if not all(v for k, v in t["kiem"].items() if isinstance(v, bool)) or t["kiem"]["cau_goc_nhieu_split"]:
        raise SystemExit("Bảng gán trượt kiểm tra (xem 'Kiểm' ở trên)")


if __name__ == "__main__":
    main()
