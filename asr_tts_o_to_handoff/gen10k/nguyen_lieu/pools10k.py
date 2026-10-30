# -*- coding: utf-8 -*-
"""Kho giá trị khe. Mỗi kho ghi nguồn trong POOL_SOURCES (mã nguồn xem README_nguon.md).
K1 = kiến thức nền của mô hình (phiên trước hoặc phiên này), chưa đối chiếu nguồn đọc được.
"""
import json, os

from cauhinh.duong_dan import ROOT

SRC_DIR = os.path.join(ROOT, "sources")

POOL_SOURCES = {}


def src(name, desc):
    POOL_SOURCES[name] = desc


def load_json(name):
    with open(os.path.join(SRC_DIR, name), encoding="utf-8") as f:
        return json.load(f)


LANG = load_json("src_lang.json")
CMDS = load_json("src_commands.json")

# ------------------------------------------------------------------ hành chính
_TINH = load_json("tinh_tp.json")
_QH = load_json("quan_huyen.json")
NORTH = {"01", "02", "04", "06", "08", "10", "11", "12", "14", "15", "17", "19", "20", "22", "24", "25", "26", "27", "30",
         "31", "33", "34", "35", "36", "37"}
CENTRAL = {"38", "40", "42", "44", "45", "46", "48", "49", "51", "52", "54", "56", "58", "60", "62", "64", "66", "67", "68"}


def region_of(code):
    return "Bắc" if code in NORTH else ("Trung" if code in CENTRAL else "Nam")


TYPE_WORD = {"quan": "quận", "huyen": "huyện", "thi-xa": "thị xã", "thanh-pho": "thành phố"}
# chỉ lấy quận/huyện của các thành phố lớn, nơi người lái hay nói tên quận
DIST_CITY = {"01": "Hà Nội", "79": "Sài Gòn", "48": "Đà Nẵng", "31": "Hải Phòng", "92": "Cần Thơ", "46": "Huế"}
DISTRICTS = []
for code, v in _QH.items():
    pc = v["parent_code"]
    if pc in DIST_CITY:
        DISTRICTS.append(dict(type=TYPE_WORD[v["type"]], name=v["name"], city=DIST_CITY[pc], region=region_of(pc)))
src("districts", "sources/quan_huyen.json (GitHub madnh/hanhchinhvn, dữ liệu trước sắp xếp 2025): quận/huyện của 6 thành phố "
    "trực thuộc trung ương. Từ 1/7/2025 cấp huyện không còn là đơn vị hành chính (K1, chưa đối chiếu văn bản trong thư mục này); "
    "tên quận vẫn dùng trong khẩu ngữ nên giữ, mỗi câu có cờ admin_name_pre2025.")

# thành phố, địa danh lớn hay được nhắc khi đi đường dài (tên gọi, không phải tên đơn vị hành chính)
CITIES = [
    ("Hà Nội", "Bắc"), ("Hải Phòng", "Bắc"), ("Hạ Long", "Bắc"), ("Bắc Ninh", "Bắc"), ("Hải Dương", "Bắc"), ("Thái Nguyên", "Bắc"),
    ("Nam Định", "Bắc"), ("Ninh Bình", "Bắc"), ("Lào Cai", "Bắc"), ("Sa Pa", "Bắc"), ("Vĩnh Yên", "Bắc"), ("Hưng Yên", "Bắc"),
    ("Thanh Hóa", "Trung"), ("Vinh", "Trung"), ("Hà Tĩnh", "Trung"), ("Đồng Hới", "Trung"), ("Huế", "Trung"), ("Đà Nẵng", "Trung"),
    ("Hội An", "Trung"), ("Quảng Ngãi", "Trung"), ("Quy Nhơn", "Trung"), ("Tuy Hòa", "Trung"), ("Nha Trang", "Trung"),
    ("Đà Lạt", "Trung"), ("Buôn Ma Thuột", "Trung"), ("Pleiku", "Trung"), ("Kon Tum", "Trung"), ("Đông Hà", "Trung"),
    ("Phan Thiết", "Nam"), ("Sài Gòn", "Nam"), ("Biên Hòa", "Nam"), ("Vũng Tàu", "Nam"), ("Thủ Dầu Một", "Nam"), ("Tây Ninh", "Nam"),
    ("Mỹ Tho", "Nam"), ("Cần Thơ", "Nam"), ("Long Xuyên", "Nam"), ("Rạch Giá", "Nam"), ("Cà Mau", "Nam"), ("Bạc Liêu", "Nam"),
    ("Sóc Trăng", "Nam"), ("Vĩnh Long", "Nam"), ("Trà Vinh", "Nam"), ("Bến Tre", "Nam"), ("Phú Quốc", "Nam"), ("Châu Đốc", "Nam"),
]
src("cities", "generator/pools.py (phiên trước, K1) và bổ sung K1: tên thành phố/địa danh thường nói; đối chiếu một phần với sources/tinh_tp.json.")

