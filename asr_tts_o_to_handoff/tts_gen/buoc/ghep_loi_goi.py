# -*- coding: utf-8 -*-
"""Ghép lời gọi trợ lý vào câu lệnh M1 đã sinh (kế hoạch chốt mục 2.1; người dùng chốt 25/10/2026).

Hai bước (từ tts_gen/, trên máy có GPU):
  python -m buoc.ghep_loi_goi dau  --tts-args "<tham số run_pilot>"     # sinh đoạn lời gọi: 24 giọng × 2 cụm × 3 bản
  python -m buoc.ghep_loi_goi ghep --ctc <thư mục wav2vec2>              # căn hàng âm tiết, ghép, ghi runs/full10k_wake/
Cụm (nhãn viết "hây" theo người dùng): "Trợ lý ơi", "Hây trợ lý".
Chọn câu gốc: câu M1 (sample_id có "-M1-") trong runs/full10k_p01..p10, kết quả chấm luật v1 là dat hoặc dat_1nguon,
tts_check đạt; lấy 12% theo băm sample_id (tất định).
Kiểu: 40% "du" (đủ cụm), 60% "duoi" (chỉ còn đuôi). Đuôi: 70% cắt ĐÚNG ranh giới âm tiết (giữ 1–2 âm tiết cuối),
30% cắt GIỮA một âm tiết (âm tiết dở bị bỏ khỏi nhãn). Nhãn theo từng âm tiết: âm tiết trọn thì ghi, dở thì bỏ.
Ranh giới âm tiết: căn hàng CTC wav2vec2 (do_toc_do_am_tiet.ctc_align, char_tokens), khung 20 ms.
Ghép: chỉnh mức RMS phần có tiếng của đoạn gọi bằng câu gốc; làm mờ 10 ms ở chỗ cắt và cuối đoạn gọi; khoảng lặng 0–300 ms;
rồi câu gốc nguyên vẹn. Dòng manifest: chép dòng câu gốc, thêm parent_utt_id, wake_phrase, wake_type, wake_giu, wake_cat,
gap_s; sample_id = <gốc>#w (câu gốc và câu ghép luôn chia CÙNG tập train/dev/test).
"""
import argparse
import collections
import csv
import glob
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from thuvien.manifest import active_rows, load_manifest  # noqa: E402

PHRASES = {"tro_ly_oi": "Trợ lý ơi", "hay_tro_ly": "Hây trợ lý"}
N_COPIES = 3
SHARE = 0.12
P_FULL = 0.40
P_BOUNDARY = 0.70
SR, SR16 = 48_000, 16_000
DAU_RUN = "runs/full10k_wake_dau"
OUT_RUN = "runs/full10k_wake"


def h01(*parts):
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def slug(v):
    import unicodedata
    s = unicodedata.normalize("NFD", v).replace("đ", "d").replace("Đ", "D")
    return re.sub(r"[^A-Za-z0-9]+", "_", "".join(ch for ch in s if unicodedata.category(ch) != "Mn")).strip("_")


def dau_rows(voices):
    """Dòng đầu vào run_pilot cho đoạn lời gọi. voices: {tên: (vùng, giới, ...)}."""
    rows = []
    for v, meta in sorted(voices.items()):
        for key, phrase in PHRASES.items():
            for k in range(N_COPIES):
                rows.append(dict(sample_id=f"WAKE-{key}-{slug(v)}-{k}", case_id="WAKE", intent_id="wake", purpose="WAKE",
                                 text_raw=phrase + ".", text_spoken=phrase + ".", n_syllables=len(phrase.split()),
                                 length_class="Rất ngắn", speaker_region=meta[0], sub_region="", residence="",
                                 review_reasons=[], review_status="không bắt buộc", voice=v, wake_phrase=key))
    return rows


def compose_label(kept, parent_text, frame):
    """Nhãn ghép: các âm tiết còn trọn của cụm + câu gốc. Chữ đầu câu gốc viết thường trừ khi khung bắt đầu bằng khe
    (tên riêng, tên app…)."""
    body = parent_text
    if not (frame or "").lstrip("~").startswith("{") and body[:1].isupper() and not body.split()[0].isupper():
        body = body[:1].lower() + body[1:]
    if not kept:
        return parent_text
    pre = " ".join(kept)
    return pre[:1].upper() + pre[1:] + ", " + body


