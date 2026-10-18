# SNR_PROBE: đo độ sạch âm học của đoạn giọng tham chiếu (chạy trên Google Colab)

Tệp này đặt cạnh thư mục sinh dữ liệu văn bản (ví dụ `docs/`). Nó **không sinh văn bản và không sửa dữ liệu v3**; nó chỉ đo âm thanh giọng tham chiếu (ví dụ ViSpeech) để quyết định đoạn nào đủ sạch dùng làm tham chiếu clone TTS. Nguyên tắc của dự án: tham chiếu clone phải sạch, nhiễu và vang chỉ thêm sau khi sinh.

## 1. Trạng thái và những gì đã kiểm

- Mã dưới đây đã chạy thử **trên âm thanh tổng hợp giống lời nói** trong môi trường của Claude (Python 3.13, numpy, scipy, soundfile, librosa, speechmos). Chưa chạy trên Google Colab và chưa chạy trên ViSpeech thật.
- Hai bộ ước lượng SNR tự định nghĩa, không dùng bảng WADA-SNR, vì bảng đó không kiểm chứng được. Chúng là **ước lượng**, lệch vài dB, nên bắt buộc hiệu chuẩn (mục 4, bước C) trước khi dùng ngưỡng 25 dB.
- Kết quả thử trên âm thanh tổng hợp (4 đoạn 8 giây, 44,1 kHz, nhiễu trắng và nhiễu hồng; chỉ chứng minh mã chạy đúng, không nói gì về ViSpeech):

| SNR thật (dB) | 10 | 15 | 20 | 25 | 30 | 35 | 40 |
|---|---|---|---|---|---|---|---|
| `snr_vad` đo được | 12,4 | 16,8 | 21,2 | 25,6 | 30,0 | 34,4 | 39,0 |
| `snr_floor` đo được | 12,3 | 16,3 | 20,3 | 24,2 | 28,1 | 31,8 | 35,3 |

- Dò "vạch cắt tần số" của MP3 trên tín hiệu tổng hợp có dải rộng: WAV gốc 0,5 dB (không có vạch), MP3 32 kbps cắt ở khoảng 8,3 kHz (14,6 dB), 64 kbps ở 16,5 kHz (13,6 dB), 128 kbps ở 20,1 kHz (16,4 dB). Quy ước: `cliff_db` lớn hơn 10 là có cắt tần số; dưới 16 kHz là đáng lo.
- Chỉ số `tail_drop_db` (độ tắt năng lượng sau khi hết tiếng) phân biệt được đoạn có vang (15 dB) với đoạn không vang (50 dB) trên tín hiệu tổng hợp. DNSMOS **không có ý nghĩa** trên tín hiệu tổng hợp; chỉ dùng trên lời nói thật.

## 2. Đo cái gì

| Cột | Ý nghĩa | Ghi chú |
|---|---|---|
| `snr_vad` | Năng lượng khung có tiếng so với sàn nhiễu ở khung nghỉ (dB) | Kém tin cậy nếu `low_conf` là True (clip không có quãng nghỉ) |
| `snr_floor` | SNR tính từ sàn phổ theo từng tần số (phân vị 10%) | Giả định nhiễu dừng; nhạy với clip quá ngắn |
| `cliff_hz`, `cliff_db` | Vạch cắt tần số do MP3 bitrate thấp | Chỉ tính khi tần số lấy mẫu từ 24 kHz |
| `clip_ratio` | Tỉ lệ mẫu chạm đỉnh | Lớn hơn 0,001 là đáng ngờ |
| `tail_drop_db` | Độ tắt 100 ms đầu sau khi hết tiếng | Nhỏ là nghi vang hoặc nhiễu nền; NaN nếu không có quãng nghỉ ≥ 150 ms |
| `ovrl_mos`, `sig_mos`, `bak_mos` | DNSMOS (cần `speechmos`) | Chưa có ngưỡng đã xác lập; chỉ xếp hạng và nghe thử |
| `pause_frac`, `dur_s`, `sr` | Mô tả clip | |

**SNR ở đây được đo trong dải 0–8 kHz** (sau khi hạ về 16 kHz), nên nhiễu trắng trải đến 22 kHz sẽ cho SNR cao hơn số tính trên toàn dải khoảng 4 dB. Khi so với ngưỡng 25 dB của dự án, hiệu chuẩn bằng cùng cách định nghĩa này.

## 3. Chuẩn bị dữ liệu mẫu nhỏ

