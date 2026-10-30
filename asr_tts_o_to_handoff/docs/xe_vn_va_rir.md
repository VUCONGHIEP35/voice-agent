# Dòng xe ở thị trường Việt Nam và RIR đo công khai (28/10/2026)

Câu hỏi của người dùng: xe nào trong các bộ RIR công khai đang bán ở Việt Nam; dòng xe phổ biến nào ở Việt Nam chưa có RIR.

Số liệu thị trường lấy từ báo chí tổng hợp số VAMA và VinFast. Các nguồn lệch nhau ở vài chỗ, nên chỉ dùng để xếp hạng, không dùng làm số chính thức.

## 1. Xe có RIR công khai: có ở Việt Nam không

| Xe trong bộ RIR | Bộ | Đang bán mới ở Việt Nam? | Ghi chú |
|---|---|---|---|
| **Honda CR-V** 2009 (thế hệ 3) | CAVEMOVE | **Có:** CR-V thế hệ 6 lắp ráp trong nước, giá 1,039–1,25 tỷ (2026) | Cùng dòng, khác đời: nội thất, kích thước và vật liệu đã đổi qua 3 thế hệ |
| **VW Golf** 2011 (Mk6) | CAVEMOVE | **Có** từ 31/10/2025: Golf 8 nhập Đức, 798 triệu – 1,898 tỷ | Khác đời (Mk6 so với Mk8); doanh số ở Việt Nam rất nhỏ |
| **Mercedes V-Class** (đời không ghi) | McVAMPIRE, ANIR | **Có:** V300 thay V250 từ 9/2025, khoảng 3,3–4 tỷ | Xe sang, doanh số rất nhỏ; cabin dài hơn nhiều so với MPV phổ thông |
| Smart forfour 2019 | CAVEMOVE | Không thấy nguồn nào về nhà phân phối chính hãng | Chỉ dùng được như xe cỡ nhỏ đại diện |
| Alfa Romeo 146 (2000) | CAVEMOVE | Không thấy nhà phân phối chính hãng | Xe cũ, chỉ dùng như hatchback hạng C đại diện |
| Peugeot 208 | IR64-CAR (loa ngoài xe) | Bảng giá Peugeot 2026 chỉ có 408, 2008, 3008, 5008, Traveller; không có 208 | Bộ này không hợp để chèn vang lời nói |
| Peugeot 206+ | eBrIRD (micro ở tai) | Không | Không hợp |
| Tesla Model X | INFER (chưa phát hành) | Không có phân phối chính hãng | Dữ liệu chưa công bố |

**Kết luận:** chỉ 3/5 xe trong kho có bán ở Việt Nam (CR-V, Golf, V-Class), và đều khác đời hoặc thuộc phân khúc bán rất ít. **Không bộ RIR công khai nào có xe Nhật hay Hàn bán chạy ở Việt Nam (trừ CR-V đời cũ), không có VinFast, không có Ford.** Tôi không tìm thấy bộ RIR công khai nào của Toyota, Hyundai, Kia, Mazda, Mitsubishi, Ford hay VinFast; tìm trên Zenodo, arXiv và GitHub, chưa tìm hết mọi kho dữ liệu.

## 2. Xe phổ biến ở Việt Nam: đã có RIR chưa

Các xe bán chạy năm 2025 và 9 tháng 2026, theo phân khúc, kèm xe đại diện gần nhất trong kho đo. Bảng kích thước đầy đủ của 43 dòng xe nằm trong `docs/kich_thuoc_xe_vn.md`.

| Phân khúc / dạng cabin | Xe bán chạy ở Việt Nam (số tham khảo) | RIR đo cùng dòng | Đại diện gần nhất trong kho | Mức khớp (nhận định) |
|---|---|---|---|---|
| Xe điện cỡ mini (dài khoảng 3,2 m) | **VinFast VF 3** (số 1: 44.585 xe năm 2025; 42.272 xe 9T/2026), VF 2 | Không | Smart forfour (3,5 m, 4 chỗ) | Trung bình: cùng cỡ nhỏ; khác hãng, khác vật liệu |
| SUV hạng A/B điện | **VF 5** (43.913 xe năm 2025), **VF 6** (23.291) | Không | CR-V (lớn hơn), Golf | Thấp–trung bình |
| SUV hạng B (xăng/hybrid) | **Toyota Yaris Cross** (14.601; 12.646 xe 9T/2026), Mitsubishi Xforce, **Kia Seltos** (7.109), **Hyundai Creta** (6.849) | Không | CR-V, Golf | Thấp–trung bình |
| SUV hạng C | **Mazda CX-5** (17.262; 11.893 xe 9T/2026), **Honda CR-V**, VF 7 | **CR-V (đời 2009)** | CR-V | **Cao nhất trong kho**, dù khác đời |
| MPV 7 chỗ phổ thông | **VinFast Limo Green** (27.127 xe chỉ trong 5 tháng 2025), **Mitsubishi Xpander** (19.891; 10.496 xe 9T/2026), Toyota Innova Cross, Veloz | Không | V-Class (van sang, dài hơn) | Thấp: V-Class rộng, dài, vật liệu khác |
| Sedan hạng B | **Toyota Vios** (13.424), **Honda City** (5.452 xe 9T/2026), Hyundai Accent | Không | Alfa 146, Golf (đều là hatchback) | Thấp: sedan có khoang hành lý tách rời, hatchback thì không |
| Bán tải | **Ford Ranger** (18.692 xe năm 2025; 9.835 xe 9T/2026) | Không | Không có | **Không có đại diện:** cabin ngắn, vách sau đứng ngay sau hàng 2 |
| SUV hạng D/E | Ford Everest, VF 8 (1.494 xe tháng 9/2026), VF 9, Santa Fe | Không | CR-V, V-Class | Thấp |

