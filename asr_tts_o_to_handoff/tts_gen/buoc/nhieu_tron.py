# -*- coding: utf-8 -*-
"""Trộn nhiễu giai đoạn 1 theo bảng gán (buoc/nhieu_gan.py), dựng lượt ASR (docs/ke_hoach_nhieu_v1.md).

Chạy (từ tts_gen/, venv_rir):
  python -m buoc.nhieu_tron --gan runs/nhieu_v1/gan --kho runs/nhieu_v1/kho --nhieu ~/asr_tts_o_to/nhieu \
      --vang-goc runs/rir_v2/aug_v1/_reverb --out runs/nhieu_v1/aug_v1 --workers 64 \
      --asr-goc runs/rir_v2/asr_dev --asr-out runs/nhieu_v1
Mỗi bản: đọc bản vang (giọng ở muc_ra_dbfs ≈ −26 dBFS), cắt đoạn nhiễu theo bảng gán (một kênh, nối vòng có làm mờ nếu
tệp ngắn), chỉnh RMS đoạn nhiễu về muc_ra_dbfs − snr_db, cộng; đỉnh vượt −1 dBFS thì hạ cả bản (SNR giữ nguyên).
Ghi <out>/<split>/<ban_id>.flac và <out>/manifest.jsonl (bảng gán + muc_nhieu_dbfs, snr_do_db, ha_chong_cat_db, dinh_ra_dbfs).
--asr-goc: thư mục asr_dev của bước RIR (sach/, vang/ cùng 500 bản dev, đã có kết quả ASR). Dựng <asr-out>/asr_dev/nhieu
  (500 bản đó, bản có nhiễu của bộ sinh ra) và <asr-out>/asr_luoi (lưới: mỗi bản × PRESET_GD1 × SNR_LUOI, nhiễu Golf,
  một đoạn nhiễu cố định theo (bản, preset) dùng chung cho mọi mức SNR; utt_id thêm "__<preset>_snr<k>" để chạy MỘT lượt
  buoc.asr_whisper cho cả lưới). Âm thanh lưới ở <asr-out>/luoi_am_thanh/.
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

import cauhinh.nhieu as N
from buoc.nhieu_gan import chon_doan
from thuvien.am_thanh import write_flac

SR = 16000


def db(x):
    return float(20 * np.log10(max(float(np.sqrt(np.mean(np.square(x)))), 1e-12)))


def doc_doan(path, kenh, bat_dau_s, n):
    """n mẫu kênh `kenh` (1–8) từ bat_dau_s; tệp ngắn thì nối vòng phần giữa tệp, làm mờ NOI_VONG_S ở chỗ nối."""
    import soundfile as sf
    info = sf.info(path)
    if info.samplerate != SR:
        raise SystemExit(f"{path}: {info.samplerate} Hz")
    a = int(N.CAT_BIEN_S * SR)
    s = int(bat_dau_s * SR)
    if s + n <= info.frames - a:
        x, _ = sf.read(path, start=s, frames=n, dtype="float64", always_2d=True)
        return x[:, kenh - 1]
    x, _ = sf.read(path, dtype="float64", always_2d=True)
    x = x[a:max(a + 1, info.frames - a), kenh - 1]
    m = min(int(N.NOI_VONG_S * SR), len(x) // 4)
    out = x.copy()
    while len(out) < n:
        if m:
            w = np.linspace(0, 1, m)
            out[-m:] = out[-m:] * (1 - w) + x[:m] * w
            out = np.concatenate([out, x[m:]])
        else:
            out = np.concatenate([out, x])
    return out[:n]


def tron(x, nz, muc_giong_db, snr_db):
    """(bản trộn float32, thông tin). Nhiễu đưa về muc_giong_db − snr_db; đỉnh > DINH_MAX_DBFS thì hạ cả bản."""
    nz = nz - nz.mean()
    g = 10 ** ((muc_giong_db - snr_db - db(nz)) / 20)
    nz = nz * g
    y = x + nz
    pk = 20 * np.log10(max(float(np.max(np.abs(y))), 1e-12))
    ha = min(0.0, N.DINH_MAX_DBFS - pk)
    k = 10 ** (ha / 20)
    y, nz = y * k, nz * k
    return y.astype(np.float32), dict(muc_nhieu_dbfs=round(db(nz), 2), snr_do_db=round(muc_giong_db + ha - db(nz), 3),
                                      ha_chong_cat_db=round(ha, 3), dinh_ra_dbfs=round(pk + ha, 2))


def ghi(path, y):
    """write_flac không tự tạo thư mục (lỗi bắt được khi thử trên cụm 29/10)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_flac(path, y, SR)


def doc_vang(path):
    import soundfile as sf
    x, sr = sf.read(path, dtype="float64")
    if sr != SR:
        raise SystemExit(f"{path}: {sr} Hz")
    return x


