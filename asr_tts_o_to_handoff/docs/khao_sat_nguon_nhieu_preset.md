# Khảo sát nguồn nhiễu cho các preset môi trường (28/10/2026)

Phạm vi: bước trộn nhiễu (bước 4) theo sheet `Preset_moi_truong` (mã E) trong `data/du_lieu_asr_tts_o_to_v0.3.xlsx`. RIR đã xong ở bước trước, không bàn ở đây.

Mỗi dòng ghi rõ cái gì đã kiểm (đọc trang dữ liệu, tài liệu, mục lục zip) và cái gì là ý kiến.

## 0. Quyết định SNR (người dùng đồng ý 28/10)

Cột "SNR mục tiêu" (10/12/15 dB) trong sheet **không dùng cho ASR**. Suy luận: E01 đỗ xe yên tĩnh có 10 dB, thấp hơn E03 cao tốc 15 dB, tức ngược chiều với SNR tại micro; cột "Mục tiêu đánh giá" viết cho tiếng nói đầu ra. Vậy đó nhiều khả năng là mức giọng trợ lý phát ra loa phải vượt nhiễu (B04, phía M5).

Thay bằng dải SNR, bốc đều cho mỗi bản; hai bản của cùng câu bốc độc lập:

| Nhóm | Preset | Dải SNR |
|---|---|---|
| Yên tĩnh | E01, E08 | 15 đến 30 dB |
| Nội đô, quạt, codec, âm báo | E02, E06, E11, E14, E15 | 5 đến 20 dB |
| Ồn cao | E03, E04, E05, E07, E09, E10, E12, E13 | −5 đến 15 dB |

Căn cứ:
- AVICAR báo SNR trong xe từ khoảng +15 xuống −10 dB.
- Hiệu ứng Lombard: người nói tăng khoảng 0,3–0,6 dB cho mỗi dB ồn trên khoảng 45–50 dBA.

Hiệu chỉnh lại khi đã có mức dBA của từng đoạn nhiễu. Giới hạn: TTS không có giọng Lombard.

## 0b. Quyết định 29/10 và việc đã làm

**Người dùng chọn:**
1. **Tải toàn bộ nhiễu** CAVEMOVE và AISHELL-5 lên cụm.
2. **E10, E12, E14 tạm dùng mô phỏng hoặc tổng hợp** (mục 3). Chưa tự ghi.
3. **Dữ liệu chỉ dùng nội bộ cho đồ án, không công bố.** Điều kiện "chia sẻ tương tự" của CC BY-SA (AISHELL-5) vì vậy không phát sinh. Vẫn phải ghi nguồn cả hai bộ.

**Kiểm lại mã bản CAVEMOVE (Zenodo API, 29/10):**
- 15064194 và 17404917 là hai phiên bản của cùng một bộ (mã gốc 13594242).
- 15064194: bản tháng 3/2025, zip 3,67 GB.
- 17404917: bản 21/10/2025, zip 7,61 GB, md5 `dec31a69…`. Đây là bản kho RIR đã dùng.
- Dùng bản 17404917. Khi đọc mục lục zip này:

  | Thư mục | Số tệp | Dung lượng nén |
  |---|---|---|
  | `noise/` | 402 | 4,14 GB |
  | `uncontrolled_conditions/` | 764 | 2,87 GB |
  | `ventilation/` | 66 | 0,59 GB |

  Phần nhiễu gần như là cả zip, nên tải nguyên zip và so md5.

**AISHELL-5:**
- `noise.tar.gz` 13,36 GB, trên OpenSLR và hai máy chủ dự phòng (elda, magicdatatech).
- Trang OpenSLR ghi giấy phép "CC BY-SA 4.0" (đã mở trang, 29/10). Trang không công bố md5, nên so kích thước và ghi sha256.

