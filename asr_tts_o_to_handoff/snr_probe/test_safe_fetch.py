"""Test bao mat cho safe_fetch.py: dung tep doc hai tu dung trong thu muc tam, KHONG dung du lieu that.
Chay: python test_safe_fetch.py   (in PASS/FAIL tung test; ma thoat 1 neu co FAIL). Can ffmpeg, ffprobe.
"""
import hashlib
import io
import os
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

import safe_fetch as S

BS = chr(92)


def expect_reject(fn, *a):
    try:
        fn(*a)
    except S.UnsafeInput as e:
        return str(e)
    raise AssertionError(f"KHONG bi chan: {fn.__name__}{a!r}"[:200])


def zinfo(name, mode=0o644, compress=zipfile.ZIP_STORED):
    zi = zipfile.ZipInfo(name)
    zi.external_attr = (stat.S_IFREG | mode) << 16
    zi.compress_type = compress
    return zi


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for zi, data in entries:
            z.writestr(zi, data)
    buf.seek(0)
    return zipfile.ZipFile(buf)


def write(path, data):
    with open(path, "wb") as f:
        f.write(data)


# ---------- ten muc trong kho nen ----------
def test_ten_hop_le_duoc_nhan():
    for n in ["trainset/a.mp3", "metadata/train.csv", "dataset/train.txt", "trainset/"]:
        assert S.check_member_name(n) == n


def test_zip_slip():
    expect_reject(S.check_member_name, "../evil.mp3")
    expect_reject(S.check_member_name, "trainset/../../evil.mp3")


def test_duong_dan_tuyet_doi():
    expect_reject(S.check_member_name, "/etc/evil.mp3")
    expect_reject(S.check_member_name, "C:/evil.mp3")


def test_dau_gach_nguoc_kieu_windows():
    expect_reject(S.check_member_name, ".." + BS + "evil.mp3")
    expect_reject(S.check_member_name, "C:" + BS + "evil.mp3")


def test_ky_tu_nul():
    expect_reject(S.check_member_name, "a.mp3" + chr(0) + ".py")


def test_duoi_tep_bi_cam():
    for n in ["run.py", "x.sh", "a.exe", "b.ipynb", "c.pkl", "d.so", "e.mp3.py", "noext"]:
        expect_reject(S.check_member_name, n)


def test_thanh_phan_an():
    expect_reject(S.check_member_name, "trainset/.hidden.mp3")
    expect_reject(S.check_member_name, "__MACOSX/trainset/._a.mp3")


def test_ten_qua_dai():
    expect_reject(S.check_member_name, "a" * 300 + ".mp3")


# ---------- thuoc tinh muc ----------
def test_lien_ket_tuong_trung():
    zi = zinfo("link.mp3")
    zi.external_attr = (stat.S_IFLNK | 0o777) << 16
    z = make_zip([(zi, b"/etc/passwd")])
    expect_reject(S.check_zipinfo, z.infolist()[0])


def test_muc_ma_hoa():
    zi = zinfo("enc.mp3")
    zi.flag_bits |= 0x1
    zi.file_size, zi.compress_size = 1000, 1000
    expect_reject(S.check_zipinfo, zi)


def test_zip_bomb_ty_le_nen():
    z = make_zip([(zinfo("bomb.mp3", compress=zipfile.ZIP_DEFLATED), bytes(10 * 2 ** 20))])
    msg = expect_reject(S.check_zipinfo, z.infolist()[0])
    assert "nen" in msg, msg


def test_tep_qua_lon():
    z = make_zip([(zinfo("big.mp3"), random.Random(0).randbytes(S.MAX_MEMBER_BYTES + 1))])
    msg = expect_reject(S.check_zipinfo, z.infolist()[0])
    assert "qua lon" in msg, msg


def test_kiem_muc_luc_truoc_khi_giai_nen():
    z = make_zip([(zinfo("trainset/ok.mp3"), b"ID3" + bytes(100)), (zinfo("../x.mp3"), b"1"), (zinfo("run.py"), b"1")])
    ok, bad = S.audit_zip(z)
    assert [i.filename for i in ok] == ["trainset/ok.mp3"], ok
    assert sorted(n for n, _ in bad) == ["../x.mp3", "run.py"], bad


