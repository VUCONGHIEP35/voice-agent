# -*- coding: utf-8 -*-
"""Hằng số bước RIR (docs/ke_hoach_RIR_v3.md; quyết định người dùng 27/10 và 28/10/2026). Đổi ở đây là đổi cho mọi
bước RIR.

Theo đặc tả gốc: micro bốc đều 4 vị trí; ghế lái 70 / phụ 20 / sau 10 cho mọi case (kể cả CS11); P(RIR) = 0,8;
EDT 0,03–0,15 giây; −26 dBFS; đuôi 0,25 giây. Không gán preset ở bước này (preset mã E gán ở bước cộng nhiễu).
Các mục ghi "nhận định" là giả định của mình, chưa đối chiếu xe thật.
"""

SR = 16_000
SEED = 20261027

# Loại khoang theo xe bán ở Việt Nam (bản 3, 28/10/2026; docs/kich_thuoc_xe_vn.md mục 4). Dải kích thước khoang
# trong (m), ước từ kích thước ngoài và thông số nội thất hãng công bố ở Mỹ/Úc:
#   rộng = rộng ngoài − 0,35…0,42 (vai ghế trước: CR-V 1,47 / 1,87; Seltos 1,41 / 1,80; Santa Fe 1,51 / 1,90; Ranger 1,44 / 1,86);
#   cao  = cao ngoài − khoảng sáng gầm − khoảng 0,12 (khớp khoảng trần + độ cao đệm: CR-V khoảng 1,35; Accent khoảng 1,22);
#   dài  = từ chân kính trước tới vách sau của khoang có người (sedan: lưng ghế sau; hatchback/SUV: có một phần khoang
#          hành lý thông với khoang người; 7 chỗ: sau hàng 3; bán tải: vách cabin ngay sau hàng 2). Nhận định.
# x_hang1: miệng hàng ghế trước cách chân kính trước (m); cach_hang: hàng 1 -> hàng 2 (m). Ghế "sau" luôn là hàng 2.
# Bảy chỗ và bán tải vượt dải chung của đặc tả gốc (dài 1,7–2,8; cao 1,1–1,35) vì đo theo xe thật; chỗ lệch ghi trong v3.
LOAI_XE = {
    "mini": dict(dai=(1.75, 1.95), rong=(1.12, 1.30), cao=(1.25, 1.35), x_hang1=(0.70, 0.80), cach_hang=(0.70, 0.80)),
    "hanga": dict(dai=(1.85, 2.10), rong=(1.20, 1.35), cao=(1.18, 1.26), x_hang1=(0.75, 0.85), cach_hang=(0.75, 0.85)),
    "sedan": dict(dai=(1.95, 2.15), rong=(1.30, 1.42), cao=(1.15, 1.25), x_hang1=(0.80, 0.90), cach_hang=(0.80, 0.88)),
    "suv_b": dict(dai=(2.20, 2.55), rong=(1.33, 1.45), cao=(1.25, 1.35), x_hang1=(0.80, 0.90), cach_hang=(0.82, 0.90)),
    "suv_c": dict(dai=(2.40, 2.75), rong=(1.45, 1.55), cao=(1.30, 1.40), x_hang1=(0.85, 0.95), cach_hang=(0.88, 0.95)),
    "bay_cho": dict(dai=(2.75, 3.10), rong=(1.36, 1.53), cao=(1.35, 1.45), x_hang1=(0.85, 0.95), cach_hang=(0.85, 0.95)),
    "ban_tai": dict(dai=(2.00, 2.20), rong=(1.44, 1.52), cao=(1.30, 1.38), x_hang1=(0.85, 0.95), cach_hang=(0.80, 0.88)),
}
XE_DAI_DIEN = {
    "mini": "VinFast VF 3, VF 2",
    "hanga": "Kia Morning, Hyundai i10, Toyota Wigo, Suzuki Swift",
    "sedan": "Toyota Vios, Honda City, Hyundai Accent, Mazda3, Kia K3",
    "suv_b": "VinFast VF 5, VF 6, Toyota Yaris Cross, Mitsubishi Xforce, Hyundai Creta, Kia Seltos, Kia Sonet, Honda HR-V",
    "suv_c": "Mazda CX-5, Honda CR-V, Hyundai Tucson, VinFast VF 7, VF 8, Ford Territory",
    "bay_cho": "VinFast Limo Green, Mitsubishi Xpander, Toyota Innova Cross, Veloz, Suzuki XL7, Fortuner, Everest, Santa Fe",
    "ban_tai": "Ford Ranger, Toyota Hilux, Mitsubishi Triton",
}
KHOANG_MOI_LOAI = 40             # đều mỗi loại (người dùng chọn 28/10)
KHOANG_DEV_MOI_LOAI = 4          # 4 khoang cuối mỗi loại vào dev -> 252 train / 28 dev

