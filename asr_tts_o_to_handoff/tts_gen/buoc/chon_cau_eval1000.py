# -*- coding: utf-8 -*-
"""Chọn 1.000 câu đánh giá (giai đoạn 2 của kế hoạch sinh TTS) và gán sẵn giọng trong 24 giọng VieNeu v3 Turbo.

Bài học từ thí điểm 100 câu được đưa vào đây:
  - Không dùng lại câu đã sinh: bỏ mọi sample_id trong runs/pilot100/manifest.jsonl và runs/minh_triet_test/ket_qua.csv.
  - Minh Triết bị loại (runs/minh_triet_test/tom_tat.md); script dừng nếu bảng giọng còn tên này.
  - Phân bổ theo tỷ lệ của bộ 10.000 câu (vùng × case × nhóm độ dài, phần dư lớn nhất) để tỷ lệ đạt đo được
    ngoại suy được cho 10.000 câu. Trong mỗi ô lấy vòng tròn theo intent để phủ intent.
  - Gán giọng trước khi chạy GPU (buoc/tts.py giữ nguyên trường "voice" có sẵn): trong mỗi vùng chia vòng tròn
    xen kẽ nữ/nam theo thứ tự (độ dài, case, có từ ngoại, băm), nên mỗi giọng nhận cùng phân bố độ dài và case.
    Ở thí điểm mỗi giọng Bắc chỉ có 2–3 câu, không đủ để đánh giá từng giọng; ở đây mỗi giọng Bắc khoảng 22 câu.
  - Câu có tên Latin chưa duyệt cách đọc ("cách đọc chưa xác minh") chia đôi trong mỗi giọng:
    loan_arm = giu_latin (TTS đọc chữ Latin như hiện tại) hoặc phien_am (TTS đọc phiên âm tiếng Việt trong tts_text).
    Nhãn ASR (text_raw) và text_spoken giữ nguyên ở cả hai nhánh.
  - Chia 2 phần A/B, mỗi giọng có mặt ở cả hai phần (thử chạy tiếp sau khi ngắt ở phần A).

Chạy (từ tts_gen/):
  python -m buoc.chon_cau_eval1000                                   # chọn + gán giọng, chưa có tts_text
  python -m buoc.chon_cau_eval1000 --tts-lexicon lexicon/doc_tu_ngoai_tts.tsv   # chạy lại sau khi có từ điển đọc
Cùng --seed thì luôn ra cùng câu, cùng giọng, cùng nhánh; --tts-lexicon chỉ điền thêm tts_text.
Ghi <out>/eval_1000.jsonl, <out>/shard_A.jsonl, <out>/shard_B.jsonl, <out>/phan_bo.md
     và <out>/tu_ngoai_can_doc.tsv (các tên Latin trong nhánh phien_am, điền sẵn đề xuất từ ../review/BANG_tu_ngoai_lai.csv
     và cảnh báo âm tiết không phải tiếng Việt; sửa tay rồi lưu thành từ điển đọc cho --tts-lexicon).

--tts-lexicon: TSV có tiêu đề  dang_trong_text_spoken<TAB>Bắc<TAB>Trung<TAB>Nam<TAB>nguon
  Mỗi ô là cách đọc viết bằng âm tiết tiếng Việt (không gạch nối; ví dụ "da lô" chứ không "za-lô", để giọng mỗi vùng
  tự áp âm vị của vùng). Ô vùng rỗng thì dùng ô vùng đầu tiên có giá trị. nguon: duyet / K1.
"""
import argparse
import collections
import csv
import glob
import itertools
import json
import os
from thuvien.chon_cau import LEN_ORDER, h32, largest_remainder, check_voice_table, is_loan, loan_names, not_vietnamese, load_tts_lexicon, load_bang, apply_tts_lexicon  # noqa: E402
from cauhinh.giong import VOICES, VOICE_SUB_REGION, EXCLUDED  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
V3 = os.path.join(os.path.dirname(HERE), "data", "m1m2_10k_v3")


def used_ids(paths):
    ids = set()
    for p in paths:
        if not os.path.exists(p):
            print(f"Không thấy {p}, bỏ qua")
            continue
        if p.endswith(".jsonl"):
            with open(p, encoding="utf-8") as f:
                ids |= {json.loads(line)["sample_id"] for line in f if line.strip()}
        else:
            with open(p, encoding="utf-8-sig") as f:
                ids |= {r["sample_id"] for r in csv.DictReader(f) if r.get("sample_id")}
    return ids


