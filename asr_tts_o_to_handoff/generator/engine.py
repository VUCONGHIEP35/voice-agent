# -*- coding: utf-8 -*-
"""Động cơ sinh câu từ khung × khe."""
import re, math
from gen_core import *
import pools as P

# ---------------------------------------------------------------- tiện ích chọn theo vùng


def pick_region(c, items, key="region", p_local=0.75):
    """Ưu tiên mục cùng vùng với biến thể giọng (nếu có)."""
    if c.v in ("Bắc", "Trung", "Nam") and c.rng.random() < p_local:
        loc = [x for x in items if (x[key] if isinstance(x, dict) else x[key]) == c.v]
        if loc:
            return c.rng.choice(loc)
    return c.rng.choice(items)


# ---------------------------------------------------------------- nhà sản xuất khe
# mỗi hàm trả về hàm g(c) -> dict(raw, spoken, feats:set, meta)

def R(raw, spoken=None, feats=(), meta=None):
    return dict(raw=raw, spoken=spoken if spoken is not None else raw, feats=set(feats), meta=meta)


def choice(lst, feats=()):
    def g(c):
        v = c.rng.choice(lst)
        return R(v, v, feats)
    return g


def choice_pairs(lst, feats=()):
    def g(c):
        a, b = c.rng.choice(lst)
        return R(a, b, feats)
    return g


def intg(lo, hi, step=1, feats=("số",), suffix_raw="", suffix_spoken=""):
    vals = list(range(lo, hi + 1, step))

    def g(c):
        n = c.rng.choice(vals)
        return R(str(n) + suffix_raw, vn_int(n, c) + suffix_spoken, feats)
    return g


def intg_w(vals, feats=("số",)):
    def g(c):
        n = c.rng.choice(vals)
        return R(str(n), vn_int(n, c), feats)
    return g


def decg(lo, hi, step=0.5, feats=("số",)):
    vals = []
    x = lo
    while x <= hi + 1e-9:
        vals.append(round(x, 1))
        x += step

    def g(c):
        x = c.rng.choice(vals)
        if abs(x - round(x)) < 1e-9 and c.rng.random() < 0.6:
            n = int(round(x))
            return R(str(n), vn_int(n, c), feats)
        raw, sp = vn_dec(x, c, 1)
        return R(raw, sp, feats)
    return g


def percent(vals):
    def g(c):
        n = c.rng.choice(vals)
        return R(f"{n}%", vn_int(n, c) + " phần trăm", ("phần trăm", "số"))
    return g


def km_val(vals, dec=False):
    def g(c):
        x = c.rng.choice(vals)
        if isinstance(x, float):
            raw, sp = vn_dec(x, c, 1)
            return R(f"{raw} km", sp + " ki lô mét", ("số", "đơn vị đo"))
        return R(f"{x} km", vn_int(x, c) + " ki lô mét", ("số", "đơn vị đo"))
    return g


def met_val(vals):
    def g(c):
        n = c.rng.choice(vals)
        return R(f"{n} mét", vn_int(n, c) + " mét", ("số", "đơn vị đo"))
    return g


def kmh(vals):
    def g(c):
        n = c.rng.choice(vals)
        return R(f"{n} km/h", vn_int(n, c) + " ki lô mét trên giờ", ("số", "đơn vị đo"))
    return g


def minutes(vals):
    def g(c):
        n = c.rng.choice(vals)
        return R(f"{n} phút", vn_int(n, c) + " phút", ("số", "đơn vị đo"))
    return g


def money(vals, unit="đồng"):
    def g(c):
        n = c.rng.choice(vals)
        raw, sp = vn_money(n, c)
        return R(f"{raw} {unit}", f"{sp} {unit}", ("tiền VND", "số"))
    return g


def kwh(vals):
    def g(c):
        n = c.rng.choice(vals)
        return R(f"{n} kWh", vn_int(n, c) + " ki lô oát giờ", ("số", "đơn vị đo", "viết tắt"))
    return g


