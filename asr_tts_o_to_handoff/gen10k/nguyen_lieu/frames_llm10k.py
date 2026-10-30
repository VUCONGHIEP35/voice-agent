# -*- coding: utf-8 -*-
"""Khung thêm ở v2 (góp ý vòng 1, mục 2; phụ lục mục 6.3).

- LLM: khung do Claude diễn đạt lại từ khung hiện có (đổi cấu trúc, trật tự, động từ, câu hỏi gián tiếp, câu cụt).
  frame_source = "LLM diễn đạt lại (cần duyệt)", evidence = "constructed"; mọi câu sinh từ đây gắn 'cần duyệt'.
- XE: khung cho chức năng xe chưa có (phụ lục mục 4) dùng từ có trong sources/src_lang.json car_terms
  (xi nhan, ca-pô, táp lô, bánh sơ-cua, số D/R/P, nổ máy, tắt máy, đầy bình, hết xăng, ắc quy/bình điện, pha, cốt,
  đèn khẩn cấp, thay dầu/thay nhớt, gương/kiếng chiếu hậu, phanh/thắng tay). Các cặp chỉ có K1 (còi/kèn, lùi/de,
  quay đầu/quay xe, bơm xăng, lề đường) không thêm.
Viết bằng từ toàn dân/Bắc; bộ viết lại từ vùng (lexicon10k) đổi sang Nam khi cần. Không thêm từ miền Trung.
"""
LLM = "LLM diễn đạt lại (cần duyệt)"
XE = "phiên v2: chức năng xe theo src_lang car_terms (cần duyệt)"
NEW = []
LABELS = {"khoi_dong_xe": "nổ máy, tắt máy, số xe"}


def F(case, intent, act, texts, src=LLM):
    for t in texts:
        NEW.append(dict(case=case, intent=intent, act=act, text=t, src=src, evidence="constructed", source_ids=[],
                        purpose=None, w=None))


# ================================================================= CS03 Điều khiển xe
F("CS03", "dieu_hoa_bat_tat_nhiet_do", "Lệnh", [
    "cho nhiệt độ trong xe về {temp_u}", "hạ nhiệt độ xuống còn {temp_u}", "nâng nhiệt độ lên {temp_u}", "để nhiệt độ ở mức {temp_u}",
    "~điều hòa {temp_u}", "mát hơn chút, khoảng {temp_u} thôi", "chỉnh lại điều hòa cho mát hơn", "điều hòa bên phụ để {temp_u} thôi",
    "cho bên lái ấm hơn {n3} độ", "~xe nóng quá, hạ xuống {temp_u} giúp tôi", "giảm điều hòa thêm {n3} độ nữa",
    "để điều hòa tự giữ ở {temp_u}", "làm mát nhanh xuống {temp_u}", "cho khoang sau mát hơn {n3} độ", "tăng nhiệt độ bên phụ lên {temp_u}",
    "~{temp_u} cho bên lái, bên phụ {temp_u#2}", "nhiệt độ cả xe {temp_u} nhé", "đổi nhiệt độ thành {temp_u}",
])
F("CS03", "dieu_hoa_bat_tat_nhiet_do", "Câu hỏi", ["điều hòa đang để bao nhiêu độ", "trong xe bây giờ bao nhiêu độ",
                                                   "nhiệt độ bên phụ đang là bao nhiêu", "để {temp_u} có lạnh quá không"])
F("CS03", "dieu_hoa_noi_nong_lanh", "Câu cụt", ["~trong xe ngột ngạt quá", "~hơi lạnh chân", "~lạnh tay quá", "~ghế sau kêu nóng",
                                                "~gió thổi vào mặt lạnh quá", "~xe bí quá", "~tôi thấy hơi oi", "~nắng chiếu nóng quá",
                                                "~ngồi sau nóng lắm", "~khô họng quá"])
F("CS03", "dieu_hoa_quat_gio", "Lệnh", ["cho quạt mạnh lên một chút", "quạt yếu đi một chút", "để gió nhẹ thôi", "gió mạnh quá, giảm xuống mức {fan}",
                                       "chuyển quạt về mức {fan}", "cho quạt chạy mức {fan}", "tắt bớt quạt gió", "~quạt to quá",
                                       "để quạt gió tự chỉnh", "quạt gió lên mức cao nhất", "giảm quạt gió về mức thấp nhất", "quạt khoang sau mức {fan}"])