**Mã:**
- `tts_gen/cauhinh/nhieu.py`: dải SNR theo nhóm, nguồn nhiễu, các preset mô phỏng.
- `tts_gen/buoc/nhieu_tai.py`: tải tiếp được khi đứt; giải nén có kiểm đường dẫn (zip) và dùng `filter="data"` (tar).
- `tts_gen/dieuphoi/slurm/tai_nhieu.sh`: chạy nền trên nút đầu.
- `kiemthu/test_nhieu.py`: 5 test.

**Trên cụm:** bắt đầu tải lúc 29/10 08:00 vào `~/asr_tts_o_to/nhieu/{cavemove,aishell5}/`, log ở `~/asr_tts_o_to/logs/tai_nhieu_*.log`. Mỗi bộ có `danh_sach.tsv` và `nguon.json`.

## 0c. Kết quả tải, tra cảnh và đo (29/10)

**Tải xong lúc 10:21:**
- CAVEMOVE: 7,61 GB, md5 khớp, giải nén 1.236 tệp (8,68 GB).
- AISHELL-5: 13,36 GB, sha256 `717c0c09…`, giải nén 282 tệp (21,56 GB, 40,29 giờ).

**Bảng tra cảnh của AISHELL-5: không có.**
- README trên GitHub nhắc tới `docs/anonymize_mapping.txt`, nhưng kho không có tệp đó.
- `spatialnet/tools/noise_list.txt` chỉ liệt kê `car_noise/001…060/noise.wav`.
- Tên tệp nhiễu dạng `noise/<001–060>/noise_DX0kC01.wav` không chứa mã cảnh.

Những gì suy ra được:
- **Số phiên khớp số cảnh.** Bài báo (Bảng 1, 2) có 30 cảnh con × ngày/đêm = 60 cảnh, và bộ nhiễu có 60 phiên. Rất có thể mỗi phiên là một cảnh, nhưng không biết phiên nào là cảnh nào.
- **21 phiên có 6 kênh.** DX05/DX06 là tín hiệu tham chiếu của dàn âm thanh, chỉ có khi dàn bật, tức các cảnh C, F, I, L có điều hòa cao. Bảng 1 cho ra 20 cảnh như vậy, khớp gần đúng.
- **Xe là Li Auto, hybrid điện.** Micro gắn trên tay nắm 4 cửa.

**Đo đặc trưng** (`phantich/do_nhieu.py`, kênh 1; `runs/nhieu_v1/do/{aishell5,cavemove}.csv`):

AISHELL-5:
- Mức tổng gần như chỉ do tiếng ầm 20–100 Hz. Dải 300 Hz–1 kHz trải từ −73 tới −48 dBFS.
- Mỗi phiên dài 30–74 phút. Nhiều phiên có nền thay đổi 20–30 dB trong phiên (dừng, chạy), không phải một cảnh đứng yên.
- **Phiên 014 và 052 là cùng một bản ghi:** tương quan 0,61, lệch 42,5 s; trộn phải gộp làm một nhóm. Các cặp 017–058, 004–035, 025–027 thì đặc trưng gần nhau nhưng không trùng (tương quan 0,05).
- Phiên 043 yên nhất: −54,5 dBFS, gần như không có tần thấp; có thể là cảnh đứng yên, tắt máy.
- Các phiên 6 kênh chia hai nhóm:
  - phổ ít phẳng và nhiều xung cao tần (005, 006, 008, 010, 011, 028, 038): có lẽ là nhạc;
  - phổ phẳng (009, 032, 045, 046): có lẽ quạt mạnh, nhạc nhỏ.

CAVEMOVE `uncontrolled_conditions`:
- Không có nhãn: ngoài âm thanh, zip chỉ có `info.json` và `info.mat` ghi tên xe. Bài báo nói có "lớp nhãn song song" nhưng không phát hành.
- **Không thấy dấu hiệu mưa to:** chỉ 3/764 tệp có chỉ số lộp độp cao tần vượt mốc p99 của các tệp có nhãn, rải rác, không thành chuỗi.
- **Tệp `unc` sáng tiếng hơn hẳn** các tệp chạy kính đóng có nhãn (dải 3–8 kHz so với 300 Hz–1 kHz). Riêng Golf, 80/83 tệp vượt mức cao nhất của tệp có nhãn. Có thể là đường ướt, kính mở, tiếng ngoài xe hoặc tiếng người; phải nghe mới biết.
- Không thấy nhịp gạt nước rõ: đỉnh tự tương quan chỉ 0,48, và nằm ở mép dải tìm 0,4 s.

