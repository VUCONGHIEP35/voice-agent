# -*- coding: utf-8 -*-
"""Đọc số tiếng Việt theo vùng (Bắc / Trung / Nam).

Quy tắc theo vùng (chọn theo sources/src_lang.json, number_rules, nguồn L5 Wikipedia
'Vietnamese numerals' và L14 Migaku; người dùng chọn nguồn này thay cho bảng trong CLAUDE.md):
  - số 0 ở hàng chục: 'linh' (Bắc), 'lẻ' (Trung, Nam)          105 -> một trăm linh/lẻ năm
  - hàng nghìn: 'nghìn' (Bắc), 'ngàn' (Trung, Nam)
Quy tắc chung: mười, mười lăm, hai mươi mốt, hai mươi tư, hai mươi lăm, mười bốn.
Số điện thoại và 113/114/115 đọc từng chữ số.
"""
import re

DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
REGIONS = ("Bắc", "Trung", "Nam")


def linh_word(region):
    return "linh" if region == "Bắc" else "lẻ"


def nghin_word(region):
    return "nghìn" if region == "Bắc" else "ngàn"


def _below_100(n, after_hundred, region):
    """n < 100. after_hundred: đứng sau hàng trăm (kể cả 'không trăm')."""
    t, u = divmod(n, 10)
    if t == 0:
        if u == 0:
            return []
        return [linh_word(region), DIG[u]] if after_hundred else [DIG[u]]
    w = ["mười"] if t == 1 else [DIG[t], "mươi"]
    if u == 0:
        return w
    if u == 5:
        return w + ["lăm"]
    if u == 1 and t >= 2:
        return w + ["mốt"]
    if u == 4 and t >= 2:
        return w + ["tư"]
    return w + [DIG[u]]


def _group(n, leading, region):
    """n < 1000; leading=False thì nhóm đứng sau nhóm lớn hơn (đọc 'không trăm')."""
    h, rest = divmod(n, 100)
    w = []
    if h > 0 or not leading:
        w += [DIG[h], "trăm"]
        w += _below_100(rest, True, region)
    else:
        w += _below_100(rest, False, region)
    return w


