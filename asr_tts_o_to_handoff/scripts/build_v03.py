# -*- coding: utf-8 -*-
import json, sys
sys.path.insert(0, ".")
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
import data_def as D
import taxonomy_def as TX
import data_v03 as V

OUT_XLSX = "../out/du_lieu_asr_tts_o_to_v0.3.xlsx"
OUT_JSONL = "../out/du_lieu_asr_tts_o_to_v0.3.jsonl"

F = "Arial"
f_norm = Font(name=F, size=10)
f_bold = Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=14, bold=True)
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
f_input = Font(name=F, size=10, color="0000FF")
f_link = Font(name=F, size=10, color="008000")
f_note = Font(name=F, size=9, italic=True, color="595959")
fill_req = PatternFill("solid", fgColor="1F3864")
fill_opt = PatternFill("solid", fgColor="7F7F7F")
fill_calc = PatternFill("solid", fgColor="548235")
fill_sec = PatternFill("solid", fgColor="D9E1F2")
fill_input = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")
center_wrap = Alignment(wrap_text=True, vertical="center", horizontal="center")
center = Alignment(horizontal="center", vertical="top")


def head(ws, title, note):
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = f_title
    ws["A2"] = note
    ws["A2"].font = f_note


def table(ws, r0, headers, rows, widths, fills=None, center_cols=()):
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=r0, column=j, value=h)
        c.font = f_head
        c.fill = fills[j - 1] if fills else fill_req
        c.alignment = center_wrap
        c.border = border
    for i, r in enumerate(rows, r0 + 1):
        for j, v in enumerate(r, 1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = f_norm
            c.alignment = center if j in center_cols else wrap
            c.border = border
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[L(j)].width = w
    ws.freeze_panes = ws.cell(row=r0 + 1, column=1)


def mark_input(c):
    c.font = f_input
    c.fill = fill_input


# ------------------------------------------------------------------ kiểm tra mã yếu tố
FR = V.factor_rows()
CODES = {r[2] for r in FR}
assert len(FR) == 71


def codes_in(s):
    return [x.strip() for x in s.split(";") if x.strip()]


for c in V.CASES:
    for k in codes_in(c[8]):
        assert k in CODES, (c[0], k)
for r in V.M_ROWS:
    for k in codes_in(r["factors"]):
        assert k in CODES, (r["case"], k)
for t in V.TEMPLATES:
    for k in codes_in(t[8]):
        assert k in CODES, (t[0], k)
for cs, d in V.MATRIX.items():
    for k in d:
        assert k in CODES, (cs, k)
for k in V.MATRIX_COLS:
    assert k in CODES, k
CASE_IDS = [c[0] for c in V.CASES]

wb = Workbook()
NR_Y = len(FR)             # 71
Y0, Y1 = 4, 3 + NR_Y       # Yeu_to data rows
MC1 = 300                  # Mau_cau last row used in ranges
RATE = "Tong_quan!$B$40"

# ------------------------------------------------------------------ Tu_vung
LISTS = {
    "muc_dich": [p[0] for p in V.PURPOSES],
    "speech_act": V.ACTS,
    "lexicon_variant": V.LEXV,
    "speaker_region": V.REGV,
    "speaker_state": V.STATES,
    "language_mix": ["Việt", "Việt + Anh"],
    "buoc": V.STAGES,
    "asr_lien_quan": ["Có", "Một phần", "Hầu như không"],
    "vung_3": ["Bắc", "Trung", "Nam"],
    "gender": D.VOCAB["gender"],
    "age_group": D.VOCAB["age_group"],
    "tieu_vung": D.VOCAB["region_dialect"],
    "f0_band": D.VOCAB["f0_band"],
    "voice_quality": D.VOCAB["voice_quality"],
    "ho_so_status": ["Ví dụ", "Đã chọn", "Đã kiểm", "Loại"],
    "kiem": ["Chưa", "Đạt", "Không đạt"],
    "case_id": CASE_IDS,
}
LCOL = {k: L(i + 1) for i, k in enumerate(LISTS)}
LLEN = {k: len(v) for k, v in LISTS.items()}


def dv(ws, rng, key):
    d = DataValidation(type="list", formula1=f"=Tu_vung!${LCOL[key]}$2:${LCOL[key]}${LLEN[key] + 1}", allow_blank=True)
    d.error = "Chọn giá trị trong danh sách (sheet Tu_vung)."
    ws.add_data_validation(d)
    d.add(rng)


# ------------------------------------------------------------------ Tong_quan
ws = wb.active
ws.title = "Tong_quan"
head(ws, "Bộ dữ liệu mẫu để sinh giọng nói trong xe cho huấn luyện ASR tiếng Việt – phiên bản 0.3",
     "12/10/2026. Viết lại từ bản 0.2: tách case study theo mục đích dữ liệu và gắn mỗi yếu tố ảnh hưởng với bước xử lý đã trao đổi.")
for col, w in zip("ABCD", (30, 90, 18, 40)):
    ws.column_dimensions[col].width = w


def sec(r, text):
    c = ws.cell(row=r, column=1, value=text)
    c.font = f_bold
    for j in range(1, 5):
        ws.cell(row=r, column=j).fill = fill_sec


def line(r, a, b):
    ws.cell(row=r, column=1, value=a).font = f_bold
    c = ws.cell(row=r, column=2, value=b)
    c.font = f_norm
    c.alignment = wrap
    ws.cell(row=r, column=1).alignment = wrap


sec(4, "TRẢ LỜI CÂU HỎI: BỘ MẪU CÂU CÓ PHẢI ĐÁP ỨNG CÁC YẾU TỐ ẢNH HƯỞNG KHÔNG?")
line(5, "Có, nhưng chỉ một phần",
     "Bộ mẫu câu phải đáp ứng các yếu tố mà chính câu quyết định (số, địa chỉ, tên riêng, từ vùng, câu cụt, độ dài...). "
     "Các yếu tố còn lại do bước khác xử lý: chọn giọng, điều khiển TTS, trộn nhiễu sau TTS, hoặc chỉ đo ở bộ đánh giá. Sheet Buoc_xu_ly và Yeu_to cho biết yếu tố nào ở bước nào.")
ws["A6"] = "Số yếu tố do câu quyết định (bước 1)"
ws["A6"].font = f_bold
ws["B6"] = f'=COUNTIF(Yeu_to!$G${Y0}:$G${Y1},"1.*")'
ws["A7"] = "Số yếu tố do bước khác quyết định"
ws["A7"].font = f_bold
ws["B7"] = f'=COUNTA(Yeu_to!$C${Y0}:$C${Y1})-B6'
ws["A8"] = "Tổng số yếu tố"
ws["A8"].font = f_bold
ws["B8"] = f"=COUNTA(Yeu_to!$C${Y0}:$C${Y1})"
for r in (6, 7, 8):
    ws.cell(row=r, column=2).font = f_norm
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="left")

