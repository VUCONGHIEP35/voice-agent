# -*- coding: utf-8 -*-
"""Nguồn dữ liệu duy nhất cho workbook và JSONL: lược đồ, case study, preset môi trường, yếu tố, mẫu câu."""

RATES = {"Chậm": 3.6, "Vừa": 4.5, "Nhanh": 5.4}  # âm tiết/giây, giả định

# ---------------------------------------------------------------- từ vựng kiểm soát
VOCAB = {
    "speech_act": ["Thông báo", "Xác nhận", "Câu hỏi", "Cảnh báo", "Hướng dẫn", "Xin lỗi/làm rõ", "Hội thoại"],
    "urgency": ["Thông tin", "Thấp", "Trung bình", "Cao", "Khẩn cấp"],
    "language_mix": ["Việt", "Việt + Anh"],
    "style": ["Trung tính", "Thân thiện", "Khẩn trương", "Trấn an", "Nghiêm túc/cảnh báo", "Vui tươi (trẻ em)"],
    "speaking_rate": ["Chậm", "Vừa", "Nhanh"],
    "voice_persona": ["Nữ – Bắc", "Nam – Bắc", "Nữ – Nam", "Nam – Nam", "Nữ – Trung", "Nam – Trung", "Nữ – trung tính"],
    "driving_state": ["Đỗ xe", "Nội đô", "Cao tốc", "Đường xấu", "Kẹt xe", "Hầm"],
    "cabin_type": ["Sedan xăng", "SUV xăng", "Xe điện", "MPV/7 chỗ", "Xe dịch vụ"],
    "windows": ["Đóng", "Mở một phần", "Mở hoàn toàn"],
    "music": ["Không", "Nhỏ", "Lớn"],
    "rain": ["Không", "Mưa nhỏ", "Mưa to"],
    "playback_channel": ["Loa xe (trước)", "Loa xe (toàn khoang)", "Loa ghế sau", "Bluetooth HFP", "Loa headrest"],
    "status": ["Mẫu", "Chờ thu", "Đã thu", "Đã duyệt", "Loại"],
    "norm_features": ["số", "số thập phân", "giờ/ngày/tháng/năm", "tiền VND", "đơn vị đo", "phần trăm",
                      "viết tắt", "tên riêng/địa danh", "địa chỉ", "số điện thoại", "từ mượn tiếng Anh",
                      "tần số/công suất", "ký hiệu"],
    "eval_focus": ["Độ rõ trong nhiễu (WER/CER)", "Đọc đúng số/đơn vị", "Độ trễ phát (TTFA)", "Độ tự nhiên (MOS)",
                   "Nhận biết mức khẩn cấp", "Đọc đúng tên riêng", "Ổn định giọng với câu dài",
                   "Độ dễ nghe qua Bluetooth", "Thanh điệu dưới nhiễu", "Ngắt nghỉ và ngữ điệu"],
    "lexicon_variant": ["Chuẩn chung", "Bắc", "Trung", "Nam"],
    "gender": ["Nam", "Nữ"],
    "age_group": ["Trẻ em (dưới 13)", "Thiếu niên (13–17)", "Thanh niên (18–34)", "Trung niên (35–54)", "Cao tuổi (55 trở lên)"],
    "region_dialect": ["Bắc Bộ", "Bắc Trung Bộ", "Nam Trung Bộ", "Tây Nguyên", "Nam Bộ", "Trung Bộ (chưa chia tiểu vùng)", "Giọng pha / không xác định"],
    "f0_band": ["Thấp", "Trung bình", "Cao", "Rất cao"],
    "data_origin": ["Tổng hợp hoàn toàn", "Tổng hợp trên nền ồn thật", "Thu thật"],
    "voice_source": ["TTS đa người nói", "TTS zero-shot (giọng tham chiếu có đồng ý)", "Biến đổi giọng (voice conversion)", "Giọng người thật có đồng ý", "Chưa xác định"],
    "noise_source": ["Ghi thực trong xe", "Kho âm thanh công khai", "Mô phỏng/tổng hợp", "Không ồn", "Chưa xác định"],
    "rir_source": ["Đo thật trong xe", "Mô phỏng khoang xe", "RIR công khai", "Không dùng", "Chưa xác định"],
    "lombard_applied": ["Không", "Mô phỏng", "Thật"],
    "qc_check": ["Đạt", "Không đạt", "Chưa kiểm"],
    "qc_status": ["Chưa kiểm", "Chấp nhận", "Loại", "Cần nghe lại"],
    "trigger_type": ["Hệ thống chủ động", "Đáp lệnh người dùng", "Chờ người dùng trả lời"],
    "dialect_intensity": ["Nhẹ", "Vừa", "Đậm"],
    "voice_quality": ["Bình thường", "Khàn", "Thều thào/hơi gió", "Căng/the thé", "Nghẹt mũi"],
    "speaker_role": ["Giọng thu TTS", "Người dùng (ASR)"],
    "side": ["Đầu vào (ASR)", "Đầu ra (TTS)", "Cả hai"],
    "record_method": ["Đo bằng công cụ", "Gán nhãn thủ công", "Cấu hình hệ thống", "Đo tại xe"],
}

# ---------------------------------------------------------------- lược đồ: (khóa, nhãn, kiểu, bắt buộc, mô tả, giá trị/ví dụ)
FIELDS = [
    ("sample_id", "Mã mẫu", "chuỗi", True, "Duy nhất, dạng <case_id>-<số thứ tự 3 chữ số>", "CS01-001"),
    ("case_id", "Mã case study", "chuỗi", True, "Khóa sang sheet Case_study", "CS01"),
    ("case_name", "Tên case study", "chuỗi", True, "Lấy từ Case_study, giữ nguyên để dễ lọc", "Dẫn đường"),
    ("intent", "Ý định / tình huống con", "chuỗi", True, "Tình huống cụ thể trong case study", "báo rẽ + khoảng cách"),
    ("speech_act", "Hành vi lời nói", "danh sách", True, "Trợ lý đang làm gì với câu này", "Thông báo | Xác nhận | Câu hỏi | Cảnh báo ..."),
    ("trigger_type", "Kiểu khởi phát", "danh sách", True, "Ai khởi đầu câu nói: hệ thống tự phát, đáp lại lệnh người dùng, hoặc hỏi và chờ người dùng trả lời", "Hệ thống chủ động | Đáp lệnh người dùng | Chờ người dùng trả lời"),
    ("asr_input", "Có đầu vào giọng nói (tự tính)", "danh sách", False, "Không nếu hệ thống tự phát và không có lời người dùng; Có nếu đáp lệnh hoặc chờ trả lời. Quyết định yếu tố phía ASR có áp dụng hay không", "Có | Không"),
    ("urgency", "Mức khẩn cấp", "danh sách", True, "Quyết định ngữ điệu, tốc độ, âm báo kèm", "Thông tin → Khẩn cấp"),
    ("text_raw", "Văn bản gốc", "chuỗi", True, "Câu trợ lý sinh ra, còn số, viết tắt, ký hiệu", "Sau 200 m, rẽ trái ..."),
    ("text_spoken", "Văn bản đọc (đã chuẩn hóa)", "chuỗi", True, "Dạng chữ đầy đủ đưa vào TTS; số, đơn vị, viết tắt đã viết thành lời", "Sau hai trăm mét, rẽ trái ..."),
    ("language_mix", "Ngôn ngữ", "danh sách", True, "Việt thuần hay có từ tiếng Anh", "Việt | Việt + Anh"),
    ("norm_features", "Đặc điểm cần chuẩn hóa", "danh sách nhiều giá trị", False, "Các loại cần chuẩn hóa trong câu, phân tách bằng dấu chấm phẩy", "số; đơn vị đo"),
    ("style", "Phong cách giọng", "danh sách", True, "Mục tiêu phong cách khi đọc", "Trung tính | Khẩn trương | Trấn an ..."),
    ("speaking_rate", "Tốc độ đọc mục tiêu", "danh sách", True, "Chậm / Vừa / Nhanh", "Vừa"),
    ("voice_persona", "Giọng đọc", "danh sách", True, "Giới tính và vùng miền của giọng", "Nữ – Bắc"),
    ("speaker_id", "Mã người nói", "chuỗi", True, "Khóa sang sheet Ho_so_nguoi_noi (hồ sơ F0, vùng miền, chất giọng)", "SPK001"),
    ("lexicon_variant", "Biến thể từ vựng", "danh sách", True, "Từ ngữ trong câu theo vùng nào; “Chuẩn chung” nếu không dùng từ địa phương (xem Tu_dia_phuong)", "Chuẩn chung | Bắc | Trung | Nam"),
    ("speaker_gender", "Giới tính người nói (tra từ hồ sơ)", "danh sách", False, "Tự tra từ speaker_id trong Ho_so_nguoi_noi; không nhập tay", "Nữ"),
    ("speaker_dialect", "Vùng giọng người nói (tra từ hồ sơ)", "danh sách", False, "Tự tra từ speaker_id trong Ho_so_nguoi_noi; không nhập tay", "Bắc Bộ"),
    ("speaker_f0_band", "Dải tần số giọng (tra từ hồ sơ)", "danh sách", False, "Thấp / Trung bình / Cao / Rất cao; tự tra từ speaker_id; ngưỡng ở Ho_so_nguoi_noi", "Cao"),
    ("est_duration_s", "Thời lượng ước lượng (giây)", "số", False, "Công thức: số âm tiết ÷ tốc độ giả định; tham số ở Tong_quan", "4,2"),
    ("env_id", "Mã preset môi trường", "danh sách", True, "Khóa sang sheet Preset_moi_truong (E01–E17)", "E02"),
    ("driving_state", "Trạng thái lái", "danh sách", True, "Lấy từ preset, có thể ghi đè theo mẫu thực tế", "Nội đô"),
    ("speed_kmh", "Tốc độ xe (km/h)", "số nguyên", True, "Tốc độ lúc thu hoặc mô phỏng", "40"),
    ("cabin_noise_dBA", "Ồn nền trong xe (dB(A), chỉ dẫn)", "chuỗi khoảng", True, "Khoảng chỉ dẫn, thay bằng số đo thực khi có", "55–65"),
    ("snr_target_dB", "SNR mục tiêu (dB)", "số nguyên", True, "Mức giọng TTS hơn nền ồn tại tai người lái; đây là mục tiêu thiết kế", "12"),
    ("cabin_type", "Loại xe", "danh sách", True, "Ảnh hưởng đến âm học khoang xe", "Sedan xăng"),
    ("hvac_level", "Mức quạt điều hòa (0–5)", "số nguyên", False, "0 = tắt", "2"),
    ("windows", "Cửa kính", "danh sách", False, "Đóng / mở một phần / mở hoàn toàn", "Đóng"),
    ("music", "Nhạc đang phát", "danh sách", False, "Không / Nhỏ / Lớn", "Không"),
    ("passengers", "Số người trên xe", "số nguyên", False, "Gồm người lái", "1"),
    ("rain", "Mưa", "danh sách", False, "Không / Mưa nhỏ / Mưa to", "Không"),
    ("playback_channel", "Kênh phát", "danh sách", True, "Đường phát âm thanh trong xe", "Loa xe (trước)"),
    ("eval_focus", "Trọng tâm đánh giá", "danh sách", True, "Chỉ số chính cần đo trên mẫu này", "Đọc đúng số/đơn vị"),
    ("data_origin", "Nguồn gốc dữ liệu", "danh sách", True, "Tổng hợp hoàn toàn, tổng hợp trên nền ồn thật hoặc thu thật; để tách tập vàng thật khỏi dữ liệu tổng hợp", "Tổng hợp hoàn toàn"),
    ("voice_source", "Nguồn giọng", "danh sách", True, "Cách tạo giọng; giọng người thật phải có đồng ý bằng văn bản", "TTS zero-shot (giọng tham chiếu có đồng ý)"),
    ("generator_model", "Mô hình sinh giọng", "chuỗi", False, "Tên và phiên bản mô hình, kèm giấy phép đã kiểm; ghi để truy vết", "(điền khi sinh)"),
    ("noise_source", "Nguồn tiếng ồn", "danh sách", True, "Ồn ghi thật, từ kho công khai hay mô phỏng", "Kho âm thanh công khai"),
    ("rir_source", "Nguồn đáp ứng xung (RIR)", "danh sách", True, "RIR đo thật, mô phỏng hay công khai", "Mô phỏng khoang xe"),
    ("lombard_applied", "Hiệu ứng Lombard", "danh sách", False, "Không, mô phỏng hay thật", "Mô phỏng"),
    ("snr_actual_dB", "SNR thực tế sau trộn (dB)", "số", False, "Pipeline điền, đo trên đoạn có tiếng nói; khác snr_target_dB là mục tiêu thiết kế", "11,8"),
    ("qc_asr_wer_pct", "WER kiểm tra (%)", "số", False, "WER của ASR trên mẫu; ngưỡng đặt riêng theo vùng", "2,4"),
    ("qc_dialect_match", "Đúng vùng giọng", "danh sách", False, "Bộ phân loại phương ngữ có đoán đúng vùng mục tiêu hay không", "Đạt | Không đạt | Chưa kiểm"),
    ("qc_f0_in_band", "F0 trong dải khai báo", "danh sách", False, "F0 đo được có nằm trong dải f0_band của người nói hay không", "Đạt | Không đạt | Chưa kiểm"),
    ("qc_native_review", "Nghe kiểm bản ngữ", "danh sách", False, "Người bản ngữ từng vùng nghe và chấm", "Đạt | Không đạt | Chưa kiểm"),
    ("qc_status", "Kết quả kiểm tra tổng", "danh sách", True, "Chấp nhận, loại hoặc cần nghe lại", "Chưa kiểm"),
    ("status", "Trạng thái", "danh sách", True, "Tiến độ thu dữ liệu", "Mẫu | Chờ thu | Đã thu | Đã duyệt | Loại"),
    ("notes", "Ghi chú", "chuỗi", False, "Điểm cần chú ý khi thu hoặc kiểm tra", "Thống nhất cách đọc “bar”"),
]
FIELD_KEYS = [f[0] for f in FIELDS]
REQUIRED = {f[0] for f in FIELDS if f[3]}

