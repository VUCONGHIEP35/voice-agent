# -*- coding: utf-8 -*-
"""Test cho tts_checks.check bằng sóng tổng hợp. Chạy: python -m unittest test_tts_checks"""
import unittest

import numpy as np

from thuvien.kiem_am_thanh import check  # noqa: E402

SR = 16000


def tone(sec, amp=0.3, f=200.0):
    t = np.arange(int(sec * SR)) / SR
    return (amp * np.sin(2 * np.pi * f * t)).astype(np.float32)


def silence(sec, amp=0.0):
    rng = np.random.default_rng(0)
    return (amp * rng.standard_normal(int(sec * SR))).astype(np.float32)


class Check(unittest.TestCase):
    def test_bat_dau_ngay_bang_tieng_noi_la_cat_dau(self):
        why, hd = check(tone(1.0), n_syl=4, speech_s=1.0)
        self.assertEqual(why, ["cat_dau"])
        self.assertGreater(hd, -40)

    def test_co_50ms_im_lang_dau_la_dat(self):
        why, _ = check(np.concatenate([silence(0.05), tone(1.0)]), n_syl=4, speech_s=1.0)
        self.assertEqual(why, [])

    def test_nhieu_nen_nho_o_dau_van_dat(self):
        why, hd = check(np.concatenate([silence(0.05, amp=0.003), tone(1.0)]), n_syl=4, speech_s=1.0)
        self.assertEqual(why, [])
        self.assertLess(hd, -40)

    def test_tieng_noi_qua_dai_so_voi_so_am_tiet(self):
        why, _ = check(np.concatenate([silence(0.05), tone(3.0)]), n_syl=3, speech_s=3.0)
        self.assertEqual(why, ["noi_lan_man"])

    def test_tieng_noi_qua_ngan_so_voi_so_am_tiet(self):
        why, _ = check(np.concatenate([silence(0.05), tone(0.2)]), n_syl=5, speech_s=0.2)
        self.assertEqual(why, ["doc_thieu"])

    def test_toc_do_bien_cua_pilot_van_dat(self):  # pilot100: 2,7 và 6,3 âm tiết/giây đều là câu tốt
        for rate in (2.7, 6.3):
            why, _ = check(np.concatenate([silence(0.05), tone(2.0)]), n_syl=10, speech_s=10 / rate)
            self.assertEqual(why, [], rate)

    def test_cat_dau_va_noi_lan_man_cung_luc(self):
        why, _ = check(tone(3.0), n_syl=2, speech_s=3.0)
        self.assertEqual(why, ["cat_dau", "noi_lan_man"])


if __name__ == "__main__":
    unittest.main()
