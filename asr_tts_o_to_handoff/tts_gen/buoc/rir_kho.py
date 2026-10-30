# -*- coding: utf-8 -*-
"""Sinh kho RIR mô phỏng khoang xe bằng pyroomacoustics (hybrid image source + ray tracing, 16 kHz), có kiểm định.

Chạy (từ tts_gen/, venv có pyroomacoustics: venv_rir trên cụm, .venv_rir trên laptop):
  python -m buoc.rir_kho --out runs/rir_v2/kho --workers 64                          # cả kho: 7 loại × 40 khoang
  python -m buoc.rir_kho --out runs/rir_v2/thu/kho --khoang-moi-loai 2 --workers 8   # thử nhỏ (đo thời gian, EDT)
Mỗi khoang: 4 ghế × 2 vị trí đầu × 4 micro = 32 RIR, mô phỏng trong MỘT lần (8 nguồn, 4 micro). Một RIR đạt khi:
EDT (trung bình octave 250 Hz–4 kHz) trong EDT_DAI, đỉnh trực tiếp lệch vị trí hình học dưới LECH_TRE_MAX_MS, không
lỗi hình dạng. Khoang được nhận khi cả 8 RIR ghế lái đạt (đặc tả: chọn khoang theo EDT ghế lái, không theo Sabine);
không thì bốc lại cả khoang (kích thước, vật liệu, vị trí đầu), tối đa LAN_BOC_MAX lần. RIR ghế khác trượt ngưỡng
được giữ trong tệp nhưng ghi dat = false và lý do; bước gán không dùng. Không sinh lại riêng từng RIR: đo 27/10 cho
thấy RIR trượt tập trung ở ghế sau và micro táp-lô của SUV/MPV (do hình học), bốc lại vị trí đầu chỉ chọn ra vị trí
lạ. Bốn khoang cuối mỗi loại vào dev.
Ghi <out>/rir/<khoang>.npy (float32, 32 hàng, đệm 0), <out>/khoang/<khoang>.json (một tệp mỗi khoang: chạy lại thì
bỏ qua khoang đã có), rồi gộp <out>/rir_manifest.jsonl, khoang_manifest.jsonl, splits.json, kho_config.json.
Lưu ý: ray tracing của pyroomacoustics không tất định (không nhận hạt giống). Kho sinh MỘT lần và giữ sha256 từng
tệp; tái lập của các bước sau tính từ kho đã lưu. Hạt giống chỉ cố định kích thước, vật liệu, vị trí.
"""
import argparse
import collections
import hashlib
import json
import os
import platform
import time
from multiprocessing import Pool

import numpy as np

import cauhinh.tang_cuong as C
from thuvien.chon_cau import h32
from thuvien.rir import do_rir, loi_hinh_dang, tim_truc_tiep

GHE_DAU = [(g, d) for g in C.GHE for d in range(C.SO_VI_TRI_DAU)]   # thứ tự nguồn trong phòng
CUA_TRUC_TIEP_MS = 0.25     # pyroomacoustics đặt đường trực tiếp đúng vị trí hình học; cửa rộng hơn có thể bắt phản xạ
LE = 0.05                                                           # toạ độ cách vách tối thiểu (m)


def ds_khoang(n_moi_loai=C.KHOANG_MOI_LOAI):
    """[(khoang_id, loai, chỉ số, split)]: 4 khoang cuối mỗi loại (theo KHOANG_MOI_LOAI) vào dev."""
    out = []
    for loai in C.LOAI_XE:
        for k in range(n_moi_loai):
            split = "dev" if k >= C.KHOANG_MOI_LOAI - C.KHOANG_DEV_MOI_LOAI else "train"
            out.append((f"{loai}{k:02d}", loai, k, split))
    return out


def rir_id(khoang, ghe, micro, dau):
    return f"rir_{khoang}_{ghe}_{micro}_h{dau}"


def bang_vat_lieu():
    from pyroomacoustics.parameters import materials_data
    return {k: v for cat in materials_data["absorption"].values() if isinstance(cat, dict) for k, v in cat.items()}


def he_so(ten, bang):
    c = list(bang[ten]["coeffs"])
    return np.array((c + [c[-1]] * len(C.TAN_SO_DAI))[:len(C.TAN_SO_DAI)])


