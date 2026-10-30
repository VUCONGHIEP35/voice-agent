# -*- coding: utf-8 -*-
"""Chuẩn hóa chữ tiếng Việt, thanh điệu, âm tiết, từ địa phương tương đương, từ điển biến thể đọc (dùng cho chấm ASR)."""
import re
import unicodedata


# ---------------------------------------------------------------- chuan hoa
TONE_MARKS = {"\u0300", "\u0301", "\u0303", "\u0309", "\u0323"}  # huyen sac nga hoi nang
def nfc(s):
    return unicodedata.normalize("NFC", s)
def norm_text(s):
    s = nfc(s).lower()
    s = re.sub(r"[^\w\s]", " ", s)  # bo dau cau
    return " ".join(unify_tone_placement(w) for w in s.split())
def strip_tone(w):
    d = unicodedata.normalize("NFD", w)
    return nfc("".join(c for c in d if c not in TONE_MARKS))
def tone_of(w):
    d = unicodedata.normalize("NFD", w)
    for c in d:
        if c in TONE_MARKS:
            return c
    return ""
def unify_tone_placement(w):
    """Kieu dat dau 'moi' (hoà, khoẻ, thuỷ) -> kieu 'cu' (hòa, khỏe, thủy) o van oa/oe/uy khong co am cuoi;
    qu- giu nguyen (quý). Hai kieu la cung mot chu: PhoWhisper-large co luc tra kieu moi, bo cau v3 tron ca hai."""
    t, b = tone_of(w), strip_tone(w)
    if not t or not re.search(r"(?<!q)(oa|oe|uy)$", b):
        return w
    return nfc(b[:-1] + t + b[-1])
def strip_all(w):
    d = unicodedata.normalize("NFD", strip_tone(w))
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")
    return d.replace("đ", "d")
# ---------------------------------------------------------------- am tiet tieng Viet
ONSETS = ["ngh", "ng", "nh", "ch", "gh", "gi", "kh", "ph", "th", "tr", "qu",
          "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x", ""]
VOWELS = "aăâeêioôơuưy"
FINALS = ["ch", "ng", "nh", "c", "m", "n", "p", "t", ""]
_SYL = re.compile(r"^(%s)([%s]{1,3})(%s)$" % ("|".join(ONSETS), VOWELS, "|".join(FINALS)))
def split_syllable(w):
    """Tra ve (onset, vowel, final) cua am tiet da bo dau thanh, hoac None neu khong hop le."""
    m = _SYL.match(strip_tone(w))
    return m.groups() if m else None
def is_viet_syllable(w):
    if not w or len([c for c in unicodedata.normalize("NFD", w) if c in TONE_MARKS]) > 1:
        return False
    return split_syllable(w) is not None
# ---------------------------------------------------------------- tu dien nho (mo rong theo du an)
DIALECT_EQUIV = {  # tu dia phuong -> dang chuan ma ASR hay tra ve
    "tui": "tôi", "hông": "không", "hổng": "không", "nghen": "nhé", "nhen": "nhé", "nha": "nhé",
    "hen": "nhé", "mô": "đâu", "răng": "sao", "rứa": "thế", "chi": "gì", "ni": "này", "tê": "kia",
    "ổng": "ông ấy", "bả": "bà ấy", "vầy": "vậy", "dzậy": "vậy", "zậy": "vậy", "hổm": "hôm",
}
LETTER_NAMES = {"a", "bê", "xê", "đê", "dê", "e", "ê", "gờ", "giê", "hát", "i", "ca", "en", "em",
                "o", "ô", "ơ", "pê", "quy", "ét", "tê", "u", "ư", "vê", "ích", "xì", "dét", "kiu"}
def is_spelled_run(tokens, i):
    """tokens[i] nam trong chuoi >= 2 ten chu cai lien tiep (vd 'em pê ba': 'em','pê')."""
    def ok(j):
        return 0 <= j < len(tokens) and tokens[j] in LETTER_NAMES
    return ok(i) and (ok(i - 1) or ok(i + 1))
# ---------------------------------------------------------------- tu dien bien the doc
def load_lexicon(path):
    """TSV: <dang chuan trong nhan><TAB><bien the 1>|<bien the 2>|...  (dong bat dau '#' bo qua).
    Vd:  auto hold\tô tô hôn|au tô hôn|ô tô hon"""
    lex = []
    if not path:
        return lex
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#") or "\t" not in line:
                continue
            canon, vars_ = line.rstrip("\n").split("\t", 1)
            lex.append((norm_text(canon), [norm_text(v) for v in vars_.split("|") if v.strip()]))
    lex.sort(key=lambda x: -len(x[0]))  # cum dai truoc
    return lex
def ref_variants(ref_norm, lex, cap=32):
    """Moi cach doc hop le cua cau tham chieu (thay dang chuan bang bien the)."""
    outs = [ref_norm]
    for canon, vars_ in lex:
        pat = re.compile(r"(?<!\w)" + re.escape(canon) + r"(?!\w)")
        new = []
        for r in outs:
            if pat.search(r):
                new.extend(pat.sub(v, r) for v in vars_)
        outs.extend(new)
        if len(outs) > cap:
            outs = outs[:cap]
    return outs
