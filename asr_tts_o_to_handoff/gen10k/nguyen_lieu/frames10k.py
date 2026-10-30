# -*- coding: utf-8 -*-
"""Khung câu (mẫu câu × khe).

Nguồn khung:
  1. sources/src_commands.json: 1008 mẫu (127 'seen' có nguồn N*, 881 'constructed'), dùng nguyên văn, đổi tên khe.
  2. generator/tpl_a.py, tpl_b.py (phiên trước, tự soạn K1): chép lại, sửa cú pháp.
  3. Bổ sung trong phiên này (tự soạn K1), chủ yếu cho CS02, CS08–CS12 và các khung nhiều khe.
Cú pháp: {khe}, {khe#2} (giá trị thứ hai cùng loại), (a|b|) lựa chọn, '~' đầu khung = không thêm tiền tố,
'!' đầu khung = giữ nguyên, không trang trí.
"""
import re
from nguyen_lieu import pools10k as P

INTENT_LABELS = {
    # CS01
    "dan_duong_den_dia_diem": "dẫn đường đến địa điểm", "dan_duong_den_dia_chi": "dẫn đường đến địa chỉ",
    "dan_duong_den_khu_vuc": "dẫn đường đến quận, thành phố", "ve_nha_co_quan": "dẫn đường về nhà hoặc nơi đã lưu",
    "hoi_con_bao_xa": "hỏi còn bao xa", "hoi_thoi_gian_den": "hỏi giờ đến", "tranh_ket_xe_cong_trinh": "tìm đường tránh tắc",
    "chon_lo_trinh": "chọn lộ trình", "them_diem_dung": "thêm điểm dừng", "huy_dan_duong": "hủy dẫn đường",
    "tim_dia_diem_gan_day": "tìm địa điểm gần đây", "nhac_lai_chi_dan": "hỏi lại chỉ dẫn", "hoi_chi_dan_tiep_theo": "hỏi chỉ dẫn tiếp theo",
    "tat_bat_tieng_dan_duong": "chỉnh giọng dẫn đường", "dieu_khien_ban_do": "điều khiển bản đồ",
    # CS02
    "canh_bao_lech_lan": "cảnh báo lệch làn", "canh_bao_va_cham": "cảnh báo va chạm", "canh_bao_diem_mu": "cảnh báo điểm mù",
    "canh_bao_met_moi": "phản hồi cảnh báo mệt mỏi", "do_nhay_canh_bao_chung": "chỉnh cảnh báo chung", "bat_tat_he_thong_ho_tro": "bật tắt hệ thống hỗ trợ lái",
    "ga_tu_dong": "ga tự động và giới hạn tốc độ",
    # CS03
    "dieu_hoa_bat_tat_nhiet_do": "đặt nhiệt độ điều hòa", "dieu_hoa_noi_nong_lanh": "nói nóng lạnh (lệnh gián tiếp)",
    "dieu_hoa_quat_gio": "chỉnh quạt gió", "dieu_hoa_huong_gio": "chỉnh hướng gió", "dieu_hoa_lay_gio": "lấy gió trong, gió ngoài",
    "say_kinh": "sấy kính", "dieu_hoa_che_do": "chế độ điều hòa", "ghe_suoi_lam_mat_massage": "sưởi, làm mát, massage ghế",
    "ghe_nho_vi_tri": "chỉnh và nhớ vị trí ghế", "cua_kinh": "điều khiển cửa kính", "cua_so_troi": "cửa sổ trời",
    "den_noi_that": "đèn trong xe", "khoa_mo_cua": "khóa, mở cửa", "guong": "gương chiếu hậu", "cop_xe": "cốp xe", "gat_mua": "gạt mưa",
    "che_do_lai": "chế độ lái", "wifi_camera": "wifi và camera", "vo_lang_den_ngoai": "vô lăng và đèn ngoài",
    # CS04
    "phat_bai_ca_si": "phát bài hát, ca sĩ", "phat_the_loai_playlist": "phát thể loại, danh sách", "phat_theo_tam_trang": "phát nhạc theo tâm trạng",
    "nguon_nhac_bluetooth_usb": "chọn nguồn phát", "radio": "nghe radio", "podcast": "podcast, sách nói", "am_luong": "chỉnh âm lượng",
    "chuyen_bai_tam_dung": "điều khiển phát", "yeu_thich": "thích, lưu bài", "hoi_bai_dang_phat": "hỏi bài đang phát",
    # CS05
    "goi_theo_ten": "gọi theo tên", "goi_theo_so": "gọi theo số", "nhan_tu_choi_cuoc_goi": "nghe, từ chối cuộc gọi", "goi_lai": "gọi lại",
    "soan_gui_tin_nhan": "gửi tin nhắn", "doc_tin_nhan": "đọc tin nhắn", "doc_thong_bao": "đọc thông báo", "nhan_zalo": "nhắn, gọi Zalo",
    "chia_se_vi_tri": "chia sẻ vị trí",
    # CS06
    "ap_suat_lop": "hỏi áp suất lốp", "nhien_lieu_quang_duong": "hỏi nhiên liệu", "bao_duong": "hỏi bảo dưỡng",
    "den_canh_bao": "hỏi đèn cảnh báo", "nhiet_do_dong_co": "hỏi nhiệt độ động cơ", "so_km_da_di": "hỏi quãng đường đã đi",
    # CS07
    "phan_tram_pin": "hỏi phần trăm pin", "quang_duong_con_lai_ev": "hỏi quãng đường còn lại (xe điện)", "tim_tram_sac": "tìm trạm sạc",
    "thoi_gian_chi_phi_sac": "hỏi thời gian, chi phí sạc", "cong_sac": "cổng sạc", "gioi_han_sac": "giới hạn sạc", "hen_gio_sac": "hẹn giờ sạc",
    "tim_tram_xang": "tìm trạm xăng, giá xăng",
    # CS08
    "tac_duong_phia_truoc": "hỏi tắc đường", "tai_nan_su_co": "hỏi tai nạn, sự cố", "toc_do_toi_da": "hỏi giới hạn tốc độ",
    "camera_phat_nguoi": "camera phạt nguội", "thoi_tiet_hom_nay_mai": "hỏi thời tiết", "nhiet_do_mua": "hỏi nhiệt độ, mưa",
    "chat_luong_khong_khi": "hỏi chất lượng không khí", "gio_den_theo_giao_thong": "hỏi giờ đến theo giao thông", "ngap_nuoc": "hỏi ngập nước",
    # CS09
    "goi_cap_cuu_115": "gọi cấp cứu", "goi_cong_an_113": "gọi công an", "goi_cuu_hoa_114": "gọi cứu hỏa", "cuu_ho_giao_thong": "gọi cứu hộ",
    "bao_tai_nan": "báo tai nạn", "toi_on": "nói tôi ổn", "keu_cuu": "kêu cứu", "bao_vi_tri_khan_cap": "báo vị trí khẩn cấp",
    # CS10
    "nhac_viec": "nhắc việc", "dat_lich": "đặt lịch", "bao_thuc_hen_gio": "báo thức, hẹn giờ", "hoi_gio_ngay": "hỏi giờ, ngày",
    "hoi_quan_an": "hỏi quán ăn", "hoi_quan_co_cho_do": "hỏi quán có chỗ đỗ xe", "hoi_dap_chung": "hỏi đáp chung",
    "tinh_toan_doi_tien": "tính toán, đổi tiền", "chao_cam_on": "chào, cảm ơn", "tro_chuyen_tam_su": "trò chuyện",
    "ke_chuyen_cuoi": "kể chuyện cười", "tin_tuc": "tin tức",
    # CS11
    "tre_xem_nhac_phim_truyen": "trẻ nhờ mở nhạc, phim, truyện", "tre_noi": "trẻ nói, hỏi", "dieu_hoa_khoang_sau": "điều hòa khoang sau",
    "tat_loa_sau": "loa khoang sau", "che_do_yen_tinh": "chế độ yên tĩnh", "nhac_day_an_toan_ghe_sau": "nhắc dây an toàn ghế sau",
    "khoa_tre_em": "khóa trẻ em, cửa và kính sau",
    # CS12
    "noi_lai": "yêu cầu nói lại", "sua_lenh": "sửa lệnh", "chon_ket_qua": "chọn kết quả", "xac_nhan_dong_y": "xác nhận, đồng ý",
    "tu_choi_huy_dung": "từ chối, hủy", "xem_them_lua_chon": "xem thêm lựa chọn", "tra_loi_gia_tri": "trả lời giá trị (số, giờ, tên)",
    "ngoai_tuyen": "mất mạng, tính năng chưa hỗ trợ",
}

# ý định có câu trả lời ngắn -> M2
M2_INTENTS = {"xac_nhan_dong_y", "tu_choi_huy_dung", "chon_ket_qua", "tra_loi_gia_tri"}

