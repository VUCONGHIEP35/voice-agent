# -*- coding: utf-8 -*-
"""Lõi sinh câu: chuẩn hóa số/đơn vị tiếng Việt, động cơ mẫu câu, từ vựng vùng, trang trí câu."""
import random, re

DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

# biến thể vùng
VARIANTS = ["Chuẩn chung", "Bắc", "Trung", "Nam"]


class Ctx:
    def __init__(self, rng, variant):
        self.rng = rng
        self.v = variant

    @property
    def linh(self):
        return "linh" if self.v == "Nam" else "lẻ"

    def nghin(self):
        if self.v == "Nam":
            return "ngàn"
        if self.v == "Trung":
            return "ngàn" if self.rng.random() < 0.5 else "nghìn"
        return "nghìn"

    def tu(self):
        return "tư" if self.rng.random() < 0.5 else "bốn"


def _three(n, c, lead):
    h, rest = divmod(n, 100)
    t, u = divmod(rest, 10)
    w = []
    if h > 0 or not lead:
        w += [DIG[h], "trăm"]
    if t == 0:
        if u > 0:
            if h > 0 or not lead:
                w += [c.linh, DIG[u]]
            else:
                w += [DIG[u]]
    elif t == 1:
        w.append("mười")
        if u == 5:
            w.append("lăm")
        elif u > 0:
            w.append(DIG[u])
    else:
        w += [DIG[t], "mươi"]
        if u == 1:
            w.append("mốt")
        elif u == 4:
            w.append(c.tu())
        elif u == 5:
            w.append("lăm")
        elif u > 0:
            w.append(DIG[u])
    return w


def vn_int(n, c):
    """Đọc số nguyên không âm."""
    if n == 0:
        return "không"
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000
    names = ["", c.nghin(), "triệu", "tỷ"]
    out = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        lead = (i == len(groups) - 1)
        out += _three(g, c, lead)
        if i > 0:
            out.append(c.nghin() if i == 1 else names[i])
    return " ".join(out)


def vn_digits(s):
    return " ".join(DIG[int(ch)] for ch in s if ch.isdigit())


def vn_dec(x, c, places=1):
    """x float -> '22,5' và 'hai mươi hai phẩy năm'."""
    s = f"{x:.{places}f}"
    ip, fp = s.split(".")
    raw = ip + "," + fp
    spoken = vn_int(int(ip), c) + " phẩy " + vn_digits(fp)
    return raw, spoken


def vn_money(n, c):
    raw = f"{n:,}".replace(",", ".")
    return raw, vn_int(n, c)


def phone_number(rng):
    pref = rng.choice(["090", "091", "093", "094", "096", "097", "098", "086", "088", "089", "032", "033", "034", "035", "036", "037", "038", "039", "070", "076", "077", "078", "079", "081", "082", "083", "084", "085", "056", "058", "059"])
    rest = "".join(str(rng.randint(0, 9)) for _ in range(7))
    num = pref + rest
    raw = f"{num[:4]} {num[4:7]} {num[7:]}"
    spoken = f"{vn_digits(num[:4])}, {vn_digits(num[4:7])}, {vn_digits(num[7:])}"
    return raw, spoken


# ---------------------------------------------------------------- từ vựng vùng
# concept -> {variant: [words]}  (danh sách = chọn ngẫu nhiên)
LEX = {
    "ac": {"Chuẩn chung": ["điều hòa"], "Bắc": ["điều hòa"], "Nam": ["máy lạnh"], "Trung": ["máy lạnh"]},
    "win": {"Chuẩn chung": ["kính"], "Bắc": ["kính"], "Nam": ["kiếng"], "Trung": ["kính"]},
    "jam": {"Chuẩn chung": ["tắc đường"], "Bắc": ["tắc đường"], "Nam": ["kẹt xe"], "Trung": ["kẹt xe"]},
    "turn": {"Chuẩn chung": ["rẽ"], "Bắc": ["rẽ"], "Nam": ["quẹo"], "Trung": ["rẽ"]},
    "park": {"Chuẩn chung": ["đỗ xe"], "Bắc": ["đỗ xe"], "Nam": ["đậu xe"], "Trung": ["đậu xe"]},
    "gas": {"Chuẩn chung": ["trạm xăng"], "Bắc": ["cây xăng"], "Nam": ["cây xăng"], "Trung": ["cây xăng"]},
    "round": {"Chuẩn chung": ["vòng xuyến"], "Bắc": ["vòng xuyến"], "Nam": ["vòng xoay"], "Trung": ["vòng xoay"]},
    "yes": {"Chuẩn chung": ["vâng"], "Bắc": ["vâng"], "Nam": ["dạ"], "Trung": ["dạ"]},
    "where": {"Chuẩn chung": ["ở đâu"], "Bắc": ["ở đâu"], "Nam": ["ở đâu"], "Trung": ["ở mô"]},
    "now": {"Chuẩn chung": ["bây giờ"], "Bắc": ["bây giờ"], "Nam": ["bây giờ"], "Trung": ["chừ"]},
    "thus": {"Chuẩn chung": ["vậy"], "Bắc": ["thế"], "Nam": ["vậy"], "Trung": ["rứa"]},
    "why": {"Chuẩn chung": ["sao"], "Bắc": ["sao"], "Nam": ["sao"], "Trung": ["răng"]},
    "this": {"Chuẩn chung": ["này"], "Bắc": ["này"], "Nam": ["này"], "Trung": ["ni"]},
    "I": {"Chuẩn chung": ["tôi"], "Bắc": ["tôi", "mình"], "Nam": ["tui"], "Trung": ["tui"]},
    "lane": {"Chuẩn chung": ["làn đường"], "Bắc": ["làn đường"], "Nam": ["làn xe"], "Trung": ["làn đường"]},
    "help": {"Chuẩn chung": ["giúp"], "Bắc": ["giúp"], "Nam": ["giùm"], "Trung": ["giùm"]},
    "mom": {"Chuẩn chung": ["mẹ"], "Bắc": ["mẹ", "u"], "Nam": ["má"], "Trung": ["mạ"]},
    "dad": {"Chuẩn chung": ["bố"], "Bắc": ["bố", "thầy"], "Nam": ["ba", "tía"], "Trung": ["ba"]},
    "ok": {"Chuẩn chung": ["được rồi"], "Bắc": ["được rồi"], "Nam": ["được rồi"], "Trung": ["được rồi"]},
}
# từ dùng riêng từng vùng: để kiểm tra lẫn vùng (không được xuất hiện ở biến thể khác)
REGION_MARKERS = {
    "Nam": ["kiếng", "máy lạnh", "kẹt xe", "quẹo", "đậu xe", "vòng xoay", "hẻm", "giùm", "tui", "nha ", "nghen", "dạ ", " má", " tía", "bùng binh"],
    "Bắc": ["điều hòa", "tắc đường", "ngõ ", "vâng", "nhỉ", " thế", " thầy"],
    "Trung": ["chừ", " mô", "rứa", "răng", "mạ", " ni", "kiệt", "nghe ", " hí", "tê "],
}


