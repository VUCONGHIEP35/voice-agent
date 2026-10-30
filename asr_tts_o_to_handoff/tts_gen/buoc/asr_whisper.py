# -*- coding: utf-8 -*-
"""Kiểm nội dung bằng ASR: PhoWhisper đọc lại bản 16 kHz, tính CER/WER so với text_spoken (và với vieneu_text),
rồi chấm từng câu dat / loai / can_nghe / sinh_lai.

Chạy (từ tts_gen/, SAU khi bước TTS đã giải phóng GPU):
  .venv/Scripts/python -m buoc.asr_whisper runs/pilot100 --model vinai/PhoWhisper-medium
  .venv/Scripts/python -m buoc.asr_whisper runs/pilot100 --model vinai/PhoWhisper-large --backend ct2 \
      --ct2-dir .cache/ct2/PhoWhisper-large-int8          # large lượng tử int8 (CTranslate2), vừa GPU 4 GB
  .venv/Scripts/python -m buoc.asr_whisper runs/pilot100 --rescore --lexicon reports/text_audit_pilot100/lexicon_template.tsv
Ghi <run>/asr_<tag>.jsonl (bỏ qua khi --rescore) và <run>/asr_gate_<tag>.csv. Không sửa âm thanh.
Lưu ý: PhoWhisper không đặt num_beams trong generation_config.json nên pipeline HF tự dùng beam 5; ở đây truyền
--beams tường minh và ghi vào kết quả.

Chấm (asr_gate_<tag>.csv), xét theo thứ tự:
  1. tts_checks (cắt đầu, nói lan man, đọc thiếu) không đạt -> sinh_lai, mọi độ dài câu.
  2. Câu <= --short-max âm tiết: đạt nếu một cấu hình bất kỳ (hyp chính, hyp_c0..c3 trong asr_diagnose.csv,
     --extra-hyp) có CER biến thể = 0; nếu không thì can_nghe. Không tự loại câu ngắn.
  3. Giọng Trung: cer_min <= ngưỡng -> dat; cer_bo_thanh_min > ngưỡng -> loai; còn lại (chỉ lỗi thanh) -> can_nghe.
  4. Giọng Bắc, Nam: cer_min <= ngưỡng -> dat, ngược lại loai.
CER biến thể: nhỏ nhất trên text_spoken, tts_text (nếu có; answer_variants) và mọi biến thể đọc trong --lexicon, mỗi biến thể so nguyên dạng và sau khi
gộp từ địa phương (tui -> tôi) như buoc/asr_chan_doan.py. Ngưỡng --thr là mốc TẠM, chốt lại sau phiếu nghe.
"""
import argparse
import csv
import json
import os
import subprocess
import threading
import time
from thuvien.cham_chu import REGIONS, cer, wer, answer_variants, best_cer  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
os.environ.setdefault("HF_HOME", os.path.join(HERE, ".cache", "hf"))
import thuvien.kiem_am_thanh as tts_checks  # noqa: E402
from thuvien.van_ban import load_lexicon  # noqa: E402

ORDER = {"sinh_lai": 0, "loai": 1, "can_nghe": 2, "dat": 3}


