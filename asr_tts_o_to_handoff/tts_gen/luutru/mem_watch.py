# -*- coding: utf-8 -*-
"""Chạy một lệnh và cứ --every giây ghi: RSS của tiến trình (cộng tiến trình con), RAM available
(psutil.virtual_memory().available), pagefile đang dùng (psutil.swap_memory().used), ổ C: trống.
Dừng tiến trình (terminate) nếu RAM available < --min-avail-gb hoặc ổ C: trống < --min-c-gb.

Chạy (từ tts_gen/):  .venv/Scripts/python -m luutru.mem_watch --log runs/x/logs/mem.csv -- .venv/Scripts/python -m buoc.tts ...
In tóm tắt: thời gian chạy, RSS đỉnh, RAM available thấp nhất, pagefile đầu/cuối/đỉnh; mã thoát = mã thoát của lệnh
(hoặc 4 nếu bị mem_watch dừng).
"""
import argparse
import csv
import os
import subprocess
import sys
import time

import psutil


def snapshot(p):
    rss = 0
    try:
        procs = [p] + p.children(recursive=True)
    except psutil.Error:
        procs = []
    for q in procs:
        try:
            rss += q.memory_info().rss
        except psutil.Error:
            pass
    return dict(t=time.strftime("%H:%M:%S"), rss_gb=round(rss / 2 ** 30, 3),
                avail_gb=round(psutil.virtual_memory().available / 2 ** 30, 3),
                pagefile_gb=round(psutil.swap_memory().used / 2 ** 30, 3),
                c_free_gb=round(psutil.disk_usage("C:\\").free / 2 ** 30, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--every", type=float, default=5.0)
    ap.add_argument("--min-avail-gb", type=float, default=0.3)
    ap.add_argument("--min-c-gb", type=float, default=3.0)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if os.path.exists(cmd[0]):          # Windows CreateProcess không nhận đường dẫn tương đối kiểu ".venv/Scripts/..."
        cmd[0] = os.path.abspath(cmd[0])
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd)
    p = psutil.Process(proc.pid)
    rows, killed = [], None
    with open(a.log, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["t", "rss_gb", "avail_gb", "pagefile_gb", "c_free_gb"])
        w.writeheader()
        while True:
            s = snapshot(p)
            rows.append(s)
            w.writerow(s)
            f.flush()
            if proc.poll() is not None:
                break
            if s["avail_gb"] < a.min_avail_gb or s["c_free_gb"] < a.min_c_gb:
                killed = f"RAM available {s['avail_gb']} GB, ổ C trống {s['c_free_gb']} GB"
                proc.terminate()
                proc.wait(30)
                break
            time.sleep(a.every)
    dt = time.perf_counter() - t0
    print(f"[mem_watch] {dt:.1f} s | RSS đỉnh {max(r['rss_gb'] for r in rows)} GB | RAM available thấp nhất "
          f"{min(r['avail_gb'] for r in rows)} GB | pagefile đầu {rows[0]['pagefile_gb']} / cuối {rows[-1]['pagefile_gb']} / "
          f"đỉnh {max(r['pagefile_gb'] for r in rows)} GB | ổ C trống thấp nhất {min(r['c_free_gb'] for r in rows)} GB"
          + (f" | DỪNG: {killed}" if killed else ""), flush=True)
    sys.exit(4 if killed else proc.returncode)


if __name__ == "__main__":
    main()