# Trạng thái người nói mặc định theo ý định (Tu_vung.speaker_state)
STATE = {
    "goi_cap_cuu_115": [("Căng thẳng / khẩn", .85), ("Bình thường", .15)], "goi_cong_an_113": [("Căng thẳng / khẩn", .8), ("Bình thường", .2)],
    "goi_cuu_hoa_114": [("Căng thẳng / khẩn", .9), ("Bình thường", .1)], "keu_cuu": [("Căng thẳng / khẩn", 1)],
    "bao_tai_nan": [("Căng thẳng / khẩn", .8), ("Bình thường", .2)], "bao_vi_tri_khan_cap": [("Căng thẳng / khẩn", .8), ("Vội / nói nhanh", .2)],
    "cuu_ho_giao_thong": [("Bình thường", .5), ("Căng thẳng / khẩn", .5)], "toi_on": [("Bình thường", .5), ("Căng thẳng / khẩn", .3), ("Mệt mỏi", .2)],
    "canh_bao_met_moi": [("Mệt mỏi", .6), ("Bình thường", .4)],
    "am_luong": [("Bình thường", .6), ("Nói trong ồn (Lombard)", .3), ("Vội / nói nhanh", .1)],
    "goi_theo_so": [("Bình thường", .8), ("Vội / nói nhanh", .2)], "sua_lenh": [("Bình thường", .6), ("Vội / nói nhanh", .4)],
    "tre_xem_nhac_phim_truyen": [("Trẻ em", .7), ("Bình thường", .3)], "tre_noi": [("Trẻ em", 1)],
    "nhac_lai_chi_dan": [("Bình thường", .7), ("Nói trong ồn (Lombard)", .3)], "noi_lai": [("Bình thường", .6), ("Nói trong ồn (Lombard)", .4)],
    "hoi_chi_dan_tiep_theo": [("Bình thường", .7), ("Vội / nói nhanh", .3)],
}
# ý định gắn D01 (tải nhận thức cao: đang dẫn đường, giao thông, cảnh báo) và D03 (khẩn cấp)
D01_INTENTS = {"hoi_chi_dan_tiep_theo", "nhac_lai_chi_dan", "tranh_ket_xe_cong_trinh", "hoi_con_bao_xa", "tac_duong_phia_truoc",
               "tai_nan_su_co", "toc_do_toi_da", "camera_phat_nguoi", "canh_bao_lech_lan", "canh_bao_va_cham", "canh_bao_diem_mu",
               "canh_bao_met_moi", "ga_tu_dong", "chon_lo_trinh", "gio_den_theo_giao_thong", "ngap_nuoc"}
D03_INTENTS = {"goi_cap_cuu_115", "goi_cong_an_113", "goi_cuu_hoa_114", "cuu_ho_giao_thong", "bao_tai_nan", "keu_cuu",
               "bao_vi_tri_khan_cap", "toi_on", "canh_bao_va_cham"}

# Trọng số ý định trong case (mặc định 1.0)
INTENT_W = {
    "dan_duong_den_dia_chi": 2.6, "dan_duong_den_dia_diem": 2.6, "dan_duong_den_khu_vuc": 1.4, "hoi_con_bao_xa": 1.0,
    "hoi_thoi_gian_den": 1.0, "tim_dia_diem_gan_day": 1.3, "hoi_chi_dan_tiep_theo": 1.0,
    "dieu_hoa_bat_tat_nhiet_do": 2.2, "cua_kinh": 1.6, "ghe_suoi_lam_mat_massage": 1.3, "dieu_hoa_quat_gio": 1.2,
    "phat_bai_ca_si": 2.2, "phat_the_loai_playlist": 1.6, "radio": 1.4, "am_luong": 1.3,
    "goi_theo_ten": 2.4, "goi_theo_so": 2.0, "soan_gui_tin_nhan": 2.2, "nhan_zalo": 1.2, "chia_se_vi_tri": 1.0,
    "nhac_viec": 2.4, "dat_lich": 1.8, "hoi_quan_an": 1.2, "hoi_dap_chung": 1.2, "tinh_toan_doi_tien": 1.0, "bao_thuc_hen_gio": 1.2,
    "sua_lenh": 1.6, "tra_loi_gia_tri": 4.5, "chon_ket_qua": 2.6, "xac_nhan_dong_y": 1.8, "tu_choi_huy_dung": 1.6,
    "noi_lai": 0.7, "xem_them_lua_chon": 0.6, "ngoai_tuyen": 0.6, "keu_cuu": 1.8,
    "thoi_tiet_hom_nay_mai": 1.6, "tac_duong_phia_truoc": 1.6, "nhiet_do_mua": 1.2,
    "bao_vi_tri_khan_cap": 1.4, "tim_tram_sac": 1.5, "hen_gio_sac": 1.0,
}

# Ánh xạ khe của src_commands.json -> khe của bộ sinh (theo ý định nếu cần)
SRC_SLOT_MAP = {
    "_default": {"dia_diem_2": "dia_diem", "nhiet_do_2": "nhiet_do", "muc": "lvl3", "so": "lvl3", "noi_dung": "msg"},
    "ghe_nho_vi_tri": {"so": "mem", "ten_lien_he": "ct2"},
    "dieu_hoa_quat_gio": {"so": "lvl3"}, "ghe_suoi_lam_mat_massage": {"muc": "lvl3"},
    "podcast": {"so": "n60"}, "chuyen_bai_tam_dung": {"so": "n60"}, "am_luong": {"muc": "vol"},
    "bao_thuc_hen_gio": {"so": "n60"}, "hoi_quan_an": {"so": "ppl"}, "ke_chuyen_cuoi": {"so": "lvl5"},
    "chon_ket_qua": {"so": "lvl5"}, "nhac_viec": {"noi_dung": "todo"}, "soan_gui_tin_nhan": {"noi_dung": "msg"},
    "nhan_zalo": {"noi_dung": "msg"}, "quang_duong_con_lai_ev": {"dia_diem": "poi"}, "nhien_lieu_quang_duong": {"dia_diem": "poi"},
    "tac_duong_phia_truoc": {"dia_diem": "poi"}, "thoi_tiet_hom_nay_mai": {"dia_diem": "city"}, "gio_den_theo_giao_thong": {"dia_diem": "poi"},
    "dat_lich": {"dia_diem": "poi"}, "tim_dia_diem_gan_day": {"dia_diem": "poi"}, "tim_tram_sac": {"dia_diem": "poi"},
    "sua_lenh": {"dia_diem": "poi", "nhiet_do": "temp"},
    "radio": {"tan_so": "freq_bare"}, "podcast": {"so": "n60", "ten_podcast": "chu_de"},
}
SRC_SLOT_MAP["tac_duong_phia_truoc"]["ten_duong"] = "st_bare"
# Sửa chữ trong khung nguồn để khe phần trăm tự mang đơn vị
SRC_TEXT_FIX = [("{phan_tram} phần trăm", "{phan_tram}"), ("80 phần trăm", "80%"), ("100 phần trăm", "100%"),
                ("{delta} độ C", "{delta} độ"), ("Kể chuyện cười đi {wake}", "Kể chuyện cười đi {wake}"),
                ("ki-lô-mét", "ki lô mét"), ("ki-lô-oát", "ki lô oát"), ("công-tơ-mét", "công tơ mét"),
                ("sang VND", "sang (tiền Việt|đồng Việt Nam)")]   # góp ý v1 mục 3: tránh đọc 'vê en đê'
SRC_CASE_EVIDENCE_NOTE = "src_commands.json"

# ------------------------------------------------------------------ khung tự soạn
MY = []


def F(case, intent, act, texts, src="phiên này (K1)", w=None, purpose=None):
    for t in texts:
        MY.append(dict(case=case, intent=intent, act=act, text=t, src=src, evidence="constructed", source_ids=[],
                       purpose=purpose, w=w))


TPL = "generator/tpl_a.py, tpl_b.py (phiên trước, K1)"
GO = "(đến|tới)"

