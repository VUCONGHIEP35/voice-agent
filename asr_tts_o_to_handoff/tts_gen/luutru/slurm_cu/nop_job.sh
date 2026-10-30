#!/usr/bin/env bash
# Nộp chay_eval.sbatch cho một SHARD (smoke | B). Chạy trên nút đầu:  bash server/nop_job.sh smoke
# - Từ chối nếu đã có job cùng tên của mình đang chờ/chạy (hai job cùng ghi một thư mục sẽ làm hỏng manifest).
# - Tài khoản user04: tối đa 2 job chạy, 6 job nộp, 1 GPU/job. Hết chỗ chạy thì job nằm chờ (AssocMaxJobsLimit), bình thường.
# - KHÔNG bao giờ scancel job không phải do script này nộp.
set -euo pipefail
SHARD=${1:?dùng: nop_job.sh smoke|B}
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
NAME=asrtts_$SHARD
mkdir -p "$BASE/logs"
if squeue -u "$USER" -h -o "%j" | grep -qx "$NAME"; then
  echo "Đã có job $NAME đang chờ/chạy:"; squeue -u "$USER" -n "$NAME"; exit 1
fi
n=$(squeue -u "$USER" -h | wc -l)
if [ "$n" -ge 6 ]; then echo "Tài khoản đã nộp $n job (tối đa 6), chưa nộp thêm"; exit 1; fi
JOB=$(sbatch --parsable --job-name="$NAME" --export=ALL,SHARD="$SHARD",BASE="$BASE" \
      --output="$BASE/logs/${NAME}_%j.out" --chdir="$TG" "$TG/server/chay_eval.sbatch")
echo "Đã nộp job $JOB ($NAME). Log: $BASE/logs/${NAME}_${JOB}.out"
echo "Theo dõi:  squeue -j $JOB   |   sacct -j $JOB --format=JobID,State,Elapsed,NodeList   |   tail -f $BASE/logs/${NAME}_${JOB}.out"
squeue -j "$JOB"
