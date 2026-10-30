<!-- ĐÃ THAY bằng docs/ke_hoach_RIR_v3.md (28/10/2026: kho mô phỏng theo xe Việt Nam, P_RIR_DO = 0,5, chia dev theo frame_id); bản này giữ làm lịch sử. -->
<!-- Viết 28/10/2026. Thay docs/ke_hoach_RIR_v1.md làm kế hoạch chính của bước RIR. v1 giữ làm lịch sử (quyết định 27/10, các phát hiện khi viết mã, kết quả thử nhỏ). -->
# Bước RIR, bản 2: ưu tiên RIR đo thật trong xe

## 1. Quyết định đang áp dụng

| Mục | Quyết định | Ngày, nguồn |
|---|---|---|
| Đầu vào | Luật v1, ghép lời gọi chỉ giữ đủ cụm và cắt đúng ranh giới: 6.961 file, khoảng 4,9 giờ | 27/10, người dùng |
| **Nguồn RIR** | **Ưu tiên RIR đo thật** (In-Car McVAMPIRE, CAVEMOVE); RIR mô phỏng chỉ để bù chỗ kho đo không có, và thêm đa dạng | 28/10, người dùng |
| Tỷ lệ ưu tiên | `P_RIR_DO = 0,7`: bản có RIR dùng RIR đo với xác suất 0,7 khi split có xe đo cho ghế + micro đã bốc | 28/10, nhận định của tôi; sửa ở `cauhinh/tang_cuong.py` |
| Xe đo cho dev | Volkswagen Golf (CAVEMOVE): có đủ ghế và cả hai cấu hình micro | 28/10, nhận định; đổi ở `XE_DO` |
| Vật liệu mô phỏng | Bộ "hút âm hơn" (bộ đầu vang hơn xe thật, `docs/danh_gia_rir_that.md`) | 28/10 |
| Ghế, micro | Theo đặc tả gốc: ghế lái 70 / phụ 20 / sau 10, micro đều 4 vị trí (trần, gương, cột A, táp-lô) | 27/10, người dùng |
| P(RIR) | 0,8 cho mọi bản; 20% bản không có RIR | đặc tả |
| Preset | Mã E (sheet `Preset_moi_truong`), gán ở bước cộng nhiễu, không gán ở bước RIR | 27/10, người dùng |
| Lọc CER sau RIR | Không. CER trước/sau chỉ tính gộp trên bản dev để bắt lỗi pipeline | 27/10, người dùng |
| Chia train/dev câu | **Chưa chốt.** Mặc định `cau_goc`; đề xuất `frame_id` (`docs/ke_hoach_RIR_v1.md` mục 8) | chờ người dùng |

## 2. Kho RIR đo thật (`buoc/rir_kho_do.py`)

### Nguồn

| Bộ | Giấy phép | Trích dẫn (bắt buộc khi công bố) | Dùng |
|---|---|---|---|
| In-Car McVAMPIRE V1.0, Zenodo 12806684 | CC BY 4.0 | K. Müller, T. Wolff, Cerence GmbH, 2024. doi:10.5281/zenodo.12806684 | 1 xe: Mercedes V-Class (minivan 8 chỗ). Miệng giả GRAS 44AA, 11 hướng; 14 micro trần; 24 kHz, RIR 85 ms |
| CAVEMOVE (bản mở 21/10/2025), Zenodo 17404917 | CC BY 4.0 (dữ liệu), MIT (mã) | arXiv:2508.19691; doi:10.5281/zenodo.17404917. Danh sách tác giả bài báo **chưa kiểm** | 4 xe: VW Golf 2011, Alfa Romeo 146 2000, Smart forfour 2019, Honda CR-V 2009. Loa NTi TalkBox; 8 micro; 16 kHz; 4 mức mở kính |

- `rir_kho_do tai` kiểm md5 tệp McVAMPIRE và tài liệu PDF CAVEMOVE.
- Với CAVEMOVE, công cụ chỉ đọc mục lục zip 7,6 GB qua HTTP Range và lấy riêng các tệp `IRs/` (khoảng 15 MB); zipfile kiểm CRC từng tệp.
- Tiếng ồn xe trong hai bộ (CAVEMOVE hơn 15 giờ, McVAMPIRE 30–150 km/h) chưa tải. Phần này dành cho bước cộng nhiễu.

### Quy kênh micro và vị trí người nói về đặc tả

| Xe | Táp-lô | Cột A | Gương | Trần | Không dùng |
|---|---|---|---|---|---|
| Golf, Smart (distributed) | 1, 6 | 2, 5 | 3, 4 | – | 7, 8 (trần sau) |
| Alfa, CR-V (distributed) | 1, 5, 6 | 2, 4 | 3 | – | 7, 8 |
| Golf, Smart, CR-V (array: mảng tròn trên táp-lô) | 1–8 | – | – | – | – |
| V-Class | – | – | – | 1–4 (trần hàng ghế trước) | 5–14 (trần hàng 2, 3) |

