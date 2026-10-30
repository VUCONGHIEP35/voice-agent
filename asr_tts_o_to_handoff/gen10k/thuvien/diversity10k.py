# -*- coding: utf-8 -*-
"""Đo độ đa dạng của bộ câu đã sinh (chỉ đọc, không sửa dữ liệu).

Thư viện (khung mang, lõi câu). Báo cáo đa dạng: py -3.13 -m phantich.diversity_report10k [../data/m1m2_10k]
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
import math, re, unicodedata

WORD = re.compile(r"[\wÀ-ỹ]+")


def toks(t):
    return WORD.findall(t.lower())


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
        from nguyen_lieu import pools10k as P
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
        from nguyen_lieu import pools10k as P
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
