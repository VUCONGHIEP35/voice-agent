#!/usr/bin/env bash
# Dựng môi trường trên NÚT ĐẦU bcm-headnode02 (nút đầu có mạng, các nút DGX chạy job ở chế độ offline).
# Chạy lại được: bước nào đã xong thì bỏ qua. Chỉ ghi trong $BASE (mặc định ~/asr_tts_o_to); không đụng ~/vieneu, ~/venvs.
#   bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/setup_server.sh
# Trước đó (một lần): đặt gói vào $BASE/goi/, kiểm sha256 và giải nén vào $BASE/code (xem dieuphoi/slurm/HUONG_DAN.md).
set -euo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
UV=${UV:-$HOME/.local/bin/uv}
export UV_CACHE_DIR=$BASE/cache/uv UV_PYTHON_INSTALL_DIR=$BASE/cache/uv-python PIP_CACHE_DIR=$BASE/cache/pip \
       TMPDIR=$BASE/cache/tmp HF_HOME=$BASE/cache/hf
mkdir -p "$TMPDIR" "$HF_HOME" "$BASE/hf_pinned" "$BASE/ct2" "$BASE/zipformer30m" "$BASE/logs" "$BASE/ket_qua"
LOG=$BASE/logs/setup_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
echo "== $(date '+%F %T') setup trên $(hostname), BASE=$BASE"
[ "$(hostname)" = bcm-headnode02 ] || echo "CẢNH BÁO: không phải nút đầu bcm-headnode02"
[ -f "$TG/run_pilot.py" ] || { echo "Chưa giải nén mã vào $TG"; exit 2; }

echo "== 1. Python 3.13 + hai venv (uv)"
"$UV" python install 3.13
[ -x "$BASE/venv_tts/bin/python" ] || "$UV" venv --python 3.13 "$BASE/venv_tts"
[ -x "$BASE/venv_zip/bin/python" ] || "$UV" venv --python 3.13 "$BASE/venv_zip"
"$UV" pip install --python "$BASE/venv_tts/bin/python" -r "$TG/requirements_server.txt"
"$UV" pip install --python "$BASE/venv_zip/bin/python" -r "$TG/requirements_zip.txt"

echo "== 2. Mô hình đúng revision ghim -> $BASE/hf_pinned"
(cd "$TG" && "$BASE/venv_tts/bin/python" -m dieuphoi.tai_mo_hinh --out "$BASE/hf_pinned")

echo "== 3. PhoWhisper-large -> CTranslate2 int8_float16 (như laptop/Colab), so sha256 với nguon.json"
CT2_DIR=$BASE/ct2/PhoWhisper-large-int8
if [ ! -f "$CT2_DIR/model.bin" ]; then
  nice -n 19 "$BASE/venv_tts/bin/ct2-transformers-converter" --model "$BASE/hf_pinned/PhoWhisper-large" \
    --output_dir "$CT2_DIR.tmp" --quantization int8_float16 --low_cpu_mem_usage \
    --copy_files tokenizer.json preprocessor_config.json
  mv "$CT2_DIR.tmp" "$CT2_DIR"
fi
"$BASE/venv_tts/bin/python" - "$CT2_DIR/model.bin" "$TG/.cache/ct2/PhoWhisper-large-int8/nguon.json" <<'EOF'
import hashlib, json, sys
h = hashlib.sha256()
with open(sys.argv[1], "rb") as f:
    for b in iter(lambda: f.read(1 << 20), b""):
        h.update(b)
want = json.load(open(sys.argv[2]))["model_bin_sha256"]
print("CT2 model.bin", h.hexdigest(), "KHỚP laptop" if h.hexdigest() == want else f"KHÁC laptop ({want})")
sys.exit(0 if h.hexdigest() == want else 3)
EOF

echo "== 4. Zipformer-30M (kiểm sha256 LFS)"
(cd "$TG" && ZIPFORMER_DIR=$BASE/zipformer30m "$BASE/venv_zip/bin/python" -m buoc.tai_zipformer)

echo "== 5. Kết quả phần A (chỉ để chấm Z/T và báo cáo gộp; không sinh lại)"
if [ -f "$BASE/goi/ket_qua_A.tar.gz" ] && [ ! -f "$TG/runs/ket_qua_A/runs/eval1000_A/manifest.jsonl" ]; then
  (cd "$BASE/goi" && sha256sum -c ket_qua_A.tar.gz.sha256)
  mkdir -p "$TG/runs/ket_qua_A"
  tar -xzf "$BASE/goi/ket_qua_A.tar.gz" -C "$TG/runs/ket_qua_A" --no-same-owner
fi

echo "== 6. Bảng phiên bản -> $BASE/server_env.json"
"$BASE/venv_tts/bin/python" - "$BASE" <<'EOF'
import importlib.metadata as md, json, os, platform, subprocess, sys, time
base = sys.argv[1]
pk = lambda py, names: json.loads(subprocess.run([py, "-c", "import importlib.metadata as md, json, sys; "
    "print(json.dumps({n: (md.version(n) if n else None) for n in sys.argv[1:]}))", *names],
    capture_output=True, text=True, check=True).stdout)
env = dict(ghi_luc=time.strftime("%F %T"), may=platform.node(), python=platform.python_version(),
           venv_tts=pk(f"{base}/venv_tts/bin/python", ["torch", "torchaudio", "vieneu", "transformers", "tokenizers",
               "huggingface_hub", "ctranslate2", "faster-whisper", "sea-g2p", "onnxruntime", "numpy", "soundfile", "soxr",
               "nvidia-cublas-cu12", "nvidia-cudnn-cu12"]),
           venv_zip=pk(f"{base}/venv_zip/bin/python", ["sherpa-onnx", "numpy", "soundfile", "soxr"]),
           pins=json.load(open(f"{base}/hf_pinned/pins.json")),
           zipformer=json.load(open(f"{base}/zipformer30m/ad6f873b/nguon.json")))
want = {"torch": "2.8.0", "vieneu": "3.8.3", "transformers": "4.57.6", "ctranslate2": "4.8.3", "faster-whisper": "1.2.1"}
bad = {k: env["venv_tts"][k] for k, v in want.items() if not env["venv_tts"][k].startswith(v)}
env["lech_ban_ghim"] = bad
json.dump(env, open(f"{base}/server_env.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: env[k] for k in ("python", "venv_tts", "venv_zip", "lech_ban_ghim")}, ensure_ascii=False, indent=1))
print({k: (v["revision"][:8], v["license"]) for k, v in env["pins"].items()})
sys.exit(3 if bad else 0)
EOF
echo "== $(date '+%F %T') setup XONG. Log: $LOG"