# ---------------------------------------------------------------- case study
CASES = [
    ("CS01", "Dẫn đường", "Chỉ đường từng chặng: rẽ, khoảng cách, tên đường, đích đến.",
     "báo rẽ; báo khoảng cách; báo đã đến; đổi lộ trình; báo làn đường",
     "Đọc đúng số, đơn vị, tên đường và địa chỉ; câu ngắn, ngắt nghỉ rõ; phát đúng lúc (độ trễ thấp).",
     "Đọc sai tên đường hoặc số nhà (ngõ, ngách, hẻm); nuốt âm cuối khi có nhiễu.", "E02; E03; E12; E10", "Cao"),
    ("CS02", "Cảnh báo an toàn (ADAS)", "Cảnh báo va chạm, lệch làn, mệt mỏi, điểm mù, quá tốc độ.",
     "va chạm phía trước; lệch làn; người lái mệt; điểm mù; vượt tốc độ",
     "Độ rõ cao nhất trong nhiễu; câu rất ngắn; mức khẩn cấp nghe được qua giọng; đi kèm âm báo.",
     "Câu dài làm chậm phản ứng; giọng quá bình thản; bị nhạc hoặc nhiễu che.", "E03; E05; E07; E04", "Cao"),
    ("CS03", "Điều khiển xe", "Điều chỉnh điều hòa, ghế, cửa kính, cửa sổ trời, đèn trong xe bằng giọng nói.",
     "đặt nhiệt độ; sưởi ghế; hạ kính; bật sấy kính; chỉnh quạt",
     "Xác nhận ngắn và chính xác thông số (nhiệt độ, mức, vị trí).",
     "Đọc nhầm mức; xác nhận sai vị trí (ghế lái hay ghế phụ).", "E01; E02; E06", "Trung bình"),
    ("CS04", "Giải trí (nhạc, radio)", "Phát nhạc, chuyển kênh radio, chỉnh âm lượng.",
     "phát danh sách; chuyển kênh FM; chỉnh âm lượng; hỏi đang phát gì",
     "Đọc đúng tên bài, kênh, từ mượn tiếng Anh; phối hợp hạ nhạc (ducking) khi trợ lý nói.",
     "Phát âm tên tiếng Anh không nhất quán; giọng bị nhạc che.", "E07; E02; E08", "Trung bình"),
    ("CS05", "Điện thoại và tin nhắn", "Báo cuộc gọi, đọc tin nhắn, gọi theo số hoặc tên.",
     "cuộc gọi đến; đọc tin nhắn; gọi số; hỏi nghe máy",
     "Đọc số điện thoại từng chữ số; đọc đúng tên người và xưng hô; chất lượng ổn định khi qua Bluetooth.",
     "Đọc sai số; đọc nội dung riêng tư ra loa chung khi có hành khách.", "E11; E02; E07", "Cao"),
    ("CS06", "Trạng thái xe và bảo dưỡng", "Báo áp suất lốp, nhiên liệu, bảo dưỡng định kỳ, đèn báo.",
     "áp suất lốp; nhiên liệu còn lại; lịch bảo dưỡng; đèn báo lỗi",
     "Đọc đúng đơn vị kỹ thuật (bar, km, %) và ngày tháng; thể hiện mức ưu tiên.",
     "Đơn vị lạ bị đọc sai hoặc không nhất quán; ngày tháng đọc thành chuỗi số.", "E01; E02; E03", "Trung bình"),
    ("CS07", "Sạc xe điện và trạm nhiên liệu", "Hỏi tình trạng pin, tìm trạm sạc, ước tính thời gian và chi phí sạc.",
     "pin còn lại; trạm sạc gần nhất; thời gian sạc; chi phí; công suất sạc",
     "Đọc đúng số thập phân, kW, %, tiền VND, thời gian.",
     "Đọc sai số tiền (nghìn, triệu, đồng); nhầm đơn vị công suất và năng lượng.", "E01; E08; E02", "Trung bình"),
    ("CS08", "Giao thông và thời tiết", "Báo tắc đường, tai nạn, giờ đến dự kiến, dự báo thời tiết.",
     "tắc đường; giờ đến; thời tiết; thay đổi lộ trình",
     "Nêu thông tin theo thứ tự ưu tiên; đọc đúng giờ, khoảng giá trị, độ C.",
     "Đọc khoảng giá trị (27–31) thành chuỗi số; thông tin quá dài khi đang lái.", "E12; E04; E02", "Trung bình"),
    ("CS09", "Khẩn cấp và cứu hộ", "Phát hiện va chạm nghiêm trọng, sự cố pin, gọi cấp cứu và cứu hộ.",
     "va chạm mạnh; hỏi thăm; gửi vị trí; cảnh báo pin; hướng dẫn rời xe",
     "Giọng trấn an, rõ, tốc độ chậm; hướng dẫn hành động ngắn; không gây hoảng.",
     "Giọng máy móc thiếu trấn an; câu dài; đọc sai số khẩn cấp.", "E03; E01; E04", "Cao"),
    ("CS10", "Hội thoại và gợi ý chủ động", "Gợi ý lịch trình, quán gần đây, nhắc việc, hỏi đáp tự nhiên.",
     "nhắc lịch họp; gợi ý quán; nhắc mua đồ; hỏi đáp chung",
     "Ngữ điệu tự nhiên, câu dài hơn, ngắt nghỉ đúng; phân biệt câu hỏi và câu kể; chuyển mã Anh–Việt.",
     "Giọng đều đều; không phân biệt câu hỏi; câu quá dài khi lái.", "E01; E02; E08", "Trung bình"),
    ("CS11", "Hành khách và trẻ em", "Thông báo cho khoang sau, nhắc dây an toàn ghế sau, nói chuyện với trẻ.",
     "nói với trẻ; nhắc dây an toàn; chế độ yên tĩnh khoang sau; định tuyến loa",
     "Định tuyến loa theo vùng; giọng phù hợp trẻ em; không làm người lái phân tâm.",
     "Thông báo ghế sau vang ra loa trước; giọng trẻ em kém tự nhiên.", "E02; E07; E08", "Trung bình"),
    ("CS12", "Lỗi, làm rõ và ngoại tuyến", "Xử lý khi không nghe rõ, trùng tên, mất mạng, tính năng chưa hỗ trợ.",
     "không nghe rõ; hỏi lại khi trùng tên; mất mạng; chức năng không hỗ trợ",
     "Diễn đạt lịch sự, ngắn, nhất quán; không đổ lỗi cho người dùng; ổn định khi lặp lại nhiều lần.",
     "Lặp lại nhàm hoặc khó chịu; giọng khác nhau giữa các lần hỏi lại.", "E02; E03; E07; E10", "Cao"),
]
_EXTRA_ENV = {"CS01": "E13", "CS02": "E14", "CS05": "E15", "CS09": "E17", "CS12": "E16"}
CASES = [c[:6] + (c[6] + "; " + _EXTRA_ENV[c[0]],) + c[7:] if c[0] in _EXTRA_ENV else c for c in CASES]
CASE_NAME = {c[0]: c[1] for c in CASES}

