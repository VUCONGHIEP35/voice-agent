# -*- coding: utf-8 -*-
"""Từ vựng vùng: viết lại phần chữ cố định của khung câu theo biến thể Bắc/Trung/Nam,
và trang trí câu bằng tiểu từ theo vùng.

Mỗi từ thay vào được ghi lại (Mark) để tính yếu tố S51/S52 và review_status.
verified=True khi src_lang.json ghi nguồn đọc được (L*) cho từ đó; chỉ K1 -> chưa xác minh.
"""
import re

W = r"(?<![\wÀ-ỹ])"   # biên trái của từ
E = r"(?![\wÀ-ỹ])"    # biên phải


class Mark:
    __slots__ = ("word", "concept", "factor", "verified", "regional")

    def __init__(self, word, concept, factor, verified, regional):
        self.word, self.concept, self.factor, self.verified, self.regional = word, concept, factor, verified, regional


# (tên khái niệm, regex khớp mọi dạng, {vùng: [(từ, trọng số)]}, {từ: (yếu tố, đã xác minh, là từ vùng)}, nguồn)
# Thứ tự quan trọng: cụm dài trước cụm ngắn.
RULES = [
    ("giúp tôi", W + r"(giúp tôi|hộ tôi|giùm tôi|dùm tôi|giúp mình)" + E,
     {"Bắc": [("giúp tôi", .6), ("hộ tôi", .25), ("giúp mình", .15)], "Trung": [("giúp tui", .5), ("giùm tui", .5)],
      "Nam": [("giùm tui", .4), ("dùm tui", .3), ("giúp tui", .3)]},
     {"hộ tôi": ("S52", False, True), "giúp tui": ("S52", True, True), "giùm tui": ("S52", False, True), "dùm tui": ("S52", False, True),
      "giúp mình": ("E06", True, False)}, "src_lang particles (hộ: K1; giùm/dùm: K1; tui: L2, L9)"),
    ("điều hòa", W + r"(điều hòa|máy lạnh)" + E + r"(?! lạnh)",
     {"Bắc": [("điều hòa", 1)], "Trung": [("máy lạnh", .5), ("điều hòa", .5)], "Nam": [("máy lạnh", .85), ("điều hòa", .15)]},
     {"máy lạnh": ("S51", True, True)}, "src_lang lexicon 'điều hòa (A/C)' (L2, high)"),
    ("kính", W + r"(kính|kiếng)" + r"(?! (mát|cận|lão|trọng|râm))" + E,
     {"Bắc": [("kính", 1)], "Trung": [("kính", .7), ("kiếng", .3)], "Nam": [("kiếng", .7), ("kính", .3)]},
     {"kiếng": ("S51", False, True)}, "src_lang lexicon 'kính' (K1, medium)"),
    ("tắc đường", W + r"(tắc đường|kẹt xe|tắc xe)" + E,
     {"Bắc": [("tắc đường", .85), ("tắc xe", .15)], "Trung": [("kẹt xe", .6), ("tắc đường", .4)], "Nam": [("kẹt xe", 1)]},
     {"kẹt xe": ("S51", False, True), "tắc đường": ("S51", False, True), "tắc xe": ("S51", False, True)},
     "src_lang lexicon 'tắc đường' (K1, medium); Tu_dia_phuong"),
    ("tắc", r"(?<!ùn )" + W + r"(tắc|kẹt)" + r"(?! (đường|xe))" + E,
     {"Bắc": [("tắc", 1)], "Trung": [("kẹt", .6), ("tắc", .4)], "Nam": [("kẹt", 1)]},
     {"kẹt": ("S51", False, True), "tắc": ("S51", False, True)}, "như trên"),
    ("rẽ", W + r"(rẽ|quẹo)" + E,
     {"Bắc": [("rẽ", 1)], "Trung": [("rẽ", .6), ("quẹo", .4)], "Nam": [("quẹo", .85), ("rẽ", .15)]},
     {"quẹo": ("S51", True, True), "rẽ": ("S51", True, True)}, "src_lang lexicon 'rẽ' (L21 + K1)"),
    ("đỗ xe", W + r"(đỗ xe|đậu xe)" + E,
     {"Bắc": [("đỗ xe", 1)], "Trung": [("đậu xe", .7), ("đỗ xe", .3)], "Nam": [("đậu xe", 1)]},
     {"đậu xe": ("S51", False, True), "đỗ xe": ("S51", False, True)}, "src_lang lexicon 'đỗ xe' (K1)"),
    ("chỗ đỗ", W + r"(bãi|chỗ|điểm|nơi) (đỗ|đậu)" + r"(?! xe)" + E,
     {"Bắc": [("{0} đỗ", 1)], "Trung": [("{0} đậu", .7), ("{0} đỗ", .3)], "Nam": [("{0} đậu", 1)]},
     {"đậu": ("S51", False, True), "đỗ": ("S51", False, True)}, "như trên"),
    ("vòng xuyến", W + r"(vòng xuyến|vòng xoay|bùng binh)" + E,
     {"Bắc": [("vòng xuyến", 1)], "Trung": [("vòng xoay", 1)], "Nam": [("vòng xoay", .6), ("bùng binh", .4)]},
     {"vòng xoay": ("S51", False, True), "bùng binh": ("S51", False, True), "vòng xuyến": ("S51", False, True)}, "Tu_dia_phuong (K1)"),
    ("gương chiếu hậu", W + r"(gương chiếu hậu|kiếng chiếu hậu)" + E,
     {"Bắc": [("gương chiếu hậu", 1)], "Trung": [("gương chiếu hậu", 1)], "Nam": [("kiếng chiếu hậu", .6), ("gương chiếu hậu", .4)]},
     {"kiếng chiếu hậu": ("S51", False, True)}, "src_lang lexicon, car_terms 'gương chiếu hậu' (K1)"),
    ("thay dầu", W + r"(thay dầu|thay nhớt)" + E,
     {"Bắc": [("thay dầu", 1)], "Trung": [("thay dầu", 1)], "Nam": [("thay nhớt", .8), ("thay dầu", .2)]},
     {"thay nhớt": ("S51", False, True)}, "src_lang lexicon 'dầu nhớt', car_terms 'bảo dưỡng' (K1)"),
    ("ắc quy", W + r"(ắc quy)" + E,
     {"Bắc": [("ắc quy", 1)], "Trung": [("ắc quy", 1)], "Nam": [("bình điện", .4), ("ắc quy", .6)]},
     {"bình điện": ("S51", False, True)}, "src_lang lexicon, car_terms 'ắc quy' (K1)"),
    ("phanh", W + r"(phanh)" + E,
     {"Bắc": [("phanh", 1)], "Trung": [("thắng", .5), ("phanh", .5)], "Nam": [("thắng", .7), ("phanh", .3)]},
     {"thắng": ("S51", False, True)}, "src_lang lexicon 'phanh' (K1)"),
    ("tôi", W + r"(tôi)" + E,
     {"Bắc": [("tôi", 1)], "Trung": [("tui", .55), ("tôi", .45)], "Nam": [("tui", .5), ("tôi", .5)]},
     {"tui": ("S52", True, True)}, "src_lang lexicon 'tôi' (L2, L9)"),
    ("nhé", W + r"(nhé|nha|nghen)" + r"(?=\s*$|\s*[,.?!])",
     {"Bắc": [("nhé", 1)], "Trung": [("nghe", .5), ("nhé", .3), ("nha", .2)], "Nam": [("nha", .7), ("nghen", .3)]},
     {"nhé": ("S52", False, True), "nha": ("S52", True, True), "nghen": ("S52", False, True), "nghe": ("S52", False, True)},
     "src_lang particles (nha: L8; nhé, nghen, nghe: K1)"),
    ("nhỉ", W + r"(nhỉ)" + r"(?=\s*$|\s*[,.?!])",
     {"Bắc": [("nhỉ", 1)], "Trung": [("hè", .5), ("nhỉ", .5)], "Nam": [("hen", .5), ("nhỉ", .5)]},
     {"hè": ("S52", True, True), "hen": ("S52", False, True), "nhỉ": ("S52", False, True)}, "src_lang lexicon 'nhỉ (tag)' (L10 + K1)"),
    ("thế cuối câu", W + r"(thế|vậy)" + r"(?=\s*$|\s*[?.!])",
     {"Bắc": [("thế", 1)], "Trung": [("rứa", .7), ("vậy", .3)], "Nam": [("vậy", 1)]},
     {"rứa": ("S52", True, True), "thế": ("S52", True, True), "vậy": ("S52", True, True)}, "src_lang lexicon 'thế/vậy' (L2)"),
    ("thế nào", r"(?<!như )" + W + r"(thế nào|ra sao)" + E,
     {"Bắc": [("thế nào", .8), ("ra sao", .2)], "Trung": [("ra răng", .5), ("thế nào", .5)], "Nam": [("ra sao", .5), ("thế nào", .35), ("sao", .15)]},
     {"ra răng": ("S51", True, True)}, "src_lang lexicon 'sao' (L2, L9, L23)"),
    ("tại sao", W + r"(tại sao|vì sao)" + E,
     {"Bắc": [("tại sao", .6), ("vì sao", .4)], "Trung": [("răng", .6), ("tại sao", .4)], "Nam": [("tại sao", .6), ("sao", .4)]},
     {"răng": ("S51", True, True)}, "như trên"),
    ("là sao", W + r"(là sao)" + E,
     {"Bắc": [("là sao", 1)], "Trung": [("là răng", .6), ("là sao", .4)], "Nam": [("là sao", 1)]},
     {"là răng": ("S51", True, True)}, "như trên"),
    ("gì", W + r"(gì)" + E,
     {"Bắc": [("gì", 1)], "Trung": [("chi", .6), ("gì", .4)], "Nam": [("gì", 1)]},
     {"chi": ("S51", True, True)}, "src_lang lexicon 'gì' (L10, L11)"),
    ("ở đâu", W + r"(ở đâu)" + E,
     {"Bắc": [("ở đâu", 1)], "Trung": [("ở mô", .6), ("ở đâu", .4)], "Nam": [("ở đâu", 1)]},
     {"ở mô": ("S51", True, True)}, "src_lang lexicon 'đâu/nào' (L2, L10, L11)"),
    ("đâu", W + r"(đâu)" + E,
     {"Bắc": [("đâu", 1)], "Trung": [("mô", .6), ("đâu", .4)], "Nam": [("đâu", 1)]},
     {"mô": ("S51", True, True)}, "src_lang lexicon 'đâu/nào' (L2, L10, L11)"),
    ("này", W + r"(này)" + E,
     {"Bắc": [("này", 1)], "Trung": [("ni", .5), ("này", .5)], "Nam": [("này", 1)]},
     {"ni": ("S51", True, True)}, "src_lang lexicon 'này' (L2, L9)"),
    ("bây giờ", W + r"(bây giờ)" + E,
     {"Bắc": [("bây giờ", 1)], "Trung": [("chừ", .5), ("bây giờ", .5)], "Nam": [("bây giờ", .6), ("giờ", .4)]},
     {"chừ": ("S51", True, True)}, "src_lang lexicon 'bây giờ' (L10 + K1)"),
    ("mẹ", W + r"(mẹ)" + E,
     {"Bắc": [("mẹ", 1)], "Trung": [("mạ", .8), ("mẹ", .2)], "Nam": [("má", .8), ("mẹ", .2)]},
     {"mạ": ("S52", True, True), "má": ("S52", True, True)}, "src_lang kinship (L6, L25)"),
    ("bố", W + r"(bố)" + E,
     {"Bắc": [("bố", 1)], "Trung": [("ba", .6), ("cha", .4)], "Nam": [("ba", 1)]},
     {"ba": ("S52", True, True), "cha": ("S52", True, True)}, "src_lang kinship (L6, L25)"),
    ("xem", W + r"(xem)" + E,
     {"Bắc": [("xem", 1)], "Trung": [("xem", .7), ("coi", .3)], "Nam": [("coi", .45), ("xem", .55)]},
     {"coi": ("S51", False, True)}, "src_lang lexicon 'xem' (K1)"),
    ("vào", W + r"(vào)" + r"(?! (lúc|ngày|buổi|thứ|cuối|sáng|chiều|tối|tháng|năm|giờ|danh|bộ))" + E,
     {"Bắc": [("vào", 1)], "Trung": [("vào", .7), ("vô", .3)], "Nam": [("vô", .5), ("vào", .5)]},
     {"vô": ("S51", False, True)}, "src_lang lexicon 'vào' (K1)"),
    ("muộn", W + r"(muộn|trễ)" + E,
     {"Bắc": [("muộn", .85), ("trễ", .15)], "Trung": [("trễ", .6), ("muộn", .4)], "Nam": [("trễ", 1)]},
     {"trễ": ("S51", True, True), "muộn": ("S51", True, True)}, "src_lang lexicon 'chậm/trễ' (L2)"),
    ("hỏng", W + r"(hỏng|hư)" + E,
     {"Bắc": [("hỏng", 1)], "Trung": [("hư", 1)], "Nam": [("hư", 1)]},
     {"hư": ("S51", True, True), "hỏng": ("S51", True, True)}, "src_lang lexicon 'hỏng/hư' (L2)"),
    ("hoài", W + r"(hoài|mãi)" + E,
     {"Bắc": [("mãi", 1)], "Trung": [("hoài", .5), ("mãi", .5)], "Nam": [("hoài", 1)]},
     {"hoài": ("S51", False, True)}, "K1"),
    ("thật", W + r"(thật|thiệt)" + E,
     {"Bắc": [("thật", 1)], "Trung": [("thiệt", .6), ("thật", .4)], "Nam": [("thiệt", .7), ("thật", .3)]},
     {"thiệt": ("S51", True, True)}, "src_lang lexicon 'thật' (L10 + K1)"),
    ("vâng", W + r"(vâng)" + E,
     {"Bắc": [("vâng", 1)], "Trung": [("dạ", 1)], "Nam": [("dạ", 1)]},
     {"dạ": ("S52", True, True), "vâng": ("S52", True, True)}, "src_lang particles (L2, L8, L9)"),
    ("ô tô", W + r"(ô tô)" + E,
     {"Bắc": [("ô tô", 1)], "Trung": [("ô tô", .7), ("xe hơi", .3)], "Nam": [("xe hơi", .5), ("ô tô", .5)]},
     {"xe hơi": ("S51", False, True)}, "src_lang lexicon 'ô tô' (K1)"),
    ("bật thiết bị", W + r"(bật)(?= (máy lạnh|điều hòa|đèn|nhạc|đài|radio|quạt))",
     {"Bắc": [("bật", 1)], "Trung": [("bật", .8), ("mở", .2)], "Nam": [("mở", .4), ("bật", .6)]},
     {}, "src_lang lexicon 'mở/bật' (K1)"),
]