# ================================================================= CS01 Dẫn đường
F("CS01", "dan_duong_den_dia_chi", "Lệnh", [
    f"dẫn đường {GO} {{addr}}", f"chỉ đường {GO} {{addr}}", f"chỉ đường cho tôi {GO} {{addr}}", f"(bắt đầu|mở) dẫn đường {GO} {{addr}}",
    f"đưa tôi {GO} {{addr}}", f"tìm đường {GO} {{addr}}", f"~tôi muốn đi {GO} {{addr}}", "~tôi cần đến {addr}",
    f"dẫn đường {GO} {{addr}} (bằng|theo) đường nhanh nhất", "đặt điểm đến là {addr}", f"đi {GO} {{addr}}", "điều hướng tới {addr}",
    "~{addr}, dẫn đường", "~ờ, đi {addr}", "chỉ đường đi {addr}", "~cho tôi về {addr}",
], TPL)
F("CS01", "dan_duong_den_dia_diem", "Lệnh", [
    f"dẫn đường {GO} {{poi}}", f"đưa tôi {GO} {{poi}}", f"tìm đường {GO} {{poi}}", "đi {poi}", "~tôi muốn đến {poi}",
    "~tôi cần đến {poi} gấp", f"điều hướng {GO} {{poi}}", f"(mở|bắt đầu) dẫn đường {GO} {{poi}}", "đặt điểm đến là {poi}",
    "~{poi}, dẫn đường", "chỉ đường ra {poi_air}", "~đi {poi_hosp} nhanh lên", "đưa tôi ra {poi_air} kịp giờ bay",
    f"dẫn đường {GO} {{poi}} rồi (ghé|qua) {{poi#2}}", "~mình đi {poi} nhé", "tìm đường ngắn nhất tới {poi}",
], TPL)
F("CS01", "dan_duong_den_khu_vuc", "Lệnh", [
    f"dẫn đường {GO} {{dist}}", f"đưa tôi {GO} {{dist}}", "~tôi cần đến {dist}", "dẫn đường đi {city}", "~tôi muốn đi {city}",
    "đưa tôi đi {city}", "dẫn đường đi {city} (theo|bằng) (cao tốc|quốc lộ|đường nhanh nhất)", "chỉ đường đi {city}",
    "đi {city} theo {hw}", "tìm đường từ đây đi {city}", "đi {city} không qua trạm thu phí", "~tối nay đi {city}, chỉ đường giúp tôi",
], TPL)
F("CS01", "ve_nha_co_quan", "Lệnh", [
    "dẫn đường về {home}", "đưa tôi về {home}", "~về {home}", "~tôi muốn về {home}", "chỉ đường về {home}", "đặt {home} làm điểm đến",
    "dẫn đường đến {place_saved}", "đưa tôi đến {place_saved}", "~đi {place_saved}", "về {home} theo đường quen", "lưu {addr} là {place_saved}",
], TPL)
F("CS01", "hoi_con_bao_xa", "Câu hỏi", [
    "còn bao xa nữa (thì|là) (đến|tới) (nơi|đích)", "còn bao nhiêu (ki lô mét|cây số) nữa", "(đến|tới) {city} còn bao xa",
    "từ đây (đến|tới) {poi} bao xa", "còn {km} nữa là (đến|tới) nơi đúng không", "từ đây đến {dist} bao nhiêu (ki lô mét|cây số)",
    "còn khoảng {km} nữa phải không", "từ {poi} đến {poi#2} bao xa",
], TPL)
F("CS01", "hoi_thoi_gian_den", "Câu hỏi", [
    "mấy giờ thì (đến|tới) nơi", "(đến|tới) {poi_air} mất bao lâu", "khoảng bao lâu nữa thì tôi (đến|tới) {city}", "dự kiến mấy giờ (đến|tới)",
    "tôi sẽ (đến|tới) nơi lúc mấy giờ", "còn khoảng {mins} nữa là (đến|tới) nơi đúng không", "(đến|tới) nơi lúc {clk} có kịp không",
    "liệu có (đến|tới) kịp lúc {clk} không", "đi {city} hết mấy tiếng", "đến {poi} trước {clk} được không",
], TPL)
F("CS01", "hoi_chi_dan_tiep_theo", "Câu hỏi", [
    "đoạn tới rẽ hướng nào", "sắp tới có phải rẽ (trái|phải) không", "rẽ (trái|phải) ở ngã tư tiếp theo đúng không",
    "còn {met} nữa là rẽ (trái|phải) đúng không", "lối ra tiếp theo là lối nào", "(đi thẳng|chạy thẳng) bao xa nữa thì rẽ (trái|phải)",
    "đến vòng xuyến thì đi lối ra thứ {ordw} đúng không", "khi nào phải chuyển sang làn (bên trái|bên phải)", "còn {met} nữa thì đến chỗ rẽ",
    "sau đó đi (thẳng|tiếp) hay rẽ", "ở ngã ba tới rẽ (trái|phải) hay đi thẳng", "rẽ vào {st} ở đâu", "có phải rẽ vào {st} không",
    "qua {met} nữa thì quay đầu đúng không",
], TPL)
F("CS01", "chon_lo_trinh", "Lệnh", [
    "(đi|chọn) đường (nhanh nhất|ngắn nhất|ít tắc đường nhất|ít đèn đỏ nhất)", "tránh (cao tốc|trạm thu phí|đường cấm tải|đoạn ngập nước)",
    "không đi qua (cao tốc|trạm thu phí|đường đang thi công)", "(ưu tiên|chọn) cao tốc", "đổi lộ trình khác",
    "cho tôi xem (các|những) (tuyến|lộ trình) (khác|còn lại)", "đi (theo|qua) {hw}", "(đi|chạy) {hw} được không", "chọn {hw}",
    "không đi {hw}", "đi qua {st} cho tôi", "tránh {st} ra",
], TPL)
F("CS01", "them_diem_dung", "Lệnh", [
    "thêm điểm dừng (tại|ở) {poi}", "ghé {cat} trước rồi (mới |)(đi tiếp|đến nơi)", "thêm một điểm dừng là {poi}", "tìm {cat} trên đường đi",
    "tìm cây xăng dọc đường", "dừng lại ở {cat} (tiếp theo|gần nhất)", "thêm {cat} vào lộ trình", "ghé qua {addr} trước",
    "ghé đón {ct} ở {addr} rồi đi tiếp",
], TPL)
F("CS01", "huy_dan_duong", "Lệnh", ["dừng lại, tôi đến nơi rồi", "~tôi đến nơi rồi, tắt dẫn đường", "hủy chỉ đường đến {poi}"], TPL)
F("CS01", "dieu_khien_ban_do", "Lệnh", [
    "phóng to bản đồ", "thu nhỏ bản đồ", "(bật|chuyển sang) chế độ bản đồ (ban đêm|ban ngày)", "chuyển bản đồ sang (ba chiều|hai chiều)",
    "xem toàn bộ lộ trình", "(hiển thị|xem) bản đồ hướng bắc lên trên", "(bật|tắt) hiển thị giao thông trên bản đồ", "hiện thông tin làn đường",
    "mở bản đồ khu vực {dist}", "tìm {st} trên bản đồ",
], TPL)
F("CS01", "tat_bat_tieng_dan_duong", "Lệnh", [
    "tăng âm lượng (chỉ đường|dẫn đường) lên {vol}", "giảm âm lượng (chỉ đường|dẫn đường) xuống {vol}", "đặt âm lượng (chỉ đường|dẫn đường) ở mức {vol}",
    "chỉ báo những chỗ quan trọng thôi", "đọc tên đường khi chỉ đường", "(bật|tắt) cảnh báo tốc độ trên bản đồ",
], TPL)
F("CS01", "tim_dia_diem_gan_day", "Lệnh", [
    "tìm {cat} gần (đây|nhất)", "~tôi cần tìm {cat}", "tìm {cat} quanh {poi}", "tìm {cat} trên {st}", "tìm {cat} ở {dist}",
    "tìm {cat} còn mở cửa", "dẫn đường đến {cat} gần nhất", "chỉ đường tới {cat} gần {poi}",
])
F("CS01", "tim_dia_diem_gan_day", "Câu hỏi", ["gần đây có {cat} nào không", "{cat} gần nhất ở đâu", "quanh {poi} có {cat} không",
                                               "có {cat} nào còn mở cửa không"])

# ================================================================= CS02 Cảnh báo an toàn
F("CS02", "bat_tat_he_thong_ho_tro", "Lệnh", [
    "(bật|tắt) {warn}", "(bật|tắt) {sysn}", "tắt tạm thời {warn}", "~tôi muốn (bật|tắt) {sysn}", "tạm tắt {sysn}",
    "bật lại {warn}", "tắt {warn} trong chuyến này", "(bật|tắt) {sysn} giúp tôi", "{warn} đang bật hay tắt",
    "(bật|tắt) auto hold", "bật lane assist", "tắt cảnh báo khi vượt quá tốc độ",
], TPL)
F("CS02", "do_nhay_canh_bao_chung", "Lệnh", [
    "đặt độ nhạy {warn} ở mức {lev}", "chỉnh {warn} sang mức {lev}", "(tăng|giảm) độ nhạy {warn}", "đổi độ nhạy cảnh báo va chạm sang mức {lev}",
    "giảm âm lượng cảnh báo xuống mức {lvl5}", "đặt âm báo cảnh báo ở mức {lvl5}", "chỉ rung vô lăng, đừng kêu", "~{warn} kêu nhiều quá",
], TPL)
F("CS02", "ga_tu_dong", "Lệnh", [
    "bật (ga tự động|hành trình thích ứng) (ở|với) tốc độ {spd}", "đặt tốc độ hành trình {spd}", "tăng tốc độ hành trình thêm {spd5}",
    "giảm tốc độ hành trình bớt {spd5}", "đặt khoảng cách với xe phía trước ở mức {gap}", "(tắt|hủy) (ga tự động|hành trình thích ứng)",
    "đặt cảnh báo khi vượt quá {spd}", "bật giới hạn tốc độ {spd}", "bật cruise control ở {spd}", "tắt cruise control", "giữ tốc độ {spd}",
], TPL)
F("CS02", "canh_bao_met_moi", "Lệnh", [
    "~tôi (tỉnh|ổn) rồi, (không cần|đừng) nhắc nữa", "tắt nhắc nhở nghỉ ngơi", "nhắc tôi nghỉ ngơi sau {mins}", "tìm trạm dừng chân gần nhất",
    "~tôi hơi mệt, tìm chỗ nghỉ gần đây", "~tôi biết rồi, tắt cảnh báo đi", "cho tôi nghỉ một lát rồi nhắc lại", "~tôi đang tỉnh, cảm ơn",
    "~buồn ngủ quá, mở {genre} cho tỉnh", "nhắc tôi nghỉ sau mỗi {mins}",
], TPL)