Theo các bảng trên, **khoảng 7/10 mẫu bán chạy nhất năm 2025 không có RIR cùng dòng, và cũng không có đại diện tốt**. Riêng 4 mẫu VinFast dẫn đầu (VF 3, VF 5, Limo Green, VF 6) đã chiếm phần lớn doanh số top 10.

## 3. Ý nghĩa cho dự án

- RIR đo công khai cho **độ thật về âm học cabin nói chung** (vang ngắn, DRR quanh 0 dB), nhưng **không cho độ thật về dòng xe Việt Nam**.
- Kho mô phỏng lấy dải kích thước theo loại xe (hạng A, sedan, SUV, MPV), nên phủ được cỡ cabin của xe Việt Nam, nhưng vẫn vang hơn thật (`docs/danh_gia_rir_that.md`).
- Thiếu hẳn hai dạng cabin bán rất chạy: **MPV 7 chỗ phổ thông** (Xpander, Limo Green, Innova) và **bán tải** (Ranger).
- Xe dev hiện là Golf: có bán ở Việt Nam nhưng bán rất ít. Nếu muốn dev phản ánh thị trường, CR-V (SUV C, cùng lớp với CX-5) là lựa chọn gần hơn, đổi lại train mất xe SUV đo duy nhất.

## 3b. Tìm thêm bộ RIR thật (28/10, lượt 2)

Đã tìm ở: Zenodo, arXiv, GitHub, HuggingFace, OpenSLR, AI Hub (Hàn), các bộ của Nhật (CIAIR Nagoya), các thư viện IR chung (MIT IR survey, danh sách RIR tổng hợp trên GitHub), và phần tổng quan tài liệu của bài CAVEMOVE (liệt kê 15 nghiên cứu hoặc bộ dữ liệu trong xe). **Không tìm thấy bộ RIR đo công khai nào có xe đang bán chạy ở Việt Nam.**

| Nguồn mới | Xe | RIR từ vị trí miệng tới micro? | Công khai | Dùng được không |
|---|---|---|---|---|
| MIT IR survey (Traer & McDermott 2016), CC BY 4.0 | 1 IR "Car", không ghi dòng xe | Loa cách micro 1,5 m | Có | Không đáng: 1 IR, không biết xe |
| autosound-measurements (GitHub), CC BY 4.0 | VW Passat B8 sedan | **Không:** đo từ từng loa âm thanh của xe | Có | Không hợp để chèn vang lời nói |
| Soeta & Sakamoto 2018 (AIST + **Suzuki Motor**), *Environments* 5(4):44, CC BY (đã đọc toàn văn, xem mục dưới) | Bài không ghi tên xe, chỉ ghi "xe A sedan dài 3,9 m" và "xe B xe nhỏ dài 3,4 m". Theo ảnh, tôi nhận là Suzuki Swift thế hệ 3 và Suzuki Wagon R (kei car) | **Không:** nguồn là loa âm thanh của xe (loa trung ở cửa, loa tép), thu ở tai đầu nộm HATS | Không: bài không có mục công bố dữ liệu hay tệp kèm | Không dùng làm RIR. Chỉ dùng số liệu để đối chiếu mô phỏng |
| CabinSep (Interspeech 2025) | 1 xe điện, 156 RIR đo | Có | **Không phát hành** | Hỏi tác giả; gần với xe điện kiểu VinFast |
| INFER (arXiv 2510.07442) | Tesla Model X, mô hình Buck | Loa tới 384 micro | Không phát hành | Không có ở Việt Nam |
| AISHELL-5 / ICMC-ASR (xe điện Li Auto) | 1 xe điện Trung Quốc | **Không có RIR**; có 40 giờ tiếng ồn nhiều kênh | Có (OpenSLR 159) | Chỉ dùng cho bước nhiễu |
| AI Hub "차량 내 대화 및 명령어 음성" (Hàn) | Không ghi | Không có RIR; tiếng nói | Chỉ cho người mang quốc tịch Hàn | Không |
| CIAIR (Nagoya), AVICAR, AV@CAR | Không ghi | Không có RIR; tiếng nói | AVICAR cấp theo yêu cầu | Không |

