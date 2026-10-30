# -*- coding: utf-8 -*-
"""Tải nguồn nhiễu cho bước trộn nhiễu (cauhinh/nhieu.py, NGUON_NHIEU). Chỉ dùng thư viện chuẩn.

Chạy trên NÚT ĐẦU cụm (có mạng), từ tts_gen/:
  python -m buoc.nhieu_tai tat_ca --dich ~/asr_tts_o_to/nhieu      # hoặc: cavemove | aishell5 (qua dieuphoi/slurm/tai_nhieu.sh)
cavemove: tải nguyên zip 7,6 GB (phần nhiễu chiếm gần hết zip), so md5 với Zenodo, giải nén noise/, ventilation/,
          uncontrolled_conditions/ và info.json của từng xe (zipfile kiểm CRC từng tệp).
aishell5: tải noise.tar.gz 13 GB (thử máy chủ dự phòng nếu lỗi); không có md5 công bố nên so độ dài với
          Content-Length và ghi sha256; giải nén bằng tarfile filter="data" (chặn đường dẫn ra ngoài, liên kết lạ).
Tải tiếp được khi đứt (HTTP Range, tệp .part); đã có và khớp thì bỏ qua. Mỗi bộ một thư mục <dich>/<bộ>/: tệp tải
về, giai_nen/, danh_sach.tsv (đường dẫn, kích thước), nguon.json (url, kích thước, md5/sha256, giấy phép, trích dẫn).
Dữ liệu tải về là không tin cậy: không chạy gì trong đó.
"""
import argparse
import hashlib
import json
import os
import tarfile
import time
import urllib.request
import zipfile

import cauhinh.nhieu as N

KHOI = 1 << 20


def bam(path, thuat="md5"):
    h = hashlib.new(thuat)
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 * KHOI), b""):
            h.update(b)
    return h.hexdigest()


def kich_thuoc_xa(url):
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
        return int(r.headers["Content-Length"]), r.url


def tai_tiep(url, path, lan_thu=20):
    """Tải url về path, tiếp tục từ path + '.part' nếu đã có. Trả (kích thước, url thật sau chuyển hướng)."""
    n, that = kich_thuoc_xa(url)
    if os.path.exists(path) and os.path.getsize(path) == n:
        return n, that
    part = path + ".part"
    for lan in range(lan_thu):
        da = os.path.getsize(part) if os.path.exists(part) else 0
        if da >= n:
            break
        try:
            req = urllib.request.Request(that, headers={"Range": f"bytes={da}-"} if da else {})
            with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab" if da else "wb") as f:
                if da and r.status != 206:
                    raise IOError(f"máy chủ không tải tiếp được (HTTP {r.status})")
                t0, moc = time.time(), da
                for b in iter(lambda: r.read(KHOI), b""):
                    f.write(b)
                    da += len(b)
                    if da - moc >= 512 * KHOI:
                        print(f"    {os.path.basename(path)}: {da / 1e9:.2f}/{n / 1e9:.2f} GB, "
                              f"{(da - moc) / 1e6 / max(time.time() - t0, 1e-3):.1f} MB/s", flush=True)
                        t0, moc = time.time(), da
        except OSError as e:
            print(f"    lỗi lần {lan + 1}: {e}; thử lại sau 30 s", flush=True)
            time.sleep(30)
    if os.path.getsize(part) != n:
        raise SystemExit(f"{path}: tải được {os.path.getsize(part)} / {n} byte")
    os.replace(part, path)
    return n, that


def an_toan(ten):
    p = ten.replace("\\", "/")
    return not (p.startswith("/") or ":" in p.split("/")[0] or ".." in p.split("/"))


def ghi_nguon(thu_muc, **kv):
    with open(os.path.join(thu_muc, "nguon.json"), "w", encoding="utf-8") as f:
        json.dump(dict(kv, ghi_luc=time.strftime("%F %T")), f, ensure_ascii=False, indent=1)