# ================================================================= CS03 Điều khiển xe
F("CS03", "dieu_hoa_bat_tat_nhiet_do", "Lệnh", [
    "đặt nhiệt độ điều hòa (ở|là) {temp_u}", "chỉnh điều hòa xuống {temp_u}", "chỉnh điều hòa lên {temp_u}", "bật điều hòa {temp_u}",
    "đặt nhiệt độ bên (lái|phụ) {temp_u}", "đặt nhiệt độ khoang sau {temp_u}", "đồng bộ nhiệt độ hai bên (ở|là) {temp_u}",
    "tăng nhiệt độ thêm {n3} độ", "giảm nhiệt độ bớt {n3} độ", "~tôi thấy nóng quá, chỉnh điều hòa xuống {temp_u}",
    "~tôi thấy lạnh quá, chỉnh điều hòa lên {temp_u}", "~{temp_u} thôi", "~tôi muốn điều hòa {temp_u}", "bật A/C {temp_u}",
    "bật air-con {temp_u}", "để điều hòa {temp_u} cho tôi", "nhiệt độ bên lái {temp_u}, bên phụ {temp_u#2}",
], TPL)
F("CS03", "dieu_hoa_quat_gio", "Lệnh", [
    "tăng quạt gió lên mức {fan}", "giảm quạt gió xuống mức {fan}", "đặt quạt gió mức {fan}", "~quạt gió mức {fan}", "chỉnh quạt (tối đa|nhỏ nhất)",
    "đặt quạt gió ở chế độ tự động", "tăng quạt thêm một nấc", "giảm quạt bớt một nấc", "quạt sau mức {fan}",
], TPL)
F("CS03", "dieu_hoa_huong_gio", "Lệnh", ["chỉnh gió {vent}", "đổi hướng gió {vent}", "cho gió thổi {vent}", "hướng gió bên phụ {vent}"], TPL)
F("CS03", "dieu_hoa_che_do", "Lệnh", [
    "(bật|tắt) điều hòa", "(bật|tắt) chế độ điều hòa tự động", "(bật|tắt) lọc không khí", "đổi sang chế độ tiết kiệm cho điều hòa",
    "(bật|tắt) chế độ điều hòa cho khoang sau", "bật điều hòa chế độ auto", "bật chế độ Eco cho điều hòa", "bật lọc bụi PM2.5",
], TPL)
F("CS03", "say_kinh", "Lệnh", ["(bật|tắt) sấy kính (trước|sau)", "bật chế độ khử sương kính", "(bật|tắt) sưởi kính sau", "sấy kính trước trong {mins}"], TPL)
F("CS03", "ghe_suoi_lam_mat_massage", "Lệnh", [
    "bật sưởi {seat} (ở |)mức {lvl3}", "tắt sưởi {seat}", "bật làm mát {seat} mức {lvl3}", "(tăng|giảm) sưởi {seat}",
    "bật massage {seat} mức {lvl3}", "tắt massage {seat}", "bật thông gió {seat} mức {lvl3}", "sưởi {seat} mức {lvl3} trong {mins}",
], TPL)
F("CS03", "ghe_nho_vi_tri", "Lệnh", [
    "đẩy ghế lái ra (sau|trước) một chút", "nâng ghế lái lên", "hạ ghế lái xuống", "chỉnh lưng ghế (lái|phụ) (ngả ra sau|dựng thẳng lên)",
    "lưu vị trí ghế vào hồ sơ {mem}", "gọi vị trí ghế đã lưu số {mem}", "đổi sang hồ sơ người lái {mem}", "đưa ghế về vị trí của {ct2}",
], TPL)
F("CS03", "cua_kinh", "Lệnh", [
    "(hạ|mở) kính {wpos} xuống (một nửa|hoàn toàn|một chút)", "kéo kính {wpos} (lên hết|lên một chút)", "đóng kính {wpos}", "đóng tất cả kính",
    "(mở|hạ) tất cả kính xuống một chút", "hạ kính {wpos} xuống {pct}", "hé kính {wpos} ra một chút", "mở kính {wpos} {pct}",
    "nâng kính {wpos} lên", "đóng kính lại, ngoài trời mưa",
], TPL)
F("CS03", "cua_so_troi", "Lệnh", ["mở cửa sổ trời {pct}", "mở cửa sổ trời (một nửa|hết)", "(đóng|mở) rèm che nắng cửa sổ trời",
                                    "hé cửa sổ trời ra", "mở rèm cửa sổ trời {pct}"], TPL)
F("CS03", "khoa_mo_cua", "Lệnh", ["(khóa|mở khóa) tất cả cửa", "mở khóa cửa {wpos}", "khóa cửa khi xe chạy trên {spd}", "tự khóa cửa khi đi"], TPL)
F("CS03", "guong", "Lệnh", ["gập gương chiếu hậu", "chỉnh gương (chiếu hậu |)(bên lái|bên phụ) (lên|xuống|vào trong|ra ngoài)",
                              "bật sấy gương", "mở gương ra"], TPL)
F("CS03", "den_noi_that", "Lệnh", ["(bật|tắt) {lamp}", "đổi màu đèn nội thất sang {color}", "chỉnh độ sáng đèn nội thất {pct}",
                                     "đèn viền màu {color}", "giảm độ sáng màn hình xuống {pct}", "tăng độ sáng màn hình lên {pct}"], TPL)
F("CS03", "gat_mua", "Lệnh", ["bật gạt mưa (chậm|nhanh|tự động)", "tắt gạt mưa", "gạt mưa mức {lvl3}", "phun nước rửa kính"], TPL)
F("CS03", "che_do_lai", "Lệnh", ["đổi chế độ lái sang (tiết kiệm|thể thao|tiêu chuẩn)", "(bật|tắt) chế độ (tiết kiệm|thể thao)",
                                   "chuyển sang chế độ Sport", "chuyển sang chế độ Eco", "về chế độ Normal", "bật chế độ lái êm"], TPL)
F("CS03", "vo_lang_den_ngoai", "Lệnh", ["(bật|tắt) sưởi vô lăng", "(bật|tắt) đèn (pha|chiếu sáng) tự động", "bật đèn sương mù",
                                          "bật đèn khẩn cấp", "tắt đèn pha", "bật đèn cốt"], TPL)
F("CS03", "wifi_camera", "Lệnh", ["bật camera 360", "mở camera trước", "xem camera lùi", "bật camera 360 độ khi lùi",
                                    "bật điểm phát wifi trên xe", "đổi mật khẩu wifi trên xe"], TPL)

# ================================================================= CS04 Giải trí
F("CS04", "phat_bai_ca_si", "Lệnh", [
    "mở bài {bai_hat}", "phát bài {bai_hat} của {ca_si}", "bật bài {bai_hat} (lên|)", "~tôi muốn nghe bài {bai_hat}", "mở nhạc của {ca_si}",
    "phát mấy bài hit của {ca_si}", "bật nhạc {ca_si} cho tôi", "cho tôi nghe {ca_si}", "phát nhạc của nhạc sĩ {composer}",
    "mở album mới nhất của {ca_si}", "phát bài mới nhất của {ca_si}", "mở bài {bai_hat} bản (live|acoustic|remix)",
], TPL)
F("CS04", "phat_the_loai_playlist", "Lệnh", [
    "(mở|bật|phát) {genre}", "cho tôi nghe {genre}", "~tôi muốn nghe {genre}", "chuyển sang {genre}", "phát {genre} liên tục",
    "(mở|bật) {genre} cho (đỡ buồn ngủ|vui|thư giãn)", "(mở|phát|bật) danh sách phát {plist}", "phát {plist}", "bật playlist {plist}",
    "mở danh sách {plist}", "phát danh sách {plist} (ngẫu nhiên|từ đầu)", "thêm bài này vào danh sách {plist}",
    "mở {genre} trên {music_app}", "phát {plist} trên {music_app}", "mở {music_app} phát {genre}",
], TPL)
F("CS04", "phat_theo_tam_trang", "Lệnh", ["mở nhạc {mood}", "bật nhạc {mood}", "phát nhạc {mood}", "cho tôi nghe nhạc {mood}",
                                            "~tôi muốn nghe nhạc {mood}", "đổi sang nhạc {mood}", "chọn nhạc {mood} giúp tôi"], TPL)
F("CS04", "chuyen_bai_tam_dung", "Lệnh", ["bỏ qua bài này", "tua tới {sec}", "tua lại {sec}", "tua về đầu bài", "(bật|tắt) phát ngẫu nhiên",
                                            "hẹn giờ tắt nhạc sau {mins}", "tắt nhạc sau {mins}"], TPL)
F("CS04", "am_luong", "Lệnh", ["tăng âm lượng lên {vol}", "giảm âm lượng xuống {vol}", "đặt âm lượng ở mức {vol}", "~âm lượng {vol}",
                                 "đặt âm lượng {pct}", "~tôi nghe không rõ, tăng âm lượng lên", "~to quá, giảm âm lượng xuống {vol}",
                                 "giảm âm lượng loa trước xuống {vol}", "chỉnh âm trầm lên mức {lvl5}", "giảm bass xuống mức {lvl5}"], TPL)
