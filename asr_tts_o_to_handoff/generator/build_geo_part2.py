# -*- coding: utf-8 -*-
exec(open('./build_geo_part1.py', encoding='utf-8').read())

def v(name, source, note=None, **kw):
    d = {"name": name, "verified": True, "source": source}
    d.update(kw)
    if note: d["note"] = note
    return d
def u(name, note="Có thật theo hiểu biết chung nhưng chưa xác minh được trong các nguồn đã đọc", **kw):
    d = {"name": name, "verified": False, "source": None}
    d.update(kw)
    d["note"] = note
    return d
def poi(name, typ, source=None, note=None):
    d = {"name": name, "type": typ, "verified": source is not None, "source": source}
    if note: d["note"] = note
    return d

TABLE = "tên có trong bảng giá đất cũ của nguồn (trước sáp nhập)"
C = {}

# ===================== HÀ NỘI =====================
C["Hà Nội"] = {
 "region":"Bắc",
 "streets":[
  v("Chùa Bộc","G26"),v("Xuân Thủy","G24"),v("Nguyễn Trãi","G26"),v("Giải Phóng","G26"),v("Láng Hạ","G26"),
  v("Trần Duy Hưng","G24"),v("Khuất Duy Tiến","G20"),v("Phạm Hùng","G24"),v("Hàng Gai","G25"),v("Hàng Bông","G25"),
  v("Hàng Đào","G25"),v("Hàng Bạc","G25"),v("Đại Cồ Việt","G28"),v("Tây Sơn","G26"),v("Thái Hà","G26"),
  v("Trường Chinh","G26"),v("Xã Đàn","G26"),v("Kim Mã","G27"),v("Liễu Giai","G27"),v("Điện Biên Phủ","G27"),
  v("Hoàng Diệu","G27"),v("Phan Đình Phùng","G27"),v("Nguyễn Chí Thanh","G26"),v("Lê Duẩn","G26"),
  v("Tôn Đức Thắng","G26"),v("Lạc Long Quân","G24"),v("Võ Chí Công","G24"),v("Văn Cao","G29"),
  v("Lê Văn Lương","G24"),v("Hoàng Quốc Việt","G24"),v("Phạm Văn Đồng","G24"),v("Bạch Mai","G28"),
  v("Minh Khai","G28"),v("Nguyễn Văn Cừ","G20"),v("Lê Đức Thọ","G24"),v("Đại lộ Thăng Long","G24"),
  v("Nguyễn Lương Bằng","G20"),v("Hoàng Cầu","G26"),v("Láng","G26"),v("Cầu Giấy","G26","Cũng là tên phố ở Đống Đa/Ba Đình; đồng thời là tên khu vực/phường"),
 ],
 "areas":[
  v("Cầu Giấy","G96","Tên quận cũ; từ 01/07/2025 là phường Cầu Giấy (phương án tên phường, G96 là dự kiến 18/4/2025; tổng 51 phường 75 xã theo G3). Vẫn dùng phổ biến",status="còn dùng phổ biến, nay là phường"),
  v("Hoàn Kiếm","G96","Tên quận cũ, giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Ba Đình","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Đống Đa","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Hai Bà Trưng","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Tây Hồ","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Thanh Xuân","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Hà Đông","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Long Biên","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Hoàng Mai","G96","Giữ làm tên phường (dự kiến)",status="còn dùng"),
  v("Từ Liêm","G96","Quận Bắc/Nam Từ Liêm cũ; phường 'Từ Liêm' và các phường Tây Mỗ, Đại Mỗ, Xuân Phương... (dự kiến)",status="còn dùng"),
  v("Mỹ Đình","G22","Tên khu vực quen gọi, không phải tên phường chính thức",status="tên khu vực quen gọi"),
  v("Trung Hòa - Nhân Chính","G22","Tên khu đô thị quen gọi",status="tên khu vực quen gọi"),
  v("Nội Bài","G33","Sân bay; thuộc huyện Sóc Sơn cũ",status="tên địa danh"),
  v("Sơn Tây","G30","Thị xã Sơn Tây cũ",status="tên địa danh"),
 ],
 "pois":[
  poi("Sân bay quốc tế Nội Bài","sân bay","G33"),
  poi("Ga Hà Nội","ga tàu","G30","Tên cũ ga Hàng Cỏ"),
  poi("Bến xe Mỹ Đình","bến xe","G77","20 Phạm Hùng; trang không có cập nhật hiện trạng"),
  poi("Bến xe Giáp Bát","bến xe","G77"),poi("Bến xe Gia Lâm","bến xe","G77"),
  poi("Bến xe Yên Nghĩa","bến xe","G77"),poi("Bến xe Nước Ngầm","bến xe","G77"),
  poi("Bệnh viện Bạch Mai","bệnh viện","G32"),poi("Bệnh viện Hữu Nghị","bệnh viện","G79"),
  poi("Bệnh viện Việt Đức","bệnh viện","G79"),poi("Bệnh viện K","bệnh viện","G79"),
  poi("Bệnh viện Nhi Trung ương","bệnh viện","G79"),poi("Bệnh viện E","bệnh viện","G79"),
  poi("Hồ Hoàn Kiếm","danh lam","G30"),poi("Hồ Tây","danh lam","G30"),
  poi("Văn Miếu - Quốc Tử Giám","danh lam","G30"),poi("Lăng Chủ tịch Hồ Chí Minh","danh lam","G30"),
  poi("Chùa Một Cột","danh lam","G30"),poi("Quảng trường Ba Đình","danh lam","G30"),
  poi("Nhà hát Lớn Hà Nội","danh lam","G30"),poi("Hoàng thành Thăng Long","danh lam","G30"),
  poi("Phố cổ Hà Nội","danh lam","G30"),
  poi("Cầu Long Biên","cầu","G30"),poi("Cầu Nhật Tân","cầu","G30"),poi("Cầu Thăng Long","cầu","G30"),
  poi("Cầu Chương Dương","cầu","G30"),poi("Cầu Vĩnh Tuy","cầu","G30"),poi("Cầu Thanh Trì","cầu","G30"),
  poi("Hầm Kim Liên","hầm","G20","Hầm chui >600 m, điểm kẹt xe hay được nhắc"),
  poi("Sân vận động Quốc gia Mỹ Đình","thể thao","G30"),
  poi("Lotte Center Hà Nội","trung tâm thương mại","G30"),
  poi("Aeon Mall Long Biên","trung tâm thương mại","G34","Chỉ liệt kê tên; thành phố suy từ tên"),
  poi("Aeon Mall Hà Đông","trung tâm thương mại","G34","Chỉ liệt kê tên; thành phố suy từ tên"),
  poi("Vincom Center Bà Triệu","trung tâm thương mại","G34","Chỉ liệt kê tên; thành phố suy từ tên"),
  poi("Vincom Mega Mall Royal City","trung tâm thương mại","G34"),
  poi("Vincom Mega Mall Times City","trung tâm thương mại","G34"),
  poi("Đại học Quốc gia Hà Nội","đại học","G30"),
  poi("Đại học Bách khoa Hà Nội","đại học","G30","Tên trong G30: Hanoi University of Science and Technology"),
  poi("Đại học Ngoại thương","đại học","G31"),poi("Đại học Y Hà Nội","đại học","G31"),
  poi("Đại học Xây dựng Hà Nội","đại học","G31"),poi("Đại học Giao thông Vận tải","đại học","G31"),
  poi("Học viện Ngân hàng","đại học","G31"),poi("Học viện Tài chính","đại học","G31"),
  poi("Metro Cát Linh - Hà Đông (tuyến 2A)","metro","G82"),poi("Metro Nhổn - ga Hà Nội (tuyến 3)","metro","G82","Đoạn trên cao khai thác từ 08/2024; đoạn ngầm chưa xong"),
 ]}