# Ghế (xe tay lái thuận: lái bên trái). Toạ độ: x từ chân kính trước (0) ra sau (dài), y từ trái (0) sang phải
# (rộng), z từ sàn (0) lên trần (cao). x theo hàng ghế của loại xe (LOAI_XE), y theo tỷ lệ rộng: nhận định.
GHE = {
    "lai": dict(hang=1, y=0.28),
    "phu": dict(hang=1, y=0.72),
    "sau_trai": dict(hang=2, y=0.28),
    "sau_phai": dict(hang=2, y=0.72),
}
MIENG_CACH_VACH_SAU_MIN = 0.25   # miệng hàng 2 cách vách sau tối thiểu (lưng ghế, tựa đầu), nhận định
TRONG_SO_GHE = {"lai": 0.70, "phu": 0.20, "sau_trai": 0.05, "sau_phai": 0.05}
DEM_GHE_CAO = 0.30               # mặt đệm ghế cách sàn (m), nhận định
MIENG_TREN_DEM = (0.60, 0.75)    # miệng cao hơn mặt đệm (đặc tả)
MIENG_CACH_TRAN_MIN = 0.12       # miệng không cao quá trần trừ mức này (đầu người), nhận định
LECH_DAU = 0.10                  # lệch ±10 cm theo x, y (đặc tả)
SO_VI_TRI_DAU = 2                # mỗi ghế 2 vị trí đầu (h0, h1)

# Micro: 4 vị trí của đặc tả. x tính bằng mét từ kính trước; y, z theo tỷ lệ rộng/cao, trừ khi ghi "_m". Nhận định.
MICRO = {
    "tran": dict(x_m=0.45, y=0.50, z_tu_tran_m=0.02),     # trần trước, cạnh đèn đọc
    "guong": dict(x_m=0.30, y=0.50, z_tu_tran_m=0.10),    # gương chiếu hậu
    "cot_a": dict(x_m=0.20, y_m=0.05, z=0.78),            # cột A phía lái
    "tap_lo": dict(x_m=0.20, y=0.50, z=0.60),             # giữa táp-lô
}
TRONG_SO_MICRO = {k: 0.25 for k in MICRO}

