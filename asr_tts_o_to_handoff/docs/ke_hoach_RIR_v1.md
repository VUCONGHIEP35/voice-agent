> **Đã thay bằng `docs/ke_hoach_RIR_v2.md` (28/10/2026): ưu tiên RIR đo thật (McVAMPIRE, CAVEMOVE).** Tệp này giữ làm lịch sử: quyết định 27/10, các phát hiện khi viết mã, kết quả thử nhỏ, các cách chia dev.

<!-- Bàn giao cho phiên thực hiện (viết 27/10/2026). Kế hoạch đã được người dùng duyệt hướng ở phiên lập kế hoạch; CHƯA viết mã, CHƯA đụng cụm. -->
> **Phiên mới:** đọc hết tệp này, CLAUDE.md và docs/cau_truc_ma.md trước. Làm theo mục 4 "Kế hoạch thực hiện", bắt đầu từ bước 1. Dừng chờ người dùng ở hai chỗ: phiếu nghe sau khi chạy thử nhỏ, và phân bố bảng gán trước khi chập toàn bộ. Quy tắc cụm (chỉ `~/asr_tts_o_to/`, 1 job một lúc, không đụng job `dh_*`, không `scancel` job của người khác) và cách SSH xem trong bộ nhớ dự án. Các số trong tệp đo ngày 27/10; kiểm lại hiện trạng cụm trước khi nộp job.

# RIR với luật v1: dữ liệu và khả năng mô phỏng đã đủ chưa, và kế hoạch chạy trên A100

## Tiến độ thực hiện (27/10/2026)

- **Bước 1 xong:** quyết định ghi ở đầu `docs/danh_gia_RIR.md`; dòng ghi chú ở đầu `docs/RIR.md`; CLAUDE.md.
- **Bước 2 xong:** `cauhinh/tang_cuong.py`, `thuvien/rir.py`, `buoc/rir_kho.py`, `buoc/rir_gan.py`, `buoc/rir_chap.py`, `phantich/rir_qa.py`, `phantich/phieu_nghe_rir.py`, `kiemthu/test_rir.py` (15 test), `dieuphoi/slurm/{setup_rir.sh, chay_rir.sbatch, nop_rir.sh}`, `requirements_rir.txt`. 86 test đều đạt.
  - Chạy thử cả chuỗi trên laptop với tập nhỏ: kho 4 khoang → gán (đủ 6.961 file) → chập 65 bản → ASR M trước/sau → QA. Mọi mục kiểm đạt.
  - Trên cụm: `venv_rir` đã dựng (numpy 2.5.4, scipy 1.18.1, pyroomacoustics 0.10.1), test đạt. Mã mới đã giải nén vào `~/asr_tts_o_to/code`.
- **Bước 3, phần máy xong; chờ người dùng nghe:**
  - Job 15295 hỏng (mã 3) sau khi mô phỏng xong 8 khoang, vì `kho_config.json` không ghi được hằng số kiểu `set`. Đã sửa.
  - Job 15326 chạy lại ngày 27/10 lúc 17:45, mất 12 s và đạt: 8 khoang đã lưu được bỏ qua, phiếu nghe tạo xong.
  - Gói `rir_v1_thu_20261027_1745.tar.gz` đã tải về và khớp sha256, giải nén ở `tts_gen/runs/ket_qua_rir_v1_thu/`. Phiếu nghe: `runs/rir_v1/thu/nghe/nghe_thu_rir.xlsx` trong thư mục đó.
  - Kho thử: 8 khoang, mỗi lần mô phỏng 32 RIR mất 9,8 s CPU trên dgx01. MPV phải bốc 2–3 lần, các loại khác 1 lần.
  - 235/256 RIR đạt; 64/64 RIR ghế lái đạt.
  - EDT trung vị theo loại xe: hạng A 0,120 / sedan 0,109 / SUV 0,120 / MPV 0,131 s.

Chỗ khác kế hoạch, phát hiện khi viết mã (đã đo trên laptop):