# ---------------------------------------------------------------- preset môi trường
# (id, tên, mô tả, trạng thái, tốc độ, ồn dB(A) chỉ dẫn, nguồn ồn chính, SNR mục tiêu, hvac, cửa kính, nhạc, mưa, hành khách, mục tiêu đánh giá)
PRESETS = [
    ("E01", "Đỗ xe, yên tĩnh", "Xe đứng yên, máy tắt hoặc chạy cầm chừng.", "Đỗ xe", 0, "35–45", "Gần như không có; tiếng ngoài trời", 10, 0, "Đóng", "Không", "Không", 1, "Độ tự nhiên, ngắt nghỉ, đọc đúng số"),
    ("E02", "Nội đô 30–50 km/h", "Chạy trong phố, xe máy và còi xung quanh.", "Nội đô", 40, "55–65", "Lốp, giao thông ngoài, còi", 12, 2, "Đóng", "Không", "Không", 1, "Độ rõ trong nhiễu vừa, đọc tên riêng"),
    ("E03", "Cao tốc 100–120 km/h", "Chạy tốc độ cao, gió và lốp lớn.", "Cao tốc", 110, "68–75", "Gió, lốp, mặt đường", 15, 3, "Đóng", "Không", "Không", 2, "Độ rõ khi ồn cao, nhận biết khẩn cấp"),
    ("E04", "Mưa lớn, gạt nước", "Mưa to, gạt nước chạy liên tục.", "Nội đô", 60, "65–75", "Mưa, gạt nước, lốp trên mặt ướt", 15, 4, "Đóng", "Không", "Mưa to", 1, "Độ rõ với nhiễu xung lặp"),
    ("E05", "Mở cửa kính khi chạy", "Cửa kính mở hoàn toàn, gió lùa vào khoang.", "Nội đô", 60, "72–85", "Gió lùa, giao thông ngoài", 15, 1, "Mở hoàn toàn", "Không", "Không", 1, "Độ rõ phụ âm xát, mức khẩn cấp"),
    ("E06", "Điều hòa quạt tối đa", "Quạt gió mức cao nhất khi trời nóng.", "Nội đô", 20, "55–65", "Quạt điều hòa", 12, 5, "Đóng", "Không", "Không", 1, "Độ rõ phụ âm, đọc đúng mức/thông số"),
    ("E07", "Nhạc lớn và hành khách nói chuyện", "Nhạc to, nhiều người nói chuyện cùng lúc.", "Nội đô", 40, "65–75", "Nhạc, tiếng người (babble)", 15, 2, "Đóng", "Lớn", "Không", 4, "Độ rõ khi có tiếng người, hạ nhạc (ducking)"),
    ("E08", "Xe điện chạy chậm, rất yên tĩnh", "Xe điện ở tốc độ thấp, nền ồn thấp.", "Nội đô", 20, "40–50", "Gió nhẹ, lốp, tiếng rít điện", 10, 2, "Đóng", "Không", "Không", 1, "Độ tự nhiên khi nền yên, lỗi nhỏ lộ rõ"),
    ("E09", "Đường xấu, rung xóc", "Mặt đường gồ ghề, gờ giảm tốc.", "Đường xấu", 40, "65–75", "Lốp, rung, tiếng cấu trúc", 15, 2, "Đóng", "Không", "Không", 1, "Độ rõ với nhiễu xung ngắt quãng"),
    ("E10", "Hầm chui, dưới gầm cầu", "Phản xạ âm mạnh, vang, nền ồn tăng.", "Hầm", 50, "70–80", "Phản xạ tiếng lốp, tiếng động cơ xe khác", 15, 2, "Đóng", "Không", "Không", 1, "Độ rõ với vang, mất mạng giữa chừng"),
    ("E11", "Cuộc gọi qua Bluetooth", "Phát qua Bluetooth hands-free, băng thông hẹp.", "Nội đô", 40, "55–65", "Nền nội đô, nén tín hiệu Bluetooth", 12, 2, "Đóng", "Không", "Không", 1, "Độ dễ nghe qua Bluetooth, đọc số điện thoại"),
    ("E12", "Kẹt xe, còi inh ỏi", "Đi chậm hoặc dừng, còi xe liên tục.", "Kẹt xe", 10, "65–75", "Còi xe, động cơ xe quanh", 15, 3, "Đóng", "Không", "Không", 1, "Độ rõ với xung còi, câu bị che âm tiết"),
]
PRESETS += [
    ("E13", "Chuyển trạng thái giữa câu", "Nền ồn đổi giữa câu: vào hầm hoặc mở kính khi đang đọc.", "Hầm", 50, "60–80 (đổi giữa câu)", "Chuyển từ nền nội đô sang phản xạ trong hầm", 12, 2, "Đóng", "Không", "Không", 1, "Độ rõ đoạn cuối câu khi SNR tụt giữa chừng"),
    ("E14", "Âm báo xe chồng thông báo", "Chuông cảnh báo, xi-nhan hoặc bíp chồng lên giọng trợ lý.", "Nội đô", 40, "55–65 (kèm âm báo)", "Nền nội đô và âm báo của xe", 12, 2, "Đóng", "Không", "Không", 1, "Độ rõ khi bị âm báo chồng"),
    ("E15", "Cuộc gọi qua điện thoại (CarPlay, Android Auto)", "Giọng đi qua codec cuộc gọi băng hẹp của điện thoại.", "Nội đô", 40, "55–65", "Nền nội đô, nén codec cuộc gọi", 12, 2, "Đóng", "Không", "Không", 1, "Độ dễ nghe qua codec cuộc gọi, đọc số điện thoại"),
    ("E16", "Mạng yếu khi TTS chạy đám mây", "Trễ biến động và mất gói trên đường truyền.", "Cao tốc", 100, "68–75", "Nền cao tốc; mạng mất gói và trễ", 15, 3, "Đóng", "Không", "Không", 1, "Độ trễ phát, tỷ lệ ngắt quãng, chuyển sang giọng trên xe"),
    ("E17", "Loa quá tải, âm lượng cao", "Nhạc và ồn cao khiến phải tăng âm lượng, loa bị méo.", "Nội đô", 40, "65–75", "Nhạc lớn, loa bị cắt đỉnh", 15, 2, "Đóng", "Lớn", "Không", 2, "Độ rõ khi loa méo"),
]
PRESET = {p[0]: p for p in PRESETS}

