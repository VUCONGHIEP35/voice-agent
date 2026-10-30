# -*- coding: utf-8 -*-
"""Nhận dạng một lượt chạy bằng Zipformer-30M (sherpa-onnx, CPU), ghi <run>/asr_<tag>.jsonl cùng dạng buoc/asr_whisper.py.

Chạy (từ tts_gen/, venv riêng):
  .venv_zip/Scripts/python -m buoc.asr_zipformer runs/ket_qua_A/runs/eval1000_A --limit 3          # thử nhanh, không ghi tệp
  .venv_zip/Scripts/python -m buoc.asr_zipformer runs/ket_qua_A/runs/eval1000_A                    # int8, greedy
  .venv_zip/Scripts/python -m buoc.asr_zipformer <run> --precision fp32 --limit 100 --write        # so int8/fp32 trên 100 câu
  .venv_zip/Scripts/python -m buoc.asr_zipformer <run> --decoding modified_beam_search --beam 4
Âm thanh: audio16 nếu tệp có; không thì đọc audio48 rồi hạ 16 kHz bằng soxr.resample (đúng cách buoc/tts.py tạo audio16).
Không ghi đè asr_<tag>.jsonl đã có. Thời gian, RTF, RAM đỉnh ghi vào <run>/logs/zipformer_<tag>.json.
Mô hình: .cache/zipformer30m/<commit8>/ do buoc/tai_zipformer.py tải (CC BY-NC-ND 4.0, chỉ đánh giá).
"""
import argparse
import json
import os
import threading
import time
from cauhinh.mo_hinh import ZIPFORMER_REV  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from thuvien.cham_chu import REGIONS, cer, wer  # noqa: E402
from thuvien.manifest import load_jsonl  # noqa: E402

MODEL_DIR = os.path.join(os.environ.get("ZIPFORMER_DIR") or os.path.join(HERE, ".cache", "zipformer30m"), ZIPFORMER_REV[:8])
SR16 = 16000


def model_files(model_dir, precision):
    suf = ".int8.onnx" if precision == "int8" else ".onnx"
    files = {k: os.path.join(model_dir, f"{k}-epoch-20-avg-10{suf}") for k in ("encoder", "decoder", "joiner")}
    files["tokens"] = os.path.join(model_dir, "tokens.txt")
    for p in files.values():
        if not os.path.exists(p):
            raise SystemExit(f"Thiếu {p}: chạy buoc/tai_zipformer.py trước")
    return files


def make_tag(precision, decoding, beam):
    return f"Zipformer-30M-{precision}" + ("" if decoding == "greedy_search" else f"-beam{beam}")


def load_audio(run, m):
    import numpy as np
    import soundfile as sf
    import soxr
    p16 = os.path.join(run, m.get("audio16", ""))
    if m.get("audio16") and os.path.exists(p16):
        w, sr = sf.read(p16, dtype="float32")
    else:
        w, sr = sf.read(os.path.join(run, m["audio48"]), dtype="float32")
    if w.ndim > 1:
        w = w.mean(axis=1)
    if sr != SR16:
        w = soxr.resample(w, sr, SR16) if len(w) else w
    return np.ascontiguousarray(w, dtype=np.float32)


