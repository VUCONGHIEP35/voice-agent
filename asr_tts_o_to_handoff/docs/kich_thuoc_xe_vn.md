# Kích thước các dòng xe phổ biến ở Việt Nam và tình trạng RIR thật (28/10/2026)

Báo cáo trả lời hai câu hỏi:
- Xe bán chạy ở Việt Nam có kích thước bao nhiêu?
- Dòng xe nào đã có RIR đo thật, dòng nào chưa?

Báo cáo này đi kèm `docs/xe_vn_va_rir.md`; tệp đó lý giải vì sao kho RIR đo hiện chỉ có 5 xe.

## Phạm vi và nguồn

- **Danh sách xe (43 dòng):**
  - 10 xe bán chạy nhất năm 2025;
  - xe bán chạy nhất của từng hãng trong 9 tháng 2026;
  - các đối thủ chính trong cùng phân khúc;
  - 5 xe có trong kho RIR đo.

  Danh sách không gồm mọi dòng xe đang bán ở Việt Nam. Xe sang (trừ V-Class), xe nhập số lượng nhỏ và xe thương mại (van chở hàng, xe tải nhẹ) không được đưa vào. Một số xe phổ biến cũng chưa có trong bảng; xem cuối mục 1.
- **Kích thước:** đều là kích thước ngoài (dài × rộng × cao, chiều dài cơ sở, đơn vị mm), lấy từ trang thông số kỹ thuật của bonbanh.com, đời mới nhất trang có (thường là 2026).
  - Khi một ô có nhiều giá trị theo phiên bản, báo cáo ghi giá trị đầu hoặc ghi cả dải.
  - Năm xe trong kho RIR đo lấy kích thước đúng đời đã đo, theo CarExpert, cars-data và VehicleSizes.
  - Số trên bonbanh là số tổng hợp, chưa đối chiếu với catalogue của hãng; sai lệch thường dưới 1%.
- **Kích thước khoang bên trong:** các hãng hầu như không công bố, nên báo cáo không có số này. Cách ước lượng nằm ở mục 4.
- **Doanh số:** theo báo chí tổng hợp số của VAMA và VinFast. Chỉ dùng để xếp hạng; các nguồn lệch nhau ở vài chỗ. Dấu "–" nghĩa là không có số trong nguồn đã đọc, không có nghĩa là bán ít.

## 1. Bảng chính: xe phổ biến ở Việt Nam

Cột "RIR thật":
- **Có, cùng dòng:** có RIR đo của chính dòng xe này, nhưng khác đời.
- **Không:** không có RIR đo công khai nào của dòng xe này.

Cột "Loại mô phỏng": loại khoang trong `LOAI_XE` (`tts_gen/cauhinh/tang_cuong.py`) gần nhất. "Chưa có" nghĩa là kho mô phỏng chưa có dạng khoang này.

