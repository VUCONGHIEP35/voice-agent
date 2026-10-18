# -*- coding: utf-8 -*-
"""Khung thêm ở v3: app trên màn hình xe (CHANGES_v3.md C2; review/PHU_LUC_app_tren_man_hinh_va_tu_ngoai.md mục 2).

Mọi khung tự biên (K1), frame_source = "K1 app", evidence = "constructed"; mọi câu sinh từ đây gắn 'cần duyệt'.
Nhóm (app_group) và số câu mục tiêu (TARGET, đã tính hạn ngạch, CHANGES_v3 mục 6). Bộ sinh áp trần cứng theo
(nhóm, case): thiếu khung thì giữ ít câu hơn, không nới.
Phân case: G1–G4 -> CS04; G5 -> CS04 (xe đang đỗ) + CS11 (ghế sau); G6 -> CS01 (dẫn đường) + CS04 (đổi app bản đồ);
G7 -> CS05; G8 -> CS01 (gần intent dẫn đường / trạm thu phí nhất).
platform: G1, G3, G4, G5, G6 = android_head_unit (app mở trên màn hình); G7 = theo app nhắn tin (Messenger, Telegram:
phone_projection theo nguồn Android Auto; Zalo, Viber: any vì chưa kiểm); G2, G8 = any.
Không có từ đánh thức thương hiệu, không có gọi xe công nghệ (G9) hay ví điện tử (CHANGES_v3 mục 7).
Viết bằng từ toàn dân/Bắc; lexicon10k đổi từ vùng khi cần. Không thêm từ miền Trung.
"""
SRC = "K1 app"
NEW = []
LABELS = {
    "mo_app": "mở ứng dụng theo tên", "dieu_khien_video": "điều khiển video, nhạc trong app", "tim_noi_dung_app": "tìm nội dung trong app",
    "chuyen_man_hinh_app": "chuyển màn hình, chuyển app, chia đôi màn hình", "ngu_canh_xe_do": "nói rõ ngữ cảnh xe đỗ, ghế sau",
    "chon_app_ban_do": "chọn app bản đồ", "tin_nhan_app": "đọc, trả lời tin nhắn app bên thứ ba", "thu_phi_khong_dung": "thu phí không dừng",
}
# số câu mục tiêu theo (nhóm, case); tổng theo nhóm = CHANGES_v3 mục 6
TARGET = {
    ("G1", "CS04"): 150, ("G2", "CS04"): 100, ("G3", "CS04"): 100, ("G4", "CS04"): 70,
    ("G5", "CS04"): 25, ("G5", "CS11"): 15, ("G6", "CS01"): 55, ("G6", "CS04"): 25,
    ("G7", "CS05"): 150, ("G8", "CS01"): 80,
}
GROUP_TARGET = {}
for (g, _), v in TARGET.items():
    GROUP_TARGET[g] = GROUP_TARGET.get(g, 0) + v
HU, ANY, BY_MSG = "android_head_unit", "any", "msg_app"
PROJECTION_MSG = {"Messenger", "Telegram"}      # nguồn: support.google.com/androidauto, slashgear (phụ lục v3)


def F(case, intent, act, texts, group, platform):
    for t in texts:
        NEW.append(dict(case=case, intent=intent, act=act, text=t, src=SRC, evidence="constructed", source_ids=[],
                        purpose=None, w=None, app_group=group, platform=platform))


# ================================================================= G1 mở app theo tên (CS04)
F("CS04", "mo_app", "Lệnh", [
    "mở {app}", "(bật|mở) {app} lên", "vào {app} (đi|cho tôi)", "chạy {app}", "mở ứng dụng {app}", "khởi động {app}",
    "~cho tôi vào {app}", "mở giúp tôi ứng dụng {app}", "mở lại {app}", "(tắt|đóng) {app}", "thoát {app}",
], "G1", HU)
F("CS04", "mo_app", "Câu hỏi", ["{app} mở chưa", "trên màn hình có {app} không", "mở {app} được không"], "G1", HU)
F("CS04", "mo_app", "Câu cụt", ["~ứng dụng {app}"], "G1", HU)

