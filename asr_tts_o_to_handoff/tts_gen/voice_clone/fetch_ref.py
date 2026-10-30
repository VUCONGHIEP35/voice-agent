# -*- coding: utf-8 -*-
"""fetch_ref.py - tải MỘT ĐOẠN âm thanh ngắn từ video ứng viên để chọn giọng tham chiếu clone.

Chỉ tải khi có quyền:
  permission = da_dong_y   chủ kênh / người nói đã đồng ý (ghi bằng chứng vào permission_note)
  permission = cc_by       video có giấy phép Creative Commons; script kiểm lại trường license do yt-dlp đọc được
  permission = khac        bị bỏ qua, trừ khi chạy với --cho-phep-chua-ro-quyen (khi đó đoạn tải về bị đánh dấu
                           chua_ro_quyen, chỉ để thử nội bộ, không được công bố dữ liệu sinh từ giọng này)
Mỗi ứng viên chỉ tải đoạn [start_s, end_s], tối đa --max-seconds (mặc định 180 s): lấy đủ để chọn đoạn 3-8 s,
không lưu cả video.

Cần: pip install yt-dlp ; ffmpeg có trong PATH.
Chạy từ tts_gen/:
  .venv/Scripts/python voice_clone/fetch_ref.py voice_clone/candidates.csv --out voice_clone/raw
Ghi: <out>/<cand_id>.wav (mono, giữ tần số gốc), <out>/<cand_id>.meta.json, <out>/fetch_log.csv
"""
import argparse
import csv
import datetime
import json
import os
import subprocess
import sys

REQUIRED = ["cand_id", "url", "start_s", "end_s", "region", "sub_region", "gender", "region_evidence", "permission"]


def read_candidates(path):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    miss = [c for c in REQUIRED if rows and c not in rows[0]]
    if miss:
        raise SystemExit(f"candidates thiếu cột: {miss}")
    ids = [r["cand_id"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise SystemExit(f"cand_id trùng: {sorted(dup)}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--out", default="voice_clone/raw")
    ap.add_argument("--max-seconds", type=float, default=180)
    ap.add_argument("--cho-phep-chua-ro-quyen", action="store_true",
                    help="tải cả dòng permission=khac để thử nội bộ (đánh dấu chua_ro_quyen)")
    ap.add_argument("--only", nargs="*", help="chỉ xử lý các cand_id này")
    a = ap.parse_args()

    try:
        import yt_dlp
        from yt_dlp.utils import download_range_func
    except ImportError:
        raise SystemExit("Chưa cài yt-dlp: .venv/Scripts/pip install yt-dlp")

    os.makedirs(a.out, exist_ok=True)
    log = []
    for r in read_candidates(a.candidates):
        cid = r["cand_id"].strip()
        if a.only and cid not in a.only:
            continue
        perm = r["permission"].strip()
        if perm not in ("da_dong_y", "cc_by") and not a.cho_phep_chua_ro_quyen:
            log.append(dict(cand_id=cid, status="bo_qua", reason=f"permission={perm}"))
            print(f"[bỏ qua] {cid}: chưa có quyền (permission={perm})")
            continue
        try:
            start, end = float(r["start_s"]), float(r["end_s"])
        except ValueError:
            log.append(dict(cand_id=cid, status="loi", reason="start_s/end_s không phải số"))
            continue
        end = min(end, start + a.max_seconds)
        if end - start < 20:
            log.append(dict(cand_id=cid, status="loi", reason="đoạn < 20 s, quá ngắn để chọn tham chiếu"))
            continue

        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            try:
                info = ydl.extract_info(r["url"], download=False)
            except Exception as e:
                log.append(dict(cand_id=cid, status="loi", reason=f"không đọc được thông tin video: {e}"))
                print(f"[lỗi] {cid}: {e}")
                continue
        lic = info.get("license") or ""
        if perm == "cc_by" and "creative commons" not in lic.lower():
            log.append(dict(cand_id=cid, status="bo_qua", reason=f"ghi cc_by nhưng license đọc được là '{lic}'"))
            print(f"[bỏ qua] {cid}: không thấy giấy phép Creative Commons (license='{lic}')")
            continue
        rights = {"da_dong_y": "da_dong_y", "cc_by": "cc_by"}.get(perm, "chua_ro_quyen")

        tmpl = os.path.join(a.out, f"{cid}.%(ext)s")
        opts = {
            "quiet": True,
            "format": "bestaudio/best",
            "outtmpl": tmpl,
            "download_ranges": download_range_func(None, [(start, end)]),
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
            "overwrites": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([r["url"]])
        except Exception as e:
            log.append(dict(cand_id=cid, status="loi", reason=f"tải thất bại: {e}"))
            print(f"[lỗi] {cid}: {e}")
            continue
        wav = os.path.join(a.out, f"{cid}.wav")
        if not os.path.exists(wav):
            log.append(dict(cand_id=cid, status="loi", reason="không thấy tệp wav sau khi tải (kiểm tra ffmpeg)"))
            continue
        # về mono, giữ tần số gốc
        mono = os.path.join(a.out, f"{cid}.mono.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", mono], check=True)
        os.replace(mono, wav)

        meta = dict(cand_id=cid, url=r["url"], title=info.get("title"), channel=info.get("channel") or info.get("uploader"),
                    channel_url=info.get("channel_url"), license=lic, rights=rights,
                    permission_note=r.get("permission_note", ""), section=[start, end],
                    region=r["region"], sub_region=r["sub_region"], gender=r["gender"],
                    region_evidence=r["region_evidence"], video_type=r.get("video_type", ""),
                    native_audio_codec=info.get("acodec"), native_abr=info.get("abr"), native_asr=info.get("asr"),
                    downloaded_at=datetime.datetime.now().isoformat(timespec="seconds"))
        with open(os.path.join(a.out, f"{cid}.meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        log.append(dict(cand_id=cid, status="ok", reason=rights))
        print(f"[ok] {cid}: {end - start:.0f} s, license='{lic}', quyền={rights}")

    with open(os.path.join(a.out, "fetch_log.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["cand_id", "status", "reason"])
        w.writeheader()
        w.writerows(log)
    print(f"\n{sum(x['status'] == 'ok' for x in log)}/{len(log)} ứng viên tải được -> {a.out}")


if __name__ == "__main__":
    sys.exit(main())
