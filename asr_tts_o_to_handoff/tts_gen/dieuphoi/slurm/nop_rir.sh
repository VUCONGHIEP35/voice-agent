#!/usr/bin/env bash
# Nộp chay_rir.sbatch. Chạy trên nút đầu, từ bất kỳ đâu:
#   bash dieuphoi/slurm/nop_rir.sh thu                 # thử nhỏ + phiếu nghe (dừng: người dùng nghe)
#   bash dieuphoi/slurm/nop_rir.sh "kho kho_do so nghe gan goi"   # kho mô phỏng + kho đo + so hai kho + phiếu nghe
#                                                                # + bảng gán + gói (dừng: người dùng xem và nghe)
#   bash dieuphoi/slurm/nop_rir.sh "chap asr qa goi"   # chập, CER trước/sau trên 500 bản dev, QA, gói
# Chỉ MỘT job asrtts_* của mình tại một thời điểm. Chỉ xin GPU khi STEPS có asr. KHÔNG scancel job không do mình nộp.
set -euo pipefail
STEPS=${1:?dùng: nop_rir.sh "<các bước>"}
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
mkdir -p "$BASE/logs"
[ -x "$BASE/venv_rir/bin/python" ] || { echo "Chưa có venv_rir: chạy dieuphoi/slurm/setup_rir.sh trên nút đầu"; exit 1; }
if squeue -u "$USER" -h -o "%j" | grep -q "^asrtts_"; then
  echo "Đã có job asrtts_* đang chờ/chạy, không nộp thêm:"; squeue -u "$USER" -o "%.8i %.20j %.8T %.10M %R"; exit 1
fi
GRES=()
case " $STEPS " in *" asr "*) GRES=(--gres=gpu:a100:1) ;; esac
JOB=$(sbatch --parsable "${GRES[@]}" --export=ALL,STEPS="$STEPS",BASE="$BASE" \
      --output="$BASE/logs/asrtts_rir_%j.out" --chdir="$TG" "$TG/dieuphoi/slurm/chay_rir.sbatch")
echo "Đã nộp job $JOB (bước: $STEPS${GRES:+, có GPU}). Log: $BASE/logs/asrtts_rir_${JOB}.out"
squeue -j "$JOB"
