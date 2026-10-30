"""phantich/kiem_van_ban.py - quet bo cau TRUOC khi sinh TTS de tim cac tu de bi doc/nghe sai.

Chi phi ty le voi so tu KHAC NHAU, khong phai so cau: 10.000 cau thuong chi co vai tram tu
ngoai lai / ten rieng, nen lap tu dien bien the doc va thu rieng tung tu la kha thi.

Dau vao: JSONL bo cau (mac dinh cot text_spoken, text_raw, speaker_region).
Dau ra (--out):
  foreign_tokens.csv   tu khong phai am tiet tieng Viet hop le: so cau, vung, cau vi du  -> ung vien lexicon
  proper_names.csv     cum viet hoa giua cau trong text_raw (dia danh, thuong hieu)     -> ung vien thu rieng
  dialect_tokens.csv   tu dia phuong co trong danh sach
  spelled_runs.csv     chuoi ten chu cai (vd 'em pê ba')
  length_stats.txt     phan bo so am tiet, so cau <= 3 am tiet theo vung
  lexicon_template.tsv khung tu dien bien the de dien tay (dang chuan<TAB>bien the 1|bien the 2)
                       --bang review/BANG_tu_ngoai_lai.csv: dien san cac cach doc trong bang (doc qua
                       gen10k/loanwords10k.py); day la de xuat K1 CHUA DUYET, chi dung de cham ASR,
                       khong dung lam text_spoken. Tu ngoai khong co trong bang giu cot bien the rong.
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thuvien.van_ban import DIALECT_EQUIV, is_spelled_run, is_viet_syllable, norm_text  # noqa: E402

WORD = re.compile(r"\w+|[.!?]")


def capital_runs(raw):
    """Cum tu viet hoa lien tiep khong o dau cau (dia danh, thuong hieu, ten playlist...)."""
    toks = WORD.findall(raw)
    runs, cur, start = [], [], True
    for t in toks:
        if t in ".!?":
            if cur:
                runs.append(cur)
            cur, start = [], True
            continue
        cap = t[0].isupper() or (cur and t[0].isdigit())
        if cap and not start:
            cur.append(t)
        else:
            if cur:
                runs.append(cur)
            cur = []
        start = False
    if cur:
        runs.append(cur)
    return [" ".join(r) for r in runs]


def bang_lexicon(path):
    """Dong lexicon tu bang tu ngoai: dang chuan = cach doc hien tai trong text_spoken (neu bang ghi) hoac chu viet;
    bien the = chu viet + cac cach doc de xuat. Tra (dong, sha256 bang, tap token da co trong bang)."""
    os.environ["BANG_TU_NGOAI"] = os.path.abspath(path)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gen10k"))
    import loanwords10k  # doc bang luc import, dung lai cach tach nhieu tu va _clean_reading cua bo sinh
    lines, seen, covered = [], set(), set()
    for e in loanwords10k.ENTRIES:
        canon = norm_text(e["current"] or e["term"])
        vars_ = []
        for v in [e["term"]] + e["readings"]:
            v = norm_text(v)
            if v and v != canon and v not in vars_:
                vars_.append(v)
        if not vars_ or canon in seen:
            continue
        seen.add(canon)
        covered.update(canon.split())
        lines.append(f"{canon}\t{'|'.join(vars_)}\n")
    return lines, loanwords10k.CSV_SHA, covered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--text-key", default="text_spoken")
    ap.add_argument("--raw-key", default="text_raw")
    ap.add_argument("--region-key", default="speaker_region")
    ap.add_argument("--out", default="text_audit")
    ap.add_argument("--bang", default=None, help="review/BANG_tu_ngoai_lai.csv: dien san bien the doc vao lexicon_template.tsv")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    bang_lines, bang_sha, covered = bang_lexicon(a.bang) if a.bang else ([], None, set())

    foreign = collections.defaultdict(lambda: {"n": 0, "reg": collections.Counter(), "ex": ""})
    names = collections.defaultdict(lambda: {"n": 0, "ex": ""})
    dialect = collections.Counter()
    spelled = collections.Counter()
    lens = collections.defaultdict(list)
    with open(a.jsonl, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            txt = d.get(a.text_key, "")
            reg = d.get(a.region_key, "?")
            toks = norm_text(txt).split()
            lens[reg].append(len(toks))
            for i, t in enumerate(toks):
                if not is_viet_syllable(t):
                    e = foreign[t]
                    e["n"] += 1
                    e["reg"][reg] += 1
                    e["ex"] = e["ex"] or txt
                if t in DIALECT_EQUIV:
                    dialect[(t, reg)] += 1
            i = 0
            while i < len(toks):
                if is_spelled_run(toks, i):
                    j = i
                    while j < len(toks) and is_spelled_run(toks, j):
                        j += 1
                    spelled[" ".join(toks[i:j])] += 1
                    i = j
                else:
                    i += 1
            raw = d.get(a.raw_key, "") or txt
            for nm in capital_runs(raw):
                if len(nm) > 1:
                    e = names[nm]
                    e["n"] += 1
                    e["ex"] = e["ex"] or raw

    with open(os.path.join(a.out, "foreign_tokens.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["token", "so_cau", "theo_vung", "cau_vi_du"])
        for t, e in sorted(foreign.items(), key=lambda x: -x[1]["n"]):
            w.writerow([t, e["n"], dict(e["reg"]), e["ex"]])
    with open(os.path.join(a.out, "proper_names.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["cum_viet_hoa", "so_cau", "cau_vi_du"])
        for t, e in sorted(names.items(), key=lambda x: -x[1]["n"]):
            w.writerow([t, e["n"], e["ex"]])
    with open(os.path.join(a.out, "dialect_tokens.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["tu", "vung", "so_lan"])
        for (t, r), n in dialect.most_common():
            w.writerow([t, r, n])
    with open(os.path.join(a.out, "spelled_runs.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["chuoi", "so_lan"])
        for t, n in spelled.most_common():
            w.writerow([t, n])
    with open(os.path.join(a.out, "lexicon_template.tsv"), "w", encoding="utf-8") as f:
        f.write("# dang chuan trong nhan<TAB>bien the doc 1|bien the doc 2 (viet bang am tiet tieng Viet)\n")
        if bang_lines:
            f.write(f"# tu {a.bang} (sha256 {bang_sha[:12]}): cach doc de xuat K1, CHUA DUYET - chi dung de cham ASR\n")
            f.writelines(bang_lines)
            f.write("# tu ngoai chua co trong bang: dien tay\n")
        for t, e in sorted(foreign.items(), key=lambda x: -x[1]["n"]):
            if t not in covered:
                f.write(f"{t}\t\n")
    lines = []
    for r, xs in sorted(lens.items()):
        xs.sort()
        short = sum(1 for x in xs if x <= 3)
        lines.append(f"{r}: {len(xs)} cau, trung vi {xs[len(xs)//2]} am tiet, "
                     f"<=3 am tiet: {short} ({short/len(xs):.0%})")
    lines.append(f"Tu ngoai lai khac nhau: {len(foreign)} | cum viet hoa khac nhau: {len(names)} | "
                 f"chuoi danh van khac nhau: {len(spelled)}")
    with open(os.path.join(a.out, "length_stats.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
