# -*- coding: utf-8 -*-
"""Đo RIR và chập RIR vào tiếng nói sạch (bước RIR, docs/ke_hoach_RIR_v1.md). Chỉ numpy/scipy, không có CLI.

Đo trên RIR (chỉ số mẫu `i` là đỉnh đường trực tiếp):
  edt / t20     Schroeder ngược; EDT = 6 × thời gian 0 → −10 dB, T20 = 3 × thời gian −5 → −25 dB (khớp bình phương tối thiểu)
  edt_bang      EDT theo dải octave (cauhinh.tang_cuong.EDT_BANG); edt_tb = trung bình các dải, là số dùng làm ngưỡng
  drr           năng lượng ±DRR_CUA_MS quanh đỉnh trực tiếp so với phần sau (chỉ ghi)
  c50           năng lượng 50 ms đầu (tính từ đỉnh trực tiếp) so với phần sau
  tim_truc_tiep đỉnh trực tiếp = |h| lớn nhất trong ±1 ms quanh vị trí tính từ hình học. Không lấy argmax cả RIR: ở
                micro xa, phản xạ đối xứng cộng dồn có thể cao hơn đường trực tiếp.
Chập (xu_ly_ban): mức giọng hoạt động về MUC_GIONG_DBFS đo trên mặt nạ có tiếng của bản sạch, chập FFT, bỏ các mẫu
trước đỉnh trực tiếp (bản vang thẳng hàng với bản sạch), giữ tối đa DUOI_S giây đuôi, khôi phục mức, chống cắt đỉnh.
Bản không có RIR chỉ qua bước mức và chống cắt đỉnh, cùng định dạng.
"""
import numpy as np
from scipy import signal

from cauhinh.tang_cuong import (DINH_MAX_DBFS, DRR_CUA_MS, DUOI_S, EDT_BANG, MUC_GIONG_DBFS, SR,
                                TRUOC_DINH_MAX)

KHUNG_MS, BUOC_MS = 20, 10
NGUONG_TIENG_DB = 40.0          # khung có tiếng: trong 40 dB dưới khung mạnh nhất
SAN_TIENG_DBFS = -70.0          # và trên −70 dBFS
TRE_PHAN_SO = 40                # nửa độ dài bộ lọc trễ phân số của pyroomacoustics (81 // 2): biên trước đỉnh


def _db(x):
    return 10 * np.log10(np.maximum(x, 1e-300))


def schroeder_db(h):
    e = np.cumsum((np.asarray(h, dtype=np.float64) ** 2)[::-1])[::-1]
    return _db(e / e[0]) if e[0] > 0 else np.full(len(e), -300.0)


def _doc(d, hi, lo, sr):
    """Khớp đường thẳng trên đoạn EDC từ hi xuống lo dB; trả thời gian tắt 60 dB (giây), không đủ điểm thì nan."""
    k = np.nonzero((d <= hi) & (d >= lo))[0]
    if len(k) < 3:
        return float("nan")
    k = np.arange(k[0], k[-1] + 1)
    p = np.polyfit(k / sr, d[k], 1)
    return float(-60.0 / p[0]) if p[0] < 0 else float("nan")


def edt(h, i=0, sr=SR):
    return _doc(schroeder_db(h[i:]), 0.0, -10.0, sr)


def t20(h, i=0, sr=SR):
    return _doc(schroeder_db(h[i:]), -5.0, -25.0, sr)


def edt_bang(h, i=0, sr=SR, bang=EDT_BANG):
    """{tần số giữa: EDT} theo dải octave (Butterworth bậc 4, lọc nhân quả, cận trên giữ dưới Nyquist)."""
    out = {}
    for fc in bang:
        hi = min(fc * 2 ** 0.5, 0.49 * sr)
        sos = signal.butter(4, [fc / 2 ** 0.5, hi], btype="band", fs=sr, output="sos")
        out[fc] = edt(signal.sosfilt(sos, np.asarray(h, dtype=np.float64)), i, sr)
    return out


def drr(h, i, sr=SR, cua_ms=DRR_CUA_MS):
    w = int(round(cua_ms * sr / 1000))
    h2 = np.asarray(h, dtype=np.float64) ** 2
    return float(_db(h2[max(i - w, 0):i + w + 1].sum()) - _db(h2[i + w + 1:].sum()))


def c50(h, i, sr=SR):
    n = i + int(0.05 * sr)
    h2 = np.asarray(h, dtype=np.float64) ** 2
    return float(_db(h2[i:n].sum()) - _db(h2[n:].sum()))


def tim_truc_tiep(h, tre_ky_vong, sr=SR, cua_ms=1.0):
    """Chỉ số đỉnh trực tiếp: |h| lớn nhất trong ±cua_ms quanh tre_ky_vong (mẫu, số thực)."""
    w = int(round(cua_ms * sr / 1000))
    a = max(int(np.floor(tre_ky_vong)) - w, 0)
    b = min(int(np.ceil(tre_ky_vong)) + w + 1, len(h))
    return a + int(np.argmax(np.abs(h[a:b])))