# ------------------------------------------------------------------ đường theo thành phố
# (vùng, từ chỉ ngõ/hẻm, [đường], [mã quận huyện để ghép])
STREETS = {
    "Hà Nội": ("Bắc", "ngõ", [
        "phố Chùa Bộc", "đường Giải Phóng", "đường Láng", "đường Nguyễn Trãi", "đường Trần Duy Hưng", "đường Phạm Văn Đồng",
        "phố Lê Duẩn", "phố Kim Mã", "đường Hoàng Quốc Việt", "đường Xuân Thủy", "phố Cầu Giấy", "phố Tây Sơn", "phố Thái Hà",
        "đường Lạc Long Quân", "phố Nguyễn Chí Thanh", "đường Trường Chinh", "phố Minh Khai", "phố Bạch Mai", "phố Đại Cồ Việt",
        "phố Hàng Bông", "phố Huế", "phố Trần Hưng Đạo", "phố Lý Thường Kiệt", "đường Nguyễn Văn Cừ", "đường Tôn Đức Thắng",
        "phố Hồ Tùng Mậu", "phố Lê Văn Lương", "phố Khuất Duy Tiến", "đường Nguyễn Xiển", "đường Tố Hữu", "đường Võ Chí Công",
        "đường Thanh Niên", "đường Âu Cơ", "phố Nghi Tàm", "phố Yên Phụ", "phố Hàng Đào", "phố Tràng Tiền", "phố Phan Đình Phùng",
        "phố Nguyễn Thái Học", "phố Giảng Võ", "phố Đội Cấn", "phố Nguyễn Lương Bằng", "phố Ngọc Hà", "phố Trung Kính",
        "phố Duy Tân", "đường Phạm Hùng", "đường Lê Trọng Tấn", "phố Ngô Gia Tự", "phố Vũ Tông Phan", "phố Hoàng Hoa Thám",
        "phố Kim Ngưu", "phố Vọng", "phố Định Công", "đường Lĩnh Nam", "phố Mai Dịch"]),
    "Hải Phòng": ("Bắc", "ngõ", ["đường Lạch Tray", "đường Lê Hồng Phong", "đường Điện Biên Phủ", "đường Tô Hiệu", "đường Trần Nguyên Hãn",
                                 "đường Nguyễn Bỉnh Khiêm", "đường Lê Lai", "đường Cát Dài", "đường Ngô Quyền", "đường Văn Cao"]),
    "Hạ Long": ("Bắc", "ngõ", ["đường Trần Hưng Đạo", "đường Lê Thánh Tông", "đường Nguyễn Văn Cừ", "đường Hạ Long", "đường Bạch Đằng"]),
    "Huế": ("Trung", "kiệt", ["đường Lê Lợi", "đường Hùng Vương", "đường Nguyễn Huệ", "đường Trần Hưng Đạo", "đường Phạm Văn Đồng",
                              "đường Hà Nội", "đường Lý Thường Kiệt", "đường Bà Triệu", "đường Điện Biên Phủ", "đường Nguyễn Sinh Cung",
                              "đường Phan Bội Châu", "đường Đội Cung", "đường Ngự Bình", "đường Phan Đình Phùng"]),
    "Đà Nẵng": ("Trung", "kiệt", ["đường Bạch Đằng", "đường Nguyễn Văn Linh", "đường Lê Duẩn", "đường Hùng Vương", "đường Trần Phú",
                                  "đường Ngô Quyền", "đường Nguyễn Tất Thành", "đường Điện Biên Phủ", "đường Hai Tháng Chín",
                                  "đường Phạm Văn Đồng", "đường Ông Ích Khiêm", "đường Hoàng Diệu", "đường Võ Nguyên Giáp",
                                  "đường Lê Đại Hành", "đường Trần Cao Vân", "đường Nguyễn Hữu Thọ", "đường Tôn Đức Thắng", "đường Hàm Nghi"]),
    "Nha Trang": ("Trung", "hẻm", ["đường Trần Phú", "đường Nguyễn Thị Minh Khai", "đường Lê Thánh Tôn", "đường Hùng Vương",
                                   "đường Phạm Văn Đồng", "đường Thái Nguyên", "đường Yersin", "đường Điện Biên Phủ"]),
    "Vinh": ("Trung", "ngõ", ["đường Lê Lợi", "đường Quang Trung", "đường Lê Duẩn", "đường Nguyễn Sỹ Sách", "đường Trường Thi", "đường Nguyễn Văn Cừ"]),
    "Sài Gòn": ("Nam", "hẻm", [
        "đường Nguyễn Huệ", "đường Lê Lợi", "đường Điện Biên Phủ", "đường Cách Mạng Tháng Tám", "đường Võ Văn Tần",
        "đường Nguyễn Thị Minh Khai", "đường Lý Tự Trọng", "đường Hai Bà Trưng", "đường Nam Kỳ Khởi Nghĩa", "đường Trường Chinh",
        "đường Cộng Hòa", "đường Hoàng Văn Thụ", "đường Phan Xích Long", "đường Nguyễn Kiệm", "đường Lê Quang Định",
        "đường Xô Viết Nghệ Tĩnh", "đường Nguyễn Hữu Cảnh", "đường Phạm Văn Đồng", "đường Võ Văn Kiệt", "đường Nguyễn Tri Phương",
        "đường Ba Tháng Hai", "đường Sư Vạn Hạnh", "đường Nguyễn Thị Thập", "đường Huỳnh Tấn Phát", "đường Lê Văn Việt",
        "đường Võ Thị Sáu", "đường Tô Hiến Thành", "đường Nguyễn Văn Cừ", "đường Trần Hưng Đạo", "đường Lê Văn Sỹ",
        "đường Hoàng Hoa Thám", "đường Phan Đăng Lưu", "đường Quang Trung", "đường Lê Đức Thọ", "đường Nguyễn Oanh",
        "đường Phạm Ngũ Lão", "đường Đinh Tiên Hoàng", "đường Nguyễn Văn Linh", "đường Mai Chí Thọ", "đường An Dương Vương",
        "đường Tên Lửa", "đường Lũy Bán Bích", "đường Âu Cơ", "đường Lạc Long Quân", "đường Tân Kỳ Tân Quý", "đường Thích Quảng Đức",
        "đường Bạch Đằng", "đường Nguyễn Đình Chiểu", "đường Pasteur", "đường Hùng Vương"]),
    "Cần Thơ": ("Nam", "hẻm", ["đường Nguyễn Văn Cừ", "đường Ba Mươi Tháng Tư", "đường Trần Hưng Đạo", "đường Mậu Thân", "đường Nguyễn Trãi",
                               "đường Hòa Bình", "đường Võ Văn Kiệt", "đường Cách Mạng Tháng Tám", "đường Nguyễn Văn Linh"]),
    "Biên Hòa": ("Nam", "hẻm", ["đường Phạm Văn Thuận", "đường Võ Thị Sáu", "đường Đồng Khởi", "đường Nguyễn Ái Quốc", "đường Hà Huy Giáp"]),
    "Vũng Tàu": ("Nam", "hẻm", ["đường Thùy Vân", "đường Trần Phú", "đường Lê Hồng Phong", "đường Hạ Long", "đường Nguyễn Thái Học"]),
}
STREET_CITY_DIST = {"Hà Nội": "Hà Nội", "Sài Gòn": "Sài Gòn", "Đà Nẵng": "Đà Nẵng", "Hải Phòng": "Hải Phòng", "Cần Thơ": "Cần Thơ", "Huế": "Huế"}
src("streets", "generator/pools.py (phiên trước, K1) + bổ sung K1: tên đường phổ biến ở 12 thành phố. Chưa đối chiếu OpenStreetMap. "
    "Số nhà, ngõ/hẻm/kiệt là ghép ngẫu nhiên -> địa chỉ tổng hợp (cờ synthetic_address).")