# ------------------------------------------------------------------ hồ sơ người nói (v2, phụ lục mục 3 và 6.1–6.2)
# Bắc, Nam: như v1. Trung chia theo nơi sống:
#   Trung-Huế / Trung-Nghệ / Trung-Quảng (sống ở quê): từ chức năng theo bảng có nguồn của phụ lục mục 2
#     (Đặng Diễm Đông 2024; VOH; Vinpearl; Báo Hà Tĩnh). Từ về xe giữ nguyên chữ của khung: chưa có nguồn tiểu vùng
#     (phụ lục 6.4: không tự điền, chờ bảng mục 5). Bỏ 'nghe', 'giùm', 'chừ', 'hè' (không có trong nguồn Huế đã đọc).
#   Trung-HN: từ về xe và từ chức năng theo Bắc (toàn dân), không tiểu từ quê.
#   Trung-HCM: từ về xe theo Nam; từ chức năng toàn dân, thêm 'nha', 'tui'.
PROFILES = ("Bắc", "Nam", "Trung-Huế", "Trung-Nghệ", "Trung-Quảng", "Trung-HN", "Trung-HCM")
CAR_RULES = {"điều hòa", "kính", "tắc đường", "tắc", "rẽ", "đỗ xe", "chỗ đỗ", "vòng xuyến", "gương chiếu hậu", "thay dầu", "ắc quy",
             "phanh", "ô tô", "bật thiết bị"}
