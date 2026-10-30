<!-- Viết 28/10/2026. Thay docs/ke_hoach_RIR_v2.md làm kế hoạch chính của bước RIR. v2 giữ làm lịch sử (kho đo thật, quy kênh micro). -->
# Bước RIR, bản 3: mô phỏng theo xe Việt Nam, hiệu chỉnh theo RIR thật

## Vì sao có bản 3

- Kho mô phỏng bản 1–2 có 4 loại khoang (hạng A, sedan, SUV, MPV) với dải kích thước tự đặt.
- Khảo sát 28/10 cho thấy:
  - Trong 43 dòng xe phổ biến ở Việt Nam, chỉ CR-V, Golf và V-Class có RIR đo, và cả ba đều khác đời đang bán (`docs/kich_thuoc_xe_vn.md`).
  - Không còn bộ RIR công khai nào khác dùng được (`docs/xe_vn_va_rir.md`).
- Bản 3 dựng lại kho mô phỏng theo các dạng khoang của xe bán ở Việt Nam, và hiệu chỉnh vật liệu để chỉ số âm học khớp RIR đo thật.
- Kho đo thật (McVAMPIRE, CAVEMOVE) giữ nguyên như bản 2.

## 1. Quyết định đang áp dụng

| Mục | Quyết định | Ngày, nguồn |
|---|---|---|
| Đầu vào | Luật v1: 6.961 file (6.491 câu thường, 470 câu ghép lời gọi) | 27/10, người dùng |
| Nguồn RIR | RIR đo thật và RIR mô phỏng theo xe Việt Nam | 28/10, người dùng |
| **Tỷ lệ RIR đo** | **`P_RIR_DO = 0,5`** (bản 2 là 0,7) | 28/10, người dùng |
| **Loại khoang mô phỏng** | **7 loại theo xe Việt Nam, đều 40 khoang mỗi loại** (252 train / 28 dev) | 28/10, người dùng (số khoang đều) |
| **Chia train/dev câu** | **`frame_id`**: dev không trùng khung câu với train | 28/10, người dùng |
| Xe đo cho dev | Golf (CAVEMOVE) | 28/10, giữ như bản 2 |
| Ghế, micro, P(RIR), preset, lọc CER | Như bản 2: ghế 70/20/5/5, micro đều 4 vị trí, P(RIR) = 0,8, preset mã E ở bước nhiễu, không lọc CER | 27/10, người dùng |

## 2. Kho mô phỏng bản 3 (`buoc/rir_kho.py`, `cauhinh/tang_cuong.py`)

### Loại khoang

| Loại | Xe Việt Nam đại diện | Dài × rộng × cao khoang (m) |
|---|---|---|
| `mini` | VF 3, VF 2 | 1,75–1,95 × 1,12–1,30 × 1,25–1,35 |
| `hanga` | Morning, i10, Wigo, Swift | 1,85–2,10 × 1,20–1,35 × 1,18–1,26 |
| `sedan` | Vios, City, Accent, Mazda3, K3 | 1,95–2,15 × 1,30–1,42 × 1,15–1,25 |
| `suv_b` | VF 5, VF 6, Yaris Cross, Xforce, Creta, Seltos, Sonet, HR-V | 2,20–2,55 × 1,33–1,45 × 1,25–1,35 |
| `suv_c` | CX-5, CR-V, Tucson, VF 7, VF 8, Territory | 2,40–2,75 × 1,45–1,55 × 1,30–1,40 |
| `bay_cho` | Limo Green, Xpander, Innova Cross, Veloz, XL7, Fortuner, Everest, Santa Fe | 2,75–3,10 × 1,36–1,53 × 1,35–1,45 |
| `ban_tai` | Ranger, Hilux, Triton | 2,00–2,20 × 1,44–1,52 × 1,30–1,38 |