1. Lấy một mẫu nhỏ ViSpeech theo hướng dẫn trên [GitHub](https://github.com/TranNguyenNB/ViSpeech) (tải từ Google Drive của họ). Kiểm giấy phép trước khi dùng cho mục đích khác ngoài thử nghiệm nội bộ; trang không nêu giấy phép.
2. Lấy khoảng **50 clip mỗi vùng**, trải qua nhiều người nói khác nhau (không lấy 50 clip của cùng một người). Ghi lại tên người nói nếu có trong `metadata`.
3. Đặt theo cấu trúc, tên thư mục là nhãn vùng:

```
samples/
  bac/    *.mp3
  trung/  *.mp3
  nam/    *.mp3
clean_ref/   # 10-20 clip chắc chắn sạch, dùng để hiệu chuẩn (xem bước C)
```

4. `clean_ref/`: ưu tiên bản ghi của chính dự án (phòng yên tĩnh, micro tốt) hoặc VIVOS (quy ước đọc câu, thu trong phòng yên tĩnh; chưa thử tải từ Colab). Không dùng clip YouTube chưa kiểm tra làm tham chiếu sạch.

## 4. Các ô chạy trên Colab (chạy theo thứ tự)

### Bước A: cài đặt và ghi mã

```python
!pip -q install soundfile librosa speechmos pandas matplotlib
```

```python
%%writefile snr_probe.py
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

```

### Bước B: kiểm tra môi trường bằng dữ liệu tổng hợp (không cần dữ liệu thật)

Ô này sinh vài đoạn giả lập lời nói, thêm nhiễu ở SNR đã biết và in kết quả. Nếu số đo không tăng theo SNR thật thì môi trường có vấn đề, dừng lại.

```python
import numpy as np, soundfile as sf, os
from scipy import signal
import snr_probe as sp

import numpy as np, soundfile as sf
from scipy import signal
def synth(seed, sr=44100, dur=8.0):
    rng=np.random.default_rng(seed)
    n=int(sr*dur); t=np.arange(n)/sr
    f0=110+25*rng.random()+12*np.sin(2*np.pi*(0.3+0.2*rng.random())*t)
    ph=2*np.pi*np.cumsum(f0)/sr
    src=np.zeros(n)
    for h in range(1,40): src+=np.sin(h*ph)/h**1.1
    out=np.zeros(n)
    # syllables of ~180ms with different formants; pauses
    i=0; 
    while i<n:
        L=int(sr*(0.12+0.15*rng.random()))
        seg=slice(i,min(n,i+L))
        F=[400+500*rng.random(),1100+1300*rng.random(),2500+300*rng.random()]
        y=np.zeros(len(src[seg]))
        for fc in F:
            b,a=signal.butter(2,[max(fc-120,50)/(sr/2),(fc+120)/(sr/2)],'band')
            y+=signal.lfilter(b,a,src[seg])
        env=np.hanning(len(y))**0.7
        out[seg]=y*env*(0.5+rng.random())
        i+=L
        if rng.random()<0.22:   # pause
            i+=int(sr*(0.15+0.3*rng.random()))
            out[max(0,i-1):i]=0
    # zero-out pauses already as zeros (skip leaves zeros)
    out/=np.max(np.abs(out)); out*=0.5
    out+=1e-4*rng.standard_normal(n)  # very low floor
    return out.astype(np.float32), sr

os.makedirs("selftest", exist_ok=True)
for s in range(3):
    x, sr = synth(s); sf.write(f"selftest/c{s}.wav", x, sr)
df, fits = sp.calibrate([f"selftest/c{s}.wav" for s in range(3)])
print(df.groupby("snr_true")[["snr_vad","snr_floor"]].mean().round(1))
```

### Bước C: hiệu chuẩn bằng clip sạch thật

```python
import glob, pandas as pd
clean = sp.scan("clean_ref")
assert len(clean) >= 10, "Can it nhat 10 clip sach de hieu chuan"
cal, fits = sp.calibrate(clean)
print(cal.groupby("snr_true")[["snr_vad","snr_floor"]].mean().round(1))
thr = sp.threshold_in_estimator_units(fits, 25.0)
print("Nguong 25 dB tuong ung:", {k: round(v,1) for k,v in thr.items()})
```

Đọc kết quả: nếu hệ số góc (trong `fits`) lệch xa 1 (dưới 0,6 chẳng hạn), bộ ước lượng nén mạnh và ngưỡng suy ra kém tin cậy; ghi rõ trong báo cáo.

### Bước D: đo mẫu ViSpeech

```python
rows = []
for p in sp.scan("samples"):
    r = sp.analyse(p)
    r["region"] = os.path.basename(os.path.dirname(p))
    rows.append(r)
df = pd.DataFrame(rows)
df["pass_snr"] = (df.snr_vad >= thr["snr_vad"]) & (df.snr_floor >= thr["snr_floor"])
df["lowpass_flag"] = (df.cliff_db > 10) & (df.cliff_hz < 16000)
df["clip_flag"] = df.clip_ratio > 0.001
df["pass_all"] = df.pass_snr & ~df.lowpass_flag & ~df.clip_flag & ~df.low_conf
df.to_csv("snr_probe_result.csv", index=False)
print(df.groupby("region").agg(n=("file","count"), pass_snr=("pass_snr","mean"),
      pass_all=("pass_all","mean"), snr_vad_med=("snr_vad","median"),
      snr_floor_med=("snr_floor","median"), lowpass=("lowpass_flag","mean")).round(2))
```

### Bước E: nghe thử và vẽ phân phối

```python
import matplotlib.pyplot as plt
from IPython.display import Audio, display
fig, ax = plt.subplots(1, 3, figsize=(13, 3.5), sharey=True)
for a, (rg, g) in zip(ax, df.groupby("region")):
    a.hist(g.snr_vad, bins=15); a.axvline(thr["snr_vad"], color="r"); a.set_title(rg)
plt.show()
# 5 clip sat nguong va 5 clip bi loai de nghe: xac nhan nguong hop ly
near = df.assign(d=(df.snr_vad - thr["snr_vad"]).abs()).nsmallest(5, "d")
bad = df[~df.pass_all].nsmallest(5, "snr_vad")
for _, r in pd.concat([near, bad]).iterrows():
    print(r.region, r.snr_vad, r.snr_floor, r.cliff_hz); display(Audio(r.file))
```

## 5. Cách quyết định sau khi đo

1. **Ngưỡng:** một clip đạt khi cả hai bộ ước lượng đạt ngưỡng đã hiệu chuẩn tương ứng 25 dB, không có cắt tần số dưới 16 kHz, không cắt đỉnh, và không `low_conf`. Nghe thử các clip sát ngưỡng để xác nhận.
2. **Tỉ lệ đạt theo vùng** quyết định có đủ giọng không. Khi tỉ lệ đạt cao, lọc toàn bộ ViSpeech rồi chọn 20 người nói mỗi vùng có nhiều clip đạt nhất. Khi tỉ lệ đạt thấp, ghi âm bổ sung hoặc lấy nguồn khác (xem tài liệu khảo sát nguồn giọng).
3. **Đo theo người nói**, không chỉ theo clip: một người nói chỉ được chọn nếu có ít nhất 3 clip đạt (khoảng 3–8 giây, dùng làm tham chiếu).
4. **Không kết luận từ một số liệu.** SNR không bắt được hết vang phòng, tiếng nói chồng và nén MP3. Luôn kèm nghe thử.

## 6. Giới hạn

- Hai bộ ước lượng SNR có thể lệch vài dB so với giá trị thật và lệch khác nhau tùy loại nhiễu; vì vậy phải hiệu chuẩn bằng clip sạch và cùng định nghĩa.
- Clip dưới 2 giây hoặc không có quãng nghỉ cho kết quả kém tin cậy (`low_conf`).
- Hiệu chuẩn thêm nhiễu trắng và nhiễu hồng nhân tạo, không phải nhiễu thật của video YouTube (tiếng quạt, tiếng nhạc nền, vang phòng). Số đo trên clip thật có thể khác.
- `tail_drop_db` chỉ là chỉ số gần đúng cho vang. DNSMOS được huấn luyện cho tiếng Anh; dùng để xếp hạng, không dùng làm ngưỡng.
- Mã chưa chạy trên Colab và chưa chạy trên ViSpeech thật. Kết quả đầu tiên cần được xem là thử nghiệm, và cần người kiểm tra bằng tai.

## 7. Đầu ra mong đợi

`snr_probe_result.csv` gồm: `file, sr, dur_s, snr_vad, snr_floor, pause_frac, low_conf, cliff_hz, cliff_db, clip_ratio, tail_drop_db, rms_dbfs, ovrl_mos, sig_mos, bak_mos, region, pass_snr, lowpass_flag, clip_flag, pass_all`. Gửi lại tệp này cùng bảng tổng hợp của bước D để cập nhật điểm "sạch" trong tài liệu khảo sát.
