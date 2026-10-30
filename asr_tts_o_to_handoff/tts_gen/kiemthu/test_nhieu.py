# -*- coding: utf-8 -*-
"""Test cấu hình và phần tải của bước nhiễu (cauhinh/nhieu.py, buoc/nhieu_tai.py). Không dùng mạng."""
import io
import os
import tarfile
import tempfile
import unittest
import zipfile

import cauhinh.nhieu as N
import cauhinh.tang_cuong as C
from buoc import nhieu_tai


class TestNhieu(unittest.TestCase):
    def test_moi_preset_asr_mot_nhom_snr(self):
        ps = [p for g in N.SNR_THEO_NHOM.values() for p in g["preset"]]
        self.assertEqual(sorted(ps), [f"E{i:02d}" for i in range(1, 16)])      # E01–E15, E16/E17 thuộc M5
        for g in N.SNR_THEO_NHOM.values():
            self.assertLess(g["snr_db"][0], g["snr_db"][1])

    def test_cavemove_cung_zip_voi_kho_rir(self):
        self.assertEqual(N.NGUON_NHIEU["cavemove"]["url"], C.RIR_DO_NGUON["cavemove"]["url"])

    def test_duong_dan_an_toan(self):
        for p in ("a/b.wav", "cavemove_dataset/Golf/noise/s50_w0.wav"):
            self.assertTrue(nhieu_tai.an_toan(p))
        for p in ("/etc/passwd", "../x.wav", "a/../../x", "C:/x.wav", "a\\..\\..\\x"):
            self.assertFalse(nhieu_tai.an_toan(p), p)

    def test_tar_duong_dan_la_bi_chan(self):
        """tarfile filter='data' (dùng khi giải nén AISHELL-5) chặn tệp trỏ ra ngoài thư mục đích."""
        with tempfile.TemporaryDirectory() as d:
            b = io.BytesIO()
            with tarfile.open(fileobj=b, mode="w:gz") as t:
                ti = tarfile.TarInfo("../ngoai.txt")
                ti.size = 1
                t.addfile(ti, io.BytesIO(b"x"))
            b.seek(0)
            with tarfile.open(fileobj=b, mode="r:gz") as t, self.assertRaises(tarfile.FilterError):
                t.extract(t.getmembers()[0], os.path.join(d, "out"), filter="data")
            self.assertFalse(os.path.exists(os.path.join(d, "ngoai.txt")))

    def test_loc_thu_muc_cavemove(self):
        """Chỉ giải nén noise/, ventilation/, uncontrolled_conditions/ và info.json (dùng zip giả, không mạng)."""
        with tempfile.TemporaryDirectory() as d:
            zp = os.path.join(d, "cavemove", "cavemove_dataset.zip")
            os.makedirs(os.path.dirname(zp))
            ten = ["cavemove_dataset/Golf/distributed/noise/s50_w0.wav", "cavemove_dataset/Golf/distributed/IRs/d50.wav",
                   "cavemove_dataset/Golf/distributed/ventilation/v3_w0.wav", "cavemove_dataset/Golf/info.json",
                   "cavemove_dataset/Golf/distributed/uncontrolled_conditions/unc_001.wav"]
            with zipfile.ZipFile(zp, "w") as z:
                for t in ten:
                    z.writestr(t, b"x")
            md5 = nhieu_tai.bam(zp)
            cu = (nhieu_tai.tai_tiep, N.NGUON_NHIEU["cavemove"]["md5"])
            nhieu_tai.tai_tiep = lambda url, path: (os.path.getsize(path), url)
            N.NGUON_NHIEU["cavemove"]["md5"] = md5
            try:
                nhieu_tai.cavemove(d)
            finally:
                nhieu_tai.tai_tiep, N.NGUON_NHIEU["cavemove"]["md5"] = cu
            out = os.path.join(d, "cavemove", "giai_nen")
            co = {t for t in ten if os.path.exists(os.path.join(out, t))}
            self.assertEqual(co, set(ten) - {"cavemove_dataset/Golf/distributed/IRs/d50.wav"})


class TestDoNhieu(unittest.TestCase):
    def test_dac_trung_phan_biet_mua_va_nhip(self):
        """Hạt lộp độp cao tần làm tăng xung_cao_tan; nền điều biên chu kỳ 1,2 s cho nhip_s ≈ 1,2 và nhip_r cao."""
        import numpy as np
        from phantich.do_nhieu import dac_trung
        rng = np.random.default_rng(0)
        n = 20 * 16000
        nen = rng.standard_normal(n) * 0.01
        mua = nen.copy()
        for i in rng.integers(0, n - 40, 400):
            mua[i:i + 40] += rng.standard_normal(40) * 0.3
        t = np.arange(n) / 16000
        gat = nen * (1 + 0.9 * (np.sin(2 * np.pi * t / 1.2) > 0.6))
        a, b, c = dac_trung(nen), dac_trung(mua), dac_trung(gat)
        self.assertGreater(b["xung_cao_tan"], 5 * a["xung_cao_tan"] + 0.01)
        self.assertAlmostEqual(c["nhip_s"], 1.2, delta=0.1)
        self.assertGreater(c["nhip_r"], a["nhip_r"] + 0.2)
        self.assertAlmostEqual(a["muc_db"], -40.0, delta=0.5)


