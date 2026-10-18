"""safe_fetch.py - kiem tra an toan cho du lieu am thanh tai tu nguon ngoai (vd ViSpeech).

Nguyen tac (du lieu tai ve la KHONG tin cay):
- Khong chay, khong import, khong mo bang trinh thong dich bat ky tep nao trong du lieu.
- Khong giai nen hang loat: kiem toan bo muc luc truoc, roi giai nen tung tep vao dung thu muc dich.
- Chi nhan duoi tep trong danh sach cho phep; tu choi duong dan tuyet doi, '..', dau gach nguoc, ky tu NUL,
  thanh phan an, lien ket tuong trung, muc ma hoa, tep qua lon, ty le nen bat thuong (zip bomb).
- Khong ghi de tep da co; xoa tep do dang neu loi giua chung.
- Tep am thanh phai dung chu ky dau tep VA giai ma duoc bang ffprobe (goi bang danh sach doi so, khong qua shell).
- Ngan sach dung luong tong cho moi lan tai.
"""
import hashlib
import os
import stat
import subprocess

BACKSLASH = chr(92)
NUL = chr(0)
ALLOWED_EXT = {".mp3", ".wav", ".flac", ".txt", ".csv", ".json"}
AUDIO_EXT = {".mp3", ".wav", ".flac"}
MAX_NAME_LEN = 255
MAX_MEMBER_BYTES = 20 * 2 ** 20      # 20 MiB moi tep sau giai nen
MAX_RATIO = 50                        # ty le giai nen / nen toi da; mp3 gan nhu khong nen them duoc
CHUNK = 2 ** 16
BAD_MAGIC = {                          # chu ky tep thuc thi / luu tru khong duoc nam trong tep "am thanh"
    "ELF": bytes([0x7F, 0x45, 0x4C, 0x46]),
    "PE/MZ": bytes([0x4D, 0x5A]),
    "ZIP": bytes([0x50, 0x4B, 0x03, 0x04]),
    "shebang": bytes([0x23, 0x21]),
}


class UnsafeInput(Exception):
    """Du lieu ngoai vi pham mot quy tac an toan."""


def check_member_name(name):
    if not name or len(name) > MAX_NAME_LEN:
        raise UnsafeInput(f"ten rong hoac qua dai: {name[:80]!r}")
    if NUL in name:
        raise UnsafeInput("ten chua ky tu NUL")
    if BACKSLASH in name:
        raise UnsafeInput(f"ten chua dau gach nguoc: {name!r}")
    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        raise UnsafeInput(f"duong dan tuyet doi: {name!r}")
    parts = [p for p in name.split("/") if p]
    if any(p == ".." for p in parts):
        raise UnsafeInput(f"duong dan thoat ra ngoai ('..'): {name!r}")
    if any(p.startswith(".") for p in parts):
        raise UnsafeInput(f"thanh phan an (bat dau bang '.'): {name!r}")
    if not name.endswith("/"):
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXT:
            raise UnsafeInput(f"duoi tep khong cho phep {ext!r}: {name!r}")
    return name


def check_zipinfo(info):
    check_member_name(info.filename)
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode):
        raise UnsafeInput(f"lien ket tuong trung: {info.filename!r}")
    if info.flag_bits & 0x1:
        raise UnsafeInput(f"muc ma hoa: {info.filename!r}")
    if info.is_dir():
        return info
    if info.file_size > MAX_MEMBER_BYTES:
        raise UnsafeInput(f"tep qua lon {info.file_size} byte: {info.filename!r}")
    if info.file_size > 0 and (info.compress_size == 0 or info.file_size / info.compress_size > MAX_RATIO):
        raise UnsafeInput(f"ty le nen bat thuong (zip bomb?): {info.filename!r}")
    return info


def audit_zip(zf):
    """Kiem toan bo muc luc truoc khi giai nen bat ky tep nao. Tra ve (muc hop le, [(ten, ly do)])."""
    ok, bad = [], []
    for info in zf.infolist():
        try:
            ok.append(check_zipinfo(info))
        except UnsafeInput as e:
            bad.append((info.filename, str(e)))
    return ok, bad


def safe_extract(zf, info, dest):
    """Giai nen DUNG MOT muc vao trong dest. Khong ghi de; xoa tep do dang neu loi."""
    check_zipinfo(info)
    if info.is_dir():
        raise UnsafeInput("khong giai nen thu muc rieng le")
    root = os.path.realpath(dest)
    target = os.path.realpath(os.path.join(root, info.filename))
    if os.path.commonpath([root, target]) != root:
        raise UnsafeInput(f"dich ra ngoai thu muc: {info.filename!r}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    created, n = False, 0
    try:
        with zf.open(info) as src:
            with open(target, "xb") as out:
                created = True
                while True:
                    buf = src.read(CHUNK)
                    if not buf:
                        break
                    n += len(buf)
                    if n > info.file_size or n > MAX_MEMBER_BYTES:
                        raise UnsafeInput(f"du lieu dai hon khai bao: {info.filename!r}")
                    out.write(buf)
    except BaseException:
        if created and os.path.exists(target):
            os.remove(target)
        raise
    return target


def sniff_audio(path):
    """Kiem chu ky dau tep khop duoi am thanh, va khong mang chu ky tep thuc thi / luu tru."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in AUDIO_EXT:
        raise UnsafeInput(f"khong phai duoi am thanh: {path!r}")
    with open(path, "rb") as f:
        h = f.read(16)
    for kind, sig in BAD_MAGIC.items():
        if h.startswith(sig):
            raise UnsafeInput(f"chu ky {kind} trong tep am thanh: {path!r}")
    ok = {
        ".mp3": h[:3] == b"ID3" or (len(h) > 1 and h[0] == 0xFF and (h[1] & 0xE0) == 0xE0),
        ".wav": h[:4] == b"RIFF" and h[8:12] == b"WAVE",
        ".flac": h[:4] == b"fLaC",
    }[ext]
    if not ok:
        raise UnsafeInput(f"chu ky dau tep khong khop {ext}: {path!r}")
    return ext


def decode_check(path, min_s=0.3, max_s=120.0, timeout=30):
    """Tep phai giai ma duoc bang ffprobe va co thoi luong hop ly. Duong dan doi sang tuyet doi
    de ten bat dau bang '-' khong bi hieu la tuy chon."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", os.path.abspath(path)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True).stdout.strip()
        dur = float(out)
    except (subprocess.SubprocessError, ValueError) as e:
        raise UnsafeInput(f"khong giai ma duoc: {path!r} ({type(e).__name__})")
    if not (min_s <= dur <= max_s):
        raise UnsafeInput(f"thoi luong {dur:.2f} s ngoai [{min_s}, {max_s}]: {path!r}")
    return dur


class Budget:
    """Ngan sach byte cho mot lan tai: vuot thi dung."""

    def __init__(self, limit_bytes):
        self.limit, self.used = int(limit_bytes), 0

    def take(self, n):
        if self.used + n > self.limit:
            raise UnsafeInput(f"vuot ngan sach dung luong: {self.used + n} > {self.limit} byte")
        self.used += n


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for buf in iter(lambda: f.read(CHUNK), b""):
            h.update(buf)
    return h.hexdigest()
