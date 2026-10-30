# -*- coding: utf-8 -*-
"""Ứng viên địa danh để sinh câu. Tác giả soạn từ kiến thức chung; chỉ dùng sau khi qua bước kiểm (file verified_places.json).
Mỗi mục: tên đúng như viết. Không ghi số nhà, không ghép đường với phường."""

# đường (hoặc phố) nổi tiếng theo thành phố (tên gọi quen thuộc, không gồm tiền tố)
STREETS = {
    "Hà Nội": [
        "Nguyễn Trãi", "Giải Phóng", "Láng Hạ", "Trần Duy Hưng", "Phạm Văn Đồng", "Xuân Thủy", "Cầu Giấy", "Kim Mã",
        "Hoàng Quốc Việt", "Lê Duẩn", "Tây Sơn", "Chùa Bộc", "Nguyễn Chí Thanh", "Đê La Thành", "Trường Chinh", "Phạm Hùng",
        "Lê Văn Lương", "Tôn Đức Thắng", "Hàng Bài", "Tràng Tiền", "Lý Thường Kiệt", "Bà Triệu", "Nguyễn Văn Cừ", "Võ Chí Công",
        "Khuất Duy Tiến", "Nguyễn Xiển", "Minh Khai", "Đại Cồ Việt", "Hoàng Hoa Thám", "Thụy Khuê", "Lạc Long Quân", "Âu Cơ",
        "Nghi Tàm", "Yên Phụ", "Hồ Tùng Mậu", "Lê Đức Thọ", "Mễ Trì", "Thái Hà", "Kim Ngưu", "Bạch Mai", "Huế", "Hàng Bông",
        "Hàng Gai", "Hàng Đào", "Đinh Tiên Hoàng", "Lê Thái Tổ", "Hai Bà Trưng", "Trần Hưng Đạo", "Lò Đúc", "Văn Cao",
        "Hoàng Minh Giám", "Xã Đàn", "Khâm Thiên", "Phan Chu Trinh", "Lê Thánh Tông", "Nguyễn Du", "Ngô Gia Tự", "Ngọc Hồi",
    ],
    "Thành phố Hồ Chí Minh": [
        "Nguyễn Huệ", "Lê Lợi", "Điện Biên Phủ", "Cách Mạng Tháng Tám", "Võ Văn Kiệt", "Nguyễn Văn Linh", "Phạm Văn Đồng",
        "Xô Viết Nghệ Tĩnh", "Nguyễn Thị Minh Khai", "Trường Chinh", "Lê Văn Việt", "Hoàng Văn Thụ", "Lê Văn Sỹ", "Nam Kỳ Khởi Nghĩa",
        "Võ Thị Sáu", "Pasteur", "Hai Bà Trưng", "Nguyễn Thị Thập", "Huỳnh Tấn Phát", "Mai Chí Thọ", "Võ Nguyên Giáp", "Tôn Đức Thắng",
        "Hoàng Diệu", "Lý Thường Kiệt", "Nguyễn Trãi", "Trần Hưng Đạo", "Đinh Tiên Hoàng", "Nguyễn Đình Chiểu", "Phan Đăng Lưu",
        "Bạch Đằng", "Quang Trung", "Cộng Hòa", "Hoàng Hoa Thám", "Trường Sơn", "Phan Xích Long", "Lạc Long Quân", "Âu Cơ",
        "Lũy Bán Bích", "Kinh Dương Vương", "Nguyễn Hữu Cảnh", "Đồng Khởi", "Nguyễn Du", "Hàm Nghi", "Võ Văn Tần", "Nguyễn Văn Trỗi",
        "Phổ Quang", "Nguyễn Kiệm", "Lê Đức Thọ", "Nguyễn Oanh", "An Dương Vương", "Tô Hiến Thành", "Ba Tháng Hai", "Sư Vạn Hạnh",
        "Hồng Bàng", "Trần Phú", "Nguyễn Thái Học", "Phạm Ngũ Lão", "Bùi Viện", "Lê Thánh Tôn",
    ],
    "Đà Nẵng": [
        "Bạch Đằng", "Nguyễn Văn Linh", "Lê Duẩn", "Điện Biên Phủ", "Hai Tháng Chín", "Trần Phú", "Nguyễn Tất Thành", "Võ Nguyên Giáp",
        "Hoàng Sa", "Ngô Quyền", "Phạm Văn Đồng", "Hùng Vương", "Lê Đình Lý", "Hải Phòng", "Nguyễn Hữu Thọ", "Trưng Nữ Vương",
        "Phan Châu Trinh", "Lý Tự Trọng", "Nguyễn Chí Thanh", "Núi Thành", "Duy Tân", "Hoàng Diệu", "Trần Cao Vân", "Ông Ích Khiêm",
        "Tôn Đản", "Cách Mạng Tháng Tám", "Trường Sa", "Nguyễn Lương Bằng", "Tôn Đức Thắng", "Nguyễn Sinh Sắc",
    ],
    "Huế": [
        "Lê Lợi", "Hùng Vương", "Trần Hưng Đạo", "Nguyễn Huệ", "Phạm Văn Đồng", "Điện Biên Phủ", "Bạch Đằng", "Hà Nội",
        "Nguyễn Sinh Cung", "Phan Bội Châu", "Bến Nghé", "Lý Thường Kiệt", "Tô Hiến Thành", "Bà Triệu", "Chi Lăng", "Mai Thúc Loan",
        "Đặng Thai Mai", "Nguyễn Chí Diểu",
    ],
    "Hải Phòng": [
        "Lạch Tray", "Điện Biên Phủ", "Lê Hồng Phong", "Trần Phú", "Nguyễn Đức Cảnh", "Tô Hiệu", "Cầu Đất", "Hoàng Diệu", "Lê Lai",
        "Trường Chinh", "Phạm Văn Đồng", "Nguyễn Văn Linh", "Hùng Vương", "Tôn Đức Thắng", "Lê Thánh Tông", "Lê Chân",
    ],
    "Cần Thơ": [
        "Nguyễn Văn Cừ", "Ba Mươi Tháng Tư", "Hòa Bình", "Trần Hưng Đạo", "Mậu Thân", "Võ Văn Kiệt", "Nguyễn Trãi", "Lý Tự Trọng",
        "Cách Mạng Tháng Tám", "Nguyễn Việt Hồng", "Quang Trung", "Đề Thám", "Trần Văn Khéo", "Phan Đình Phùng",
    ],
    "Nha Trang": [
        "Trần Phú", "Nguyễn Thiện Thuật", "Thống Nhất", "Lê Hồng Phong", "Phạm Văn Đồng", "Hai Mươi Ba Tháng Mười", "Yersin", "Hùng Vương",
        "Nguyễn Tất Thành", "Lê Thánh Tôn", "Quang Trung", "Ngô Gia Tự",
    ],
    "Đà Lạt": [
        "Trần Phú", "Phan Đình Phùng", "Hoàng Văn Thụ", "Hai Bà Trưng", "Bùi Thị Xuân", "Yersin", "Xô Viết Nghệ Tĩnh", "Hồ Tùng Mậu",
        "Lê Đại Hành", "Nguyễn Văn Cừ", "Trần Hưng Đạo", "Ba Tháng Tư", "Khe Sanh",
    ],
    "Vũng Tàu": [
        "Trần Phú", "Thùy Vân", "Hạ Long", "Lê Hồng Phong", "Nguyễn An Ninh", "Hoàng Hoa Thám", "Thống Nhất", "Bình Giã", "Lê Lợi",
        "Quang Trung", "Nam Kỳ Khởi Nghĩa",
    ],
}
# đường có số trong tên: (viết gốc, cách đọc)
STREETS_NUM = {
    "Đà Nẵng": [("2 Tháng 9", "Hai Tháng Chín")],
    "Cần Thơ": [("30 Tháng 4", "Ba Mươi Tháng Tư")],
    "Nha Trang": [("23 Tháng 10", "Hai Mươi Ba Tháng Mười")],
    "Đà Lạt": [("3 Tháng 4", "Ba Tháng Tư")],
}