# ---------------------------------------------------------------- yếu tố ảnh hưởng
# (nhóm, mã, yếu tố, cách thay đổi, khoảng/giá trị chỉ dẫn, cách mô phỏng hoặc đo, ảnh hưởng đến TTS, chỉ số đánh giá, ưu tiên)
FACTORS = [
    ("Nhiễu nền khoang xe", "A01", "Tiếng lốp và mặt đường", "Loại mặt đường (nhựa mịn, bê tông, sỏi); tốc độ", "Tăng theo tốc độ, năng lượng ở dải thấp đến trung", "Ghi nhiễu thật bằng mic đặt ở tai người lái; trộn với TTS ở SNR xác định", "Che nguyên âm và thanh điệu", "WER/CER theo SNR; nghe kiểm thanh điệu", "Cao"),
    ("Nhiễu nền khoang xe", "A02", "Tiếng gió", "Tốc độ; cửa kính; cửa sổ trời", "Tăng mạnh khi mở cửa kính", "Ghi âm ở 60 và 100 km/h với cửa đóng và cửa mở", "Nhiễu băng rộng, che phụ âm xát", "WER; độ rõ phụ âm", "Cao"),
    ("Nhiễu nền khoang xe", "A03", "Động cơ hoặc mô-tơ điện", "Xăng/dầu/hybrid/điện; vòng tua", "Xe điện nền thấp nhưng có tiếng rít điện", "Ghi âm theo từng loại xe ở tải khác nhau", "Xe điện làm lỗi nhỏ của TTS lộ rõ hơn", "MOS; WER", "Trung bình"),
    ("Nhiễu nền khoang xe", "A04", "Quạt điều hòa", "Mức 0–5; hướng gió", "Mức cao tạo nhiễu băng rộng ở trung–cao", "Đo ở từng mức quạt", "Che phụ âm, giảm độ rõ", "WER theo mức quạt", "Trung bình"),
    ("Nhiễu nền khoang xe", "A05", "Mưa và gạt nước", "Mưa nhỏ/to; tốc độ gạt", "Mưa to là một trong các nền ồn cao", "Ghi âm khi mưa thật hoặc dùng bản ghi chuẩn", "Nhiễu xung lặp theo nhịp gạt", "WER; ổn định giọng", "Trung bình"),
    ("Nhiễu nền khoang xe", "A06", "Giao thông bên ngoài (còi, xe máy)", "Mật độ xe máy; còi liên tục", "Xung ngắn, cường độ cao", "Thu âm nội đô giờ cao điểm", "Che mất âm tiết ngắn; cảnh báo ngắn dễ bị nuốt", "WER; tỷ lệ âm tiết bị mất", "Cao"),
    ("Nhiễu nền khoang xe", "A07", "Nhạc hoặc radio đang phát", "Nhỏ/lớn; có lời hay không lời; bật/tắt ducking", "Cạnh tranh phổ với giọng nói", "Trộn bản nhạc với TTS, so sánh có và không ducking", "Che giọng khi nhạc có lời", "WER có/không ducking", "Cao"),
    ("Nhiễu nền khoang xe", "A08", "Hành khách nói chuyện, trẻ em", "Số người; trẻ khóc hoặc la", "Tiếng người cạnh tranh, khó lọc", "Trộn nhiễu nhiều người nói (babble)", "Gây phân tâm, làm giảm độ rõ", "WER; đánh giá mức phân tâm", "Cao"),
    ("Nhiễu nền khoang xe", "A09", "Rung và tiếng cấu trúc", "Đường xấu, gờ giảm tốc, mặt cầu", "Xung va chạm ngắt quãng", "Ghi âm trên đường xấu", "Ngắt âm tiết ngắn", "WER", "Thấp"),
    ("Nhiễu nền khoang xe", "A10", "Hầm, cầu, gầm cầu", "Phản xạ lớn, nền ồn tăng, có thể mất mạng", "Vang dài", "Dùng đáp ứng xung phòng (RIR) hoặc ghi âm thực", "Vang làm nhòe âm tiết; mất mạng ảnh hưởng TTS đám mây", "WER; hoạt động ngoại tuyến", "Trung bình"),
    ("Âm học khoang xe", "B01", "Kích thước và vật liệu nội thất", "Sedan/SUV/MPV; da, vải, kính", "Thời gian vang khác nhau theo xe", "Đo hoặc mô phỏng đáp ứng xung (RIR) cho từng xe", "Vang làm nhòe âm tiết, đổi nhịp nghe", "WER; độ rõ (STOI)", "Trung bình"),
    ("Âm học khoang xe", "B02", "Vị trí và số lượng loa", "4, 6, 8 loa trở lên; loa headrest", "Phổ và hướng âm khác nhau", "Đo đáp ứng tần số tại từng ghế", "Một số dải bị yếu hoặc nhấn quá mức", "Độ rõ; MOS", "Trung bình"),
    ("Âm học khoang xe", "B03", "Vị trí tai người nghe", "Ghế lái, ghế phụ, ghế sau", "Mức và vang khác nhau theo ghế", "Đo RIR tại từng ghế", "Người ngồi sau nghe kém hơn", "WER theo ghế", "Trung bình"),
    ("Âm học khoang xe", "B04", "Mức phát và bù âm theo tốc độ", "Âm lượng mặc định; bù theo tốc độ", "Phụ thuộc cấu hình hệ thống âm thanh xe", "Cấu hình bù âm theo tốc độ, đo ở nhiều mức", "TTS cần to hơn khi nền ồn tăng", "SNR tại tai; độ rõ", "Cao"),
    ("Âm học khoang xe", "B05", "Tiếng vọng và ngắt lời (AEC, barge-in)", "Người dùng nói chen khi TTS đang phát", "Tiếng TTS lọt vào mic", "Kịch bản nói chen trong xe", "Ảnh hưởng nhận dạng giọng nói và việc dừng TTS", "Tỷ lệ ngắt đúng; WER ASR", "Trung bình"),
    ("Âm học khoang xe", "B06", "Vùng âm thanh (zone)", "Chỉ người lái; toàn khoang; riêng ghế sau", "Thông báo gửi đúng vùng", "Kiểm thử định tuyến loa", "Lộ nội dung hoặc làm phiền người không liên quan", "Tỷ lệ phát đúng vùng", "Trung bình"),
    ("Chuỗi tín hiệu", "C01", "Tần số lấy mẫu và băng thông", "16 kHz; 22,05 kHz; 24 kHz; 44,1–48 kHz", "Băng thông thấp mất thông tin ở dải cao", "Tạo cùng một câu ở nhiều tần số lấy mẫu", "Mất phụ âm xát, âm nghe nghẹt", "MOS; độ rõ", "Trung bình"),
    ("Chuỗi tín hiệu", "C02", "Bluetooth (HFP, A2DP)", "HFP băng hẹp (8 kHz) hoặc rộng (16 kHz); A2DP", "Chất lượng giảm khi nén", "Chạy TTS qua bộ mã hóa/giải mã Bluetooth", "Mất chi tiết, tiếng rè, nghe kém", "WER qua Bluetooth", "Cao"),
    ("Chuỗi tín hiệu", "C03", "Chuẩn hóa độ lớn và nén động", "Mục tiêu độ lớn (LUFS); nén động (DRC)", "Cần ổn định giữa các câu và giữa các giọng", "Đo độ lớn từng câu", "Câu to nhỏ không đều gây khó chịu", "Độ lệch độ lớn giữa các câu", "Trung bình"),
    ("Chuỗi tín hiệu", "C04", "Độ trễ và phát luồng", "Thời gian đến âm đầu (TTFA); kích thước đoạn", "Cảnh báo cần trễ rất thấp", "Đo TTFA ở nhiều độ dài câu", "Trễ làm mất giá trị của cảnh báo và dẫn đường", "TTFA (p50, p95)", "Cao"),
    ("Chuỗi tín hiệu", "C05", "Ưu tiên và ngắt thông báo", "Cảnh báo > dẫn đường > giải trí", "Quy tắc xếp hàng và ngắt", "Kịch bản nhiều thông báo cùng lúc", "Thông báo quan trọng bị cắt hoặc chờ", "Tỷ lệ phát đúng thứ tự", "Cao"),
    ("Chuỗi tín hiệu", "C06", "Chạy trên thiết bị và trên đám mây", "Mất mạng; lượng tử hóa; giới hạn bộ nhớ", "Chất lượng có thể giảm khi nén mô hình", "So sánh bản đầy đủ và bản nén", "Giảm chất lượng giọng; mất mạng giữa chừng", "MOS; WER; tỷ lệ phục vụ được ngoại tuyến", "Trung bình"),
    ("Người nghe và ngữ cảnh lái", "D01", "Tải nhận thức của người lái", "Thấp (đỗ xe) đến cao (cao tốc, kẹt xe, mưa)", "Tải càng cao càng cần câu ngắn", "Phân loại kịch bản theo tải", "Câu dài hoặc nhiều thông tin gây phân tâm", "Độ dài câu; đánh giá của người nghe", "Cao"),
    ("Người nghe và ngữ cảnh lái", "D02", "Tuổi và thính lực", "Người lớn tuổi có thể giảm nghe ở dải cao", "Cần tốc độ chậm hơn và độ rõ cao hơn", "Thử nghiệm với nhóm người nghe lớn tuổi", "Phụ âm dải cao khó nghe", "Độ rõ theo nhóm tuổi", "Trung bình"),
    ("Người nghe và ngữ cảnh lái", "D03", "Mức khẩn cấp", "Thông tin → Thấp → Trung bình → Cao → Khẩn cấp", "Ngữ điệu, tốc độ, âm báo thay đổi theo mức", "Dán nhãn mức khẩn cấp cho từng mẫu", "Giọng không đúng mức khẩn cấp gây phản ứng sai", "Nhận biết mức khẩn cấp bởi người nghe", "Cao"),
    ("Người nghe và ngữ cảnh lái", "D04", "Thời điểm trong ngày", "Ban ngày/ban đêm", "Ban đêm cần giọng dịu và mức nhỏ hơn", "Tạo bản đọc nhẹ cho ban đêm", "Giọng gắt hoặc quá to gây khó chịu", "Đánh giá thoải mái của người nghe", "Thấp"),
    ("Người nghe và ngữ cảnh lái", "D05", "Quyền riêng tư và số người trên xe", "Chỉ người lái; có hành khách", "Nội dung nhạy cảm không nên phát ra loa chung", "Kịch bản có hành khách", "Lộ tin nhắn, cuộc gọi cá nhân", "Tỷ lệ đúng chính sách riêng tư", "Trung bình"),
    ("Ngôn ngữ tiếng Việt", "E01", "Giọng vùng miền", "Bắc, Trung, Nam; giọng nam/nữ", "Khác biệt về thanh điệu và phát âm", "Dùng nhiều giọng khác nhau trong cùng bộ dữ liệu", "Giọng không quen thuộc làm giảm độ dễ hiểu", "Đánh giá theo vùng miền người nghe", "Cao"),
    ("Ngôn ngữ tiếng Việt", "E02", "Thanh điệu dưới nhiễu", "Hỏi và ngã; sắc và nặng; huyền và ngang", "Thanh điệu dễ nhầm khi ồn", "Cặp câu tối thiểu (minimal pair) trong nhiễu", "Nghe nhầm từ khi nhiễu che đường nét cao độ", "Tỷ lệ nghe đúng thanh điệu", "Cao"),
    ("Ngôn ngữ tiếng Việt", "E03", "Chuẩn hóa số, giờ, ngày, tiền, đơn vị", "Số, số thập phân, giờ, ngày tháng năm, VND, đơn vị đo", "Đọc theo thói quen nói của người Việt", "Bộ chuẩn hóa văn bản dùng chung + bộ kiểm thử", "Đọc sai hoặc đọc từng chữ số làm nhầm thông tin", "Tỷ lệ câu chuẩn hóa đúng", "Cao"),
    ("Ngôn ngữ tiếng Việt", "E04", "Tên đường, địa danh, địa chỉ", "Ngõ, ngách, hẻm; tên đơn vị hành chính có thể thay đổi", "Cần từ điển được cập nhật", "Danh sách tên riêng kiểm thử, cập nhật định kỳ", "Đọc sai tên làm lạc đường", "Tỷ lệ đọc đúng tên riêng", "Cao"),
    ("Ngôn ngữ tiếng Việt", "E05", "Từ mượn và chuyển mã Anh–Việt", "Tên bài hát, thương hiệu, thuật ngữ xe", "Cần quy tắc thống nhất", "Danh sách từ mượn kèm cách đọc chuẩn", "Phát âm lúc Anh lúc Việt gây khó hiểu", "Tỷ lệ đọc đúng từ mượn", "Trung bình"),
    ("Ngôn ngữ tiếng Việt", "E06", "Xưng hô và từ đệm", "Anh, chị, bạn, quý khách; từ lịch sự", "Cần nhất quán toàn hệ thống", "Hướng dẫn viết câu cho trợ lý", "Xưng hô không hợp làm giảm cảm giác tự nhiên", "Đánh giá của người dùng", "Thấp"),
    ("Ngôn ngữ tiếng Việt", "E07", "Viết tắt và ký hiệu", "QL, TP.HCM, km/h, °C, %, kW", "Cần bảng ánh xạ", "Bảng viết tắt kèm cách đọc", "Đọc từng chữ hoặc bỏ sót", "Tỷ lệ viết tắt đọc đúng", "Cao"),
    ("Ngôn ngữ tiếng Việt", "E08", "Độ dài câu và ngắt nghỉ", "Cảnh báo ngắn; hội thoại dài hơn", "Đề xuất: cảnh báo khẩn cấp dưới khoảng 8–10 âm tiết (cần kiểm chứng)", "Thử nghiệm độ dài với người nghe", "Câu dài làm chậm phản ứng", "Thời gian phản ứng; độ rõ", "Cao"),
]