**Phiếu nghe:** `tts_gen/runs/nhieu_v1/do/nghe2/phieu_nghe_nhieu.xlsx`, tạo bằng `phantich/phieu_nghe_nhieu.py`:
- 60 đoạn AISHELL-5, mỗi đoạn 10 s giữa phiên;
- 40 đoạn CAVEMOVE `unc`: 12 lộp độp nhất, 12 sáng tiếng nhất, 4 nhịp mạnh nhất, 12 ngẫu nhiên.

Kế hoạch trộn: `docs/ke_hoach_nhieu_v1.md`.

## 1. Hai nguồn chính đã kiểm

### CAVEMOVE (Zenodo 15064194)
- **Giấy phép:** CC BY 4.0 (trang Zenodo). Đây là cùng tệp zip đã dùng cho RIR.
- **Đã đọc mục lục zip từ xa** bằng `buoc/rir_kho_do.HttpFile`, không tải cả zip. Có 4 thư mục xe: Golf 2011, Alfa Romeo 146 2000, Smart forfour 2019, Honda CR-V 2009. Tài liệu PDF chỉ liệt kê 3 xe, không có Honda.
- **Nhãn nằm ngay trong tên tệp** (theo tài liệu PDF, mục 5):
  - `noise/s<tốc độ>_w<kính>[_verN][_coarse].wav`
  - `ventilation/v<mức>_w<kính>.wav`
- **Ký hiệu kính:**
  - w0: đóng hết;
  - w1: hai kính trước hé khoảng 10 cm;
  - w2: mở hết kính trước;
  - w3: mở cả bốn.
- **Tốc độ và quạt:**
  - Tốc độ từ 50 tới 110 km/h, bước 10. Có vài bản 30–40 km/h.
  - Quạt có 2–3 mức (v1–v3), ghi khi xe đứng yên.
- **"coarse" (mặt đường nhám):** chỉ có ở s30, mọi xe.
- **Thư mục `uncontrolled_conditions/unc_###.wav`** (84–129 tệp mỗi xe/bộ micro): tài liệu PDF không mô tả. Bài báo nói có phiên "mưa hoặc đường ướt" được ghi nhãn ở một lớp riêng, nhưng **chưa tìm thấy lớp nhãn đó trong zip**.
- **Dung lượng:**

  | Phần | Dung lượng |
  |---|---|
  | `noise/` | khoảng 4,5 GB |
  | `uncontrolled_conditions/` | khoảng 3,1 GB |
  | `ventilation/` | khoảng 0,7 GB |

  Lấy riêng từng phần được bằng HTTP Range, như bước RIR đã làm.
- **Loại động cơ:** tài liệu không ghi. Không giả định có xe điện.

### AISHELL-5 (OpenSLR SLR159)
- **Giấy phép:** CC BY-SA 4.0, theo trang OpenSLR qua kết quả tìm kiếm; cần mở trang để xác nhận lần cuối.
- **Bộ nhiễu:** `noise.tar.gz` 13 GB, khoảng 40 giờ, "cùng cấu hình với dữ liệu far-field, không có giọng người".
- **Xe:** **hybrid điện**. 4 micro gắn trên tay nắm cửa.
- **Cảnh ghi** (Bảng 1 trong bài báo):
  - Kính: N1 kính lái mở 1/3; N2 cửa trời mở 1/2; N3 cả hai mở 1/2; M đóng hết.
  - Trạng thái xe A–L: đứng yên / 0–40 (bảng kia ghi 0–60) / 40–80 / 80–120 km/h, kết hợp với điều hòa tắt / vừa / cao.
  - **Dàn âm thanh "vừa" luôn đi kèm điều hòa "cao"** (cảnh C, F, I, L), nên không có bản "quạt tối đa" sạch, không lẫn nhạc.
