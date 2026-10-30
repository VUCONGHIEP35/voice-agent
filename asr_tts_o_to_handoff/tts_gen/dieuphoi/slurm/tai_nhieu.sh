#!/usr/bin/env bash
# Tải nguồn nhiễu (CAVEMOVE 7,6 GB, AISHELL-5 13 GB) trên NÚT ĐẦU bcm-headnode02 (có mạng), chạy nền:
#   nohup bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/tai_nhieu.sh [tat_ca|cavemove|aishell5] >/dev/null 2>&1 &
# Chạy lại được (tải tiếp tệp .part, bỏ qua tệp đã giải nén). Chỉ ghi trong $BASE/nhieu và $BASE/logs.
set -euo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
mkdir -p "$BASE/nhieu" "$BASE/logs"
LOG=$BASE/logs/tai_nhieu_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
echo "== $(date '+%F %T') tai_nhieu ${1:-tat_ca} trên $(hostname); đĩa: $(df -h "$BASE" | tail -1)"
cd "$TG"
"$BASE/venv_rir/bin/python" -m buoc.nhieu_tai "${1:-tat_ca}" --dich "$BASE/nhieu"
du -sh "$BASE"/nhieu/* || true
echo "== $(date '+%F %T') tai_nhieu XONG. Log: $LOG"
