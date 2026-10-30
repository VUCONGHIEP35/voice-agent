# -*- coding: utf-8 -*-
"""Báo cáo đánh giá 1.000 câu theo nhóm (việc T6; mục 8 của docs/ke_hoach_sinh_1000_cau.md). Chỉ đọc, không sửa gì.

Chạy (từ tts_gen/; chạy được với riêng phần A, và cả khi chưa có ASR):
  .venv/Scripts/python -m phantich.bao_cao runs/eval1000_A --plan eval1000_tts/eval_1000.jsonl --out reports/eval1000
Đọc mỗi lượt: manifest.jsonl (eval_common.active_rows), run_config.json, gate_hop.csv và gate_hop_tom_tat.json (nếu có),
logs/thoi_gian_asr.json (nếu có: {bước: giây}). Ghi <out>/bao_cao.md và <out>/theo_giong.csv.
Nhóm: vùng, giọng, độ dài, case, review_status, loan_arm, giong_khop_tieu_vung. Mỗi nhóm: n, co_sinh_lai (số câu phải sinh lại), số đổi giọng,
số còn lỗi kỹ thuật, số câu theo kết quả chấm, tỷ lệ dat kèm Wilson 95 %, CER trung bình câu > 3 âm tiết, trung vị âm tiết/giây.
Cờ giọng: cận trên Wilson của tỷ lệ dat < tỷ lệ chung của vùng; CER trung bình > 2 × trung vị CER của các giọng trong
vùng; từ 5 % số câu trở lên vẫn cắt đầu sau khi sinh lại.
"""
import argparse
import collections
import csv
import json
import os
import statistics

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from thuvien.manifest import active_rows, load_jsonl, load_manifest, wilson  # noqa: E402

VERDICTS = ("dat", "dat_1nguon", "can_nghe", "loai", "sinh_lai")
GROUPS = (("Vùng", "speaker_region"), ("Giọng", "voice"), ("Độ dài", "length_class"), ("Case", "case_id"),
          ("review_status", "review_status"), ("Nhánh từ ngoại", "loan_arm"), ("Giọng khớp tiểu vùng", "giong_khop_tieu_vung"))
N_10K = 10000


