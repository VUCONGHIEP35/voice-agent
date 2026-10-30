# -*- coding: utf-8 -*-
"""Lỗi ASR theo vị trí từ trong câu (đầu / giữa / cuối): kiểm xem mô hình có hay sai/mất TỪ ĐẦU không.

Chạy (từ tts_gen/):
  .venv/Scripts/python -m phantich.vi_tri_loi runs/ket_qua_B/runs/ket_qua_A/runs/eval1000_A runs/ket_qua_B/runs/eval1000_B \
      --gate-name gate_hop_server --lexicon lexicon/asr_bien_the.tsv --out reports/vi_tri_loi_AB.md
Mỗi dòng hiện hành (eval_common.active_rows) và mỗi cấu hình có hyp trong <gate>.csv: lấy biến thể đáp án khớp nhất
(asr_check.best_cer), gộp từ địa phương (asr_check.equiv), căn hàng theo từ (Levenshtein có truy vết). Một từ đáp án là
"sai" nếu bị thay hoặc bị mất. Báo tỷ lệ sai ở từ đầu, từ giữa, từ cuối; riêng "mất từ đầu" (xóa ở vị trí 0); theo vùng,
theo cấu hình, theo mức 5 ms đầu (head_db trong manifest: > -40 dBFS là tín hiệu cắt đầu). Chỉ câu >= 3 từ.
Lượt có manifest và tệp chấm ở hai thư mục khác nhau: viết "<thư mục manifest>::<thư mục chứa tệp chấm>".
"""
import argparse
import collections
import csv
import os
from thuvien.can_hang import word_states  # noqa: E402

from thuvien.cham_chu import norm  # noqa: E402
from thuvien.van_ban import load_lexicon  # noqa: E402
from thuvien.manifest import active_rows, load_manifest  # noqa: E402

CONFIGS = ("L", "M", "c3", "Z", "T")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--gate-name", default="gate_hop_server")
    ap.add_argument("--lexicon", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    # cnt[(nhóm, cấu hình)][vị trí] = [số từ, số sai, số mất]
    cnt = collections.defaultdict(lambda: {p: [0, 0, 0] for p in ("dau", "giua", "cuoi")})
    first_examples = collections.Counter()
    for spec in a.runs:
        run, gate_dir = spec.split("::", 1) if "::" in spec else (spec, spec)
        man = {m["utt_id"]: m for m in active_rows(load_manifest(run))}
        with open(os.path.join(gate_dir, f"{a.gate_name}.csv"), encoding="utf-8-sig") as f:
            gate = list(csv.DictReader(f))
        for g in gate:
            m = man.get(g["utt_id"])
            if m is None or g["tts_check"] != "dat":
                continue
            head_db = m.get("head_db")
            head = "dau>-40dB" if head_db is not None and head_db > -40 else "dau_im"
            for c in CONFIGS:
                hyp = g.get(f"hyp_{c}")
                if hyp is None or hyp == "":
                    continue
                st = word_states(m, hyp, lex)
                if len(st) < 3:
                    continue
                for grp in ("Tất cả", g["region"], head):
                    for k in (c, "mọi"):
                        box = cnt[(grp, k)]
                        for i, s in enumerate(st):
                            p = "dau" if i == 0 else ("cuoi" if i == len(st) - 1 else "giua")
                            box[p][0] += 1
                            box[p][1] += s != "ok"
                            box[p][2] += s == "del"
                if c in ("L", "M") and st[0] != "ok":
                    first_examples[(norm(m["text_spoken"]).split() or ["?"])[0]] += 1
    rate = lambda x: f"{x[1] / x[0]:.1%}" if x[0] else "—"
    L = ["# Lỗi ASR theo vị trí từ (chỉ câu tts_check đạt, >= 3 từ; 'sai' = bị thay hoặc mất)", "",
         f"Lượt: {', '.join(a.runs)}; tệp chấm: {a.gate_name}.csv", "",
         "| Nhóm | Cấu hình | Từ đầu: sai | Từ đầu: MẤT | Từ giữa: sai | Từ cuối: sai | Đầu / giữa |", "|---|---|---|---|---|---|---|"]
    order = ["Tất cả", "Bắc", "Trung", "Nam", "dau_im", "dau>-40dB"]
    for grp in order:
        for k in ("mọi",) + CONFIGS:
            b = cnt.get((grp, k))
            if not b or not b["dau"][0]:
                continue
            ratio = (b["dau"][1] / b["dau"][0]) / (b["giua"][1] / b["giua"][0]) if b["giua"][1] else float("nan")
            L.append(f"| {grp} | {k} | {rate(b['dau'])} ({b['dau'][1]}/{b['dau'][0]}) | "
                     f"{b['dau'][2] / b['dau'][0]:.1%} | {rate(b['giua'])} | {rate(b['cuoi'])} | {ratio:.1f}× |")
    L += ["", "Từ đầu câu hay bị L/M nghe sai nhất (từ đáp án: số lần):",
          ", ".join(f"{w}: {n}" for w, n in first_examples.most_common(15))]
    txt = "\n".join(L) + "\n"
    print(txt)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)


if __name__ == "__main__":
    main()