| # | Xe (đời/thế hệ) | Dạng khoang | Dài × Rộng × Cao (mm) | Cơ sở (mm) | Chỗ | Doanh số tham khảo | RIR thật | Loại mô phỏng |
|---|---|---|---|---|---|---|---|---|
| | **Xe mini, hạng A** | | | | | | | |
| 1 | VinFast VF 3 (2024–) | Mini điện, 2 cửa | 3.190 × 1.679 × 1.622 | 2.075 | 4 | **44.585** (2025); **42.272** (9T/2026) | Không | hanga (dài hơn VF 3 thật) |
| 2 | VinFast VF 2 (2026) | Mini điện | 3.090 × 1.496 × 1.663 | 2.065 | 4 | – (mới bán) | Không | hanga |
| 3 | Kia Morning (thế hệ 3) | Hatchback A | 3.595 × 1.595 × 1.495 | 2.400 | 5 | – | Không | hanga |
| 4 | Hyundai Grand i10 (thế hệ 3, hatchback) | Hatchback A | 3.815 × 1.680 × 1.520 | 2.450 | 5 | – | Không | hanga |
| 5 | Toyota Wigo (thế hệ 2) | Hatchback A | 3.760 × 1.665 × 1.515 | 2.525 | 5 | – | Không | hanga |
| 6 | Suzuki Swift (thế hệ 4) | Hatchback B | 3.860 × 1.735 × 1.495 | 2.450 | 5 | – | Không | hanga |
| | **Sedan** | | | | | | | |
| 7 | Toyota Vios (2023–) | Sedan B | 4.425 × 1.730 × 1.475 | 2.550 | 5 | **13.424** (2025) | Không | sedan |
| 8 | Honda City (thế hệ 7) | Sedan B | 4.580 × 1.748 × 1.467 | 2.600 | 5 | **5.452** (9T/2026) | Không | sedan |
| 9 | Hyundai Accent (thế hệ 6) | Sedan B | 4.535 × 1.765 × 1.485 | 2.670 | 5 | – | Không | sedan |
| 10 | Mitsubishi Attrage (thế hệ 3) | Sedan B | 4.305 × 1.670 × 1.515 | 2.550 | 5 | – | Không | sedan |
| 11 | Mazda3 sedan (thế hệ 4) | Sedan C | 4.660 × 1.795 × 1.440 | 2.725 | 5 | – | Không | sedan |
| 12 | Kia K3 (thế hệ 4) | Sedan C | 4.640 × 1.800 × 1.450 | 2.700 | 5 | – | Không | sedan |
| | **SUV/CUV hạng A–B** | | | | | | | |
| 13 | VinFast VF 5 (2023–) | SUV A điện | 3.967 × 1.723 × 1.579 | 2.513 | 5 | **43.913** (2025) | Không | hanga/suv |
| 14 | Suzuki Fronx (2024–) | SUV A | 3.995 × 1.765 × 1.550 | 2.520 (*) | 5 | – | Không | suv |
| 15 | Kia Sonet (2024–) | SUV A | 4.120 × 1.790 × 1.642 | 2.500 | 5 | 1.152 (riêng tháng 9/2026) | Không | suv |
| 16 | Toyota Yaris Cross (2023–) | SUV B | 4.310 × 1.770 × 1.655 | 2.620 | 5 | **14.601** (2025); **12.646** (9T/2026) | Không | suv |
| 17 | Hyundai Creta (thế hệ 2) | SUV B | 4.330 × 1.790 × 1.660 | 2.610 | 5 | **6.849** (9T/2026) | Không | suv |
| 18 | Kia Seltos (2024–) | SUV B | 4.365 × 1.800 × 1.645 | 2.610 | 5 | **7.109** (9T/2026) | Không | suv |
| 19 | Mitsubishi Xforce (2023–) | SUV B | 4.390 × 1.810 × 1.660 | 2.650 | 5 | **15.254** (2025) | Không | suv |
| 20 | Honda HR-V (thế hệ 3) | SUV B | 4.347–4.385 × 1.790 × 1.590 | 2.610 | 5 | – | Không | suv |
| 21 | VinFast VF 6 (2024–) | SUV B điện | 4.241 × 1.834 × 1.580 | 2.730 | 5 | **23.291** (2025) | Không | suv |
| 22 | Toyota Corolla Cross (2020–) | SUV B+/C | 4.460 × 1.825 × 1.620 | 2.640 | 5 | – | Không | suv |
| | **SUV hạng C** | | | | | | | |
| 23 | Mazda CX-5 (thế hệ 2, KF) | SUV C | 4.590 × 1.845 × 1.680 | 2.700 | 5 | **17.262** (2025); **11.893** (9T/2026) | Không | suv |
| 24 | **Honda CR-V** (thế hệ 6, 2023–, lắp ráp trong nước) | SUV C, 5+2 chỗ | 4.691 × 1.866 × 1.681 | 2.701 | 7 | – | **Có, cùng dòng** (CAVEMOVE, CR-V 2009) | suv |
| 25 | Hyundai Tucson (thế hệ 4) | SUV C | 4.640 × 1.865 × 1.700 | 2.755 | 5 | – | Không | suv |
| 26 | Ford Territory (2025–) | SUV C | 4.685 × 1.935 × 1.706 | 2.726 | 5 | – | Không | suv (rộng hơn dải) |
| 27 | VinFast VF 7 (2023–) | SUV C điện | 4.545 × 1.890 × 1.635 | 2.840 | 5 | – | Không | suv |
| | **SUV hạng D, 7 chỗ** | | | | | | | |
| 28 | VinFast VF 8 (đời 2026) | SUV D điện | 4.701 × 1.872 × 1.670 | 2.840 | 5 | 1.494 (riêng tháng 9/2026) | Không | suv |
| 29 | Toyota Fortuner (thế hệ 2) | SUV D khung rời | 4.795 × 1.855 × 1.835 | 2.745 | 7 | – | Không | mpv (3 hàng ghế) |
| 30 | Ford Everest (thế hệ 3) | SUV D khung rời | 4.914 × 1.923 × 1.840 | 2.900 | 7 | – | Không | mpv (3 hàng ghế) |
| 31 | Hyundai Santa Fe (thế hệ 5) | SUV D | 4.830 × 1.900 × 1.770 | 2.815 | 7 | – | Không | mpv (3 hàng ghế) |
| 32 | Mitsubishi Destinator (2025–) | SUV 7 chỗ | 4.680 × 1.840 × 1.780 | 2.815 | 7 | – | Không | mpv |
| | **MPV** | | | | | | | |
| 33 | VinFast Limo Green (2025–) | MPV 7 chỗ điện | 4.740 × 1.872 × 1.723 | 2.840 | 7 | **27.127** (2025) | Không | mpv |
| 34 | Mitsubishi Xpander (bản Cross) | MPV 7 chỗ | 4.595 × 1.790 × 1.750 | 2.775 | 7 | **19.891** (2025); **10.496** (9T/2026) | Không | mpv |
| 35 | Toyota Innova Cross (AG10, 2023–) | MPV 7–8 chỗ | 4.755 × 1.850 × 1.790 | 2.850 | 7–8 | – | Không | mpv |
| 36 | Toyota Veloz Cross (2022–) | MPV 7 chỗ | 4.475 × 1.750 × 1.700 | 2.750 | 7 | – | Không | mpv |
| 37 | Suzuki XL7 (2020–) | MPV 7 chỗ | 4.450 × 1.775 × 1.710 | 2.740 | 7 | – | Không | mpv |
| 38 | Kia Carnival (thế hệ 4) | MPV cỡ lớn | 5.155 × 2.010 × 1.775 | 3.090 | 7–8 | – | Không | mpv (dài, rộng hơn dải) |
| 39 | **Mercedes V-Class** (W447, V300) | Van hạng sang | 5.140–5.370 × 1.928 × 1.910 | 3.200–3.430 | 6–7 | rất ít | **Có, cùng dòng** (McVAMPIRE; ANIR chưa xin) | mpv |
| | **Bán tải** | | | | | | | |
| 40 | Ford Ranger (thế hệ 4) | Bán tải cabin kép | 5.362 × 1.918 × 1.875 | 3.270 | 5 | **18.692** (2025); **9.835** (9T/2026) | Không | **Chưa có** |
| 41 | Toyota Hilux (thế hệ 9) | Bán tải cabin kép | 5.320 × 1.855 × 1.815 | 3.085 | 5 | – | Không | **Chưa có** |
| 42 | Mitsubishi Triton (thế hệ 6) | Bán tải cabin kép | 5.320–5.360 × 1.865–1.930 × 1.795–1.815 | 3.130 | 5 | – | Không | **Chưa có** |
| | **Hatchback hạng C** | | | | | | | |
| 43 | **VW Golf** (Mk8, nhập Đức, bán từ 31/10/2025) | Hatchback C | 4.286 × 1.789 × 1.458–1.491 | 2.619–2.628 | 5 | rất ít | **Có, cùng dòng** (CAVEMOVE, Golf 2011) | sedan |