def phone():
    def g(c):
        raw, sp = phone_number(c.rng)
        return R(raw, sp, ("số điện thoại", "số"))
    return g


def clock(period=True):
    """Giờ nói tự nhiên, kèm buổi."""
    def g(c):
        r = c.rng
        per = r.choice(["sáng", "sáng", "chiều", "tối"])
        hour = {"sáng": r.choice([5, 6, 7, 8, 9, 10, 11]), "chiều": r.choice([1, 2, 3, 4, 5, 6]), "tối": r.choice([6, 7, 8, 9, 10])}[per]
        style = r.choice(["gio", "gio", "ruoi", "phut", "kem"])
        if style == "kem" and hour > 10:
            style = "gio"
        if style == "gio":
            raw = f"{hour} giờ {per}"
            sp = f"{vn_int(hour, c)} giờ {per}"
        elif style == "ruoi":
            raw = f"{hour} giờ rưỡi {per}"
            sp = f"{vn_int(hour, c)} giờ rưỡi {per}"
        elif style == "phut":
            m = r.choice([5, 10, 15, 20, 25, 40, 45, 50])
            raw = f"{hour} giờ {m} phút {per}"
            sp = f"{vn_int(hour, c)} giờ {vn_int(m, c)} phút {per}"
        else:
            m = r.choice([10, 15, 20])
            h2 = hour + 1
            raw = f"{h2} giờ kém {m} {per}"
            sp = f"{vn_int(h2, c)} giờ kém {vn_int(m, c)} {per}"
        return R(raw, sp, ("giờ/ngày/tháng/năm", "số"))
    return g


def day_phrase():
    """Ngày trong tuần hoặc ngày tháng."""
    def g(c):
        r = c.rng
        k = r.random()
        if k < 0.45:
            return R(r.choice(["hôm nay", "ngày mai", "ngày kia", "tối nay", "sáng mai", "chiều nay", "cuối tuần này", "sáng nay"]), None, ())
        if k < 0.75:
            d = r.choice(["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"])
            return R(d, d, ("giờ/ngày/tháng/năm",))
        dd = r.randint(1, 28)
        mm = r.randint(1, 12)
        return R(f"ngày {dd} tháng {mm}", f"ngày {vn_int(dd, c)} tháng {vn_int(mm, c)}", ("giờ/ngày/tháng/năm", "số"))
    return g


# ---------------------------------------------------------------- khe địa danh/địa chỉ
def _house_no(c):
    r = c.rng
    k = r.random()
    if k < 0.6:
        return str(r.randint(1, 120))
    if k < 0.9:
        return str(r.randint(121, 450))
    return f"{r.randint(1, 120)}{r.choice('ABC')}"


LETTER_SPOKEN = {"a": "a", "b": "bê", "c": "xê"}


def _spoken_house(s, c):
    m = re.match(r"^(\d+)([A-Z]?)$", s)
    n = int(m.group(1))
    l = m.group(2)
    return vn_int(n, c) + ((" " + LETTER_SPOKEN[l.lower()]) if l else "")