1. **Luật nhận khoang.** Nếu đòi cả 32 RIR cùng đạt thì gần như không có khoang MPV nào được nhận. Trong 20 lần bốc, RIR ghế lái luôn đạt (EDT 0,08–0,13 s). Khoảng 8% RIR trượt, tập trung ở ghế sau và micro táp-lô của SUV/MPV.
   - Làm theo chữ của đặc tả: nhận khoang theo 8 RIR ghế lái.
   - RIR ghế khác mà trượt ngưỡng thì ghi `dat = false` kèm lý do, và không được gán. Không sinh lại riêng từng RIR, vì bốc lại vị trí đầu chỉ chọn ra vị trí lạ.
2. **Ray tracing của pyroomacoustics không tất định**, kể cả khi đặt cùng seed. Kho sinh một lần, lưu sha256 từng tệp; tái lập của bước gán và chập tính từ kho đã lưu.
3. **Đỉnh trực tiếp.** Lấy |h| lớn nhất trong ±0,25 ms quanh vị trí hình học, không lấy argmax cả RIR: ở micro xa, phản xạ cộng dồn có thể cao hơn đường trực tiếp. `dinh_max_sau_truc_tiep_ms` được ghi lại để xem.
4. **Kiểm "đỉnh trước đường trực tiếp".** pyroomacoustics lọc dải octave bằng FIR pha tuyến tính, nên RIR nào cũng có rung trước đỉnh (tới 6% biên độ, kể cả khi chỉ dùng image source). Vì vậy ngưỡng là biên độ trước đỉnh ≤ 20% đỉnh, không phải năng lượng.
5. **Kiểm độ trễ sạch/vang bằng đường đến đầu tiên.** Phép đo: giải chập Wiener ra RIR ước lượng, lấy mẫu đầu tiên đạt ≥ 50% đỉnh. Kết quả trên 400 bản phiếu nghe của cụm:
   - tương quan chéo thường lệch tới 20 ms; chỉ 56% bản dưới 2 ms;
   - GCC-PHAT (bản đầu tiên tôi đổi sang): 93,5% bản dưới 2 ms, vẫn trượt mốc 99%. 24/26 bản lệch trùng đúng vị trí phản xạ mạnh nhất của RIR, nên phép căn trễ vẫn đúng, chỉ là thước đo bắt nhầm;
   - đường đến đầu tiên: 400/400 bản trong khoảng −0,25…1,12 ms.
6. **EDT** = trung bình EDT các dải octave 250 Hz–4 kHz. Dải 8 kHz vượt Nyquist ở 16 kHz. Dải 250 Hz cao hơn hẳn (khoảng 0,2 s) do vật liệu ít hấp thụ âm trầm.
7. **Vật liệu:** mỗi mặt hộp trộn vật liệu của bảng pyroomacoustics theo tỷ lệ diện tích (kính, ghế bọc vải, thảm, trần vải), bốc ±20%. Tỷ lệ trộn là nhận định (`cauhinh/tang_cuong.py`).
8. **Chia train/dev: chờ người dùng chọn ở điểm dừng 2.** Dev chiếm 10% (cùng tỷ lệ 16/160 khoang); dev có 1 bản mỗi câu, train 2 bản (RIR.md). Cách băm chọn bằng `CHIA_DEV_THEO` trong `cauhinh/tang_cuong.py` (hoặc `--chia-theo`), mặc định `cau_goc`. Đo bằng `rir_gan` trên tập v1:

   | Chia theo | Câu gốc dev | Trùng lõi (core) với train | Trùng khung (frame_id) với train | Vùng lệch (mốc ≤ 2 điểm) | CS11 trong dev |
   |---|---|---|---|---|---|
   | `cau_goc` (mặc định) | 652 | 32% | 86% | 1,03 | 15 |
   | `core` | 661 | 0% | 70% | **3,40** (trượt) | 9 |
   | `frame_id` | 744 | 3% | 0% | 1,83 | 11 |

   Với `cau_goc`, không câu dev nào trùng chữ với train, nhưng phần lớn trùng mẫu câu. Vì vậy CER trên dev sẽ lạc quan.
