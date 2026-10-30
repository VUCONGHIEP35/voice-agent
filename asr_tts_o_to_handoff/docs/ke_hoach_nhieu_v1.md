<!-- Viết 29/10/2026, sửa cùng ngày theo quyết định người dùng: giai đoạn 1 chỉ dùng CAVEMOVE có nhãn (phương án 1), 6 preset có nhãn thật, thử ASR bằng lưới SNR cố định. Nguồn và số đo: docs/khao_sat_nguon_nhieu_preset.md (mục 0b, 0c). -->
# Bước trộn nhiễu, bản 1: kế hoạch

## 1. Bối cảnh và quyết định

- **Đầu vào:** bộ "chỉ có vang" của bước RIR (job 15467, cụm, `runs/rir_v2/aug_v1/_reverb/`).
  - 13.126 bản (train 12.330, dev 796), giọng ở mức −26 dBFS.
  - 10.508 bản có RIR; số còn lại chỉ được chỉnh mức.
  - Không sinh lại RIR.
- **Mục tiêu giai đoạn 1:** cộng tiếng ồn có nhãn thật vào bộ vang, rồi **xem ASR phản ứng thế nào**: CER theo loại tiếng ồn và theo mức SNR. Đây là việc phải làm trước khi mở rộng sang các preset mô phỏng.
- **Thứ tự xử lý đúng về vật lý:** tiếng ồn CAVEMOVE ghi ngay tại micro trong xe, tức đã mang âm học của khoang. Vì vậy nhiễu chỉ được cộng sau bước RIR, không chập RIR vào nhiễu.
- **Quyết định người dùng:**

  | Ngày | Quyết định |
  |---|---|
  | 28/10 | SNR bốc đều theo nhóm: yên tĩnh 15–30 dB, nội đô 5–20 dB, ồn cao −5–15 dB |
  | 29/10 | Tải toàn bộ nhiễu CAVEMOVE và AISHELL-5 (đã xong); dữ liệu chỉ dùng nội bộ cho đồ án |
  | 29/10 | Người dùng nghe phiếu nhưng không gán được cảnh bằng tai. Chọn **phương án 1** (mục 2) để bảo đảm chính xác |
  | 29/10 | Giai đoạn 1 chỉ dùng **6 preset có nhãn thật**: E01, E02, E03, E05, E06, E09 |
  | 29/10 | Gán preset **60% theo cột "Case dùng", 40% ngẫu nhiên** trong 6 preset |
  | 29/10 | Thử ASR bằng **lưới SNR cố định** cộng bộ sinh ra; chạy **cả 3 mô hình** L, M, T |
  | 29/10 | Thử nhỏ trên laptop trước, rồi mới nộp job đầy đủ trên server |

- **Trường preset:** ghi vào **`preset_moi_truong`**. Không dùng `factors_covered`: trường đó là mã yếu tố nội dung của sheet `Yeu_to`, cũng bắt đầu bằng E.

## 2. Ba phương án nguồn nhiễu (lưu lại 29/10)

| Phương án | Nguồn | Preset phủ | Tiếng ồn cho train | Việc thêm | Rủi ro |
|---|---|---|---|---|---|
| **1. Chỉ CAVEMOVE có nhãn** (**đang dùng**) | `noise/`, `ventilation/` của 4 xe; nhãn tốc độ, kính, quạt nằm trong tên tệp | 6 preset nhãn thật. Các preset khác mô phỏng hoặc chờ (mục 7) | Khoảng 2,5 giờ, 3 xe (Golf giữ cho dev) | Ít nhất | Chỉ 4 xe châu Âu/Nhật; không có xe điện; không có nhạc |
| 2. Thêm `unc` sau khi kiểm tiếng nói | Phương án 1, cộng 2,4 giờ `uncontrolled_conditions` (lái ngoài đời), sau khi lọc đoạn có tiếng nói bằng VAD | Như 1 | Khoảng 4,2 giờ | Chạy VAD, loại đoạn có tiếng nói | `unc` không có nhãn cảnh; chỉ dùng làm nền chung |
| 3. Thêm AISHELL-5 gắn nhãn bằng mô hình | Phương án 2, cộng 40 giờ AISHELL-5 (xe hybrid điện). Gắn nhãn từng đoạn 10 s bằng mô hình nhận dạng âm thanh huấn luyện trên AudioSet (PANNs/AST), sau khi kiểm độ đúng của mô hình trên CAVEMOVE có nhãn | 15/15 (có E08 xe điện, nhạc cho E07) | Hơn 40 giờ | Tải mô hình, kiểm giấy phép trọng số, kiểm độ tin cậy | Nhãn tự động có thể sai |