# ===================== TP HỒ CHÍ MINH =====================
C["TP Hồ Chí Minh"] = {
 "region":"Nam",
 "streets":[
  v("Nguyễn Huệ","G41"),v("Lê Lợi","G41"),v("Đồng Khởi","G41"),v("Nam Kỳ Khởi Nghĩa","G41"),
  v("Cách Mạng Tháng Tám","G41","Bảng ghi 'Cách Mạng Tháng 8'"),v("Điện Biên Phủ","G41"),v("Lê Duẩn","G41"),
  v("Hai Bà Trưng","G41"),v("Nguyễn Thị Minh Khai","G41"),v("Bùi Viện","G41"),v("Hàm Nghi","G41"),
  v("Lý Tự Trọng","G41"),v("Pasteur","G44"),v("Võ Văn Tần","G44"),v("Võ Thị Sáu","G44"),
  v("Hoàng Sa","G44"),v("Trường Sa","G44"),v("Hoàng Văn Thụ","G45"),v("Phan Đăng Lưu","G45"),
  v("Phan Xích Long","G45"),v("Nguyễn Kiệm","G45"),v("Cộng Hòa","G43"),v("Hoàng Hoa Thám","G42"),
  v("Bạch Đằng","G42"),v("Nguyễn Văn Trỗi","G45"),v("Phan Đình Phùng","G45"),v("Nguyễn Đình Chiểu","G44"),
  v("Lê Văn Sỹ","G44"),v("Phạm Ngọc Thạch","G44"),v("Trương Định","G44"),v("Phạm Ngũ Lão","G35"),
  v("Võ Văn Kiệt","G18"),v("Nguyễn Văn Linh","G18"),v("Phạm Văn Đồng","G18"),
  v("Xa lộ Hà Nội","G18","Tên báo chí 2025 vẫn dùng; chưa kiểm tra tên chính thức hiện hành"),
  v("Quốc lộ 13","G18"),v("Hoàng Quốc Việt","G46"),
 ],
 "areas":[
  v("Thủ Đức","G95","Từ 01/07/2025 là phường Thủ Đức (trước là TP Thủ Đức); vẫn dùng phổ biến",status="còn dùng phổ biến"),
  v("Sài Gòn","G95","Phường Sài Gòn (gồm Bến Nghé, một phần Đa Kao, Nguyễn Thái Bình - tức trung tâm Quận 1 cũ)",status="phường mới"),
  v("Bến Thành","G95","Phường Bến Thành (Quận 1 cũ)",status="phường mới"),
  v("Tân Định","G95","Phường Tân Định (Quận 1 cũ)",status="phường mới"),
  v("Quận 1","G95","Không còn là đơn vị hành chính cấp quận từ 01/07/2025 (G95 ghi 'Former Quận 1 -> 4 wards: Tân Định, Bến Thành, Sài Gòn, Cầu Ông Lãnh'); người dân vẫn gọi 'Quận 1'",status="tên cũ vẫn dùng khẩu ngữ"),
  v("Quận 3","G95","Cũ -> phường Bàn Cờ, Xuân Hòa, Nhiêu Lộc",status="tên cũ vẫn dùng khẩu ngữ"),
  v("Quận 7","G95","Cũ -> phường Tân Mỹ, Tân Hưng, Tân Thuận, Phú Thuận",status="tên cũ vẫn dùng khẩu ngữ"),
  v("Bình Thạnh","G95","Phường Bình Thạnh (cũ phường 12, 14, 26); các phường Gia Định, Bình Lợi Trung, Thạnh Mỹ Tây, Bình Quới",status="còn dùng"),
  v("Tân Bình","G95","Phường Tân Bình; các phường Tân Sơn Hòa, Tân Sơn Nhất, Tân Hòa, Bảy Hiền, Tân Sơn",status="còn dùng"),
  v("Gò Vấp","G95","Phường Gò Vấp; Hạnh Thông, An Nhơn, Thông Tây Hội, An Hội Tây, An Hội Đông",status="còn dùng"),
  v("Phú Nhuận","G95","Phường Phú Nhuận; Đức Nhuận, Cầu Kiệu",status="còn dùng"),
  v("Chợ Lớn","G35","Tên khu vực lịch sử",status="tên khu vực quen gọi"),
  v("Phú Mỹ Hưng","G35","Khu đô thị",status="tên khu vực quen gọi"),
  v("Thảo Điền","G34","Khu vực quen gọi",status="tên khu vực quen gọi"),
  v("Củ Chi","G35","Huyện cũ",status="tên cũ"),v("Hóc Môn","G35","Huyện cũ",status="tên cũ"),
  v("Bình Chánh","G35","Huyện cũ",status="tên cũ"),v("Nhà Bè","G35","Huyện cũ",status="tên cũ"),v("Cần Giờ","G35","Huyện cũ",status="tên cũ"),
  v("Côn Đảo","G33","Là đặc khu trực thuộc TP.HCM (G3 ghi HCM có 1 đặc khu; suy ra Côn Đảo, sân bay Côn Đảo thuộc HCM theo G33)",status="đặc khu"),
 ],
 "pois":[
  poi("Sân bay quốc tế Tân Sơn Nhất","sân bay","G33"),
  poi("Sân bay quốc tế Long Thành","sân bay","G35","Wikipedia ghi dự kiến mở 2026; thuộc Đồng Nai chứ không phải TP.HCM (G33); chưa xác minh đã khai thác"),
  poi("Ga Sài Gòn","ga tàu","G35"),
  poi("Bến xe Miền Đông mới","bến xe","G78","501 Hoàng Hữu Nam, mở 10/10/2020"),
  poi("Bến xe Miền Tây","bến xe","G78"),poi("Bến xe An Sương","bến xe","G78"),poi("Bến xe Ngã Tư Ga","bến xe","G78"),
  poi("Metro số 1 Bến Thành - Suối Tiên","metro","G81","Khai thác từ 22/12/2024; có 14 ga"),
  poi("Ga metro Bến Thành","metro","G81"),poi("Ga metro Nhà hát Thành phố","metro","G81"),
  poi("Bệnh viện Chợ Rẫy","bệnh viện","G32"),poi("Bệnh viện Răng Hàm Mặt Trung ương TP.HCM","bệnh viện","G79"),
  poi("Chợ Bến Thành","danh lam","G35"),poi("Dinh Độc Lập","danh lam","G35"),
  poi("Nhà thờ Đức Bà Sài Gòn","danh lam","G35"),poi("Bưu điện Trung tâm Sài Gòn","danh lam","G35"),
  poi("Nhà hát Thành phố","danh lam","G35"),poi("Bảo tàng Chứng tích Chiến tranh","danh lam","G35"),
  poi("Công viên Tao Đàn","danh lam","G35"),poi("Thảo Cầm Viên Sài Gòn","danh lam","G35"),
  poi("Tòa nhà Bitexco Financial Tower","tòa nhà","G35"),poi("Landmark 81","tòa nhà","G35"),
  poi("Phố đi bộ Nguyễn Huệ","danh lam","G35"),poi("Phố Tây Bùi Viện","danh lam","G35"),
  poi("Cầu Bình Triệu","cầu","G18"),poi("Cầu Phú Cường","cầu","G18"),poi("Nút giao An Phú","nút giao","G18"),
  poi("Cảng Cát Lái","cảng","G18"),
  poi("Vincom Center Landmark 81","trung tâm thương mại","G34"),poi("Vincom Center Đồng Khởi","trung tâm thương mại","G34"),
  poi("Saigon Centre - Takashimaya","trung tâm thương mại","G34"),poi("Diamond Plaza","trung tâm thương mại","G34"),
  poi("AEON Mall Tân Phú Celadon","trung tâm thương mại","G34"),poi("AEON Mall Bình Tân","trung tâm thương mại","G34"),
  poi("Vincom Mega Mall Thảo Điền","trung tâm thương mại","G34"),
  poi("Đại học Bách khoa TP.HCM","đại học","G35"),poi("Đại học Quốc gia TP.HCM","đại học","G35"),
  poi("Đại học Y Dược TP.HCM","đại học","G31"),poi("Đại học Luật TP.HCM","đại học","G31"),
  poi("Đại học Kinh tế TP.HCM","đại học","G31"),poi("Đại học Tôn Đức Thắng","đại học","G31"),
 ]}

