# -*- coding: utf-8 -*-
"""Góp ý v1 mục 5: đồng bộ data/du_lieu_asr_tts_o_to_v0.3.xlsx với quy tắc linh (Bắc) / lẻ (Trung, Nam).

Sửa thẳng XML trong file xlsx (không mở-lưu bằng openpyxl) để giữ nguyên công thức, giá trị đã tính, định dạng, kiểm dữ liệu:
  - Tu_dia_phuong, dòng 'số 105': Bắc = một trăm linh năm; Trung = một trăm lẻ năm; Nam = một trăm lẻ năm.
  - Mau_cau, hai câu M4 CS07 'Số 105 có đúng không?': câu gắn Bắc đọc 'linh', câu gắn Nam đọc 'lẻ'
    (đổi chỗ hai chuỗi text_spoken; số âm tiết không đổi nên giá trị tính sẵn vẫn đúng).
Cặp 'Giá 1.200 đồng' (nghìn Bắc / ngàn Nam) vốn đã đúng, không sửa.
Chạy: py -3.13 fix_xlsx_105.py <đường dẫn xlsx>   (in ra thay đổi; chạy lại lần hai không đổi gì)
"""
import re, shutil, sys, zipfile, os
from xml.sax.saxutils import escape

P = sys.argv[1]
z = zipfile.ZipFile(P)
files = {n: z.read(n) for n in z.namelist()}
infos = {i.filename: i for i in z.infolist()}
z.close()

ss_xml = files["xl/sharedStrings.xml"].decode("utf-8")
sis = re.findall(r"<si>.*?</si>", ss_xml, flags=re.S)


def si_text(si):
    return "".join(re.findall(r"<t[^>]*>(.*?)</t>", si, flags=re.S))


strings = [si_text(s) for s in sis]


def idx_of(text):
    """chỉ số chuỗi dùng chung; thêm mới nếu chưa có."""
    global ss_xml
    t = escape(text)
    if t in strings:
        return strings.index(t)
    strings.append(t)
    ss_xml = re.sub(r"</sst>", f"<si><t>{t}</t></si></sst>", ss_xml)
    return len(strings) - 1


wb = files["xl/workbook.xml"].decode("utf-8")
rels = files["xl/_rels/workbook.xml.rels"].decode("utf-8")


def sheet_path(name):
    rid = re.search(r'<sheet [^>]*name="' + re.escape(name) + r'"[^>]*r:id="(rId\d+)"', wb).group(1)
    tgt = re.search(r'Id="' + rid + r'"[^>]*Target="([^"]+)"', rels) or re.search(r'Target="([^"]+)"[^>]*Id="' + rid + '"', rels)
    t = tgt.group(1).lstrip("/")
    return t if t.startswith("xl/") else "xl/" + t


def get_cell(xml, ref):
    m = re.search(r'<c r="' + ref + r'"([^>]*?)(/>|>(.*?)</c>)', xml, flags=re.S)
    return m


def set_cell_str(xml, ref, sidx):
    m = get_cell(xml, ref)
    if m:
        attrs = re.sub(r'\s*t="[^"]*"', "", m.group(1))
        new = f'<c r="{ref}"{attrs} t="s"><v>{sidx}</v></c>'
        return xml[:m.start()] + new + xml[m.end():]
    # ô chưa có: chèn vào dòng theo thứ tự cột
    row = re.match(r"[A-Z]+(\d+)", ref).group(1)
    rm = re.search(r'<row r="' + row + r'"[^>]*>(.*?)</row>', xml, flags=re.S)
    cells = list(re.finditer(r'<c r="([A-Z]+)' + row + r'"', rm.group(0)))
    col = re.match(r"[A-Z]+", ref).group(0)
    pos = rm.end() - len("</row>")
    for c in cells:
        if (len(c.group(1)), c.group(1)) > (len(col), col):
            pos = rm.start() + c.start()
            break
    return xml[:pos] + f'<c r="{ref}" t="s"><v>{sidx}</v></c>' + xml[pos:]


def cell_text(xml, ref):
    m = get_cell(xml, ref)
    if not m or not m.group(3):
        return None
    v = re.search(r"<v>(.*?)</v>", m.group(3))
    return strings[int(v.group(1))] if v and 't="s"' in m.group(1) else (v.group(1) if v else None)


changes = []
# --- Tu_dia_phuong
tp = sheet_path("Tu_dia_phuong")
x = files[tp].decode("utf-8")
row = next(r for r in range(1, 60) if cell_text(x, f"B{r}") == "số 105")
want = {"C": "một trăm linh năm", "D": "một trăm lẻ năm", "E": "một trăm lẻ năm"}
for col, val in want.items():
    old = cell_text(x, f"{col}{row}")
    if old != val:
        x = set_cell_str(x, f"{col}{row}", idx_of(val))
        changes.append(f"Tu_dia_phuong!{col}{row}: {old!r} -> {val!r}")
files[tp] = x.encode("utf-8")
# --- Mau_cau
mp = sheet_path("Mau_cau")
x = files[mp].decode("utf-8")
for r in range(1, 200):
    if cell_text(x, f"G{r}") == "Số 105 có đúng không?":
        lex = cell_text(x, f"K{r}")
        val = "Số một trăm linh năm có đúng không?" if lex == "Bắc" else "Số một trăm lẻ năm có đúng không?"
        old = cell_text(x, f"H{r}")
        if old != val:
            x = set_cell_str(x, f"H{r}", idx_of(val))
            changes.append(f"Mau_cau!H{r} ({lex}): {old!r} -> {val!r}")
files[mp] = x.encode("utf-8")

if not changes:
    print("Không có gì cần sửa.")
    sys.exit(0)
# cập nhật số chuỗi trong sst
cnt = len(re.findall(r"<si>", ss_xml))
ss_xml = re.sub(r'uniqueCount="\d+"', f'uniqueCount="{cnt}"', ss_xml)
files["xl/sharedStrings.xml"] = ss_xml.encode("utf-8")
tmp = P + ".tmp"
with zipfile.ZipFile(tmp, "w") as zo:
    for n, data in files.items():
        zo.writestr(infos[n], data, compress_type=zipfile.ZIP_DEFLATED)
shutil.move(tmp, P)
print("\n".join(changes))