Những gì AISHELL-5 cho mà CAVEMOVE không có: **E08** (xe điện), **nhạc phát trong xe** cho E07, và độ đa dạng (40 giờ, ngày/đêm, điều hòa kèm nhạc). Không có AISHELL-5 thì E08 phải xấp xỉ hoặc bỏ, còn nhạc cho E07 lấy từ kho nhạc mở (ví dụ MUSAN, cần kiểm giấy phép) rồi chập với RIR khoang xe.

## 3. Giai đoạn 1: nguồn nhiễu

CAVEMOVE có nhãn, ở `~/asr_tts_o_to/nhieu/cavemove/giai_nen/cavemove_dataset/<xe>/<cấu hình>/`. Ký hiệu tên tệp: `s<km/h>_w<kính>[_verN]`, trong đó w0 là kính đóng, w2 mở kính trước, w3 mở cả bốn; `v<mức>` là mức quạt khi xe đứng yên.

| Preset | Tệp | Nhóm SNR |
|---|---|---|
| E01 đỗ, yên tĩnh | `noise/s0_w0`. Dev: Golf không có `s0`, nên dùng `ventilation/v1_w0` của Golf (đứng yên, quạt thấp nhất) | 15–30 dB |
| E02 nội đô | `noise/s40_w0*`, `s50_w0*`, `s60_w0*` | 5–20 dB |
| E03 cao tốc | `noise/s90_w0*` … `s120_w0*` | −5–15 dB |
| E05 mở kính | `noise/s50–s70_w2*`, `w3*` | −5–15 dB |
| E06 quạt mạnh | `ventilation/` mức cao nhất của từng xe, `w0`: Alfa `v2`, CR-V, Smart, Golf `v3` | 5–20 dB |
| E09 đường nhám | `noise/s30_w0_coarse` | −5–15 dB |

- **Tách train/dev theo xe:**
  - train dùng Alfa 146, Honda CR-V, Smart forfour;
  - dev dùng **VW Golf**, trùng xe dev của bước RIR, để dev là xe chưa thấy cả về vang lẫn về nhiễu.
- **Kênh micro:** tệp CAVEMOVE có 8 kênh. Kênh được lấy theo micro mà bản đã nhận ở bước RIR:

  | Micro của bản | Kênh |
  |---|---|
  | táp-lô, cột A, gương | Kênh tương ứng theo `MICRO_DO` (`cauhinh/tang_cuong.py`), cấu hình micro phân tán; táp-lô có thể lấy thêm từ cấu hình mảng |
  | trần | Kênh 7/8, là micro trần sau của CAVEMOVE (bước RIR không dùng hai kênh này) |
  | Bản không có RIR | Kênh ngẫu nhiên trong cấu hình phân tán |

## 4. Giai đoạn 1: gán và trộn

- **Preset:**
  - bốc theo (câu gốc, bản);
  - 60% bốc trong giao của danh sách "Case dùng" (sheet `Preset_moi_truong`) với 6 preset; cả 12 case đều có ít nhất một;
  - 40% bốc đều trong 6 preset.

  Câu ghép lời gọi có cùng preset với câu gốc. E09 không có case nào trong sheet, nên chỉ xuất hiện qua phần 40%.
- **Tệp, kênh, điểm bắt đầu, SNR:** bốc theo (sample_id, bản, SEED). Thêm hay bớt file không làm đổi kết quả của file khác.
- **Trộn:**
  - Giọng đã ở −26 dBFS sau bước RIR. Nhiễu được chỉnh để RMS của đoạn cắt bằng −26 − SNR dBFS.
  - Đoạn nhiễu cắt ở điểm ngẫu nhiên, bỏ 0,5 s đầu và cuối tệp. Tệp ngắn hơn bản thì nối vòng, có làm mờ chỗ nối.
  - Đỉnh vượt −1 dBFS thì hạ cả bản; SNR giữ nguyên.
- **Đầu ra:** `runs/nhieu_v1/aug_v1/<split>/<ban_id>.flac` và `manifest.jsonl`, gồm: preset, xe, tệp, kênh, điểm bắt đầu, SNR đặt và SNR đo, mức hạ chống cắt đỉnh.