# ===================== ĐÀ NẴNG =====================
C["Đà Nẵng"] = {
 "region":"Trung",
 "streets":[
  v("Bạch Đằng","G47"),v("Nguyễn Văn Linh","G47"),v("Trần Phú","G47"),v("Lê Duẩn","G47"),
  v("Hoàng Hoa Thám","G47"),v("Trần Hưng Đạo","G47"),v("2 Tháng 9","G47","Nguồn viết 'Đường 2/9'"),
  v("Phan Thanh","G47"),v("Võ Nguyên Giáp","G47"),v("Nguyễn Huy Chương","G47"),v("Phạm Văn Đồng","G47"),
  v("Võ Văn Kiệt","G47"),v("Nguyễn Du","G49"),v("Nguyễn Tất Thành","G51","Chỉ nhắc trong phần giới thiệu bài"),
  v("Điện Biên Phủ","G51","Chỉ nhắc trong phần giới thiệu bài"),v("Trường Chinh","G51","Nằm trong tên dự án khu dân cư"),
  v("Trần Cao Vân","G51","Nằm trong tên dự án khu dân cư"),v("Phan Bội Châu","G50","Nằm trong tên dự án TĐC"),
  v("Trần Quý Cáp","G50","Nằm trong tên dự án TĐC"),v("Lê Thanh Nghị","G50"),v("Thăng Long","G50"),
  v("Nguyễn Phi Khanh","G50"),v("Hồ Nghinh","G52"),v("Ngô Quang Huy","G52"),
  v("Nguyễn Sinh Sắc","G98"),v("Lê Doãn Nhạ","G98"),
  u("Hùng Vương"),u("Ông Ích Khiêm"),u("Quang Trung"),u("Hải Phòng"),u("Nguyễn Chí Thanh"),
 ],
 "areas":[
  v("Hải Châu","G36","Quận cũ; hiện là phường Hải Châu (Đà Nẵng có 23 phường, G3; tên phường cụ thể chưa xác minh từ nguồn đọc được)",status="tên cũ/còn dùng phổ biến"),
  v("Sơn Trà","G36","Quận cũ, cũng là bán đảo/núi Sơn Trà",status="còn dùng"),
  v("Ngũ Hành Sơn","G36","Quận cũ, cũng là danh thắng",status="còn dùng"),
  v("Liên Chiểu","G36","Quận cũ",status="tên cũ"),v("Thanh Khê","G36","Quận cũ",status="tên cũ"),
  v("Điện Bàn","G36","Thị xã thuộc Quảng Nam cũ, nay trong Đà Nẵng",status="tên cũ"),
  v("Hội An","G91","Du lịch; thuộc Quảng Nam cũ nay nằm trong Đà Nẵng (suy ra từ G1)",status="còn dùng"),
 ],
 "pois":[
  poi("Sân bay quốc tế Đà Nẵng","sân bay","G33"),poi("Sân bay Chu Lai","sân bay","G33","Nội địa; Quảng Nam cũ, nay trong Đà Nẵng (suy ra)"),
  poi("Cầu Rồng","cầu","G36"),poi("Cầu Sông Hàn","cầu","G36"),poi("Cầu Trần Thị Lý","cầu","G36"),
  poi("Cầu Thuận Phước","cầu","G36"),poi("Cầu Vàng","cầu","G36"),poi("Hầm Hải Vân","hầm","G16"),
  poi("Bà Nà Hills","danh lam","G36"),poi("Ngũ Hành Sơn","danh lam","G36"),poi("Bán đảo Sơn Trà","danh lam","G36"),
  poi("Biển Mỹ Khê","danh lam","G36"),poi("Chợ Hàn","chợ","G36"),poi("Chợ Cồn","chợ","G36"),
  poi("Bệnh viện C Đà Nẵng","bệnh viện","G79"),poi("Bệnh viện Đà Nẵng","bệnh viện","G36"),
  poi("Bệnh viện Hoàn Mỹ Đà Nẵng","bệnh viện","G36"),
  poi("Đại học Đà Nẵng","đại học","G36"),poi("Đại học Duy Tân","đại học","G36"),
  poi("Đại học Bách khoa - Đại học Đà Nẵng","đại học","G36"),poi("Đại học Kinh tế - Đại học Đà Nẵng","đại học","G36"),
  poi("Đại học Sư phạm - Đại học Đà Nẵng","đại học","G36"),poi("Đại học Ngoại ngữ - Đại học Đà Nẵng","đại học","G36"),
  poi("Đại học Kiến trúc Đà Nẵng","đại học","G31"),
  poi("Ga Đà Nẵng","ga tàu",None,"G36 chỉ nói Đà Nẵng là ga trên tuyến Bắc-Nam, không nêu tên ga"),
  poi("Vincom Plaza Ngô Quyền","trung tâm thương mại","G34","Tên có trong danh sách nhưng không nêu thành phố; suy luận Đà Nẵng chưa xác nhận"),
 ]}