def viec_ban(task):
    r, vang_goc, nhieu, out = task
    x = doc_vang(os.path.join(vang_goc, r["audio"]))
    nz = doc_doan(os.path.join(nhieu, r["nhieu_tep"]), r["kenh"], r["bat_dau_s"], len(x))
    y, info = tron(x, nz, r["muc_ra_dbfs"], r["snr_db"])
    rel = f"{r['split']}/{r['ban_id']}.flac"
    ghi(os.path.join(out, rel), y)
    return dict(r, audio_vang=r["audio"], audio=rel, **info)


def viec_luoi(task):
    """Một bản của lưới: mọi preset × mọi SNR. Trả các dòng manifest ASR."""
    m, r, kho, nhieu, out_am = task
    x = doc_vang(m["audio16"])
    dong = []
    for p in N.PRESET_GD1:
        d, _ = chon_doan(kho, p, "dev", r["micro"], ("luoi", r["ban_id"], p), r["dai_s"])
        nz = doc_doan(os.path.join(nhieu, d["nhieu_tep"]), d["kenh"], d["bat_dau_s"], len(x))
        for snr in N.SNR_LUOI:
            dk = f"{p}_snr{snr}"
            y, info = tron(x, nz, r["muc_ra_dbfs"], float(snr))
            path = os.path.abspath(os.path.join(out_am, dk, f"{r['ban_id']}.flac"))
            ghi(path, y)
            dong.append(dict(m, utt_id=f"{m['utt_id']}__{dk}", utt_id_goc=m["utt_id"], audio16=path, dieu_kien=dk,
                             preset_moi_truong=p, snr_dat_db=snr, nhieu_id=d["nhieu_id"], kenh=d["kenh"], **info))
    return dong


def ghi_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gan", required=True)
    ap.add_argument("--kho", required=True)
    ap.add_argument("--nhieu", required=True, help="thư mục gốc chứa cavemove/giai_nen (tep trong kho tính từ đây)")
    ap.add_argument("--vang-goc", required=True, help="thư mục bộ vang (audio trong manifest vang tính từ đây)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--asr-goc", default=None, help="asr_dev của bước RIR (vang/manifest.jsonl: 500 bản dev)")
    ap.add_argument("--asr-out", default=None)
    a = ap.parse_args()
    nhieu = os.path.expanduser(a.nhieu)
    rows = []
    for sp in ("train", "dev"):
        with open(os.path.join(a.gan, f"assign_{sp}.jsonl"), encoding="utf-8") as f:
            rows += [json.loads(x) for x in f if x.strip()]
    with open(os.path.join(a.kho, "kho_nhieu.jsonl"), encoding="utf-8") as f:
        kho = [json.loads(x) for x in f if x.strip()]
    with Pool(a.workers) as pool:
        man = pool.map(viec_ban, [(r, a.vang_goc, nhieu, a.out) for r in rows], chunksize=16)
        ghi_jsonl(os.path.join(a.out, "manifest.jsonl"), man)
        loi = [m for m in man if abs(m["snr_do_db"] - m["snr_db"]) > 0.5]
        print(f"Trộn {len(man)} bản -> {a.out}; hạ chống cắt đỉnh {sum(m['ha_chong_cat_db'] < 0 for m in man)} bản; "
              f"SNR lệch > 0,5 dB: {len(loi)}", flush=True)
        if a.asr_goc:
            with open(os.path.join(a.asr_goc, "vang", "manifest.jsonl"), encoding="utf-8") as f:
                goc = [json.loads(x) for x in f if x.strip()]
            theo_ban = {m["ban_id"]: m for m in man}
            nh = [dict(m, audio16=os.path.abspath(os.path.join(a.out, theo_ban[m["ban_id"]]["audio"])),
                       preset_moi_truong=theo_ban[m["ban_id"]]["preset_moi_truong"], snr_db=theo_ban[m["ban_id"]]["snr_db"])
                  for m in goc]
            ghi_jsonl(os.path.join(a.asr_out, "asr_dev", "nhieu", "manifest.jsonl"), nh)
            luoi = pool.map(viec_luoi, [(m, theo_ban[m["ban_id"]], kho, nhieu, os.path.join(a.asr_out, "luoi_am_thanh"))
                                        for m in goc], chunksize=4)
            luoi = [d for ds in luoi for d in ds]
            ghi_jsonl(os.path.join(a.asr_out, "asr_luoi", "manifest.jsonl"), luoi)
            print(f"Lượt ASR: asr_dev/nhieu {len(nh)} bản; asr_luoi {len(luoi)} tệp "
                  f"({len(N.PRESET_GD1)} preset × {len(N.SNR_LUOI)} mức SNR × {len(goc)} bản)", flush=True)
    if loi:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