# ------------------------------------------------------------------ địa điểm (POI)
POIS = []


def poi(kind, names, region, city, alias=False, note=None):
    for n in names:
        POIS.append(dict(name=n, kind=kind, region=region, city=city, alias=alias, note=note))


poi("sân bay", ["sân bay Nội Bài"], "Bắc", "Hà Nội")
poi("sân bay", ["sân bay Cát Bi"], "Bắc", "Hải Phòng")
poi("sân bay", ["sân bay Tân Sơn Nhất"], "Nam", "Sài Gòn")
poi("sân bay", ["sân bay Đà Nẵng"], "Trung", "Đà Nẵng")
poi("sân bay", ["sân bay Phú Bài"], "Trung", "Huế")
poi("sân bay", ["sân bay Cam Ranh"], "Trung", "Nha Trang")
poi("sân bay", ["sân bay Liên Khương"], "Trung", "Đà Lạt")
poi("sân bay", ["sân bay Cần Thơ"], "Nam", "Cần Thơ")
poi("sân bay", ["sân bay Phú Quốc"], "Nam", "Phú Quốc")
poi("sân bay", ["sân bay Vinh"], "Trung", "Vinh")
poi("ga", ["ga Hà Nội"], "Bắc", "Hà Nội")
poi("ga", ["ga Sài Gòn"], "Nam", "Sài Gòn")
poi("ga", ["ga Đà Nẵng"], "Trung", "Đà Nẵng")
poi("ga", ["ga Huế"], "Trung", "Huế")
poi("ga", ["ga Vinh"], "Trung", "Vinh")
poi("ga", ["ga Nha Trang"], "Trung", "Nha Trang")
poi("bến xe", ["bến xe Mỹ Đình", "bến xe Giáp Bát", "bến xe Nước Ngầm", "bến xe Yên Nghĩa", "bến xe Gia Lâm"], "Bắc", "Hà Nội")
poi("bến xe", ["bến xe Miền Đông", "bến xe Miền Tây"], "Nam", "Sài Gòn")
poi("bến xe", ["bến xe trung tâm Đà Nẵng"], "Trung", "Đà Nẵng")
poi("bệnh viện", ["bệnh viện Bạch Mai", "bệnh viện Việt Đức", "bệnh viện Nhi Trung ương", "bệnh viện K", "bệnh viện Phụ sản Trung ương",
                  "bệnh viện Hữu Nghị", "bệnh viện Thanh Nhàn", "bệnh viện Đại học Y Hà Nội", "bệnh viện Xanh Pôn"], "Bắc", "Hà Nội")
poi("bệnh viện", ["bệnh viện Chợ Rẫy", "bệnh viện Từ Dũ", "bệnh viện Thống Nhất", "bệnh viện Đại học Y Dược", "bệnh viện Hùng Vương",
                  "bệnh viện Nhân dân Gia Định"], "Nam", "Sài Gòn")
poi("bệnh viện", ["bệnh viện Trung ương Huế"], "Trung", "Huế")
poi("bệnh viện", ["bệnh viện Đà Nẵng", "bệnh viện C Đà Nẵng"], "Trung", "Đà Nẵng")
poi("bệnh viện", ["bệnh viện Đa khoa Trung ương Cần Thơ"], "Nam", "Cần Thơ")
poi("trường đại học", ["Đại học Bách khoa Hà Nội", "Đại học Quốc gia Hà Nội", "Đại học Kinh tế Quốc dân", "Đại học Xây dựng",
                       "Đại học Sư phạm Hà Nội", "Đại học Ngoại thương", "Đại học Y Hà Nội"], "Bắc", "Hà Nội")
poi("trường đại học", ["Đại học Bách khoa thành phố Hồ Chí Minh", "Đại học Kinh tế thành phố Hồ Chí Minh",
                       "Đại học Sư phạm thành phố Hồ Chí Minh", "Đại học Tôn Đức Thắng"], "Nam", "Sài Gòn")
poi("trường đại học", ["Đại học Huế"], "Trung", "Huế")
poi("trường đại học", ["Đại học Bách khoa Đà Nẵng", "Đại học Đà Nẵng"], "Trung", "Đà Nẵng")
poi("trung tâm thương mại", ["Vincom Center Bà Triệu", "Royal City", "Aeon Mall Long Biên", "Aeon Mall Hà Đông", "Lotte Center Hà Nội",
                             "Times City", "Tràng Tiền Plaza"], "Bắc", "Hà Nội")
