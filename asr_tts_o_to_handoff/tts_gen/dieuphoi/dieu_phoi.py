# -*- coding: utf-8 -*-
"""Bộ điều phối chạy SONG SONG trong MỘT job Slurm (1 A100 80 GB + nhiều CPU): TTS + kiểm + ASR + chấm cho nhiều phần.

Chạy (trong job, từ tts_gen/; xem server/chay_10k.sbatch):
  venv_tts/bin/python -m dieuphoi.dieu_phoi --shards smoke p01 p02 ... [--gpu-slots 4] [--tts-slots 1] [--cpu-slots 3]
  venv_tts/bin/python -m dieuphoi.dieu_phoi --thu-lo        # so cỡ lô ASR (lô 2 với lô 16) trên 200 câu phần B rồi thoát
Mỗi phần S: đầu vào full10k/shard_S.jsonl (smoke: runs/eval1000_A/logs/input_smoke24.jsonl), thư mục runs/full10k_S.
Phần đặc biệt "wake" (chạy SAU p01..p10): bước tts = buoc/ghep_loi_goi.py dau + ghep -> runs/full10k_wake; bỏ kiểm/đổi giọng;
ASR và chấm như phần thường.
Đồ thị tác vụ của một phần:
  tts -> kiem1 -> doi_giong -> kiem2 -> {M, L, T (GPU); Z (CPU)} ; M -> c3 (asr_diagnose đọc c0 từ kết quả M)
  {M, L, c3, T, Z} -> cham (gate_union luật v2 -> gate_hop, luật v1 -> gate_hop_v1) -> goi (tar, bỏ audio16)
Lập lịch: hàng đợi ưu tiên theo (thứ tự phần, thứ tự bước); khe tài nguyên riêng: TTS (--tts-slots, mặc định 1, để TTS
phần sau chạy chồng lên ASR phần trước), GPU-ASR (--gpu-slots), CPU (--cpu-slots, cho Z). Mỗi tác vụ là một tiến trình
con, log riêng ở runs/full10k_S/logs/<tác vụ>.log; thời gian ghi qua dieuphoi/ghi_buoc.py (run_config + thoi_gian_asr).
Bỏ qua tác vụ đã có kết quả (asr_xong / diag_xong / tệp chấm / tệp gói), run_pilot tự chạy tiếp -> nộp lại job là chạy tiếp.
Tác vụ lỗi: dừng phần đó (các tác vụ sau của phần bị bỏ), phần khác chạy tiếp; tiến trình bị giết (rc < 0) thử lại 1 lần
với ít khe GPU hơn. Theo dõi nvidia-smi mỗi 5 s; VRAM > 70 GB thì giảm khe GPU (tối thiểu 2).
Điểm dừng chất lượng: sau khi chấm một phần, tỷ lệ dat (luật v1) của vùng nào dưới ngưỡng NGUONG_DAT (mốc eval1000
cận dưới Wilson − 0,05) thì ghi tệp DUNG_CHAT_LUONG và không bắt đầu phần mới (các tác vụ đang chạy được làm xong).
"""
import argparse
import collections
import heapq
import json
import os
import shutil
import subprocess
import sys
import threading
import time

from cauhinh.duong_dan import GOC as TG  # noqa: E402
BASE = os.environ.get("BASE", os.path.expanduser("~/asr_tts_o_to"))
PY = os.path.join(BASE, "venv_tts", "bin", "python")
PYZ = os.path.join(BASE, "venv_zip", "bin", "python")
PIN = os.path.join(BASE, "hf_pinned")
CT2_DIR = os.path.join(BASE, "ct2", "PhoWhisper-large-int8")
LEX = "lexicon/asr_bien_the.tsv"
TTS_ARGS = ["--batch", "16", "--dtype", "bfloat16", "--backbone-repo", f"{PIN}/vieneu", "--moss-tokenizer", f"{PIN}/moss",
            "--no-ref-codes-voice", "Thái Sơn"]
