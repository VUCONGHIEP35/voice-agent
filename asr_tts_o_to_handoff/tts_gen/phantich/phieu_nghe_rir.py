# -*- coding: utf-8 -*-
"""Phiếu nghe thử kho RIR (docs/ke_hoach_RIR_v1.md bước 3; dùng lại ở v3): 5 câu × 20 RIR mỗi loại xe, kèm bản sạch để so.

Chạy (từ tts_gen/, venv_rir: cần numpy, scipy, soundfile, openpyxl):
  python -m phantich.phieu_nghe_rir --kho runs/rir_v2/thu/kho --out runs/rir_v2/thu/nghe
Chọn (tất định theo băm, không nhìn chỉ số âm học):
  câu  5 câu thường đạt luật v1: 2 Bắc, 2 Nam, 1 Trung (vùng của giọng), mỗi câu một độ dài khác nhau nếu được.
  RIR  mỗi loại xe 20 RIR đạt, đi vòng qua các cặp (ghế, micro) để phủ đủ ghế sau và cả 4 micro.
Mỗi câu chập với mọi RIR của loại xe bằng đúng hàm của bước chập (thuvien.rir.xu_ly_ban): 100 tệp mỗi loại xe ở
<out>/am_thanh/<loại xe>/, bản sạch cùng mức ở <out>/sach/. Phiếu <out>/nghe_thu_rir.xlsx (liên kết tương đối, nên để
phiếu cùng thư mục với am_thanh/, sach/). Đợt 1 = mỗi loại xe 10 bản (lái 4, phụ 2, sau 4; mỗi câu tối đa 2; 70 bản
với 7 loại của v3),
còn lại đợt 2.
Các cột máy (EDT, DRR, C50, mã RIR, khoang) bị gập để người nghe không bị dẫn dắt.
"""
import argparse
import collections
import json
import os

import numpy as np

import cauhinh.tang_cuong as C
from buoc.rir_chap import lay_rir
from buoc.rir_gan import doc_dau_vao
from cauhinh.duong_dan import GOC
from thuvien.am_thanh import write_flac
from thuvien.chon_cau import h32
from thuvien.rir import xu_ly_ban

SO_CAU = {"Bắc": 2, "Nam": 2, "Trung": 1}
RIR_MOI_LOAI = 20
DOT1_NHOM_GHE = {"lai": 4, "phu": 2, "sau": 4}      # 10 bản mỗi loại xe ở đợt 1


def chon_cau(inp):
    out, dai = [], set()
    for vung, n in SO_CAU.items():
        pool = sorted((f for f in inp if f["phan"] == "thuong" and f["vung"] == vung), key=lambda f: h32("nghe_rir", f["utt_id"]))
        got = []
        for f in pool:                       # lượt 1: độ dài chưa có; lượt 2: bất kỳ
            if len(got) < n and f["length_class"] not in dai:
                got.append(f)
                dai.add(f["length_class"])
        for f in pool:
            if len(got) < n and f not in got:
                got.append(f)
        out += got
    return out


def chon_rir(rir_rows, loai):
    cells = collections.defaultdict(list)
    for r in sorted((r for r in rir_rows if r["loai_xe"] == loai and r["dat"]), key=lambda r: h32("nghe_rir", r["rir_id"])):
        cells[(r["ghe"], r["micro"])].append(r)
    order = sorted(cells, key=lambda k: h32("o", loai, *k))
    got = []
    while len(got) < RIR_MOI_LOAI and any(cells[k] for k in order):
        for k in order:
            if len(got) < RIR_MOI_LOAI and cells[k]:
                got.append(cells[k].pop(0))
    return got


def chon_dot1(items):
    """Mỗi loại xe DOT1_MOI_LOAI bản theo hạn ngạch nhóm ghế; mỗi câu tối đa 2 bản, mỗi RIR một bản."""
    out = []
    for loai in C.LOAI_XE:
        xs = sorted((it for it in items if it["rir"]["loai_xe"] == loai), key=lambda it: h32("dot1", it["ten"]))
        chosen, dung_rir, theo_cau, theo_nhom = [], set(), collections.Counter(), collections.Counter()
        for it in xs:
            nhom = "sau" if it["rir"]["ghe"].startswith("sau") else it["rir"]["ghe"]
            if (theo_nhom[nhom] < DOT1_NHOM_GHE[nhom] and it["rir"]["rir_id"] not in dung_rir
                    and theo_cau[it["cau"]["utt_id"]] < 2):
                chosen.append(it)
                dung_rir.add(it["rir"]["rir_id"])
                theo_cau[it["cau"]["utt_id"]] += 1
                theo_nhom[nhom] += 1
        out += chosen
    return out