Kết luận lượt 2: tập RIR đo công khai dùng được cho tiếng nói trong xe vẫn chỉ có **McVAMPIRE, CAVEMOVE, ANIR** (ANIR cũng là V-Class). Hai nguồn đáng thử liên hệ:
- CabinSep: RIR đo trên xe điện.
- AISHELL-5: chỉ để lấy tiếng ồn xe điện.

### Soeta & Sakamoto 2018: đã đọc toàn văn (28/10)

Người dùng tải bản PDF về `docs/environments-05-00044.pdf`.

- **Cách đo:** sine sweep 20 Hz–20 kHz trong 20 s, phát qua dàn loa của xe. Thu bằng đầu nộm B&K 4128C ở 48 kHz, 24 bit, mỗi cấu hình đo 3 lần. Đầu nộm đặt ở ghế lái, ghế phụ và các ghế sau. Xe đứng yên, nổ máy không tải.
- **Vì sao không dùng làm RIR:** đường truyền là loa cửa → tai người ngồi, khác đường miệng người nói → micro mà dự án cần. Dữ liệu cũng không công bố. Hỏi xin cũng không giải quyết được chuyện sai đường truyền, nên tôi bỏ khỏi danh sách liên hệ.
- **Xe:** bài chỉ ghi "xe A" và "xe B". Tên dòng xe ở bảng trên là tôi nhận theo ảnh và chiều dài. Swift có bán ở Việt Nam nhưng với số lượng ít; Wagon R bản kei car thì không bán ở Việt Nam.
- **Số liệu đọc từ biểu đồ (sai số khoảng ±0,01 s):**

  | Ghế lái | 125 Hz | 250 Hz | 500 Hz | 1 kHz | 2 kHz | 4 kHz |
  |---|---|---|---|---|---|---|
  | EDT xe A (s) | 0,15 | 0,11 | 0,05 | 0,07 | 0,05 | 0,05 |
  | EDT xe B (s) | 0,11 | 0,06 | 0,03 | 0,045 | 0,04 | 0,065 |
  | T20 xe A (s) | 0,37 | 0,17 | 0,10 | 0,08 | 0,06 | 0,06 |
  | T20 xe B (s) | 0,43 | 0,17 | 0,10 | 0,06 | 0,07 | 0,06 |

- **Đối chiếu với kho của ta:**
  - Từ 500 Hz trở lên, EDT ghế lái là 0,03–0,07 s. Mức này khớp CAVEMOVE (0,044–0,057 s) và bộ vật liệu "hút âm hơn" (0,035–0,062 s).
  - Ở 250 Hz, EDT là 0,06–0,11 s. CAVEMOVE là 0,08 s, mô phỏng "hút âm hơn" là 0,106 s, tức đã nằm trong dải xe thật. Bộ vật liệu cũ cho 0,185 s, vượt dải này.
  - Ở 125 Hz, đuôi vang dài (T20 0,37–0,59 s) ở cả hai xe, nhưng lọc octave 125 Hz cũng tự kéo dài phép đo. Kho của ta tính EDT từ 250 Hz trở lên nên không bị ảnh hưởng.
  - Mở kính, bật điều hòa hoặc chở thêm người không làm EDT hay RT đổi có ý nghĩa thống kê. Điều này khớp với CAVEMOVE, nơi mở kính chỉ đổi EDT chút ít. Vì vậy kho không cần tách biến thể theo các yếu tố này.
  - Ghế sau có EDT dài hơn ghế trước ở dải 125–1000 Hz (xe B). Chiều này cùng chiều với kho của ta.

## 4. Đề xuất (chờ người dùng)

1. **Tự đo RIR trên xe phổ biến ở Việt Nam.** Đây là cách duy nhất để có RIR đúng dòng xe. Ưu tiên theo doanh số và dạng cabin:
   - VinFast VF 3 (mini) và VF 5 hoặc VF 6 (SUV nhỏ);
   - một MPV 7 chỗ (Limo Green hoặc Xpander);
   - một sedan B (Vios hoặc City);
   - Mazda CX-5 hoặc CR-V đời mới;
   - Ford Ranger.

   Cách đo theo khảo sát phần cứng và đặc tả: sine sweep mũ, loa có hướng phát giống miệng người (kiểu NTi TalkBox, như CAVEMOVE), 4 ghế × các vị trí micro thật của xe. Làm khi xe đứng yên, kính đóng; thêm một lần kính mở.

   Thiết bị, xe mượn và thời gian cần người dùng lo. Mỗi xe khoảng nửa ngày (ước tính, chưa kiểm).
