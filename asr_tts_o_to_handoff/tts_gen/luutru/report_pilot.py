# -*- coding: utf-8 -*-
"""Báo cáo và phiếu nghe cho một lượt sinh thí điểm (đọc manifest.jsonl, run_config.json; không sửa âm thanh).

Chạy (từ tts_gen/):  python -m luutru.report_pilot [runs/pilot100]
Ghi vào thư mục lượt chạy:
  report.md               số đo kỹ thuật, tốc độ nói, phân bố theo vùng/giọng/độ dài, câu nghi lỗi
  phieu_nghe.csv          phiếu nghe MÙ: thứ tự xáo, không có nhãn vùng; người nghe điền đúng lời, vùng nghe được, điểm
  phieu_nghe_khoa.csv     khóa đối chiếu (utt_id -> vùng, giọng) để chấm sau khi nghe; KHÔNG đưa cho người nghe
Ngưỡng ở đây là mốc ban đầu của kế hoạch (tốc độ 4,0–5,6 âm tiết/giây), sẽ chốt lại sau khi nghe.
"""
import collections
import csv
import hashlib
import json
import os
import sys

RATE_LO, RATE_HI = 4.0, 5.6          # âm tiết / giây có tiếng (kế hoạch, mục kiểm soát chất lượng)
SEC_PER_SYL_MAX = 0.6                # nghi "nói thêm": thời lượng có tiếng quá dài so với số âm tiết


def q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 2)


