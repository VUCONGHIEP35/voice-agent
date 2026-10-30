# -*- coding: utf-8 -*-
"""Gán giọng VieNeu cho cả 10.000 câu v3.1 và chia 10 phần p01..p10 để sinh TTS trên A100 (kế hoạch chốt 25/10/2026).

Chạy (từ tts_gen/):  python -m buoc.chon_cau_10k [--src ../data/m1m2_10k_v31] [--out full10k] [--tts-lexicon lexicon/doc_tu_ngoai_tts.tsv]
Dùng lại từ buoc/chon_cau_eval1000.py: bảng 24 giọng (VOICES, VOICE_SUB_REGION; Minh Triết bị loại), is_loan, loan_names,
load_tts_lexicon, apply_tts_lexicon, check_voice_table, h32.
- Giọng: trong mỗi vùng, xoay vòng có trọng số mượt (smooth weighted round robin) trên vòng xen kẽ nữ/nam; câu xếp theo
  (độ dài, case, có từ ngoại, băm) nên mỗi giọng nhận cùng phân bố độ dài và case. Giọng đọc nhanh (Thùy Dung, Thanh Bình,
  Hải Đăng: 5,5–5,7 âm tiết/giây ở eval1000) trọng số 0,5.
- Từ ngoại: câu có tên Latin chưa duyệt chia đôi trong mỗi giọng: phien_am (tts_text theo từ điển đọc) / giu_latin.
  text_raw và text_spoken giữ nguyên ở cả hai nhánh (người dùng chọn 50/50, 25/10).
- Phần: trong mỗi giọng chia vòng tròn 10 phần, lệch pha theo giọng -> mỗi phần cân vùng và giọng.
Ghi <out>/all_10k.jsonl, <out>/shard_pXX.jsonl, <out>/phan_bo.md. Cùng --seed thì luôn ra cùng kết quả.
"""
import argparse
import collections
import glob
import itertools
import json
import os

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from cauhinh.giong import VOICE_WEIGHT, EXCLUDED, VOICE_SUB_REGION, VOICES  # noqa: E402
from thuvien.chon_cau import LEN_ORDER, apply_tts_lexicon, check_voice_table, h32, is_loan, load_tts_lexicon, loan_names  # noqa: E402

V31 = os.path.join(os.path.dirname(HERE), "data", "m1m2_10k_v31")
N_SHARDS = 10


def ring_for(region):
    fem = sorted(v for v, m in VOICES.items() if m[0] == region and m[1] == "female")
    mal = sorted(v for v, m in VOICES.items() if m[0] == region and m[1] == "male")
    return [x for pair in itertools.zip_longest(fem, mal) for x in pair if x]


def smooth_wrr(ring, weights, n):
    """Dãy n giọng theo xoay vòng có trọng số mượt (nginx): tỷ lệ đúng trọng số, rải đều, tất định."""
    cur = {v: 0.0 for v in ring}
    total = sum(weights[v] for v in ring)
    out = []
    for _ in range(n):
        for v in ring:
            cur[v] += weights[v]
        best = max(ring, key=lambda v: (cur[v], -ring.index(v)))
        cur[best] -= total
        out.append(best)
    return out


def assign(rows, seed, lex):
    """Trả danh sách dòng đã có voice, voice_*, loan_arm, tts_text, shard."""
    weights = {v: VOICE_WEIGHT.get(v, 1.0) for v in VOICES}
    out = []
    for reg in sorted({r["speaker_region"] for r in rows}):
        ring = ring_for(reg)
        if not ring:
            raise SystemExit(f"Vùng {reg} không có giọng")
        rs = sorted((r for r in rows if r["speaker_region"] == reg),
                    key=lambda r: (LEN_ORDER[r["length_class"]], r["case_id"], is_loan(r), h32(seed, "v", r["sample_id"])))
        for r, v in zip(rs, smooth_wrr(ring, weights, len(rs))):
            out.append(dict(r, voice=v))
    by_voice = collections.defaultdict(list)
    for r in out:
        by_voice[r["voice"]].append(r)
    final, missing = [], collections.Counter()
    for vi, (v, rs) in enumerate(sorted(by_voice.items())):
        reg, gender, style, _ = VOICES[v]
        rs.sort(key=lambda r: (LEN_ORDER[r["length_class"]], r["case_id"], h32(seed, "s", r["sample_id"])))
        k_loan = 0
        for i, r in enumerate(rs):
            arm = ""
            if is_loan(r):
                arm = ("giu_latin", "phien_am")[(k_loan + h32(seed, "arm", v)) % 2]
                k_loan += 1
            r = dict(r, voice_gender=gender, voice_style=style, voice_region=reg, voice_sub_region=VOICE_SUB_REGION.get(v, ""),
                     giong_khop_tieu_vung=(None if reg != "Trung" or r.get("residence") != "Quê"
                                           else r.get("sub_region") == VOICE_SUB_REGION.get(v)),
                     loan_arm=arm, loan_names=loan_names(r), shard=f"p{(i + vi) % N_SHARDS + 1:02d}", tts_text="", pron_variant="")
            if arm == "phien_am" and lex is not None:
                t, used = apply_tts_lexicon(r["text_spoken"], reg, lex)
                done = {u.split("=", 1)[0] for u in used}
                for nm in r["loan_names"]:
                    if nm.lower() not in done and nm.lower() in r["text_spoken"].lower():
                        missing[nm] += 1
                if used:
                    r.update(tts_text=t, pron_variant="; ".join(used))
            final.append(r)
    final.sort(key=lambda r: (r["shard"], r["speaker_region"], r["voice"], LEN_ORDER[r["length_class"]], r["sample_id"]))
    for i, r in enumerate(final):
        r["eval_idx"] = i
    return final, missing