def addr():
    cities = [k for k in P.STREETS]

    def g(c):
        r = c.rng
        city = None
        if c.v in ("Bắc", "Trung", "Nam") and r.random() < 0.8:
            cand = [k for k in cities if P.STREETS[k][0] == c.v]
            if cand:
                city = r.choice(cand)
        if city is None:
            city = r.choice(cities)
        reg, alley_term, streets = P.STREETS[city]
        street = r.choice(streets)
        n = _house_no(c)
        form = r.random()
        raw = []
        sp = []
        if form < 0.25:  # số nhà + đường
            raw = [f"số {n}", street]
            sp = [f"số {_spoken_house(n, c)}", street]
        elif form < 0.5:
            raw = [f"{n}", street]
            sp = [f"{_spoken_house(n, c)}", street]
        elif form < 0.85:  # có ngõ/hẻm/kiệt
            m = r.randint(2, 280)
            term = alley_term
            if reg == "Trung" and r.random() < 0.25:
                term = "hẻm"
            raw = [f"số {n}", f"{term} {m}", street]
            sp = [f"số {_spoken_house(n, c)}", f"{term} {vn_int(m, c)}", street]
        else:  # chỉ đường
            raw = [street]
            sp = [street]
        # thêm thành phố
        if r.random() < (0.65 if c.v == reg else 1.0):
            raw.append(", " + city)
            sp.append(", " + city)
        # ghép
        def join(parts):
            out = ""
            for p in parts:
                out += p if p.startswith(",") else (" " + p if out else p)
            return out
        feats = {"địa chỉ", "tên riêng/địa danh", "số"} if len(raw) > 1 else {"địa chỉ", "tên riêng/địa danh"}
        return R(join(raw), join(sp), feats, meta=dict(city=city, region=reg))
    return g


def _numfix(name, c):
    """Đọc số trong tên địa danh (vd. 'quận 1')."""
    if re.fullmatch(r"\d+", name):
        return vn_int(int(name), c)
    return name


def district():
    def g(c):
        r = c.rng
        d = pick_region(c, P.DISTRICTS, p_local=0.7)
        prov = P.PROV[d["prov"]]
        nm = d["name"]
        raw = f'{d["type"]} {nm}'
        sp = f'{d["type"]} {_numfix(nm, c)}'
        if r.random() < 0.6:
            pn = prov["name"]
            if pn == "Hồ Chí Minh":
                pn_say = r.choice(["thành phố Hồ Chí Minh", "Sài Gòn"]) if c.v == "Nam" else "thành phố Hồ Chí Minh"
            elif prov["type"] == "thanh-pho":
                pn_say = "thành phố " + pn
            else:
                pn_say = ("tỉnh " + pn) if r.random() < 0.5 else pn
            raw += ", " + pn_say
            sp += ", " + pn_say
        return R(raw, sp, ("tên riêng/địa danh", "địa chỉ") + (("số",) if re.fullmatch(r"\d+", nm) else ()), meta=dict(prov=prov["name"]))
    return g


def city():
    def g(c):
        item = pick_region(c, [dict(n=a, region=b) for a, b in P.CITIES], p_local=0.6)
        return R(item["n"], item["n"], ("tên riêng/địa danh",), meta=dict(region=item["region"]))
    return g


def poi(kinds=None, with_city=0.35):
    def g(c):
        items = [x for x in P.POIS if (kinds is None or x["kind"] in kinds)]
        it = pick_region(c, items, p_local=0.7)
        raw = it["name"]
        sp = raw
        for k, v in P.POI_SPOKEN_FIX.items():
            sp = sp.replace(k, v)
        feats = {"tên riêng/địa danh"}
        if any(ch.isdigit() for ch in raw):
            feats.add("số")
        if re.search(r"[A-Za-z]{3,}", re.sub(r"(Đại học|Quốc|Hà Nội|Bách|Hồ Chí Minh)", "", raw)) and any(w in raw for w in ["Mall", "City", "Center", "Royal", "Hills", "Landmark", "Sala", "Crescent", "Saigon", "Vincom", "Aeon", "Lotte", "Giga", "Indochina", "Plaza", "Riverside", "Vinhomes", "Park", "Central", "Ecopark", "Vinpearl", "Times", "Grand"]):
            feats.add("từ mượn tiếng Anh")
        if with_city and c.rng.random() < with_city and it["city"] not in raw:
            raw += ", " + it["city"]
            sp += ", " + it["city"]
        return R(raw, sp, feats, meta=dict(kind=it["kind"], city=it["city"]))
    return g


