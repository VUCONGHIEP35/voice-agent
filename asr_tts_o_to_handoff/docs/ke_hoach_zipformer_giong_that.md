# Kế hoạch: Zipformer-30M chấm bộ ket_qua_A và thử trên giọng thật

Ngày lập: 23/10/2026. Mỗi mục ghi rõ phần **đã kiểm** (đọc từ nguồn) và phần **giả định** (kiểm ở bước 1).

**Trạng thái (23/10/2026):** đã xong mục 2 và 3. Kết quả ở `tts_gen/reports/eval1000_A_zip/bao_cao_zipformer.md` và `so_nghe.md`.

- Các giả định ở mục 1 đều đúng: mô hình là loại offline, sherpa-onnx 2.0.0 có wheel cho Python 3.13.
- Bộ dữ liệu được giải nén vào `tts_gen/runs/ket_qua_A/`, không phải `runs_colab/` như dự kiến.
- Mục 4 (giọng thật) đang chờ người dùng quyết các điểm ở mục 6, từ điểm 2 trở đi.

## 0. Mục tiêu

1. Thêm một ASR thứ ba, khác kiến trúc với PhoWhisper (RNN-T thay vì encoder-decoder), để chấm 498 câu phần A. Hai câu hỏi:
   - Z có đổi kết quả chấm không, nhất là ở Trung (51/166 đạt)?
   - Z đóng góp thêm bao nhiêu so với L+M+c3?
2. Thu giọng thật của người dùng trên **cùng các câu** của phần A. So từng câu: giọng thật và giọng TTS, mỗi bên qua Z, L, M. Mục đích là trả lời: điểm ASR trên dữ liệu TTS có báo trước được điểm trên giọng người thật không?

## 1. Mô hình (đã kiểm trên Hugging Face ngày 23/10/2026)

- Repo `hynt/Zipformer-30M-RNNT-6000h`: Zipformer khoảng 30 triệu tham số, loss RNN-T, huấn luyện bằng k2/icefall trên khoảng 6.000 giờ tiếng Việt công khai. Theo thẻ mô hình, mô hình đạt hạng nhất VLSP 2025.
- WER do tác giả công bố: VLSP2025 Private 8,10; GigaSpeech2 7,56. Tác giả cũng công bố PhoWhisper-large đạt 16,31 và 10,00 trên hai tập này. Đây là số của tác giả, chưa đo lại.
- Tệp trên repo:
  - `encoder/decoder/joiner-epoch-20-avg-10.onnx` (fp32, encoder 92 MB) và bản `.int8.onnx` (encoder 28 MB);
  - `bpe.model`;
  - `config.json`: thực chất là bảng token "token id", khoảng 2.000 mục, `<blk>`=0;
  - `jit_script.pt` (107 MB), `qr.jpg`.
- Đầu ra là chữ HOA, không dấu câu, ví dụ "▁KHÔNG". `norm()` trong `asr_check.py` đã đưa về chữ thường và bỏ dấu câu, nên chấm chung được.
- **Giấy phép: CC BY-NC-ND 4.0.** Dự án là phi thương mại, nghiên cứu (CLAUDE.md), nên được dùng Z để đánh giá. Phần ND nghĩa là nếu sau này tinh chỉnh Z trên dữ liệu sinh thì **không được chia sẻ** bản đã tinh chỉnh. Nếu dự án chuyển sang thương mại thì không được dùng Z. Crate phostt ghi "Apache 2.0", nhưng điều đó trái với thẻ mô hình; tôi theo thẻ mô hình.
- **Giả định, sẽ kiểm ở bước 1:**
  - Mô hình là loại không streaming, chạy được bằng `sherpa_onnx.OfflineRecognizer.from_transducer`. Thẻ mô hình không ghi; kiểm bằng tên đầu vào của encoder.onnx (bản streaming có các đầu vào trạng thái cache).
  - Đầu vào 16 kHz, 80 fbank.
  - Có wheel `sherpa-onnx` cho Windows, Python 3.13.

## 2. Cài đặt (trên laptop, chạy CPU)

