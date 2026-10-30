# -*- coding: utf-8 -*-
"""QA bước trộn nhiễu giai đoạn 1 và bảng phản ứng của ASR (docs/ke_hoach_nhieu_v1.md). Chỉ cần numpy.

Chạy (từ tts_gen/):  python -m phantich.nhieu_qa --goc runs/nhieu_v1 --asr-goc runs/rir_v2/asr_dev
Đọc gan/phan_bo.json, aug_v1/manifest.jsonl, asr_dev/nhieu, asr_luoi (asr_gate_<tag>.csv, cer_min) và mốc "sạch"/"chỉ
vang" của bước RIR (<asr-goc>/{sach,vang}: cùng 500 bản). Ghi <goc>/qa/qa.json, qa.md. CER là trung bình cer_min.
Kiểm hợp lý tính: trong mỗi preset, CER không được giảm khi SNR giảm (dung sai 0,005).
"""
import argparse
import collections
import json
import os

import numpy as np

import cauhinh.nhieu as N
from phantich.rir_qa import ASR_TAGS, doc_gate

DUNG_SAI = 0.005


def doc_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def tb(v):
    v = [x for x in v if x is not None]
    return round(float(np.mean(v)), 4) if v else None


def qa_tron(goc):
    man = doc_jsonl(os.path.join(goc, "aug_v1", "manifest.jsonl"))
    lech = np.array([abs(m["snr_do_db"] - m["snr_db"]) for m in man])
    return dict(so_ban=len(man), snr_lech_max_db=round(float(lech.max()), 3), snr_lech_qua_0_5=int((lech > 0.5).sum()),
                ha_chong_cat=int(sum(m["ha_chong_cat_db"] < 0 for m in man)),
                dinh_max_dbfs=round(max(m["dinh_ra_dbfs"] for m in man), 2),
                kenh_khop=round(sum(m["kenh_khop"] for m in man) / len(man), 4),
                preset={sp: dict(collections.Counter(m["preset_moi_truong"] for m in man if m["split"] == sp))
                        for sp in ("train", "dev")})


def qa_cer(goc, asr_goc):
    out = {}
    luoi_man = doc_jsonl(os.path.join(goc, "asr_luoi", "manifest.jsonl"))
    nh_man = doc_jsonl(os.path.join(goc, "asr_dev", "nhieu", "manifest.jsonl"))
    for k, tag in ASR_TAGS.items():
        ps = [os.path.join(asr_goc, "sach", f"asr_gate_{tag}.csv"), os.path.join(asr_goc, "vang", f"asr_gate_{tag}.csv"),
              os.path.join(goc, "asr_dev", "nhieu", f"asr_gate_{tag}.csv"), os.path.join(goc, "asr_luoi", f"asr_gate_{tag}.csv")]
        if not all(os.path.exists(p) for p in ps):
            continue
        s, v, nh, lu = (doc_gate(p) for p in ps)
        utts = [m["utt_id"] for m in nh_man]
        luoi = collections.defaultdict(list)
        vung = collections.defaultdict(list)
        micro = collections.defaultdict(list)
        for m in luoi_man:
            c = lu.get(m["utt_id"])
            luoi[(m["preset_moi_truong"], m["snr_dat_db"])].append(c)
            vung[(m.get("voice_region") or m["speaker_region"], m["snr_dat_db"])].append(c)
            micro[(m.get("micro") or "khong_rir", m["snr_dat_db"])].append(c)
        bang = {p: {str(snr): tb(luoi[(p, snr)]) for snr in N.SNR_LUOI} for p in N.PRESET_GD1}
        don_dieu = {p: all((bang[p][str(b)] or 0) >= (bang[p][str(a)] or 0) - DUNG_SAI
                           for a, b in zip(N.SNR_LUOI, N.SNR_LUOI[1:])) for p in N.PRESET_GD1}
        nh_preset = collections.defaultdict(list)
        for m in nh_man:
            nh_preset[m["preset_moi_truong"]].append(nh.get(m["utt_id"]))
        out[k] = dict(mo_hinh=tag, n=len(utts), sach=tb([s.get(u) for u in utts]), chi_vang=tb([v.get(u) for u in utts]),
                      bo_sinh_ra=tb([nh.get(u) for u in utts]), bo_sinh_ra_theo_preset={p: tb(x) for p, x in sorted(nh_preset.items())},
                      luoi=bang, luoi_tb_theo_snr={str(snr): tb([c for p in N.PRESET_GD1 for c in luoi[(p, snr)]]) for snr in N.SNR_LUOI},
                      luoi_theo_vung={f"{a}|{b}": tb(x) for (a, b), x in sorted(vung.items())},
                      luoi_theo_micro={f"{a}|{b}": tb(x) for (a, b), x in sorted(micro.items())},
                      so_o_luoi=len(luoi_man), don_dieu=don_dieu)
    return out