# ================================================================= G2 điều khiển video/nhạc trong app (CS04)
F("CS04", "dieu_khien_video", "Lệnh", [
    "tua đi {sec}", "tua lại {sec}", "tua nhanh {sec}", "lùi lại {sec}", "bỏ qua quảng cáo", "tắt quảng cáo này đi",
    "phát lại từ đầu", "xem lại từ đầu video", "(bật|tắt) toàn màn hình", "thu nhỏ video lại", "phóng to video lên",
    "(bật|tắt) phụ đề", "đổi phụ đề sang tiếng Việt", "tạm dừng video", "phát tiếp video", "chuyển sang video tiếp theo",
    "quay lại video trước", "tăng tốc độ phát video", "giảm tốc độ phát video", "phát video ở tốc độ bình thường",
    "(bật|tắt) tự động phát", "lặp lại video này", "tắt tiếng video", "chỉ nghe tiếng, tắt hình", "(tăng|giảm) chất lượng video",
    "thích video này", "lưu video này để xem sau", "đăng ký kênh này", "tắt video đi", "bỏ qua đoạn mở đầu",
    "tua tới giữa video", "tua đến cuối bài",
    "tua tới phút thứ {n60}", "quay lại đoạn vừa nãy", "nghe lại câu vừa rồi", "dừng ở đây, lát xem tiếp", "đánh dấu chỗ này để xem tiếp",
    "phát video kế tiếp trong danh sách", "trộn ngẫu nhiên danh sách video", "phát hết danh sách này", "xóa video này khỏi danh sách",
    "thêm video này vào danh sách phát", "không đề xuất kênh này nữa", "ẩn video này đi", "đừng tự chuyển video nữa",
    "để video chạy nền, tắt màn hình", "tắt hình, giữ tiếng", "mở lại hình video", "tua chậm lại một chút", "đóng phụ đề lại",
    "chỉnh phụ đề to hơn", "đổi giọng lồng tiếng", "bật chế độ chỉ âm thanh", "tua qua đoạn giới thiệu", "bỏ qua bài này trên Spotify",
    "phát bài trước trên Spotify", "tạm dừng Spotify", "phát tiếp Spotify", "tắt chế độ lặp lại", "lặp lại cả danh sách",
    "đóng cửa sổ quảng cáo", "xem lại đoạn cuối video", "phát video gốc, đừng phát bản rút gọn",
], "G2", ANY)
F("CS04", "dieu_khien_video", "Câu hỏi", ["video này còn bao lâu nữa hết", "video này tên là gì", "đang phát video của kênh nào",
                                         "có phụ đề tiếng Việt không"], "G2", ANY)
F("CS04", "dieu_khien_video", "Câu cụt", ["~quảng cáo dài quá", "~video bị giật", "~hình mờ quá", "~tiếng nhỏ quá, không nghe rõ video"],
  "G2", ANY)

# ================================================================= G3 tìm nội dung trong app (CS04)
F("CS04", "tim_noi_dung_app", "Lệnh", [
    "mở YouTube tìm {chu_de}", "tìm trên YouTube về {chu_de}", "xem {kenh} trên YouTube", "mở {kenh} trên YouTube",
    "mở video mới nhất của {kenh}", "tìm video hướng dẫn nấu {dish}", "tìm {ten_phim} trên YouTube", "mở YouTube cho bé xem {ten_phim}",
    "tìm bài {bai_hat} trên {music_app}", "mở {music_app} tìm {ca_si}", "tìm podcast về {chu_de} trên Spotify",
    "mở danh sách xem sau trên YouTube", "xem tiếp video hôm qua trên YouTube", "tìm trên YouTube cách thay lốp xe",
    "mở YouTube xem tin {news}", "tìm video du lịch {city}", "phát video ca nhạc của {ca_si}", "tìm trên {music_app} danh sách {genre}",
    "mở lịch sử xem trên YouTube", "tìm video mới về {chu_de}",
], "G3", HU)
F("CS04", "tim_noi_dung_app", "Câu hỏi", ["trên YouTube có video nào về {chu_de} không", "{kenh} có video mới không",
                                         "{music_app} có bài {bai_hat} không", "video nào đang thịnh hành trên YouTube"], "G3", HU)

# ================================================================= G4 chuyển màn hình/app, chia đôi màn hình (CS04)
F("CS04", "chuyen_man_hinh_app", "Lệnh", [
    "quay lại bản đồ", "về màn hình chính", "chuyển sang {app}", "đổi qua {app}", "quay lại {app}",
    "chia đôi màn hình bản đồ và nhạc", "chia đôi màn hình", "tắt chia đôi màn hình", "mở {app} ở nửa màn hình",
    "để bản đồ bên trái, nhạc bên phải", "phóng to bản đồ ra cả màn hình", "đưa {app} ra màn hình chính", "quay lại màn hình trước",
    "đóng hết ứng dụng đang mở", "mở danh sách ứng dụng", "chuyển màn hình sang chế độ tối", "tắt màn hình trung tâm",
    "(tăng|giảm) độ sáng màn hình", "mở lại ứng dụng vừa dùng", "chuyển qua lại giữa bản đồ và nhạc",
], "G4", HU)
F("CS04", "chuyen_man_hinh_app", "Câu hỏi", ["đang mở những ứng dụng nào", "có chia đôi màn hình được không"], "G4", HU)

