"""phantich/khai_thac_loi_asr.py - khai thac va phan loai loi nhan dang tren du lieu TTS tieng Viet.

Muc dich: tach CER thanh cac nguon loi khac nhau de biet cau nao TTS doc sai that,
cau nao ASR nghe sai vi giong vung / tu ngoai lai / cau qua ngan, cau nao chi lech nhan.
Chay duoc tren 100 hay 10.000 cau; chi dung thu vien chuan.

Dau vao (mot trong hai):
  --jsonl FILE   moi dong {"utt_id","ref","hyp", tuy chon "region","voice","text_raw"}
                 (doi ten cot bang --ref-key/--hyp-key/...)
  --log FILE     log dang "  0.55 <utt_id> | đọc: <ref> | nghe: <hyp>"
Dau ra (thu muc --out):
  utt_report.csv       moi cau: CER, CER bo dau thanh, CER tuong duong phuong ngu, nhan loai loi, muc uu tien nghe
  confusions.csv       cap tu bi nham (ref -> hyp), loai, so lan
  tokens_foreign.csv   tu khong phai am tiet tieng Viet hop le (ung vien tu dien phat am) va ty le nghe sai
  summary.txt          bang tong hop theo vung x loai loi
"""
import argparse
import collections
import csv
import json
import os
import re
from thuvien.van_ban import norm_text, strip_tone, tone_of, strip_all, split_syllable, is_viet_syllable, DIALECT_EQUIV, is_spelled_run, load_lexicon, ref_variants  # noqa: E402