poi("trung tâm thương mại", ["Aeon Mall Tân Phú", "Crescent Mall", "Vincom Center Đồng Khởi", "Saigon Centre", "Vạn Hạnh Mall",
                             "Giga Mall", "Takashimaya"], "Nam", "Sài Gòn")
poi("trung tâm thương mại", ["Vincom Plaza Ngô Quyền", "Lotte Mart Đà Nẵng"], "Trung", "Đà Nẵng")
poi("danh thắng", ["Hồ Hoàn Kiếm", "Văn Miếu Quốc Tử Giám", "Lăng Chủ tịch Hồ Chí Minh", "Hồ Tây", "Hoàng thành Thăng Long",
                   "Nhà hát Lớn Hà Nội", "Chùa Một Cột", "phố cổ Hà Nội", "chợ Đồng Xuân", "cầu Long Biên"], "Bắc", "Hà Nội")
poi("danh thắng", ["Tràng An", "Tam Cốc", "chùa Bái Đính"], "Bắc", "Ninh Bình")
poi("danh thắng", ["Đại Nội Huế", "chùa Thiên Mụ", "lăng Khải Định", "lăng Tự Đức", "cầu Trường Tiền", "chợ Đông Ba"], "Trung", "Huế")
poi("danh thắng", ["Bà Nà Hills", "cầu Rồng", "bán đảo Sơn Trà", "Ngũ Hành Sơn", "bãi biển Mỹ Khê", "chợ Hàn", "cầu sông Hàn"], "Trung", "Đà Nẵng")
poi("danh thắng", ["phố cổ Hội An", "chùa Cầu"], "Trung", "Hội An")
poi("danh thắng", ["chợ Bến Thành", "Dinh Độc Lập", "Nhà thờ Đức Bà", "phố đi bộ Nguyễn Huệ", "Bưu điện Thành phố", "Thảo Cầm Viên",
                   "công viên Đầm Sen", "khu du lịch Suối Tiên", "bến Bạch Đằng", "chợ Bình Tây", "công viên Tao Đàn", "Landmark 81",
                   "cầu Ánh Sao"], "Nam", "Sài Gòn")
poi("danh thắng", ["chợ nổi Cái Răng", "bến Ninh Kiều"], "Nam", "Cần Thơ")
poi("danh thắng", ["hồ Xuân Hương", "thung lũng Tình Yêu", "thác Datanla", "chợ Đà Lạt"], "Trung", "Đà Lạt")
poi("danh thắng", ["tháp Bà Ponagar", "Hòn Chồng"], "Trung", "Nha Trang")
poi("khu đô thị", ["khu đô thị Ecopark", "Vinhomes Ocean Park", "khu đô thị Ciputra", "khu đô thị Linh Đàm", "Vinhomes Smart City"], "Bắc", "Hà Nội")
poi("khu đô thị", ["khu đô thị Phú Mỹ Hưng", "khu đô thị Sala", "Vinhomes Grand Park", "Vinhomes Central Park", "khu Thảo Điền"], "Nam", "Sài Gòn")
# tên gọi quen của người địa phương (S54) — K1, cần người địa phương xác nhận
poi("tên gọi quen", ["Bờ Hồ", "ngã tư Sở", "ngã tư Vọng", "ngã sáu Ô Chợ Dừa", "Hồ Gươm"], "Bắc", "Hà Nội", alias=True,
    note="Bờ Hồ, Hồ Gươm = khu Hồ Hoàn Kiếm")
poi("tên gọi quen", ["chợ Lớn", "ngã tư Hàng Xanh", "bùng binh Cây Gõ", "Hồ Con Rùa", "ngã sáu Phù Đổng", "ngã tư Bảy Hiền",
                     "cầu Sài Gòn", "bùng binh Quách Thị Trang"], "Nam", "Sài Gòn", alias=True,
    note="Hồ Con Rùa = Công trường Quốc tế; bùng binh = vòng xoay")
poi("tên gọi quen", ["cầu Rồng", "ngã ba Huế", "chợ Cồn"], "Trung", "Đà Nẵng", alias=True)
POI_SPOKEN = {"Landmark 81": "Landmark tám mươi mốt", "bệnh viện K": "bệnh viện Ca", "bệnh viện C Đà Nẵng": "bệnh viện Xê Đà Nẵng"}
POI_LOANWORD = ("Mall", "Center", "City", "Royal", "Hills", "Landmark", "Crescent", "Saigon", "Vincom", "Aeon", "Lotte", "Giga",
                "Plaza", "Vinhomes", "Park", "Central", "Ecopark", "Times", "Takashimaya", "Smart", "Ocean", "Mart", "Centre")
src("pois", "generator/pools.py (phiên trước, K1) + bổ sung K1: sân bay, ga, bến xe, bệnh viện, trường, trung tâm thương mại, danh thắng, "
    "khu đô thị; nhóm 'tên gọi quen' là cách gọi của người địa phương (S54), cần duyệt. Tên chưa đối chiếu bản đồ hiện hành.")

HOME_LIKE = ["nhà", "nhà ba mẹ", "nhà ngoại", "nhà nội", "nhà ông bà", "nhà bà ngoại", "nhà anh trai", "nhà chị gái", "nhà em gái",
             "nhà bố mẹ vợ", "quê", "nhà riêng"]
PLACE_LIKE = ["cơ quan", "công ty", "trường của con", "văn phòng", "xưởng", "cửa hàng", "kho hàng", "chi nhánh", "trường mẫu giáo",
              "phòng khám", "phòng tập", "chỗ làm"]
