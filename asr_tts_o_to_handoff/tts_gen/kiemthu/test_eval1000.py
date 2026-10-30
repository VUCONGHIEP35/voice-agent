# -*- coding: utf-8 -*-
"""Test cho các thay đổi đánh giá 1.000 câu (T2–T6, active_rows). Không cần GPU.
Chạy (từ tts_gen/): .venv/Scripts/python -m unittest test_eval1000 -v"""
import csv
import json
import os
import shutil
import tempfile
import unittest

import buoc.asr_whisper as asr_check  # noqa: E402
import thuvien.manifest as eval_common  # noqa: E402
import buoc.cham as gate_union  # noqa: E402
import buoc.doi_giong as make_fallback  # noqa: E402
import buoc.tts as run_pilot  # noqa: E402


def mrow(sid, voice, check="dat", **kw):
    return dict(dict(sample_id=sid, utt_id=f"{sid}__{voice}__a0", voice=voice, tts_check=check, n_syllables=6,
                     speaker_region="Nam", text_spoken="Mở YouTube.", rate_syl_per_s=4.5, attempt=0, retries=[]), **kw)


class ActiveRows(unittest.TestCase):
    def test_lay_dong_cuoi_dat(self):
        man = [mrow("s1", "A", "loi:cat_dau"), mrow("s1", "B", "dat", voice_fallback_from="A"), mrow("s2", "A")]
        act = eval_common.active_rows(man)
        self.assertEqual([(m["sample_id"], m["voice"]) for m in act], [("s1", "B"), ("s2", "A")])

    def test_khong_dong_nao_dat_thi_lay_dong_cuoi(self):
        man = [mrow("s1", "A", "loi:cat_dau"), mrow("s1", "B", "loi:noi_lan_man", voice_fallback_from="A")]
        self.assertEqual(eval_common.active_rows(man)[0]["voice"], "B")

    def test_dong_dat_truoc_dong_loi_sau(self):
        man = [mrow("s1", "A", "dat"), mrow("s1", "B", "loi:cat_dau")]
        self.assertEqual(eval_common.active_rows(man)[0]["voice"], "A")

    def test_wilson(self):
        lo, hi = eval_common.wilson(8, 10)
        self.assertAlmostEqual(lo, 0.490, places=2)
        self.assertAlmostEqual(hi, 0.943, places=2)


class RunPilotT2(unittest.TestCase):
    def test_tts_input_uu_tien_tts_text(self):
        self.assertEqual(run_pilot.tts_input({"text_spoken": "Mở YouTube.", "tts_text": "Mở diu túp."}), "Mở diu túp.")
        self.assertEqual(run_pilot.tts_input({"text_spoken": "Mở YouTube.", "tts_text": ""}), "Mở YouTube.")

    def test_chan_minh_triet(self):
        with self.assertRaises(SystemExit):
            run_pilot.check_excluded([{"sample_id": "s1", "voice": "Minh Triết"}])
        run_pilot.check_excluded([{"sample_id": "s1", "voice": "Adam"}])

    def test_doc_slowdown_temp(self):
        txt = "        GPU Shutdown Temp                 : 100 C\n        GPU Slowdown Temp                 : 97 C\n"
        self.assertEqual(run_pilot.slowdown_temp_c(txt), 97)
        self.assertIsNone(run_pilot.slowdown_temp_c("không có"))

    def test_nghi_toi_khi_giam_du(self):
        temps = iter([96, 93, 91, 89, 88])
        slept = []
        w = run_pilot.cool_down(94, 5, poll=10, read=lambda: next(temps), sleep=slept.append, log=lambda *a, **k: None)
        self.assertEqual(w, 30)              # 96 -> 93 -> 91 -> 89 (<= 89 thì thôi)
        self.assertEqual(len(slept), 3)

    def test_khong_nong_thi_khong_nghi(self):
        self.assertEqual(run_pilot.cool_down(94, 5, read=lambda: 70, sleep=lambda s: None), 0.0)

    def test_gop_run_config(self):
        old = dict(calls=[dict(wall_s=2.0, audio_s=20.0)], load_s=20.0, n_rows=10, cooldown_count=1, cooldown_s=30.0,
                   tts_checks={}, lan_chay=None)
        new = dict(calls=[dict(wall_s=1.0, audio_s=10.0)], load_s=15.0, n_rows=10, cooldown_count=0, cooldown_s=0.0,
                   bat_dau="x", tts_checks={})
        out = run_pilot.merge_run_config(old, new)
        self.assertEqual(len(out["calls"]), 2)
        self.assertEqual(out["gen_wall_s"], 3.0)
        self.assertEqual(out["rtf_overall"], 0.1)
        self.assertEqual(len(out["lan_chay"]), 2)
        self.assertEqual(out["load_s_total"], 35.0)
        self.assertEqual(out["cooldown_count"], 1)