(*) Bonbanh ghi chiều dài cơ sở của Fronx là 2.250 mm, trong khi chiều dài toàn xe là 3.995 mm; con số này có vẻ gõ nhầm. Báo cáo ghi 2.520 mm theo thông số hãng công bố ở thị trường khác. Cần kiểm lại.

Một số xe phổ biến chưa có trong bảng; tôi sẽ thêm nếu cần:
- Mazda2, Mazda CX-3, Mazda CX-30;
- Hyundai Stargazer, Hyundai Custin, Kia Carens;
- Honda BR-V, Honda Civic, Toyota Camry;
- VF 9.

**Tổng hợp:**
- Chỉ 3/43 dòng có RIR đo cùng dòng: CR-V, Golf, V-Class. Cả ba đều khác đời, và hai xe Golf, V-Class bán rất ít.
- Toàn bộ 10 xe bán chạy nhất năm 2025 đều không có RIR đo.

## 2. Năm xe trong kho RIR đo

| Khoang trong kho | Xe đã đo (đời) | Dài × Rộng × Cao (mm) | Cơ sở (mm) | Có ở Việt Nam? | Đời đang bán ở Việt Nam, so với đời đã đo |
|---|---|---|---|---|---|
| `do_crv` (train) | Honda CR-V 2009 (thế hệ 3, RE) | 4.520 × 1.820 × 1.680 | 2.620 | Có | Thế hệ 6 dài hơn 17 cm, rộng hơn 5 cm, cơ sở dài hơn 8 cm, thêm hàng ghế thứ 3 |
| `do_golf` (dev) | VW Golf 2011 (Mk6) | 4.199 × 1.785 × 1.479 | 2.574 | Có | Mk8 dài hơn 9 cm, cơ sở dài hơn 5 cm |
| `do_vclass` (train) | Mercedes V-Class (bộ dữ liệu không ghi đời) | khoảng 5.140–5.370 × 1.928 × 1.880–1.910 | 3.200–3.430 | Có | Cùng thế hệ W447 nếu đo sau 2014 (chưa kiểm) |
| `do_smart` (train) | Smart forfour 2019 (W453) | 3.495 × 1.665 × 1.554 | 2.494 | Không | Gần cỡ VF 3, Morning, i10 |
| `do_alfa` (train) | Alfa Romeo 146 (2000) | 4.250 × 1.712 × 1.420 | 2.540 | Không | Gần cỡ Golf và các sedan B, nhưng là hatchback |

