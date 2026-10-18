"""vispeech_sampler.py - lấy mẫu ViSpeech (~50 clip/vùng, trải nhiều người nói) vào samples/<vung>/
và lấy ~15 clip sạch từ VIVOS vào clean_ref/.

Không sửa dữ liệu gốc: chỉ tải, giải nén vào thư mục tạm, rồi CHÉP các clip được chọn.
Cấu trúc metadata của ViSpeech chưa được kiểm chứng, nên mã tự dò file metadata và tên cột.
"""
import hashlib
import io
import os
import random
import re
import shutil
import subprocess
import tarfile
import unicodedata
import zipfile

import pandas as pd
import soundfile as sf

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
META_EXTS = (".csv", ".tsv", ".txt", ".json", ".jsonl", ".parquet", ".xlsx")
REGIONS = ("bac", "trung", "nam")

VISPEECH_FILE_ID = "1-BbOHf42o6eBje2WqQiiRKMtNxmZiRf9"   # từ README của ViSpeech
VIVOS_URL = "https://zenodo.org/records/7068130/files/vivos.tar.gz?download=1"
VIVOS_MD5 = "72972a8b14050f3f11ea7c3debabd7af"           # md5 ghi trên trang Zenodo

ALIASES = {
    "audio_name": ("audio_name", "file_name", "filename", "file", "audio_path", "path", "audio"),
    "dialect": ("dialect", "region", "accent"),
    "speaker": ("speaker", "speaker_id", "spk", "spk_id"),
    "gender": ("gender", "sex"),
}


# ---------------------------------------------------------------- tải và giải nén
def extract_archive(path, dest):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            z.extractall(dest)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as t:
            try:
                t.extractall(dest, filter="data")
            except TypeError:           # Python cũ không có tham số filter
                t.extractall(dest)
    else:
        with open(path, "rb") as f:
            head = f.read(8)
        raise RuntimeError(
            f"Không nhận ra định dạng nén (8 byte đầu: {head!r}). Nếu là .rar hoặc .7z, "
            "cài p7zip (!apt-get -qq install p7zip-full) rồi giải nén bằng lệnh 7z, "
            "sau đó chạy tiếp từ bước dò metadata với extract_dir là thư mục đã giải nén.")


def download_vispeech(raw_dir="/content/vispeech_raw", file_id=VISPEECH_FILE_ID):
    """Tải ViSpeech từ Google Drive về ổ cục bộ của Colab (nhanh, không tốn dung lượng Drive)."""
    import gdown
    os.makedirs(raw_dir, exist_ok=True)
    archive = os.path.join(raw_dir, "vispeech_archive.bin")
    extract_dir = os.path.join(raw_dir, "extracted")
    marker = os.path.join(extract_dir, ".done")
    if os.path.exists(marker):
        print("Đã giải nén sẵn:", extract_dir)
        return extract_dir
    if not os.path.exists(archive):
        out = gdown.download("https://drive.google.com/uc?id=" + file_id, archive, quiet=False)
        if out is None:
            raise RuntimeError("gdown không tải được (thường do Drive giới hạn lượt tải). "
                               "Xem mục 'Lỗi thường gặp' để làm theo cách tải qua Drive của bạn.")
    os.makedirs(extract_dir, exist_ok=True)
    print("Đang giải nén ...")
    try:
        extract_archive(archive, extract_dir)
    except Exception:
        print("Giải nén lỗi. Nếu file tải về bị hỏng, xóa", archive, "rồi chạy lại.")
        raise
    open(marker, "w").close()
    return extract_dir


