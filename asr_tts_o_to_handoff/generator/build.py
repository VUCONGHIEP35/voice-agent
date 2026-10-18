import json, re, sys, os
D = "./"
ACT = {"L": "Lệnh", "Q": "Câu hỏi", "C": "Câu cụt"}
REG = {"t": "trung tính", "m": "thân mật", "l": "lịch sự"}
intents = []
for part in ("part1.txt", "part2.txt", "part3.txt"):
    cur = None
    for line in open(D + part, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("## "):
            case, name = [x.strip() for x in line[3:].split("|")]
            cur = {"case": case, "intent": name, "patterns": []}
            intents.append(cur)
            continue
        f = line.split("|")
        text = f[0].strip()
        act = ACT[f[1]] if len(f) > 1 and f[1] else "Lệnh"
        reg = REG[f[2]] if len(f) > 2 and f[2] else "trung tính"
        src = f[3].strip() if len(f) > 3 and f[3].strip() else None
        cur["patterns"].append({"text": text, "act": act,
                                "evidence": "seen" if src else "constructed",
                                "source": src, "register": reg})

def S(id, url, what, fetched=True):
    return {"id": id, "url": url, "what": what, "fetched": fetched}

sources = [
 S("N1","https://vinfastauto.com/vn_vi/node/9362","Trang chính thức VinFast (tiếng Việt): từ đánh thức 'Hey VinFast'/'VinFast ơi' và danh sách câu lệnh mẫu: điều hòa, quạt gió, hướng gió, lấy gió trong/ngoài, sấy kính, cốp, wifi, dẫn đường, tìm trạm sạc, nhạc Bluetooth/USB, radio, podcast, kể truyện cười"),
 S("N2","https://vinfastauto.com/vn_vi/cau-hoi-thuong-gap/cau-hoi-xe-o-to/tro-ly-ao","Mục Trợ lý ảo của VinFast: trùng nội dung N1 (xác nhận chéo)"),
 S("N3","https://vinfastauto.com/vn_en/node/9362","Bản tiếng Anh của N1; thêm lệnh 'Open Front/Rear Camera' (chỉ thấy bản Anh, mẫu tiếng Việt được tự soạn)"),
 S("N4","https://doanhnhan.baophapluat.vn/tro-ly-ao-vinfast-da-thay-doi-thoi-quen-lai-xe-cua-nguoi-viet-the-nao-64239.html","Hai ví dụ: 'Hey VinFast, tăng điều hòa lên 2 độ C'; 'Hey VinFast, gọi điện tới số 098xxxxxxx'"),
 S("N5","https://diendandoanhnghiep.vn/tro-ly-ao-vivi-vinfast-dau-an-moi-cua-ky-nguyen-cong-nghe-giong-noi-214119.html","Ví dụ hội thoại với Vivi: 'Tôi buồn quá', 'Tâm sự với tôi đi', 'Bạn yêu ai nhất', 'Làm sao để giảm cân', 'Hôm nay ăn gì nhỉ?', 'Chỉ tôi mấy câu thả thính', 'Kể chuyện cười đi ViVi'"),
 S("N6","https://tuoitre.vn/nu-youtuber-noi-tieng-danh-gia-vinfast-vf8-camera-thu-vi-sau-vo-lang-chia-khoa-se-som-thay-doi-20220428080105356.htm","Bài đánh giá VF8: 'tăng nhiệt độ điều hòa' (trực tiếp), 'tôi thấy lạnh', 'tôi đói' (gián tiếp)"),
 S("N7","https://fptshop.com.vn/tin-tuc/thu-thuat/huong-dan-su-dung-siri-tren-iphone-trong-o-to-78318","Siri trên ô tô: 'Gọi cho [tên]', 'Nhắn tin cho', 'Chỉ đường đến [địa điểm]', 'Phát nhạc', 'Bài hát tiếp theo', 'Thời tiết hôm nay thế nào', 'Nhắc tôi…', 'Chỉ đường về nhà'"),
 S("N8","https://viettelstore.vn/tin-tuc/siri-co-the-lam-duoc-gi","Ví dụ Siri tiếng Việt: thời tiết, nhắc việc, báo thức, lịch họp, gọi cho mẹ, nhắn cho Linh, đọc tin nhắn mới nhất, tính toán, đổi tiền, hỏi đáp"),
 S("N9","https://www.thegioididong.com/tin-tuc/cach-su-dung-siri-tieng-viet-1576421","Siri: 'chỉ đường đến Nhà thờ Đức Bà'"),
 S("N10","https://www.thegioididong.com/hoi-dap/huong-dan-su-dung-tro-ly-ao-siri-tren-iphone-590970","Siri: gọi cho tên/số, nhắn tin, đặt lịch hẹn, báo thức, lời nhắc, tìm quán cà phê gần đây, chỉ đường, thời tiết ngày mai, phát nhạc, tăng âm lượng"),
 S("N11","https://www.tcl.com/vn/vi/blog/playbooks/google-assistant-101-how-to-make-it-enjoyable-and-useful-for-you","Google Assistant tiếng Việt: nhắc việc, hỏi đường/khoảng cách/thời gian/giao thông, phát nhạc theo bài/ca sĩ"),
 S("N12","https://apps.apple.com/vn/app/id1564418703","Mô tả app Kiki (Zalo): 'Mở bài…', 'Mở nhạc Rap', 'mở nhạc Tuấn Hưng', 'Mở bảng xếp hạng nhạc Việt', thời tiết, giá vàng, ngày âm lịch, tin mới, nhắc việc, tính toán, đổi tiền"),
 S("N13","https://zalo.me/en/post/kiki-auto","Trang Kiki Auto: ví dụ 'Chỉ đường tới cây xăng gần nhất'"),
 S("N14","https://fptshop.com.vn/tin-tuc/thu-thuat/cach-dieu-khien-nhac-bang-giong-noi-tren-zing-mp3-nho-tro-ly-ao-kiki-160640","Kiki + Zing MP3: 'mở nhạc của Bích Phương'; mô tả hẹn giờ tắt nhạc (chỉ mô tả)"),
 S("N15","https://tech.zingnews.vn/tro-ly-ao-tieng-viet-kiki-ra-mat-da-nen-tang-chay-duoc-tren-oto-post1164990.html","Kiki: từ đánh thức 'Kiki ơi'; câu hỏi tri thức 'Dân số Hà Nội là bao nhiêu', 'Việt Nam giáp với nước nào', 'Tác giả thuyết tương đối là ai'"),
 S("N16","https://tech.zingnews.vn/tro-ly-ai-tren-o-to-yeu-to-khien-nguoi-mua-xe-can-nhac-khi-chot-keo-post1578442.html","Cách nói địa điểm lưu sẵn khi xin chỉ đường: 'nhà', 'cơ quan', 'quê'"),
 S("N17","https://www.thegioididong.com/hoi-dap/huong-dan-su-dung-tro-ly-ao-google-asisstant-tren-1164688","Google Assistant tiếng Việt: 'Tạo lịch hẹn', 'Tạo nhắc nhở', 'Gọi điện', 'Gửi tin nhắn', 'Đặt bàn', 'Thời tiết', 'Đặt báo thức', 'Kết quả bóng đá Euro'"),
 S("N18","https://vnexpress.net/nguoi-dung-noi-gi-ve-xe-dien-vinfast-4708961.html","Chủ xe VF8 mô tả chức năng Vivi (chỉnh quạt gió/điều hòa, camera 360, lên xuống kính, đóng mở cốp, giá vàng/ngoại hối); chỉ là mô tả chức năng, không phải câu nói nguyên văn"),
 S("N19","https://baodautu.vn/vf-8-xe-em-hon-them-nhieu-tinh-nang-moi-sau-moi-lan-cap-nhat-phan-mem-d199336.html","Từ đánh thức 'VinFast ơi' và 'Hey VinFast' (chỉ từ đánh thức)"),
 S("N20","https://www.brandsvietnam.com/congdong/topic/345237-kiki-auto-cua-zalo-ai-dat-1-trieu-luot-cai-dat-tren-o-to","Mô tả chức năng Kiki Auto: dẫn đường, nhạc, tra cứu, kiểm tra phạt nguội, mở camera, tăng/giảm âm lượng, cảnh báo tốc độ (không có câu nguyên văn)"),
 S("N21","https://fptshop.com.vn/tin-tuc/thu-thuat/huong-dan-cai-dat-tro-ly-ao-kiki-giong-noi-tieng-viet-160618","Đã đọc: chỉ mô tả nhóm chức năng Kiki (chỉ đường, mở Youtube, mở nhạc, tin tức), không có câu lệnh nguyên văn"),
 S("N22","https://cellphones.com.vn/sforum/tro-ly-kiki-zalo","Đã đọc: chỉ mô tả nhóm chức năng Kiki, không có câu lệnh nguyên văn"),
 S("N23","https://www.thegioididong.com/tin-tuc/chung-ta-da-co-the-su-dung-google-assistant-bang-tieng-viet-1164350","Đã đọc: chỉ mô tả chung (gọi điện, nhắn tin, bật tắt wifi, mở ứng dụng); không có câu nguyên văn"),
 S("N24","https://www.dienmayxanh.com/kinh-nghiem-hay/xx-meo-cuc-hay-khi-dung-google-assistant-co-the-ba-1235178","Đã đọc: ví dụ Google Assistant đều bằng tiếng Anh, không dùng"),
 S("N25","https://vnreview.vn/threads/tro-ly-giong-noi-vivi-tren-o-to-vinfast-co-gi-noi-bat.9737/latest","Không truy cập được (robots.txt chặn)", False),
 S("N26","https://vnreview.vn/threads/huong-dan-cai-dat-kiki-dieu-khien-bang-giong-noi-tren-o-to-cuc-don-gian.2927/latest","Không truy cập được (robots.txt chặn)", False),
 S("N27","https://support.google.com/androidauto/answer/6395485","Trang hỗ trợ Android Auto của Google (cả bản vi và en): lỗi khi tải", False),
 S("N28","https://tinhte.vn/t/3241824","Tinh tế 'Trên tay Kiki': lỗi khi tải", False),
 S("N29","https://tinhte.vn/thread/2954403","Tinh tế skills tiếng Việt cho Google Assistant: lỗi khi tải", False),
 S("N30","https://om.vinfastauto.com/vi_vn","Sách hướng dẫn sử dụng VinFast online: lỗi khi tải", False),
 S("N31","https://tapchitoaan.vn/tro-ly-ao-vinfast-3.0-cham-dung-gu-nguoi-tre-15389.html","Bài về Trợ lý ảo VinFast 3.0: lỗi khi tải", False),
 S("N32","https://support.google.com/maps/answer/6251268","Trợ giúp Google Maps (lệnh giọng nói): lỗi khi tải", False),
]

slots_seen = {
 "dia_diem": ["Nhà thờ Đức Bà","cây xăng gần nhất","cửa hàng Thế Giới Di Động gần đây","Vincom Bà Triệu","nhà","cơ quan","quê"],
 "loai_dia_diem": ["quán cà phê","cây xăng","trạm sạc","quán ăn"],
 "ten_lien_he": ["mẹ","Mẹ","Linh","An"],
 "ca_si": ["Bích Phương","Tuấn Hưng","Hoàng Thùy Linh"],
 "bai_hat": ["Đi Đua Đưa Đi","See Tình","Đường Đến Ngày Vinh Quang","Let It Go"],
 "the_loai": ["Rap","nhạc Việt"],
 "nhiet_do": ["2 độ C","25 độ"],
 "huong_gio": ["mặt","chân","mặt, chân","chân và cửa kính trước"],
 "thoi_gian": ["8 giờ sáng mai","8 giờ sáng hàng ngày","9 giờ tối","6 giờ sáng mai","5 giờ chiều","3 giờ chiều ngày mai"],
 "noi_dung": ["đi khám sức khỏe","uống thuốc","mua sữa","ăn trưa","mình đến muộn 10 phút","con sẽ về trễ","con đang trên đường về"],
 "chu_de": ["(chỉ thấy placeholder X, Y, Z trong N1, chưa có giá trị thật)"],
 "so_dien_thoai": ["098xxxxxxx (đã bị che trong N4)"],
 "thanh_pho": [],
 "ung_dung": ["Zalo (chỉ thấy như tên ứng dụng), YouTube, Spotify, Netflix (N17, mở ứng dụng)"],
}
slots_seen = {k: v for k, v in slots_seen.items() if v}

particles = {
 "cuoi_cau": ["nhé","nha","đi","với","giúp tôi","giùm tôi","được không","làm ơn","thôi","luôn","ạ","nào","nhỉ","đã","hộ tôi"],
 "mo_dau": ["Cho tôi","Giúp tôi","Làm ơn","Hãy","Tôi muốn","Tôi cần","Bạn ơi","Này","Cho mình","Mở giúp","Nhờ bạn","Xin hãy","Ê"],
 "wake": ["Hey VinFast / VinFast ơi (N1,N19)","Kiki ơi (N15)","Ok Google / Hey Google (N17)","Hey Siri (N8,N9)"],
 "ghi_chu": "Chỉ 'đi' (Kể chuyện cười đi, Tâm sự với tôi đi, N5), 'nhỉ' (Hôm nay ăn gì nhỉ, N5), 'giúp' và 'ơi' (từ đánh thức) thật sự thấy trong nguồn; các hạt còn lại do tự soạn theo tiếng Việt khẩu ngữ. Dùng khe {wake} tùy chọn, không gắn tên thương hiệu vào mẫu."
}

notes = ("1) Nguồn có câu lệnh thật tiếng Việt đáng tin nhất là trang chính thức VinFast (N1) cho điều hòa, quạt, sấy kính, cốp, wifi, dẫn đường, tìm trạm sạc, nhạc, radio, podcast, truyện cười. "
"Các nhóm còn lại (Siri, Google Assistant, Kiki) chỉ có vài ví dụ rời rạc, nhiều bài chỉ mô tả chức năng. "
"2) Không tìm được tài liệu tiếng Việt về lệnh giọng nói trên xe Hyundai, Toyota, Kia, Mazda, MG, Ford tại Việt Nam; các tìm kiếm chỉ trả về tài liệu tiếng Anh/nước ngoài (không dùng). "
"3) Không tìm được thread Otofun/Voz/Webtretho có câu nói nguyên văn; không có trang diễn đàn nào truy cập được qua tìm kiếm. "
"4) Android Auto/Google Assistant: trang hỗ trợ của Google không tải được; chỉ dùng bài TCL (N11) và TGDĐ (N17). CarPlay: không có trang tiếng Việt riêng, dùng bài Siri (N7-N10). "
"5) Các nhóm CS02 (cảnh báo an toàn), CS06 (trạng thái xe), CS07 (xe điện, trừ 'Tìm trạm sạc'), CS09 (khẩn cấp), CS11 (hành khách) hầu như hoàn toàn tự soạn, chưa có bằng chứng nguồn về cách người Việt thực sự nói. "
"6) Các lệnh VinFast trong N1 dùng 'điều hoà' (dấu cũ); mẫu của tôi dùng 'điều hòa'. Các slot X trong N1 là placeholder, không phải giá trị thật. "
"7) Số điện thoại trong N4 bị che; tên kênh radio, tần số, tên trạm sạc, tên phố, tên quán trong mẫu là giá trị minh họa, chưa thấy trong nguồn. "
"8) Lệnh camera trước/sau chỉ thấy bản tiếng Anh (N3); mẫu tiếng Việt do tự soạn. "
"9) Dữ liệu 'seen' có thể đã được tôi chuyển sang dạng khe (ví dụ 'Gọi cho mẹ' thành 'Gọi cho {ten_lien_he}'); cấu trúc câu là thật, giá trị khe có thể khác. "
"10) Các câu 'Tôi nóng/Tôi lạnh/Tôi đói' là lệnh gián tiếp (suy ra ý định), cần nhãn riêng khi huấn luyện NLU.")

out = {"sources": sources, "intents": intents, "slots_seen": slots_seen, "particles": particles, "notes": notes}
path = D + "src_commands.json"
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# validation
ids = {s["id"] for s in sources}
seen = cons = 0
bad = []
for it in intents:
    n = len(it["patterns"])
    texts = [p["text"] for p in it["patterns"]]
    if not (6 <= n <= 15): bad.append((it["intent"], n))
    if len(set(texts)) != n: bad.append((it["intent"], "dup"))
    for p in it["patterns"]:
        if p["source"] and p["source"] not in ids: bad.append((it["intent"], p["source"]))
        if p["evidence"] == "seen": seen += 1
        else: cons += 1
        if re.search(r"VinFast|Vivi|ViVi|Kiki|Siri|Google", p["text"]): bad.append((it["intent"], "brand", p["text"]))
print("intents", len(intents), "patterns", seen + cons, "seen", seen, "constructed", cons)
print("sources fetched", sum(s["fetched"] for s in sources), "failed", sum(not s["fetched"] for s in sources))
print("bad", bad)
# per-case counts
from collections import Counter
c = Counter(i["case"] for i in intents); print(dict(c))