def loi_hinh_dang(h, i, sr=SR):
    """Danh sách lỗi hình dạng: khong_huu_han, truoc_dinh (đỉnh lạ trước đường trực tiếp), duoi_khong_tat. Rỗng là đạt."""
    h = np.asarray(h, dtype=np.float64)
    if not np.all(np.isfinite(h)):
        return ["khong_huu_han"]
    loi = []
    truoc = np.abs(h[:max(i - TRE_PHAN_SO, 0)])
    if h[i] == 0 or (len(truoc) and truoc.max() > TRUOC_DINH_MAX * abs(h[i])):
        loi.append("truoc_dinh")
    n = int(0.025 * sr)
    dau, cuoi = (h[i:i + n] ** 2).sum(), (h[-n:] ** 2).sum()
    if len(h) - i < 4 * n or _db(cuoi) > _db(dau) - 30:
        loi.append("duoi_khong_tat")
    return loi


def do_rir(h, i, sr=SR):
    """Mọi chỉ số ghi vào rir_manifest (đỉnh trực tiếp i đã biết)."""
    b = edt_bang(h, i, sr)
    vals = [v for v in b.values() if np.isfinite(v)]
    return dict(edt_s=round(float(np.mean(vals)), 4) if vals else None,
                edt_bang={str(k): (round(v, 4) if np.isfinite(v) else None) for k, v in b.items()},
                edt_rong_s=_r(edt(h, i, sr)), t20_s=_r(t20(h, i, sr)), drr_db=round(drr(h, i, sr), 2),
                c50_db=round(c50(h, i, sr), 2))


def _r(v):
    return round(v, 4) if np.isfinite(v) else None


def mat_na_tieng(x, sr=SR):
    """Mặt nạ theo mẫu: True ở khung có tiếng (kiểu VAD năng lượng đơn giản, gần P.56)."""
    x = np.asarray(x, dtype=np.float64)
    n, s = int(sr * KHUNG_MS / 1000), int(sr * BUOC_MS / 1000)
    m = np.zeros(len(x), dtype=bool)
    if len(x) < n:
        m[:] = True
        return m
    starts = np.arange(0, len(x) - n + 1, s)
    e = np.array([np.mean(x[a:a + n] ** 2) for a in starts])
    db = _db(e)
    on = (db > db.max() - NGUONG_TIENG_DB) & (db > SAN_TIENG_DBFS)
    for a in starts[on]:
        m[a:a + n] = True
    return m


def muc_db(x, mask):
    x = np.asarray(x, dtype=np.float64)
    mask = mask[:len(x)] if len(mask) >= len(x) else np.pad(mask, (0, len(x) - len(mask)))
    p = np.mean(x[mask] ** 2) if mask.any() else np.mean(x ** 2)
    return float(_db(p))


def chap(x, h, i, sr=SR, duoi_s=DUOI_S):
    """Chập FFT, bỏ i mẫu đầu (trước đỉnh trực tiếp), dài ra = len(x) + tối đa duoi_s giây."""
    from scipy.signal import fftconvolve
    y = fftconvolve(np.asarray(x, dtype=np.float64), np.asarray(h, dtype=np.float64))
    return y[i:i + len(x) + int(round(duoi_s * sr))]


def xu_ly_ban(x, h=None, i=0, sr=SR):
    """Một bản trộn: trả (y float32, thông tin). h None = không RIR (chỉ chỉnh mức, chống cắt đỉnh)."""
    x = np.asarray(x, dtype=np.float64)
    mask = mat_na_tieng(x, sr)
    muc_sach = muc_db(x, mask)
    y = x if h is None else chap(x, h, i, sr)
    g = MUC_GIONG_DBFS - muc_db(y, mask)
    y = y * 10 ** (g / 20)
    dinh = float(np.max(np.abs(y))) if len(y) else 0.0
    ha = 0.0
    lim = 10 ** (DINH_MAX_DBFS / 20)
    if dinh > lim:
        ha = 20 * np.log10(lim / dinh)
        y = y * (lim / dinh)
    return y.astype(np.float32), dict(muc_sach_dbfs=round(muc_sach, 2), he_so_muc_db=round(g, 2),
                                      ha_chong_cat_db=round(ha, 2), muc_ra_dbfs=round(muc_db(y, mask), 2),
                                      dinh_ra_dbfs=round(float(_db(np.max(np.abs(y)) ** 2)), 2) if len(y) else None,
                                      tre_bo_mau=int(i) if h is not None else 0, dai_s=round(len(y) / sr, 3))


def lech_tre_ms(x, y, sr=SR, max_ms=20.0, nguong=0.5):
    """Độ trễ (ms) của y so với x: giải chập Wiener ra RIR ước lượng trong ±max_ms, lấy đường đến ĐẦU TIÊN đạt
    ≥ nguong × đỉnh. Dương: y trễ hơn x.
    Không lấy đỉnh lớn nhất: trong khoang xe DRR thường âm và phản xạ cộng dồn có thể mạnh hơn đường trực tiếp. Đo
    27/10 trên 400 bản phiếu nghe của cụm: tương quan chéo thường lệch tới 20 ms (56% bản dưới 2 ms); GCC-PHAT (đỉnh
    lớn nhất) 93,5% dưới 2 ms, các bản lệch trùng vị trí phản xạ mạnh nhất của RIR; cách này: mọi bản trong −0,25…1,12 ms."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)[:len(x)]
    n = len(x) + len(y)
    X, Y = np.fft.rfft(x, n), np.fft.rfft(y, n)
    p = np.abs(X) ** 2
    h = np.abs(np.fft.irfft(Y * np.conj(X) / (p + 1e-3 * p.mean()), n))
    w = int(max_ms * sr / 1000)
    h = np.concatenate([h[-w:], h[:w + 1]])
    return (int(np.argmax(h >= nguong * h.max())) - w) * 1000.0 / sr