def lex_resolve(text, c):
    def rep(m):
        key = m.group(1)
        opts = LEX[key][c.v]
        return c.rng.choice(opts)
    return re.sub(r"\{L:(\w+)\}", rep, text)


def resolve_alts(text, c):
    """Giải '(a|b|)' lặp cho tới khi không còn."""
    pat = re.compile(r"\(([^()]*\|[^()]*)\)")
    for _ in range(10):
        m = pat.search(text)
        if not m:
            break
        opts = m.group(1).split("|")
        text = text[:m.start()] + c.rng.choice(opts) + text[m.end():]
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- trang trí
PREFIX = {
    "Chuẩn chung": [("", 0.60), ("làm ơn ", 0.12), ("giúp tôi ", 0.14), ("cho tôi ", 0.08), ("hãy ", 0.06)],
    "Bắc": [("", 0.58), ("làm ơn ", 0.12), ("giúp tôi ", 0.14), ("bạn ơi, ", 0.08), ("cho tôi ", 0.08)],
    "Nam": [("", 0.58), ("làm ơn ", 0.10), ("giúp tui ", 0.12), ("cho tui ", 0.12), ("bạn ơi, ", 0.08)],
    "Trung": [("", 0.60), ("làm ơn ", 0.12), ("giúp tui ", 0.14), ("cho tui ", 0.14)],
}
SUFFIX_CMD = {
    "Chuẩn chung": [("", 0.55), (" nhé", 0.15), (" giúp tôi", 0.10), (" ngay", 0.05), (" đi", 0.05), (" với", 0.10)],
    "Bắc": [("", 0.50), (" nhé", 0.22), (" đi", 0.10), (" giúp tôi", 0.08), (" với", 0.10)],
    "Nam": [("", 0.50), (" nha", 0.22), (" nghen", 0.08), (" giùm", 0.08), (" đi", 0.06), (" dùm", 0.06)],
    "Trung": [("", 0.52), (" nghe", 0.18), (" giùm", 0.10), (" hí", 0.10), (" đi", 0.10)],
}
SUFFIX_Q = {
    "Chuẩn chung": [("", 0.60), (" vậy", 0.20), (" ạ", 0.20)],
    "Bắc": [("", 0.55), (" nhỉ", 0.15), (" thế", 0.15), (" ạ", 0.15)],
    "Nam": [("", 0.55), (" vậy", 0.20), (" ta", 0.10), (" ạ", 0.15)],
    "Trung": [("", 0.60), (" rứa", 0.25), (" ạ", 0.15)],
}
WAKE = "trợ lý ơi, "


def pick_w(rng, pairs):
    r = rng.random()
    acc = 0
    for v, w in pairs:
        acc += w
        if r <= acc:
            return v
    return pairs[-1][0]


def decorate(text, act, c, allow_prefix=True, allow_suffix=True, wake_p=0.08):
    rng = c.rng
    pre = ""
    if allow_prefix and act in ("Lệnh",):
        pre = pick_w(rng, PREFIX[c.v])
    suf = ""
    if allow_suffix:
        if act in ("Lệnh", "Câu cụt"):
            suf = pick_w(rng, SUFFIX_CMD[c.v])
        elif act == "Câu hỏi":
            suf = pick_w(rng, SUFFIX_Q[c.v])
    wake = WAKE if rng.random() < wake_p else ""
    body = pre + text + suf
    out = wake + body
    return out


def finish(text, act):
    t = text.strip()
    t = t[0].upper() + t[1:]
    if act == "Câu hỏi":
        t += "?"
    elif act == "Kêu cứu":
        t += "!"
    else:
        t += "."
    return t


def asr_norm(text):
    t = text.lower()
    t = re.sub(r"[\.,;:!?\"“”()\[\]]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def syllables(text):
    return len(re.sub(r"[\.,;:!?]", " ", text).split())