src("saved", "src_commands.json slots_seen (nhà, cơ quan, quê; N16) + tự biên (K1).")

NEARBY = ["quán cà phê", "nhà hàng", "quán phở", "quán bún chả", "quán cơm", "hiệu thuốc", "bệnh viện", "ngân hàng", "cây ATM", "siêu thị",
          "cửa hàng tiện lợi", "bãi đỗ xe", "trạm dừng chân", "nhà vệ sinh công cộng", "tiệm sửa xe", "tiệm rửa xe", "trạm đăng kiểm",
          "chợ", "công viên", "khách sạn", "nhà nghỉ", "quán ăn gia đình", "tiệm bánh", "cửa hàng hoa", "tiệm cắt tóc", "phòng khám",
          "bưu điện", "đồn công an", "quán bún bò", "quán lẩu", "quán nướng", "tiệm vá lốp", "gara ô tô", "trạm sạc", "cây xăng",
          "quán ăn chay", "tiệm thuốc tây", "nhà sách", "trạm thu phí"]
src("nearby", "src_commands.json slots_seen loai_dia_diem (quán cà phê, cây xăng, trạm sạc, quán ăn; N1,N10,N13) + tự biên K1.")

HIGHWAYS = [("quốc lộ 1A", "QL1A"), ("quốc lộ 5", "QL5"), ("quốc lộ 6", "QL6"), ("quốc lộ 18", "QL18"), ("quốc lộ 22", "QL22"),
            ("quốc lộ 51", "QL51"), ("quốc lộ 13", "QL13"), ("quốc lộ 14", "QL14"), ("quốc lộ 32", "QL32"), ("quốc lộ 3", "QL3"),
            ("quốc lộ 1K", "QL1K"), ("quốc lộ 20", "QL20"), ("quốc lộ 21", "QL21"), ("quốc lộ 9", "QL9"),
            ("cao tốc Hà Nội – Hải Phòng", None), ("cao tốc Pháp Vân – Cầu Giẽ", None), ("cao tốc Nội Bài – Lào Cai", None),
            ("cao tốc Thành phố Hồ Chí Minh – Trung Lương", None), ("cao tốc Thành phố Hồ Chí Minh – Long Thành – Dầu Giây", None),
            ("cao tốc Đà Nẵng – Quảng Ngãi", None), ("cao tốc Cam Lộ – La Sơn", None), ("cao tốc Hạ Long – Hải Phòng", None),
            ("cao tốc Hà Nội – Thái Nguyên", None), ("đại lộ Thăng Long", None), ("đường vành đai ba", None), ("đường vành đai hai", None),
            ("cầu Thanh Trì", None), ("cầu Nhật Tân", None), ("hầm Thủ Thiêm", None), ("cầu Phú Mỹ", None), ("hầm Hải Vân", None),
            ("đèo Hải Vân", None), ("cao tốc Trung Lương – Mỹ Thuận", None)]
src("highways", "generator/pools.py (phiên trước, K1) + bổ sung K1; dạng viết tắt QL dùng cho yếu tố E07.")

# ------------------------------------------------------------------ người, xưng hô (src_lang.json names + kinship)
_n = LANG["names"]
MALE = [x["name"] for x in _n["male_given"]] + ["Khoa", "Vinh", "Lâm", "Quân", "Tiến", "Hiệp", "Thịnh", "Kiên", "Toàn", "Duy", "Hậu", "Việt"]
FEMALE = [x["name"] for x in _n["female_given"] if x["name"] != "Hiếu"] + ["Oanh", "Diệp", "Quyên", "Nga", "Châu", "My", "Trâm", "Uyên"]
SURNAMES = [x["name"].split("/")[0] for x in _n["surnames"]] + ["Huỳnh", "Võ"]
MID_M = [x["name"] for x in _n["male_middle"]]
MID_F = [x["name"].split("/")[0] for x in _n["female_middle"]]
src("names", "sources/src_lang.json names (họ: L4, L12, L13; tên đệm: L4 + K1; tên gọi: K1) + bổ sung K1 từ generator/pools.py. "
    "Tên là tổ hợp phổ biến, không nhắm tới người có thật.")
HON_PEER = {"M": ["anh"], "F": ["chị"]}
HON_ELDER = {"M": ["chú", "bác", "cậu", "thầy", "ông"], "F": ["cô", "dì", "bác", "mợ", "cô giáo", "bà"]}
HON_YOUNG = ["em", "bé"]
BIRTH = ["Hai", "Ba", "Tư", "Năm", "Sáu", "Bảy", "Tám", "Út"]
CONTEXT_TAGS = ["công ty", "hàng xóm", "cũ", "kế toán", "bên bảo hiểm", "đối tác", "bên kho", "ở quê", "bạn học", "phòng nhân sự",
                "lái xe", "sửa xe", "giao hàng", "chủ nhà", "trưởng phòng", "tổ trưởng"]
KIN = {
    "Bắc": [("mẹ", False), ("bố", False), ("vợ", False), ("chồng", False), ("ông xã", False), ("bà xã", False), ("anh trai", False),
            ("chị gái", False), ("em gái", False), ("em trai", False), ("con gái", False), ("con trai", False), ("ông nội", False),
            ("bà ngoại", False), ("u", True), ("thầy u", True)],
    "Nam": [("má", True), ("ba", True), ("vợ", False), ("chồng", False), ("ông xã", False), ("bà xã", False), ("anh Hai", True),
            ("chị Hai", True), ("em gái", False), ("con gái", False), ("con trai", False), ("ông ngoại", False), ("bà nội", False),
            ("tía", True), ("dượng", True), ("thím Ba", True)],
    "Trung": [("mạ", True), ("ba", True), ("cha", True), ("o", True), ("mệ", True), ("vợ", False), ("chồng", False), ("anh trai", False),
              ("chị gái", False), ("em gái", False), ("con trai", False), ("ông nội", False)],
}
src("kinship", "sources/src_lang.json names.kinship, lexicon (mẹ/mạ/má: L6, L25; bố/ba/tía: L6, L25; o, mệ: L10, L11) + K1.")