# Vật liệu: mỗi mặt hộp trộn các vật liệu trong bảng của pyroomacoustics theo tỷ lệ diện tích (nhận định; hộp không
# có ghế nên phần ghế bọc vải được dồn vào sàn, vách sau, hai bên). Mỗi hệ số bốc ±20% theo từng dải.
# Mặt theo tên pyroomacoustics: west = kính trước (x = 0), east = sau, south = trái (y = 0), north = phải, floor, ceiling.
# Bộ "hút âm hơn" (28/10/2026), thay bộ đầu (sàn ghế 0,8, sau ghế 0,7, hai bên kính 0,4/cứng 0,3/ghế 0,3, trần
# carpet_6mm_open_cell_foam). Bộ đầu vang hơn RIR đo thật: EDT ghế lái trung vị 0,10 s so với 0,05–0,07 s ở 4 xe
# CAVEMOVE (docs/danh_gia_rir_that.md); bộ này cho 0,063 s. Âm trầm (250 Hz) vẫn vang hơn thật.
VAT_LIEU = {
    "west": dict(tron=[("glass_window", 0.6), ("hard_surface", 0.4)], tan_xa=0.15),
    "east": dict(tron=[("chairs_upholstered_cloth", 0.85), ("glass_window", 0.15)], tan_xa=0.40),
    "south": dict(tron=[("glass_window", 0.35), ("hard_surface", 0.15), ("chairs_upholstered_cloth", 0.5)], tan_xa=0.25),
    "north": dict(tron=[("glass_window", 0.35), ("hard_surface", 0.15), ("chairs_upholstered_cloth", 0.5)], tan_xa=0.25),
    "floor": dict(tron=[("chairs_upholstered_cloth", 0.9), ("carpet_cotton", 0.1)], tan_xa=0.50),
    "ceiling": dict(tron=[("curtains_cotton_0.5", 1.0)], tan_xa=0.20),
}
# Mặt khác bộ chung theo loại xe. Bán tải: vách cabin ngay sau hàng 2 (không có khoang hành lý thông với khoang
# người); lưng ghế sau bọc nệm che gần hết vách, kính sau nhỏ. Bản đầu (ghế 0,5 / kính 0,4 / kim loại 0,1) vang quá:
# job 15463 cho EDT trung vị 0,080 s so với 0,053 s ở 6 loại khác, ghế sau 0,09–0,11 s ở 500 Hz–4 kHz; người nghe
# xác nhận "hơi vang" (28/10). Nhận định.
VAT_LIEU_THEO_LOAI = {
    "ban_tai": {"east": dict(tron=[("chairs_upholstered_cloth", 0.8), ("glass_window", 0.2)], tan_xa=0.40)},
}
VAT_LIEU_LECH = 0.20
TAN_SO_DAI = [125, 250, 500, 1000, 2000, 4000, 8000]
# Hiệu chỉnh theo RIR đo (bản 3, phantich/so_kho_rir.py). Lượt 1 (28/10, 14 khoang): EDT 250 Hz ghế lái mô phỏng
# 0,09–0,18 s so với 0,06–0,09 s ở 5 xe đo; DRR ghế sau −4,4…−5,5 dB so với khoảng 0 dB ở 4 xe CAVEMOVE.
# HAP_THU_THEM: hấp thụ cộng vào mọi mặt theo dải (vỏ và tấm ốp mỏng rung, hút âm trầm; bảng vật liệu phòng không có).
# HUONG_MIENG_P: miệng phát mạnh về phía trước (nguồn đo thật là miệng giả/TalkBox, cũng có hướng), dạng cardioid
# p + (1 − p)·cos θ quay về kính trước; p = 0,5 là cardioid (chỉ số hướng 4,8 dB), p = 1 là vô hướng.
# Lượt 2 ([0,30; 0,20; 0,05; 0…], p = 0,5): đạt 72/77 mục tiêu; EDT 250 Hz ghế lái 0,06–0,07 s, DRR sau −0,9…−1,7 dB;
# trượt 5 mục EDT 1 kHz ghế sau hơi ngắn (0,025–0,030 so với ≥ 0,032 s). Lượt 3 ([0,30; 0,20; 0…], p = 0,6): 73/77,
# vẫn trượt 4 mục EDT 1 kHz ghế sau; dải 500 Hz–2 kHz ở mép khô của xe thật (vải trong bảng pyroomacoustics hút
# 0,8–0,9 ở 1 kHz). Lượt 4 ([0,30; 0,20; −0,08; −0,12; −0,08; 0; 0]; số âm là bớt): 75/77, trượt EDT 500 Hz bán tải
# (vách sau kính + kim loại hút ít, bớt 0,08 thì gần sàn 0,01). Lượt 5: bớt 0,04 ở 500 Hz.
HAP_THU_THEM = [0.30, 0.20, -0.04, -0.12, -0.08, 0.0, 0.0]
HUONG_MIENG_P = 0.6

# Mô phỏng: hybrid image source + ray tracing (pyroomacoustics), hấp thụ không khí bật.
ISM_BAC = 6
RAY_SO_TIA = 20_000
RAY_BAN_KINH_THU = 0.10          # m; mặc định 0,5 m quá lớn so với khoang xe
RAY_THOI_GIAN = 0.30             # s

