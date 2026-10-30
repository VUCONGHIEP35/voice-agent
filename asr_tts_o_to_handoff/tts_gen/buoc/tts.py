# -*- coding: utf-8 -*-
"""Sinh âm thanh thí điểm bằng VieNeu v3 Turbo (giai đoạn 0–1 của kế hoạch sinh TTS).

Chạy (từ tts_gen/):
  .venv/Scripts/python -m buoc.tts --smoke   # giai đoạn 0: 6 câu (mỗi vùng: câu ít âm tiết nhất + nhiều nhất)
  .venv/Scripts/python -m buoc.tts           # giai đoạn 1: toàn bộ pilot/pilot_100.jsonl
Ghi runs/<tên>/: audio48/*.flac (48 kHz, nguyên bản), audio16/*.flac (16 kHz cho ASR), manifest.jsonl, run_config.json.
Chạy lại thì bỏ qua câu đã có đủ tệp và dòng manifest (theo sample_id + giọng).
Chỉ đo, không chỉnh âm thanh: không co giãn tốc độ, không cắt im lặng, không thêm nhiễu (thuộc các bước sau).
Tự kiểm (thuvien/kiem_am_thanh.py): câu cắt đầu / nói lan man / đọc thiếu được sinh lại với seed mới (attempt + 1), tối đa
--max-retry lần; chỉ ghi âm thanh của lần cuối, manifest ghi tts_check và retries. Không chọn bản theo CER của ASR.
Dòng đầu vào có sẵn trường "voice" thì giữ giọng đó (dùng để sinh lại đúng giọng cũ).
Thư mục tạm và cache (HF_HOME, TEMP/TMP, TORCH_HOME, CUDA_CACHE_PATH, PIP_CACHE_DIR) đặt trong tts_gen/.cache (thuvien/moi_truong.py).

Đánh giá 1.000 câu (docs/ke_hoach_sinh_1000_cau.md, việc T2):
  - Chữ đưa vào TTS là tts_text nếu có, không thì text_spoken; vieneu_text tính từ chữ thật sự đọc, ghi tts_input.
  - Manifest có thêm tts_text, pron_variant, loan_arm, eval_idx, shard, voice_fallback_from, doi_gioi, giong_khop_tieu_vung.
  - EXCLUDED_VOICES (Minh Triết) bị loại khỏi danh sách giọng; đầu vào có giọng này thì dừng.
  - Mỗi lần gọi infer_batch tối đa --batch câu cùng giọng; giữa các lần gọi đọc nhiệt GPU, quá --max-gpu-temp
    (mặc định: GPU Slowdown Temp của nvidia-smi − 3 °C) thì nghỉ tới khi nhiệt giảm --cooldown °C; RAM trống dưới
    --min-free-ram-gb thì dừng (mã thoát 3) sau khi ghi run_config.json.
  - Chạy tiếp vào thư mục cũ: run_config.json được gộp (calls cộng dồn, mỗi lần chạy thêm một mục trong "lan_chay").
  - Ngắt có kiểm soát: Ctrl+C, hoặc tạo tệp <out>/STOP (khi chạy nền); script ghi run_config rồi thoát, chạy lại cùng
    lệnh để làm tiếp (tệp STOP tự xóa khi khởi động).
"""
import argparse
import collections
import hashlib
import itertools
import json
import os
import platform
import random
import subprocess
import time
import unicodedata
from thuvien.am_thanh import write_flac  # noqa: E402

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
import thuvien.moi_truong as tts_env  # noqa: E402
ENV_DIRS = tts_env.setup()  # phải chạy trước khi import torch / huggingface_hub

import numpy as np          # noqa: E402
import soxr                 # noqa: E402

import thuvien.kiem_am_thanh as tts_checks  # noqa: E402

RUN_SEED = 20261018
SR = 48_000
SR16 = 16_000
LEN_ORDER = {"Rất ngắn": 0, "Ngắn": 1, "Thường": 2, "Dài": 3}
SAMPLING = dict(temperature=0.8, top_k=25)       # mặc định của V3TurboVieNeuTTS.infer_batch
from cauhinh.giong import EXCLUDED as EXCLUDED_VOICES  # noqa: E402
EXTRA_FIELDS = ("tts_text", "pron_variant", "loan_arm", "loan_names", "eval_idx", "shard", "voice_fallback_from",
                "doi_gioi", "giong_khop_tieu_vung", "voice_sub_region")