def load_run(run, gate_name="gate_hop"):
    man = load_manifest(run)
    act = active_rows(man)
    cfg = json.load(open(os.path.join(run, "run_config.json"), encoding="utf-8"))
    gate, summ, asr_t = {}, None, {}
    p = os.path.join(run, f"{gate_name}.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            gate = {r["sample_id"]: r for r in csv.DictReader(f)}
    p = os.path.join(run, f"{gate_name}_tom_tat.json")
    if os.path.exists(p):
        summ = json.load(open(p, encoding="utf-8"))
    p = os.path.join(run, "logs", "thoi_gian_asr.json")
    if os.path.exists(p):
        asr_t = json.load(open(p, encoding="utf-8"))
    return dict(run=run, man=man, act=act, cfg=cfg, gate=gate, summ=summ, asr_t=asr_t)


def rows_of(runs):
    """Một bản ghi gộp cho mỗi sample_id: dòng hiện hành + cờ sinh lại / đổi giọng / kết quả chấm."""
    out = []
    for R in runs:
        by_sid = collections.defaultdict(list)
        for m in R["man"]:
            by_sid[m["sample_id"]].append(m)
        for m in R["act"]:
            hist = by_sid[m["sample_id"]]
            first = hist[0]
            g = R["gate"].get(m["sample_id"], {})
            cer = None
            for k in ("cer_L", "cer_M"):
                if g.get(k) not in (None, ""):
                    cer = float(g[k])
                    break
            out.append(dict(m, _run=R["run"], _sinh_lai=bool(first.get("retries")) or first.get("attempt", 0) > 0,
                            _doi_giong=any(x.get("voice_fallback_from") for x in hist),
                            _con_loi=m.get("tts_check", "dat") != "dat",
                            _cat_dau_giong_goc=[x["voice"] for x in hist if "cat_dau" in x.get("tts_check", "")],
                            _ket_qua=g.get("ket_qua", ""), _cer=cer, _voice_goc=first["voice"]))
    return out


def stats(g):
    n = len(g)
    k = sum(r["_ket_qua"] == "dat" for r in g)
    lo, hi = wilson(k, n)
    cers = [r["_cer"] for r in g if r["_cer"] is not None and r["n_syllables"] > 3]
    rates = [r["rate_syl_per_s"] for r in g if r.get("rate_syl_per_s")]
    return dict(n=n, co_sinh_lai=sum(r["_sinh_lai"] for r in g), doi_giong=sum(r["_doi_giong"] for r in g),
                con_loi=sum(r["_con_loi"] for r in g), **{v: sum(r["_ket_qua"] == v for r in g) for v in VERDICTS},
                ty_le_dat=round(k / n, 3) if n else None, wilson_lo=round(lo, 3), wilson_hi=round(hi, 3),
                cer_tb_tren3=round(sum(cers) / len(cers), 4) if cers else None,
                am_tiet_giay_trung_vi=round(statistics.median(rates), 2) if rates else None)


def voice_flags(rows, has_asr):
    """{giọng: [lý do]} theo mục 8. Cắt đầu tính trên câu giao ban đầu cho giọng (kể cả câu sau đó đổi giọng)."""
    flags = collections.defaultdict(list)
    assigned = collections.Counter(r["_voice_goc"] for r in rows)
    cut = collections.Counter(v for r in rows for v in set(r["_cat_dau_giong_goc"]) if v == r["_voice_goc"])
    for v, n in assigned.items():
        if n and cut[v] / n >= 0.05:
            flags[v].append(f"cắt đầu sau sinh lại {cut[v]}/{n}")
    if has_asr:
        for reg in ("Bắc", "Trung", "Nam"):
            g = [r for r in rows if r["speaker_region"] == reg]
            if not g:
                continue
            p_reg = sum(r["_ket_qua"] == "dat" for r in g) / len(g)
            means = {}
            for v in sorted({r["voice"] for r in g}):
                gv = [r for r in g if r["voice"] == v]
                k = sum(r["_ket_qua"] == "dat" for r in gv)
                if wilson(k, len(gv))[1] < p_reg:
                    flags[v].append(f"tỷ lệ dat {k}/{len(gv)}, cận trên Wilson < tỷ lệ vùng {p_reg:.2f}")
                c = [r["_cer"] for r in gv if r["_cer"] is not None and r["n_syllables"] > 3]
                if c:
                    means[v] = sum(c) / len(c)
            if means:
                med = statistics.median(means.values())
                for v, mu in means.items():
                    if med > 0 and mu > 2 * med:
                        flags[v].append(f"CER TB {mu:.3f} > 2 × trung vị vùng {med:.3f}")
    return dict(flags)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--plan", required=True, help="eval_1000.jsonl (để đối chiếu số câu)")
    ap.add_argument("--out", default=os.path.join(HERE, "reports", "eval1000"))
    ap.add_argument("--gate-name", default="gate_hop", help="đọc <run>/<tên>.csv và <tên>_tom_tat.json (vd gate_hop_server)")
    a = ap.parse_args()
    runs = [load_run(r, a.gate_name) for r in a.runs]
    rows = rows_of(runs)
    plan = load_jsonl(a.plan)
    has_asr = all(R["gate"] for R in runs)
    shards = sorted({r.get("shard") for r in rows if r.get("shard")})
    plan_ids = {r["sample_id"] for r in plan if not shards or r.get("shard") in shards}
    got = [r["sample_id"] for r in rows]
    L = [f"# Báo cáo đánh giá: {', '.join(os.path.basename(r) for r in a.runs)}", ""]
    L += ["## Kiểm số câu", "",
          f"- Kế hoạch (phần {', '.join(shards) or '?'}): {len(plan_ids)} sample_id; báo cáo: {len(got)} dòng, "
          f"{len(set(got))} sample_id duy nhất.",
          f"- Thiếu so với kế hoạch: {len(plan_ids - set(got))}; thừa: {len(set(got) - plan_ids)}; "
          f"dòng manifest: {sum(len(R['man']) for R in runs)}; utt_id trùng: "
          f"{sum(len(R['man']) - len({m['utt_id'] for m in R['man']}) for R in runs)}.",
          f"- Kết quả ASR: {'có' if has_asr else 'CHƯA có (gate_hop.csv) — các cột chấm để trống'}.", ""]
    L += ["## Thời gian", ""]
    for R in runs:
        c = R["cfg"]
        L.append(f"- {os.path.basename(R['run'])}: TTS sinh {c.get('gen_wall_s')} s cho {c.get('gen_audio_s')} s âm thanh "
                 f"(RTF {c.get('rtf_overall')}), nạp mô hình cộng dồn {c.get('load_s_total', c.get('load_s'))} s, "
                 f"{len(c.get('lan_chay') or [1])} lần chạy, nghỉ vì nhiệt {c.get('cooldown_count', 0)} lần / "
                 f"{c.get('cooldown_s', 0)} s, VRAM đỉnh {c.get('vram_peak_alloc_gb')} GB.")
        for k, v in (R["asr_t"] or {}).items():
            L.append(f"  - ASR {k}: {v} s")
    n = len(rows)
    syl = sum(r["n_syllables"] for r in rows)
    wall = sum(R["cfg"].get("gen_wall_s") or 0 for R in runs)
    asr_s = sum(sum(R["asr_t"].values()) for R in runs if R["asr_t"])
    L += ["", f"Ngoại suy cho {N_10K:,} câu (tỷ lệ {N_10K / n:.1f}×, theo số câu): TTS khoảng {wall * N_10K / n / 60:.0f} phút "
          f"sinh (chưa tính nạp mô hình){f', ASR khoảng {asr_s * N_10K / n / 3600:.1f} giờ' if asr_s else ''}; "
          f"{syl} âm tiết trong {n} câu.", ""]
    if has_asr:
        cn = sum(r["_ket_qua"] == "can_nghe" for r in rows)
        L.append(f"Hàng chờ nghe ngoại suy cho {N_10K:,} câu: khoảng {cn * N_10K / n:.0f} câu (can_nghe {cn}/{n}).")
        for R in runs:
            if R["summ"]:
                L.append(f"Đóng góp biên ({os.path.basename(R['run'])}): {R['summ']['dong_gop_bien']}")
        L.append("")
    head = ["n", "co_sinh_lai", "doi_giong", "con_loi", *VERDICTS, "ty_le_dat", "wilson_lo", "wilson_hi", "cer_tb_tren3",
            "am_tiet_giay_trung_vi"]
    for title, key in GROUPS:
        groups = collections.defaultdict(list)
        for r in rows:
            groups[str(r.get(key) if r.get(key) not in (None, "") else "—")].append(r)
        L += [f"## Theo {title}", "", "| " + " | ".join([title] + head) + " |", "|" + "---|" * (len(head) + 1)]
        for k in sorted(groups):
            s = stats(groups[k])
            L.append("| " + " | ".join([k] + [str(s[h]) for h in head]) + " |")
        s = stats(rows)
        L += ["| **Tổng** | " + " | ".join(str(s[h]) for h in head) + " |", ""]
    flags = voice_flags(rows, has_asr)
    L += ["## Cờ giọng", ""] + ([f"- {v}: {'; '.join(x)}" for v, x in sorted(flags.items())] or ["- Không có."])
    if not has_asr:
        L.append("- (Chưa có ASR: mới xét được cờ cắt đầu.)")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "bao_cao.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(a.out, "theo_giong.csv"), "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["voice", "vung", *head, "co"])
        by_v = collections.defaultdict(list)
        for r in rows:
            by_v[r["voice"]].append(r)
        for v in sorted(by_v):
            s = stats(by_v[v])
            wr.writerow([v, by_v[v][0].get("voice_region") or by_v[v][0]["speaker_region"], *[s[h] for h in head],
                         "; ".join(flags.get(v, []))])
    print("\n".join(L[:12]))
    print(f"... ghi {os.path.join(a.out, 'bao_cao.md')} và theo_giong.csv")


if __name__ == "__main__":
    main()