- **Cách ước kích thước khoang:** từ kích thước ngoài, kiểm bằng thông số nội thất hãng công bố ở Mỹ và Úc (rộng vai, khoảng trần, chỗ để chân). Chi tiết ở `docs/kich_thuoc_xe_vn.md` mục 4.
- **Lệch đặc tả gốc:** `bay_cho` và `ban_tai` vượt dải chung của đặc tả (dài tới 2,8 m, cao tới 1,35 m), vì dải ở đây đặt theo xe thật.
- **Bỏ loại `mpv` cũ:** loại này neo theo V-Class. V-Class đã có RIR đo, và van hạng sang bán ít ở Việt Nam.

### Thay đổi so với bản 2

1. **Vị trí ghế tính bằng mét theo loại xe:**
   - miệng hàng 1 cách chân kính trước 0,70–0,95 m;
   - hàng 2 sau hàng 1 thêm 0,70–0,95 m;
   - miệng hàng 2 cách vách sau ít nhất 0,25 m.

   Bản 2 tính theo tỷ lệ chiều dài (0,42 và 0,80), nên trong khoang 3 hàng ghế, "ghế sau" rơi vào hàng 3.
2. **Vật liệu riêng cho bán tải:** vách sau là lưng ghế cộng kính sau và vách kim loại (`VAT_LIEU_THEO_LOAI`).
3. **Miệng có hướng phát:** nguồn dạng cardioid `p + (1 − p)·cos θ` quay về kính trước, với `HUONG_MIENG_P = 0,6`. Nguồn đo thật (miệng giả của McVAMPIRE, TalkBox của CAVEMOVE) cũng phát mạnh về phía trước. Bản 2 dùng nguồn vô hướng.
4. **Hiệu chỉnh hấp thụ theo dải** (`HAP_THU_THEM`, cộng vào mọi mặt):

   | Dải | 125 Hz | 250 Hz | 500 Hz | 1 kHz | 2 kHz | 4–8 kHz |
   |---|---|---|---|---|---|---|
   | Thêm | +0,30 | +0,20 | −0,04 | −0,12 | −0,08 | 0 |

   - Phần cộng ở âm trầm thay cho kiểu hấp thụ của vỏ và tấm ốp mỏng rung; bảng vật liệu phòng của pyroomacoustics không có kiểu này.
   - Phần trừ ở 500 Hz–2 kHz bù cho các vật liệu vải trong bảng, vốn hút tới 0,8–0,9 ở 1 kHz, làm mô phỏng khô hơn xe thật.
   - Đây là số hiệu chỉnh cho khớp đo đạc, không phải số đo vật liệu.

### Hiệu chỉnh theo RIR đo (`phantich/so_kho_rir.py`)

**Mục tiêu:**
- **EDT từng dải 250 Hz–4 kHz** (ghế lái và ghế sau): trung vị của mỗi loại nằm trong [min, max] trung vị của 5 xe đo, nới ±25%.
- **DRR ghế sau:** nằm trong ±3 dB quanh trung vị của 4 xe CAVEMOVE.

Đánh giá trên 7 loại × (ghế lái + ghế sau), tổng 77 mục.

| Lượt (laptop) | Thay đổi | Đạt | Còn trượt |
|---|---|---|---|
| 1 | Loại khoang và vị trí ghế mới, vật liệu "hút âm hơn" của bản 2 | 58/77 | EDT 250 Hz 0,09–0,20 s (xe thật 0,06–0,09 s); DRR ghế sau −4,4…−5,5 dB (xe thật khoảng 0 dB) |
| 2 | Thêm hấp thụ +0,30 / +0,20 / +0,05 ở 125 / 250 / 500 Hz; miệng cardioid p = 0,5 | 72/77 | EDT 1 kHz ghế sau hơi ngắn |
| 3 | Bỏ phần thêm ở 500 Hz; p = 0,6 | 73/77 | Như lượt 2 |
| 4 | Bớt hấp thụ −0,08 / −0,12 / −0,08 ở 500 Hz / 1 kHz / 2 kHz | 75/77 | EDT 500 Hz của bán tải |
| 5 | Chỉ bớt −0,04 ở 500 Hz | 76/77 | EDT 1 kHz ghế lái bán tải, do dao động ngẫu nhiên: với cùng hệ số 1 kHz, giá trị đi từ 0,054 s ở lượt 4 lên 0,085 s ở lượt 5 |
| **Kho đầy đủ** (280 khoang, bộ hệ số lượt 5) | | **77/77** | |

