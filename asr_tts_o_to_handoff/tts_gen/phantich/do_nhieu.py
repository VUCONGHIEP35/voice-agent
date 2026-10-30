# -*- coding: utf-8 -*-
"""Đo đặc trưng các tệp nhiễu đã tải (buoc/nhieu_tai.py) và cắt đoạn nghe thử, để gán cảnh cho AISHELL-5 (tên tệp không
có mã cảnh) và tìm phiên mưa trong uncontrolled_conditions/unc_### của CAVEMOVE (không có nhãn).

Chạy trên cụm (venv_rir; nút đầu, ưu tiên thấp), từ tts_gen/:
  nice -n 19 python -m phantich.do_nhieu --nhieu ~/asr_tts_o_to/nhieu --out runs/nhieu_v1/do --workers 4
Mỗi tệp chỉ đo kênh 1 (AISHELL-5: DX01; CAVEMOVE: kênh 1, cả distributed lẫn array). Đặc trưng (mức dBFS chưa hiệu
chuẩn sang dBA, chỉ để so trong cùng bộ):
  muc_db                mức RMS cả tệp
  p10/p50/p90_db        phân vị mức theo khối 1 s; dao_dong_db = p90 − p10 (nền đổi nhiều: đổi tốc độ, xe khác vượt…)
  b20_100 … b3k_8k      mức theo dải (dB) từ phổ trung bình
  trong_tam_hz          trọng tâm phổ
  phang_300_3k          độ phẳng phổ 300 Hz–3 kHz, trung vị theo khung (nhạc: thấp hơn ồn đường)
  xung_cao_tan          tỷ lệ khung 10 ms mà năng lượng 3–8 kHz vượt 4 lần trung vị 0,5 s quanh nó (hạt mưa lộp độp)
  nhip_r, nhip_s        đỉnh tự tương quan của đường bao 20–1000 Hz ở trễ 0,4–3 s và chu kỳ (gạt nước)
AISHELL-5 thêm so_kenh (6 = có DX05/DX06, tín hiệu tham chiếu chỉ có khi dàn âm thanh bật: cảnh C, F, I, L).
Ghi <out>/aishell5.csv, cavemove.csv, nghe/aishell5/<phiên>.flac (10 s giữa phiên), nghe/cavemove_unc/<xe>_<cấu
hình>_<unc>.flac (cả tệp, kênh 1). Đoạn nghe đưa về −26 dBFS RMS (đỉnh tối đa −1 dBFS); mức gốc ở cột muc_db.
"""
import argparse
import csv
import glob
import os
from multiprocessing import Pool

import numpy as np
from scipy import signal

from thuvien.am_thanh import write_flac

SR = 16000
DAI = [(20, 100), (100, 300), (300, 1000), (1000, 3000), (3000, 8000)]


def db(x):
    return float(10 * np.log10(max(float(x), 1e-20)))