# ---------------------------------------------------------------- mẫu câu
# (case, n, ý định, hành vi, khẩn cấp, raw, spoken, ngôn ngữ, đặc điểm chuẩn hóa, phong cách, tốc độ, giọng, env, xe, kênh, người, trọng tâm, ghi chú)
S = []
def add(case, n, intent, act, urg, raw, spoken, lang, feats, style, rate, voice, env, cabin, channel, pax, focus, notes="", lex="Chuẩn chung"):
    S.append(dict(case=case, n=n, intent=intent, act=act, urg=urg, raw=raw, spoken=spoken, lang=lang, feats=feats,
                  style=style, rate=rate, voice=voice, env=env, cabin=cabin, channel=channel, pax=pax, focus=focus, notes=notes, lex=lex))

add("CS01", 1, "báo rẽ + khoảng cách", "Hướng dẫn", "Thấp",
    "Sau 200 m, rẽ trái vào đường Nguyễn Văn Cừ.",
    "Sau hai trăm mét, rẽ trái vào đường Nguyễn Văn Cừ.",
    "Việt", "số; đơn vị đo; tên riêng/địa danh", "Trung tính", "Vừa", "Nữ – Bắc", "E02", "Sedan xăng", "Loa xe (trước)", None,
    "Đọc đúng tên riêng")
add("CS01", 2, "báo đã đến + địa chỉ", "Thông báo", "Thông tin",
    "Bạn đã đến nơi. Điểm đến nằm bên phải, số 15 ngõ 28 Chùa Bộc, Q. Đống Đa.",
    "Bạn đã đến nơi. Điểm đến nằm bên phải, số mười lăm ngõ hai mươi tám Chùa Bộc, quận Đống Đa.",
    "Việt", "số; địa chỉ; viết tắt; tên riêng/địa danh", "Thân thiện", "Vừa", "Nam – Bắc", "E12", "SUV xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Thống nhất cách đọc “Q.” thành “quận”")
add("CS01", 3, "lộ trình dài trên cao tốc", "Hướng dẫn", "Thông tin",
    "Đi thẳng 12,5 km trên QL1A, sau đó vào cao tốc TP.HCM – Long Thành – Dầu Giây.",
    "Đi thẳng mười hai phẩy năm ki lô mét trên quốc lộ một A, sau đó vào cao tốc thành phố Hồ Chí Minh, Long Thành, Dầu Giây.",
    "Việt", "số thập phân; đơn vị đo; viết tắt; tên riêng/địa danh", "Trung tính", "Vừa", "Nữ – Nam", "E03", "Xe điện", "Loa xe (trước)", None,
    "Ổn định giọng với câu dài")

add("CS02", 1, "va chạm phía trước", "Cảnh báo", "Khẩn cấp",
    "Cảnh báo va chạm phía trước! Phanh ngay!", "Cảnh báo va chạm phía trước! Phanh ngay!",
    "Việt", "", "Khẩn trương", "Nhanh", "Nam – Bắc", "E03", "Sedan xăng", "Loa xe (trước)", None,
    "Nhận biết mức khẩn cấp", "Kèm âm báo trước câu; câu ngắn")
add("CS02", 2, "lệch làn", "Cảnh báo", "Cao",
    "Xe đang lệch làn trái. Hãy giữ chắc vô lăng.", "Xe đang lệch làn trái. Hãy giữ chắc vô lăng.",
    "Việt", "", "Nghiêm túc/cảnh báo", "Vừa", "Nữ – trung tính", "E05", "SUV xăng", "Loa xe (trước)", None,
    "Độ rõ trong nhiễu (WER/CER)")
add("CS02", 3, "người lái mệt", "Cảnh báo", "Trung bình",
    "Bạn có dấu hiệu mệt mỏi. Hãy dừng nghỉ ở trạm dừng chân gần nhất, cách 8 km.",
    "Bạn có dấu hiệu mệt mỏi. Hãy dừng nghỉ ở trạm dừng chân gần nhất, cách tám ki lô mét.",
    "Việt", "số; đơn vị đo", "Thân thiện", "Chậm", "Nữ – Nam", "E07", "MPV/7 chỗ", "Loa xe (trước)", 4,
    "Nhận biết mức khẩn cấp")

add("CS03", 1, "đặt nhiệt độ ghế lái", "Xác nhận", "Thông tin",
    "Đã đặt nhiệt độ 24°C cho ghế lái.", "Đã đặt nhiệt độ hai mươi tư độ C cho ghế lái.",
    "Việt", "số; ký hiệu; đơn vị đo", "Trung tính", "Vừa", "Nữ – trung tính", "E01", "Sedan xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị")
add("CS03", 2, "hạ kính hành khách", "Xác nhận", "Thông tin",
    "Đã hạ kính phía hành khách xuống một nửa.", "Đã hạ kính phía hành khách xuống một nửa.",
    "Việt", "", "Trung tính", "Vừa", "Nam – Nam", "E02", "SUV xăng", "Loa xe (trước)", 2,
    "Độ tự nhiên (MOS)")
add("CS03", 3, "bật sưởi ghế và quạt", "Câu hỏi", "Thấp",
    "Đã bật sưởi ghế mức 2 và quạt gió mức 3. Bạn có muốn bật sấy kính không?",
    "Đã bật sưởi ghế mức hai và quạt gió mức ba. Bạn có muốn bật sấy kính không?",
    "Việt", "số", "Thân thiện", "Vừa", "Nữ – Bắc", "E06", "Xe điện", "Loa xe (trước)", None,
    "Ngắt nghỉ và ngữ điệu", "Phân biệt ngữ điệu câu kể và câu hỏi")

add("CS04", 1, "phát danh sách nhạc", "Thông báo", "Thông tin",
    "Đang phát danh sách nhạc “Chill cuối tuần” trên Spotify.", "Đang phát danh sách nhạc Chill cuối tuần trên Spotify.",
    "Việt + Anh", "từ mượn tiếng Anh; tên riêng/địa danh", "Thân thiện", "Vừa", "Nam – Nam", "E07", "SUV xăng", "Loa xe (toàn khoang)", None,
    "Đọc đúng tên riêng", "Hạ nhạc (ducking) trước khi phát")
add("CS04", 2, "chuyển kênh radio", "Xác nhận", "Thông tin",
    "Đã chuyển sang VOV Giao thông, FM 91 MHz.", "Đã chuyển sang V O V Giao thông, F M chín mươi mốt mê ga héc.",
    "Việt + Anh", "viết tắt; tần số/công suất; số", "Trung tính", "Vừa", "Nữ – Bắc", "E02", "Sedan xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị")
add("CS04", 3, "chỉnh âm lượng", "Thông báo", "Thấp",
    "Âm lượng đã tăng lên 18. Tôi sẽ tự giảm khi có thông báo dẫn đường.",
    "Âm lượng đã tăng lên mười tám. Tôi sẽ tự giảm khi có thông báo dẫn đường.",
    "Việt", "số", "Trung tính", "Vừa", "Nữ – trung tính", "E08", "Xe điện", "Loa xe (trước)", None,
    "Độ tự nhiên (MOS)")

add("CS05", 1, "cuộc gọi đến", "Câu hỏi", "Trung bình",
    "Bạn có cuộc gọi đến từ anh Minh. Bạn muốn nghe máy không?", "Bạn có cuộc gọi đến từ anh Minh. Bạn muốn nghe máy không?",
    "Việt", "tên riêng/địa danh", "Thân thiện", "Vừa", "Nữ – Nam", "E11", "Sedan xăng", "Bluetooth HFP", None,
    "Độ dễ nghe qua Bluetooth")
