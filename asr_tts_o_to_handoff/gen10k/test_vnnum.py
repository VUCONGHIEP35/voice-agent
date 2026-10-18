# -*- coding: utf-8 -*-
"""Test bộ đọc số. Chạy: py -3.13 test_vnnum.py"""
import unittest
from vnnum import read_int, read_digits, read_decimal, normalize


class TestReadInt(unittest.TestCase):
    def test_basic(self):
        cases = {0: "không", 1: "một", 5: "năm", 10: "mười", 11: "mười một", 14: "mười bốn", 15: "mười lăm",
                 20: "hai mươi", 21: "hai mươi mốt", 24: "hai mươi tư", 25: "hai mươi lăm", 31: "ba mươi mốt",
                 44: "bốn mươi tư", 55: "năm mươi lăm", 91: "chín mươi mốt", 99: "chín mươi chín", 100: "một trăm",
                 110: "một trăm mười", 115: "một trăm mười lăm", 121: "một trăm hai mươi mốt", 999: "chín trăm chín mươi chín"}
        for region in ("Bắc", "Trung", "Nam"):
            for n, s in cases.items():
                self.assertEqual(read_int(n, region), s, (n, region))

    def test_linh_le(self):
        # linh (Bắc), lẻ (Trung, Nam) — theo src_lang.json (L5, L14)
        self.assertEqual(read_int(105, "Bắc"), "một trăm linh năm")
        self.assertEqual(read_int(105, "Trung"), "một trăm lẻ năm")
        self.assertEqual(read_int(105, "Nam"), "một trăm lẻ năm")
        self.assertEqual(read_int(101, "Bắc"), "một trăm linh một")
        self.assertEqual(read_int(104, "Nam"), "một trăm lẻ bốn")
        self.assertEqual(read_int(108, "Bắc"), "một trăm linh tám")

    def test_nghin_ngan(self):
        self.assertEqual(read_int(1000, "Bắc"), "một nghìn")
        self.assertEqual(read_int(1000, "Nam"), "một ngàn")
        self.assertEqual(read_int(1000, "Trung"), "một ngàn")
        self.assertEqual(read_int(1200, "Bắc"), "một nghìn hai trăm")
        self.assertEqual(read_int(1200, "Nam"), "một ngàn hai trăm")
        self.assertEqual(read_int(1005, "Bắc"), "một nghìn không trăm linh năm")
        self.assertEqual(read_int(1005, "Nam"), "một ngàn không trăm lẻ năm")
        self.assertEqual(read_int(1050, "Bắc"), "một nghìn không trăm năm mươi")
        self.assertEqual(read_int(50000, "Bắc"), "năm mươi nghìn")
        self.assertEqual(read_int(50000, "Trung"), "năm mươi ngàn")
        self.assertEqual(read_int(3500, "Nam"), "ba ngàn năm trăm")

    def test_large(self):
        self.assertEqual(read_int(1500000, "Bắc"), "một triệu năm trăm nghìn")
        self.assertEqual(read_int(2000000, "Nam"), "hai triệu")
        self.assertEqual(read_int(1005000, "Bắc"), "một triệu không trăm linh năm nghìn")
        self.assertEqual(read_int(1000000000, "Bắc"), "một tỷ")
        self.assertEqual(read_int(25000, "Bắc"), "hai mươi lăm nghìn")


class TestDigitsDecimals(unittest.TestCase):
    def test_phone(self):
        self.assertEqual(read_digits("0912 345 678"), "không chín một hai, ba bốn năm, sáu bảy tám")
        self.assertEqual(read_digits("0903 456 789"), "không chín không ba, bốn năm sáu, bảy tám chín")

    def test_emergency(self):
        self.assertEqual(read_digits("115"), "một một năm")
        self.assertEqual(read_digits("113"), "một một ba")
        self.assertEqual(read_digits("114"), "một một bốn")

    def test_decimal(self):
        self.assertEqual(read_decimal("22,5", "Bắc"), "hai mươi hai phẩy năm")
        self.assertEqual(read_decimal("102,7", "Bắc"), "một trăm linh hai phẩy bảy")
        self.assertEqual(read_decimal("102,7", "Nam"), "một trăm lẻ hai phẩy bảy")
        self.assertEqual(read_decimal("0,25", "Nam"), "không phẩy hai mươi lăm")
        self.assertEqual(read_decimal("1,05", "Bắc"), "một phẩy không năm")


class TestNormalize(unittest.TestCase):
    def n(self, s, r="Bắc"):
        return normalize(s, r).text

    def test_units(self):
        self.assertEqual(self.n("Gọi cấp cứu 115"), "Gọi cấp cứu một một năm")
        self.assertEqual(self.n("Gọi 113 ngay"), "Gọi một một ba ngay")
        self.assertEqual(self.n("Gọi 114, cháy ở đây"), "Gọi một một bốn, cháy ở đây")
        self.assertEqual(self.n("Gọi 115."), "Gọi một một năm.")
        self.assertEqual(self.n("Còn 114,5 km"), "Còn một trăm mười bốn phẩy năm ki lô mét")
        self.assertEqual(self.n("Gọi số 0912 345 678"), "Gọi số không chín một hai, ba bốn năm, sáu bảy tám")
        self.assertEqual(self.n("Sạc từ 20% lên 80%"), "Sạc từ hai mươi phần trăm lên tám mươi phần trăm")
        self.assertEqual(self.n("Bật điều hòa 24 độ"), "Bật điều hòa hai mươi tư độ")
        self.assertEqual(self.n("Đặt 22,5 độ"), "Đặt hai mươi hai phẩy năm độ")
        self.assertEqual(self.n("Còn 15 km nữa"), "Còn mười lăm ki lô mét nữa")
        self.assertEqual(self.n("Chạy 60 km/h"), "Chạy sáu mươi ki lô mét trên giờ")
        self.assertEqual(self.n("Mở FM 91 MHz"), "Mở ép em chín mươi mốt mê ga héc")
        self.assertEqual(self.n("Mở FM 102,7 MHz", "Nam"), "Mở ép em một trăm lẻ hai phẩy bảy mê ga héc")
        self.assertEqual(self.n("Giá 50.000 đồng", "Bắc"), "Giá năm mươi nghìn đồng")
        self.assertEqual(self.n("Giá 50.000 đồng", "Nam"), "Giá năm mươi ngàn đồng")
        self.assertEqual(self.n("Số 105", "Bắc"), "Số một trăm linh năm")
        self.assertEqual(self.n("Số 105", "Trung"), "Số một trăm lẻ năm")
        self.assertEqual(self.n("Tính 12 x 15"), "Tính mười hai nhân mười lăm")
        self.assertEqual(self.n("Bật 24°C"), "Bật hai mươi tư độ xê")
        self.assertEqual(self.n("Mở kênh VOV Giao thông"), "Mở kênh vê ô vê Giao thông")
        self.assertEqual(self.n("Phát nhạc từ USB"), "Phát nhạc từ u ét bê")

    def test_no_digit_left(self):
        for s in ["Bật camera 360", "Đổi 100 USD sang VND", "Chỉ số bụi PM2.5 hiện tại là bao nhiêu", "Còn 1.250 km"]:
            out = self.n(s)
            self.assertFalse(any(c.isdigit() for c in out), out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