def cavemove(dich):
    s = N.NGUON_NHIEU["cavemove"]
    d = os.path.join(dich, "cavemove")
    os.makedirs(d, exist_ok=True)
    zp = os.path.join(d, "cavemove_dataset.zip")
    n, that = tai_tiep(s["url"], zp)
    m = bam(zp)
    if m != s["md5"]:
        raise SystemExit(f"{zp}: md5 {m} khác Zenodo {s['md5']}")
    print(f"  CAVEMOVE: {n / 1e9:.2f} GB, md5 khớp", flush=True)
    out = os.path.join(d, "giai_nen")
    dong = []
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            p = i.filename.split("/")
            if i.is_dir() or not (set(p) & set(s["thu_muc"]) or p[-1] == "info.json"):
                continue
            if not an_toan(i.filename):
                raise SystemExit(f"đường dẫn lạ trong zip: {i.filename}")
            dich_tep = os.path.join(out, i.filename)
            if not (os.path.exists(dich_tep) and os.path.getsize(dich_tep) == i.file_size):
                z.extract(i, out)
            dong.append((i.filename, i.file_size))
    with open(os.path.join(d, "danh_sach.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("duong_dan\tkich_thuoc\n" + "".join(f"{a}\t{b}\n" for a, b in dong))
    ghi_nguon(d, url=that, kich_thuoc=n, md5=m, so_tep=len(dong), giay_phep=s["giay_phep"], trich_dan=s["trich_dan"])
    print(f"  CAVEMOVE: giải nén {len(dong)} tệp ({sum(b for _, b in dong) / 1e9:.2f} GB), CRC đã kiểm", flush=True)


def aishell5(dich):
    s = N.NGUON_NHIEU["aishell5"]
    d = os.path.join(dich, "aishell5")
    os.makedirs(d, exist_ok=True)
    tp = os.path.join(d, "noise.tar.gz")
    loi = None
    for url in (s["url"],) + tuple(s["url_du_phong"]):
        try:
            n, that = tai_tiep(url, tp)
            break
        except (OSError, SystemExit) as e:
            loi = e
            print(f"  {url}: {e}; thử máy chủ khác", flush=True)
    else:
        raise SystemExit(f"AISHELL-5: không tải được ({loi})")
    sha = bam(tp, "sha256")
    print(f"  AISHELL-5: {n / 1e9:.2f} GB, khớp Content-Length, sha256 {sha[:16]}…", flush=True)
    out = os.path.join(d, "giai_nen")
    dong = []
    with tarfile.open(tp, "r:gz") as t:
        for m in t:
            if not m.isfile():
                continue
            if not an_toan(m.name):
                raise SystemExit(f"đường dẫn lạ trong tar: {m.name}")
            dich_tep = os.path.join(out, m.name)
            if not (os.path.exists(dich_tep) and os.path.getsize(dich_tep) == m.size):
                t.extract(m, out, filter="data")
            dong.append((m.name, m.size))
    with open(os.path.join(d, "danh_sach.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("duong_dan\tkich_thuoc\n" + "".join(f"{a}\t{b}\n" for a, b in dong))
    ghi_nguon(d, url=that, kich_thuoc=n, sha256=sha, so_tep=len(dong), giay_phep=s["giay_phep"], trich_dan=s["trich_dan"])
    print(f"  AISHELL-5: giải nén {len(dong)} tệp ({sum(b for _, b in dong) / 1e9:.2f} GB)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bo", choices=["cavemove", "aishell5", "tat_ca"])
    ap.add_argument("--dich", required=True)
    a = ap.parse_args()
    dich = os.path.abspath(os.path.expanduser(a.dich))
    for bo, f in (("cavemove", cavemove), ("aishell5", aishell5)):
        if a.bo in (bo, "tat_ca"):
            print(f"== {time.strftime('%F %T')} {bo} -> {dich}", flush=True)
            f(dich)
    print(f"== {time.strftime('%F %T')} xong", flush=True)


if __name__ == "__main__":
    main()