- **Chưa biết:** tệp nhiễu có mang mã cảnh hay không. Repo GitHub chỉ nhắc `docs/anonymize_mapping.txt` cho dữ liệu giọng. Phải xem danh sách tệp trước khi dùng.

## 2. Tám preset chưa có nguồn: kết quả

| Preset | Nguồn mở tìm được | Mức phủ | Còn thiếu / ghi chú |
|---|---|---|---|
| E04 Mưa, gạt nước | CAVEMOVE có phiên mưa/đường ướt theo bài báo, nhưng chưa thấy nhãn (có thể nằm trong `unc_###`). Freesound có vài clip mưa trong xe mang CC0 hoặc CC BY, giấy phép theo từng clip | **Một phần, chưa xác nhận** | Không có gạt nước. Phải nghe `unc_###` để tìm mưa |
| E05 Mở kính khi chạy | CAVEMOVE w1/w2/w3 × 50–110 km/h, 4 xe; AISHELL-5 N1–N3 | **Đủ** | Kiểm nhãn cảnh của AISHELL-5 |
| E06 Quạt điều hòa tối đa | CAVEMOVE `ventilation/` v1–v3 × w0–w3 (xe đứng yên); AISHELL-5 điều hòa cao (lẫn nhạc) | **Đủ** | Chưa rõ v3 có phải mức tối đa của xe không. Bản đứng yên thiếu tiếng lốp; có thể cộng với nền nội đô |
| E08 Xe điện chạy chậm | AISHELL-5 (xe hybrid điện): cảnh A/B đứng yên, D/E 0–40 km/h | **Có thể đủ** | Chưa biết lúc ghi xe chạy điện hay máy xăng; chưa biết tệp nhiễu có nhãn cảnh không |
| E09 Đường xấu, rung xóc | CAVEMOVE `_coarse`, chỉ ở 30 km/h | **Một phần** | Chỉ là đường nhám, không có ổ gà hay gờ giảm tốc. Sheet chưa gán E09 cho case nào |
| E10 Hầm | **Không có** bộ ghi trong xe ở hầm. Một bài tổng quan 19 nghiên cứu cho T60 hầm 5–10 s ở dải giữa, tới 27 s ở tần thấp | **Không có, phải mô phỏng hoặc tự ghi** | Xem mục 3 |
| E12 Kẹt xe, còi | Không có bộ dữ liệu Việt Nam mở. FSD50K có lớp "Vehicle horn" (CC BY 4.0 chung, giấy phép từng clip trong metadata). ZapSplat có bản "Hanoi traffic" theo điều khoản riêng của ZapSplat, không phải CC | **Một phần** | Còi ghi ngoài trời phải lọc qua vỏ xe trước khi trộn. Còi xe máy kiểu Việt Nam nên tự ghi |
| E14 Âm báo xe | **Không có** bộ dữ liệu mở | **Không có** | Tổng hợp bằng mã hoặc ghi từ xe thật |

**Đã loại** (giấy phép không phù hợp):
- ASR-CabNois (MagicHub): CC BY-NC-ND. ND cấm tạo bản phái sinh, mà trộn nhiễu là tạo bản phái sinh.
- Nexdata In-Car Noise: dữ liệu trả phí.
- HISSandaROAR UFX026: trả phí.
- UrbanSound8K và ESC-50: NC (không dùng cho mục đích thương mại). Điều này theo hiểu biết của tôi, chưa kiểm lại trong phiên này.

## 3. Ý kiến cho E10, E13, E14 (chưa kiểm chứng)

