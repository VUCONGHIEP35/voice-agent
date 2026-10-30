# -*- coding: utf-8 -*-
"""Kho RIR ĐO THẬT (McVAMPIRE, CAVEMOVE; CC BY 4.0) cùng định dạng với kho mô phỏng (docs/ke_hoach_RIR_v2.md).

Chạy (từ tts_gen/, venv có numpy, scipy, soundfile, soxr):
  python -m buoc.rir_kho_do tai --dich .cache/rir_do            # cần mạng (nút đầu cụm, hoặc laptop)
  python -m buoc.rir_kho_do dung --nguon .cache/rir_do --out runs/rir_v2/kho_do
tai:  McVAMPIRE tải nguyên zip (256 MB), so md5 với Zenodo, giải nén ir/, geometry.*, tài liệu PDF.
      CAVEMOVE: zip 7,6 GB phần lớn là tiếng ồn, nên chỉ đọc mục lục từ xa (HTTP Range) và lấy <xe>/<cấu hình>/IRs/ và
      info.json (zipfile kiểm CRC từng tệp); tài liệu PDF tải riêng, so md5. Mỗi bộ một thư mục riêng; không chạy gì
      trong đó. Đã có thì bỏ qua.
dung: mỗi xe trong XE_DO là một khoang của kho đo (split theo XE_DO). Mỗi tệp × kênh micro thuộc MICRO_DO, ở ghế
      có trong bảng ghế, là một RIR: đưa về 16 kHz (soxr; McVAMPIRE gốc 24 kHz), tìm đỉnh trực tiếp (đường đến đầu
      tiên ≥ 30% đỉnh, rồi |h| lớn nhất trong 0,5 ms sau đó: RIR đo không có toạ độ để tính trước), giữ 40 mẫu trước
      đỉnh và tối đa RIR_DAI_S giây sau, làm mờ 5 ms cuối, đo EDT/T20/DRR/C50 bằng thuvien.rir.
      RIR đo là chuẩn thật nên KHÔNG lọc theo EDT; chỉ loại khi có giá trị không hữu hạn. Lỗi hình dạng khác chỉ ghi
      vào canh_bao (vd McVAMPIRE chỉ dài 85 ms nên "duoi_khong_tat" luôn bật).
      Ghi <out>/rir/<khoang>.npy, rir_manifest.jsonl, khoang_manifest.jsonl, splits.json, kho_config.json (nguồn,
      md5, giấy phép, trích dẫn).
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import time
import urllib.request
import zipfile

import numpy as np

import cauhinh.tang_cuong as C
from thuvien.rir import TRE_PHAN_SO, do_rir, loi_hinh_dang


# ---------- tải ----------
class HttpFile(io.RawIOBase):
    """Tệp chỉ đọc qua HTTP Range, đủ để zipfile đọc mục lục và từng tệp con mà không tải cả zip."""

    def __init__(self, url):
        self.pos = 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            self.size, self.url = int(r.headers["Content-Length"]), r.url

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def readinto(self, b):
        if self.pos >= self.size or not len(b):
            return 0
        end = min(self.pos + len(b), self.size) - 1
        for lan in range(5):
            try:
                req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    if r.status != 206:
                        raise IOError(f"máy chủ không hỗ trợ Range (HTTP {r.status})")
                    d = r.read()
                break
            except OSError:
                if lan == 4:
                    raise
        b[:len(d)] = d
        self.pos += len(d)
        return len(d)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tai_tep(url, path, md5_dung):
    if not (os.path.exists(path) and md5(path) == md5_dung):
        urllib.request.urlretrieve(url, path + ".tmp")
        os.replace(path + ".tmp", path)
    if md5(path) != md5_dung:
        raise SystemExit(f"{path}: md5 {md5(path)} khác Zenodo {md5_dung}")
    print(f"  {os.path.basename(path)}: md5 khớp")


def giai_nen_an_toan(z, info, out):
    n = info.filename
    if n.startswith("/") or ".." in n.replace("\\", "/").split("/"):
        raise SystemExit(f"đường dẫn lạ trong zip: {n}")
    z.extract(info, out)


def tai(dich):
    mv, cm = (os.path.join(dich, x) for x in ("mcvampire", "cavemove"))
    os.makedirs(mv, exist_ok=True)
    os.makedirs(cm, exist_ok=True)
    s = C.RIR_DO_NGUON["mcvampire"]
    zp = os.path.join(mv, "In-Car_McVAMPIRE_V1.0.zip")
    tai_tep(s["url"], zp, s["md5"])
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            if i.filename.startswith("ir/") or i.filename.startswith("geometry") or i.filename.endswith(".pdf"):
                giai_nen_an_toan(z, i, os.path.join(mv, "giai_nen"))
    s = C.RIR_DO_NGUON["cavemove"]
    tai_tep(s["url_tai_lieu"], os.path.join(cm, "dataset_documentation.pdf"), s["md5_tai_lieu"])
    out = os.path.join(cm, "giai_nen")
    with zipfile.ZipFile(io.BufferedReader(HttpFile(s["url"]), buffer_size=1 << 20)) as z:
        can = [i for i in z.infolist() if not i.is_dir() and
               (re.search(r"/IRs/[^/]+\.wav$", i.filename) or i.filename.endswith("/info.json"))]
        moi = [i for i in can if not (os.path.exists(os.path.join(out, i.filename)) and
                                      os.path.getsize(os.path.join(out, i.filename)) == i.file_size)]
        for i in moi:
            giai_nen_an_toan(z, i, out)
    print(f"  CAVEMOVE: {len(can)} tệp IR/info (tải mới {len(moi)}), CRC đã kiểm khi giải nén")


# ---------- dựng kho ----------
def dinh_truc_tiep(h, nguong=0.3):
    a = np.abs(h)
    i0 = int(np.argmax(a >= nguong * a.max()))
    return i0 + int(np.argmax(a[i0:i0 + 8]))


def cat_rir(h):
    """(đoạn RIR từ 40 mẫu trước đỉnh tới RIR_DAI_S sau đỉnh, đã làm mờ cuối; vị trí đỉnh trong đoạn)."""
    i = dinh_truc_tiep(h)
    a = max(0, i - TRE_PHAN_SO)
    g = np.array(h[a:i + int(C.RIR_DAI_S * C.SR)], dtype=np.float64)
    nf = min(int(C.MO_CUOI_MS * C.SR / 1000), len(g) // 4)
    if nf:
        g[-nf:] *= np.hanning(2 * nf)[nf:]
    return g, i - a


def ghe_cavemove(vi_tri):
    if vi_tri.startswith("d"):
        return "lai"
    if vi_tri.startswith("pf"):
        return "phu"
    return {"prl": "sau_trai", "prr": "sau_phai"}.get(vi_tri[:3])     # prm (giữa) -> None


def micro_cua(bo, xe, cau_hinh):
    return C.MICRO_DO.get((bo, xe, cau_hinh)) or C.MICRO_DO.get((bo, "*", cau_hinh)) or {}


def doc_tep(nguon, khoang):
    """[(đường dẫn, cấu hình, vị trí, biến thể, ghế)] của một xe đo."""
    bo, xe = C.XE_DO[khoang][:2]
    out = []
    if bo == "mcvampire":
        for p in sorted(glob.glob(os.path.join(nguon, "mcvampire", "giai_nen", "ir", "ir_mouth_pos*.wav"))):
            pos, huong = re.search(r"_(pos\d)_(-?\d+)\.wav$", p).groups()
            out.append((p, "tran", pos, f"o{huong}", C.GHE_MCVAMPIRE.get(pos)))
    else:
        for cfg in ("distributed", "array"):
            for p in sorted(glob.glob(os.path.join(nguon, "cavemove", "giai_nen", "cavemove_dataset", xe, cfg, "IRs", "*.wav"))):
                vt, w = os.path.basename(p)[:-4].rsplit("_", 1)
                out.append((p, cfg, vt, w, ghe_cavemove(vt)))
    return out


def dung_khoang(nguon, khoang):
    import soundfile as sf
    import soxr
    bo, xe, loai, split = C.XE_DO[khoang]
    rows, hs, bo_qua = [], [], {"ghe": 0, "kenh": 0}
    for p, cfg, vt, bien_the, ghe in doc_tep(nguon, khoang):
        mic_map = micro_cua(bo, xe, cfg)
        x, sr = sf.read(p, dtype="float64", always_2d=True)
        if ghe is None:
            bo_qua["ghe"] += x.shape[1]
            continue
        if sr != C.SR:
            x = soxr.resample(x, sr, C.SR)
        bo_qua["kenh"] += x.shape[1] - len([k for k in mic_map if k <= x.shape[1]])
        for k, mic in sorted(mic_map.items()):
            if k > x.shape[1]:
                continue
            g, i = cat_rir(x[:, k - 1])
            loi = [] if np.all(np.isfinite(g)) else ["khong_huu_han"]
            met = do_rir(g, i) if not loi else {}
            ma = f"{vt}_{bien_the}_{cfg[0]}{k}"
            rows.append(dict(rir_id=f"rir_{khoang}_{ghe}_{mic}_{ma}", nguon="do", bo=bo, xe=xe, cau_hinh=cfg, kenh=k,
                             vi_tri=vt, bien_the=bien_the, loai_xe=loai, khoang=khoang, ghe=ghe, micro=mic, dau=ma,
                             split=split, sr_goc=sr, tre_truc_tiep=int(i), **met, dat=not loi, loi=loi,
                             canh_bao=loi_hinh_dang(g, i) if not loi else [],
                             tep_goc=os.path.relpath(p, nguon).replace("\\", "/"),
                             giay_phep=C.RIR_DO_NGUON[bo]["giay_phep"], trich_dan=C.RIR_DO_NGUON[bo]["trich_dan"]))
            hs.append(g.astype(np.float32))
    n = max(len(h) for h in hs)
    arr = np.zeros((len(hs), n), dtype=np.float32)
    for r, h in enumerate(hs):
        arr[r, :len(h)] = h
        rows[r].update(hang=r, n_mau=len(h), tep=f"rir/{khoang}.npy")
    return rows, arr, bo_qua


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dung(nguon, out):
    os.makedirs(os.path.join(out, "rir"), exist_ok=True)
    all_rows, cab = [], []
    for khoang, (bo, xe, loai, split) in C.XE_DO.items():
        rows, arr, bo_qua = dung_khoang(nguon, khoang)
        p = os.path.join(out, "rir", f"{khoang}.npy")
        np.save(p + ".tmp.npy", arr)
        os.replace(p + ".tmp.npy", p)
        all_rows += rows
        cab.append(dict(khoang=khoang, nguon="do", bo=bo, xe=xe, loai_xe=loai, split=split, so_rir=len(rows),
                        so_rir_dat=sum(r["dat"] for r in rows), bo_qua=bo_qua, sha256=sha256(p)))
        e = [r["edt_s"] for r in rows if r["dat"]]
        print(f"  {khoang:9s} {xe:17s} {split:5s} {len(rows):4d} RIR | ghế {dict(sorted(_dem(rows, 'ghe').items()))} | "
              f"micro {dict(sorted(_dem(rows, 'micro').items()))} | EDT trung vị {np.median(e):.3f} s | bỏ {bo_qua}")
    for name, data in (("rir_manifest.jsonl", all_rows), ("khoang_manifest.jsonl", cab)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "splits.json"), "w", encoding="utf-8") as f:
        json.dump({s: sorted(c["khoang"] for c in cab if c["split"] == s) for s in ("train", "dev")}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "kho_config.json"), "w", encoding="utf-8") as f:
        json.dump(dict(nguon=C.RIR_DO_NGUON, xe_do=C.XE_DO, micro_do={"|".join(k): v for k, v in C.MICRO_DO.items()},
                       ghe_mcvampire=C.GHE_MCVAMPIRE, sr=C.SR, rir_dai_s=C.RIR_DAI_S, ghi_luc=time.strftime("%F %T")),
                  f, ensure_ascii=False, indent=1)
    print(f"Xong: {len(all_rows)} RIR đo, {sum(r['dat'] for r in all_rows)} đạt -> {out}")


def _dem(rows, k):
    d = {}
    for r in rows:
        d[r[k]] = d.get(r[k], 0) + 1
    return d


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="lenh", required=True)
    t = sub.add_parser("tai")
    t.add_argument("--dich", required=True)
    d = sub.add_parser("dung")
    d.add_argument("--nguon", required=True)
    d.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.lenh == "tai":
        tai(a.dich)
    else:
        dung(a.nguon, a.out)


if __name__ == "__main__":
    main()