def boc(loai, khoang, lan, seed, bang):
    """Kích thước, hệ số hấp thụ từng mặt, toạ độ 8 miệng và 4 micro (tất định theo hạt giống). x của miệng theo hàng
    ghế (mét từ chân kính trước), hàng 2 không sát vách sau quá MIENG_CACH_VACH_SAU_MIN."""
    s = h32("khoang", khoang, lan, seed)
    rng = np.random.default_rng(s)
    cfg = C.LOAI_XE[loai]
    L, W, H = (float(rng.uniform(*cfg[k])) for k in ("dai", "rong", "cao"))
    x1 = float(rng.uniform(*cfg["x_hang1"]))
    x_hang = {1: x1, 2: min(x1 + float(rng.uniform(*cfg["cach_hang"])), L - C.MIENG_CACH_VACH_SAU_MIN)}
    vl = {}
    rieng = C.VAT_LIEU_THEO_LOAI.get(loai, {})
    for mat, v in C.VAT_LIEU.items():
        v = rieng.get(mat, v)
        base = sum(f * he_so(n, bang) for n, f in v["tron"]) + np.array(C.HAP_THU_THEM)
        lech = rng.uniform(1 - C.VAT_LIEU_LECH, 1 + C.VAT_LIEU_LECH, size=len(base))
        vl[mat] = dict(hap_thu=[round(float(x), 4) for x in np.clip(base * lech, 0.01, 0.99)], tan_xa=v["tan_xa"])

    def trong(p):
        return [float(np.clip(p[0], LE, L - LE)), float(np.clip(p[1], LE, W - LE)), float(np.clip(p[2], LE, H - LE))]
    mieng = []
    for g, _ in GHE_DAU:
        gx, gy = x_hang[C.GHE[g]["hang"]], C.GHE[g]["y"] * W
        z = min(C.DEM_GHE_CAO + rng.uniform(*C.MIENG_TREN_DEM), H - C.MIENG_CACH_TRAN_MIN)
        mieng.append(trong([gx + rng.uniform(-C.LECH_DAU, C.LECH_DAU), gy + rng.uniform(-C.LECH_DAU, C.LECH_DAU), z]))
    mic = {}
    for m, v in C.MICRO.items():
        x = v["x_m"]
        y = v["y_m"] if "y_m" in v else v["y"] * W
        z = H - v["z_tu_tran_m"] if "z_tu_tran_m" in v else v["z"] * H
        mic[m] = trong([x, y, z])
    return s, (L, W, H), vl, mieng, mic


def mo_phong(kich_thuoc, vl, mieng, mic):
    import pyroomacoustics as pra
    from pyroomacoustics.directivities import CardioidFamily, DirectionVector
    mats = {k: pra.Material({"description": k, "coeffs": v["hap_thu"], "center_freqs": C.TAN_SO_DAI}, v["tan_xa"])
            for k, v in vl.items()}
    huong = None
    if C.HUONG_MIENG_P < 1:      # miệng quay về kính trước (x = 0)
        huong = CardioidFamily(orientation=DirectionVector(azimuth=180, colatitude=90, degrees=True), p=C.HUONG_MIENG_P)
    room = pra.ShoeBox(list(kich_thuoc), fs=C.SR, materials=mats, max_order=C.ISM_BAC, air_absorption=True,
                       ray_tracing=True)
    room.set_ray_tracing(n_rays=C.RAY_SO_TIA, receiver_radius=C.RAY_BAN_KINH_THU, energy_thres=1e-7,
                         time_thres=C.RAY_THOI_GIAN)
    for p in mieng:
        room.add_source(p, directivity=huong)
    room.add_microphone_array(np.array(list(mic.values())).T)
    room.compute_rir()
    return room


