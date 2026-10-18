# -*- coding: utf-8 -*-
"""Đọc số, giờ, ngày, tiền, tần số tiếng Việt theo vùng.
Nguồn quy tắc: Wikipedia 'Vietnamese numerals' (mốt/lăm/tư/mươi; linh miền Bắc, lẻ miền Nam và Trung; nghìn miền Bắc, ngàn miền Nam)
và Wiktionary (lẻ: chủ yếu miền Nam). Các quy tắc này cần người bản ngữ xác nhận."""

D = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def zero_word(region):
    """chữ số 0 trong số trăm/nghìn: Bắc 'linh', Trung và Nam 'lẻ'."""
    return "linh" if region == "Bắc" else "lẻ"


def thousand_word(region):
    return "nghìn" if region in ("Bắc", "Trung") else "ngàn"


def _two(n, tu=False):
    """10..99 (đọc đầy đủ)."""
    t, u = divmod(n, 10)
    if t == 1:
        s = "mười"
    else:
        s = D[t] + " mươi"
    if u == 0:
        return s
    if u == 1:
        return s + (" một" if t == 1 else " mốt")
    if u == 4:
        return s + (" tư" if (tu and t >= 2) else " bốn")
    if u == 5:
        return s + " lăm"
    return s + " " + D[u]


def _hundreds(n, region, lead_zero_hundred=False, tu=False):
    """1..999. lead_zero_hundred: đọc 'không trăm' khi n<100 và đứng sau nghìn/triệu."""
    h, r = divmod(n, 100)
    parts = []
    if h > 0:
        parts.append(D[h] + " trăm")
    elif lead_zero_hundred:
        parts.append("không trăm")
    if r == 0:
        return " ".join(parts)
    if r < 10:
        if h > 0 or lead_zero_hundred:
            parts.append(zero_word(region))
        parts.append(D[r])
    else:
        parts.append(_two(r, tu))
    return " ".join(parts)


def cardinal(n, region="Bắc", tu=False):
    """Đọc số nguyên 0 <= n < 10^9."""
    assert 0 <= n < 10 ** 9
    if n == 0:
        return "không"
    if n < 10:
        return D[n]
    if n < 100:
        return _two(n, tu)
    if n < 1000:
        return _hundreds(n, region, tu=tu)
    parts = []
    tw = thousand_word(region)
    for unit, name in ((10 ** 6, "triệu"), (10 ** 3, tw)):
        pass
    mil, rest = divmod(n, 10 ** 6)
    th, rest = divmod(rest, 1000)
    started = False
    if mil:
        parts.append(_hundreds(mil, region, tu=tu) + " triệu")
        started = True
    if th:
        parts.append(_hundreds(th, region, lead_zero_hundred=False, tu=tu) + " " + tw)
        started = True
    if rest:
        if started and rest < 100:
            parts.append(_hundreds(rest, region, lead_zero_hundred=True, tu=tu))
        else:
            parts.append(_hundreds(rest, region, tu=tu))
    return " ".join(parts)


def digits(s):
    """Đọc từng chữ số (số điện thoại, mã). Nhóm cách nhau bằng dấu cách trong s -> dấu phẩy."""
    out = []
    for grp in s.split():
        out.append(" ".join(D[int(c)] for c in grp))
    return ", ".join(out)


def decimal(x_int, x_frac, region="Bắc"):
    """x_int,x_frac như '2' và '5' -> 'hai phẩy năm'."""
    return cardinal(int(x_int), region) + " phẩy " + " ".join(D[int(c)] for c in x_frac)


def hour_min(h, m, region="Bắc", style="full"):
    """style: full ('chín giờ ba mươi'), phut ('chín giờ ba mươi phút'), ruoi (chỉ khi m=30)."""
    hs = cardinal(h, region)
    if m == 0:
        return hs + " giờ"
    if m == 30 and style == "ruoi":
        return hs + " rưỡi"
    ms = cardinal(m, region) if m >= 10 else zero_word(region) + " " + D[m]
    if style == "phut" or m < 10:
        return f"{hs} giờ {ms} phút"
    return f"{hs} giờ {ms}"


MONTH = {1: "một", 2: "hai", 3: "ba", 4: "tư", 5: "năm", 6: "sáu", 7: "bảy", 8: "tám", 9: "chín", 10: "mười", 11: "mười một", 12: "mười hai"}


def date_dm(d, m, region="Bắc"):
    return f"ngày {cardinal(d, region)} tháng {MONTH[m]}"


def money_vnd(n, region="Bắc"):
    return cardinal(n, region) + " đồng"


# kiểm ngược: từ chữ về số, để kiểm tra bộ đọc
_W = {w: i for i, w in enumerate(D)}


def parse(s):
    """Phân tích ngược chuỗi chữ số do cardinal() tạo ra -> số; dùng để kiểm thử."""
    toks = s.split()
    total = 0
    cur = 0
    last = 0
    i = 0
    seen_zero_hundred = False
    while i < len(toks):
        t = toks[i]
        if t in _W and t != "không":
            val = _W[t]
        elif t == "không":
            val = 0
        elif t == "mốt":
            val = 1
        elif t == "lăm":
            val = 5
        elif t == "tư":
            val = 4
        elif t == "mười":
            cur += 10
            i += 1
            continue
        elif t == "mươi":
            cur = cur - last + last * 10
            last = 0
            i += 1
            continue
        elif t == "trăm":
            cur = cur - last + last * 100
            last = 0
            i += 1
            continue
        elif t in ("linh", "lẻ"):
            i += 1
            continue
        elif t in ("nghìn", "ngàn"):
            total += cur * 1000
            cur = 0
            last = 0
            i += 1
            continue
        elif t == "triệu":
            total += cur * 10 ** 6
            cur = 0
            last = 0
            i += 1
            continue
        else:
            raise ValueError(t)
        cur += val
        last = val
        i += 1
    return total + cur


if __name__ == "__main__":
    import random
    tests = [(0, "không"), (5, "năm"), (10, "mười"), (11, "mười một"), (14, "mười bốn"), (15, "mười lăm"), (21, "hai mươi mốt"),
             (24, "hai mươi bốn"), (25, "hai mươi lăm"), (100, "một trăm"), (105, "một trăm lẻ năm"), (110, "một trăm mười"),
             (115, "một trăm mười lăm"), (1000, "một ngàn"), (1001, "một ngàn không trăm lẻ một"), (1200, "một ngàn hai trăm"),
             (50000, "năm mươi ngàn"), (2500000, "hai triệu năm trăm ngàn"), (605, "sáu trăm lẻ năm")]
    for n, w in tests:
        got = cardinal(n, "Nam")
        assert got == w, (n, got, w)
    assert cardinal(105, "Bắc") == "một trăm linh năm"
    assert cardinal(1001, "Bắc") == "một nghìn không trăm linh một"
    assert cardinal(24, "Bắc", tu=True) == "hai mươi tư"
    assert cardinal(14, "Bắc", tu=True) == "mười bốn"
    for _ in range(20000):
        n = random.randint(0, 999999999)
        for rg in ("Bắc", "Trung", "Nam"):
            s = cardinal(n, rg, tu=random.random() < .5)
            assert parse(s) == n, (n, s, parse(s))
    print("num ok")