## 3. So kích thước xe Việt Nam với kho RIR

Ghép theo cỡ ngoài (dài, cơ sở), đây là xe trong kho gần với từng nhóm xe Việt Nam nhất:

| Nhóm xe Việt Nam | Xe đo gần nhất về cỡ | Khác biệt chính |
|---|---|---|
| VF 3, VF 2 (dài khoảng 3,1–3,2 m, cao khoảng 1,62–1,66 m) | Smart forfour (3,5 m, 1,55 m) | VF 3 và VF 2 ngắn hơn nhưng cao hơn; khoang ngắn và cao |
| Hatchback A (Morning, i10, Wigo) | Smart forfour | Gần nhau |
| Sedan B (Vios, City, Accent) và VF 5 | Golf Mk6, Alfa 146 | Hai xe đo đều là hatchback, khoang hành lý không tách khỏi khoang người |
| SUV B (Yaris Cross, Xforce, Creta, Seltos, VF 6) | Golf Mk6, CR-V 2009 | Cỡ nằm giữa hai xe này |
| SUV C (CX-5, CR-V, Tucson, VF 7) | **CR-V 2009** | Khớp nhất trong kho |
| MPV 7 chỗ (Limo Green, Xpander, Innova Cross, Veloz, XL7) | V-Class | V-Class dài hơn 0,4–0,9 m, rộng hơn khoảng 0,1 m, cao hơn khoảng 0,15 m |
| SUV D 7 chỗ (Everest, Fortuner, Santa Fe) | V-Class, CR-V | Không có xe đo 3 hàng ghế cỡ này |
| Bán tải (Ranger, Hilux, Triton) | **Không có** | Khoang ngắn, có vách đứng ngay sau hàng ghế 2, không có khoang hành lý thông với khoang người |