SAME = [("{same}", 1)]
_QUE_COMMON = {
    "gì": [("chi", .6), ("gì", .4)], "ở đâu": [("ở mô", .6), ("ở đâu", .4)], "đâu": [("mô", .6), ("đâu", .4)],
    "tại sao": [("răng", .6), ("tại sao", .4)], "là sao": [("là răng", .6), ("là sao", .4)], "thế nào": [("ra răng", .5), ("thế nào", .5)],
    "thế cuối câu": [("rứa", .7), ("vậy", .3)], "này": [("ni", .5), ("này", .5)], "vâng": [("dạ", 1)], "bố": [("ba", .6), ("cha", .4)],
    "hỏng": [("hư", 1)], "muộn": [("trễ", .6), ("muộn", .4)], "thật": [("thiệt", .6), ("thật", .4)],
    "giúp tôi": [("giúp tôi", 1)], "tôi": [("tôi", 1)], "nhé": SAME, "nhỉ": [("", 1)], "mẹ": [("mẹ", 1)],
}
QUE = {
    "Trung-Huế": dict(_QUE_COMMON, **{"tôi": [("tui", .55), ("tôi", .45)], "giúp tôi": [("giúp tui", 1)], "mẹ": [("mạ", .8), ("mẹ", .2)],
                                     "nhé": [("nghe", 1)], "nhỉ": [("", 1)], "xem": [("coai", .25), ("xem", .75)]}),
    "Trung-Nghệ": dict(_QUE_COMMON, **{"bây giờ": [("dừ", .5), ("bây giờ", .5)]}),
    "Trung-Quảng": dict(_QUE_COMMON),
}
HN_OVERRIDE = {"nhỉ": [("", 1)]}
HCM_OVERRIDE = {"tôi": [("tôi", .6), ("tui", .4)], "giúp tôi": [("giúp tôi", .5), ("giúp tui", .5)], "nhé": [("nha", 1)],
                "thế cuối câu": [("vậy", 1)], "nhỉ": [("", 1)], "vâng": [("dạ", 1)]}