# ===================== HUẾ =====================
C["Huế"] = {
 "region":"Trung",
 "streets":[v(n,"G40") for n in [
  "Lê Lợi","Hùng Vương","Nguyễn Huệ","Hà Nội","Trần Hưng Đạo","Phạm Văn Đồng","Điện Biên Phủ","Bến Nghé",
  "Nguyễn Sinh Cung","Lê Duẩn","Phan Bội Châu","Hai Bà Trưng","Trần Phú","Nguyễn Văn Cừ","Đống Đa",
  "Bạch Đằng","Nguyễn Chí Thanh","Tố Hữu","Nguyễn Công Trứ","Phan Đình Phùng","Lý Thường Kiệt","Nguyễn Trãi",
  "Ngô Quyền","Chi Lăng","Kim Long","Võ Thị Sáu","Phạm Ngũ Lão","Chu Văn An","Võ Nguyên Giáp","Trường Chinh",
  "Nguyễn Thái Học","Xuân Diệu","Hoàng Diệu","Nguyễn Tri Phương"]],
 "streets_note":"Huế có phố tên 'Hà Nội' (đường Hà Nội, Huế) - dễ nhầm với thành phố Hà Nội; 'Bến Nghé' ở Huế không phải Bến Nghé (Sài Gòn).",
 "areas":[
  v("Phú Xuân","G37","Wikipedia ghi 'Phú Xuân district / Thuận Hóa district (urban districts, 2025)'; sau 07/2025 Huế chỉ còn xã phường (40 đơn vị, 21 phường theo G3) - tên phường cụ thể chưa xác minh",status="chưa rõ tình trạng"),
  v("Thuận Hóa","G37","Xem ghi chú Phú Xuân",status="chưa rõ tình trạng"),
  v("Kim Long","G37","Khu vực nổi tiếng",status="tên khu vực quen gọi"),
  v("Thuận An","G37","Cảng/cửa biển",status="tên địa danh"),v("Lăng Cô","G37","Thị trấn/vịnh",status="tên địa danh"),
  v("Hương Thủy","G37","Thị xã cũ",status="tên cũ"),v("Hương Trà","G37","Thị xã cũ",status="tên cũ"),
 ],
 "pois":[
  poi("Sân bay quốc tế Phú Bài","sân bay","G33"),poi("Ga Huế","ga tàu","G37"),
  poi("Đại Nội Huế (Hoàng thành Huế)","danh lam","G37"),poi("Chùa Thiên Mụ","danh lam","G37"),
  poi("Lăng Khải Định","danh lam","G37"),poi("Lăng Tự Đức","danh lam","G37"),poi("Lăng Minh Mạng","danh lam","G37"),
  poi("Cầu Trường Tiền","cầu","G37"),poi("Sông Hương","danh lam","G37"),poi("Vườn quốc gia Bạch Mã","danh lam","G37"),
  poi("Cảng Chân Mây","cảng","G37"),poi("Cảng Thuận An","cảng","G37"),
  poi("Bệnh viện Trung ương Huế","bệnh viện","G37"),poi("Đại học Huế","đại học","G37"),
  poi("Đại học Y Dược Huế","đại học","G37"),poi("Đại học Khoa học Huế","đại học","G37"),
  poi("Đại học Sư phạm Huế","đại học","G37"),poi("Học viện Âm nhạc Huế","đại học","G31"),
  poi("Trường Quốc Học Huế","trường học","G37"),
  poi("Hầm Hải Vân","hầm","G16","Giữa Huế và Đà Nẵng"),poi("Đèo Phước Tượng","đèo","G14"),poi("Đèo Phú Gia","đèo","G14"),
 ]}