F("CS04", "radio", "Lệnh", ["(mở|bật|nghe) (đài|kênh) {radio}", "chuyển sang (đài|kênh) {radio}", "~tôi muốn nghe (đài|kênh) {radio}",
                              "chuyển sang {freq}", "dò đài {freq}", "(mở|bật) đài {freq}", "bật radio {freq}", "lưu đài {freq} vào mục yêu thích",
                              "~đài nào đang phát tin giao thông"], TPL)
F("CS04", "nguon_nhac_bluetooth_usb", "Lệnh", ["chuyển sang nguồn {src}", "(bật|tắt) {src}", "phát nhạc từ {src}", "ngắt kết nối {src}",
                                                 "đổi nguồn phát sang {src}"], TPL)
F("CS04", "podcast", "Lệnh", ["(nghe|mở|phát) {pod}", "tiếp tục (nghe|phát) {pod} (đang nghe dở|từ chỗ dừng)", "~tôi muốn nghe {pod}",
                                "mở podcast về {chu_de}", "tìm podcast chủ đề {chu_de}", "phát tập mới nhất về {chu_de}", "đọc {pod} cho tôi nghe",
                                "tua podcast tới {mins}", "phát sách nói về {chu_de}"], TPL)
F("CS04", "hoi_bai_dang_phat", "Câu hỏi", ["bài này của (album|đĩa) nào", "bài này phát hành (năm nào|lúc nào)", "{ca_si} còn bài nào hay không",
                                            "bài này có phải của {ca_si} không"], TPL)
F("CS04", "yeu_thich", "Lệnh", ["thêm bài này vào (danh sách yêu thích|bài hát yêu thích)", "lưu bài này vào {plist}", "xóa bài này khỏi {plist}"], TPL)

# ================================================================= CS05 Điện thoại
F("CS05", "goi_theo_ten", "Lệnh", [
    "gọi (điện |)(cho |){ct}", "gọi điện thoại cho {ct}", "gọi {ct} giúp tôi", "gọi {ct} (số di động|số cơ quan|số nhà)", "~tôi muốn gọi cho {ct}",
    "quay số gọi {ct}", "bắt đầu cuộc gọi với {ct}", "liên lạc với {ct}", "gọi video cho {ct}", "kêu {ct} giùm tôi", "gọi cho {ct} bằng loa ngoài",
], TPL)
F("CS05", "goi_theo_so", "Lệnh", ["bấm số {ph}", "gọi tới số {ph}", "quay số {ph}", "gọi giúp tôi số {ph}", "~tôi cần gọi số {ph}",
                                    "gọi số này {ph}", "lưu số {ph} tên là {ct}", "gửi số {ph} cho {ct}"], TPL)
F("CS05", "goi_lai", "Lệnh", ["gọi lại cuộc gọi nhỡ (vừa rồi|gần nhất)", "gọi cho người vừa gọi cho tôi", "gọi lại số cuối cùng",
                                "xem (danh sách |)cuộc gọi nhỡ", "gọi lại cho {ct} lúc {clk}", "nhắc tôi gọi lại cho {ct} sau {mins}"], TPL)
F("CS05", "nhan_tu_choi_cuoc_goi", "Lệnh", ["chuyển cuộc gọi sang loa ngoài", "tăng âm lượng cuộc gọi", "tắt tiếng micro", "bật lại micro",
                                              "(giữ|chờ) máy một lát", "chuyển cuộc gọi sang điện thoại", "từ chối và nhắn là {msg}"], TPL)
F("CS05", "doc_tin_nhan", "Lệnh", ["đọc tin nhắn (mới nhất|vừa tới)", "đọc tin nhắn của {ct}", "đọc lại tin nhắn của {ct}",
                                     "(đọc|nghe) tin nhắn từ {ct}", "đọc tin nhắn {msg_app} của {ct}"], TPL)
F("CS05", "soan_gui_tin_nhan", "Lệnh", [
    "trả lời (tin nhắn |)(là|rằng) {msg}", "nhắn (cho |tin cho ){ct} (là|rằng) {msg}", "gửi tin nhắn cho {ct}: {msg}", "nhắn lại (là|rằng) {msg}",
    "nhắn cho {ct} là tôi đến muộn {mins}", "nhắn {ct} đợi {mins}", "nhắn cho {ct} khoảng {clk} mình đến", "báo cho {ct} là tôi đến lúc {clk}",
    "báo {ct} biết tôi sẽ đến sau {mins}", "nhắn {ct} gặp nhau ở {poi}", "gửi cho {ct} địa chỉ {addr}",
], TPL)
F("CS05", "nhan_zalo", "Lệnh", ["nhắn Zalo cho {ct} (là|rằng) {msg}", "gọi Zalo cho {ct}", "gửi Zalo cho {ct} vị trí hiện tại",
                                  "nhắn {msg_app} cho {ct}: {msg}", "gọi video Zalo cho {ct}", "gọi {msg_app} cho {ct}"], TPL)
F("CS05", "chia_se_vi_tri", "Lệnh", ["gửi vị trí (hiện tại |)(cho|tới) {ct}", "chia sẻ (lộ trình|vị trí) (cho|với) {ct}",
                                       "gửi giờ đến dự kiến cho {ct}", "chia sẻ chuyến đi này với {ct}", "dừng chia sẻ vị trí với {ct}",
                                       "gửi {ct} địa chỉ đang dẫn đường", "chia sẻ vị trí với {ct} trong {mins}"], TPL)

# ================================================================= CS06 Trạng thái xe
F("CS06", "ap_suat_lop", "Câu hỏi", ["áp suất {tire} là bao nhiêu", "có lốp nào (thiếu hơi|non hơi|bị xì) không", "{tire} có ổn không",
                                     "{tire} có cần bơm không", "lốp nào áp suất thấp nhất"], TPL)
F("CS06", "ap_suat_lop", "Lệnh", ["kiểm tra áp suất {tire}", "hiện áp suất bốn lốp lên màn hình", "đặt lại cảm biến áp suất lốp"], TPL)
F("CS06", "nhien_lieu_quang_duong", "Câu hỏi", ["còn đủ xăng đi {km} nữa không", "đi thêm {km} có cần đổ xăng không",
                                                "xăng còn đủ để (đến|tới) {city} không", "kim xăng còn bao nhiêu", "mức tiêu hao trung bình chuyến này là bao nhiêu",
                                                "đổ đầy bình hết khoảng bao nhiêu tiền", "~tôi có cần đổ xăng chưa"], TPL)
F("CS06", "bao_duong", "Câu hỏi", ["còn {km} nữa thì đến kỳ bảo dưỡng phải không", "{part} còn tốt không",
                                   "lần bảo dưỡng gần nhất là khi nào", "xe có lỗi nào đang báo không", "{part} bao lâu thì phải thay"], TPL)
F("CS06", "bao_duong", "Lệnh", ["đặt lịch bảo dưỡng {when}", "nhắc tôi thay dầu sau {km}", "hẹn bảo dưỡng ở {place_saved} {day}",
                                "nhắc tôi kiểm tra {part} {day}", "gọi xưởng dịch vụ đặt lịch {when}", "kiểm tra tình trạng {part}"], TPL)
F("CS06", "den_canh_bao", "Câu hỏi", ["đèn báo {wlamp} (sáng|nhấp nháy) nghĩa là gì", "đèn {wlamp} sáng là sao", "đèn {wlamp} sáng có nguy hiểm không",
                                      "tại sao đèn {wlamp} sáng", "tôi có cần dừng xe vì đèn {wlamp} không", "đèn check engine sáng là sao"], TPL)
F("CS06", "so_km_da_di", "Câu hỏi", ["quãng đường đã đi (hôm nay|trong chuyến này) là bao nhiêu", "tốc độ trung bình (của chuyến đi |)là bao nhiêu",
                                     "đã chạy được bao lâu rồi", "xe đã chạy quá {km} chưa"], TPL)
F("CS06", "so_km_da_di", "Lệnh", ["đặt lại công tơ mét hành trình", "đặt lại quãng đường chuyến đi"], TPL)
F("CS06", "nhiet_do_dong_co", "Câu hỏi", ["nhiệt độ nước làm mát bây giờ bao nhiêu độ", "nhiệt độ máy có vượt {eng_temp} không",
                                          "nước làm mát {eng_temp} có bình thường không", "máy đang {eng_temp} có sao không"], TPL)

# ================================================================= CS07 Sạc xe điện và trạm xăng
F("CS07", "phan_tram_pin", "Câu hỏi", ["pin còn trên {pct_bat} không", "mức pin (khi|lúc) (đến|tới) {poi} (là|sẽ là) bao nhiêu",
                                       "tình trạng pin (thế nào|ra sao)", "(sức khỏe|tình trạng) pin (hiện tại |)là bao nhiêu",
                                       "pin xuống dưới {pct_bat} chưa"], TPL)
F("CS07", "phan_tram_pin", "Lệnh", ["báo tôi khi pin còn {pct_bat}", "hiện phần trăm pin lên màn hình"], TPL)
F("CS07", "quang_duong_con_lai_ev", "Câu hỏi", ["pin có đủ (để |)đi (đến|tới) {poi} không", "pin còn đủ để (đến|tới) {city} không",
                                                "còn đi được {km} nữa không", "đi {city} có cần sạc giữa đường không", "bật điều hòa thì còn đi được bao xa"], TPL)
