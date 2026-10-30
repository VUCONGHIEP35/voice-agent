# -*- coding: utf-8 -*-
"""Chấm gộp mọi cấu hình ASR cho một lượt chạy (việc T5; quy tắc ở mục 6 của docs/ke_hoach_sinh_1000_cau.md).

Chạy (từ tts_gen/):  .venv/Scripts/python -m buoc.cham runs/eval1000_A --lexicon lexicon/asr_bien_the.tsv
Cấu hình (có tệp nào dùng tệp đó):
  L   asr_PhoWhisper-large-ct2-int8.jsonl      M   asr_PhoWhisper-medium.jsonl
  c1, c2, c3  cột hyp_c1..hyp_c3 của asr_diagnose.csv (c1: M + đệm, tham lam; c2: M + đệm + beam 5; c3: wav2vec2 CTC)
  Z   asr_Zipformer-30M-int8-beam4.jsonl (buoc/asr_zipformer.py, sherpa-onnx CPU; tùy chọn, chỉ góp vào dat_1nguon)
Đáp án: text_spoken, tts_text và biến thể trong --lexicon; từ địa phương tương đương (asr_check.answer_variants/best_cer).
Mỗi sample_id lấy một dòng (eval_common.active_rows). Xét theo thứ tự:
  1. tts_check không đạt: chưa đổi giọng -> sinh_lai; đã đổi giọng -> can_nghe (tts)
  2. câu <= --short-max âm tiết: cấu hình bất kỳ CER = 0 -> dat, không thì can_nghe (cau_ngan)
  3. L và M cùng <= ngưỡng -> dat
  4. ít nhất một cấu hình <= ngưỡng -> dat_1nguon (ghi các cấu hình đạt)
  5. không cấu hình nào đạt: giọng Trung mà CER bỏ thanh nhỏ nhất <= ngưỡng -> can_nghe (chi_loi_thanh), còn lại loai
Ghi <run>/gate_hop.csv và <run>/gate_hop_tom_tat.json; in tóm tắt theo vùng và đóng góp biên của từng cấu hình.
  T   asr_PhoWhisper-small.jsonl: mô hình ĐÍCH sẽ fine-tune, zero-shot. CHỈ ĐO (cột cer_T, CER TB, CER theo kết quả chấm);
      không bao giờ vào judge/marginal: lọc bằng mô hình đích sẽ bỏ đúng câu nó cần học.
Có Z: thêm "thu_2tren3" (nếu luật dat là "ít nhất 2 trong L, M, Z đạt" thì có bao nhiêu câu dat) để cân nhắc, KHÔNG đổi luật.
Ngưỡng 0,10 là mốc TẠM, chốt lại sau khi nghe.

--luat v2 (MẶC ĐỊNH từ 25/10/2026, kế hoạch sinh 10.000 câu); --luat v1 = luật cũ ở trên, giữ để so:
  a. bỏ từ đệm (FILLERS: ờ, ừm, ơ, ê, nè, nì) ở cả đáp án lẫn câu máy nghe ra trước khi chấm;
  b. một cấu hình chỉ "đạt" khi CER <= ngưỡng VÀ không mất/thay từ nội dung nào (căn hàng theo từ,
     phan_tich_vi_tri_loi.align; tiểu từ cuối câu END_PARTICLES và "ơi" được miễn); câu ngắn vẫn đòi CER = 0;
  c. Z chỉ được tính khi c3 cũng đạt hoặc CER của Z <= 0,05 (phiếu nghe A: Z một mình cho đạt 4/9 câu người nghe Sai);
  d. kết quả dat_1nguon mà L, M, Z nghe từ đầu câu khác nhau (đúng/sai) -> can_nghe (tu_dau_lech).
  Cột dat_<cấu hình> ghi cấu hình đó có đạt theo luật đang dùng không (marginal/two_of_three đọc cột này).
"""
import argparse
import collections
import csv
import json
import os
from cauhinh.nguong import CAU_NGAN_MAX, CER_NGUONG_TAM  # noqa: E402
from thuvien.luat_cham import CONFIGS, FILES, MEASURE_ONLY, VERDICTS, config_pass_v2, content_errors, judge, judge_v2, load_hyps, marginal, mean_cer, passes, strip_fillers, tts_check_of, two_of_three  # noqa: E402