Z int8 nhỏ (khoảng 30 MB) và chạy trên CPU nên không cần Colab, không cần GPU. Cũng nhờ vậy, **giọng thật không phải rời khỏi máy**.

1. Tạo venv riêng `tts_gen/.venv_zip` (Python 3.13) để không đụng `.venv` của TTS/ASR. Cài ghim phiên bản: `sherpa-onnx`, `numpy`, `soundfile`, `soxr`. Ghi phiên bản vào `requirements_zip.txt`. Cache pip, tệp tạm và HF đặt dưới `tts_gen/.cache/` như `tts_env.py`, để không làm đầy ổ C:.
2. Tải từ HF, **ghim commit** (lấy hash qua API và ghi lại), vào `tts_gen/.cache/zipformer30m/`. Chỉ tải 3 tệp `.int8.onnx`, 3 tệp `.onnx` fp32, `bpe.model`, `config.json`. **Không tải `jit_script.pt`**: TorchScript nạp bằng pickle, có thể chạy mã, mà ta cũng không cần đến nó. Ghi sha256 từng tệp vào `nguon.json`.
3. Tạo `tokens.txt` từ `config.json`. Kiểm đủ 2.000 dòng, id liên tục 0..1999, `<blk>` là 0, khớp kích thước đầu ra của joiner.
4. Thử nhanh: nhận dạng 3 câu trong `runs/pilot100`, đã có audio16 trên laptop. In ra câu nghe được, thời gian và RAM.
   - **Điểm dừng:** nếu ra rỗng hoặc vô nghĩa, kiểm lại loại mô hình (offline hay streaming) và tokens trước khi đi tiếp.

## 3. Chấm 498 câu phần A bằng Z

1. Tải `ket_qua_A.tar.gz` và `.sha256` từ Drive. Kiểm sha256 phải ra `3970e7ba…8b49db`. Giải nén vào **thư mục mới** `tts_gen/runs_colab/`, không giải nén đè lên `runs/`. Kiểm: 510 dòng manifest, 510 tệp audio48.
2. Script mới `asr_zipformer.py`:
   - Đọc audio48 rồi hạ xuống 16 kHz bằng `soxr.resample` trong bộ nhớ. Gói tải về không có audio16, và đây đúng là cách `run_pilot.py` đã tạo audio16.
   - Nhận dạng, ghi `asr_Zipformer-30M-int8.jsonl` theo cùng dạng với `asr_check.py` (utt_id, hyp, cer…).
   - Ghi thời gian, số luồng CPU, RAM đỉnh. Không ghi đè tệp đã có.
   - Hai cách giải mã: `greedy_search` và `modified_beam_search` (beam 4).
   - Bản fp32 chỉ chạy trên 100 câu, để xem int8 có làm giảm chất lượng không.
3. Thêm cấu hình `Z` vào `gate_union.py`, không bắt buộc: chỉ dùng khi có tệp. Thêm các tập so sánh: Z, L+Z, L+M+Z, L+M+c3+Z. Cũng thêm vào `report_eval.py` và `compare_dtype.py` nếu cần. Viết test cho quy tắc mới, chạy lại bộ test cũ.
4. Ghi kết quả vào thư mục mới `reports/eval1000_A_zip/`. Không ghi đè `reports/eval1000`. Báo cáo gồm:
   - CER trung bình theo vùng của Z, L, M.
   - Số câu đổi kết quả chấm khi thêm Z.
   - Số câu chỉ đạt nhờ Z.
   - Riêng Trung: Z có kéo các câu `chi_loi_thanh` và `dat_1nguon` lên không.

Chưa đo thời gian chạy trên laptop. Tác giả ghi khoảng 0,3 s CPU cho một đoạn 12 s. Nếu đúng vậy thì 498 câu (khoảng 22 phút âm thanh) mất cỡ vài phút.

## 4. Thiết kế thu giọng thật

### 4.1 Chọn câu: `select_real.py` → `giong_that/phieu_thu_am.csv` và `.md` để in