## 4. Liên hệ với kho mô phỏng

Trước bản 3, `LOAI_XE` đặt dải kích thước **khoang trong** như sau (m):

| Loại | Dài | Rộng | Cao |
|---|---|---|---|
| hanga | 1,7–2,0 | 1,30–1,40 | 1,10–1,20 |
| sedan | 1,9–2,2 | 1,40–1,50 | 1,10–1,20 |
| suv | 2,0–2,5 | 1,45–1,60 | 1,20–1,35 |
| mpv | 2,4–2,8 | 1,45–1,60 | 1,20–1,35 |

Hãng không công bố kích thước khoang trong dạng hộp. Ở thị trường Mỹ và Úc, hãng có công bố một số kích thước nội thất. Tôi đã tra các số đó (28/10) để kiểm quy tắc ước:

| Xe | Rộng vai ghế trước (m) | Rộng ngoài (m) | Chênh (m) | Khoảng trần ghế trước (m) | Nguồn |
|---|---|---|---|---|---|
| Honda CR-V (2025) | 1,47 | 1,87 | 0,40 | 1,02 (không cửa sổ trời) | đại lý Honda Mỹ, iSeeCars |
| Mazda CX-5 (2024–2026) | 1,45–1,46 | 1,845 | 0,39 | 1,01 | đại lý Mazda Mỹ, iSeeCars |
| Kia Seltos (2021) | 1,41 | 1,80 | 0,39 | 1,02 | TrueDelta |
| Hyundai Accent sedan (2021) | 1,38 | 1,73 | 0,35 | 0,99 | TrueDelta |
| Hyundai Santa Fe (2024) | 1,51 | 1,90 | 0,39 | 1,02–1,04 | iSeeCars, TrueDelta |
| Ford Ranger cabin kép | 1,44 | 1,86 (không gương) | 0,42 | 1,02 | GoAuto (Úc, đời 2016); khoảng trần trước 1,02 m cũng là số Ford công bố cho đời mới |

Quy tắc dùng cho kho mô phỏng v3 (đã sửa quy tắc chiều cao so với bản đầu của mục này):
- **Rộng khoang** ≈ rộng ngoài − 0,35…0,42 m. Khớp cả sáu xe ở bảng trên.
- **Cao khoang** (sàn đến trần) ≈ cao ngoài − khoảng sáng gầm − khoảng 0,12 m. Kiểm bằng khoảng trần cộng độ cao đệm ghế: CR-V khoảng 1,35 m, Accent khoảng 1,22 m. Bản đầu của mục này trừ 0,40–0,50 m là quá tay với sedan.
- **Dài khoang** tính từ chân kính trước tới vách sau của khoang có người:
  - sedan: tới lưng ghế sau;
  - hatchback và SUV: thêm một phần khoang hành lý, vì phần này thông với khoang người;
  - xe 7 chỗ: tới sau hàng 3;
  - bán tải: tới vách cabin ngay sau hàng 2.

  Đây là nhận định của tôi, chưa có số đo.
- **Vị trí ghế** tính bằng mét:
  - miệng hàng 1 cách chân kính trước 0,70–0,95 m;
  - hàng 2 sau hàng 1 thêm 0,70–0,95 m, ước từ chỗ để chân hàng sau mà hãng công bố: Ranger 0,90 m, Seltos 0,97 m, Accent 0,85 m.

