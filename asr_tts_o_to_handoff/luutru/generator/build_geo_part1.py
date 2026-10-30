# -*- coding: utf-8 -*-
# Part 1: sources, provinces
SRC = {}
def src(i, url, what, fetched=True):
    SRC[i] = {"id": i, "url": url, "what": what, "fetched": fetched}

src("G1","https://thuvienphapluat.vn/hoi-dap-phap-luat/danh-sach-34-tinh-thanh-sau-sap-nhap-tu-bac-vao-nam-gom-nhung-tinh-thanh-nao-138070718.html","Danh sách 34 đơn vị cấp tỉnh + tỉnh cũ gộp vào; căn cứ Điều 1 Nghị quyết 202/2025/QH15 (28 tỉnh + 6 thành phố)")
src("G2","https://thuvienphapluat.vn/phap-luat-nha-dat/danh-sach-34-tinh-thanh-sau-sap-nhap-theo-vung-mien-cap-nhat-moi-nhat-2026-15983.html","34 đơn vị chia 6 vùng kinh tế - xã hội, hiệu lực 01/07/2025 (23 đơn vị hợp nhất, 11 không sáp nhập)")
src("G3","https://thuvienphapluat.vn/hoi-dap-phap-luat/danh-sach-3321-dvhc-cap-xa-cua-34-tinh-thanh-sau-sap-nhap-2025-chi-tiet-ra-sao-138053823.html","3.321 ĐVHC cấp xã; số phường/xã của Hà Nội 126, TP.HCM 168, Hải Phòng 114, Đà Nẵng 94, Huế 40, Cần Thơ 103")
src("G4","https://en.wikipedia.org/wiki/Voice_of_Vietnam","Wikipedia EN Voice of Vietnam: kênh VOV và tần số FM (VOV3 102.7; VOVGT 91 HN/HCM; Mekong FM 90; VOV5 105.5/105.7; FM89; English 24/7 104)")
src("G5","https://en.wikipedia.org/wiki/List_of_radio_stations_in_Vietnam","Wikipedia EN danh sách đài/trạm phát lại VOV, VOH, Đài Hà Nội... theo trạm phát (Tam Đảo, Mễ Trì, Quán Tre, Sơn Trà, Bạch Mã, VN2 Cần Thơ...). Có thể lỗi thời")
src("G6","https://thuvienphapluat.vn/hoi-dap-phap-luat/tan-so-cac-kenh-chuong-trinh-thuoc-dai-tieng-noi-viet-nam-tai-da-nang-nam-2018-218947.html","Tần số VOV tại Đà Nẵng theo Phụ lục II Thông tư 37/2017/TT-BTTTT (hiệu lực 23/01/2018)")
src("G7","https://voh.com.vn/radio/nghe-radio-truc-tuyen-02240315000000002.html","Trang VOH liệt kê kênh FM: VOH 95.6/99.9/87.7, Hà Nội HTV 90/96, Đà Nẵng DRT 98.5, Huế TRT 93.0, Cần Thơ 93.7, Khánh Hòa 106.5, Nghệ An 99.6...")
src("G8","https://voh.com.vn/gioi-thieu.html","VOH giới thiệu: FM 99.9, FM 95.6 (giao thông/đô thị), FM 87.7, AM 610 kHz")
src("G9","https://vov.vn/xa-hoi/thuong-hieu-vov-giao-thong-128958.vov","Bài VOV 11/12/2009: VOV Giao thông TP.HCM FM 91 và 94 MHz khi ra mắt (có thể đã đổi)")
src("G10","https://en.wikipedia.org/wiki/Expressways_of_Vietnam","Wikipedia EN: CT.01-CT.43, chiều dài và tình trạng (có thể lỗi thời)")
src("G11","https://www.vietnamplus.vn/dua-vao-khai-thac-3345km-cao-toc-viet-nam-tiep-tuc-mo-rong-ha-tang-giao-thong-post1122973.vnp","VietnamPlus 08/07/2026: 3.345 km cao tốc đang khai thác; Bắc-Nam phía Đông thông Lạng Sơn - Cà Mau; Quảng Ngãi-Hoài Nhơn; Cầu Giẽ-Ninh Bình giảm tốc độ từ 120 xuống 100 km/h từ 12/10")
src("G12","https://baodauthau.vn/mang-luoi-cao-toc-hien-dai-va-xung-tam-nhan-len-khat-vong-phat-trien-post191691.html","Báo Đấu thầu: tình trạng Bắc-Nam phía Đông, Vành đai 3 TP.HCM, Bến Lức-Long Thành, Biên Hòa-Vũng Tàu, Châu Đốc-Cần Thơ-Sóc Trăng, Cam Lộ-La Sơn...")
src("G13","https://en.wikipedia.org/wiki/National_Route_1_(Vietnam)","Wikipedia EN QL1: 2.482 km, Hữu Nghị Quan - Năm Căn (Cà Mau)")
src("G14","https://vietnamnews.vn/society/381960/new-tunnel-route-in-central-vn-to-open-soon.html","Vietnam News 2017: QL1A, hầm Đèo Cả, đèo Cổ Mã, hầm Hải Vân, đèo Phước Tượng, Phú Gia, đèo Ngang")
src("G15","https://nhadautu.vn/tu-deo-ca-len-huu-nghi-quan-d17355.html","Nhà đầu tư: hầm Đèo Cả 4.125 m, Cổ Mã 500 m, Cù Mông 2.600 m (Bình Định-Phú Yên)")
src("G16","https://en.wikipedia.org/wiki/H%E1%BA%A3i_V%C3%A2n_Tunnel","Wikipedia EN: hầm Hải Vân 6.280 m, mở 2005; hầm thứ hai mở 2021, QL1")
src("G17","https://vov.vn/xa-hoi/khanh-hoa-nghiem-cam-phuong-tien-qua-deo-khanh-le-khi-co-mua-lon-post1143494.vov","VOV 20/12/2024: đèo Khánh Lê thuộc QL27C, Khánh Vĩnh (Khánh Hòa), nối Nha Trang - Đà Lạt")
src("G18","https://plo.vn/tphcm-tap-trung-xu-ly-un-tac-giao-thong-tai-336-diem-co-nguy-co-post876613.html","PLO: điểm nghẽn TP.HCM (QL13, Xa lộ Hà Nội, Cộng Hòa, Phạm Văn Đồng, Võ Văn Kiệt, Nguyễn Văn Linh, cầu Bình Triệu, Phú Cường, QL1, QL51, QL22, nút giao An Phú, cảng Cát Lái...)")
src("G19","https://tuoitre.vn/tp-hcm-se-lap-them-camera-o-cac-nut-that-giao-thong-20251016170740729.htm","Tuổi Trẻ 16/10/2025: nút thắt An Phú, Mỹ Thủy, QL13, QL1...")
src("G20","https://vietnamnet.vn/ha-noi-sat-tet-tac-tu-ngo-ra-pho-tu-trua-den-dem-506096.html","Vietnamnet: điểm kẹt xe Hà Nội (hầm Kim Liên, Xã Đàn, Đại Cồ Việt, Tây Sơn, Nguyễn Trãi, Chùa Bộc, Khuất Duy Tiến...)")
src("G21","https://thuvienphapluat.vn/phap-luat-nha-dat/moi-nhat-ban-do-vanh-dai-1-ha-noi-vanh-dai-1-ha-noi-gom-nhung-tuyen-duong-pho-nao-5526.html","Các phố thuộc Vành đai 1 Hà Nội")
src("G22","https://nhadautu.vn/diem-mat-nhung-cung-duong-day-dac-du-an-bat-dong-san-o-ha-noi-d757.html","Tên đường Hà Nội: Lê Văn Lương, Võ Chí Công, Đại lộ Thăng Long, Tố Hữu, Trần Duy Hưng, Phạm Hùng...")
src("G23","https://baovanhoa.vn/van-hoa/dat-ten-va-dieu-chinh-42-ten-duong-ten-pho-o-ha-noi-43333.html","Báo Văn hóa: đặt tên/điều chỉnh 42 đường phố Hà Nội")
src("G24","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-cau-giay","Bảng giá đất Hà Nội, quận Cầu Giấy (đã hết hiệu lực 01/01/2026, trước sáp nhập; bảng bị cắt, theo thứ tự chữ cái)")
src("G25","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-hoan-kiem","Bảng giá đất Hà Nội, quận Hoàn Kiếm (hết hiệu lực; bị cắt)")
src("G26","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-dong-da","Bảng giá đất Hà Nội, quận Đống Đa (hết hiệu lực; bị cắt)")
src("G27","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-ba-dinh","Bảng giá đất Hà Nội, quận Ba Đình (hết hiệu lực; bị cắt)")
src("G28","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-hai-ba-trung","Bảng giá đất Hà Nội, quận Hai Bà Trưng (hết hiệu lực; bị cắt)")
src("G29","https://thuviennhadat.vn/bang-gia-dat/ha-noi/quan-tay-ho","Bảng giá đất Hà Nội, quận Tây Hồ (hết hiệu lực; bị cắt)")
src("G30","https://en.wikipedia.org/wiki/Hanoi","Wikipedia EN Hà Nội: danh thắng, cầu, ga Hà Nội (Hàng Cỏ), trường đại học, sân vận động, metro 2A/3")
src("G31","https://en.wikipedia.org/wiki/List_of_universities_in_Vietnam","Wikipedia EN danh sách trường đại học theo thành phố")
src("G32","https://en.wikipedia.org/wiki/List_of_hospitals_in_Vietnam","Wikipedia EN danh sách bệnh viện (rất ít mục: Bạch Mai, Chợ Rẫy...)")
src("G33","https://en.wikipedia.org/wiki/List_of_airports_in_Vietnam","Wikipedia EN danh sách sân bay Việt Nam, mã IATA, tỉnh")
src("G34","https://en.wikipedia.org/wiki/List_of_shopping_malls_in_Vietnam","Wikipedia EN danh sách trung tâm thương mại (Aeon, Vincom, Parkson, Lotte...; có thể lỗi thời)")
src("G35","https://en.wikipedia.org/wiki/Ho_Chi_Minh_City","Wikipedia EN TP.HCM: Nguyễn Huệ, Bùi Viện, Phạm Ngũ Lão, Chợ Bến Thành, Landmark 81, Bitexco, Chợ Rẫy, Tân Sơn Nhất, Ga Sài Gòn...")
src("G36","https://en.wikipedia.org/wiki/Da_Nang","Wikipedia EN Đà Nẵng: cầu Rồng, Sông Hàn, Trần Thị Lý, Thuận Phước, Cầu Vàng, hầm Hải Vân, Bà Nà, Ngũ Hành Sơn, bệnh viện, đại học")
src("G37","https://en.wikipedia.org/wiki/Hu%E1%BA%BF","Wikipedia EN Huế: Đại Nội, chùa Thiên Mụ, cầu Trường Tiền, ga Huế, Bệnh viện Trung ương Huế, Đại học Huế, sân bay Phú Bài")
src("G38","https://en.wikipedia.org/wiki/Haiphong","Wikipedia EN Hải Phòng: cầu Bính, QL5, QL10, Cát Bi, cảng, Nhà hát Lớn, Cát Bà, Đồ Sơn...")
src("G39","https://en.wikipedia.org/wiki/C%E1%BA%A7n_Th%C6%A1","Wikipedia EN Cần Thơ: cầu Cần Thơ, bến Ninh Kiều, chợ nổi Cái Răng, ĐH Cần Thơ, sân bay quốc tế Cần Thơ")
src("G40","https://thuviennhadat.vn/bang-gia-dat/thua-thien-hue/thanh-pho-hue","Bảng giá đất TP Huế (hết hiệu lực; 2.582 dòng, đã đọc phần đầu theo vần)")
src("G41","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-1","Bảng giá đất TP.HCM, Quận 1 cũ (hết hiệu lực; bị cắt)")
src("G42","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-binh-thanh","Bảng giá đất TP.HCM, Bình Thạnh cũ (bị cắt)")
src("G43","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-tan-binh","Bảng giá đất TP.HCM, Tân Bình cũ (bị cắt)")
src("G44","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-3","Bảng giá đất TP.HCM, Quận 3 cũ (bị cắt)")
src("G45","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-phu-nhuan","Bảng giá đất TP.HCM, Phú Nhuận cũ (bị cắt)")
src("G46","https://thuviennhadat.vn/bang-gia-dat/ho-chi-minh/quan-7","Bảng giá đất TP.HCM, Quận 7 cũ (bị cắt)")
src("G47","https://vietnamfinance.vn/nhung-tuyen-duong-co-gia-dat-dat-do-nhat-da-nang-d129416.html","Vietnamfinance: đường Đà Nẵng giá đất cao (Bạch Đằng, Nguyễn Văn Linh, Trần Phú, Lê Duẩn, 2/9...)")
src("G48","https://baovanhoa.vn/kinh-te/da-nang-dieu-chinh-gia-dat-nhieu-tuyen-pho-trung-tam-tang-manh-147388.html","Báo Văn hóa: đường Đà Nẵng điều chỉnh giá đất")
src("G49","https://tuoitre.vn/duong-dep-nhat-da-nang-co-he-so-gia-dat-chenh-1-toi-2-9-2023122212053991.htm","Tuổi Trẻ 2023: đường Đà Nẵng (Bạch Đằng, Lê Duẩn, Nguyễn Văn Linh, Nguyễn Du, Võ Nguyên Giáp, Phạm Văn Đồng, Võ Văn Kiệt)")
src("G50","https://thuviennhadat.vn/bang-gia-dat/da-nang/quan-hai-chau","Bảng giá đất Đà Nẵng, Hải Châu cũ (chủ yếu tên khu dân cư; có nhắc đường 2/9, Lê Thanh Nghị, Thăng Long, Phan Bội Châu, Trần Quý Cáp, Nguyễn Phi Khanh, Nguyễn Văn Linh)")
src("G51","https://thuviennhadat.vn/bang-gia-dat/da-nang/quan-thanh-khe","Bảng giá đất Đà Nẵng, Thanh Khê cũ (nhắc Điện Biên Phủ, Trường Chinh, Trần Cao Vân, Lê Đình Lý, Nguyễn Tất Thành, Lê Duẩn)")
src("G52","https://thuviennhadat.vn/bang-gia-dat/da-nang/quan-son-tra","Bảng giá đất Đà Nẵng, Sơn Trà cũ (Hồ Nghinh, Mỹ Khê, Ngô Quang Huy, cầu Sông Hàn/Trần Thị Lý/Rồng)")
src("G53","https://thuviennhadat.vn/bang-gia-dat/hai-phong/quan-le-chan","Bảng giá đất Hải Phòng, trang quận Lê Chân (bị cắt)")
src("G54","https://thuviennhadat.vn/bang-gia-dat/hai-phong/quan-hong-bang","Bảng giá đất Hải Phòng, trang quận Hồng Bàng (bị cắt)")
src("G55","https://thuviennhadat.vn/bang-gia-dat/can-tho/quan-ninh-kieu","Bảng giá đất Cần Thơ, Ninh Kiều cũ (bị cắt)")
src("G56","https://thuviennhadat.vn/bang-gia-dat/khanh-hoa/thanh-pho-nha-trang","Bảng giá đất TP Nha Trang (bị cắt; 2.554 dòng; lẫn tên làng/xã)")
src("G57","https://thuviennhadat.vn/bang-gia-dat/nghe-an/thanh-pho-vinh","Bảng giá đất TP Vinh (chỉ lấy được vài tên: Nguyễn Trường Tộ, Trần Bình Trọng, Nguyễn Hiền, Nguyễn Xuân Linh)")
src("G58","https://thuviennhadat.vn/bang-gia-dat/lam-dong/thanh-pho-da-lat","Bảng giá đất TP Đà Lạt (bị cắt)")
src("G59","https://caselaw.vn/van-ban-phap-luat/157805-quyet-dinh-298-qd-ubnd-nam-2015-ve-cong-nhan-cac-tuyen-truc-duong-pho-chinh-tren-dia-ban-thanh-pho-da-lat-tinh-lam-dong","Quyết định 298/QĐ-UBND (2015): công nhận 34 tuyến đường chính TP Đà Lạt")
src("G60","https://thuvienphapluat.vn/van-ban/Van-hoa-Xa-hoi/Quyet-dinh-773-1998-QD-UB-doi-dat-ten-duong-pho-Buon-Ma-Thuot-Dak-Lak-280438.aspx","Quyết định 773/1998/QĐ-UB đổi/đặt tên đường phố Buôn Ma Thuột (văn bản 1998; có thể đã thay đổi sau này)")
src("G61","https://hethongphapluat.com/nghi-quyet-353-2010-nq-hdnd-ve-dat-doi-ten-duong-tren-dia-ban-thanh-pho-vinh-tinh-nghe-an-dot-iv.html","Nghị quyết 353/2010/NQ-HĐND đặt tên đường TP Vinh đợt IV (trích đoạn)")
src("G62","https://lsvn.vn/tp-vinh-nhieu-tuyen-duong-ngap-sau-anh-huong-giao-thong-sinh-hoat-cua-nguoi-dan-a126454.html","LSVN: Đại lộ Lê Nin, Hồng Bàng, Phan Bội Châu (TP Vinh)")
src("G63","https://vnexpress.net/thanh-pho-vinh-ngap-nang-3997790.html","VnExpress: Vinh ngập nặng - Nguyễn Thị Minh Khai, Đặng Thái Thân, Phan Bội Châu, Đinh Công Tráng, Lê Ninh, Phong Định Cảng, Quang Trung")
src("G64","https://vnexpress.net/quy-nhon-lung-linh-ve-dem-4693493.html","VnExpress: Quy Nhơn - Nguyễn Tất Thành, Nguyễn Thiếp, Xuân Diệu, vòng xoay Lê Hồng Phong - Trần Hưng Đạo, quảng trường Nguyễn Tất Thành")
src("G65","https://www.greensm.com/vn-vi/news/buoi-toi-o-quy-nhon-nen-di-dau","Greensm: Quy Nhơn - Xuân Diệu, An Dương Vương, Nguyễn Huệ, Trần Phú, Lê Đức Thọ, Ngô Văn Sở, cầu Thị Nại, Ghềnh Ráng, Bãi Xép")
src("G66","https://daibieunhandan.vn/nha-trang-nhu-ten-mot-co-gai-10103699.html","Đại biểu Nhân dân: Nha Trang - Đại lộ Nguyễn Tất Thành, Trần Phú, Hòn Chồng, Tháp Trầm Hương, Quảng trường 2 tháng 4")
src("G67","https://vinpearl.com/vi/kinh-nghiem-kham-pha-duong-tran-phu-nha-trang-sam-uat-nhat-pho-bien","Vinpearl: đường Trần Phú, Thái Nguyên, Lê Thánh Tôn, vòng xoay Ngã 6, nhà ga Nha Trang, Nhà thờ Núi, Viện Hải dương học, Chợ đêm")
src("G68","https://vov.vn/xa-hoi/khanh-hoa-chinh-thuc-co-dai-lo-mang-ten-dai-tuong-vo-nguyen-giap-729301.vov","VOV: đại lộ Võ Nguyên Giáp (Nha Trang - Diên Khánh, ~10 km, mở 02/2018)")
src("G69","https://en.wikipedia.org/wiki/Nha_Trang","Wikipedia EN Nha Trang: Tháp Bà Ponagar, Hòn Chồng, chùa Long Sơn, ga Nha Trang, ĐH Nha Trang, sân bay Cam Ranh")
src("G70","https://en.wikipedia.org/wiki/Vinh","Wikipedia EN Vinh: Lenin, Phan Bội Châu, Quang Trung, ga Vinh, sân bay Vinh, Quảng trường Hồ Chí Minh, các bến xe...")
src("G71","https://en.wikipedia.org/wiki/Da_Lat","Wikipedia EN Đà Lạt: hồ Xuân Hương, ga Đà Lạt, Crazy House, Dinh III, nhà thờ chính tòa, Chợ Đà Lạt")
src("G72","https://en.wikipedia.org/wiki/Quy_Nh%C6%A1n","Wikipedia EN Quy Nhơn: sân bay Phù Cát, ga Quy Nhơn, ga Diêu Trì, cảng Quy Nhơn, ĐH Quy Nhơn")
src("G73","https://en.wikipedia.org/wiki/Bu%C3%B4n_Ma_Thu%E1%BB%99t","Wikipedia EN Buôn Ma Thuột: tượng đài Chiến thắng (Ngã 6), Bản Đôn, Bảo tàng Thế giới Cà phê, sân bay")
src("G74","https://thuviennhadat.vn/bang-gia-dat/binh-dinh/thanh-pho-quy-nhon","Bảng giá đất trang TP Quy Nhơn (3.482 dòng, bị cắt; độ tin cậy trung bình)")
src("G75","https://thuviennhadat.vn/bang-gia-dat/dak-lak/thanh-pho-buon-ma-thuot","Bảng giá đất TP Buôn Ma Thuột (bị cắt; 2.709 dòng)")
src("G76","https://plo.vn/dat-ten-moi-cho-78-duong-o-tp-buon-ma-thuot-post796570.html","PLO: đặt tên 78 đường ở BMT; Y Ngông, Nguyễn Đình Chiểu, Trần Nhật Duật, Nguyễn Hồng Ưng")
src("G77","https://mia.vn/cam-nang-du-lich/thong-tin-ve-ben-xe-my-dinh-15514","Mia.vn: Bến xe Mỹ Đình (20 Phạm Hùng), nhắc bến Giáp Bát, Nước Ngầm, Gia Lâm, Yên Nghĩa")
src("G78","https://vietnamnews.vn/society/793302/viet-nam-s-biggest-bus-station-opens-in-hcm-city.html","Vietnam News: Bến xe Miền Đông mới (501 Hoàng Hữu Nam, mở 10/10/2020); nhắc Miền Tây, An Sương, Ngã Tư Ga")
src("G79","https://nhathuoclongchau.com.vn/bai-viet/benh-vien-tuyen-trung-uong-la-gi-danh-sach-benh-vien-tuyen-trung-uong-hien-nay.html","Danh sách 34 BV trung ương Bộ Y tế + 5 BV Bộ Quốc phòng (Bạch Mai, Việt Đức, K, E, Nhi TW, Hữu Nghị, TW Huế, C Đà Nẵng, ĐK TW Cần Thơ...)")
src("G80","https://baohiemxahoidientu.vn/bhxh/benh-vien-tuyen-trung-uong.html","BHXH điện tử: danh sách BV tuyến trung ương")
src("G81","https://en.wikipedia.org/wiki/Ho_Chi_Minh_City_Metro_Line_1","Wikipedia EN Metro số 1 Bến Thành - Suối Tiên, 14 ga, khai thác từ 22/12/2024")
src("G82","https://en.wikipedia.org/wiki/Hanoi_Metro","Wikipedia EN Metro Hà Nội: tuyến 2A Cát Linh - Hà Đông (từ 11/2021), tuyến 3 Nhổn - ga Hà Nội (đoạn trên cao từ 08/2024)")
src("G83","https://viettimes.vn/2-ong-lon-xang-dau-pv-oil-va-petrolimex-kinh-doanh-ra-sao-post194695.html","Viettimes 12/02/2026: Petrolimex >5.500 cửa hàng (~50%), PVOIL >900 (~20%), nhắc Thanh Lễ, Saigon Petro, Mipec; tổng ~17.200 cây xăng")
src("G84","https://tuoitre.vn/den-luot-shell-gas-roi-thi-truong-vn-515499.htm","Tuổi Trẻ 12/10/2012: Shell bán mảng gas tại VN cho Siam Gas; chỉ nói tập trung dầu nhờn (không xác nhận có trạm xăng Shell)")
src("G85","https://bizhub.vietnamnews.vn/v-green-to-invest-380-million-in-nationwide-super-charging-network-post400452.html","Bizhub 19/03/2026: V-GREEN đầu tư 99 trạm sạc siêu nhanh dọc quốc lộ/tỉnh lộ ở 34 tỉnh thành năm 2026")
src("G86","https://vtcnews.vn/v-green-va-vnpt-phat-trien-mang-luoi-tram-sac-tu-doi-pin-xe-dien-tren-toan-quoc-ar1020102.html","VTC 26/05/2026: V-GREEN hợp tác VNPT, mục tiêu 60.000 tủ đổi pin, 150.000 cổng sạc")
src("G87","https://doanhnghiephoinhap.vn/thi-truong-chuoi-ca-phe-viet-nam-chung-kien-giai-doan-phat-trien-manh-me-60461.html","Bài ngày 16/08/2024: Highlands ~800 cửa hàng, Trung Nguyên E-Coffee 676, Phúc Long 174 + 62 kiosk, The Coffee House 115 (thu hẹp), Katinat, Starbucks")
src("G88","https://doanhnghiephoinhap.vn/thi-truong-ban-le-viet-nam-tiep-da-tai-co-cau-manh-me.html","Bài 17/04/2021: VinMart -> WinMart; Big C -> GO!/Tops Market; Metro -> MM Mega Market; Auchan rút lui; Aeon mở rộng")
src("G89","https://baophapluat.vn/thuong-hieu-big-c-se-khong-con-o-viet-nam-post383926.html","Báo Pháp luật 04/03/2021: Big C đổi sang GO! và Tops Market")
src("G90","https://vietnamdrive.com/supermarkets-in-vietnam","VietnamDrive 01/2024: GO! 38 cửa hàng, Co.opmart 128, WinMart 3.586, Lotte Mart 15, MM Mega Market 21, Bách Hóa Xanh ~1.700, Emart 3, Aeon 8 TTTM")
src("G91","https://en.wikipedia.org/wiki/Tourism_in_Vietnam","Wikipedia EN du lịch VN: Sa Pa, Hạ Long, Đà Lạt, Phú Quốc, Hội An, Mũi Né, Huế, Ninh Bình, Côn Đảo, Cát Bà, Phong Nha, Đà Nẵng")
src("G92","https://en.wikipedia.org/wiki/Vietnam","Wikipedia EN Vietnam: Hạ Long, Phong Nha-Kẻ Bàng, Phú Quốc, Hội An, Cát Bà, đồng bằng sông Cửu Long")
src("G93","https://en.wikipedia.org/wiki/Sapa","Wikipedia EN Sa Pa: thị xã/phường thuộc tỉnh Lào Cai (chưa nhắc sáp nhập 2025)")
src("G94","https://en.wikipedia.org/wiki/Ph%C3%BA_Qu%E1%BB%91c","Wikipedia EN Phú Quốc: nay thuộc An Giang, đặc khu từ 16/06/2025")
src("G95","https://daibieunhandan.vn/chi-tiet-168-don-vi-hanh-chinh-cap-xa-cua-tp-ho-chi-minh-sau-hop-nhat-10371821.html","Đại biểu Nhân dân: 168 xã phường TP.HCM (phường Thủ Đức, Sài Gòn, Bến Thành, Tân Định, Bàn Cờ, Gia Định, Bình Thạnh, Tân Bình, Gò Vấp, Phú Nhuận, Tân Mỹ, Tân Hưng...). Đây là phương án sắp xếp")
src("G96","https://nhandan.vn/ha-noi-du-kien-ten-goi-126-xa-phuong-sau-sap-xep-post873727.html","Nhân Dân: phương án tên 47 phường nội đô Hà Nội (Hoàn Kiếm, Cửa Nam, Ba Đình, Cầu Giấy, Đống Đa, Láng, Ô Chợ Dừa, Kim Liên, Hai Bà Trưng, Tây Hồ, Thanh Xuân, Hà Đông, Long Biên...), họp 18/4/2025 - mới là dự kiến")
src("G97","https://daibieunhandan.vn/tp-ho-chi-minh-dat-lai-ten-59-tuyen-duong-dieu-chinh-ly-trinh-7-tuyen-10383920.html","Đại biểu Nhân dân 20/08/2025: TP.HCM đặt tên 59 đường mới, phường Sài Gòn (Nguyễn Thị Minh Khai, Nguyễn Đình Chiểu), Tân Hưng, Tân Thuận, An Phú Đông")
src("G98","https://thuviennhadat.vn/bang-gia-dat/da-nang","Bảng giá đất Đà Nẵng trang gốc (Liên Chiểu: Nguyễn Sinh Sắc, Lê Doãn Nhạ, Nguyễn Huy Tưởng...)")
src("G99","https://tuoitre.vn/starbucks-cham-moc-150-cua-hang-thi-truong-ghi-nhan-chuoi-ca-phe-trung-cao-cap-no-ro-20260101192014398.htm","Chỉ thấy tiêu đề kết quả tìm kiếm: Starbucks chạm mốc 150 cửa hàng (01/2026)",False)
src("G100","https://znews.vn/cay-xang-cua-saigon-petro-van-tap-nap-sau-khi-bi-tuoc-giay-phep-post1352677.html","Chỉ thấy tiêu đề kết quả tìm kiếm: cây xăng Saigon Petro vẫn tấp nập sau khi bị tước giấy phép (không rõ ngày)",False)
src("G101","https://vi.wikipedia.org/wiki/Danh_sách_đơn_vị_hành_chính_cấp_tỉnh_của_Việt_Nam","Wikipedia tiếng Việt (nhiều URL thử): WebFetch trả URL_NOT_FOUND, curl bị proxy chặn 403 -> không đọc được",False)
src("G102","https://baonghean.vn/en/thanh-pho-vinh-nhung-goc-nhin-moi-10078811.html","Báo Nghệ An EN: lỗi server khi fetch",False)
src("G103","https://vbpl.moj.gov.vn/FileData/TW/Lists/vbpq/Attachments/118156/VanBanGoc_NQ38%20BG9.pdf","Bị robots.txt chặn",False)
src("G104","https://lsvn.vn/le-cong-bo-quyet-dinh-benh-vien-huu-nghi-da-khoa-tinh-nghe-an-la-benh-vien-tuyen-cuoi-khu-vuc-bac-trung-bo1618158470-a102834.html","Chỉ thấy tiêu đề kết quả tìm kiếm: BV Hữu nghị Đa khoa Nghệ An là bệnh viện tuyến cuối khu vực Bắc Trung Bộ",False)