def plan_cut(n_syl, key):
    """(kiểu, chỉ số âm tiết đầu tiên được giữ, cắt giữa âm tiết nào hoặc None, phân số cắt)."""
    if h01(key, "kieu") < P_FULL:
        return "du", 0, None, 0.0
    if h01(key, "ranh_gioi") < P_BOUNDARY:
        k = 1 + int(h01(key, "giu") * (n_syl - 1))          # giữ 1..n-1 âm tiết cuối
        return "duoi", n_syl - k, None, 0.0
    j = int(h01(key, "giua") * n_syl)                        # cắt giữa âm tiết j; giữ j+1..n-1
    return "duoi", j + 1, j, 0.3 + 0.4 * h01(key, "frac")


def syllable_times(w16, text, proc, model, vocab, blank, sep, dev):
    """[(bắt đầu s, kết thúc s)] mỗi âm tiết của text trong w16 (CTC Viterbi), hoặc None."""
    import torch
    from thuvien.can_hang import FRAME_S, char_tokens, ctc_align, words_of  # noqa: E402
    ws = words_of(text)
    toks, lens = [], []
    for i, w in enumerate(ws):
        if i and sep is not None:
            toks.append(sep)
        ids = [x for ch in w for x in (char_tokens(ch, vocab) or [])]
        toks += ids
        lens.append(len(ids))
    x = proc(w16, sampling_rate=SR16, return_tensors="pt").input_values.to(dev)
    with torch.no_grad():
        logp = torch.log_softmax(model(x).logits[0].float(), -1).cpu().numpy()
    spans = ctc_align(logp, toks, blank)
    if spans is None:
        return None
    if sep is not None:
        spans = [s for t, s in zip(toks, spans) if t != sep]
    out, i = [], 0
    for n in lens:
        seg = spans[i:i + n]
        out.append((seg[0][0] * FRAME_S, (seg[-1][1] + 1) * FRAME_S))
        i += n
    return out


def speech_rms(w):
    import numpy as np
    a = np.abs(w)
    thr = max(a.max() * 0.05, 1e-4) if len(a) else 1e-4
    sel = w[a > thr]
    return float(np.sqrt(np.mean(sel ** 2))) if len(sel) else 0.0


