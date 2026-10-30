#!/usr/bin/env bash
#SBATCH --job-name=asrtts_tocdo
#SBATCH --partition=defq
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
# Đo độ dài âm tiết theo vị trí (do_toc_do_am_tiet.py) trên 1.000 câu A+B. Nộp:
#   sbatch --output=$HOME/asr_tts_o_to/logs/%x_%j.out --chdir=$HOME/asr_tts_o_to/code/tts_gen server/do_toc_do.sbatch
set -euo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
cd "$BASE/code/tts_gen"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
"$BASE/venv_tts/bin/python" do_toc_do_am_tiet.py runs/ket_qua_A/runs/eval1000_A runs/eval1000_B \
  --ctc "$BASE/hf_pinned/wav2vec2" --gate-name gate_hop_server --out reports/toc_do_am_tiet
tar -czf "$BASE/ket_qua/toc_do_am_tiet.tar.gz" -C "$BASE/code/tts_gen" reports/toc_do_am_tiet
(cd "$BASE/ket_qua" && sha256sum toc_do_am_tiet.tar.gz > toc_do_am_tiet.tar.gz.sha256)
echo "XONG"
