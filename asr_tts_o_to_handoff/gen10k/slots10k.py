# -*- coding: utf-8 -*-
"""Bộ sinh giá trị khe. Mỗi bộ sinh nhận Ctx và trả SV(raw, spoken, feats, flags, marks, meta)."""
import re
import pools10k as P
import loanwords10k as LW
from vnnum import read_int, read_digits, read_decimal, fmt_dec, fmt_money, DIG
from lexicon10k import Mark, rewrite


RESIDENCE_PLACE = {"Hà Nội": "Bắc", "TP.HCM": "Nam"}


class Ctx:
    """region: vùng giọng người nói (đọc số, xưng hô gia đình).
    profile: hồ sơ từ vựng (lexicon10k.PROFILES). place_region: vùng nơi sống (chọn địa danh gần)."""

    def __init__(self, rng, region, case, profile=None, residence="Quê", sub_region=None):
        self.rng, self.region, self.case = rng, region, case
        self.profile = profile or ("Trung-Quảng" if region == "Trung" else region)
        self.residence, self.sub_region = residence, sub_region
        self.place_region = RESIDENCE_PLACE.get(residence, region)
        self.vocab = {"Trung-HN": "Bắc", "Trung-HCM": "Nam"}.get(self.profile, region)
        self.memo = {}       # dùng chung trong một câu (thành phố đang nói, khái niệm đã chọn...)
        self.lexmemo = {}    # lựa chọn từ vùng trong câu

    def local(self, items, key=lambda x: x["region"], p=0.7):
        """Ưu tiên mục cùng vùng với nơi sống của người nói."""
        if self.rng.random() < p:
            loc = [x for x in items if key(x) == self.place_region]
            if loc:
                return self.rng.choice(loc)
        return self.rng.choice(items)


class SV:
    __slots__ = ("raw", "spoken", "feats", "flags", "marks", "meta")

    def __init__(self, raw, spoken=None, feats=(), flags=(), marks=(), meta=None):
        self.raw = raw
        self.spoken = raw if spoken is None else spoken
        self.feats, self.flags, self.marks = set(feats), set(flags), list(marks)
        self.meta = dict(meta or {})


def n(c, x):
    return read_int(x, c.region)


def pick(c, items):
    return c.rng.choice(items)


# ------------------------------------------------------------------ số và đơn vị
def g_int(lo, hi, feats=("số",)):
    def g(c):
        x = c.rng.randint(lo, hi)
        return SV(str(x), n(c, x), feats)
    return g


def g_vals(vals, feats=("số",)):
    def g(c):
        x = pick(c, vals)
        return SV(str(x), n(c, x), feats)
    return g


def g_temp(c):
    r = c.rng.random()
    if r < 0.25:
        x = pick(c, [16.5, 17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5, 25.5, 26.5])
        return SV(fmt_dec(x), read_decimal(fmt_dec(x), c.region), ("số",))
    x = c.rng.randint(16, 30)
    return SV(str(x), n(c, x), ("số",))


def g_temp_unit(c):
    """nhiệt độ kèm 'độ' hoặc '°C'."""
    v = g_temp(c)
    if c.rng.random() < 0.15:
        return SV(v.raw + "°C", v.spoken + " độ xê", ("số", "đơn vị đo", "viết tắt"))
    return SV(v.raw + " độ", v.spoken + " độ", ("số",))


def g_delta(c):
    x = pick(c, [1, 1, 2, 2, 3, 0.5, 1.5])
    if isinstance(x, float):
        return SV(fmt_dec(x), read_decimal(fmt_dec(x), c.region), ("số",))
    return SV(str(x), n(c, x), ("số",))


def g_pct(vals=(10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100)):
    def g(c):
        x = pick(c, list(vals))
        if c.rng.random() < 0.2:
            return SV(f"{x} phần trăm", f"{n(c, x)} phần trăm", ("phần trăm", "số"))
        return SV(f"{x}%", f"{n(c, x)} phần trăm", ("phần trăm", "số", "viết tắt"))
    return g


def g_pct_pair(c):
    a = pick(c, [5, 10, 15, 20, 25, 30, 35, 40, 50, 60])
    b = pick(c, [x for x in (60, 70, 80, 85, 90, 95, 100) if x > a])
    return SV(f"{a}% lên {b}%", f"{n(c, a)} phần trăm lên {n(c, b)} phần trăm", ("phần trăm", "số", "viết tắt"))


def g_km(c):
    r = c.rng.random()
    if r < 0.2:
        x = pick(c, [0.5, 1.2, 1.5, 2.5, 3.5, 4.5, 7.5, 12.5])
        return SV(f"{fmt_dec(x)} km", f"{read_decimal(fmt_dec(x), c.region)} ki lô mét", ("số", "đơn vị đo", "viết tắt"))
    x = pick(c, [1, 2, 3, 4, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 102, 105, 108, 120, 150, 200, 204, 250, 300, 305,
                 350, 400, 500, 1000, 1005, 1200, 1500])
    if r < 0.45:
        return SV(f"{x} cây số", f"{n(c, x)} cây số", ("số", "đơn vị đo"))
    return SV(f"{x} km", f"{n(c, x)} ki lô mét", ("số", "đơn vị đo", "viết tắt"))