def ghi_xlsx(path, items):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    hd = wb.active
    hd.title = "Hướng dẫn"
    lines = [
        ("Nghe thử kho RIR mô phỏng (khoang xe, pyroomacoustics)", True),
        (f"{len(items)} bản: 5 câu × 20 RIR × 4 loại xe. Đợt 1 ({sum(i['dot'] == 1 for i in items)} bản, khoảng 15 phút) là bắt buộc; "
         "đợt 2 tùy chọn.", False),
        ("Cách nghe", True),
        ("1. Sheet \"Nghe\": bấm \"▶ Vang\" rồi \"▶ Sạch\" để so (phiếu phải nằm cạnh thư mục am_thanh/ và sach/). Nên dùng tai nghe.", False),
        ("2. \"Giống trong xe?\": Giống xe / Vang quá (như phòng lớn, nhà tắm) / Khô quá (như không có vang) / Không chắc.", False),
        ("3. \"Tiếng lạ\": Không / Kim loại (tiếng ống, hộp thiếc) / Click hoặc lụp bụp / Lặp, vọng.", False),
        ("4. \"Nghe rõ lời?\": Rõ / Hơi khó / Khó.", False),
        ("5. CHƯA mở các cột bị gập bên phải cho tới khi xong (đó là chỉ số máy đo).", False),
        ("Giới hạn", True),
        ("RIR mô phỏng trong hộp chữ nhật (không có ghế, táp-lô); chưa hiệu chỉnh với xe thật. Một người nghe, chỉ để định hướng.", False),
    ]
    for t, bold in lines:
        hd.append([t])
        hd.cell(hd.max_row, 1).font = Font(bold=bold, size=12 if bold else 11)
        hd.cell(hd.max_row, 1).alignment = Alignment(wrap_text=True)
    hd.column_dimensions["A"].width = 120
    hd.append([])
    hd.append(["Tổng hợp (tự cập nhật)"])
    hd.cell(hd.max_row, 1).font = Font(bold=True, size=12)
    head = ["Loại xe", "Số bản", "Đã nghe", "Giống xe", "Vang quá", "Khô quá", "Có tiếng lạ", "Khó nghe"]
    hd.append(head)
    for i in range(1, len(head) + 1):
        hd.cell(hd.max_row, i).font = Font(bold=True)
    for loai in C.LOAI_XE:
        q = f'"{loai}"'
        hd.append([loai, f"=COUNTIF(Nghe!$C:$C,{q})", f'=COUNTIFS(Nghe!$C:$C,{q},Nghe!$I:$I,"<>")',
                   *[f'=COUNTIFS(Nghe!$C:$C,{q},Nghe!$I:$I,"{v}")' for v in ("Giống xe", "Vang quá", "Khô quá")],
                   f'=COUNTIFS(Nghe!$C:$C,{q},Nghe!$J:$J,"<>Không",Nghe!$J:$J,"<>")',
                   f'=COUNTIFS(Nghe!$C:$C,{q},Nghe!$K:$K,"Khó")'])
    ws = wb.create_sheet("Nghe")
    cols = [("STT", 5), ("Đợt", 5), ("Loại xe", 8), ("Ghế", 9), ("Micro", 8), ("Vang", 8), ("Sạch", 8), ("Câu", 44),
            ("Giống trong xe?", 13), ("Tiếng lạ", 13), ("Nghe rõ lời?", 11), ("Ghi chú", 26), ("_", 2),
            ("EDT (s)", 8), ("DRR (dB)", 8), ("C50 (dB)", 8), ("Khoang", 9), ("Mã RIR", 32), ("Mã câu", 34), ("Giọng", 12)]
    ws.append([c for c, _ in cols])
    for i, (_, w) in enumerate(cols, 1):
        c = ws.cell(1, i)
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[c.column_letter].width = w
    fill = PatternFill("solid", fgColor="FFF2CC")
    for k, it in enumerate(items, 1):
        r, f = it["rir"], it["cau"]
        ws.append([k, it["dot"], r["loai_xe"], r["ghe"], r["micro"], "▶ Vang", "▶ Sạch", f["text_raw"], "", "", "", "", "",
                   r["edt_s"], r["drr_db"], r["c50_db"], r["khoang"], r["rir_id"], f["utt_id"], f["voice"]])
        for col, rel in ((6, it["tep"]), (7, it["sach"])):
            c = ws.cell(k + 1, col)
            c.hyperlink = rel.replace("/", "\\")
            c.font = Font(color="0563C1", underline="single")
        for col in (9, 10, 11, 12):
            ws.cell(k + 1, col).fill = fill
        ws.cell(k + 1, 8).alignment = Alignment(wrap_text=True, vertical="top")
    n = len(items) + 1
    for rng, opts in ((f"I2:I{n}", "Giống xe,Vang quá,Khô quá,Không chắc"), (f"J2:J{n}", "Không,Kim loại,Click,Lặp/vọng"),
                      (f"K2:K{n}", "Rõ,Hơi khó,Khó")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(rng)
    ws.column_dimensions.group("M", "T", hidden=True, outline_level=1)
    ws.freeze_panes = "F2"
    ws.auto_filter.ref = f"A1:T{n}"
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kho", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs-goc", default=os.path.join(GOC, "runs"))
    a = ap.parse_args()
    import soundfile as sf
    with open(os.path.join(a.kho, "rir_manifest.jsonl"), encoding="utf-8") as f:
        rir_rows = [json.loads(x) for x in f if x.strip()]
    cau = chon_cau(doc_dau_vao(a.runs_goc))
    items = []
    os.makedirs(os.path.join(a.out, "sach"), exist_ok=True)
    for f in cau:
        x, sr = sf.read(os.path.join(a.runs_goc, f["run"], f["audio16"]), dtype="float32")
        f["_x"] = np.asarray(x, dtype=np.float64)
        y, _ = xu_ly_ban(f["_x"], None)
        f["_sach"] = f"sach/{f['utt_id']}.flac"
        write_flac(os.path.join(a.out, f["_sach"]), y, C.SR)
    for loai in C.LOAI_XE:
        os.makedirs(os.path.join(a.out, "am_thanh", loai), exist_ok=True)
        for r in chon_rir(rir_rows, loai):
            h = lay_rir(a.kho, r)
            for f in cau:
                y, _ = xu_ly_ban(f["_x"], h, r["tre_truc_tiep"])
                ten = f"{r['rir_id']}__{f['utt_id']}"
                rel = f"am_thanh/{loai}/{ten}.flac"
                write_flac(os.path.join(a.out, rel), y, C.SR)
                items.append(dict(ten=ten, tep=rel, sach=f["_sach"], rir=r, cau={k: v for k, v in f.items() if not k.startswith("_")}))
    dot1 = {it["ten"] for it in chon_dot1(items)}
    for it in items:
        it["dot"] = 1 if it["ten"] in dot1 else 2
    items.sort(key=lambda it: (it["dot"], h32("tron", it["ten"])))
    path = os.path.join(a.out, "nghe_thu_rir.xlsx")
    ghi_xlsx(path, items)
    with open(os.path.join(a.out, "nghe_thu_rir.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for it in items:
            f.write(json.dumps(dict(dot=it["dot"], tep=it["tep"], sach=it["sach"], rir_id=it["rir"]["rir_id"],
                                    utt_id=it["cau"]["utt_id"]), ensure_ascii=False) + "\n")
    print(f"{len(items)} bản -> {path}")
    print("Câu:", [(f["utt_id"], f["vung"], f["length_class"]) for f in cau])
    print("Đợt 1 theo loại xe × ghế:", dict(collections.Counter((it["rir"]["loai_xe"], it["rir"]["ghe"]) for it in items if it["dot"] == 1)))


if __name__ == "__main__":
    main()