9. **Câu ghép lời gọi dùng cùng khoang, ghế, micro với bản cùng số của câu gốc** (cùng người, cùng xe), vì các lựa chọn này lấy hạt giống từ (câu gốc, bản). Có RIR hay không và vị trí đầu vẫn theo hạt giống riêng `h32(sample_id, bản, seed)`.
10. **Không cắt lặng đầu/cuối** bản sạch (chưa có quyết định; `danh_gia_RIR.md` đề xuất không cắt đầu). Bản ra dài bằng bản sạch cộng tối đa 0,25 s đuôi.

Kiểm lại trên dữ liệu cụm (27/10 tối):
- **Luật nhận khoang:** 21 RIR loại, đều ở ghế sau, đều vì EDT vượt ngưỡng (0,151–0,180 s). Cặp ghế sau × micro táp-lô chỉ còn 7/16 và 10/16 RIR đạt, nên ít RIR khác nhau cho cặp đó. Tỷ lệ micro khi gán vẫn đều, vì ghế và micro được bốc trước, khoang bốc sau.
- **Không tất định:** mô phỏng lại sedan00 với đúng hình học của cụm (cùng seed). RIR khác nhau ở cả hai lần trên laptop và khác bản trên cụm; khác cả biên độ đường trực tiếp.
  - EDT của cùng RIR ghế lái: cụm 0,077, laptop 0,062 và 0,049 s.
  - Qua 5 lần lặp, độ lệch chuẩn EDT là 0,01–0,02 s. Tăng lên 100.000 tia không giảm được mà chậm 4,5 lần, nên giữ 20.000 tia.
  - Hệ quả: ngưỡng EDT 0,15 s là ranh giới "mềm" khoảng ±0,02 s. EDT ghi trong manifest đo trên đúng RIR đã lưu. sha256 của 8 tệp kho khớp manifest.
- **Độ trễ:** xem mục 5.
- **Chia dev:** xem mục 8.

Việc của người dùng (27/10):
1. Nghe phiếu `tts_gen/runs/ket_qua_rir_v1_thu/runs/rir_v1/thu/nghe/nghe_thu_rir.xlsx`, đợt 1 (40 bản, khoảng 15 phút). Kết luận: kho dùng được, hay vang quá / khô quá, hay có tiếng lạ.
2. Chọn cách chia dev: `cau_goc` / `core` / `frame_id` (mục 8).
3. Giữ ngưỡng EDT 0,15 s hay nới ra (ghế sau × micro táp-lô mất khoảng một nửa số RIR).
4. Cho phép gửi mã mới lên cụm và nộp `"kho gan"`; xem phân bố bảng gán; rồi cho nộp `"chap asr qa goi"` (job này xin 1 GPU).

Cách chạy trên cụm (nút đầu, từ `~/asr_tts_o_to/code/tts_gen`):
- `bash dieuphoi/slurm/nop_rir.sh thu`: kho thử 8 khoang và phiếu nghe; gói kết quả ở `~/asr_tts_o_to/ket_qua/rir_v1_thu_*.tar.gz`. **Dừng 1:** người dùng nghe.
- `bash dieuphoi/slurm/nop_rir.sh "kho gan"`. **Dừng 2:** người dùng xem `runs/rir_v1/gan/phan_bo.json`.
- `bash dieuphoi/slurm/nop_rir.sh "chap asr qa goi"`: bước này tự xin 1 GPU vì có `asr`.

## Context

Người dùng tạm chốt **luật chấm v1** (27/10/2026, sau khi nghe 49 câu trong `nghe_thu_full10k.xlsx`). Câu hỏi đặt ra: với dữ liệu TTS đã sinh, dự án đã đủ dữ liệu thực tế và đủ khả năng mô phỏng để làm bước RIR theo `docs/danh_gia_RIR.md` chưa, và có dùng được A100 không. Mọi số dưới đây đã đo trực tiếp trên laptop (`tts_gen/runs/ket_qua_full10k/runs/`) và trên cụm (chỉ đọc, ngày 27/10).