add("CS05", 2, "đọc tin nhắn", "Thông báo", "Thấp",
    "Tin nhắn mới từ chị Lan lúc 14:30: “Mình đến muộn 10 phút nhé.”",
    "Tin nhắn mới từ chị Lan lúc mười bốn giờ ba mươi: Mình đến muộn mười phút nhé.",
    "Việt", "giờ/ngày/tháng/năm; số; tên riêng/địa danh", "Trung tính", "Vừa", "Nam – Trung", "E11", "MPV/7 chỗ", "Bluetooth HFP", 1,
    "Độ dễ nghe qua Bluetooth", "Chỉ đọc ra loa chung khi người lái cho phép")
add("CS05", 3, "gọi theo số", "Xác nhận", "Thông tin",
    "Đang gọi số 0912 345 678.", "Đang gọi số không chín một hai, ba bốn năm, sáu bảy tám.",
    "Việt", "số điện thoại; số", "Trung tính", "Chậm", "Nữ – Bắc", "E02", "SUV xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Đọc từng chữ số, nhóm 4–3–3")

add("CS06", 1, "áp suất lốp thấp", "Cảnh báo", "Cao",
    "Áp suất lốp trước bên phải thấp: 1,9 bar. Mức khuyến nghị là 2,3 bar.",
    "Áp suất lốp trước bên phải thấp: một phẩy chín bar. Mức khuyến nghị là hai phẩy ba bar.",
    "Việt + Anh", "số thập phân; đơn vị đo", "Nghiêm túc/cảnh báo", "Vừa", "Nam – Bắc", "E01", "SUV xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Thống nhất cách đọc “bar” (bar hay ba)")