sec(10, "QUY TRÌNH TỔNG QUÁT")
pipe = [
    ("1", "Chọn giọng thật sạch từ bộ dữ liệu có nhãn vùng (Bắc, Trung, Nam) và chọn đoạn tham chiếu."),
    ("2", "Clone hoặc tinh chỉnh TTS (zero-shot trước; tinh chỉnh theo vùng nếu giọng vùng bị kéo về giọng chuẩn). Mục tiêu của TTS là sinh dữ liệu, không phải huấn luyện ASR."),
    ("3", "Sinh câu của người dùng trong xe (M1, M2) và tập đối chiếu ngoài miền xe (M3) bằng cùng giọng, dạng âm thanh sạch."),
    ("4", "Trộn nhiễu xe thật, đáp ứng xung khoang xe, giọng người khác, nhạc; đặt SNR; ghi lại nguồn ồn."),
    ("5", "Huấn luyện ASR bằng dữ liệu thật ngoài miền xe cộng dữ liệu sinh đã trộn nhiễu."),
    ("6", "Đánh giá trên bộ thật giữ riêng; bộ M4 dùng để chọn mô hình TTS trước khi sinh hàng loạt."),
]
for i, (a, b) in enumerate(pipe, 11):
    line(i, "Bước " + a, b)

sec(18, "CÁC SHEET")
sheets_desc = [
    ("Muc_dich", "5 mục đích dữ liệu M1–M5: ai nói, dùng vào đâu, có vào huấn luyện ASR không."),
    ("Case_study", "12 case study, mỗi case gắn mục đích chính, phần người dùng và phần trợ lý, yếu tố trọng yếu, preset môi trường."),
    ("Yeu_to", "71 yếu tố đã trao đổi, mỗi yếu tố gắn bước xử lý chính, cách xử lý, bằng chứng, số câu mẫu phủ."),
    ("Buoc_xu_ly", "Số yếu tố theo từng bước xử lý."),
    ("Ma_tran", "Case × yếu tố do câu quyết định, kèm số câu mẫu phủ từng yếu tố."),
    ("Mau_khung", "Mẫu câu × khe thông tin; sức chứa tổ hợp để phủ số câu cần."),
    ("Mau_cau", "Câu mẫu của người dùng (M1, M2) và câu chẩn đoán (M4), có nhãn yếu tố."),
    ("Chi_tieu", "Số người nói, số câu, giờ âm thanh, tỷ lệ sinh/thật; ô vàng sửa được."),
    ("Preset_moi_truong", "17 preset môi trường kèm nguồn ồn thật có thể dùng."),
    ("Danh_gia", "Điểm giải pháp và điểm giữ giọng vùng (nhận định của mình, không phải số đo)."),
    ("Ho_so_nguoi_noi", "Mẫu hồ sơ giọng thật sẽ clone."),
    ("Nguon_giay_phep", "Nguồn dữ liệu và tình trạng giấy phép."),
    ("Tai_lieu", "Bài báo đã dùng và mức đã đọc."),
    ("Tu_dia_phuong, Tu_vung", "Từ vựng vùng miền và danh sách giá trị cho ô chọn."),
]
for i, (a, b) in enumerate(sheets_desc, 19):
    line(i, a, b)

sec(34, "LƯU Ý")
notes = [
    ("Số liệu", "Các hạn ngạch (số người nói, số câu, tỷ lệ) lấy từ các bài báo tiếng Anh, Hàn, Mân Nam; chưa ai kiểm cho tiếng Việt. Xem Danh_gia và Tai_lieu."),
    ("Câu mẫu", "Câu mẫu chỉ để minh họa cấu trúc và nhãn. Từ vựng và cách đọc từng vùng cần người bản ngữ duyệt trước khi dùng."),
    ("M3", "Tập đối chiếu ngoài miền xe chưa có transcript vì chưa chọn bộ thật; chỉ cần lấy từ bộ thật đã chọn, không dùng câu của tập kiểm thử."),
]
for i, (a, b) in enumerate(notes, 35):
    line(i, a, b)

sec(39, "THAM SỐ ƯỚC LƯỢNG THỜI LƯỢNG (sửa được)")
ws["A40"] = "Tốc độ nói để ước thời lượng"
ws["A40"].font = f_bold
ws["B40"] = 4.5
mark_input(ws["B40"])
ws["B40"].alignment = Alignment(horizontal="left")
ws["C40"] = "âm tiết/giây"
ws["C40"].font = f_norm
ws["D40"] = "Giá trị vừa của bản 0.2 (chọn tạm, chưa đo)."
ws["D40"].font = f_note

# ------------------------------------------------------------------ Muc_dich
ws = wb.create_sheet("Muc_dich")
head(ws, "Mục đích dữ liệu M1–M5", "Mỗi dòng của Mau_cau thuộc đúng một mục đích. Cột xanh lá tự tính.")
rows = [list(p) for p in V.PURPOSES]
for i, r in enumerate(rows):
    r.append(f'=COUNTIF(Mau_cau!$B$4:$B${MC1},A{4 + i})')
table(ws, 3, ["Mã", "Tên", "Ai nói", "Dùng để làm gì", "Vào huấn luyện ASR", "Vào kiểm thử", "Nguồn văn bản", "Nguồn giọng",
              "Bước áp dụng", "Ghi chú", "Số câu mẫu trong Mau_cau"], rows,
      [6, 30, 12, 50, 14, 22, 32, 30, 24, 40, 14], fills=[fill_req] * 10 + [fill_calc], center_cols=(1, 5))

