# -*- coding: utf-8 -*-
"""Test bước RIR (thuvien/rir.py, buoc/rir_gan.py, buoc/rir_kho.py). Phần cần pyroomacoustics tự bỏ qua nếu thiếu."""
import importlib.util
import unittest

import numpy as np

import cauhinh.tang_cuong as C
from buoc import rir_gan
from buoc.rir_kho import GHE_DAU, ds_khoang, rir_id
from thuvien import rir as R

CO_PRA = importlib.util.find_spec("pyroomacoustics") is not None


def tieng_gia(n=24000, seed=0):
    """Tín hiệu giả kiểu tiếng nói: nhiễu điều biên, có lặng hai đầu."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / C.SR
    x = rng.standard_normal(n) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) * 0.1
    x[:2000] = 0
    x[-3000:] = 0
    return x


def kho_gia():
    rows = []
    for kh, lo, _, sp in ds_khoang():
        for m in C.MICRO:
            for g, d in GHE_DAU:
                rows.append(dict(rir_id=rir_id(kh, g, m, d), khoang=kh, loai_xe=lo, ghe=g, micro=m, dau=d, split=sp, dat=True))
    return rir_gan.chi_muc_kho([dict(r, nguon="mo_phong") for r in rows])


def file_gia(i, phan="thuong", goc=None):
    sid = goc or f"CS01-M1-{i:05d}"
    return dict(utt_id=f"{sid}{'__w' if phan == 'ghep' else ''}__v__a0", sample_id=sid + ("#w" if phan == "ghep" else ""),
                run="full10k_wake" if phan == "ghep" else "full10k_p01", phan=phan, vung="Bắc", case_id="CS01",
                speaker_region="Bắc", voice="v", voice_region="Bắc", length_class="Ngắn", n_syllables=5, duration_s=2.0,
                clipped=False, text_raw="x", audio16="audio16/x.flac", wake_type="du" if phan == "ghep" else None,
                wake_cat="", parent_utt_id=None)


class TestChap(unittest.TestCase):
    def test_xung_don_vi_cho_ra_ban_sach(self):
        x = tieng_gia()
        for i in (0, 57):
            h = np.zeros(400)
            h[i] = 1.0
            y, info = R.xu_ly_ban(x, h, i)
            g = 10 ** ((C.MUC_GIONG_DBFS - R.muc_db(x, R.mat_na_tieng(x))) / 20)    # info làm tròn 0,01 dB
            self.assertEqual(len(y), len(x) + min(int(C.DUOI_S * C.SR), len(h) - 1 - i))   # đuôi tối đa 0,25 s
            np.testing.assert_allclose(y[:len(x)], x * g, atol=1e-6)
            np.testing.assert_allclose(y[len(x):], 0, atol=1e-6)
            self.assertEqual(info["tre_bo_mau"], i)

    def test_do_tre_bo_dung(self):
        x = tieng_gia()
        h = np.zeros(1000)
        h[120], h[320] = 1.0, 0.4                     # đường trực tiếp ở mẫu 120, phản xạ sau 200 mẫu
        y, _ = R.xu_ly_ban(x, h, 120)
        ref = x.copy()
        ref[200:] += 0.4 * x[:-200]
        g = 10 ** ((C.MUC_GIONG_DBFS - R.muc_db(ref, R.mat_na_tieng(x))) / 20)
        np.testing.assert_allclose(y[:len(x)], ref * g, atol=1e-5)
        self.assertAlmostEqual(R.lech_tre_ms(x, y), 0.0, places=3)

    def test_muc_26_dbfs(self):
        x = tieng_gia() * 3
        for h, i in ((None, 0), (np.r_[np.zeros(30), 1.0, 0.5 * np.exp(-np.arange(2000) / 300.0)], 30)):
            y, info = R.xu_ly_ban(x, h, i)
            self.assertAlmostEqual(R.muc_db(y, R.mat_na_tieng(x)), C.MUC_GIONG_DBFS, places=2)
            self.assertAlmostEqual(info["muc_ra_dbfs"], C.MUC_GIONG_DBFS, places=2)

    def test_chong_cat_dinh(self):
        x = tieng_gia()
        x[5000] = 5.0                                   # một đỉnh rất cao so với mức giọng
        y, info = R.xu_ly_ban(x, None)
        self.assertLessEqual(20 * np.log10(np.max(np.abs(y))), C.DINH_MAX_DBFS + 1e-3)
        self.assertLess(info["ha_chong_cat_db"], 0)

    def test_lech_tre_duong_den_dau_tien(self):
        x = tieng_gia()
        y = np.r_[np.zeros(80), x][:len(x)]             # trễ 5 ms
        self.assertAlmostEqual(R.lech_tre_ms(x, y), 5.0, places=3)

    def test_lech_tre_khong_lay_phan_xa_manh_hon(self):
        x = tieng_gia()
        h = np.zeros(1200)
        h[100], h[148] = 0.6, 1.0                       # phản xạ sau 3 ms mạnh hơn đường trực tiếp
        y, _ = R.xu_ly_ban(x, h, 100)
        self.assertAlmostEqual(R.lech_tre_ms(x, y), 0.0, places=3)


class TestDoRir(unittest.TestCase):
    def test_edt_tat_dan_mu(self):
        rng = np.random.default_rng(1)
        for T in (0.05, 0.12):
            t = np.arange(int(0.4 * C.SR)) / C.SR
            h = rng.standard_normal(len(t)) * 10 ** (-3 * t / T)       # tắt 60 dB sau T giây
            h[0] = 0.0
            self.assertAlmostEqual(R.edt(h, 0), T, delta=0.15 * T)
            self.assertAlmostEqual(R.t20(h, 0), T, delta=0.15 * T)

    def test_tim_truc_tiep_khong_lay_phan_xa_manh_hon(self):
        h = np.zeros(800)
        h[100], h[140] = 0.5, 0.9                      # phản xạ cộng dồn cao hơn đường trực tiếp
        self.assertEqual(R.tim_truc_tiep(h, 100.3, cua_ms=0.25), 100)

    def test_hinh_dang(self):
        rng = np.random.default_rng(2)
        t = np.arange(4000) / C.SR
        h = np.r_[np.zeros(60), rng.standard_normal(4000) * 10 ** (-3 * t / 0.1)]
        h[60] = 3.0
        self.assertEqual(R.loi_hinh_dang(h, 60), [])
        h2 = h.copy()
        h2[5] = 2.0                                     # đỉnh lạ trước đường trực tiếp
        self.assertIn("truoc_dinh", R.loi_hinh_dang(h2, 60))
        h3 = h.copy()
        h3[-400:] = 0.5                                 # đuôi không tắt
        self.assertIn("duoi_khong_tat", R.loi_hinh_dang(h3, 60))
        h4 = h.copy()
        h4[100] = np.nan
        self.assertEqual(R.loi_hinh_dang(h4, 60), ["khong_huu_han"])


class TestGan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx, cls.cab, cls.loai, cls.meta = kho_gia()

    def gan(self, f):
        return rir_gan.gan_file(f, self.idx, self.cab, self.loai, self.meta)

    def test_chia_khoang_252_28_deu_moi_loai(self):
        ds = ds_khoang()
        sp = [s for *_, s in ds]
        self.assertEqual((sp.count("train"), sp.count("dev")), (252, 28))
        for lo in C.LOAI_XE:
            self.assertEqual(sum(d[1] == lo for d in ds), C.KHOANG_MOI_LOAI)
            self.assertEqual(sum(d[1] == lo and d[3] == "dev" for d in ds), C.KHOANG_DEV_MOI_LOAI)
        self.assertFalse(set(self.cab["train"]["mo_phong"]) & set(self.cab["dev"]["mo_phong"]))

    def test_hat_giong_khong_doi_khi_them_file(self):
        cu = [file_gia(i) for i in range(50)]
        truoc = [r for f in cu for r in self.gan(f)]
        gia = [file_gia(10_000 + i) for i in range(100)]
        sau = [r for f in gia[:50] + cu + gia[50:] for r in self.gan(f)]
        sau_cu = [r for r in sau if r["sample_id"] in {f["sample_id"] for f in cu}]
        self.assertEqual(truoc, sau_cu)

    def test_so_ban_va_hai_ban_khac_rir(self):
        n = {"train": 0, "dev": 0}
        for i in range(400):
            rows = self.gan(file_gia(i))
            sp = rows[0]["split"]
            n[sp] += 1
            self.assertEqual(len(rows), C.SO_BAN[sp])
            co = [r for r in rows if r["co_rir"]]
            self.assertEqual(len({r["khoang"] for r in co}), len(co))
            for r in rows:
                self.assertIn(r["khoang"], self.cab[sp]["mo_phong"]) if r["co_rir"] else self.assertEqual(r["rir_id"], "")
        self.assertGreater(n["dev"], 10)

    def test_dev_khong_dung_rir_train(self):
        rows = [r for i in range(600) for r in self.gan(file_gia(i))]
        tr = {r["rir_id"] for r in rows if r["split"] == "train" and r["co_rir"]}
        self.assertFalse({r["rir_id"] for r in rows if r["split"] == "dev" and r["co_rir"]} & tr)
        p = np.mean([r["co_rir"] for r in rows])
        self.assertAlmostEqual(p, C.P_RIR, delta=0.04)

    def test_cau_ghep_cung_split_khoang_voi_cau_goc(self):
        for i in range(200):
            goc = self.gan(file_gia(i))
            ghep = self.gan(file_gia(i, "ghep", goc=f"CS01-M1-{i:05d}"))
            self.assertEqual(len(goc), len(ghep))
            for a, b in zip(goc, ghep):
                self.assertEqual(a["split"], b["split"])
                if a["co_rir"] and b["co_rir"]:
                    self.assertEqual((a["khoang"], a["ghe"], a["micro"]), (b["khoang"], b["ghe"], b["micro"]))

    def test_chia_theo_nhom(self):
        """Câu cùng nhóm chia (vd cùng lõi câu) luôn cùng split, dù mã câu khác nhau."""
        for k in range(60):
            fs = [dict(file_gia(i), nhom_chia=f"core:loi{k}") for i in range(k * 10, k * 10 + 5)]
            self.assertEqual(len({self.gan(f)[0]["split"] for f in fs}), 1)

    def test_bo_rir_khong_dat(self):
        """RIR loại (dat = false) không bao giờ được gán."""
        rows = []
        for kh, lo, _, sp in ds_khoang():
            for m in C.MICRO:
                for g, d in GHE_DAU:
                    rows.append(dict(rir_id=rir_id(kh, g, m, d), khoang=kh, loai_xe=lo, ghe=g, micro=m, dau=d, split=sp,
                                     dat=not (g == "phu" and m == "tran" and d == 0)))
        idx, cab, loai, meta = rir_gan.chi_muc_kho(rows)
        got = {r["rir_id"] for i in range(800) for r in rir_gan.gan_file(file_gia(i), idx, cab, loai, meta) if r["co_rir"]}
        self.assertFalse({x for x in got if "_phu_tran_h0" in x})


def kho_do_gia():
    """Hai xe đo giả: do_tr (train) chỉ có micro táp-lô và cột A; do_dv (dev) chỉ có táp-lô."""
    rows = []
    for kh, sp, mics in (("do_tr", "train", ("tap_lo", "cot_a")), ("do_dv", "dev", ("tap_lo",))):
        for g in C.GHE:
            for m in mics:
                for k in range(3):
                    rows.append(dict(rir_id=f"rir_{kh}_{g}_{m}_v{k}", khoang=kh, loai_xe="sedan", ghe=g, micro=m,
                                     dau=f"v{k}", split=sp, dat=True, nguon="do"))
    return rows


class TestGanDo(unittest.TestCase):
    """Bảng gán có cả kho đo (ưu tiên RIR thật, P_RIR_DO)."""

    @classmethod
    def setUpClass(cls):
        sim = []
        for kh, lo, _, sp in ds_khoang():
            for m in C.MICRO:
                for g, d in GHE_DAU:
                    sim.append(dict(rir_id=rir_id(kh, g, m, d), khoang=kh, loai_xe=lo, ghe=g, micro=m, dau=d, split=sp,
                                    dat=True, nguon="mo_phong"))
        cls.sim = rir_gan.chi_muc_kho(sim)
        cls.k = rir_gan.chi_muc_kho(sim + kho_do_gia())

    def gan(self, f, p_do=C.P_RIR_DO):
        return rir_gan.gan_file(f, *self.k, p_do=p_do)

    def test_uu_tien_rir_do_khi_co(self):
        rows = [r for i in range(1500) for r in self.gan(file_gia(i)) if r["co_rir"]]
        # bản 0: bản 1 của cùng câu không được dùng lại xe đo duy nhất (hai bản khác xe) nên bị kéo về mô phỏng
        co_do = [r for r in rows if r["micro"] in ("tap_lo", "cot_a") and r["split"] == "train" and r["ban"] == 0]
        ty_le = np.mean([r["nguon_rir"] == "do" for r in co_do])
        self.assertAlmostEqual(ty_le, C.P_RIR_DO, delta=0.05)
        self.assertTrue(all(r["nguon_rir"] == "mo_phong" for r in rows if r["micro"] in ("tran", "guong")))
        self.assertTrue(all(r["khoang"] == "do_tr" for r in rows if r["nguon_rir"] == "do" and r["split"] == "train"))
        self.assertTrue(all(r["khoang"] != "do_tr" for r in rows if r["split"] == "dev"))

    def test_p_do_0_giong_chi_mo_phong(self):
        for i in range(200):
            self.assertEqual(self.gan(file_gia(i), p_do=0.0), rir_gan.gan_file(file_gia(i), *self.sim))

    def test_cau_ghep_cung_xe_do_voi_cau_goc(self):
        for i in range(300):
            goc = self.gan(file_gia(i))
            ghep = self.gan(file_gia(i, "ghep", goc=f"CS01-M1-{i:05d}"))
            for a, b in zip(goc, ghep):
                if a["co_rir"] and b["co_rir"]:
                    self.assertEqual((a["khoang"], a["ghe"], a["micro"], a["nguon_rir"]), (b["khoang"], b["ghe"], b["micro"], b["nguon_rir"]))


class TestKhoDo(unittest.TestCase):
    def test_ghe_va_micro_cavemove(self):
        from buoc.rir_kho_do import ghe_cavemove, micro_cua
        for vt, g in (("d50", "lai"), ("d63", "lai"), ("pf80", "phu"), ("pfr90", "phu"), ("prl66", "sau_trai"),
                      ("prl10r", "sau_trai"), ("prr67", "sau_phai"), ("prm", None), ("prm10l", None)):
            self.assertEqual(ghe_cavemove(vt), g, vt)
        self.assertEqual(set(micro_cua("cavemove", "Honda_CR-V", "array").values()), {"tap_lo"})
        self.assertEqual(len(micro_cua("cavemove", "Honda_CR-V", "array")), 8)
        golf = micro_cua("cavemove", "Volkswagen_Golf", "distributed")
        self.assertNotIn(7, golf)                       # micro trần sau không dùng
        self.assertEqual(set(golf.values()), {"tap_lo", "cot_a", "guong"})

    def test_cat_rir_lay_duong_den_dau_tien(self):
        from buoc.rir_kho_do import cat_rir
        rng = np.random.default_rng(3)
        h = np.zeros(6000)
        h[300], h[340] = 0.6, 1.0                       # phản xạ mạnh hơn đường trực tiếp
        h[341:] = rng.standard_normal(6000 - 341) * 0.05 * np.exp(-np.arange(6000 - 341) / 400)
        g, i = cat_rir(h)
        self.assertEqual(i, 40)
        self.assertAlmostEqual(g[i], 0.6)
        self.assertEqual(len(g), 40 + int(C.RIR_DAI_S * C.SR))


class TestCauHinh(unittest.TestCase):
    def test_kho_config_ghi_duoc_json(self):
        """rir_kho ghi mọi hằng số vào kho_config.json; MICRO_DO có khoá tuple (job hỏng mã 3 nếu không đổi)."""
        import json
        from buoc.rir_kho import khoa_chuoi
        cfg = {k: khoa_chuoi(v) for k, v in vars(C).items() if k.isupper()}
        s = json.dumps(cfg, ensure_ascii=False, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
        self.assertIn("cavemove|Volkswagen_Golf|distributed", s)

    def test_loai_xe_du_truong(self):
        for lo, cfg in C.LOAI_XE.items():
            self.assertEqual(set(cfg), {"dai", "rong", "cao", "x_hang1", "cach_hang"}, lo)
            self.assertIn(lo, C.XE_DAI_DIEN)
        self.assertTrue({v[2] for v in C.XE_DO.values()} <= set(C.LOAI_XE))


@unittest.skipUnless(CO_PRA, "cần pyroomacoustics (venv_rir)")
class TestKho(unittest.TestCase):
    def test_boc_tat_dinh_va_trong_hop(self):
        from buoc.rir_kho import bang_vat_lieu, boc
        bang = bang_vat_lieu()
        a = boc("suv_c", "suv_c03", 0, C.SEED, bang)
        self.assertEqual(a, boc("suv_c", "suv_c03", 0, C.SEED, bang))
        self.assertNotEqual(a[1], boc("suv_c", "suv_c03", 1, C.SEED, bang)[1])
        L, W, H = a[1]
        for p in a[3] + list(a[4].values()):
            self.assertTrue(0 < p[0] < L and 0 < p[1] < W and 0 < p[2] < H, p)
        for v in a[2].values():
            self.assertTrue(all(0.01 <= x <= 0.99 for x in v["hap_thu"]))

    def test_hang_ghe_theo_met_moi_loai(self):
        """Mọi loại: miệng hàng 2 sau hàng 1 và cách vách sau tối thiểu; micro trước miệng hàng 1; trong dải loại."""
        from buoc.rir_kho import GHE_DAU, bang_vat_lieu, boc
        bang = bang_vat_lieu()
        for lo, cfg in C.LOAI_XE.items():
            for k in range(30):
                _, (L, W, H), _, mieng, mic = boc(lo, f"{lo}{k:02d}", 0, C.SEED, bang)
                for v, ten in ((L, "dai"), (W, "rong"), (H, "cao")):
                    self.assertTrue(cfg[ten][0] <= v <= cfg[ten][1], (lo, ten, v))
                x = {g: [] for g in C.GHE}
                for (g, _), p in zip(GHE_DAU, mieng):
                    x[g].append(p[0])
                truoc = x["lai"] + x["phu"]
                sau = x["sau_trai"] + x["sau_phai"]
                self.assertGreater(min(sau) - max(truoc), 0.4, lo)       # lệch đầu ±0,1 m mỗi miệng
                self.assertLessEqual(max(sau), L - C.MIENG_CACH_VACH_SAU_MIN + C.LECH_DAU + 1e-9, lo)
                self.assertLess(max(p[0] for p in mic.values()), min(truoc), lo)

    def test_vat_lieu_rieng_ban_tai(self):
        from buoc.rir_kho import bang_vat_lieu, boc
        bang = bang_vat_lieu()
        bt = [boc("ban_tai", f"ban_tai{k:02d}", 0, C.SEED, bang)[2]["east"]["hap_thu"] for k in range(20)]
        se = [boc("sedan", f"sedan{k:02d}", 0, C.SEED, bang)[2]["east"]["hap_thu"] for k in range(20)]
        # vách sau bán tải có kính và kim loại nên hút âm cao tần (2–4 kHz) ít hơn lưng ghế bọc vải
        self.assertLess(np.mean([v[4:6] for v in bt]), np.mean([v[4:6] for v in se]))
        self.assertEqual(boc("ban_tai", "ban_tai00", 0, C.SEED, bang)[2]["west"]["tan_xa"], C.VAT_LIEU["west"]["tan_xa"])


if __name__ == "__main__":
    unittest.main()