## 5. Giai đoạn 1: thử ASR

- **Lưới SNR cố định:**
  - Dùng đúng 500 bản dev của bước RIR (`chon_asr_dev`), nên lấy lại được CER "sạch" và "chỉ vang" của job 15467.
  - Mỗi bản ghép với 6 preset × SNR {20, 10, 5, 0} dB, nhiễu Golf, hạt giống cố định theo (bản, preset): **24 điều kiện, 12.000 tệp**.
  - Mỗi điều kiện là một lượt giả `asr_luoi/<preset>_snr<k>/manifest.jsonl`, chạy `buoc.asr_whisper` với PhoWhisper-large (CT2 int8), medium, small.
- **Bộ sinh ra:** 500 bản dev có nhiễu với SNR ngẫu nhiên như lúc huấn luyện (`asr_dev/nhieu`).
- **CER:** lấy `cer_min` trong `asr_gate_<tag>.csv` (có tính biến thể đọc), như `phantich/rir_qa.py`. Báo cáo theo mô hình × preset × SNR, kèm mốc "sạch" và "chỉ vang", chia thêm theo vùng giọng, micro, ghế.
- **Thời gian (ước tính từ job 15467):** khoảng 37.500 lượt giải mã, khoảng 2 giờ trên một GPU A100.

## 6. Các bước

0. Ghi kế hoạch này vào kho (xong 29/10).
1. **Mã:**
   - `cauhinh/nhieu.py`: thêm `PRESET_GD1`, nguồn theo preset, xe train/dev, `CASE_PRESET`, tỷ lệ 0,6, `SNR_LUOI`, kênh theo micro.
   - `buoc/nhieu_kho.py`: chỉ mục tệp, kênh, độ dài, split → `kho_nhieu.jsonl`. Có `--tu-csv` để dựng chỉ mục trên laptop.
   - `buoc/nhieu_gan.py`: bảng gán, `phan_bo.json`, các phép kiểm.
   - `buoc/nhieu_tron.py`: trộn; `--asr-dev 500`; `--luoi`.
   - `phantich/nhieu_qa.py`: `qa.md`, `qa.json`.
   - `dieuphoi/slurm/chay_nhieu.sbatch` và `nop_nhieu.sh`: bước `kho gan tron asr qa goi`, chỉ xin GPU khi có `asr`.
2. **Test** (`kiemthu/test_nhieu.py`):
   - SNR đạt ±0,1 dB;
   - tất định khi thêm file;
   - câu ghép cùng preset với câu gốc;
   - tỷ lệ 60/40;
   - dev chỉ dùng Golf;
   - micro trần lấy kênh 7/8;
   - không ghi `factors_covered`;
   - đỉnh ≤ −1 dBFS.
3. **Thử trên laptop:**
   - dựng chỉ mục từ `runs/nhieu_v1/do/cavemove.csv`;
   - gán trên manifest vang đã tải về;
   - trộn khoảng 30 bản, với câu sạch có sẵn và vài tệp nhiễu tải riêng (khoảng 50 MB).

   Lý do thử trên laptop: bắt lỗi trong vài phút, không tốn lượt job trên tài khoản dùng chung.
4. **Trên server:** đóng gói, gửi, nộp `nop_nhieu.sh "kho gan tron asr qa goi"` (có GPU). Tải gói kết quả về và đánh giá.
5. Cập nhật `CLAUDE.md`, `docs/cau_truc_ma.md` và bộ nhớ.

## 7. Kiểm (verification)

- Toàn bộ unit test đạt; pyflakes sạch.
- `phan_bo.json`:
  - tỷ lệ preset khớp 60/40;
  - mỗi case có preset hợp lệ;
  - dev chỉ dùng tệp Golf;
  - vùng giọng lệch ≤ 2 điểm.
- Trộn:
  - 100% bản có SNR đo lệch SNR đặt ≤ 0,5 dB;
  - 0 bản có đỉnh vượt −1 dBFS;
  - số bản phải hạ mức được báo.
- Lưới đủ 24 điều kiện × 500 bản × 3 mô hình. **Kiểm hợp lý tính:** trong mỗi preset, CER phải tăng khi SNR giảm; nếu ngược lại là pipeline có lỗi.
- `qa.md` có:
  - bảng CER theo mô hình × preset × SNR, cùng mốc "sạch" và "chỉ vang";
  - CER của bộ sinh ra;
  - nhận định preset và mức SNR mà PhoWhisper-small bắt đầu kém rõ.