# ------------------------------------------------------------------ Case_study
ws = wb.create_sheet("Case_study")
head(ws, "12 case study theo mục đích",
     "Mục đích chính: M1 người dùng nói lệnh, M2 câu trả lời ngắn, M5 trợ lý nói. Liên quan ASR là nhận định của mình dựa trên việc ai nói chủ yếu.")
rows = []
for i, c in enumerate(V.CASES):
    cid, name, desc, mp, rel, user, asst, reason, fac, pre, note = c
    r = 4 + i
    rows.append([cid, name, desc, mp, rel, user, asst, reason, fac, pre, note,
                 f'=COUNTIFS(Mau_cau!$C$4:$C${MC1},A{r},Mau_cau!$B$4:$B${MC1},"M1")',
                 f'=COUNTIFS(Mau_cau!$C$4:$C${MC1},A{r},Mau_cau!$B$4:$B${MC1},"M2")',
                 f"=INDEX(Chi_tieu!$C$27:$C$38,MATCH(A{r},Chi_tieu!$A$27:$A$38,0))",
                 f"=INDEX(Chi_tieu!$D$27:$D$38,MATCH(A{r},Chi_tieu!$A$27:$A$38,0))"])
table(ws, 3, ["Mã", "Tên case", "Mô tả", "Mục đích chính", "Liên quan ASR", "Phần người dùng nói (M1, M2)", "Phần trợ lý nói (M5, ngoài ASR)",
              "Lý do và điểm khó", "Yếu tố trọng yếu (mã)", "Preset môi trường", "Ghi chú", "Câu mẫu M1", "Câu mẫu M2",
              "Trọng số (Chi_tieu)", "Số câu mục tiêu (Chi_tieu)"], rows,
      [7, 24, 36, 10, 12, 42, 34, 46, 24, 18, 22, 10, 10, 12, 14],
      fills=[fill_req] * 11 + [fill_calc] * 4, center_cols=(1, 4, 5))
for r in range(4, 16):
    ws.cell(row=r, column=14).number_format = "0%"
    ws.cell(row=r, column=14).font = f_link
    ws.cell(row=r, column=15).font = f_link
dv(ws, "D4:D15", "muc_dich")
dv(ws, "E4:E15", "asr_lien_quan")
ws["A17"] = "Mã yếu tố dùng ở cột I xem sheet Yeu_to. Số câu mục tiêu và trọng số lấy từ sheet Chi_tieu (sửa ở đó)."
ws["A17"].font = f_note

# ------------------------------------------------------------------ Yeu_to
ws = wb.create_sheet("Yeu_to")
head(ws, "71 yếu tố ảnh hưởng: bước xử lý chính và cách xử lý",
     "Bước xử lý chính là nơi yếu tố được giải quyết; bước phụ là nơi cần kiểm hoặc hỗ trợ. Bằng chứng ghi nguồn và giới hạn; 'Chưa có bằng chứng đã đọc' nghĩa là mình chưa có bài báo nào cho điểm này.")
rows = [r + [None] for r in FR]
for i, r in enumerate(rows):
    rr = 4 + i
    if r[6] == V.S_TEXT or r[7] == V.S_TEXT:
        r[14] = f'=COUNTIF(Mau_cau!$N$4:$N${MC1},"*"&C{rr}&"*")'
    else:
        r[14] = "Không do câu quyết định"
table(ws, 3, ["Nhóm", "Nhóm con", "Mã", "Yếu tố", "Mức", "Phía", "Bước xử lý chính", "Bước phụ", "Cách xử lý", "Bằng chứng",
              "Tác động", "Chỉ số đo", "Ưu tiên", "Dữ liệu thật", "Số câu mẫu phủ"], rows,
      [22, 20, 7, 30, 12, 12, 30, 26, 52, 46, 40, 30, 10, 28, 14],
      fills=[fill_req] * 14 + [fill_calc], center_cols=(3, 13))
ws.auto_filter.ref = f"A3:O{Y1}"
dv(ws, f"G4:H{Y1}", "buoc")

# ------------------------------------------------------------------ Buoc_xu_ly
ws = wb.create_sheet("Buoc_xu_ly")
head(ws, "Số yếu tố theo bước xử lý", "Đếm từ sheet Yeu_to. Bước 1 là phần bộ mẫu câu phải đáp ứng trực tiếp.")
rows = []
for i, s in enumerate(V.STAGES):
    r = 4 + i
    rows.append([s, V.STAGE_DESC[s],
                 f"=COUNTIF(Yeu_to!$G${Y0}:$G${Y1},A{r})",
                 f"=COUNTIF(Yeu_to!$H${Y0}:$H${Y1},A{r})"])
table(ws, 3, ["Bước xử lý", "Làm gì", "Số yếu tố (bước chính)", "Số yếu tố (bước phụ)"], rows, [44, 90, 16, 16],
      fills=[fill_req, fill_req, fill_calc, fill_calc], center_cols=(3, 4))
n = len(V.STAGES)
ws.cell(row=4 + n, column=1, value="Tổng").font = f_bold
ws.cell(row=4 + n, column=3, value=f"=SUM(C4:C{3 + n})").font = f_bold
ws.cell(row=4 + n, column=4, value=f"=SUM(D4:D{3 + n})").font = f_bold
ws.cell(row=5 + n, column=1, value="Kiểm tra: tổng bước chính bằng số yếu tố").font = f_norm
ws.cell(row=5 + n, column=3, value=f'=IF(C{4 + n}=COUNTA(Yeu_to!$C${Y0}:$C${Y1}),"Khớp","Lệch")').font = f_norm
for r in (4 + n,):
    for j in (1, 3, 4):
        ws.cell(row=r, column=j).border = border

# ------------------------------------------------------------------ Ma_tran
ws = wb.create_sheet("Ma_tran")
head(ws, "Ma trận case × yếu tố",
     "● = case cần yếu tố này (trọng yếu); ○ = có xuất hiện. Hàng 5 cho bước xử lý chính; chỉ yếu tố thuộc bước 1 được phủ bằng câu, hàng 21 đếm số câu mẫu phủ.")