def kho_gia():
    """Kho nhiễu giả: mỗi preset × xe một tệp phân tán (8 kênh) và, với Golf, thêm một tệp mảng."""
    from buoc.nhieu_kho import GOC_CM
    rows = []
    for p in N.PRESET_GD1:
        for xe, sp in N.XE_NHIEU.items():
            for ch in (("distributed", "array") if xe == "Volkswagen_Golf" else ("distributed",)):
                rows.append(dict(nhieu_id=f"{p}_{xe}_{ch}_x", preset=p, split=sp, xe=xe, cau_hinh=ch, loai="noise",
                                 ten="x", tep=f"{GOC_CM}/{xe}/{ch}/noise/x.wav", dai_s=30.0, so_kenh=8, thay_the=False))
    return rows


def ban_gia(i, phan="thuong", split="train", micro="tap_lo", case="CS03"):
    goc = f"{case}-M1-{i:05d}"
    return dict(ban_id=f"{goc}__v__a0__r0", sample_id=goc + ("#w" if phan == "ghep" else ""), cau_goc=goc, ban=0,
                phan=phan, split=split, micro=micro, case_id=case, dai_s=3.0, muc_ra_dbfs=-26.0, vung="Bắc",
                audio=f"{split}/{goc}.flac")


class TestNhieuGan(unittest.TestCase):
    def test_tat_dinh_va_ghep_cung_preset(self):
        from buoc.nhieu_gan import gan_ban
        kho = kho_gia()
        a = [gan_ban(ban_gia(i), kho) for i in range(50)]
        b = [gan_ban(ban_gia(i), kho) for i in range(50)]
        self.assertEqual(a, b)
        for i in range(200):
            self.assertEqual(gan_ban(ban_gia(i), kho)["preset_moi_truong"],
                             gan_ban(ban_gia(i, phan="ghep"), kho)["preset_moi_truong"])

    def test_ty_le_sheet_va_preset_hop_le(self):
        from buoc.nhieu_gan import gan_ban
        kho = kho_gia()
        rows = [gan_ban(ban_gia(i, case="CS04"), kho) for i in range(3000)]       # CS04: sheet chỉ ghi E02 trong 6 preset
        self.assertAlmostEqual(sum(r["nguon_preset"] == "sheet" for r in rows) / len(rows), N.TY_LE_THEO_SHEET, delta=0.03)
        self.assertTrue(all(r["preset_moi_truong"] == "E02" for r in rows if r["nguon_preset"] == "sheet"))
        for r in rows:
            lo, hi = N.nhom_snr(r["preset_moi_truong"])
            self.assertTrue(lo <= r["snr_db"] <= hi)

    def test_dev_chi_golf_va_kenh_theo_micro(self):
        from buoc.nhieu_gan import gan_ban, kenh_cho
        kho = kho_gia()
        for i in range(300):
            r = gan_ban(ban_gia(i, split="dev", micro="tran"), kho)
            self.assertEqual(r["nhieu_xe"], "Volkswagen_Golf")
            self.assertIn(r["kenh"], N.KENH_TRAN)
            self.assertEqual(r["nhieu_cau_hinh"], "distributed")
            t = gan_ban(ban_gia(i, micro="cot_a"), kho)
            self.assertNotEqual(t["nhieu_xe"], "Volkswagen_Golf")
            self.assertIn(t["kenh"], kenh_cho("cot_a", t["nhieu_xe"], t["nhieu_cau_hinh"]))
        self.assertEqual(set(kenh_cho("tap_lo", "Volkswagen_Golf", "array")), set(range(1, 9)))

    def test_khong_nhan_factors_covered(self):
        from buoc.nhieu_gan import gan_ban
        with self.assertRaises(SystemExit):
            gan_ban(dict(ban_gia(0), factors_covered=["E06"]), kho_gia())