Dải đã đặt trong `tts_gen/cauhinh/tang_cuong.py` (`LOAI_XE`, đơn vị m):

| Loại | Dài | Rộng | Cao | Miệng hàng 1 | Hàng 1 → hàng 2 |
|---|---|---|---|---|---|
| `mini` (VF 3, VF 2) | 1,75–1,95 | 1,12–1,30 | 1,25–1,35 | 0,70–0,80 | 0,70–0,80 |
| `hanga` | 1,85–2,10 | 1,20–1,35 | 1,18–1,26 | 0,75–0,85 | 0,75–0,85 |
| `sedan` | 1,95–2,15 | 1,30–1,42 | 1,15–1,25 | 0,80–0,90 | 0,80–0,88 |
| `suv_b` | 2,20–2,55 | 1,33–1,45 | 1,25–1,35 | 0,80–0,90 | 0,82–0,90 |
| `suv_c` | 2,40–2,75 | 1,45–1,55 | 1,30–1,40 | 0,85–0,95 | 0,88–0,95 |
| `bay_cho` (MPV, SUV 7 chỗ) | 2,75–3,10 | 1,36–1,53 | 1,35–1,45 | 0,85–0,95 | 0,85–0,95 |
| `ban_tai` | 2,00–2,20 | 1,44–1,52 | 1,30–1,38 | 0,85–0,95 | 0,80–0,88 |

Miệng hàng 2 luôn cách vách sau ít nhất 0,25 m. `bay_cho` và `ban_tai` vượt dải chung của đặc tả gốc (dài tới 2,8 m, cao tới 1,35 m), vì dải ở đây đặt theo xe thật.

Theo cách ước này, các thay đổi đã đưa vào kho mô phỏng v3:
1. **Bán tải chưa có loại riêng.** Ranger, Hilux và Triton có cơ sở 3,1–3,3 m, nhưng phần lớn chiều dài đó là thùng hàng. Khoang người chỉ có hai hàng ghế, với vách cứng ngay sau hàng 2. Cần thêm loại `bantai`: dài ngắn (khoảng như sedan), rộng và cao như SUV, vách sau là vật liệu cứng (kính sau và vách kim loại).
2. **MPV và SUV 7 chỗ phổ thông cao hơn dải hiện tại.** Cao ngoài 1,70–1,84 m cho cao khoang ước 1,25–1,40 m, phần trên vượt mức 1,35 của `mpv`. Nên tách "MPV phổ thông" (Xpander, Limo Green, Innova Cross) ra khỏi `mpv` hiện tại, vì `mpv` đang được neo theo V-Class.
3. **Xe mini điện (VF 3, VF 2)** ngắn hơn hanga (cơ sở chỉ 2,07 m, nên dài khoang ước 1,55–1,85 m) nhưng cao hơn (cao ngoài 1,62–1,66 m). Nên cho `hanga` thêm dải "ngắn và cao", hoặc tách thành loại `mini`.
4. **Ford Territory và Kia Carnival rộng gần 1,94–2,01 m**, có thể vượt dải rộng 1,60 m. Đây là xe ít phổ biến hơn, không cần ưu tiên.

Các con số trên vẫn là ước tính. Muốn chính xác hơn thì cần đo khoang trong trên vài xe thật. Đặc biệt cần đo VF 3 và Limo Green, vì hai xe này không bán ở Mỹ nên không có thông số nội thất để đối chiếu.

## Nguồn