def g_met(c):
    x = pick(c, [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800])
    return SV(f"{x} mét", f"{n(c, x)} mét", ("số", "đơn vị đo"))


def g_kmh(vals=(30, 40, 50, 60, 70, 80, 90, 100, 110, 120)):
    def g(c):
        x = pick(c, list(vals))
        if c.rng.random() < 0.3:
            return SV(f"{x} cây số một giờ", f"{n(c, x)} cây số một giờ", ("số", "đơn vị đo"))
        return SV(f"{x} km/h", f"{n(c, x)} ki lô mét trên giờ", ("số", "đơn vị đo", "viết tắt"))
    return g


def g_minutes(vals=(2, 3, 5, 7, 10, 12, 15, 20, 25, 30, 40, 45, 50, 60, 90)):
    def g(c):
        x = pick(c, list(vals))
        if x == 30 and c.rng.random() < 0.3:
            return SV("nửa tiếng", "nửa tiếng", ())
        if x in (60, 90) and c.rng.random() < 0.5:
            return SV("1 tiếng" if x == 60 else "1 tiếng rưỡi", "một tiếng" if x == 60 else "một tiếng rưỡi", ("số", "giờ/ngày/tháng/năm"))
        return SV(f"{x} phút", f"{n(c, x)} phút", ("số", "giờ/ngày/tháng/năm"))
    return g


def g_seconds(c):
    x = pick(c, [5, 10, 15, 20, 30, 45, 60, 90])
    return SV(f"{x} giây", f"{n(c, x)} giây", ("số",))


def g_kwh(c):
    x = pick(c, [5, 10, 15, 20, 25, 30, 40, 45, 50, 60, 75, 82, 87])
    return SV(f"{x} kWh", f"{n(c, x)} ki lô oát giờ", ("số", "đơn vị đo", "viết tắt"))


def g_kw(c):
    x = pick(c, [7, 11, 22, 30, 60, 120, 150, 250])
    return SV(f"{x} kW", f"{n(c, x)} ki lô oát", ("số", "tần số/công suất", "đơn vị đo", "viết tắt"))


def g_money(c):
    unit = "nghìn" if c.region == "Bắc" else "ngàn"
    r = c.rng.random()
    if r < 0.4:
        x = pick(c, [3500, 5000, 10000, 15000, 20000, 25000, 30000, 50000, 100000, 150000, 200000, 250000, 500000, 1200000, 1500000])
        return SV(f"{fmt_money(x)} đồng", f"{n(c, x)} đồng", ("tiền VND", "số"))
    if r < 0.8:
        x = pick(c, [5, 10, 15, 20, 25, 30, 50, 100, 120, 150, 200, 300, 500])
        return SV(f"{x} {unit}", f"{n(c, x)} {unit}", ("tiền VND", "số"))
    x = pick(c, [1, 2, 3, 5])
    return SV(f"{x} triệu rưỡi", f"{n(c, x)} triệu rưỡi", ("tiền VND", "số"))


def g_phone(c):
    pref = pick(c, ["090", "091", "093", "094", "096", "097", "098", "086", "088", "089", "032", "033", "034", "035", "036", "037",
                    "038", "039", "070", "076", "077", "078", "079", "081", "082", "083", "084", "085", "056", "058", "059", "052"])
    num = pref + "".join(str(c.rng.randint(0, 9)) for _ in range(7))
    if c.rng.random() < 0.8:
        raw = f"{num[:4]} {num[4:7]} {num[7:]}"
    else:
        raw = f"{num[:3]} {num[3:6]} {num[6:]}"
    return SV(raw, read_digits(raw), ("số điện thoại", "số"))


def g_level(lo, hi):
    def g(c):
        x = c.rng.randint(lo, hi)
        return SV(str(x), n(c, x), ("số",))
    return g


def g_ordinal(c):
    w = pick(c, ["nhất", "hai", "ba", "tư", "năm"])
    return SV(w, w, ("số",))


def g_freq(c):
    f = pick(c, P.FREQS)
    if abs(f - round(f)) < 1e-9:
        fr, fs = str(int(round(f))), n(c, int(round(f)))
    else:
        fr = fmt_dec(f)
        fs = read_decimal(fr, c.region)
    form = c.rng.random()
    if form < 0.6:
        return SV(f"FM {fr} MHz", f"ép em {fs} mê ga héc", ("tần số/công suất", "số", "đơn vị đo", "viết tắt"))
    if form < 0.85:
        return SV(f"{fr} MHz", f"{fs} mê ga héc", ("tần số/công suất", "số", "đơn vị đo", "viết tắt"))
    return SV(f"FM {fr}", f"ép em {fs}", ("tần số/công suất", "số", "viết tắt"))