# ------------------------------------------------------------------ nhạc (src_lang.json music)
_m = LANG["music"]
ARTISTS = [a["name"] for a in _m["artists"] if a["verified"] and not a["name"].startswith("(nhạc sĩ)")]
ARTISTS = [a.replace("Đen (Đen Vâu)", "Đen Vâu") for a in ARTISTS]
COMPOSERS = [a["name"].replace("(nhạc sĩ) ", "") for a in _m["artists"] if a["name"].startswith("(nhạc sĩ)")]
SONGS = [(s["title"], s["artist"]) for s in _m["songs"] if s["verified"] and s["title"] != "Tiến quân ca"]
src("music", "sources/src_lang.json music: chỉ lấy ca sĩ và bài có verified=true (nguồn L7, L16–L20, L24). Chỉ dùng tên, không dùng lời.")
GENRES = ["nhạc trữ tình", "nhạc vàng", "nhạc bolero", "nhạc trẻ", "nhạc rock", "nhạc pop", "nhạc dân ca", "nhạc cách mạng",
          "nhạc không lời", "nhạc EDM", "nhạc Hàn", "nhạc Hoa", "nhạc Âu Mỹ", "nhạc thiếu nhi", "nhạc cổ điển", "nhạc jazz",
          "nhạc lofi", "nhạc thư giãn", "nhạc sôi động", "nhạc remix", "nhạc acoustic", "nhạc quê hương", "nhạc Trịnh", "nhạc rap Việt",
          "nhạc tiền chiến", "nhạc indie", "nhạc cải lương", "nhạc quan họ", "nhạc K-pop", "nhạc V-pop", "nhạc xuân", "nhạc phim"]
GENRE_BARE = ["trữ tình", "vàng", "bolero", "trẻ", "rock", "pop", "dân ca", "cách mạng", "không lời", "EDM", "Hàn", "Hoa", "Âu Mỹ",
              "thiếu nhi", "cổ điển", "jazz", "lofi", "thư giãn", "remix", "acoustic", "Trịnh", "rap", "tiền chiến", "indie", "K-pop",
              "V-pop", "xuân", "đỏ", "hip hop", "ballad", "quê hương", "cải lương"]
src("genres", "sources/src_lang.json music.genres (L7, L17, L24 + K1) + generator/pools.py (K1).")
MOODS = ["vui vẻ", "thư giãn", "tập trung", "lãng mạn", "sôi động", "nhẹ nhàng", "tỉnh táo", "hoài niệm", "tràn đầy năng lượng",
         "yên tĩnh", "buồn", "chill", "dễ chịu", "lạc quan"]
PLAYLISTS = [p for p in _m["playlists"]] + ["Chill cuối tuần", "Đường dài", "Buổi sáng tỉnh táo", "Yêu thích", "Mới nghe gần đây",
                                           "Nhạc đi làm", "Cho chuyến đi xa", "Gia đình cùng nghe", "Nhạc cho bé", "Top nhạc tuần này",
                                           "Hit một thời", "Road Trip", "Nhạc chạy đêm"]
src("playlists", "sources/src_lang.json music.playlists (K1, không phải playlist có thật) + generator/pools.py (K1).")
PODCASTS = ["tin tức buổi sáng", "sách nói", "truyện audio", "podcast kinh doanh", "podcast lịch sử", "bản tin giao thông",
            "truyện cổ tích", "chương trình học tiếng Anh", "tin thể thao", "tin công nghệ", "truyện đêm khuya", "podcast tâm lý",
            "podcast tài chính cá nhân", "sách nói kỹ năng sống"]
TOPICS = ["lịch sử", "kinh doanh", "sức khỏe", "công nghệ", "nuôi dạy con", "tài chính cá nhân", "du lịch", "thể thao", "âm nhạc",
          "khởi nghiệp", "ẩm thực", "tâm lý", "ô tô", "chứng khoán", "bất động sản", "giáo dục", "khoa học", "thời sự", "bóng đá",
          "xe điện", "văn hóa", "kỹ năng giao tiếp"]
src("podcast", "Tự biên K1 (thể loại, chủ đề chung; N1 chỉ có placeholder X, Y, Z).")
APPS = ["Zalo", "Messenger", "YouTube", "Spotify", "Zing MP3", "Facebook", "Gmail", "Viber", "Telegram", "Google Maps", "lịch",
        "Vietmap", "Waze", "VETC", "ePass"]
src("apps", "src_commands.json slots_seen ung_dung (Zalo, YouTube, Spotify; N17) + src_lang music.apps (L15) + K1. "
    "v3: thêm Vietmap, Waze, VETC, ePass theo review/PHU_LUC_app_tren_man_hinh_va_tu_ngoai.md (Vietmap: fptshop 'Màn hình Vietmap', "
    "baohatinh VF Connect 'Vietmap Live'; VETC, ePass: hai thẻ thu phí không dừng; Waze: phụ lục, chưa có nguồn lệnh trên xe).")
MUSIC_APPS = ["YouTube", "Spotify", "Zing MP3", "YouTube Music", "Apple Music"]
MSG_APPS = ["Zalo", "Messenger", "Viber", "Telegram"]
src("music_msg_apps", "Chuyển từ slots10k (music_app, msg_app, v2). Phụ lục v3: Android Auto đọc Messenger, Telegram (support.google.com, "
    "slashgear); Zalo, Viber chưa kiểm có hỗ trợ trên Android Auto.")
