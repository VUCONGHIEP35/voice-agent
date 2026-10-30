# -*- coding: utf-8 -*-
"""Kiểm chất lượng bước RIR (giai đoạn 5 của docs/RIR.md, sửa theo docs/ke_hoach_RIR_v1.md mục 5). Chỉ đọc, ghi báo cáo.

Chạy (từ tts_gen/):  python -m phantich.rir_qa --goc runs/rir_v2        # đọc kho/, gan/, aug_v1/_reverb/, asr_dev/ nếu có
Ghi <goc>/qa/qa.json và qa.md. Phần nào chưa có tệp thì bỏ qua và ghi "chưa có".
  kho   phân bố EDT / DRR / C50 / T20 theo loại xe, ghế, micro; RIR loại và lý do; lệch trễ; train/dev không chung khoang
  gán   tỷ lệ có RIR 0,8 ± 0,02 mỗi split; tỷ lệ vùng lệch ≤ 2 điểm so với tập đã lọc v1; các kiểm của rir_gan
  chập  mức ra −26 ± 0,5 dBFS ở ≥ 99% bản; không bản nào có đỉnh > −1 dBFS; |lệch trễ| < 2 ms ở ≥ 99% bản có RIR
  CER   trước/sau RIR trên bản dev (asr_dev/sach, asr_dev/vang; cer_min của asr_gate_<tag>.csv), theo mô hình × vùng,
        loại xe, ghế. CHỈ để bắt lỗi pipeline (sai trễ, sai tần số lấy mẫu làm CER tăng vọt), không dùng để lọc.
Mục "mô phỏng so với đo" trên mô hình B0 hoãn: đã có RIR đo (kho_do), chưa có mô hình B0.
"""
import argparse
import collections
import csv
import json
import os

import numpy as np

import cauhinh.tang_cuong as C
from thuvien.manifest import load_jsonl

ASR_TAGS = {"L": "PhoWhisper-large-ct2-int8", "M": "PhoWhisper-medium", "T": "PhoWhisper-small"}


def pct(v):
    v = np.asarray([x for x in v if x is not None], dtype=float)
    if not len(v):
        return None
    return dict(n=len(v), p5=round(float(np.percentile(v, 5)), 3), trung_vi=round(float(np.median(v)), 3),
                p95=round(float(np.percentile(v, 95)), 3))


def qa_kho(d):
    rows = load_jsonl(os.path.join(d, "rir_manifest.jsonl"))
    cab = load_jsonl(os.path.join(d, "khoang_manifest.jsonl"))
    with open(os.path.join(d, "splits.json"), encoding="utf-8") as f:
        sp = json.load(f)
    dat = [r for r in rows if r["dat"]]
    out = dict(so_khoang=len(cab), khoang_that_bai=[c["khoang"] for c in cab if c.get("that_bai")], so_rir=len(rows),
               so_rir_dat=len(dat), loai_theo_ly_do=dict(collections.Counter(x for r in rows for x in r["loi"])),
               loai_theo_ghe_micro={f"{g}/{m}": n for (g, m), n in sorted(collections.Counter((r["ghe"], r["micro"]) for r in rows if not r["dat"]).items())},
               lan_boc_tb=round(float(np.mean([c["lan_boc"] for c in cab])), 2),
               giay_moi_lan_tb=round(float(np.mean([c["giay"] / c["lan_boc"] for c in cab])), 1),
               lech_tre_max_ms=round(max(abs(r["lech_tre_ms"]) for r in rows), 3),
               edt_ngoai_dai_trong_rir_dat=sum(not C.EDT_DAI[0] <= r["edt_s"] <= C.EDT_DAI[1] for r in dat),
               train_dev_chung_khoang=sorted(set(sp["train"]) & set(sp["dev"])),
               so_khoang_split={k: len(v) for k, v in sp.items()})
    for key in ("loai_xe", "ghe", "micro"):
        out[f"theo_{key}"] = {v: {m: pct([r[m] for r in dat if r[key] == v]) for m in ("edt_s", "drr_db", "c50_db", "t20_s")}
                              for v in sorted({r[key] for r in dat})}
    return out