def flags_of(m):
    f = []
    if m["duration_s"] <= 0.05 or m["speech_s"] <= 0.05:
        f.append("rỗng")
    if m.get("clipped"):
        f.append("chạm đỉnh")
    r = m.get("rate_syl_per_s")
    if r is not None and m["n_syllables"] > 3 and not (RATE_LO <= r <= RATE_HI):
        f.append(f"tốc độ {r}")
    if m["speech_s"] and m["speech_s"] / max(m["n_syllables"], 1) > SEC_PER_SYL_MAX:
        f.append("nghi nói thêm")
    if (m.get("lead_sil_s") or 0) > 0.5 or (m.get("trail_sil_s") or 0) > 0.8:
        f.append("im lặng dài")
    return f


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", "pilot100")
    with open(os.path.join(run, "manifest.jsonl"), encoding="utf-8") as f:
        man = [json.loads(line) for line in f]
    cfg = json.load(open(os.path.join(run, "run_config.json"), encoding="utf-8"))
    C = collections.Counter
    L = []
    L.append(f"# Báo cáo lượt sinh `{os.path.basename(run)}`\n")
    L.append(f"- Mô hình: VieNeu v3 Turbo `{cfg.get('backbone_repo')}`, vieneu {cfg.get('vieneu')}, torch {cfg.get('torch')}, "
             f"{cfg.get('backend')} / {cfg.get('device')} / {cfg.get('dtype')}, watermark: {cfg.get('watermark')}, commit mã `{cfg.get('git_commit')}`")
    L.append(f"- GPU: {cfg.get('gpu')}; max_batch_size {cfg.get('max_batch_size')}; lấy mẫu {cfg.get('sampling')}; seed gốc {cfg.get('run_seed')}")
    L.append(f"- Nạp mô hình {cfg.get('load_s')} s; sinh {cfg.get('gen_wall_s')} s cho {cfg.get('gen_audio_s')} s âm thanh; "
             f"**RTF {cfg.get('rtf_overall')}**; VRAM đỉnh {cfg.get('vram_peak_alloc_gb')} GB (reserved {cfg.get('vram_peak_reserved_gb')} GB)")
    L.append(f"- Số câu: {len(man)}\n")
    L.append("## Phân bố\n")
    L.append(f"- Theo vùng: {dict(C(m['speaker_region'] for m in man))}")
    L.append(f"- Theo độ dài: {dict(C(m['length_class'] for m in man))}")
    L.append(f"- Số câu mỗi giọng: {dict(sorted(C(m['voice'] for m in man).items(), key=lambda x: -x[1]))}")
    L.append(f"- Giới tính giọng: {dict(C((m['speaker_region'], m['voice_gender']) for m in man))}\n")
    L.append("## Số đo kỹ thuật (chưa chỉnh gì)\n")
    L.append("| Chỉ số | min | p10 | trung vị | p90 | max |\n|---|---|---|---|---|---|")
    for name, key in [("Thời lượng (s)", "duration_s"), ("Thời gian có tiếng (s)", "speech_s"),
                      ("Tốc độ (âm tiết/giây có tiếng)", "rate_syl_per_s"), ("Im lặng đầu (s)", "lead_sil_s"),
                      ("Im lặng cuối (s)", "trail_sil_s"), ("Biên độ đỉnh", "peak")]:
        xs = [m.get(key) for m in man]
        L.append(f"| {name} | {q(xs, 0)} | {q(xs, .1)} | {q(xs, .5)} | {q(xs, .9)} | {q(xs, 1)} |")
    L.append("")
    L.append("Tốc độ theo vùng và độ dài (trung vị, chỉ câu > 3 âm tiết):\n")
    for reg in ("Bắc", "Trung", "Nam"):
        parts = []
        for lc in ("Ngắn", "Thường", "Dài"):
            xs = [m["rate_syl_per_s"] for m in man if m["speaker_region"] == reg and m["length_class"] == lc and m["rate_syl_per_s"]]
            parts.append(f"{lc} {q(xs, .5)} (n={len(xs)})")
        L.append(f"- {reg}: " + ", ".join(parts))
    in_band = [m for m in man if m["n_syllables"] > 3 and m["rate_syl_per_s"] and RATE_LO <= m["rate_syl_per_s"] <= RATE_HI]
    n_gt3 = sum(1 for m in man if m["n_syllables"] > 3)
    L.append(f"\nCâu > 3 âm tiết nằm trong {RATE_LO}–{RATE_HI} âm tiết/giây: {len(in_band)}/{n_gt3}\n")
    flagged = [(m, flags_of(m)) for m in man]
    flagged = [(m, f) for m, f in flagged if f]
    L.append(f"## Câu cần nghe trước ({len(flagged)} câu có cờ kỹ thuật)\n")
    L.append("| utt_id | vùng | âm tiết | thời lượng | tốc độ | cờ | text_spoken |\n|---|---|---|---|---|---|---|")
    for m, f in sorted(flagged, key=lambda x: x[0]["pilot_idx"] or 0):
        L.append(f"| {m['utt_id']} | {m['speaker_region']} | {m['n_syllables']} | {m['duration_s']} | {m['rate_syl_per_s']} | "
                 f"{'; '.join(f)} | {m['text_spoken']} |")
    diff = [m for m in man if m["vieneu_text"].strip().rstrip(".?!") != m["text_spoken"].lower().strip().rstrip(".?!")]
    L.append(f"\n## VieNeu chuẩn hóa khác `text_spoken` ({len(diff)} câu)\n")
    L.append("Mô hình đọc theo cột `vieneu_text`. Nhãn ASR vẫn là `text_raw`; cần nghe xem cách đọc có chấp nhận được không.\n")
    L.append("| utt_id | text_spoken | vieneu_text | tên Latin chưa duyệt |\n|---|---|---|---|")
    for m in diff:
        L.append(f"| {m['utt_id']} | {m['text_spoken']} | {m['vieneu_text']} | {m['loan_unverified']} |")
    L.append("\n## Chưa làm trong báo cáo này\n")
    L.append("- Kiểm nội dung bằng ASR (PhoWhisper) và CER: chạy riêng sau bước TTS.")
    L.append("- Nghe mù: dùng `phieu_nghe.csv`; chấm bằng `phieu_nghe_khoa.csv`.")
    with open(os.path.join(run, "report.md"), "w", encoding="utf-8", newline="\n") as fo:
        fo.write("\n".join(L) + "\n")

    order = sorted(man, key=lambda m: hashlib.sha1(("nghe|" + m["utt_id"]).encode()).hexdigest())
    with open(os.path.join(run, "phieu_nghe.csv"), "w", encoding="utf-8-sig", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["stt", "tep_am_thanh", "cau_can_doc", "doc_dung_loi(Y/N)", "tu_doc_sai",
                    "vung_nghe_duoc(Bac/Trung/Nam/khong_ro)", "tu_nhien(1-5)", "ghi_chu"])
        for i, m in enumerate(order, 1):
            w.writerow([i, m["audio48"], m["text_raw"], "", "", "", "", ""])
    with open(os.path.join(run, "phieu_nghe_khoa.csv"), "w", encoding="utf-8-sig", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["stt", "utt_id", "speaker_region", "sub_region", "residence", "voice", "voice_region", "voice_gender", "voice_style"])
        for i, m in enumerate(order, 1):
            w.writerow([i, m["utt_id"], m["speaker_region"], m["sub_region"], m["residence"], m["voice"], m["voice_region"],
                        m["voice_gender"], m["voice_style"]])
    print("\n".join(L[:12]))
    print(f"... đã ghi report.md, phieu_nghe.csv, phieu_nghe_khoa.csv vào {run}")


if __name__ == "__main__":
    main()