- Mỗi lượt thử dùng 2 khoang mỗi loại (14 khoang).
- Ray tracing không tất định, nên chỉ đánh giá trên trung vị.

**Kho đầy đủ trên laptop, trung vị ghế lái so với xe đo:**

| | EDT 250 Hz | 500 Hz | 1 kHz | 2 kHz | 4 kHz | DRR lái | DRR sau | T20 |
|---|---|---|---|---|---|---|---|---|
| 5 xe đo (khoảng trung vị theo xe) | 0,064–0,088 | 0,033–0,054 | 0,032–0,056 | 0,029–0,066 | 0,030–0,070 | 0,3–3,2 | CAVEMOVE −1,5…0,8; V-Class −4,6 | 0,045–0,081 |
| Mô phỏng bản 3 (6 loại, trừ bán tải) | 0,062–0,066 | 0,043–0,048 | 0,031–0,034 | 0,035–0,040 | 0,037–0,041 | 1,2–1,9 | −1,4…−1,8 | 0,092–0,111 |
| Bán tải | 0,065 | 0,063 | 0,046 | 0,066 | 0,057 | 0,9 | −2,4 | 0,122 |
| Mô phỏng bản 1, vật liệu cũ (kho thử trên cụm 27/10, để so) | 0,185 | 0,080 | 0,059 | 0,070 | 0,089 | −2,0 | −6,3 | 0,135 |

- Kho đầy đủ: 280/280 khoang đạt ngay lần bốc đầu.
- Trong 8.960 RIR, 15 RIR bị loại vì EDT vượt 0,15 s; tất cả ở ghế sau của bán tải.
- Thời gian trên laptop: khoảng 4 giây CPU mỗi khoang, 5 phút với 4 tiến trình.

## 3. Bảng gán thử (laptop, kho đầy đủ + kho đo thật, chia theo `frame_id`)

| | Câu | Bản | Có RIR | RIR đo / mô phỏng | Xe đo | Mô phỏng theo loại |
|---|---|---|---|---|---|---|
| train | 6.165 | 12.330 | 80,1% | 49,6% / 50,4% | Alfa 25%, CR-V 26%, Smart 26%, V-Class 24% | Mỗi loại 13,9–15,0% |
| dev | 796 (744 câu gốc) | 796 | 79,9% | 39,6% / 60,4% | Golf 100% | 10–19% mỗi loại (chỉ 4 khoang dev mỗi loại) |

Mọi phép kiểm đều đạt:
- dev không dùng RIR hay khoang của train;
- hai bản của cùng câu khác RIR;
- câu ghép cùng split, khoang, ghế và micro với câu gốc;
- 0/214 khung câu dev trùng với train, 4,1% lõi câu trùng;
- vùng giọng lệch tối đa 1,83 điểm (mốc 2 điểm).

Dev có ít RIR đo hơn train vì Golf không có micro trần.

**Chập thử** (laptop không có âm thanh TTS, nên dùng 2 câu sạch trong `runs/nghe_rir_that/` chập với 57 RIR lấy từ bảng gán: 15 RIR đo, 42 mô phỏng, đủ 7 loại):
- 100% bản ở −26,00 dBFS;
- lệch trễ tối đa 0,25 ms.

## 4. Cách chạy trên cụm (chờ người dùng cho phép)

Trên nút đầu, sau khi giải nén gói mã mới vào `~/asr_tts_o_to/code`:

```bash
bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/setup_rir.sh       # venv_rir + test + tải RIR thật vào ~/asr_tts_o_to/rir_do
cd ~/asr_tts_o_to/code/tts_gen
bash dieuphoi/slurm/nop_rir.sh "kho kho_do so nghe gan goi"  # -> DỪNG: người dùng xem kho/so_sanh.json, gan/phan_bo.json, nghe phiếu
bash dieuphoi/slurm/nop_rir.sh "chap asr qa goi"             # chập, CER trước/sau 500 bản dev (xin 1 GPU), QA, gói
```

