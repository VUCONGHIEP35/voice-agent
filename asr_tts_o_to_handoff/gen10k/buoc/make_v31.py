# -*- coding: utf-8 -*-
"""v3.1 = v3 bỏ từ đệm / tiếng gọi / từ đánh thức (người dùng chốt 25/10/2026). Không sinh lại: chỉ sửa câu bị ảnh hưởng.

Chạy (từ gen10k/):
  py -3.13 -m buoc.make_v31 [--src ../data/m1m2_10k_v3] [--out ../data/m1m2_10k_v31] [--refill-pool <thư mục> ...]
Bỏ ở ĐẦU câu (text_raw và text_spoken, phải khớp cả hai): "Trợ lý ơi, " "Này trợ lý, " "Bạn ơi, " "Này, " "Ê, " "Ờ, " "Nè, "
"Nì, "; "Ờ không, …" (khung sửa lệnh) thành "Không, …"; bỏ ở CUỐI câu từ đánh thức của khe {wake} ("… đi trợ lý ơi."). Không đụng câu "Trả lời ngắn" ("Ừ.", "Ừ, làm đi.").
Lý do: 0/127 lệnh 'seen' có từ đệm đầu câu; từ đánh thức sẽ được thêm bằng cách GHÉP âm thanh (tts_gen/make_wake_aug.py),
không nằm trong văn bản.
Tính lại theo luật build10k.annotate: n_syllables, length_class, has_wake, factors_covered (E06, E08, S23, S34; S52 chỉ bỏ
khi tiếng vừa xóa là tiểu từ vùng và câu không còn tiểu từ vùng nào), regional_words (bỏ từ không còn trong câu),
review_reasons/review_status (bỏ lý do về tiểu từ đã xóa, xếp lại cần/nên duyệt), notes (bỏ ghi chú từ đánh thức),
core/core_cap (diversity10k.carrier / carrier_cap với build_masks/build_keep, như validate10k).
Câu sửa xong mà trùng (asr_key của text_raw hoặc text_spoken) hoặc gần trùng (cos TF-IDF >= --near) câu khác thì bỏ. --refill-pool: bù bằng câu từ bộ sinh
chạy seed khác (build10k.py --seed S --out <thư mục>): cùng case, purpose, speech_act, speaker_region (ưu tiên cùng
frame_source, frame_id; bắt buộc cùng app_group), không có từ đánh thức/tiền tố bị bỏ, không trùng, không vượt trần 3 câu/core_cap, cos TF-IDF
< --near với toàn bộ; sample_id mới nối tiếp số lớn nhất của (case, purpose). Log: <out>/v31_thay_doi.json.
Không ghi đè thư mục ra đã có.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import shutil
import time

from buoc import build10k as B  # noqa: E402
from thuvien import diversity10k as DV  # noqa: E402
from cauhinh.duong_dan import ROOT  # noqa: E402
from nguyen_lieu.lexicon10k import LOW_WORDS, PARTICLE_INFO, REGIONAL_PARTICLES  # noqa: E402

PREFIX_RE = re.compile(r"^(trợ lý ơi|này trợ lý|bạn ơi|này|ê|ờ|nè|nì)\s*,\s*", re.I)
CORRECTION_RE = re.compile(r"^ờ\s+(?=không\s*,)", re.I)
SUFFIX_WAKE_RE = re.compile(r"\s+trợ lý( ơi)?(?=[.?!]$)", re.I)
CONTACT_SLOTS = {"ct", "ten_lien_he", "ct2"}
E06_WORDS = {"ạ", "dạ", "vâng", "nhé", "nha", "nghen", "nghe", "giùm", "dùm", "hộ", "tui", "mình", "con"}
WAKE_NOTE = "Có từ đánh thức chung 'trợ lý', không gắn thương hiệu."
# Tiểu từ Huế "hí", "nở", "hớ" (người dùng 25/10/2026: thay). Thay bằng tiểu từ có nguồn trong Đặng Diễm Đông 2024:
# câu lệnh / câu cụt / kêu cứu -> "nghe" (tr. 103 "…ghé mua cho o nghe!") 60% hoặc bỏ 40%;
# câu hỏi -> "rứa" (Bảng 2: rứa/ri = thế, 50 lần) 50% hoặc bỏ 50%. Chọn theo băm sample_id (ổn định khi chạy lại).
# Không dùng "giùm" dù bài có (tr. 99): validate10k/lexicon10k đang cấm "giùm" ở hồ sơ Trung ở quê.
HUE_RE = re.compile(r"\s*(?<![\wÀ-ỹ])(hí|nở|hớ)(?![\wÀ-ỹ])(?=\s*[,.?!])", re.I)


HUE_NEW_REGIONAL = {"nghe", "rứa"}


def hue_choice(sample_id, act):
    x = int(hashlib.md5(("hue|" + sample_id).encode()).hexdigest(), 16) % 100
    if act == "Câu hỏi":
        return " rứa" if x < 50 else ""
    return " nghe" if x < 60 else ""


def replace_hue(t, sample_id, act):
    """(câu mới, 'cũ->mới') hoặc (t, None). Thay mọi "hí/nở/hớ" trước dấu câu, cùng một lựa chọn cho cả câu."""
    if not HUE_RE.search(t):
        return t, None
    new = hue_choice(sample_id, act)
    olds = [m.group(1).lower() for m in HUE_RE.finditer(t)]
    t2 = HUE_RE.sub(new, t)
    return t2, "+".join(olds) + "->" + (new.strip() or "bỏ")


def words(t):
    return set(re.findall(r"[\wÀ-ỹ]+", t.lower()))


def strip_text(t):
    """(câu mới, phần đã bỏ) hoặc (t, None)."""
    m = CORRECTION_RE.match(t)                 # khung sửa lệnh "~ờ không, {cau_dung}": giữ "Không, …"
    if m:
        rest = t[m.end():]
        return rest[:1].upper() + rest[1:], "ờ (sửa lệnh)"
    m = PREFIX_RE.match(t)
    if m:
        rest = t[m.end():]
        return rest[:1].upper() + rest[1:], m.group(1).lower()
    m = SUFFIX_WAKE_RE.search(t)
    if m:
        return t[:m.start()] + t[m.end():], "cuối:" + m.group(0).strip().lower()
    return t, None


def must_reason(reason):
    """Lý do 'cần duyệt' theo luật build10k.annotate (phần còn lại là 'nên duyệt')."""
    if reason.startswith(("khung do LLM", "khung chức năng xe", "khung app", "giọng miền Trung")):
        return True
    m = re.match(r"từ vùng chỉ có nguồn K1: (.+)$", reason)
    if m:
        return m.group(1) in LOW_WORDS
    m = re.match(r"tiểu từ chỉ có nguồn K1: (.+)$", reason)
    if m:
        return PARTICLE_INFO.get(m.group(1), "low") == "low"
    return any(k in reason for k in B.LOW_FLAG_KEYS)


def profile_of(r):
    if r["speaker_region"] != "Trung":
        return r["speaker_region"]
    if r.get("residence") == "Hà Nội":
        return "Trung-HN"
    if r.get("residence") == "TP.HCM":
        return "Trung-HCM"
    return B.SUB_PROFILE.get(r.get("sub_region"), "Trung-Quảng")


def fix_row(r, removed, hue=None):
    raw, sp = r["text_raw"], r["text_spoken"]
    out = dict(r)
    n = B.syllables(sp)
    out["n_syllables"], out["length_class"], out["has_wake"] = n, B.length_class(n), False
    lw = words(raw)
    fac = set(r["factors_covered"])
    if (lw & E06_WORDS) or "bạn ơi" in raw.lower() or "trợ lý" in raw.lower() or (set(r["slots"]) & CONTACT_SLOTS):
        fac.add("E06")
    else:
        fac.discard("E06")
    fac.add("E08") if (n <= 3 or n >= 16) else fac.discard("E08")
    s23 = (r["speech_act"] in ("Câu cụt", "Kêu cứu") or r["intent_id"] == "sua_lenh"
           or re.search(r"(^|, )(ờ|à|ừm),", raw.lower()) or r["speaker_state"] in ("Vội / nói nhanh", "Căng thẳng / khẩn"))
    fac.add("S23") if s23 else fac.discard("S23")
    fac.add("S34") if "," in raw.rstrip(".?!") else fac.discard("S34")
    regional = [w for w in r["regional_words"] if (w in lw if " " not in w else w in raw.lower())]
    reg_particles = REGIONAL_PARTICLES.get(profile_of(r), set())
    gone = {removed} if removed else set()
    if hue:
        olds, new = hue.split("->")
        gone |= set(olds.split("+"))
        if new in HUE_NEW_REGIONAL and new not in regional:
            regional.append(new)
    out["regional_words"] = sorted(regional)
    if gone & (reg_particles | {"hí", "nở", "hớ"}) and not (set(regional) & (reg_particles | HUE_NEW_REGIONAL)):
        fac.discard("S52")
    out["factors_covered"] = sorted(fac)
    reasons = []
    for x in r["review_reasons"]:
        m = re.match(r"tiểu từ chỉ có nguồn K1: (.+)$", x)
        if m and m.group(1) not in lw:
            continue
        reasons.append(x)
    must = [x for x in reasons if must_reason(x)]
    out["review_reasons"] = must + [x for x in reasons if x not in must]
    out["review_status"] = "cần duyệt" if must else ("nên duyệt" if reasons else "không bắt buộc")
    out["notes"] = " ".join(r["notes"].replace(WAKE_NOTE, "").split())
    if removed:
        out["v31_bo"] = removed
    if hue:
        out["v31_tieu_tu_hue"] = hue
    return out


def recompute_core(r, masks, keep):
    r["core"] = DV.carrier(r["text_raw"], masks)[1]
    r["core_cap"] = DV.carrier_cap(r["text_raw"], masks, keep)[1]


def keys_of(r):
    return B.asr_key(r["text_raw"]), B.asr_key(r["text_spoken"])


def clean_candidate(r):
    """Câu từ bộ bù: không có từ đánh thức, không có tiền tố/hậu tố thuộc loại bị bỏ."""
    return not r["has_wake"] and strip_text(r["text_raw"])[1] is None and strip_text(r["text_spoken"])[1] is None


def prep_candidate(r, masks, keep):
    """Câu bù có tiểu từ Huế cũ: đổi theo cùng luật như câu v3 (replace_hue) thay vì loại, để giữ đủ câu Huế."""
    raw2, h1 = replace_hue(r["text_raw"], r["sample_id"], r["speech_act"])
    sp2, h2 = replace_hue(r["text_spoken"], r["sample_id"], r["speech_act"])
    if h1 is None and h2 is None:
        return r
    if h1 != h2:
        return None
    r2 = fix_row(dict(r, text_raw=raw2, text_spoken=sp2), None, h1)
    recompute_core(r2, masks, keep)
    return r2


def refill(out_rows, dropped, pool_dirs, masks, keep, near_thr, log):
    import scipy.sparse as sp
    all_rows = [r for rs in out_rows.values() for r in rs]
    raw_keys = {keys_of(r)[0] for r in all_rows}
    sp_keys = {keys_of(r)[1] for r in all_rows}
    cap = collections.Counter(r["core_cap"] for r in all_rows)
    case_cores = {(r["case_id"], r["core"]) for r in all_rows}
    used_ids = {r["sample_id"] for r in all_rows} | {d["sample_id"] for d in dropped}
    nxt = collections.Counter()
    for sid in used_ids:
        pre, num = sid.rsplit("-", 1)
        nxt[pre] = max(nxt[pre], int(num))
    pool = []
    for d in pool_dirs:
        for f in sorted(glob.glob(os.path.join(d, "0*.jsonl"))):
            pool += [dict(json.loads(l), _file=os.path.basename(f), _pool=os.path.basename(os.path.normpath(d)))
                     for l in open(f, encoding="utf-8")]
    pool = [p for p in (prep_candidate(r, masks, keep) for r in pool if clean_candidate(r)) if p is not None]
    vec, X = B.tfidf_fit([B.spoken_doc(r["text_spoken"]) for r in all_rows])
    file_of = {os.path.basename(f): f for f in out_rows}
    # trần khung: mỗi khung <= 5% số câu của case (validate10k)
    case_n = collections.Counter(r["case_id"] for r in all_rows) + collections.Counter(d["case_id"] for d in dropped)
    frame_n = collections.Counter((r["case_id"], r["frame_id"]) for r in all_rows)
    taken, missing = [], []
    # Lượt 1 bắt buộc cùng speech_act và (giọng Trung) cùng sub_region + residence; lượt 2 (câu cụt/hỏi ngắn đã cạn khung)
    # cho phép khác các trường đó, vẫn cùng case, purpose, vùng, app_group.
    todo = [(d, True) for d in dropped]
    for d, strict in todo:
        cands = [c for c in pool if c["case_id"] == d["case_id"] and c["purpose"] == d["purpose"]
                 and (not strict or (c["speech_act"] == d["speech_act"]
                                     and (c.get("sub_region"), c.get("residence")) == (d.get("sub_region"), d.get("residence"))))
                 and c["speaker_region"] == d["speaker_region"]
                 and (c.get("app_group") or "") == (d.get("app_group") or "")      # giữ đúng số câu từng nhóm G
                 and frame_n[(c["case_id"], c["frame_id"])] + 1 <= 0.05 * case_n[c["case_id"]]]
        cands.sort(key=lambda c: (c["speech_act"] != d["speech_act"],
                                  (c["case_id"], c["core"]) in case_cores,          # ưu tiên lõi mới trong case
                                  (c.get("sub_region"), c.get("residence")) != (d.get("sub_region"), d.get("residence")),
                                  c["frame_source"] != d["frame_source"], c["frame_id"] != d["frame_id"]))
        chosen = None
        for c in cands:
            kr, ks = keys_of(c)
            if kr in raw_keys or ks in sp_keys or cap[c["core_cap"]] >= 3:
                continue
            if (vec.transform([B.spoken_doc(c["text_spoken"])]) @ X.T).max() >= near_thr:
                continue
            chosen = c
            break
        if chosen is None:
            if strict:
                todo.append((d, False))
            else:
                missing.append(d["sample_id"])
            continue
        pool.remove(chosen)
        kr, ks = keys_of(chosen)
        raw_keys.add(kr)
        sp_keys.add(ks)
        cap[chosen["core_cap"]] += 1
        case_cores.add((chosen["case_id"], chosen["core"]))
        frame_n[(chosen["case_id"], chosen["frame_id"])] += 1
        pre = d["sample_id"].rsplit("-", 1)[0]
        nxt[pre] += 1
        new = {k: v for k, v in chosen.items() if not k.startswith("_")}
        new["sample_id"] = f"{pre}-{nxt[pre]:05d}"
        assert new["sample_id"] not in used_ids
        used_ids.add(new["sample_id"])
        new["v31_bo"] = (f"bù cho {d['sample_id']} (bộ sinh {chosen['_pool']}"
                         + ("" if chosen["speech_act"] == d["speech_act"] else f"; khác loại câu: {d['speech_act']}") + ")")
        recompute_core(new, masks, keep)
        out_rows[file_of[chosen["_file"]]].append(new)
        X = sp.vstack([X, vec.transform([B.spoken_doc(new["text_spoken"])])]).tocsr()
        taken.append(new)
        log.append(dict(sample_id=new["sample_id"], bu_cho=d["sample_id"], cau=new["text_raw"]))
    return taken, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(ROOT, "data", "m1m2_10k_v3"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "m1m2_10k_v31"))
    ap.add_argument("--refill-pool", nargs="*", default=[])
    ap.add_argument("--near", type=float, default=0.9)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} đã có, không ghi đè")
    masks, keep = DV.build_masks(), DV.build_keep()
    files = sorted(glob.glob(os.path.join(a.src, "0*.jsonl")))
    rows = {f: [json.loads(l) for l in open(f, encoding="utf-8")] for f in files}
    raw_keys = collections.Counter(keys_of(r)[0] for rs in rows.values() for r in rs)
    sp_keys = collections.Counter(keys_of(r)[1] for rs in rows.values() for r in rs)
    log, stat, out_rows, dropped = [], collections.Counter(), {}, []
    for f, rs in rows.items():
        keep_rows = []
        for r in rs:
            if r["speech_act"] == "Trả lời ngắn":
                keep_rows.append(r)
                continue
            raw2, k1 = strip_text(r["text_raw"])
            sp2, k2 = strip_text(r["text_spoken"])
            if k1 != k2:
                raise SystemExit(f"{r['sample_id']}: text_raw và text_spoken không cùng tiền tố ({k1!r} / {k2!r})")
            raw2, h1 = replace_hue(raw2, r["sample_id"], r["speech_act"])
            sp2, h2 = replace_hue(sp2, r["sample_id"], r["speech_act"])
            if h1 != h2:
                raise SystemExit(f"{r['sample_id']}: tiểu từ Huế khác nhau giữa text_raw và text_spoken ({h1!r} / {h2!r})")
            if k1 is None and h1 is None:
                keep_rows.append(r)
                continue
            ok, osk = keys_of(r)
            nk, nsk = B.asr_key(raw2), B.asr_key(sp2)
            raw_keys[ok] -= 1
            sp_keys[osk] -= 1
            if raw_keys[nk] > 0 or sp_keys[nsk] > 0:
                stat["bo_vi_trung"] += 1
                dropped.append(r)
                log.append(dict(sample_id=r["sample_id"], ly_do="trùng sau khi bỏ", truoc=r["text_raw"], sau=raw2))
                continue
            raw_keys[nk] += 1
            sp_keys[nsk] += 1
            r2 = fix_row(dict(r, text_raw=raw2, text_spoken=sp2), k1, h1)
            recompute_core(r2, masks, keep)
            if k1:
                stat[k1] += 1
            if h1:
                stat["hue:" + h1] += 1
            for fld in ("review_status", "length_class", "core", "core_cap"):
                if r2[fld] != r[fld]:
                    stat[f"doi_{fld}"] += 1
            log.append(dict(sample_id=r["sample_id"], bo=k1 or "", tieu_tu_hue=h1 or "", truoc=r["text_raw"], sau=raw2))
            keep_rows.append(r2)
        out_rows[f] = keep_rows
    # Câu đã sửa mà gần trùng (cos TF-IDF >= --near, như vòng lọc của build10k) với câu khác: bỏ và bù như câu trùng.
    # Nguyên nhân: tiền tố vừa xóa từng là chỗ khác nhau duy nhất ("…bao nhiêu ạ?" / "Ờ, …bao nhiêu?").
    orig = {r["sample_id"]: r for rs in rows.values() for r in rs}
    modified = {x["sample_id"] for x in log if "bo" in x}
    # Câu đổi tiểu từ Huế mà trùng LÕI (carrier) với câu khác cùng case: bỏ và bù. Carrier không lược "hí/nở/hớ" nên
    # "X hí" và "X" từng là hai lõi; sau khi đổi chúng dồn một lõi -> tỷ lệ lõi/câu tụt (validate10k so với v2).
    # Câu sửa nào làm một core_cap vượt trần 3 cũng bỏ và bù.
    flat = [r for rs in out_rows.values() for r in rs]
    case_core = collections.Counter((r["case_id"], r["core"]) for r in flat)
    capc = collections.Counter(r["core_cap"] for r in flat)
    bad = set()
    for r in flat:
        if r["sample_id"] not in modified:
            continue
        if (r.get("v31_tieu_tu_hue") and case_core[(r["case_id"], r["core"])] > 1) or capc[r["core_cap"]] > 3:
            bad.add(r["sample_id"])
            case_core[(r["case_id"], r["core"])] -= 1
            capc[r["core_cap"]] -= 1
    for f in out_rows:
        out_rows[f] = [r for r in out_rows[f] if r["sample_id"] not in bad]
    for sid in sorted(bad):
        dropped.append(orig[sid])
        modified.discard(sid)
        stat["bo_vi_trung_loi"] += 1
        log.append(dict(sample_id=sid, ly_do="trùng lõi sau khi đổi", truoc=orig[sid]["text_raw"]))
    while True:
        flat = [r for rs in out_rows.values() for r in rs]
        _, X = B.tfidf_fit([B.spoken_doc(r["text_spoken"]) for r in flat])
        best, nn = B.nearest(X)
        bad = set()
        for i in sorted(range(len(flat)), key=lambda i: -best[i]):
            if best[i] < a.near:
                break
            pair = (flat[i], flat[int(nn[i])])
            if any(p["sample_id"] in bad for p in pair):
                continue
            mod = [p for p in pair if p["sample_id"] in modified]
            if mod:
                bad.add(mod[0]["sample_id"])
        if not bad:
            break
        for f in out_rows:
            out_rows[f] = [r for r in out_rows[f] if r["sample_id"] not in bad]
        for sid in sorted(bad):
            dropped.append(orig[sid])
            modified.discard(sid)
            stat["bo_vi_gan_trung"] += 1
            log.append(dict(sample_id=sid, ly_do=f"gần trùng (cos >= {a.near}) sau khi bỏ", truoc=orig[sid]["text_raw"]))
    taken, missing = refill(out_rows, dropped, a.refill_pool, masks, keep, a.near, log) if a.refill_pool else ([], [])
    stat["bu"], stat["khong_bu_duoc"] = len(taken), len(missing)
    os.makedirs(a.out)
    man = json.load(open(os.path.join(a.src, "manifest.json"), encoding="utf-8"))
    total = 0
    for f, rs in out_rows.items():
        p = os.path.join(a.out, os.path.basename(f))
        with open(p, "w", encoding="utf-8", newline="\n") as fo:
            for r in rs:
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
        total += len(rs)
        for e in man["files"]:
            if e["file"] == os.path.basename(f):
                e["n"] = len(rs)
                e["sha256"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    man.update(generator="gen10k-3.1 (make_v31.py từ gen10k-3.0, không sinh lại)", created=time.strftime("%Y-%m-%d"),
               total=total, v31=dict(nguon=os.path.basename(os.path.normpath(a.src)), thong_ke=dict(stat),
                                     khong_bu_duoc=missing, bo_bu=[os.path.basename(os.path.normpath(d)) for d in a.refill_pool],
                                     ly_do="Người dùng 25/10/2026: bỏ hẳn từ đệm và từ đánh thức trong văn bản; "
                                           "từ đánh thức thêm bằng ghép âm thanh."))
    json.dump(man, open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(log, open(os.path.join(a.out, "v31_thay_doi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if os.path.exists(os.path.join(a.src, "README_nguon.md")):
        shutil.copy(os.path.join(a.src, "README_nguon.md"), os.path.join(a.out, "README_nguon.md"))
    print(f"v3.1: {total} câu -> {a.out}")
    print("Thống kê:", dict(stat))
    if missing:
        print("Không bù được:", missing[:20])


if __name__ == "__main__":
    main()