def dac_trung(x, sr=SR):
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    out = dict(dai_s=round(len(x) / sr, 2), muc_db=round(db(np.mean(x ** 2)), 2))
    k = sr
    khoi = [db(np.mean(x[i:i + k] ** 2)) for i in range(0, len(x) - k + 1, k)] or [out["muc_db"]]
    p10, p50, p90 = np.percentile(khoi, [10, 50, 90])
    out.update(p10_db=round(p10, 2), p50_db=round(p50, 2), p90_db=round(p90, 2), dao_dong_db=round(p90 - p10, 2))
    f, _, S = signal.stft(x, sr, nperseg=800, noverlap=400)
    P = np.abs(S) ** 2
    pm = P.mean(axis=1)
    for a, b in DAI:
        m = (f >= a) & (f < b)
        out[f"b{a}_{b}"] = round(db(pm[m].sum()), 2)
    out["trong_tam_hz"] = round(float((f * pm).sum() / max(pm.sum(), 1e-20)), 1)
    m = (f >= 300) & (f <= 3000)
    Pm = P[m] + 1e-20
    out["phang_300_3k"] = round(float(np.median(np.exp(np.log(Pm).mean(0)) / Pm.mean(0))), 4)
    # hạt mưa: năng lượng 3–8 kHz theo khung 10 ms so với trung vị trượt 0,5 s
    hp = signal.sosfilt(signal.butter(4, 3000, "highpass", fs=sr, output="sos"), x)
    n = int(0.01 * sr)
    e = (hp[:len(hp) // n * n].reshape(-1, n) ** 2).mean(1) + 1e-20
    tv = signal.medfilt(e, 51)
    out["xung_cao_tan"] = round(float(np.mean(e > 4 * tv)), 4)
    # nhịp chậm (gạt nước): tự tương quan đường bao 20–1000 Hz, khung 25 ms
    lp = signal.sosfilt(signal.butter(4, [20, 1000], "bandpass", fs=sr, output="sos"), x)
    n = int(0.025 * sr)
    env = np.log((lp[:len(lp) // n * n].reshape(-1, n) ** 2).mean(1) + 1e-20)
    env = env - signal.medfilt(env, 161)               # bỏ xu hướng chậm hơn 4 s
    env = env - env.mean()
    nf = 1 << int(np.ceil(np.log2(2 * len(env))))       # tự tương quan qua FFT (np.correlate là O(n²): quá chậm với 35 phút)
    a = np.fft.irfft(np.abs(np.fft.rfft(env, nf)) ** 2, nf)[:len(env)]
    a = a / max(a[0], 1e-20)
    lo, hi = int(0.4 / 0.025), min(int(3 / 0.025), len(a) - 1)
    if hi > lo:
        j = lo + int(np.argmax(a[lo:hi]))
        out.update(nhip_r=round(float(a[j]), 3), nhip_s=round(j * 0.025, 3))
    else:
        out.update(nhip_r=None, nhip_s=None)
    return out


def doc_kenh1(path):
    import soundfile as sf
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        raise SystemExit(f"{path}: {sr} Hz")
    return x[:, 0]


def doan_nghe(x, path, giua_s=None):
    if giua_s:
        i = max(0, len(x) // 2 - int(giua_s * SR / 2))
        x = x[i:i + int(giua_s * SR)]
    x = np.asarray(x, dtype=np.float64)
    r = np.sqrt(np.mean(x ** 2)) + 1e-12
    y = x * (10 ** (-26 / 20) / r)
    pk = np.max(np.abs(y))
    if pk > 10 ** (-1 / 20):
        y *= 10 ** (-1 / 20) / pk
    write_flac(path, y.astype(np.float32), SR)


def viec_aishell(task):
    phien, thu_muc, out = task
    tep = sorted(glob.glob(os.path.join(thu_muc, "*.wav")))
    x = doc_kenh1(os.path.join(thu_muc, "noise_DX01C01.wav"))
    doan_nghe(x, os.path.join(out, "nghe", "aishell5", f"{phien}.flac"), giua_s=10)
    return dict(bo="aishell5", phien=phien, so_kenh=len(tep), **dac_trung(x))


def viec_cavemove(task):
    path, goc, out = task
    rel = os.path.relpath(path, goc).replace("\\", "/")           # <xe>/<cấu hình>/<loại>/<tệp>.wav
    xe, ch, loai, ten = rel.split("/")
    x = doc_kenh1(path)
    if loai == "uncontrolled_conditions":
        doan_nghe(x, os.path.join(out, "nghe", "cavemove_unc", f"{xe}_{ch}_{ten[:-4]}.flac"))
    return dict(bo="cavemove", xe=xe, cau_hinh=ch, loai=loai, tep=ten[:-4], **dac_trung(x))


def ghi_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhieu", required=True, help="thư mục đích của buoc.nhieu_tai (có aishell5/, cavemove/)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    nh = os.path.abspath(os.path.expanduser(a.nhieu))
    for d in ("nghe/aishell5", "nghe/cavemove_unc"):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)
    ta = [(os.path.basename(d), d, a.out) for d in sorted(glob.glob(os.path.join(nh, "aishell5", "giai_nen", "noise", "*")))]
    goc = os.path.join(nh, "cavemove", "giai_nen", "cavemove_dataset")
    tc = [(p, goc, a.out) for p in sorted(glob.glob(os.path.join(goc, "*", "*", "*", "*.wav")))
          if p.replace("\\", "/").split("/")[-2] in ("noise", "ventilation", "uncontrolled_conditions")]
    print(f"AISHELL-5: {len(ta)} phiên; CAVEMOVE: {len(tc)} tệp; {a.workers} tiến trình", flush=True)
    with Pool(a.workers) as pool:
        ra = pool.map(viec_aishell, ta)
        ghi_csv(os.path.join(a.out, "aishell5.csv"), ra)
        rc = pool.map(viec_cavemove, tc, chunksize=8)
        ghi_csv(os.path.join(a.out, "cavemove.csv"), rc)
    print(f"Xong: {len(ra)} phiên AISHELL-5 ({sum(r['so_kenh'] == 6 for r in ra)} phiên 6 kênh), {len(rc)} tệp CAVEMOVE "
          f"-> {a.out}", flush=True)


if __name__ == "__main__":
    main()