## 1. Đầu vào TTS theo v1: ĐỦ

| Phần | Số câu | Giờ âm thanh |
|---|---|---|
| 10k thường, v1 dat | 6.491 (Bắc 2.742 / Nam 2.532 / Trung 1.217) | 4,49 giờ (Bắc 1,75 / Nam 1,84 / Trung 0,91) |
| Ghép lời gọi, v1 dat, chỉ hai kiểu đủ cụm (255) và cắt đúng ranh giới (215); bỏ kiểu cắt giữa âm tiết | 470 | khoảng 0,3 giờ |
| **Tổng vào RIR** | **khoảng 6.960 file** | **khoảng 4,8 giờ** → với 2 bản cho mỗi câu train, khoảng 13.900 bản trộn |

- Bản 16 kHz `audio16` có đủ trên máy chủ (p01 có 1.014 tệp, wake có 1.002 tệp), nên **không cần lấy mẫu lại**. Laptop không có, nhưng việc chạy nằm trên cụm.
- Lệch miền: Trung chỉ chiếm 19% số câu. Điều này đã biết; với v1, người nghe là người Bắc nghe đúng 8/10 câu Trung. Phần Trung để mở cho tới khi có người miền Trung nghe.

## 2. Dữ liệu thực tế: CHƯA CÓ, nhưng không chặn bước mô phỏng

| Loại | Hiện trạng | Có chặn không |
|---|---|---|
| RIR đo trong xe (CAVEMOVE, IR64-CAR) | Chưa tải. Giấy phép CAVEMOVE chưa rõ; IR64-CAR chưa kiểm | Không chặn. Chạy bằng RIR mô phỏng trước, đúng như RIR.md đề xuất |
| Kích thước khoang và vật liệu xe thật | Chỉ có dải trong đặc tả; chưa đo xe đích | Không chặn. Kho mô phỏng dùng dải; chưa hiệu chỉnh |
| Ghi âm tiếng Việt thật trong xe (để kiểm định đầu cuối) | Không có | **Chặn việc kết luận "giống xe thật"**. Không chặn việc sinh dữ liệu |
| Nhiễu xe thật (AISHELL-5 CC BY-SA 4.0, nhiễu CAVEMOVE) | Chưa tải; đây là bước sau RIR | Không chặn bước RIR |
| Bảng preset (E01–E10 trong xlsx, P01–P08 trong đặc tả 15/10 không có trong repo) | Chưa chốt | **Không chặn**, nếu tách preset ra khỏi bảng gán RIR (xem mục 4). Preset chỉ cần ở bước nhiễu |

**Kết luận:** làm được một kho RIR mô phỏng có kiểm định nội bộ, gồm:
- dải EDT;
- độ trễ đường trực tiếp;
- hình dạng RIR;
- nghe thử;
- CER trước/sau khi chèn RIR.

**Chưa** kiểm định được với xe thật. Mục "mô phỏng so với đo" (B0) phải hoãn.

## 3. Khả năng mô phỏng và tài nguyên: ĐỦ (đã kiểm trên cụm)

- `pyroomacoustics` 0.10.1, giấy phép MIT, có wheel `cp313 manylinux_2_28_x86_64`, khớp Python 3.13.15 trên cụm. **Chưa cài.** Đề xuất cài vào một venv riêng `~/asr_tts_o_to/venv_rir` (numpy, scipy, soundfile, soxr, pyroomacoustics), để không làm đổi phiên bản numpy trong `venv_tts` đang ghim cho torch/VieNeu.
- `gpuRIR` (mô phỏng RIR trên GPU) **không có trên PyPI**, phải tự biên dịch CUDA, mà nút đầu không có `nvcc`. Không đáng làm, vì CPU đã dư.
- Mỗi nút dgx01/dgx02 có **256 lõi CPU**, 2 TB RAM, 8 × A100. Một job xin 32–64 lõi là đủ cho:
  - mô phỏng 5.120 RIR (ước tính vài chục phút, sẽ đo trên 50 RIR trước);
  - chập khoảng 14.000 bản (vài phút).