# từ mới có nguồn ở phụ lục (PL: Đặng Diễm Đông 2024 cho Huế; VOH cho Nghệ Tĩnh)
# 25/10/2026 (người dùng): bỏ hí/nở/hớ; "nghe" có nguồn Huế (Đặng Diễm Đông 2024 tr. 103), xem docs/kiem_tra_nguon_tieu_tu_Hue.md
_EXTRA_INFO = {"nhé": {"nghe": ("S52", True, True)},
               "bây giờ": {"dừ": ("S51", True, True)}, "xem": {"coai": ("S51", True, True)}}
for _r in RULES:
    _r[3].update(_EXTRA_INFO.get(_r[0], {}))


def opts_for(name, opts, profile):
    if profile in ("Bắc", "Nam"):
        return opts[profile]
    if profile == "Trung-HN":
        return HN_OVERRIDE.get(name, opts["Bắc"])
    if profile == "Trung-HCM":
        if name in CAR_RULES:
            return opts["Nam"]
        return HCM_OVERRIDE.get(name, opts["Bắc"])
    if name in CAR_RULES:
        return SAME
    return QUE[profile].get(name, SAME)


_COMPILED = [(name, re.compile(pat), opts, info, srcs) for name, pat, opts, info, srcs in RULES]


def _pick(rng, pairs):
    r = rng.random() * sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if r <= acc:
            return v
    return pairs[-1][0]