nc = len(V.MATRIX_COLS)
c0 = 4
ws.cell(row=3, column=1, value="Mã case")
ws.cell(row=3, column=2, value="Tên case")
ws.cell(row=3, column=3, value="Mục đích chính")
for j, code in enumerate(V.MATRIX_COLS):
    ws.cell(row=3, column=c0 + j, value=code)
    col = L(c0 + j)
    ws.cell(row=4, column=c0 + j, value=f"=INDEX(Yeu_to!$D${Y0}:$D${Y1},MATCH({col}$3,Yeu_to!$C${Y0}:$C${Y1},0))")
    ws.cell(row=5, column=c0 + j, value=f"=INDEX(Yeu_to!$G${Y0}:$G${Y1},MATCH({col}$3,Yeu_to!$C${Y0}:$C${Y1},0))")
ws.cell(row=4, column=1, value="Tên yếu tố")
ws.cell(row=5, column=1, value="Bước xử lý chính")
cl = c0 + nc
for k, t in enumerate(["Số yếu tố ●", "Số câu mẫu M1, M2"]):
    ws.cell(row=3, column=cl + k, value=t)
for r in (3, 4, 5):
    for j in range(1, cl + 2):
        c = ws.cell(row=r, column=j)
        c.font = f_head
        c.fill = fill_req if j < cl else fill_calc
        c.alignment = center_wrap
        c.border = border
ws.row_dimensions[4].height = 66
ws.row_dimensions[5].height = 66
for i, cid in enumerate(CASE_IDS):
    r = 6 + i
    ws.cell(row=r, column=1, value=cid)
    ws.cell(row=r, column=2, value=f"=INDEX(Case_study!$B$4:$B$15,MATCH(A{r},Case_study!$A$4:$A$15,0))")
    ws.cell(row=r, column=3, value=f"=INDEX(Case_study!$D$4:$D$15,MATCH(A{r},Case_study!$A$4:$A$15,0))")
    for j, code in enumerate(V.MATRIX_COLS):
        ws.cell(row=r, column=c0 + j, value=V.MATRIX.get(cid, {}).get(code, None))
    rng = f"{L(c0)}{r}:{L(cl - 1)}{r}"
    ws.cell(row=r, column=cl, value=f'=COUNTIF({rng},"●")')
    ws.cell(row=r, column=cl + 1, value=f'=COUNTIFS(Mau_cau!$C$4:$C${MC1},A{r},Mau_cau!$B$4:$B${MC1},"<>M4")')
    for j in range(1, cl + 2):
        c = ws.cell(row=r, column=j)
        c.font = f_norm
        c.border = border
        c.alignment = center if j >= c0 else wrap
last = 5 + len(CASE_IDS)
r_cnt, r_cov = last + 2, last + 3
ws.cell(row=r_cnt, column=1, value="Số case cần (●)")
ws.cell(row=r_cov, column=1, value="Số câu mẫu phủ")
for j in range(nc):
    col = L(c0 + j)
    ws.cell(row=r_cnt, column=c0 + j, value=f'=COUNTIF({col}6:{col}{last},"●")')
    ws.cell(row=r_cov, column=c0 + j,
            value=f'=IF(LEFT({col}$5,1)="1",COUNTIF(Mau_cau!$N$4:$N${MC1},"*"&{col}$3&"*"),"—")')
for r in (r_cnt, r_cov):
    for j in range(1, cl + 2):
        c = ws.cell(row=r, column=j)
        c.font = f_bold if j == 1 else f_norm
        c.border = border
        c.alignment = center if j >= c0 else wrap
ws.column_dimensions["A"].width = 18
ws.column_dimensions["B"].width = 26
ws.column_dimensions["C"].width = 12
for j in range(nc):
    ws.column_dimensions[L(c0 + j)].width = 14
ws.column_dimensions[L(cl)].width = 12
ws.column_dimensions[L(cl + 1)].width = 14
ws.freeze_panes = "D6"

# ------------------------------------------------------------------ Mau_khung
ws = wb.create_sheet("Mau_khung")
head(ws, "Mẫu câu × khe thông tin",
     "Số giá trị mỗi khe là mục tiêu cần liệt kê (ô vàng sửa được), không phải danh sách đã có. Sức chứa là tích tối đa; khe phụ thuộc nhau thì thực tế thấp hơn. Diễn đạt lại bằng LLM và người duyệt sẽ nhân thêm.")
rows = []
for i, t in enumerate(V.TEMPLATES):
    tid, cs, intent, tpl, s1, s2, s3, var, fac, note = t
    r = 4 + i
    row = [tid, cs, intent, tpl]
    for s in (s1, s2, s3):
        row += list(s) if s else [None, None, None]
    row += [f'=G{r}*IF(J{r}="",1,J{r})*IF(M{r}="",1,M{r})', var, fac, note]
    rows.append(row)
table(ws, 3, ["Mã", "Case", "Ý định", "Mẫu câu", "Khe 1", "Giá trị ví dụ khe 1", "Số giá trị mục tiêu khe 1",
              "Khe 2", "Giá trị ví dụ khe 2", "Số giá trị mục tiêu khe 2", "Khe 3", "Giá trị ví dụ khe 3", "Số giá trị mục tiêu khe 3",
              "Sức chứa tổ hợp", "Biến thể vùng", "Yếu tố (mã)", "Ghi chú"], rows,
      [6, 7, 22, 34, 12, 34, 10, 12, 34, 10, 12, 30, 10, 12, 26, 18, 44],
      fills=[fill_req] * 13 + [fill_calc] + [fill_req] * 3, center_cols=(1, 2, 7, 10, 13, 14))
for r in range(4, 4 + len(V.TEMPLATES)):
    for col in (7, 10, 13):
        mark_input(ws.cell(row=r, column=col))
dv(ws, f"B4:B{3 + len(V.TEMPLATES) + 40}", "case_id")
TPL_LAST = 3 + len(V.TEMPLATES)

# ------------------------------------------------------------------ Mau_cau
ws = wb.create_sheet("Mau_cau")
head(ws, "Câu mẫu của người dùng (M1, M2) và câu chẩn đoán (M4)",
     "Cột xanh lá tự tính (số âm tiết = số từ cách nhau bởi dấu cách; thời lượng = âm tiết / tốc độ ở Tong_quan!B40). M3 chưa có dòng vì chưa chọn bộ thật. Ví dụ từ vùng cần người bản ngữ duyệt.")