- Kích thước xe Việt Nam: trang "thông số kỹ thuật" của [bonbanh.com](https://bonbanh.com/thong-so-ky-thuat-xe), ví dụ [VF 3](https://bonbanh.com/thong-so-ky-thuat-xe-vinfast-vf3), [VF 5](https://bonbanh.com/thong-so-ky-thuat-xe-vinfast-vf5), [VF 6](https://bonbanh.com/thong-so-ky-thuat-xe-vinfast-vf6), [Limo Green](https://bonbanh.com/thong-so-ky-thuat-xe-vinfast-limo-green), [Vios](https://bonbanh.com/thong-so-ky-thuat-xe-toyota-vios-nam-2025), [Yaris Cross](https://bonbanh.com/thong-so-ky-thuat-xe-toyota-yaris-cross), [Xpander](https://bonbanh.com/thong-so-ky-thuat-xe-mitsubishi-xpander), [CX-5](https://bonbanh.com/thong-so-ky-thuat-xe-mazda-cx5), [Ranger](https://bonbanh.com/thong-so-ky-thuat-xe-ford-ranger), [CR-V](https://bonbanh.com/thong-so-ky-thuat-xe-honda-crv), [Golf](https://bonbanh.com/thong-so-ky-thuat-xe-volkswagen-golf), [V-Class](https://bonbanh.com/thong-so-ky-thuat-xe-mercedes_benz-v_class); các xe khác theo cùng mẫu đường dẫn `thong-so-ky-thuat-xe-<hãng>-<dòng>`. Limo Green đối chiếu thêm [Wikipedia](https://en.wikipedia.org/wiki/VinFast_Limo_Green), VF 3 đối chiếu thêm [VnExpress](https://vnexpress.net/vf-3-xe-dien-re-nhat-cua-vinfast-co-gi-4744294.html), Ranger 2022 theo [bảng so sánh của bonbanh](https://bonbanh.com/so-sanh-xe-ford-ranger-xls-2.0l-4x4-at-2022-14593,mitsubishi-triton-4x2-mt-2019-9773).
- Xe trong kho RIR đo: [CR-V 2009 (CarExpert)](https://www.carexpert.com.au/honda/cr-v/2009/dimensions), [Golf 2011 (CarExpert)](https://www.carexpert.com.au/volkswagen/golf/2011/dimensions), [Smart forfour W453 (cars-data)](https://cars-data.com/en/smart/forfour/dimensions), [Alfa 146 (VehicleScore)](https://vehiclescore.co.uk/car-dimensions-check/alfa%20romeo/146).
- Nội thất (mục 4): [CR-V (Mainline Honda)](https://www.mainlinehonda.com/honda-research/cr-v-interior/), [CR-V (iSeeCars)](https://www.iseecars.com/car/2025-honda-cr__v-dimensions), [CX-5 2024 (Sam Leman Mazda)](https://www.samlemanmazda.com/2024-mazda-cx-5-dimensions/), [CX-5 (iSeeCars)](https://www.iseecars.com/car/mazda-cx-5-dimensions), [Accent và Seltos (TrueDelta)](https://www.truedelta.com/Hyundai-Accent-vs-Kia-Seltos-specs-comparison,118-1492,2021&r=3), [Santa Fe (iSeeCars)](https://www.iseecars.com/car/2024-hyundai-santa_fe_hybrid-dimensions), [Ranger (GoAuto)](https://www.goauto.com.au/car-reviews/ford/ranger/xl-4x4-double-cab-pickup/2016-09-26/42246.html), [Ranger thế hệ mới (Just4x4s)](https://www.just4x4s.com.au/news-and-reviews/ford-ranger-big-on-space/9433).
- Doanh số: như `docs/xe_vn_va_rir.md`; thêm [thanhnien.vn (9 tháng 2026)](https://thanhnien.vn/o-to-ban-chay-nhat-cua-cac-hang-xe-tai-viet-nam-9-thang-dau-nam-2026-185261025094850065.htm), [vietnamplus (tháng 9/2026)](https://www.vietnamplus.vn/doanh-so-ban-oto-tai-viet-nam-tang-38-xe-hybrid-tang-toc-post1141084.vnp), [CafeF (tháng 9/2026)](https://cafef.vn/top-10-xe-ban-chay-nhat-tai-viet-nam-t9-2026-mot-cai-ten-gay-bat-ngo-lon-188261011093341294.chn).
