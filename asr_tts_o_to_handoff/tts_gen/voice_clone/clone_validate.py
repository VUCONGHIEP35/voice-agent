# -*- coding: utf-8 -*-
"""clone_validate.py - đăng ký giọng clone từ đoạn tham chiếu đã chọn và kiểm định trước khi đưa vào kho giọng.

Cùng cách làm với test_voice_config.py (kiểm tra Minh Triết): mỗi giọng mới đọc 8 câu của đúng vùng/tiểu vùng × 2 seed,
cùng 2 giọng có sẵn của vùng đó làm đối chứng; chấm bằng CER nhỏ nhất qua các ASR, độ giống người nói, kiểm tra kỹ thuật,
và phiếu nghe mù.

Bước (chạy từ tts_gen/, mỗi bước một tiến trình; TTS và ASR không chung tiến trình):
  1. .venv/Scripts/python voice_clone/clone_validate.py register voice_clone/approved.csv
       approved.csv: voice_id, clip, region, sub_region, gender, denoise(Y/N), cand_id, rights
       (lấy từ các dòng chon_YN = Y trong phieu_chon_tham_chieu.csv; voice_id đặt ẩn danh, vd clone_trung_hue_f01)
       -> voice_clone/voices_clone.json (embedding + mã tham chiếu, kèm vùng, giới tính, nguồn, quyền)
  2. .venv/Scripts/python voice_clone/clone_validate.py gen --batch dot1
       -> runs/clone_test/dot1/ (audio48, audio16, manifest.jsonl cùng định dạng runs/pilot100)
  3. ASR như thường lệ:
       .venv/Scripts/python asr_check.py runs/clone_test/dot1 --model vinai/PhoWhisper-large --backend ct2 --ct2-dir .cache/ct2/PhoWhisper-large-int8
       .venv/Scripts/python asr_check.py runs/clone_test/dot1 --model vinai/PhoWhisper-medium
       .venv/Scripts/python asr_diagnose.py runs/clone_test/dot1
  4. .venv/Scripts/python voice_clone/clone_validate.py report --batch dot1 --lexicon reports/text_audit_pilot100/lexicon_template.tsv
       -> runs/clone_test/dot1/ket_qua.csv, tom_tat.md, nghe_mu/
Quyết định cuối cùng chỉ sau khi có phiếu nghe mù (người bản ngữ đúng vùng).
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import random
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TTS_GEN = os.path.dirname(HERE)
os.environ.setdefault("HF_HOME", os.path.join(TTS_GEN, ".cache", "hf"))
sys.path.insert(0, TTS_GEN)

BANK = os.path.join(HERE, "voices_clone.json")
OUT_ROOT = os.path.join(TTS_GEN, "runs", "clone_test")
CONTROLS = {"Bắc": ["Hải Đăng", "Ngọc Huyền"], "Trung": ["Quang Sơn", "Ngọc Trân"], "Nam": ["Đức Trí", "Mỹ Duyên"]}
SEEDS = (1, 2)
LEN_CLASSES = ["Rất ngắn", "Ngắn", "Thường", "Dài"]
GEN = dict(use_ref_codes=True, temperature=0.8, top_k=25, batch=8)   # cấu hình A của run_pilot.py
CER_OK = 0.10


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:12]


def load_bank():
    if not os.path.exists(BANK):
        raise SystemExit(f"Chưa có {BANK}; chạy bước register trước")
    return json.load(open(BANK, encoding="utf-8"))["voices"]


# ---------------------------------------------------------------- 1. register
def register(a):
    import numpy as np
    from vieneu import Vieneu
    rows = list(csv.DictReader(open(a.approved, encoding="utf-8-sig")))
    need = ["voice_id", "clip", "region", "sub_region", "gender", "denoise", "cand_id", "rights"]
    miss = [c for c in need if rows and c not in rows[0]]
    if miss:
        raise SystemExit(f"approved.csv thiếu cột {miss}")
    bank = json.load(open(BANK, encoding="utf-8"))["voices"] if os.path.exists(BANK) else {}
    tts = Vieneu("v3turbo", max_batch_size=GEN["batch"])
    for r in rows:
        vid = r["voice_id"].strip()
        if r["region"] not in CONTROLS:
            raise SystemExit(f"{vid}: region phải là Bắc/Trung/Nam")
        clip = r["clip"] if os.path.isabs(r["clip"]) else os.path.join(TTS_GEN, r["clip"])
        den = r["denoise"].strip().upper() == "Y"
        emb, codes = tts.encode_reference(clip, denoise=den)
        bank[vid] = dict(region=r["region"], sub_region=r["sub_region"], gender=r["gender"], cand_id=r["cand_id"],
                         rights=r["rights"], denoise=den, ref_clip=os.path.relpath(clip, TTS_GEN), ref_sha1=sha1(clip),
                         registered_at=time.strftime("%Y-%m-%d %H:%M"),
                         speaker_emb=[round(float(v), 6) for v in np.asarray(emb).reshape(-1)],
                         codes=None if codes is None else np.asarray(codes).astype(int).tolist())
        n = 0 if codes is None else np.asarray(codes).shape[0]
        print(f"[đăng ký] {vid}: {r['region']}/{r['sub_region']}, {r['gender']}, {n} khung mã tham chiếu, quyền={r['rights']}")
    with open(BANK, "w", encoding="utf-8") as f:
        json.dump({"note": "giọng clone, KHÔNG công bố: chứa đặc trưng giọng người thật", "voices": bank}, f, ensure_ascii=False)
    print(f"-> {BANK} ({len(bank)} giọng)")


def voice_dict(v):
    import numpy as np
    return {"speaker_emb": np.asarray(v["speaker_emb"], dtype=np.float32),
            "codes": None if v["codes"] is None else np.asarray(v["codes"], dtype=np.int64)}


# ---------------------------------------------------------------- 2. gen
def pick_sentences(region, sub_region):
    """8 câu: 1 câu thuần Việt mỗi lớp độ dài (4) + 2 câu có từ địa phương + 2 câu có từ ngoại lai, ưu tiên đúng tiểu vùng."""
    from asr_error_mining import DIALECT_EQUIV, is_viet_syllable, norm_text
    from run_pilot import RUN_SEED, h32
    rows = [json.loads(l) for p in sorted(glob.glob(os.path.join(TTS_GEN, "..", "data", "m1m2_10k_v3", "*.jsonl")))
            for l in open(p, encoding="utf-8")]
    # câu miền Trung trong bộ v3 đều "cần duyệt", nên không lọc theo review_status; chỉ ưu tiên câu không bắt buộc duyệt
    pool = [r for r in rows if r["speaker_region"] == region]
    same = [r for r in pool if r.get("sub_region") == sub_region]
    key = lambda r: (r.get("review_status") != "không bắt buộc", h32(RUN_SEED, "clone_test", region, sub_region, r["sample_id"]))
    toks = lambda r: norm_text(r["text_spoken"]).split()
    out, used = [], set()

    def take(cands, k, tag):
        for src in (same, pool):
            for r in sorted((r for r in src if cands(r) and r["sample_id"] not in used), key=key):
                if k == 0:
                    return
                out.append(dict(r, nguon=tag))
                used.add(r["sample_id"])
                k -= 1
    for lc in LEN_CLASSES:
        take(lambda r, lc=lc: r["length_class"] == lc and all(is_viet_syllable(t) for t in toks(r)), 1, f"thuan_viet_{lc}")
    take(lambda r: any(t in DIALECT_EQUIV for t in toks(r)), 2, "tu_dia_phuong")
    take(lambda r: any(not is_viet_syllable(t) for t in toks(r)), 2, "tu_ngoai_lai")
    take(lambda r: True, 8 - len(out), "bo_sung")   # vùng ít từ địa phương/ngoại lai: bù cho đủ 8 câu
    return out


def gen(a):
    import numpy as np
    import soxr
    import torch
    import vieneu
    from vieneu import Vieneu
    from vieneu_utils.phonemize_text import normalize_to_chunks_v3_with_gaps
    import tts_checks
    from run_pilot import SR, SR16, measure, slug, write_flac

    bank = load_bank()
    if a.voices:
        bank = {k: v for k, v in bank.items() if k in a.voices}
    out = os.path.join(OUT_ROOT, a.batch)
    if os.path.exists(os.path.join(out, "manifest.jsonl")):
        raise SystemExit(f"{out} đã có manifest.jsonl; đặt --batch khác hoặc xóa thư mục")
    for d in ("audio48", "audio16"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    with open(os.path.join(os.path.dirname(vieneu.__file__), "assets", "voices_v3_turbo.json"), encoding="utf-8") as f:
        presets = json.load(f)["presets"]
    tts = Vieneu("v3turbo", max_batch_size=GEN["batch"])
    # mỗi nhóm (vùng, tiểu vùng) có giọng mới: giọng mới + 2 giọng đối chứng của vùng, cùng 8 câu
    groups = {}
    for vid, v in bank.items():
        groups.setdefault((v["region"], v["sub_region"]), []).append(vid)
    ref_emb = {vid: np.asarray(v["speaker_emb"], dtype=np.float32) for vid, v in bank.items()}
    for name in {n for ns in CONTROLS.values() for n in ns}:
        ref_emb[name] = np.asarray(presets[name]["speaker_emb"], dtype=np.float32)
    done_controls = set()
    with open(os.path.join(out, "manifest.jsonl"), "w", encoding="utf-8", newline="\n") as man:
        for (region, sub), vids in sorted(groups.items()):
            sents = pick_sentences(region, sub)
            print(f"[{region}/{sub}] {len(sents)} câu, giọng mới {vids}, đối chứng {CONTROLS[region]}")
            for voice in vids + CONTROLS[region]:
                is_clone = voice in bank
                if not is_clone and (voice, region, sub) in done_controls:
                    continue
                done_controls.add((voice, region, sub))
                vref = voice_dict(bank[voice]) if is_clone else voice
                for seed in SEEDS:
                    torch.manual_seed(seed)
                    random.seed(seed)
                    np.random.seed(seed)
                    wavs = tts.infer_batch([s["text_spoken"] for s in sents], voice=vref, apply_watermark=False,
                                           use_ref_codes=GEN["use_ref_codes"], temperature=GEN["temperature"],
                                           top_k=GEN["top_k"], batch_size=GEN["batch"])
                    for s, w in zip(sents, wavs):
                        w = np.asarray(w, dtype=np.float32)
                        q = measure(w)
                        w16 = soxr.resample(w, SR, SR16) if len(w) else w
                        why, hd = tts_checks.check(w16, s["n_syllables"], q["speech_s"], SR16)
                        utt = f"{s['sample_id']}__{slug(voice)}__{slug(sub)}__s{seed}"
                        p48, p16 = f"audio48/{utt}.flac", f"audio16/{utt}.flac"
                        write_flac(os.path.join(out, p48), w, SR)
                        write_flac(os.path.join(out, p16), w16, SR16)
                        # độ giống người nói: embedding của chính bộ mã hóa VieNeu, đầu ra so với tham chiếu
                        try:
                            e_out, _ = tts.encode_reference(os.path.join(out, p48), denoise=False)
                            e_out = np.asarray(e_out, dtype=np.float32).reshape(-1)
                            e_ref = ref_emb[voice].reshape(-1)
                            sim = float(e_out @ e_ref / (np.linalg.norm(e_out) * np.linalg.norm(e_ref) + 1e-9))
                        except Exception as ex:
                            sim = None
                            print(f"  không tính được độ giống cho {utt}: {ex}")
                        chunks, _ = normalize_to_chunks_v3_with_gaps(s["text_spoken"], max_chars=256)
                        meta = bank[voice] if is_clone else presets[voice]
                        rec = dict(utt_id=utt, sample_id=s["sample_id"], nguon=s["nguon"], test_group=f"{region}/{sub}",
                                   case_id=s["case_id"], intent_id=s["intent_id"], text_raw=s["text_raw"],
                                   text_spoken=s["text_spoken"], vieneu_text=" ".join(chunks),
                                   speaker_region=s["speaker_region"], sub_region=s["sub_region"], residence=s["residence"],
                                   length_class=s["length_class"], n_syllables=s["n_syllables"], voice=voice,
                                   voice_source="clone" if is_clone else "preset", voice_region=meta.get("region"),
                                   voice_sub_region=meta.get("sub_region", ""), voice_gender=meta.get("gender"),
                                   rights=meta.get("rights", "preset"), seed=seed, attempt=0, **q,
                                   rate_syl_per_s=round(s["n_syllables"] / q["speech_s"], 2) if q["speech_s"] else None,
                                   clipped=bool(q["peak"] >= 0.999), head_db=hd,
                                   tts_check="dat" if not why else "loi:" + "+".join(why), spk_sim=None if sim is None else round(sim, 3),
                                   review_status=s["review_status"], audio48=p48, audio16=p16)
                        man.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f"  {voice:24s} seed {seed}: xong")
    with open(os.path.join(out, "run_config.json"), "w", encoding="utf-8") as f:
        json.dump(dict(batch=a.batch, gen=GEN, seeds=SEEDS, voices=sorted(bank), controls=CONTROLS,
                       engine_dtype=str(getattr(tts.engine, "dtype", None))), f, ensure_ascii=False, indent=1)
    print(f"-> {out}")


# ---------------------------------------------------------------- 4. report
def report(a):
    import statistics as st
    from asr_check import best_cer, norm
    from asr_error_mining import load_lexicon, ref_variants
    out = os.path.join(OUT_ROOT, a.batch)
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    man = [json.loads(l) for l in open(os.path.join(out, "manifest.jsonl"), encoding="utf-8")]
    hyps = {}
    for p in sorted(glob.glob(os.path.join(out, "asr_*.jsonl"))):
        hyps[os.path.basename(p)[4:-6]] = {r["utt_id"]: r["hyp"] for r in map(json.loads, open(p, encoding="utf-8"))}
    dp = os.path.join(out, "asr_diagnose.csv")
    if os.path.exists(dp):
        for r in csv.DictReader(open(dp, encoding="utf-8-sig")):
            for k in ("c1", "c2", "c3"):
                if r.get(f"hyp_{k}"):
                    hyps.setdefault(f"diag_{k}", {})[r["utt_id"]] = r[f"hyp_{k}"]
    if not hyps:
        raise SystemExit("Chưa có kết quả ASR trong thư mục; chạy bước 3 trước")
    rows = []
    for m in man:
        vs = ref_variants(norm(m["text_spoken"]), lex)
        per = {k: round(best_cer(vs, h[m["utt_id"]])[0], 3) for k, h in hyps.items() if h.get(m["utt_id"])}
        best = min(per, key=per.get) if per else ""
        rows.append(dict(test_group=m["test_group"], voice=m["voice"], voice_source=m["voice_source"], seed=m["seed"],
                         sample_id=m["sample_id"], nguon=m["nguon"], text_spoken=m["text_spoken"], tts_check=m["tts_check"],
                         rate_syl_per_s=m["rate_syl_per_s"], spk_sim=m.get("spk_sim"),
                         cer_min=per[best] if per else None, nguon_tot_nhat=best,
                         hyp_tot_nhat=hyps[best][m["utt_id"]] if best else "",
                         **{f"cer_{k}": v for k, v in sorted(per.items())}, audio48=m["audio48"]))
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(os.path.join(out, "ket_qua.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    def stats(g):
        cs = [r["cer_min"] for r in g if r["cer_min"] is not None]
        sims = [r["spk_sim"] for r in g if r["spk_sim"] is not None]
        rates = [r["rate_syl_per_s"] for r in g if r["rate_syl_per_s"]]
        return dict(n=len(g), dat=sum(c <= CER_OK for c in cs), cer=st.mean(cs) if cs else None,
                    sim=st.median(sims) if sims else None, rate=st.median(rates) if rates else None,
                    tts_loi=sum(r["tts_check"] != "dat" for r in g))

    lines = ["# Kiểm định giọng clone: kết quả tự động", "",
             f"CER nhỏ nhất qua mọi nguồn ASR (so với text_spoken và biến thể từ điển), ngưỡng đạt {CER_OK}. "
             "Độ giống: cosine giữa embedding VieNeu của đầu ra và của tham chiếu (trung vị). "
             "Kết luận tự động chỉ là sàng lọc; quyết định cuối cùng cần phiếu nghe mù.", "",
             "| Nhóm thử | Giọng | Nguồn | Câu đạt | CER TB | Độ giống | Tốc độ (âm tiết/s) | Lỗi kỹ thuật | Sàng lọc |",
             "|---|---|---|---|---|---|---|---|---|"]
    for grp in sorted({r["test_group"] for r in rows}):
        g = [r for r in rows if r["test_group"] == grp]
        ctl = [stats([r for r in g if r["voice"] == v]) for v in sorted({r["voice"] for r in g if r["voice_source"] == "preset"})]
        ctl_cer = max([c["cer"] for c in ctl if c["cer"] is not None] or [0.0])
        ctl_sim = min([c["sim"] for c in ctl if c["sim"] is not None] or [0.0])
        for v in sorted({r["voice"] for r in g}, key=lambda v: (v not in {x["voice"] for x in g if x["voice_source"] == "clone"}, v)):
            gv = [r for r in g if r["voice"] == v]
            s = stats(gv)
            src = gv[0]["voice_source"]
            verdict = "đối chứng"
            if src == "clone":
                ok = (s["tts_loi"] == 0 and s["dat"] >= s["n"] - 2 and s["cer"] is not None
                      and s["cer"] <= max(2 * ctl_cer, 0.03) and (s["sim"] is None or s["sim"] >= ctl_sim - 0.05))
                verdict = "qua sàng lọc, chờ nghe" if ok else "trượt sàng lọc"
            fmt = lambda x, d=3: "–" if x is None else f"{x:.{d}f}"
            lines.append(f"| {grp} | {v} | {src} | {s['dat']}/{s['n']} | {fmt(s['cer'])} | {fmt(s['sim'])} | "
                         f"{fmt(s['rate'], 2)} | {s['tts_loi']} | {verdict} |")
    lines += ["", "Tiêu chí sàng lọc cho giọng clone: không có lỗi kỹ thuật; trượt tối đa 2 câu; CER TB không quá 2 lần "
              "giọng đối chứng kém hơn của cùng nhóm (tối thiểu 0,03); độ giống không thấp hơn đối chứng quá 0,05.",
              "Qua sàng lọc rồi mới đưa vào phiếu nghe mù: người bản ngữ đúng vùng xác nhận đọc đúng, dễ nghe (≥ 4/5) "
              "và nghe ra đúng vùng/tiểu vùng."]
    with open(os.path.join(out, "tom_tat.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    nd = os.path.join(out, "nghe_mu")
    os.makedirs(nd, exist_ok=True)
    rng = random.Random(20261020)
    order = rows[:]
    rng.shuffle(order)
    codes = rng.sample(range(10000, 100000), len(order))
    with open(os.path.join(nd, "phieu_nghe.csv"), "w", newline="", encoding="utf-8-sig") as fp, \
            open(os.path.join(nd, "khoa_KHONG_DUA_NGUOI_NGHE.csv"), "w", newline="", encoding="utf-8-sig") as fk:
        wp, wk = csv.writer(fp), csv.writer(fk)
        wp.writerow(["stt", "tep", "cau_can_doc", "doc_dung_loi(Y/N)", "tu_doc_sai", "de_nghe(1-5)",
                     "vung_nghe_duoc(Bac/Trung/Nam/khong_ro)", "tieu_vung_nghe_duoc", "ghi_chu"])
        wk.writerow(["tep", "test_group", "voice", "voice_source", "seed", "sample_id", "cer_min", "spk_sim"])
        for i, (r, code) in enumerate(zip(order, codes), 1):
            name = f"f{code}.flac"
            shutil.copyfile(os.path.join(out, r["audio48"]), os.path.join(nd, name))
            wp.writerow([i, name, r["text_spoken"], "", "", "", "", "", ""])
            wk.writerow([name, r["test_group"], r["voice"], r["voice_source"], r["seed"], r["sample_id"], r["cer_min"], r["spk_sim"]])
    print(f"\nPhiếu nghe mù: {len(order)} tệp -> {nd}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("approved")
    g = sub.add_parser("gen")
    g.add_argument("--batch", required=True)
    g.add_argument("--voices", nargs="*", help="chỉ thử các voice_id này")
    p = sub.add_parser("report")
    p.add_argument("--batch", required=True)
    p.add_argument("--lexicon", action="append", default=[])
    a = ap.parse_args()
    {"register": register, "gen": gen, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