counter = {}
rows = []
for i, m in enumerate(V.M_ROWS):
    r = 4 + i
    key = (m["case"], m["purpose"])
    counter[key] = counter.get(key, 0) + 1
    sid = f'{m["case"]}-{m["purpose"]}-{counter[key]:03d}'
    m["sample_id"] = sid
    rows.append([sid, m["purpose"], m["case"],
                 f'=IFERROR(INDEX(Case_study!$B$4:$B$15,MATCH(C{r},Case_study!$A$4:$A$15,0)),"")',
                 m["intent"], m["act"], m["raw"], m["spoken"], m["lang"], m["feats"], m["lex"], m["region"], m["state"],
                 m["factors"],
                 f'=LEN(TRIM(H{r}))-LEN(SUBSTITUTE(TRIM(H{r})," ",""))+1',
                 f'=IF(O{r}<=3,"Rất ngắn (≤3)",IF(O{r}<=8,"Ngắn (4–8)","Thường (>8)"))',
                 f"=ROUND(O{r}/{RATE},1)", m["notes"]])
table(ws, 3, ["sample_id", "purpose", "case_id", "case_name", "intent", "speech_act", "text_raw", "text_spoken", "language_mix",
              "norm_features", "lexicon_variant", "speaker_region", "speaker_state", "factors_covered", "so_am_tiet", "do_dai",
              "est_duration_s", "notes"], rows,
      [14, 9, 8, 20, 24, 12, 38, 42, 12, 24, 14, 14, 18, 22, 9, 14, 10, 38],
      fills=[fill_req] * 3 + [fill_calc] + [fill_req] * 10 + [fill_calc] * 3 + [fill_opt],
      center_cols=(2, 3, 15, 17))
ws.auto_filter.ref = f"A3:R{3 + len(rows)}"
dv(ws, f"B4:B{MC1}", "muc_dich")
dv(ws, f"C4:C{MC1}", "case_id")
dv(ws, f"F4:F{MC1}", "speech_act")
dv(ws, f"I4:I{MC1}", "language_mix")
dv(ws, f"K4:K{MC1}", "lexicon_variant")
dv(ws, f"L4:L{MC1}", "speaker_region")
dv(ws, f"M4:M{MC1}", "speaker_state")
NS = len(rows)

# ------------------------------------------------------------------ Chi_tieu
ws = wb.create_sheet("Chi_tieu")
head(ws, "Chỉ tiêu số lượng",
     "Ô chữ xanh nền vàng là tham số sửa được; ô xanh lá là kết quả tự tính. Các số khởi đầu là đề xuất của mình theo bài báo đã đọc, chưa kiểm cho tiếng Việt.")
for col, w in zip("ABCDEFGHI", (44, 14, 18, 18, 22, 28, 20, 14, 14)):
    ws.column_dimensions[col].width = w
for j, h in enumerate(["Tham số", "Giá trị", "Nguồn hoặc lý do"], 1):
    c = ws.cell(row=4, column=j, value=h)
    c.font = f_head
    c.fill = fill_req
    c.alignment = center_wrap
    c.border = border
params = [
    (5, "Tổng số người nói clone", 60, "0", "Versatile TTS và Ogun et al.: khoảng 50–100 người nói là đủ. 60 là số mình chọn trong khoảng đó."),
    (6, "Tỷ lệ giọng Bắc", 0.30, "0%", "Tự chọn."),
    (7, "Tỷ lệ giọng Trung", 0.40, "0%", "Nhiều hơn vì ViMD cho thấy giọng Trung khó nhất (WER 17,15%) và không phải một giọng; tự chọn."),
    (8, "Tỷ lệ giọng Nam", 0.30, "0%", "Tự chọn."),
    (10, "Tỷ lệ giọng nữ", 0.5, "0%", "Cân bằng giới; tự chọn."),
    (11, "Số câu khác nhau tối thiểu (M1 + M2)", 10000, "#,##0", "Versatile TTS (Mân Nam): dưới khoảng 10.000 câu thì CER tăng rõ."),
    (12, "Số lần đọc mỗi câu (khác giọng hoặc khác nền ồn)", 5, "0", "Tự chọn; tăng để có thêm giờ mà không cần thêm câu, nhưng đa dạng câu quan trọng hơn."),
    (13, "Thời lượng trung bình mỗi câu (giây)", 3.5, "0.0", None),
    (14, "Tỷ lệ M3 so với M1 + M2", 1.0, "0.0", "Đề xuất của mình: M3 cùng số lượng để cân bằng 'giọng sinh' giữa miền xe và ngoài miền."),
    (15, "Tỷ lệ giờ sinh : thật mục tiêu", 1.0, "0.0", "Versatile TTS: 1:1 (tiếng Hàn); thêm nữa gần như không cải thiện."),
    (16, "Giờ dữ liệu thật ngoài miền xe dự kiến", 100, "#,##0", "Số ví dụ; nhập khi chọn bộ dữ liệu thật."),
]
for r, a, v, fmt, note in params:
    ws.cell(row=r, column=1, value=a).font = f_norm
    c = ws.cell(row=r, column=2, value=v)
    mark_input(c)
    c.number_format = fmt
    c.alignment = Alignment(horizontal="right")
    n = ws.cell(row=r, column=3, value=note)
    n.font = f_norm
    n.alignment = wrap
    for j in (1, 2, 3):
        ws.cell(row=r, column=j).border = border
ws["C13"] = f'="Trung bình các câu trong Mau_cau: "&TEXT(AVERAGE(Mau_cau!$Q$4:$Q${MC1}),"0.0")&" giây (câu mẫu ngắn hơn câu thật nhiều nên chỉnh theo dữ liệu thật)."'
ws["C13"].font = f_norm
ws["C13"].alignment = wrap
ws["A9"] = "Kiểm tra tổng tỷ lệ vùng"
ws["A9"].font = f_norm
ws["B9"] = "=SUM(B6:B8)"
ws["B9"].number_format = "0%"
ws["B9"].font = f_norm
ws["C9"] = '=IF(ROUND(B9,6)=1,"OK","Tổng khác 100%")'
ws["C9"].font = f_norm
for j in (1, 2, 3):
    ws.cell(row=9, column=j).border = border
