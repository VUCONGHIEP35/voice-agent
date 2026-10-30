# -*- coding: utf-8 -*-
"""Bảng 24 giọng VieNeu v3 Turbo dùng trong dự án, giọng bị loại, trọng số khi gán giọng cho 10.000 câu."""



# 24 giọng dùng (vùng, giới, phong cách theo voices_v3_turbo.json / get_preset_voice, đã ghi trong runs/pilot100/manifest.jsonl).
# theo_doi: ghi chú từ thí điểm, cỡ mẫu rất nhỏ (2–5 câu mỗi giọng), chỉ là lý do để xem kỹ, chưa phải kết luận.
VOICES = {
    # Bắc: 6 nữ, 9 nam
    "Ngọc Linh": ("Bắc", "female", "doc_truyen", ""),
    "Đoan Trang": ("Bắc", "female", "tu_nhien", ""),
    "Quỳnh Anh": ("Bắc", "female", "doc_truyen", ""),
    "Mai Anh": ("Bắc", "female", "tin_tuc", ""),
    "Ngọc Huyền": ("Bắc", "female", "tu_nhien", ""),
    "Trúc Ly": ("Bắc", "female", "tu_nhien", ""),
    "Minh Đức": ("Bắc", "male", "tin_tuc", ""),
    "Phạm Tuyên": ("Bắc", "male", "tu_nhien", ""),
    "Xuân Vĩnh": ("Bắc", "male", "tu_nhien", "thí điểm 2/2 loại; tham chiếu chỉ ~1 s; 5,48 âm tiết/s"),
    "Thanh Bình": ("Bắc", "male", "doc_truyen", "thí điểm 2/2 cắt đầu, 1 câu cắt đầu sau 3 lần sinh"),
    "Quốc Tuấn": ("Bắc", "male", "tu_nhien", ""),
    "Adam bựa": ("Bắc", "male", "tu_nhien", ""),
    "Hải Đăng": ("Bắc", "male", "tu_nhien", "thí điểm CER trung bình 0,148 (3 câu)"),
    "Thiền Tâm Đức": ("Bắc", "male", "doc_truyen", ""),
    "Thiện Minh": ("Bắc", "male", "doc_truyen", ""),
    # Nam: 4 nữ, 3 nam (đã bỏ Minh Triết)
    "Thục Đoan": ("Nam", "female", "doc_truyen", ""),
    "Mỹ Duyên": ("Nam", "female", "doc_truyen", ""),
    "Kim Thanh": ("Nam", "female", "doc_truyen", ""),
    "Thùy Dung": ("Nam", "female", "tin_tuc", "thí điểm CER trung bình 0,109 (4 câu)"),
    "Adam": ("Nam", "male", "tu_nhien", ""),
    "Thái Sơn": ("Nam", "male", "doc_truyen", "thí điểm 3/4 cắt đầu, 2 câu cắt đầu sau 3 lần sinh"),
    "Đức Trí": ("Nam", "male", "doc_truyen", ""),
    # Trung: 1 nữ, 1 nam, cả hai giọng Huế
    "Ngọc Trân": ("Trung", "female", "tu_nhien", "giọng Huế; gánh một nửa phần Trung"),
    "Quang Sơn": ("Trung", "male", "tu_nhien", "giọng Huế; gánh một nửa phần Trung"),
}
VOICE_SUB_REGION = {"Ngọc Trân": "Huế", "Quang Sơn": "Huế"}
EXCLUDED = {"Minh Triết": "CER gấp 5–8 lần giọng đối chứng ở cả 4 cấu hình (runs/minh_triet_test/tom_tat.md); người nghe xác nhận khó nghe"}

# Giọng đọc nhanh (5,5–5,7 âm tiết/giây ở eval1000) nhận nửa số câu (kế hoạch chốt 25/10/2026)
VOICE_WEIGHT = {"Thùy Dung": 0.5, "Thanh Bình": 0.5, "Hải Đăng": 0.5}