# ---------- giai nen ----------
def test_giai_nen_khong_thoat_thu_muc():
    d = tempfile.mkdtemp()
    try:
        z = make_zip([(zinfo("../outside.mp3"), b"ID3" + bytes(100))])
        expect_reject(S.safe_extract, z, z.infolist()[0], os.path.join(d, "dest"))
        assert not os.path.exists(os.path.join(d, "outside.mp3"))
    finally:
        shutil.rmtree(d)


def test_khong_ghi_de_tep_da_co():
    d = tempfile.mkdtemp()
    try:
        z = make_zip([(zinfo("a/x.txt"), b"1")])
        S.safe_extract(z, z.infolist()[0], d)
        try:
            S.safe_extract(z, z.infolist()[0], d)
            raise AssertionError("KHONG bi chan: ghi de tep da co")
        except FileExistsError:
            pass
    finally:
        shutil.rmtree(d)


def test_muc_luc_noi_doi_kich_thuoc_va_xoa_tep_do_dang():
    d = tempfile.mkdtemp()
    try:
        z = make_zip([(zinfo("lie.txt"), b"x" * 1000)])
        info = z.infolist()[0]
        info.file_size = 10
        try:
            S.safe_extract(z, info, d)
            raise AssertionError("KHONG bi chan: kich thuoc khai bao sai")
        except (S.UnsafeInput, zipfile.BadZipFile):
            pass
        assert not os.path.exists(os.path.join(d, "lie.txt")), "tep do dang chua bi xoa"
    finally:
        shutil.rmtree(d)


# ---------- noi dung tep am thanh ----------
def test_gia_mao_tep_am_thanh():
    d = tempfile.mkdtemp()
    try:
        for name, data in [("elf.mp3", S.BAD_MAGIC["ELF"] + bytes(64)),
                           ("sh.mp3", b"#!/bin/sh" + bytes([10]) + b"echo pwned"),
                           ("zip.mp3", S.BAD_MAGIC["ZIP"] + bytes(64)),
                           ("mz.wav", S.BAD_MAGIC["PE/MZ"] + bytes(64)),
                           ("text.mp3", b"hello, not audio at all")]:
            p = os.path.join(d, name)
            write(p, data)
            expect_reject(S.sniff_audio, p)
    finally:
        shutil.rmtree(d)


def test_chu_ky_id3_gia_nhung_khong_giai_ma_duoc():
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "spoof.mp3")
        write(p, b"ID3" + bytes([3, 0, 0, 0, 0, 0, 0]) + bytes(4096))
        assert S.sniff_audio(p) == ".mp3"
        expect_reject(S.decode_check, p)
    finally:
        shutil.rmtree(d)


def test_mp3_hop_le_qua_tron_quy_trinh():
    d = tempfile.mkdtemp()
    try:
        mp3 = os.path.join(d, "s.mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=2", "-ar", "44100", mp3],
                       check=True, timeout=60)
        data = open(mp3, "rb").read()
        z = make_zip([(zinfo("trainset/ok.mp3"), data)])
        dest = os.path.join(d, "dest")
        out = S.safe_extract(z, z.infolist()[0], dest)
        assert out.startswith(os.path.realpath(dest) + os.sep), out
        assert S.sniff_audio(out) == ".mp3"
        dur = S.decode_check(out)
        assert 1.8 < dur < 2.3, dur
        assert S.sha256_file(out) == hashlib.sha256(data).hexdigest()
    finally:
        shutil.rmtree(d)


# ---------- ngan sach va chinh sach ma nguon ----------
def test_ngan_sach_dung_luong():
    b = S.Budget(100)
    b.take(60)
    expect_reject(b.take, 50)
    b.take(40)
    assert b.used == 100


def test_ma_nguon_safe_fetch_khong_dung_ham_nguy_hiem():
    src = open(S.__file__, encoding="utf-8").read()
    for bad in ["extractall", "eval(", "exec(", "shell=True", "pickle", "os.system", "__import__"]:
        assert bad not in src, bad


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for n, f in tests:
        try:
            f()
            print("PASS", n)
        except Exception as e:
            fails += 1
            print("FAIL", n, "|", type(e).__name__, str(e)[:200])
    print(f"{len(tests) - fails}/{len(tests)} PASS")
    sys.exit(1 if fails else 0)