## 7b. Tiến độ (29/10)

**Mã:**
- `cauhinh/nhieu.py` (phần giai đoạn 1);
- `buoc/nhieu_kho.py`, `nhieu_gan.py`, `nhieu_tron.py`;
- `phantich/nhieu_qa.py`;
- `dieuphoi/slurm/chay_nhieu.sbatch`, `nop_nhieu.sh`;
- `kiemthu/test_nhieu.py`: 14 test đạt, pyflakes sạch.

**Khác với mục 3:** Golf có `noise/s0_w0` ở cấu hình **mảng** (9,4 s, chỉ micro táp-lô), nên E01 dev dùng tệp này, là nhãn "đứng yên" thật, thay cho tiếng quạt. Bản dev có micro khác táp-lô thì lấy kênh táp-lô và ghi `kenh_khop = false` (7,7% bản dev).

**Kho:** 152 tệp. Mỗi preset × split đều có nguồn:

| | E01 | E02 | E03 | E05 | E06 | E09 |
|---|---|---|---|---|---|---|
| Train, phút | 2,3 | 11,6 | 10,9 | 16,7 | 2,4 | 4,0 |
| Dev, phút | 0,2 | 4,7 | 6,0 | 12,7 | 0,9 | 2,4 |

**Bảng gán (13.126 bản, mọi phép kiểm đạt):**
- Preset ở train: E02 42%, E03 17%, E01 16%, E05 10%, E06 9%, E09 7%.
- Theo sheet 59%, ngẫu nhiên 41%.
- Kênh đúng vị trí micro: train 100%, dev 92%.

**Thử trên laptop:** test, dựng kho từ csv, gán trên manifest thật. Tải tệp nhiễu về laptop thì hết giờ (370 MB, khoảng 0,5 MB/s), nên phần trộn thử chuyển sang **nút đầu của cụm** (lệnh trực tiếp, không nộp job, dữ liệu thật).
- Lần thử bắt được một lỗi: `write_flac` không tạo thư mục. Đã sửa và thêm test.
- Kết quả 32 bản: SNR đo lại từ tệp lệch 0,000 dB; đỉnh tối đa −7,2 dBFS; lưới 48 tệp đúng.
- `nhieu_qa` chạy trọn vẹn trên manifest thật với CER giả.

**Job 15535** (`kho gan tron asr qa goi`, có GPU) nộp 29/10, khoảng 15:50.

## 8. Giai đoạn 2 (chưa làm)

| Preset | Hướng đã bàn |
|---|---|
| E04 mưa, gạt nước | Không thấy mưa trong CAVEMOVE (mục 0c của khảo sát). Mô phỏng (hạt mưa, nhịp gạt nước khoảng 1 Hz trên nền E02) hoặc tự ghi |
| E07 nhạc và hành khách | Nhạc: AISHELL-5 (phương án 3) hoặc kho nhạc mở chập với RIR khoang xe. Hành khách: trộn 2–4 câu TTS khác, không dùng giọng người thật |
| E08 xe điện chạy chậm | AISHELL-5 (phương án 3), hoặc xấp xỉ bằng tiếng lốp tốc độ thấp cộng tiếng rít điện tổng hợp |
| E10 hầm, E13 chuyển trạng thái | Mô phỏng: nền E02 cộng đuôi vang dài kiểu hầm (T60 khoảng 2–4 s, lọc qua vỏ xe); E13 là E02 chuyển dần sang E10 ở 30–70% độ dài câu |
| E11 Bluetooth, E15 điện thoại | Mô phỏng codec băng hẹp 8 kHz (G.711) cho cả giọng lẫn nhiễu; cần quyết có làm không, vì ASR dự án nghe qua micro trong xe |
| E12 kẹt xe, còi | Mô phỏng: còi tổng hợp lọc qua vỏ xe, trên nền đứng yên hoặc chậm |
| E14 âm báo xe | Tổng hợp: tích tắc xi-nhan, chuông dây an toàn, bíp cảnh báo, trên nền E02 |

Quyết định còn treo cho giai đoạn 2:
- E04 mô phỏng hay bỏ;
- E11, E15 có làm không;
- có thêm phương án 2 hoặc 3 không;
- có cần một phần bản không nhiễu làm đối chứng không.