ws.column_dimensions["C"].width = 44

# người nói
ws["A18"] = "Người nói theo vùng"
ws["A18"].font = f_bold
for j, h in enumerate(["Vùng", "Tỷ lệ", "Số người nói mục tiêu", "Nữ", "Nam", "Đã chọn (Ho_so_nguoi_noi)", "Còn thiếu"], 1):
    c = ws.cell(row=19, column=j, value=h)
    c.font = f_head
    c.fill = fill_calc if j > 1 else fill_req
    c.alignment = center_wrap
    c.border = border
for k, (reg, srow) in enumerate((("Bắc", 6), ("Trung", 7), ("Nam", 8))):
    r = 20 + k
    ws.cell(row=r, column=1, value=reg)
    ws.cell(row=r, column=2, value=f"=B{srow}").number_format = "0%"
    ws.cell(row=r, column=3, value=(f"=ROUND($B$5*B{r},0)" if reg != "Nam" else "=$B$5-C20-C21"))
    ws.cell(row=r, column=4, value=f"=ROUND(C{r}*$B$10,0)")
    ws.cell(row=r, column=5, value=f"=C{r}-D{r}")
    ws.cell(row=r, column=6, value=f'=COUNTIFS(Ho_so_nguoi_noi!$D$4:$D$300,A{r},Ho_so_nguoi_noi!$Q$4:$Q$300,"<>Ví dụ",Ho_so_nguoi_noi!$Q$4:$Q$300,"<>Loại",Ho_so_nguoi_noi!$A$4:$A$300,"<>")')
    ws.cell(row=r, column=7, value=f"=MAX(0,C{r}-F{r})")
ws.cell(row=23, column=1, value="Tổng")
for j in (3, 4, 5, 6, 7):
    ws.cell(row=23, column=j, value=f"=SUM({L(j)}20:{L(j)}22)")
for r in range(20, 24):
    for j in range(1, 8):
        c = ws.cell(row=r, column=j)
        c.font = f_bold if (r == 23 or j == 1) else f_norm
        c.border = border
        c.alignment = center if j > 1 else wrap

# câu theo case
ws["A25"] = "Câu theo case"
ws["A25"].font = f_bold
hdr = ["Mã case", "Tên case", "Trọng số (sửa được)", "Số câu khác nhau mục tiêu", "Sức chứa khung (Mau_khung)", "Đánh giá khung",
       "Câu mẫu hiện có (M1, M2)", "Số lượt đọc", "Giờ âm thanh"]
for j, h in enumerate(hdr, 1):
    c = ws.cell(row=26, column=j, value=h)
    c.font = f_head
    c.fill = fill_calc if j > 3 else fill_req
    c.alignment = center_wrap
    c.border = border
WEIGHTS = {"CS01": 0.15, "CS02": 0.03, "CS03": 0.14, "CS04": 0.12, "CS05": 0.12, "CS06": 0.05, "CS07": 0.06, "CS08": 0.07,
           "CS09": 0.03, "CS10": 0.11, "CS11": 0.03, "CS12": 0.09}
assert abs(sum(WEIGHTS.values()) - 1) < 1e-9
for i, cid in enumerate(CASE_IDS):
    r = 27 + i
    ws.cell(row=r, column=1, value=cid)
    ws.cell(row=r, column=2, value=f"=INDEX(Case_study!$B$4:$B$15,MATCH(A{r},Case_study!$A$4:$A$15,0))")
    c = ws.cell(row=r, column=3, value=WEIGHTS[cid])
    mark_input(c)
    c.number_format = "0%"
    ws.cell(row=r, column=4, value=f"=ROUND($B$11*C{r},0)").number_format = "#,##0"
    ws.cell(row=r, column=5, value=f"=SUMIF(Mau_khung!$B$4:$B${TPL_LAST + 40},A{r},Mau_khung!$N$4:$N${TPL_LAST + 40})").number_format = "#,##0"
    ws.cell(row=r, column=6, value=f'=IF(E{r}>=D{r},"Đủ khung","Cần thêm khung hoặc diễn đạt lại")')
    ws.cell(row=r, column=7, value=f'=COUNTIFS(Mau_cau!$C$4:$C${MC1},A{r},Mau_cau!$B$4:$B${MC1},"<>M4")')
    ws.cell(row=r, column=8, value=f"=D{r}*$B$12").number_format = "#,##0"
    ws.cell(row=r, column=9, value=f"=H{r}*$B$13/3600").number_format = "0.0"
ws.cell(row=39, column=1, value="Tổng")
ws.cell(row=39, column=3, value="=SUM(C27:C38)").number_format = "0%"
for j in (4, 5, 7, 8):
    ws.cell(row=39, column=j, value=f"=SUM({L(j)}27:{L(j)}38)").number_format = "#,##0"
ws.cell(row=39, column=9, value="=SUM(I27:I38)").number_format = "0.0"
ws.cell(row=39, column=6, value='=IF(ROUND(C39,6)=1,"Tổng trọng số = 100%","Tổng trọng số khác 100%")')
for r in range(27, 40):
    for j in range(1, 10):
        c = ws.cell(row=r, column=j)
        c.border = border
        if c.font != f_input:
            c.font = f_bold if r == 39 else (c.font if j == 3 else f_norm)
        c.alignment = center if j in (3, 4, 5, 7, 8, 9) else wrap
for r in range(27, 39):
    mark_input(ws.cell(row=r, column=3))

# giờ và tỷ lệ
ws["A41"] = "Giờ âm thanh và tỷ lệ sinh : thật"
ws["A41"].font = f_bold
lab = [
    (42, "Giờ M1 + M2 (sinh)", "=I39", "0.0"),
    (43, "Giờ M3 (sinh, ngoài miền xe)", "=B42*B14", "0.0"),
    (44, "Tổng giờ sinh", "=B42+B43", "0.0"),
    (45, "Giờ dữ liệu thật ngoài miền xe", "=B16", "#,##0.0"),
    (46, "Tỷ lệ sinh : thật hiện tại", '=IF(B45=0,"",B44/B45)', "0.00"),
    (47, "Đánh giá so với mục tiêu", '=IF(B46="","",IF(ABS(B46-B15)<=0.25*B15,"Gần mục tiêu","Lệch mục tiêu: chỉnh số lượt đọc hoặc giờ thật"))', "@"),
]
for r, a, f_, fmt in lab:
    ws.cell(row=r, column=1, value=a).font = f_norm
    c = ws.cell(row=r, column=2, value=f_)
    c.font = f_norm
    c.number_format = fmt
    c.alignment = Alignment(horizontal="right")
    for j in (1, 2):
        ws.cell(row=r, column=j).border = border