F("CS07", "tim_tram_sac", "Lệnh", ["tìm trạm sạc (gần nhất|gần đây|trên đường đi|dọc lộ trình)", "tìm trạm sạc nhanh (gần nhất|gần đây)",
                                   "tìm trạm sạc (còn trống|có cổng trống)", "dẫn đường đến trạm sạc (gần nhất|nhanh nhất)", "tìm trạm sạc gần {poi}",
                                   "tìm trạm sạc ở {city}", "tìm trạm sạc có {cat} gần đây", "~tôi cần sạc xe, tìm trạm sạc gần nhất",
                                   "tìm trạm sạc trên {st}", "tìm trạm sạc ở {dist}", "tìm trụ sạc {kw} gần đây", "tìm trạm sạc trên {hw}"], TPL)
F("CS07", "gioi_han_sac", "Lệnh", ["đặt (giới hạn|mức) sạc (tối đa |)ở {pct_bat}", "sạc (đến|lên) {pct_bat} (rồi|thì) (dừng|báo)",
                                   "tắt sạc (khi|lúc) pin đạt {pct_bat}", "sạc (đến|lên) {pct_bat} thôi"], TPL)
F("CS07", "hen_gio_sac", "Lệnh", ["(đặt|hẹn) giờ sạc (lúc|vào) {clk}", "hủy (hẹn giờ |lịch )sạc", "(tăng|giảm) dòng sạc", "sạc xong trước {clk}",
                                  "bắt đầu sạc lúc {clk} {day}"], TPL)
F("CS07", "cong_sac", "Lệnh", ["mở (nắp|cổng) sạc", "đóng (nắp|cổng) sạc"], TPL)
F("CS07", "thoi_gian_chi_phi_sac", "Câu hỏi", ["sạc từ {pct2} mất bao lâu", "sạc thêm {kwh} hết bao nhiêu tiền", "(chi phí|giá) sạc một ki lô oát giờ là bao nhiêu",
                                               "đã sạc được bao nhiêu ki lô oát giờ rồi", "sạc (đến|lên) {pct_bat} còn (mất |)bao lâu",
                                               "sạc ở trụ {kw} thì bao lâu đầy", "giá sạc {money} một ki lô oát giờ đúng không", "sạc {kwh} mất bao lâu"], TPL)
F("CS07", "tim_tram_xang", "Lệnh", ["tìm cây xăng (gần nhất|trên đường đi|gần đây)", "dẫn đường đến cây xăng (gần nhất|)",
                                    "tìm cây xăng có (cửa hàng tiện lợi|nhà vệ sinh)", "tìm cây xăng ở {city}", "~tôi cần đổ xăng, tìm cây xăng gần nhất",
                                    "tìm cây xăng trên {st}", "tìm cây xăng trên {hw}"], TPL)
F("CS07", "tim_tram_xang", "Câu hỏi", ["giá xăng (hôm nay |)là bao nhiêu", "cây xăng gần nhất ở đâu", "giá xăng 95 bao nhiêu một lít",
                                       "đổ {money} xăng thì được mấy lít",
                                       "xăng tăng giá lên {money} phải không"], TPL)

# ================================================================= CS08 Giao thông và thời tiết
F("CS08", "tac_duong_phia_truoc", "Câu hỏi", [
    "{st} có đang tắc đường không", "{hw} có tắc không", "đường từ đây (đến|tới) {poi} có tắc không", "tình hình giao thông ở {dist} thế nào",
    "tắc đường còn kéo dài khoảng {km} nữa không", "đoạn tắc phía trước dài bao nhiêu", "giờ này {st} có đông không", "cầu {st} có kẹt không",
    "đi {hw} giờ này có tắc không", "khu vực {poi} có tắc đường không",
])
F("CS08", "tac_duong_phia_truoc", "Lệnh", ["đọc tin giao thông trên {hw}", "báo cho tôi nếu {st} tắc đường", "cập nhật tình hình giao thông đến {poi}",
                                           "cảnh báo tôi khi phía trước tắc đường"])
F("CS08", "tai_nan_su_co", "Câu hỏi", ["có tai nạn trên {hw} không", "trên {st} có sự cố gì không", "phía trước có xe hỏng không",
                                       "chỗ tai nạn còn cách bao xa", "đoạn {st} đang sửa đường phải không", "trên đường đi {city} có sự cố gì không"])
F("CS08", "tai_nan_su_co", "Lệnh", ["báo cáo có tai nạn ở đây", "báo có xe hỏng chắn đường", "báo đoạn này đang có công an kiểm tra"])
F("CS08", "toc_do_toi_da", "Câu hỏi", ["đoạn này giới hạn {spd} phải không", "{hw} chạy tối đa bao nhiêu", "trên {hw} tốc độ tối thiểu là bao nhiêu",
                                       "tôi chạy {spd} có quá tốc độ không", "trong khu dân cư được chạy bao nhiêu"])
F("CS08", "toc_do_toi_da", "Lệnh", ["nhắc tôi khi vượt quá {spd}", "hiện biển báo tốc độ lên màn hình"])
F("CS08", "camera_phat_nguoi", "Câu hỏi", ["trên {hw} có camera phạt nguội không", "còn {met} nữa có camera đúng không", "xe tôi có bị phạt nguội không"])
F("CS08", "camera_phat_nguoi", "Lệnh", ["tra cứu phạt nguội cho xe tôi", "cảnh báo trước {met} khi có camera"])
F("CS08", "thoi_tiet_hom_nay_mai", "Câu hỏi", [
    "thời tiết ở {city} {day} thế nào", "{day} {city} có {weather} không", "{city} {day} bao nhiêu độ", "{day} ở {city} có mưa không",
    "dự báo thời tiết {city} {day} ra sao", "trên đường đi {city} có {weather} không", "lúc {clk} ở {city} có mưa không",
    "cuối tuần này {city} có {weather} không", "ở {dist} đang mưa hay nắng", "{day} có nên mang ô không",
])
F("CS08", "thoi_tiet_hom_nay_mai", "Lệnh", ["đọc dự báo thời tiết {city} {day}", "cho tôi xem thời tiết {day}", "báo tôi nếu {city} có {weather}"])
F("CS08", "nhiet_do_mua", "Câu hỏi", ["ngoài trời có trên {temp_u} không", "mấy giờ thì {city} tạnh mưa", "khả năng mưa {day} là bao nhiêu phần trăm",
                                      "nhiệt độ thấp nhất {day} ở {city} là bao nhiêu", "{city} {day} nóng nhất bao nhiêu độ", "mưa ở {city} kéo dài đến mấy giờ"])
F("CS08", "chat_luong_khong_khi", "Câu hỏi", ["chỉ số không khí ở {city} hôm nay là bao nhiêu", "AQI {aqi} có nguy hiểm không",
                                              "không khí ở {dist} có ô nhiễm không", "có nên đóng kính và bật lọc không khí không"])
F("CS08", "gio_den_theo_giao_thong", "Câu hỏi", ["đi bây giờ thì mấy giờ đến {poi}", "nếu tắc đường thì có kịp đến {poi} lúc {clk} không",
                                                 "đi đường {hw} thì đến {city} lúc mấy giờ", "giờ này đi {dist} mất bao lâu",
                                                 "xuất phát lúc {clk} thì mấy giờ tới {poi}"])
F("CS08", "ngap_nuoc", "Câu hỏi", ["{st} có ngập không", "đường đến {poi} có bị ngập không", "ở {dist} đang ngập chỗ nào",
                                   "nước ngập sâu bao nhiêu", "đoạn ngập phía trước xe gầm thấp đi được không"])
F("CS08", "ngap_nuoc", "Lệnh", ["tìm đường tránh chỗ ngập", "báo cho tôi các điểm ngập ở {dist}", "tránh {st} vì đang ngập"])

# ================================================================= CS09 Khẩn cấp
F("CS09", "goi_cap_cuu_115", "Lệnh", ["gọi 115, có người bị thương ở {addr}", "gọi cấp cứu đến {poi}", "gọi 115, tai nạn trên {hw}",
                                      "gọi cấp cứu, tôi đang ở {st}", "gọi xe cấp cứu tới {addr}", "gọi 115 ngay, có người ngất"])
F("CS09", "goi_cong_an_113", "Lệnh", ["gọi 113, có người đập kính xe ở {st}", "gọi công an tới {addr}", "báo công an có trộm ở {poi}"])
F("CS09", "goi_cuu_hoa_114", "Lệnh", ["gọi 114, xe đang bốc khói trên {hw}", "gọi cứu hỏa đến {addr}", "gọi 114, cháy ở {st}"])
F("CS09", "cuu_ho_giao_thong", "Lệnh", ["gọi cứu hộ, xe chết máy trên {hw}", "gọi cứu hộ đến {st}", "gọi xe kéo đến {addr}",
                                        "xe hết pin trên {hw}, gọi cứu hộ", "gọi cứu hộ, tôi bị thủng lốp ở {dist}", "gọi cho {ct}, xe tôi bị hỏng ở {st}"])
F("CS09", "bao_tai_nan", "Lệnh", ["báo cho {ct} là tôi bị tai nạn", "gửi vị trí tai nạn cho {ct}", "gọi cho {ct}, tôi vừa va chạm",
                                  "báo tai nạn trên {hw}"])