# ---------------------------------------------------------------- can chinh tu
def align(ref, hyp):
    """Levenshtein muc tu; tra ve list (op, r, h) voi op in {'=','S','D','I'}."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                          d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1))
    i, j, ops = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            ops.append(("=" if ref[i - 1] == hyp[j - 1] else "S", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("D", ref[i - 1], ""))
            i -= 1
        else:
            ops.append(("I", "", hyp[j - 1]))
            j -= 1
    return ops[::-1]


def char_err_rate(ref, hyp):
    r, h = list(ref), list(hyp)
    if not r:
        return 0.0 if not h else 1.0
    prev = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        cur = [i] + [0] * len(h)
        for j in range(1, len(h) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r[i - 1] != h[j - 1]))
        prev = cur
    return prev[-1] / len(r)


def classify_sub(r, h):
    """Loai loi cho mot cap thay the tu."""
    if strip_tone(r) == strip_tone(h):
        return "thanh_dieu"
    if strip_all(r) == strip_all(h):
        return "dau_nguyen_am"
    sr, sh = split_syllable(r), split_syllable(h)
    if sr and sh:
        (o1, v1, f1), (o2, v2, f2) = sr, sh
        if o1 == o2 and v1 == v2 and {f1, f2} in ({"n", "ng"}, {"t", "c"}, {"nh", "n"}, {"ch", "t"}):
            return "am_cuoi_n_ng_t_c"
        if v1 == v2 and f1 == f2 and o1 != o2:
            return "phu_am_dau"
        if o1 == o2 and (v1 != v2 or f1 != f2):
            return "van"
    return "khac"


def dialect_equiv_text(tokens):
    out = []
    for t in tokens:
        out.extend(DIALECT_EQUIV.get(t, t).split())
    return out


def merger_key(t):
    """Gop n/ng, t/c o cuoi am tiet (hien tuong giong Nam) de tinh CER tuong duong."""
    s = split_syllable(t)
    if not s:
        return t
    o, v, f = s
    f = {"ng": "n", "c": "t", "nh": "n", "ch": "t"}.get(f, f)
    return o + v + f + tone_of(t)


# ---------------------------------------------------------------- doc dau vao
VOICE_REGION = {  # 25 giong san co cua v3 Turbo (voices_v3_turbo.json)
    "Adam_bua": "Bắc", "Truc_Ly": "Bắc", "Thien_Minh": "Bắc", "Mai_Anh": "Bắc", "Hai_Dang": "Bắc",
    "Thien_Tam_Duc": "Bắc", "Ngoc_Huyen": "Bắc", "Minh_Duc": "Bắc", "Pham_Tuyen": "Bắc",
    "Xuan_Vinh": "Bắc", "Thanh_Binh": "Bắc", "Ngoc_Linh": "Bắc", "Doan_Trang": "Bắc",
    "Quynh_Anh": "Bắc", "Quoc_Tuan": "Bắc", "Quang_Son": "Trung", "Ngoc_Tran": "Trung",
    "Thuy_Dung": "Nam", "Thai_Son": "Nam", "Thuc_Doan": "Nam", "Minh_Triet": "Nam",
    "My_Duyen": "Nam", "Duc_Tri": "Nam", "Kim_Thanh": "Nam", "Adam": "Nam",
}
LOG_RE = re.compile(r"^\s*([\d.]+)\s+(\S+)\s*\|\s*đọc:\s*(.*?)\s*\|\s*nghe:\s*(.*?)\s*$")


def voice_from_uttid(u):
    parts = u.split("__")
    return parts[1] if len(parts) >= 3 else ""


def load_rows(a):
    rows = []
    if a.log:
        with open(a.log, encoding="utf-8") as f:
            for line in f:
                m = LOG_RE.match(line)
                if m:
                    rows.append({"utt_id": m.group(2), "ref": m.group(3), "hyp": m.group(4)})
    else:
        opener = open(a.jsonl, encoding="utf-8")
        if a.jsonl.endswith(".csv"):
            it = csv.DictReader(opener)
        else:
            it = (json.loads(l) for l in opener if l.strip())
        for d in it:
            rows.append({"utt_id": d.get(a.id_key, ""), "ref": d.get(a.ref_key, ""),
                         "hyp": d.get(a.hyp_key, ""), "region": d.get(a.region_key, ""),
                         "voice": d.get(a.voice_key, "")})
    for r in rows:
        r.setdefault("voice", "")
        r["voice"] = r["voice"] or voice_from_uttid(r["utt_id"])
        r.setdefault("region", "")
        r["region"] = r["region"] or VOICE_REGION.get(r["voice"], "?")
    return rows


# ---------------------------------------------------------------- phan tich
def analyse(rows, short_max=3, lex=()):
    confusions = collections.Counter()
    foreign = collections.defaultdict(lambda: [0, 0])  # token -> [so lan xuat hien, so lan sai]
    out = []
    for r in rows:
        ref_t, hyp_t = norm_text(r["ref"]).split(), norm_text(r["hyp"]).split()
        ops = align(ref_t, hyp_t)
        n_syl = len(ref_t)
        tags = collections.Counter()
        err_tokens = 0
        wrong = []  # (token, flags, loai) cho moi tu tham chieu bi sai
        ri = 0
        for op, a, b in ops:
            if op == "I":
                err_tokens += 1
                tags["them_tu"] += 1
                continue
            flags = set()
            if not is_viet_syllable(a):
                flags.add("ngoai_lai")
            if a in DIALECT_EQUIV:
                flags.add("tu_dia_phuong")
            if is_spelled_run(ref_t, ri):
                flags.add("danh_van")
            if "ngoai_lai" in flags:
                foreign[a][0] += 1
                foreign[a][1] += op != "="
            if op != "=":
                err_tokens += 1
                typ = classify_sub(a, b) if op == "S" else "mat_tu"
                if op == "S":
                    confusions[(a, b, typ)] += 1
                tags[typ] += 1
                wrong.append((ri, a, flags, typ))
            ri += 1
        special = {i for i, t in enumerate(ref_t)
                   if not is_viet_syllable(t) or is_spelled_run(ref_t, i)}
        # tu thuong bi sai ngay canh tu ngoai lai/danh van: thuong do can chinh "tran" sang
        spill = {i for i in range(len(ref_t)) if (i - 1 in special or i + 1 in special)}
        plain = [(i, t) for i, a, f, t in wrong if not f and i not in spill]
        cats = set()
        if any("ngoai_lai" in f for _, _, f, _ in wrong):
            cats.add("tu_ngoai_lai")
        if any("danh_van" in f for _, _, f, _ in wrong):
            cats.add("danh_van")
        if any("tu_dia_phuong" in f for _, _, f, _ in wrong):
            cats.add("tu_dia_phuong")
        if n_syl <= short_max and err_tokens:
            cats.add("cau_ngan")
        soft = ("thanh_dieu", "am_cuoi_n_ng_t_c")
        if plain and all(t in soft for _, t in plain):
            cats.add("chi_thanh_dieu_hoac_am_cuoi")
        # tu tieng Viet thuong, khong ke can tu ngoai lai, sai ve phu am / van -> nghi TTS doc sai
        if any(t not in soft for _, t in plain):
            cats.add("loi_chung")
        ref_s, hyp_s = " ".join(ref_t), " ".join(hyp_t)
        cer = char_err_rate(ref_s, hyp_s)
        cer_notone = char_err_rate(strip_tone(ref_s), strip_tone(hyp_s))
        eq_r = " ".join(merger_key(t) for t in dialect_equiv_text(ref_t))
        eq_h = " ".join(merger_key(t) for t in dialect_equiv_text(hyp_t))
        cer_eq = char_err_rate(eq_r, eq_h)
        cer_lex = min(char_err_rate(v, hyp_s) for v in ref_variants(ref_s, lex)) if lex else cer
        prio = 0
        if "loi_chung" in cats:
            prio = 3
        elif "cau_ngan" in cats:
            prio = 2
        elif cats:
            prio = 1
        out.append({**r, "n_syl": n_syl, "cer": round(cer, 3), "cer_bo_thanh": round(cer_notone, 3),
                    "cer_tuong_duong": round(cer_eq, 3), "cer_bien_the": round(cer_lex, 3), "n_tu_sai": err_tokens,
                    "loai_loi": ";".join(f"{k}:{v}" for k, v in sorted(tags.items())),
                    "nhom": ";".join(sorted(cats)), "uu_tien_nghe": prio})
    return out, confusions, foreign


def write_outputs(out, confusions, foreign, d):
    os.makedirs(d, exist_ok=True)
    cols = ["utt_id", "region", "voice", "n_syl", "cer", "cer_bo_thanh", "cer_tuong_duong", "cer_bien_the",
            "n_tu_sai", "loai_loi", "nhom", "uu_tien_nghe", "ref", "hyp"]
    with open(os.path.join(d, "utt_report.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(out, key=lambda x: (-x["uu_tien_nghe"], -x["cer"])):
            w.writerow(r)
    with open(os.path.join(d, "confusions.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ref", "hyp", "loai", "so_lan"])
        for (a, b, t), c in confusions.most_common():
            w.writerow([a, b, t, c])
    with open(os.path.join(d, "tokens_foreign.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["token", "so_lan", "so_lan_sai", "ty_le_sai"])
        for t, (n, e) in sorted(foreign.items(), key=lambda x: (-x[1][1], -x[1][0])):
            w.writerow([t, n, e, round(e / n, 2)])
    # tong hop
    lines = []
    regions = sorted({r["region"] for r in out})
    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")
    lines.append(f"{'vung':6s} {'n':>4s} {'CER':>6s} {'CER bo thanh':>13s} {'CER tuong duong':>16s} {'CER bien the':>13s}")
    for g in regions + ["Tat ca"]:
        rs = [r for r in out if g == "Tat ca" or r["region"] == g]
        lines.append(f"{g:6s} {len(rs):4d} {mean([r['cer'] for r in rs]):6.3f} "
                     f"{mean([r['cer_bo_thanh'] for r in rs]):13.3f} {mean([r['cer_tuong_duong'] for r in rs]):16.3f} "
                     f"{mean([r['cer_bien_the'] for r in rs]):13.3f}")
    lines.append("")
    lines.append("So cau co loi theo nhom (mot cau co the thuoc nhieu nhom):")
    groups = collections.Counter()
    by_reg = collections.defaultdict(collections.Counter)
    for r in out:
        for c in filter(None, r["nhom"].split(";")):
            groups[c] += 1
            by_reg[r["region"]][c] += 1
    for c, n in groups.most_common():
        lines.append(f"  {c:30s} {n:4d}  " + "  ".join(f"{g}:{by_reg[g][c]}" for g in regions))
    lines.append("")
    lines.append("Loai loi muc tu (tong):")
    tot = collections.Counter()
    for r in out:
        for kv in filter(None, r["loai_loi"].split(";")):
            k, v = kv.split(":")
            tot[k] += int(v)
    for k, v in tot.most_common():
        lines.append(f"  {k:22s} {v}")
    with open(os.path.join(d, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--jsonl")
    g.add_argument("--log")
    ap.add_argument("--out", default="asr_error_report")
    ap.add_argument("--id-key", default="utt_id")
    ap.add_argument("--ref-key", default="ref")
    ap.add_argument("--hyp-key", default="hyp")
    ap.add_argument("--region-key", default="region")
    ap.add_argument("--voice-key", default="voice")
    ap.add_argument("--short-max", type=int, default=3)
    ap.add_argument("--lexicon", help="TSV dang chuan -> bien the doc, de tinh cer_bien_the")
    a = ap.parse_args()
    rows = load_rows(a)
    out, conf, foreign = analyse(rows, a.short_max, load_lexicon(a.lexicon))
    print(write_outputs(out, conf, foreign, a.out))
    print(f"\n{len(rows)} cau -> {a.out}/")


if __name__ == "__main__":
    main()
