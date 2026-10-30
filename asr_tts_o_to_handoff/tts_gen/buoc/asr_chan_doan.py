# -*- coding: utf-8 -*-
"""buoc/asr_chan_doan.py - tach loi do ASR khoi loi do TTS bang cach doi cau hinh nhan dang.

Y tuong: neu chi can doi cach giai ma (dem im lang, beam search) hoac doi sang mo hinh khac kien truc
ma cau duoc nghe dung, thi am thanh TTS nhieu kha nang dung va loi thuoc ve ASR. Neu moi cau hinh deu sai,
cau do dang nghi TTS doc sai -> uu tien nghe.

Cac dieu kien (deu chay tren ban 16 kHz trong manifest):
  c0  PhoWhisper nhu buoc/asr_whisper.py (doc lai tu asr_<model>.jsonl, khong chay lai). Luu y: PhoWhisper khong dat
      num_beams trong generation_config.json nen pipeline ASR dung mac dinh cua no la beam 5 -> c0 da la beam 5
  c1  PhoWhisper + dem 0,3 s im lang dau va cuoi, giai ma tham lam (num_beams=1 dat tuong minh)
  c2  PhoWhisper + dem + beam search 5 (so voi c0 chi khac phan dem)
  (them) dau_bi_cat: 5 ms dau co nang luong > -40 dBFS, tuc am thanh bat dau giua am vi -> TTS cat dau cau
  c3  wav2vec2 CTC khong co mo hinh ngon ngu (nguyenvulebinh/wav2vec2-base-vietnamese-250h, CC BY-NC 4.0) + dem

Chay tu tts_gen/ (GPU 4 GB: giu --batch 1 cho beam search):
  .venv/Scripts/python -m buoc.asr_chan_doan runs/pilot100 --whisper vinai/PhoWhisper-medium
  .venv/Scripts/python -m buoc.asr_chan_doan runs/pilot100 --skip c3          # bo wav2vec2 neu khong tai duoc
Ghi <run>/asr_diagnose.csv va in tom tat theo vung.
"""
import argparse
import csv
import json
import os
import re
import time
import unicodedata

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
os.environ.setdefault("HF_HOME", os.path.join(HERE, ".cache", "hf"))

DIALECT_EQUIV = {"tui": "tôi", "hông": "không", "hổng": "không", "nghen": "nhé", "nhen": "nhé",
                 "nha": "nhé", "hen": "nhé", "mô": "đâu", "răng": "sao", "rứa": "thế", "chi": "gì",
                 "ni": "này", "tê": "kia", "vầy": "vậy"}


def norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def cer(ref, hyp, equiv=False):
    r, h = norm(ref), norm(hyp)
    if equiv:  # bo qua tu dia phuong bi ASR doi sang tu pho thong
        r = " ".join(DIALECT_EQUIV.get(w, w) for w in r.split())
        h = " ".join(DIALECT_EQUIV.get(w, w) for w in h.split())
    r, h = r.replace(" ", ""), h.replace(" ", "")
    return edit_distance(r, h) / max(len(r), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--whisper", default="vinai/PhoWhisper-medium")
    ap.add_argument("--ctc", default="nguyenvulebinh/wav2vec2-base-vietnamese-250h")
    ap.add_argument("--pad", type=float, default=0.3, help="giay im lang them vao dau va cuoi")
    ap.add_argument("--beams", type=int, default=5)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--thr", type=float, default=0.05, help="CER coi la nghe dung")
    ap.add_argument("--skip", nargs="*", default=[], choices=["c1", "c2", "c3"])
    a = ap.parse_args()

    import numpy as np
    import soundfile as sf
    import torch

    with open(os.path.join(a.run, "manifest.jsonl"), encoding="utf-8") as f:
        man = [json.loads(l) for l in f]
    tag = a.whisper.split("/")[-1]
    base = {}
    p0 = os.path.join(a.run, f"asr_{tag}.jsonl")
    if os.path.exists(p0):
        with open(p0, encoding="utf-8") as f:
            base = {d["utt_id"]: d["hyp"] for d in map(json.loads, f)}
    dev = 0 if torch.cuda.is_available() else -1
    pad = int(a.pad * 16000)
    raw, padded = [], []
    for m in man:
        w, sr = sf.read(os.path.join(a.run, m["audio16"]), dtype="float32")
        assert sr == 16000, f"{m['audio16']}: {sr} Hz"
        raw.append(w)
        padded.append(np.pad(w, (pad, pad)))
    hyps = {"c0": [base.get(m["utt_id"], "") for m in man]}

    if not {"c1", "c2"} <= set(a.skip):
        from transformers import pipeline
        asr = pipeline("automatic-speech-recognition", model=a.whisper,
                       dtype=torch.float16 if dev == 0 else torch.float32, device=dev)
        gk = {"language": "vi", "task": "transcribe"}
        def feats():  # pipeline pop() khoa "raw"/"sampling_rate" khoi dict dau vao -> moi lan goi can dict moi
            return [{"raw": w, "sampling_rate": 16000} for w in padded]
        if "c1" not in a.skip:
            t = time.perf_counter()
            hyps["c1"] = [o["text"].strip() for o in
                          asr(feats(), batch_size=a.batch, generate_kwargs={**gk, "num_beams": 1})]
            print(f"c1 (dem, tham lam): {time.perf_counter() - t:.1f} s")
        if "c2" not in a.skip:
            t = time.perf_counter()
            hyps["c2"] = [o["text"].strip() for o in
                          asr(feats(), batch_size=a.batch, generate_kwargs={**gk, "num_beams": a.beams})]
            print(f"c2 (dem + beam {a.beams}): {time.perf_counter() - t:.1f} s")
        del asr
        if dev == 0:
            torch.cuda.empty_cache()

    if "c3" not in a.skip:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        proc = Wav2Vec2Processor.from_pretrained(a.ctc)
        model = Wav2Vec2ForCTC.from_pretrained(a.ctc).eval()
        if dev == 0:
            model = model.cuda()
        t = time.perf_counter()
        out = []
        with torch.no_grad():
            for w in padded:
                x = proc(w, sampling_rate=16000, return_tensors="pt").input_values
                if dev == 0:
                    x = x.cuda()
                ids = torch.argmax(model(x).logits, dim=-1)
                out.append(proc.batch_decode(ids)[0].strip())
        hyps["c3"] = out
        print(f"c3 (wav2vec2 CTC): {time.perf_counter() - t:.1f} s")

    conds = [c for c in ("c0", "c1", "c2", "c3") if c in hyps]
    rows = []
    for i, m in enumerate(man):
        head = raw[i][:80]  # 5 ms dau o 16 kHz
        head_db = float(20 * np.log10(np.sqrt(np.mean(head ** 2)) + 1e-9)) if len(head) else -200.0
        r = {"utt_id": m["utt_id"], "region": m["speaker_region"], "voice": m["voice"],
             "n_syl": m["n_syllables"], "lead_sil_s": m.get("lead_sil_s"),
             "dau_bi_cat": head_db > -40,  # am thanh bat dau giua am vi -> TTS cat mat dau cau, nen sinh lai
             "text_spoken": m["text_spoken"]}
        cs = {}
        for c in conds:
            h = hyps[c][i]
            cs[c] = cer(m["text_spoken"], h, equiv=True) if h else None
            r[f"hyp_{c}"] = h
            r[f"cer_{c}"] = None if cs[c] is None else round(cs[c], 3)
        valid = {c: v for c, v in cs.items() if v is not None}
        best = min(valid, key=valid.get) if valid else ""
        r["cer_min"] = round(valid[best], 3) if valid else None
        r["best"] = best
        c0 = cs.get("c0")
        if r["dau_bi_cat"]:
            v = "tts_cat_dau_sinh_lai"
        elif c0 is not None and c0 <= a.thr:
            v = "dung_ngay"
        elif any(cs.get(c) is not None and cs[c] <= a.thr for c in ("c1", "c2")):
            v = "loi_cau_hinh_asr"      # dem/beam la sua duoc -> am thanh dung
        elif cs.get("c3") is not None and cs["c3"] <= a.thr:
            v = "loi_mo_hinh_asr"       # mo hinh khac kien truc nghe dung
        else:
            v = "nghi_tts_can_nghe"
        r["ket_luan"] = v
        rows.append(r)

    out_p = os.path.join(a.run, "asr_diagnose.csv")
    with open(out_p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        order = {"tts_cat_dau_sinh_lai": 0, "nghi_tts_can_nghe": 1, "loi_mo_hinh_asr": 2,
                 "loi_cau_hinh_asr": 3, "dung_ngay": 4}
        for r in sorted(rows, key=lambda r: (order[r["ket_luan"]], -(r["cer_min"] or 0))):
            w.writerow(r)
    print(f"\nNguong CER {a.thr} (da gop tu dia phuong). Ket qua -> {out_p}")
    for reg in ("Bắc", "Trung", "Nam", None):
        g = [r for r in rows if reg is None or r["region"] == reg]
        if not g:
            continue
        cnt = {k: sum(r["ket_luan"] == k for r in g) for k in order}
        means = "  ".join(f"{c}={sum(r[f'cer_{c}'] or 0 for r in g) / len(g):.3f}" for c in conds)
        print(f"  {reg or 'Tat ca':6s} n={len(g):3d} | {means} | " + ", ".join(f"{k}: {v}" for k, v in cnt.items()))


if __name__ == "__main__":
    main()