def rewrite(text, profile, rng, skip=(), memo=None):
    """Viết lại chữ cố định theo hồ sơ người nói (PROFILES; 'Trung' cũ được hiểu là Trung-Quảng). Trả (text, [Mark]).
    memo: dict dùng chung trong một câu để cùng một khái niệm chọn cùng một từ."""
    if profile == "Trung":
        profile = "Trung-Quảng"
    marks = []
    memo = {} if memo is None else memo
    for name, rx, opts, info, _ in _COMPILED:
        if name in skip:
            continue

        def rep(m):
            if name not in memo:
                memo[name] = _pick(rng, opts_for(name, opts, profile))
            choice = memo[name]
            if choice == "{same}":
                choice = m.group(0)
            elif "{0}" in choice:
                choice = choice.replace("{0}", m.group(1))
            # ghi nhận từ vùng
            key = choice.split()[-1] if name == "chỗ đỗ" else choice
            if key in info:
                f, ver, reg = info[key]
                marks.append(Mark(key, name, f, ver, reg))
            # giữ chữ hoa đầu nếu bản gốc viết hoa
            if m.group(0)[:1].isupper():
                choice = choice[:1].upper() + choice[1:]
            return choice
        text = rx.sub(rep, text)
    text = re.sub(r"\s+([,.?!])", r"\1", re.sub(r"  +", " ", text))   # khi tiểu từ bị bỏ (nhỉ -> '')
    return text, marks


