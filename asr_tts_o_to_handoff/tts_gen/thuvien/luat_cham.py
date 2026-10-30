# -*- coding: utf-8 -*-
"""Luật chấm gộp nhiều cấu hình ASR (v1 và v2). Xem buoc/cham.py để biết thứ tự xét và ý nghĩa từng luật."""
import csv
import json
import os

from cauhinh.nguong import Z_ALONE_MAX
from thuvien.can_hang import align
from thuvien.cham_chu import equiv, norm


CONFIGS = ("L", "M", "c1", "c2", "c3", "Z")
FILES = {"L": "asr_PhoWhisper-large-ct2-int8.jsonl", "M": "asr_PhoWhisper-medium.jsonl",
         "Z": "asr_Zipformer-30M-int8-beam4.jsonl", "T": "asr_PhoWhisper-small.jsonl"}
MEASURE_ONLY = ("T",)    # nạp và ghi CER, nhưng không nằm trong CONFIGS nên không ảnh hưởng kết quả chấm
VERDICTS = ("dat", "dat_1nguon", "can_nghe", "loai", "sinh_lai")
FILLERS = {"ờ", "ừm", "ơ", "ê", "nè", "nì"}
END_PARTICLES = {"nhé", "nha", "nghe", "nghen", "hen", "ạ", "à", "hả", "nhỉ", "thế", "vậy", "rứa", "hè", "ta", "đi", "với",
                 "luôn", "giùm", "dùm", "ngay", "hí", "nở", "hớ", "nờ", "tề", "chơ"}
SUBSETS = (("L",), ("L", "M"), ("L", "c3"), ("L", "M", "c3"), ("Z",), ("L", "Z"), ("L", "M", "Z"), ("L", "M", "c3", "Z"),
           CONFIGS)