class AsrCheckT3(unittest.TestCase):
    def test_hyp_doc_phien_am_khop_tts_text(self):
        m = {"text_spoken": "Mở YouTube.", "tts_text": "Mở diu túp."}
        c, _ = asr_check.best_cer(asr_check.answer_variants(m, []), "mở diu túp")
        self.assertEqual(c, 0)

    def test_khong_co_tts_text_thi_chi_text_spoken(self):
        m = {"text_spoken": "Mở YouTube.", "tts_text": ""}
        self.assertEqual(asr_check.answer_variants(m, []), ["mở youtube"])
        c, _ = asr_check.best_cer(asr_check.answer_variants(m, []), "mở diu túp")
        self.assertGreater(c, 0.3)


VOICES = {"A": ("Nam", "male", "x", ""), "B": ("Nam", "male", "x", ""), "C": ("Nam", "male", "x", ""),
          "F": ("Nam", "female", "x", ""), "T1": ("Trung", "female", "x", ""), "T2": ("Trung", "male", "x", "")}


class FallbackT4(unittest.TestCase):
    def test_cung_vung_cung_gioi_uu_tien_khong_cat_dau_roi_it_cau(self):
        v, dg = make_fallback.pick_voice("A", "s1", VOICES, {"B": 1, "C": 5}, cut_flagged={"B"})
        self.assertEqual((v, dg), ("C", False))
        v, _ = make_fallback.pick_voice("A", "s1", VOICES, {"B": 1, "C": 5}, cut_flagged=set())
        self.assertEqual(v, "B")

    def test_trung_doi_gioi(self):
        self.assertEqual(make_fallback.pick_voice("T1", "s1", VOICES, {}, set()), ("T2", True))

    def test_build_chi_mot_vong_va_giu_truong_goc(self):
        man = [mrow("s1", "A", "loi:cat_dau"), mrow("s2", "A"),
               mrow("s3", "A", "loi:cat_dau"), mrow("s3", "B", "loi:cat_dau", voice_fallback_from="A")]
        plan = [dict(sample_id=s, voice="A", text_spoken="x", residence="Quê", sub_region="Nam Bộ", eval_idx=i)
                for i, s in enumerate(("s1", "s2", "s3"))]
        rows = make_fallback.build(man, plan, VOICES)
        self.assertEqual([r["sample_id"] for r in rows], ["s1"])       # s3 đã đổi giọng một lần
        self.assertEqual(rows[0]["voice_fallback_from"], "A")
        self.assertNotEqual(rows[0]["voice"], "A")
        self.assertEqual(rows[0]["eval_idx"], 0)
        # sau khi sinh bằng giọng mới, active_rows chọn dòng mới
        man2 = man + [mrow("s1", rows[0]["voice"], "dat", voice_fallback_from="A")]
        self.assertEqual(eval_common.active_rows(man2)[0]["voice"], rows[0]["voice"])
        self.assertEqual(sum(m["sample_id"] == "s1" for m in man2), 2)


