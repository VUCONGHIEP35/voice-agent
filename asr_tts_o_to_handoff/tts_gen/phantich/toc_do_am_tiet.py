# -*- coding: utf-8 -*-
"""Đo độ dài từng âm tiết bằng căn hàng cưỡng bức (CTC, wav2vec2) để kiểm "TTS đọc nhanh ở đầu câu".

Chạy (từ tts_gen/, cần GPU hoặc CPU + torch, transformers):
  python -m phantich.toc_do_am_tiet <run>[::<thư mục gate>] ... --ctc <thư mục wav2vec2> --out reports/toc_do_am_tiet
Mỗi dòng hiện hành, tts_check đạt, >= 4 âm tiết: lấy chữ đã đưa vào TTS (tts_text, không có thì text_spoken), chữ thường,
bỏ dấu câu; câu có ký tự ngoài bộ chữ của mô hình thì bỏ qua (đếm lại). Logit wav2vec2 trên audio16 -> căn hàng Viterbi
CTC (tự viết, không cần torchaudio) -> khung bắt đầu/kết thúc từng âm tiết (20 ms/khung).
Độ dài âm tiết = từ lúc nó bắt đầu tới lúc âm tiết kế tiếp bắt đầu (gồm cả quãng ngắt sau nó, như dấu phẩy sau "Này,").
Chỉ số mỗi câu: im lặng đầu (đến âm tiết 1), độ dài âm tiết 1, 2, trung vị các âm tiết GIỮA (bỏ 2 đầu, 1 cuối), âm tiết cuối;
tỷ lệ = âm tiết đầu / trung vị giữa. Tỷ lệ < 1 nghĩa là âm tiết đầu ngắn hơn (đọc nhanh hơn) phần giữa câu.
Ghi <out>/am_tiet.csv (mỗi câu một dòng) và <out>/tom_tat.md (theo vùng, giọng, loại từ đầu, máy sai/đúng từ đầu).
Lưu ý: ranh giới căn hàng sai số khoảng 1–2 khung (20–40 ms); giọng Trung căn kém hơn vì mô hình nghe Trung kém hơn.
"""
import argparse
import collections
import csv
import os
import statistics
from thuvien.can_hang import FRAME_S, words_of, char_tokens, ctc_align, word_spans  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
from thuvien.manifest import active_rows, load_manifest  # noqa: E402

FILL = {"này", "ờ", "ê", "ơ", "ừ", "à", "nè", "nì", "ủa"}


