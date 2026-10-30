# -*- coding: utf-8 -*-
"""Hàm dùng chung khi chọn câu và gán giọng: băm tất định, chia theo tỷ lệ, nhận diện từ ngoại, từ điển đọc cho TTS."""
import csv
import hashlib
import json
import os
import re

from cauhinh.giong import VOICES


LEN_ORDER = {"Rất ngắn": 0, "Ngắn": 1, "Thường": 2, "Dài": 3}
LOAN_FLAG = "cách đọc chưa xác minh"
def h32(*parts):
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)
def largest_remainder(weights, total):
    """weights: {k: số câu trong bộ}; trả {k: số câu chọn} cộng đúng total, theo tỷ lệ."""
    s = sum(weights.values())
    raw = {k: total * w / s for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    rest = total - sum(out.values())
    for k in sorted(raw, key=lambda k: (-(raw[k] - out[k]), str(k)))[:rest]:
        out[k] += 1
    return out
def check_voice_table(voices_json):
    """So bảng VOICES với voices_v3_turbo.json của gói vieneu (nếu tìm được). Lệch thì dừng."""
    path = voices_json
    if not path:
        try:
            import vieneu
            path = os.path.join(os.path.dirname(vieneu.__file__), "assets", "voices_v3_turbo.json")
        except ImportError:
            print("Không import được vieneu: bỏ qua bước so bảng giọng với voices_v3_turbo.json (chạy bằng .venv để kiểm).")
            return
    with open(path, encoding="utf-8") as f:
        presets = json.load(f).get("presets", {})
    bad = [f"{n}: bảng ghi {v[0]}, tệp ghi {presets.get(n, {}).get('region')}"
           for n, v in VOICES.items() if presets.get(n, {}).get("region") != v[0]]
    if bad:
        raise SystemExit("Bảng giọng lệch voices_v3_turbo.json:\n  " + "\n  ".join(bad))
    print(f"Đã so bảng giọng với {path}: khớp {len(VOICES)} giọng.")
def is_loan(r):
    return any(x.startswith(LOAN_FLAG) for x in r["review_reasons"])
def loan_names(r):
    return [x.split(":", 1)[1].strip() for x in r["review_reasons"] if x.startswith(LOAN_FLAG) and ":" in x]
ONSETS = {"", "b", "c", "ch", "d", "đ", "g", "gh", "gi", "h", "k", "kh", "l", "m", "n", "ng", "ngh", "nh", "p", "ph",
          "q", "qu", "r", "s", "t", "th", "tr", "v", "x"}
CODAS = {"", "c", "ch", "m", "n", "ng", "nh", "p", "t"}
def base_letters(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "\x00"))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", s).replace("\x00", "đ")
def not_vietnamese(reading):
    """Âm tiết không theo cấu trúc tiếng Việt (vd 'za', 'plây', 'blu'): VieNeu có thể đọc kiểu Anh. Trả danh sách âm tiết lỗi."""
    bad = []
    for syl in reading.split():
        b = base_letters(syl)
        m = re.fullmatch(r"([^aeiouy]*)([aeiouy]+)([^aeiouy]*)", b)
        if not m or re.search(r"[fjwz]", b) or m.group(1) not in ONSETS or m.group(3) not in CODAS:
            bad.append(syl)
    return bad
def load_tts_lexicon(path):
    """{dạng viết thường: {vùng: cách đọc}}; ô vùng rỗng lấy ô có giá trị đầu tiên. Cảnh báo âm tiết không phải tiếng Việt."""
    lex = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            key = (r.get("dang_trong_text_spoken") or "").strip()
            if not key or key.startswith("#") or key.startswith("?"):
                continue
            vals = {reg: re.sub(r"\s+", " ", (r.get(reg) or "").replace("-", " ")).strip() for reg in ("Bắc", "Trung", "Nam")}
            first = next((v for v in vals.values() if v), "")
            if first:
                lex[key.lower()] = {reg: (v or first) for reg, v in vals.items()} | {"_nguon": (r.get("nguon") or "").strip()}
                bad = sorted({s for v in vals.values() for s in not_vietnamese(v)})
                if bad:
                    print(f"[cảnh báo] {key}: âm tiết không theo cấu trúc tiếng Việt {bad} -> VieNeu có thể đọc kiểu Anh")
    return lex
def load_bang(path):
    """BANG_tu_ngoai_lai.csv -> {tên viết thường: (đọc Bắc, Trung, Nam, nguồn, đề xuất khác)}.
    Có cột người_X_nói đã điền thì dùng (nguồn 'duyet'); chưa thì dùng cach_doc_de_xuat_1 cho cả 3 vùng (nguồn 'K1 chưa duyệt').
    Dòng gộp kiểu 'Eco / Sport / Normal' được tách theo ' / '."""
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            names = [x.strip() for x in r["dang_viet(text_raw)"].split(" / ")]
            cols = {k: [x.strip() for x in (r.get(k) or "").split(" / ")] for k in
                    ("nguoi_Bac_noi", "nguoi_Trung_noi", "nguoi_Nam_noi", "cach_doc_de_xuat_1", "cach_doc_de_xuat_2", "cach_doc_de_xuat_3")}
            for i, nm in enumerate(names):
                get = lambda k: (cols[k][i] if i < len(cols[k]) else "").replace("-", " ")
                reviewed = [get(k) for k in ("nguoi_Bac_noi", "nguoi_Trung_noi", "nguoi_Nam_noi")]
                if any(reviewed):
                    out[nm.lower()] = (*reviewed, "duyet", "")
                else:
                    k1 = get("cach_doc_de_xuat_1")
                    others = " | ".join(x for x in (get("cach_doc_de_xuat_2"), get("cach_doc_de_xuat_3")) if x)
                    out[nm.lower()] = (k1, k1, k1, "K1 chưa duyệt", others)
    return out
def apply_tts_lexicon(text, region, lex):
    """Thay các dạng trong từ điển (dài trước, không phân biệt hoa thường, đúng ranh giới từ). Trả (tts_text, [mục đã thay])."""
    used = []
    out = text
    for key in sorted(lex, key=len, reverse=True):
        pat = re.compile(r"(?<![\wÀ-ỹ])" + re.escape(key) + r"(?![\wÀ-ỹ])", re.IGNORECASE)
        if pat.search(out):
            out = pat.sub(lex[key][region], out)
            used.append(f"{key}={lex[key][region]} ({lex[key]['_nguon'] or 'chưa ghi nguồn'})")
    return out, used
