# -*- coding: utf-8 -*-
"""So các lượt sinh lại pilot100 theo kiểu số (bf16 laptop / fp16 T4 / fp32 T4) trên cùng các sample_id.

Chạy (từ tts_gen/):
  python -m luutru.compare_dtype bf16_laptop=runs/pilot100 fp16_t4=runs/pilot100_t4_fp16 fp32_t4=runs/pilot100_t4_fp32 \
      --lexicon reports/text_audit_pilot100/lexicon_template.tsv --out runs/so_sanh_kieu_so.md
Mỗi lượt cần manifest.jsonl, asr_PhoWhisper-medium.jsonl, asr_PhoWhisper-large-ct2-int8.jsonl. tts_check lấy trong
manifest; lượt cũ không có thì đọc <run>/tts_check_bf16_laptop.jsonl (tính sẵn trên laptop từ âm thanh).
Chỉ số theo vùng: tỷ lệ cắt đầu (lần sinh đầu; lượt T4 chạy --max-retry 0), trung vị âm tiết/giây, CER trung bình của
L (large CT2) và M (medium) so với đáp án (asr_check.answer_variants + từ điển), số câu theo kết quả chấm L+M
(gate_union.judge, ngưỡng TẠM 0,10), và số câu đổi kết quả chấm so với lượt đầu tiên.
"""
import argparse
import collections
import os
import statistics

from thuvien.cham_chu import answer_variants, best_cer  # noqa: E402
from thuvien.van_ban import load_lexicon  # noqa: E402
from thuvien.manifest import active_rows, load_jsonl, load_manifest  # noqa: E402
from thuvien.luat_cham import judge  # noqa: E402

REGIONS = ("Bắc", "Trung", "Nam")
FILES = {"L": "asr_PhoWhisper-large-ct2-int8.jsonl", "M": "asr_PhoWhisper-medium.jsonl"}
VERDICTS = ("dat", "dat_1nguon", "can_nghe", "loai", "sinh_lai")


def load(run, lex, thr):
    rows = {m["sample_id"]: m for m in active_rows(load_manifest(run))}
    tc_file = os.path.join(run, "tts_check_bf16_laptop.jsonl")
    tc = {d["utt_id"]: d["tts_check"] for d in load_jsonl(tc_file)} if os.path.exists(tc_file) else {}
    hyps = {}
    for c, fn in FILES.items():
        p = os.path.join(run, fn)
        hyps[c] = {d["utt_id"]: d["hyp"] for d in load_jsonl(p)} if os.path.exists(p) else {}
    out = {}
    for sid, m in rows.items():
        check = m.get("tts_check") or tc.get(m["utt_id"], "dat")
        var = answer_variants(m, lex)
        cers = {c: best_cer(var, hyps[c][m["utt_id"]])[0] for c in FILES if m["utt_id"] in hyps[c]}
        nt = {c: best_cer(var, hyps[c][m["utt_id"]], tone=False)[0] for c in FILES if m["utt_id"] in hyps[c]}
        v, _, _ = judge(m, cers, nt, check, thr)
        out[sid] = dict(region=m.get("voice_region") or m["speaker_region"], voice=m["voice"], check=check,
                        rate=m.get("rate_syl_per_s"), cers=cers, verdict=v, n_syl=m["n_syllables"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="tên=thư mục, lượt đầu là mốc")
    ap.add_argument("--lexicon", action="append", default=[])
    ap.add_argument("--thr", type=float, default=0.10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    named = [x.split("=", 1) for x in a.runs]
    data = {n: load(p, lex, a.thr) for n, p in named}
    common = set.intersection(*(set(d) for d in data.values()))
    base = named[0][0]
    voice_diff = sum(len({data[n][s]["voice"] for n, _ in named}) > 1 for s in common)
    L = [f"# So kiểu số trên pilot100 ({len(common)} câu chung; mốc: {base})", "",
         f"Giọng khác nhau giữa các lượt ở cùng câu: {voice_diff} (phải là 0). Ngưỡng chấm TẠM {a.thr}, chấm bằng L+M.", ""]
    head = ["Lượt", "Vùng", "n", "cắt đầu", "âm tiết/giây (trung vị)", "CER L TB", "CER M TB", *VERDICTS, "đổi kết quả so với mốc"]
    L += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for n, _ in named:
        d = data[n]
        for reg in REGIONS + (None,):
            ids = sorted(s for s in common if reg is None or d[s]["region"] == reg)
            if not ids:
                continue
            cut = sum("cat_dau" in d[s]["check"] for s in ids)
            rates = [d[s]["rate"] for s in ids if d[s]["rate"]]
            mean = lambda c: (lambda xs: f"{sum(xs) / len(xs):.3f}" if xs else "—")([d[s]["cers"][c] for s in ids if c in d[s]["cers"]])
            vc = collections.Counter(d[s]["verdict"] for s in ids)
            changed = sum(d[s]["verdict"] != data[base][s]["verdict"] for s in ids)
            L.append("| " + " | ".join([n, reg or "**Tất cả**", str(len(ids)), f"{cut} ({cut / len(ids):.1%})",
                                        f"{statistics.median(rates):.2f}" if rates else "—", mean("L"), mean("M"),
                                        *[str(vc[v]) for v in VERDICTS], "—" if n == base else str(changed)]) + " |")
    txt = "\n".join(L) + "\n"
    print(txt)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)


if __name__ == "__main__":
    main()
