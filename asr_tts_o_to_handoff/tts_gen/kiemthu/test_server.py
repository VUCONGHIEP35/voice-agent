# -*- coding: utf-8 -*-
"""Test cho phần chạy trên máy chủ: hồ sơ đóng gói (không lọt tệp cấm), T chỉ đo trong gate_union, check_run, ghi_buoc."""
import collections
import json
import os
import sys
import tempfile
import unittest

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
import buoc.kiem_luot as check_run  # noqa: E402
import buoc.cham as gate_union  # noqa: E402
import dieuphoi.ghi_buoc as ghi_buoc  # noqa: E402
import dieuphoi.dong_goi as pack_colab  # noqa: E402


def touch(root, rel, text="x"):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


class TestPack(unittest.TestCase):
    def test_tep_cam(self):
        bad = ["giong_that/a.wav", "giong_that/ket_qua_zipformer.xlsx", "runs/x/audio48/a.flac", "a.mp3", ".venv_zip/x.py",
               ".venv/Lib/x.py", "__pycache__/a.pyc", "KET_NOI_USER04/00_SSH_KEYS/id_ed25519", "id_ed25519.pub",
               ".mcp.json", "docs/phien_claude_ai.jsonl", ".cache/hf/x.json", ".cache/zipformer30m/ad6f873b/tokens.txt",
               "k.pem"]
        for rel in bad:
            self.assertFalse(pack_colab.allowed(rel), rel)
        for rel in ["buoc/tts.py", "server/chay_eval.sbatch", "lexicon/asr_bien_the.tsv", "eval1000_tts/shard_B.jsonl",
                    ".cache/ct2/PhoWhisper-large-int8/nguon.json", "requirements_server.txt"]:
            self.assertTrue(pack_colab.allowed(rel), rel)

    def test_ho_so_server(self):
        root = tempfile.mkdtemp()
        for rel in ["buoc/tts.py", "thuvien/a.py", "cauhinh/giong.py", "dieuphoi/slurm/setup_server.sh", "phantich/b.py",
                    "kiemthu/test_x.py", "luutru/cu.py", "goc_cu.py", "eval1000_tts/shard_B.jsonl", "lexicon/l.tsv",
                    "requirements_server.txt", "giong_that/x.wav", "runs/eval1000_A/logs/input_smoke24.jsonl",
                    "runs/eval1000_A/manifest.jsonl", ".cache/ct2/PhoWhisper-large-int8/nguon.json", ".cache/hf/big.bin",
                    "pilot/p.jsonl", "nb.ipynb"]:
            touch(root, rel)
        got = set(pack_colab.files(pack_colab.PROFILES["server"]["pats"], root=root))
        self.assertEqual(got, {"buoc/tts.py", "thuvien/a.py", "cauhinh/giong.py", "dieuphoi/slurm/setup_server.sh",
                               "phantich/b.py", "kiemthu/test_x.py", "eval1000_tts/shard_B.jsonl", "lexicon/l.tsv",
                               "requirements_server.txt", "runs/eval1000_A/logs/input_smoke24.jsonl",
                               ".cache/ct2/PhoWhisper-large-int8/nguon.json"})          # luutru/ và .py ở gốc: không đóng gói

    def test_ho_so_colab_giu_nguyen(self):
        self.assertEqual(pack_colab.PROFILES["colab"]["zip"], "colab_eval_A.zip")
        self.assertIn("runs/pilot100/manifest.jsonl", pack_colab.PROFILES["colab"]["pats"])