class TestNhieuKho(unittest.TestCase):
    def test_luat_preset_va_thay_the(self):
        from buoc.nhieu_kho import chon, nhan
        self.assertEqual(nhan("noise", "s110_w0_ver2"), (110, 0, False))
        self.assertEqual(nhan("noise", "s30_w1_coarse"), (30, 1, True))
        self.assertEqual(nhan("ventilation", "v3_w0"), (3, 0, False))
        tep = [("Smart_forfour", "distributed", "noise", t, 30.0, 8) for t in ("s0_w0", "s50_w0_ver1", "s60_w2_ver1",
                                                                              "s100_w0_ver1", "s30_w0_coarse", "s50_w1_ver1")]
        tep += [("Smart_forfour", "distributed", "ventilation", t, 30.0, 8) for t in ("v1_w0", "v3_w0", "v3_w1")]
        tep += [("Volkswagen_Golf", "distributed", "ventilation", "v1_w0", 30.0, 8)]      # Golf không có s0
        p = {(r["preset"], r["xe"]): r for r in chon(tep)}
        self.assertEqual(p[("E01", "Smart_forfour")]["ten"], "s0_w0")
        self.assertEqual(p[("E02", "Smart_forfour")]["ten"], "s50_w0_ver1")
        self.assertEqual(p[("E03", "Smart_forfour")]["ten"], "s100_w0_ver1")
        self.assertEqual(p[("E05", "Smart_forfour")]["ten"], "s60_w2_ver1")
        self.assertEqual(p[("E06", "Smart_forfour")]["ten"], "v3_w0")
        self.assertEqual(p[("E09", "Smart_forfour")]["ten"], "s30_w0_coarse")
        self.assertTrue(p[("E01", "Volkswagen_Golf")]["thay_the"])
        self.assertNotIn(("E02", "Volkswagen_Golf"), p)


class TestNhieuTron(unittest.TestCase):
    def test_snr_dung_va_khong_cat_dinh(self):
        import numpy as np
        from buoc.nhieu_tron import db, tron
        rng = np.random.default_rng(0)
        x = rng.standard_normal(32000) * 10 ** (-26 / 20)
        for snr in (20.0, 5.0, -5.0):
            nz = rng.standard_normal(32000) * 0.3
            y, info = tron(x, nz, -26.0, snr)
            self.assertAlmostEqual(info["snr_do_db"], snr, delta=0.1)
            self.assertAlmostEqual(db(y.astype(np.float64) / 10 ** (info["ha_chong_cat_db"] / 20) - x), -26 - snr, delta=0.1)
            self.assertLessEqual(info["dinh_ra_dbfs"], N.DINH_MAX_DBFS + 1e-6)
            self.assertLessEqual(20 * np.log10(np.max(np.abs(y))), N.DINH_MAX_DBFS + 1e-3)

    def test_viec_ban_tao_thu_muc_va_dung_snr(self):
        """Trộn một bản đầu-cuối: thư mục đầu ra chưa có vẫn ghi được; SNR đo lại từ tệp khớp SNR đặt."""
        import numpy as np
        import soundfile as sf
        from buoc.nhieu_tron import viec_ban
        rng = np.random.default_rng(1)
        with tempfile.TemporaryDirectory() as d:
            x = rng.standard_normal(16000 * 2) * 10 ** (-26 / 20)
            os.makedirs(os.path.join(d, "vang", "dev"))
            sf.write(os.path.join(d, "vang", "dev", "b.flac"), x, 16000, subtype="PCM_24")
            os.makedirs(os.path.join(d, "nhieu", "cm"))
            sf.write(os.path.join(d, "nhieu", "cm", "n.wav"), rng.standard_normal((16000 * 5, 8)) * 0.05, 16000, subtype="FLOAT")
            r = dict(ban_id="b", split="dev", audio="dev/b.flac", nhieu_tep="cm/n.wav", kenh=7, bat_dau_s=0.5,
                     muc_ra_dbfs=-26.0, snr_db=3.0)
            m = viec_ban((r, os.path.join(d, "vang"), os.path.join(d, "nhieu"), os.path.join(d, "ra", "chua_co")))
            y, _ = sf.read(os.path.join(d, "ra", "chua_co", m["audio"]))
            x2, _ = sf.read(os.path.join(d, "vang", "dev", "b.flac"))
            n = y / 10 ** (m["ha_chong_cat_db"] / 20) - x2
            self.assertAlmostEqual(-26 - 20 * np.log10(np.sqrt(np.mean(n ** 2))), 3.0, delta=0.1)
            self.assertEqual(m["audio_vang"], "dev/b.flac")

    def test_doc_doan_dung_kenh_va_noi_vong(self):
        import numpy as np
        import soundfile as sf
        from buoc.nhieu_tron import doc_doan
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "n.wav")
            x = np.tile(np.arange(1, 9) / 100.0, (16000 * 3, 1))          # 3 s, kênh k có giá trị k/100
            sf.write(p, x, 16000, subtype="FLOAT")
            a = doc_doan(p, 3, 0.6, 8000)
            self.assertEqual(len(a), 8000)
            self.assertTrue(np.allclose(a, 0.03))
            b = doc_doan(p, 7, 0.5, 16000 * 5)                             # dài hơn tệp: nối vòng
            self.assertEqual(len(b), 16000 * 5)
            self.assertTrue(np.allclose(b, 0.07))


if __name__ == "__main__":
    unittest.main()