add("CS06", 2, "lịch bảo dưỡng", "Thông báo", "Thấp",
    "Xe cần bảo dưỡng định kỳ sau 500 km nữa hoặc trước ngày 15/11/2026.",
    "Xe cần bảo dưỡng định kỳ sau năm trăm ki lô mét nữa hoặc trước ngày mười lăm tháng mười một năm hai nghìn không trăm hai mươi sáu.",
    "Việt", "số; đơn vị đo; giờ/ngày/tháng/năm", "Trung tính", "Vừa", "Nữ – trung tính", "E02", "Xe dịch vụ", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị")
add("CS06", 3, "nhiên liệu còn lại", "Cảnh báo", "Trung bình",
    "Nhiên liệu còn khoảng 12%, đủ đi thêm khoảng 60 km.", "Nhiên liệu còn khoảng mười hai phần trăm, đủ đi thêm khoảng sáu mươi ki lô mét.",
    "Việt", "phần trăm; số; đơn vị đo", "Nghiêm túc/cảnh báo", "Vừa", "Nam – Nam", "E03", "Sedan xăng", "Loa xe (trước)", None,
    "Độ rõ trong nhiễu (WER/CER)")

add("CS07", 1, "pin và trạm sạc gần nhất", "Thông báo", "Trung bình",
    "Pin hiện còn 18%. Trạm sạc gần nhất cách 7,2 km, còn 3 cổng trống.",
    "Pin hiện còn mười tám phần trăm. Trạm sạc gần nhất cách bảy phẩy hai ki lô mét, còn ba cổng trống.",
    "Việt", "phần trăm; số thập phân; đơn vị đo; số", "Trung tính", "Vừa", "Nữ – Nam", "E08", "Xe điện", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị")
add("CS07", 2, "thời gian và chi phí sạc", "Thông báo", "Thông tin",
    "Ước tính sạc từ 20% lên 80% mất 28 phút, chi phí khoảng 185.000đ.",
    "Ước tính sạc từ hai mươi phần trăm lên tám mươi phần trăm mất hai mươi tám phút, chi phí khoảng một trăm tám mươi lăm nghìn đồng.",
    "Việt", "phần trăm; số; tiền VND", "Trung tính", "Vừa", "Nữ – Bắc", "E01", "Xe điện", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Dấu chấm phân cách hàng nghìn, không phải số thập phân")
add("CS07", 3, "công suất sạc", "Cảnh báo", "Thấp",
    "Công suất sạc hiện tại là 150 kW. Vui lòng không rút cáp khi đang sạc.",
    "Công suất sạc hiện tại là một trăm năm mươi ki lô oát. Vui lòng không rút cáp khi đang sạc.",
    "Việt", "tần số/công suất; số", "Trung tính", "Vừa", "Nam – Nam", "E08", "Xe điện", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Phân biệt kW (công suất) và kWh (năng lượng)")

add("CS08", 1, "tắc đường phía trước", "Thông báo", "Trung bình",
    "Phía trước tắc đường 3 km do tai nạn. Thời gian đến nơi dự kiến chậm thêm 15 phút.",
    "Phía trước tắc đường ba ki lô mét do tai nạn. Thời gian đến nơi dự kiến chậm thêm mười lăm phút.",
    "Việt", "số; đơn vị đo", "Trung tính", "Vừa", "Nam – Bắc", "E12", "Sedan xăng", "Loa xe (trước)", None,
    "Độ rõ trong nhiễu (WER/CER)")
add("CS08", 2, "dự báo thời tiết", "Thông báo", "Thông tin",
    "Dự báo chiều nay Hà Nội có mưa to, nhiệt độ 27–31°C.",
    "Dự báo chiều nay Hà Nội có mưa to, nhiệt độ từ hai mươi bảy đến ba mươi mốt độ C.",
    "Việt", "số; ký hiệu; tên riêng/địa danh", "Trung tính", "Vừa", "Nữ – Bắc", "E04", "SUV xăng", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị", "Khoảng giá trị đọc thành “từ ... đến ...”")
add("CS08", 3, "giờ đến dự kiến", "Thông báo", "Thông tin",
    "Bạn sẽ đến văn phòng lúc 08:45, đúng giờ.", "Bạn sẽ đến văn phòng lúc tám giờ bốn mươi lăm, đúng giờ.",
    "Việt", "giờ/ngày/tháng/năm", "Thân thiện", "Vừa", "Nữ – Nam", "E02", "Xe dịch vụ", "Loa xe (trước)", None,
    "Đọc đúng số/đơn vị")

add("CS09", 1, "phát hiện va chạm mạnh", "Câu hỏi", "Khẩn cấp",
    "Phát hiện va chạm mạnh. Bạn có ổn không? Nếu không trả lời trong 10 giây, tôi sẽ gọi cấp cứu 115.",
    "Phát hiện va chạm mạnh. Bạn có ổn không? Nếu không trả lời trong mười giây, tôi sẽ gọi cấp cứu một một năm.",
    "Việt", "số; số điện thoại", "Trấn an", "Chậm", "Nữ – trung tính", "E03", "SUV xăng", "Loa xe (toàn khoang)", None,
    "Nhận biết mức khẩn cấp", "Số khẩn cấp đọc từng chữ số")
add("CS09", 2, "gửi vị trí cứu hộ", "Thông báo", "Cao",
    "Đang gửi vị trí của bạn đến trung tâm cứu hộ. Hãy giữ bình tĩnh, lực lượng cứu hộ đang trên đường đến.",
    "Đang gửi vị trí của bạn đến trung tâm cứu hộ. Hãy giữ bình tĩnh, lực lượng cứu hộ đang trên đường đến.",
    "Việt", "", "Trấn an", "Chậm", "Nam – Nam", "E01", "Sedan xăng", "Loa xe (toàn khoang)", None,
    "Độ tự nhiên (MOS)")
add("CS09", 3, "sự cố nhiệt độ pin", "Cảnh báo", "Khẩn cấp",
    "Cảnh báo: nhiệt độ pin cao bất thường. Hãy dừng xe ở nơi an toàn và rời khỏi xe ngay.",
    "Cảnh báo: nhiệt độ pin cao bất thường. Hãy dừng xe ở nơi an toàn và rời khỏi xe ngay.",
    "Việt", "", "Khẩn trương", "Vừa", "Nam – Bắc", "E04", "Xe điện", "Loa xe (toàn khoang)", None,
    "Nhận biết mức khẩn cấp")

add("CS10", 1, "nhắc lịch họp", "Hội thoại", "Thấp",
    "Hôm nay bạn có cuộc họp lúc 9 giờ. Với giao thông hiện tại, bạn nên xuất phát trước 7 giờ 30 để kịp giờ.",
    "Hôm nay bạn có cuộc họp lúc chín giờ. Với giao thông hiện tại, bạn nên xuất phát trước bảy giờ ba mươi để kịp giờ.",
    "Việt", "giờ/ngày/tháng/năm; số", "Thân thiện", "Vừa", "Nữ – Nam", "E01", "Sedan xăng", "Loa xe (trước)", None,
    "Ngắt nghỉ và ngữ điệu")
add("CS10", 2, "gợi ý quán cà phê", "Câu hỏi", "Thông tin",
    "Gần đây có một quán cà phê đánh giá 4,7 sao, cách 600 m, có chỗ đỗ xe. Bạn muốn tôi dẫn đường không?",
    "Gần đây có một quán cà phê đánh giá bốn phẩy bảy sao, cách sáu trăm mét, có chỗ đỗ xe. Bạn muốn tôi dẫn đường không?",
    "Việt", "số thập phân; số; đơn vị đo", "Thân thiện", "Vừa", "Nữ – Bắc", "E02", "SUV xăng", "Loa xe (trước)", 2,
    "Ổn định giọng với câu dài")
add("CS10", 3, "nhắc việc", "Xác nhận", "Thông tin",
    "Ok, tôi sẽ nhắc bạn mua sữa khi đi ngang siêu thị gần nhà.", "Ô kê, tôi sẽ nhắc bạn mua sữa khi đi ngang siêu thị gần nhà.",
    "Việt + Anh", "từ mượn tiếng Anh", "Thân thiện", "Vừa", "Nam – Trung", "E08", "Xe điện", "Loa xe (trước)", None,
    "Độ tự nhiên (MOS)", "Chuyển mã “Ok” trong câu Việt")

add("CS11", 1, "nói chuyện với trẻ", "Thông báo", "Thông tin",
    "Chào các bé! Còn 20 phút nữa là đến nhà bà ngoại rồi nhé.", "Chào các bé! Còn hai mươi phút nữa là đến nhà bà ngoại rồi nhé.",
    "Việt", "số", "Vui tươi (trẻ em)", "Vừa", "Nữ – Nam", "E07", "MPV/7 chỗ", "Loa ghế sau", 4,
    "Độ tự nhiên (MOS)", "Phát ở loa ghế sau, không vang ra loa trước")
add("CS11", 2, "nhắc dây an toàn ghế sau", "Cảnh báo", "Trung bình",
    "Ghế sau bên trái chưa cài dây an toàn. Nhờ hành khách cài dây giúp.", "Ghế sau bên trái chưa cài dây an toàn. Nhờ hành khách cài dây giúp.",
    "Việt", "", "Nghiêm túc/cảnh báo", "Vừa", "Nam – Nam", "E02", "MPV/7 chỗ", "Loa xe (toàn khoang)", 3,
    "Độ rõ trong nhiễu (WER/CER)")
add("CS11", 3, "chế độ yên tĩnh khoang sau", "Xác nhận", "Thông tin",
    "Đã bật chế độ yên tĩnh cho khoang sau. Thông báo dẫn đường chỉ phát ở loa phía trước.",
    "Đã bật chế độ yên tĩnh cho khoang sau. Thông báo dẫn đường chỉ phát ở loa phía trước.",
    "Việt", "", "Trung tính", "Vừa", "Nữ – trung tính", "E08", "Xe điện", "Loa headrest", 3,
    "Độ tự nhiên (MOS)")

add("CS12", 1, "không nghe rõ", "Xin lỗi/làm rõ", "Thấp",
    "Xin lỗi, tôi chưa nghe rõ. Bạn có thể nói lại được không?", "Xin lỗi, tôi chưa nghe rõ. Bạn có thể nói lại được không?",
    "Việt", "", "Thân thiện", "Vừa", "Nữ – Bắc", "E02", "Sedan xăng", "Loa xe (trước)", None,
    "Ổn định giọng với câu dài", "Kiểm tra độ ổn định khi lặp lại nhiều lần")
add("CS12", 2, "hỏi lại khi trùng tên", "Câu hỏi", "Thấp",
    "Bạn muốn gọi cho anh Hùng nào: Hùng Nguyễn hay Hùng Trần?", "Bạn muốn gọi cho anh Hùng nào: Hùng Nguyễn hay Hùng Trần?",
    "Việt", "tên riêng/địa danh", "Trung tính", "Chậm", "Nam – Bắc", "E07", "SUV xăng", "Loa xe (trước)", 4,
    "Đọc đúng tên riêng", "Phân biệt rõ hai lựa chọn trong nhiễu")
add("CS12", 3, "mất kết nối mạng", "Thông báo", "Thấp",
    "Hiện chưa có kết nối mạng nên một số tính năng bị giới hạn. Tôi vẫn điều khiển được các chức năng trên xe.",
    "Hiện chưa có kết nối mạng nên một số tính năng bị giới hạn. Tôi vẫn điều khiển được các chức năng trên xe.",
    "Việt", "", "Trấn an", "Vừa", "Nữ – Nam", "E10", "SUV xăng", "Loa xe (trước)", None,
    "Ổn định giọng với câu dài", "Kịch bản mất mạng trong hầm; cần TTS chạy ngoại tuyến")


# ---- biến thể từ vựng theo vùng (cần người bản ngữ vùng đó duyệt trước khi dùng thật)
add("CS01", 4, "báo rẽ vào hẻm (cách nói miền Nam)", "Hướng dẫn", "Thấp",
    "Sau 200 m, quẹo trái vào hẻm 28 đường Nguyễn Văn Cừ.",
    "Sau hai trăm mét, quẹo trái vào hẻm hai mươi tám đường Nguyễn Văn Cừ.",
    "Việt", "số; đơn vị đo; địa chỉ; tên riêng/địa danh", "Trung tính", "Vừa", "Nam – Nam", "E02", "Sedan xăng", "Loa xe (trước)", None,
    "Đọc đúng tên riêng", "Từ vùng miền: quẹo (rẽ), hẻm (ngõ); đối chiếu CS01-001", lex="Nam")
add("CS02", 4, "phanh gấp (cách nói miền Nam)", "Cảnh báo", "Khẩn cấp",
    "Coi chừng! Thắng gấp, phía trước có xe!", "Coi chừng! Thắng gấp, phía trước có xe!",
    "Việt", "", "Khẩn trương", "Nhanh", "Nam – Nam", "E03", "SUV xăng", "Loa xe (trước)", None,
    "Nhận biết mức khẩn cấp", "Từ vùng miền: coi chừng (cẩn thận), thắng (phanh); đối chiếu CS02-001", lex="Nam")
add("CS03", 4, "hạ kính (cách nói miền Nam)", "Xác nhận", "Thông tin",
    "Dạ, đã hạ kiếng bên ghế phụ xuống một nửa rồi nha.", "Dạ, đã hạ kiếng bên ghế phụ xuống một nửa rồi nha.",
    "Việt", "", "Thân thiện", "Vừa", "Nữ – Nam", "E02", "Sedan xăng", "Loa xe (trước)", 2,
    "Độ tự nhiên (MOS)", "Từ vùng miền: dạ (vâng), kiếng (kính), nha (nhé); đối chiếu CS03-002 và CS03-005", lex="Nam")
add("CS03", 5, "hạ kính (cách nói miền Bắc)", "Xác nhận", "Thông tin",
    "Vâng, đã hạ kính bên ghế phụ xuống một nửa rồi nhé.", "Vâng, đã hạ kính bên ghế phụ xuống một nửa rồi nhé.",
    "Việt", "", "Thân thiện", "Vừa", "Nữ – Bắc", "E02", "Sedan xăng", "Loa xe (trước)", 2,
    "Độ tự nhiên (MOS)", "Từ vùng miền: vâng, nhé; đối chiếu CS03-004", lex="Bắc")
add("CS05", 4, "cuộc gọi đến (cách nói miền Trung)", "Câu hỏi", "Trung bình",
    "Có cuộc gọi đến từ mạ. Bạn nghe máy không?", "Có cuộc gọi đến từ mạ. Bạn nghe máy không?",
    "Việt", "tên riêng/địa danh", "Thân thiện", "Vừa", "Nữ – Trung", "E11", "MPV/7 chỗ", "Bluetooth HFP", 1,
    "Độ dễ nghe qua Bluetooth", "Từ vùng miền: mạ (mẹ); cần người bản ngữ Trung Bộ duyệt", lex="Trung")
add("CS08", 4, "tắc đường (cách nói miền Trung)", "Câu hỏi", "Trung bình",
    "Phía trước tắc đường, chừng 15 phút nữa mới đi được. Rứa bạn có muốn đi đường khác không?",
    "Phía trước tắc đường, chừng mười lăm phút nữa mới đi được. Rứa bạn có muốn đi đường khác không?",
    "Việt", "số", "Trung tính", "Vừa", "Nam – Trung", "E12", "Sedan xăng", "Loa xe (trước)", None,
    "Ngắt nghỉ và ngữ điệu", "Từ vùng miền: rứa (vậy); cần người bản ngữ Trung Bộ duyệt", lex="Trung")

add("CS01", 5, "báo vào hầm, nền đổi giữa câu", "Hướng dẫn", "Thấp",
    "Sau 300 m, vào hầm Thủ Thiêm. Hãy giữ khoảng cách an toàn.",
    "Sau ba trăm mét, vào hầm Thủ Thiêm. Hãy giữ khoảng cách an toàn.",
    "Việt", "số; đơn vị đo; tên riêng/địa danh", "Trung tính", "Vừa", "Nữ – Nam", "E13", "Sedan xăng", "Loa xe (trước)", None,
    "Độ rõ trong nhiễu (WER/CER)", "Nền đổi từ nội đô sang hầm ở giữa câu; đo WER riêng đoạn cuối")
add("CS02", 5, "cảnh báo khi có âm báo xe chồng lên", "Cảnh báo", "Cao",
    "Chú ý! Xe phía trước phanh gấp, giữ khoảng cách 30 m.",
    "Chú ý! Xe phía trước phanh gấp, giữ khoảng cách ba mươi mét.",
    "Việt", "số; đơn vị đo", "Khẩn trương", "Nhanh", "Nam – Bắc", "E14", "SUV xăng", "Loa xe (trước)", None,
    "Nhận biết mức khẩn cấp", "Âm báo của xe chồng lên phần đầu câu")
add("CS05", 5, "báo cuộc gọi nhỡ qua điện thoại", "Câu hỏi", "Trung bình",
    "Cuộc gọi nhỡ từ số 0903 456 789 lúc 14:05. Bạn có muốn gọi lại không?",
    "Cuộc gọi nhỡ từ số không chín không ba, bốn năm sáu, bảy tám chín lúc mười bốn giờ không năm phút. Bạn có muốn gọi lại không?",
    "Việt", "số điện thoại; giờ/ngày/tháng/năm", "Trung tính", "Vừa", "Nữ – Bắc", "E15", "Sedan xăng", "Bluetooth HFP", 1,
    "Độ dễ nghe qua Bluetooth", "Qua codec cuộc gọi của điện thoại")
add("CS09", 4, "cảnh báo cháy, loa quá tải", "Cảnh báo", "Khẩn cấp",
    "Phát hiện cháy khoang động cơ. Dừng xe và rời xe ngay!",
    "Phát hiện cháy khoang động cơ. Dừng xe và rời xe ngay!",
    "Việt", "", "Khẩn trương", "Nhanh", "Nam – Nam", "E17", "SUV xăng", "Loa xe (toàn khoang)", None,
    "Nhận biết mức khẩn cấp", "Loa đang ở mức cao, kiểm tra méo")
add("CS12", 4, "báo mạng yếu, chuyển giọng trên xe", "Thông báo", "Trung bình",
    "Mạng đang yếu nên tôi sẽ dùng giọng đọc trên xe. Một số tin tức có thể chưa cập nhật.",
    "Mạng đang yếu nên tôi sẽ dùng giọng đọc trên xe. Một số tin tức có thể chưa cập nhật.",
    "Việt", "", "Trấn an", "Vừa", "Nữ – trung tính", "E16", "Xe dịch vụ", "Loa xe (trước)", None,
    "Độ trễ phát (TTFA)", "Kiểm tra lúc chuyển từ giọng đám mây sang giọng trên xe")

SPK_BY_VOICE = {"Nữ – Bắc": "SPK001", "Nam – Bắc": "SPK002", "Nữ – Nam": "SPK003", "Nam – Nam": "SPK004",
                "Nữ – Trung": "SPK005", "Nam – Trung": "SPK006", "Nữ – trung tính": "SPK007"}


# hồ sơ người nói: (id, vai trò, giới tính, nhóm tuổi, vùng giọng, mức giọng địa phương, dải F0, khoảng F0 chỉ dẫn (Hz),
#                   chất giọng, tốc độ mặc định, ghi chú)
# Khoảng F0 là giá trị chỉ dẫn theo hiểu biết ngữ âm học chung, chưa đo; cột F0 đo thực để trống cho người thu điền.
SPEAKERS = [
    ("SPK001", "Giọng thu TTS", "Nữ", "Thanh niên (18–34)", "Bắc Bộ", "Nhẹ", "Cao", "170–260", "Bình thường", "Vừa", "Giọng dẫn đường chuẩn miền Bắc"),
    ("SPK002", "Giọng thu TTS", "Nam", "Trung niên (35–54)", "Bắc Bộ", "Nhẹ", "Trung bình", "90–170", "Bình thường", "Vừa", "Giọng nam chuẩn miền Bắc"),
    ("SPK003", "Giọng thu TTS", "Nữ", "Thanh niên (18–34)", "Nam Bộ", "Nhẹ", "Cao", "170–260", "Bình thường", "Vừa", "Giọng nữ miền Nam"),
    ("SPK004", "Giọng thu TTS", "Nam", "Trung niên (35–54)", "Nam Bộ", "Nhẹ", "Trung bình", "90–170", "Bình thường", "Vừa", "Giọng nam miền Nam"),
    ("SPK005", "Giọng thu TTS", "Nữ", "Thanh niên (18–34)", "Trung Bộ (chưa chia tiểu vùng)", "Nhẹ", "Cao", "170–260", "Bình thường", "Vừa", "Cần chọn tiểu vùng cụ thể (Huế, Nghệ An, Đà Nẵng…) và người bản ngữ duyệt"),
    ("SPK006", "Giọng thu TTS", "Nam", "Trung niên (35–54)", "Trung Bộ (chưa chia tiểu vùng)", "Nhẹ", "Trung bình", "90–170", "Bình thường", "Vừa", "Cần chọn tiểu vùng cụ thể và người bản ngữ duyệt"),
    ("SPK007", "Giọng thu TTS", "Nữ", "Thanh niên (18–34)", "Giọng pha / không xác định", "Nhẹ", "Cao", "170–260", "Bình thường", "Vừa", "Giọng trung tính dùng khi chưa biết vùng của người dùng"),
    ("SPK101", "Người dùng (ASR)", "Nam", "Trung niên (35–54)", "Nam Bộ", "Đậm", "Trung bình", "90–170", "Bình thường", "Nhanh", "Ví dụ người dùng: nói nhanh, dùng nhiều từ miền Nam"),
    ("SPK102", "Người dùng (ASR)", "Nữ", "Cao tuổi (55 trở lên)", "Bắc Trung Bộ", "Đậm", "Cao", "170–260", "Bình thường", "Chậm", "Ví dụ người dùng: giọng địa phương đậm, nói chậm"),
    ("SPK103", "Người dùng (ASR)", "Nam", "Thanh niên (18–34)", "Bắc Bộ", "Vừa", "Trung bình", "90–170", "Nghẹt mũi", "Vừa", "Ví dụ người dùng đang bị cảm"),
    ("SPK104", "Người dùng (ASR)", "Nữ", "Trẻ em (dưới 13)", "Giọng pha / không xác định", "Nhẹ", "Rất cao", "250–400", "Bình thường", "Vừa", "Ví dụ hành khách nhỏ tuổi"),
    ("SPK105", "Người dùng (ASR)", "Nữ", "Thanh niên (18–34)", "Nam Trung Bộ", "Vừa", "Cao", "170–260", "Bình thường", "Vừa", "Ví dụ người dùng giọng Trung pha Nam"),
]
SPK = {s[0]: s for s in SPEAKERS}
F0_BAND_GUIDE = [
    ("Thấp", "dưới khoảng 110 Hz", "Nam giọng trầm"),
    ("Trung bình", "khoảng 110–165 Hz", "Nam giọng thường"),
    ("Cao", "khoảng 165–255 Hz", "Nữ trưởng thành"),
    ("Rất cao", "trên khoảng 255 Hz", "Trẻ em"),
]


# kiểu khởi phát từng mẫu (nhãn do tôi gán theo nội dung câu; cần nhóm dữ liệu rà lại)
_CH, _DL, _TL = "Hệ thống chủ động", "Đáp lệnh người dùng", "Chờ người dùng trả lời"
TRIGGER = {
    "CS01-001": _CH, "CS01-002": _CH, "CS01-003": _CH, "CS01-004": _CH,
    "CS02-001": _CH, "CS02-002": _CH, "CS02-003": _CH, "CS02-004": _CH,
    "CS03-001": _DL, "CS03-002": _DL, "CS03-003": _TL, "CS03-004": _DL, "CS03-005": _DL,
    "CS04-001": _DL, "CS04-002": _DL, "CS04-003": _DL,
    "CS05-001": _TL, "CS05-002": _CH, "CS05-003": _DL, "CS05-004": _TL,
    "CS06-001": _CH, "CS06-002": _CH, "CS06-003": _CH,
    "CS07-001": _DL, "CS07-002": _DL, "CS07-003": _CH,
    "CS08-001": _CH, "CS08-002": _DL, "CS08-003": _DL, "CS08-004": _TL,
    "CS09-001": _TL, "CS09-002": _CH, "CS09-003": _CH,
    "CS10-001": _CH, "CS10-002": _TL, "CS10-003": _DL,
    "CS11-001": _CH, "CS11-002": _CH, "CS11-003": _DL,
    "CS12-001": _TL, "CS12-002": _TL, "CS12-003": _CH,
    "CS01-005": _CH, "CS02-005": _CH, "CS05-005": _TL, "CS09-004": _CH, "CS12-004": _CH,
}


def est_duration(spoken, rate):
    n = len(spoken.split())
    return round(n / RATES[rate], 1)


def build_rows():
    rows = []
    for s in S:
        p = PRESET[s["env"]]
        pax = s["pax"] if s["pax"] is not None else p[12]
        rows.append({
            "sample_id": f'{s["case"]}-{s["n"]:03d}',
            "case_id": s["case"],
            "case_name": CASE_NAME[s["case"]],
            "intent": s["intent"],
            "trigger_type": TRIGGER[f'{s["case"]}-{s["n"]:03d}'],
            "asr_input": "Không" if TRIGGER[f'{s["case"]}-{s["n"]:03d}'] == _CH else "Có",
            "speech_act": s["act"],
            "urgency": s["urg"],
            "text_raw": s["raw"],
            "text_spoken": s["spoken"],
            "language_mix": s["lang"],
            "norm_features": s["feats"],
            "style": s["style"],
            "speaking_rate": s["rate"],
            "voice_persona": s["voice"],
            "speaker_id": SPK_BY_VOICE[s["voice"]],
            "lexicon_variant": s["lex"],
            "speaker_gender": SPK[SPK_BY_VOICE[s["voice"]]][2],
            "speaker_dialect": SPK[SPK_BY_VOICE[s["voice"]]][4],
            "speaker_f0_band": SPK[SPK_BY_VOICE[s["voice"]]][6],
            "est_duration_s": est_duration(s["spoken"], s["rate"]),
            "env_id": s["env"],
            "driving_state": p[3],
            "speed_kmh": p[4],
            "cabin_noise_dBA": p[5],
            "snr_target_dB": p[7],
            "cabin_type": s["cabin"],
            "hvac_level": p[8],
            "windows": p[9],
            "music": p[10],
            "passengers": pax,
            "rain": p[11],
            "playback_channel": s["channel"],
            "eval_focus": s["focus"],
            "data_origin": "Tổng hợp hoàn toàn",
            "voice_source": "Chưa xác định",
            "generator_model": None,
            "noise_source": "Chưa xác định",
            "rir_source": "Chưa xác định",
            "lombard_applied": "Không",
            "snr_actual_dB": None,
            "qc_asr_wer_pct": None,
            "qc_dialect_match": "Chưa kiểm",
            "qc_f0_in_band": "Chưa kiểm",
            "qc_native_review": "Chưa kiểm",
            "qc_status": "Chưa kiểm",
            "status": "Mẫu",
            "notes": s["notes"],
        })
    rows.sort(key=lambda r: r["sample_id"])
    return rows
