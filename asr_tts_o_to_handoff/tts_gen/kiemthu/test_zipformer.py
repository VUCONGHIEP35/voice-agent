# -*- coding: utf-8 -*-
"""Test phần Zipformer: dựng tokens.txt, tên tag, cấu hình Z trong gate_union (không cần mô hình)."""
import os
import tempfile
import unittest

import buoc.tai_zipformer as fetch_zipformer  # noqa: E402
import buoc.cham as gate_union  # noqa: E402
from buoc.asr_zipformer import make_tag  # noqa: E402


def row(n_syl=6, **cers):
    r = dict(tts_check="dat", n_syl=n_syl)
    for c in gate_union.CONFIGS:
        r[f"cer_{c}"] = cers.get(c, "")
    return r


class TestTokens(unittest.TestCase):
    def build(self, text):
        d = tempfile.mkdtemp()
        src, dst = os.path.join(d, "config.json"), os.path.join(d, "tokens.txt")
        open(src, "w", encoding="utf-8").write(text)
        return fetch_zipformer.build_tokens(src, dst), open(dst, encoding="utf-8").read()

    def test_dung(self):
        n, out = self.build("<blk> 0\n<sos/eos> 1\n<unk> 2\n▁KHÔNG 3\n")
        self.assertEqual(n, 4)
        self.assertTrue(out.startswith("<blk> 0\n"))

    def test_id_khong_lien_tuc(self):
        with self.assertRaises(SystemExit):
            self.build("<blk> 0\n▁A 2\n")

    def test_blk_khong_phai_0(self):
        with self.assertRaises(SystemExit):
            self.build("▁A 0\n<blk> 1\n")

    def test_dong_la(self):
        with self.assertRaises(SystemExit):
            self.build('{"json": true}\n')


class TestTag(unittest.TestCase):
    def test_tag(self):
        self.assertEqual(make_tag("int8", "greedy_search", 4), "Zipformer-30M-int8")
        self.assertEqual(make_tag("int8", "modified_beam_search", 4), "Zipformer-30M-int8-beam4")
        self.assertEqual(gate_union.FILES["Z"], "asr_Zipformer-30M-int8-beam4.jsonl")


class TestGateZ(unittest.TestCase):
    def test_z_chi_gop_dat_1nguon(self):
        m = dict(speaker_region="Bắc", n_syllables=6)
        v, why, ok = gate_union.judge(m, {"L": 0.3, "M": 0.3, "Z": 0.0}, {}, "dat", 0.10)
        self.assertEqual((v, ok), ("dat_1nguon", ["Z"]))
        v, _, _ = gate_union.judge(m, {"L": 0.0, "M": 0.05, "Z": 0.5}, {}, "dat", 0.10)
        self.assertEqual(v, "dat")

    def test_hai_tren_ba(self):
        rows = [row(L=0.0, M=0.5, Z=0.05), row(L=0.5, M=0.5, Z=0.0), row(L=0.0, M=0.0, Z=0.9),
                row(n_syl=2, L=0.0, M=0.1, Z=0.0), dict(row(L=0.0, M=0.0, Z=0.0), tts_check="loi:cat_dau")]
        self.assertEqual(gate_union.two_of_three(rows, 0.10), 3)

    def test_marginal_co_z(self):
        rows = [row(L=0.5, M=0.5, Z=0.0), row(L=0.0, M=0.5, Z=0.5)]
        res = gate_union.marginal(rows, ["L", "M", "Z"], 0.10)
        self.assertEqual(res["chi_nho"]["Z"], 1)
        self.assertEqual(res["tap"]["L+Z"], 2)


if __name__ == "__main__":
    unittest.main()
