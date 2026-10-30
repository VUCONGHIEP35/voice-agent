# -*- coding: utf-8 -*-
"""Bảng từ ngoại lai (review/BANG_tu_ngoai_lai.csv) -> cách đọc theo vùng (CHANGES_v3.md C4, mục 4).

Quy tắc:
  1. Câu có speaker_region = X chỉ dùng các cách đọc ghi ở cột vùng X (nguoi_Bac_noi / nguoi_Trung_noi / nguoi_Nam_noi).
  2. Cột vùng X rỗng (chưa duyệt): giữ cách đọc hiện tại trong text_spoken, gắn cờ; không tự chọn.
  3. Nhiều số: chọn ngẫu nhiên theo rng của bộ sinh, ghi pron_variant (vd 'L01-2').
  4. text_raw luôn giữ dạng viết.
Hai mức cờ (quyết định của người dùng 2026-10-15):
  - 'nên duyệt' (FLAG_SHOULD, không nằm trong LOW_FLAG_KEYS): từ vay đã Việt hóa và viết tắt/đơn vị đã đổi sang chữ
    (cách đọc hiện tại khác chữ viết, vd USB -> 'u ét bê'; hoặc dòng từ vay Việt hóa camera / video / radio).
  - 'cần duyệt' (FLAG_MUST, chứa 'cách đọc chưa xác minh'): tên thương hiệu, tên riêng, từ giữ chữ Latin chưa có cách đọc
    (cách đọc hiện tại 'giữ nguyên' hoặc '(chưa có)'), kể cả Vietmap, Waze, VETC, ePass.
Cột vùng ghi '0' (vùng không dùng cách nào): giữ cách đọc hiện tại, gắn cờ 'cần duyệt'.
"""
import csv, hashlib, os, re

from cauhinh.duong_dan import ROOT

CSV_PATH = os.environ.get("BANG_TU_NGOAI", os.path.join(os.path.dirname(ROOT), "review", "BANG_tu_ngoai_lai.csv"))
REGION_COL = {"Bắc": "nguoi_Bac_noi", "Trung": "nguoi_Trung_noi", "Nam": "nguoi_Nam_noi"}
VIET_HOA_IDS = {"L58"}                       # camera / video / radio: từ vay đã Việt hóa
FLAG_MUST = "cách đọc chưa xác minh: {}"
FLAG_SHOULD = "cách đọc từ ngoại đã đổi chữ, chưa duyệt theo vùng: {}"
FLAG_ZERO = "cách đọc chưa xác minh (vùng {} ghi 0, không dùng cách nào): {}"
KEEP_AS_IS = ("giữ nguyên", "(chưa có)", "")

ENTRIES = []          # mỗi mục: dict(id, term, current, readings, cols, level, pat)
CSV_SHA = None


def _clean_reading(s):
    s = re.sub(r"\s*\([^)]*\)", "", s).strip()
    return re.sub(r"\s+", " ", s.replace("-", " "))


def _pattern(term):
    parts = [re.escape(p) for p in re.split(r"[-\s]+", term)]
    return re.compile(r"(?<![\wÀ-ỹ])" + r"[-\s]?".join(parts) + r"(?![\wÀ-ỹ])", re.I)


def _load():
    global CSV_SHA
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"Không thấy bảng từ ngoại: {CSV_PATH}")
    CSV_SHA = hashlib.sha256(open(CSV_PATH, "rb").read()).hexdigest()
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            terms = [t.strip() for t in row["dang_viet(text_raw)"].split("/")]
            cur_all = [c.strip() for c in row["cach_doc_hien_tai_trong_bo"].split("/")]
            reads = [row.get(f"cach_doc_de_xuat_{k}", "").strip() for k in (1, 2, 3)]
            for j, term in enumerate(terms):
                cur = cur_all[j] if len(cur_all) == len(terms) else cur_all[0]
                cur = "" if cur in KEEP_AS_IS else cur
                # dòng ghép nhiều từ ('a / b / c'): cách đọc đề xuất cũng tách theo '/'
                rd = []
                for r in reads:
                    ps = [p.strip() for p in r.split("/")] if r else []
                    rd.append(_clean_reading(ps[j] if len(ps) == len(terms) else (ps[0] if ps else "")))
                # đã đổi chữ = cách đọc hiện tại không còn phần chữ viết gốc nào (USB -> 'u ét bê'; 'Zing em pê ba', 'ca pop' thì chưa)
                parts = [p for p in re.split(r"[-\s]+", term) if len(p) >= 2]
                converted = bool(cur) and not any(re.search(r"(?<![\wÀ-ỹ])" + re.escape(p) + r"(?![\wÀ-ỹ])", cur, re.I) for p in parts)
                level = "should" if converted or row["id"] in VIET_HOA_IDS else "must"
                ENTRIES.append(dict(id=row["id"], term=term, current=cur, readings=rd,
                                    cols={g: row.get(c, "").strip() for g, c in REGION_COL.items()},
                                    level=level, pat=_pattern(term)))
    ENTRIES.sort(key=lambda e: -len(e["term"]))


_load()


def current_reading(raw):
    """Cách đọc hiện tại của một tên (dùng cho khe): giữ chữ viết nếu bảng ghi 'giữ nguyên' hoặc chưa có."""
    for e in ENTRIES:
        if e["term"].lower() == raw.lower() and e["current"]:
            return e["current"]
    return raw


def apply(raw, spoken, region, rng):
    """Tra mọi từ trong bảng có mặt ở text_raw. Trả (spoken, flags, pron_variants)."""
    flags, variants, taken = [], [], []
    for e in ENTRIES:
        for m in e["pat"].finditer(raw):
            if any(a < m.end() and m.start() < b for a, b in taken):   # đã khớp tên dài hơn ('YouTube Music' trước 'YouTube')
                continue
            taken.append((m.start(), m.end()))
            col = e["cols"][region]
            nums = [int(x) for x in re.findall(r"\d", col)]
            if not col:
                flags.append((FLAG_SHOULD if e["level"] == "should" else FLAG_MUST).format(e["term"]))
                continue
            ok = [k for k in nums if 1 <= k <= 3 and e["readings"][k - 1]]
            if not ok:
                flags.append(FLAG_ZERO.format(region, e["term"]))
                continue
            k = rng.choice(ok)
            src = e["current"] or m.group(0)
            new = _sub_once(spoken, src, e["readings"][k - 1])
            if new is None:
                flags.append(FLAG_MUST.format(e["term"]) + " (không tìm thấy trong text_spoken để thay)")
                continue
            spoken = new
            variants.append(f"{e['id']}-{k}")
    return spoken, sorted(set(flags)), variants


def _sub_once(text, old, new):
    m = re.search(r"(?<![\wÀ-ỹ])" + re.escape(old) + r"(?![\wÀ-ỹ])", text, re.I)
    if not m:
        return None
    rep = new[0].upper() + new[1:] if m.start() == 0 else new
    return text[:m.start()] + rep + text[m.end():]