F("CS03", "dieu_hoa_quat_gio", "Câu hỏi", ["quạt gió đang ở mức mấy", "quạt sau đang chạy mức bao nhiêu"])
F("CS03", "dieu_hoa_huong_gio", "Lệnh", ["gió thổi {vent} thôi", "cho gió ra {vent}", "chuyển cửa gió {vent}", "đừng thổi vào mặt nữa",
                                        "chỉnh cửa gió bên lái {vent}", "đổi gió phía sau {vent}", "cho gió thổi đều cả xe"])
F("CS03", "dieu_hoa_huong_gio", "Câu hỏi", ["gió đang thổi vào đâu", "cửa gió bên phụ đang hướng nào"])
F("CS03", "dieu_hoa_lay_gio", "Lệnh", ["đóng cửa lấy gió ngoài lại", "chuyển sang lấy gió trong cho đỡ bụi", "mở lấy gió ngoài cho thoáng",
                                      "cho điều hòa chạy tuần hoàn trong xe", "đi qua đoạn khói bụi, đóng gió ngoài", "lấy gió ngoài {mins} rồi chuyển lại"])
F("CS03", "dieu_hoa_lay_gio", "Câu hỏi", ["đang lấy gió trong hay gió ngoài", "có nên lấy gió ngoài lúc này không"])
F("CS03", "say_kinh", "Lệnh", ["làm tan sương kính trước", "~kính trước bị mờ, sấy giúp tôi", "khử sương kính sau", "sấy kính sau trong {mins}",
                              "tắt sấy kính sau đi", "~kính bị đọng hơi nước", "sấy cả kính trước và kính sau", "bật sấy kính trước mức cao nhất"])
F("CS03", "dieu_hoa_che_do", "Lệnh", ["chuyển điều hòa sang chế độ tiết kiệm", "để điều hòa chạy tự động", "tắt chế độ tự động của điều hòa",
                                     "bật chế độ lọc bụi", "cho điều hòa chạy êm thôi", "bật điều hòa hai vùng riêng", "gộp nhiệt độ hai bên làm một",
                                     "bật chế độ làm lạnh nhanh"])
F("CS03", "dieu_hoa_che_do", "Câu hỏi", ["điều hòa đang chạy chế độ gì", "lọc không khí đang bật hay tắt"])
F("CS03", "ghe_suoi_lam_mat_massage", "Lệnh", [
    "sưởi ấm {seat} mức {lvl3}", "~{seat} sưởi mức {lvl3}", "làm mát {seat} giúp tôi", "cho {seat} mát hơn", "tăng massage {seat} lên mức {lvl3}",
    "chuyển massage {seat} sang chế độ nhẹ", "tắt hết sưởi ghế", "bật thông gió cho {seat}", "~ghế nóng quá, tắt sưởi đi", "giảm sưởi {seat} xuống mức {lvl3}",
    "massage lưng cho {seat} trong {mins}", "tắt làm mát {seat}", "cho {seat} ấm lên một chút",
])
F("CS03", "ghe_suoi_lam_mat_massage", "Câu hỏi", ["{seat} đang sưởi mức mấy", "sưởi ghế đã bật chưa"])
F("CS03", "ghe_nho_vi_tri", "Lệnh", ["kéo ghế lái lên trước một chút", "lùi ghế phụ ra sau", "ngả lưng ghế phụ thêm chút", "dựng lưng ghế lái thẳng lên",
                                    "nâng đệm ghế lái cao hơn", "chỉnh ghế về vị trí số {mem}", "lưu vị trí ghế hiện tại vào số {mem}",
                                    "chỉnh tựa đầu ghế lái lên", "chỉnh vô lăng (lên|xuống) một chút", "đưa vô lăng (ra|vào) một chút",
                                    "đẩy ghế phụ lên để người sau ngồi rộng", "gập hàng ghế sau xuống"])
F("CS03", "cua_kinh", "Lệnh", ["mở hé kính {wpos}", "cho kính {wpos} xuống {pct}", "nâng hết các kính lên", "hạ kính {wpos} khoảng một nửa",
                              "đóng kính {wpos} lại", "mở kính cho thoáng một chút", "kéo kính {wpos} lên giúp tôi", "hạ hết kính xuống",
                              "~kính {wpos} còn hở", "để kính {wpos} hé {pct}", "mở kính hai bên phía trước", "đóng hết kính, sắp vào hầm"])