- A100 dùng cho: CER trước/sau RIR trên 500 câu dev. Gọi thẳng `buoc.asr_whisper` (L, M, T) trong job RIR, **không qua `dieu_phoi`**. Chập bằng torch trên GPU không cần thiết.
- **Bước RIR không lọc CER lần nữa.** Việc lọc đã làm một lần trên âm thanh sạch (v1). CER sau RIR chỉ được tính gộp để bắt lỗi pipeline (sai độ trễ, sai tần số lấy mẫu), không dùng để loại từng file, đúng như RIR.md mục G5.
- Đĩa: NFS còn 45 TB; phần RIR thêm khoảng 2–3 GB.
- **Hai việc vướng trên cụm (đã thấy ngày 27/10):**
  1. Tài khoản `user04` đang có **2 job `dh_*` của người khác chạy** (giới hạn chung 2 job), nên job của ta sẽ phải chờ tới khi một job kia xong. Không đụng vào job của họ.
  2. Còn tệp `runs/DUNG_CHAT_LUONG` từ lượt ghép lời gọi (Trung 0,209 < 0,23). Tệp này chỉ chặn các lượt chạy qua `dieu_phoi` (TTS → ASR → chấm), **không chặn job RIR**. Để nguyên; chỉ xử lý khi sinh lại TTS (ví dụ 25 câu Zing).

## 4. Kế hoạch thực hiện (sau khi duyệt)

1. **Ghi quyết định:** cập nhật CLAUDE.md và `docs/danh_gia_RIR.md` theo mục 4a, cùng số đầu vào ở mục 1 và bảng hiện trạng ở mục 2–3. Trong `docs/RIR.md`, thêm một dòng ghi chú ở đầu: preset dùng mã E theo xlsx; các trọng số theo đặc tả gốc.
2. **Mã** (theo lớp của `tts_gen/`, dùng lại các hàm có sẵn):
   - `cauhinh/tang_cuong.py`: dải kích thước 4 loại xe, ghế, micro, trọng số theo đặc tả gốc (micro đều 4 vị trí; ghế 70/20/10 cho mọi case), ngưỡng EDT 0,03–0,15 giây, −26 dBFS, đuôi 0,25 giây, P(RIR) = 0,8, tỷ lệ train/dev theo khoang (144/16).
   - `thuvien/rir.py`: EDT, T20, C50, DRR (chỉ ghi, không dùng làm ngưỡng); độ trễ đường trực tiếp; mức giọng hoạt động; chập FFT (`scipy.signal.fftconvolve`). Đọc/ghi qua `thuvien/am_thanh.write_flac`.
   - `buoc/rir_kho.py`: sinh RIR trong khoang hộp bằng `pyroomacoustics` (hybrid ISM + ray tracing, 16 kHz); bốc lại khoang khi EDT ghế lái nằm ngoài dải; ghi `rir_manifest.jsonl`; chạy song song bằng multiprocessing.
   - `buoc/rir_gan.py`:
     - đọc `gate_hop_v1.csv` (dat) cùng manifest; ghép lời gọi lọc theo `wake_type`/`wake_cat`;
     - hạt giống riêng mỗi bản = `thuvien/chon_cau.h32(sample_id, số bản, seed)`;
     - câu ghép và câu gốc (`parent_utt_id`) cùng split, cùng khoang;
     - **không gán preset**; ghi khoang, ghế, micro, rir_id.
   - `buoc/rir_chap.py`: chập, căn trễ, giữ đuôi, khôi phục −26 dBFS bằng mặt nạ của bản sạch, chống cắt đỉnh; ghi `aug_v1/_reverb/` (FLAC) và manifest.
   - `phantich/rir_qa.py`: phân bố EDT/DRR theo loại xe, ghế, micro; kiểm bảng gán; CER trước/sau (đọc kết quả ASR).
   - `kiemthu/test_rir.py`: xung đơn vị cho ra đúng bản sạch; độ trễ bỏ đúng; mức đúng −26 dBFS; hạt giống không đổi khi thêm file; câu ghép cùng split với câu gốc; không RIR dev nào nằm trong train.
   - `dieuphoi/slurm/chay_rir.sbatch` và `nop_rir.sh`:
     - `--cpus-per-task=64 --gres=gpu:a100:1`, chạy trong `venv_rir`, không qua `dieu_phoi`;
     - các bước: kho → gán → chập trên CPU; rồi `buoc.asr_whisper` (venv_tts) trên 500 câu dev, cả bản sạch lẫn bản vang, trên GPU;
     - `nop_rir.sh` từ chối nộp khi `user04` đang có job `asrtts_*`, để giữ quy tắc 1 job một lúc.