- Thư mục chạy là `runs/rir_v2/`, khác với `runs/rir_v1/` của job thử 27/10.
- Bước `so` (mới) chạy `phantich.so_kho_rir` trên kho dựng ở cụm.
- Bước `nghe` (mới) làm phiếu nghe trên cả kho: 5 câu × 20 RIR mỗi loại, đợt 1 gồm 70 bản (10 mỗi loại).
- `goi` gói những gì đã có, nên gọi được ngay sau bước gán.

Trên laptop (`.venv_rir`):
- `python -m buoc.rir_kho --out runs/rir_v2_laptop/kho --workers 4` (laptop ít RAM: 14 tiến trình làm hết bộ nhớ).
- `python -m phantich.so_kho_rir --mo-phong runs/rir_v2_laptop/kho --do runs/rir_v2_laptop/kho_do`.

## 5. Đã kiểm

- **97 test đạt** (`python -m unittest discover -s kiemthu -t .`); pyflakes sạch. `kiemthu/test_rir.py` có 26 test, gồm các test mới:
  - 252/28 khoang, đều mỗi loại;
  - hàng ghế theo mét ở mọi loại: hàng 2 sau hàng 1, cách vách sau, micro đứng trước miệng;
  - vật liệu riêng của bán tải;
  - `kho_config.json` ghi được ra JSON;
  - `LOAI_XE` có đủ trường.
- **Lỗi đã sửa:** `rir_kho` ghi `kho_config.json` bị hỏng vì `MICRO_DO` có khóa dạng tuple. Lỗi này có từ khi thêm kho đo (28/10). Trên cụm, job sẽ thoát mã 3 ngay sau khi dựng kho xong.

## 6. Giới hạn

- **Kích thước khoang trong là ước tính.** VF 3, VF 2 và Limo Green không bán ở Mỹ, nên không có thông số nội thất để đối chiếu.
- **Hộp chữ nhật** không có ghế, người, táp-lô. Bộ hệ số hiệu chỉnh chỉ làm khớp trung vị EDT và DRR, không làm khớp hình dạng RIR.
- **Đuôi vang mô phỏng vẫn dài hơn xe đo:** T20 0,09–0,12 s so với 0,045–0,08 s. T20 không nằm trong mục tiêu hiệu chỉnh. EDT (phần nghe thấy rõ nhất) đã khớp.
- **Dải 1 kHz** mô phỏng (0,031–0,034 s) nằm sát mép dưới của dải xe đo.
- **Hướng phát của miệng** là cardioid không đổi theo tần số; miệng thật có hướng rõ hơn ở tần cao.
- **Kho đo** giữ các giới hạn của bản 2: 5 xe châu Âu/Nhật, micro trần chỉ có ở V-Class, đo khi xe đứng yên.
- **Tập kiểm thu thật** trong xe Việt Nam vẫn là thước đo cuối cùng.

## 7. Kết quả trên cụm (job 15463, 28/10)

**Chuẩn bị:**
- Gói mã server: 93 tệp, sha256 `19e0b65d…`.
- `setup_rir.sh` trên nút đầu: 26 test đạt; tải RIR thật vào `~/asr_tts_o_to/rir_do`, md5 và CRC khớp.

**Job:**
- Nộp với `"kho kho_do so nghe gan goi"`. Job phải chờ vì tài khoản dùng chung đã chạy đủ 2 job; chạy trên dgx02 từ 18:54, xong sau 2 phút 54 giây, mã thoát 0.
- Gói kết quả: `rir_v2_20261028_1857.tar.gz` (115 MB, sha256 `43fdbe6b…`). Trên laptop: `tts_gen/dist/tai_ve/rir_v2/`, giải nén ở `tts_gen/runs/ket_qua_rir_v2/`.