from thuvien.cham_chu import answer_variants, best_cer, cer, norm  # noqa: E402
from thuvien.van_ban import load_lexicon  # noqa: E402
from thuvien.manifest import active_rows, load_manifest  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--lexicon", action="append", default=[])
    ap.add_argument("--thr", type=float, default=CER_NGUONG_TAM, help="ngưỡng CER TẠM cho cả ba vùng")
    ap.add_argument("--short-max", type=int, default=CAU_NGAN_MAX)
    ap.add_argument("--diag", default=None)
    ap.add_argument("--configs", nargs="*", default=None, choices=list(CONFIGS), help="chỉ dùng các cấu hình này (mặc định: mọi cấu hình có tệp)")
    ap.add_argument("--out-name", default="gate_hop", help="tên tệp ra: <run>/<tên>.csv và <tên>_tom_tat.json")
    ap.add_argument("--luat", choices=["v1", "v2"], default="v2", help="v2: mặc định từ 25/10/2026; v1: luật cũ (để so)")
    a = ap.parse_args()
    lex = [e for p in a.lexicon for e in load_lexicon(p)]
    lex.sort(key=lambda x: -len(x[0]))
    hyps = load_hyps(a.run, a.diag)
    avail = [c for c in CONFIGS if c in hyps and (a.configs is None or c in a.configs)]
    meas = [c for c in MEASURE_ONLY if c in hyps]
    if not avail:
        raise SystemExit(f"{a.run}: chưa có kết quả ASR nào ({', '.join(FILES.values())}, asr_diagnose.csv)")
    rows = []
    for m in active_rows(load_manifest(a.run)):
        u = m["utt_id"]
        variants = answer_variants(m, lex)
        if a.luat == "v2":
            variants = list(dict.fromkeys(strip_fillers(x) for x in variants))
            hy = {c: strip_fillers(norm(hyps[c][u])) for c in avail + meas if u in hyps[c]}
        else:
            hy = {c: hyps[c][u] for c in avail + meas if u in hyps[c]}
        best = {c: best_cer(variants, hy[c]) for c in avail if c in hy}
        cers = {c: round(b[0], 4) for c, b in best.items()}
        cers_nt = {c: round(best_cer(variants, hy[c], tone=False)[0], 4) for c in avail if c in hy}
        cer_meas = {c: round(best_cer(variants, hy[c])[0], 4) for c in meas if c in hy}
        tc = tts_check_of(m, a.run)
        if a.luat == "v2":
            errs, first_ok = {}, {}
            for c, (_, var) in best.items():
                bad, st = content_errors(var, hy[c])
                errs[c] = bad
                if c in ("L", "M", "Z") and st:
                    first_ok[c] = 0 not in bad
            okc = config_pass_v2(cers, errs, m["n_syllables"], a.thr, a.short_max)
            v, why, ok = judge_v2(m, okc, cers_nt, first_ok, tc, a.thr, a.short_max)
        else:
            v, why, ok = judge(m, cers, cers_nt, tc, a.thr, a.short_max)
            okc = {c: passes(dict(n_syl=m["n_syllables"], **{f"cer_{c}": cers[c]}), c, a.thr, a.short_max) for c in cers}
        rows.append(dict(utt_id=u, sample_id=m["sample_id"], region=m.get("voice_region") or m["speaker_region"],
                         speaker_region=m["speaker_region"], voice=m["voice"], voice_fallback_from=m.get("voice_fallback_from") or "",
                         n_syl=m["n_syllables"], tts_check=tc, **{f"cer_{c}": cers.get(c, "") for c in CONFIGS},
                         **{f"cer_{c}": cer_meas.get(c, "") for c in MEASURE_ONLY},
                         cer_bo_thanh_min=min(cers_nt.values()) if cers_nt else "", cau_hinh_dat="+".join(ok),
                         **{f"dat_{c}": okc.get(c, "") for c in CONFIGS}, luat=a.luat,
                         ket_qua=v, ly_do=why, nguong=a.thr, cer_text_spoken_L=round(cer(m["text_spoken"], hyps["L"][u]), 4)
                         if "L" in hyps and u in hyps["L"] else "", text_spoken=m["text_spoken"], tts_text=m.get("tts_text") or "",
                         **{f"hyp_{c}": hyps[c].get(u, "") for c in avail + meas}))
    with open(os.path.join(a.run, f"{a.out_name}.csv"), "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    by_reg = {reg: dict(collections.Counter(r["ket_qua"] for r in rows if r["region"] == reg))
              for reg in ("Bắc", "Trung", "Nam")}
    summ = dict(run=a.run, n=len(rows), cau_hinh=avail, nguong=a.thr, lexicon=a.lexicon, luat=a.luat,
                theo_ket_qua=dict(collections.Counter(r["ket_qua"] for r in rows)), theo_vung=by_reg,
                ly_do=dict(collections.Counter(r["ly_do"] for r in rows if r["ket_qua"] in ("can_nghe", "sinh_lai"))),
                dong_gop_bien=marginal(rows, avail, a.thr, a.short_max),
                dong_gop_bien_theo_vung={reg: marginal([r for r in rows if r["region"] == reg], avail, a.thr, a.short_max)
                                         for reg in ("Bắc", "Trung", "Nam")},
                cer_tb={reg or "Tất cả": mean_cer([r for r in rows if reg is None or r["region"] == reg], avail + meas)
                        for reg in ("Bắc", "Trung", "Nam", None)},
                chi_do=meas)
    if meas:
        summ["chi_do_theo_ket_qua"] = {v: mean_cer([r for r in rows if r["ket_qua"] == v], meas) for v in VERDICTS
                                       if any(r["ket_qua"] == v for r in rows)}
    if "Z" in avail and "L" in avail and "M" in avail:
        summ["thu_2tren3"] = {reg or "Tất cả": two_of_three([r for r in rows if reg is None or r["region"] == reg], a.thr, a.short_max)
                              for reg in ("Bắc", "Trung", "Nam", None)}
    with open(os.path.join(a.run, f"{a.out_name}_tom_tat.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, ensure_ascii=False, indent=1)
    print(f"{a.run}: {len(rows)} câu, cấu hình {avail}, ngưỡng TẠM {a.thr}, luật {a.luat}")
    print(f"  {'':6s}" + "".join(f"{k:>11s}" for k in VERDICTS))
    for reg in ("Bắc", "Trung", "Nam", None):
        g = [r for r in rows if reg is None or r["region"] == reg]
        print(f"  {reg or 'Tất cả':6s}" + "".join(f"{sum(r['ket_qua'] == k for r in g):11d}" for k in VERDICTS))
    print("  Lý do can_nghe / sinh_lai:", summ["ly_do"])
    print("  Số câu đạt theo tập cấu hình:", summ["dong_gop_bien"]["tap"])
    print("  Số câu chỉ đạt nhờ một cấu hình:", summ["dong_gop_bien"]["chi_nho"])
    print("  CER TB (đáp án biến thể):", summ["cer_tb"])
    if meas:
        print(f"  Chỉ đo (không vào chấm) {meas}: CER TB theo kết quả chấm", summ["chi_do_theo_ket_qua"])
    if "thu_2tren3" in summ:
        print("  Thử luật dat = 2/3 trong L, M, Z:", summ["thu_2tren3"])


if __name__ == "__main__":
    main()