class TestChiDoT(unittest.TestCase):
    def test_T_khong_vao_cham(self):
        self.assertNotIn("T", gate_union.CONFIGS)
        self.assertIn("T", gate_union.MEASURE_ONLY)
        self.assertEqual(gate_union.FILES["T"], "asr_PhoWhisper-small.jsonl")

    def test_ket_qua_khong_doi_khi_co_T(self):
        """Chạy gate_union trên một lượt giả hai lần: không có và có asr_PhoWhisper-small.jsonl -> ket_qua giống hệt."""
        run = tempfile.mkdtemp()
        rows = [("u1", "Bật điều hòa lên.", "bật điều hòa lên", "bật điều hòa lên"),
                ("u2", "Mở cửa sổ bên phụ.", "mở của sổ bên phụ", "sai hết rồi"),
                ("u3", "Tìm trạm sạc gần nhất.", "tìm trạm sát gần nhất", "tìm trạm sạc gần nhất")]
        with open(os.path.join(run, "manifest.jsonl"), "w", encoding="utf-8") as f:
            for i, (u, t, _, _) in enumerate(rows):
                f.write(json.dumps(dict(utt_id=u, sample_id=f"S{i}", text_spoken=t, speaker_region="Bắc", voice="V",
                                        n_syllables=5, tts_check="dat", audio16="x.flac"), ensure_ascii=False) + "\n")
        for fn, k in (("asr_PhoWhisper-large-ct2-int8.jsonl", 2), ("asr_PhoWhisper-medium.jsonl", 2)):
            with open(os.path.join(run, fn), "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(dict(utt_id=r[0], hyp=r[k]), ensure_ascii=False) + "\n")

        def verdicts(name):
            sys_argv = sys.argv
            sys.argv = ["buoc/cham.py", run, "--out-name", name]
            try:
                gate_union.main()
            finally:
                sys.argv = sys_argv
            import csv
            with open(os.path.join(run, f"{name}.csv"), encoding="utf-8-sig") as f:
                return {r["utt_id"]: (r["ket_qua"], r["cau_hinh_dat"]) for r in csv.DictReader(f)}

        before = verdicts("khong_T")
        with open(os.path.join(run, "asr_PhoWhisper-small.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(dict(utt_id=r[0], hyp=r[3]), ensure_ascii=False) + "\n")
        after = verdicts("co_T")
        self.assertEqual(before, after)
        summ = json.load(open(os.path.join(run, "co_T_tom_tat.json"), encoding="utf-8"))
        self.assertEqual(summ["chi_do"], ["T"])
        self.assertNotIn("T", summ["cau_hinh"])
        self.assertIn("T", summ["cer_tb"]["Tất cả"])


class TestCheckRun(unittest.TestCase):
    def setUp(self):
        self.run = tempfile.mkdtemp()
        self.plan = os.path.join(self.run, "plan.jsonl")
        with open(self.plan, "w", encoding="utf-8") as f:
            for s, tt in (("S1", None), ("S2", "mở gu gồ mép")):
                f.write(json.dumps(dict(sample_id=s, tts_text=tt), ensure_ascii=False) + "\n")

    def write_man(self, rows):
        with open(os.path.join(self.run, "manifest.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                for k in ("audio48", "audio16"):
                    touch(self.run, r[k])
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def row(self, sid, **kw):
        return dict(dict(utt_id=f"{sid}__V__a0", sample_id=sid, voice="V", tts_check="dat", tts_input="x",
                         audio48=f"audio48/{sid}.flac", audio16=f"audio16/{sid}.flac"), **kw)

    def test_dat(self):
        self.write_man([self.row("S1"), self.row("S2", tts_input="mở gu gồ mép")])
        res, stop = check_run.check(self.run, self.plan)
        self.assertEqual(stop, [])
        self.assertEqual(res["sample_id_duy_nhat"], 2)

    def test_thieu_cau_va_tts_text(self):
        self.write_man([self.row("S2", tts_input="mở google maps")])
        res, stop = check_run.check(self.run, self.plan)
        self.assertEqual(res["so_thieu"], 1)
        self.assertEqual(len(stop), 2)

    def test_sinh_lai_qua_nguong(self):
        self.write_man([self.row("S1", retries=[{"attempt": 0}]), self.row("S2", tts_input="mở gu gồ mép")])
        _, stop = check_run.check(self.run, self.plan, max_retry_rate=0.25)
        self.assertTrue(any("sinh lại" in s for s in stop))


class TestGhiBuoc(unittest.TestCase):
    def test_ghi_va_xong(self):
        run = tempfile.mkdtemp()
        touch(run, "manifest.jsonl", json.dumps({"utt_id": "u1"}) + "\n" + json.dumps({"utt_id": "u2"}) + "\n")
        touch(run, "run_config.json", "{}")
        self.assertFalse(ghi_buoc.asr_xong(run, "M"))
        touch(run, "asr_M.jsonl", json.dumps({"utt_id": "u1"}) + "\n")
        self.assertFalse(ghi_buoc.asr_xong(run, "M"))
        touch(run, "asr_M.jsonl", json.dumps({"utt_id": "u1"}) + "\n" + json.dumps({"utt_id": "u2"}) + "\n")
        self.assertTrue(ghi_buoc.asr_xong(run, "M"))
        touch(run, "asr_diagnose.csv", "utt_id,hyp_c0\nu1,a\nu2,b\n")
        self.assertFalse(ghi_buoc.diag_xong(run))
        touch(run, "asr_diagnose.csv", "utt_id,hyp_c0,hyp_c3\nu1,a,a\nu2,b,b\n")
        self.assertTrue(ghi_buoc.diag_xong(run))
        if hasattr(os, "uname"):
            ghi_buoc.ghi(run, "asr_medium", "12.34", "0")
            ghi_buoc.ghi(run, "asr_medium", "1", "0")
            t = json.load(open(os.path.join(run, "logs", "thoi_gian_asr.json")))
            self.assertEqual(t["asr_medium"], 13.3)
            self.assertEqual(len(json.load(open(os.path.join(run, "run_config.json")))["server_steps"]), 2)


class TestLuatV2(unittest.TestCase):
    def test_bo_tu_dem(self):
        self.assertEqual(gate_union.strip_fillers("ờ mở điều hòa ừm nhé"), "mở điều hòa nhé")

    def test_tu_noi_dung_sai(self):
        bad, _ = gate_union.content_errors("đến thành phố hồ chí minh còn bao xa", "đến thành phố chí minh còn bao xa")
        self.assertEqual(bad, [3])
        bad, _ = gate_union.content_errors("kiểm tra lốp sau nhé", "kiểm tra lốp sau")          # tiểu từ cuối: miễn
        self.assertEqual(bad, [])
        bad, st = gate_union.content_errors("trợ lý ơi bật đèn", "trợ lý bật đèn")              # 'ơi': miễn
        self.assertEqual(bad, [])

    def test_z_can_c3_hoac_cer_thap(self):
        ok = gate_union.config_pass_v2({"L": 0.3, "M": 0.3, "c3": 0.3, "Z": 0.08}, {}, 8, 0.10)
        self.assertFalse(ok["Z"])
        ok = gate_union.config_pass_v2({"L": 0.3, "M": 0.3, "c3": 0.05, "Z": 0.08}, {}, 8, 0.10)
        self.assertTrue(ok["Z"] and ok["c3"])
        ok = gate_union.config_pass_v2({"L": 0.3, "M": 0.3, "c3": 0.3, "Z": 0.04}, {}, 8, 0.10)
        self.assertTrue(ok["Z"])
        ok = gate_union.config_pass_v2({"L": 0.05, "M": 0.0}, {"L": [2]}, 8, 0.10)          # CER thấp nhưng sai từ nội dung
        self.assertEqual(ok, {"L": False, "M": True})

    def test_tu_dau_lech(self):
        m = dict(speaker_region="Bắc", n_syllables=8)
        v, why, _ = gate_union.judge_v2(m, {"L": False, "M": True, "Z": False}, {}, {"L": False, "M": True, "Z": True}, "dat", 0.10)
        self.assertEqual((v, why), ("can_nghe", "tu_dau_lech"))
        v, why, _ = gate_union.judge_v2(m, {"L": False, "M": True, "Z": False}, {}, {"L": True, "M": True, "Z": True}, "dat", 0.10)
        self.assertEqual(v, "dat_1nguon")
        v, _, _ = gate_union.judge_v2(m, {"L": True, "M": True}, {}, {"L": True, "M": True, "Z": False}, "dat", 0.10)
        self.assertEqual(v, "dat")


class TestDieuPhoi(unittest.TestCase):
    """Bộ điều phối với tác vụ giả: đúng thứ tự phụ thuộc, có chạy song song, phần lỗi không kéo phần khác."""

    def run_fake(self, fail_stage=None):
        import dieuphoi.dieu_phoi as D  # noqa: E402
        tmp = tempfile.mkdtemp()
        D.TG, D.PY, D.BASE = tmp, sys.executable, tmp
        os.makedirs(os.path.join(tmp, "runs"), exist_ok=True)
        stamp = os.path.join(tmp, "stamp.txt")

        class FakeShard(D.Shard):
            def done(self, st):
                return False

            def need_ok(self, st):
                return True

            def cmd(self, st):
                code = 1 if (self.name == "b" and st == fail_stage) else 0
                return [sys.executable, "-c", f"import time,sys; open(r'{stamp}','a').write('{self.name}/{st} start %f\\n' % time.time());"
                        f"time.sleep(0.4); open(r'{stamp}','a').write('{self.name}/{st} end %f\\n' % time.time()); sys.exit({code})"]
        logs = []
        rc = D.run_all([FakeShard("a", 2), FakeShard("b", 2)], 4, 1, 2, logs.append)
        ev = [l.split() for l in open(stamp).read().splitlines()]
        return rc, ev, logs

    def test_thu_tu_va_song_song(self):
        rc, ev, _ = self.run_fake()
        self.assertEqual(rc, 0)
        t = {(e[0], e[1]): float(e[2]) for e in ev}
        import dieuphoi.dieu_phoi as D  # noqa: E402
        for sn in ("a", "b"):
            for st, deps in D.DEPS.items():
                for d in deps:
                    self.assertGreaterEqual(t[(f"{sn}/{st}", "start")], t[(f"{sn}/{d}", "end")], (sn, st, d))
        # M, L, T của phần a phải chạy chồng thời gian (song song)
        self.assertLess(t[("a/L", "start")], t[("a/M", "end")])
        # TTS của phần b bắt đầu trước khi ASR của phần a xong (dây chuyền)
        self.assertLess(t[("b/tts", "start")], t[("a/cham", "start")])

    def test_phan_loi_khong_keo_phan_khac(self):
        rc, ev, logs = self.run_fake(fail_stage="L")
        self.assertEqual(rc, 2)
        names = {e[0] for e in ev}
        self.assertIn("a/goi", names)
        self.assertNotIn("b/cham", names)
        self.assertTrue(any("LỖI" in l and "[b/L]" in l for l in logs))


class TestSelect10k(unittest.TestCase):
    def test_wrr(self):
        import buoc.chon_cau_10k as S  # noqa: E402
        seq = S.smooth_wrr(["a", "b", "c"], {"a": 1, "b": 1, "c": 0.5}, 500)
        c = collections.Counter(seq)
        self.assertEqual(c["a"], 200)
        self.assertEqual(c["c"], 100)
        self.assertNotEqual(seq[:3], ["a", "a", "a"])

    @unittest.skipUnless(os.path.exists(os.path.join(HERE, "full10k", "all_10k.jsonl")), "chưa chạy buoc/chon_cau_10k.py")
    def test_phan_bo_that(self):
        import buoc.chon_cau_10k as S  # noqa: E402
        rows = [json.loads(l) for l in open(os.path.join(HERE, "full10k", "all_10k.jsonl"), encoding="utf-8")]
        self.assertEqual(len(rows), 10000)
        self.assertEqual(len({r["sample_id"] for r in rows}), 10000)
        self.assertNotIn("Minh Triết", {r["voice"] for r in rows})
        per = collections.Counter(r["voice"] for r in rows)
        for v, w in S.VOICE_WEIGHT.items():
            peers = [per[o] for o, m in S.VOICES.items() if m[0] == S.VOICES[v][0] and o not in S.VOICE_WEIGHT]
            self.assertAlmostEqual(per[v] / (sum(peers) / len(peers)), w, delta=0.03)
        for sh in {r["shard"] for r in rows}:
            reg = collections.Counter(r["speaker_region"] for r in rows if r["shard"] == sh)
            self.assertLessEqual(max(reg.values()) - min(reg.values()), 5)
        tts = [r for r in rows if r["tts_text"]]
        self.assertTrue(all(r["loan_arm"] == "phien_am" for r in tts))


class TestWakeAug(unittest.TestCase):
    def test_dau_rows(self):
        import buoc.ghep_loi_goi as W  # noqa: E402
        from cauhinh.giong import VOICES  # noqa: E402
        rows = W.dau_rows(VOICES)
        self.assertEqual(len(rows), 24 * 2 * 3)
        self.assertEqual(len({r["sample_id"] for r in rows}), len(rows))
        self.assertIn("Hây trợ lý.", {r["text_raw"] for r in rows})

    def test_nhan(self):
        import buoc.ghep_loi_goi as W  # noqa: E402
        self.assertEqual(W.compose_label(["trợ", "lý", "ơi"], "Bật điều hòa.", "bật điều hòa"), "Trợ lý ơi, bật điều hòa.")
        self.assertEqual(W.compose_label(["lý", "ơi"], "Bật điều hòa.", "bật điều hòa"), "Lý ơi, bật điều hòa.")
        self.assertEqual(W.compose_label(["ơi"], "Zalo của chị Nga nói gì?", "{app} của {ct} nói gì"), "Ơi, Zalo của chị Nga nói gì?")
        self.assertEqual(W.compose_label(["trợ", "lý"], "VETC còn bao nhiêu tiền?", "kiểm tra"), "Trợ lý, VETC còn bao nhiêu tiền?")
        self.assertEqual(W.compose_label([], "Bật điều hòa.", ""), "Bật điều hòa.")

    def test_ty_le_cat(self):
        import buoc.ghep_loi_goi as W  # noqa: E402
        kinds = collections.Counter()
        for i in range(4000):
            kind, first, mid, frac = W.plan_cut(3, f"S{i}")
            kinds[(kind, mid is None)] += 1
            if kind == "du":
                self.assertEqual(first, 0)
            else:
                self.assertTrue(1 <= first <= 3)
                if mid is not None:
                    self.assertEqual(first, mid + 1)
                    self.assertTrue(0.3 <= frac <= 0.7)
        self.assertAlmostEqual(kinds[("du", True)] / 4000, 0.40, delta=0.03)
        self.assertAlmostEqual(kinds[("duoi", True)] / 4000, 0.60 * 0.70, delta=0.03)

    def test_ghep_am_thanh(self):
        import numpy as np
        import buoc.ghep_loi_goi as W  # noqa: E402
        wake = np.concatenate([np.zeros(4800), 0.5 * np.ones(48000 * 3 // 2)]).astype(np.float32)   # 0,1 s im + 1,5 s tiếng
        times = [(0.1, 0.6), (0.6, 1.1), (1.1, 1.6)]
        par = 0.1 * np.ones(48000, dtype=np.float32)
        w = W.build_clip(wake, times, par, "duoi", 2, None, 0.0, 0.2)
        cut = int((1.1 - 0.02) * 48000)
        end = min(len(wake), int((1.6 + 0.08) * 48000))
        self.assertEqual(len(w), (end - cut) + int(0.2 * 48000) + 48000)
        self.assertAlmostEqual(float(abs(w[0])), 0.0, places=3)            # làm mờ ở chỗ cắt
        self.assertAlmostEqual(float(np.abs(w[100:1000]).max()), 0.1, delta=0.02)   # mức RMS khớp câu gốc


if __name__ == "__main__":
    unittest.main()
