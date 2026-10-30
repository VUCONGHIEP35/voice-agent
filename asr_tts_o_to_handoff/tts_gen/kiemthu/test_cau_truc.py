# -*- coding: utf-8 -*-
"""Giữ cấu trúc layer: phụ thuộc chỉ đi một chiều (docs/cau_truc_ma.md).
  cauhinh  -> (không import gì của dự án)
  thuvien  -> cauhinh, thuvien
  buoc     -> cauhinh, thuvien, buoc
  phantich -> cauhinh, thuvien, buoc, phantich
  dieuphoi -> cauhinh, thuvien, buoc, dieuphoi           (gọi bước qua python -m buoc.<tên>)
  kiemthu  -> mọi lớp trừ luutru
Không lớp nào import luutru (lưu trữ, không bảo trì)."""
import ast
import glob
import os
import unittest

from cauhinh.duong_dan import GOC

CHO_PHEP = {
    "cauhinh": set(),
    "thuvien": {"cauhinh", "thuvien"},
    "buoc": {"cauhinh", "thuvien", "buoc"},
    "phantich": {"cauhinh", "thuvien", "buoc", "phantich"},
    "dieuphoi": {"cauhinh", "thuvien", "buoc", "dieuphoi"},
    "kiemthu": {"cauhinh", "thuvien", "buoc", "phantich", "dieuphoi", "kiemthu"},
}
LOP = set(CHO_PHEP) | {"luutru"}


def imports_of(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name.split(".")[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module.split(".")[0], node.lineno


class TestCauTruc(unittest.TestCase):
    def test_phu_thuoc_mot_chieu(self):
        sai = []
        for lop, cho in CHO_PHEP.items():
            for f in glob.glob(os.path.join(GOC, lop, "*.py")):
                for mod, ln in imports_of(f):
                    if mod in LOP and mod not in cho:
                        sai.append(f"{os.path.relpath(f, GOC)}:{ln} import {mod}")
        self.assertEqual(sai, [])

    def test_khong_con_script_o_goc(self):
        """Mã chỉ nằm trong các lớp; gốc tts_gen/ không còn .py rời."""
        self.assertEqual(glob.glob(os.path.join(GOC, "*.py")), [])

    def test_lop_co_init(self):
        for lop in CHO_PHEP:                     # luutru/ không có trong gói gửi lên máy chủ nên không bắt buộc
            self.assertTrue(os.path.exists(os.path.join(GOC, lop, "__init__.py")), lop)


if __name__ == "__main__":
    unittest.main()
