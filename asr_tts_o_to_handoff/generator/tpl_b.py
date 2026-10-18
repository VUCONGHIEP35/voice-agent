# -*- coding: utf-8 -*-
from tplbase import *

# ================================================================= CS04 Giải trí
GN = pool_choice("GENRES", ("tên riêng/địa danh",)) if False else None
P.POOLS["GENRES_L"] = P.GENRES
G4 = dict(
    genre=choice(P.GENRES), mood=choice([m for m in P.MOODS if m not in ("dễ ngủ", "buồn")]), plist=choice(P.PLAYLISTS, ("tên riêng/địa danh",)),
    pod=choice(P.PODCAST), vol=intg(1, 30), pct=percent([10, 20, 25, 30, 40, 50, 60, 70, 80]), sec=intg_w([10, 15, 20, 30, 45, 60], ("số",)),
    radio=radio(0.35), freq=freq_only(), src=link_src(), gpair=genre_pair(),
)
T("CS04", "T-MUS-GENRE", "mở nhạc theo thể loại", "Lệnh", [
    "(mở|bật|phát) (một số |vài bài |){genre}", "(mở|bật) {genre} đi", "cho {L:I} nghe {genre}", "~{L:I} muốn nghe {genre}", "nghe {genre} (nhé|đi|)".replace("(nhé|đi|)", ""),
    "chuyển sang {genre}", "phát (liên tục |){genre}", "(mở|bật) {genre} cho (đỡ buồn ngủ|vui|thư giãn)",
], G4, w=1.8, factors="E05")
T("CS04", "T-MUS-MOOD", "mở nhạc theo tâm trạng", "Lệnh", [
    "mở nhạc {mood}", "bật nhạc {mood}", "phát nhạc {mood}", "cho {L:I} nghe nhạc {mood}", "~{L:I} muốn nghe nhạc {mood}", "(mở|bật) vài bài nhạc {mood}",
    "đổi sang nhạc {mood}", "chọn nhạc {mood} giúp {L:I}",
], G4, w=1.1)
T("CS04", "T-MUS-LIST", "mở danh sách phát", "Lệnh", [
    "(mở|phát|bật) danh sách phát {plist}", "phát {plist}", "bật danh sách {plist}", "mở danh sách nhạc {plist}", "cho {L:I} nghe danh sách {plist}", "~{L:I} muốn nghe {plist}",
    "phát danh sách {plist} (ngẫu nhiên|từ đầu)", "thêm bài này vào danh sách {plist}",
], G4, w=1.4, factors="E05")
T("CS04", "T-MUS-CTRL", "điều khiển phát nhạc", "Lệnh", [
    "(bật |)(bài|bản) (tiếp theo|kế tiếp)", "(bật |)(bài|bản) trước", "chuyển bài", "bỏ qua bài này", "(tạm dừng|dừng|tiếp tục) (phát |)nhạc", "(phát lại|lặp lại) bài này",
    "(bật|tắt) (chế độ )?(phát ngẫu nhiên|lặp lại)".replace("(chế độ )?", ""), "tua tới {sec} giây", "tua lại {sec} giây", "tua về đầu bài", "tạm dừng một lát",
], G4, w=2.0, factors="E08")
T("CS04", "T-MUS-VOL", "chỉnh âm lượng", "Lệnh", [
    "tăng âm lượng lên {vol}", "giảm âm lượng xuống {vol}", "đặt âm lượng ở mức {vol}", "âm lượng {vol}", "tăng âm lượng một chút", "giảm âm lượng một chút", "tăng âm lượng thêm vài nấc",
    "tắt tiếng", "bật lại tiếng", "âm lượng (tối đa|nhỏ nhất)", "nhỏ tiếng (lại|bớt)", "to tiếng lên (chút|)", "đặt âm lượng {pct}", "~{L:I} nghe không rõ, tăng âm lượng lên",
    "~to quá, giảm âm lượng xuống",
], G4, w=2.2, factors="E03; E08", state=[("Bình thường", 0.6), ("Nói trong ồn (Lombard)", 0.3), ("Vội / nói nhanh", 0.1)])
T("CS04", "T-MUS-RADIO", "mở đài radio", "Lệnh", [
    "(mở|bật|nghe) (đài|kênh) {radio}", "chuyển sang (đài|kênh) {radio}", "~{L:I} muốn nghe (đài|kênh) {radio}", "cho {L:I} nghe {radio}", "chuyển sang {freq}",
    "dò đài {freq}", "(mở|bật) đài {freq}", "chuyển kênh {radio}", "bật radio {freq}", "đài nào đang (phát|có) tin giao thông",
], G4, w=1.6, factors="E07; E03")
T("CS04", "T-MUS-SRC", "nguồn phát", "Lệnh", [
    "chuyển sang nguồn {src}", "(bật|tắt) {src}", "kết nối {src} (với|vào) điện thoại", "phát nhạc từ {src}", "đổi nguồn phát sang (radio|{src})", "ngắt kết nối {src}",
], G4, w=0.8, factors="E05; S55")
T("CS04", "T-MUS-INFO", "hỏi thông tin bài hát", "Câu hỏi", [
    "(bài|bản nhạc) {L:this} (là bài gì|của ai|ai hát|tên gì)", "đang phát (bài|bản) gì", "(bài|bản) {L:this} tên gì", "đọc tên bài hát đang phát", "ca sĩ nào đang hát",
    "bài này (thuộc|của) (album|đĩa) nào", "bài này phát hành (năm nào|lúc nào)",
], G4, w=0.9)
T("CS04", "T-MUS-LIKE", "thích hoặc lưu bài", "Lệnh", [
    "(thích|bỏ thích) bài này", "thêm bài này vào (danh sách yêu thích|bài hát yêu thích)", "lưu bài này lại", "xóa bài này khỏi danh sách (yêu thích|phát)",
], G4, w=0.5)
T("CS04", "T-MUS-POD", "sách nói và podcast", "Lệnh", [
    "(nghe|mở|phát) {pod}", "mở {pod} đi", "tiếp tục (nghe|phát) {pod} (đang nghe dở|từ chỗ dừng)", "phát tiếp chương (tiếp theo|trước)", "tăng tốc độ đọc lên (một chút|nhanh hơn)",
    "~{L:I} muốn nghe {pod}", "đọc {pod} cho {L:I} nghe",
], G4, w=0.9)
T("CS04", "T-MUS-ALT", "đổi ý giữa hai thể loại", "Câu cụt", [
    "không phải {gpair}", "đổi sang {genre}, đừng nghe {genre} nữa".replace("đổi sang {genre}, đừng nghe {genre} nữa", "đổi sang {genre} đi"),
], G4, w=0.2)