2. **Trong lúc chưa đo được:**
   - giữ kho đo hiện tại để có độ thật về âm học;
   - tăng phần mô phỏng cho các dạng cabin thiếu: thêm loại "bán tải" và "MPV phổ thông" vào `LOAI_XE`, kích thước lấy từ thông số nội thất của Ranger, Xpander, Limo Green (cần tra);
   - có thể giảm trọng số Smart và Alfa (không bán ở Việt Nam), hoặc giữ vì chúng vẫn đại diện cho cabin nhỏ.
3. **Tập kiểm thu thật trong xe Việt Nam vẫn là thước đo cuối cùng**, như CLAUDE.md đã ghi. RIR, dù đo hay mô phỏng, không thay được tập này.

## Nguồn

- Top 10 năm 2025: [tinxe.vn](https://tinxe.vn/tin-thi-truong/10-o-to-ban-chay-nhat-viet-nam-trong-nam-2025-vinfast-chiem-4-vi-tri-dau-id20260123003845656), [cartimes.tapchicongthuong.vn](https://cartimes.tapchicongthuong.vn/top-10-o-to-ban-chay-nhat-viet-nam-nam-2025--vinfast-ap-dao--xe-dien-lan-dau-chiem-vi-tri-dan-dau-17920.htm), [motorist.vn](https://www.motorist.vn/article/5435/top-10-best-selling-cars-in-vietnam-2025-vinfast-dominates-the-market)
- Xe bán chạy nhất từng hãng, 9 tháng 2026: [thanhnien.vn](https://thanhnien.vn/o-to-ban-chay-nhat-cua-cac-hang-xe-tai-viet-nam-9-thang-dau-nam-2026-185261025094850065.htm)
- Tháng 9/2026: [dantri.com.vn](https://dantri.com.vn/o-to-xe-may/top-10-o-to-ban-chay-thang-9-xe-dien-ap-dao-ban-tai-vang-bong-20261011110858027.htm), [tinxe.vn](https://tinxe.vn/tin-thi-truong/top-10-o-to-ban-chay-nhat-viet-nam-trong-thang-92026-vinfast-vf-2-xuat-hien-ford-ranger-bien-mat-id20261013114300487)
- VW Golf ở Việt Nam: [bonbanh.com](https://bonbanh.com/gia-xe-oto-volkswagen-golf), [laodong.vn](https://news.laodong.vn/xe/chi-tiet-mau-xe-hatchback-volkswagen-golf-the-he-moi-vua-ra-mat-tai-viet-nam-1601379.ldo)
- Mercedes V-Class ở Việt Nam: [bonbanh.com](https://bonbanh.com/gia-xe-oto-mercedes_benz-v_class)
- Honda CR-V lắp ráp ở Việt Nam: [vtcnews.vn](https://vtcnews.vn/honda-cr-v-2026-ban-xang-bo-sung-trang-bi-gia-tu-1-039-ty-dong-ar1008162.html), [baophapluat.vn](https://baophapluat.vn/honda-cr-v-e-hev-lap-rap-tai-viet-nam-chinh-thuc-ra-mat-nhung-chua-co-gia-ban.html)
- Peugeot ở Việt Nam: [bizhub.vietnamnews.vn](https://bizhub.vietnamnews.vn/thaco-cuts-prices-of-four-peugeot-models-post10530.html), [baodautu.vn](https://baodautu.vn/peugeot-viet-nam-ap-dung-gia-moi-cho-bo-3-suv-cao-cap-d198738.html)
- Tìm thêm: [MIT IR survey](https://mcdermottlab.mit.edu/Reverb/IR_Survey.html), [bản trên HuggingFace](https://huggingface.co/datasets/benjamin-paine/mit-impulse-response-survey), [autosound-measurements](https://github.com/ayukhno/autosound-measurements), [Soeta & Sakamoto 2018](https://mdpi.com/2076-3298/5/4/44), [CabinSep](https://www.isca-archive.org/interspeech_2025/han25d_interspeech.pdf), [AISHELL-5](https://www.openslr.org/159/), [ICMC-ASR](https://arxiv.org/pdf/2401.03473), [AI Hub](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=112), [CAVEMOVE (tổng quan tài liệu)](https://arxiv.org/html/2508.19691v1), [danh sách RIR tổng hợp](https://github.com/Graphi07/room-impulse-responses)
- Bộ RIR: [CAVEMOVE](https://zenodo.org/records/17404917), [IR64-CAR](https://zenodo.org/records/15168578), [INFER](https://arxiv.org/pdf/2510.07442), [eBrIRD](https://www.phon.ucl.ac.uk/resource/ebrird)
