# -*- coding: utf-8 -*-
"""Góp ý v1 mục 4: chuẩn bị danh sách khung để người bản ngữ Trung Bộ viết lại theo tiểu vùng.
Không sinh câu, không tự điền từ Trung.

Chạy: py -3.13 make_trung_list.py [../data/m1m2_10k_v2]
Ghi vào <thư mục dữ liệu>/cho_nguoi_ban_ngu/:
  khung_mien_Trung_can_viet_lai.tsv  — mọi khung đã dùng, xếp theo ưu tiên; cột trống cho Huế / Nghệ Tĩnh / Quảng Nam – Đà Nẵng / Nam Trung Bộ
  bang_tu_xe_theo_tieu_vung.tsv      — bảng mục 5 của phụ lục, để điền
"""
import collections, csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "data", "m1m2_10k_v2")
OUT = os.path.join(D, "cho_nguoi_ban_ngu")
SUBS = ["Huế", "Nghệ Tĩnh", "Quảng Nam – Đà Nẵng", "Nam Trung Bộ"]
# từ chức năng mà tiếng Trung khác toàn dân (phụ lục mục 2): khung có các từ này được ưu tiên
FUNC = re.compile(r"(?<![\wÀ-ỹ])(đâu|nào|sao|thế|vậy|gì|này|kia|đó|ấy|bây giờ|không|thấy|làm|xem|nhé|nhỉ|tôi|chưa|à|hả)(?![\wÀ-ỹ])")
CAR = re.compile(r"(?<![\wÀ-ỹ])(điều hòa|máy lạnh|kính|kiếng|rẽ|quẹo|đỗ|đậu|tắc|kẹt|ngõ|hẻm|phanh|thắng|còi|lùi|lốp|xi nhan|đổ xăng)(?![\wÀ-ỹ])")


def main():
    rows = [json.loads(l) for p in sorted(glob.glob(os.path.join(D, "*.jsonl"))) for l in open(p, encoding="utf-8")]
    by_frame = collections.defaultdict(list)
    for r in rows:
        by_frame[r["frame_id"]].append(r)
    items = []
    for fid, rr in by_frame.items():
        f = rr[0]
        text = f["frame"].lstrip("~!")
        func = sorted(set(m.group(1) for m in FUNC.finditer(text)))
        car = sorted(set(m.group(1) for m in CAR.finditer(text)))
        tr = [x for x in rr if x["speaker_region"] == "Trung"]
        ex = (tr[0] if tr else rr[0])["text_raw"]
        score = len(rr) * (1.5 if func else 1.0) * (1.3 if car else 1.0) * (1.2 if f["speech_act"] in ("Câu hỏi", "Câu cụt") else 1.0)
        items.append(dict(fid=fid, case=f["case_id"], intent=f["intent"], act=f["speech_act"], frame=text, n=len(rr), n_trung=len(tr),
                          func=", ".join(func), car=", ".join(car), ex=ex, score=score, src=f["frame_source"]))
    items.sort(key=lambda x: -x["score"])
    total = len(rows)
    cum = 0
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "khung_mien_Trung_can_viet_lai.tsv"), "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter="\t")
        w.writerow(["uu_tien", "frame_id", "case_id", "y_dinh", "loai_cau", "so_cau_trong_v2", "so_cau_giong_Trung", "ty_le_cong_don",
                    "tu_chuc_nang_can_xem", "tu_ve_xe_can_xem", "khung", "vi_du_cau", "nguon_khung"] + [f"viet_lai_{s}" for s in SUBS] + ["ghi_chu"])
        for k, it in enumerate(items):
            cum += it["n"]
            pri = 1 if k < 150 else 2 if cum / total <= 0.8 else 3
            w.writerow([pri, it["fid"], it["case"], it["intent"], it["act"], it["n"], it["n_trung"], f"{cum / total:.3f}", it["func"], it["car"],
                        it["frame"], it["ex"], it["src"]] + [""] * (len(SUBS) + 1))
    concepts = ["điều hòa / máy lạnh", "kính / kiếng (cửa xe)", "rẽ / quẹo", "đỗ / đậu xe", "tắc / kẹt xe", "ngõ / hẻm / kiệt", "phanh / thắng",
                "còi / kèn", "lùi xe", "lốp / vỏ", "xi nhan", "đổ / bơm xăng", "\"ở đâu?\" khi hỏi trợ lý", "tiểu từ cuối lệnh (nhé/nha/hí...)",
                "có dùng từ quê khi nói với máy không?"]
    with open(os.path.join(OUT, "bang_tu_xe_theo_tieu_vung.tsv"), "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo, delimiter="\t")
        w.writerow(["khai_niem"] + SUBS + ["ghi_chu"])
        for c in concepts:
            w.writerow([c] + [""] * (len(SUBS) + 1))
    n1 = sum(1 for k in range(len(items)) if k < 150)
    cov1 = sum(it["n"] for it in items[:150]) / total
    print(f"{len(items)} khung; ưu tiên 1: {n1} khung phủ {cov1:.1%} số câu; ghi vào {OUT}")


if __name__ == "__main__":
    main()