def md(q):
    L = ["# QA trộn nhiễu giai đoạn 1 (6 preset CAVEMOVE có nhãn)", ""]
    t = q["tron"]
    L += ["## Trộn", "",
          f"- {t['so_ban']} bản; SNR đo lệch SNR đặt tối đa {t['snr_lech_max_db']} dB ({t['snr_lech_qua_0_5']} bản lệch > 0,5 dB); "
          f"hạ chống cắt đỉnh {t['ha_chong_cat']} bản; đỉnh tối đa {t['dinh_max_dbfs']} dBFS; kênh đúng vị trí micro {t['kenh_khop']:.1%}.",
          f"- Preset train {t['preset']['train']}; dev {t['preset']['dev']}.", "",
          "## Bảng gán", "", f"- Kiểm: {q['gan']['kiem']}", ""]
    for k, c in q["cer"].items():
        L += [f"## CER {k} ({c['mo_hinh']}), {c['n']} bản dev", "",
              f"Mốc: sạch {c['sach']}, chỉ vang {c['chi_vang']}, bộ sinh ra (SNR ngẫu nhiên) {c['bo_sinh_ra']}.", "",
              "| Preset | " + " | ".join(f"SNR {s} dB" for s in N.SNR_LUOI) + " | đơn điệu |",
              "|---|" + "---|" * (len(N.SNR_LUOI) + 1)]
        for p in N.PRESET_GD1:
            L.append(f"| {p} | " + " | ".join(str(c["luoi"][p][str(s)]) for s in N.SNR_LUOI) + f" | {'đạt' if c['don_dieu'][p] else 'TRƯỢT'} |")
        L.append("| trung bình | " + " | ".join(str(c["luoi_tb_theo_snr"][str(s)]) for s in N.SNR_LUOI) + " | |")
        L.append("")
    L += ["## Danh sách kiểm", ""]
    for ten, ok in q["danh_sach"]:
        L.append(f"- [{'x' if ok else ' '}] {ten}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goc", required=True)
    ap.add_argument("--asr-goc", required=True)
    a = ap.parse_args()
    with open(os.path.join(a.goc, "gan", "phan_bo.json"), encoding="utf-8") as f:
        gan = json.load(f)
    q = dict(gan=gan, tron=qa_tron(a.goc), cer=qa_cer(a.goc, a.asr_goc))
    q["danh_sach"] = [
        ("Bảng gán đạt mọi phép kiểm", all(v for v in gan["kiem"].values() if isinstance(v, bool))),
        ("SNR đo lệch SNR đặt ≤ 0,5 dB ở mọi bản", q["tron"]["snr_lech_qua_0_5"] == 0),
        ("Không bản nào đỉnh > −1 dBFS", q["tron"]["dinh_max_dbfs"] <= N.DINH_MAX_DBFS + 1e-6),
        ("Đã đo CER đủ 3 mô hình", set(q["cer"]) == set(ASR_TAGS)),
        ("CER tăng khi SNR giảm ở mọi preset, mọi mô hình", all(all(c["don_dieu"].values()) for c in q["cer"].values())),
    ]
    os.makedirs(os.path.join(a.goc, "qa"), exist_ok=True)
    with open(os.path.join(a.goc, "qa", "qa.json"), "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)
    s = md(q)
    with open(os.path.join(a.goc, "qa", "qa.md"), "w", encoding="utf-8") as f:
        f.write(s)
    print(s)


if __name__ == "__main__":
    main()
