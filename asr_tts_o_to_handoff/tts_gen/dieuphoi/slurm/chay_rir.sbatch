#!/usr/bin/env bash
#SBATCH --job-name=asrtts_rir
#SBATCH --partition=defq
#SBATCH --cpus-per-task=64
#SBATCH --mem=128G
#SBATCH --time=04:00:00
# Bước RIR (docs/ke_hoach_RIR_v3.md). MỘT job, không qua dieu_phoi (nên runs/DUNG_CHAT_LUONG không chặn). Không lọc CER.
# Biến STEPS (truyền qua nop_rir.sh), các bước chạy theo thứ tự ghi:
#   thu   kho thử 2 khoang mỗi loại + phiếu nghe 10 RIR mỗi loại xe + gói kết quả   -> runs/rir_v2/thu/
#   kho   cả kho mô phỏng 280 khoang (7 loại)                                                -> runs/rir_v2/kho/
#   kho_do  kho RIR đo thật từ $BASE/rir_do (tải trước bằng setup_rir.sh trên nút đầu)   -> runs/rir_v2/kho_do/
#   so    so kho mô phỏng với kho đo (EDT theo dải, DRR ghế sau; cần kho, kho_do)        -> runs/rir_v2/kho/so_sanh.json
#   nghe  phiếu nghe trên cả kho: 5 câu × 20 RIR mỗi loại xe, đợt 1 = 10 bản mỗi loại    -> runs/rir_v2/nghe/
#   gan   bảng gán (người dùng xem phân bố trước khi chập)                                -> runs/rir_v2/gan/
#   chap  chập + bộ đệm "chỉ có vang" + dựng 500 bản dev cho ASR                           -> runs/rir_v2/aug_v1/_reverb/, asr_dev/
#   asr   PhoWhisper L, M, T trên asr_dev/sach và asr_dev/vang (venv_tts, cần GPU: nop_rir.sh tự xin)
#   qa    phantich.rir_qa -> runs/rir_v2/qa/
#   goi   gói kho, kho_do, gan, qa, asr_dev (không gói âm thanh vang) -> $BASE/ket_qua/rir_v2_<ngày>.tar.gz + .sha256
# gan và chap dùng runs/rir_v2/kho và (nếu có) runs/rir_v2/kho_do: ưu tiên RIR đo, P_RIR_DO trong cauhinh/tang_cuong.py.
set -uo pipefail
BASE=${BASE:-$HOME/asr_tts_o_to}
TG=$BASE/code/tts_gen
PYR=$BASE/venv_rir/bin/python
PY=$BASE/venv_tts/bin/python
PIN=$BASE/hf_pinned
CT2=$BASE/ct2/PhoWhisper-large-int8
LEX=lexicon/asr_bien_the.tsv
R=runs/rir_v2
N=${SLURM_CPUS_PER_TASK:-64}
KHO=$R/kho
[ -f $R/kho_do/rir_manifest.jsonl ] || [[ " ${STEPS:-} " == *" kho_do "* ]] && KHO="$R/kho $R/kho_do"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
cd "$TG" || exit 2
mkdir -p "$R"
echo "== $(date '+%F %T') job ${SLURM_JOB_ID:-?} trên $(hostname), STEPS=${STEPS:?đặt STEPS}, $N lõi, GPU=${CUDA_VISIBLE_DEVICES:-không}"
buoc() { echo "== $(date '+%F %T') bắt đầu $1"; SECONDS=0; }
xong() { echo "== $(date '+%F %T') xong $1 sau ${SECONDS} s"; }
goi() {  # goi <tên> <thư mục...>
  local ten=$1; shift
  local out=$BASE/ket_qua/$ten.tar.gz
  mkdir -p "$BASE/ket_qua"
  tar -czf "$out" "$@" && (cd "$BASE/ket_qua" && sha256sum "$ten.tar.gz" > "$ten.tar.gz.sha256")
  echo "Gói: $out ($(du -h "$out" | cut -f1)), sha256 $(cut -c1-16 "$out.sha256")…"
}
for s in $STEPS; do
  buoc "$s"
  case $s in
    thu)
      "$PYR" -m buoc.rir_kho --out $R/thu/kho --khoang-moi-loai 2 --workers 8 || exit 3
      "$PYR" -m phantich.phieu_nghe_rir --kho $R/thu/kho --out $R/thu/nghe || exit 3
      goi "rir_v2_thu_$(date +%Y%m%d_%H%M)" $R/thu ;;
    kho) "$PYR" -m buoc.rir_kho --out $R/kho --workers "$N" || exit 3 ;;
    kho_do) "$PYR" -m buoc.rir_kho_do dung --nguon "$BASE/rir_do" --out $R/kho_do || exit 3 ;;
    so) "$PYR" -m phantich.so_kho_rir --mo-phong $R/kho --do $R/kho_do --out $R/kho/so_sanh.json || exit 3 ;;
    nghe) "$PYR" -m phantich.phieu_nghe_rir --kho $R/kho --out $R/nghe || exit 3 ;;
    # shellcheck disable=SC2086
    gan) "$PYR" -m buoc.rir_gan --kho $KHO --out $R/gan || exit 3 ;;
    # shellcheck disable=SC2086
    chap) "$PYR" -m buoc.rir_chap --gan $R/gan --kho $KHO --out $R/aug_v1/_reverb --workers "$N" \
            --asr-dev 500 --asr-out $R/asr_dev || exit 3 ;;
    asr)
      nvidia-smi --query-gpu=name,memory.total --format=csv || { echo "*** bước asr cần GPU ***"; exit 3; }
      LD=$(ls -d "$BASE"/venv_tts/lib/python3*/site-packages/nvidia/*/lib | paste -sd:)
      for d in sach vang; do
        "$PY" -m buoc.asr_whisper $R/asr_dev/$d --model "$PIN/PhoWhisper-medium" --batch 16 --lexicon $LEX || exit 3
        "$PY" -m buoc.asr_whisper $R/asr_dev/$d --model "$PIN/PhoWhisper-small" --batch 16 --lexicon $LEX || exit 3
        /usr/bin/env LD_LIBRARY_PATH="$LD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$PY" -m buoc.asr_whisper $R/asr_dev/$d \
          --model vinai/PhoWhisper-large --backend ct2 --ct2-dir "$CT2" --lexicon $LEX || exit 3
      done ;;
    qa) "$PYR" -m phantich.rir_qa --goc $R || exit 3 ;;
    # gói những gì đã có (gọi được ngay sau "kho kho_do so nghe gan" để người dùng xem trước khi chập)
    goi) ds=$(ls -d $R/kho $R/kho_do $R/gan $R/nghe $R/qa $R/asr_dev/*/*.jsonl $R/asr_dev/*/*.csv \
                 $R/aug_v1/_reverb/manifest.jsonl 2>/dev/null)
         # shellcheck disable=SC2086
         goi "rir_v2_$(date +%Y%m%d_%H%M)" $ds ;;
    *) echo "Bước lạ: $s"; exit 2 ;;
  esac
  xong "$s"
done
echo "== $(date '+%F %T') hết STEPS"
