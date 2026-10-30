# -*- coding: utf-8 -*-
"""Chọn câu thí điểm từ bộ v3 (giai đoạn 1 của kế hoạch sinh TTS bằng VieNeu v3 Turbo).

Phân tầng: vùng giọng (speaker_region) × nhóm độ dài (length_class). Trong mỗi tầng, rải đều theo case
(câu của case chưa có được ưu tiên). Mỗi vùng bắt buộc có câu chứa tên Latin chưa duyệt cách đọc
(cờ "cách đọc chưa xác minh") và câu chứa số, để giai đoạn 1 kiểm được VieNeu đọc các câu này thế nào.
Câu rất ngắn và câu dài được lấy dư so với tỷ lệ trong bộ, để thử lỗi "nói thêm" và câu dài.
Thứ tự xác định bằng sha1(seed, sample_id): chạy lại cho cùng kết quả.

Chạy (từ tts_gen/):  python -m luutru.select_pilot [--seed 20261018] [--out pilot/pilot_100.jsonl]
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
V3 = os.path.join(os.path.dirname(HERE), "data", "m1m2_10k_v3")
REGION_N = {"Bắc": 34, "Trung": 33, "Nam": 33}
LEN_TARGET = {"Rất ngắn": 5, "Ngắn": 13, "Thường": 11, "Dài": 4}     # 33 câu; vùng 34 câu thêm 1 câu "Ngắn"
FEATURE_MIN = {"loan": 3, "so": 3}                                    # mỗi vùng
LOAN_FLAG = "cách đọc chưa xác minh"


def is_loan(r):
    return any(x.startswith(LOAN_FLAG) for x in r["review_reasons"])


def has_num(r):
    return bool(re.search(r"\d", r["text_raw"]))


def load_v3(path=V3):
    rows = []
    for fn in sorted(glob.glob(os.path.join(path, "*.jsonl"))):
        with open(fn, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f]
    return rows


def select(rows, seed):
    def order(r):
        return hashlib.sha1(f"{seed}|{r['sample_id']}".encode()).hexdigest()

    picked = []
    for region, n in REGION_N.items():
        pool = sorted((r for r in rows if r["speaker_region"] == region), key=order)
        target = dict(LEN_TARGET)
        target["Ngắn"] += n - sum(LEN_TARGET.values())
        got, cases, chosen = collections.Counter(), collections.Counter(), set()

        def take(pred, k):
            for strict in (True, False):           # lượt 1: chỉ case chưa có; lượt 2: case bất kỳ
                for r in pool:
                    if k <= 0:
                        return
                    lc = r["length_class"]
                    if r["sample_id"] in chosen or got[lc] >= target[lc] or not pred(r):
                        continue
                    if strict and cases[r["case_id"]]:
                        continue
                    chosen.add(r["sample_id"])
                    got[lc] += 1
                    cases[r["case_id"]] += 1
                    picked.append(dict(r, pilot_region_rank=len(chosen)))
                    k -= 1

        take(is_loan, FEATURE_MIN["loan"])
        take(lambda r: has_num(r) and not is_loan(r), FEATURE_MIN["so"])
        for lc, t in target.items():
            take(lambda r, lc=lc: r["length_class"] == lc, t - got[lc])
        if sum(got.values()) != n:
            raise SystemExit(f"{region}: chỉ chọn được {sum(got.values())}/{n} câu")
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="20261018")
    ap.add_argument("--out", default=os.path.join(HERE, "pilot", "pilot_100.jsonl"))
    a = ap.parse_args()
    picked = select(load_v3(), a.seed)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fo:
        for i, r in enumerate(picked):
            fo.write(json.dumps(dict(r, pilot_idx=i), ensure_ascii=False) + "\n")
    c = collections.Counter
    print(f"{len(picked)} câu -> {a.out}")
    print("vùng × độ dài:", dict(c((r["speaker_region"], r["length_class"]) for r in picked)))
    print("số case:", len(c(r["case_id"] for r in picked)), dict(sorted(c(r["case_id"] for r in picked).items())))
    print("có tên Latin chưa duyệt:", sum(is_loan(r) for r in picked), "| có số:", sum(has_num(r) for r in picked),
          "| nhóm G:", sum(bool(r["app_group"]) for r in picked))
    print("Trung theo tiểu vùng / nơi sống:", dict(c((r["sub_region"], r["residence"]) for r in picked if r["speaker_region"] == "Trung")))
    print("âm tiết:", min(r["n_syllables"] for r in picked), "–", max(r["n_syllables"] for r in picked))


if __name__ == "__main__":
    main()