- **Ghế, CAVEMOVE:** `d<cm>` → lái; `pf*` → phụ (kể cả `pfr90`, người phụ quay về phía lái); `prl*` → sau trái; `prr*` → sau phải; `prm*` (giữa) không dùng.
- **Ghế, V-Class:** pos1 lái; pos2 phụ; pos3 và pos6 sau trái; pos5 và pos8 sau phải; pos4 và pos7 (giữa) không dùng.
- Quy kênh dựa vào ảnh trong tài liệu của từng bộ. Kênh ghi là "gương" thật ra nằm sát gương chiếu hậu, ở mép trên kính.

### Kết quả dựng kho (laptop, 28/10)

| Xe | Split | RIR | Ghế lái / phụ / sau trái / sau phải | Micro | EDT trung vị |
|---|---|---|---|---|---|
| V-Class | train | 264 | 44 / 44 / 88 / 88 | trần 264 | 0,099 s |
| Smart forfour | train | 246 | 60 / 66 / 60 / 60 | táp-lô 162, cột A 42, gương 42 | 0,053 s |
| Alfa 146 | train | 144 | 36 / 36 / 36 / 36 | táp-lô 72, cột A 48, gương 24 | 0,051 s |
| Honda CR-V | train | 280 | 112 / 56 / 56 / 56 | táp-lô 220, cột A 40, gương 20 | 0,062 s |
| VW Golf | **dev** | 280 | 80 / 88 / 56 / 56 | táp-lô 200, cột A 40, gương 40 | 0,049 s |

- **Tổng 1.214 RIR, tất cả đạt.**
- **Không lọc theo EDT:** RIR đo là chuẩn thật; chỉ loại khi có giá trị không hữu hạn.
- **Cảnh báo:** McVAMPIRE chỉ dài 85 ms, nên mọi RIR của bộ này đều bật cảnh báo "đuôi không tắt". Không phải lỗi.
- **Đỉnh trực tiếp:** RIR đo không có toạ độ để tính trước, nên lấy đường đến đầu tiên đạt ≥ 30% đỉnh, rồi |h| lớn nhất trong 0,5 ms sau đó. Mỗi RIR giữ 40 mẫu trước đỉnh.
- **Lưu trữ:** mỗi xe một tệp `rir/<xe>.npy`, tổng khoảng 10 MB. `rir_manifest.jsonl` ghi tệp gốc, kênh, biến thể (vị trí, hướng, kính), giấy phép và trích dẫn.

## 3. Kho RIR mô phỏng (`buoc/rir_kho.py`), vai trò phụ

- Giữ như bản 1: 4 loại xe × 40 khoang, 144 khoang train / 16 dev; luật nhận khoang theo ghế lái; RIR khác trượt ngưỡng thì ghi `dat = false`.
- Đổi vật liệu sang bộ "hút âm hơn". Thử trên laptop: EDT ghế lái 0,063 s, gần xe thật hơn bộ cũ (0,10 s). Âm trầm 250 Hz vẫn vang hơn thật.
- Vai trò:
  - bù micro trần cho dev (Golf không có micro trần);
  - bù micro trần cho bản thứ hai của câu khi bản đầu đã dùng V-Class (hai bản của cùng câu phải khác xe);
  - 30% bản còn lại, để thêm đa dạng kích thước khoang.

## 4. Bảng gán (`buoc/rir_gan.py`)

Mỗi bản b của câu chọn theo thứ tự:
1. **Ghế, micro:** bốc theo (câu gốc, b), đúng trọng số đặc tả.
2. **Nguồn:** với xác suất `P_RIR_DO` (bốc theo câu gốc, b) thì thử kho đo trước, nếu không thì dùng mô phỏng.
3. **Xe/khoang:** bốc đều trong các xe của nguồn đó, thuộc split của câu, có RIR đạt cho ghế + micro, và chưa dùng cho bản khác của câu. Không có thì chuyển sang mô phỏng.
4. **Có RIR không và RIR cụ thể:** có RIR với xác suất 0,8; RIR cụ thể là vị trí đầu hoặc biến thể hướng/kính/kênh. Hai lựa chọn này theo hạt giống riêng của bản.

Câu ghép lời gọi đi cùng câu gốc: cùng split, cùng xe, ghế, micro, nguồn. Nếu chỉ có kho mô phỏng, bảng gán giống hệt bản 1 (đã kiểm từng dòng).

Chạy thử trên laptop với kho mô phỏng giả đủ 160 khoang và kho đo thật (28/10):

