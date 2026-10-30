# -*- coding: utf-8 -*-
"""Căn hàng: theo từ giữa đáp án và câu ASR (Levenshtein có truy vết); căn hàng cưỡng bức CTC (wav2vec2) để lấy
thời điểm từng âm tiết trong âm thanh."""
import re
import unicodedata

from thuvien.cham_chu import answer_variants, best_cer, equiv, norm


def align(ref, hyp):
    """Trạng thái từng từ đáp án: 'ok' | 'sub' | 'del' (căn hàng Levenshtein theo từ, truy vết)."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]))
    out, i, j = [None] * n, n, m
    while i > 0:
        if j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            out[i - 1] = "ok" if ref[i - 1] == hyp[j - 1] else "sub"
            i, j = i - 1, j - 1
        elif d[i][j] == d[i - 1][j] + 1:
            out[i - 1] = "del"
            i -= 1
        else:
            j -= 1
    return out
def word_states(m, hyp, lex):
    _, v = best_cer(answer_variants(m, lex), hyp)
    return align(equiv(norm(v)).split(), equiv(norm(hyp)).split())


# ------------------------------------------------------------------ căn hàng CTC
FRAME_S = 0.02
TONE_MARKS = {"̀", "́", "̃", "̉", "̣"}   # huyền, sắc, ngã, hỏi, nặng
def words_of(text):
    t = unicodedata.normalize("NFC", text.lower())
    t = re.sub(r"[^\w\s]", " ", t)
    return t.split()
def char_tokens(ch, vocab):
    """Id token cho một ký tự: có sẵn thì dùng; không có thì tách NFD (chữ gốc + dấu kết hợp) nếu mọi phần đều có."""
    if ch in vocab:
        return [vocab[ch]]
    parts = unicodedata.normalize("NFD", ch)
    if all(p in vocab for p in parts):
        return [vocab[p] for p in parts]
    tones = [p for p in parts if p in TONE_MARKS]       # tách dấu thanh, giữ dấu mũ/móc/trăng trong chữ gốc
    base = unicodedata.normalize("NFC", "".join(p for p in parts if p not in TONE_MARKS))
    if base in vocab and all(t in vocab for t in tones):
        return [vocab[base]] + [vocab[t] for t in tones]
    return None
def ctc_align(logp, tokens, blank):
    """Viterbi CTC: logp (T, V) log-xác suất; tokens: id không blank. Trả [(khung đầu, khung cuối)] cho từng token,
    hoặc None nếu không căn được (âm thanh quá ngắn)."""
    import numpy as np
    T = logp.shape[0]
    ext = [blank]
    for t in tokens:
        ext += [t, blank]
    S = len(ext)
    if T < len(tokens):
        return None
    neg = -1e30
    ext = np.asarray(ext)
    dp = np.full((T, S), neg)
    bp = np.zeros((T, S), dtype=np.int64)
    dp[0, 0] = logp[0, ext[0]]
    if S > 1:
        dp[0, 1] = logp[0, ext[1]]
    skip_ok = np.zeros(S, dtype=bool)          # được nhảy s-2 -> s: token khác blank và khác token cách 2 bước
    skip_ok[2:] = (ext[2:] != blank) & (ext[2:] != ext[:-2])
    for t in range(1, T):
        prev = dp[t - 1]
        c0 = prev
        c1 = np.concatenate(([neg], prev[:-1]))
        c2 = np.where(skip_ok, np.concatenate(([neg, neg], prev[:-2])), neg)
        cand = np.stack([c0, c1, c2])
        arg = cand.argmax(axis=0)
        dp[t] = cand[arg, np.arange(S)] + logp[t, ext]
        bp[t] = arg
    s = S - 1 if S == 1 or dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2
    path = [0] * T
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= int(bp[t, s])
    spans = [None] * len(tokens)
    for t, s in enumerate(path):
        if s % 2 == 1:
            k = s // 2
            a, b = spans[k] or (t, t)
            spans[k] = (min(a, t), max(b, t))
    return spans if all(spans) else None
def word_spans(char_spans, word_lens):
    out, i = [], 0
    for n in word_lens:
        seg = char_spans[i:i + n]
        out.append((seg[0][0], seg[-1][1] + 1))
        i += n
    return out