# ================================================================= G5 ngữ cảnh xe đỗ (CS04) / ghế sau (CS11)
F("CS04", "ngu_canh_xe_do", "Lệnh", [
    "~xe đang đỗ, mở video đi", "~đỗ xe rồi, mở YouTube xem chút", "~dừng xe rồi, bật phim cho tôi xem", "~đang chờ người, mở {kenh} xem",
    "~đang sạc xe, mở {music_app} nghe chút", "~xe đỗ rồi, cho xem video toàn màn hình", "~đang nghỉ trưa trong xe, mở phim lên",
    "~xe đứng yên rồi, mở video được chưa", "~đỗ chờ con tan học, mở {kenh} đi", "~đang đổ xăng, phát tiếp video lúc nãy",
], "G5", HU)
F("CS04", "ngu_canh_xe_do", "Câu hỏi", ["xe đang đỗ thì xem video được không", "sao đỗ xe rồi mà không mở được video"], "G5", HU)
F("CS11", "ngu_canh_xe_do", "Lệnh", [
    "~tôi ngồi ghế sau, bật phim", "mở phim cho ghế sau xem", "bật {ten_phim} trên màn hình sau", "cho màn hình sau mở YouTube",
    "~ghế sau muốn xem {kenh}", "mở video cho người ngồi sau xem", "~tôi ngồi sau, mở {music_app} giúp tôi",
    "tắt video ở màn hình sau", "cho màn hình sau xem video riêng",
], "G5", HU)

# ================================================================= G6 chọn app bản đồ: dẫn đường (CS01) / đổi app (CS04)
F("CS01", "chon_app_ban_do", "Lệnh", [
    "dẫn đường bằng {map_app}", "mở {map_app} dẫn tới {poi}", "dùng {map_app} chỉ đường (đến|tới) {poi}", "dùng {map_app} chỉ đường về {home}",
    "tìm {cat} trên {map_app}", "chỉ đường tới {poi} bằng {map_app}", "dẫn đường về {home} bằng {map_app}",
    "mở {map_app} tìm đường đi {city}", "tìm {cat} gần nhất trên {map_app}", "dùng {map_app} tránh tắc đường",
    "đi {city} theo {map_app}", "dùng {map_app} cho chuyến này",
], "G6", HU)
F("CS01", "chon_app_ban_do", "Câu hỏi", ["{map_app} có báo tắc đường không", "{map_app} bảo còn bao xa", "theo {map_app} thì mấy giờ tới {poi}",
                                        "{map_app} có báo camera phạt nguội không"], "G6", HU)
F("CS04", "chon_app_ban_do", "Lệnh", ["đổi sang {map_app}", "chuyển bản đồ sang {map_app}", "dùng {map_app} thay cho {map_app#2}",
                                     "(bật|mở) {map_app} lên", "đặt {map_app} làm bản đồ mặc định", "tắt {map_app} đi"], "G6", HU)
F("CS04", "chon_app_ban_do", "Câu hỏi", ["đang dùng bản đồ nào", "{map_app} mở chưa"], "G6", HU)

# ================================================================= G7 tin nhắn app bên thứ ba (CS05)
F("CS05", "tin_nhan_app", "Câu hỏi", [
    "có tin {msg_app} mới không", "{msg_app} có ai nhắn không", "có bao nhiêu tin {msg_app} chưa đọc", "{ct} có nhắn {msg_app} không",
    "nhóm {msg_app} gia đình có gì mới không", "ai vừa nhắn {msg_app} cho tôi", "tin {msg_app} vừa rồi của ai",
], "G7", BY_MSG)
F("CS05", "tin_nhan_app", "Lệnh", [
    "đọc tin {msg_app} của {ct}", "trả lời {msg_app} là {msg}", "đọc tin {msg_app} mới nhất", "trả lời {ct} trên {msg_app}: {msg}",
    "đọc lại tin {msg_app} vừa rồi", "(tắt|bật) thông báo {msg_app} khi đang lái", "đánh dấu tin {msg_app} là đã đọc",
    "gửi tin {msg_app} cho {ct} là {msg}", "đọc tin nhóm {msg_app}", "đọc hết tin {msg_app} chưa đọc", "trả lời tin {msg_app} vừa rồi: {msg}",
    "nhắn lại cho {ct} qua {msg_app}: {msg}", "bỏ qua tin {msg_app} này", "đọc tin {msg_app} từ sáng đến giờ", "mở tin {msg_app} của {ct}",
], "G7", BY_MSG)

# ================================================================= G8 thu phí không dừng (CS01)
F("CS01", "thu_phi_khong_dung", "Câu hỏi", [
    "số dư {etc_app} còn bao nhiêu", "{etc_app} còn đủ tiền qua trạm không", "còn bao xa tới trạm thu phí", "trạm thu phí tiếp theo ở đâu",
    "phí qua trạm tiếp theo bao nhiêu tiền", "đi đường này qua mấy trạm thu phí", "trạm thu phí phía trước có làn {etc_app} không",
    "đi {city} hết bao nhiêu tiền phí", "hôm nay {etc_app} bị trừ bao nhiêu", "tài khoản {etc_app} có bị lỗi không",
    "qua trạm vừa rồi bị trừ bao nhiêu",
], "G8", ANY)
F("CS01", "thu_phi_khong_dung", "Lệnh", [
    "nạp {money} vào {etc_app}", "kiểm tra tài khoản {etc_app}", "nhắc tôi nạp tiền {etc_app}", "xem lịch sử trừ tiền {etc_app}",
    "báo tôi khi {etc_app} sắp hết tiền", "tìm đường không qua trạm thu phí", "chọn làn thu phí không dừng",
    "đọc số dư {etc_app} cho tôi",
], "G8", ANY)