def build_clip(wake48, times, parent48, kind, first_keep, mid_j, frac, gap_s):
    """Âm thanh ghép 48 kHz. times: âm tiết theo giây trong đoạn gọi."""
    import numpy as np
    fade = int(0.010 * SR)
    end = min(len(wake48), int((times[-1][1] + 0.08) * SR))
    if kind == "du":
        start = 0
    elif mid_j is None:
        start = max(0, int((times[first_keep][0] - 0.02) * SR))
    else:
        a, b = times[mid_j]
        start = int((a + frac * (b - a)) * SR)
    seg = np.array(wake48[start:end], dtype=np.float32)
    r_w, r_p = speech_rms(seg), speech_rms(parent48)
    if r_w > 0 and r_p > 0:
        seg *= min(r_p / r_w, 0.99 / max(np.abs(seg).max(), 1e-6))
    if kind != "du" and len(seg) > fade:
        seg[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    if len(seg) > fade:
        seg[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    gap = np.zeros(int(gap_s * SR), dtype=np.float32)
    return np.concatenate([seg, gap, np.asarray(parent48, dtype=np.float32)])


def cmd_dau(a):
    from cauhinh.giong import VOICES  # noqa: E402
    os.makedirs(os.path.join(HERE, DAU_RUN), exist_ok=True)
    inp = os.path.join(HERE, DAU_RUN, "input.jsonl")
    with open(inp, "w", encoding="utf-8", newline="\n") as f:
        for r in dau_rows(VOICES):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cmd = [sys.executable, "-m", "buoc.tts", "--input", inp, "--out", os.path.join(HERE, DAU_RUN)]
    cmd += shlex.split(a.tts_args)
    print("Chạy:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=HERE)


def cmd_ghep(a):
    import soundfile as sf
    import soxr
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    from thuvien.am_thanh import write_flac  # noqa: E402
    out = os.path.join(HERE, OUT_RUN)
    if os.path.exists(os.path.join(out, "manifest.jsonl")):
        raise SystemExit(f"{out}/manifest.jsonl đã có, không ghi đè")
    src = {json.loads(l)["sample_id"]: json.loads(l) for l in open(os.path.join(HERE, "full10k", "all_10k.jsonl"), encoding="utf-8")}
    # đoạn lời gọi đạt kiểm kỹ thuật
    dau_dir = os.path.join(HERE, DAU_RUN)
    clips = collections.defaultdict(list)
    for m in active_rows(load_manifest(dau_dir)):
        if m.get("tts_check") == "dat":
            key = m["sample_id"].split("-")[1]
            clips[(m["voice"], key)].append(m)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    proc = Wav2Vec2Processor.from_pretrained(a.ctc)
    model = Wav2Vec2ForCTC.from_pretrained(a.ctc).eval().to(dev)
    vocab = proc.tokenizer.get_vocab()
    blank, sep = proc.tokenizer.pad_token_id, vocab.get(proc.tokenizer.word_delimiter_token)
    times = {}
    for ms in clips.values():
        for m in ms:
            w16, _ = sf.read(os.path.join(dau_dir, m["audio16"]), dtype="float32")
            t = syllable_times(w16, PHRASES[m["sample_id"].split("-")[1]], proc, model, vocab, blank, sep, dev)
            if t:
                times[m["utt_id"]] = t
    os.makedirs(os.path.join(out, "audio48"), exist_ok=True)
    os.makedirs(os.path.join(out, "audio16"), exist_ok=True)
    stat = collections.Counter()
    with open(os.path.join(out, "manifest.jsonl"), "w", encoding="utf-8", newline="\n") as man:
        for run in sorted(glob.glob(os.path.join(HERE, "runs", "full10k_p[0-9][0-9]"))):
            gate = {r["utt_id"]: r for r in csv.DictReader(open(os.path.join(run, "gate_hop_v1.csv"), encoding="utf-8-sig"))}
            for m in active_rows(load_manifest(run)):
                g = gate.get(m["utt_id"])
                if ("-M1-" not in m["sample_id"] or not g or g["ket_qua"] not in ("dat", "dat_1nguon")
                        or m.get("tts_check") != "dat" or h01(m["sample_id"], "chon") >= SHARE):
                    continue
                key = "tro_ly_oi" if h01(m["sample_id"], "cum") < 0.5 else "hay_tro_ly"
                cands = [c for c in clips.get((m["voice"], key), []) if c["utt_id"] in times] or \
                        [c for k2 in PHRASES for c in clips.get((m["voice"], k2), []) if c["utt_id"] in times]
                if not cands:
                    stat["khong_co_doan_goi"] += 1
                    continue
                c = cands[int(h01(m["sample_id"], "ban") * len(cands))]
                key = c["sample_id"].split("-")[1]
                words = PHRASES[key].lower().split()
                kind, first_keep, mid_j, frac = plan_cut(len(words), m["sample_id"])
                kept = words[first_keep:]
                gap = round(0.3 * h01(m["sample_id"], "gap"), 3)
                w_wake, _ = sf.read(os.path.join(dau_dir, c["audio48"]), dtype="float32")
                w_par, _ = sf.read(os.path.join(run, m["audio48"]), dtype="float32")
                w = build_clip(w_wake, times[c["utt_id"]], w_par, kind, first_keep, mid_j, frac, gap)
                utt = m["utt_id"] + f"__w{kind}"
                p48, p16 = f"audio48/{utt}.flac", f"audio16/{utt}.flac"
                write_flac(os.path.join(out, p48), w, SR)
                write_flac(os.path.join(out, p16), soxr.resample(w, SR, SR16), SR16)
                frame = src.get(m["sample_id"], {}).get("frame", "")
                rec = dict(m, utt_id=utt, sample_id=m["sample_id"] + "#w", parent_utt_id=m["utt_id"],
                           parent_run=os.path.basename(run), wake_phrase=key, wake_type=kind, wake_giu=" ".join(kept),
                           wake_cat=("ranh_gioi" if mid_j is None else f"giua_am_tiet_{mid_j}") if kind == "duoi" else "",
                           gap_s=gap, text_raw=compose_label(kept, m["text_raw"], frame),
                           text_spoken=compose_label(kept, m["text_spoken"], frame),
                           tts_text=compose_label(kept, m.get("tts_text") or m["text_spoken"], frame) if m.get("tts_text") else "",
                           n_syllables=m["n_syllables"] + len(kept), duration_s=round(len(w) / SR, 3),
                           audio48=p48, audio16=p16, retries=[], attempt=0)
                man.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stat[f"{kind}:{rec['wake_cat'] or 'du'}"] += 1
                stat["tong"] += 1
    json.dump(dict(thong_ke=stat, ty_le_chon=SHARE, p_du=P_FULL, p_ranh_gioi=P_BOUNDARY, doan_goi=len(times)),
              open(os.path.join(out, "wake_tom_tat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Ghép xong:", dict(stat), "| đoạn gọi căn hàng được:", len(times))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dau")
    d.add_argument("--tts-args", default="--batch 16 --dtype bfloat16")
    g = sub.add_parser("ghep")
    g.add_argument("--ctc", required=True)
    a = ap.parse_args()
    return cmd_dau(a) if a.cmd == "dau" else cmd_ghep(a)


if __name__ == "__main__":
    sys.exit(main())