# ------------------------------------------------------------------ trang trí theo vùng (src_lang particles)
PREFIX = {
    # 'làm ơn' giảm từ 8–10% xuống 2% (góp ý v1 mục 3: 'Làm ơn' chiếm 5,3% câu, mục tiêu khoảng 1%)
    # 25/10/2026 (người dùng): bỏ hẳn từ đệm/tiếng gọi đầu câu (ờ, ê, nè, nì, này, bạn ơi) — 0/127 lệnh 'seen' có;
    # phần tỷ lệ đó dồn vào "" (không tiền tố).
    "Bắc": [("", .84), ("làm ơn ", .02), ("cho tôi ", .06), ("giúp tôi ", .08)],
    "Trung": [("", .80), ("làm ơn ", .02), ("cho tui ", .08), ("giúp tui ", .1)],
    "Nam": [("", .82), ("làm ơn ", .02), ("cho tui ", .08), ("giúp tui ", .08)],
}
SUFFIX_CMD = {
    "Bắc": [("", .52), (" nhé", .2), (" đi", .1), (" với", .06), (" hộ tôi", .04), (" giúp tôi", .04), (" luôn", .02), (" ngay", .02)],
    "Trung": [("", .55), (" nghe", .14), (" đi", .12), (" giùm", .08), (" với", .06), (" luôn", .05)],
    "Nam": [("", .5), (" nha", .2), (" nghen", .06), (" đi", .08), (" giùm", .05), (" dùm", .04), (" luôn", .04), (" đi nha", .03)],
}
SUFFIX_Q = {
    "Bắc": [("", .6), (" nhỉ", .12), (" thế", .12), (" ạ", .1), (" à", .06)],
    "Trung": [("", .68), (" rứa", .12), (" hè", .08), (" ạ", .12)],
    "Nam": [("", .58), (" vậy", .16), (" ta", .08), (" ạ", .1), (" hả", .08)],
}
SUFFIX_ANS = {
    "Bắc": [("", .7), (" nhé", .15), (" ạ", .15)],
    "Trung": [("", .8), (" ạ", .2)],
    "Nam": [("", .7), (" nha", .2), (" ạ", .1)],
}
# v2: bảng theo hồ sơ người nói. 'Trung' cũ (nghe, giùm, hè, nì) không dùng nữa (phụ lục 6.2).
_TQ_PREFIX = [("", .82), ("làm ơn ", .02), ("cho tôi ", .08), ("giúp tôi ", .08)]
PREFIX.update({
    "Trung-Huế": [("", .82), ("làm ơn ", .02), ("cho tui ", .08), ("giúp tui ", .08)],
    "Trung-Nghệ": _TQ_PREFIX, "Trung-Quảng": _TQ_PREFIX,
    "Trung-HN": [("", .82), ("làm ơn ", .02), ("cho tôi ", .08), ("giúp tôi ", .08)],
    "Trung-HCM": [("", .80), ("làm ơn ", .02), ("cho tui ", .08), ("giúp tui ", .06), ("cho tôi ", .04)],
})
_TQ_CMD = [("", .68), (" đi", .16), (" với", .1), (" luôn", .06)]
SUFFIX_CMD.update({
    "Trung-Huế": [("", .6), (" nghe", .22), (" đi", .1), (" với", .05), (" luôn", .03)],
    "Trung-Nghệ": _TQ_CMD, "Trung-Quảng": _TQ_CMD,
    "Trung-HN": [("", .6), (" nhé", .12), (" đi", .14), (" với", .08), (" luôn", .03), (" giúp tôi", .03)],
    "Trung-HCM": [("", .58), (" nha", .16), (" đi", .12), (" với", .08), (" luôn", .06)],
})
_TQ_Q = [("", .7), (" rứa", .15), (" ạ", .15)]
SUFFIX_Q.update({
    "Trung-Huế": [("", .7), (" rứa", .2), (" ạ", .1)],
    "Trung-Nghệ": _TQ_Q, "Trung-Quảng": _TQ_Q,
    "Trung-HN": [("", .7), (" ạ", .15), (" à", .1), (" thế", .05)],
    "Trung-HCM": [("", .68), (" vậy", .16), (" ạ", .16)],
})
for _p in ("Trung-Huế", "Trung-Nghệ", "Trung-Quảng", "Trung-HN", "Trung-HCM"):
    SUFFIX_ANS[_p] = [("", .8), (" ạ", .2)]
WAKE = ["trợ lý ơi, ", "này trợ lý, "]   # 25/10/2026: không còn dùng (wake_p = 0 trong build10k); từ đánh thức thêm bằng ghép âm thanh

# từ cuối câu đã là tiểu từ -> không thêm nữa
PARTICLES_END = {"nhé", "nha", "nghen", "nghe", "đi", "với", "giùm", "dùm", "luôn", "ngay", "nhỉ", "thế", "vậy", "rứa", "hè", "ta",
                 "ạ", "à", "hả", "hen", "thôi", "nào", "cơ", "đã", "chứ", "không", "chưa", "đâu", "mô", "nữa", "lắm", "quá",
                 "hí", "nở", "hớ"}

