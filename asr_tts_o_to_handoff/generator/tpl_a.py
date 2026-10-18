# -*- coding: utf-8 -*-
from tplbase import *

G = dict(
    addr=addr(), poi=poi(None, 0.35), poi_air=poi({"sân bay", "ga", "bến xe"}, 0.3), dist=district(), city=city(),
    home=saved("home"), place=saved("place"), cat=pool_choice("nearby"), hw=highway(), st=street_only(),
    mins=minutes([2, 3, 5, 7, 10, 12, 15, 20, 25, 30, 40, 45, 60, 90, 120]),
    km=km_val([0.5, 0.8, 1, 1.5, 2, 3, 4, 5, 8, 10, 12, 15, 20, 30, 50, 80, 120, 200, 350]),
    met=met_val([50, 100, 150, 200, 300, 400, 500, 800]),
    vol=intg(1, 30), ordw=ordinal_word(), clk=clock(),
)

# ================================================================= CS01 Dẫn đường
GO = "(đến|tới)"
T("CS01", "T-NAV-ADDR", "dẫn đường đến địa chỉ", "Lệnh", [
    f"dẫn đường {GO} {{addr}}", f"chỉ đường {GO} {{addr}}", f"chỉ đường cho {{L:I}} {GO} {{addr}}",
    f"(bắt đầu|mở) dẫn đường {GO} {{addr}}", f"đưa {{L:I}} {GO} {{addr}}", f"tìm đường {GO} {{addr}}",
    f"điều hướng {GO} {{addr}}", f"~{{L:I}} muốn đi {GO} {{addr}}", f"~{{L:I}} cần đến {{addr}}",
    f"dẫn đường {GO} {{addr}} (bằng|theo) đường nhanh nhất", "đặt điểm đến là {addr}", f"đi {GO} {{addr}}",
], G, w=3.0, factors="E04; S54")
T("CS01", "T-NAV-POI", "dẫn đường đến địa điểm", "Lệnh", [
    f"dẫn đường {GO} {{poi}}", f"chỉ đường {GO} {{poi}}", f"đưa {{L:I}} {GO} {{poi}}", f"tìm đường {GO} {{poi}}",
    "đi {poi}", f"~{{L:I}} muốn đến {{poi}}", f"~{{L:I}} cần đến {{poi}}", f"điều hướng {GO} {{poi}}",
    f"(mở|bắt đầu) dẫn đường {GO} {{poi}}", "đặt điểm đến là {poi}",
], G, w=2.6, factors="E04")
T("CS01", "T-NAV-CAT", "dẫn đường đến loại địa điểm gần nhất", "Lệnh", [
    "dẫn đường đến {cat} gần nhất", "đưa {L:I} đến {cat} gần nhất", "tìm {cat} gần nhất rồi dẫn đường", "chỉ đường đến {cat} gần nhất",
    "~{L:I} muốn đến {cat} gần nhất", "dẫn đường đến {cat} gần đây",
], G, w=0.9, factors="E04")
T("CS01", "T-NAV-DIST", "dẫn đường đến quận huyện hoặc thành phố", "Lệnh", [
    f"dẫn đường {GO} {{dist}}", f"đưa {{L:I}} {GO} {{dist}}", f"tìm đường {GO} {{dist}}", f"đi {GO} {{dist}}", f"~{{L:I}} cần đến {{dist}}",
    "dẫn đường đi {city}", "~{L:I} muốn đi {city}", "đưa {L:I} đi {city}", "dẫn đường đi {city} (theo|bằng) (cao tốc|quốc lộ|đường nhanh nhất)",
    "chỉ đường đi {city}",
], G, w=1.4, factors="E04")
T("CS01", "T-NAV-HOME", "dẫn đường về nhà", "Lệnh", [
    "dẫn đường về {home}", "đưa {L:I} về {home}", "~về {home}", "~{L:I} muốn về {home}", "chỉ đường về {home}", "đặt {home} làm điểm đến", "dẫn {L:I} về {home}",
], G, w=0.8)
T("CS01", "T-NAV-PLACE", "dẫn đường đến nơi đã lưu", "Lệnh", [
    f"dẫn đường {GO} {{place}}", f"đưa {{L:I}} {GO} {{place}}", f"chỉ đường {GO} {{place}}", f"đi {GO} {{place}}", f"~{{L:I}} cần đến {{place}}", f"điều hướng {GO} {{place}}",
], G, w=0.7)
T("CS01", "T-NAV-ETA", "hỏi khoảng cách và thời gian", "Câu hỏi", [
    "còn bao xa nữa (thì|là) (đến|tới) (nơi|đích)", "còn bao lâu nữa (thì|là) (đến|tới) (nơi|đích)", "còn bao nhiêu (ki lô mét|cây số) nữa",
    "mấy giờ (thì|) (đến|tới) nơi", "(đến|tới) {poi_air} mất bao lâu", "(đến|tới) {city} còn bao xa",
    "từ đây (đến|tới) {poi} bao xa", "khoảng bao lâu nữa thì {L:I} (đến|tới) {city}", "dự kiến mấy giờ (đến|tới)",
    "{L:I} sẽ (đến|tới) nơi lúc mấy giờ", "còn khoảng {mins} nữa là (đến|tới) nơi đúng không",
    "còn {km} nữa là (đến|tới) nơi đúng không", "(đến|tới) nơi lúc {clk} có kịp không", "liệu có (đến|tới) kịp lúc {clk} không",
    "từ đây đến {dist} bao nhiêu (ki lô mét|cây số)", "còn đi bao lâu nữa {L:thus}",
], G, w=1.8, factors="E04; D01")
T("CS01", "T-NAV-NEXT", "hỏi chỉ dẫn tiếp theo", "Câu hỏi", [
    "đoạn tới {L:turn} hướng nào", "sắp tới có phải {L:turn} (trái|phải) không", "{L:turn} (trái|phải) ở ngã tư tiếp theo đúng không",
    "còn {met} nữa là {L:turn} (trái|phải) đúng không", "lối ra tiếp theo là lối nào", "(đi thẳng|chạy thẳng) bao xa nữa thì {L:turn} (trái|phải)",
    "đến {L:round} thì đi lối ra thứ {ordw} đúng không", "khi nào phải chuyển sang {L:lane} (bên trái|bên phải)", "còn {met} nữa thì đến chỗ {L:turn}",
    "sau đó đi (thẳng|tiếp) hay {L:turn}", "ở ngã ba tới {L:turn} (trái|phải) hay đi thẳng",
], G, w=1.1, factors="D01; E03")
T("CS01", "T-NAV-VOICE", "chỉnh giọng hướng dẫn", "Lệnh", [
    "nhắc lại (hướng dẫn|chỉ dẫn) (vừa rồi|)", "nói lại đoạn vừa rồi", "(tắt|bật) giọng (chỉ đường|dẫn đường)", "tăng âm lượng (chỉ đường|dẫn đường) lên {vol}",
    "giảm âm lượng (chỉ đường|dẫn đường) xuống {vol}", "đặt âm lượng (chỉ đường|dẫn đường) ở mức {vol}", "chỉ đường nhỏ tiếng lại", "chỉ đường to hơn một chút",
    "chỉ báo những chỗ quan trọng thôi", "đọc tên đường khi chỉ đường", "(bật|tắt) cảnh báo tốc độ trên bản đồ",
], G, w=0.7)
T("CS01", "T-NAV-ROUTE", "chọn tuyến đường", "Lệnh", [
    "(đi|chọn) đường (nhanh nhất|ngắn nhất|ít {L:jam} nhất|ít đèn đỏ nhất|ít cua nhất)",
    "tránh (cao tốc|trạm thu phí|đường cấm tải|đường đang thi công|đoạn ngập nước)", "không đi qua (cao tốc|trạm thu phí|đường đang thi công)",
    "(ưu tiên|chọn) cao tốc", "tìm đường khác tránh {L:jam}", "đổi lộ trình khác", "có đường nào khác không", "cho {L:I} xem (các|những) (tuyến|lộ trình) (khác|còn lại)",
    "đi (theo|qua) {hw}", "(đi|chạy) {hw} được không", "chọn {hw}", "~{L:I} muốn đi đường (nhanh nhất|ngắn nhất)",
], G, w=1.2, factors="D01")
T("CS01", "T-NAV-STOP", "thêm điểm dừng", "Lệnh", [
    "thêm điểm dừng (tại|ở) {poi}", "ghé {cat} trước rồi (mới |)(đi tiếp|đến nơi)", "thêm một điểm dừng là {poi}", "xóa điểm dừng", "bỏ điểm dừng cuối",
    "tìm {cat} trên đường đi", "tìm {L:gas} dọc đường", "dừng lại ở {cat} (tiếp theo|gần nhất)", "thêm {cat} vào lộ trình", "ghé qua {poi} trước",
], G, w=0.8, factors="E04")
T("CS01", "T-NAV-CANCEL", "kết thúc dẫn đường", "Lệnh", [
    "hủy dẫn đường", "dừng dẫn đường", "thôi không đi nữa", "kết thúc (chuyến đi|hành trình)", "thoát chỉ đường", "tắt dẫn đường đi", "không cần dẫn đường nữa",
    "hủy lộ trình", "dừng lại, {L:I} đến nơi rồi", "~{L:I} đến nơi rồi, tắt dẫn đường",
], G, w=0.5, factors="E08")
T("CS01", "T-NAV-MAP", "điều khiển bản đồ", "Lệnh", [
    "phóng to bản đồ", "thu nhỏ bản đồ", "(bật|chuyển sang) chế độ bản đồ (ban đêm|ban ngày)", "chuyển bản đồ sang (ba chiều|hai chiều)", "xem toàn bộ lộ trình",
    "(hiển thị|xem) bản đồ (theo hướng xe|hướng bắc lên trên)", "(bật|tắt) hiển thị giao thông trên bản đồ", "xem các điểm dừng", "hiện thông tin làn đường",
    "(bật|tắt) chế độ ban đêm cho bản đồ",
], G, w=0.5)

