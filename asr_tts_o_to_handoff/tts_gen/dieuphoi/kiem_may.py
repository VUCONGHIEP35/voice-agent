# -*- coding: utf-8 -*-
"""Kiểm tra phần cứng trước khi sinh TTS (giai đoạn 0 của kế hoạch VieNeu v3 Turbo).

Chạy (từ tts_gen/):  .venv/Scripts/python -m dieuphoi.kiem_may
In bảng tiếng Việt và ghi hw_report.json. Báo cáo không ghi tên máy, tên người dùng hay đường dẫn.
Bổ sung cho src/benchmark_hardware.py (đo DataLoader, VRAM giả lập): ở đây kiểm nvidia-smi, chạy thử
fp16/bf16 thật trên GPU, cờ CPU (VNNI), ổ đĩa, pin, và rút kết luận theo quy tắc của kế hoạch.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import time

from cauhinh.duong_dan import GOC as HERE  # noqa: E402
GPU_GOOD_GB = 8      # kế hoạch: "có GPU NVIDIA từ 8 GB thì chạy tại máy"
RAM_OK_GB = 16
DISK_MIN_GB = 20


def _run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def torch_facts():
    try:
        import torch
    except Exception as e:  # noqa
        return {"installed": False, "error": repr(e)}
    t = {"installed": True, "version": torch.__version__, "cuda_build": torch.version.cuda,
         "cuda_available": torch.cuda.is_available()}
    if not t["cuda_available"]:
        return t
    try:
        p = torch.cuda.get_device_properties(0)
        t.update(device=p.name, capability=f"{p.major}.{p.minor}", total_gb=round(p.total_memory / 2 ** 30, 2),
                 bf16=bool(torch.cuda.is_bf16_supported()))
        free, _ = torch.cuda.mem_get_info()
        t["free_gb"] = round(free / 2 ** 30, 2)
        a = torch.randn(2048, 2048, device="cuda")
        b = torch.randn(2048, 2048, device="cuda")
        ref = a @ b
        torch.cuda.synchronize()
        tests = {}
        for name, dt in (("fp32", torch.float32), ("fp16", torch.float16), ("bf16", torch.bfloat16)):
            try:
                x, y = a.to(dt), b.to(dt)
                z = x @ y
                torch.cuda.synchronize()
                t0 = time.perf_counter()
                for _ in range(10):
                    z = x @ y
                torch.cuda.synchronize()
                dtm = (time.perf_counter() - t0) / 10
                err = ((z.float() - ref).abs().max() / ref.abs().max()).item()
                tests[name] = {"ms": round(dtm * 1000, 2), "tflops": round(2 * 2048 ** 3 / dtm / 1e12, 2),
                               "rel_err": float(f"{err:.2e}")}
            except Exception as e:  # noqa
                tests[name] = {"error": repr(e)}
        t["matmul_2048"] = tests
        del a, b, ref
        torch.cuda.empty_cache()
    except Exception as e:  # noqa
        t["error"] = repr(e)
    return t


def collect():
    f = {"errors": [], "os": platform.platform(), "python": platform.python_version()}
    try:
        import psutil
        vm = psutil.virtual_memory()
        f.update(ram_total_gb=round(vm.total / 2 ** 30, 1), ram_avail_gb=round(vm.available / 2 ** 30, 1),
                 cpu_physical=psutil.cpu_count(logical=False), cpu_logical=psutil.cpu_count(logical=True))
        bat = psutil.sensors_battery()
        f["on_battery"] = bool(bat is not None and not bat.power_plugged)
        f["battery_pct"] = None if bat is None else round(bat.percent)
        disks = {}
        for part in psutil.disk_partitions(all=False):
            if "fixed" not in part.opts and os.name == "nt":
                continue
            try:
                u = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            disks[part.device.rstrip("\\/").upper()] = {"free_gb": round(u.free / 2 ** 30, 1), "total_gb": round(u.total / 2 ** 30, 1)}
        f["disks"] = disks
    except Exception as e:  # noqa
        f["errors"].append(f"psutil: {e!r}")
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        f["cpu_name"] = info.get("brand_raw")
        f["cpu_flags"] = sorted(x for x in set(info.get("flags", [])) if x in ("avx2", "avx512f") or "vnni" in x)
    except Exception as e:  # noqa
        f["errors"].append(f"cpuinfo: {e!r}")
    f["project_drive"] = os.path.splitdrive(HERE)[0].upper()
    hf = os.environ.get("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    f["hf_cache_drive"] = os.path.splitdrive(hf)[0].upper()
    f["hf_home_set"] = bool(os.environ.get("HF_HOME"))
    gpus = []
    q = _run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version,compute_cap",
              "--format=csv,noheader,nounits"])
    for line in q.strip().splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) == 5:
            gpus.append({"name": p[0], "mem_total_mb": int(p[1]), "mem_free_mb": int(p[2]), "driver": p[3], "compute_cap": p[4]})
    f["nvidia_smi_gpus"] = gpus
    m = re.search(r"CUDA Version:\s*([0-9.]+)", _run(["nvidia-smi"]))
    f["driver_max_cuda"] = m.group(1) if m else None
    f["ffmpeg"] = bool(shutil.which("ffmpeg"))
    f["torch"] = torch_facts()
    return f


def danh_gia(f):
    """Rút kết luận từ số liệu (hàm thuần, có test). Trả danh sách (mục, kết luận, lý do)."""
    out = []
    t = f.get("torch") or {}
    gpus = f.get("nvidia_smi_gpus") or []
    vram = t.get("total_gb") if t.get("cuda_available") else (gpus[0]["mem_total_mb"] / 1024 if gpus else None)
    if vram is None:
        out.append(("Máy chạy TTS", "CPU (ONNX)", "không có GPU NVIDIA"))
        vnni = [x for x in (f.get("cpu_flags") or []) if "vnni" in x]
        if vnni:
            out.append(("int8 trên CPU", "dùng được nhưng phải nghe thử", f"CPU có cờ {', '.join(vnni)}"))
        else:
            out.append(("int8 trên CPU", "KHÔNG dùng", "không thấy cờ VNNI; README cảnh báo âm thanh bị méo"))
    elif vram >= GPU_GOOD_GB:
        out.append(("Máy chạy TTS", "ưu tiên chạy tại máy", f"GPU {vram:.1f} GB ≥ {GPU_GOOD_GB} GB (quy tắc của kế hoạch)"))
        out.append(("ASR kiểm tra (PhoWhisper-large)", "chạy tại máy, sau bước TTS", "không chạy song song với TTS nếu VRAM sát"))
    else:
        out.append(("Máy chạy TTS", "chạy tại máy, phải đo VRAM khi gom lô ở giai đoạn 0",
                    f"GPU {vram:.1f} GB < {GPU_GOOD_GB} GB; README đo 1,1 GB đỉnh ở chế độ stream 16 luồng, chưa đo infer_batch"))
        out.append(("ASR kiểm tra (PhoWhisper-large)", "chạy trên Colab, hoặc thử fp16 tại máy sau khi giải phóng TTS",
                    f"mô hình large khoảng 3 GB trọng số fp16, GPU chỉ có {vram:.1f} GB"))
    if gpus and not t.get("installed"):
        out.append(("torch", "chưa cài", "có GPU qua nvidia-smi nhưng chưa có torch để thử CUDA"))
    elif gpus and not t.get("cuda_available"):
        out.append(("torch", "không dùng được CUDA", "có GPU nhưng torch là bản CPU, hoặc driver không hợp"))
    elif t.get("cuda_available"):
        mm = (t.get("matmul_2048") or {}).get("bf16") or {}
        if t.get("bf16") and mm and "error" not in mm:
            out.append(("Kiểu số trên GPU", "bf16", f"compute capability {t.get('capability')}, nhân ma trận bf16 chạy được"))
        else:
            out.append(("Kiểu số trên GPU", "fp16, phải nghe so với fp32", "GPU không hỗ trợ bf16 hoặc thử bf16 bị lỗi"))
    ram = f.get("ram_total_gb")
    if ram is not None and ram < RAM_OK_GB:
        out.append(("RAM", f"cảnh báo: {ram} GB", f"dưới {RAM_OK_GB} GB: tối đa 4 tiến trình CPU, không dùng 'số nhân − 1'"))
    disks = f.get("disks") or {}
    for label, drv in (("Ổ chứa dự án / đầu ra", f.get("project_drive")), ("Ổ chứa cache Hugging Face", f.get("hf_cache_drive"))):
        d = disks.get(drv)
        if d and d["free_gb"] < DISK_MIN_GB:
            best = max(disks, key=lambda k: disks[k]["free_gb"])
            out.append((label, f"cảnh báo: {drv} còn {d['free_gb']} GB",
                        f"dưới {DISK_MIN_GB} GB; nên chuyển sang {best} (còn {disks[best]['free_gb']} GB)"))
    if f.get("on_battery"):
        out.append(("Nguồn điện", "cảnh báo: đang chạy pin", "laptop chạy pin thường hạ xung GPU/CPU; cắm sạc khi đo và khi sinh"))
    if f.get("ffmpeg") is False:
        out.append(("ffmpeg", "chưa có trên PATH", "cần để đọc/ghi mp3 và kiểm tra giải mã"))
    return out


def main():
    f = collect()
    t = f["torch"]
    print("=" * 72)
    print("KIỂM TRA PHẦN CỨNG CHO KẾ HOẠCH SINH TTS")
    print("=" * 72)
    print(f"Hệ điều hành   {f['os']} | Python {f['python']}")
    print(f"CPU            {f.get('cpu_name')} | {f.get('cpu_physical')} nhân / {f.get('cpu_logical')} luồng | cờ: {f.get('cpu_flags')}")
    print(f"RAM            tổng {f.get('ram_total_gb')} GB, trống {f.get('ram_avail_gb')} GB")
    print(f"Ổ đĩa          " + ", ".join(f"{k} trống {v['free_gb']}/{v['total_gb']} GB" for k, v in (f.get('disks') or {}).items()))
    print(f"Cache HF       ổ {f['hf_cache_drive']} (HF_HOME {'đã' if f['hf_home_set'] else 'chưa'} đặt) | dự án ở ổ {f['project_drive']}")
    for g in f["nvidia_smi_gpus"]:
        print(f"GPU (smi)      {g['name']} | {g['mem_total_mb']} MiB, trống {g['mem_free_mb']} MiB | driver {g['driver']} | "
              f"compute {g['compute_cap']} | CUDA tối đa của driver {f['driver_max_cuda']}")
    print(f"torch          {t.get('version')} (CUDA build {t.get('cuda_build')}) | cuda_available={t.get('cuda_available')} | "
          f"bf16={t.get('bf16')} | VRAM trống {t.get('free_gb')} GB")
    for k, v in (t.get("matmul_2048") or {}).items():
        print(f"  nhân ma trận 2048 {k:5s} {v}")
    if t.get("error"):
        print("  LỖI torch:", t["error"])
    print(f"Pin            {'ĐANG CHẠY PIN' if f.get('on_battery') else 'cắm sạc / không có pin'} ({f.get('battery_pct')}%) | ffmpeg: {f.get('ffmpeg')}")
    for e in f["errors"]:
        print("LỖI thu thập:", e)
    print("-" * 72)
    verdict = danh_gia(f)
    for muc, kl, ly in verdict:
        print(f"* {muc}: {kl}\n    lý do: {ly}")
    f["danh_gia"] = [dict(muc=a, ket_luan=b, ly_do=c) for a, b, c in verdict]
    with open(os.path.join(HERE, "hw_report.json"), "w", encoding="utf-8") as fo:
        json.dump(f, fo, ensure_ascii=False, indent=1)
    print("Đã ghi hw_report.json")


if __name__ == "__main__":
    main()