ws["C47"] = "Ngưỡng 25% là mình đặt tạm."
ws["C47"].font = f_note
ws.freeze_panes = None

# ------------------------------------------------------------------ Preset_moi_truong
ws = wb.create_sheet("Preset_moi_truong")
head(ws, "17 preset môi trường",
     "Dùng ở bước trộn nhiễu (bước 4). Cột xanh lá là bổ sung ở bản 0.3. E16, E17 thuộc phía loa phát (M5), không dùng cho ASR.")
case_by_preset = {}
for c in V.CASES:
    for p in [x.strip() for x in c[9].split(";")]:
        case_by_preset.setdefault(p, []).append(c[0])
rows = []
for p in D.PRESETS:
    pid = p[0]
    avail, src = V.PRESET_REAL[pid]
    use = "Không (M5)" if pid in ("E16", "E17") else "Có"
    rows.append(list(p) + [", ".join(case_by_preset.get(pid, [])), use, avail, src])
table(ws, 3, ["Mã", "Tên", "Mô tả", "Trạng thái xe", "Tốc độ (km/h)", "Ồn dB(A)", "Nguồn ồn", "SNR mục tiêu (dB)", "Mức điều hòa",
              "Cửa kính", "Nhạc", "Mưa", "Số người", "Mục tiêu đánh giá", "Case dùng", "Dùng cho ASR", "Có nguồn ồn thật", "Nguồn ồn gợi ý"],
      rows, [6, 24, 36, 14, 10, 10, 30, 10, 10, 10, 10, 10, 8, 30, 20, 12, 12, 52],
      fills=[fill_req] * 14 + [fill_calc] * 4, center_cols=(1, 5, 6, 8, 9, 13))

# ------------------------------------------------------------------ Danh_gia
ws = wb.create_sheet("Danh_gia")
head(ws, "Điểm giải pháp và điểm giữ giọng vùng",
     "Thang 10, nhận định của mình, không phải số đo. Trọng số bốn tiêu chí bằng nhau (cột Trung bình = AVERAGE). Điểm được chấm lại ở bản 0.3 nên có thể lệch vài điểm so với bảng trong chat trước.")
rows = []
for i, s in enumerate(V.SOLUTIONS_EVAL):
    r = 4 + i
    rows.append([s[0], s[1], s[2], s[3], s[4], s[5], s[6], f"=ROUND(AVERAGE(D{r}:G{r}),1)", s[7]])
table(ws, 3, ["Mã", "Khoảng trống", "Giải pháp", "Bằng chứng", "Hiệu quả kỳ vọng", "Khả thi", "An toàn (ít rủi ro)", "Trung bình", "Căn cứ"],
      rows, [6, 22, 52, 11, 11, 10, 11, 11, 80],
      fills=[fill_req] * 7 + [fill_calc, fill_req], center_cols=(1, 4, 5, 6, 7, 8))
for r in range(4, 4 + len(rows)):
    for col in (4, 5, 6, 7):
        ws.cell(row=r, column=col).font = f_input
r = 5 + len(rows)
ws.cell(row=r, column=1, value="Không nên dùng").font = f_bold
for k, (cid, name, why) in enumerate(V.SOLUTIONS_NOTE):
    ws.cell(row=r + 1 + k, column=1, value=cid).font = f_norm
    ws.cell(row=r + 1 + k, column=2, value=name).font = f_norm
    c = ws.cell(row=r + 1 + k, column=3, value=why)
    c.font = f_norm
    c.alignment = wrap
r2 = r + 4
ws.cell(row=r2, column=1, value="Điểm giữ giọng vùng (thang 10, nhận định của mình)").font = f_bold
heads = ["Vùng", "Zero-shot", "Có tinh chỉnh theo vùng", "Tăng thêm", "Nhận xét"]
for j, h in enumerate(heads):
    col = [1, 4, 5, 6, 9][j]
    c = ws.cell(row=r2 + 1, column=col, value=h)
    c.font = f_head
    c.fill = fill_calc if h == "Tăng thêm" else fill_req
    c.alignment = center_wrap
    c.border = border
for k, (reg, z, ft, note) in enumerate(V.DIALECT_SCORES):
    rr = r2 + 2 + k
    ws.cell(row=rr, column=1, value=reg)
    ws.cell(row=rr, column=4, value=z)
    ws.cell(row=rr, column=5, value=ft)
    ws.cell(row=rr, column=6, value=f"=E{rr}-D{rr}")
    ws.cell(row=rr, column=9, value=note)
    for col in (1, 4, 5, 6, 9):
        c = ws.cell(row=rr, column=col)
        c.font = f_input if col in (4, 5) else f_norm
        c.border = border
        c.alignment = wrap if col in (1, 9) else center
rr = r2 + 2 + len(V.DIALECT_SCORES)
ws.cell(row=rr, column=1, value="Trung bình ba vùng").font = f_bold
for col in (4, 5, 6):
    c = ws.cell(row=rr, column=col, value=f"=ROUND(AVERAGE({L(col)}{rr - 3}:{L(col)}{rr - 1}),1)")
    c.font = f_bold
    c.alignment = center
    c.border = border
ws.cell(row=rr + 1, column=1, value="Chưa có paper nào đo độ giữ giọng vùng của TTS tiếng Việt; các điểm này suy từ ViMD (WER theo vùng) và Singlish (tiếng Anh).").font = f_note
ws.freeze_panes = "A4"

# ------------------------------------------------------------------ Ho_so_nguoi_noi
ws = wb.create_sheet("Ho_so_nguoi_noi")
head(ws, "Hồ sơ giọng thật sẽ clone",
     "Dòng 'Ví dụ' chỉ minh họa định dạng, không phải người thật, và không được tính vào số người đã chọn. Thay bằng người chọn từ bộ dữ liệu thật sau khi kiểm giấy phép.")