def sinh_khoang(task):
    """Một khoang: bốc tới khi 8 RIR ghế lái đạt. Trả (thông tin khoang, [dòng RIR], mảng float32 (32, n)); thất bại thì mảng None."""
    khoang, loai, k, split, seed = task
    import pyroomacoustics as pra
    bang = bang_vat_lieu()
    off = pra.constants.get("frac_delay_length") // 2
    n_rir = int(C.RIR_DAI_S * C.SR)
    mo = np.ones(n_rir)
    nf = int(C.MO_CUOI_MS * C.SR / 1000)
    mo[-nf:] = np.hanning(2 * nf)[nf:]
    loi_dem = {}
    t0 = time.perf_counter()
    for lan in range(C.LAN_BOC_MAX):
        s, kt, vl, mieng, mic = boc(loai, khoang, lan, seed, bang)
        np.random.seed(s % 2 ** 32)
        room = mo_phong(kt, vl, mieng, mic)
        rows, hs = [], []
        for j, m in enumerate(mic):
            for si, (g, d) in enumerate(GHE_DAU):
                h = np.asarray(room.rir[j][si], dtype=np.float64)
                kc = float(np.linalg.norm(np.array(mieng[si]) - np.array(mic[m])))
                tre_kv = kc / room.c * C.SR + off
                i = tim_truc_tiep(h, tre_kv, cua_ms=CUA_TRUC_TIEP_MS)
                dinh_max = int(np.argmax(np.abs(h)))
                h = np.pad(h, (0, max(0, i + n_rir - len(h))))[:i + n_rir]
                loi = loi_hinh_dang(h, i)
                met = do_rir(h, i)
                lech = (i - tre_kv) * 1000 / C.SR
                if met["edt_s"] is None or not C.EDT_DAI[0] <= met["edt_s"] <= C.EDT_DAI[1]:
                    loi.append("edt_ngoai_dai")
                if abs(lech) >= C.LECH_TRE_MAX_MS:
                    loi.append("lech_tre")
                for x in loi:
                    loi_dem[x] = loi_dem.get(x, 0) + 1
                h[i:] *= mo[:len(h) - i]
                hs.append(h.astype(np.float32))
                rows.append(dict(rir_id=rir_id(khoang, g, m, d), nguon="mo_phong", loai_xe=loai, khoang=khoang, ghe=g,
                                 micro=m, dau=d, split=split, mieng=[round(v, 3) for v in mieng[si]],
                                 micro_xyz=[round(v, 3) for v in mic[m]], kich_thuoc=[round(v, 3) for v in kt],
                                 khoang_cach_m=round(kc, 3), tre_ky_vong=round(tre_kv, 2), tre_truc_tiep=int(i),
                                 lech_tre_ms=round(lech, 3), dinh_max_sau_truc_tiep_ms=round((dinh_max - i) * 1000 / C.SR, 2),
                                 **met, dat=not loi, loi=loi))
        if not any(r["loi"] for r in rows if r["ghe"] == "lai"):
            n = max(len(h) for h in hs)
            arr = np.zeros((len(hs), n), dtype=np.float32)
            for r, h in enumerate(hs):
                arr[r, :len(h)] = h
            for r, row in enumerate(rows):
                row.update(hang=r, n_mau=len(hs[r]), tep=f"rir/{khoang}.npy", seed=int(s), lan_boc=lan + 1,
                           giay_phep="tự sinh bằng pyroomacoustics (MIT)", cong_cu=f"pyroomacoustics {pra.__version__}")
            info = dict(khoang=khoang, loai_xe=loai, chi_so=k, split=split, kich_thuoc=[round(v, 3) for v in kt],
                        vat_lieu=vl, seed=int(s), lan_boc=lan + 1, giay=round(time.perf_counter() - t0, 1),
                        dem_loi=loi_dem, rir_loai=sum(not r["dat"] for r in rows))
            return info, rows, arr
    return dict(khoang=khoang, loai_xe=loai, chi_so=k, split=split, that_bai=True, lan_boc=C.LAN_BOC_MAX,
                giay=round(time.perf_counter() - t0, 1), dem_loi=loi_dem), [], None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def khoa_chuoi(v):
    """Khoá tuple (vd MICRO_DO) thành chuỗi "a|b|c" để ghi JSON."""
    if isinstance(v, dict):
        return {"|".join(map(str, k)) if isinstance(k, tuple) else k: khoa_chuoi(x) for k, x in v.items()}
    return v