# Kiểm định kho
EDT_DAI = (0.03, 0.15)           # giây, cận dưới chưa có nguồn (đặc tả)
EDT_BANG = (250, 500, 1000, 2000, 4000)   # dải octave đo EDT; 8 kHz vượt Nyquist ở 16 kHz nên bỏ
DRR_CUA_MS = 1.0                 # ±1 ms quanh đỉnh trực tiếp; chỉ ghi, không làm ngưỡng
LECH_TRE_MAX_MS = 1.0
# |h| lớn nhất trước đỉnh trực tiếp (trừ 40 mẫu của bộ lọc trễ phân số) / |đỉnh trực tiếp|. pyroomacoustics lọc dải
# octave bằng FIR pha tuyến tính nên RIR nào cũng có rung trước đỉnh (đo 27/10: tới 0,06, cả khi chỉ dùng image source);
# ngưỡng này chỉ bắt đỉnh lạ do sai toạ độ.
TRUOC_DINH_MAX = 0.2
LAN_BOC_MAX = 40                 # bốc lại khoang tối đa

# RIR lưu và chập
RIR_DAI_S = 0.25                 # cắt RIR ở 0,25 giây sau đỉnh trực tiếp
DUOI_S = 0.25                    # bản ra = bản sạch + tối đa 0,25 giây đuôi vang
MO_CUOI_MS = 5                   # làm mờ cuối RIR khi cắt
MUC_GIONG_DBFS = -26.0
DINH_MAX_DBFS = -1.0

# Đầu vào: luật v1 (người dùng tạm chốt 27/10/2026). Ghép lời gọi chỉ giữ đủ cụm và cắt đúng ranh giới âm tiết.
CHAM_DAU_VAO = "gate_hop_v1.csv"
KET_QUA_DAU_VAO = ("dat",)
LUOT_THUONG = tuple(f"full10k_p{i:02d}" for i in range(1, 11))
LUOT_GHEP = "full10k_wake"
GHEP_GIU = {("du", ""), ("duoi", "ranh_gioi")}       # (wake_type, wake_cat)

# Bảng gán
P_RIR = 0.8
SO_BAN = {"train": 2, "dev": 1}
TY_LE_DEV_CAU = 0.10             # tỷ lệ nhóm vào dev (16/160 khoang); nhận định, chờ người dùng xem
# Băm theo gì để chia train/dev (người dùng chọn ở điểm dừng 2). Đo 27/10 bằng rir_gan trên tập v1 (câu gốc dev; vùng
# lệch = tỷ lệ vùng của bản dev so với đầu vào, mốc QA ≤ 2 điểm):
#   cau_goc   652 câu; 0 trùng chữ, nhưng 32% trùng lõi (core), 86% trùng khung (frame_id) với train; vùng lệch 1,03
#   core      661 câu; 0% trùng lõi, 70% trùng khung; vùng lệch 3,40 (trượt mốc QA); CS11 chỉ 9 câu
#   frame_id  744 câu; 0% trùng khung, 3% trùng lõi; vùng lệch 1,83; CS11 11 câu
CHIA_DEV_THEO = "frame_id"       # người dùng chọn 28/10
NHAN_CAU = "full10k/all_10k.jsonl"   # có core, frame_id theo sample_id (tính từ tts_gen/)

