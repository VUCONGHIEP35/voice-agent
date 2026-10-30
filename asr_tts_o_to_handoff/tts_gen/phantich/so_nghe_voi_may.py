# -*- coding: utf-8 -*-
"""Đối chiếu phiếu nghe của người (nghe_thu_A.xlsx, sheet "Nghe") với từng cấu hình ASR trong gate_hop*.csv.

Chạy (từ tts_gen/):
  .venv/Scripts/python -m phantich.so_nghe_voi_may runs/ket_qua_A/runs/eval1000_A --gate gate_hop_z.csv --out reports/eval1000_A_zip/so_nghe.md
Đọc xlsx bằng zipfile + regex (không cần openpyxl; chỉ đọc sharedStrings và sheet2), lấy cột "Bạn nghe: đúng?" (Đúng/Sai/
Không chắc), "Nhóm", "Mã câu" (utt_id). Mỗi cấu hình: "máy đạt" = cấu hình đó qua ngưỡng (câu <= 3 âm tiết: CER = 0, như
gate_union.passes). Bảng: người Đúng/Sai × máy đạt/không; hai lỗi cần chú ý: máy đạt mà người nghe Sai (máy dễ dãi, có thể
do mô hình ngôn ngữ trong ASR tự "sửa" âm thanh sai) và máy không đạt mà người nghe Đúng (máy khắt khe).
Giới hạn: một người nghe, không mù hoàn toàn (xem ghi chú trong phiếu); câu "Không chắc" không tính vào bảng chính.
"""
import argparse
import collections
import csv
import os
import re
import zipfile

from thuvien.luat_cham import CONFIGS, passes  # noqa: E402

MAX_XML = 20 * 2 ** 20


def _read(z, name):
    info = z.getinfo(name)
    if info.file_size > MAX_XML:
        raise SystemExit(f"{name} quá lớn ({info.file_size} byte)")
    return z.read(name).decode("utf-8")


def _unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
            .replace("&amp;", "&"))


def read_sheet(path, sheet="xl/worksheets/sheet2.xml"):
    """[{tên cột ở dòng 1: giá trị}] của một sheet; chuỗi chung và chuỗi inline đều đọc được."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ss = []
        if "xl/sharedStrings.xml" in names:
            for si in re.findall(r"<si>(.*?)</si>", _read(z, "xl/sharedStrings.xml"), re.S):
                ss.append(_unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
        x = _read(z, sheet)
    table = []
    for r in re.finditer(r"<row[^>]*>(.*?)</row>", x, re.S):
        cells = {}
        for c in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', r.group(1), re.S):
            col, attrs, body = c.group(1), c.group(2), c.group(3) or ""
            inline = re.search(r"<t[^>]*>(.*?)</t>", body, re.S)
            v = re.search(r"<v>(.*?)</v>", body, re.S)
            if inline:
                cells[col] = _unescape(inline.group(1))
            elif v:
                cells[col] = ss[int(v.group(1))] if 't="s"' in attrs else _unescape(v.group(1))
        table.append(cells)
    if not table:
        return []
    head = table[0]
    return [{head[k]: row.get(k) for k in head} for row in table[1:]]


def load_gate(path):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["n_syl"] = int(r["n_syl"])
        for c in CONFIGS:
            v = r.get(f"cer_{c}", "")
            r[f"cer_{c}"] = float(v) if v not in ("", None) else ""
    return {r["utt_id"]: r for r in rows}


def compare(listen, gate, configs, thr):
    out = {}
    for c in configs:
        t = collections.Counter()
        for x in listen:
            g = gate.get(x["utt_id"])
            if g is None or x["nguoi"] not in ("Đúng", "Sai"):
                continue
            t[(x["nguoi"], passes(g, c, thr))] += 1
        out[c] = t
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--xlsx", default=None, help="mặc định <run>/nghe_thu_A.xlsx")
    ap.add_argument("--gate", default="gate_hop_z.csv")
    ap.add_argument("--thr", type=float, default=0.10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = read_sheet(a.xlsx or os.path.join(a.run, "nghe_thu_A.xlsx"))
    listen = [dict(utt_id=r["Mã câu"], nguoi=(r.get("Bạn nghe: đúng?") or "").strip(), nhom=r.get("Nhóm") or "",
                   cau=r.get("Câu cần đọc") or "", ghi_chu=" | ".join(x for x in (r.get("Lỗi kỹ thuật"), r.get("Ghi chú")) if x))
              for r in rows if r.get("Mã câu")]
    gate = load_gate(os.path.join(a.run, a.gate))
    miss = [x["utt_id"] for x in listen if x["utt_id"] not in gate]
    configs = [c for c in CONFIGS if any(g[f"cer_{c}"] != "" for g in gate.values())]
    L = [f"# Phiếu nghe so với máy ({os.path.basename(a.run)}, {a.gate}, ngưỡng TẠM {a.thr})", "",
         f"- Câu trong phiếu: {len(listen)}; người nghe: {dict(collections.Counter(x['nguoi'] or '(trống)' for x in listen))}.",
         f"- Câu không tìm thấy trong {a.gate}: {miss or 'không'}.",
         "- Một người nghe, không mù hoàn toàn; câu \"Không chắc\" không vào bảng chính.", "",
         "## Theo cấu hình (chỉ câu người nghe Đúng/Sai)", "",
         "| Cấu hình | Người Đúng, máy đạt | Người Đúng, máy KHÔNG đạt (khắt khe) | Người Sai, máy đạt (DỄ DÃI) | Người Sai, máy không đạt | Khớp người |",
         "|---|---|---|---|---|---|"]
    for c, t in compare(listen, gate, configs, a.thr).items():
        n = sum(t.values())
        agree = t[("Đúng", True)] + t[("Sai", False)]
        L.append(f"| {c} | {t[('Đúng', True)]} | {t[('Đúng', False)]} | {t[('Sai', True)]} | {t[('Sai', False)]} | "
                 f"{agree}/{n} |")
    L += ["", "## Theo nhóm trong phiếu", "", "| Nhóm | n | Đúng | Sai | Không chắc | Kết quả gate_hop có Z |", "|---|---|---|---|---|---|"]
    for nhom in sorted({x["nhom"] for x in listen}):
        xs = [x for x in listen if x["nhom"] == nhom]
        k = collections.Counter(x["nguoi"] for x in xs)
        v = collections.Counter(gate[x["utt_id"]]["ket_qua"] for x in xs if x["utt_id"] in gate)
        L.append(f"| {nhom} | {len(xs)} | {k['Đúng']} | {k['Sai']} | {k['Không chắc']} | {dict(v)} |")
    L += ["", "## Câu người nghe Sai hoặc Không chắc mà có cấu hình cho đạt", "",
          "| utt_id | Người | Cấu hình đạt | Câu | hyp Z | Ghi chú người nghe |", "|---|---|---|---|---|---|"]
    for x in listen:
        g = gate.get(x["utt_id"])
        if g and x["nguoi"] in ("Sai", "Không chắc"):
            ok = [c for c in configs if passes(g, c, a.thr)]
            if ok:
                L.append(f"| {x['utt_id']} | {x['nguoi']} | {'+'.join(ok)} | {x['cau']} | {g.get('hyp_Z', '')} | {x['ghi_chu']} |")
    txt = "\n".join(L) + "\n"
    print(txt)
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)


if __name__ == "__main__":
    main()