def gop(out):
    """Gộp các tệp khoang/*.json thành manifest, splits, cấu hình; in tóm tắt."""
    infos, rows = [], []
    for fn in sorted(os.listdir(os.path.join(out, "khoang"))):
        with open(os.path.join(out, "khoang", fn), encoding="utf-8") as f:
            d = json.load(f)
        infos.append(d["khoang"])
        rows += d["rir"]
    with open(os.path.join(out, "rir_manifest.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "khoang_manifest.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for d in infos:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    sp = {s: sorted(d["khoang"] for d in infos if d["split"] == s and not d.get("that_bai")) for s in ("train", "dev")}
    with open(os.path.join(out, "splits.json"), "w", encoding="utf-8") as f:
        json.dump(sp, f, ensure_ascii=False, indent=1)
    return infos, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--khoang-moi-loai", type=int, default=C.KHOANG_MOI_LOAI, help="thử nhỏ: số khoang đầu mỗi loại")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--seed", type=int, default=C.SEED)
    a = ap.parse_args()
    import pyroomacoustics as pra
    for d in ("rir", "khoang"):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)
    tasks = [(kh, lo, k, sp, a.seed) for kh, lo, k, sp in ds_khoang(a.khoang_moi_loai)
             if not os.path.exists(os.path.join(a.out, "khoang", f"{kh}.json"))]
    print(f"{len(tasks)} khoang cần sinh ({a.khoang_moi_loai} mỗi loại, đã có {len(C.LOAI_XE) * a.khoang_moi_loai - len(tasks)}), "
          f"{a.workers} tiến trình", flush=True)
    t0 = time.perf_counter()
    with Pool(a.workers) as pool:
        for n, (info, rows, arr) in enumerate(pool.imap_unordered(sinh_khoang, tasks), 1):
            if arr is not None:
                p = os.path.join(a.out, "rir", f"{info['khoang']}.npy")
                np.save(p + ".tmp.npy", arr)
                os.replace(p + ".tmp.npy", p)
                info["sha256"] = sha256(p)
            tmp = os.path.join(a.out, "khoang", f"{info['khoang']}.json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dict(khoang=info, rir=rows), f, ensure_ascii=False)
            os.replace(tmp, tmp[:-4])
            print(f"  [{n}/{len(tasks)}] {info['khoang']}: {'THẤT BẠI' if arr is None else 'đạt'} sau {info['lan_boc']} lần, "
                  f"{info['giay']} s, RIR loại {info.get('rir_loai', '-')}/32, đếm lỗi mọi lần {info['dem_loi']}", flush=True)
    wall = time.perf_counter() - t0
    infos, rows = gop(a.out)
    cfg = {k: khoa_chuoi(v) for k, v in vars(C).items() if k.isupper()}
    cfg.update(seed=a.seed, pyroomacoustics=pra.__version__, numpy=np.__version__, python=platform.python_version(),
               may=platform.node(), workers=a.workers, giay_lan_nay=round(wall, 1), ghi_luc=time.strftime("%F %T"))
    with open(os.path.join(a.out, "kho_config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
    fail = [d["khoang"] for d in infos if d.get("that_bai")]
    giay = [d["giay"] / d["lan_boc"] for d in infos if not d.get("that_bai")]
    print(f"\nXong {len(infos)} khoang, {len(rows)} RIR, {wall:.0f} s đồng hồ; mỗi lần mô phỏng (32 RIR) trung bình "
          f"{np.mean(giay) if giay else float('nan'):.1f} s CPU; khoang thất bại: {fail or 'không'}")
    for lo in C.LOAI_XE:
        ds = [d for d in infos if d["loai_xe"] == lo and not d.get("that_bai")]
        if ds:
            rr = [r for r in rows if r["loai_xe"] == lo]
            e = np.array([r["edt_s"] for r in rr if r["edt_s"] is not None])
            loai = collections.Counter((r["ghe"], r["micro"]) for r in rr if not r["dat"])
            print(f"  {lo:7s} {len(ds)} khoang, lần bốc trung bình {np.mean([d['lan_boc'] for d in ds]):.1f}, "
                  f"EDT p5/trung vị/p95 {np.percentile(e, 5):.3f}/{np.median(e):.3f}/{np.percentile(e, 95):.3f}, "
                  f"RIR loại {sum(loai.values())}/{len(rr)} {dict(loai.most_common(6))}")
    if fail:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