def qa_gan(d):
    with open(os.path.join(d, "phan_bo.json"), encoding="utf-8") as f:
        t = json.load(f)
    return dict(phan_bo=t, rir_trong_0_8=all(abs(t[s]["ty_le_co_rir"] - C.P_RIR) <= 0.02 for s in ("train", "dev")),
                vung_lech_le_2=all(t[s]["vung_lech_diem"] <= 2 for s in ("train", "dev")),
                kiem_dat=all(v for v in t["kiem"].values() if isinstance(v, bool)) and not t["kiem"]["cau_goc_nhieu_split"])


def qa_kho_do(d):
    """Kho RIR đo thật (buoc/rir_kho_do.py): số RIR, chỉ số theo xe × ghế; xe dev không có trong train."""
    rows = load_jsonl(os.path.join(d, "rir_manifest.jsonl"))
    with open(os.path.join(d, "splits.json"), encoding="utf-8") as f:
        sp = json.load(f)
    dat = [r for r in rows if r["dat"]]
    return dict(so_rir=len(rows), so_rir_dat=len(dat), splits=sp, train_dev_chung_xe=sorted(set(sp["train"]) & set(sp["dev"])),
                canh_bao=dict(collections.Counter(f"{r['bo']}:{x}" for r in rows for x in r.get("canh_bao", []))),
                giay_phep=sorted({r["giay_phep"] for r in rows}), trich_dan=sorted({r["trich_dan"] for r in rows}),
                theo_xe={k: {g: {m: pct([r[m] for r in dat if r["khoang"] == k and r["ghe"] == g]) for m in ("edt_s", "drr_db", "c50_db")}
                             for g in sorted({r["ghe"] for r in dat if r["khoang"] == k})}
                         for k in sorted({r["khoang"] for r in dat})})


def qa_chap(d):
    rows = load_jsonl(os.path.join(d, "manifest.jsonl"))
    co = [r for r in rows if r["co_rir"]]
    muc = np.array([r["muc_ra_dbfs"] for r in rows])
    lech = np.abs([r["lech_tre_ms"] for r in co]) if co else np.zeros(1)
    return dict(so_ban=len(rows), so_co_rir=len(co),
                ty_le_muc_trong_0_5=round(float(np.mean(np.abs(muc - C.MUC_GIONG_DBFS) <= 0.5)), 4),
                dinh_tren_1dbfs=sum(r["dinh_ra_dbfs"] > C.DINH_MAX_DBFS + 0.01 for r in rows),
                so_ban_ha_chong_cat=sum(r["ha_chong_cat_db"] < 0 for r in rows),
                ty_le_lech_tre_duoi_2ms=round(float(np.mean(lech < 2.0)), 4), lech_tre_p99_ms=round(float(np.percentile(lech, 99)), 3),
                ban_clipped_tu_tts=sum(bool(r.get("clipped")) for r in rows),
                dai_s=pct([r["dai_s"] for r in rows]))


def doc_gate(path):
    with open(path, encoding="utf-8-sig") as f:
        return {r["utt_id"]: float(r["cer_min"]) for r in csv.DictReader(f)}


def qa_cer(d):
    man = {m["utt_id"]: m for m in load_jsonl(os.path.join(d, "vang", "manifest.jsonl"))}
    out = {}
    for k, tag in ASR_TAGS.items():
        ps, pv = (os.path.join(d, x, f"asr_gate_{tag}.csv") for x in ("sach", "vang"))
        if not (os.path.exists(ps) and os.path.exists(pv)):
            continue
        s, v = doc_gate(ps), doc_gate(pv)
        u = sorted(set(s) & set(v) & set(man))

        def nhom(key):
            g = collections.defaultdict(list)
            for x in u:
                g[man[x].get(key) or man[x].get("speaker_region")].append(x)
            return {gk: dict(n=len(xs), truoc=round(float(np.mean([s[x] for x in xs])), 4),
                             sau=round(float(np.mean([v[x] for x in xs])), 4)) for gk, xs in sorted(g.items())}
        out[k] = dict(mo_hinh=tag, n=len(u), truoc=round(float(np.mean([s[x] for x in u])), 4),
                      sau=round(float(np.mean([v[x] for x in u])), 4),
                      tang_qua_0_1=sum(v[x] - s[x] > 0.1 for x in u), theo_vung=nhom("voice_region"),
                      theo_loai_xe=nhom("loai_xe"), theo_ghe=nhom("ghe"), theo_micro=nhom("micro"),
                      theo_nguon_rir=nhom("nguon_rir"))
    return out