| Phần | Kết quả |
|---|---|
| Kho mô phỏng | 280/280 khoang đạt. 1 khoang phải bốc lại 1 lần; trên laptop không khoang nào phải bốc lại. 10/8.960 RIR bị loại: 9 ở ghế sau của bán tải, 1 ở ghế phụ của suv_b. EDT trung vị 0,052–0,054 s ở 6 loại, 0,080 s ở bán tải |
| So với kho laptop | Cùng hạt giống nên kích thước khoang giống 100%. EDT lệch trung vị +0,0001 s, \|lệch\| p95 0,024 s, do ray tracing không tất định, như đã biết |
| So với RIR đo | **77/77 mục tiêu đạt.** Trung vị gần như giống kho laptop (EDT 250 Hz ghế lái 0,061–0,067 s; DRR ghế sau −1,3…−2,5 dB) |
| Kho đo | 1.214/1.214 RIR, giống laptop |
| Bảng gán | Mọi phép kiểm đạt. 13.070/13.126 bản giống hệt bản gán thử trên laptop; 56 bản khác vì trên cụm có vài RIR khác bị loại (do ray tracing). Train: 49,6% RIR đo, mỗi loại mô phỏng khoảng 7%. Dev: 39,6% RIR đo, toàn bộ là Golf |
| Phiếu nghe | 700 bản (5 câu × 20 RIR × 7 loại), mức âm −26,00 dBFS. Đợt 1 gồm 70 bản: 10 mỗi loại; ghế lái 28, phụ 14, sau 28; đủ 4 micro. Chỉ có RIR mô phỏng; muốn so với RIR thật thì nghe `runs/nghe_rir_that/` |

**Điểm cần biết:**
1. **Dev lệch về sedan (51% bản có RIR).** Phần RIR đo của dev chỉ có Golf, và Golf được xếp vào loại `sedan`. Phần mô phỏng của dev vẫn chia đều theo loại.
2. **Micro trần của dev chỉ có RIR mô phỏng.** Golf không có micro trần. Ở train, micro trần cũng chỉ có 46% RIR đo, vì RIR đo trần chỉ có ở V-Class.
3. **Bán tải vang nhất:** EDT ghế sau 0,09–0,11 s ở dải 500 Hz–4 kHz, chỉ ngang V-Class. Không có RIR bán tải thật để kiểm. Đây là chỗ nên nghe kỹ trong phiếu.
4. **T20 mô phỏng vẫn dài hơn xe đo**, như mục 6.

## 8. Sửa bán tải và chạy cả chuỗi (28/10)

**Nhận xét của người nghe:** bán tải "hơi vang", khớp với điểm 3 ở mục 7.

**Sửa:** vách sau của bán tải đổi từ "ghế 0,5 / kính 0,4 / kim loại 0,1" sang "ghế 0,8 / kính 0,2". Lý do: ở cabin kép, lưng ghế sau bọc nệm che gần hết vách, kính sau nhỏ.

Thử trên laptop (6 khoang mỗi loại):
- EDT trung vị của bán tải giảm từ 0,080 s xuống 0,057 s. Sedan là 0,051 s, SUV B là 0,052 s.
- EDT ghế sau ở 500 Hz–4 kHz giảm từ 0,09–0,11 s xuống 0,048–0,068 s.
- Không RIR bán tải nào bị loại.
- Vẫn đạt 77/77 mục tiêu.

**Kiểm:** 26 test RIR đạt. Trong lần chạy toàn bộ test, 1 test điều phối (`test_server ... test_thu_tu_va_song_song`) lỗi vì canh thời gian; chạy lại riêng thì đạt cả 3 lần.

**Triển khai:**
- Gói mã sha256 `7bf0c673…`.
- Trên cụm, kho, bảng gán và phiếu nghe của job 15463 được chuyển sang `runs/rir_v2_cu_15463/`, vì `rir_kho` bỏ qua khoang đã có. Kho đo được giữ lại.
- Job **15467** chạy liền các bước `"kho so nghe gan chap asr qa goi"`, có GPU.

## 9. Kết quả job 15467 (28/10, dgx02, 22:12–22:25, mã thoát 0)

Gói kết quả: `rir_v2_20261028_2225.tar.gz`, sha256 `6caaf228…`. Trên laptop: `tts_gen/runs/ket_qua_rir_v2_15467/`. QA đầy đủ ở `qa/qa.md`.

