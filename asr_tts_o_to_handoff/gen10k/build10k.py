# -*- coding: utf-8 -*-
"""Sinh khoảng 10.000 câu M1 + M2 theo mẫu câu × khe.

Chạy (từ thư mục gen10k/):  py -3.13 build10k.py [--seed 20261013] [--out ../data/m1m2_10k]
Ghi: 9 file JSONL theo nhóm chủ đề, manifest.json, README_nguon.md (sinh tự động phần số liệu).
"""
import argparse, collections, hashlib, json, math, os, random, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vnnum import normalize, has_digit, REGIONS
from lexicon10k import rewrite, decorate, forbidden_hits, PARTICLE_INFO, REGIONAL_PARTICLES, LOW_WORDS
from slots10k import Ctx, SV, SLOTS
import frames10k as FR
import frames_app10k as FA
import pools10k as P
import diversity10k as DV
import loanwords10k as LW

VERSION = "gen10k-3.0"
ROOT = os.path.dirname(HERE)
XLSX = os.path.join(ROOT, "data", "du_lieu_asr_tts_o_to_v0.3.xlsx")

FALLBACK_QUOTA = {"CS01": 1500, "CS02": 300, "CS03": 1400, "CS04": 1200, "CS05": 1200, "CS06": 500, "CS07": 600, "CS08": 700,
                  "CS09": 300, "CS10": 1100, "CS11": 300, "CS12": 900}
CASE_NAMES = {}

GROUPS = [
    ("01_dan_duong.jsonl", "Dẫn đường", ["CS01"]),
    ("02_dieu_khien_xe.jsonl", "Điều khiển xe", ["CS03"]),
    ("03_giai_tri.jsonl", "Giải trí", ["CS04"]),
    ("04_dien_thoai.jsonl", "Điện thoại và tin nhắn", ["CS05"]),
    ("05_trang_thai_xe_va_sac.jsonl", "Trạng thái xe, sạc và nhiên liệu", ["CS06", "CS07"]),
    ("06_giao_thong_thoi_tiet.jsonl", "Giao thông và thời tiết", ["CS08"]),
    ("07_hoi_thoai_chu_dong.jsonl", "Hội thoại và gợi ý chủ động", ["CS10"]),
    ("08_tra_loi_ngan_lam_ro.jsonl", "Trả lời ngắn, làm rõ, ngoại tuyến", ["CS12"]),
    ("09_khan_cap_an_toan_hanh_khach.jsonl", "Khẩn cấp, cảnh báo an toàn, hành khách", ["CS02", "CS09", "CS11"]),
]

SLOT_RE = re.compile(r"\{(\w+)(?:#(\d))?\}")
DUP_RE = re.compile(r"(?<![\wÀ-ỹ])([\wÀ-ỹ]{2,})\s+((?i:\1))(?![\wÀ-ỹ])")
ALT_RE = re.compile(r"\(([^()]*\|[^()]*)\)")
PLACE_SLOTS = {"addr", "poi", "poi_air", "poi_hosp", "dist", "city", "st", "hw", "dia_diem", "thanh_pho", "ten_duong", "quan_huyen",
               "so_nha", "ten_tram_sac", "ten_quan"}
TONE_PAIRS = {"đỗ", "đổ", "rẽ", "rẻ", "nghỉ", "nghĩ", "mở", "mỡ", "bảy", "bẫy", "sửa", "sữa", "nửa", "nữa", "bão", "bảo", "giữ",
              "chỗ", "lẽ", "lễ", "hủy", "ngã", "ngả", "dẫn", "dẩn", "kẹt", "kẻ", "đã", "đả"}
ENGLISH = {"bluetooth", "wi-fi", "wifi", "playlist", "podcast", "auto", "air-con", "ok", "eco", "sport", "normal", "cruise", "control",
           "lane", "assist", "hold", "check", "engine", "youtube", "spotify", "messenger", "facebook", "gmail", "viber", "telegram",
           "google", "maps", "apple", "carplay", "android", "mall", "center", "centre", "city", "royal", "plaza", "landmark", "crescent",
           "saigon", "aeon", "lotte", "giga", "vinhomes", "park", "central", "ocean", "smart", "mart", "times", "ecopark", "takashimaya",
           "hills", "chill", "road", "trip", "top", "hit", "edm", "lofi", "lo-fi", "remix", "acoustic", "indie", "hip", "hop", "ballad",
           "rap", "pop", "rock", "jazz", "k-pop", "v-pop", "live", "tinny", "love", "binz", "karik", "jack", "suboi", "justatee",
           "hieuthuhai", "rpt", "mck", "da", "lab", "wren", "evans", "k-icm", "amee", "grey", "t.r.i", "noo", "m-tp", "doraemon", "tom",
           "jerry", "peppa", "pig", "frozen", "baby", "shark", "masha", "conan", "usb", "fm", "mhz", "vov", "voh", "a/c", "gps", "aqi",
           "usd", "atm", "abs", "odo", "kwh", "kw", "sms", "zing", "mp3", "vaicaunoicokhiennguoithaydoi", "ron", "bot", "euro", "won",
           "pasteur", "yersin", "datanla", "online", "offline", "video", "pm2.5", "vnd",
           "vietmap", "waze", "vetc", "epass", "music"}          # v3: tên app mới (C4); 'music' của YouTube Music / Apple Music