def md(q):
    L = ["# QA bước RIR (luật v1)", ""]
    k = q.get("kho")
    if k:
        L += ["## Kho RIR", "",
              f"- {k['so_khoang']} khoang ({k['so_khoang_split']}), thất bại: {k['khoang_that_bai'] or 'không'}; "
              f"lần bốc trung bình {k['lan_boc_tb']}, {k['giay_moi_lan_tb']} s CPU mỗi lần mô phỏng 32 RIR.",
              f"- {k['so_rir']} RIR, đạt {k['so_rir_dat']}. Loại theo lý do: {k['loai_theo_ly_do'] or 'không'}; "
              f"theo ghế/micro: {k['loai_theo_ghe_micro'] or 'không'}.",
              f"- Lệch trễ trực tiếp tối đa {k['lech_tre_max_ms']} ms; train/dev chung khoang: {k['train_dev_chung_khoang'] or 'không'}.",
              "", "| Nhóm | EDT p5 / trung vị / p95 (s) | DRR (dB) | C50 (dB) |", "|---|---|---|---|"]
        for key in ("theo_loai_xe", "theo_ghe", "theo_micro"):
            for v, m in k[key].items():
                L.append(f"| {v} | " + " | ".join(f"{m[x]['p5']} / {m[x]['trung_vi']} / {m[x]['p95']}" for x in ("edt_s", "drr_db", "c50_db")) + " |")
        L.append("")
    kd = q.get("kho_do")
    if kd:
        L += ["## Kho RIR đo thật", "",
              f"- {kd['so_rir']} RIR, đạt {kd['so_rir_dat']}; split {kd['splits']}; giấy phép {kd['giay_phep']}; cảnh báo {kd['canh_bao'] or 'không'}.",
              "", "| Xe | Ghế | EDT p5 / trung vị / p95 (s) | DRR (dB) |", "|---|---|---|---|"]
        for xe, d in kd["theo_xe"].items():
            for g2, m in d.items():
                L.append(f"| {xe} | {g2} | {m['edt_s']['p5']} / {m['edt_s']['trung_vi']} / {m['edt_s']['p95']} | {m['drr_db']['trung_vi']} |")
        L += ["", "Trích dẫn bắt buộc (CC BY 4.0): " + "; ".join(kd["trich_dan"]), ""]
    g = q.get("gan")
    if g:
        t = g["phan_bo"]
        L += ["## Bảng gán", ""]
        for s in ("train", "dev"):
            L.append(f"- {s}: {t[s]['so_cau']} câu, {t[s]['so_ban']} bản, có RIR {t[s]['ty_le_co_rir']}; vùng {t[s]['vung']} "
                     f"(lệch {t[s]['vung_lech_diem']:.2f} điểm); loại xe {t[s]['loai_xe']}; ghế {t[s]['ghe']}; micro {t[s]['micro']}")
        L += [f"- Kiểm: {t['kiem']}", ""]
    c = q.get("chap")
    if c:
        L += ["## Chập", "", f"- {c['so_ban']} bản ({c['so_co_rir']} có RIR). Mức trong −26 ± 0,5 dBFS: {c['ty_le_muc_trong_0_5']}; "
              f"đỉnh > −1 dBFS: {c['dinh_tren_1dbfs']}; hạ chống cắt đỉnh: {c['so_ban_ha_chong_cat']} bản; "
              f"|lệch trễ| < 2 ms: {c['ty_le_lech_tre_duoi_2ms']} (p99 {c['lech_tre_p99_ms']} ms); "
              f"bản từ file TTS đã cắt đỉnh (clipped): {c['ban_clipped_tu_tts']}.", ""]
    e = q.get("cer")
    if e:
        L += ["## CER trước / sau RIR (bản dev, chỉ để bắt lỗi pipeline, không lọc)", "",
              "| Mô hình | n | trước | sau | số câu tăng > 0,1 | Bắc | Trung | Nam |", "|---|---|---|---|---|---|---|---|"]
        for k2, x in e.items():
            vv = x["theo_vung"]
            L.append(f"| {k2} ({x['mo_hinh']}) | {x['n']} | {x['truoc']} | {x['sau']} | {x['tang_qua_0_1']} | " +
                     " | ".join(f"{vv[r]['truoc']} → {vv[r]['sau']}" if r in vv else "-" for r in ("Bắc", "Trung", "Nam")) + " |")
        L.append("")
    L += ["## Danh sách kiểm", ""] + [f"- [{'x' if ok else ' '}] {ten}" for ten, ok in q["danh_sach"]]
    L += ["- [ ] Mô phỏng so với đo trên mô hình B0: hoãn, đã có RIR đo (kho_do) nhưng chưa có mô hình B0.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goc", required=True, help="thư mục gốc của lượt RIR (kho/, gan/, aug_v1/_reverb/, asr_dev/)")
    a = ap.parse_args()
    q, ds = {}, []
    parts = (("kho", "kho", "rir_manifest.jsonl", qa_kho), ("kho_do", "kho_do", "rir_manifest.jsonl", qa_kho_do),
             ("gan", "gan", "phan_bo.json", qa_gan),
             ("chap", os.path.join("aug_v1", "_reverb"), "manifest.jsonl", qa_chap), ("cer", "asr_dev", os.path.join("vang", "manifest.jsonl"), qa_cer))
    for key, sub, need, fn in parts:
        d = os.path.join(a.goc, sub)
        q[key] = fn(d) if os.path.exists(os.path.join(d, need)) else None
    if q["kho"]:
        k = q["kho"]
        ds += [("Mọi RIR đạt nằm trong dải EDT", k["edt_ngoai_dai_trong_rir_dat"] == 0),
               ("Lệch trễ trực tiếp < 1 ms", k["lech_tre_max_ms"] < C.LECH_TRE_MAX_MS),
               ("0 RIR lỗi hình dạng", not any(x in k["loai_theo_ly_do"] for x in ("khong_huu_han", "truoc_dinh", "duoi_khong_tat"))),
               ("Train/dev không chung khoang", not k["train_dev_chung_khoang"]), ("Không khoang thất bại", not k["khoang_that_bai"])]
    if q["kho_do"]:
        ds.append(("Kho đo: xe dev không có trong train", not q["kho_do"]["train_dev_chung_xe"]))
    if q["gan"]:
        ds += [("Tỷ lệ có RIR 0,8 ± 0,02 mỗi split", q["gan"]["rir_trong_0_8"]),
               ("Tỷ lệ vùng lệch ≤ 2 điểm so với tập đã lọc v1", q["gan"]["vung_lech_le_2"]),
               ("Kiểm bảng gán (dev không dùng RIR/khoang train, hai bản khác RIR, câu ghép cùng split/khoang)", q["gan"]["kiem_dat"])]
    if q["chap"]:
        c = q["chap"]
        ds += [("Mức −26 ± 0,5 dBFS ở ≥ 99% bản", c["ty_le_muc_trong_0_5"] >= 0.99), ("Không bản nào đỉnh > −1 dBFS", c["dinh_tren_1dbfs"] == 0),
               ("|Lệch trễ| < 2 ms ở ≥ 99% bản có RIR", c["ty_le_lech_tre_duoi_2ms"] >= 0.99)]
    if q["cer"]:
        ds.append(("Đã đo CER trước/sau RIR (L, M, T)", set(q["cer"]) == set(ASR_TAGS)))
    q["danh_sach"] = ds
    out = os.path.join(a.goc, "qa")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "qa.json"), "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "qa.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md(q))
    print(md(q))


if __name__ == "__main__":
    main()
