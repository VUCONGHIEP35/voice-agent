#!/usr/bin/env bash
#SBATCH --job-name=asrtts_eval
#SBATCH --partition=defq
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=06:00:00
# Một job làm trọn một lượt: TTS -> kiểm -> đổi giọng -> ASR (M, L, c3, T, Z) -> chấm -> báo cáo -> đóng gói.
# Tuần tự trong một job nên TTS và ASR không chạy cùng lúc. Bước nào đã có kết quả thì bỏ qua -> nộp lại là chạy tiếp.
# Nộp bằng server/nop_job.sh (đặt SHARD=smoke|B, --output vào $BASE/logs). Chạy offline: mô hình đã tải ở setup_server.sh.
set -uo pipefail
SHARD=${SHARD:?đặt SHARD=smoke hoặc B}
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
PY=$BASE/venv_tts/bin/python
PYZ=$BASE/venv_zip/bin/python
PIN=$BASE/hf_pinned
CT2_DIR=$BASE/ct2/PhoWhisper-large-int8
LEX=lexicon/asr_bien_the.tsv
RUN_A=runs/ket_qua_A/runs/eval1000_A
case "$SHARD" in
  smoke) IN=runs/eval1000_A/logs/input_smoke24.jsonl; RUN=runs/server_smoke ;;
  B)     IN=eval1000_tts/shard_B.jsonl;               RUN=runs/eval1000_B ;;
  *)     echo "SHARD lạ: $SHARD"; exit 64 ;;
esac
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1 ZIPFORMER_DIR=$BASE/zipformer30m
TTS_ARGS=(--batch 16 --dtype bfloat16 --backbone-repo "$PIN/vieneu" --moss-tokenizer "$PIN/moss")
cd "$TG" || exit 2
mkdir -p "$RUN/logs"
echo "== $(date '+%F %T') job ${SLURM_JOB_ID:-?} trên $(hostname), SHARD=$SHARD, RUN=$RUN, GPU=${CUDA_VISIBLE_DEVICES:-?}"
nvidia-smi --query-gpu=name,memory.total,driver_version,temperature.gpu --format=csv | tee -a "$RUN/logs/gpu_dau.txt"
nvidia-smi --query-gpu=timestamp,temperature.gpu,utilization.gpu,memory.used,clocks.sm,clocks_throttle_reasons.active \
  --format=csv,noheader -l 5 >> "$RUN/logs/gpu_log.csv" 2>/dev/null &
MON=$!
trap 'kill $MON 2>/dev/null' EXIT

# Thư viện CUDA 12 (cuBLAS/cuDNN đi kèm torch cu128) cho ctranslate2: CHỈ đặt trong lệnh CT2.
# Gọi /usr/bin/env tường minh: trên cụm, "env" trong PATH là ~/.local/bin/env (script của trình cài uv, không chạy lệnh),
# lần chạy thử 24/10/2026 bước CT2 vì thế "xong" ngay với rc=0 mà không ghi gì.
CT2_LD=$("$PY" -c "import glob, os, site; print(':'.join(sorted(glob.glob(os.path.join(site.getsitepackages()[0], 'nvidia', '*', 'lib')))))")

step() {   # step <tên> <lệnh...>: chạy, ghi thời gian; lỗi thì dừng cả job (trừ khi đã là bước cuối)
  local name=$1; shift
  local t0; t0=$(date +%s.%N)
  echo "== $(date '+%F %T') [$name] $*"
  "$@"; local rc=$?
  local dt; dt=$(awk -v a="$t0" -v b="$(date +%s.%N)" 'BEGIN { printf "%.1f", b - a }')
  "$PY" server/ghi_buoc.py ghi "$RUN" "$name" "$dt" "$rc"
  echo "== [$name] rc=$rc, ${dt%.*} s"
  if [ "$rc" -ne 0 ]; then echo "*** DỪNG ở bước $name (rc=$rc) ***"; exit "$rc"; fi
}
asr_done() { "$PY" server/ghi_buoc.py asr_xong "$1" "$2"; }
need() {   # need <run> <tag>: sau một bước ASR, bắt buộc có đủ asr_<tag>.jsonl (rc=0 mà không có tệp là lỗi)
  asr_done "$1" "$2" || { echo "*** DỪNG: bước ASR rc=0 nhưng thiếu $1/asr_$2.jsonl ***"; exit 3; }
}