3. **Thử nhỏ trước (cùng job):**
   - 50 RIR để đo thời gian và EDT;
   - 5 câu × 20 RIR mỗi loại xe để tạo phiếu nghe (xlsx, giống `phantich/phieu_nghe_full10k.py`).
   - Người dùng nghe xong mới chạy cả kho.
4. **Chạy cả kho**, gán, chập, QA; đóng gói kết quả kèm sha256, tải về theo quy trình đã dùng.

## 4a. Quyết định đã chốt (người dùng, 27/10)

- Luật v1 (tạm chốt). Ghép lời gọi chỉ giữ kiểu đủ cụm và kiểu cắt đúng ranh giới.
- **Bảng preset = sheet `Preset_moi_truong` trong `data/du_lieu_asr_tts_o_to_v0.3.xlsx`** (mã E). Có 17 preset; 15 preset dùng cho ASR (E16, E17 là M5). E09 chưa ghi "Case dùng".
  - 8 mã P01–P08 **chỉ xuất hiện trong `docs/RIR.md`** (và trong bản đánh giá của tôi). Chúng lấy từ "đặc tả 15/10" viết ở ứng dụng Claude, không có trong repo. Bỏ mã P; sửa RIR.md và danh_gia_RIR.md theo mã E.
  - Preset được gán ở bước cộng nhiễu (đọc bảng E). Bảng gán RIR không có preset; P(RIR) = 0,8 cho mọi bản.
- Theo **đặc tả gốc**: micro bốc đều 4 vị trí; ghế lái 70 / phụ 20 / sau 10 cho mọi case, kể cả CS11. Vẫn lưu bộ đệm "chỉ có vang".
- Bước RIR không lọc CER. Không qua `dieu_phoi`, nên chưa cần xử lý tệp `DUNG_CHAT_LUONG`.

## 4b. Giải thích ba điểm cần chốt (người dùng hỏi 27/10)

**Tệp `DUNG_CHAT_LUONG` (đã đọc mã `dieuphoi/dieu_phoi.py`, dòng 211–218 và 332–334):**
- Đây là "điểm dừng chất lượng" của bộ điều phối. Sau khi chấm một phần, nếu tỷ lệ dat (v1) của vùng nào thấp hơn `NGUONG_DAT` trong `cauhinh/nguong.py` (Bắc 0,74 / Nam 0,63 / Trung 0,23), bộ điều phối ghi tệp này và không mở phần mới.
- Lần chạy tới, nếu tệp còn đó, `dieu_phoi` thoát ngay với mã 3 và không chạy gì.
- Tệp này được ghi ở **phần cuối cùng (wake)**, khi p01–p10 đã chạy xong, nên lúc đó **không dữ liệu nào bị chặn**.
- Mốc 0,23 được đặt cho câu thường. Câu ghép lời gọi khó hơn, và v1 vẫn còn đếm cả kiểu cắt giữa âm tiết. Vì vậy Trung 0,209 ở đây là báo động không có ý nghĩa mới; Trung thấp đã biết và đã chấp nhận khi chốt v1.
- Ảnh hưởng nếu để nguyên: mọi lượt chạy mới qua `dieu_phoi` (sinh lại 25 câu Zing, kiểm CER trước/sau RIR) đều dừng ngay. Job RIR viết riêng không qua `dieu_phoi` thì không bị chặn.
- Đề xuất: **không xóa mất thông tin**. Đổi tên tệp thành `runs/DUNG_CHAT_LUONG_wake_20261025.daxem`, có ghi một dòng lý do; như vậy vừa giữ dấu vết, vừa bỏ chặn.

