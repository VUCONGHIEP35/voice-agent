# -*- coding: utf-8 -*-
"""Đo độ đa dạng của bộ câu đã sinh (chỉ đọc, không sửa dữ liệu).

Chạy (từ gen10k/):  py -3.13 diversity10k.py [../data/m1m2_10k]
Cần: numpy, scikit-learn (pip install numpy scikit-learn).
Ghi: diversity_report.json và diversity_near_dups.tsv vào thư mục dữ liệu.

Các chỉ số:
  A. Từ vựng: số âm tiết khác nhau, distinct-1..4 (tỷ lệ n-gram khác nhau / tổng n-gram) trên text_spoken.
  B. Khung câu: số khung mỗi ý định, entropy chuẩn hóa của phân bố khung trong ý định.
  C. Khung mang (carrier): câu sau khi che số, tên riêng và giá trị khe phổ biến; bỏ tiền tố/tiểu từ -> 'lõi'.
     Số khung mang khác nhau cho biết có bao nhiêu cách nói thật sự khác nhau, không tính phần điền khe.
  D. Câu gần trùng: cosine TF-IDF (từ + cặp từ) >= 0.9 giữa hai câu khác nhau.
  E. Lặp giá trị khe: tên riêng, số dùng nhiều nhất.
  F. Mở đầu và kết thúc câu.
  G. Khác biệt vùng: tỷ lệ câu không có từ vùng; độ chính xác đoán vùng từ chữ (hồi quy logistic, 5 lần chia).
  H. Thanh điệu và âm tiết.
"""
import collections, json, math, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "data", "m1m2_10k")

WORD = re.compile(r"[\wÀ-ỹ]+")


def toks(t):
    return WORD.findall(t.lower())


def load():
    man = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8"))
    rows = []
    for fi in man["files"]:
        for l in open(os.path.join(D, fi["file"]), encoding="utf-8"):
            r = json.loads(l)
            r["_file"] = fi["file"]
            rows.append(r)
    return rows


def distinct_n(seqs, n):
    tot, uniq = 0, set()
    for s in seqs:
        for i in range(len(s) - n + 1):
            uniq.add(tuple(s[i:i + n]))
            tot += 1
    return round(len(uniq) / tot, 4) if tot else 0.0, len(uniq)


def entropy_norm(counter):
    n = sum(counter.values())
    k = len(counter)
    if k <= 1:
        return 0.0
    h = -sum(c / n * math.log(c / n) for c in counter.values())
    return round(h / math.log(k), 3)


# ------------------------------------------------------------------ che giá trị khe
def build_masks():
    try:
        import pools10k as P
    except Exception as e:  # noqa
        print("Không import được pools10k, chỉ che số và tên riêng viết hoa:", e)
        return []
    lists = []
    for name in ("NEARBY", "GENRES", "MOODS", "REMIND", "MESSAGES", "PODCASTS", "TOPICS", "HOME_LIKE", "PLACE_LIKE", "WARNS", "PARTS",
                 "LAMPS", "SEATS", "WPOS", "VENTS", "TIRES", "WEATHER", "DISHES", "SHOP", "NEWS_TOPICS", "CONTEXT_TAGS",
                 "COLORS", "WARN_LAMPS", "PLAYLISTS", "GENRE_BARE"):
        for v in getattr(P, name, []):
            if isinstance(v, str) and len(v) >= 3:
                lists.append((v.lower(), "<" + name + ">"))
    for v, _ in getattr(P, "SYSTEMS", []):
        lists.append((v.lower(), "<SYSTEMS>"))
    for reg, items in getattr(P, "KIN", {}).items():
        for w, _ in items:
            if len(w) >= 2:
                lists.append((w.lower(), "<KIN>"))
    lists.sort(key=lambda x: -len(x[0]))
    return lists


PARTICLE_EDGE = re.compile(r"^(trợ lý ơi|này trợ lý|làm ơn|bạn ơi|cho tôi|cho tui|giúp tôi|giúp tui|giùm tui|này|ê|ờ|nì|nè)\s+")
PARTICLE_END = re.compile(r"\s+(nhé|nha|nghen|nghe|đi nha|đi|với|hộ tôi|giúp tôi|giùm|dùm|luôn|ngay|nhỉ|thế|vậy|rứa|hè|ta|ạ|à|hả|hen)$")