| | Câu | Bản | RIR đo / mô phỏng | Xe đo |
|---|---|---|---|---|
| train | 6.264 | 12.528 | 69% / 31% | Alfa 25%, CR-V 25%, Smart 26%, V-Class 24% |
| dev | 697 | 697 | 54% / 46% | Golf 100% |

- Dev ít RIR đo hơn vì Golf không có micro trần, nên mọi bản dev bốc trúng "trần" (25%) dùng mô phỏng.
- Mọi phép kiểm đạt: dev không dùng RIR hay xe của train; hai bản của cùng câu khác RIR; câu ghép cùng split và cùng xe với câu gốc; tỷ lệ vùng lệch ≤ 1,03 điểm.

## 5. Chập, ASR trước/sau, QA

Giữ như bản 1 (`buoc/rir_chap.py`, `phantich/rir_qa.py`), có thêm:
- `rir_chap --kho` nhận nhiều kho.
- `asr_dev/*/manifest.jsonl` ghi `nguon_rir`, nên `rir_qa` tách CER trước/sau theo RIR đo và RIR mô phỏng.
- `rir_qa` có thêm phần kho đo: chỉ số theo xe × ghế, giấy phép, trích dẫn, và kiểm xe dev không có trong train.
- Chạy thử cả chuỗi trên laptop: 65 bản, trong đó 32 bản RIR đo và 18 bản mô phỏng (còn lại không RIR). Mức −26 ± 0,5 dBFS đạt ở 100%; lệch trễ tối đa 0,44 ms.

## 6. Cách chạy trên cụm

Trên nút đầu (có mạng), sau khi giải nén gói mã mới vào `~/asr_tts_o_to/code`:

```bash
bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/setup_rir.sh      # venv_rir + test + tải RIR thật vào ~/asr_tts_o_to/rir_do
cd ~/asr_tts_o_to/code/tts_gen
bash dieuphoi/slurm/nop_rir.sh "kho kho_do gan"     # kho mô phỏng + kho đo + bảng gán  -> DỪNG: người dùng xem gan/phan_bo.json
bash dieuphoi/slurm/nop_rir.sh "chap asr qa goi"    # chập, CER trước/sau 500 bản dev (xin 1 GPU), QA, gói kết quả
```

Trên laptop: `python -m buoc.rir_kho_do tai --dich .cache/rir_do`, rồi `dung --nguon .cache/rir_do --out <thư mục>` (trong `.venv_rir`).

## 7. Đã kiểm

- 93 test đạt (`python -m unittest discover -s kiemthu -t .`). Riêng `kiemthu/test_rir.py` có 22 test, gồm các test mới:
  - quy ghế và micro của CAVEMOVE;
  - cắt RIR đo lấy đường đến đầu tiên, kể cả khi có phản xạ mạnh hơn;
  - ưu tiên RIR đo đúng tỷ lệ;
  - micro không có RIR đo thì dùng mô phỏng;
  - dev không dùng xe đo của train;
  - `P_RIR_DO = 0` cho kết quả giống hệt bản chỉ có mô phỏng;
  - câu ghép cùng xe đo với câu gốc.
- pyflakes sạch. Mã RIR duy nhất giữa hai kho.

## 8. Giới hạn

- Chỉ 5 xe đo, đều là xe châu Âu hoặc Nhật. Chỉ CR-V, Golf, V-Class có bán ở Việt Nam, và đều khác đời hoặc bán rất ít. Không có VinFast, MPV phổ thông, sedan B hay bán tải. Đối chiếu đầy đủ: `docs/xe_vn_va_rir.md`. Tập kiểm thu thật trong xe vẫn cần.
- Vị trí micro trần chỉ có 1 xe đo (V-Class, minivan), nên RIR đo cho micro trần đều mang âm học minivan. Dev không có micro trần đo.
- RIR đo khi xe đứng yên. Nguồn là loa hoặc miệng giả, không phải người thật.
- McVAMPIRE đã bị cắt ở 85 ms. Với T60 khoảng 90 ms, phần đuôi bị mất là nhỏ.
- Quy kênh micro dựa vào ảnh, chưa có toạ độ đo. Mảng 8 micro trên táp-lô cho 8 RIR gần giống nhau, nên đa dạng thật ít hơn số đếm.
- Mô phỏng vẫn vang hơn thật ở âm trầm; chưa hiệu chỉnh theo dải.

## 9. Chờ người dùng

1. Chọn cách chia train/dev câu (`cau_goc` / `core` / `frame_id`).
2. Xác nhận `P_RIR_DO = 0,7` và xe dev Golf, hoặc đổi.
3. Cho phép gửi mã lên cụm, chạy `setup_rir.sh` (tải RIR thật), rồi nộp `"kho kho_do gan"`.
4. Nghe lại (tùy chọn): `tts_gen/runs/nghe_rir_that/` (RIR thật so với mô phỏng cũ).