# tiểu từ/xưng hô theo vùng (để nhận S52 trong câu đã trang trí) và mức xác minh
# True = có nguồn đọc được (L*); "medium" = chỉ K1 mức trung bình; "low" = K1 mức thấp hoặc do bộ sinh suy ra
PARTICLE_INFO = {
    "nhé": "medium", "nha": True, "nghen": "medium", "nghe": True, "hộ": "medium", "giùm": "medium", "dùm": "medium", "hen": "medium",
    "hè": True, "rứa": True, "ta": "low", "ạ": True, "nhỉ": "medium", "thế": True, "vậy": True, "hả": "medium", "dạ": True,
    "vâng": True, "ê": "low", "nè": True, "nì": "low", "tui": True, "hông": "medium",
    # tiểu từ chung toàn quốc, không coi là từ vùng
    "à": True, "luôn": True, "đi": True, "với": True, "ngay": True,
    # Huế, có nguồn: Đặng Diễm Đông 2024 (phụ lục mục 2)
    "hí": True, "nở": True, "hớ": True,
}
# từ vùng mức thấp (src_lang confidence low hoặc không có trong src_lang)
LOW_WORDS = {"nghe", "dượng", "thím Ba", "u", "thầy u", "vỏ xe"}
REGIONAL_PARTICLES = {"Bắc": {"nhé", "nhỉ", "hộ", "vâng", "thế"}, "Nam": {"nha", "nghen", "giùm", "dùm", "hen", "ta", "nè", "tui", "dạ"},
                      "Trung": {"nghe", "rứa", "hè", "giùm", "tui", "nì", "dạ"},
                      "Trung-Huế": {"nghe", "rứa", "tui", "dạ"}, "Trung-Nghệ": {"rứa", "dạ"}, "Trung-Quảng": {"rứa", "dạ"},
                      "Trung-HN": {"nhé", "thế"}, "Trung-HCM": {"nha", "tui"}}


# động từ mở đầu câu lệnh: chỉ khi câu bắt đầu bằng các từ này mới thêm 'giúp tôi/cho tôi/làm ơn' và tiểu từ cuối câu lệnh
VERBS = set("""dẫn chỉ đưa tìm bật tắt mở đóng gọi nhắn gửi đặt chỉnh tăng giảm hạ kéo phát chuyển đọc nhắc thêm xóa hủy dừng lưu kiểm
đổi chọn khóa gập phóng thu xem tránh ghé đi về sạc hẹn bấm quay chia trả nghe kể tính báo tua bỏ lặp sấy dò ngắt kết liên mời dời
tải thử đánh thả nâng đẩy hé phun giữ điều hiện hiển tra tạo nói cập hiện lấy làm thoát né đồng soạn quét vặn rút sửa cài
thắt nhả hiện ưu""".split())
# cụm mở đầu là danh từ dù từ đầu có thể là động từ: không coi là câu bắt đầu bằng động từ (góp ý v1 mục 3, 'cảnh báo')
NOUN_START = re.compile(r"^\s*(cảnh báo|điều hòa|báo thức|chỉ số|kết quả|đồng hồ|hiện tại|thu phí|chỉ dẫn|đèn báo|tin nhắn|lịch hẹn|"
                        r"giới hạn|ưu đãi|liên hệ|kết nối wifi)(?![\wÀ-ỹ])", re.I)
HELP_WORDS = re.compile(r"(?<![\wÀ-ỹ])(giúp|giùm|dùm|hộ)(?![\wÀ-ỹ])")
VOCATIVE_PREFIX = {"bạn ơi, ", "này, ", "ê, ", "nè, ", "nì, ", "ờ, "}


def first_word(s):
    m = re.match(r"\s*([\wÀ-ỹ]+)", s)
    return m.group(1).lower() if m else ""