def report(final, path, missing):
    L = ["# Phân bổ 10.000 câu v3.1 cho TTS (buoc/chon_cau_10k.py)", "",
         f"Tổng {len(final)} câu; {len({r['voice'] for r in final})} giọng; trọng số 0,5: {', '.join(VOICE_WEIGHT)}.", ""]
    L += ["## Theo giọng", "", "| Giọng | Vùng | Giới | Số câu | phien_am | giu_latin | có tts_text |", "|---|---|---|---|---|---|---|"]
    for v in sorted({r["voice"] for r in final}, key=lambda v: (VOICES[v][0], v)):
        rs = [r for r in final if r["voice"] == v]
        L.append(f"| {v} | {VOICES[v][0]} | {VOICES[v][1]} | {len(rs)} | {sum(r['loan_arm'] == 'phien_am' for r in rs)} | "
                 f"{sum(r['loan_arm'] == 'giu_latin' for r in rs)} | {sum(bool(r['tts_text']) for r in rs)} |")
    L += ["", "## Theo phần", "", "| Phần | Số câu | Bắc | Trung | Nam | Số giọng |", "|---|---|---|---|---|---|"]
    for s in sorted({r["shard"] for r in final}):
        rs = [r for r in final if r["shard"] == s]
        c = collections.Counter(r["speaker_region"] for r in rs)
        L.append(f"| {s} | {len(rs)} | {c['Bắc']} | {c['Trung']} | {c['Nam']} | {len({r['voice'] for r in rs})} |")
    if missing:
        L += ["", f"Tên ngoại chưa có trong từ điển đọc (nhánh phien_am vẫn đọc chữ Latin): {dict(missing)}"]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=V31)
    ap.add_argument("--out", default=os.path.join(HERE, "full10k"))
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--tts-lexicon", default=os.path.join(HERE, "lexicon", "doc_tu_ngoai_tts.tsv"))
    ap.add_argument("--voices-json", default=None)
    a = ap.parse_args()
    if set(VOICES) & set(EXCLUDED):
        raise SystemExit(f"Giọng bị loại vẫn có trong bảng: {set(VOICES) & set(EXCLUDED)}")
    check_voice_table(a.voices_json)
    rows = []
    for p in sorted(glob.glob(os.path.join(a.src, "0*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    if len({r["sample_id"] for r in rows}) != len(rows):
        raise SystemExit("sample_id trùng trong bộ nguồn")
    lex = load_tts_lexicon(a.tts_lexicon) if a.tts_lexicon else None
    final, missing = assign(rows, a.seed, lex)
    os.makedirs(a.out, exist_ok=True)

    def dump(path, items):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in items:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump(os.path.join(a.out, "all_10k.jsonl"), final)
    for s in sorted({r["shard"] for r in final}):
        dump(os.path.join(a.out, f"shard_{s}.jsonl"), [r for r in final if r["shard"] == s])
    report(final, os.path.join(a.out, "phan_bo.md"), missing)
    print(f"Ghi {len(final)} câu -> {a.out}: " + ", ".join(f"{s} {n}" for s, n in sorted(collections.Counter(r['shard'] for r in final).items())))
    if missing:
        print("Chưa có trong từ điển đọc:", dict(missing))


if __name__ == "__main__":
    main()
