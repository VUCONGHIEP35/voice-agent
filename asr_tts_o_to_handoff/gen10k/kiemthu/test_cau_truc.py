# -*- coding: utf-8 -*-
"""Giữ cấu trúc layer của gen10k/: phụ thuộc chỉ đi một chiều (docs/cau_truc_ma.md).
  cauhinh     -> (không import gì của dự án)
  nguyen_lieu -> cauhinh, nguyen_lieu          (kho khe, khung câu, từ vùng, từ ngoại)
  thuvien     -> cauhinh, nguyen_lieu, thuvien  (đọc số, điền khe, khung mang/lõi câu)
  buoc        -> mọi lớp trên + buoc            (build10k, make_v31, validate10k)
  phantich    -> mọi lớp trên + buoc, phantich
  kiemthu     -> mọi lớp trừ luutru
Không lớp nào import luutru (lưu trữ, không bảo trì)."""
import ast
import glob
import os
import unittest

from cauhinh.duong_dan import GOC

CHO_PHEP = {
    "cauhinh": set(),
    "nguyen_lieu": {"cauhinh", "nguyen_lieu"},
    "thuvien": {"cauhinh", "nguyen_lieu", "thuvien"},
    "buoc": {"cauhinh", "nguyen_lieu", "thuvien", "buoc"},
    "phantich": {"cauhinh", "nguyen_lieu", "thuvien", "buoc", "phantich"},
    "kiemthu": {"cauhinh", "nguyen_lieu", "thuvien", "buoc", "phantich", "kiemthu"},
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
        """Mã chỉ nằm trong các lớp; gốc gen10k/ không còn .py rời."""
        self.assertEqual(glob.glob(os.path.join(GOC, "*.py")), [])

    def test_khong_con_import_kieu_cu(self):
        """Import phẳng kiểu cũ (import pools10k, from vnnum import …) chỉ chạy được khi sys.path trỏ vào gen10k/."""
        cu = {os.path.splitext(os.path.basename(f))[0] for lop in LOP for f in glob.glob(os.path.join(GOC, lop, "*.py"))}
        sai = [f"{os.path.relpath(f, GOC)}:{ln} import {mod}"
               for lop in CHO_PHEP for f in glob.glob(os.path.join(GOC, lop, "*.py"))
               for mod, ln in imports_of(f) if mod in cu]
        self.assertEqual(sai, [])

    def test_lop_co_init(self):
        for lop in CHO_PHEP:
            self.assertTrue(os.path.exists(os.path.join(GOC, lop, "__init__.py")), lop)


if __name__ == "__main__":
    unittest.main()
