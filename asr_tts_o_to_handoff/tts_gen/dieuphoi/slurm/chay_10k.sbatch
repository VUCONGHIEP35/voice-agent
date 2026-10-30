#!/usr/bin/env bash
#SBATCH --job-name=asrtts_10k
#SBATCH --partition=defq
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=08:00:00
# MỘT job (người dùng chọn 25/10/2026), chạy song song bên trong bằng dieuphoi/slurm/dieu_phoi.py trên 1 A100 80 GB.
# Biến (truyền qua nop_10k.sh): SHARDS="smoke p01 …" (bắt buộc); THU_LO=1 để so lô 2/16 trước (một lần, có kết quả thì bỏ
# qua); GPU_SLOTS (mặc định 4), TTS_SLOTS (1), CPU_SLOTS (3). Nộp lại cùng lệnh là chạy tiếp từ chỗ dừng.
set -uo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
PY=$BASE/venv_tts/bin/python
cd "$TG" || exit 2
mkdir -p runs
echo "== $(date '+%F %T') job ${SLURM_JOB_ID:-?} trên $(hostname), SHARDS=${SHARDS:?đặt SHARDS}, GPU=${CUDA_VISIBLE_DEVICES:-?}"
nvidia-smi --query-gpu=name,memory.total,driver_version,temperature.gpu --format=csv
if [ "${THU_LO:-0}" = 1 ] && [ ! -f runs/thu_lo/ket_qua.json ]; then
  HF_HUB_OFFLINE=1 "$PY" -m dieuphoi.dieu_phoi --thu-lo || { echo "*** thử cỡ lô lỗi ***"; exit 3; }
fi
# shellcheck disable=SC2086
"$PY" -m dieuphoi.dieu_phoi --shards $SHARDS --gpu-slots "${GPU_SLOTS:-4}" --tts-slots "${TTS_SLOTS:-1}" --cpu-slots "${CPU_SLOTS:-3}"
rc=$?
echo "== $(date '+%F %T') dieu_phoi rc=$rc"
exit $rc