def decorate(body, act, region, rng, allow_prefix=True, wake_p=0.05, allow_suffix=True):
    """Thêm tiền tố, tiểu từ cuối câu, từ đánh thức. Trả (text, [tiểu từ đã thêm], has_wake).
    region: hồ sơ người nói (PROFILES); 'Trung' cũ được hiểu là Trung-Quảng."""
    if region == "Trung":
        region = "Trung-Quảng"
    added = []
    starts_verb = first_word(body) in VERBS and not NOUN_START.match(body)
    has_help = bool(HELP_WORDS.search(body))
    # không thêm từ đánh thức khi khung đã gọi 'trợ lý' (góp ý v1 mục 3)
    wake = rng.choice(WAKE) if (act != "Trả lời ngắn" and "trợ lý" not in body.lower() and rng.random() < wake_p) else ""
    pre = ""
    if allow_prefix and act == "Lệnh":
        pre = _pick(rng, PREFIX[region])
        if pre and pre not in VOCATIVE_PREFIX:          # giúp tôi/cho tôi/làm ơn: chỉ trước động từ, không lặp 'giúp'
            if not starts_verb or (has_help and pre.startswith(("giúp", "cho"))) or re.search(r"(tôi|tui|mình)", body[:15]):
                pre = ""
        if wake and pre in VOCATIVE_PREFIX:              # không gọi hai lần
            pre = ""
    last = re.sub(r"[^\wÀ-ỹ ⟦⟧]", "", body).split()[-1:] or [""]
    suf = ""
    multi_clause = "," in body
    desire = first_word(body) in ("tôi", "tui", "mình", "con")      # 'tôi muốn ...': không thêm 'đi/nhé'
    if allow_suffix and last[0].lower() not in PARTICLES_END and not multi_clause and not (desire and act in ("Lệnh", "Câu cụt")):
        if act == "Lệnh" or (act == "Câu cụt" and starts_verb):
            suf = _pick(rng, SUFFIX_CMD[region])
            if suf.strip() in ("giùm", "dùm", "hộ tôi", "giúp tôi") and (has_help or pre.startswith(("giúp", "cho"))):
                suf = ""
        elif act == "Câu hỏi":
            suf = _pick(rng, SUFFIX_Q[region])
            if suf == " ta" and last[0].startswith("⟦"):
                suf = ""
        elif act == "Trả lời ngắn":
            suf = _pick(rng, SUFFIX_ANS[region])
    if act == "Câu hỏi" and suf == "" and region == "Nam" and re.search(r"(?<![\wÀ-ỹ])không$", body) and rng.random() < 0.2:
        body = re.sub(r"không$", "hông", body)
        added.append("hông")
    if suf.strip() and re.search(r"(?<![\wÀ-ỹ])" + re.escape(suf.strip()) + r"(?![\wÀ-ỹ])", body):
        suf = ""
    for p in (pre, suf):
        for w in re.sub(r"[,]", " ", p).split():
            if w in PARTICLE_INFO:
                added.append(w)
    return wake + pre + body + suf, added, bool(wake)


# từ của vùng khác không được xuất hiện trong phần chữ cố định (kiểm lẫn vùng; không áp cho tên riêng/địa chỉ)
FORBIDDEN = {
    "Bắc": ["kiếng", "quẹo", "đậu xe", "kẹt xe", "tui", "nha", "nghen", "giùm", "dùm", "rứa", "chừ", "ở mô", "hông", "máy lạnh", "mạ",
            "vòng xoay", "bùng binh", "thiệt", "hoài", "tía", "hè", "là răng", "ra răng", "thắng", "vô"],
    "Nam": ["rứa", "chừ", "ở mô", "mạ", "vâng", "tắc đường", "vòng xuyến", "hè", "là răng", "ra răng", "u", "nhé", "hộ tôi", "nì"],
    "Trung": ["tía", "u", "thầy u", "nghen", "vòng xuyến", "hộ tôi", "nhỉ", "hen", "dùm"],
}
_TQ_FORB = ["tía", "u", "thầy u", "nghen", "nha", "hen", "dùm", "giùm", "hộ tôi", "nhỉ", "chừ", "nì", "hè"]   # không chặn 'nghe' (cũng là động từ)
FORBIDDEN.update({"Trung-Huế": _TQ_FORB, "Trung-Nghệ": _TQ_FORB + ["tui"], "Trung-Quảng": _TQ_FORB + ["tui"],
                  "Trung-HN": FORBIDDEN["Bắc"], "Trung-HCM": FORBIDDEN["Nam"] + ["nghen", "dùm", "giùm"]})
_FORB = {r: [re.compile(W + re.escape(w) + E) for w in ws] for r, ws in FORBIDDEN.items()}


def forbidden_hits(text, profile):
    return [rx.pattern for rx in _FORB[profile] if rx.search(text)]