ex = [
    ["VD-001", "(ví dụ) tên bộ dữ liệu", "(mã gốc)", "Bắc", "Bắc Bộ", "Nữ", "Thanh niên (18–34)", 210, None, None, 8, 3, 12, 25, "Chưa", "Chưa", "Ví dụ", "Dòng ví dụ; thay khi có dữ liệu."],
    ["VD-002", "(ví dụ) tên bộ dữ liệu", "(mã gốc)", "Trung", "Trung Bộ (chưa chia tiểu vùng)", "Nam", "Trung niên (35–54)", 120, None, None, 5, 3, 10, 22, "Chưa", "Chưa", "Ví dụ", "Dòng ví dụ; thay khi có dữ liệu."],
    ["VD-003", "(ví dụ) tên bộ dữ liệu", "(mã gốc)", "Nam", "Nam Bộ", "Nữ", "Thanh niên (18–34)", 200, None, None, 6, 3, 11, 28, "Chưa", "Chưa", "Ví dụ", "Dòng ví dụ; thay khi có dữ liệu."],
]
table(ws, 3, ["speaker_id", "Nguồn dữ liệu", "Mã trong bộ gốc", "Vùng (3)", "Tiểu vùng", "Giới", "Nhóm tuổi", "F0 trung bình (Hz, đo)", "Dải F0",
              "Chất giọng", "Giờ giọng sạch có sẵn", "Số đoạn tham chiếu", "Độ dài đoạn tham chiếu (giây)", "SNR đoạn tham chiếu (dB, đo)",
              "Bản ngữ vùng duyệt", "Giấy phép cho phép clone", "Trạng thái", "Ghi chú"], ex,
      [11, 24, 14, 10, 28, 8, 20, 12, 18, 18, 12, 12, 14, 14, 12, 14, 12, 34],
      fills=[fill_req] * 18, center_cols=(1, 4, 6, 8, 11, 12, 13, 14, 15, 16, 17))
for rr in range(4, 7):
    for col in range(1, 19):
        mark_input(ws.cell(row=rr, column=col))
dv(ws, "D4:D300", "vung_3")
dv(ws, "E4:E300", "tieu_vung")
dv(ws, "F4:F300", "gender")
dv(ws, "G4:G300", "age_group")
dv(ws, "I4:I300", "f0_band")
dv(ws, "J4:J300", "voice_quality")
dv(ws, "O4:P300", "kiem")
dv(ws, "Q4:Q300", "ho_so_status")
ws["A8"] = "Điều kiện cho đoạn tham chiếu: sạch, một người nói, không nhạc nền, không vang rõ, độ dài và SNR ghi lại; giọng đọc cùng vùng với từ vựng của câu sẽ sinh. Ngưỡng cụ thể chưa có bằng chứng."
ws["A8"].font = f_note

# ------------------------------------------------------------------ Nguon_giay_phep
ws = wb.create_sheet("Nguon_giay_phep")
head(ws, "Nguồn dữ liệu và giấy phép", "Chỉ ghi điều đã kiểm qua bài báo hoặc trang dữ liệu; 'chưa rõ' nghĩa là chưa tìm thấy, cần đọc điều khoản gốc trước khi dùng.")
src_rows = [list(s) for s in TX.SOURCES]
ncol = max(len(s) for s in src_rows)
for s in src_rows:
    while len(s) < ncol:
        s.append("")
hd = ["Nguồn", "Loại", "Dùng cho", "Giấy phép", "Tình trạng kiểm tra", "Quy mô"][:ncol]
while len(hd) < ncol:
    hd.append("Ghi chú")
table(ws, 3, hd, src_rows, [30, 28, 34, 40, 24, 30, 30][:ncol])

# ------------------------------------------------------------------ Tai_lieu
ws = wb.create_sheet("Tai_lieu")
head(ws, "Tài liệu đã dùng", "Mức đã đọc: bảng kết quả hoặc toàn văn so với chỉ đọc tóm tắt. Điểm chỉ dựa trên tóm tắt nên coi là gợi ý.")
table(ws, 3, ["Tài liệu", "Đường dẫn", "Dùng cho", "Mức đã đọc"], [list(p) for p in V.PAPERS], [60, 56, 56, 34])

# ------------------------------------------------------------------ Tu_dia_phuong
ws = wb.create_sheet("Tu_dia_phuong")
head(ws, "Từ vựng vùng miền", "Gợi ý ban đầu; người bản ngữ từng vùng cần duyệt trước khi dùng. Ô trống = chưa có từ riêng, dùng từ chuẩn chung.")
table(ws, 3, ["Nhóm", "Khái niệm", "Bắc", "Trung", "Nam", "Ghi chú"], [list(x) for x in TX.LEXICON], [16, 28, 18, 18, 18, 44])

# ------------------------------------------------------------------ Tu_vung (cuối)
ws = wb.create_sheet("Tu_vung")
for j, (k, vals) in enumerate(LISTS.items(), 1):
    c = ws.cell(row=1, column=j, value=k)
    c.font = f_head
    c.fill = fill_req
    for i, v in enumerate(vals, 2):
        ws.cell(row=i, column=j, value=v).font = f_norm
    ws.column_dimensions[L(j)].width = 24
ws.freeze_panes = "A2"

wb.save(OUT_XLSX)

# ------------------------------------------------------------------ JSONL
with open(OUT_JSONL, "w", encoding="utf-8") as fh:
    for m in V.M_ROWS:
        syl = len(m["spoken"].split())
        dl = "Rất ngắn" if syl <= 3 else ("Ngắn" if syl <= 8 else "Thường")
        rec = {
            "sample_id": m["sample_id"], "purpose": m["purpose"], "case_id": m["case"], "intent": m["intent"],
            "speech_act": m["act"], "text_raw": m["raw"], "text_spoken": m["spoken"], "language_mix": m["lang"],
            "norm_features": [x.strip() for x in m["feats"].split(";") if x.strip()],
            "lexicon_variant": m["lex"], "speaker_region": m["region"], "speaker_state": m["state"],
            "factors_covered": codes_in(m["factors"]), "n_syllables": syl, "length_class": dl, "notes": m["notes"],
        }
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("OK", NS, "mẫu")