class GateUnionT5(unittest.TestCase):
    def j(self, cers, nt=None, check="dat", syl=6, region="Nam", **kw):
        m = dict(n_syllables=syl, voice_region=region, speaker_region=region, **kw)
        return gate_union.judge(m, cers, nt or cers, check, 0.10)[:2]

    def test_quy_tac(self):
        self.assertEqual(self.j({}, check="loi:cat_dau"), ("sinh_lai", "loi:cat_dau"))
        self.assertEqual(self.j({}, check="loi:cat_dau", voice_fallback_from="A"), ("can_nghe", "tts"))
        self.assertEqual(self.j({"L": 0.2, "c3": 0.0}, syl=2), ("dat", "cau_ngan_khop"))
        self.assertEqual(self.j({"L": 0.05, "M": 0.08}, syl=3), ("can_nghe", "cau_ngan"))
        self.assertEqual(self.j({"L": 0.05, "M": 0.08}), ("dat", ""))
        self.assertEqual(self.j({"L": 0.3, "M": 0.3, "c3": 0.05}), ("dat_1nguon", "c3"))
        self.assertEqual(self.j({"L": 0.3, "M": 0.3}, {"L": 0.05, "M": 0.3}, region="Trung"), ("can_nghe", "chi_loi_thanh"))
        self.assertEqual(self.j({"L": 0.3, "M": 0.3}, {"L": 0.05, "M": 0.3}, region="Bắc"), ("loai", "sai"))

    def test_dong_gop_bien(self):
        rows = [dict(tts_check="dat", n_syl=6, cer_L=0.0, cer_M=0.5, cer_c3=""),
                dict(tts_check="dat", n_syl=6, cer_L=0.5, cer_M=0.05, cer_c3=""),
                dict(tts_check="loi:cat_dau", n_syl=6, cer_L=0.0, cer_M=0.0, cer_c3="")]
        r = gate_union.marginal(rows, ["L", "M"], 0.10)
        self.assertEqual(r["tap"]["L"], 1)
        self.assertEqual(r["tap"]["L+M"], 2)
        self.assertEqual(r["chi_nho"], {"L": 1, "M": 1})


class ReportT6(unittest.TestCase):
    def test_so_cau_khop_manifest(self):
        import phantich.bao_cao as report_eval  # noqa: E402
        d = tempfile.mkdtemp()
        try:
            run = os.path.join(d, "run")
            os.makedirs(run)
            man = [mrow("s1", "A", "loi:cat_dau", shard="A"), mrow("s1", "B", "dat", voice_fallback_from="A", shard="A"),
                   mrow("s2", "A", shard="A", retries=[{"attempt": 0}], attempt=1), mrow("s3", "B", shard="A")]
            with open(os.path.join(run, "manifest.jsonl"), "w", encoding="utf-8") as f:
                f.writelines(json.dumps(m, ensure_ascii=False) + "\n" for m in man)
            json.dump(dict(gen_wall_s=1.0, gen_audio_s=10.0, rtf_overall=0.1, calls=[]),
                      open(os.path.join(run, "run_config.json"), "w", encoding="utf-8"))
            with open(os.path.join(run, "gate_hop.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=["sample_id", "ket_qua", "cer_L", "cer_M"])
                w.writeheader()
                w.writerows([dict(sample_id="s1", ket_qua="dat", cer_L=0, cer_M=0),
                             dict(sample_id="s2", ket_qua="loai", cer_L=0.4, cer_M=0.5),
                             dict(sample_id="s3", ket_qua="dat", cer_L=0.0, cer_M="")])
            plan = os.path.join(d, "plan.jsonl")
            with open(plan, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(dict(sample_id=s, shard="A")) + "\n" for s in ("s1", "s2", "s3"))
            rows = report_eval.rows_of([report_eval.load_run(run)])
            self.assertEqual(len(rows), 3)
            s = report_eval.stats(rows)
            self.assertEqual((s["n"], s["dat"], s["loai"], s["doi_giong"], s["co_sinh_lai"]), (3, 2, 1, 1, 1))
            out = os.path.join(d, "rep")
            import sys
            argv = sys.argv
            sys.argv = ["phantich/bao_cao.py", run, "--plan", plan, "--out", out]
            try:
                report_eval.main()
            finally:
                sys.argv = argv
            txt = open(os.path.join(out, "bao_cao.md"), encoding="utf-8").read()
            self.assertIn("3 sample_id duy nhất", txt)
            self.assertIn("Thiếu so với kế hoạch: 0", txt)
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