**Vì sao cuối cùng vẫn phải chốt bảng preset:**
- Preset quyết định loại nhiễu, SNR mục tiêu, và câu nào được gán preset nào (cột "Case dùng"). Đó là việc của **bước cộng nhiễu**, nên mã bước đó phải đọc đúng một bảng.
- Hiện có hai bảng khác nhau. Xlsx có 17 preset mã E (E01–E10 có cột "Case dùng"; riêng E09 để trống cột này). RIR.md dùng 8 preset mã P, lấy từ đặc tả 15/10 không có trong repo.
- Với bước RIR, preset gần như không đóng vai trò gì: xác suất có RIR là 0,8 cho mọi preset (theo đặc tả), còn hầm thì RIR.md để sau.
- Vì vậy tách preset ra **không mất gì**. Ràng buộc "hai bản của cùng câu khác preset hoặc khác SNR" được đáp ứng ở bước nhiễu.
- Chỉ cần chốt bảng preset trước bước nhiễu, không cần trước bước RIR.

**Dùng đặc tả gốc thì có vấn đề gì (số CS11 theo v1: 166 câu, khoảng 332 bản):**
- *Micro bốc đều 4 vị trí:* không sai. Mỗi vị trí 25%, nên tập huấn luyện đa dạng hơn. Hệ quả là táp-lô và cột A chiếm nhiều hơn mức có thể gặp ở xe thật, nếu khảo sát phần cứng (micro thường gắn cụm trên trần) là đúng. Trọng số đề xuất 50/20/15/15 cũng **chưa có số đếm**, nên cả hai cách đều là phỏng đoán. Bốc đều là lựa chọn trung lập hơn.
- *CS11 lái 70 / phụ 20 / sau 10:*
  - Khoảng 233 trong 332 bản câu hành khách (ví dụ "Tôi ngồi sau, mở…") sẽ mang âm học ghế lái, tức nội dung và âm học không khớp nhau.
  - Ảnh hưởng tới mô hình nhỏ: tỷ lệ ghế sau toàn tập khoảng 10% theo đặc tả, khoảng 11% theo đề xuất.
  - Đặc tả gốc lại có lợi ở một điểm: ít dùng RIR ghế sau mô phỏng, vốn kém thật vì hộp không có lưng ghế.
- *Bộ đệm "chỉ có vang":* đặc tả không cấm.
  - Nếu không lưu, bước nhiễu phải chập lại mỗi lần đổi SNR, và không có hệ đối chứng "RIR không nhiễu".
  - Chi phí khoảng 1–1,5 GB trên NFS còn 45 TB.
  - Phương án "theo đặc tả gốc" trong câu hỏi vẫn giữ bộ đệm.

## 5. Kiểm chứng

- `python -m unittest discover -s kiemthu -t .`: 71 test cũ cộng test RIR mới.
- `rir_qa`: mọi RIR nằm trong dải EDT, lệch độ trễ < 1 ms, 0 RIR lỗi hình dạng; tỷ lệ có RIR 0,8 ± 0,02; tỷ lệ miền so với **tập đã lọc v1** lệch ≤ 2 điểm; train/dev không chung khoang.
- Chạy lại cùng seed: mã băm giống hệt. Thêm 100 file giả: mã băm các file cũ không đổi.
- CER trước/sau RIR trên 500 câu dev (L, M, và T đo riêng): ghi lại, dùng để bắt lỗi pipeline, không dùng để lọc.
- Phiếu nghe 30 bản mỗi loại xe và nhóm ghế.
