# -*- coding: utf-8 -*-
"""Hằng số bước trộn nhiễu (bước 4, preset mã E của sheet Preset_moi_truong; docs/khao_sat_nguon_nhieu_preset.md).

Quyết định người dùng:
  28/10  SNR bốc đều theo nhóm preset (bỏ cột "SNR mục tiêu" của sheet).
  29/10  Tải toàn bộ nhiễu CAVEMOVE và AISHELL-5 lên cụm; E10, E12, E14 tạm dùng mô phỏng/tổng hợp; dữ liệu chỉ dùng
         nội bộ cho đồ án, không công bố (nên điều kiện "chia sẻ tương tự" của CC BY-SA không phát sinh; vẫn ghi nguồn).
LƯU Ý: trường factors_covered của câu dùng mã E của sheet Yeu_to (yếu tố nội dung), KHÔNG phải preset. Preset của bản
trộn ghi vào trường riêng (preset_moi_truong).
"""

SNR_THEO_NHOM = {
    "yen_tinh": dict(preset=("E01", "E08"), snr_db=(15.0, 30.0)),
    "noi_do": dict(preset=("E02", "E06", "E11", "E14", "E15"), snr_db=(5.0, 20.0)),
    "on_cao": dict(preset=("E03", "E04", "E05", "E07", "E09", "E10", "E12", "E13"), snr_db=(-5.0, 15.0)),
}
PRESET_MO_PHONG = ("E10", "E12", "E14")      # chưa có nguồn mở; tạm mô phỏng/tổng hợp (29/10)

# Nguồn nhiễu. Tệp tải về là dữ liệu không tin cậy: mỗi bộ một thư mục, giải nén có kiểm đường dẫn, không chạy gì trong đó.
NGUON_NHIEU = {
    # Cùng bộ (concept 13594242) và cùng tệp zip với kho RIR đo (cauhinh.tang_cuong.RIR_DO_NGUON["cavemove"]); bản
    # 15064194 (3/2025, 3,67 GB) là phiên bản cũ hơn, không dùng.
    "cavemove": dict(ten="CAVEMOVE (bản 21/10/2025)", doi="10.5281/zenodo.17404917", giay_phep="CC BY 4.0",
                     url="https://zenodo.org/records/17404917/files/cavemove_dataset.zip?download=1",
                     md5="dec31a69f02a304a2b55b6b4db665c5e",
                     thu_muc=("noise", "ventilation", "uncontrolled_conditions"),
                     trich_dan="CAVEMOVE, FORTH-ICS. arXiv:2508.19691; dữ liệu doi:10.5281/zenodo.17404917"),
    # Trang OpenSLR không công bố md5: so Content-Length, ghi sha256 sau khi tải.
    "aishell5": dict(ten="AISHELL-5 noise (OpenSLR SLR159)", giay_phep="CC BY-SA 4.0",
                     url="https://openslr.trmal.net/resources/159/noise.tar.gz",
                     url_du_phong=("https://openslr.elda.org/resources/159/noise.tar.gz",
                                   "https://openslr.magicdatatech.com/resources/159/noise.tar.gz"),
                     trich_dan="AISHELL-5, OpenSLR SLR159, arXiv:2505.23036 (CC BY-SA 4.0)"),
}

# ---------- Giai đoạn 1 (người dùng chọn 29/10; docs/ke_hoach_nhieu_v1.md) ----------
# Chỉ CAVEMOVE có nhãn (phương án 1), chỉ 6 preset có tiếng ồn ghi thật đúng nhãn. Các preset khác: giai đoạn 2.
SEED = 20261029
PRESET_GD1 = ("E01", "E02", "E03", "E05", "E06", "E09")
# Cột "Case dùng" của sheet Preset_moi_truong (data/du_lieu_asr_tts_o_to_v0.3.xlsx, đọc 29/10). E09 không có case nào.
CASE_PRESET = {
    "E01": ("CS03", "CS06", "CS07", "CS09", "CS10"),
    "E02": ("CS01", "CS03", "CS04", "CS05", "CS06", "CS07", "CS08", "CS10", "CS11", "CS12"),
    "E03": ("CS01", "CS02", "CS06", "CS09", "CS12"),
    "E04": ("CS02", "CS08", "CS09"),
    "E05": ("CS02", "CS03"),
    "E06": ("CS03",),
    "E07": ("CS02", "CS04", "CS05", "CS11", "CS12"),
    "E08": ("CS04", "CS07", "CS10", "CS11"),
    "E09": (),
    "E10": ("CS01", "CS12"),
    "E11": ("CS05",),
    "E12": ("CS01", "CS08"),
    "E13": ("CS01",),
    "E14": ("CS02",),
    "E15": ("CS05",),
}
TY_LE_THEO_SHEET = 0.6       # 60% bốc trong preset sheet ghi cho case (giao với PRESET_GD1), 40% đều trong PRESET_GD1
# Nguồn theo preset trong CAVEMOVE (tên tệp noise/s<km/h>_w<kính>[_verN][_coarse], ventilation/v<mức>_w<kính>).
# quat="max": mức quạt cao nhất mà xe có. thay_the: dùng khi xe không có tệp nào khớp (Golf không có s0).
NGUON_PRESET = {
    "E01": dict(loai="noise", toc_do=(0, 0), kinh=(0,), nham=False, thay_the=dict(loai="ventilation", quat=1, kinh=(0,))),
    "E02": dict(loai="noise", toc_do=(40, 60), kinh=(0,), nham=False),
    "E03": dict(loai="noise", toc_do=(90, 120), kinh=(0,), nham=False),
    "E05": dict(loai="noise", toc_do=(50, 70), kinh=(2, 3), nham=False),
    "E06": dict(loai="ventilation", quat="max", kinh=(0,)),
    "E09": dict(loai="noise", toc_do=(30, 30), kinh=(0,), nham=True),
}
# Xe -> split. Golf giữ cho dev, trùng xe dev của bước RIR (cauhinh.tang_cuong.XE_DO).
XE_NHIEU = {"AlfaRomeo_146": "train", "Honda_CR-V": "train", "Smart_forfour": "train", "Volkswagen_Golf": "dev"}
CAU_HINH_NHIEU = ("distributed", "array")
KENH_TRAN = (7, 8)           # micro trần sau của CAVEMOVE (phân tán), bước RIR không dùng
SNR_LUOI = (20, 10, 5, 0)    # lưới thử ASR, dB
CAT_BIEN_S = 0.5             # bỏ 0,5 s đầu/cuối tệp nhiễu
NOI_VONG_S = 0.05            # làm mờ chỗ nối khi tệp nhiễu ngắn hơn bản
DINH_MAX_DBFS = -1.0


def nhom_snr(preset):
    """(SNR thấp, SNR cao) dB của preset theo SNR_THEO_NHOM."""
    return next(g["snr_db"] for g in SNR_THEO_NHOM.values() if preset in g["preset"])