def carrier(raw, masks):
    t = raw.strip().rstrip(".?!")
    # tên riêng: chuỗi từ viết hoa không ở đầu câu
    words = t.split(" ")
    out = []
    for i, w in enumerate(words):
        if i > 0 and w[:1].isupper() and not re.match(r"^\d", w):
            if out and out[-1] == "<TÊN>":
                continue
            out.append("<TÊN>")
        else:
            out.append(w)
    t = " ".join(out).lower()
    t = re.sub(r"\d[\d.,:/]*(\s?(%|°c|km/h|kwh|kw|km|mhz)(?![\wÀ-ỹ]))?", "<SỐ>", t)
    t = re.sub(r"\s+", " ", t)
    for v, tag in masks:
        if v in t:
            t = re.sub(r"(?<![\wÀ-ỹ])" + re.escape(v) + r"(?![\wÀ-ỹ])", tag, t)
    t = re.sub(r"(<TÊN>\s*)+", "<TÊN> ", t)
    t = re.sub(r"(<SỐ>\s*)+", "<SỐ> ", t)
    t = re.sub(r"[,;:]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    core = t
    for _ in range(3):
        core = PARTICLE_EDGE.sub("", core)
        core = PARTICLE_END.sub("", core)
    return t, core


# ------------------------------------------------------------------ lõi dùng cho trần câu/lõi (v3, CHANGES_v3 C1)
def build_keep():
    """Tên app, bản đồ, thu phí, nguồn kết nối: không che khi đếm lõi để áp trần (lệnh 'mở YouTube' ≠ 'mở Zalo')."""
    try:
        import pools10k as P
    except Exception as e:  # noqa
        print("Không import được pools10k, carrier_cap = carrier:", e)
        return []
    names = set()
    for name in ("APPS", "MAP_APPS", "ETC_APPS", "MUSIC_APPS", "MSG_APPS"):
        names |= {v for v in getattr(P, name, []) if isinstance(v, str)}
    names |= {raw for raw, _, _ in getattr(P, "LINK_SRC", [])}
    names = {v for v in names if any(ch.isupper() for ch in v)}   # 'lịch', 'điện thoại' không phải tên riêng; giữ 'ePass'
    keep = [(v, "k_" + re.sub(r"[^0-9a-z]", "", v.lower())) for v in names]
    keep.sort(key=lambda x: -len(x[0]))
    return keep


def carrier_cap(raw, masks, keep):
    """Như carrier, nhưng tên trong keep được thay bằng mã chữ thường liền nhau nên không bị gắn <TÊN>."""
    for v, code in keep:
        if v.lower() in raw.lower():
            raw = re.sub(r"(?<![\wÀ-ỹ])" + re.escape(v) + r"(?![\wÀ-ỹ])", code, raw, flags=re.I)
    return carrier(raw, masks)


# ------------------------------------------------------------------ thanh điệu
TONE_MARK = {"́": "sắc", "̀": "huyền", "̉": "hỏi", "̃": "ngã", "̣": "nặng"}


def tone_of(syl):
    for ch in unicodedata.normalize("NFD", syl):
        if ch in TONE_MARK:
            return TONE_MARK[ch]
    return "ngang"


def main():
    rows = load()
    N = len(rows)
    rep = {"n": N}
    sp = [toks(r["text_spoken"]) for r in rows]

    # A. từ vựng
    vocab = collections.Counter(w for s in sp for w in s)
    rep["A_tu_vung"] = dict(
        so_am_tiet_khac_nhau=len(vocab), tong_am_tiet=sum(vocab.values()),
        am_tiet_chi_xuat_hien_1_lan=sum(1 for v in vocab.values() if v == 1),
        top30=vocab.most_common(30),
        distinct={f"d{n}": distinct_n(sp, n)[0] for n in (1, 2, 3, 4)},
        distinct_theo_file={}, distinct_theo_vung={},
    )
    for f in sorted({r["_file"] for r in rows}):
        ss = [s for s, r in zip(sp, rows) if r["_file"] == f]
        rep["A_tu_vung"]["distinct_theo_file"][f] = dict(n=len(ss), am_tiet=len({w for s in ss for w in s}),
                                                         d2=distinct_n(ss, 2)[0], d3=distinct_n(ss, 3)[0])
    for g in ("Bắc", "Trung", "Nam"):
        ss = [s for s, r in zip(sp, rows) if r["lexicon_variant"] == g]
        rep["A_tu_vung"]["distinct_theo_vung"][g] = dict(n=len(ss), am_tiet=len({w for s in ss for w in s}),
                                                          d2=distinct_n(ss, 2)[0], d3=distinct_n(ss, 3)[0])

    # B. khung theo ý định
    by_int = collections.defaultdict(collections.Counter)
    for r in rows:
        by_int[(r["case_id"], r["intent_id"])][r["frame_id"]] += 1
    ints = []
    for (c, i), cc in by_int.items():
        ints.append(dict(case=c, intent=i, cau=sum(cc.values()), khung=len(cc), cau_moi_khung=round(sum(cc.values()) / len(cc), 1),
                         entropy=entropy_norm(cc)))
    ints.sort(key=lambda x: -x["cau_moi_khung"])
    rep["B_khung"] = dict(
        so_y_dinh=len(ints), so_khung=len({r["frame_id"] for r in rows}),
        y_dinh_it_khung=[x for x in ints if x["khung"] < 5],
        y_dinh_nhieu_cau_moi_khung_nhat=ints[:15],
        trung_vi_khung_moi_y_dinh=sorted(x["khung"] for x in ints)[len(ints) // 2],
        evidence=dict(collections.Counter(r["evidence"] for r in rows)),
        khung_seen=len({r["frame_id"] for r in rows if r["evidence"] == "seen"}),
    )

    # C. khung mang
    masks = build_masks()
    car = [carrier(r["text_raw"], masks) for r in rows]
    full = collections.Counter(c for c, _ in car)
    core = collections.Counter(k for _, k in car)
    rep["C_khung_mang"] = dict(
        khung_mang_khac_nhau=len(full), ty_le=round(len(full) / N, 3),
        loi_khac_nhau=len(core), ty_le_loi=round(len(core) / N, 3),
        loi_lap_nhieu_nhat=core.most_common(25),
        so_cau_thuoc_loi_lap_tu_10_lan=sum(v for v in core.values() if v >= 10),
        theo_case={},
    )
    for c in sorted({r["case_id"] for r in rows}):
        cc = collections.Counter(k for (_, k), r in zip(car, rows) if r["case_id"] == c)
        n = sum(cc.values())
        rep["C_khung_mang"]["theo_case"][c] = dict(cau=n, loi=len(cc), ty_le=round(len(cc) / n, 3), lap_nhieu_nhat=cc.most_common(1)[0])

    # D. gần trùng
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        texts = [" ".join(s) for s in sp]
        X = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"\S+", sublinear_tf=True).fit_transform(texts).astype(np.float32)
        best = np.zeros(N, dtype=np.float32)
        nn = np.zeros(N, dtype=np.int64)
        pairs = 0
        for s in range(0, N, 1000):
            S = (X[s:s + 1000] @ X.T).toarray()
            for k in range(S.shape[0]):
                S[k, s + k] = 0
            pairs += int((S >= 0.9).sum())
            nn[s:s + S.shape[0]] = S.argmax(1)
            best[s:s + S.shape[0]] = S.max(1)
        same_frame = sum(1 for i in range(N) if best[i] >= 0.9 and rows[i]["frame_id"] == rows[nn[i]]["frame_id"])
        rep["D_gan_trung"] = dict(
            cap_cos_tu_0_9=pairs // 2,
            cau_co_hang_xom_cos_tu_0_9=int((best >= 0.9).sum()),
            cau_co_hang_xom_cos_tu_0_8=int((best >= 0.8).sum()),
            trong_do_cung_khung=same_frame,
            trung_vi_cos_hang_xom_gan_nhat=round(float(np.median(best)), 3),
        )
        order = np.argsort(-best)
        with open(os.path.join(D, "diversity_near_dups.tsv"), "w", encoding="utf-8") as fo:
            fo.write("cos\tsample_a\ttext_a\tsample_b\ttext_b\tcung_khung\n")
            seen = set()
            for i in order[:400]:
                j = int(nn[i])
                key = tuple(sorted((i, j)))
                if key in seen:
                    continue
                seen.add(key)
                fo.write(f"{best[i]:.3f}\t{rows[i]['sample_id']}\t{rows[i]['text_spoken']}\t{rows[j]['sample_id']}\t{rows[j]['text_spoken']}\t"
                         f"{rows[i]['frame_id'] == rows[j]['frame_id']}\n")
    except ImportError as e:
        rep["D_gan_trung"] = f"bỏ qua: {e}"

    # E. lặp giá trị khe
    names = collections.Counter()
    nums = collections.Counter()
    for r in rows:
        ws = r["text_raw"].rstrip(".?!").split(" ")
        run = []
        for i, w in enumerate(ws + ["x"]):
            if i > 0 and i < len(ws) and w[:1].isupper():
                run.append(w.strip(","))
            else:
                if run:
                    names[" ".join(run)] += 1
                run = []
        for m in re.findall(r"\d[\d.,]*", r["text_raw"]):
            nums[m.rstrip(".,")] += 1
    rep["E_gia_tri_khe"] = dict(ten_rieng_khac_nhau=len(names), lan_xuat_hien_ten_rieng=sum(names.values()),
                                ten_rieng_top20=names.most_common(20), so_khac_nhau=len(nums), so_top20=nums.most_common(20))

    # F. mở đầu, kết thúc
    first2 = collections.Counter(" ".join(s[:2]) for s in sp)
    last1 = collections.Counter(s[-1] if s else "" for s in sp)
    rep["F_mo_dau_ket_thuc"] = dict(
        mo_dau_2_tu_khac_nhau=len(first2), top10_mo_dau=first2.most_common(10),
        ty_le_top10_mo_dau=round(sum(v for _, v in first2.most_common(10)) / N, 3),
        top10_tu_cuoi=last1.most_common(10),
    )

    # G. vùng
    reg = {}
    for g in ("Bắc", "Trung", "Nam"):
        rr = [r for r in rows if r["lexicon_variant"] == g]
        wc = collections.Counter(w for r in rr for w in r["regional_words"])
        reg[g] = dict(n=len(rr), khong_co_tu_vung=round(sum(1 for r in rr if not r["regional_words"]) / len(rr), 3), top_tu_vung=wc.most_common(12))
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.feature_extraction.text import CountVectorizer
        Xc = CountVectorizer(token_pattern=r"[\wÀ-ỹ]+", ngram_range=(1, 1), min_df=2).fit_transform([r["text_raw"].lower() for r in rows])
        y = [r["lexicon_variant"] for r in rows]
        acc = cross_val_score(LogisticRegression(max_iter=2000), Xc, y, cv=5).mean()
        reg["doan_vung_tu_chu_acc"] = round(float(acc), 3)
        reg["ghi_chu"] = "1/3 = chữ không mang dấu hiệu vùng; càng cao càng dễ đoán vùng chỉ từ chữ."
    except Exception as e:  # noqa
        reg["doan_vung_tu_chu_acc"] = f"bỏ qua: {e}"
    rep["G_vung"] = reg

    # H. thanh điệu, âm tiết
    tones = collections.Counter(tone_of(w) for s in sp for w in s)
    tot = sum(tones.values())
    rep["H_thanh_dieu"] = {k: round(v / tot, 3) for k, v in tones.most_common()}
    rep["H_do_dai"] = dict(collections.Counter(r["length_class"] for r in rows))

    json.dump(rep, open(os.path.join(D, "diversity_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1)[:12000])


if __name__ == "__main__":
    main()
