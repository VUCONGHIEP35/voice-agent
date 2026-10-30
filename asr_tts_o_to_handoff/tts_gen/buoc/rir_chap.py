# -*- coding: utf-8 -*-
"""Chập RIR theo bảng gán, ghi bộ đệm "chỉ có vang" (giai đoạn 4 của docs/RIR.md; docs/ke_hoach_RIR_v1.md).

Chạy (từ tts_gen/, venv có numpy/scipy/soundfile: venv_rir):
  python -m buoc.rir_chap --gan runs/rir_v2/gan --kho runs/rir_v2/kho runs/rir_v2/kho_do --out runs/rir_v2/aug_v1/_reverb --workers 64 \
      --asr-dev 500 --asr-out runs/rir_v2/asr_dev
Mỗi bản (thuvien.rir.xu_ly_ban): mức giọng hoạt động về −26 dBFS trên mặt nạ có tiếng của bản sạch; có RIR thì chập
FFT, bỏ các mẫu trước đỉnh trực tiếp (tre_truc_tiep trong rir_manifest), giữ tối đa 0,25 giây đuôi, khôi phục mức; đỉnh
vượt −1 dBFS thì hạ cả bản. Bản không RIR chỉ qua bước mức và chống cắt đỉnh. Nhiễu xe không bao giờ đi qua bước này.
Ghi <out>/<split>/<ban_id>.flac (16 kHz FLAC PCM_16) và <out>/manifest.jsonl: các trường của bảng gán, thông tin xử lý
(hệ số mức, mức hạ chống cắt đỉnh, số mẫu trễ đã bỏ), lech_tre_ms (đường đến đầu tiên của RIR giải chập từ bản sạch và bản vang),
sha_float32 (băm mẫu trước khi lượng tử, để kiểm tái lập). Không lọc CER.
--asr-dev N: chọn N bản dev có RIR (theo băm, tất định) và dựng hai lượt giả <asr-out>/sach, <asr-out>/vang
(manifest.jsonl của lượt gốc, audio16 trỏ tuyệt đối tới bản sạch / bản vang) để chạy buoc.asr_whisper trước/sau RIR.
"""
import argparse
import collections
import hashlib
import json
import os
import time
from multiprocessing import Pool

import numpy as np

import cauhinh.tang_cuong as C
from cauhinh.duong_dan import GOC
from thuvien.am_thanh import write_flac
from thuvien.chon_cau import h32
from thuvien.manifest import load_jsonl, load_manifest
from thuvien.rir import lech_tre_ms, xu_ly_ban

_KHO = {}


def nap_kho(*kho):
    """{rir_id: dòng} từ một hoặc nhiều kho (mô phỏng, đo); mỗi dòng ghi thêm _kho = thư mục kho của nó."""
    out = {}
    for d in kho:
        with open(os.path.join(d, "rir_manifest.jsonl"), encoding="utf-8") as f:
            for r in map(json.loads, f):
                if r["rir_id"] in out:
                    raise SystemExit(f"rir_id trùng giữa các kho: {r['rir_id']}")
                out[r["rir_id"]] = dict(r, _kho=d)
    return out


def lay_rir(kho, r):
    """Mảng RIR (đã cắt đúng n_mau) của một dòng rir_manifest; mỗi tiến trình giữ bộ nhớ đệm theo tệp khoang."""
    p = os.path.join(r.get("_kho") or kho, r["tep"])
    if p not in _KHO:
        _KHO[p] = np.load(p, mmap_mode="r")
    return np.asarray(_KHO[p][r["hang"], :r["n_mau"]], dtype=np.float64)


def xu_ly(task):
    row, rr, runs_goc, kho, out = task
    import soundfile as sf
    x, sr = sf.read(os.path.join(runs_goc, row["run"], row["audio16"]), dtype="float32")
    assert sr == C.SR, f"{row['audio16']}: {sr} Hz"
    x = np.asarray(x, dtype=np.float64)
    if rr is None:
        y, info = xu_ly_ban(x, None)
        lech = 0.0
    else:
        y, info = xu_ly_ban(x, lay_rir(kho, rr), rr["tre_truc_tiep"])
        lech = lech_tre_ms(x, y)
    rel = f"{row['split']}/{row['ban_id']}.flac"
    write_flac(os.path.join(out, rel), y, C.SR)
    return dict(row, audio=rel, lech_tre_ms=round(lech, 3), sha_float32=hashlib.sha256(np.clip(y, -1, 1).tobytes()).hexdigest(),
                **({"edt_s": rr["edt_s"], "drr_db": rr["drr_db"], "c50_db": rr["c50_db"]} if rr else {}), **info)


