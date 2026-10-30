#!/usr/bin/env bash
#SBATCH --job-name=asrtts_nhieu
#SBATCH --partition=defq
#SBATCH --cpus-per-task=64
#SBATCH --mem=128G
#SBATCH --time=06:00:00
# Bước trộn nhiễu giai đoạn 1 (docs/ke_hoach_nhieu_v1.md). MỘT job. Đầu vào: bộ vang runs/rir_v2/aug_v1/_reverb và
# asr_dev của bước RIR (runs/rir_v2/asr_dev, đã có ASR sạch/vang); nhiễu CAVEMOVE ở $BASE/nhieu (buoc.nhieu_tai).
# Biến STEPS (truyền qua nop_nhieu.sh), các bước chạy theo thứ tự ghi:
#   kho   chỉ mục nhiễu theo preset                                   -> runs/nhieu_v1/kho/
#   gan   bảng gán preset, tệp, kênh, SNR                             -> runs/nhieu_v1/gan/
#   tron  trộn 13.126 bản + lượt ASR asr_dev/nhieu (500) + lưới asr_luoi (500 × 6 preset × 4 SNR)
#   asr   PhoWhisper L, M, T trên asr_dev/nhieu và asr_luoi (venv_tts, cần GPU: nop_nhieu.sh tự xin)
#   qa    phantich.nhieu_qa -> runs/nhieu_v1/qa/
#   goi   gói kho, gan, manifest, asr (không gói âm thanh) -> $BASE/ket_qua/nhieu_v1_<ngày>.tar.gz + .sha256
set -uo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
PYR=$BASE/venv_rir/bin/python
PY=$BASE/venv_tts/bin/python
PIN=$BASE/hf_pinned
CT2=$BASE/ct2/PhoWhisper-large-int8
LEX=lexicon/asr_bien_the.tsv
R=runs/nhieu_v1
V=runs/rir_v2
N=${SLURM_CPUS_PER_TASK:-64}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd "$TG" || exit 2
mkdir -p "$R"
echo "== $(date '+%F %T') job ${SLURM_JOB_ID:-?} trên $(hostname), STEPS=${STEPS:?đặt STEPS}, $N lõi, GPU=${CUDA_VISIBLE_DEVICES:-không}"
buoc() { echo "== $(date '+%F %T') bắt đầu $1"; SECONDS=0; }
xong() { echo "== $(date '+%F %T') xong $1 sau ${SECONDS} s"; }
goi() {  # goi <tên> <đường dẫn...>
  local ten=$1; shift
  local out=$BASE/ket_qua/$ten.tar.gz
  mkdir -p "$BASE/ket_qua"
  tar -czf "$out" "$@" && (cd "$BASE/ket_qua" && sha256sum "$ten.tar.gz" > "$ten.tar.gz.sha256")
  echo "Gói: $out ($(du -h "$out" | cut -f1)), sha256 $(cut -c1-16 "$out.sha256")…"
}
for s in $STEPS; do
  buoc "$s"
  case $s in
    kho) "$PYR" -m buoc.nhieu_kho --nhieu "$BASE/nhieu" --out $R/kho || exit 3 ;;
    gan) "$PYR" -m buoc.nhieu_gan --vang $V/aug_v1/_reverb/manifest.jsonl --kho $R/kho --out $R/gan || exit 3 ;;
    tron) "$PYR" -m buoc.nhieu_tron --gan $R/gan --kho $R/kho --nhieu "$BASE/nhieu" --vang-goc $V/aug_v1/_reverb \
            --out $R/aug_v1 --workers "$N" --asr-goc $V/asr_dev --asr-out $R || exit 3 ;;
    asr)
      nvidia-smi --query-gpu=name,memory.total --format=csv || { echo "*** bước asr cần GPU ***"; exit 3; }
      LD=$(ls -d "$BASE"/venv_tts/lib/python3*/site-packages/nvidia/*/lib | paste -sd:)
      for d in $R/asr_dev/nhieu $R/asr_luoi; do
        "$PY" -m buoc.asr_whisper $d --model "$PIN/PhoWhisper-medium" --batch 16 --lexicon $LEX || exit 3
        "$PY" -m buoc.asr_whisper $d --model "$PIN/PhoWhisper-small" --batch 16 --lexicon $LEX || exit 3
        /usr/bin/env LD_LIBRARY_PATH="$LD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$PY" -m buoc.asr_whisper $d \
          --model vinai/PhoWhisper-large --backend ct2 --ct2-dir "$CT2" --lexicon $LEX || exit 3
      done ;;
    qa) "$PYR" -m phantich.nhieu_qa --goc $R --asr-goc $V/asr_dev || exit 3 ;;
    # gói những gì đã có; không gói âm thanh (aug_v1/<split>/, luoi_am_thanh/)
    goi) ds=$(ls -d $R/kho $R/gan $R/qa $R/aug_v1/manifest.jsonl $R/asr_dev/nhieu/*.jsonl $R/asr_dev/nhieu/*.csv \
                 $R/asr_luoi/*.jsonl $R/asr_luoi/*.csv 2>/dev/null)
         # shellcheck disable=SC2086
         goi "nhieu_v1_$(date +%Y%m%d_%H%M)" $ds ;;
    *) echo "Bước lạ: $s"; exit 2 ;;
  esac
  xong "$s"
done
echo "== $(date '+%F %T') hết STEPS"