F("CS09", "bao_vi_tri_khan_cap", "Lệnh", ["gửi vị trí của tôi cho {ct} ngay", "chia sẻ vị trí khẩn cấp cho {ct}", "gửi vị trí cho cứu hộ",
                                          "gửi vị trí cho 115", "~tôi đang ở gần {poi}, gửi vị trí đi", "~tôi đang ở {addr}, gọi người tới giúp",
                                          "gửi tin nhắn khẩn cấp cho {ct}", "bật đèn khẩn cấp và gọi {ct}"])
F("CS09", "toi_on", "Câu cụt", ["~tôi ổn, không cần gọi {ct}", "~đừng gọi 115, tôi không sao", "~không sao, chỉ va nhẹ thôi",
                                "~tôi ổn, hủy gửi vị trí", "~báo nhầm, tắt cảnh báo đi"])
F("CS09", "keu_cuu", "Kêu cứu", ["!cứu với, có cháy", "!cứu tôi với, kẹt cửa rồi", "!có ai không, giúp với", "!cứu, xe bị lật",
                                 "!gọi người giúp với", "!cứu với, có người bị thương", "!cứu với, xe rơi xuống nước", "!mở cửa ra, cứu tôi",
                                 "!cứu, tôi không mở được cửa", "!giúp tôi với, xe đang cháy", "!cứu với, có người ngất",
                                 "!dừng xe lại, cứu với", "!cứu, tôi bị kẹt chân", "!giúp với, bé bị khó thở", "!cứu, có người bị ngã xe",
                                 "!nhanh lên, gọi cấp cứu", "!cứu với, tôi đang ở {st}", "!cứu tôi, tôi bị tai nạn ở {hw}",
                                 "!có cháy ở {addr}, cứu với", "!cứu với, có người bị thương ở {poi}"])
F("CS09", "toi_on", "Câu cụt", ["~tôi không bị thương", "~mọi người đều ổn", "~không ai bị thương cả", "~tôi ổn, chỉ hơi choáng",
                                "~không cần gọi cứu hộ, xe vẫn chạy được"])

# ================================================================= CS10 Hội thoại
F("CS10", "nhac_viec", "Lệnh", ["nhắc tôi {todo} {when}", "nhắc tôi {todo} lúc {clk}", "{when} nhắc tôi {todo}", "đặt lời nhắc {todo} {when}",
                                "nhắc tôi {todo} khi về đến {home}", "nhắc tôi {todo} khi đến {place_saved}", "nhắc tôi {todo} sau {mins}",
                                "nhắc tôi {todo} khi đi ngang {cat}", "nhắc tôi gọi cho {ct} {when}", "nhắc tôi mua {mon_hang} khi đi ngang siêu thị",
                                "tạo lời nhắc {todo} hằng ngày lúc {clk}", "xóa lời nhắc {todo}", "dời lời nhắc {todo} sang {when}",
                                "~ờ, nhắc tôi {todo} nhé"], TPL)
F("CS10", "dat_lich", "Lệnh", ["đặt lịch hẹn với {ct} {when}", "đặt lịch họp với {ct} {when} ở {poi}", "dời cuộc họp với {ct} sang {when}",
                               "hủy lịch hẹn {when}", "thêm lịch đi {city} {day}", "đặt lịch khám ở {poi_hosp} {when}", "mời {ct} họp {when}"], TPL)
F("CS10", "dat_lich", "Câu hỏi", ["{day} tôi có lịch gì", "cuộc hẹn với {ct} là lúc mấy giờ", "{when} tôi có rảnh không"])
F("CS10", "bao_thuc_hen_gio", "Lệnh", ["đặt báo thức lúc {clk}", "đặt báo thức {clk} {day}", "hẹn giờ {mins}", "đếm ngược {mins}",
                                       "báo thức {clk} các ngày trong tuần", "tắt báo thức {clk}"], TPL)
F("CS10", "hoi_gio_ngay", "Câu hỏi", ["{day} là ngày bao nhiêu", "{day} là thứ mấy", "còn mấy ngày nữa đến {day}", "{day} là ngày mấy âm lịch",
                                      "bây giờ ở {quoc_gia} là mấy giờ"])
F("CS10", "hoi_quan_an", "Câu hỏi", ["quanh đây có quán {dish} nào ngon không", "gần {poi} có quán {dish} không", "quán {ten_quan} mấy giờ đóng cửa",
                                     "quán {dish} nào còn mở lúc {clk}", "ở {dist} ăn {dish} ở đâu ngon"])
F("CS10", "hoi_quan_an", "Lệnh", ["đặt bàn ở quán {ten_quan} {when}", "đặt bàn cho {ppl} người lúc {clk}", "tìm quán {dish} gần {poi}",
                                  "gợi ý quán {dish} ở {city}", "gọi điện cho quán {ten_quan}", "dẫn đường đến quán {ten_quan}"])
F("CS10", "hoi_quan_co_cho_do", "Câu hỏi", ["gần đây có {cat} nào có chỗ đỗ xe không", "quán {ten_quan} có chỗ đỗ ô tô không",
                                            "{poi} có bãi đỗ xe không", "gần {poi} chỗ nào đỗ xe được", "đỗ xe ở {poi} mất bao nhiêu tiền",
                                            "bãi đỗ xe gần {poi} còn chỗ không"])
F("CS10", "hoi_dap_chung", "Câu hỏi", ["thủ đô của {quoc_gia} là gì", "dân số {city} là bao nhiêu", "từ {city} đến {city#2} bao nhiêu cây số",
                                       "{city} có món gì ngon", "{city} có gì chơi", "đặc sản {city} là gì", "giá vàng hôm nay bao nhiêu",
                                       "tỷ giá đô la hôm nay là bao nhiêu"])
F("CS10", "tinh_toan_doi_tien", "Câu hỏi", ["{arith} bằng bao nhiêu", "{currency} là bao nhiêu tiền Việt", "{money} chia {ppl} người mỗi người bao nhiêu"])
F("CS10", "tinh_toan_doi_tien", "Lệnh", ["tính giúp tôi {arith}", "đổi {currency} sang tiền Việt", "chia đều {money} cho {ppl} người"])
F("CS10", "tin_tuc", "Lệnh", ["đọc tin {news} hôm nay", "cho tôi nghe tin {news}", "đọc tin mới về {chu_de}", "tóm tắt tin {news} sáng nay",
                              "mở bản tin {news} lúc {clk}"])
F("CS10", "tro_chuyen_tam_su", "Câu cụt", ["~hôm nay tôi mệt quá", "~tôi chán quá, nói gì vui đi", "~tôi đang buồn, mở {genre} đi"])
F("CS10", "chao_cam_on", "Câu cụt", ["~cảm ơn nhé, hẹn gặp lại", "~chào buổi (sáng|chiều|tối)", "~ok, cảm ơn", "~được rồi, cảm ơn bạn"])

# ================================================================= CS11 Hành khách và trẻ em
F("CS11", "tre_xem_nhac_phim_truyen", "Lệnh", ["mở {ten_phim} cho con xem", "con muốn xem {ten_phim}", "bật nhạc thiếu nhi cho con nghe",
                                              "mở bài {bai_hat} cho con", "kể chuyện cổ tích cho con nghe đi", "con muốn nghe {genre}",
                                              "mở phim {ten_phim} ở màn hình sau", "bật {pod} cho các bé"])
F("CS11", "tre_noi", "Câu cụt", ["~con nóng quá", "~con buồn ngủ", "~con muốn đi vệ sinh", "~con đói", "~mẹ ơi con say xe",
                                 "~con muốn mở kính ra", "~con lạnh", "~tắt nhạc đi, con muốn ngủ", "~bố ơi con khát nước"])
F("CS11", "tre_noi", "Câu hỏi", ["~bao giờ mới tới nơi", "~còn bao lâu nữa tới {poi}", "!mình đi {city} hả bố", "!sắp tới {poi} chưa mẹ",
                                 "~con xem {ten_phim} được không", "~ngoài trời có mưa không", "!bố ơi còn xa không",
                                 "!mẹ ơi mấy giờ mình tới {city}"])
F("CS11", "dieu_hoa_khoang_sau", "Lệnh", ["đặt nhiệt độ hàng ghế sau {temp_u}", "điều hòa phía sau {temp_u}", "giảm quạt hàng ghế sau xuống mức {fan}",
                                          "tăng quạt khoang sau lên mức {fan}", "chỉnh gió hàng ghế sau {vent}", "tắt điều hòa hàng ghế thứ ba",
                                          "bật sưởi {seat} mức {lvl3}"])
F("CS11", "tat_loa_sau", "Lệnh", ["đặt âm lượng loa sau ở mức {vol}", "giảm loa sau xuống {vol}", "cho hàng ghế sau nghe {genre}",
                                  "phát {plist} ở loa sau", "tắt loa sau trong {mins}"])
F("CS11", "che_do_yen_tinh", "Lệnh", ["bật chế độ yên tĩnh trong {mins}", "bé ngủ rồi, giảm âm lượng xuống {vol}", "bật chế độ ru ngủ cho bé",
                                      "chỉ phát dẫn đường ở loa trước"])