def load_hyps(run, diag_path=None):
    """{cấu hình: {utt_id: hyp}} cho các cấu hình có tệp."""
    out = {}
    for c, fn in FILES.items():
        p = os.path.join(run, fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out[c] = {d["utt_id"]: d["hyp"] for d in map(json.loads, f)}
    p = diag_path or os.path.join(run, "asr_diagnose.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        for c in ("c1", "c2", "c3"):
            if rows and f"hyp_{c}" in rows[0]:
                out[c] = {r["utt_id"]: r[f"hyp_{c}"] for r in rows}
    return out
def tts_check_of(m, run):
    """tts_check trong manifest; lượt chạy cũ (thí điểm) không có thì tính lại từ âm thanh 16 kHz."""
    if "tts_check" in m:
        return m["tts_check"]
    import soundfile as sf
    import tts_checks
    w, _ = sf.read(os.path.join(run, m["audio16"]), dtype="float32")
    why, _ = tts_checks.check(w, m["n_syllables"], m.get("speech_s"))
    return "dat" if not why else "loi:" + "+".join(why)
def judge(m, cers, cers_nt, tts_check, thr, short_max=3):
    """(ket_qua, ly_do, [cấu hình đạt]). cers/cers_nt: {cấu hình: CER} chỉ cho cấu hình có hyp."""
    region = m.get("voice_region") or m["speaker_region"]
    if tts_check != "dat":
        if m.get("voice_fallback_from"):
            return "can_nghe", "tts", []
        return "sinh_lai", tts_check, []
    if m["n_syllables"] <= short_max:
        ok = [c for c in CONFIGS if c in cers and cers[c] == 0]
        return ("dat", "cau_ngan_khop", ok) if ok else ("can_nghe", "cau_ngan", [])
    ok = [c for c in CONFIGS if c in cers and cers[c] <= thr]
    if "L" in ok and "M" in ok:
        return "dat", "", ok
    if ok:
        return "dat_1nguon", "+".join(ok), ok
    if region == "Trung" and cers_nt and min(cers_nt.values()) <= thr:
        return "can_nghe", "chi_loi_thanh", []
    return "loai", "sai", []
def strip_fillers(t):
    """Chuỗi đã chuẩn hóa -> bỏ các tiếng đệm đứng riêng."""
    return " ".join(w for w in t.split() if w not in FILLERS)
def content_errors(variant, hyp):
    """Chỉ số các từ nội dung của đáp án bị mất/thay (căn hàng theo từ, đã gộp từ địa phương và bỏ từ đệm).
    Miễn: tiểu từ ở cuối câu (END_PARTICLES) và 'ơi'."""
    ref = strip_fillers(equiv(norm(variant))).split()
    hy = strip_fillers(equiv(norm(hyp))).split()
    if not ref:
        return [], []
    st = align(ref, hy)
    bad = [i for i, x in enumerate(st) if x != "ok" and not (ref[i] == "ơi" or (i == len(ref) - 1 and ref[i] in END_PARTICLES))]
    return bad, st
def config_pass_v2(cers, errs, n_syl, thr, short_max=3):
    """{cấu hình: đạt?} theo luật v2 (b, c). cers: CER đã bỏ từ đệm; errs: {cấu hình: [từ nội dung sai]}."""
    ok = {}
    for c, v in cers.items():
        ok[c] = (v == 0) if n_syl <= short_max else (v <= thr and not errs.get(c))
    if "Z" in ok and ok["Z"] and n_syl > short_max and not (ok.get("c3") or cers["Z"] <= Z_ALONE_MAX):
        ok["Z"] = False
    return ok
def judge_v2(m, ok, cers_nt, first_ok, tts_check, thr, short_max=3):
    """(ket_qua, ly_do, [cấu hình đạt]) theo luật v2. ok: {cấu hình: bool}; first_ok: {L/M/Z: từ đầu đúng?}."""
    region = m.get("voice_region") or m["speaker_region"]
    if tts_check != "dat":
        if m.get("voice_fallback_from"):
            return "can_nghe", "tts", []
        return "sinh_lai", tts_check, []
    good = [c for c in CONFIGS if ok.get(c)]
    if m["n_syllables"] <= short_max:
        return ("dat", "cau_ngan_khop", good) if good else ("can_nghe", "cau_ngan", [])
    if ok.get("L") and ok.get("M"):
        return "dat", "", good
    if good:
        fo = {first_ok[c] for c in ("L", "M", "Z") if c in first_ok}
        if len(fo) > 1:
            return "can_nghe", "tu_dau_lech", good
        return "dat_1nguon", "+".join(good), good
    if region == "Trung" and cers_nt and min(cers_nt.values()) <= thr:
        return "can_nghe", "chi_loi_thanh", []
    return "loai", "sai", []
def passes(row, c, thr, short_max=3):
    flag = row.get(f"dat_{c}")
    if flag not in (None, ""):                 # luật đã chấm sẵn trong cột dat_<c> (v1 hoặc v2)
        return flag in (True, "True", "1", 1)
    v = row.get(f"cer_{c}")
    if v is None or v == "":
        return False
    return v == 0 if row["n_syl"] <= short_max else v <= thr
def marginal(rows, avail, thr, short_max=3):
    """Đóng góp biên: số câu đạt khi dùng từng tập cấu hình, và số câu chỉ đạt nhờ đúng một cấu hình."""
    ok_rows = [r for r in rows if r["tts_check"] == "dat"]
    res = {"tap": {}, "chi_nho": {}}
    for s in SUBSETS:
        s = tuple(c for c in s if c in avail)
        if s:
            res["tap"]["+".join(s)] = sum(any(passes(r, c, thr, short_max) for c in s) for r in ok_rows)
    for c in avail:
        res["chi_nho"][c] = sum(passes(r, c, thr, short_max) and not any(passes(r, o, thr, short_max)
                                                                          for o in avail if o != c) for r in ok_rows)
    return res
def two_of_three(rows, thr, short_max=3):
    """Số câu dat nếu luật là 'ít nhất 2 trong L, M, Z đạt' (chỉ để cân nhắc; câu ngắn giữ luật CER = 0)."""
    ok_rows = [r for r in rows if r["tts_check"] == "dat"]
    return sum(sum(passes(r, c, thr, short_max) for c in ("L", "M", "Z")) >= 2 for r in ok_rows)
def mean_cer(rows, avail):
    """CER trung bình (theo đáp án biến thể) của từng cấu hình trên các câu tts_check đạt."""
    out = {}
    for c in avail:
        xs = [r[f"cer_{c}"] for r in rows if r["tts_check"] == "dat" and r[f"cer_{c}"] != ""]
        out[c] = round(sum(xs) / len(xs), 4) if xs else None
    return out