# 1. TTS (run_pilot tự chạy tiếp từ manifest nếu job trước bị ngắt)
step tts "$PY" run_pilot.py --input "$IN" --out "$RUN" "${TTS_ARGS[@]}"
step kiem_tts "$PY" check_run.py "$RUN" "$IN"
# 2. Đổi giọng cho câu vẫn lỗi (1 vòng). Đã có fallback_input.jsonl thì chỉ chạy tiếp phần dở.
if [ -s "$RUN/fallback_input.jsonl" ]; then
  step tts_doi_giong "$PY" run_pilot.py --input "$RUN/fallback_input.jsonl" --out "$RUN" "${TTS_ARGS[@]}"
else
  step tts_doi_giong "$PY" make_fallback.py "$RUN" --run-tts --batch 16 --pilot-args "${TTS_ARGS[*]:2}"
fi
step kiem_sau_doi_giong "$PY" check_run.py "$RUN" "$IN"

# 3. ASR, mỗi mô hình một tiến trình, lần lượt
asr_all() {   # asr_all <run>
  local r=$1
  asr_done "$r" PhoWhisper-medium || step asr_medium "$PY" asr_check.py "$r" --model "$PIN/PhoWhisper-medium" --batch 2 --lexicon "$LEX"
  asr_done "$r" PhoWhisper-large-ct2-int8 || step asr_large_ct2 /usr/bin/env LD_LIBRARY_PATH="$CT2_LD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
      "$PY" asr_check.py "$r" --model vinai/PhoWhisper-large --backend ct2 --ct2-dir "$CT2_DIR" --lexicon "$LEX"
  need "$r" PhoWhisper-medium; need "$r" PhoWhisper-large-ct2-int8
  "$PY" server/ghi_buoc.py diag_xong "$r" || step asr_diagnose_c3 "$PY" asr_diagnose.py "$r" --whisper "$PIN/PhoWhisper-medium" \
      --ctc "$PIN/wav2vec2" --skip c1 c2
}
asr_target_z() {   # asr_target_z <run>: T (mô hình đích, chỉ đo) và Z
  local r=$1
  asr_done "$r" PhoWhisper-small || step asr_dich_T "$PY" asr_check.py "$r" --model "$PIN/PhoWhisper-small" --batch 2 --lexicon "$LEX"
  asr_done "$r" Zipformer-30M-int8-beam4 || step asr_zipformer_Z "$PYZ" asr_zipformer.py "$r" --decoding modified_beam_search \
      --beam 4 --threads 8
  need "$r" PhoWhisper-small; need "$r" Zipformer-30M-int8-beam4
}
asr_all "$RUN"
asr_target_z "$RUN"

# 4. Chấm: gate_hop (mọi cấu hình có) và gate_hop_server (L, M, c3, Z: cùng bộ cho A và B để so)
step gate_union "$PY" gate_union.py "$RUN" --lexicon "$LEX"
step gate_union_server "$PY" gate_union.py "$RUN" --lexicon "$LEX" --configs L M c3 Z --out-name gate_hop_server

OUT_FILES=("$RUN")
if [ "$SHARD" = B ] && [ -f "$RUN_A/manifest.jsonl" ]; then
  # 5. Phần A (đã sinh trên Colab): dựng audio16, thêm T và Z, chấm cùng bộ cấu hình, báo cáo gộp 1.000 câu
  RUN_SAVE=$RUN; RUN=$RUN_A
  step audio16_A "$PY" make_audio16.py "$RUN_A"
  asr_target_z "$RUN_A"
  step gate_union_server "$PY" gate_union.py "$RUN_A" --lexicon "$LEX" --configs L M c3 Z --out-name gate_hop_server
  RUN=$RUN_SAVE
  step report_eval "$PY" report_eval.py "$RUN_A" "$RUN" --plan eval1000_tts/eval_1000.jsonl --out reports/eval1000_AB \
      --gate-name gate_hop_server
  OUT_FILES+=(reports/eval1000_AB "$RUN_A/asr_PhoWhisper-small.jsonl" "$RUN_A/asr_gate_PhoWhisper-small.csv"
              "$RUN_A/asr_Zipformer-30M-int8-beam4.jsonl" "$RUN_A/gate_hop_server.csv" "$RUN_A/gate_hop_server_tom_tat.json"
              "$RUN_A/logs")
fi

# 6. Đóng gói kết quả (bỏ audio16: dựng lại được bằng make_audio16.py)
PKG=$BASE/ket_qua/ket_qua_${SHARD}.tar.gz
kill $MON 2>/dev/null
tar -czf "$PKG.tmp" --exclude='*/audio16/*' -C "$TG" "${OUT_FILES[@]}" && mv "$PKG.tmp" "$PKG"
(cd "$BASE/ket_qua" && sha256sum "$(basename "$PKG")" > "$(basename "$PKG").sha256" && cat "$(basename "$PKG").sha256")
echo "== $(date '+%F %T') XONG SHARD=$SHARD -> $PKG"