- **E10 hầm:**
  - Khi kính đóng, giọng người lái truyền trong khoang. Vỏ xe chặn phần lớn âm, nên vang hầm gần như chỉ tác động lên **tiếng ồn bên ngoài lọt vào**, không tác động lên giọng.
  - Vì vậy E10 có thể làm như sau, không cần thêm RIR hầm cho giọng:
    1. lấy nhiễu ngoài trời hoặc nhiễu lốp;
    2. chập với RIR hầm mô phỏng (T60 khoảng 5–10 s);
    3. lọc qua vỏ xe (thông thấp, giảm mức);
    4. cộng với nền trong xe.
  - Khi kính mở (w2/w3), tác động lên giọng lớn hơn; tạm bỏ qua.
- **E13** = E02 chuyển dần sang E10 trong một câu. Làm được ngay khi đã có E10.
- **E14:**
  - Chuông xi-nhan, chuông dây an toàn và tiếng bíp cảnh báo là các âm đơn giản: chuỗi xung, sin, nhịp đều.
  - Tổng hợp bằng mã là tất định và không vướng giấy phép. Nhược điểm: không giống hệt âm báo của từng hãng.

## 4. Nếu tự ghi (một buổi lái xe)

Một buổi ghi phủ được E04 (gạt nước), E09 (gờ giảm tốc, ổ gà), E10 và E13 (qua hầm Kim Liên hoặc Thủ Thiêm), E12 (giờ cao điểm), E14 (âm báo của xe).

Gợi ý cách ghi (ý kiến):
- Điện thoại đặt ở cụm đèn trần, kính đóng.
- Ghi WAV, từ 16 kHz trở lên.
- Mỗi tình huống vài phút.
- **Không để có tiếng người nói.** Giọng người là dữ liệu sinh trắc; đoạn nào lẫn giọng thì cắt bỏ.

## 5. Bước tiếp theo đề xuất

1. Lấy `noise/` và `ventilation/` của CAVEMOVE (khoảng 5,2 GB) lên cụm bằng HTTP Range như bước RIR. Nghe thử vài tệp `unc_###` để tìm mưa.
2. Tải nhiễu AISHELL-5 (13 GB) vào thư mục riêng trên cụm. Liệt kê tên tệp để xem có mã cảnh không, rồi mới quyết định E08.
3. Viết mã tổng hợp E14. Mô phỏng E10, rồi E13.
4. E12: lọc FSD50K lớp còi theo giấy phép từng clip (CC0 và CC BY). Tự ghi nếu được.
5. Chốt E09: gán case nào, hoặc bỏ ở v1.
6. Giấy phép:
   - CC BY và CC BY-SA đòi ghi nguồn.
   - CC BY-SA có thể buộc phát hành bản trộn với cùng giấy phép nếu chia sẻ ra ngoài.
   - Cần người dùng xác nhận mục đích dùng; tôi không phải luật sư.

Tệp tải về là dữ liệu không tin cậy: mỗi bộ một thư mục riêng, đọc bằng Python `-I`, không chạy gì từ trong đó.

## Nguồn
- CAVEMOVE: https://zenodo.org/records/15064194 ; https://arxiv.org/abs/2508.19691 ; tài liệu `dataset-documentation.pdf` (Zenodo)
- AISHELL-5: https://openslr.org/159/ ; https://arxiv.org/abs/2505.23036 ; https://github.com/daiyvhang/aishell-5
- AVICAR: https://people.csail.mit.edu/klivescu/ws06/papers/lee_etal_ICSLP04_AVICAR.pdf
- Lombard: https://pmc.ncbi.nlm.nih.gov/articles/PMC7316514 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC5612409
- Hầm (T60): https://bast.opus.hbz-nrw.de/files/366/B80.pdf
- Còi, giao thông Việt Nam: https://www.zapsplat.com/music/busy-traffic-hanoi-vietnam-motorcycles-trucks-and-cars-passing-horns-beeping/ ; https://www.researchgate.net/publication/392743982
- FSD50K (giấy phép): https://huggingface.co/datasets/Fhrozen/FSD50k/blob/main/LICENSE-DATASET.md
- Đã loại: https://magichub.com/datasets/in-vehicle-noise-dataset/ ; https://www.nexdata.ai/datasets/speechrecog/233