# RIR ĐO THẬT (người dùng chọn 28/10/2026: ưu tiên RIR thật; docs/ke_hoach_RIR_v2.md). Cả hai bộ CC BY 4.0: phải trích
# dẫn khi công bố. Mỗi xe là một "khoang" của kho đo. Kênh micro được quy về 4 vị trí của đặc tả theo ảnh trong tài
# liệu của từng bộ; kênh không thuộc 4 vị trí (micro trần sau) và ghế sau giữa không dùng.
RIR_DO_NGUON = {
    "mcvampire": dict(ten="In-Car McVAMPIRE V1.0", doi="10.5281/zenodo.12806684", giay_phep="CC BY 4.0",
                      url="https://zenodo.org/records/12806684/files/In-Car_McVAMPIRE_V1.0.zip?download=1",
                      md5="187b2d91cb8a3b0ea0ae397a3de8afe0",
                      trich_dan="K. Müller, T. Wolff: In-Car McVAMPIRE dataset V1.0, Cerence GmbH, 2024. doi:10.5281/zenodo.12806684"),
    "cavemove": dict(ten="CAVEMOVE (bản mở, 21/10/2025)", doi="10.5281/zenodo.17404917", giay_phep="CC BY 4.0",
                     url="https://zenodo.org/records/17404917/files/cavemove_dataset.zip?download=1",
                     url_tai_lieu="https://zenodo.org/records/17404917/files/dataset_documentation.pdf?download=1",
                     md5_tai_lieu="a76e68b81c8ea7c042b89c111f157040",
                     # tài liệu chỉ ghi người liên hệ (A. Symiakakis, N. Stefanakis, FORTH-ICS); tác giả bài báo chưa kiểm
                     trich_dan="CAVEMOVE, FORTH-ICS. arXiv:2508.19691; dữ liệu doi:10.5281/zenodo.17404917 (kiểm danh sách tác giả trước khi công bố)"),
}
# khoang -> (bộ, thư mục xe trong bộ, loại xe gần nhất trong LOAI_XE, split). Giữ riêng Golf (đủ ghế, đủ hai cấu hình
# micro) cho dev, như kế hoạch "giữ một xe đo cho dev"; đổi xe dev ở đây.
XE_DO = {
    "do_vclass": ("mcvampire", "Mercedes V-Class", "bay_cho", "train"),
    "do_smart": ("cavemove", "Smart_forfour", "hanga", "train"),
    "do_alfa": ("cavemove", "AlfaRomeo_146", "sedan", "train"),
    "do_crv": ("cavemove", "Honda_CR-V", "suv_c", "train"),
    "do_golf": ("cavemove", "Volkswagen_Golf", "sedan", "dev"),
}
# Kênh -> vị trí micro. CAVEMOVE "distributed" theo ảnh mục 6.x của dataset_documentation.pdf; "array" là mảng tròn
# bán kính 5 cm đặt giữa táp-lô (cả 8 kênh). McVAMPIRE: micro 1–4 trên trần hàng ghế trước (Hình 1 của tài liệu).
MICRO_DO = {
    ("cavemove", "Volkswagen_Golf", "distributed"): {1: "tap_lo", 6: "tap_lo", 2: "cot_a", 5: "cot_a", 3: "guong", 4: "guong"},
    ("cavemove", "Smart_forfour", "distributed"): {1: "tap_lo", 6: "tap_lo", 2: "cot_a", 5: "cot_a", 3: "guong", 4: "guong"},
    ("cavemove", "AlfaRomeo_146", "distributed"): {1: "tap_lo", 5: "tap_lo", 6: "tap_lo", 2: "cot_a", 4: "cot_a", 3: "guong"},
    ("cavemove", "Honda_CR-V", "distributed"): {1: "tap_lo", 5: "tap_lo", 6: "tap_lo", 2: "cot_a", 4: "cot_a", 3: "guong"},
    ("cavemove", "*", "array"): {k: "tap_lo" for k in range(1, 9)},
    ("mcvampire", "Mercedes V-Class", "tran"): {1: "tran", 2: "tran", 3: "tran", 4: "tran"},
}
# Vị trí người nói -> ghế. CAVEMOVE: d<cm> lái, pf* phụ, prl* sau trái, prr* sau phải, prm* (giữa) bỏ.
# McVAMPIRE: pos1 lái, pos2 phụ, pos3/pos6 sau trái (hàng 2/3), pos5/pos8 sau phải, pos4/pos7 (giữa) bỏ.
GHE_MCVAMPIRE = {"pos1": "lai", "pos2": "phu", "pos3": "sau_trai", "pos6": "sau_trai", "pos5": "sau_phai", "pos8": "sau_phai"}
P_RIR_DO = 0.5      # người dùng chọn 28/10 (trước 0,7). Bản có RIR: xác suất dùng RIR đo khi split có xe đo cho ghế + micro đã bốc; còn lại (và khi không có) dùng mô phỏng