def chon_asr_dev(rows, n):
    dev = sorted((r for r in rows if r["split"] == "dev" and r["co_rir"]), key=lambda r: h32("asr_dev", r["ban_id"]))
    return dev[:n]


def dung_asr(sel, runs_goc, out, asr_out):
    """Hai lượt giả cho buoc.asr_whisper: cùng dòng manifest gốc, audio16 = bản sạch gốc / bản vang."""
    man = {}
    for run in sorted({r["run"] for r in sel}):
        for m in load_manifest(os.path.join(runs_goc, run)):
            man[m["utt_id"]] = (run, m)
    for ten in ("sach", "vang"):
        d = os.path.join(asr_out, ten)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "manifest.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for r in sel:
                run, m = man[r["utt_id"]]
                p = (os.path.join(runs_goc, run, m["audio16"]) if ten == "sach" else os.path.join(out, r["audio"]))
                f.write(json.dumps(dict(m, audio16=os.path.abspath(p), ban_id=r["ban_id"], rir_id=r["rir_id"],
                                        loai_xe=r["loai_xe"], ghe=r["ghe"], micro=r["micro"], phan=r["phan"],
                                        nguon_rir=r.get("nguon_rir", "mo_phong"), khoang=r["khoang"]),
                                   ensure_ascii=False) + "\n")
    print(f"Dựng lượt ASR trước/sau RIR: {len(sel)} bản dev -> {asr_out}/sach, {asr_out}/vang; "
          f"vùng {dict(collections.Counter(r['vung'] for r in sel))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gan", required=True, help="thư mục bảng gán (assign_train.jsonl, assign_dev.jsonl)")
    ap.add_argument("--kho", nargs="+", required=True, help="các thư mục kho đã dùng khi gán (mô phỏng, đo)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs-goc", default=os.path.join(GOC, "runs"))
    ap.add_argument("--split", nargs="+", default=["train", "dev"])
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--asr-dev", type=int, default=0)
    ap.add_argument("--asr-out", default=None)
    a = ap.parse_args()
    rir = nap_kho(*a.kho)
    rows = [r for sp in a.split for r in load_jsonl(os.path.join(a.gan, f"assign_{sp}.jsonl"))]
    thieu = sorted({r["rir_id"] for r in rows if r["co_rir"] and (r["rir_id"] not in rir or not rir[r["rir_id"]]["dat"])})
    if thieu:
        raise SystemExit(f"{len(thieu)} rir_id trong bảng gán không có (hoặc không đạt) trong kho, ví dụ {thieu[:3]}")
    for sp in a.split:
        os.makedirs(os.path.join(a.out, sp), exist_ok=True)
    tasks = [(r, rir[r["rir_id"]] if r["co_rir"] else None, a.runs_goc, None, a.out) for r in rows]
    t0 = time.perf_counter()
    res = []
    with Pool(a.workers) as pool:
        for n, r in enumerate(pool.imap(xu_ly, tasks, chunksize=16), 1):
            res.append(r)
            if n % 1000 == 0 or n == len(tasks):
                print(f"  {n}/{len(tasks)} bản, {time.perf_counter() - t0:.0f} s", flush=True)
    tmp = os.path.join(a.out, "manifest.jsonl.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for r in res:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, tmp[:-4])
    co = [r for r in res if r["co_rir"]]
    muc = np.array([r["muc_ra_dbfs"] for r in res])
    lech = np.abs([r["lech_tre_ms"] for r in co]) if co else np.zeros(1)
    print(f"Xong {len(res)} bản ({len(co)} có RIR) trong {time.perf_counter() - t0:.0f} s -> {a.out}")
    print(f"  mức ra trong −26 ± 0,5 dBFS: {np.mean(np.abs(muc - C.MUC_GIONG_DBFS) <= 0.5):.4f}; "
          f"đỉnh > −1 dBFS: {sum(r['dinh_ra_dbfs'] > C.DINH_MAX_DBFS + 0.01 for r in res)}; "
          f"bản phải hạ chống cắt đỉnh: {sum(r['ha_chong_cat_db'] < 0 for r in res)}; "
          f"|lệch trễ| p99 {np.percentile(lech, 99):.2f} ms, tối đa {lech.max():.2f} ms")
    if a.asr_dev:
        dung_asr(chon_asr_dev(res, a.asr_dev), a.runs_goc, a.out, a.asr_out or os.path.join(os.path.dirname(a.out), "asr_dev"))


if __name__ == "__main__":
    main()
