#!/usr/bin/env bash
# Dựng venv_rir trên NÚT ĐẦU bcm-headnode02 (có mạng). Chạy lại được. Chỉ ghi trong $BASE; không đụng venv_tts.
#   bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/setup_rir.sh
set -euo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
UV=${UV:-$HOME/.local/bin/uv}
export UV_CACHE_DIR=$BASE/cache/uv UV_PYTHON_INSTALL_DIR=$BASE/cache/uv-python TMPDIR=$BASE/cache/tmp
mkdir -p "$TMPDIR" "$BASE/logs"
LOG=$BASE/logs/setup_rir_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
echo "== $(date '+%F %T') setup_rir trên $(hostname), BASE=$BASE"
[ -x "$BASE/venv_rir/bin/python" ] || "$UV" venv --python 3.13 "$BASE/venv_rir"
"$UV" pip install --python "$BASE/venv_rir/bin/python" -r "$TG/requirements_rir.txt"
"$BASE/venv_rir/bin/python" -c "import sys, numpy, scipy, soundfile, soxr, pyroomacoustics, openpyxl; \
print(sys.version.split()[0], 'numpy', numpy.__version__, 'scipy', scipy.__version__, 'pyroomacoustics', pyroomacoustics.__version__)"
(cd "$TG" && "$BASE/venv_rir/bin/python" -m unittest kiemthu.test_rir)
echo "== RIR đo thật (McVAMPIRE, CAVEMOVE; CC BY 4.0) -> $BASE/rir_do (cần mạng: chỉ chạy trên nút đầu)"
(cd "$TG" && "$BASE/venv_rir/bin/python" -m buoc.rir_kho_do tai --dich "$BASE/rir_do")
echo "== $(date '+%F %T') setup_rir XONG. Log: $LOG"
