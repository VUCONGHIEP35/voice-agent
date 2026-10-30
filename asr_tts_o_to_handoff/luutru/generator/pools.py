# -*- coding: utf-8 -*-
"""Các danh sách giá trị khe, mỗi danh sách có nguồn. region: Bắc/Trung/Nam/None."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = {}  # tên pool -> mô tả nguồn
POOLS = {}


def pool(name, items, source):
    POOLS[name] = items
    SRC[name] = source


# ------------------------------------------------------------------ hành chính (nguồn: GitHub madnh/hanhchinhvn)
_t = json.load(open(os.path.join(HERE, "src", "tinh_tp.json"), encoding="utf-8"))
_q = json.load(open(os.path.join(HERE, "src", "quan_huyen.json"), encoding="utf-8"))
NORTH = {"01", "02", "04", "06", "08", "10", "11", "12", "14", "15", "17", "19", "20", "22", "24", "25", "26", "27", "30", "31", "33", "34", "35", "36", "37"}
CENTRAL = {"38", "40", "42", "44", "45", "46", "48", "49", "51", "52", "54", "56", "58", "60", "62", "64", "66", "67", "68"}


def region_of(code):
    if code in NORTH:
        return "Bắc"
    if code in CENTRAL:
        return "Trung"
    return "Nam"


PROV = {}
for code, v in _t.items():
    nm = v["name"]
    PROV[code] = dict(name=nm, type=v["type"], region=region_of(code))
# tên nói của tỉnh/thành
def prov_spoken(code):
    p = PROV[code]
    if p["type"] == "thanh-pho":
        return "thành phố " + p["name"]
    return "tỉnh " + p["name"]


TYPE_WORD = {"quan": "quận", "huyen": "huyện", "thi-xa": "thị xã", "thanh-pho": "thành phố"}
DISTRICTS = []  # (raw, spoken_needs_num, province_code, region)
for code, v in _q.items():
    pc = v["parent_code"]
    DISTRICTS.append(dict(type=TYPE_WORD[v["type"]], name=v["name"], prov=pc, region=PROV[pc]["region"]))
SRC["tinh_huyen"] = "GitHub madnh/hanhchinhvn (63 tỉnh, 705 quận/huyện trước sáp nhập 2025; giấy phép chưa rõ vì repo không có file LICENSE)"

# tên thành phố/tỉnh người ta hay nói (kèm vùng)
CITIES = [
    ("Hà Nội", "Bắc"), ("Hải Phòng", "Bắc"), ("Quảng Ninh", "Bắc"), ("Hạ Long", "Bắc"), ("Bắc Ninh", "Bắc"), ("Hải Dương", "Bắc"),
    ("Thái Nguyên", "Bắc"), ("Nam Định", "Bắc"), ("Ninh Bình", "Bắc"), ("Lào Cai", "Bắc"), ("Sa Pa", "Bắc"), ("Vĩnh Phúc", "Bắc"),
    ("Thanh Hóa", "Trung"), ("Vinh", "Trung"), ("Hà Tĩnh", "Trung"), ("Đồng Hới", "Trung"), ("Huế", "Trung"), ("Đà Nẵng", "Trung"),
    ("Hội An", "Trung"), ("Quảng Ngãi", "Trung"), ("Quy Nhơn", "Trung"), ("Tuy Hòa", "Trung"), ("Nha Trang", "Trung"), ("Phan Thiết", "Nam"),
    ("Đà Lạt", "Trung"), ("Buôn Ma Thuột", "Trung"), ("Pleiku", "Trung"), ("Kon Tum", "Trung"),
    ("Sài Gòn", "Nam"), ("thành phố Hồ Chí Minh", "Nam"), ("Biên Hòa", "Nam"), ("Vũng Tàu", "Nam"), ("Thủ Dầu Một", "Nam"), ("Tây Ninh", "Nam"),
    ("Mỹ Tho", "Nam"), ("Cần Thơ", "Nam"), ("Long Xuyên", "Nam"), ("Rạch Giá", "Nam"), ("Cà Mau", "Nam"), ("Bạc Liêu", "Nam"), ("Sóc Trăng", "Nam"),
    ("Vĩnh Long", "Nam"), ("Trà Vinh", "Nam"), ("Bến Tre", "Nam"), ("Phú Quốc", "Nam"),
]
SRC["cities"] = "Danh sách tự biên theo thành phố, tỉnh lỵ thường được nhắc; đối chiếu một phần với tinh_huyen"
CITY_NAMES = [c for c, _ in CITIES]

# ------------------------------------------------------------------ đường theo thành phố (tự biên từ kiến thức; chưa đối chiếu OSM vì mạng bị chặn)
# (city_for_alley_word, {city_name: [đường]}) alley term: Bắc ngõ, Nam hẻm, Trung kiệt/hẻm
STREETS = {
    "Hà Nội": ("Bắc", "ngõ", [
        "phố Chùa Bộc", "đường Giải Phóng", "đường Láng", "đường Nguyễn Trãi", "đường Trần Duy Hưng", "đường Phạm Văn Đồng", "phố Lê Duẩn",
        "phố Kim Mã", "đường Hoàng Quốc Việt", "đường Xuân Thủy", "phố Cầu Giấy", "phố Tây Sơn", "phố Thái Hà", "đường Lạc Long Quân",
        "phố Nguyễn Chí Thanh", "đường Trường Chinh", "phố Minh Khai", "phố Bạch Mai", "phố Đại Cồ Việt", "phố Hàng Bông", "phố Huế",
        "phố Trần Hưng Đạo", "phố Lý Thường Kiệt", "đường Nguyễn Văn Cừ", "đường Tôn Đức Thắng", "phố Hồ Tùng Mậu", "phố Lê Văn Lương",
        "phố Khuất Duy Tiến", "phố Nguyễn Xiển", "đường Quang Trung", "đường Tố Hữu", "đường Võ Chí Công", "đường Thanh Niên", "đường Âu Cơ",
        "phố Nghi Tàm", "phố Yên Phụ", "phố Hàng Đào", "phố Tràng Tiền", "phố Phan Đình Phùng", "phố Nguyễn Thái Học", "phố Giảng Võ",
        "phố Đội Cấn", "phố Hào Nam", "phố Nguyễn Lương Bằng", "phố Tây Hồ", "phố Ngọc Hà", "phố Nguyễn Khang", "phố Trung Kính", "phố Duy Tân",
        "đường Phạm Hùng", "đường Lê Trọng Tấn", "đường Nguyễn Văn Linh", "phố Ngô Gia Tự", "phố Nguyễn Sơn", "phố Vũ Tông Phan",
    ]),
    "Hải Phòng": ("Bắc", "ngõ", ["đường Lạch Tray", "đường Lê Hồng Phong", "đường Điện Biên Phủ", "đường Tô Hiệu", "đường Trần Nguyên Hãn", "đường Nguyễn Bỉnh Khiêm", "đường Lê Lai", "đường Cát Dài", "đường Phạm Văn Đồng", "đường Ngô Quyền"]),
    "Quảng Ninh": ("Bắc", "ngõ", ["đường Trần Hưng Đạo", "đường Lê Thánh Tông", "đường Nguyễn Văn Cừ", "đường Hạ Long", "đường Bạch Đằng"]),
    "Huế": ("Trung", "kiệt", ["đường Lê Lợi", "đường Hùng Vương", "đường Nguyễn Huệ", "đường Trần Hưng Đạo", "đường Phạm Văn Đồng", "đường Hà Nội", "đường Lý Thường Kiệt", "đường Bà Triệu", "đường Điện Biên Phủ", "đường Nguyễn Sinh Cung", "đường Phan Bội Châu", "đường Đội Cung"]),
    "Đà Nẵng": ("Trung", "kiệt", ["đường Bạch Đằng", "đường Nguyễn Văn Linh", "đường Lê Duẩn", "đường Hùng Vương", "đường Trần Phú", "đường Ngô Quyền", "đường Nguyễn Tất Thành", "đường Điện Biên Phủ", "đường Hai Tháng Chín", "đường Phạm Văn Đồng", "đường Ông Ích Khiêm", "đường Hoàng Diệu", "đường Võ Nguyên Giáp", "đường Lê Đại Hành", "đường Trần Cao Vân", "đường Nguyễn Hữu Thọ"]),
    "Nha Trang": ("Trung", "hẻm", ["đường Trần Phú", "đường Nguyễn Thị Minh Khai", "đường Lê Thánh Tôn", "đường Hùng Vương", "đường Phạm Văn Đồng", "đường Thái Nguyên", "đường Yersin", "đường Điện Biên Phủ"]),
    "Vinh": ("Trung", "ngõ", ["đường Lê Lợi", "đường Quang Trung", "đường Lê Duẩn", "đường Nguyễn Sỹ Sách", "đường Trường Thi"]),
    "Sài Gòn": ("Nam", "hẻm", [
        "đường Nguyễn Huệ", "đường Lê Lợi", "đường Điện Biên Phủ", "đường Cách Mạng Tháng Tám", "đường Võ Văn Tần", "đường Nguyễn Thị Minh Khai",
        "đường Lý Tự Trọng", "đường Hai Bà Trưng", "đường Nam Kỳ Khởi Nghĩa", "đường Trường Chinh", "đường Cộng Hòa", "đường Hoàng Văn Thụ",
        "đường Phan Xích Long", "đường Nguyễn Kiệm", "đường Lê Quang Định", "đường Xô Viết Nghệ Tĩnh", "đường Nguyễn Hữu Cảnh", "đường Phạm Văn Đồng",
        "đường Võ Văn Kiệt", "đường Nguyễn Tri Phương", "đường Ba Tháng Hai", "đường Sư Vạn Hạnh", "đường Nguyễn Thị Thập", "đường Huỳnh Tấn Phát",
        "đường Lê Văn Việt", "đường Võ Thị Sáu", "đường Tô Hiến Thành", "đường Nguyễn Văn Cừ", "đường Trần Hưng Đạo", "đường Lê Văn Sỹ",
        "đường Hoàng Hoa Thám", "đường Bạch Đằng", "đường Phan Đăng Lưu", "đường Quang Trung", "đường Lê Đức Thọ", "đường Nguyễn Oanh",
        "đường Phạm Ngũ Lão", "đường Đinh Tiên Hoàng", "đường Nguyễn Văn Linh", "đường Nguyễn Thị Định", "đường Mai Chí Thọ", "đường An Dương Vương",
        "đường Tên Lửa", "đường Lũy Bán Bích", "đường Âu Cơ", "đường Lạc Long Quân", "đường Tân Kỳ Tân Quý", "đường Thích Quảng Đức",
    ]),
    "Cần Thơ": ("Nam", "hẻm", ["đường Nguyễn Văn Cừ", "đường Ba Mươi Tháng Tư", "đường Trần Hưng Đạo", "đường Mậu Thân", "đường Nguyễn Trãi", "đường Hòa Bình", "đường Võ Văn Kiệt", "đường Cách Mạng Tháng Tám", "đường Nguyễn Văn Linh"]),
    "Biên Hòa": ("Nam", "hẻm", ["đường Phạm Văn Thuận", "đường Võ Thị Sáu", "đường Đồng Khởi", "đường Nguyễn Ái Quốc", "đường Hà Huy Giáp"]),
    "Vũng Tàu": ("Nam", "hẻm", ["đường Thùy Vân", "đường Trần Phú", "đường Lê Hồng Phong", "đường Hạ Long", "đường Nguyễn Thái Học"]),
}
SRC["streets"] = "Tự biên theo kiến thức tên đường phổ biến ở 11 thành phố; địa chỉ ghép số nhà là giả định, không khẳng định tồn tại; chưa đối chiếu OpenStreetMap vì mạng ngoài danh sách cho phép bị chặn"

# ------------------------------------------------------------------ địa điểm (POI)
# (tên nói, loại, thành phố, vùng)
POIS = []


def poi(kind, items, region, city):
    for it in items:
        POIS.append(dict(name=it, kind=kind, city=city, region=region))


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
poi("bến xe", ["bến xe Mỹ Đình", "bến xe Giáp Bát", "bến xe Nước Ngầm", "bến xe Yên Nghĩa"], "Bắc", "Hà Nội")
poi("bến xe", ["bến xe Miền Đông", "bến xe Miền Tây"], "Nam", "Sài Gòn")
poi("bến xe", ["bến xe trung tâm Đà Nẵng"], "Trung", "Đà Nẵng")
poi("bệnh viện", ["bệnh viện Bạch Mai", "bệnh viện Việt Đức", "bệnh viện Nhi Trung ương", "bệnh viện K", "bệnh viện Quân y 108", "bệnh viện Phụ sản Trung ương", "bệnh viện Hữu Nghị", "bệnh viện Thanh Nhàn", "bệnh viện Đại học Y Hà Nội"], "Bắc", "Hà Nội")
poi("bệnh viện", ["bệnh viện Chợ Rẫy", "bệnh viện Từ Dũ", "bệnh viện Nhi Đồng 1", "bệnh viện Nhân dân 115", "bệnh viện Thống Nhất", "bệnh viện Đại học Y Dược"], "Nam", "Sài Gòn")
poi("bệnh viện", ["bệnh viện Trung ương Huế"], "Trung", "Huế")
poi("bệnh viện", ["bệnh viện Đà Nẵng"], "Trung", "Đà Nẵng")
poi("bệnh viện", ["bệnh viện Đa khoa Cần Thơ"], "Nam", "Cần Thơ")
poi("trường đại học", ["Đại học Bách khoa Hà Nội", "Đại học Quốc gia Hà Nội", "Đại học Kinh tế Quốc dân", "Đại học Xây dựng", "Đại học Sư phạm Hà Nội", "Đại học Ngoại thương", "Đại học Y Hà Nội"], "Bắc", "Hà Nội")
poi("trường đại học", ["Đại học Bách khoa thành phố Hồ Chí Minh", "Đại học Quốc gia thành phố Hồ Chí Minh", "Đại học Kinh tế thành phố Hồ Chí Minh", "Đại học Sư phạm thành phố Hồ Chí Minh"], "Nam", "Sài Gòn")
poi("trường đại học", ["Đại học Huế"], "Trung", "Huế")
poi("trường đại học", ["Đại học Bách khoa Đà Nẵng", "Đại học Đà Nẵng"], "Trung", "Đà Nẵng")
poi("trung tâm thương mại", ["Vincom Center Bà Triệu", "Royal City", "Aeon Mall Long Biên", "Aeon Mall Hà Đông", "Lotte Center Hà Nội", "Times City"], "Bắc", "Hà Nội")
poi("trung tâm thương mại", ["Aeon Mall Tân Phú", "Crescent Mall", "Vincom Center Đồng Khởi", "Saigon Centre", "Landmark 81", "Vạn Hạnh Mall", "Gigamall", "Sala"], "Nam", "Sài Gòn")
poi("trung tâm thương mại", ["Vincom Plaza Đà Nẵng", "Vincom Plaza Huế", "Indochina Riverside"], "Trung", "Đà Nẵng")
poi("danh thắng", ["Hồ Hoàn Kiếm", "Văn Miếu Quốc Tử Giám", "Lăng Chủ tịch Hồ Chí Minh", "Hồ Tây", "Chùa Hương", "Hoàng thành Thăng Long", "Nhà hát Lớn Hà Nội", "Chùa Một Cột", "Phố cổ Hà Nội", "Vườn quốc gia Ba Vì"], "Bắc", "Hà Nội")
poi("danh thắng", ["vịnh Hạ Long", "Sa Pa", "Tràng An", "Tam Cốc", "Yên Tử"], "Bắc", "Quảng Ninh")
poi("danh thắng", ["Đại Nội Huế", "chùa Thiên Mụ", "lăng Khải Định", "lăng Tự Đức", "cầu Trường Tiền"], "Trung", "Huế")
poi("danh thắng", ["Bà Nà Hills", "cầu Rồng", "bán đảo Sơn Trà", "Ngũ Hành Sơn", "bãi biển Mỹ Khê", "cầu Vàng"], "Trung", "Đà Nẵng")
poi("danh thắng", ["phố cổ Hội An", "Mỹ Sơn"], "Trung", "Hội An")
poi("danh thắng", ["chợ Bến Thành", "Dinh Độc Lập", "Nhà thờ Đức Bà", "phố đi bộ Nguyễn Huệ", "Bưu điện Thành phố", "Thảo Cầm Viên", "Đầm Sen", "Suối Tiên", "Bến Bạch Đằng", "Bảo tàng Chứng tích Chiến tranh", "chợ Bình Tây", "công viên Tao Đàn"], "Nam", "Sài Gòn")
poi("danh thắng", ["chợ nổi Cái Răng", "bến Ninh Kiều"], "Nam", "Cần Thơ")
poi("danh thắng", ["hồ Xuân Hương", "Thung lũng Tình Yêu", "thác Datanla"], "Trung", "Đà Lạt")
poi("danh thắng", ["tháp Bà Ponagar", "Vinpearl Nha Trang"], "Trung", "Nha Trang")
poi("khu đô thị", ["khu đô thị Ecopark", "khu đô thị Vinhomes Ocean Park", "khu đô thị Times City", "khu đô thị Ciputra"], "Bắc", "Hà Nội")
poi("khu đô thị", ["khu đô thị Phú Mỹ Hưng", "khu đô thị Sala", "Vinhomes Grand Park", "Vinhomes Central Park"], "Nam", "Sài Gòn")
POI_SPOKEN_FIX = {"Nhi Đồng 1": "Nhi Đồng một", "Landmark 81": "Landmark tám mươi mốt", "Quân y 108": "Quân y một trăm lẻ tám", "Nhân dân 115": "Nhân dân một trăm mười lăm"}
SRC["pois"] = "Tự biên theo kiến thức địa danh phổ biến (sân bay, ga, bến xe, bệnh viện, trường, trung tâm thương mại, danh thắng); tên là tên riêng đã dùng rộng rãi, cần kiểm tên hiện hành trước khi dùng thật"

# nơi đã lưu
HOME_LIKE = ["nhà", "nhà", "nhà ba mẹ", "nhà ngoại", "nhà ông bà", "nhà bà nội", "nhà bà ngoại", "nhà anh trai", "nhà chị gái", "nhà em gái", "nhà bố mẹ vợ"]
PLACE_LIKE = ["cơ quan", "công ty", "trường", "văn phòng", "xưởng", "cửa hàng", "kho hàng", "chi nhánh", "trường mẫu giáo", "trường cấp ba", "phòng khám", "phòng tập"]
HOME_LIKE = ["nhà", "nhà ba mẹ", "nhà ngoại", "nhà ông bà", "nhà bà nội", "nhà bà ngoại", "nhà anh trai", "nhà chị gái", "nhà em gái", "nhà bố mẹ vợ"]
SRC["saved"] = "Tự biên (nhãn nơi lưu thông dụng)"

# ------------------------------------------------------------------ tên người, xưng hô
MALE = ["Hùng", "Minh", "Tuấn", "Dũng", "Nam", "Long", "Hải", "Đức", "Thành", "Quang", "Phong", "Sơn", "Bình", "Cường", "Khánh", "Huy", "Trung", "Tâm", "Việt", "Hiếu", "Khoa", "Tùng", "Thắng", "Phúc", "Lộc", "Tài", "Nghĩa", "Hoàng", "Đạt", "Kiên", "Toàn", "Vinh", "Duy", "Bảo", "Hậu", "Lâm", "Quân", "Tiến", "Hiệp", "Thịnh"]
FEMALE = ["Lan", "Hoa", "Mai", "Hương", "Thu", "Trang", "Ngọc", "Linh", "Hạnh", "Thảo", "Phương", "Huyền", "Yến", "Nhung", "Loan", "Hằng", "Vân", "Oanh", "Diệp", "Quyên", "Thủy", "Nga", "Dung", "Châu", "Tuyết", "Liên", "Hiền", "My", "Ly", "Trâm", "Nhi", "Hồng", "Cúc", "Đào", "Giang", "Hà", "Thanh", "Tâm", "Uyên", "Vy"]
SURNAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
MID_M = ["Văn", "Đức", "Minh", "Quốc", "Hữu", "Thành", "Anh", "Xuân"]
MID_F = ["Thị", "Thu", "Ngọc", "Thanh", "Kim", "Mai", "Hồng", "Bích"]
SRC["names"] = "Tự biên: họ, tên đệm, tên phổ biến; tên là giả định, không dùng tên người có thật"
HON_PEER = {"M": ["anh"], "F": ["chị"]}
HON_ELDER = {"M": ["chú", "bác", "cậu", "thầy"], "F": ["cô", "dì", "bác", "mợ", "cô giáo"]}
# gọi theo thứ tự sinh (Nam Bộ): anh Hai, chị Ba, chú Tư, dì Năm
BIRTH = ["Hai", "Ba", "Tư", "Năm", "Sáu", "Bảy", "Tám", "Chín", "Mười"]
SRC["birth_order"] = "Cách gọi theo thứ tự sinh ở Nam Bộ (anh Hai, chị Ba, chú Tư...) – cần người bản ngữ Nam Bộ duyệt"
CONTEXT_TAGS = ["công ty", "hàng xóm", "cũ", "trường", "bên bảo hiểm", "đối tác", "bên kho", "ở quê", "bạn học", "bên kế toán"]

# ------------------------------------------------------------------ giải trí
GENRES = ["nhạc trữ tình", "nhạc vàng", "nhạc bolero", "nhạc trẻ", "nhạc rock", "nhạc pop", "nhạc dân ca", "nhạc cách mạng", "nhạc không lời", "nhạc EDM", "nhạc Hàn", "nhạc Hoa", "nhạc Âu Mỹ", "nhạc thiếu nhi", "nhạc cổ điển", "nhạc jazz", "nhạc lofi", "nhạc thư giãn", "nhạc sôi động", "nhạc buồn", "nhạc ru ngủ", "nhạc đường dài", "nhạc remix", "nhạc acoustic", "nhạc quê hương", "nhạc Trịnh", "nhạc hip hop", "nhạc rap Việt", "nhạc tiền chiến", "nhạc đỏ"]
MOODS = ["vui vẻ", "thư giãn", "tập trung", "lãng mạn", "buồn", "sôi động", "nhẹ nhàng", "tỉnh táo", "dễ ngủ", "hoài niệm", "tràn đầy năng lượng", "yên tĩnh"]
PLAYLISTS = ["Chill cuối tuần", "Đường dài", "Buổi sáng tỉnh táo", "Yêu thích", "Mới nghe gần đây", "Nhạc đi làm", "Cho chuyến đi xa", "Nhạc về quê", "Buổi tối thư giãn", "Gia đình cùng nghe", "Nhạc cho bé", "Nhạc chạy xe đêm", "Top nhạc tuần này", "Nhạc không lời lái xe", "Hit một thời"]
PODCAST = ["tin tức buổi sáng", "sách nói", "truyện audio", "podcast kinh doanh", "podcast lịch sử", "bản tin giao thông", "truyện cổ tích", "chương trình ngoại ngữ", "tin thể thao", "tin công nghệ"]
SRC["entertainment"] = "Tự biên: thể loại, tâm trạng, tên danh sách phát chung (không dùng tên bài hay nghệ sĩ cụ thể để tránh vướng bản quyền)"
# đài: (tên nói, tần số MHz hoặc None, vùng phát)
RADIO = [("VOV Giao thông", 91.0, None), ("VOV ba", 102.7, None), ("VOV hai", 96.5, None), ("VOV Một", None, None), ("VOV Giao thông Hà Nội", 91.0, "Bắc"), ("VOV Giao thông Sài Gòn", 91.0, "Nam"), ("VOH", 99.9, "Nam"), ("VOV năm", 105.5, "Bắc")]
SRC["radio"] = "Wikipedia 'List of radio stations in Vietnam' (đọc qua công cụ tóm tắt, chưa đối chiếu nguồn gốc); tần số khác nhau theo địa phương nên chỉ giữ cặp ổn định; đã bỏ VOV Một có tần số vì khác nhau theo thành phố"

# ------------------------------------------------------------------ xe
SEATS = ["ghế lái", "ghế phụ", "ghế sau bên trái", "ghế sau bên phải", "ghế hành khách phía trước"]
SEATS_SHORT = ["ghế lái", "ghế phụ", "ghế sau trái", "ghế sau phải"]
WINDOWS = ["cửa sổ phía lái", "cửa sổ phụ", "cửa sổ sau trái", "cửa sổ sau phải"]  # dùng với {L:win}
TIRES = ["lốp trước bên trái", "lốp trước bên phải", "lốp sau bên trái", "lốp sau bên phải", "lốp dự phòng"]
VENTS = ["hướng lên mặt", "hướng xuống chân", "hướng vào kính chắn gió", "hướng cả mặt và chân", "hướng kính và chân"]
SRC["car"] = "Tự biên theo các tính năng phổ biến trên xe du lịch; chưa đối chiếu với tài liệu hãng cụ thể"

# ------------------------------------------------------------------ đường quốc lộ/cao tốc
HIGHWAYS = ["quốc lộ 1A", "quốc lộ 5", "quốc lộ 6", "quốc lộ 18", "quốc lộ 22", "quốc lộ 51", "quốc lộ 13", "quốc lộ 14", "quốc lộ 32", "quốc lộ 3",
            "cao tốc Hà Nội – Hải Phòng", "cao tốc Pháp Vân – Cầu Giẽ", "cao tốc Hà Nội – Lào Cai", "cao tốc Thành phố Hồ Chí Minh – Trung Lương",
            "cao tốc Thành phố Hồ Chí Minh – Long Thành – Dầu Giây", "cao tốc Đà Nẵng – Quảng Ngãi", "cao tốc Cam Lộ – La Sơn", "cao tốc Hạ Long – Hải Phòng",
            "cao tốc Hà Nội – Thái Nguyên", "cao tốc Nội Bài – Lào Cai", "đại lộ Thăng Long", "đường vành đai ba", "đường vành đai hai", "đường vành đai bốn"]
SRC["highways"] = "Tự biên theo tên tuyến phổ biến; tuyến cao tốc mới có thể thay đổi, cần cập nhật"

# ------------------------------------------------------------------ danh mục tìm quanh đây
NEARBY = ["quán cà phê", "nhà hàng", "quán phở", "quán bún chả", "quán cơm", "hiệu thuốc", "bệnh viện", "ngân hàng", "cây ATM", "siêu thị", "cửa hàng tiện lợi",
          "bãi đỗ xe", "trạm dừng chân", "nhà vệ sinh công cộng", "tiệm sửa xe", "tiệm rửa xe", "trạm kiểm định", "chợ", "công viên", "khách sạn", "nhà nghỉ", "quán ăn gia đình", "tiệm bánh", "cửa hàng hoa", "tiệm cắt tóc", "phòng khám", "bưu điện", "đồn công an"]
SRC["nearby"] = "Tự biên: danh mục địa điểm hay tìm khi đang lái xe"