LOANS_VI = {"camera", "massage", "album", "sofa", "karaoke", "video", "radio", "taxi", "micro", "podcast"}
FREE_TEXT_SLOTS = {"msg", "noi_dung_tin", "cau_dung", "wake"}
# cờ cần người duyệt (mức 'cần duyệt'); các cờ khác là 'nên duyệt'
LOW_FLAG_KEYS = ("viết tắt chưa xác minh", "xẹt", "nghệ danh", "tên đài", "mồng/mùng", "tên bệnh viện", "cách đọc chưa xác minh")


def pick_w(rng, pairs):
    r = rng.random() * sum(w for _, w in pairs)
    acc = 0
    for v, w in pairs:
        acc += w
        if r <= acc:
            return v
    return pairs[-1][0]


def read_quota():
    try:
        import openpyxl
        wb = openpyxl.load_workbook(XLSX, data_only=True)
        ws = wb["Chi_tieu"]
        q = {}
        start = False
        for row in ws.iter_rows(values_only=True):
            if row and row[0] == "Mã case":
                start = True
                continue
            if start and row and isinstance(row[0], str) and re.fullmatch(r"CS\d\d", row[0]):
                CASE_NAMES[row[0]] = row[1]
                target = row[3] if isinstance(row[3], (int, float)) else (row[2] or 0) * 10000
                q[row[0]] = int(round(target))
        if len(q) == 12:
            return q, "data/du_lieu_asr_tts_o_to_v0.3.xlsx, sheet Chi_tieu (cột 'Số câu khác nhau mục tiêu')"
    except Exception as e:  # noqa
        print("Không đọc được Chi_tieu, dùng hạn ngạch mặc định:", e)
    return dict(FALLBACK_QUOTA), "hạn ngạch mặc định trong CLAUDE.md (không đọc được xlsx)"


# ------------------------------------------------------------------ dựng một câu
def resolve_alts(text, rng):
    for _ in range(12):
        m = ALT_RE.search(text)
        if not m:
            break
        text = text[:m.start()] + rng.choice(m.group(1).split("|")) + text[m.end():]
    return re.sub(r"\s+", " ", text).strip()


def ph(k):
    return "⟦s" + "abcdefghij"[k] + "⟧"


