# -*- coding: utf-8 -*-
"""Kiểm tra giọng Minh Triết theo docs/kiem_tra_giong_minh_triet.md: lỗi do cấu hình sinh hay do giọng mẫu.

8 câu (4 câu thí điểm của Minh Triết + 4 câu Nam thuần Việt từ bộ v3, mỗi lớp độ dài một câu)
× 3 giọng (Minh Triết; đối chứng Đức Trí, Mỹ Duyên) × 2 seed × 4 cấu hình:
  A  như buoc/tts.py: use_ref_codes=True, temperature 0.8, top_k 25, bf16, gom lô 8
  B  use_ref_codes=False (chỉ embedding người nói)
  C  temperature 0.6
  D  fp32, batch_size 1

Chạy từ tts_gen/, mỗi bước một tiến trình (RAM thấp; TTS và ASR không chung tiến trình):
  .venv/Scripts/python -m luutru.test_voice_config gen --cfg A        # rồi B, C, D
  .venv/Scripts/python -m buoc.asr_whisper runs/minh_triet_test/A --model vinai/PhoWhisper-large --backend ct2 --ct2-dir .cache/ct2/PhoWhisper-large-int8
  .venv/Scripts/python -m buoc.asr_whisper runs/minh_triet_test/A --model vinai/PhoWhisper-medium
  .venv/Scripts/python -m buoc.asr_chan_doan runs/minh_triet_test/A
  .venv/Scripts/python -m luutru.test_voice_config report --lexicon reports/text_audit_pilot100/lexicon_template.tsv
Ghi runs/minh_triet_test/<cfg>/ (audio48, audio16, manifest.jsonl cùng định dạng runs/pilot100) và
runs/minh_triet_test/ket_qua.csv, tom_tat.md, nghe_mu/ (tệp đổi tên ngẫu nhiên, phieu_nghe.csv, khoa_KHONG_DUA_NGUOI_NGHE.csv).
"""
import argparse
import csv
import glob
import json
import os
import random
import shutil
import time

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
os.environ.setdefault("HF_HOME", os.path.join(HERE, ".cache", "hf"))
OUT = os.path.join(HERE, "runs", "minh_triet_test")
VOICES = ["Minh Triết", "Đức Trí", "Mỹ Duyên"]
TARGET = "Minh Triết"
SEEDS = (1, 2)
PILOT_IDS = ["CS09-M1-00175", "CS04-M1-00332", "CS03-M1-00570", "CS10-M1-00222"]
LEN_CLASSES = ["Rất ngắn", "Ngắn", "Thường", "Dài"]
CFGS = {
    "A": dict(desc="mốc: ref codes, T 0.8, bf16, lô 8", dtype="auto", batch=8, use_ref_codes=True, temperature=0.8),
    "B": dict(desc="use_ref_codes=False", dtype="auto", batch=8, use_ref_codes=False, temperature=0.8),
    "C": dict(desc="temperature 0.6", dtype="auto", batch=8, use_ref_codes=True, temperature=0.6),
    "D": dict(desc="fp32, batch_size 1", dtype="float32", batch=1, use_ref_codes=True, temperature=0.8),
}
TOP_K = 25
CER_OK = 0.10


def pick_sentences():
    from thuvien.van_ban import is_viet_syllable, norm_text  # noqa: E402
    from buoc.tts import RUN_SEED, h32  # noqa: E402
    with open(os.path.join(HERE, "pilot", "pilot_100.jsonl"), encoding="utf-8") as f:
        pil = {r["sample_id"]: r for r in map(json.loads, f)}
    rows = [json.loads(l) for p in sorted(glob.glob(os.path.join(HERE, "..", "data", "m1m2_10k_v3", "*.jsonl")))
            for l in open(p, encoding="utf-8")]
    ok = [r for r in rows if r["speaker_region"] == "Nam" and r["sample_id"] not in pil
          and r["review_status"] == "không bắt buộc"
          and all(is_viet_syllable(t) for t in norm_text(r["text_spoken"]).split())]
    extra = []
    for lc in LEN_CLASSES:
        extra.append(min((r for r in ok if r["length_class"] == lc), key=lambda r: h32(RUN_SEED, "minh_triet_test", r["sample_id"])))
    return [dict(pil[i], nguon="thi_diem_minh_triet") for i in PILOT_IDS] + [dict(r, nguon="v3_nam_thuan_viet") for r in extra]


