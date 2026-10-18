# -*- coding: utf-8 -*-
from engine import *
import pools as P

TEMPLATES = []


def T(case, tid, intent, act, frames, slots=None, w=1.0, purpose="M1", state=None, factors="", feats_extra=(), review=False,
      variants=None):
    TEMPLATES.append(dict(case=case, id=tid, intent=intent, act=act, frames=frames, slots=slots or {}, w=w, purpose=purpose,
                          state=state, factors=factors, feats_extra=set(feats_extra), review=review, variants=variants))


# ---------------------------------------------------------------- khe dùng chung
def street_only():
    def g(c):
        city = c.rng.choice(list(P.STREETS))
        st = c.rng.choice(P.STREETS[city][2])
        return R(st, st, ("tên riêng/địa danh",))
    return g


def ordinal_word():
    def g(c):
        v = c.rng.choice(["nhất", "hai", "ba", "tư"])
        return R(v, v, ("số",))
    return g


def pct_pair():
    def g(c):
        a = c.rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 70])
        b = c.rng.choice([x for x in (60, 70, 80, 90, 100) if x > a])
        return R(f"{a}% lên {b}%", f"{vn_int(a, c)} phần trăm lên {vn_int(b, c)} phần trăm", ("phần trăm", "số"))
    return g


RADIO_PAIRS = [
    ("VOV Giao thông", "vê ô vê Giao thông", 91.0, None),
    ("VOV 3", "vê ô vê ba", 102.7, None),
    ("VOV 2", "vê ô vê hai", 96.5, None),
    ("VOV 1", "vê ô vê một", None, None),
    ("VOV 5", "vê ô vê năm", 105.5, "Bắc"),
    ("VOH", "vê ô hát", 99.9, "Nam"),
]


def radio(with_freq=0.4):
    def g(c):
        cand = [x for x in RADIO_PAIRS if x[3] in (None, c.v if c.v in ("Bắc", "Nam") else None)]
        raw, sp, f, reg = c.rng.choice(cand)
        feats = {"viết tắt", "tên riêng/địa danh"}
        if f is not None and c.rng.random() < with_freq:
            fr, fs = vn_dec(f, c, 1)
            if abs(f - round(f)) < 1e-9:
                fr, fs = str(int(round(f))), vn_int(int(round(f)), c)
            raw = f"{raw}, FM {fr} MHz"
            sp = f"{sp}, ép em {fs} mê ga héc"
            feats |= {"tần số/công suất", "số", "đơn vị đo"}
        return R(raw, sp, feats)
    return g


def freq_only():
    def g(c):
        f = c.rng.choice([88.0, 89.0, 91.0, 92.5, 94.0, 96.5, 99.9, 100.0, 102.7, 104.0, 105.5, 90.5, 95.0])
        if abs(f - round(f)) < 1e-9:
            fr, fs = str(int(round(f))), vn_int(int(round(f)), c)
        else:
            fr, fs = vn_dec(f, c, 1)
        return R(f"FM {fr} MHz", f"ép em {fs} mê ga héc", ("tần số/công suất", "số", "đơn vị đo", "viết tắt"))
    return g


def link_src():
    def g(c):
        raw, sp = c.rng.choice([("Bluetooth", "blu tút"), ("USB", "u ét bê"), ("Wi-Fi", "oai phai")])
        return R(raw, sp, ("từ mượn tiếng Anh", "viết tắt") if raw == "USB" else ("từ mượn tiếng Anh",))
    return g


def emerg():
    def g(c):
        num, nm = c.rng.choice([("113", "công an"), ("114", "cứu hỏa"), ("115", "cấp cứu")])
        sp = vn_digits(num)
        if c.rng.random() < 0.5:
            return R(f"{nm} {num}", f"{nm} {sp}", ("số",))
        return R(f"{num} {nm}", f"{sp} {nm}", ("số",))
    return g


def poi_swap():
    def g(c):
        a = poi(None, 0.0)(c)
        for _ in range(10):
            b = poi(None, 0.0)(c)
            if b["raw"] != a["raw"]:
                break
        return R(f'{a["raw"]} mà là {b["raw"]}', f'{a["spoken"]} mà là {b["spoken"]}', a["feats"] | b["feats"])
    return g


def contact_swap():
    def g(c):
        a = contact(("anh_chi", "elder", "full"))(c)
        for _ in range(10):
            b = contact(("anh_chi", "elder", "full"))(c)
            if b["raw"] != a["raw"]:
                break
        return R(f'{a["raw"]} mà là {b["raw"]}', f'{a["spoken"]} mà là {b["spoken"]}', a["feats"])
    return g


def num_swap(lo, hi, unit=""):
    def g(c):
        a = c.rng.randint(lo, hi)
        b = c.rng.choice([x for x in range(lo, hi + 1) if x != a])
        return R(f"{a}{unit} mà là {b}{unit}", f"{vn_int(a, c)}{unit} mà là {vn_int(b, c)}{unit}", ("số",))
    return g


def genre_pair():
    def g(c):
        a, b = c.rng.sample(P.GENRES, 2)
        return R(f"{a} mà là {b}", f"{a} mà là {b}", ())
    return g


def numgen_arith():
    def g(c):
        a = c.rng.randint(2, 99)
        b = c.rng.randint(2, 20)
        op, w = c.rng.choice([("cộng", "+"), ("trừ", "-"), ("nhân", "x"), ("chia", ":")])
        if op == "trừ" and a < b:
            a, b = b, a
        return R(f"{a} {op} {b}", f"{vn_int(a, c)} {op} {vn_int(b, c)}", ("số",))
    return g


CFG = dict()