# ================================================================= CS05 Điện thoại
G5 = dict(
    ct=contact(), ct2=contact(("anh_chi", "elder", "full")), ph=phone(), mins=minutes([5, 10, 15, 20, 30, 45, 60]), clk=clock(), day=day_phrase(),
    canned=choice([
        "tôi đang lái xe, lát nữa gọi lại", "mình sắp đến rồi", "tối nay mình về trễ", "đã nhận được, cảm ơn", "hẹn gặp lại sau nhé", "chờ mình ở cổng nhé",
        "mình đang trên đường", "để mình gọi lại sau", "mình đã đến nơi", "đừng đợi mình ăn cơm nhé", "mình bận chút, lát nói chuyện sau", "đồng ý, cứ như vậy nhé",
    ]),
)
T("CS05", "T-CALL-NAME", "gọi theo tên", "Lệnh", [
    "gọi (điện |)(cho |){ct}", "gọi điện thoại cho {ct}", "gọi {ct} giúp {L:I}", "gọi {ct} (số di động|số cơ quan|số nhà)", "~{L:I} muốn gọi cho {ct}", "gọi lại cho {ct}",
    "gọi cho {ct} (nhé|đi|)".replace("(nhé|đi|)", ""), "quay số gọi {ct}", "bắt đầu cuộc gọi với {ct}", "liên lạc với {ct}",
], G5, w=3.0, factors="E06")
T("CS05", "T-CALL-NUM", "gọi theo số", "Lệnh", [
    "gọi (số |đến số |)(số )?{ph}".replace("(số )?", ""), "bấm số {ph}", "gọi tới số {ph}", "quay số {ph}", "gọi giúp {L:I} số {ph}", "~{L:I} cần gọi số {ph}", "gọi số này {ph}", "gọi điện đến số {ph}",
], G5, w=2.4, state=[("Bình thường", 0.8), ("Vội / nói nhanh", 0.2)], factors="E03; S53")
T("CS05", "T-CALL-REDIAL", "gọi lại", "Lệnh", [
    "gọi lại số vừa gọi", "gọi lại cuộc gọi nhỡ (vừa rồi|gần nhất)", "gọi cho người vừa gọi cho {L:I}", "gọi lại số cuối cùng", "xem (danh sách |)cuộc gọi nhỡ", "gọi lại số này",
], G5, w=0.7)
T("CS05", "T-CALL-ANS", "nghe, từ chối, kết thúc cuộc gọi", "Lệnh", [
    "(nghe|trả lời|nhấc) máy", "(từ chối|không nghe) cuộc gọi (này|)", "(cúp|ngắt) máy", "kết thúc cuộc gọi", "chuyển cuộc gọi sang loa ngoài", "tăng âm lượng cuộc gọi",
    "giảm âm lượng cuộc gọi", "tắt tiếng micro", "bật lại micro", "(giữ|chờ) máy một lát", "từ chối và nhắn là {L:I} đang lái xe", "chuyển cuộc gọi sang điện thoại",
], G5, w=1.3, factors="E08")
T("CS05", "T-SMS-READ", "đọc tin nhắn", "Lệnh", [
    "(đọc|nghe) tin nhắn (mới|)", "đọc tin nhắn (mới nhất|vừa tới)", "đọc tin nhắn của {ct}", "(có|) tin nhắn (mới|) nào không", "đọc lại tin nhắn (vừa rồi|)", "(đọc|nghe) tin nhắn từ {ct}",
    "đọc tin nhắn (thoại|)".replace("(thoại|)", ""),
], G5, w=1.0, factors="E06")
T("CS05", "T-SMS-SEND", "gửi tin nhắn", "Lệnh", [
    "trả lời (tin nhắn |)(là|rằng) {canned}", "nhắn (cho |tin cho ){ct} (là|rằng) {canned}", "gửi tin nhắn cho {ct}: {canned}", "nhắn lại (là|rằng) {canned}",
    "trả lời tin nhắn là mình đến muộn {mins}", "nhắn cho {ct} là mình đến muộn {mins}", "nhắn {ct} đợi {mins}", "nhắn cho {ct} khoảng {clk} mình đến",
    "báo cho {ct} là {L:I} đến lúc {clk}", "báo {ct} biết {L:I} sẽ đến sau {mins}",
], G5, w=2.6, factors="E03; E06")
T("CS05", "T-LOC-SHARE", "chia sẻ vị trí", "Lệnh", [
    "gửi vị trí (hiện tại |)(cho|tới) {ct}", "chia sẻ (lộ trình|vị trí) (cho|với) {ct}", "gửi giờ đến dự kiến cho {ct}", "chia sẻ chuyến đi này với {ct}", "dừng chia sẻ vị trí",
    "gửi {ct} địa chỉ đang dẫn đường",
], G5, w=1.1, factors="E06")