# ===================== HẢI PHÒNG =====================
C["Hải Phòng"] = {
 "region":"Bắc",
 "streets":[
  v("Tô Hiệu","G53"),v("Nguyễn Đức Cảnh","G53"),v("Hai Bà Trưng","G53"),v("Tôn Đức Thắng","G53"),
  v("Trần Nguyên Hãn","G53"),v("Nguyễn Công Trứ","G53"),v("Nguyễn Văn Linh","G53"),v("Võ Nguyên Giáp","G53"),
  v("Lam Sơn","G53"),v("Hàng Kênh","G53"),v("Quang Trung","G54"),v("Hoàng Văn Thụ","G54"),
  v("Điện Biên Phủ","G54"),v("Trần Hưng Đạo","G54"),v("Phan Bội Châu","G54"),v("Lý Tự Trọng","G54"),
  v("Hoàng Diệu","G54"),v("Phạm Hồng Thái","G54"),v("Bạch Đằng","G54"),v("Hùng Vương","G54"),
  v("Minh Khai","G54"),v("Lê Đại Hành","G54"),v("Tôn Đản","G54"),v("Nguyễn Tri Phương","G54"),
  v("Hồ Xuân Hương","G54"),v("Nguyễn Thượng Hiền","G54"),v("Tam Bạc","G54","Có thể là tên khu/phố"),
  v("Hà Nội","G54","Đường Hà Nội ở Hải Phòng - dễ nhầm với thành phố Hà Nội"),
  v("Cầu Bính","G54","Đường Cầu Bính (liên quan cầu Bính, G38)"),
  u("Lạch Tray"),u("Lê Hồng Phong"),u("Cầu Rào","Chỉ thấy tiêu đề kết quả tìm kiếm (mia.vn/thanh tra); chưa đọc"),
 ],
 "areas":[
  v("Hồng Bàng","G38","Quận cũ; trước sáp nhập 2025 là quận. Hải Phòng nay có 45 phường 67 xã 2 đặc khu (G3); tên phường cụ thể chưa xác minh",status="tên cũ/còn dùng"),
  v("Lê Chân","G38","Quận cũ",status="tên cũ/còn dùng"),u("Ngô Quyền","Quận cũ của Hải Phòng; G38 không nhắc, G34 chỉ có tên Vincom Plaza Ngô Quyền",status="tên cũ"),
  v("Kiến An","G38","Quận cũ",status="tên cũ"),v("Thủy Nguyên","G38","Huyện/thành phố cũ",status="tên cũ"),
  v("Đồ Sơn","G38","Bãi biển/khu du lịch",status="tên địa danh"),v("Cát Bà","G38","Đảo/du lịch",status="tên địa danh"),
  v("Bạch Long Vĩ","G38","Đảo/đặc khu (G3 ghi Hải Phòng có 2 đặc khu)",status="tên địa danh"),
  v("Hải Dương","G1","Tỉnh cũ nay thuộc Hải Phòng (sáp nhập)",status="tên cũ vẫn dùng"),
 ],
 "pois":[
  poi("Sân bay quốc tế Cát Bi","sân bay","G33"),poi("Cảng Hải Phòng","cảng","G38"),
  poi("Cầu Bính","cầu","G38"),poi("Nhà hát Lớn Hải Phòng","danh lam","G38"),poi("Nhà thờ lớn Hải Phòng","danh lam","G38"),
  poi("Bưu điện Hải Phòng","danh lam","G38"),poi("Bãi biển Đồ Sơn","danh lam","G38"),poi("Đảo Cát Bà","danh lam","G38"),
  poi("Đại học Hàng hải Việt Nam","đại học","G31"),poi("Đại học Y Dược Hải Phòng","đại học","G31"),poi("Đại học Hải Phòng","đại học","G31"),
  poi("Vincom Imperia Hải Phòng","trung tâm thương mại","G34","Chỉ liệt kê tên"),
  poi("Aeon Mall Hải Phòng Lê Chân","trung tâm thương mại","G34","Chỉ liệt kê tên"),
  poi("Bệnh viện Việt Tiệp","bệnh viện",None,"Chưa xác minh trong nguồn đọc được"),
  poi("Cầu Tân Vũ - Lạch Huyện","cầu",None,"G38 không nhắc"),
  poi("Ga Hải Phòng","ga tàu",None,"G38 không nêu ga"),
 ]}

# ===================== CẦN THƠ =====================
C["Cần Thơ"] = {
 "region":"Nam",
 "streets":[v(n,"G55") for n in [
  "Hai Bà Trưng","Hùng Vương","3 Tháng 2","30 Tháng 4","Mậu Thân","Hòa Bình","Nam Kỳ Khởi Nghĩa",
  "Châu Văn Liêm","Cách Mạng Tháng Tám","Đồng Khởi","Điện Biên Phủ","Lý Tự Trọng","Ngô Quyền","Lê Lợi",
  "Lê Lai","Lê Thánh Tôn","Hoàng Văn Thụ","Huỳnh Thúc Kháng","Nguyễn An Ninh","Nguyễn Bỉnh Khiêm",
  "Nguyễn Du","Nguyễn Đình Chiểu","Nguyễn Cư Trinh","Lý Thường Kiệt","Đinh Tiên Hoàng","Cao Thắng",
  "Bùi Thị Xuân","Hồ Xuân Hương","Ngô Gia Tự","Mạc Đĩnh Chi","Hậu Giang"]] + [
  u("Nguyễn Văn Cừ","Có trong G55 chỉ như điểm đầu/cuối đoạn đường (không phải mục chính)"),
  u("Võ Văn Kiệt"),u("Nguyễn Văn Linh"),u("Trần Hưng Đạo")],
 "areas":[
  v("Ninh Kiều","G39","Quận cũ; Cần Thơ nay có 31 phường 72 xã (G3) sau khi gộp Sóc Trăng, Hậu Giang",status="tên cũ/còn dùng"),
  v("Cái Răng","G39","Quận cũ; chợ nổi Cái Răng",status="tên cũ/còn dùng"),
  v("Bình Thủy","G39","Quận cũ",status="tên cũ"),v("Ô Môn","G39","Quận cũ",status="tên cũ"),v("Thốt Nốt","G39","Quận cũ",status="tên cũ"),
  v("Phong Điền","G39","Huyện cũ; chợ nổi Phong Điền",status="tên cũ"),
  v("Sóc Trăng","G1","Tỉnh cũ nay thuộc Cần Thơ",status="tên cũ vẫn dùng"),v("Hậu Giang","G1","Tỉnh cũ nay thuộc Cần Thơ",status="tên cũ vẫn dùng"),
 ],
 "pois":[
  poi("Sân bay quốc tế Cần Thơ","sân bay","G33"),poi("Cầu Cần Thơ","cầu","G39"),poi("Cầu đi bộ Cần Thơ","cầu","G39"),
  poi("Bến Ninh Kiều","danh lam","G39"),poi("Chợ nổi Cái Răng","danh lam","G39"),poi("Chợ nổi Phong Điền","danh lam","G39"),
  poi("Chợ đêm Tây Đô","chợ","G39"),poi("Công viên Lưu Hữu Phước","danh lam","G39"),poi("Bảo tàng Cần Thơ","danh lam","G39"),
  poi("Chùa Ông","danh lam","G39"),poi("Thiền viện Trúc Lâm Phương Nam","danh lam","G39"),poi("Nhà thờ Cần Thơ (Cần Thơ Cathedral)","danh lam","G39"),
  poi("Bệnh viện Đa khoa Trung ương Cần Thơ","bệnh viện","G79"),
  poi("Đại học Cần Thơ","đại học","G31"),poi("Đại học Y Dược Cần Thơ","đại học","G31"),
  poi("Đại học Tây Đô","đại học","G39"),poi("Đại học Nam Cần Thơ","đại học","G31"),
  poi("GO! Cần Thơ","trung tâm thương mại","G89","Big C Cần Thơ đổi thương hiệu 2021"),
 ]}

