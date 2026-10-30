# -*- coding: utf-8 -*-
"""So câu ASR nghe ra với đáp án: chuẩn hóa, CER/WER, đáp án biến thể (text_spoken, tts_text, từ điển), CER tốt nhất."""
import re
import unicodedata

from thuvien.van_ban import DIALECT_EQUIV, ref_variants, strip_tone, unify_tone_placement


REGIONS = ("Bắc", "Trung", "Nam")
def norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(unify_tone_placement(w) for w in t.split())  # hoả = hỏa, thuỷ = thủy
def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]
def cer(ref, hyp):
    ref, hyp = norm(ref).replace(" ", ""), norm(hyp).replace(" ", "")
    return edit_distance(ref, hyp) / max(len(ref), 1)
def wer(ref, hyp):
    r, h = norm(ref).split(), norm(hyp).split()
    return edit_distance(r, h) / max(len(r), 1)
def equiv(t):
    return " ".join(DIALECT_EQUIV.get(w, w) for w in t.split())
def answer_variants(m, lex):
    """Mọi đáp án chấp nhận được cho một dòng manifest: text_spoken và (nếu có) tts_text — chữ thật sự đưa vào TTS ở
    nhánh phiên âm từ ngoại —, mỗi dạng cộng các biến thể đọc trong từ điển. Không trùng, giữ thứ tự (text_spoken trước)."""
    out = ref_variants(norm(m["text_spoken"]), lex)
    if m.get("tts_text"):
        out = out + ref_variants(norm(m["tts_text"]), lex)
    return list(dict.fromkeys(out))
def best_cer(variants, hyp, tone=True):
    """(CER nhỏ nhất, biến thể khớp) trên các biến thể tham chiếu, so nguyên dạng và sau khi gộp từ địa phương."""
    h = norm(hyp)
    best = (float("inf"), "")
    for v in variants:
        for r, hh in ((v, h), (equiv(v), equiv(h))):
            if not tone:
                r, hh = strip_tone(r), strip_tone(hh)
            c = cer(r, hh)
            if c < best[0]:
                best = (c, v)
    return best
