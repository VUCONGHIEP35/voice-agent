# -*- coding: utf-8 -*-
"""pick_ref.py - cắt và xếp hạng các đoạn 3-8 giây làm giọng tham chiếu clone từ bản ghi dài.

Với mỗi tệp <cand_id>.wav (do fetch_ref.py tải, hoặc bản ghi tự thu):
  1. Tìm vùng có tiếng theo năng lượng (khung 25 ms, bước 10 ms).
  2. Ghép các vùng thành cửa sổ 3-8 s: có >= 0,2 s im lặng trước và sau (để đoạn không bắt đầu giữa âm vị,
     bài học từ lỗi "cắt đầu" của TTS), quãng nghỉ bên trong <= 0,6 s.
  3. Đo: SNR ước lượng, tỷ lệ có tiếng, cắt đỉnh, vách cắt tần số (dấu hiệu nén mạnh),
     mức nền trong các quãng nghỉ (cao = có nhạc hoặc tiếng ồn liên tục).
  4. Chấm điểm, chọn tối đa --top đoạn không chồng nhau cho mỗi ứng viên, ghi wav + phiếu nghe.

Chỉ dùng numpy, scipy, soundfile. Chạy từ tts_gen/:
  .venv/Scripts/python voice_clone/pick_ref.py voice_clone/raw --out voice_clone/clips
Ghi: <out>/<cand_id>__c<k>.wav (tần số gốc, mono) và <out>/phieu_chon_tham_chieu.csv
"""
import argparse
import csv
import glob
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR16 = 16000
FRAME, HOP = 400, 160          # 25 ms, 10 ms ở 16 kHz
MIN_S, MAX_S, TARGET_S = 3.0, 8.0, 6.0
EDGE_SIL_S = 0.2               # im lặng tối thiểu trước và sau đoạn
MAX_INNER_PAUSE_S = 0.6
PAD_S = 0.1                    # giữ lại khi cắt