def g_freq_bare(c):
    """tần số không kèm chữ FM (khung đã có 'FM' hoặc 'đài')."""
    v = g_freq(c)
    if v.raw.startswith("FM "):
        raw, sp = v.raw[3:], v.spoken[len("ép em "):]
        return SV(raw, sp, v.feats, v.flags)
    return v


def g_radio(c):
    cand = [x for x in P.RADIO if x[3] in (None, c.place_region)]
    raw, sp, f, _ = pick(c, cand)
    feats = {"tên riêng/địa danh"} | ({"viết tắt"} if "VO" in raw else set())
    flags = {"cách đọc viết tắt chưa xác minh: VOH"} if raw == "VOH" else set()
    if raw.startswith("VOV") and raw[-1].isdigit():
        flags.add("cách đọc tên đài chưa xác minh")
    if f is not None and c.rng.random() < 0.35:
        fr = str(int(f)) if abs(f - round(f)) < 1e-9 else fmt_dec(f)
        fs = n(c, int(f)) if abs(f - round(f)) < 1e-9 else read_decimal(fr, c.region)
        return SV(f"{raw}, FM {fr} MHz", f"{sp}, ép em {fs} mê ga héc", feats | {"tần số/công suất", "số", "đơn vị đo"}, flags)
    return SV(raw, sp, feats, flags)


# ------------------------------------------------------------------ thời gian
PERIOD_HOURS = {"sáng": [5, 6, 7, 8, 9, 10, 11], "trưa": [11, 12], "chiều": [1, 2, 3, 4, 5, 6], "tối": [6, 7, 8, 9, 10, 11]}


def g_clock(c, with_period=True):
    r = c.rng
    per = r.choice(["sáng", "sáng", "chiều", "tối", "trưa"])
    h = r.choice(PERIOD_HOURS[per])
    style = r.choice(["gio", "gio", "ruoi", "phut", "kem", "24h"])
    pr = (" " + per) if with_period else ""
    if style == "24h":
        hh = h + 12 if per in ("chiều", "tối") and h < 12 else h
        m = r.choice([0, 15, 30, 45])
        if m:
            return SV(f"{hh} giờ {m}", f"{n(c, hh)} giờ {n(c, m)}", ("giờ/ngày/tháng/năm", "số"))
        return SV(f"{hh} giờ", f"{n(c, hh)} giờ", ("giờ/ngày/tháng/năm", "số"))
    if style == "ruoi":
        return SV(f"{h} giờ rưỡi{pr}", f"{n(c, h)} giờ rưỡi{pr}", ("giờ/ngày/tháng/năm", "số"))
    if style == "phut":
        m = r.choice([5, 10, 15, 20, 25, 35, 40, 45, 50, 55])
        return SV(f"{h} giờ {m} phút{pr}", f"{n(c, h)} giờ {n(c, m)} phút{pr}", ("giờ/ngày/tháng/năm", "số"))
    if style == "kem" and h < 11:
        m = r.choice([5, 10, 15, 20])
        return SV(f"{h + 1} giờ kém {m}{pr}", f"{n(c, h + 1)} giờ kém {n(c, m)}{pr}", ("giờ/ngày/tháng/năm", "số"))
    return SV(f"{h} giờ{pr}", f"{n(c, h)} giờ{pr}", ("giờ/ngày/tháng/năm", "số"))


MONTH_SPOKEN = {1: "một", 2: "hai", 3: "ba", 4: "tư", 5: "năm", 6: "sáu", 7: "bảy", 8: "tám", 9: "chín", 10: "mười", 11: "mười một", 12: "mười hai"}