def read_int(n, region="Bắc"):
    """Đọc số nguyên không âm (< 10^12)."""
    if n < 0:
        return "âm " + read_int(-n, region)
    if n == 0:
        return "không"
    if n >= 10 ** 12:
        raise ValueError(n)
    units = ["", nghin_word(region), "triệu", "tỷ"]
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000
    out = []
    top = len(groups) - 1
    for i in range(top, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        out += _group(g, i == top, region)
        if units[i]:
            out.append(units[i])
    return " ".join(out)


def read_digits(s):
    """Đọc từng chữ số; khoảng trắng trong chuỗi số thành dấu phẩy ngắt nhóm."""
    groups = [g for g in re.split(r"[\s.\-]+", s.strip()) if g]
    return ", ".join(" ".join(DIG[int(c)] for c in g if c.isdigit()) for g in groups)


def read_decimal(s, region="Bắc"):
    """'22,5' -> 'hai mươi hai phẩy năm'. Phần thập phân đọc từng chữ số nếu bắt đầu bằng 0,
    ngược lại đọc như số (0,25 -> không phẩy hai mươi lăm)."""
    ip, fp = s.replace(".", ",").split(",")
    left = read_int(int(ip), region)
    if fp.startswith("0") or len(fp) > 2:
        right = " ".join(DIG[int(c)] for c in fp)
    else:
        right = read_int(int(fp), region)
    return f"{left} phẩy {right}"


def read_money(n, region="Bắc"):
    return read_int(n, region)


def fmt_money(n):
    """1500000 -> '1.500.000' (dấu chấm phân cách nghìn)."""
    return f"{n:,}".replace(",", ".")


def fmt_dec(x, places=1):
    return f"{x:.{places}f}".replace(".", ",")


# ------------------------------------------------------------------ chuẩn hóa chuỗi viết -> nói
LETTER = {"A": "a", "B": "bê", "C": "xê", "D": "đê", "Đ": "đê", "E": "e", "F": "ép", "G": "giê", "H": "hát", "I": "i",
          "J": "gi", "K": "ca", "L": "e lờ", "M": "em", "N": "en", "O": "ô", "P": "pê", "Q": "quy", "R": "e rờ", "S": "ét",
          "T": "tê", "U": "u", "V": "vê", "W": "vê kép", "X": "ích xì", "Y": "i dài", "Z": "dét"}

# viết tắt -> (đọc, mức chắc chắn); 'low' sẽ gắn cờ cần duyệt
ABBR = {
    "VOV": ("vê ô vê", "medium"), "VOH": ("vê ô hát", "low"), "FM": ("ép em", "medium"), "USB": ("u ét bê", "medium"),
    "A/C": ("a xê", "low"), "GPS": ("gi pi ét", "low"), "BOT": ("bốt", "low"), "AQI": ("a quy i", "low"),
    "USD": ("u ét đê", "low"), "VND": ("vê en đê", "low"), "ABS": ("a bê ét", "low"), "ODO": ("ô đô", "low"),
    "Odo": ("ô đô", "low"), "TP.HCM": ("thành phố Hồ Chí Minh", "high"), "PM2.5": ("pê em hai chấm năm", "low"),
    "CSGT": ("cảnh sát giao thông", "medium"), "MHz": ("mê ga héc", "high"), "kWh": ("ki lô oát giờ", "medium"),
    "km/h": ("ki lô mét trên giờ", "high"), "km": ("ki lô mét", "high"), "°C": ("độ xê", "medium"), "kW": ("ki lô oát", "medium"),
    "QL": ("quốc lộ", "high"), "ATM": ("a tê em", "low"), "SOS": ("ét ô ét", "low"), "AI": ("a i", "low"),
}
EMERGENCY = {"113", "114", "115"}


class Norm:
    """Kết quả chuẩn hóa: text nói + danh sách cờ (viết tắt chưa chắc...)."""

    def __init__(self, text, flags, feats):
        self.text, self.flags, self.feats = text, flags, feats


def normalize(raw, region="Bắc"):
    """Chuẩn hóa phần chữ cố định của khung câu (không áp cho giá trị khe đã có cách đọc riêng)."""
    flags, feats = set(), set()
    t = raw

    def sub(pat, fn, s):
        return re.sub(pat, fn, s)

    # số điện thoại 4-3-3
    def ph(m):
        feats.update({"số điện thoại", "số"})
        return read_digits(m.group(0))
    t = sub(r"\b0\d{3} \d{3} \d{3}\b", ph, t)

    # số khẩn cấp
    def em(m):
        feats.add("số")
        return read_digits(m.group(0))
    t = sub(r"(?<![\d,.])\b(113|114|115)\b(?!\d|[,.]\d)", em, t)

    # tần số FM x MHz
    def fm(m):
        feats.update({"tần số/công suất", "số", "đơn vị đo", "viết tắt"})
        v = m.group(1)
        num = read_decimal(v, region) if "," in v else read_int(int(v), region)
        return f"ép em {num} mê ga héc"
    t = sub(r"\bFM (\d+(?:,\d)?) MHz\b", fm, t)

    # viết tắt có chữ số
    for k in ("PM2.5",):
        if k in t:
            t = t.replace(k, ABBR[k][0])
            feats.add("viết tắt")
            flags.add(f"cách đọc viết tắt chưa xác minh: {k}")

    # tiền có dấu chấm nghìn
    def money(m):
        feats.update({"số"})
        return read_int(int(m.group(0).replace(".", "")), region)
    t = sub(r"\b\d{1,3}(?:\.\d{3})+\b", money, t)

    # thập phân
    def dec(m):
        feats.add("số")
        return read_decimal(m.group(0), region)
    t = sub(r"\b\d+,\d+\b", dec, t)

    # phần trăm
    def pct(m):
        feats.update({"phần trăm", "số"})
        return f"{m.group(1)} phần trăm"
    t = sub(r"(\S+?)\s?%", pct, t)

    # x (nhân) giữa hai số
    t = sub(r"(?<=\d) x (?=\d)", " nhân ", t)

    # độ C viết liền sau số
    if "°C" in t:
        t = t.replace("°C", " độ xê")
        feats.update({"đơn vị đo", "viết tắt"})

    # số nguyên còn lại
    def integer(m):
        feats.add("số")
        return read_int(int(m.group(0)), region)
    t = sub(r"\b\d+\b", integer, t)

    # viết tắt (dài trước, ngắn sau)
    for k in sorted(ABBR, key=len, reverse=True):
        if k == "PM2.5":
            continue
        pat = r"(?<![\wÀ-ỹ])" + re.escape(k) + r"(?![\wÀ-ỹ])"
        if re.search(pat, t):
            say, conf = ABBR[k]
            t = re.sub(pat, say, t)
            if k not in ("km", "km/h", "MHz", "QL", "TP.HCM"):
                feats.add("viết tắt")
            if k in ("km", "km/h", "kWh", "MHz", "°C", "kW"):
                feats.add("đơn vị đo")
            if conf == "low":
                flags.add(f"cách đọc viết tắt chưa xác minh: {k}")
    t = re.sub(r"\s+", " ", t).strip()
    return Norm(t, flags, feats)


def has_digit(s):
    return any(ch.isdigit() for ch in s)