class VramPoller:
    """Đỉnh bộ nhớ GPU theo nvidia-smi (ct2 không đi qua torch.cuda nên không đo bằng max_memory_allocated)."""

    def __init__(self, every=0.2):
        self.every, self.peak, self.base, self._stop = every, None, None, threading.Event()

    def read(self):
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=5).stdout
            return int(out.split()[0])
        except (OSError, subprocess.SubprocessError, ValueError, IndexError):
            return None

    def _loop(self):
        while not self._stop.is_set():
            v = self.read()
            if v is not None:
                self.peak = max(self.peak or 0, v)
            self._stop.wait(self.every)

    def __enter__(self):
        self.base = self.read()
        threading.Thread(target=self._loop, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self._stop.set()


def is_oom(e):
    s = str(e).lower()
    return "out of memory" in s or "cuda_error_out_of_memory" in s or "cublas_status_alloc_failed" in s


def run_hf(a, audios):
    import torch
    from transformers import pipeline
    dev = 0 if torch.cuda.is_available() else -1
    if dev == 0:
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    asr = pipeline("automatic-speech-recognition", model=a.model, dtype=torch.float16 if dev == 0 else torch.float32,
                   device=dev)
    load_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    feats = [{"raw": w, "sampling_rate": 16000} for w in audios]  # pipeline pop() khóa khỏi dict: không dùng lại
    outs = asr(feats, batch_size=a.batch, generate_kwargs={"language": "vi", "task": "transcribe", "num_beams": a.beams})
    peak = round(torch.cuda.max_memory_allocated() / 2 ** 30, 2) if dev == 0 else None
    return [o["text"].strip() for o in outs], load_s, time.perf_counter() - t1, a.beams, f"torch {peak} GB"


def run_ct2(a, audios):
    if hasattr(os, "add_dll_directory"):  # Windows: dùng cuBLAS/cuDNN đi kèm torch cu128
        import torch
        os.add_dll_directory(os.path.join(os.path.dirname(torch.__file__), "lib"))
    from faster_whisper import WhisperModel
    t0 = time.perf_counter()
    model = WhisperModel(a.ct2_dir, device="cuda", compute_type=a.compute_type)
    load_s = time.perf_counter() - t0
    beams = a.beams
    while True:
        try:
            t1 = time.perf_counter()
            hyps = []
            for w in audios:
                segs, _ = model.transcribe(w, language="vi", task="transcribe", beam_size=beams, temperature=0.0,
                                           without_timestamps=True, condition_on_previous_text=False,
                                           vad_filter=False, no_speech_threshold=None)
                hyps.append(" ".join(s.text.strip() for s in segs).strip())
            return hyps, load_s, time.perf_counter() - t1, beams, None
        except RuntimeError as e:
            lower = [b for b in (2, 1) if b < beams]
            if not (is_oom(e) and lower):
                raise
            print(f"Hết VRAM ở beam {beams}, thử beam {lower[0]}", flush=True)
            beams = lower[0]


def transcribe(a, man, tag):
    import numpy as np
    import soundfile as sf
    audios = []
    for m in man:
        w, sr = sf.read(os.path.join(a.run, m["audio16"]), dtype="float32")
        assert sr == 16000, f"{m['audio16']}: {sr} Hz"
        audios.append(np.asarray(w))
    with VramPoller() as vp:
        hyps, load_s, dt, beams, extra = (run_ct2 if a.backend == "ct2" else run_hf)(a, audios)
    res = []
    with open(os.path.join(a.run, f"asr_{tag}.jsonl"), "w", encoding="utf-8", newline="\n") as fo:
        for m, hyp in zip(man, hyps):
            r = dict(utt_id=m["utt_id"], model=a.model, backend=a.backend,
                     compute_type=a.compute_type if a.backend == "ct2" else "float16", num_beams=beams, hyp=hyp,
                     text_spoken=m["text_spoken"], vieneu_text=m["vieneu_text"],
                     cer=round(cer(m["text_spoken"], hyp), 4), wer=round(wer(m["text_spoken"], hyp), 4),
                     cer_vs_vieneu_text=round(cer(m["vieneu_text"], hyp), 4), speaker_region=m["speaker_region"],
                     length_class=m["length_class"], n_syllables=m["n_syllables"], loan_unverified=m["loan_unverified"])
            res.append(r)
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    used = f"{(vp.peak or 0) - (vp.base or 0)} MB" if vp.peak is not None else "?"
    print(f"{tag}: nạp {load_s:.1f} s, nhận dạng {len(man)} câu trong {dt:.1f} s, beam {beams}, "
          f"VRAM đỉnh nvidia-smi {vp.peak} MB (tăng {used} so với trước khi nạp){', ' + extra if extra else ''}")
    for reg in REGIONS + (None,):
        xs = [r for r in res if reg is None or r["speaker_region"] == reg]
        cs = sorted(r["cer"] for r in xs)
        if not cs:
            continue
        print(f"  {reg or 'Tất cả':6s} n={len(xs):3d} | CER trung bình {sum(cs) / len(cs):.3f}, trung vị {cs[len(cs) // 2]:.3f} | "
              f"CER = 0: {sum(c == 0 for c in cs)} | CER > 0,1: {sum(c > 0.1 for c in cs)}")
    print("Câu CER cao nhất:")
    for r in sorted(res, key=lambda r: -r["cer"])[:12]:
        print(f"  {r['cer']:.2f} {r['utt_id']} | đọc: {r['text_spoken']} | nghe: {r['hyp']}")
    return {r["utt_id"]: r["hyp"] for r in res}


def gate(a, man, hyps, tag):
    import soundfile as sf
    thr = {k: float(v) for k, v in (x.split("=", 1) for x in a.thr)}
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    diag = {}
    if os.path.exists(a.diag):
        with open(a.diag, encoding="utf-8-sig") as f:
            diag = {d["utt_id"]: d for d in csv.DictReader(f)}
    extra = []
    for p in a.extra_hyp:
        with open(p, encoding="utf-8") as f:
            extra.append({d["utt_id"]: d["hyp"] for d in map(json.loads, f)})
    rows = []
    for m in man:
        u, hyp = m["utt_id"], hyps.get(m["utt_id"], "")
        region = m.get("voice_region") or m["speaker_region"]
        variants = answer_variants(m, lex)
        c_min, match = best_cer(variants, hyp)
        c_nt, _ = best_cer(variants, hyp, tone=False)
        w, _ = sf.read(os.path.join(a.run, m["audio16"]), dtype="float32")
        why, hd = tts_checks.check(w, m["n_syllables"], m.get("speech_s"))
        t = thr[region]
        short = m["n_syllables"] <= a.short_max
        c_short = None
        if why:
            v, ly = "sinh_lai", "+".join(why)
        elif short:
            cands = [hyp] + [d.get(u, "") for d in extra]
            if u in diag:
                cands += [diag[u].get(f"hyp_c{i}", "") for i in range(4)]
            c_short = min(best_cer(variants, h)[0] for h in cands if h) if any(cands) else 1.0
            v, ly = ("dat", "cau_ngan_khop") if c_short == 0 else ("can_nghe", "cau_ngan")
            if u not in diag:
                ly += "+chua_chan_doan"
        elif c_min <= t:
            v, ly = "dat", ""
        elif region == "Trung":
            v, ly = ("loai", "sai_ngoai_thanh") if c_nt > t else ("can_nghe", "chi_loi_thanh")
        else:
            v, ly = "loai", "sai"
        rows.append(dict(utt_id=u, region=region, voice=m["voice"], n_syl=m["n_syllables"], head_db=hd,
                         tts_check="dat" if not why else "loi:" + "+".join(why), cer=round(cer(m["text_spoken"], hyp), 3),
                         cer_min=round(c_min, 3), cer_bo_thanh_min=round(c_nt, 3),
                         bien_the_khop=match if match != variants[0] else "",
                         cer_ngan_tot_nhat=None if c_short is None else round(c_short, 3),
                         ket_qua=v, ly_do=ly, nguong=t, text_spoken=m["text_spoken"], hyp=hyp))
    out_p = os.path.join(a.run, f"asr_gate_{tag}.csv")
    with open(out_p, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        for r in sorted(rows, key=lambda r: (ORDER[r["ket_qua"]], -r["cer_min"])):
            wr.writerow(r)
    print(f"\nChấm {tag} | ngưỡng TẠM {thr} | từ điển {sum(bool(v) for _, v in lex)} mục có biến thể | "
          f"asr_diagnose: {'có' if diag else 'không'} -> {out_p}")
    print(f"  {'':8s}" + "".join(f"{k:>10s}" for k in ORDER))
    for reg in REGIONS + (None,):
        g = [r for r in rows if reg is None or r["region"] == reg]
        print(f"  {reg or 'Tất cả':8s}" + "".join(f"{sum(r['ket_qua'] == k for r in g):10d}" for k in ORDER))
    if diag:
        print("  asr_diagnose.ket_luan -> ket_qua:")
        tab = {}
        for r in rows:
            k = diag.get(r["utt_id"], {}).get("ket_luan", "?")
            tab.setdefault(k, {}).setdefault(r["ket_qua"], 0)
            tab[k][r["ket_qua"]] += 1
        for k, d in sorted(tab.items()):
            print(f"    {k:22s} {d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--model", default="vinai/PhoWhisper-medium", help="mô hình HF (backend ct2: tên mô hình gốc để ghi lại)")
    ap.add_argument("--backend", choices=["hf", "ct2"], default="hf")
    ap.add_argument("--ct2-dir", default=None, help="thư mục mô hình CTranslate2 (ct2-transformers-converter)")
    ap.add_argument("--compute-type", default="int8_float16")
    ap.add_argument("--batch", type=int, default=2, help="backend hf, GPU 4 GB: lô 8 câu với medium bị hết VRAM (bộ đệm cross-attention)")
    ap.add_argument("--beams", type=int, default=5)
    ap.add_argument("--rescore", action="store_true", help="không chạy ASR, chấm lại từ asr_<tag>.jsonl đã có")
    ap.add_argument("--lexicon", action="append", default=[], help="TSV biến thể đọc (phantich/kiem_van_ban.py), dùng được nhiều lần")
    ap.add_argument("--thr", nargs=3, default=["Bắc=0.10", "Trung=0.10", "Nam=0.10"], metavar="VÙNG=NGƯỠNG",
                    help="ngưỡng CER theo vùng (mốc tạm, chốt sau phiếu nghe)")
    ap.add_argument("--diag", default=None, help="mặc định <run>/asr_diagnose.csv")
    ap.add_argument("--extra-hyp", action="append", default=[], help="asr_*.jsonl khác, thêm làm cấu hình cho câu ngắn")
    ap.add_argument("--short-max", type=int, default=3)
    ap.add_argument("--tag", default=None, help="tên tệp ra asr_<tag>.jsonl (mặc định suy từ --model/--backend); dùng khi so cỡ lô")
    a = ap.parse_args()
    a.diag = a.diag or os.path.join(a.run, "asr_diagnose.csv")
    if a.backend == "ct2" and not a.ct2_dir:
        ap.error("--backend ct2 cần --ct2-dir")
    tag = a.tag or (a.model.split("/")[-1] + (f"-ct2-{a.compute_type.split('_')[0]}" if a.backend == "ct2" else ""))

    with open(os.path.join(a.run, "manifest.jsonl"), encoding="utf-8") as f:
        man = [json.loads(line) for line in f]
    if a.rescore:
        with open(os.path.join(a.run, f"asr_{tag}.jsonl"), encoding="utf-8") as f:
            hyps = {d["utt_id"]: d["hyp"] for d in map(json.loads, f)}
    else:
        hyps = transcribe(a, man, tag)
    gate(a, man, hyps, tag)


if __name__ == "__main__":
    main()