def g_day(c):
    r = c.rng.random()
    if r < 0.45:
        v = pick(c, ["hôm nay", "ngày mai", "ngày kia", "tối nay", "sáng mai", "chiều nay", "cuối tuần này", "chiều mai", "tuần sau",
                     "sáng thứ hai", "chiều thứ sáu"])
        return SV(v, v, ())
    if r < 0.7:
        v = pick(c, ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"])
        v = pick(c, ["", "", "sáng ", "chiều ", "tối "]) + v + pick(c, ["", " tuần sau", " này"])
        return SV(v.strip(), v.strip(), ("giờ/ngày/tháng/năm",))
    d, m = c.rng.randint(1, 28), c.rng.randint(1, 12)
    mung = ("mồng " if c.region == "Bắc" else "mùng ") if d <= 10 else ""
    flags = {"cách đọc mồng/mùng miền Trung chưa xác minh"} if (d <= 10 and c.region == "Trung") else set()
    if c.rng.random() < 0.3:
        return SV(f"ngày {d}/{m}", f"ngày {mung}{n(c, d)} tháng {MONTH_SPOKEN[m]}", ("giờ/ngày/tháng/năm", "số", "viết tắt"), flags)
    return SV(f"ngày {d} tháng {m}", f"ngày {mung}{n(c, d)} tháng {MONTH_SPOKEN[m]}", ("giờ/ngày/tháng/năm", "số"), flags)


def g_when(c):
    """thời điểm: giờ, ngày hoặc giờ + ngày."""
    r = c.rng.random()
    if r < 0.45:
        return g_clock(c)
    if r < 0.6:
        return g_day(c)
    b = g_day(c)
    day_has_period = b.raw.split()[0] in ("sáng", "chiều", "tối", "trưa") or b.raw in ("tối nay", "chiều nay", "sáng mai", "chiều mai")
    a = g_clock(c, with_period=(not day_has_period) and c.rng.random() < 0.5)
    if day_has_period and re.search(r"\b(sáng|chiều|tối|trưa)\b", a.raw):
        a = g_clock(c, with_period=False)
    if day_has_period and re.search(r"\b(sáng|chiều|tối|trưa)\b", a.raw):   # dạng 24 giờ không có buổi; kiểm lần nữa cho chắc
        return b
    return SV(f"{a.raw} {b.raw}", f"{a.spoken} {b.spoken}", a.feats | b.feats, a.flags | b.flags)


# ------------------------------------------------------------------ địa danh, địa chỉ
LETTER_SP = {"A": "a", "B": "bê", "C": "xê", "D": "đê"}


def _house(c):
    r = c.rng.random()
    if r < 0.12:   # số có hàng chục bằng 0 (101–909): đọc linh/lẻ theo vùng (S53)
        x = c.rng.randint(1, 9) * 100 + c.rng.randint(1, 9)
        return str(x), n(c, x), set()
    if r < 0.55:
        x = c.rng.randint(1, 120)
        return str(x), n(c, x), set()
    if r < 0.85:
        x = c.rng.randint(121, 520)
        return str(x), n(c, x), set()
    if r < 0.93 or c.place_region != "Nam":
        x = c.rng.randint(1, 99)
        l = c.rng.choice("ABC")
        return f"{x}{l}", f"{n(c, x)} {LETTER_SP[l]}", {"cách đọc chữ cái trong số nhà chưa xác minh"}
    x, y = c.rng.randint(10, 400), c.rng.randint(1, 60)
    return f"{x}/{y}", f"{n(c, x)} xẹt {n(c, y)}", {"cách đọc dấu xẹt trong địa chỉ chưa xác minh"}


def _choose_city(c, p_local=0.8):
    if "city" in c.memo:
        return c.memo["city"]
    cities = list(P.STREETS)
    if c.rng.random() < p_local:
        loc = [k for k in cities if P.STREETS[k][0] == c.place_region]
        city = c.rng.choice(loc) if loc else c.rng.choice(cities)
    else:
        city = c.rng.choice(cities)
    c.memo["city"] = city
    return city


def g_street(c):
    city = _choose_city(c)
    st = pick(c, P.STREETS[city][2])
    return SV(st, st, ("tên riêng/địa danh",), meta=dict(city=city))


def g_street_bare(c):
    """tên đường không kèm chữ 'đường' (khung đã có 'đường')."""
    city = _choose_city(c)
    st = pick(c, [s for s in P.STREETS[city][2] if s.startswith("đường ")] or P.STREETS["Sài Gòn"][2])
    st = st[len("đường "):]
    return SV(st, st, ("tên riêng/địa danh",), meta=dict(city=city))


def _city_say(c, city):
    if city == "Sài Gòn":
        if c.rng.random() < 0.15:
            return "TP.HCM", "thành phố Hồ Chí Minh", {"viết tắt"}
        if c.place_region == "Nam" and c.rng.random() < 0.7:
            return "Sài Gòn", "Sài Gòn", set()
        return "thành phố Hồ Chí Minh", "thành phố Hồ Chí Minh", set()
    return city, city, set()


def g_addr(c):
    city = _choose_city(c)
    reg, alley, streets = P.STREETS[city]
    st = pick(c, streets)
    hn, hs, fl = _house(c)
    raw, sp = [], []
    form = c.rng.random()
    if form < 0.3:
        raw, sp = [f"số {hn}", st], [f"số {hs}", st]
    elif form < 0.5:
        raw, sp = [hn, st], [hs, st]
    elif form < 0.88:
        m = c.rng.randint(2, 320)
        term = alley
        if city in ("Huế", "Đà Nẵng") and c.rng.random() < 0.3:
            term = "hẻm"
        raw, sp = [f"số {hn}", f"{term} {m}"], [f"số {hs}", f"{term} {n(c, m)}"]
        if term == "ngõ" and c.rng.random() < 0.25:
            k = c.rng.randint(2, 40)
            raw.append(f"ngách {k}")
            sp.append(f"ngách {n(c, k)}")
        raw.append(st)
        sp.append(st)
    else:
        raw, sp = [st], [st]
        hn = None
    feats = {"địa chỉ", "tên riêng/địa danh"}
    if hn is not None:
        feats.add("số")
    marks = []
    for term in ("ngõ", "ngách", "hẻm", "kiệt"):
        if any(x.startswith(term + " ") for x in raw):
            marks.append(Mark(term, "ngõ/hẻm", "S51", term != "kiệt", True))
            if term == "kiệt":
                fl = fl | {"từ địa phương 'kiệt' (Huế, Đà Nẵng) cần người bản ngữ duyệt"}
    rs, ss = " ".join(raw), " ".join(sp)
    if c.rng.random() < (0.6 if reg == c.place_region else 0.95):
        cr, cs, cf = _city_say(c, city)
        rs, ss = rs + ", " + cr, ss + ", " + cs
        feats |= cf
    return SV(rs, ss, feats, fl, marks, meta=dict(city=city, synthetic_address=True))


def g_house_no(c):
    hn, hs, fl = _house(c)
    return SV(hn, hs, ("số", "địa chỉ"), fl, meta=dict(synthetic_address=True))


def g_district(c):
    city = c.memo.get("city")
    pool = [d for d in P.DISTRICTS if d["city"] == city] if city else []
    if not pool:
        d = c.local(P.DISTRICTS, p=0.7)
    else:
        d = pick(c, pool)
    nm = d["name"]
    raw = f'{d["type"]} {nm}'
    sp = f'{d["type"]} {n(c, int(nm))}' if nm.isdigit() else raw
    feats = {"tên riêng/địa danh", "địa chỉ"} | ({"số"} if nm.isdigit() else set())
    if not city and c.rng.random() < 0.4:
        cr, cs, cf = _city_say(c, d["city"])
        raw, sp = raw + ", " + cr, sp + ", " + cs
        feats |= cf
    return SV(raw, sp, feats, meta=dict(admin_name_pre2025=True))


def g_city(c):
    item = c.local([dict(n=a, region=b) for a, b in P.CITIES], p=0.6)
    cr, cs, cf = _city_say(c, item["n"])
    return SV(cr, cs, {"tên riêng/địa danh"} | cf)


def g_poi(kinds=None, with_city=0.3):
    def g(c):
        items = [x for x in P.POIS if kinds is None or x["kind"] in kinds]
        it = c.local(items, p=0.7)
        raw = it["name"]
        sp = P.POI_SPOKEN.get(raw, raw)
        feats = {"tên riêng/địa danh"}
        flags = set()
        if any(ch.isdigit() for ch in raw):
            feats.add("số")
        if any(w in raw.split() for w in P.POI_LOANWORD):
            feats.add("từ mượn tiếng Anh")
        if raw in ("bệnh viện K", "bệnh viện C Đà Nẵng"):
            feats.add("viết tắt")
            flags.add("cách đọc chữ cái trong tên bệnh viện chưa xác minh")
        meta = dict(alias=it["alias"])
        if it["alias"]:
            flags.add("tên gọi quen địa phương (K1) cần người địa phương xác nhận")
        if with_city and c.rng.random() < with_city and it["city"] not in raw and not it["alias"]:
            cr, cs, cf = _city_say(c, it["city"])
            raw, sp = raw + " ở " + cr, sp + " ở " + cs
            feats |= cf
        return SV(raw, sp, feats, flags, meta=meta)
    return g


def g_saved(kind):
    def g(c):
        v = pick(c, P.HOME_LIKE if kind == "home" else P.PLACE_LIKE)
        return SV(v, v, ())
    return g


def g_nearby(c):
    v = pick(c, P.NEARBY)
    if c.vocab == "Nam":
        v = v.replace("bãi đỗ xe", "bãi đậu xe").replace("hiệu thuốc", "nhà thuốc")
    # Trung ở quê: giữ nguyên chữ (chưa có nguồn từ xe theo tiểu vùng, phụ lục 6.4)
    feats = {"từ mượn tiếng Anh", "viết tắt"} if "ATM" in v else set()
    sp = v.replace("ATM", "a tê em")
    flags = {"cách đọc viết tắt chưa xác minh: ATM"} if "ATM" in v else set()
    return SV(v, sp, feats, flags)


def g_place(c):
    """địa điểm đích chung: POI, địa chỉ, nơi đã lưu, quận/thành phố, tên gọi quen."""
    r = c.rng.random()
    if r < 0.42:
        return g_poi(None, 0.25)(c)
    if r < 0.62:
        return g_addr(c)
    if r < 0.72:
        return g_saved("home" if c.rng.random() < 0.5 else "place")(c)
    if r < 0.82:
        return g_district(c)
    if r < 0.92:
        return g_city(c)
    v = g_nearby(c)
    return SV(v.raw + " gần nhất", v.spoken + " gần nhất", v.feats, v.flags)


def g_highway(c):
    name, abbr = pick(c, P.HIGHWAYS)
    feats = {"tên riêng/địa danh"}
    m = re.match(r"quốc lộ (\d+)([A-Z]?)$", name)
    if m:
        num, let = int(m.group(1)), m.group(2)
        sp = "quốc lộ " + n(c, num) + ((" " + LETTER_SP.get(let, let.lower()) if let in LETTER_SP else (" ca" if let == "K" else "")))
        feats.add("số")
        if abbr and c.rng.random() < 0.3:
            return SV(abbr, sp, feats | {"viết tắt"})
        return SV(name, sp, feats)
    return SV(name, name.replace(" – ", " "), feats)


# ------------------------------------------------------------------ người
def g_contact(kinds=("peer", "peer", "elder", "kin", "full", "ctx", "birth")):
    def g(c):
        r = c.rng
        kind = r.choice(kinds)
        if kind == "birth" and c.region != "Nam":
            kind = "peer"
        sex = r.choice("MF")
        first = r.choice(P.MALE if sex == "M" else P.FEMALE)
        marks, flags = [], set()
        if kind == "peer":
            v = f"{r.choice(P.HON_PEER[sex])} {first}"
        elif kind == "elder":
            v = f"{r.choice(P.HON_ELDER[sex])} {first}"
        elif kind == "full":
            v = f"{r.choice(['anh', 'chị', 'chú', 'cô'] if sex else ['anh'])} {r.choice(P.SURNAMES)} {r.choice(P.MID_M if sex == 'M' else P.MID_F)} {first}"
            if v.split()[0] in ("anh", "chú") and sex == "F" or v.split()[0] in ("chị", "cô") and sex == "M":
                v = ("anh " if sex == "M" else "chị ") + " ".join(v.split()[1:])
        elif kind == "ctx":
            v = f"{r.choice(P.HON_PEER[sex])} {first} {r.choice(P.CONTEXT_TAGS)}"
        elif kind == "birth":
            v = f"{r.choice(['anh', 'chị', 'chú', 'dì', 'cô', 'bác'])} {r.choice(P.BIRTH)}"
            marks.append(Mark(v.split()[0] + " " + v.split()[1], "gọi theo thứ tự sinh", "S52", False, True))
            flags.add("cách gọi theo thứ tự sinh (Nam Bộ, K1) cần người bản ngữ duyệt")
        else:
            kin = P.KIN[c.region]
            if c.region == "Trung" and c.sub_region != "Huế":      # o, mệ, mạ: nguồn chỉ ghi cho Huế
                kin = [k for k in kin if k[0] not in ("o", "mệ", "mạ")]
            word, regional = r.choice(kin)
            v = word
            if regional:
                marks.append(Mark(word, "xưng hô gia đình", "S52", word not in ("u", "thầy u", "dượng", "thím Ba", "tía"), True))
        return SV(v, v, ("tên riêng/địa danh",), flags, marks, meta=dict(kind=kind))
    return g


# ------------------------------------------------------------------ giải trí
def g_song(c):
    title, artist = pick(c, P.SONGS)
    feats = {"tên riêng/địa danh"}
    if re.search(r"[A-Za-z]{4,}", title) and not re.search(r"[À-ỹ]", title):
        feats.add("từ mượn tiếng Anh")
    c.memo["artist"] = artist.split(",")[0].strip()
    return SV(title, title, feats)


def g_artist(c):
    a = c.memo.get("artist") or pick(c, P.ARTISTS)
    feats = {"tên riêng/địa danh"}
    sp, flags = a, set()
    if re.search(r"[A-Z]{2,}|M-TP|\.", a) or a in ("Binz", "Karik", "Jack", "Suboi", "JustaTee", "Wren Evans", "Noo Phước Thịnh"):
        feats.add("từ mượn tiếng Anh")
        flags.add(f"cách đọc nghệ danh chưa xác minh: {a}")
    return SV(a.rstrip("."), sp.rstrip("."), feats, flags)


def g_genre_bare(c):
    v = pick(c, P.GENRE_BARE)
    feats = {"từ mượn tiếng Anh"} if re.search(r"EDM|pop|rock|jazz|lofi|remix|acoustic|indie|hip hop|ballad|rap", v) else set()
    if v == "EDM":
        return SV(v, "i đi em", feats | {"viết tắt"}, {"cách đọc viết tắt chưa xác minh: EDM"})
    if v in ("K-pop", "V-pop"):
        return SV(v, v.replace("-", " ").replace("K", "ca").replace("V", "vi"), feats, {f"cách đọc chưa xác minh: {v}"})
    return SV(v, v, feats)


def g_genre(c):
    v = g_genre_bare(c)
    return SV("nhạc " + v.raw, "nhạc " + v.spoken, v.feats, v.flags)


def g_playlist(c):
    v = pick(c, P.PLAYLISTS)
    feats = {"tên riêng/địa danh"}
    if re.search(r"Chill|Road Trip|Top|Hit|EDM|lo-fi|rap", v):
        feats.add("từ mượn tiếng Anh")
    sp = v.replace("EDM", "i đi em").replace("lo-fi", "lo fi")
    return SV(v, sp, feats)


def choice_sv(lst, feats=(), flags=()):
    def g(c):
        v = pick(c, lst)
        return SV(v, v, feats, flags)
    return g


def pair_sv(lst, feats=()):
    def g(c):
        a, b = pick(c, lst)
        return SV(a, b if b is not None else a, feats)
    return g


VI_NAMES = {"Zalo", "lịch", "tin nhắn", "điện thoại", "thẻ nhớ"}


def g_named(lst):
    """Một hàm cho mọi khe tên app / nguồn kết nối (v3, CHANGES_v3 C4): text_spoken lấy cách đọc hiện tại từ bảng từ ngoại
    (loanwords10k); cờ và pron_variant gắn ở bước quét toàn câu trong build10k.render, không gắn ở đây."""
    feats_of = {raw: f for raw, _, f in P.LINK_SRC}

    def g(c):
        v = pick(c, lst)
        if v in feats_of:
            feats = set(feats_of[v])
        else:
            feats = {"tên riêng/địa danh"} | ({"từ mượn tiếng Anh"} if v not in VI_NAMES else set())
        return SV(v, LW.current_reading(v), feats)
    return g


g_link_src = g_named([raw for raw, _, _ in P.LINK_SRC])


def g_eng_temp(c):
    x = pick(c, [85, 88, 90, 92, 95, 98, 100, 102, 105, 108, 110, 115])
    return SV(f"{x} độ", f"{n(c, x)} độ", ("số",))


g_app_from = g_named
g_app = g_named(P.APPS)


# ------------------------------------------------------------------ nội dung
def g_message(c):
    v = pick(c, P.MESSAGES)
    v2, marks = rewrite(v, c.profile, c.rng, memo=c.lexmemo)
    if c.rng.random() < 0.25:
        m = pick(c, [5, 10, 15, 20, 30])
        raw = f"mình đến muộn {m} phút"
        raw, mk2 = rewrite(raw, c.profile, c.rng, memo=c.lexmemo)
        return SV(raw, raw.replace(str(m), n(c, m)), ("số",), marks=mk2)
    if v2.startswith("ok"):
        return SV(v2, v2.replace("ok", "ô kê", 1), ("từ mượn tiếng Anh",), marks=marks)
    return SV(v2, v2, (), marks=marks)


def g_remind(c):
    v = pick(c, P.REMIND)
    v2, marks = rewrite(v, c.profile, c.rng, memo=c.lexmemo)
    return SV(v2, v2, (), marks=marks)


def g_aqi(c):
    x = pick(c, [35, 50, 75, 100, 120, 150, 180, 200])
    return SV(str(x), n(c, x), ("số",))


def g_arith(c):
    a, b = c.rng.randint(2, 99), c.rng.randint(2, 30)
    op_raw, op_sp = pick(c, [("+", "cộng"), ("-", "trừ"), ("x", "nhân"), (":", "chia")])
    if op_raw == "-" and a < b:
        a, b = b, a
    if c.rng.random() < 0.5:
        return SV(f"{a} {op_sp} {b}", f"{n(c, a)} {op_sp} {n(c, b)}", ("số",))
    return SV(f"{a} {op_raw} {b}", f"{n(c, a)} {op_sp} {n(c, b)}", ("số", "viết tắt"))


def g_currency(c):
    x = pick(c, [10, 20, 50, 100, 200, 250, 500, 1000])
    cur_raw, cur_sp, f = pick(c, [("USD", "u ét đê", True), ("đô", "đô", False), ("đô la Mỹ", "đô la Mỹ", False), ("euro", "ơ rô", False),
                                  ("yên Nhật", "yên Nhật", False), ("won", "uôn", False), ("nhân dân tệ", "nhân dân tệ", False),
                                  ("baht Thái", "bạt Thái", False)])
    flags = {"cách đọc viết tắt chưa xác minh: USD"} if f else set()
    return SV(f"{x} {cur_raw}", f"{n(c, x)} {cur_sp}", ("số", "tiền VND") + (("viết tắt",) if f else ()), flags)


def g_short_cmd(c):
    v = pick(c, P.SHORT_CMDS)
    v2, marks = rewrite(v, c.profile, c.rng, memo=c.lexmemo)
    return SV(v2, v2, (), marks=marks)


def g_wake(c):
    v = pick(c, ["trợ lý", "trợ lý ơi"])
    return SV(v, v, ())


def g_restaurant(c):
    dish = pick(c, P.DISHES)
    city = _choose_city(c)
    st = pick(c, P.STREETS[city][2]).replace("đường ", "").replace("phố ", "")
    return SV(f"{dish} {st}", f"{dish} {st}", ("tên riêng/địa danh",))


# ------------------------------------------------------------------ bảng khe
SLOTS = {
    # địa điểm
    "addr": g_addr, "poi": g_poi(None, 0.3), "poi_air": g_poi({"sân bay", "ga", "bến xe"}, 0.2),
    "poi_hosp": g_poi({"bệnh viện"}, 0.2), "dist": g_district, "city": g_city, "home": g_saved("home"), "place_saved": g_saved("place"),
    "cat": g_nearby, "hw": g_highway, "st": g_street, "dia_diem": g_place, "loai_dia_diem": g_nearby, "thanh_pho": g_city,
    "ten_duong": g_street, "st_bare": g_street_bare, "freq_bare": g_freq_bare, "so_nha": g_house_no, "quan_huyen": g_district, "dia_chi_luu": g_saved("place"), "ten_tram_sac": g_poi(None, 0.0),
    # số đo
    "mins": g_minutes(), "km": g_km, "met": g_met, "vol": g_level(1, 30), "ordw": g_ordinal, "clk": g_clock, "day": g_day,
    "when": g_when, "thoi_gian": g_when, "temp": g_temp, "temp_u": g_temp_unit, "nhiet_do": g_temp, "nhiet_do_2": g_temp,
    "delta": g_delta, "n3": g_delta, "fan": g_level(1, 7), "muc_quat": g_level(1, 7), "lvl3": g_level(1, 3), "lvl5": g_level(1, 5),
    "pct": g_pct(), "phan_tram": g_pct(), "pct_bat": g_pct((10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100)), "pct2": g_pct_pair,
    "spd": g_kmh(), "spd5": g_kmh((5, 10)), "sec": g_seconds, "kwh": g_kwh, "kw": g_kw, "money": g_money, "aqi": g_aqi,
    "ph": g_phone, "so_dien_thoai": g_phone, "freq": g_freq, "tan_so": g_freq, "radio": g_radio, "kenh_radio": g_radio,
    "arith": g_arith, "currency": g_currency, "mem": g_level(1, 3), "ppl": g_level(2, 12),
    "n60": g_vals([1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 45, 60, 90]),
    # xe
    "seat": choice_sv(P.SEATS), "wpos": choice_sv(P.WPOS), "vent": choice_sv(P.VENTS), "huong_gio": choice_sv(P.VENTS),
    "color": choice_sv(P.COLORS), "lamp": choice_sv(P.LAMPS), "tire": choice_sv(P.TIRES), "part": choice_sv(P.PARTS),
    "wlamp": lambda c: (SV("ABS", "a bê ét", ("viết tắt",), {"cách đọc viết tắt chưa xác minh: ABS"}) if (v := pick(c, P.WARN_LAMPS)) == "ABS"
                        else SV(v, v)), "warn": choice_sv(P.WARNS), "sysn": pair_sv(P.SYSTEMS, ("số",)),
    "lev": choice_sv(["thấp", "trung bình", "cao", "nhạy nhất", "ít nhạy nhất"]), "gap": choice_sv(["gần", "vừa", "xa", "một", "hai", "ba"]),
    # người
    "ct": g_contact(), "ten_lien_he": g_contact(), "ct2": g_contact(("peer", "elder", "full", "ctx")),
    # giải trí
    "bai_hat": g_song, "ca_si": g_artist, "artist": g_artist, "the_loai": g_genre_bare, "genre": g_genre, "mood": choice_sv(P.MOODS),
    "plist": g_playlist, "ten_playlist": g_playlist, "pod": choice_sv(P.PODCASTS), "ten_podcast": choice_sv(P.PODCASTS),
    "chu_de": choice_sv(P.TOPICS), "src": g_link_src, "ung_dung": g_app, "app": g_app, "eng_temp": g_eng_temp,
    "gear": lambda c: SV(*pick(c, [("D", "đê"), ("R", "e rờ"), ("N", "en"), ("P", "pê")]), ("viết tắt",),
                         {"tên chữ cái của số xe theo src_lang car_terms (K1)"}),
    "msg_app": g_app_from(P.MSG_APPS), "music_app": g_app_from(P.MUSIC_APPS), "ten_phim": choice_sv(P.CARTOONS, ("tên riêng/địa danh",)),
    "map_app": g_app_from(P.MAP_APPS), "etc_app": g_app_from(P.ETC_APPS), "kenh": choice_sv(P.CHANNELS),
    "composer": choice_sv(P.COMPOSERS, ("tên riêng/địa danh",)),
    # nội dung
    "noi_dung_tin": g_message, "noi_dung_nhac": g_remind, "msg": g_message, "todo": g_remind, "mon_hang": choice_sv(P.SHOP),
    "quoc_gia": choice_sv(P.COUNTRIES, ("tên riêng/địa danh",)), "dish": choice_sv(P.DISHES), "ten_quan": g_restaurant,
    "news": choice_sv(P.NEWS_TOPICS), "weather": choice_sv(P.WEATHER), "cau_dung": g_short_cmd, "wake": g_wake,
}