MAP_APPS = ["Google Maps", "Vietmap", "Waze"]
src("map_apps", "Phụ lục v3 G6: Vietmap và Google Maps dùng song song trên màn hình Android (fptshop 'Màn hình Vietmap'); Kiki mở Google Maps; "
    "Waze theo phụ lục, chưa có nguồn lệnh trên xe.")
ETC_APPS = ["VETC", "ePass"]
src("etc_apps", "Phụ lục v3 G8: VETC và ePass là hai thẻ thu phí không dừng (khảo sát 14–15/10/2026).")
# nguồn kết nối: (chữ viết, cách đọc hiện tại trong bộ, đặc trưng) — cách đọc dùng khi bảng từ ngoại chưa duyệt
LINK_SRC = [("Bluetooth", "Bluetooth", ("từ mượn tiếng Anh",)), ("USB", "u ét bê", ("viết tắt",)), ("điện thoại", "điện thoại", ()),
            ("Apple CarPlay", "Apple CarPlay", ("từ mượn tiếng Anh",)), ("Android Auto", "Android Auto", ("từ mượn tiếng Anh",)),
            ("thẻ nhớ", "thẻ nhớ", ())]
src("link_src", "Chuyển từ slots10k.g_link_src (v2): src_commands nguon_nhac_bluetooth_usb + K1.")
CHANNELS = ["kênh nấu ăn", "kênh tin tức", "kênh du lịch", "kênh hoạt hình cho bé", "kênh ca nhạc", "kênh hài", "kênh đánh giá xe",
            "kênh học tiếng Anh", "kênh thể thao", "kênh bóng đá", "kênh kể chuyện", "kênh phim tài liệu", "kênh thời sự",
            "kênh nhạc thiếu nhi", "kênh sức khỏe", "kênh công nghệ", "kênh câu cá", "kênh làm vườn", "kênh phượt", "kênh lịch sử"]
src("channels", "Tự biên K1, tên mô tả loại kênh (không dùng tên kênh thật), theo quyết định của người dùng 2026-10-15.")
CARTOONS = ["Doraemon", "Tom và Jerry", "Peppa Pig", "Shin cậu bé bút chì", "Thám tử lừng danh Conan", "Frozen", "Baby Shark",
            "Masha và chú gấu", "Thỏ Bảy Màu", "Dế Mèn phiêu lưu ký"]
src("cartoons", "Tự biên K1: tên phim/chương trình thiếu nhi phổ biến; chưa kiểm.")

RADIO = [("VOV Giao thông", "vê ô vê Giao thông", 91.0, None), ("VOV3", "vê ô vê ba", 102.7, None), ("VOV2", "vê ô vê hai", 96.5, None),
         ("VOV1", "vê ô vê một", None, None), ("VOV5", "vê ô vê năm", 105.5, "Bắc"), ("VOH", "vê ô hát", 99.9, "Nam")]
FREQS = [87.5, 88.0, 89.0, 90.0, 91.0, 92.5, 94.0, 95.6, 96.5, 97.0, 98.9, 99.9, 100.0, 101.5, 102.7, 103.5, 104.0, 105.5, 106.5]
src("radio", "generator/pools.py (phiên trước): tên đài và tần số theo Wikipedia 'List of radio stations in Vietnam' đọc qua công cụ tóm tắt, "
    "chưa đối chiếu nguồn gốc; tần số khác nhau theo địa phương. Tần số trong FREQS chỉ là giá trị dải FM hợp lệ, không khẳng định có đài.")

# ------------------------------------------------------------------ xe
TIRES = ["lốp trước bên trái", "lốp trước bên phải", "lốp sau bên trái", "lốp sau bên phải", "lốp dự phòng", "lốp trước", "lốp sau"]
VENTS = ["lên mặt", "xuống chân", "vào kính chắn gió", "cả mặt và chân", "lên kính và xuống chân", "vào giữa"]
SEATS = ["ghế lái", "ghế phụ", "ghế sau bên lái", "ghế sau bên phụ", "hàng ghế sau", "ghế trước"]
WPOS = ["bên lái", "bên phụ", "sau bên lái", "sau bên phụ", "sau bên trái", "sau bên phải", "phía trước", "phía sau"]
LAMPS = ["đèn trong xe", "đèn đọc sách", "đèn nội thất", "đèn sương mù", "đèn pha tự động", "đèn trần", "đèn viền nội thất", "đèn cốp"]
COLORS = ["xanh dương", "đỏ", "tím", "trắng", "cam", "xanh lá", "hồng", "vàng", "xanh ngọc", "xanh lam"]
WARN_LAMPS = ["động cơ", "phanh", "ắc quy", "áp suất lốp", "túi khí", "dầu máy", "nhiệt độ nước làm mát", "cửa chưa đóng",
              "dây an toàn", "phanh tay", "bảo dưỡng", "ABS", "hệ thống lái", "nhiên liệu"]
PARTS = ["dầu máy", "phanh", "ắc quy", "nước làm mát", "nước rửa kính", "lốp", "đèn xe", "lọc gió", "má phanh", "gạt mưa", "dầu phanh"]
WARNS = ["cảnh báo lệch làn", "cảnh báo va chạm phía trước", "cảnh báo điểm mù", "cảnh báo vượt tốc độ", "cảnh báo người lái buồn ngủ",
         "cảnh báo va chạm khi lùi", "cảnh báo mở cửa", "cảnh báo phương tiện cắt ngang", "cảnh báo khoảng cách"]