# ================================================================= CS06 Trạng thái xe
G6 = dict(tire=choice(P.TIRES), lamp=choice(["động cơ", "phanh", "ắc quy", "áp suất lốp", "túi khí", "dầu máy", "nhiệt độ nước làm mát", "cửa chưa đóng", "dây an toàn", "phanh tay", "đèn pha", "bảo dưỡng"]),
          part=choice(["dầu máy", "phanh", "ắc quy", "nước làm mát", "nước rửa kính", "lốp", "đèn xe"]), km=km_val([100, 200, 300, 500, 800, 1000, 1500, 2000, 5000]))
T("CS06", "T-VEH-TIRE", "hỏi áp suất lốp", "Câu hỏi", [
    "áp suất {tire} là bao nhiêu", "kiểm tra áp suất (các |)lốp", "có lốp nào (thiếu hơi|non hơi|bị xì) không", "áp suất lốp (có |)(bình thường|ổn) không", "lốp xe (có |)(vấn đề|ổn) không",
    "{tire} bao nhiêu (hơi|)".replace("(hơi|)", ""), "(cả bốn lốp|các lốp) (có|) đủ hơi không",
], G6, w=1.2, factors="E03")
T("CS06", "T-VEH-FUEL", "hỏi nhiên liệu", "Câu hỏi", [
    "(xe |)còn bao nhiêu (xăng|nhiên liệu|dầu)", "(xăng|nhiên liệu) (còn|đủ) đi (được |)bao xa", "mức tiêu hao nhiên liệu trung bình là bao nhiêu", "~{L:I} có cần đổ xăng chưa",
    "kim xăng còn bao nhiêu", "(xe |)còn (đi|chạy) được bao nhiêu ki lô mét nữa", "mức (xăng|nhiên liệu) (bây giờ|hiện tại) là bao nhiêu",
], G6, w=1.2)
T("CS06", "T-VEH-SERVICE", "hỏi bảo dưỡng", "Câu hỏi", [
    "(khi nào|bao giờ|lúc nào) (phải|cần|tới hạn) bảo dưỡng (tiếp|)", "còn bao nhiêu ki lô mét nữa (đến|tới) kỳ bảo dưỡng", "kiểm tra tình trạng {part}", "xe có (đèn|lỗi|cảnh báo) nào đang sáng không",
    "lần bảo dưỡng gần nhất là khi nào", "(đặt|hẹn) lịch bảo dưỡng (vào |)(cuối tuần|ngày mai|tuần sau)", "{part} (còn|) (tốt|ổn) không",
], G6, w=1.2, factors="E03")
T("CS06", "T-VEH-LAMP", "hỏi đèn cảnh báo", "Câu hỏi", [
    "đèn báo {lamp} (sáng|nhấp nháy) là (sao|gì)".replace("là (sao|gì)", "nghĩa là gì"), "đèn {lamp} (sáng|nhấp nháy) là {L:why}", "đèn {lamp} sáng có nguy hiểm không", "đèn {lamp} sáng nghĩa là gì",
    "(vì sao|tại sao) đèn {lamp} sáng", "{L:I} có cần dừng xe vì đèn {lamp} không",
], G6, w=0.9, factors="E02")
T("CS06", "T-VEH-TRIP", "hỏi hành trình", "Câu hỏi", [
    "quãng đường đã đi (hôm nay|trong chuyến này) là bao nhiêu", "xe đã chạy được bao nhiêu ki lô mét", "đặt lại công tơ mét hành trình", "tốc độ trung bình (của chuyến đi |)là bao nhiêu",
    "(cửa|cốp) (nào |)(chưa đóng|đang mở) không", "đã chạy được bao lâu rồi", "tổng quãng đường (của |)xe là bao nhiêu",
], G6, w=0.9)

