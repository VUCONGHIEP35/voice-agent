#!/usr/bin/env bash
# Nộp chay_10k.sbatch. Chạy trên nút đầu:
#   bash dieuphoi/slurm/nop_10k.sh "smoke p01" 1        # danh sách phần, THU_LO (1 = so lô 2/16 trước)
#   bash dieuphoi/slurm/nop_10k.sh "p02 p03 p04 p05 p06 p07 p08 p09 p10"
# Chỉ MỘT job asrtts_* của mình tại một thời điểm (người dùng chọn 25/10/2026; chừa chỗ cho người dùng chung tài khoản).
# KHÔNG bao giờ scancel job không phải do script này nộp.
set -euo pipefail
SHARDS=${1:?dùng: nop_10k.sh "<danh sách phần>" [THU_LO]}
THU_LO=${2:-0}
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
mkdir -p "$BASE/logs"
if squeue -u "$USER" -h -o "%j" | grep -q "^asrtts_"; then
  echo "Đã có job asrtts_* đang chờ/chạy, không nộp thêm:"; squeue -u "$USER" -o "%.8i %.20j %.8T %.10M %R"; exit 1
fi
JOB=$(sbatch --parsable --export=ALL,SHARDS="$SHARDS",THU_LO="$THU_LO",BASE="$BASE",GPU_SLOTS="${GPU_SLOTS:-4}" \
      --output="$BASE/logs/asrtts_10k_%j.out" --chdir="$TG" "$TG/dieuphoi/slurm/chay_10k.sbatch")
echo "Đã nộp job $JOB (phần: $SHARDS). Log: $BASE/logs/asrtts_10k_${JOB}.out; tiến độ: $TG/runs/full10k_dieu_phoi.log"
squeue -j "$JOB"
