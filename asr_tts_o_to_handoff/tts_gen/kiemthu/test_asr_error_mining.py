# -*- coding: utf-8 -*-
"""Test chuẩn hóa vị trí dấu thanh trong asr_error_mining. Chạy: python -m unittest test_asr_error_mining"""
import unittest

from thuvien.van_ban import norm_text, unify_tone_placement  # noqa: E402
from thuvien.cham_chu import cer  # noqa: E402


class TonePlacement(unittest.TestCase):
    def test_kieu_moi_ve_kieu_cu(self):
        for new, old in (("hoả", "hỏa"), ("khoẻ", "khỏe"), ("thuỷ", "thủy"), ("hoà", "hòa"), ("loạ", "lọa")):
            self.assertEqual(unify_tone_placement(new), old)

    def test_giu_nguyen(self):
        for w in ("hỏa", "quý", "quỳ", "hoàng", "toán", "huỳnh", "thuế", "khuya", "hoa", "tôi", "chill"):
            self.assertEqual(unify_tone_placement(w), w)

    def test_cer_khong_tinh_khac_kieu_dau(self):
        self.assertEqual(cer("Gọi cứu hỏa.", "gọi cứu hoả"), 0.0)
        self.assertEqual(norm_text("Điều Hoà, Thuỷ"), "điều hòa thủy")


if __name__ == "__main__":
    unittest.main()