# ================================================================= CS07 Sạc xe điện và trạm xăng
G7 = dict(pct=percent([20, 30, 40, 50, 60, 70, 80, 90, 100]), pct2=pct_pair(), kwh=kwh([5, 10, 15, 20, 30, 40, 50, 60]), clk=clock(), poi=poi(None, 0.0), city=city(), mins=minutes([10, 15, 20, 30, 45, 60]),
          st=street_only(), cat=choice(["cửa hàng tiện lợi", "nhà vệ sinh", "quán cà phê", "chỗ nghỉ", "nhà hàng"]))
T("CS07", "T-EV-BATT", "hỏi pin và quãng đường", "Câu hỏi", [
    "pin (còn |)bao nhiêu phần trăm", "(xe |)còn đi được bao nhiêu ki lô mét nữa", "pin có đủ (để |)đi (đến|tới) {poi} không", "mức pin (khi|lúc) (đến|tới) {poi} (là|sẽ là) bao nhiêu",
    "tình trạng pin (thế nào|ra sao)", "pin có đủ về nhà không", "pin còn đủ để (đến|tới) {city} không", "(sức khỏe|tình trạng) pin (hiện tại |)(là |)bao nhiêu",
], G7, w=1.5, factors="E03")
T("CS07", "T-EV-FIND", "tìm trạm sạc", "Lệnh", [
    "tìm trạm sạc (gần nhất|gần đây|trên đường đi|dọc lộ trình)", "tìm trạm sạc nhanh (gần nhất|gần đây)", "tìm trạm sạc (còn trống|có cổng trống) (gần đây|)",
    "dẫn đường đến trạm sạc (gần nhất|nhanh nhất)", "tìm trạm sạc gần {poi}", "tìm trạm sạc ở {city}", "trạm sạc gần nhất {L:where}", "tìm trạm sạc có {cat} gần đây",
    "~{L:I} cần sạc xe, tìm trạm sạc gần nhất", "tìm trạm sạc trên {st}",
], G7, w=1.7, factors="E04")
T("CS07", "T-EV-CTRL", "điều khiển sạc", "Lệnh", [
    "(bắt đầu|dừng) sạc", "đặt (giới hạn|mức) sạc (tối đa |)ở {pct}", "(đặt|hẹn) giờ sạc (lúc|vào) {clk}", "sạc (đến|lên) {pct} (rồi|thì) (dừng|báo)", "mở (nắp|cổng) sạc", "đóng (nắp|cổng) sạc",
    "tắt sạc (khi|lúc) pin đạt {pct}", "sạc (đến|lên) {pct} thôi", "hủy (hẹn giờ |lịch )sạc", "(tăng|giảm) dòng sạc",
], G7, w=1.6, factors="E03")
T("CS07", "T-EV-TIME", "hỏi thời gian và chi phí sạc", "Câu hỏi", [
    "sạc từ {pct2} mất bao lâu", "sạc đầy mất (bao lâu|bao nhiêu phút)", "sạc thêm {kwh} hết bao nhiêu tiền", "(chi phí|giá) sạc một ki lô oát giờ là bao nhiêu", "đã sạc được bao nhiêu ki lô oát giờ rồi",
    "giá sạc (hiện tại |)là bao nhiêu", "còn bao lâu nữa thì sạc (đầy|xong)", "sạc (đến|lên) {pct} còn (mất |)bao lâu", "sạc xong lúc mấy giờ",
], G7, w=1.4, factors="E03; E07")
T("CS07", "T-GAS-FIND", "tìm trạm xăng", "Lệnh", [
    "tìm {L:gas} (gần nhất|trên đường đi|gần đây)", "dẫn đường đến {L:gas} (gần nhất|)", "{L:gas} gần nhất {L:where}", "tìm {L:gas} có (cửa hàng tiện lợi|nhà vệ sinh)", "giá xăng (hôm nay |)là bao nhiêu",
    "tìm {L:gas} ở {city}", "~{L:I} cần đổ xăng, tìm {L:gas} gần nhất", "tìm {L:gas} trên {st}",
], G7, w=0.9, factors="E04")
