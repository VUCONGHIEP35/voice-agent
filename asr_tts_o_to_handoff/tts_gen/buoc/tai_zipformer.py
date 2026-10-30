# -*- coding: utf-8 -*-
"""Tải Zipformer-30M (hynt/Zipformer-30M-RNNT-6000h) đúng commit đã ghim vào .cache/zipformer30m/<commit8>/.

Chạy (từ tts_gen/):  .venv_zip/Scripts/python -m buoc.tai_zipformer      (thư mục ra đổi bằng biến ZIPFORMER_DIR)
Chỉ tải ONNX (fp32 + int8), bpe.model, config.json (thực chất là bảng token). KHÔNG tải jit_script.pt (TorchScript nạp
bằng pickle, có thể chạy mã) và qr.jpg. Mỗi tệp: kiểm kích thước và sha256 với thông tin LFS do API HF trả về (tệp không
LFS thì chỉ kiểm kích thước), ghi tạm rồi đổi tên. Sau đó dựng tokens.txt từ config.json và ghi nguon.json.
Giấy phép mô hình: CC BY-NC-ND 4.0 (chỉ đánh giá/nghiên cứu phi thương mại; không chia sẻ bản tinh chỉnh).
"""
import hashlib
import json
import os
import re
import urllib.request
from cauhinh.mo_hinh import ZIPFORMER_REPO as REPO, ZIPFORMER_REV as REV  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
WANT = ["encoder-epoch-20-avg-10.int8.onnx", "decoder-epoch-20-avg-10.int8.onnx", "joiner-epoch-20-avg-10.int8.onnx",
        "encoder-epoch-20-avg-10.onnx", "decoder-epoch-20-avg-10.onnx", "joiner-epoch-20-avg-10.onnx",
        "bpe.model", "config.json"]
MAX_BYTES = 200 * 2 ** 20
# Thư mục ra: biến ZIPFORMER_DIR (vd trên máy chủ ~/asr_tts_o_to/zipformer30m) + /<commit8>; mặc định .cache/zipformer30m/
OUT = os.path.join(os.environ.get("ZIPFORMER_DIR") or os.path.join(HERE, ".cache", "zipformer30m"), REV[:8])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read(5 * 2 ** 20))


def download(name, size, oid):
    dst = os.path.join(OUT, name)
    if os.path.exists(dst) and os.path.getsize(dst) == size and (oid is None or sha256(dst) == oid):
        return dst
    url = f"https://huggingface.co/{REPO}/resolve/{REV}/{name}"
    tmp = dst + ".tmp"
    got = 0
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        for b in iter(lambda: r.read(1 << 20), b""):
            got += len(b)
            if got > min(size, MAX_BYTES):
                raise SystemExit(f"{name}: nhận quá {size} byte, dừng")
            f.write(b)
    if got != size:
        raise SystemExit(f"{name}: kích thước {got} != {size}")
    if oid is not None and sha256(tmp) != oid:
        raise SystemExit(f"{name}: sha256 lệch với LFS {oid}")
    os.replace(tmp, dst)
    print(f"Tải {name} ({size / 2 ** 20:.1f} MB)")
    return dst


def build_tokens(cfg_path, out_path):
    """config.json của repo là các dòng 'token id' -> tokens.txt cho sherpa-onnx; kiểm id liên tục, <blk> = 0."""
    lines = [l for l in open(cfg_path, encoding="utf-8").read().splitlines() if l.strip()]
    pairs = []
    for l in lines:
        m = re.fullmatch(r"(\S+) (\d+)", l)
        if not m:
            raise SystemExit(f"Dòng token lạ: {l!r}")
        pairs.append((m.group(1), int(m.group(2))))
    ids = [i for _, i in pairs]
    if ids != list(range(len(ids))) or pairs[0][0] != "<blk>":
        raise SystemExit("Bảng token không liên tục hoặc <blk> không phải 0")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(f"{t} {i}" for t, i in pairs) + "\n")
    return len(pairs)


def main():
    os.makedirs(OUT, exist_ok=True)
    tree = {e["path"]: e for e in get_json(f"https://huggingface.co/api/models/{REPO}/tree/{REV}")}
    info = {}
    for name in WANT:
        e = tree[name]
        oid = (e.get("lfs") or {}).get("oid")
        p = download(name, e["size"], oid)
        info[name] = dict(byte=e["size"], sha256=sha256(p), lfs_oid=oid)
    n = build_tokens(os.path.join(OUT, "config.json"), os.path.join(OUT, "tokens.txt"))
    json.dump(dict(repo=REPO, revision=REV, license="cc-by-nc-nd-4.0", files=info, tokens=n,
                   bo_qua=["jit_script.pt", "qr.jpg"]), open(os.path.join(OUT, "nguon.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Xong: {OUT} | {n} token")


if __name__ == "__main__":
    main()