# địa điểm theo loại: (tên, thành phố/tỉnh gần nhất)
AIRPORTS = [
    ("sân bay Nội Bài", "Hà Nội"), ("sân bay Tân Sơn Nhất", "Thành phố Hồ Chí Minh"), ("sân bay Đà Nẵng", "Đà Nẵng"),
    ("sân bay Cam Ranh", "Khánh Hòa"), ("sân bay Phú Bài", "Huế"), ("sân bay Cát Bi", "Hải Phòng"), ("sân bay Vinh", "Nghệ An"),
    ("sân bay Liên Khương", "Lâm Đồng"), ("sân bay Buôn Ma Thuột", "Đắk Lắk"), ("sân bay Pleiku", "Gia Lai"),
    ("sân bay Phù Cát", "Gia Lai"), ("sân bay Tuy Hòa", "Đắk Lắk"), ("sân bay Cần Thơ", "Cần Thơ"), ("sân bay Phú Quốc", "An Giang"),
    ("sân bay Côn Đảo", "Thành phố Hồ Chí Minh"), ("sân bay Chu Lai", "Đà Nẵng"), ("sân bay Đồng Hới", "Quảng Trị"),
    ("sân bay Thọ Xuân", "Thanh Hóa"), ("sân bay Vân Đồn", "Quảng Ninh"),
]
STATIONS = [
    ("ga Hà Nội", "Hà Nội"), ("ga Sài Gòn", "Thành phố Hồ Chí Minh"), ("ga Đà Nẵng", "Đà Nẵng"), ("ga Huế", "Huế"), ("ga Vinh", "Nghệ An"),
    ("ga Nha Trang", "Khánh Hòa"), ("ga Hải Phòng", "Hải Phòng"), ("ga Giáp Bát", "Hà Nội"), ("ga Long Biên", "Hà Nội"),
    ("ga Biên Hòa", "Đồng Nai"), ("ga Thanh Hóa", "Thanh Hóa"), ("ga Đồng Hới", "Quảng Trị"),
]
BUS_STATIONS = [
    ("bến xe Mỹ Đình", "Hà Nội"), ("bến xe Giáp Bát", "Hà Nội"), ("bến xe Gia Lâm", "Hà Nội"), ("bến xe Nước Ngầm", "Hà Nội"),
    ("bến xe Yên Nghĩa", "Hà Nội"), ("bến xe Miền Đông", "Thành phố Hồ Chí Minh"), ("bến xe Miền Tây", "Thành phố Hồ Chí Minh"),
    ("bến xe An Sương", "Thành phố Hồ Chí Minh"), ("bến xe trung tâm Đà Nẵng", "Đà Nẵng"), ("bến xe Cần Thơ", "Cần Thơ"),
]
HOSPITALS = [
    ("bệnh viện Bạch Mai", "Hà Nội"), ("bệnh viện Việt Đức", "Hà Nội"), ("bệnh viện Nhi Trung ương", "Hà Nội"),
    ("bệnh viện Phụ sản Trung ương", "Hà Nội"), ("bệnh viện Hữu Nghị", "Hà Nội"), ("bệnh viện Chợ Rẫy", "Thành phố Hồ Chí Minh"),
    ("bệnh viện Từ Dũ", "Thành phố Hồ Chí Minh"), ("bệnh viện Nhi Đồng 1", "Thành phố Hồ Chí Minh"),
    ("bệnh viện Nhi Đồng 2", "Thành phố Hồ Chí Minh"), ("bệnh viện Phạm Ngọc Thạch", "Thành phố Hồ Chí Minh"),
    ("bệnh viện Trung ương Huế", "Huế"), ("bệnh viện Đà Nẵng", "Đà Nẵng"), ("bệnh viện Thống Nhất", "Thành phố Hồ Chí Minh"),
]
UNIVERSITIES = [
    ("Đại học Bách khoa Hà Nội", "Hà Nội"), ("Đại học Kinh tế Quốc dân", "Hà Nội"), ("Đại học Quốc gia Hà Nội", "Hà Nội"),
    ("Đại học Sư phạm Hà Nội", "Hà Nội"), ("Đại học Ngoại thương", "Hà Nội"), ("Đại học Bách khoa Thành phố Hồ Chí Minh", "Thành phố Hồ Chí Minh"),
    ("Đại học Tôn Đức Thắng", "Thành phố Hồ Chí Minh"), ("Đại học Huế", "Huế"), ("Đại học Đà Nẵng", "Đà Nẵng"), ("Đại học Cần Thơ", "Cần Thơ"),
]
LANDMARKS = [
    ("Hồ Hoàn Kiếm", "Hà Nội"), ("Văn Miếu Quốc Tử Giám", "Hà Nội"), ("Lăng Chủ tịch Hồ Chí Minh", "Hà Nội"),
    ("Hoàng thành Thăng Long", "Hà Nội"), ("Nhà hát Lớn Hà Nội", "Hà Nội"), ("cầu Long Biên", "Hà Nội"), ("Hồ Tây", "Hà Nội"),
    ("chợ Đồng Xuân", "Hà Nội"), ("Dinh Độc Lập", "Thành phố Hồ Chí Minh"), ("chợ Bến Thành", "Thành phố Hồ Chí Minh"),
    ("Nhà thờ Đức Bà", "Thành phố Hồ Chí Minh"), ("Landmark 81", "Thành phố Hồ Chí Minh"), ("Thảo Cầm Viên", "Thành phố Hồ Chí Minh"),
    ("cầu Rồng", "Đà Nẵng"), ("Bà Nà Hills", "Đà Nẵng"), ("Ngũ Hành Sơn", "Đà Nẵng"), ("bán đảo Sơn Trà", "Đà Nẵng"),
    ("bãi biển Mỹ Khê", "Đà Nẵng"), ("phố cổ Hội An", "Đà Nẵng"), ("Đại Nội Huế", "Huế"), ("chùa Thiên Mụ", "Huế"), ("vịnh Hạ Long", "Quảng Ninh"),
    ("Tràng An", "Ninh Bình"), ("Phong Nha", "Quảng Trị"), ("Sa Pa", "Lào Cai"), ("đỉnh Fansipan", "Lào Cai"), ("hồ Xuân Hương", "Đà Lạt"),
    ("tháp Bà Ponagar", "Nha Trang"), ("Mũi Né", "Lâm Đồng"), ("bến Ninh Kiều", "Cần Thơ"), ("chợ nổi Cái Răng", "Cần Thơ"),
]