def load_mono(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    return x.mean(axis=1), sr


def to16(x, sr):
    if sr == SR16:
        return x
    g = np.gcd(int(sr), SR16)
    return resample_poly(x, SR16 // g, int(sr) // g).astype(np.float32)


def frame_db(x16):
    if len(x16) < FRAME:
        return np.array([-120.0])
    n = 1 + (len(x16) - FRAME) // HOP
    idx = np.arange(FRAME)[None, :] + HOP * np.arange(n)[:, None]
    return 10 * np.log10((x16[idx].astype(np.float64) ** 2).mean(axis=1) + 1e-12)


def otsu(v, bins=64):
    h, e = np.histogram(v, bins=bins)
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h)
    w1 = w0[-1] - w0
    m0 = np.cumsum(h * c) / np.maximum(w0, 1)
    m1 = (np.sum(h * c) - np.cumsum(h * c)) / np.maximum(w1, 1)
    return c[np.argmax(w0 * w1 * (m0 - m1) ** 2)]


def speech_mask(db):
    floor = np.percentile(db, 10)
    thr = max(otsu(db), floor + 6.0)
    m = db > thr
    # lấp quãng lặng rất ngắn (< 0,15 s) và bỏ đảo tiếng rất ngắn (< 0,08 s)
    def runs(mask, val):
        out, i = [], 0
        while i < len(mask):
            if mask[i] == val:
                j = i
                while j < len(mask) and mask[j] == val:
                    j += 1
                out.append((i, j))
                i = j
            else:
                i += 1
        return out
    for a, b in runs(m, False):
        if 0 < a and b < len(m) and (b - a) < 15:
            m[a:b] = True
    for a, b in runs(m, True):
        if (b - a) < 8:
            m[a:b] = False
    return m, thr, floor


def segments(mask):
    segs, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            segs.append((i, j))
            i = j
        else:
            i += 1
    return segs  # chỉ số khung, [a, b)


def lowpass_cliff(seg, sr):
    """Vách cắt tần số (dấu hiệu nén MP3/AAC bitrate thấp hoặc ghi âm băng hẹp): tần số f trong 4-22 kHz có mức
    giảm lớn nhất giữa dải 600 Hz ngay dưới và ngay trên f. Trả (f_hz, drop_db); sr < 16 kHz hoặc đoạn quá ngắn -> (nan, nan)."""
    from scipy.signal import welch
    if sr < 16000 or len(seg) < 4096:
        return float("nan"), float("nan")
    f, p = welch(seg, fs=sr, nperseg=4096)
    db = 10 * np.log10(p + 1e-20)
    df = f[1] - f[0]
    w = int(600 / df)
    best_f, best = float("nan"), -1e9
    for i in range(int(4000 / df), min(int(22000 / df), len(f) - w - 1)):
        drop = db[i - w:i].mean() - db[i + 1:i + 1 + w].mean()
        if drop > best:
            best_f, best = float(f[i]), float(drop)
    return best_f, best


def windows(segs, n_frames):
    """Các cửa sổ (a, b) theo khung, ghép từ đoạn có tiếng liên tiếp, thỏa điều kiện biên và độ dài."""
    edge = int(EDGE_SIL_S * 100)
    inner = int(MAX_INNER_PAUSE_S * 100)
    out = []
    for i in range(len(segs)):
        a = segs[i][0]
        before = a - (segs[i - 1][1] if i > 0 else 0)
        if before < edge:
            continue
        for j in range(i, len(segs)):
            if j > i and segs[j][0] - segs[j - 1][1] > inner:
                break
            b = segs[j][1]
            dur = (b - a) / 100
            if dur > MAX_S:
                break
            after = (segs[j + 1][0] if j + 1 < len(segs) else n_frames) - b
            if dur >= MIN_S and after >= edge:
                out.append((a, b))
    return out


def analyse_file(path, meta, top):
    x, sr = load_mono(path)
    x16 = to16(x, sr)
    db = frame_db(x16)
    mask, thr, floor = speech_mask(db)
    segs = segments(mask)
    nz = db[~mask]
    noise_db = float(np.median(nz)) if len(nz) else float(np.percentile(db, 5))
    cands = []
    for a, b in windows(segs, len(db)):
        wdb, wm = db[a:b], mask[a:b]
        sp_db = 10 * np.log10(np.mean(10 ** (wdb[wm] / 10)))
        pause = wdb[~wm]
        pause_rel = float(np.mean(pause) - noise_db) if len(pause) else 0.0
        s0, s1 = int(a * HOP / SR16 * sr), int((b * HOP + FRAME) / SR16 * sr)
        seg = x[s0:s1]
        peak = float(np.max(np.abs(seg))) if len(seg) else 0.0
        clip = float(np.mean(np.abs(seg) >= 0.999)) if len(seg) else 0.0
        cliff_hz, cliff_db = lowpass_cliff(seg, sr)
        dur = (b - a) / 100
        snr = float(sp_db - noise_db)
        flags = []
        if clip > 0.001:
            flags.append("cat_dinh")
        if pause_rel > 10:
            flags.append("nen_lien_tuc")   # quãng nghỉ ồn hơn nền chung: nhạc nền hoặc tiếng ồn
        if snr < 25:
            flags.append("snr_thap")
        if cliff_db == cliff_db and cliff_db > 15 and cliff_hz < 11000:
            flags.append("bang_thong_hep")   # có vách cắt dưới 11 kHz: nén mạnh hoặc thu băng hẹp
        score = (0.5 * min(max(snr, 0), 40) / 40 + 0.2 * float(wm.mean())
                 + 0.15 * max(0.0, 1 - abs(dur - TARGET_S) / 3)
                 + 0.15 * (0.0 if "bang_thong_hep" in flags else 1.0)
                 - 0.3 * ("cat_dinh" in flags) - 0.2 * ("nen_lien_tuc" in flags))
        cands.append(dict(a=a, b=b, start_s=round(a / 100, 2), end_s=round(b / 100 + FRAME / SR16, 2),
                          dur_s=round(dur, 2), snr_db=round(snr, 1), speech_ratio=round(float(wm.mean()), 2),
                          pause_rel_db=round(pause_rel, 1), peak_dbfs=round(20 * np.log10(peak + 1e-9), 1),
                          clip_ratio=round(clip, 5),
                          cliff_hz=round(cliff_hz) if cliff_hz == cliff_hz else "",
                          cliff_db=round(cliff_db, 1) if cliff_db == cliff_db else "",
                          flags="+".join(flags), score=round(score, 3)))
    cands.sort(key=lambda c: -c["score"])
    chosen = []
    for c in cands:
        if all(c["b"] <= d["a"] or c["a"] >= d["b"] for d in chosen):
            chosen.append(c)
        if len(chosen) >= top:
            break
    return x, sr, chosen, dict(n_windows=len(cands), noise_db=round(noise_db, 1), thr_db=round(float(thr), 1),
                               dur_s=round(len(x) / sr, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir")
    ap.add_argument("--out", default="voice_clone/clips")
    ap.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    files = sorted(p for p in glob.glob(os.path.join(a.raw_dir, "*.wav")) if not p.endswith(".mono.wav"))
    if not files:
        raise SystemExit(f"Không có tệp .wav trong {a.raw_dir}")
    for p in files:
        cid = os.path.splitext(os.path.basename(p))[0]
        mp = os.path.join(a.raw_dir, f"{cid}.meta.json")
        meta = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
        x, sr, chosen, info = analyse_file(p, meta, a.top)
        print(f"{cid}: {info['dur_s']} s, {info['n_windows']} cửa sổ hợp lệ, chọn {len(chosen)}")
        for k, c in enumerate(chosen, 1):
            s0 = max(0, int((c["start_s"] - PAD_S) * sr))
            s1 = min(len(x), int((c["end_s"] + PAD_S) * sr))
            name = f"{cid}__c{k}.wav"
            sf.write(os.path.join(a.out, name), x[s0:s1], sr)
            rows.append(dict(clip=name, cand_id=cid, region=meta.get("region", ""), sub_region=meta.get("sub_region", ""),
                             gender=meta.get("gender", ""), rights=meta.get("rights", ""), sr=sr,
                             **{k2: v for k2, v in c.items() if k2 not in ("a", "b")},
                             mot_nguoi_noi_YN="", sach_YN="", dung_giong_vung_YN="", de_nghe_1_5="", chon_YN="", ghi_chu=""))
        if not chosen:
            rows.append(dict(clip="", cand_id=cid, region=meta.get("region", ""), sub_region=meta.get("sub_region", ""),
                             gender=meta.get("gender", ""), rights=meta.get("rights", ""), sr=sr,
                             flags="khong_co_cua_so_hop_le", ghi_chu=f"{info['n_windows']} cửa sổ"))
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    out_csv = os.path.join(a.out, "phieu_chon_tham_chieu.csv")
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"\n{sum(1 for r in rows if r['clip'])} đoạn -> {a.out}. Nghe và điền các cột *_YN, de_nghe_1_5, chon_YN trong {out_csv}")


if __name__ == "__main__":
    main()