| Bước | Thời gian | Kết quả |
|---|---|---|
| kho | 141 s | 280/280 khoang. 8.959/8.960 RIR đạt; 1 RIR bị loại (ghế phụ, micro táp-lô). Bán tải: EDT trung vị 0,059 s (trước khi sửa 0,080 s) và 0 RIR bị loại (trước 9) |
| so | 1 s | 77/77 mục tiêu |
| nghe | 11 s | 700 bản, đợt 1 có 70 bản |
| gan | 2 s | Mọi phép kiểm đạt. Train 12.330 bản, dev 796 bản |
| chap | 34 s | 13.126 bản, 10.508 bản có RIR. Mức −26 ± 0,5 dBFS ở 99,99% bản; 0 bản có đỉnh vượt −1 dBFS; 1 bản phải hạ chống cắt đỉnh; lệch trễ p99 0,44 ms |
| asr | 612 s | 500 bản dev, 3 mô hình, mỗi bản đo cả bản sạch và bản có vang |
| qa | 1 s | 13/14 mục kiểm đạt. Mục còn lại (so mô phỏng với đo trên mô hình B0) hoãn vì chưa có mô hình B0 |

**CER trước/sau RIR** trên 500 bản dev, theo CER của bước chấm (có tính đáp án biến thể), số trong `qa.md`:

| Mô hình | Trước | Sau | Số bản CER tăng > 0,1 |
|---|---|---|---|
| L (PhoWhisper-large) | 0,0267 | 0,0341 | 17 |
| M (PhoWhisper-medium) | 0,0264 | 0,0366 | 19 |
| **T (PhoWhisper-small, mô hình đích)** | 0,0505 | 0,0519 | 24 |

Phân tích thêm theo CER thô của từng bản (`cer` trong `asr_*.jsonl`, nên số tuyệt đối khác bảng trên; dev chỉ có 20–46 bản mỗi nhóm, trừ sedan có 252):
- **RIR đo và RIR mô phỏng làm CER tăng ngang nhau:**
  - L: đo 0,034 → 0,041, mô phỏng 0,030 → 0,039;
  - M: đo 0,029 → 0,042, mô phỏng 0,033 → 0,042;
  - T: đo 0,053 → 0,054, mô phỏng 0,060 → 0,062.

  Kho mô phỏng đã hiệu chỉnh tác động lên ASR cỡ như RIR thật.
- **Không loại xe nào tăng vượt hẳn các loại khác.** Bán tải tăng ở M (0,035 → 0,054) và T (0,044 → 0,056), nhưng giảm ở L (0,035 → 0,033); với 33 bản thì chưa kết luận được.
- **Ghế và micro:** micro gương tăng nhiều nhất ở cả 3 mô hình. Ghế sau dao động lớn vì chỉ có 43 bản.
- **Bản tăng mạnh:** chỉ 1 bản tăng > 0,1 ở cả 3 mô hình ("Mở cốp xe nhé." → "mở cột xe nhá"; Golf đo thật, micro gương). 10 bản tăng ở ít nhất 2 mô hình. Đó là lỗi nhầm âm bình thường trên câu ngắn ("Nam Định" → "làm định"), không phải lỗi chập (lệch trễ, cắt đỉnh, câm).

**Nhận định:**
- Vang trong xe (EDT khoảng 0,05 s) làm ASR kém đi ít: khoảng 0,7–1 điểm CER với large và medium, chỉ 0,14 điểm với small.
- Pipeline không có dấu hiệu lỗi.
- Tập 500 bản dev chỉ gồm bản có RIR, nên không có nhóm đối chứng không RIR.

## 10. Chờ người dùng

1. Xem kết quả. Nếu đạt, bước tiếp theo của dự án là cộng tiếng ồn (preset mã E) lên bộ `runs/rir_v2/aug_v1/_reverb/` trên cụm.
2. Tùy chọn: nghe lại phiếu mới (`runs/ket_qua_rir_v2_15467/runs/rir_v2/nghe/nghe_thu_rir.xlsx`) để kiểm bán tải sau khi sửa.