def tts_input(j):
    """Chữ thật sự đưa vào TTS: tts_text (nhánh phiên âm từ ngoại) nếu có, không thì text_spoken."""
    return j.get("tts_text") or j["text_spoken"]


def check_excluded(rows):
    """Dừng nếu đầu vào gán giọng bị loại."""
    bad = sorted({(r["sample_id"], r["voice"]) for r in rows if r.get("voice") in EXCLUDED_VOICES})
    if bad:
        raise SystemExit(f"Đầu vào có giọng bị loại {sorted({v for _, v in bad})}: {len(bad)} câu, vd {bad[:3]}")


def _smi(args):
    try:
        return subprocess.run(["nvidia-smi"] + args, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def gpu_temp_c():
    out = _smi(["--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"]).strip().splitlines()
    try:
        return int(out[0])
    except (IndexError, ValueError):
        return None


def slowdown_temp_c(text=None):
    """'GPU Slowdown Temp' trong nvidia-smi -q -d TEMPERATURE (None nếu không đọc được)."""
    import re
    text = _smi(["-q", "-d", "TEMPERATURE"]) if text is None else text
    m = re.search(r"GPU Slowdown Temp\s*:\s*(\d+)\s*C", text)
    return int(m.group(1)) if m else None


def free_ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except Exception:  # noqa
        return None


def cool_down(limit, drop, poll=10.0, read=gpu_temp_c, sleep=time.sleep, log=print):
    """Nhiệt > limit thì nghỉ tới khi <= limit - drop. Trả số giây đã nghỉ (0 nếu không phải nghỉ)."""
    t = read()
    if t is None or t <= limit:
        return 0.0
    waited = 0.0
    log(f"GPU {t} °C > {limit} °C: nghỉ tới khi <= {limit - drop} °C", flush=True)
    while t is not None and t > limit - drop:
        sleep(poll)
        waited += poll
        t = read()
    log(f"Hết nghỉ sau {waited:.0f} s ({t} °C)", flush=True)
    return waited


def merge_run_config(old, new):
    """Gộp run_config cũ (lượt chạy trước, cùng thư mục) với lượt mới: calls cộng dồn, tổng tính lại trên mọi calls,
    thông tin từng lần chạy giữ trong 'lan_chay'. Trường mô tả cấu hình lấy theo lượt mới."""
    runs = list((old or {}).get("lan_chay") or [])
    if old and not runs:   # run_config kiểu cũ: một lần chạy
        runs = [{k: old.get(k) for k in ("load_s", "n_rows", "vram_peak_alloc_gb", "vram_peak_reserved_gb",
                                        "gen_wall_s", "gen_audio_s", "cooldown_count", "cooldown_s", "dung_vi")}]
    runs.append({k: new.get(k) for k in ("bat_dau", "load_s", "n_rows", "vram_peak_alloc_gb", "vram_peak_reserved_gb",
                                         "gen_wall_s", "gen_audio_s", "cooldown_count", "cooldown_s", "dung_vi")})
    calls = list((old or {}).get("calls") or []) + list(new.get("calls") or [])
    out = dict(old or {})          # giữ khóa chỉ có ở config cũ (vd colab_steps do notebook ghi)
    out.update(new)
    out.update(calls=calls, lan_chay=runs)
    wall = sum(c["wall_s"] for c in calls)
    audio = sum(c["audio_s"] for c in calls)
    out.update(gen_wall_s=round(wall, 1), gen_audio_s=round(audio, 1),
               rtf_overall=round(wall / audio, 4) if audio else None,
               load_s_total=round(sum(r.get("load_s") or 0 for r in runs), 1),
               cooldown_count=sum(r.get("cooldown_count") or 0 for r in runs),
               cooldown_s=round(sum(r.get("cooldown_s") or 0 for r in runs), 1))
    return out


def slug(name):
    s = unicodedata.normalize("NFD", name.replace("Đ", "D").replace("đ", "d"))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")


def h32(*parts):
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def assign_voices(rows, voices):
    """Trong mỗi vùng: xếp câu theo (độ dài, case, băm), chia vòng tròn cho các giọng của vùng, xen kẽ nữ/nam.
    voices: {tên: meta có 'region', 'gender'}. Vùng không có giọng thì dừng, không dồn sang vùng khác.
    Dòng có sẵn 'voice' (giọng phải có trong voices) giữ nguyên, không tham gia chia vòng."""
    out = []
    for r in rows:
        if r.get("voice"):
            if r["voice"] not in voices:
                raise SystemExit(f"{r['sample_id']}: giọng {r['voice']} không có hoặc không ghi vùng")
            out.append(dict(r))
    rows = [r for r in rows if not r.get("voice")]
    for region in sorted({r["speaker_region"] for r in rows}):
        fem = sorted(n for n, m in voices.items() if m.get("region") == region and m.get("gender") == "female")
        mal = sorted(n for n, m in voices.items() if m.get("region") == region and m.get("gender") == "male")
        ring = [x for pair in itertools.zip_longest(fem, mal) for x in pair if x]
        if not ring:
            raise SystemExit(f"Vùng {region} không có giọng sẵn có nào")
        rs = sorted((r for r in rows if r["speaker_region"] == region),
                    key=lambda r: (LEN_ORDER[r["length_class"]], r["case_id"], h32(RUN_SEED, r["sample_id"])))
        for i, r in enumerate(rs):
            out.append(dict(r, voice=ring[i % len(ring)]))
    return out


def measure(w):
    """Số đo kỹ thuật trên bản 48 kHz (chỉ đo): thời lượng, phần có tiếng (năng lượng khung 25 ms > đỉnh − 35 dB),
    im lặng đầu/cuối, biên độ đỉnh."""
    w16 = soxr.resample(w, SR, SR16) if len(w) else w
    dur = len(w) / SR
    if len(w16) < 400:
        return dict(duration_s=round(dur, 3), speech_s=0.0, lead_sil_s=None, trail_sil_s=None, peak=float(np.max(np.abs(w))) if len(w) else 0.0)
    n = 1 + (len(w16) - 400) // 160
    idx = np.arange(400)[None, :] + 160 * np.arange(n)[:, None]
    db = 10 * np.log10((w16[idx].astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    voiced = db > max(db.max() - 35.0, -70.0)
    vi = np.where(voiced)[0]
    return dict(duration_s=round(dur, 3), speech_s=round(voiced.sum() * 0.01, 3),
                lead_sil_s=round(vi[0] * 0.01, 3) if len(vi) else None,
                trail_sil_s=round(max(0.0, dur - (vi[-1] * 0.01 + 0.025)), 3) if len(vi) else None,
                peak=round(float(np.max(np.abs(w))), 4))


def hf_revisions():
    """Commit của các repo Hugging Face đã tải (gồm mã tùy biến trust_remote_code của MOSS-Audio-Tokenizer)."""
    hub = os.path.join(os.environ["HF_HOME"], "hub")
    out = {}
    for d in sorted(os.listdir(hub)) if os.path.isdir(hub) else []:
        snaps = os.path.join(hub, d, "snapshots")
        if d.startswith("models--") and os.path.isdir(snaps):
            out[d[len("models--"):].replace("--", "/")] = sorted(os.listdir(snaps))
    return out


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=HERE, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=os.path.join(HERE, "pilot", "pilot_100.jsonl"))
    ap.add_argument("--smoke", action="store_true", help="giai đoạn 0: mỗi vùng 2 câu (ít và nhiều âm tiết nhất)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--batch", type=int, default=8, help="max_batch_size cho GPU (VRAM 4 GB: bắt đầu nhỏ)")
    ap.add_argument("--max-retry", type=int, default=2, help="số lần sinh lại tối đa cho câu không qua tts_checks")
    ap.add_argument("--max-gpu-temp", type=int, default=None,
                    help="°C; mặc định = GPU Slowdown Temp (nvidia-smi -q -d TEMPERATURE) − 3")
    ap.add_argument("--cooldown", type=int, default=5, help="quá ngưỡng thì nghỉ tới khi nhiệt giảm chừng này °C")
    ap.add_argument("--min-free-ram-gb", type=float, default=0.5, help="RAM trống thấp hơn thì dừng (mã thoát 3)")
    ap.add_argument("--dtype", default="auto", choices=["auto", "bfloat16", "float16", "float32"],
                    help="kiểu số PyTorch; auto = bf16 nếu GPU hỗ trợ, không thì fp16 (T4)")
    ap.add_argument("--backbone-repo", default="pnnbao-ump/VieNeu-TTS-v3-Turbo",
                    help="repo HF hoặc thư mục snapshot đã ghim revision")
    ap.add_argument("--moss-tokenizer", default="OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano",
                    help="repo HF hoặc thư mục snapshot đã ghim revision")
    ap.add_argument("--no-ref-codes", action="store_true",
                    help="cấu hình B của luutru/test_voice_config.py: use_ref_codes=False (chỉ embedding người nói)")
    ap.add_argument("--no-ref-codes-voice", action="append", default=[], metavar="TÊN_GIỌNG",
                    help="tắt ref codes chỉ cho giọng này (lặp lại được), vd Thái Sơn: cắt đầu ít hơn ở cấu hình B")
    a = ap.parse_args()
    slow = slowdown_temp_c()
    if a.max_gpu_temp is None:
        a.max_gpu_temp = (slow - 3) if slow else 83
    print(f"Ngưỡng nhiệt: {a.max_gpu_temp} °C (GPU Slowdown Temp {slow} °C), nghỉ tới khi giảm {a.cooldown} °C; "
          f"dừng nếu RAM trống < {a.min_free_ram_gb} GB", flush=True)
    out = a.out or os.path.join(HERE, "runs", "smoke" if a.smoke else "pilot100")
    old_cfg_path = os.path.join(out, "run_config.json")
    old_cfg = None
    if os.path.exists(old_cfg_path):
        with open(old_cfg_path, encoding="utf-8") as f:
            old_cfg = json.load(f)
        if "tts_checks" not in old_cfg:
            raise SystemExit(f"{out} là lượt chạy trước khi có tts_checks; không ghi thêm vào đó, dùng --out khác")

    with open(a.input, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    check_excluded(rows)
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    if a.smoke:
        pick = []
        for region in ("Bắc", "Trung", "Nam"):
            rs = sorted((r for r in rows if r["speaker_region"] == region), key=lambda r: (r["n_syllables"], r["sample_id"]))
            pick += [rs[0], rs[-1]]
        rows = pick

    import torch
    from vieneu import Vieneu
    from vieneu_utils.phonemize_text import normalize_to_chunks_v3_with_gaps
    import vieneu

    os.makedirs(os.path.join(out, "audio48"), exist_ok=True)
    os.makedirs(os.path.join(out, "audio16"), exist_ok=True)
    man_path = os.path.join(out, "manifest.jsonl")
    done = set()
    if os.path.exists(man_path):
        with open(man_path, encoding="utf-8") as f:
            for line in f:
                m = json.loads(line)
                if os.path.exists(os.path.join(out, m["audio48"])) and os.path.exists(os.path.join(out, m["audio16"])):
                    done.add((m["sample_id"], m["voice"]))

    t0 = time.perf_counter()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    tts = Vieneu("v3turbo", max_batch_size=a.batch, dtype=a.dtype, backbone_repo=a.backbone_repo,
                 moss_tokenizer=a.moss_tokenizer)
    load_s = time.perf_counter() - t0
    # Vùng chỉ có trong tệp voices_v3_turbo.json (V3TurboVieNeuTTS không nạp trường 'region' vào _preset_voices).
    # Giọng nạp thêm từ repo mô hình mà không ghi vùng thì không dùng.
    with open(os.path.join(os.path.dirname(vieneu.__file__), "assets", "voices_v3_turbo.json"), encoding="utf-8") as f:
        region_of = {n: v.get("region") for n, v in json.load(f).get("presets", {}).items()}
    vmeta = {}
    for _, name in tts.list_preset_voices():
        m = tts.get_preset_voice(name)
        if name in EXCLUDED_VOICES:
            print(f"Loại giọng {name}: {EXCLUDED_VOICES[name]}")
        elif region_of.get(name):
            vmeta[name] = dict(region=region_of[name], gender=m.get("gender"), style=m.get("style"))
        else:
            print(f"Bỏ qua giọng không ghi vùng: {name}")
    print("Giọng theo vùng:", dict(collections.Counter(v["region"] for v in vmeta.values())))
    jobs = assign_voices(rows, vmeta)

    from importlib.metadata import version as pkg_version
    cfg = dict(vieneu=pkg_version("vieneu"), transformers=pkg_version("transformers"), torch=torch.__version__,
               cuda=torch.version.cuda, device=str(tts.engine.device) if hasattr(tts.engine, "device") else None,
               dtype=str(getattr(tts.engine, "dtype", None)), backend=tts.backend, watermark=tts.watermarker is not None,
               backbone_repo=tts.backbone_repo, max_batch_size=a.batch, sampling=SAMPLING, run_seed=RUN_SEED,
               babble_retries=tts.babble_retries, max_retry=a.max_retry, excluded_voices=EXCLUDED_VOICES,
               max_gpu_temp=a.max_gpu_temp, gpu_slowdown_temp=slow, cooldown_drop=a.cooldown,
               min_free_ram_gb=a.min_free_ram_gb, env_dirs=ENV_DIRS, bat_dau=started, use_ref_codes=not a.no_ref_codes,
               no_ref_codes_voices=sorted(a.no_ref_codes_voice), dtype_requested=a.dtype, moss_tokenizer=a.moss_tokenizer,
               tts_checks=dict(head_ms=tts_checks.HEAD_MS, head_db_max=tts_checks.HEAD_DB_MAX,
                               sec_per_syl_max=tts_checks.SEC_PER_SYL_MAX, sec_per_syl_min=tts_checks.SEC_PER_SYL_MIN),
               git_commit=git_commit(), hf_revisions=hf_revisions(),
               python=platform.python_version(),
               gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, load_s=round(load_s, 1),
               input=os.path.relpath(a.input, HERE) if os.path.splitdrive(os.path.abspath(a.input))[0].lower()
               == os.path.splitdrive(HERE)[0].lower() else os.path.abspath(a.input), n_rows=len(rows))
    print(json.dumps(cfg, ensure_ascii=False))

    by_voice = collections.defaultdict(list)
    for j in jobs:
        by_voice[j["voice"]].append(j)
    calls = []
    cool = dict(n=0, s=0.0)
    stop_reason = None
    stop_file = os.path.join(out, "STOP")
    if os.path.exists(stop_file):
        os.remove(stop_file)
        print("Đã xóa tệp STOP của lần ngắt trước", flush=True)

    def guard():
        """Giữa các lần gọi: nghỉ nếu GPU nóng; dừng nếu RAM trống quá thấp."""
        w = cool_down(a.max_gpu_temp, a.cooldown)
        if w:
            cool["n"] += 1
            cool["s"] += w
        ram = free_ram_gb()
        if ram is not None and ram < a.min_free_ram_gb:
            raise MemoryError(f"RAM trống {ram:.2f} GB < {a.min_free_ram_gb} GB")
        if os.path.exists(stop_file):           # ngắt có kiểm soát, như Ctrl+C (dùng khi chạy nền)
            raise KeyboardInterrupt

    try:
        with open(man_path, "a", encoding="utf-8", newline="\n") as man:
            for voice, items in sorted(by_voice.items()):
                todo = [j for j in items if (j["sample_id"], voice) not in done]
                history = {j["sample_id"]: [] for j in todo}
                vm = vmeta[voice]
                uref = not (a.no_ref_codes or voice in a.no_ref_codes_voice)
                for attempt in range(a.max_retry + 1):
                    if not todo:
                        break
                    retry = []
                    for ci in range(0, len(todo), a.batch):     # mỗi lần gọi tối đa --batch câu
                        group = todo[ci:ci + a.batch]
                        guard()
                        seed = h32(RUN_SEED, voice, attempt, ci // a.batch)
                        torch.manual_seed(seed)
                        random.seed(seed)
                        np.random.seed(seed)
                        t1 = time.perf_counter()
                        wavs = tts.infer_batch([tts_input(j) for j in group], voice=voice, apply_watermark=False,
                                               use_ref_codes=uref, batch_size=a.batch, **SAMPLING)
                        if torch.cuda.is_available():
                            torch.cuda.synchronize()
                        dt = time.perf_counter() - t1
                        audio_s = sum(len(w) for w in wavs) / SR
                        calls.append(dict(voice=voice, attempt=attempt, n=len(group), wall_s=round(dt, 2),
                                          audio_s=round(audio_s, 2), rtf=round(dt / audio_s, 4) if audio_s else None))
                        n_retry = 0
                        for j, w in zip(group, wavs):
                            w = np.asarray(w, dtype=np.float32)
                            q = measure(w)
                            w16 = soxr.resample(w, SR, SR16) if len(w) else w
                            why, hd = tts_checks.check(w16, j["n_syllables"], q["speech_s"], SR16)
                            if why and attempt < a.max_retry:      # còn lượt: sinh lại với seed mới, chưa ghi tệp
                                history[j["sample_id"]].append(dict(attempt=attempt, seed=seed, ly_do=why, head_db=hd))
                                retry.append(j)
                                n_retry += 1
                                continue
                            utt = f"{j['sample_id']}__{slug(voice)}__a{attempt}"
                            p48, p16 = os.path.join("audio48", utt + ".flac"), os.path.join("audio16", utt + ".flac")
                            write_flac(os.path.join(out, p48), w, SR)
                            write_flac(os.path.join(out, p16), w16, SR16)
                            chunks, _ = normalize_to_chunks_v3_with_gaps(tts_input(j), max_chars=256)
                            rec = dict(
                                utt_id=utt, sample_id=j["sample_id"], pilot_idx=j.get("pilot_idx"), case_id=j["case_id"],
                                intent_id=j["intent_id"], text_raw=j["text_raw"], text_spoken=j["text_spoken"],
                                tts_input=tts_input(j), vieneu_text=" ".join(chunks), speaker_region=j["speaker_region"],
                                sub_region=j["sub_region"], residence=j["residence"], length_class=j["length_class"],
                                n_syllables=j["n_syllables"], voice=voice, voice_source="preset",
                                voice_region=vm.get("region"), voice_gender=vm.get("gender"), voice_style=vm.get("style"),
                                seed=seed, attempt=attempt, **q,
                                rate_syl_per_s=round(j["n_syllables"] / q["speech_s"], 2) if q["speech_s"] else None,
                                clipped=bool(q["peak"] >= 0.999), head_db=hd,
                                tts_check="dat" if not why else "loi:" + "+".join(why), retries=history[j["sample_id"]],
                                review_status=j["review_status"],
                                loan_unverified=any(x.startswith("cách đọc chưa xác minh") for x in j["review_reasons"]),
                                app_group=j.get("app_group", ""), audio48=p48.replace(os.sep, "/"),
                                audio16=p16.replace(os.sep, "/"), use_ref_codes=uref)
                            rec.update({k: j.get(k) for k in EXTRA_FIELDS if k in j})
                            man.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            man.flush()
                        print(f"{voice:14s} a{attempt} {len(group):3d} câu | {dt:6.1f} s cho {audio_s:6.1f} s âm thanh | "
                              f"RTF {dt / max(audio_s, 1e-9):.3f} | sinh lại {n_retry}", flush=True)
                    todo = retry
    except KeyboardInterrupt:
        stop_reason = "ngat_tay"
        print("Bị ngắt (Ctrl+C): ghi run_config rồi thoát; chạy lại cùng lệnh để làm tiếp.", flush=True)
    except MemoryError as e:
        stop_reason = "thieu_ram"
        print(f"DỪNG: {e}. Đóng bớt ứng dụng rồi chạy lại cùng lệnh.", flush=True)
    finally:
        if torch.cuda.is_available():
            cfg["vram_peak_alloc_gb"] = round(torch.cuda.max_memory_allocated() / 2 ** 30, 3)
            cfg["vram_peak_reserved_gb"] = round(torch.cuda.max_memory_reserved() / 2 ** 30, 3)
        cfg.update(calls=calls, gen_wall_s=round(sum(c["wall_s"] for c in calls), 1),
                   gen_audio_s=round(sum(c["audio_s"] for c in calls), 1), cooldown_count=cool["n"],
                   cooldown_s=round(cool["s"], 1), dung_vi=stop_reason)
        cfg = merge_run_config(old_cfg, cfg)
        tmp = os.path.join(out, "run_config.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fo:
            json.dump(cfg, fo, ensure_ascii=False, indent=1)
        os.replace(tmp, os.path.join(out, "run_config.json"))
    print(f"Xong lượt này: nạp mô hình {load_s:.1f} s | gộp mọi lượt: sinh {cfg['gen_wall_s']} s cho {cfg['gen_audio_s']} s "
          f"âm thanh | RTF {cfg['rtf_overall']} | VRAM đỉnh {cfg.get('vram_peak_alloc_gb')} GB "
          f"(reserved {cfg.get('vram_peak_reserved_gb')}) | nghỉ vì nhiệt {cfg['cooldown_count']} lần, {cfg['cooldown_s']} s")
    if stop_reason == "thieu_ram":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