# ================================================================= CS02 Cảnh báo an toàn
WARN = ["cảnh báo lệch làn", "cảnh báo va chạm phía trước", "cảnh báo điểm mù", "cảnh báo vượt tốc độ", "cảnh báo người lái buồn ngủ", "cảnh báo va chạm khi lùi xe", "cảnh báo khi có xe tới gần lúc mở cửa"]
SYS = ["hệ thống hỗ trợ giữ làn", "hệ thống phanh khẩn cấp tự động", "hệ thống nhận diện biển báo", "hệ thống giám sát người lái", "hệ thống hỗ trợ đỗ xe", "camera lùi", "cảm biến đỗ xe", "camera ba trăm sáu mươi độ"]
SYS_RAW = {"camera ba trăm sáu mươi độ": "camera 360 độ"}
G2 = dict(warn=choice(WARN), sysn=choice_pairs([(SYS_RAW.get(x, x), x) for x in SYS], ("số",)),
          spd=kmh([50, 60, 70, 80, 90, 100, 110, 120]), spd5=kmh([5, 10]), mins=minutes([10, 15, 20, 30, 45, 60]),
          lev=choice(["thấp", "trung bình", "cao"]), dist=choice(["gần", "vừa", "xa"]))
T("CS02", "T-ADAS-TOGGLE", "bật tắt cảnh báo", "Lệnh", [
    "(bật|tắt) {warn}", "(bật|tắt) {sysn}", "tắt tạm thời {warn}", "(bật|tắt) {warn} giúp {L:I}", "~{L:I} muốn (bật|tắt) {sysn}", "tạm tắt {sysn}",
], G2, w=2.0, factors="E08")
T("CS02", "T-ADAS-SENS", "chỉnh độ nhạy", "Lệnh", [
    "đặt độ nhạy {warn} ở mức {lev}", "chỉnh {warn} sang mức {lev}", "(tăng|giảm) độ nhạy {warn}", "đổi độ nhạy cảnh báo va chạm sang mức {lev}",
], G2, w=1.0)
T("CS02", "T-ADAS-CRUISE", "ga tự động và hành trình", "Lệnh", [
    "bật (ga tự động|hành trình thích ứng) (ở|với) tốc độ {spd}", "đặt tốc độ hành trình {spd}", "tăng tốc độ hành trình thêm {spd5}", "giảm tốc độ hành trình bớt {spd5}",
    "đặt khoảng cách với xe phía trước ở mức {dist}", "(tắt|hủy) (ga tự động|hành trình thích ứng)", "đặt cảnh báo khi vượt quá {spd}", "bật giới hạn tốc độ {spd}",
], G2, w=1.5, factors="E03")
T("CS02", "T-ADAS-FATIGUE", "phản hồi nhắc nghỉ", "Lệnh", [
    "~{L:I} (tỉnh|ổn) rồi, (không cần|đừng) nhắc nữa", "tắt nhắc nhở nghỉ ngơi", "nhắc {L:I} nghỉ ngơi sau {mins}", "tìm trạm dừng chân gần nhất",
    "~{L:I} hơi mệt, tìm chỗ nghỉ gần đây", "~{L:I} biết rồi, tắt cảnh báo đi", "cho {L:I} nghỉ một lát rồi nhắc lại", "~{L:I} đang tỉnh, cảm ơn",
], G2, w=1.1, state=[("Mệt mỏi", 0.6), ("Bình thường", 0.4)], factors="S22; S23")