def gen(a):
    import numpy as np
    import soxr
    import torch
    import vieneu
    from vieneu import Vieneu
    from vieneu_utils.phonemize_text import normalize_to_chunks_v3_with_gaps
    import thuvien.kiem_am_thanh as tts_checks  # noqa: E402
    from buoc.tts import SR, SR16, measure, slug  # noqa: E402
    from thuvien.am_thanh import write_flac  # noqa: E402

    c = CFGS[a.cfg]
    out = os.path.join(OUT, a.cfg)
    if os.path.exists(os.path.join(out, "manifest.jsonl")):
        raise SystemExit(f"{out} đã có manifest.jsonl; xóa thư mục nếu muốn sinh lại")
    for d in ("audio48", "audio16"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    sents = pick_sentences()
    with open(os.path.join(os.path.dirname(vieneu.__file__), "assets", "voices_v3_turbo.json"), encoding="utf-8") as f:
        presets = json.load(f)["presets"]
    t0 = time.perf_counter()
    tts = Vieneu("v3turbo", max_batch_size=c["batch"], dtype=c["dtype"])
    load_s = time.perf_counter() - t0
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    calls = []
    with open(os.path.join(out, "manifest.jsonl"), "w", encoding="utf-8", newline="\n") as man:
        for voice in VOICES:
            vm = presets[voice]
            for seed in SEEDS:
                torch.manual_seed(seed)
                random.seed(seed)
                np.random.seed(seed)
                t1 = time.perf_counter()
                wavs = tts.infer_batch([s["text_spoken"] for s in sents], voice=voice, apply_watermark=False,
                                       use_ref_codes=c["use_ref_codes"], temperature=c["temperature"], top_k=TOP_K,
                                       batch_size=c["batch"])
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                dt = time.perf_counter() - t1
                audio_s = sum(len(w) for w in wavs) / SR
                calls.append(dict(voice=voice, seed=seed, wall_s=round(dt, 2), audio_s=round(audio_s, 2)))
                print(f"{a.cfg} {voice:11s} seed {seed}: {dt:5.1f} s cho {audio_s:5.1f} s âm thanh", flush=True)
                for s, w in zip(sents, wavs):
                    w = np.asarray(w, dtype=np.float32)
                    q = measure(w)
                    w16 = soxr.resample(w, SR, SR16) if len(w) else w
                    why, hd = tts_checks.check(w16, s["n_syllables"], q["speech_s"], SR16)
                    utt = f"{s['sample_id']}__{slug(voice)}__s{seed}"
                    p48, p16 = f"audio48/{utt}.flac", f"audio16/{utt}.flac"
                    write_flac(os.path.join(out, p48), w, SR)
                    write_flac(os.path.join(out, p16), w16, SR16)
                    chunks, _ = normalize_to_chunks_v3_with_gaps(s["text_spoken"], max_chars=256)
                    rec = dict(utt_id=utt, sample_id=s["sample_id"], nguon=s["nguon"], cfg=a.cfg, case_id=s["case_id"],
                               intent_id=s["intent_id"], text_raw=s["text_raw"], text_spoken=s["text_spoken"],
                               vieneu_text=" ".join(chunks), speaker_region=s["speaker_region"], sub_region=s["sub_region"],
                               residence=s["residence"], length_class=s["length_class"], n_syllables=s["n_syllables"],
                               voice=voice, voice_source="preset", voice_region=vm.get("region"),
                               voice_gender=vm.get("gender"), voice_style=vm.get("style"), seed=seed, attempt=0, **q,
                               rate_syl_per_s=round(s["n_syllables"] / q["speech_s"], 2) if q["speech_s"] else None,
                               clipped=bool(q["peak"] >= 0.999), head_db=hd,
                               tts_check="dat" if not why else "loi:" + "+".join(why), retries=[],
                               review_status=s["review_status"],
                               loan_unverified=any(x.startswith("cách đọc chưa xác minh") for x in s["review_reasons"]),
                               app_group=s.get("app_group", ""), audio48=p48, audio16=p16)
                    man.write(json.dumps(rec, ensure_ascii=False) + "\n")
    cfg = dict(cfg=a.cfg, **c, top_k=TOP_K, seeds=SEEDS, voices=VOICES, sentences=[s["sample_id"] for s in sents],
               engine_dtype=str(getattr(tts.engine, "dtype", None)), load_s=round(load_s, 1), calls=calls,
               vram_peak_alloc_gb=round(torch.cuda.max_memory_allocated() / 2 ** 30, 3) if torch.cuda.is_available() else None)
    with open(os.path.join(out, "run_config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    print(f"Xong {a.cfg}: dtype {cfg['engine_dtype']}, VRAM đỉnh {cfg['vram_peak_alloc_gb']} GB -> {out}")


def report(a):
    from thuvien.cham_chu import best_cer, norm  # noqa: E402
    from thuvien.van_ban import load_lexicon, ref_variants  # noqa: E402
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    rows = []
    for cfg in CFGS:
        d = os.path.join(OUT, cfg)
        if not os.path.exists(os.path.join(d, "manifest.jsonl")):
            print(f"Thiếu cấu hình {cfg}, bỏ qua")
            continue
        man = [json.loads(l) for l in open(os.path.join(d, "manifest.jsonl"), encoding="utf-8")]
        hyps = {}  # nguồn -> {utt_id: hyp}
        for p in sorted(glob.glob(os.path.join(d, "asr_*.jsonl"))):
            name = os.path.basename(p)[4:-6]
            hyps[name] = {r["utt_id"]: r["hyp"] for r in map(json.loads, open(p, encoding="utf-8"))}
        dp = os.path.join(d, "asr_diagnose.csv")
        if os.path.exists(dp):
            for r in csv.DictReader(open(dp, encoding="utf-8-sig")):
                for k in ("c1", "c2", "c3"):
                    if r.get(f"hyp_{k}"):
                        hyps.setdefault(f"diag_{k}", {})[r["utt_id"]] = r[f"hyp_{k}"]
        for m in man:
            vs = ref_variants(norm(m["text_spoken"]), lex)
            per = {k: round(best_cer(vs, h[m["utt_id"]])[0], 3) for k, h in hyps.items() if h.get(m["utt_id"])}
            best = min(per, key=per.get) if per else ""
            rows.append(dict(cfg=cfg, voice=m["voice"], seed=m["seed"], sample_id=m["sample_id"], nguon=m["nguon"],
                             length_class=m["length_class"], text_spoken=m["text_spoken"], tts_check=m["tts_check"],
                             head_db=m["head_db"], rate_syl_per_s=m["rate_syl_per_s"],
                             cer_min=per[best] if per else None, nguon_tot_nhat=best,
                             hyp_tot_nhat=hyps[best][m["utt_id"]] if best else "",
                             **{f"cer_{k}": v for k, v in sorted(per.items())}, audio48=os.path.join(cfg, m["audio48"])))
    if not rows:
        raise SystemExit("Chưa có cấu hình nào")
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(os.path.join(OUT, "ket_qua.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    def stats(g):
        cs = [r["cer_min"] for r in g if r["cer_min"] is not None]
        by_seed = {s: sum(r["cer_min"] is not None and r["cer_min"] <= CER_OK for r in g if r["seed"] == s) for s in SEEDS}
        return dict(n=len(g), cer_tb=sum(cs) / len(cs) if cs else None, dat=sum(c <= CER_OK for c in cs),
                    by_seed=by_seed, tts_loi=sum(r["tts_check"] != "dat" for r in g))

    lines = ["# Kiểm tra giọng Minh Triết: kết quả tự động", "",
             f"CER nhỏ nhất qua mọi nguồn ASR có sẵn cho từng tệp (so với text_spoken và biến thể từ điển). "
             f"Ngưỡng đạt: CER ≤ {CER_OK}. Mỗi ô: số câu đạt / 8 cho seed 1 và seed 2; CER trung bình; số tệp lỗi tts_checks.", "",
             "| Cấu hình | " + " | ".join(VOICES) + " |", "|---|" + "---|" * len(VOICES)]
    for cfg, c in CFGS.items():
        cells = []
        for v in VOICES:
            g = [r for r in rows if r["cfg"] == cfg and r["voice"] == v]
            if not g:
                cells.append("–")
                continue
            s = stats(g)
            cells.append(f"{s['by_seed'][1]}/8, {s['by_seed'][2]}/8; CER {s['cer_tb']:.3f}; tts lỗi {s['tts_loi']}")
        lines.append(f"| {cfg} ({c['desc']}) | " + " | ".join(cells) + " |")
    lines += ["", f"## {TARGET} theo câu (CER nhỏ nhất, seed 1 / seed 2)", "",
              "| Câu | Nguồn | " + " | ".join(CFGS) + " |", "|---|---|" + "---|" * len(CFGS)]
    for sid in dict.fromkeys(r["sample_id"] for r in rows):
        txt = next(r["text_spoken"] for r in rows if r["sample_id"] == sid)
        src = next(r["nguon"] for r in rows if r["sample_id"] == sid)
        cells = []
        for cfg in CFGS:
            vals = [next((r["cer_min"] for r in rows if r["cfg"] == cfg and r["voice"] == TARGET and r["sample_id"] == sid
                          and r["seed"] == s), None) for s in SEEDS]
            cells.append(" / ".join("–" if v is None else f"{v:.2f}" for v in vals))
        lines.append(f"| {txt} | {src} | " + " | ".join(cells) + " |")
    with open(os.path.join(OUT, "tom_tat.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # phiếu nghe mù: đổi tên tệp ngẫu nhiên, giấu giọng và cấu hình; seed 1 ở nửa đầu để nghe được một nửa trước
    nd = os.path.join(OUT, "nghe_mu")
    os.makedirs(nd, exist_ok=True)
    rng = random.Random(20261020)
    half = [[r for r in rows if r["seed"] == s] for s in SEEDS]
    order = []
    for h in half:
        h = h[:]
        rng.shuffle(h)
        order += h
    codes = rng.sample(range(1000, 10000), len(order))
    with open(os.path.join(nd, "phieu_nghe.csv"), "w", newline="", encoding="utf-8-sig") as fp, \
            open(os.path.join(nd, "khoa_KHONG_DUA_NGUOI_NGHE.csv"), "w", newline="", encoding="utf-8-sig") as fk:
        wp, wk = csv.writer(fp), csv.writer(fk)
        wp.writerow(["stt", "tep", "cau_can_doc", "doc_dung_loi(Y/N)", "tu_doc_sai", "de_nghe(1-5)",
                     "vung_nghe_duoc(Bac/Trung/Nam/khong_ro)", "ghi_chu"])
        wk.writerow(["tep", "cfg", "voice", "seed", "sample_id", "cer_min"])
        for i, (r, code) in enumerate(zip(order, codes), 1):
            name = f"f{code}.flac"
            shutil.copyfile(os.path.join(OUT, r["audio48"]), os.path.join(nd, name))
            wp.writerow([i, name, r["text_spoken"], "", "", "", "", ""])
            wk.writerow([name, r["cfg"], r["voice"], r["seed"], r["sample_id"], r["cer_min"]])
    print(f"\nPhiếu nghe mù: {len(order)} tệp -> {nd} (dòng 1–{len(half[0])} là seed 1)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--cfg", choices=list(CFGS), required=True)
    r = sub.add_parser("report")
    r.add_argument("--lexicon", action="append", default=[])
    a = ap.parse_args()
    gen(a) if a.cmd == "gen" else report(a)


if __name__ == "__main__":
    main()