# Mốc từ eval1000 A+B (luật v1, L M c3 Z; reports/eval1000_AB): cận dưới Wilson − 0,05. Văn bản v3.1 đã bỏ từ đệm nên
# tỷ lệ dự kiến không thấp hơn; dưới mốc này là có vấn đề hệ thống.
from cauhinh.nguong import NGUONG_DAT  # noqa: E402
STAGES = ["tts", "kiem1", "doi_giong", "kiem2", "M", "L", "T", "Z", "c3", "cham", "goi"]
KIND = {"tts": "tts", "doi_giong": "tts", "kiem1": "cpu_nhe", "kiem2": "cpu_nhe", "M": "gpu", "L": "gpu", "T": "gpu",
        "c3": "gpu", "Z": "cpu", "cham": "cpu_nhe", "goi": "cpu_nhe"}
DEPS = {"tts": [], "kiem1": ["tts"], "doi_giong": ["kiem1"], "kiem2": ["doi_giong"], "M": ["kiem2"], "L": ["kiem2"],
        "T": ["kiem2"], "Z": ["kiem2"], "c3": ["M"], "cham": ["M", "L", "T", "Z", "c3"], "goi": ["cham"]}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ct2_ld():
    import glob
    import site
    libs = sorted(glob.glob(os.path.join(site.getsitepackages()[0], "nvidia", "*", "lib")))
    return ":".join(libs + [x for x in os.environ.get("LD_LIBRARY_PATH", "").split(":") if x])


class Shard:
    def __init__(self, name, lo):
        self.name = name
        self.input = "runs/eval1000_A/logs/input_smoke24.jsonl" if name == "smoke" else f"full10k/shard_{name}.jsonl"
        self.run = f"runs/full10k_{name}"
        self.lo = lo

    def done(self, st):
        """Tác vụ đã có kết quả từ lần chạy trước thì bỏ qua."""
        x = lambda *a: subprocess.run([PY, "-m", "dieuphoi.ghi_buoc", *a], cwd=TG).returncode == 0
        if st == "M":
            return x("asr_xong", self.run, "PhoWhisper-medium")
        if st == "L":
            return x("asr_xong", self.run, "PhoWhisper-large-ct2-int8")
        if st == "T":
            return x("asr_xong", self.run, "PhoWhisper-small")
        if st == "Z":
            return x("asr_xong", self.run, "Zipformer-30M-int8-beam4")
        if st == "c3":
            return x("diag_xong", self.run)
        if st == "cham":
            return all(os.path.exists(os.path.join(TG, self.run, f)) for f in ("gate_hop.csv", "gate_hop_v1.csv"))
        if st == "goi":
            return os.path.exists(os.path.join(BASE, "ket_qua", f"ket_qua_full10k_{self.name}.tar.gz"))
        if self.name == "wake":                        # phần ghép lời gọi: không có kiểm/đổi giọng kiểu TTS thường
            if st in ("kiem1", "doi_giong", "kiem2"):
                return True
            if st == "tts":
                return os.path.exists(os.path.join(TG, self.run, "manifest.jsonl"))
        return False                                   # tts/kiem/doi_giong: tự chạy tiếp, chạy lại rẻ

    def cmd(self, st):
        r, i = self.run, self.input
        if st == "tts" and self.name == "wake":         # sinh đoạn lời gọi rồi ghép vào câu M1 của p01..p10
            ta = " ".join(f'"{x}"' if " " in x else x for x in TTS_ARGS)
            return ["/bin/bash", "-c", f"{PY} -m buoc.ghep_loi_goi dau --tts-args '{ta}' && "
                                       f"{PY} -m buoc.ghep_loi_goi ghep --ctc {PIN}/wav2vec2"]
        if st == "tts":
            return [PY, "-m", "buoc.tts", "--input", i, "--out", r, *TTS_ARGS]
        if st in ("kiem1", "kiem2"):
            return [PY, "-m", "buoc.kiem_luot", r, i]
        if st == "doi_giong":
            if os.path.exists(os.path.join(TG, r, "fallback_input.jsonl")) and os.path.getsize(os.path.join(TG, r, "fallback_input.jsonl")):
                return [PY, "-m", "buoc.tts", "--input", f"{r}/fallback_input.jsonl", "--out", r, *TTS_ARGS]
            return [PY, "-m", "buoc.doi_giong", r, "--run-tts", "--batch", "16", "--pilot-args",
                    " ".join(f'"{x}"' if " " in x else x for x in TTS_ARGS[2:])]
        if st == "M":
            return [PY, "-m", "buoc.asr_whisper", r, "--model", f"{PIN}/PhoWhisper-medium", "--batch", str(self.lo), "--lexicon", LEX]
        if st == "T":
            return [PY, "-m", "buoc.asr_whisper", r, "--model", f"{PIN}/PhoWhisper-small", "--batch", str(self.lo), "--lexicon", LEX]
        if st == "L":
            return ["/usr/bin/env", f"LD_LIBRARY_PATH={ct2_ld()}", PY, "-m", "buoc.asr_whisper", r, "--model", "vinai/PhoWhisper-large",
                    "--backend", "ct2", "--ct2-dir", CT2_DIR, "--lexicon", LEX]
        if st == "c3":
            return [PY, "-m", "buoc.asr_chan_doan", r, "--whisper", f"{PIN}/PhoWhisper-medium", "--ctc", f"{PIN}/wav2vec2", "--skip", "c1", "c2"]
        if st == "Z":
            return [PYZ, "-m", "buoc.asr_zipformer", r, "--decoding", "modified_beam_search", "--beam", "4", "--threads", "8"]
        if st == "cham":
            return ["/bin/bash", "-c",
                    f"{PY} -m buoc.cham {r} --lexicon {LEX} --configs L M c3 Z --luat v2 --out-name gate_hop && "
                    f"{PY} -m buoc.cham {r} --lexicon {LEX} --configs L M c3 Z --luat v1 --out-name gate_hop_v1"]
        if st == "goi":
            pkg = os.path.join(BASE, "ket_qua", f"ket_qua_full10k_{self.name}.tar.gz")
            return ["/bin/bash", "-c",
                    f"tar -czf {pkg}.tmp --exclude='*/audio16/*' -C {TG} {r} && mv {pkg}.tmp {pkg} && "
                    f"cd {BASE}/ket_qua && sha256sum {os.path.basename(pkg)} > {os.path.basename(pkg)}.sha256"]
        raise ValueError(st)

    def need_ok(self, st):
        """Bước ASR rc=0 mà thiếu tệp kết quả là lỗi (bài học lần smoke 24/10: 'env' giả của uv)."""
        return self.done(st) if st in ("M", "L", "T", "Z", "c3", "cham") else True