# ================================================================= CS03 Điều khiển xe
T3 = dict(
    temp=decg(16, 30, 0.5), n3=decg(0.5, 3, 0.5), fan=intg(1, 7), lvl3=intg(1, 3), lvl5=intg(1, 5), pct=percent([10, 20, 25, 30, 40, 50, 60, 70, 75, 80]), nn=intg(1, 3),
    seat=choice(["ghế lái", "ghế phụ", "ghế sau bên lái", "ghế sau bên phụ"]), seatf=choice(["ghế lái", "ghế phụ"]),
    wpos=choice(["bên lái", "bên phụ", "sau bên lái", "sau bên phụ", "phía trước bên lái"]),
    vent=choice(P.VENTS), color=choice(["xanh dương", "đỏ", "tím", "trắng", "cam", "xanh lá", "hồng", "vàng", "xanh ngọc"]),
    lamp=choice(["đèn trong xe", "đèn đọc sách", "đèn nội thất", "đèn sương mù", "đèn pha tự động"]),
)
T("CS03", "T-CAR-TEMP", "đặt nhiệt độ điều hòa", "Lệnh", [
    "đặt nhiệt độ {L:ac} (ở|là) {temp} độ", "chỉnh {L:ac} xuống {temp} độ", "chỉnh {L:ac} lên {temp} độ", "bật {L:ac} {temp} độ", "bật {L:ac} ở {temp} độ",
    "đặt nhiệt độ bên (lái|phụ) {temp} độ", "đặt nhiệt độ khoang sau {temp} độ", "đồng bộ nhiệt độ hai bên (ở|là) {temp} độ",
    "tăng nhiệt độ thêm {n3} độ", "giảm nhiệt độ bớt {n3} độ", "~{L:I} thấy nóng quá, chỉnh {L:ac} xuống {temp} độ", "~{L:I} thấy lạnh quá, chỉnh {L:ac} lên {temp} độ", "{temp} độ thôi", "~{L:I} muốn {L:ac} {temp} độ",
], T3, w=2.6, factors="E03; E02")
T("CS03", "T-CAR-FAN", "chỉnh quạt gió", "Lệnh", [
    "tăng quạt gió lên mức {fan}", "giảm quạt gió xuống mức {fan}", "đặt quạt gió mức {fan}", "quạt gió mức {fan}", "(bật|tắt) quạt gió", "chỉnh quạt (tối đa|nhỏ nhất)",
    "đặt quạt gió (ở chế độ tự động|tự động)", "chỉnh gió {vent}", "đổi hướng gió {vent}", "tăng quạt thêm một nấc", "giảm quạt bớt một nấc",
], T3, w=1.2, factors="E03; E02")
T("CS03", "T-CAR-ACMODE", "chế độ điều hòa", "Lệnh", [
    "(bật|tắt) {L:ac}", "(bật|tắt) chế độ {L:ac} tự động", "{L:ac} (lấy gió ngoài|chạy tuần hoàn trong|chạy chế độ gió trong)", "(bật|tắt) sấy kính (trước|sau)",
    "bật chế độ khử sương kính", "(bật|tắt) sưởi kính sau", "(bật|tắt) lọc không khí", "đổi sang chế độ tiết kiệm cho {L:ac}", "(bật|tắt) chế độ {L:ac} cho khoang sau",
    "tắt {L:ac} đi", "bật {L:ac} lên",
], T3, w=1.6)
T("CS03", "T-CAR-SEAT", "điều khiển ghế", "Lệnh", [
    "bật sưởi {seat} (ở |)mức {lvl3}", "tắt sưởi {seat}", "bật làm mát {seat} mức {lvl3}", "(tăng|giảm) sưởi {seatf}", "đẩy ghế lái ra (sau|trước) một chút", "nâng ghế lái lên",
    "hạ ghế lái xuống", "chỉnh lưng ghế (lái|phụ) (ngả ra sau|dựng thẳng lên)", "lưu vị trí ghế vào hồ sơ {nn}", "gọi vị trí ghế đã lưu {nn}",
    "bật massage {seatf} mức {lvl3}", "tắt massage {seatf}", "(bật|tắt) sưởi ghế",
], T3, w=1.8, factors="E03")
T("CS03", "T-CAR-WIN", "điều khiển cửa kính", "Lệnh", [
    "(hạ|mở) {L:win} {wpos} xuống (một nửa|hoàn toàn|một chút)", "kéo {L:win} {wpos} (lên hết|lên một chút)", "đóng {L:win} {wpos}", "đóng tất cả {L:win}",
    "(mở|hạ) tất cả {L:win} xuống một chút", "hạ {L:win} {wpos} xuống {pct}", "(mở|đóng) cửa sổ trời", "mở cửa sổ trời (một nửa|hết)",
    "(đóng|mở) rèm che nắng cửa sổ trời", "khóa {L:win} sau", "(mở|đóng) cốp (xe|sau)", "mở khóa {L:win} sau", "hé {L:win} {wpos} ra một chút",
], T3, w=2.2, factors="E03")
T("CS03", "T-CAR-MISC", "khóa cửa, gương, đèn, gạt mưa", "Lệnh", [
    "(khóa|mở khóa) (tất cả )?cửa", "gập gương chiếu hậu", "(mở|gập) gương (chiếu hậu|)", "chỉnh gương (chiếu hậu )?(bên lái|bên phụ) (lên|xuống|vào trong|ra ngoài)",
    "(bật|tắt) {lamp}", "bật gạt mưa (chậm|nhanh|tự động)", "đổi màu đèn nội thất sang {color}", "chỉnh độ sáng đèn nội thất {pct}", "(bật|tắt) sưởi vô lăng",
    "đổi chế độ lái sang (tiết kiệm|thể thao|tiêu chuẩn)", "(bật|tắt) chế độ (tiết kiệm|thể thao)", "tắt gạt mưa", "(bật|tắt) đèn (pha|chiếu sáng) tự động",
], T3, w=2.0)