def asr_key(t):
    t = t.lower()
    t = re.sub(r"[\.,;:!?\"“”()\[\]–-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def syllables(t):
    return len(re.sub(r"[\.,;:!?–]", " ", t).split())


def length_class(n):
    return "Rất ngắn" if n <= 3 else "Ngắn" if n <= 8 else "Thường" if n <= 15 else "Dài"


def finish(t, act):
    t = t.strip().rstrip(",")
    t = t[0].upper() + t[1:]
    end = "?" if act == "Câu hỏi" else "!" if act == "Kêu cứu" else "."
    return t + end


class Reject(Exception):
    pass


# Hồ sơ người nói miền Trung (phụ lục mục 3, đề xuất 40/30/30; suy luận chưa kiểm chứng)
TRUNG_RESIDENCE = [("Quê", .4), ("Hà Nội", .3), ("TP.HCM", .3)]
TRUNG_SUB_QUE = ["Huế", "Nghệ Tĩnh", "Quảng Nam – Đà Nẵng"]          # có bảng từ có nguồn
TRUNG_SUB_ALL = TRUNG_SUB_QUE + ["Nam Trung Bộ"]                    # sống ở HN/HCM: từ không phụ thuộc tiểu vùng
SUB_PROFILE = {"Huế": "Trung-Huế", "Nghệ Tĩnh": "Trung-Nghệ", "Quảng Nam – Đà Nẵng": "Trung-Quảng"}


def pick_profile(region, rng):
    if region == "Bắc":
        return dict(profile="Bắc", residence="Quê", sub_region="Bắc Bộ", vocab_source="Bắc")
    if region == "Nam":
        return dict(profile="Nam", residence="Quê", sub_region="Nam Bộ", vocab_source="Nam")
    res = pick_w(rng, TRUNG_RESIDENCE)
    if res == "Quê":
        sub = rng.choice(TRUNG_SUB_QUE)
        return dict(profile=SUB_PROFILE[sub], residence=res, sub_region=sub, vocab_source="Trung")
    sub = rng.choice(TRUNG_SUB_ALL)
    if res == "Hà Nội":
        return dict(profile="Trung-HN", residence=res, sub_region=sub, vocab_source="Bắc")
    return dict(profile="Trung-HCM", residence=res, sub_region=sub, vocab_source="Nam")


def render(frame, region, rng, prof=None):
    prof = prof or pick_profile(region, rng)
    profile = prof["profile"]
    text = frame["text"]
    nodeco = text.startswith("!")
    noprefix = text.startswith("~") or nodeco
    text = text.lstrip("!~")
    text = resolve_alts(text, rng)
    c = Ctx(rng, region, frame["case"], profile, prof["residence"], prof["sub_region"])

    # tách khe -> placeholder
    slots = []

    def take(m):
        slots.append((m.group(1), m.group(2)))
        return ph(len(slots) - 1)
    skel = SLOT_RE.sub(take, text)

    # viết lại từ vùng cho phần chữ cố định
    skel, marks = rewrite(skel, profile, rng, memo=c.lexmemo)
    added, has_wake = [], False
    if not nodeco:
        ends_free = (bool(slots) and slots[-1][0] in FREE_TEXT_SLOTS and skel.rstrip().endswith(ph(len(slots) - 1))) \
            or frame["intent"] in ("sua_lenh", "keu_cuu")
        wake_p = 0.0 if any(name == "wake" for name, _ in slots) else 0.05
        skel, added, has_wake = decorate(skel, frame["act"], profile, rng, allow_prefix=not noprefix, allow_suffix=not ends_free,
                                         wake_p=wake_p)
        if profile in ("Nam", "Trung-Huế", "Trung-HCM") and c.lexmemo.get("tôi") == "tôi":
            skel = re.sub(r"(?<![\wÀ-ỹ])tui(?![\wÀ-ỹ])", "tôi", skel)
    literal_only = re.sub(r"⟦s.⟧", " ", skel)
    hits = forbidden_hits(literal_only, profile)
    if hits:
        raise Reject("lẫn vùng: " + ";".join(hits))

    # sinh giá trị khe
    vals = []
    seen_by_name = collections.defaultdict(list)
    for name, idx in slots:
        if name not in SLOTS:
            raise KeyError(f"khe chưa định nghĩa: {name} ({frame['fid']} {frame['src']})")
        sv = None
        for _ in range(12):
            sv = SLOTS[name](c)
            if sv.raw not in seen_by_name[name]:
                break
        if sv.raw in seen_by_name[name]:
            raise Reject("không sinh được giá trị khác nhau")
        seen_by_name[name].append(sv.raw)
        vals.append((name, sv))

    norm = normalize(skel, region)
    spoken = norm.text
    raw = skel
    for k, (name, sv) in enumerate(vals):
        raw = raw.replace(ph(k), sv.raw)
        spoken = spoken.replace(ph(k), sv.spoken)
    if "⟦" in raw or "⟦" in spoken:
        raise Reject("placeholder sót")
    raw = finish(re.sub(r"\s+", " ", raw), frame["act"])
    spoken = finish(re.sub(r"\s+", " ", spoken), frame["act"])
    for m in DUP_RE.finditer(raw):
        a, b = m.group(1), m.group(2)
        if not (a.islower() and b[:1].isupper()):          # cho phép 'anh Anh', 'chị Chi'
            raise Reject(f"lặp từ liền nhau: {a} {b}")
    # từ ngoại (v3, C4): cách đọc theo cột vùng đã duyệt của bảng; chưa duyệt thì giữ nguyên và gắn cờ
    spoken, loan_flags, pron = LW.apply(raw, spoken, region, rng)
    if has_digit(spoken):
        raise Reject("còn chữ số trong text_spoken: " + spoken)
    return dict(raw=raw, spoken=spoken, vals=vals, marks=marks, added=added, has_wake=has_wake, norm=norm, literal=literal_only,
                prof=prof, loan_flags=loan_flags, pron_variant=",".join(pron))


# ------------------------------------------------------------------ gắn nhãn
def annotate(frame, region, r, rng):
    raw, spoken, vals = r["raw"], r["spoken"], r["vals"]
    feats = set(r["norm"].feats)
    flags = set(r["norm"].flags) | set(r["loan_flags"])
    marks = list(r["marks"])
    meta = {}
    used_place = False
    contact_kind = None
    for name, sv in vals:
        feats |= sv.feats
        flags |= sv.flags
        marks += sv.marks
        meta.update({k: v for k, v in sv.meta.items() if v})
        if name in PLACE_SLOTS:
            used_place = True
        if "kind" in sv.meta:
            contact_kind = sv.meta["kind"]
    tokens = re.findall(r"[\wÀ-ỹ][\wÀ-ỹ/.\-]*", raw.lower())
    eng = sorted({t.strip(".") for t in tokens if t.strip(".") in ENGLISH})
    loans = sorted({t for t in tokens if t in LOANS_VI})
    if eng:
        feats.add("từ mượn tiếng Anh")
    language_mix = "Việt + Anh" if eng else "Việt"

    n_syl = syllables(spoken)
    lc = length_class(n_syl)
    fac = set()
    if feats & {"số", "giờ/ngày/tháng/năm", "tiền VND", "phần trăm", "đơn vị đo", "số điện thoại", "tần số/công suất"}:
        fac.add("E03")
    if used_place or "địa chỉ" in feats:
        fac.add("E04")
    if eng or loans:
        fac.add("E05")
    if "viết tắt" in feats or re.search(r"[%°/]|[A-Z]{2,}|km/h|\bkm\b|kWh|MHz", raw):
        fac.add("E07")
    lw = set(re.findall(r"[\wÀ-ỹ]+", raw.lower()))
    if contact_kind or lw & {"ạ", "dạ", "vâng", "nhé", "nha", "nghen", "nghe", "giùm", "dùm", "hộ", "tui", "mình", "con"} \
            or "bạn ơi" in raw.lower() or "trợ lý" in raw.lower():
        fac.add("E06")
    if n_syl <= 3 or n_syl >= 16:
        fac.add("E08")
    if set(re.findall(r"[\wÀ-ỹ]+", spoken.lower())) & TONE_PAIRS:
        fac.add("E02")
    regional_marks = [m for m in marks if m.regional]
    if any(m.factor == "S51" for m in regional_marks):
        fac.add("S51")
    if any(m.factor == "S52" for m in regional_marks) or set(r["added"]) & REGIONAL_PARTICLES[r["prof"]["profile"]]:
        fac.add("S52")
    sp_words = set(re.findall(r"[\wÀ-ỹ]+", spoken.lower()))
    if sp_words & {"linh", "lẻ", "nghìn", "ngàn", "mồng", "mùng"} and not set(re.findall(r"[\wÀ-ỹ]+", raw.lower())) & {"linh", "lẻ", "nghìn", "ngàn", "mồng", "mùng"}:
        fac.add("S53")
    if raw.lower().count("nghìn") or raw.lower().count("ngàn"):
        fac.add("S53")
    if meta.get("alias") or "Sài Gòn" in raw:
        fac.add("S54")
    if language_mix == "Việt + Anh":
        fac.add("S55")
    state = pick_w(rng, FR.STATE.get(frame["intent"], [("Bình thường", 1)]))
    if frame["act"] in ("Câu cụt", "Kêu cứu") or frame["intent"] == "sua_lenh" or re.search(r"(^|, )(ờ|à|ừm),", raw.lower()) \
            or state in ("Vội / nói nhanh", "Căng thẳng / khẩn"):
        fac.add("S23")
    if frame["act"] == "Câu hỏi":
        fac.add("S33")
    if "," in raw.rstrip(".?!"):
        fac.add("S34")
    if frame["intent"] in FR.D01_INTENTS:
        fac.add("D01")
    if frame["intent"] in FR.D03_INTENTS or frame["act"] == "Kêu cứu":
        fac.add("D03")

    # duyệt: 'cần duyệt' (bắt buộc) / 'nên duyệt' / 'không bắt buộc'
    must, should = [], []
    if frame["src"].startswith("LLM"):
        must.append("khung do LLM diễn đạt lại (v2), chưa có người duyệt")
    elif frame["src"].startswith("phiên v2"):
        must.append("khung chức năng xe thêm ở v2 (từ src_lang car_terms, K1), chưa có người duyệt")
    elif frame["src"] == FA.SRC:
        must.append(f"khung app thêm ở v3 (nhóm {frame['app_group']}, K1), chưa có người duyệt")
    if region == "Trung":
        must.append(f"giọng miền Trung ({r['prof']['sub_region']}, sống ở {r['prof']['residence']}): cần người bản ngữ Trung Bộ duyệt")
    for m in regional_marks:
        if not m.verified:
            (must if m.word in LOW_WORDS else should).append(f"từ vùng chỉ có nguồn K1: {m.word}")
    for p in r["added"]:
        lv = PARTICLE_INFO.get(p, "low")
        if lv is not True:
            (must if lv == "low" else should).append(f"tiểu từ chỉ có nguồn K1: {p}")
    for fl in sorted(flags):
        (must if any(k in fl for k in LOW_FLAG_KEYS) else should).append(fl)
    must, should = list(dict.fromkeys(must)), list(dict.fromkeys(should))
    reasons = must + [x for x in should if x not in must]
    review_status = "cần duyệt" if must else ("nên duyệt" if should else "không bắt buộc")
    notes = []
    if meta.get("synthetic_address"):
        notes.append("Địa chỉ tổng hợp: số nhà/ngõ/hẻm ghép ngẫu nhiên với tên đường thật.")
    if meta.get("admin_name_pre2025"):
        notes.append("Tên quận/huyện theo danh mục trước sắp xếp 2025, vẫn dùng trong khẩu ngữ.")
    if region == "Trung" and r["prof"]["residence"] != "Quê":
        notes.append(f"Người nói miền Trung sống ở {r['prof']['residence']}: từ về xe theo miền {r['prof']['vocab_source']}, giọng vẫn Trung (hồ sơ theo phụ lục, suy luận chưa kiểm chứng).")
    elif region == "Trung":
        notes.append("Trung ở quê: từ chức năng theo tiểu vùng (có nguồn); từ về xe giữ chữ của khung, chưa có nguồn tiểu vùng.")
    if state == "Trẻ em":
        notes.append("Câu của trẻ em: cần nguồn giọng trẻ thật có đồng ý, không tạo từ giọng người lớn.")
    if frame["intent"] == "dieu_hoa_noi_nong_lanh" or frame["intent"] == "tre_noi":
        notes.append("Lệnh gián tiếp (suy ra ý định).")
    if r["has_wake"]:
        notes.append("Có từ đánh thức chung 'trợ lý', không gắn thương hiệu.")
    return dict(
        language_mix=language_mix, norm_features=sorted(feats), speaker_state=state, factors_covered=sorted(fac),
        n_syllables=n_syl, length_class=lc, review_status=review_status, review_reasons=reasons,
        synthetic_address=bool(meta.get("synthetic_address")), admin_name_pre2025=bool(meta.get("admin_name_pre2025")),
        has_wake=r["has_wake"], notes=" ".join(notes), regional_words=sorted({m.word for m in regional_marks} | (set(r["added"]) & REGIONAL_PARTICLES[r["prof"]["profile"]])),
        slot_names=sorted({n for n, _ in vals}),
    )


# ------------------------------------------------------------------ sinh theo case
def has_slot(f):
    return bool(SLOT_RE.search(f["text"]))


class Shared:
    """Trạng thái dùng chung giữa các case: khóa chống trùng chuỗi và đếm lõi (core) toàn tập."""

    def __init__(self, core_cap, core_soft):
        self.seen_raw, self.seen_sp = set(), set()
        self.core_count = collections.Counter()
        self.core_cap, self.core_soft = core_cap, core_soft
        self.masks = DV.build_masks()
        self.keep = DV.build_keep()


def core_of(raw, masks):
    """Lõi đo đa dạng (carrier cũ, như v2; ghi vào trường core)."""
    return DV.carrier(raw, masks)[1]


def core_cap_of(raw, masks, keep):
    """Lõi dùng để áp trần câu/lõi (giữ tên app, bản đồ, thu phí; ghi vào trường core_cap)."""
    return DV.carrier_cap(raw, masks, keep)[1]


class CaseGen:
    """Sinh câu cho một case; giữ trạng thái để bù câu sau vòng lọc gần trùng."""

    def __init__(self, case, quota, frames, rng, shared, log):
        self.case, self.quota, self.rng, self.sh, self.log = case, quota, rng, shared, log
        self.fr = [f for f in frames if f["case"] == case]
        by_intent = collections.defaultdict(list)
        for f in self.fr:
            by_intent[f["intent"]].append(f)
        self.weights = {}
        for intent, lst in by_intent.items():
            wi = FR.INTENT_W.get(intent, 1.0)
            fw = {f["fid"]: (2.5 if has_slot(f) else 1.0) * (1.5 if f["evidence"] == "seen" else 1.0) for f in lst}
            s = sum(fw.values())
            for f in lst:
                self.weights[f["fid"]] = wi * fw[f["fid"]] / s
        self.cap_slot = max(10, math.ceil(0.03 * quota))
        self.cap_flat = 4
        self.intent_cap = math.ceil(0.3 * quota)
        self.soft = shared.core_soft          # trần lõi đang áp (nâng dần tới core_cap khi cạn)
        self.count = collections.Counter()
        self.icount = collections.Counter()
        self.fails = collections.Counter()
        self.exhausted = set()                 # (fid, vùng)
        self.targets = {r: quota // 3 for r in REGIONS}
        for k in range(quota - 3 * (quota // 3)):
            self.targets[REGIONS[(k + int(case[2:])) % 3]] += 1
        self.got = collections.Counter()
        self.relax_steps = 0
        # nhóm app G1–G8 (v3): trần cứng theo (nhóm, case), sinh trước; cạn khung thì giữ ít hơn, không nới
        self.app_target = {g: v for (g, c), v in FA.TARGET.items() if c == case}
        self.gcount = collections.Counter()
        self.app_done = set()                  # vùng đã cạn khung nhóm app

    def _app_open(self, region):
        return region not in self.app_done and any(self.gcount[g] < t for g, t in self.app_target.items())

    def _relax(self):
        """Nới trần khung/ý định (không bao giờ vượt core_cap). Trả False nếu không còn gì để nới."""
        if self.soft < self.sh.core_cap:
            self.soft += 1
        elif self.cap_flat < 12:
            self.cap_flat += 2
        elif self.cap_slot < math.ceil(0.05 * self.quota):
            self.cap_slot += 2
        elif self.intent_cap < self.quota:
            self.intent_cap += math.ceil(0.05 * self.quota)
        else:
            return False
        self.log.append(f"{self.case}: nới -> lõi {self.soft}, khung có khe {self.cap_slot}, khung không khe {self.cap_flat}, ý định {self.intent_cap}")
        self.exhausted.clear()
        self.fails.clear()
        return True

    def next(self, region, accept=None):
        """Sinh một câu mới cho vùng; accept(r) -> bool là kiểm thêm (gần trùng). Trả bộ (f, region, r, ann) hoặc None nếu cạn."""
        sh = self.sh
        tries = 0
        while True:
            app_phase = self._app_open(region)
            elig = [f for f in self.fr if (f["fid"], region) not in self.exhausted
                    and self.count[f["fid"]] < (self.cap_slot if has_slot(f) else self.cap_flat)
                    and self.icount[f["intent"]] < self.intent_cap
                    and (self.gcount[f["app_group"]] < self.app_target.get(f["app_group"], 0) if app_phase else not f["app_group"])]
            if not elig:
                if app_phase:
                    self.app_done.add(region)
                    self.log.append(f"{self.case}: vùng {region} cạn khung nhóm app ở {dict(self.gcount)}")
                    continue
                if not self._relax():
                    return None
                continue
            f = self.rng.choices(elig, weights=[self.weights[x["fid"]] for x in elig])[0]
            tries += 1
            if tries > 200000:
                return None
            try:
                r = render(f, region, self.rng)
            except Reject as e:
                self._fail(f, region)
                if "lẫn vùng" in str(e) or "chữ số" in str(e):
                    self.log.append(f"{self.case} {f['fid']} loại: {e}")
                continue
            kr, ks = asr_key(r["raw"]), asr_key(r["spoken"])
            core = core_cap_of(r["raw"], sh.masks, sh.keep)
            # khung nhóm app dùng thẳng trần cứng core_cap (tên app là thứ cần học); khung cũ dùng trần mềm như v2
            if kr in sh.seen_raw or ks in sh.seen_sp or sh.core_count[core] >= (sh.core_cap if f["app_group"] else self.soft):
                self._fail(f, region)
                continue
            if accept is not None and not accept(r):
                self._fail(f, region)
                continue
            self.fails[(f["fid"], region)] = 0
            sh.seen_raw.add(kr)
            sh.seen_sp.add(ks)
            sh.core_count[core] += 1
            self.count[f["fid"]] += 1
            self.icount[f["intent"]] += 1
            self.gcount[f["app_group"]] += 1
            self.got[region] += 1
            r["core_cap"] = core
            r["core"] = core_of(r["raw"], sh.masks)
            return (f, region, r, annotate(f, region, r, self.rng))

    def _fail(self, f, region):
        k = (f["fid"], region)
        self.fails[k] += 1
        if self.fails[k] > 25:
            self.exhausted.add(k)

    def drop(self, item):
        f, region, r, _ = item
        self.count[f["fid"]] -= 1
        self.icount[f["intent"]] -= 1
        self.gcount[f["app_group"]] -= 1
        if f["app_group"]:
            self.app_done.clear()                   # cho phép bù lại bằng khung cùng nhóm
        self.got[region] -= 1
        self.sh.core_count[r["core_cap"]] -= 1         # khóa chuỗi giữ lại trong seen để không sinh lại đúng câu đó

    def fill(self, out, accept=None):
        while len(out) < self.quota:
            region = max(REGIONS, key=lambda g: (self.targets[g] - self.got[g], self.rng.random()))
            if self.targets[region] - self.got[region] <= 0:
                break
            item = self.next(region, accept)
            if item is None:
                # vùng này cạn: thử vùng khác còn thiếu, nếu không thì dừng (giữ ít câu hơn, không nới trần lõi)
                self.targets[region] = self.got[region]
                self.log.append(f"{self.case}: vùng {region} cạn ở {self.got[region]} câu")
                if all(self.targets[g] <= self.got[g] for g in REGIONS):
                    break
                continue
            out.append(item)
        return out


# ------------------------------------------------------------------ lọc gần trùng (cùng chỉ số với diversity10k)
def tfidf_fit(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    vec = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"\S+", sublinear_tf=True)
    X = vec.fit_transform(texts).astype(np.float32)
    return vec, X


def spoken_doc(t):
    return " ".join(DV.toks(t))


def nearest(X):
    import numpy as np
    N = X.shape[0]
    best = np.zeros(N, dtype=np.float32)
    nn = np.zeros(N, dtype=np.int64)
    for s in range(0, N, 1000):
        S = (X[s:s + 1000] @ X.T).toarray()
        for k in range(S.shape[0]):
            S[k, s + k] = 0
        nn[s:s + S.shape[0]] = S.argmax(1)
        best[s:s + S.shape[0]] = S.max(1)
    return best, nn


def refine_near_dups(gens, rows_by_case, thr, thr_same, log, rounds=6):
    """Bỏ một câu trong mỗi cặp cos >= thr (hoặc cùng khung >= thr_same), bù câu mới có cos < thr với mọi câu đang giữ."""
    hist = []
    for rd in range(rounds):
        flat = [(c, i) for c in sorted(rows_by_case) for i in range(len(rows_by_case[c]))]
        items = [rows_by_case[c][i] for c, i in flat]
        vec, X = tfidf_fit([spoken_doc(it[2]["spoken"]) for it in items])
        best, nn = nearest(X)
        n09 = int((best >= thr).sum())
        same95 = sum(1 for k in range(len(items)) if best[k] >= thr_same and items[k][0]["fid"] == items[nn[k]][0]["fid"])
        hist.append(dict(vong=rd, cau_co_hang_xom_tu_nguong=n09, cung_khung_tu_nguong_cao=same95))
        log.append(f"lọc gần trùng vòng {rd}: {n09} câu có hàng xóm cos>={thr}, {same95} cặp cùng khung cos>={thr_same}")
        if n09 == 0:
            break
        # chọn câu bỏ: đi theo cos giảm dần, mỗi cặp bỏ câu sau
        order = sorted(range(len(items)), key=lambda k: -best[k])
        drop = set()
        for k in order:
            if best[k] < thr:
                break
            j = int(nn[k])
            if k in drop or j in drop:
                continue
            drop.add(max(k, j))
        keep_idx = [k for k in range(len(items)) if k not in drop]
        Xk = X[keep_idx]
        new_vecs = []

        def accept(r, _vec=vec):
            v = _vec.transform([spoken_doc(r["spoken"])])
            if (Xk @ v.T).max() >= thr:
                return False
            for w in new_vecs:
                if (w @ v.T).toarray()[0, 0] >= thr:
                    return False
            new_vecs.append(v)
            return True

        by_case_drop = collections.defaultdict(list)
        for k in drop:
            c, i = flat[k]
            by_case_drop[c].append(i)
        for c, idxs in by_case_drop.items():
            g = gens[c]
            for i in idxs:
                g.drop(rows_by_case[c][i])
            kept = [it for i, it in enumerate(rows_by_case[c]) if i not in set(idxs)]
            rows_by_case[c] = g.fill(kept, accept)
    return hist


PLATFORMS = ("oem_vinfast", "android_head_unit", "phone_projection", "any")


def platform_of(f, r):
    """platform (v3, C5): theo khung; khung G7 theo app nhắn tin (Messenger, Telegram: phone_projection theo nguồn Android Auto;
    Zalo, Viber chưa kiểm: any). Khung cũ: any."""
    p = f.get("platform", "any")
    if p == FA.BY_MSG:
        app = next((sv.raw for name, sv in r["vals"] if name == "msg_app"), None)
        return "phone_projection" if app in FA.PROJECTION_MSG else "any"
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "m1m2_10k_v3"))
    ap.add_argument("--core-cap", type=int, default=3, help="số câu tối đa cho một lõi trên toàn tập (trần cứng, không nới)")
    ap.add_argument("--core-soft", type=int, default=2, help="trần lõi áp trước; nâng dần tới --core-cap khi case cạn khung")
    ap.add_argument("--near", type=float, default=0.9, help="ngưỡng cos gần trùng cần lọc")
    ap.add_argument("--near-same", type=float, default=0.95, help="ngưỡng cos cùng khung (không được có)")
    ap.add_argument("--no-refine", action="store_true", help="bỏ vòng lọc gần trùng")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    t0 = time.time()
    quota, quota_src = read_quota()
    frames = FR.load_frames()
    # kiểm khe chưa định nghĩa
    missing = sorted({m.group(1) for f in frames for m in SLOT_RE.finditer(f["text"]) if m.group(1) not in SLOTS})
    if missing:
        raise SystemExit(f"Khe chưa định nghĩa: {missing}")
    shared = Shared(a.core_cap, a.core_soft)
    log = []
    rows_by_case, gens = {}, {}
    for case in sorted(quota):
        g = CaseGen(case, quota[case], frames, rng, shared, log)
        gens[case] = g
        rows_by_case[case] = g.fill([])
        print(f"{case}: {len(rows_by_case[case])}/{quota[case]} câu", flush=True)
    refine_hist = [] if a.no_refine else refine_near_dups(gens, rows_by_case, a.near, a.near_same, log)
    stats = {}
    for case, g in gens.items():
        cnt = collections.Counter(it[0]["fid"] for it in rows_by_case[case])
        icnt = collections.Counter(it[0]["intent"] for it in rows_by_case[case])
        cores = {it[2]["core"] for it in rows_by_case[case]}
        n = len(rows_by_case[case])
        stats[case] = dict(quota=quota[case], generated=n, shortfall=quota[case] - n,
                           frames_available=sum(1 for f in frames if f["case"] == case), frames_used=len(cnt),
                           frames_new_used=sum(1 for fid in cnt if fid in FR.NEW_FIDS),
                           frames_app_used=sum(1 for fid in cnt if fid in FR.APP_FIDS),
                           app_groups={gr: dict(target=t, generated=g.gcount[gr]) for gr, t in sorted(g.app_target.items())},
                           cores_cap=len({it[2]["core_cap"] for it in rows_by_case[case]}),
                           max_per_frame=max(cnt.values()), max_frame_share=round(max(cnt.values()) / quota[case], 4),
                           max_intent_share=round(max(icnt.values()) / quota[case], 4), cores=len(cores), core_ratio=round(len(cores) / n, 3),
                           caps=dict(core_soft_end=g.soft, cap_slot=g.cap_slot, cap_flat=g.cap_flat, intent_cap=g.intent_cap))
        print(f"{case}: {n}/{quota[case]} câu, {len(cnt)} khung, lõi {len(cores)} ({len(cores) / n:.3f}), tối đa {max(cnt.values())}/khung", flush=True)

    os.makedirs(a.out, exist_ok=True)
    manifest_files = []
    counters = collections.defaultdict(collections.Counter)
    for fname, title, cases in GROUPS:
        path = os.path.join(a.out, fname)
        n_in = 0
        per = collections.defaultdict(int)
        with open(path, "w", encoding="utf-8", newline="\n") as fo:
            for case in cases:
                for f, region, r, ann in rows_by_case[case]:
                    per[(case, f["purpose"])] += 1
                    sid = f"{case}-{f['purpose']}-{per[(case, f['purpose'])]:05d}"
                    row = dict(
                        sample_id=sid, purpose=f["purpose"], case_id=case, intent=f["intent_label"], intent_id=f["intent"],
                        speech_act=f["act"], text_raw=r["raw"], text_spoken=r["spoken"], language_mix=ann["language_mix"],
                        norm_features=ann["norm_features"], lexicon_variant=r["prof"]["vocab_source"], speaker_region=region,
                        sub_region=r["prof"]["sub_region"], residence=r["prof"]["residence"], vocab_source=r["prof"]["vocab_source"],
                        speaker_state=ann["speaker_state"], factors_covered=ann["factors_covered"], n_syllables=ann["n_syllables"],
                        length_class=ann["length_class"], review_status=ann["review_status"], review_reasons=ann["review_reasons"],
                        regional_words=ann["regional_words"], synthetic_address=ann["synthetic_address"],
                        admin_name_pre2025=ann["admin_name_pre2025"], has_wake=ann["has_wake"], frame_id=f["fid"], frame=f["text"],
                        frame_source=f["src"], evidence=f["evidence"], source_ids=f["source_ids"], slots=ann["slot_names"],
                        core=r["core"], core_cap=r["core_cap"], app_group=f["app_group"], platform=platform_of(f, r),
                        pron_variant=r["pron_variant"], notes=ann["notes"])
                    fo.write(json.dumps(row, ensure_ascii=False) + "\n")
                    n_in += 1
                    for k in ("purpose", "case_id", "lexicon_variant", "speaker_region", "speech_act", "review_status", "length_class",
                              "language_mix", "speaker_state", "evidence", "residence", "sub_region"):
                        counters[k][row[k]] += 1
                    for x in row["factors_covered"]:
                        counters["factors"][x] += 1
                    counters["synthetic_address"][str(row["synthetic_address"])] += 1
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        manifest_files.append(dict(file=fname, title=title, cases=cases, n=n_in, sha256=h))
    manifest = dict(
        dataset="Lệnh giọng nói trong xe tiếng Việt, M1 + M2 (văn bản để sinh TTS)", generator=VERSION, seed=a.seed,
        created=time.strftime("%Y-%m-%d"), total=sum(x["n"] for x in manifest_files), files=manifest_files,
        quota=quota, quota_source=quota_src, case_names=CASE_NAMES,
        rules=dict(
            number_reading="linh (Bắc) / lẻ (Trung, Nam); nghìn (Bắc) / ngàn (Trung, Nam) — theo sources/src_lang.json (L5, L14), người dùng chọn thay cho bảng CLAUDE.md",
            region_balance="mỗi case chia đều giọng Bắc/Trung/Nam theo speaker_region (lệch tối đa 1 câu)",
            trung_profile=("giọng Trung: 40% sống ở quê (sub_region Huế / Nghệ Tĩnh / Quảng Nam – Đà Nẵng, từ chức năng theo bảng có nguồn "
                           "của review/PHU_LUC_tu_vung_mien_Trung.md; từ về xe giữ chữ của khung), 30% sống ở Hà Nội (từ theo Bắc), "
                           "30% sống ở TP.HCM (từ về xe theo Nam, từ chức năng toàn dân + nha/tui). lexicon_variant = vocab_source. "
                           "Tỷ lệ là đề xuất của phụ lục, chưa có dữ liệu kiểm chứng."),
            dedup="không trùng text_raw và không trùng text_spoken sau khi bỏ dấu câu, chữ thường, trên toàn bộ tập",
            core_cap=(f"mỗi lõi theo diversity10k.carrier_cap (như carrier: che số, tên riêng, giá trị khe, bỏ tiền tố, tiểu từ; nhưng giữ "
                      f"tên app, bản đồ, thu phí, nguồn kết nối) tối đa {a.core_cap} câu trên toàn tập; khung cũ áp trần {a.core_soft} trước, "
                      f"nâng dần khi case cạn khung; khung nhóm app áp thẳng {a.core_cap}; không nới quá {a.core_cap}, thiếu thì giữ ít câu hơn. "
                      f"Trường core = lõi theo carrier cũ (để so với v2), core_cap = lõi dùng cho trần"),
            app_groups=("khung G1–G8 (frames_app10k.py, frame_source 'K1 app', mọi câu 'cần duyệt'); trần cứng theo (nhóm, case) "
                        f"{ {f'{g}/{c}': v for (g, c), v in sorted(FA.TARGET.items())} }; sinh trước khung cũ; cạn khung thì giữ ít hơn"),
            loanwords=(f"bảng {os.path.relpath(LW.CSV_PATH, ROOT)} (sha256 {LW.CSV_SHA[:16]}…): chỉ dùng cách đọc ở cột vùng của người nói; "
                       "cột rỗng thì giữ cách đọc hiện tại và gắn cờ: 'cách đọc chưa xác minh: <tên>' (cần duyệt) cho tên giữ chữ Latin, "
                       "'cách đọc từ ngoại đã đổi chữ, chưa duyệt theo vùng: <tên>' (nên duyệt) cho viết tắt đã đổi chữ và từ vay Việt hóa; "
                       "pron_variant = mã dòng-số cách đọc khi đã thay"),
            platform=("oem_vinfast / android_head_unit / phone_projection / any. G1, G3–G6: android_head_unit; G7: phone_projection với "
                      "Messenger, Telegram, any với Zalo, Viber (chưa kiểm Android Auto); G2, G8 và khung cũ: any. Chưa có câu oem_vinfast."),
            near_dup=(f"TF-IDF từ + cặp từ trên text_spoken (như diversity10k): bỏ một câu trong mỗi cặp cos >= {a.near}, "
                      f"bù câu mới có cos < {a.near} với mọi câu đang giữ; lặp tối đa 6 vòng"),
            frame_cap="khung có khe ≤ max(10, 3% hạn ngạch case); khung không khe ≤ 4 (nới khi cạn); ý định ≤ 30% case",
            review=("'cần duyệt' khi: câu miền Trung; từ/tiểu từ mức thấp (K1 low hoặc bộ sinh suy ra); cách đọc viết tắt, nghệ danh, "
                    "dấu xẹt, mồng/mùng miền Trung chưa xác minh. 'nên duyệt' khi: từ vùng/tiểu từ chỉ có nguồn K1 mức trung bình, "
                    "tên gọi quen địa phương, kiệt, chữ cái trong số nhà, gọi theo thứ tự sinh. Còn lại 'không bắt buộc'."),
        ),
        per_case=stats, near_dup_rounds=refine_hist, counts={k: dict(v) for k, v in counters.items()}, generation_log=log[:300],
        elapsed_sec=round(time.time() - t0, 1),
    )
    with open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8") as fo:
        json.dump(manifest, fo, ensure_ascii=False, indent=1)
    print("Tổng:", manifest["total"], "câu; ghi vào", a.out, f"({manifest['elapsed_sec']} giây)")


if __name__ == "__main__":
    main()