F("CS03", "cua_kinh", "Câu hỏi", ["kính {wpos} đang mở à", "còn kính nào chưa đóng không"])
F("CS03", "cua_so_troi", "Lệnh", ["hé cửa sổ trời {pct}", "đóng hẳn cửa sổ trời", "kéo rèm cửa sổ trời lại", "mở rèm che nắng ra",
                                 "nghiêng cửa sổ trời lên", "mở cửa sổ trời cho thoáng"])
F("CS03", "cua_so_troi", "Câu hỏi", ["cửa sổ trời đang mở hay đóng"])
F("CS03", "den_noi_that", "Lệnh", ["tắt đèn trần đi", "cho đèn trong xe tối bớt", "đèn trong xe sáng {pct}", "đổi đèn viền sang màu {color}",
                                  "bật đèn đọc sách bên phụ", "giảm sáng màn hình về {pct}", "~màn hình chói quá", "để đèn nội thất màu {color}",
                                  "chuyển màn hình sang chế độ tối", "tắt hết đèn trong xe"])
F("CS03", "khoa_mo_cua", "Lệnh", ["khóa hết cửa lại", "mở khóa tất cả các cửa", "bật tự khóa cửa khi xe chạy", "mở khóa cửa cho người ngồi sau",
                                 "khóa cửa {wpos}"])
F("CS03", "khoa_mo_cua", "Câu hỏi", ["cửa đã khóa hết chưa", "cửa nào đang chưa khóa"])
F("CS03", "guong", "Lệnh", ["gập hai gương lại", "mở hai gương ra", "chỉnh gương chiếu hậu bên phụ xuống thấp", "gương bên lái chỉnh ra ngoài một chút",
                           "bật sấy gương chiếu hậu", "hạ gương bên phụ khi lùi xe", "tự gập gương chiếu hậu khi khóa xe"], XE)
F("CS03", "cop_xe", "Lệnh", ["mở cốp sau ra", "đóng cốp lại giúp tôi", "mở cốp điện", "dừng đóng cốp", "mở ca-pô", "mở nắp ca-pô giúp tôi"], XE)
F("CS03", "cop_xe", "Câu hỏi", ["cốp đã đóng chưa", "ca-pô đóng chặt chưa"], XE)
F("CS03", "gat_mua", "Lệnh", ["cho gạt mưa chạy nhanh hơn", "gạt mưa chậm thôi", "để gạt mưa tự động", "gạt một lần thôi", "phun nước rửa kính trước",
                             "bật gạt mưa kính sau", "tắt gạt mưa sau", "gạt mưa nhanh nhất", "~mưa to quá, gạt nhanh lên"])
F("CS03", "che_do_lai", "Lệnh", ["chuyển sang chạy chế độ thể thao", "để xe chạy chế độ tiết kiệm", "về lại chế độ tiêu chuẩn",
                                "bật chế độ lái tiết kiệm pin", "chạy chế độ êm cho người ngồi sau"])
F("CS03", "che_do_lai", "Câu hỏi", ["xe đang ở chế độ lái nào", "chế độ thể thao có tốn pin hơn không"])
F("CS03", "vo_lang_den_ngoai", "Lệnh", ["bật pha", "bật cốt", "chuyển đèn sang pha", "chuyển sang đèn cốt", "tắt đèn khẩn cấp", "bật đèn khẩn cấp lên",
                                       "bật sưởi vô lăng mức {lvl3}", "bật đèn sương mù phía sau", "để đèn pha tự chuyển sang cốt"], XE)
F("CS03", "vo_lang_den_ngoai", "Câu hỏi", ["đèn pha đang bật hay tắt", "đèn khẩn cấp đã tắt chưa"], XE)
F("CS03", "wifi_camera", "Lệnh", ["mở camera 360 độ", "cho xem camera sau", "tắt camera lùi", "bật điểm phát wifi", "tắt wifi trên xe",
                                 "cho xem camera bên phụ", "mở camera hành trình xem lại", "chụp ảnh từ camera trước"])
F("CS03", "khoi_dong_xe", "Lệnh", ["nổ máy xe từ xa", "tắt máy xe", "nổ máy và bật điều hòa trước {mins}", "bật giữ phanh tự động",
                                  "tắt giữ phanh tự động", "nhả phanh tay", "nhắc tôi kéo phanh tay khi đỗ xe", "nhắc tôi về số {gear} khi đỗ xe"], XE)