def pool_choice(name, feats=("tên riêng/địa danh",)):
    def g(c):
        v = c.rng.choice(P.POOLS[name])
        return R(v, v, feats)
    return g


def saved(kind):
    def g(c):
        lst = P.HOME_LIKE if kind == "home" else P.PLACE_LIKE
        v = c.rng.choice(lst)
        return R(v, v, ())
    return g


def highway():
    def g(c):
        v = c.rng.choice(P.HIGHWAYS)
        sp = v
        sp = re.sub(r"quốc lộ (\d+)([A-Z]?)", lambda m: "quốc lộ " + vn_int(int(m.group(1)), c) + ((" " + m.group(2).lower()) if m.group(2) else ""), sp)
        feats = {"tên riêng/địa danh"}
        if re.search(r"\d", v):
            feats.add("số")
        return R(v, sp, feats)
    return g


# ---------------------------------------------------------------- khe người
def contact(kinds=("anh_chi", "elder", "relative", "full", "ctx", "birth")):
    def g(c):
        r = c.rng
        kind = r.choice(kinds)
        if kind == "birth" and c.v != "Nam":
            kind = "anh_chi"
        gender = r.choice(["M", "F"])
        first = r.choice(P.MALE if gender == "M" else P.FEMALE)
        if kind == "anh_chi":
            v = f'{r.choice(P.HON_PEER[gender])} {first}'
        elif kind == "elder":
            v = f'{r.choice(P.HON_ELDER[gender])} {first}'
        elif kind == "full":
            sur = r.choice(P.SURNAMES)
            mid = r.choice(P.MID_M if gender == "M" else P.MID_F)
            hon = r.choice(["anh", "chị", "cô", "chú", "bác"] if gender == "M" and False else (P.HON_PEER[gender] + [h for h in P.HON_ELDER[gender] if h in ("cô", "chú", "bác", "dì")]))
            v = f'{hon} {sur} {mid} {first}'
        elif kind == "ctx":
            hon = r.choice(P.HON_PEER[gender])
            v = f'{hon} {first} {r.choice(P.CONTEXT_TAGS)}'
        elif kind == "birth":
            b = r.choice(P.BIRTH)
            v = f'{r.choice(["anh", "chị", "chú", "dì", "cô", "bác"])} {b}'
        else:  # relative
            opts = {"Chuẩn chung": ["mẹ", "bố", "vợ", "chồng", "em gái", "em trai", "anh trai", "chị gái", "con gái", "con trai"],
                    "Bắc": ["mẹ", "bố", "u", "bầm", "vợ", "chồng", "em gái", "anh trai", "chị gái"],
                    "Nam": ["má", "ba", "tía", "vợ", "chồng", "em gái", "anh Hai", "chị Hai", "con gái"],
                    "Trung": ["mạ", "ba", "o", "vợ", "chồng", "em gái", "anh trai", "chị gái"]}
            v = r.choice(opts[c.v])
        return R(v, v, ("tên riêng/địa danh",), meta=dict(kind=kind))
    return g


# ---------------------------------------------------------------- kết xuất
SLOT_RE = re.compile(r"\{(?!L:)(\w+)\}")


def build_text(frame, slots, gens, c):
    """frame: chuỗi có {L:x}, (a|b), {slot}; trả (skeleton, values)."""
    sk = lex_resolve(frame, c)
    sk = resolve_alts(sk, c)
    names = SLOT_RE.findall(sk)
    vals = {}
    for n in names:
        if n not in vals:
            if n in gens:
                vals[n] = gens[n](c)
            elif n in GLOBAL_SLOTS:
                vals[n] = GLOBAL_SLOTS[n](c)
            else:
                raise KeyError(n)
    return sk, vals


def substitute(sk, vals, which):
    return SLOT_RE.sub(lambda m: vals[m.group(1)][which], sk)


GLOBAL_SLOTS = {}


def register_global(name, g):
    GLOBAL_SLOTS[name] = g