class RamPeak:
    """RSS đỉnh của tiến trình này, lấy mẫu mỗi 0,2 s."""
    def __init__(self):
        import psutil
        self.p, self.peak, self._stop = psutil.Process(), 0, False

    def __enter__(self):
        def loop():
            while not self._stop:
                self.peak = max(self.peak, self.p.memory_info().rss)
                time.sleep(0.2)
        self.t = threading.Thread(target=loop, daemon=True)
        self.t.start()
        return self

    def __exit__(self, *exc):
        self._stop = True
        self.t.join()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--model-dir", default=MODEL_DIR)
    ap.add_argument("--precision", choices=["int8", "fp32"], default="int8")
    ap.add_argument("--decoding", choices=["greedy_search", "modified_beam_search"], default="greedy_search")
    ap.add_argument("--beam", type=int, default=4)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="chỉ N dòng đầu manifest (thử); không ghi tệp trừ khi --write")
    ap.add_argument("--write", action="store_true", help="ghi tệp cả khi có --limit (tag thêm _N)")
    a = ap.parse_args()

    import sherpa_onnx
    man = load_jsonl(os.path.join(a.run, "manifest.jsonl"))
    if a.limit:
        man = man[:a.limit]
    tag = make_tag(a.precision, a.decoding, a.beam) + (f"_{a.limit}" if a.limit else "")
    out = os.path.join(a.run, f"asr_{tag}.jsonl")
    write = not a.limit or a.write
    if write and os.path.exists(out):
        raise SystemExit(f"Đã có {out}: không ghi đè")

    f = model_files(a.model_dir, a.precision)
    with RamPeak() as rp:
        t0 = time.time()
        rec = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f["encoder"], decoder=f["decoder"], joiner=f["joiner"], tokens=f["tokens"], num_threads=a.threads,
            sample_rate=SR16, feature_dim=80, decoding_method=a.decoding, max_active_paths=a.beam, provider="cpu")
        load_s = time.time() - t0
        audios = [load_audio(a.run, m) for m in man]
        t1 = time.time()
        hyps = []
        for w in audios:
            s = rec.create_stream()
            s.accept_waveform(SR16, w)
            rec.decode_stream(s)
            hyps.append(s.result.text.strip())
        dt = time.time() - t1
    audio_s = sum(len(w) for w in audios) / SR16
    res = []
    for m, hyp in zip(man, hyps):
        res.append(dict(utt_id=m["utt_id"], model="hynt/Zipformer-30M-RNNT-6000h", backend="sherpa-onnx", compute_type=a.precision,
                        decoding=a.decoding, num_beams=a.beam if a.decoding != "greedy_search" else 1, hyp=hyp,
                        text_spoken=m["text_spoken"], vieneu_text=m.get("vieneu_text"),
                        cer=round(cer(m["text_spoken"], hyp), 4), wer=round(wer(m["text_spoken"], hyp), 4),
                        speaker_region=m["speaker_region"], length_class=m.get("length_class"),
                        n_syllables=m.get("n_syllables"), loan_unverified=m.get("loan_unverified")))
    info = dict(tag=tag, n=len(res), load_s=round(load_s, 2), decode_s=round(dt, 2), audio_s=round(audio_s, 1),
                rtf=round(dt / max(audio_s, 1e-9), 4), ram_peak_gb=round(rp.peak / 2 ** 30, 2), threads=a.threads,
                sherpa_onnx=sherpa_onnx.__version__, model_dir=os.path.relpath(a.model_dir, HERE).replace(os.sep, "/"),
                luc=time.strftime("%Y-%m-%d %H:%M:%S"))
    print(f"{tag}: nạp {load_s:.1f} s, nhận dạng {len(res)} câu ({audio_s:.0f} s âm thanh) trong {dt:.1f} s, "
          f"RTF {info['rtf']}, RAM đỉnh {info['ram_peak_gb']} GB, {a.threads} luồng")
    for reg in REGIONS + (None,):
        cs = sorted(r["cer"] for r in res if reg is None or r["speaker_region"] == reg)
        if cs:
            print(f"  {reg or 'Tất cả':6s} n={len(cs):3d} | CER (so text_spoken) TB {sum(cs) / len(cs):.3f}, "
                  f"trung vị {cs[len(cs) // 2]:.3f} | CER = 0: {sum(c == 0 for c in cs)}")
    for r in res[:5] if a.limit else sorted(res, key=lambda r: -r["cer"])[:10]:
        print(f"  {r['cer']:.2f} {r['utt_id']} | đọc: {r['text_spoken']} | nghe: {r['hyp']}")
    if write:
        with open(out, "w", encoding="utf-8", newline="\n") as fo:
            for r in res:
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.makedirs(os.path.join(a.run, "logs"), exist_ok=True)
        json.dump(info, open(os.path.join(a.run, "logs", f"zipformer_{tag}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("Ghi", out)


if __name__ == "__main__":
    main()