# ===================== NHA TRANG =====================
C["Nha Trang"] = {
 "region":"Trung","province_now":"Khánh Hòa",
 "streets":[
  v("Trần Phú","G67"),v("Thái Nguyên","G67"),v("Lê Thánh Tôn","G67"),v("Nguyễn Tất Thành","G66","Đại lộ Nguyễn Tất Thành"),
  v("Võ Nguyên Giáp","G68","Đại lộ Nha Trang - Diên Khánh, ~10 km"),v("Điện Biên Phủ","G56"),v("2 Tháng 4","G56","Nguồn viết 'Đường 2/4'; quảng trường 2 tháng 4 ở G66"),
  v("An Dương Vương","G56"),v("Âu Cơ","G56"),v("Bạch Đằng","G56"),v("Bà Triệu","G56"),v("Cao Thắng","G56"),
  v("Chu Văn An","G56"),v("Đinh Tiên Hoàng","G56"),v("Đống Đa","G56"),v("Cù Chính Lan","G56"),v("Châu Văn Liêm","G56"),
  v("Chi Lăng","G56"),v("Bế Văn Đàn","G56"),v("Bùi Thị Xuân","G56"),v("Cao Bá Quát","G56"),v("Chương Dương","G56"),
  u("Phạm Văn Đồng"),u("Yersin"),u("Hùng Vương"),u("Nguyễn Thị Minh Khai"),u("Lê Hồng Phong"),
 ],
 "areas":[
  v("Cam Ranh","G33","Sân bay quốc tế Cam Ranh; Khánh Hòa",status="tên địa danh"),
  v("Diên Khánh","G68","Huyện cũ",status="tên cũ"),v("Khánh Vĩnh","G17","Huyện cũ có đèo Khánh Lê",status="tên cũ"),
  v("Phan Rang - Tháp Chàm","G1","Ninh Thuận cũ nay thuộc Khánh Hòa (suy ra từ G1)",status="tên cũ vẫn dùng"),
 ],
 "pois":[
  poi("Sân bay quốc tế Cam Ranh","sân bay","G33"),poi("Ga Nha Trang","ga tàu","G69"),
  poi("Tháp Bà Ponagar","danh lam","G69"),poi("Hòn Chồng","danh lam","G69"),poi("Chùa Long Sơn","danh lam","G69"),
  poi("Nhà thờ Núi Nha Trang","danh lam","G67"),poi("Tháp Trầm Hương","danh lam","G69"),poi("Vinpearl Nha Trang (cáp treo, Vinpearl Land)","danh lam","G69"),
  poi("Viện Hải dương học Nha Trang","danh lam","G67"),poi("Bảo tàng Yersin","danh lam","G67"),poi("Viện Pasteur Nha Trang","danh lam","G67"),
  poi("Chợ Đầm","chợ","G56"),poi("Chợ đêm Nha Trang","chợ","G67"),poi("Quảng trường 2 tháng 4","danh lam","G66"),
  poi("Vòng xoay Ngã 6 Nha Trang","nút giao","G67"),
  poi("Đại học Nha Trang","đại học","G31"),poi("Đại học Khánh Hòa","đại học","G31"),
  poi("GO! Nha Trang","trung tâm thương mại","G89","Big C Nha Trang đổi tên 03/2021"),
  poi("Đèo Khánh Lê","đèo","G17","QL27C Nha Trang - Đà Lạt"),
  poi("Bệnh viện Đa khoa tỉnh Khánh Hòa","bệnh viện",None,"Chưa xác minh trong nguồn"),
  poi("Bến xe phía Nam Nha Trang","bến xe",None,"Chưa xác minh trong nguồn"),
 ]}

# ===================== VINH =====================
C["Vinh"] = {
 "region":"Trung","province_now":"Nghệ An",
 "streets":[
  v("Lê Nin","G62","Nguồn viết 'Đại lộ Lê Nin' (Lenin Avenue ở G70); cũng gặp 'Lê-nin'"),
  v("Phan Bội Châu","G62"),v("Quang Trung","G63"),v("Nguyễn Thị Minh Khai","G63"),v("Đặng Thái Thân","G63"),
  v("Đinh Công Tráng","G63"),v("Lê Ninh","G63","Nguồn ghi 'Lệ Ninh'/'Lê Ninh' (G63, báo Đầu tư 'đường Lê Ninh'); chính tả chuẩn cần kiểm tra"),
  v("Hồng Bàng","G62"),v("Phong Định Cảng","G63"),v("Đào Tấn","G70"),v("Lê Hồng Phong","G70"),
  v("Xuân Thủy","G61"),v("Nguyễn Lương Bằng","G61"),v("Nguyễn Thị Định","G61"),v("Trần Khánh Dư","G61"),
  v("Kim Liên","G61"),v("Lý Thái Tổ","G61"),v("Trần Đăng Ninh","G61"),v("Nam Cao","G61"),v("Hoàng Xuân Hãn","G61"),
  v("Trương Hán Siêu","G61"),v("Tô Ngọc Vân","G61"),v("Đặng Văn Ngữ","G61"),v("Nguyễn Minh Châu","G61"),
  v("Nguyễn Trường Tộ","G57"),v("Trần Bình Trọng","G57"),
  u("Lê Lợi"),u("Lê Mao"),u("Nguyễn Sỹ Sách"),u("Trường Thi"),u("Hồ Tùng Mậu"),
 ],
 "areas":[
  v("Cửa Lò","G70","Thị xã/bãi biển",status="tên địa danh"),v("Cửa Hội","G70","Khu nghỉ dưỡng",status="tên địa danh"),
  v("Vinh Tân","G70","Phường (vị trí Bến xe Trung tâm); trạng thái sau 2025 chưa xác minh",status="chưa rõ"),
  v("Kim Liên","G70","Xã quê Bác Hồ (Nam Đàn cũ)",status="tên địa danh"),
 ],
 "pois":[
  poi("Sân bay quốc tế Vinh","sân bay","G33"),poi("Ga Vinh","ga tàu","G70"),
  poi("Quảng trường Hồ Chí Minh","danh lam","G70"),poi("Thành cổ Vinh (Phượng Hoàng Trung Đô)","danh lam","G70"),
  poi("Núi Dũng Quyết","danh lam","G70"),poi("Bảo tàng Xô Viết Nghệ Tĩnh","danh lam","G70"),poi("Bảo tàng Nghệ An","danh lam","G70"),
  poi("Bãi biển Cửa Lò","danh lam","G70"),poi("Cảng Cửa Lò","cảng","G70"),
  poi("Bến xe Trung tâm Vinh","bến xe","G70","G70: KM 20 Vinh Road, Block 2, Vinh Tân ward; địa chỉ chưa kiểm chứng thêm"),
  poi("Bến xe chợ Vinh","bến xe","G70"),poi("Bến xe phía Bắc Vinh","bến xe","G70"),
  poi("Sân vận động Vinh","thể thao","G70"),
  poi("Đại học Vinh","đại học","G31"),poi("Đại học Sư phạm Kỹ thuật Vinh","đại học","G31"),
  poi("Đại học Y khoa Vinh","đại học","G31"),poi("Đại học Kinh tế Nghệ An","đại học","G31"),
  poi("Đại học Công nghiệp Vinh","đại học","G31"),
  poi("City Hub (Galaxy Cinema)","trung tâm thương mại","G70","Không có TTTM lớn được nêu tên trong G70"),
  poi("Bệnh viện Hữu nghị Đa khoa Nghệ An","bệnh viện",None,"Chỉ thấy tiêu đề tìm kiếm (G104) - chưa đọc nội dung"),
 ]}