def pick_cell(rows, n, seed):
    """Lấy n câu trong một ô: vòng tròn theo intent (thứ tự băm), trong intent theo băm."""
    by_int = collections.defaultdict(list)
    for r in rows:
        by_int[r["intent_id"]].append(r)
    queues = [sorted(v, key=lambda r: h32(seed, r["sample_id"])) for _, v in
              sorted(by_int.items(), key=lambda kv: h32(seed, "intent", kv[0]))]
    out = []
    while len(out) < n and any(queues):
        for q in queues:
            if q and len(out) < n:
                out.append(q.pop(0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--out", default=os.path.join(HERE, "eval1000"))
    ap.add_argument("--exclude", nargs="*", default=[os.path.join(HERE, "runs", "pilot100", "manifest.jsonl"),
                                                       os.path.join(HERE, "runs", "minh_triet_test", "ket_qua.csv")])
    ap.add_argument("--voices-json", default=None, help="đường dẫn voices_v3_turbo.json nếu không import được vieneu")
    ap.add_argument("--tts-lexicon", default=None)
    ap.add_argument("--bang", default=os.path.join(os.path.dirname(os.path.dirname(HERE)), "review", "BANG_tu_ngoai_lai.csv"),
                    help="điền sẵn đề xuất K1 (hoặc cách đọc đã duyệt) vào tu_ngoai_can_doc.tsv")
    a = ap.parse_args()

    if set(VOICES) & set(EXCLUDED):
        raise SystemExit(f"Giọng bị loại vẫn có trong bảng: {set(VOICES) & set(EXCLUDED)}")
    check_voice_table(a.voices_json)

    rows = []
    for p in sorted(glob.glob(os.path.join(V3, "0*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    used = used_ids(a.exclude)
    pool = [r for r in rows if r["sample_id"] not in used]
    print(f"Bộ v3: {len(rows)} câu; bỏ {len(rows) - len(pool)} câu đã sinh; còn {len(pool)}")

    # 1. Phân bổ theo tỷ lệ của bộ đầy đủ (không phải của phần còn lại), để ngoại suy cho 10.000 câu
    reg_n = largest_remainder(collections.Counter(r["speaker_region"] for r in rows), a.n)
    picked = []
    for reg, n_reg in sorted(reg_n.items()):
        full = collections.Counter((r["case_id"], r["length_class"]) for r in rows if r["speaker_region"] == reg)
        tgt = largest_remainder(full, n_reg)
        cells = collections.defaultdict(list)
        for r in pool:
            if r["speaker_region"] == reg:
                cells[(r["case_id"], r["length_class"])].append(r)
        for cell, k in sorted(tgt.items()):
            got = pick_cell(cells[cell], k, a.seed)
            if len(got) < k:
                raise SystemExit(f"Ô {reg} {cell} thiếu câu: cần {k}, còn {len(got)}")
            picked += got
    assert len(picked) == a.n and len({r["sample_id"] for r in picked}) == a.n

    # 2. Gán giọng: vòng tròn xen kẽ nữ/nam trong mỗi vùng
    out = []
    for reg in sorted(reg_n):
        fem = sorted(v for v, m in VOICES.items() if m[0] == reg and m[1] == "female")
        mal = sorted(v for v, m in VOICES.items() if m[0] == reg and m[1] == "male")
        ring = [x for pair in itertools.zip_longest(fem, mal) for x in pair if x]
        if not ring:
            raise SystemExit(f"Vùng {reg} không có giọng")
        rs = sorted((r for r in picked if r["speaker_region"] == reg),
                    key=lambda r: (LEN_ORDER[r["length_class"]], r["case_id"], is_loan(r), h32(a.seed, "v", r["sample_id"])))
        for i, r in enumerate(rs):
            v = ring[i % len(ring)]
            out.append(dict(r, voice=v))

    # 3. Nhánh đọc từ ngoại và chia phần A/B, xen kẽ trong từng giọng
    lex = load_tts_lexicon(a.tts_lexicon) if a.tts_lexicon else None
    missing = collections.Counter()
    by_voice = collections.defaultdict(list)
    for r in out:
        by_voice[r["voice"]].append(r)
    final = []
    for vi, (v, rs) in enumerate(sorted(by_voice.items())):
        reg, gender, style, note = VOICES[v]
        rs.sort(key=lambda r: (LEN_ORDER[r["length_class"]], r["case_id"], h32(a.seed, "s", r["sample_id"])))
        k_loan = 0
        for i, r in enumerate(rs):
            arm = ""
            if is_loan(r):
                arm = ("giu_latin", "phien_am")[(k_loan + h32(a.seed, "arm", v)) % 2]
                k_loan += 1
            r = dict(r, voice_gender=gender, voice_style=style, voice_region=reg,
                     voice_sub_region=VOICE_SUB_REGION.get(v, ""),
                     giong_khop_tieu_vung=(None if reg != "Trung" or r["residence"] != "Quê"
                                           else r["sub_region"] == VOICE_SUB_REGION.get(v)),
                     loan_arm=arm, loan_names=loan_names(r), shard="AB"[(i + vi) % 2], tts_text="", pron_variant="")
            if arm == "phien_am" and lex is not None:
                t, used_items = apply_tts_lexicon(r["text_spoken"], reg, lex)
                done_keys = {u.split("=", 1)[0] for u in used_items}
                for nm in r["loan_names"]:
                    if nm.lower() not in done_keys and nm.lower() in r["text_spoken"].lower():
                        missing[nm] += 1
                if used_items:
                    r.update(tts_text=t, pron_variant="; ".join(used_items))
            final.append(r)
    final.sort(key=lambda r: (r["shard"], r["speaker_region"], r["voice"], LEN_ORDER[r["length_class"]], r["sample_id"]))
    for i, r in enumerate(final):
        r["eval_idx"] = i

    os.makedirs(a.out, exist_ok=True)

    def dump(path, items):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in items:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump(os.path.join(a.out, "eval_1000.jsonl"), final)
    for s in "AB":
        dump(os.path.join(a.out, f"shard_{s}.jsonl"), [r for r in final if r["shard"] == s])

    # Khung từ điển đọc cho các tên Latin trong nhánh phien_am. Tên không có nguyên dạng trong text_spoken
    # (vd 'Zing MP3' đã thành 'Zing em pê ba') ghi '?<tên>' để người lập từ điển sửa khóa cho đúng chữ trong text_spoken.
    bang = load_bang(a.bang) if a.bang and os.path.exists(a.bang) else {}
    names = collections.defaultdict(lambda: collections.Counter())
    example = {}
    for r in final:
        if r["loan_arm"] == "phien_am":
            for nm in r["loan_names"]:
                names[nm][r["speaker_region"]] += 1
                example.setdefault(nm, r["text_spoken"])
    with open(os.path.join(a.out, "tu_ngoai_can_doc.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("dang_trong_text_spoken\tBắc\tTrung\tNam\tnguon\tde_xuat_khac\tcanh_bao\tso_cau_Bac\tso_cau_Trung\tso_cau_Nam\tvi_du_text_spoken\n")
        for nm, c in sorted(names.items(), key=lambda kv: -sum(kv[1].values())):
            key = nm if nm.lower() in example[nm].lower() else "?" + nm
            b, t, n_, src, oth = bang.get(nm.lower(), ("", "", "", "", ""))
            bad = sorted({s for v in (b, t, n_) for s in not_vietnamese(v)})
            warn = ("âm tiết không phải tiếng Việt: " + " ".join(bad)) if bad else ""
            f.write(f"{key}\t{b}\t{t}\t{n_}\t{src}\t{oth}\t{warn}\t{c['Bắc']}\t{c['Trung']}\t{c['Nam']}\t{example[nm]}\n")

    write_report(a, final, rows, used, missing, lex)
    print(f"Ghi {len(final)} câu -> {a.out} (A {sum(r['shard'] == 'A' for r in final)}, B {sum(r['shard'] == 'B' for r in final)})")
    if lex is not None and missing:
        print(f"Chưa có trong từ điển đọc (nhánh phien_am vẫn đọc chữ Latin): {dict(missing)}")


def pct(x, n):
    return f"{100 * x / n:.1f}%" if n else "-"


def write_report(a, final, rows, used, missing, lex):
    L = ["# Phân bổ 1.000 câu đánh giá (giai đoạn 2)", "",
         f"Seed {a.seed}. Bỏ {len(used)} câu đã sinh ở thí điểm và kiểm tra Minh Triết. "
         f"Giọng loại: " + "; ".join(f"{k} ({v})" for k, v in EXCLUDED.items()) + ".", ""]
    N = len(rows)
    L += ["## Vùng × nhóm độ dài (so với bộ 10.000 câu)", "",
          "| Vùng | " + " | ".join(LEN_ORDER) + " | Tổng | Tỷ lệ trong 10k |", "|---|" + "---|" * (len(LEN_ORDER) + 2)]
    for reg in ("Bắc", "Trung", "Nam"):
        c = collections.Counter(r["length_class"] for r in final if r["speaker_region"] == reg)
        L.append(f"| {reg} | " + " | ".join(str(c[k]) for k in LEN_ORDER) + f" | {sum(c.values())} | "
                 f"{pct(sum(r['speaker_region'] == reg for r in rows), N)} |")
    L += ["", "## Case", "", "| Case | Chọn | Tỷ lệ chọn | Tỷ lệ trong 10k | Số intent phủ / có |", "|---|---|---|---|---|"]
    for cs in sorted({r["case_id"] for r in rows}):
        k = sum(r["case_id"] == cs for r in final)
        ints = {r["intent_id"] for r in final if r["case_id"] == cs}
        all_ints = {r["intent_id"] for r in rows if r["case_id"] == cs}
        L.append(f"| {cs} | {k} | {pct(k, len(final))} | {pct(sum(r['case_id'] == cs for r in rows), N)} | {len(ints)} / {len(all_ints)} |")
    tr = [r for r in final if r["speaker_region"] == "Trung"]
    L += ["", "## Miền Trung: tiểu vùng và nơi sống", "",
          "Cả hai giọng Trung là giọng Huế. Cột `giong_khop_tieu_vung`: True khi người nói sống ở quê và tiểu vùng là Huế; "
          "None khi sống ở Hà Nội / TP.HCM (từ theo nơi sống, giọng vẫn Trung).", "",
          "| Tiểu vùng | Nơi sống | Số câu |", "|---|---|---|"]
    for (s, res), k in sorted(collections.Counter((r["sub_region"], r["residence"]) for r in tr).items()):
        L.append(f"| {s} | {res} | {k} |")
    L.append(f"\nKhớp tiểu vùng Huế: {sum(r['giong_khop_tieu_vung'] is True for r in tr)} câu; "
             f"không khớp: {sum(r['giong_khop_tieu_vung'] is False for r in tr)}; không xét: {sum(r['giong_khop_tieu_vung'] is None for r in tr)}.")
    L += ["", "## Từng giọng", "",
          "| Giọng | Vùng | Giới | Phong cách | Câu | Rất ngắn / Ngắn / Thường / Dài | Từ ngoại (Latin / phiên âm) | A / B | Theo dõi |",
          "|---|---|---|---|---|---|---|---|---|"]
    for v, (reg, g, st, note) in sorted(VOICES.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[0])):
        rs = [r for r in final if r["voice"] == v]
        c = collections.Counter(r["length_class"] for r in rs)
        arm = collections.Counter(r["loan_arm"] for r in rs)
        sh = collections.Counter(r["shard"] for r in rs)
        L.append(f"| {v} | {reg} | {'nữ' if g == 'female' else 'nam'} | {st} | {len(rs)} | "
                 + " / ".join(str(c[k]) for k in LEN_ORDER)
                 + f" | {arm['giu_latin']} / {arm['phien_am']} | {sh['A']} / {sh['B']} | {note} |")
    by_reg_gender = collections.Counter((r["speaker_region"], r["voice_gender"]) for r in final)
    L += ["", "Tỷ lệ nam theo vùng: " + ", ".join(
        f"{reg} {pct(by_reg_gender[(reg, 'male')], by_reg_gender[(reg, 'male')] + by_reg_gender[(reg, 'female')])}"
        for reg in ("Bắc", "Trung", "Nam")) + "."]
    loan = [r for r in final if r["loan_arm"]]
    L += ["", "## Câu có tên Latin chưa duyệt cách đọc", "",
          f"{len(loan)} câu: giu_latin {sum(r['loan_arm'] == 'giu_latin' for r in loan)}, "
          f"phien_am {sum(r['loan_arm'] == 'phien_am' for r in loan)}. "
          + ("Chưa chạy với --tts-lexicon: nhánh phien_am chưa có tts_text." if lex is None else
             f"Đã điền tts_text cho {sum(bool(r['tts_text']) for r in loan)} câu; "
             f"tên chưa có trong từ điển: {dict(missing) or 'không'}."), ""]
    L += ["## Trạng thái duyệt", "", "| review_status | Chọn | Tỷ lệ trong 10k |", "|---|---|---|"]
    for k, n in collections.Counter(r["review_status"] for r in final).most_common():
        L.append(f"| {k} | {n} | {pct(sum(r['review_status'] == k for r in rows), N)} |")
    with open(os.path.join(a.out, "phan_bo.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
