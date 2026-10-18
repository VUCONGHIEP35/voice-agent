"""snr_probe.py - do do sach am hoc cua doan giong tham chieu (khong can tin hieu sach).

Phu thuoc: numpy, scipy, soundfile (mp3 can libsndfile >= 1.1; neu khong doc duoc thi dung ffmpeg).
Tuy chon: speechmos (DNSMOS). Moi ham la mot uoc luong, KHONG phai SNR that.
"""
import glob
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy import signal

SR = 16000          # tan so de uoc luong SNR
FRAME = 400         # 25 ms
HOP = 160           # 10 ms
EPS = 1e-12


# ---------- doc am thanh ----------
def load_audio(path):
    """Tra ve (x_native mono float32, sr_native). Doc mp3/wav/flac; thieu thi goi ffmpeg."""
    try:
        x, sr = sf.read(path, dtype="float32", always_2d=True)
    except Exception:
        with tempfile.TemporaryDirectory() as d:
            wav = os.path.join(d, "t.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, wav], check=True)
            x, sr = sf.read(wav, dtype="float32", always_2d=True)
    return x.mean(axis=1), sr


def to_16k(x, sr):
    if sr == SR:
        return x
    g = np.gcd(int(sr), SR)
    return signal.resample_poly(x, SR // g, int(sr) // g).astype(np.float32)


# ---------- khung nang luong va VAD ----------
def frame_power(x):
    n = 1 + max(0, (len(x) - FRAME) // HOP)
    idx = np.arange(FRAME)[None, :] + HOP * np.arange(n)[:, None]
    f = x[idx] if len(x) >= FRAME else np.pad(x, (0, FRAME - len(x)))[None, :]
    return (f.astype(np.float64) ** 2).mean(axis=1)


def otsu_threshold(v, bins=64):
    h, e = np.histogram(v, bins=bins)
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h)
    w1 = w0[-1] - w0
    m0 = np.cumsum(h * c) / np.maximum(w0, 1)
    m1 = (np.sum(h * c) - np.cumsum(h * c)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return c[np.argmax(between)]


def vad_snr(x16):
    """SNR (dB) = nang luong khung co tieng tru san nhieu / san nhieu (khung nghi).
    Tra ve (snr_db, ty_le_khung_nghi, tin_cay_thap)."""
    e = frame_power(x16)
    le = 10 * np.log10(e + EPS)
    thr = otsu_threshold(le)
    speech = le > thr
    low_conf = False
    if (~speech).mean() < 0.10 or speech.sum() < 5:
        # clip khong co quang nghi ro: lay 10% khung yeu nhat lam nhieu
        k = max(3, int(0.10 * len(e)))
        order = np.argsort(e)
        noise_idx = order[:k]
        speech = np.ones_like(speech, dtype=bool)
        speech[noise_idx] = False
        low_conf = True
    # san nhieu = 50% khung yeu nhat trong so khung nghi (tranh lan khung tieng nho/dau-cuoi am tiet)
    ns = np.where(~speech)[0]
    ns = ns[np.argsort(e[ns])[: max(3, len(ns) // 2)]]
    pn = e[ns].mean()
    ps = e[speech].mean()
    snr = 10 * np.log10(max(ps - pn, 1e-3 * pn) / (pn + EPS))
    return float(snr), float((~speech).mean()), low_conf


def floor_snr(x16, p=0.10):
    """SNR (dB) tu san pho: moi bin tan so lay phan vi p cua cong suat theo thoi gian,
    chia cho -ln(1-p) (gia dinh nhieu dung, cong suat bin phan phoi mu). Dung khi clip co quang nghi."""
    f, t, z = signal.stft(x16, fs=SR, nperseg=512, noverlap=512 - HOP, window="hann")
    pw = np.abs(z) ** 2
    band = (f >= 100) & (f <= 7500)
    pw = pw[band]
    noise_bin = np.percentile(pw, 100 * p, axis=1) / (-np.log(1 - p))
    noise_total = noise_bin.sum()
    tot = pw.sum(axis=0)
    thr = otsu_threshold(10 * np.log10(tot + EPS))
    act = 10 * np.log10(tot + EPS) > thr
    if act.sum() < 3:
        act = np.ones_like(act, dtype=bool)
    sig = tot[act].mean()
    return float(10 * np.log10(max(sig - noise_total, 1e-3 * noise_total) / (noise_total + EPS)))


# ---------- chi so khac ----------
def lowpass_cliff(x, sr):
    """Tim 'vach' cat tan so (dau hieu MP3 bitrate thap): tan so f (8-21 kHz) co muc giam lon nhat
    giua dai 600 Hz ngay duoi f va dai 600 Hz ngay tren f. Tra ve (f_hz, drop_db); sr < 24 kHz -> (nan, nan)."""
    if sr < 24000:
        return float("nan"), float("nan")
    f, pxx = signal.welch(x, fs=sr, nperseg=4096)
    db = 10 * np.log10(pxx + EPS)
    df = f[1] - f[0]
    w = int(600 / df)
    best_f, best_drop = float("nan"), -1e9
    for i in range(int(8000 / df), min(int(21000 / df), len(f) - w - 1)):
        drop = db[i - w:i].mean() - db[i + 1:i + 1 + w].mean()
        if drop > best_drop:
            best_f, best_drop = float(f[i]), float(drop)
    return best_f, best_drop


def clipping_ratio(x):
    peak = np.max(np.abs(x)) + EPS
    return float(np.mean(np.abs(x) >= 0.999 * peak) if peak >= 0.99 else 0.0)


def tail_drop_db(x16, pause_ms=150):
    """Do tat nang luong 100 ms dau sau khi het tieng (dB). Nho = nghi co vang hoac nhieu nen.
    Chi la chi so gan dung; tra ve nan neu khong co quang nghi du dai."""
    e = frame_power(x16)
    le = 10 * np.log10(e + EPS)
    sp = le > otsu_threshold(le)
    need = pause_ms // 10
    drops = []
    for i in range(5, len(sp) - need - 12):
        if sp[i - 1] and not sp[i] and not sp[i:i + need].any():
            before = le[i - 5:i].mean()
            after = le[i + 8:i + 12].mean()
            drops.append(before - after)
    return float(np.median(drops)) if drops else float("nan")


def dnsmos_scores(x16):
    try:
        from speechmos import dnsmos
        r = dnsmos.run(np.clip(x16, -1.0, 1.0).astype(np.float32), SR)
        return {k: float(r[k]) for k in ("ovrl_mos", "sig_mos", "bak_mos")}
    except Exception as ex:  # chua cai hoac loi
        return {"ovrl_mos": np.nan, "sig_mos": np.nan, "bak_mos": np.nan}


def analyse(path, use_dnsmos=True):
    x, sr = load_audio(path)
    x16 = to_16k(x, sr)
    snr_v, pause_frac, low = vad_snr(x16)
    cliff = lowpass_cliff(x, sr)
    out = {
        "file": path,
        "sr": sr,
        "dur_s": round(len(x) / sr, 2),
        "snr_vad": round(snr_v, 1),
        "snr_floor": round(floor_snr(x16), 1),
        "pause_frac": round(pause_frac, 2),
        "low_conf": low,
        "cliff_hz": round(cliff[0]) if cliff[0] == cliff[0] else float("nan"),
        "cliff_db": round(cliff[1], 1) if cliff[1] == cliff[1] else float("nan"),
        "clip_ratio": round(clipping_ratio(x), 5),
        "tail_drop_db": round(tail_drop_db(x16), 1),
        "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(x ** 2)) + EPS), 1),
    }
    if use_dnsmos:
        out.update({k: round(v, 2) for k, v in dnsmos_scores(x16).items()})
    return out


# ---------- hieu chuan ----------
def add_noise(clean16, snr_db, kind="white", rng=None):
    """Tron nhieu o SNR da biet. SNR dinh nghia theo cong suat trung binh cac khung co tieng cua clip sach."""
    rng = rng or np.random.default_rng(0)
    e = frame_power(clean16)
    le = 10 * np.log10(e + EPS)
    act = le > otsu_threshold(le)
    p_sig = e[act].mean()
    n = rng.standard_normal(len(clean16))
    if kind == "pink":
        spec = np.fft.rfft(n)
        spec /= np.sqrt(np.maximum(np.arange(len(spec)), 1))
        n = np.fft.irfft(spec, len(clean16))
    n = n / (np.sqrt(np.mean(n ** 2)) + EPS) * np.sqrt(p_sig / (10 ** (snr_db / 10)))
    return (clean16 + n).astype(np.float32)


def calibrate(clean_paths, levels=(10, 15, 20, 25, 30, 35, 40), kinds=("white", "pink")):
    """Tra ve (bang uoc luong theo SNR that, he so hoi quy est = a * that + b cho moi bo uoc luong)."""
    import pandas as pd
    rows = []
    for p in clean_paths:
        x, sr = load_audio(p)
        c = to_16k(x, sr)
        for k in kinds:
            for s in levels:
                y = add_noise(c, s, k)
                rows.append({"file": os.path.basename(p), "noise": k, "snr_true": s,
                             "snr_vad": vad_snr(y)[0], "snr_floor": floor_snr(y)})
    df = pd.DataFrame(rows)
    fits = {}
    for col in ("snr_vad", "snr_floor"):
        a, b = np.polyfit(df["snr_true"], df[col], 1)
        fits[col] = (float(a), float(b))
    return df, fits


def threshold_in_estimator_units(fits, snr_true_target=25.0):
    """Doi nguong 'SNR that' sang gia tri do duoc cua tung bo uoc luong."""
    return {k: a * snr_true_target + b for k, (a, b) in fits.items()}


def scan(folder, exts=("wav", "mp3", "flac", "ogg", "m4a")):
    files = []
    for e in exts:
        files += glob.glob(os.path.join(folder, "**", f"*.{e}"), recursive=True)
    return sorted(files)