def sentence_stats(spans):
    """Độ dài âm tiết = khoảng từ lúc âm tiết bắt đầu tới lúc âm tiết kế tiếp bắt đầu (CTC cho đỉnh nhọn nên đo
    đầu-cuối ký tự sẽ ngắn sai); âm tiết cuối: từ lúc bắt đầu tới ký tự cuối."""
    d = [(spans[i + 1][0] - spans[i][0]) * FRAME_S for i in range(len(spans) - 1)]
    d.append((spans[-1][1] - spans[-1][0]) * FRAME_S)
    mid = d[2:-1]
    med = statistics.median(mid) if mid else None
    return dict(n_syl=len(d), lead_s=round(spans[0][0] * FRAME_S, 3), d1=round(d[0], 3), d2=round(d[1], 3),
                mid_med=round(med, 3) if med else None, d_last=round(d[-1], 3),
                gap12=round((spans[1][0] - spans[0][1]) * FRAME_S, 3),
                r1=round(d[0] / med, 3) if med else None, r2=round(d[1] / med, 3) if med else None,
                syl_per_s=round(len(d) / ((spans[-1][1] - spans[0][0]) * FRAME_S), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--ctc", required=True)
    ap.add_argument("--gate-name", default="gate_hop_server")
    ap.add_argument("--min-syl", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(HERE, "reports", "toc_do_am_tiet"))
    a = ap.parse_args()
    import soundfile as sf
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    proc = Wav2Vec2Processor.from_pretrained(a.ctc)
    model = Wav2Vec2ForCTC.from_pretrained(a.ctc).eval()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev)
    vocab = proc.tokenizer.get_vocab()
    blank = proc.tokenizer.pad_token_id
    sep = vocab.get(proc.tokenizer.word_delimiter_token, None)
    from thuvien.can_hang import word_states  # noqa: E402
    from thuvien.van_ban import load_lexicon  # noqa: E402
    lex = load_lexicon(os.path.join(HERE, "lexicon", "asr_bien_the.tsv"))
    lex.sort(key=lambda x: -len(x[0]))
    rows, skipped = [], collections.Counter()
    for spec in a.runs:
        run, gate_dir = spec.split("::", 1) if "::" in spec else (spec, spec)
        man = {m["utt_id"]: m for m in active_rows(load_manifest(run))}
        with open(os.path.join(gate_dir, f"{a.gate_name}.csv"), encoding="utf-8-sig") as f:
            gate = {g["utt_id"]: g for g in csv.DictReader(f)}
        for u, m in man.items():
            g = gate.get(u)
            if not g or m.get("tts_check", "dat") != "dat":
                skipped["tts_check/khong_cham"] += 1
                continue
            ws = words_of(m.get("tts_text") or m["text_spoken"])
            if len(ws) < a.min_syl:
                skipped["ngan"] += 1
                continue
            per_word = [[char_tokens(ch, vocab) for ch in w] for w in ws]
            if any(t is None for pw in per_word for t in pw):
                skipped["ky_tu_ngoai_bo_chu"] += 1
                continue
            toks, lens = [], []
            for i, pw in enumerate(per_word):
                if i and sep is not None:
                    toks.append(sep)
                ids = [x for t in pw for x in t]
                toks += ids
                lens.append(len(ids))
            w16, sr = sf.read(os.path.join(run, m["audio16"]), dtype="float32")
            x = proc(w16, sampling_rate=16000, return_tensors="pt").input_values.to(dev)
            with torch.no_grad():
                logp = torch.log_softmax(model(x).logits[0].float(), dim=-1).cpu().numpy()
            spans = ctc_align(logp, toks, blank)
            if spans is None:
                skipped["khong_can_duoc"] += 1
                continue
            if sep is not None:      # bỏ span của dấu cách giữa từ
                keep = [s for t, s in zip(toks, spans) if t != sep]
                spans = keep
            st = sentence_stats(word_spans(spans, lens))
            first_wrong = {}
            for c in ("L", "M", "Z"):
                s = word_states(m, g.get(f"hyp_{c}", ""), lex)
                first_wrong[c] = (s[0] != "ok") if s else None
            kind = "từ đệm/gọi" if ws[0] in FILL else ("trợ lý" if ws[:2] == ["trợ", "lý"] else "từ nội dung")
            rows.append(dict(utt_id=u, run=os.path.basename(run), region=m.get("voice_region") or m["speaker_region"],
                             voice=m["voice"], loai_tu_dau=kind, tu_dau=ws[0], text=" ".join(ws),
                             L_sai_tu_dau=first_wrong["L"], M_sai_tu_dau=first_wrong["M"], Z_sai_tu_dau=first_wrong["Z"],
                             head_db=m.get("head_db"), **st))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "am_tiet.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def summ(rs):
        md = lambda k: statistics.median([r[k] for r in rs if r[k] is not None])
        below = sum(1 for r in rs if r["r1"] is not None and r["r1"] < 0.7)
        return (f"{len(rs)} | {md('lead_s'):.2f} | {md('d1'):.3f} | {md('d2'):.3f} | {md('mid_med'):.3f} | {md('d_last'):.3f} | "
                f"{md('r1'):.2f} | {md('r2'):.2f} | {below / len(rs):.0%} | {md('syl_per_s'):.1f}")
    head = ("| Nhóm | n | im lặng đầu (s) | âm tiết 1 (s) | âm tiết 2 (s) | trung vị giữa (s) | âm tiết cuối (s) | "
            "tỷ lệ 1/giữa | tỷ lệ 2/giữa | câu có tỷ lệ 1 < 0,7 | âm tiết/giây |")
    L = ["# Độ dài âm tiết theo vị trí (căn hàng CTC wav2vec2, giá trị là TRUNG VỊ)", "",
         f"Câu đo được: {len(rows)}; bỏ qua: {dict(skipped)}. Khung 20 ms, sai số ranh giới khoảng 20–40 ms.", "",
         head, "|" + "---|" * 11]
    groups = [("Tất cả", rows)]
    groups += [(f"Vùng {k}", [r for r in rows if r["region"] == k]) for k in ("Bắc", "Trung", "Nam")]
    groups += [(f"Từ đầu: {k}", [r for r in rows if r["loai_tu_dau"] == k]) for k in ("từ nội dung", "từ đệm/gọi", "trợ lý")]
    groups += [("L sai từ đầu", [r for r in rows if r["L_sai_tu_dau"]]), ("L đúng từ đầu", [r for r in rows if r["L_sai_tu_dau"] is False])]
    groups += [("Từ nội dung, L sai từ đầu", [r for r in rows if r["loai_tu_dau"] == "từ nội dung" and r["L_sai_tu_dau"]]),
               ("Từ nội dung, L đúng từ đầu", [r for r in rows if r["loai_tu_dau"] == "từ nội dung" and r["L_sai_tu_dau"] is False])]
    for name, rs in groups:
        if rs:
            L.append(f"| {name} | {summ(rs)} |")
    L += ["", "## Theo giọng", "", head.replace("Nhóm", "Giọng"), "|" + "---|" * 11]
    for v in sorted({r["voice"] for r in rows}):
        rs = [r for r in rows if r["voice"] == v]
        L.append(f"| {v} | {summ(rs)} |")
    txt = "\n".join(L) + "\n"
    open(os.path.join(a.out, "tom_tat.md"), "w", encoding="utf-8", newline="\n").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
