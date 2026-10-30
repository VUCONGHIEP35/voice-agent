# -*- coding: utf-8 -*-
"""Ngưỡng dùng chung. Ngưỡng CER 0,10 là mốc TẠM, chốt lại sau phiếu nghe."""



# Kiểm kỹ thuật âm thanh TTS (thuvien/kiem_am_thanh.py)
HEAD_MS = 5
HEAD_DB_MAX = -40.0
SEC_PER_SYL_MAX = 0.6
SEC_PER_SYL_MIN = 0.12

# Chấm ASR (thuvien/luat_cham.py, buoc/cham.py)
CER_NGUONG_TAM = 0.10
CAU_NGAN_MAX = 3            # câu <= số âm tiết này: đòi CER = 0
Z_ALONE_MAX = 0.05          # luật v2: Zipformer một mình chỉ được tính khi CER <= mức này (hoặc c3 cũng đạt)

# Kiểm một lượt sinh (buoc/kiem_luot.py)
SINH_LAI_MAX = 0.25         # quá tỷ lệ câu phải sinh lại này là điểm dừng

# Điểm dừng chất lượng khi chạy 10.000 câu (dieuphoi/dieu_phoi.py): tỷ lệ dat luật v1 theo vùng dưới mốc này thì
# không mở phần mới. Mốc = cận dưới Wilson của eval1000 A+B − 0,05.
NGUONG_DAT = {"Bắc": 0.74, "Nam": 0.63, "Trung": 0.23}