# ===================== ĐÀ LẠT =====================
C["Đà Lạt"] = {
 "region":"Trung","province_now":"Lâm Đồng",
 "streets":[v(n,"G59","Quyết định 298/2015 - tuyến đường chính") for n in [
  "Ba Tháng Hai","Ba Tháng Tư","Đinh Tiên Hoàng","Hồ Tùng Mậu","Hùng Vương","Hồ Xuân Hương","Nguyên Tử Lực",
  "Nguyễn Đình Chiểu","Nguyễn Văn Cừ","Phan Chu Trinh","Phan Đình Phùng","Phù Đổng Thiên Vương","Quang Trung",
  "Trần Hưng Đạo","Trần Nhân Tông","Trần Phú","Trần Quốc Toản","Trần Quý Cáp","Xô Viết Nghệ Tĩnh","Yersin",
  "Khe Sanh","Triệu Việt Vương","Lê Hồng Phong","Hoàng Văn Thụ","Trần Thánh Tông","Trúc Lâm","Mai Anh Đào"]] + [
  v("Nguyễn Thị Minh Khai","G58"),v("Bùi Thị Xuân","G58"),v("Lý Tự Trọng","G58"),v("Phan Bội Châu","G58"),
  v("Tăng Bạt Hổ","G58"),v("Nam Kỳ Khởi Nghĩa","G58")],
 "areas":[
  v("Khu Hòa Bình","G71","Khu trung tâm quanh Hòa Bình Hall",status="tên khu vực quen gọi"),
  v("Tà Nung","G58","Xã ngoại thành",status="tên địa danh"),
  v("Liên Khương","G33","Sân bay quốc tế Liên Khương (Đức Trọng)",status="tên địa danh"),
  v("Prenn","G59","Đèo Prenn",status="tên địa danh"),
  v("Phan Thiết","G33","Phan Thiet Airport; Bình Thuận cũ nay thuộc Lâm Đồng (G1)",status="tên cũ vẫn dùng"),
 ],
 "pois":[
  poi("Sân bay quốc tế Liên Khương","sân bay","G33"),poi("Ga Đà Lạt","ga tàu","G71"),
  poi("Hồ Xuân Hương","danh lam","G71"),poi("Chợ Đà Lạt","chợ","G71"),poi("Nhà thờ Chính tòa Đà Lạt","danh lam","G71","Tên quen gọi 'nhà thờ Con Gà' chưa có trong nguồn"),
  poi("Thiền viện Trúc Lâm Đà Lạt","danh lam","G71"),poi("Biệt thự Hằng Nga (Crazy House)","danh lam","G71"),
  poi("Dinh III (Dinh Bảo Đại)","danh lam","G71"),poi("Hòa Bình Hall","danh lam","G71"),
  poi("Đại học Đà Lạt","đại học","G31"),poi("Học viện Lục quân","đại học","G31"),poi("Viện Nghiên cứu hạt nhân Đà Lạt","viện","G71"),
  poi("Đèo Prenn","đèo","G59"),
  poi("Thung lũng Tình Yêu","danh lam",None),poi("Hồ Tuyền Lâm","danh lam",None),poi("Thác Datanla","danh lam",None),
  poi("Bệnh viện Đa khoa Lâm Đồng","bệnh viện",None),
 ]}