- Lấy từ 498 câu phần A, để mỗi câu đã có sẵn bản TTS và kết quả L, M, Z để so.
- Mặc định **60 câu**, đọc mất khoảng 10–15 phút:
  - 5 câu cho mỗi case CS01–CS12;
  - trộn độ dài: Rất ngắn, Ngắn, Thường, Dài;
  - ít nhất 8 câu có từ ngoại (Spotify, Google Maps, VETC…);
  - ít nhất 10 câu mà TTS bị chấm `can_nghe` hoặc `loai`, để xem lỗi nằm ở TTS hay ở ASR.
- Ưu tiên câu có `lexicon_variant` trùng vùng của người đọc, cộng thêm câu trung tính. Đọc từ địa phương của vùng khác sẽ không tự nhiên.
- Phiếu ghi: số thứ tự, `sample_id`, câu cần đọc (`text_spoken`), và ghi chú cách đọc từ ngoại đã duyệt. Người đọc được đọc theo thói quen của mình, nhưng nếu đọc khác thì ghi lại.

### 4.2 Quy cách tệp người dùng gửi

| Mục | Yêu cầu |
|---|---|
| Định dạng | Tốt nhất là WAV PCM 16-bit, **mono**, 16 kHz hoặc 48 kHz (bản gốc giữ nguyên, ASR dùng bản hạ 16 kHz). **MP3 cũng nhận** (đã thử: soundfile 0.14 / libsndfile 1.2.2 đọc được), nên từ 128 kbps trở lên. Không nhận m4a/aac vì máy không có ffmpeg. Định dạng tệp được ghi lại để tách khi phân tích |
| Mỗi tệp | 1 câu, có 0,5 s im lặng ở đầu và cuối, dài 0,5–15 s |
| Tên tệp | `<sample_id>__<dieu_kien>.wav`, ví dụ `CS04-M1-00008__phong.wav` |
| Điều kiện | `phong` (phòng yên tĩnh) là bắt buộc. Tùy chọn: `xe_no_may` (trong xe, nổ máy, bật điều hòa) và `xe_chay` (xe đang chạy, người khác lái) |
| Cách đọc | Tự nhiên như đang ra lệnh trong xe, không đọc chậm từng chữ. Vấp thì thu lại cả câu |
| Thiết bị | Điện thoại hoặc micro, đặt cách miệng khoảng 30–50 cm (gần giống micro trên xe). Ghi tên thiết bị |
| Kèm theo | `nguoi_noi.json`: mã người nói (ví dụ `nguoi01`, không ghi tên thật), vùng, tiểu vùng, giới, nhóm tuổi, thiết bị, điều kiện |

Cách gửi: chép tệp vào `tts_gen/giong_that/nhan/<đợt>/`, rồi báo tôi. Không cần đưa lên mạng.

### 4.3 Riêng tư

Giọng nói là dữ liệu sinh trắc.

- Trước khi nhận tệp, thêm `asr_tts_o_to_handoff/tts_gen/giong_that/` vào `.gitignore`. `*.wav` đã nằm sẵn trong đó.
- Không đẩy lên git, không chép lên Colab hay Drive nếu người dùng chưa đồng ý.
- **Không dùng để clone giọng**, không đưa vào TTS. Quy tắc "không clone giọng" vẫn giữ nguyên.
- Xóa toàn bộ khi người dùng yêu cầu.

### 4.4 Kiểm tệp nhận: `check_real_wav.py` (coi như dữ liệu chưa tin cậy)

- Chỉ nhận đuôi `.wav` hoặc `.mp3`, mỗi tệp tối đa 20 MB. Kiểm thêm phần đầu tệp có đúng định dạng không: WAV phải bắt đầu bằng `RIFF…WAVE`, MP3 phải bắt đầu bằng thẻ `ID3` hoặc khung MPEG. Đọc header bằng `soundfile`, chạy Python với `-I` và đường dẫn truyền qua tham số.
- Nếu gửi zip: chặn đường dẫn `..` hoặc tuyệt đối, symlink, tổng dung lượng giải nén quá giới hạn, số tệp quá giới hạn.
- Kiểm nội dung từng tệp:
  - đúng PCM;
  - số kênh: stereo thì lấy trung bình hai kênh và báo lại;
  - tần số lấy mẫu ít nhất 16 kHz;
  - thời lượng 0,5–15 s;
  - mẫu bị xén đỉnh (|x| ≥ 0,999) không quá 0,1%;
  - đỉnh không thấp hơn −30 dBFS (tránh thu quá nhỏ);
  - có im lặng ở đầu (dùng lại kiểm `cat_dau` của `tts_checks.py`);
  - ước lượng SNR.
