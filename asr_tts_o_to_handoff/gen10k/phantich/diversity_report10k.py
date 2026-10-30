# -*- coding: utf-8 -*-
"""Báo cáo đa dạng của bộ câu đã sinh (chỉ đọc, không sửa dữ liệu); các chỉ số xem thuvien/diversity10k.py.

Chạy (từ gen10k/):  py -3.13 -m phantich.diversity_report10k [../data/m1m2_10k]
Ghi: diversity_report.json và diversity_near_dups.tsv vào thư mục dữ liệu.
"""
import collections, json, os, re, sys

from cauhinh.duong_dan import ROOT
from thuvien.diversity10k import build_masks, carrier, distinct_n, entropy_norm, toks, tone_of

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "m1m2_10k")


def load():
    man = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8"))
    rows = []
    for fi in man["files"]:
        for l in open(os.path.join(D, fi["file"]), encoding="utf-8"):
            r = json.loads(l)
            r["_file"] = fi["file"]
            rows.append(r)
    return rows


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