F("CS03", "khoi_dong_xe", "Câu hỏi", ["xe đã tắt máy chưa", "phanh tay đã kéo chưa", "~xe đang ở số {gear} phải không", "cần số đang ở số mấy"], XE)

# ================================================================= CS02 Cảnh báo an toàn
F("CS02", "bat_tat_he_thong_ho_tro", "Lệnh", ["tắt giúp tôi {warn}", "tạm thời đừng dùng {sysn}", "bỏ {warn} đi", "mở lại {sysn}",
                                              "kích hoạt {sysn}", "tạm ngắt {warn} một lúc", "tắt hết các cảnh báo âm thanh", "bật lại hết hỗ trợ lái",
                                              "chỉ giữ {warn}, tắt các cảnh báo khác"])
F("CS02", "bat_tat_he_thong_ho_tro", "Câu hỏi", ["{sysn} có đang hoạt động không", "{warn} đang bật à", "xe có {sysn} không"])
F("CS02", "do_nhay_canh_bao_chung", "Lệnh", ["cho {warn} báo muộn hơn", "chuyển {warn} sang chỉ rung", "để {warn} ở mức {lev}", "~{warn} nhạy quá",
                                             "giảm tiếng bíp cảnh báo", "cho {warn} báo sớm hơn", "để cảnh báo chỉ hiện trên màn hình"])
F("CS02", "do_nhay_canh_bao_chung", "Câu hỏi", ["{warn} báo sớm hơn được không", "độ nhạy {warn} đang để mức nào"])
F("CS02", "ga_tu_dong", "Lệnh", ["giữ xe chạy đều {spd}", "tăng tốc độ đặt lên {spd}", "đặt lại tốc độ ga tự động {spd}",
                                "giữ khoảng cách xa hơn với xe trước", "giữ khoảng cách gần hơn với xe trước", "báo tôi khi chạy quá {spd}",
                                "~đến {hw} thì bật ga tự động {spd}"])
F("CS02", "ga_tu_dong", "Câu hỏi", ["ga tự động đang để bao nhiêu", "~đạp phanh thì ga tự động có tự tắt không", "khoảng cách với xe trước đang để mức nào"])
F("CS02", "canh_bao_met_moi", "Lệnh", ["~tôi không buồn ngủ, đừng báo nữa", "~tôi mới nghỉ xong", "~cho tôi lái thêm {mins} nữa",
                                      "tìm chỗ dừng nghỉ trên {hw}", "~mắt hơi díp, tìm trạm dừng chân", "nhắc tôi uống nước sau {mins}",
                                      "bật nhạc to lên cho tỉnh", "mở {genre} cho đỡ buồn ngủ"])
F("CS02", "canh_bao_lech_lan", "Lệnh", ["~xe cứ rung vô lăng, tắt giữ làn đi", "để giữ làn chỉ cảnh báo, không tự đánh lái"])
F("CS02", "canh_bao_va_cham", "Lệnh", ["cho cảnh báo va chạm báo sớm hơn", "tắt tiếng cảnh báo va chạm, giữ đèn báo"])

# ================================================================= CS04 Giải trí
F("CS04", "phat_bai_ca_si", "Lệnh", ["bật giúp tôi bài {bai_hat}", "có bài {bai_hat} không, mở đi", "cho nghe vài bài của {ca_si}",
                                    "phát ngẫu nhiên nhạc {ca_si}", "~{bai_hat}, mở bài đó", "mở bài gì của {ca_si} cũng được",
                                    "tìm bài {bai_hat} rồi phát", "nghe bài {bai_hat} một lần nữa", "phát bài {bai_hat} tiếp theo",
                                    "xếp bài {bai_hat} vào sau bài này"])
F("CS04", "phat_bai_ca_si", "Câu hỏi", ["có bài nào mới của {ca_si} không", "bài {bai_hat} là của {ca_si} phải không"])
F("CS04", "phat_the_loai_playlist", "Lệnh", ["mở {genre} nhẹ nhẹ thôi", "đổi qua {genre}", "cho nghe {genre} đi đường", "phát lại {plist} từ bài đầu",
                                            "tiếp tục danh sách {plist}", "~nhạc này hay, lưu vào {plist}", "trộn bài trong {plist}",
                                            "tạo danh sách mới tên {plist}"])