# ---------------------------------------------------------------- dò cấu trúc
def strip_accents(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def region_of(v):
    """Chuẩn hóa nhãn phương ngữ về bac/trung/nam; không nhận ra thì trả None."""
    s = strip_accents(v).lower().strip()
    if s in ("0", "0.0"):
        return "bac"
    if s in ("1", "1.0"):
        return "trung"
    if s in ("2", "2.0"):
        return "nam"
    for key, reg in (("north", "bac"), ("bac", "bac"), ("central", "trung"),
                     ("trung", "trung"), ("south", "nam"), ("nam", "nam")):
        if key in s:
            return reg
    return None


def set_of(rel_path):
    p = rel_path.lower().replace("\\", "/")
    if "noise" in p:
        return "noise_testset"
    if "clean" in p:
        return "clean_testset"
    if "train" in p:
        return "trainset"
    return "other"


def index_audio(root):
    files = []
    for d, _, names in os.walk(root):
        for n in names:
            if n.lower().endswith(AUDIO_EXTS):
                full = os.path.join(d, n)
                rel = os.path.relpath(full, root)
                files.append({"path": full, "name": n, "stem": os.path.splitext(n)[0],
                              "set": set_of(rel)})
    return files


def describe(root):
    """In cấu trúc để đối chiếu bằng mắt: số file audio theo thư mục và các file nghi là metadata."""
    files = index_audio(root)
    print(f"Tổng số file audio: {len(files)}")
    counts = {}
    for f in files:
        rel = os.path.relpath(os.path.dirname(f["path"]), root)
        top = "/".join(rel.split(os.sep)[:2])
        counts[top] = counts.get(top, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    print("File có thể là metadata:")
    for d, _, names in os.walk(root):
        for n in names:
            if n.lower().endswith(META_EXTS):
                p = os.path.join(d, n)
                print(f"  {os.path.relpath(p, root)}  ({os.path.getsize(p) // 1024} KB)")


def read_table(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".parquet":
        return pd.read_parquet(path)
    if ext == ".xlsx":
        return pd.read_excel(path)
    if ext == ".jsonl":
        return pd.read_json(path, lines=True)
    if ext == ".json":
        try:
            return pd.read_json(path)
        except ValueError:
            return pd.read_json(path, lines=True)
    return pd.read_csv(path, sep=None, engine="python")


def load_metadata(root):
    cands = []
    for d, _, names in os.walk(root):
        for n in names:
            if n.lower().endswith(META_EXTS):
                p = os.path.join(d, n)
                rel = os.path.relpath(p, root).lower()
                if "metadata" in rel:
                    cands.append(p)
    if not cands:   # không thấy thư mục metadata: thử mọi file bảng nhỏ
        for d, _, names in os.walk(root):
            for n in names:
                p = os.path.join(d, n)
                if n.lower().endswith(META_EXTS) and os.path.getsize(p) < 50_000_000:
                    cands.append(p)
    frames, diag = [], []
    for p in sorted(cands):
        try:
            t = read_table(p)
        except Exception as e:
            diag.append((p, f"không đọc được: {e}"))
            continue
        cols = {str(c).strip().lower(): c for c in t.columns}
        pick = {}
        for key, names in ALIASES.items():
            for nm in names:
                if nm in cols:
                    pick[key] = cols[nm]
                    break
        diag.append((p, list(t.columns)))
        if not {"audio_name", "dialect", "speaker"} <= set(pick):
            continue
        sub = pd.DataFrame({k: t[v] for k, v in pick.items()})
        if "gender" not in sub:
            sub["gender"] = ""
        sub["meta_file"] = os.path.relpath(p, root)
        frames.append(sub)
    if not frames:
        print("Không file nào có đủ 3 cột audio_name, dialect, speaker. Các file đã thử:")
        for p, c in diag:
            print(" ", os.path.relpath(p, root), "->", c)
        raise RuntimeError("Không dò được metadata. Gửi lại phần in ở trên để chỉnh ALIASES.")
    return pd.concat(frames, ignore_index=True)


def _name(v):
    if isinstance(v, dict):
        v = v.get("path") or v.get("name")
    return os.path.basename(str(v).replace("\\", "/"))


def build_table(root):
    """Ghép metadata với file audio thật. Trả về bảng: path, name, speaker, gender, region, set."""
    files = index_audio(root)
    meta = load_metadata(root)
    meta["region"] = meta["dialect"].map(region_of)
    unknown = sorted(set(meta.loc[meta.region.isna(), "dialect"].astype(str)))
    if unknown:
        raise RuntimeError(f"Có nhãn dialect chưa nhận ra: {unknown}. Thêm vào hàm region_of.")
    vals = set(meta["dialect"].astype(str))
    if vals <= {"0", "1", "2", "0.0", "1.0", "2.0"}:
        print("Lưu ý: dialect là số; giả định 0=bac, 1=trung, 2=nam theo README (dialect = số % 3).")

    by_name, by_stem = {}, {}
    for f in files:
        by_name.setdefault(f["name"].lower(), []).append(f)
        by_stem.setdefault(f["stem"].lower(), []).append(f)

    rows, missing = [], 0
    for r in meta.itertuples(index=False):
        key = _name(r.audio_name).lower()
        cands = by_name.get(key) or by_stem.get(os.path.splitext(key)[0]) or []
        if not cands:
            missing += 1
            continue
        hint = set_of(r.meta_file)
        best = next((c for c in cands if c["set"] == hint), cands[0])
        rows.append({"path": best["path"], "name": best["name"], "speaker": str(r.speaker),
                     "gender": str(r.gender), "region": r.region, "set": best["set"]})
    tab = pd.DataFrame(rows).drop_duplicates("path")
    print(f"Dòng metadata: {len(meta)}; ghép được với file audio: {len(tab)}; không thấy file: {missing}")
    if tab.empty:
        raise RuntimeError("Không ghép được dòng metadata nào với file audio. Kiểm tra cột audio_name.")
    print(tab.groupby(["region", "set"]).agg(clips=("path", "count"), speakers=("speaker", "nunique")))
    return tab


# ---------------------------------------------------------------- chọn mẫu
_dur_cache = {}


def duration_s(path):
    if path in _dur_cache:
        return _dur_cache[path]
    d = float("nan")
    try:
        d = float(sf.info(path).duration)
    except Exception:
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "default=nw=1:nk=1", path],
                                 capture_output=True, text=True, check=True)
            d = float(out.stdout.strip())
        except Exception:
            pass
    _dur_cache[path] = d
    return d


def _safe_id(s):
    return re.sub(r"[^0-9A-Za-z\-]", "-", str(s)) or "unk"   # không chứa dấu gạch dưới


def sample_regions(tab, out_dir="samples", n_per_region=50, clips_per_speaker=3,
                   min_dur=3.0, max_dur=8.0, exclude_sets=("noise_testset",),
                   seed=42, force=False, manifest="samples_manifest.csv"):
    """Mỗi vùng: chọn ngẫu nhiên các người nói, mỗi người đúng clips_per_speaker clip dài
    min_dur..max_dur giây, cho tới khi đủ ~n_per_region. Tên file đích: <nguoi_noi>_<ten_goc>."""
    rng = random.Random(seed)
    tab = tab[~tab["set"].isin(exclude_sets)]
    print("Tập bị loại:", list(exclude_sets), "| còn lại", len(tab), "clip")
    rows = []
    for region in REGIONS:
        dest = os.path.join(out_dir, region)
        os.makedirs(dest, exist_ok=True)
        have = [f for f in os.listdir(dest) if f.lower().endswith(AUDIO_EXTS)]
        if have and not force:
            print(f"[{region}] đã có {len(have)} file, bỏ qua (đặt force=True để chọn lại).")
            continue
        if have and force:
            for f in have:
                os.remove(os.path.join(dest, f))
        d = tab[tab.region == region]
        groups = {s: g.sample(frac=1, random_state=seed) for s, g in d.groupby("speaker")}
        speakers = list(groups)
        rng.shuffle(speakers)
        full, partial = [], []
        n_full = 0
        for spk in speakers:
            got = []
            for r in groups[spk].itertuples(index=False):
                dur = duration_s(r.path)
                if dur == dur and min_dur <= dur <= max_dur:
                    got.append((r, dur))
                    if len(got) == clips_per_speaker:
                        break
            if len(got) == clips_per_speaker:
                full.append((spk, got))
                n_full += len(got)
                if n_full >= n_per_region:
                    break
            elif got:
                partial.append((spk, got))
        chosen = full[:]
        total = sum(len(g) for _, g in chosen)
        for item in partial:            # thiếu mới lấy thêm người có ít clip hơn
            if total >= n_per_region:
                break
            chosen.append(item)
            total += len(item[1])
        for spk, got in chosen:
            for r, dur in got:
                new = f"{_safe_id(spk)}_{os.path.splitext(r.name)[0]}{os.path.splitext(r.name)[1].lower()}"
                shutil.copy2(r.path, os.path.join(dest, new))
                rows.append({"file": os.path.join(dest, new), "region": region, "speaker": spk,
                             "gender": r.gender, "set": r.set, "dur_s": round(dur, 2), "src": r.path})
        flag = "" if total >= 0.9 * n_per_region else "  <-- THIẾU, nới min_dur/max_dur hoặc giảm clips_per_speaker"
        print(f"[{region}] {total} clip từ {len(chosen)} người nói{flag}")
    man = pd.DataFrame(rows)
    if len(man):
        man.to_csv(manifest, index=False)
        print("Đã ghi", manifest)
    return man


# ---------------------------------------------------------------- clean_ref từ VIVOS
def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def make_clean_ref(out_dir="clean_ref", n=16, clips_per_speaker=2, min_dur=3.0, max_dur=8.0,
                   work_dir="/content/vivos_raw", url=VIVOS_URL, md5=VIVOS_MD5, archive=None):
    """Lấy n clip VIVOS (đọc câu, phòng yên tĩnh) trải nhiều người nói, đọc thẳng từ file nén
    và dừng sớm khi đủ. VIVOS: CC BY-NC-SA 4.0, chỉ dùng học thuật."""
    os.makedirs(out_dir, exist_ok=True)
    have = [f for f in os.listdir(out_dir) if f.lower().endswith(AUDIO_EXTS)]
    if have:
        print(f"{out_dir} đã có {len(have)} file, bỏ qua.")
        return have
    if archive is None:
        os.makedirs(work_dir, exist_ok=True)
        archive = os.path.join(work_dir, "vivos.tar.gz")
        if not os.path.exists(archive):
            subprocess.run(["wget", "-q", "--show-progress", "-c", "-O", archive, url], check=True)
        got = _md5(archive)
        print("md5:", got, "(khớp)" if got == md5 else f"(KHÔNG khớp {md5}; file có thể hỏng)")
    per_spk, saved = {}, []
    with tarfile.open(archive) as t:
        for m in t:
            if not (m.isfile() and m.name.lower().endswith(".wav")):
                continue
            spk = os.path.basename(os.path.dirname(m.name))
            if per_spk.get(spk, 0) >= clips_per_speaker:
                continue
            data = t.extractfile(m).read()
            try:
                dur = sf.info(io.BytesIO(data)).duration
            except Exception:
                continue
            if not (min_dur <= dur <= max_dur):
                continue
            base = os.path.basename(m.name)
            new = base if base.startswith(_safe_id(spk) + "_") else f"{_safe_id(spk)}_{base}"
            with open(os.path.join(out_dir, new), "wb") as f:
                f.write(data)
            per_spk[spk] = per_spk.get(spk, 0) + 1
            saved.append(new)
            if len(saved) >= n:
                break
    print(f"Đã lưu {len(saved)} clip từ {len(per_spk)} người nói vào {out_dir}")
    return saved