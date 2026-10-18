# -*- coding: utf-8 -*-
"""So hai bộ đã sinh theo text_raw (sample_id đánh theo vị trí nên không so được). Chỉ đọc bộ cũ.

Chạy: py -3.13 compare10k.py ../data/m1m2_10k_v2 ../data/m1m2_10k_v3
Ghi <bộ mới>/so_voi_v2.tsv: câu của bộ cũ không còn trong bộ mới, và câu mới của bộ mới.
In bảng theo case và các số đếm dùng cho báo cáo.
"""
import collections, json, os, re, sys

LOAN_MUST = "cách đọc chưa xác minh"
LOAN_SHOULD = "cách đọc từ ngoại đã đổi chữ"


def load(d):
    man = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    rows = []
    for fi in man["files"]:
        rows += [json.loads(l) for l in open(os.path.join(d, fi["file"]), encoding="utf-8")]
    return rows


def key(t):
    t = re.sub(r"[\.,;:!?\"“”()\[\]–-]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def main():
    old_dir, new_dir = sys.argv[1], sys.argv[2]
    a, b = load(old_dir), load(new_dir)
    ka, kb = {key(r["text_raw"]) for r in a}, {key(r["text_raw"]) for r in b}
    lost = [r for r in a if key(r["text_raw"]) not in kb]
    new = [r for r in b if key(r["text_raw"]) not in ka]
    n_a = collections.Counter(r["case_id"] for r in a)
    n_lost = collections.Counter(r["case_id"] for r in lost)
    n_new = collections.Counter(r["case_id"] for r in new)
    n_g = collections.Counter(r["case_id"] for r in b if r.get("app_group"))
    print("case\tcũ\tgiữ nguyên câu\tcũ không còn\tcâu mới\ttrong đó nhóm G")
    for c in sorted(n_a):
        print(f"{c}\t{n_a[c]}\t{n_a[c] - n_lost[c]}\t{n_lost[c]}\t{n_new[c]}\t{n_g[c]}")
    print(f"tổng\t{len(a)}\t{len(a) - len(lost)}\t{len(lost)}\t{len(new)}\t{sum(n_g.values())}")
    out = dict(
        lost_by_source=collections.Counter("src_commands.json" if r["frame_source"].startswith("src_commands") else r["frame_source"]
                                           for r in lost).most_common(),
        seen=dict(old=sum(r["evidence"] == "seen" for r in a), new=sum(r["evidence"] == "seen" for r in b)),
        review_status=dict(old=dict(collections.Counter(r["review_status"] for r in a)),
                           new=dict(collections.Counter(r["review_status"] for r in b))),
        language_mix=dict(old=dict(collections.Counter(r["language_mix"] for r in a)),
                          new=dict(collections.Counter(r["language_mix"] for r in b))),
        loan_must_rows=sum(any(x.startswith(LOAN_MUST) for x in r["review_reasons"]) for r in b),
        loan_should_rows=sum(any(x.startswith(LOAN_SHOULD) for x in r["review_reasons"]) for r in b),
        loan_must_terms=collections.Counter(x.split(": ", 1)[1].split(" (")[0] for r in b for x in r["review_reasons"]
                                            if x.startswith(LOAN_MUST)).most_common(),
        loan_should_terms=collections.Counter(x.split(": ", 1)[1] for r in b for x in r["review_reasons"]
                                              if x.startswith(LOAN_SHOULD)).most_common(),
        intent_change=sorted((sum(1 for r in b if (r["case_id"], r["intent_id"]) == k) - v, k[0], k[1])
                             for k, v in collections.Counter((r["case_id"], r["intent_id"]) for r in a).items())[:12],
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    with open(os.path.join(new_dir, "so_voi_v2.tsv"), "w", encoding="utf-8", newline="\n") as fo:
        fo.write("trang_thai\tcase_id\tsample_id\tframe_id\tframe_source\ttext_raw\n")
        for st, rs in (("v2_khong_con_trong_v3", lost), ("v3_moi", new)):
            for r in rs:
                fo.write(f"{st}\t{r['case_id']}\t{r['sample_id']}\t{r['frame_id']}\t{r['frame_source']}\t{r['text_raw']}\n")


if __name__ == "__main__":
    main()