def dat_rates(run):
    p = os.path.join(TG, run, "gate_hop_v1_tom_tat.json")
    if not os.path.exists(p):
        return {}
    s = json.load(open(p, encoding="utf-8"))
    out = {}
    for reg, c in s["theo_vung"].items():
        n = sum(c.values())
        out[reg] = round(c.get("dat", 0) / n, 3) if n else None
    return out


class GpuWatch(threading.Thread):
    def __init__(self, path):
        super().__init__(daemon=True)
        self.path, self.peak_mb, self.last_mb, self.stop = path, 0, 0, False

    def run(self):
        with open(self.path, "a", encoding="utf-8") as f:
            while not self.stop:
                r = subprocess.run(["nvidia-smi", "--query-gpu=timestamp,temperature.gpu,utilization.gpu,memory.used",
                                    "--format=csv,noheader,nounits"], capture_output=True, text=True)
                line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
                if line:
                    f.write(line + "\n")
                    f.flush()
                    try:
                        self.last_mb = int(line.split(",")[3])
                        self.peak_mb = max(self.peak_mb, self.last_mb)
                    except (IndexError, ValueError):
                        pass
                time.sleep(5)


def run_all(shards, gpu_slots, tts_slots, cpu_slots, log):
    slots = {"gpu": gpu_slots, "tts": tts_slots, "cpu": cpu_slots, "cpu_nhe": 8}
    busy = collections.Counter()
    state = {}            # (shard, stage) -> pending|running|ok|fail|skip
    order = {s.name: i for i, s in enumerate(shards)}
    procs = {}            # (shard, stage) -> (Popen, t0, logf, retried)
    retried = set()
    stop_new = False
    heap = []
    for s in shards:
        for k, st in enumerate(STAGES):
            state[(s.name, st)] = "pending"
            heapq.heappush(heap, (order[s.name], k, s.name, st))
    by = {s.name: s for s in shards}
    watch = GpuWatch(os.path.join(TG, "runs", "full10k_gpu_log.csv"))
    watch.start()
    timing = collections.defaultdict(dict)

    def ready(sn, st):
        return all(state[(sn, d)] == "ok" for d in DEPS[st])

    def blocked(sn, st):
        return any(state[(sn, d)] in ("fail", "skip") for d in DEPS[st])

    while True:
        # thu tác vụ đã xong
        for key, (p, t0, lf, _) in list(procs.items()):
            rc = p.poll()
            if rc is None:
                continue
            lf.close()
            sn, st = key
            dt = round(time.time() - t0, 1)
            busy[KIND[st]] -= 1
            del procs[key]
            s = by[sn]
            subprocess.run([PY, "-m", "dieuphoi.ghi_buoc", "ghi", s.run, f"song_song_{st}", str(dt), str(rc)], cwd=TG)
            timing[sn][st] = dt
            if rc == 0 and s.need_ok(st):
                state[key] = "ok"
                log(f"[{sn}/{st}] xong {dt} s")
                if st == "cham":
                    rates = dat_rates(s.run)
                    low = {r: v for r, v in rates.items() if v is not None and v < NGUONG_DAT.get(r, 0)}
                    log(f"[{sn}] tỷ lệ dat (luật v1) theo vùng: {rates}")
                    if low and sn != "smoke":
                        stop_new = True
                        open(os.path.join(TG, "runs", "DUNG_CHAT_LUONG"), "a").write(f"{now()} {sn} {low}\n")
                        log(f"*** ĐIỂM DỪNG chất lượng ở {sn}: {low} < {NGUONG_DAT}; không mở phần mới ***")
            elif rc < 0 and key not in retried:
                retried.add(key)
                slots["gpu"] = max(2, slots["gpu"] - 1)
                state[key] = "pending"
                heapq.heappush(heap, (order[sn], STAGES.index(st), sn, st))
                log(f"[{sn}/{st}] bị giết (rc {rc}) -> thử lại 1 lần, khe GPU còn {slots['gpu']}")
            else:
                state[key] = "fail"
                log(f"*** [{sn}/{st}] LỖI rc={rc} (xem {s.run}/logs/{st}.log); dừng phần {sn} ***")
        # VRAM cao -> bớt khe
        if watch.last_mb > 70_000 and slots["gpu"] > 2:
            slots["gpu"] -= 1
            log(f"VRAM {watch.last_mb} MB > 70 GB -> khe GPU còn {slots['gpu']}")
        # khởi động tác vụ sẵn sàng, theo thứ tự ưu tiên
        rest = []
        while heap:
            item = heapq.heappop(heap)
            _, _, sn, st = item
            key = (sn, st)
            if state[key] != "pending":
                continue
            if blocked(sn, st):
                state[key] = "skip"
                continue
            if not ready(sn, st) or busy[KIND[st]] >= slots[KIND[st]]:
                rest.append(item)
                continue
            if st == "tts" and stop_new:
                state[key] = "skip"
                log(f"[{sn}] không mở vì điểm dừng chất lượng")
                continue
            s = by[sn]
            if s.done(st):
                state[key] = "ok"
                log(f"[{sn}/{st}] đã có kết quả, bỏ qua")
                continue
            os.makedirs(os.path.join(TG, s.run, "logs"), exist_ok=True)
            lf = open(os.path.join(TG, s.run, "logs", f"{st}.log"), "a", encoding="utf-8")
            c = s.cmd(st)
            lf.write(f"\n===== {now()} {' '.join(c)}\n")
            lf.flush()
            env = dict(os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONUNBUFFERED="1",
                       ZIPFORMER_DIR=os.path.join(BASE, "zipformer30m"))
            procs[key] = (subprocess.Popen(c, cwd=TG, stdout=lf, stderr=subprocess.STDOUT, env=env), time.time(), lf, False)
            busy[KIND[st]] += 1
            state[key] = "running"
            log(f"[{sn}/{st}] bắt đầu (đang chạy: {dict(busy)})")
        for item in rest:
            heapq.heappush(heap, item)
        if not procs and not any(v == "pending" for v in state.values()):
            break
        if not procs and all(v != "pending" or not ready(k[0], k[1]) for k, v in state.items()) and not heap:
            break
        time.sleep(3)
    watch.stop = True
    summary = {sn: {st: state[(sn, st)] for st in STAGES} for sn in by}
    json.dump(dict(xong_luc=now(), trang_thai=summary, thoi_gian=timing, vram_dinh_mb=watch.peak_mb,
                   dat_v1={sn: dat_rates(by[sn].run) for sn in by}),
              open(os.path.join(TG, "runs", f"full10k_dieu_phoi_{time.strftime('%Y%m%d_%H%M%S')}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    bad = [sn for sn in by if any(summary[sn][st] in ("fail", "skip") for st in STAGES)]
    log(f"KẾT THÚC. VRAM đỉnh {watch.peak_mb} MB. Phần lỗi/bỏ dở: {bad or 'không'}")
    return 0 if not bad else 2


def thu_lo(log):
    """So lô 2 với lô 16 cho M và T trên 200 câu đầu phần B: tỷ lệ câu nghe ra giống hệt."""
    src = os.path.join(TG, "runs", "eval1000_B")
    dst = os.path.join(TG, "runs", "thu_lo")
    os.makedirs(dst, exist_ok=True)
    rows = [json.loads(l) for l in open(os.path.join(src, "manifest.jsonl"), encoding="utf-8")][:200]
    with open(os.path.join(dst, "manifest.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if not os.path.exists(os.path.join(dst, "audio16")):
        os.symlink(os.path.join(src, "audio16"), os.path.join(dst, "audio16"))
    res = {}
    for name, model in (("M", f"{PIN}/PhoWhisper-medium"), ("T", f"{PIN}/PhoWhisper-small")):
        hy = {}
        for lo in (2, 16):
            tag = f"{name}_lo{lo}"
            t0 = time.time()
            subprocess.run([PY, "-m", "buoc.asr_whisper", dst, "--model", model, "--batch", str(lo), "--lexicon", LEX, "--tag", tag],
                           cwd=TG, env=dict(os.environ, HF_HUB_OFFLINE="1"), stdout=subprocess.DEVNULL, check=True)
            hy[lo] = {json.loads(l)["utt_id"]: json.loads(l)["hyp"] for l in open(os.path.join(dst, f"asr_{tag}.jsonl"), encoding="utf-8")}
            res[f"{name}_lo{lo}_giay"] = round(time.time() - t0, 1)
        same = sum(hy[2][u].strip() == hy[16][u].strip() for u in hy[2]) / len(hy[2])
        res[f"{name}_giong_het"] = round(same, 4)
    res["dung_lo_16"] = res["M_giong_het"] >= 0.99 and res["T_giong_het"] >= 0.99
    json.dump(res, open(os.path.join(dst, "ket_qua.json"), "w"), indent=1)
    log(f"Thử cỡ lô: {res}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", nargs="*", default=[])
    ap.add_argument("--gpu-slots", type=int, default=4)
    ap.add_argument("--tts-slots", type=int, default=1)
    ap.add_argument("--cpu-slots", type=int, default=3)
    ap.add_argument("--thu-lo", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.join(TG, "runs"), exist_ok=True)
    logp = os.path.join(TG, "runs", "full10k_dieu_phoi.log")

    def log(msg):
        line = f"{now()} {msg}"
        print(line, flush=True)
        with open(logp, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    if a.thu_lo:
        return thu_lo(log)
    if os.path.exists(os.path.join(TG, "runs", "DUNG_CHAT_LUONG")):
        log("Có runs/DUNG_CHAT_LUONG từ lần trước: đọc, xử lý rồi xóa tay mới chạy tiếp")
        return 3
    kq = os.path.join(TG, "runs", "thu_lo", "ket_qua.json")
    lo = 16 if os.path.exists(kq) and json.load(open(kq)).get("dung_lo_16") else 2
    shards = [Shard(n, lo) for n in a.shards]
    log(f"Bắt đầu {len(shards)} phần {a.shards}; lô ASR (M, T) = {lo}; khe GPU {a.gpu_slots}, TTS {a.tts_slots}, CPU {a.cpu_slots}")
    shutil.which("nvidia-smi") or log("CẢNH BÁO: không có nvidia-smi")
    return run_all(shards, a.gpu_slots, a.tts_slots, a.cpu_slots, log)


if __name__ == "__main__":
    sys.exit(main())