# ===================== QUY NHƠN =====================
C["Quy Nhơn"] = {
 "region":"Trung","province_now":"Gia Lai",
 "streets":[
  v("Nguyễn Tất Thành","G64"),v("Nguyễn Thiếp","G64"),v("Xuân Diệu","G64"),v("Lê Hồng Phong","G64"),
  v("Trần Hưng Đạo","G64"),v("An Dương Vương","G65"),v("Nguyễn Huệ","G65"),v("Trần Phú","G65"),
  v("Lê Đức Thọ","G65"),v("Ngô Văn Sở","G65"),
  v("Bạch Đằng","G74","Bảng giá đất trang TP Quy Nhơn, độ tin cậy trung bình"),
  v("Điện Biên Phủ","G74","độ tin cậy trung bình"),v("Diên Hồng","G74","độ tin cậy trung bình"),
  v("Đào Tấn","G74","độ tin cậy trung bình"),v("Bà Triệu","G74","độ tin cậy trung bình"),
  v("Chương Dương","G74","độ tin cậy trung bình"),v("Cần Vương","G74","độ tin cậy trung bình"),
  v("Chu Văn An","G74","độ tin cậy trung bình"),v("Cao Thắng","G74","độ tin cậy trung bình"),
  v("Bùi Thị Xuân","G74","độ tin cậy trung bình"),v("Bế Văn Đàn","G74","độ tin cậy trung bình"),
  u("Ngô Mây"),u("Hai Bà Trưng"),u("Phạm Hùng"),u("Tây Sơn"),
 ],
 "areas":[
  v("Ghềnh Ráng","G65","Danh thắng",status="tên địa danh"),v("Bãi Xép","G65","Bãi biển",status="tên địa danh"),
  v("Phương Mai","G65","Bán đảo",status="tên địa danh"),v("Phú Tài","G72","Khu công nghiệp",status="tên địa danh"),
  v("Nhơn Hội","G72","Khu kinh tế",status="tên địa danh"),v("Diêu Trì","G72","Ga Diêu Trì (Tuy Phước)",status="tên địa danh"),
  v("Bình Định","G1","Tỉnh cũ nay thuộc Gia Lai; người dùng vẫn gọi 'Bình Định'",status="tên cũ vẫn dùng"),
 ],
 "pois":[
  poi("Sân bay Phù Cát","sân bay","G33","Nội địa; Bình Định cũ"),poi("Ga Quy Nhơn","ga tàu","G72"),poi("Ga Diêu Trì","ga tàu","G72"),
  poi("Cảng Quy Nhơn","cảng","G72"),poi("Quảng trường Nguyễn Tất Thành","danh lam","G64"),
  poi("Tượng đài Quang Trung","danh lam","G64"),poi("Công viên biển Quy Nhơn","danh lam","G65"),
  poi("Cầu Thị Nại","cầu","G65"),poi("Chợ đêm Quy Nhơn","chợ","G65"),poi("Ghềnh Ráng Tiên Sa","danh lam","G65","Nguồn ghi 'Ghềnh Ráng' và 'Tiên Sa' riêng"),
  poi("Bãi Xép","danh lam","G65"),
  poi("Đại học Quy Nhơn","đại học","G31"),poi("Đại học Quang Trung","đại học","G72"),
  poi("Bệnh viện Phong - Da liễu Trung ương Quy Hòa","bệnh viện",None,"G79 chỉ liệt kê tên bệnh viện, không nêu thành phố"),
  poi("Eo Gió","danh lam",None),poi("Kỳ Co","danh lam",None),poi("Tháp Đôi","danh lam",None),
 ]}

# ===================== BUÔN MA THUỘT =====================
C["Buôn Ma Thuột"] = {
 "region":"Trung","province_now":"Đắk Lắk",
 "streets":[v(n,"G60","QĐ 773/1998; có thể đã đổi/thêm sau đó") for n in [
  "Phan Chu Trinh","Xô Viết Nghệ Tĩnh","Đinh Tiên Hoàng","Điện Biên Phủ","Đào Duy Từ","Hai Bà Trưng","Hùng Vương",
  "Y Jút","Lý Thường Kiệt","Lý Tự Trọng","Nguyễn Đức Cảnh","Nguyễn Trãi","Nguyễn Bỉnh Khiêm","Quang Trung",
  "Trần Phú","Phan Bội Châu","Nguyễn Văn Cừ","Nguyễn Thị Minh Khai","Lê Đại Hành","Ngô Gia Tự","Ngô Mây",
  "Nguyễn Du","Nguyễn Văn Trỗi","Phạm Hồng Thái","Phạm Ngũ Lão","Nơ Trang Long","Nguyễn Tất Thành","Lê Duẩn",
  "Trần Hưng Đạo","Ngô Quyền","Tôn Đức Thắng","Trường Chinh","Mai Hắc Đế","Hoàng Diệu","Y Wang"]] + [
  v("Y Ngông","G76"),v("Trần Nhật Duật","G76"),v("Nguyễn Hồng Ưng","G76"),v("Nguyễn Đình Chiểu","G76"),
  v("30 Tháng 4","G75"),v("10 Tháng 3","G75","Có trong bảng giá đất; QĐ 773/1998 ghi 'Mai Hắc Đế' thay '10 tháng 3' - tên có thể đã đổi"),
  v("Đồng Khởi","G75"),
 ],
 "areas":[
  v("Ngã 6 Ban Mê","G73","Tượng đài Chiến thắng Buôn Ma Thuột",status="tên khu vực quen gọi"),
  v("Bản Đôn","G73","Điểm du lịch (Buôn Đôn)",status="tên địa danh"),
  v("Phú Yên","G1","Tỉnh cũ (Tuy Hòa) nay thuộc Đắk Lắk",status="tên cũ vẫn dùng"),
  u("Thắng Lợi","Chỉ thấy trong tiêu đề kết quả tìm kiếm guland (phường BMT sau sáp nhập), chưa đọc",status="chưa rõ"),
  u("Tân Thành","Chỉ thấy trong tiêu đề kết quả tìm kiếm guland, chưa đọc",status="chưa rõ"),
  u("Thành Nhất","Chỉ thấy trong tiêu đề kết quả tìm kiếm guland, chưa đọc",status="chưa rõ"),
 ],
 "pois":[
  poi("Sân bay Buôn Ma Thuột","sân bay","G33"),poi("Tượng đài Chiến thắng Buôn Ma Thuột","danh lam","G73"),
  poi("Bảo tàng Thế giới Cà phê","danh lam","G73"),poi("Làng cà phê Trung Nguyên","danh lam","G73"),
  poi("Biệt điện Bảo Đại (Bảo tàng Dân tộc Đắk Lắk)","danh lam","G73"),poi("Buôn Akô Đhông","danh lam","G73"),
  poi("Bản Đôn (Buôn Đôn)","danh lam","G73"),poi("Chùa Sắc tứ Khải Đoan","danh lam","G73"),
  poi("Hồ Ea Kao","danh lam","G73"),poi("Thác Dray Nur","danh lam","G73"),poi("Thác Dray Sáp","danh lam","G73"),
  poi("Công viên Nguyễn Tất Thành (Buôn Ma Thuột)","danh lam","G76"),
  poi("Đại học Tây Nguyên","đại học","G31"),poi("Đại học Y khoa Buôn Ma Thuột","đại học","G31","Tên trong danh sách"),
  poi("Vincom Plaza Buôn Ma Thuột","trung tâm thương mại","G34","Chỉ liệt kê tên"),
  poi("Đèo Hà Lan","đèo",None,"Chỉ thấy là điểm trạm phát sóng ở G5 (Đèo Hà Lan, Đắk Lắk)"),
  poi("Bệnh viện Đa khoa Vùng Tây Nguyên","bệnh viện",None),
 ]}