F("CS11", "nhac_day_an_toan_ghe_sau", "Lệnh", ["nhắc {ct} thắt dây an toàn", "kiểm tra dây an toàn {seat}", "báo khi {seat} tháo dây an toàn"])
F("CS11", "khoa_tre_em", "Lệnh", ["bật khóa trẻ em cửa sau", "khóa kính sau lại", "khóa cửa {wpos}", "tắt khóa trẻ em", "khóa kính {wpos}",
                                  "không cho mở kính sau", "mở khóa cửa sau cho {ct} xuống"])

# ================================================================= CS12 Làm rõ, trả lời ngắn
F("CS12", "sua_lenh", "Lệnh", [
    "~không phải, ý tôi là {cau_dung}", "~nhầm rồi, {cau_dung}", "~không phải {poi}, tôi muốn đến {poi#2}", "~sai rồi, tôi muốn đến {addr}",
    "~không phải {ct}, gọi {ct#2}", "~không, ý tôi là bài {bai_hat}", "~sửa lại thành {temp_u}", "~đổi lại thành {poi}", "~ý tôi là {ca_si} cơ",
    "~tôi nói là {poi}, không phải chỗ đó", "~không phải {city}, là {city#2}", "~ý tôi là {dist}", "~không phải số đó, số {ph}",
    "~nhầm rồi, {clk} chứ không phải {clk#2}", "~không phải mức đó, mức {fan}", "~ờ không, {cau_dung}", "~không phải {genre}, mở {genre#2}",
    "~tôi nói {st} chứ không phải {st#2}", "~sai tên rồi, là {ct}", "~không, nhắn cho {ct} cơ", "~không phải đâu, đi {home}",
    "~ý tôi là {mins} chứ không phải {mins#2}", "~không phải đài đó, mở {radio}",
])
F("CS12", "noi_lai", "Lệnh", ["~nói lại chậm hơn được không", "~đọc lại địa chỉ đó", "~đọc lại số điện thoại vừa rồi", "~nhắc lại tên đường giúp tôi",
                              "~đọc lại tin nhắn của {ct}", "~nói lại giờ đến giúp tôi"])
F("CS12", "xem_them_lua_chon", "Lệnh", ["~xem thêm {cat} khác", "~cho xem kết quả ở {dist}", "~tìm {cat} khác gần hơn"])
F("CS12", "xem_them_lua_chon", "Câu hỏi", ["~cái nào gần {poi} nhất", "~có quán nào rẻ hơn không", "~còn {cat} nào khác không"])
F("CS12", "ngoai_tuyen", "Câu hỏi", ["~mất mạng rồi à", "~sao không tìm được đường", "~không có mạng thì dẫn đường được không",
                                     "~tải bản đồ {city} để dùng không cần mạng được không", "~sao không gọi được cho {ct}", "~sao không phát được bài này"])
F("CS12", "ngoai_tuyen", "Lệnh", ["~tải bản đồ {city} về máy", "~thử kết nối lại mạng", "~chuyển sang bản đồ ngoại tuyến"])
# M2: câu trả lời ngắn cho câu hỏi của trợ lý
F("CS12", "tra_loi_gia_tri", "Trả lời ngắn", [
    "~{temp_u}", "~{temp_u} thôi", "~mức {fan}", "~mức {lvl5}", "~{clk}", "~lúc {clk}", "~{day}", "~{ct}", "~gọi {ct}", "~{poi}", "~{dist}",
    "~{city}", "~{ph}", "~số {ph}", "~{mins}", "~khoảng {mins}", "~{pct_bat}", "~{vol}", "~âm lượng {vol}", "~số {mem}", "~hồ sơ {mem}",
    "~{genre}", "~bài {bai_hat}", "~{ca_si}", "~{radio}", "~{freq}", "~{home}", "~{place_saved}", "~{st}", "~{ppl} người", "~{cat}",
    "~{money}", "~{km}", "~đường {hw}",
], purpose="M2")
F("CS12", "chon_ket_qua", "Trả lời ngắn", [
    "~cái thứ {ordw}", "~số {lvl5}", "~chọn số {lvl5}", "~lấy cái thứ {ordw}", "~cái {ordw}", "~(quán|trạm|chỗ|đường|người) thứ {ordw}",
    "~chọn {poi}", "~cái ở {st}", "~cái gần {poi}", "~cái ở {dist}", "~chọn {ct}", "~người tên {ct}", "~cái đầu tiên", "~cái cuối cùng",
    "~cái gần nhất", "~cái rẻ nhất", "~đường thứ {ordw}", "~lộ trình {lvl3}", "~chọn tuyến {lvl3}", "~kết quả {lvl5}",
], purpose="M2")
F("CS12", "xac_nhan_dong_y", "Trả lời ngắn", [
    "~có", "~có, đúng rồi", "~vâng", "~vâng ạ", "~dạ", "~dạ đúng", "~dạ phải", "~đúng", "~đúng rồi", "~phải", "~phải rồi", "~ừ", "~ừ đúng rồi",
    "~ừ, làm đi", "~ok", "~ok luôn", "~được", "~được rồi", "~đồng ý", "~xác nhận", "~gửi đi", "~gọi đi", "~đi thôi", "~chính xác",
    "~đúng rồi, dẫn đường đi", "~đúng, gọi luôn", "~ừ, gửi luôn", "~có, nhắn lại đi", "~có, mở đi", "~vâng, đúng người đó", "~chắc chắn",
    "~đúng địa chỉ đó", "~đúng số đó", "~có, lưu lại", "~ừ, bật lên", "~được, cứ thế",
], purpose="M2")
F("CS12", "tu_choi_huy_dung", "Trả lời ngắn", [
    "~không", "~không phải", "~không đúng", "~thôi", "~thôi khỏi", "~hủy", "~hủy đi", "~hủy bỏ", "~dừng", "~dừng lại", "~đừng", "~không cần",
    "~không cần đâu", "~để sau", "~lát nữa", "~chưa", "~chưa cần", "~bỏ qua", "~không gửi", "~không gọi nữa", "~thôi, không đi nữa",
    "~khoan đã", "~chờ chút", "~đợi đã", "~không, cảm ơn", "~thôi, để tôi tự làm", "~đừng gửi", "~không lưu", "~quay lại", "~trở lại",
], purpose="M2")


def _load_src_frames():
    """Khung từ sources/src_commands.json."""
    out = []
    for it in P.CMDS["intents"]:
        intent = it["intent"]
        smap = dict(SRC_SLOT_MAP["_default"])
        smap.update(SRC_SLOT_MAP.get(intent, {}))
        for i, p in enumerate(it["patterns"]):
            t = p["text"]
            for a, b in SRC_TEXT_FIX:
                t = t.replace(a, b)
            t = re.sub(r"\{(\w+)\}", lambda m: "{" + smap.get(m.group(1), m.group(1)) + "}", t)
            t = t.rstrip("?.!").strip()
            t = t[0].lower() + t[1:] if t and not t.startswith("{") and not re.match(r"[A-Z]{2}", t) else t
            # tên riêng đầu câu giữ hoa
            for name in ("Zalo", "Podcast", "Radio", "Messenger", "Tết", "Apple", "Hà Nội", "Việt Nam", "Đô", "USD", "VND", "AQI", "Odo"):
                t = re.sub(r"\b" + name.lower() + r"\b", name, t) if name in p["text"] else t
            t = t.replace("Podcast", "podcast").replace("Radio", "radio")
            act = p["act"]
            purpose = None
            if intent in M2_INTENTS:
                act, purpose = "Trả lời ngắn", "M2"
            if intent == "keu_cuu":
                act = "Kêu cứu"
            out.append(dict(case=it["case"], intent=intent, act=act, text=t, src=f"src_commands.json:{intent}#{i}",
                            evidence=p["evidence"], source_ids=[p["source"]] if p["source"] else [], purpose=purpose,
                            register=p["register"], w=None))
    return out


NEW_FIDS = set()   # khung thêm từ v2 (frames_llm10k.py)
APP_FIDS = set()   # khung thêm từ v3 (frames_app10k.py, nhóm G1–G8); nối sau cùng nên mã khung cũ không đổi


def load_frames():
    frames = _load_src_frames() + [dict(f, register=None) for f in MY]
    n_old = len(frames)
    try:
        from nguyen_lieu import frames_llm10k as FL
        frames += [dict(f, register=None) for f in FL.NEW]
        INTENT_LABELS.update(FL.LABELS)
    except ImportError:
        pass
    n_v2 = len(frames)
    try:
        from nguyen_lieu import frames_app10k as FA
        frames += [dict(f, register=None) for f in FA.NEW]
        INTENT_LABELS.update(FA.LABELS)
    except ImportError:
        pass
    for k, f in enumerate(frames):
        f["fid"] = f"F{k:04d}"
        f.setdefault("app_group", "")
        f.setdefault("platform", "any")
        if n_old <= k < n_v2:
            NEW_FIDS.add(f["fid"])
        elif k >= n_v2:
            APP_FIDS.add(f["fid"])
        f["intent_label"] = INTENT_LABELS.get(f["intent"], f["intent"].replace("_", " "))
        if f["purpose"] is None:
            f["purpose"] = "M2" if f["intent"] in M2_INTENTS else "M1"
    return frames