F("CS04", "radio", "Lệnh", ["chuyển đài khác", "lùi về đài trước", "dò tìm đài có tín hiệu tốt", "nghe tin giao thông trên {radio}"])
F("CS04", "radio", "Câu hỏi", ["{radio} đang phát gì", "đài {freq} có tin giao thông không", "đang nghe đài nào"])
F("CS04", "am_luong", "Lệnh", ["nhỏ nhạc lại một chút", "để âm lượng nhỏ thôi", "vặn to thêm một chút", "giảm âm lượng còn {vol}",
                              "âm lượng lên {vol} giúp tôi", "~nhạc nhỏ quá", "cân bằng âm thanh về phía lái", "tăng âm trầm lên một chút"])
F("CS04", "chuyen_bai_tam_dung", "Lệnh", ["bỏ bài này, qua bài khác", "phát lại từ đầu bài", "tạm dừng nhạc một chút", "mở tiếp nhạc",
                                         "~bài trước hay hơn, quay lại", "lặp lại cả danh sách", "nghe tiếp bài đang dở"])
F("CS04", "podcast", "Lệnh", ["nghe tiếp {pod} hôm qua", "đọc tiếp chương sau", "tìm podcast nói về {chu_de}", "tăng tốc độ phát lên một chút",
                             "phát chậm lại", "lưu tập này để nghe sau"])
F("CS04", "hoi_bai_dang_phat", "Câu hỏi", ["ca sĩ hát bài này là ai", "bài này ra năm nào", "bài vừa phát tên là gì", "đây là bài của {ca_si} à"])
F("CS04", "nguon_nhac_bluetooth_usb", "Lệnh", ["nghe nhạc trong điện thoại qua {src}", "kết nối lại {src}", "đổi sang nghe {src}"])

# ================================================================= CS05 Điện thoại
F("CS05", "goi_theo_ten", "Lệnh", ["gọi ngay cho {ct}", "kết nối cuộc gọi tới {ct}", "cho tôi nói chuyện với {ct}", "~{ct}, gọi đi",
                                  "tìm số {ct} rồi gọi", "gọi cho {ct} ở nhà"])
F("CS05", "goi_theo_so", "Lệnh", ["bấm gọi {ph} giúp tôi", "gọi vào số {ph}", "~số {ph}, gọi giúp tôi"])
F("CS05", "soan_gui_tin_nhan", "Lệnh", ["nhắn {ct} rằng {msg}", "soạn tin gửi {ct}: {msg}", "trả lời {ct} là {msg}", "báo {ct} là tôi sắp đến",
                                       "nhắn cho {ct} là tôi đang ở {poi}"])
F("CS05", "doc_tin_nhan", "Lệnh", ["đọc tin nhắn mới của {ct}", "đọc to tin nhắn vừa nhận"])
F("CS05", "doc_tin_nhan", "Câu hỏi", ["có ai nhắn tin không", "{ct} vừa nhắn gì", "có tin nhắn nào của {ct} chưa đọc không"])
F("CS05", "chia_se_vi_tri", "Lệnh", ["gửi vị trí của tôi cho {ct}", "cho {ct} biết tôi đang ở đâu", "gửi lộ trình đang đi cho {ct}"])

# ================================================================= CS06 Trạng thái xe
F("CS06", "ap_suat_lop", "Lệnh", ["kiểm tra hơi {tire}", "hiện áp suất lốp cho tôi xem", "kiểm tra hơi (lốp dự phòng|bánh sơ-cua)"], XE)
F("CS06", "ap_suat_lop", "Câu hỏi", ["áp suất các lốp có đều không", "lốp nào cần bơm thêm", "(lốp dự phòng|bánh sơ-cua) còn đủ hơi không",
                                     "{tire} còn bao nhiêu hơi"], XE)
F("CS06", "nhien_lieu_quang_duong", "Câu hỏi", ["đổ đầy bình hết bao nhiêu lít", "sắp hết xăng chưa", "còn bao nhiêu cây số thì hết xăng",
                                                "đèn báo hết xăng sáng thì còn đi được bao xa", "đổ đầy bình đi được bao xa",
                                                "với chỗ xăng này có tới {city} không"], XE)