- Kiểm danh sách: tên tệp phải khớp `sample_id` trong phiếu, báo câu thiếu, thừa, trùng.
- Có test bảo mật: zip có `..`, symlink, tệp giả đuôi `.wav`, header hỏng, tệp 0 byte, tệp quá lớn, stereo, 8 kHz.

### 4.5 Chạy và so

1. Ghi `giong_that/manifest.jsonl` cùng dạng với manifest TTS. Dùng `text_spoken` và `tts_text` của câu gốc để chấm bằng cùng `answer_variants` và từ điển `lexicon/asr_bien_the.tsv`.
2. Chạy trên laptop, **lần lượt từng mô hình**: Z (CPU), rồi L (CT2 int8, khoảng 2 GB VRAM, đã chạy được trên laptop), rồi M (lô 2). Theo dõi RAM bằng `mem_watch.py`; RAM trống dưới 0,5 GB thì dừng.
3. Báo cáo `reports/giong_that/bao_cao.md`:
   - CER của Z, L, M trên giọng thật, chia theo điều kiện thu.
   - Bảng cặp từng câu: CER giọng thật và CER TTS (giọng VieNeu đã sinh câu đó). Tương quan hạng Spearman giữa hai cột.
   - Tỷ lệ cùng kết quả chấm giữa giọng thật và TTS.
   - Hai danh sách quan trọng nhất:
     - (a) giọng thật nghe đúng nhưng TTS bị loại: lỗi do TTS;
     - (b) TTS đạt nhưng giọng thật sai: ASR yếu với giọng người, hoặc câu khó đọc tự nhiên.
   - Câu có từ ngoại: người dùng đọc thế nào, có khớp cách phiên âm đã duyệt không.
4. Bộ giọng thật này là mầm của "bộ thật giữ riêng" ghi trong mục tiêu ở CLAUDE.md. Vì vậy **không bao giờ** dùng nó để huấn luyện hay tinh chỉnh, chỉ dùng để đánh giá.
5. Giới hạn: chỉ có 1 người nói và 60 câu. Kết luận chỉ đúng cho giọng đó, không suy ra cho cả vùng. Khoảng tin cậy Wilson sẽ rộng, khoảng ±12 điểm phần trăm.

## 5. Điểm dừng

- sha256 của gói hoặc của mô hình lệch.
- Z ra rỗng hoặc vô nghĩa sau bước 2.4.
- RAM trống dưới 0,5 GB, hoặc ổ C: còn dưới 3 GB.
- Tệp giọng thật không qua kiểm 4.4. Khi đó báo danh sách tệp lỗi, không tự sửa âm thanh.
- Thiếu câu, trùng câu, hoặc tên tệp không khớp phiếu.

## 6. Cần người dùng quyết

1. Xác nhận dùng Z theo **CC BY-NC-ND**: chỉ đánh giá và nghiên cứu, không chia sẻ bản tinh chỉnh.
2. Vùng, tiểu vùng và giới của người đọc, để chọn câu đúng phương ngữ.
3. Số câu (mặc định 60) và điều kiện thu (chỉ `phong`, hay thêm `xe_no_may` / `xe_chay`).
4. Sau khi có kết quả: có đưa Z vào cổng chấm chính thức cho phần B và bộ 10.000 câu không.

## 7. Thứ tự làm

1. Cài và thử nhanh Z (mục 2).
2. Lấy `ket_qua_A` về, chấm bằng Z (mục 3).
3. Tạo phiếu thu âm (4.1) và gửi người dùng.
4. Người dùng thu âm.
5. Kiểm tệp (4.4).
6. Chạy ASR và so (4.5).
7. Báo cáo.

Bước 1–3 làm được ngay trong lúc chờ thu âm.