SYSTEMS = [("hệ thống hỗ trợ giữ làn", None), ("hệ thống phanh khẩn cấp tự động", None), ("hệ thống nhận diện biển báo", None),
           ("hệ thống giám sát người lái", None), ("hệ thống hỗ trợ đỗ xe", None), ("camera lùi", None), ("cảm biến đỗ xe", None),
           ("camera 360 độ", "camera ba trăm sáu mươi độ"), ("đèn pha thích ứng", None), ("hỗ trợ khởi hành ngang dốc", None)]
src("car", "sources/src_lang.json car_terms (L22, L27 + K1) + generator/pools.py, tpl_a.py (K1). Chưa đối chiếu sách hướng dẫn hãng.")

# ------------------------------------------------------------------ hội thoại, nhắc việc, tin nhắn
REMIND = ["đi khám sức khỏe", "uống thuốc", "mua sữa", "ăn trưa", "đón con", "đón con ở trường", "họp với khách hàng", "gọi cho mẹ",
          "nộp báo cáo", "đóng tiền điện", "đổ xăng", "sạc xe", "mua hoa", "lấy đồ giặt", "đi bảo dưỡng xe", "thay dầu", "đặt bánh sinh nhật",
          "trả sách thư viện", "chuyển khoản tiền nhà", "mang áo mưa", "tưới cây", "đi chợ", "gửi hồ sơ", "gọi lại cho khách",
          "mua quà cho vợ", "đón bà ở sân bay", "kiểm tra áp suất lốp", "gia hạn bảo hiểm xe", "nạp tiền thu phí không dừng",
          "đi tập thể dục", "mua thuốc cho bố", "ký hợp đồng", "đặt vé xe", "rút tiền", "mua bánh mì", "đi đăng kiểm xe"]
src("remind", "src_commands.json slots_seen noi_dung (đi khám sức khỏe, uống thuốc, mua sữa, ăn trưa; N7, N8, N12) + tự biên K1.")
MESSAGES = ["tôi đang lái xe, lát nữa gọi lại", "mình sắp đến rồi", "tối nay mình về trễ", "đã nhận được, cảm ơn", "hẹn gặp lại sau nhé",
            "chờ mình ở cổng nhé", "mình đang trên đường", "để mình gọi lại sau", "mình đã đến nơi", "đừng đợi mình ăn cơm",
            "mình bận chút, lát nói chuyện sau", "đồng ý, cứ như vậy nhé", "con sẽ về trễ", "con đang trên đường về",
            "đang kẹt xe, chắc đến muộn", "anh đến đón em nhé", "mở cổng giúp mình", "mình đậu xe ở tầng hầm", "nhớ mang theo giấy tờ",
            "họp dời sang chiều nhé", "gửi mình địa chỉ với", "mình đang ở bãi xe", "tối nay ăn gì", "mua giúp mình chai nước",
            "cuộc họp bắt đầu chưa", "khoảng mười phút nữa mình tới", "cảm ơn nhiều nhé", "ok, mình biết rồi"]
src("messages", "src_commands.json slots_seen noi_dung (mình đến muộn 10 phút, con sẽ về trễ, con đang trên đường về; N7, N8) + tự biên K1.")
SHOP = ["sữa", "bánh mì", "trứng", "rau", "nước mắm", "giấy vệ sinh", "thuốc cảm", "hoa quả", "gạo", "dầu ăn", "nước suối", "cà phê",
        "tã cho bé", "bỉm", "thịt", "cá", "đồ ăn sáng"]
COUNTRIES = ["Nhật Bản", "Hàn Quốc", "Pháp", "Đức", "Úc", "Canada", "Thái Lan", "Lào", "Campuchia", "Ấn Độ", "Brazil", "Ai Cập",
             "Mỹ", "Anh", "Ý", "Tây Ban Nha", "Singapore", "Malaysia", "Indonesia", "Philippines", "Nga", "Trung Quốc"]
DISHES = ["phở", "bún chả", "bún bò", "cơm tấm", "bánh xèo", "lẩu", "bún riêu", "mì Quảng", "cơm gà", "bánh canh", "hủ tiếu",
          "bún đậu", "cháo", "bánh cuốn", "gà nướng", "hải sản", "ốc", "chè", "bánh mì"]
NEWS_TOPICS = ["giá xăng", "thời tiết", "bóng đá", "giao thông", "chứng khoán", "giá vàng", "thể thao", "công nghệ", "kinh tế",
               "thế giới", "xe điện", "giáo dục", "sức khỏe", "giải trí", "pháp luật", "bất động sản"]
src("misc", "Tự biên K1: hàng hóa, quốc gia, món ăn, chủ đề tin tức.")

WEATHER = ["mưa", "nắng", "mưa to", "mưa rào", "giông", "sương mù", "rét", "nắng nóng", "gió mạnh", "mưa đá", "ngập", "lạnh", "bão",
           "áp thấp"]
src("weather", "Mau_khung T13 (mưa, nắng, ngập) + tự biên K1.")

SHORT_CMDS = ["dẫn đường về nhà", "đi đường khác", "gọi anh Hùng", "bật điều hòa", "mở nhạc", "tắt nhạc", "tăng âm lượng",
              "giảm quạt gió", "đọc tin nhắn", "gọi lại cho mẹ", "tìm cây xăng", "tìm trạm sạc", "mở cửa sổ trời", "đóng cốp",
              "bật sưởi ghế", "chuyển bài", "nghe đài giao thông", "hủy dẫn đường", "bật đèn trong xe", "khóa cửa", "tắt sấy kính",
              "đi đường nhanh nhất", "tránh cao tốc", "gửi vị trí cho vợ", "đặt báo thức", "tắt cảnh báo lệch làn"]
src("short_cmds", "Rút gọn từ các khung CS01–CS10 trong src_commands.json (dùng cho 'ý tôi là ...' ở CS12).")
