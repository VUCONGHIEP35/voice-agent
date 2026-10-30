# -*- coding: utf-8 -*-
"""Đóng gói mã + đầu vào thành một zip kèm sha256 (chạy trên laptop), theo hồ sơ:
  colab   cho notebook colab_eval_A.ipynb
  server  cho cụm A100 HUST (tts_gen/server/: setup_server.sh, chay_eval.sbatch, nop_job.sh)

Chạy (từ tts_gen/):  python -m dieuphoi.dong_goi                   -> dist/colab_eval_A.zip (+ .sha256)
                     python -m dieuphoi.dong_goi --profile server  -> dist/server_eval_B.zip (+ .sha256)
Hồ sơ colab:
Gồm: mã *.py và notebook trong tts_gen/; eval1000_tts/; lexicon/; pilot/; reports/text_audit_*;
     runs/pilot100: manifest, run_config, kết quả ASR/chấm, tts_check_bf16_laptop.jsonl (để so kiểu số);
     runs/eval1000_A/logs/input_*.jsonl (đầu vào chạy thử 24 câu, 4 câu Thái Sơn);
     .cache/ct2/PhoWhisper-large-int8/nguon.json (lệnh chuyển CT2 và sha256 để đối chiếu trên Colab).
Không gồm: .venv, .cache (trừ nguon.json), mọi tệp âm thanh, __pycache__, các lượt chạy khác, data/ (không script nào
trên Colab cần bộ v3). Trong zip có DANH_SACH.tsv: đường dẫn, kích thước, sha256 từng tệp.
Hồ sơ server: mã *.py, server/*, requirements_*.txt, eval1000_tts/, lexicon/, runs/eval1000_A/logs/input_smoke24.jsonl,
nguon.json của CT2. Không có pilot, notebook, kết quả cũ. Mọi hồ sơ: tệp nằm trong FORBIDDEN (âm thanh, giong_that/, khóa,
.mcp.json, bản ghi hội thoại, venv, cache) bị chặn cứng, có test (test_pack.py).
"""
import argparse
import glob
import hashlib
import os
import re
import zipfile

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
AUDIO = (".flac", ".wav", ".mp3", ".ogg", ".m4a", ".opus")
PROFILES = {
    "colab": dict(zip="colab_eval_A.zip", pats=[
        "cauhinh/*.py", "thuvien/*.py", "buoc/*.py", "dieuphoi/*.py", "dieuphoi/slurm/*", "phantich/*.py", "kiemthu/*.py", "luutru/colab_eval_A.ipynb", "eval1000_tts/*", "lexicon/*", "pilot/*.jsonl", "reports/text_audit_*/*",
        "runs/pilot100/manifest.jsonl", "runs/pilot100/run_config.json", "runs/pilot100/asr_*.jsonl",
        "runs/pilot100/asr_gate_*.csv", "runs/pilot100/asr_diagnose.csv", "runs/pilot100/gate_hop*",
        "runs/pilot100/tts_check_bf16_laptop.jsonl", "runs/eval1000_A/logs/input_*.jsonl",
        ".cache/ct2/PhoWhisper-large-int8/nguon.json"]),
    "server": dict(zip="server_eval_B.zip", pats=[
        "cauhinh/*.py", "thuvien/*.py", "buoc/*.py", "dieuphoi/*.py", "dieuphoi/slurm/*", "phantich/*.py", "kiemthu/*.py", "requirements_*.txt", "eval1000_tts/*", "full10k/*", "lexicon/*",
        "runs/eval1000_A/logs/input_smoke24.jsonl", ".cache/ct2/PhoWhisper-large-int8/nguon.json"]),
}
# Không bao giờ đóng gói, dù mẫu tệp có khớp: âm thanh, giọng thật, khóa/cấu hình máy, bản ghi hội thoại, venv, cache khác
FORBIDDEN = re.compile(r"(\.(flac|wav|mp3|ogg|m4a|opus|pem|ppk)$)|(^|/)(giong_that|\.venv[^/]*|__pycache__|KET_NOI_USER04|"
                       r"00_SSH_KEYS)(/|$)|id_ed25519|id_rsa|\.mcp\.json$|phien_claude_ai\.jsonl$|(^|/)\.cache/(?!ct2/[^/]+/nguon\.json$)",
                       re.I)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def allowed(rel):
    return not rel.endswith(AUDIO) and not FORBIDDEN.search(rel)


def files(pats=None, root=HERE):
    pats = PROFILES["colab"]["pats"] if pats is None else pats
    out = []
    for p in pats:
        for f in sorted(glob.glob(os.path.join(root, p))):
            rel = os.path.relpath(f, root).replace(os.sep, "/")
            if os.path.isfile(f) and allowed(rel) and rel not in out:
                out.append(rel)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=list(PROFILES), default="colab")
    a = ap.parse_args()
    prof = PROFILES[a.profile]
    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    zp = os.path.join(dist, prof["zip"])
    rels = files(prof["pats"])
    lines = ["duong_dan\tbyte\tsha256"]
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in rels:
            full = os.path.join(HERE, rel)
            z.write(full, "tts_gen/" + rel)
            lines.append(f"tts_gen/{rel}\t{os.path.getsize(full)}\t{sha256(full)}")
        z.writestr("tts_gen/DANH_SACH.tsv", "\n".join(lines) + "\n")
    h = sha256(zp)
    with open(zp + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{h}  {prof['zip']}\n")
    print(f"{len(rels)} tệp, {os.path.getsize(zp) / 2 ** 20:.1f} MB -> {zp}\nsha256 {h}")


if __name__ == "__main__":
    main()