# ---------------- provinces ----------------
def prov(name, region, old, src_id="G1", verified=True, note=None, fullname=None):
    d = {"name": name, "region": region, "old_names": old, "verified": verified, "source": src_id}
    if fullname: d["official_name"] = fullname
    if note: d["note"] = note
    return d

P = []
P += [
 prov("Tuyên Quang","Bắc",["Hà Giang","Tuyên Quang"],note="Tên cũ Hà Giang vẫn dùng phổ biến (Hà Giang loop, Đồng Văn, Mèo Vạc)"),
 prov("Cao Bằng","Bắc",[],note="Không sáp nhập"),
 prov("Lai Châu","Bắc",[],note="Không sáp nhập"),
 prov("Lào Cai","Bắc",["Yên Bái","Lào Cai"],note="Sa Pa nay thuộc Lào Cai (cũ vẫn Lào Cai); Yên Bái, Nghĩa Lộ vẫn được gọi tên cũ"),
 prov("Thái Nguyên","Bắc",["Bắc Kạn","Thái Nguyên"]),
 prov("Điện Biên","Bắc",[],note="Không sáp nhập"),
 prov("Lạng Sơn","Bắc",[],note="Không sáp nhập"),
 prov("Sơn La","Bắc",[],note="Không sáp nhập"),
 prov("Phú Thọ","Bắc",["Hòa Bình","Vĩnh Phúc","Phú Thọ"],note="Tên cũ Vĩnh Phúc (Tam Đảo, Vĩnh Yên), Hòa Bình (Mai Châu) vẫn hay được gọi"),
 prov("Hà Nội","Bắc",[],fullname="Thành phố Hà Nội",note="Không sáp nhập"),
 prov("Hải Phòng","Bắc",["Hải Dương","Hải Phòng"],fullname="Thành phố Hải Phòng",note="Hải Dương cũ nay thuộc Hải Phòng"),
 prov("Bắc Ninh","Bắc",["Bắc Giang","Bắc Ninh"]),
 prov("Quảng Ninh","Bắc",[],note="Không sáp nhập (Hạ Long, Vân Đồn, Móng Cái)"),
 prov("Hưng Yên","Bắc",["Thái Bình","Hưng Yên"]),
 prov("Ninh Bình","Bắc",["Hà Nam","Nam Định","Ninh Bình"],note="Nam Định, Hà Nam cũ nay thuộc Ninh Bình"),
 prov("Thanh Hóa","Trung",[],note="Không sáp nhập"),
 prov("Nghệ An","Trung",[],note="Không sáp nhập (Vinh, Cửa Lò)"),
 prov("Hà Tĩnh","Trung",[],note="Không sáp nhập"),
 prov("Quảng Trị","Trung",["Quảng Bình","Quảng Trị"],note="Quảng Bình cũ (Đồng Hới, Phong Nha) nay thuộc Quảng Trị"),
 prov("Huế","Trung",["Thừa Thiên Huế"],fullname="Thành phố Huế",note="Thành phố trực thuộc trung ương; source G1 ghi 'không sáp nhập' (trước đó là tỉnh Thừa Thiên Huế)"),
 prov("Đà Nẵng","Trung",["Quảng Nam","Đà Nẵng"],fullname="Thành phố Đà Nẵng",note="Hội An, Tam Kỳ, Chu Lai, Điện Bàn (Quảng Nam cũ) nay thuộc Đà Nẵng"),
 prov("Quảng Ngãi","Trung",["Kon Tum","Quảng Ngãi"],note="Kon Tum nay thuộc Quảng Ngãi (Măng Đen, Đắk Glei); người dùng vẫn gọi 'Kon Tum'"),
 prov("Gia Lai","Trung",["Bình Định","Gia Lai"],note="Quy Nhơn (Bình Định cũ) nay thuộc Gia Lai"),
 prov("Đắk Lắk","Trung",["Phú Yên","Đắk Lắk"],note="Tuy Hòa (Phú Yên cũ) nay thuộc Đắk Lắk; Buôn Ma Thuột vẫn là Đắk Lắk"),
 prov("Khánh Hòa","Trung",["Ninh Thuận","Khánh Hòa"],note="Phan Rang - Tháp Chàm, Ninh Thuận cũ nay thuộc Khánh Hòa; Nha Trang, Cam Ranh vẫn Khánh Hòa"),
 prov("Lâm Đồng","Trung",["Đắk Nông","Bình Thuận","Lâm Đồng"],note="Phan Thiết, Mũi Né, Phú Quý (Bình Thuận cũ) và Gia Nghĩa (Đắk Nông cũ) nay thuộc Lâm Đồng; Đà Lạt vẫn Lâm Đồng"),
 prov("Đồng Nai","Nam",["Bình Phước","Đồng Nai"],note="Bình Phước (Đồng Xoài) nay thuộc Đồng Nai; sân bay Long Thành ở Đồng Nai"),
 prov("Tây Ninh","Nam",["Long An","Tây Ninh"],note="Long An (Tân An) nay thuộc Tây Ninh"),
 prov("TP Hồ Chí Minh","Nam",["Bình Dương","Bà Rịa - Vũng Tàu","TP Hồ Chí Minh"],fullname="Thành phố Hồ Chí Minh",note="Bình Dương (Thủ Dầu Một, Dĩ An, Thuận An) và Bà Rịa - Vũng Tàu (Vũng Tàu, Bà Rịa, Phú Mỹ, Long Điền, Côn Đảo) nay thuộc TP.HCM; người dùng vẫn gọi 'Bình Dương', 'Vũng Tàu'"),
 prov("Đồng Tháp","Nam",["Tiền Giang","Đồng Tháp"],note="Tiền Giang (Mỹ Tho) nay thuộc Đồng Tháp"),
 prov("An Giang","Nam",["Kiên Giang","An Giang"],note="Kiên Giang cũ (Rạch Giá, Phú Quốc, Hà Tiên) nay thuộc An Giang"),
 prov("Vĩnh Long","Nam",["Bến Tre","Trà Vinh","Vĩnh Long"],note="Bến Tre, Trà Vinh nay thuộc Vĩnh Long"),
 prov("Cần Thơ","Nam",["Sóc Trăng","Hậu Giang","Cần Thơ"],fullname="Thành phố Cần Thơ",note="Sóc Trăng, Hậu Giang nay thuộc Cần Thơ"),
 prov("Cà Mau","Nam",["Bạc Liêu","Cà Mau"],note="Bạc Liêu nay thuộc Cà Mau"),
]
# region note
PROV_NOTE = ("Vùng Bắc/Trung/Nam là phân loại ba miền truyền thống do người soạn gán (nguồn G2 chia 6 vùng kinh tế-xã hội). "
             "Số đơn vị cấp tỉnh: 34 = 28 tỉnh + 6 thành phố trực thuộc trung ương (Hà Nội, TP HCM, Hải Phòng, Huế, Đà Nẵng, Cần Thơ) theo Nghị quyết 202/2025/QH15; hiệu lực từ 01/07/2025 (G1, G2). "
             "Tên chính thức viết ngắn 'Hồ Chí Minh'/'Huế'... trong G2; G1 viết 'TP. Hồ Chí Minh'.")