F("CS06", "bao_duong", "Câu hỏi", ["xe sắp đến kỳ bảo dưỡng chưa", "còn bao lâu nữa thì phải bảo dưỡng", "bao giờ phải thay dầu",
                                   "lần thay dầu trước là khi nào", "ắc quy có yếu không"], XE)
F("CS06", "bao_duong", "Lệnh", ["đặt lịch thay dầu {when}", "nhắc tôi đi bảo dưỡng {day}", "kiểm tra ắc quy", "nhắc tôi thay dầu sau {km} nữa"], XE)
F("CS06", "den_canh_bao", "Câu hỏi", ["đèn {wlamp} vừa bật lên, có sao không", "đèn trên táp lô đang báo gì", "đèn xi nhan bên (trái|phải) có bị hỏng không",
                                      "xe báo yếu ắc quy là sao"], XE)
F("CS06", "den_canh_bao", "Câu cụt", ["~trên táp lô có đèn {wlamp} sáng", "~xe báo lỗi đèn xi nhan"], XE)
F("CS06", "so_km_da_di", "Câu hỏi", ["từ sáng đến giờ đi được bao nhiêu cây số", "chuyến này đi hết bao lâu rồi", "tháng này xe chạy bao nhiêu cây số"])

# ================================================================= CS07 Sạc và nhiên liệu
F("CS07", "phan_tram_pin", "Câu hỏi", ["pin xe hiện tại thế nào", "còn bao nhiêu phần trăm pin", "pin sạc tới đâu rồi"])
F("CS07", "quang_duong_con_lai_ev", "Câu hỏi", ["với mức pin này có về đến {home} không", "đi {city} thì phải sạc mấy lần",
                                                "tắt điều hòa thì đi thêm được bao xa"])
F("CS07", "tim_tram_sac", "Lệnh", ["tìm chỗ sạc gần {poi}", "dẫn đường tới trạm sạc còn trụ trống"])
F("CS07", "tim_tram_sac", "Câu hỏi", ["có trạm sạc nào trên đường đi {city} không", "trạm sạc gần nhất còn trụ trống không", "trạm sạc ở {poi} có sạc nhanh không"])
F("CS07", "gioi_han_sac", "Lệnh", ["dừng sạc khi đầy {pct_bat}", "chỉ sạc tới {pct_bat}", "sạc đầy thì báo tôi"])
F("CS07", "hen_gio_sac", "Lệnh", ["hẹn sạc bắt đầu lúc {clk}", "sạc vào ban đêm cho rẻ", "đổi giờ sạc sang {clk}"])
F("CS07", "cong_sac", "Lệnh", ["mở nắp sạc giúp tôi", "mở khóa súng sạc"])
F("CS07", "thoi_gian_chi_phi_sac", "Câu hỏi", ["sạc nhanh mất bao lâu thì đầy", "sạc tới {pct_bat} hết bao nhiêu tiền"])
F("CS07", "tim_tram_xang", "Lệnh", ["tìm cây xăng còn mở cửa", "~xe sắp hết xăng, tìm cây xăng", "tìm cây xăng có đổ đầy bình nhanh"], XE)

# ================================================================= CS11 Hành khách và trẻ em
F("CS11", "tre_xem_nhac_phim_truyen", "Lệnh", ["con muốn nghe bài {bai_hat}", "mở nhạc thiếu nhi cho em bé", "bật phim hoạt hình cho bé ở màn hình sau",
                                              "cho con xem tiếp {ten_phim}"])
F("CS11", "dieu_hoa_khoang_sau", "Lệnh", ["chỉnh điều hòa ghế sau xuống {temp_u}", "hàng ghế sau để {temp_u}", "cho ghế sau mát hơn một chút"])
F("CS11", "tat_loa_sau", "Lệnh", ["chỉ mở loa phía trước", "~bé đang ngủ, tắt nhạc ở ghế sau"])
F("CS11", "khoa_tre_em", "Lệnh", ["khóa kính sau lại không cho bé mở", "khóa cửa sau trong lúc xe chạy"])
F("CS11", "nhac_day_an_toan_ghe_sau", "Lệnh", ["kiểm tra dây an toàn của bé", "nhắc ghế sau thắt dây"])
F("CS11", "nhac_day_an_toan_ghe_sau", "Câu hỏi", ["ghế sau ai chưa thắt dây"])
