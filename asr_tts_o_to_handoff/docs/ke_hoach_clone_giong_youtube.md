# Kế hoạch clone thêm giọng từ YouTube, phủ 3 miền

Ngày lập: 20/10/2026. Đường dẫn tính từ `asr_tts_o_to_handoff/asr_tts_o_to_handoff/`.

## 1. Vì sao cần thêm giọng

- Kho giọng có sẵn của VieNeu v3 Turbo lệch: Bắc 15, Nam 8, Trung 2.
- Sau kiểm tra, **Minh Triết bị loại** (CER gấp 5–8 lần giọng đối chứng ở cả 4 cấu hình). Miền Nam còn 3 giọng nam (Adam, Thái Sơn, Đức Trí), trong đó Thái Sơn có 3 câu bị cắt đầu dai dẳng.
- Câu miền Trung trải 4 tiểu vùng (thí điểm: Quảng Nam – Đà Nẵng 14, Huế 9, Nghệ Tĩnh 8, Nam Trung Bộ 2), nhưng 2 giọng Trung không khớp tiểu vùng. Câu có tiểu từ Quảng Nam ("nở") đang do giọng Huế đọc.

## 2. Số giọng cần thêm

| Vùng | Tiểu vùng | Cần thêm | Ghi chú |
|---|---|---|---|
| Trung | Huế | 1 nam, 1 nữ | |
| Trung | Quảng Nam – Đà Nẵng | 1 nam, 1 nữ | Tiểu vùng nhiều câu nhất |
| Trung | Nghệ Tĩnh | 1 nam, 1 nữ | Giọng khác Huế rõ rệt |
| Trung | Nam Trung Bộ | 1 nam, 1 nữ | |
| Nam | Nam Bộ | 2 nam | Thay Minh Triết, bù Thái Sơn |
| Bắc | Bắc Bộ | 0–1 | Chỉ khi Xuân Vĩnh (tham chiếu ~1 s) không qua nghe kiểm |

Tổng khoảng 10–11 giọng. Dự kiến khoảng một nửa ứng viên trượt kiểm định, nên cần tìm khoảng **20–24 ứng viên**.

## 3. Nguyên tắc về quyền và dữ liệu cá nhân

Đây là phần phải làm trước tiên. Tôi không phải luật sư; các điểm dưới đây cần người có chuyên môn xác nhận trước khi công bố dữ liệu.

- **Giọng nói có thể là dữ liệu cá nhân nhạy cảm.** Theo các phân tích về Nghị định 13/2023/NĐ-CP, dữ liệu sinh trắc học (trong đó có giọng nói) được xếp vào nhóm nhạy cảm. Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 có hiệu lực từ 01/01/2026 và xây dựng trên nền Nghị định 13.
- **Điều khoản YouTube không cho tải nội dung nếu không có nút tải hoặc sự cho phép.** Vì vậy công cụ chỉ tải khi:
  1. **Có đồng ý của chủ kênh hoặc người nói** (ưu tiên số 1, `permission = da_dong_y`). Ghi lại bằng chứng: email, tin nhắn, ngày.
  2. **Video có giấy phép Creative Commons** (`permission = cc_by`). Script kiểm lại trường giấy phép.
  3. Các trường hợp khác bị bỏ qua. Cờ `--cho-phep-chua-ro-quyen` chỉ dùng để thử nội bộ; giọng đó bị đánh dấu `chua_ro_quyen` và **không được dùng cho dữ liệu sẽ công bố**.
- **Không chọn:** người nổi tiếng, chính trị gia, phát thanh viên có thương hiệu giọng (rủi ro giả mạo), trẻ em, nội dung nhạy cảm.
- **Giảm thiểu dữ liệu:** chỉ tải đoạn tối đa 180 giây. Đặt `voice_id` ẩn danh (ví dụ `clone_trung_hue_f01`), giữ URL và tên kênh trong tệp meta nội bộ.
- **Không công bố:** đoạn tham chiếu gốc, `voices_clone.json` (chứa embedding giọng người thật), hay bản ghi tải về. Nên thêm `tts_gen/voice_clone/raw/`, `clips/` và `voices_clone.json` vào `.gitignore`.
- **Phương án tốt hơn vẫn là tự thu giọng tình nguyện viên có ký đồng ý.** Các công cụ dưới đây dùng được cho bản ghi tự thu: đặt `<cand_id>.wav` và `<cand_id>.meta.json` vào `raw/` rồi chạy từ bước 3.

## 4. Tiêu chí chọn video và người nói

- Một người nói liên tục (vlog, kể chuyện, hướng dẫn, podcast một người), không nhạc nền, không hiệu ứng.
- Mic gần, phòng ít vang; tránh quay ngoài trời và livestream nén mạnh.
- Văn phong tự nhiên, không đọc tin. Bài học từ Minh Triết: giọng mẫu đọc nhanh (~5 âm tiết/giây) cho đầu ra khó nghe. Ưu tiên tốc độ khoảng 4–5 âm tiết/giây.
- **Bằng chứng vùng:** người nói tự nêu quê trong video hoặc trên kênh. Người bản ngữ cùng tiểu vùng nghe xác nhận giọng thật của người đó. Không đoán vùng chỉ qua tên kênh.
- Người lớn, giới tính khớp chỗ cần bù trong bảng mục 2.

## 5. Quy trình và công cụ

Công cụ nằm trong `tts_gen/voice_clone/`. Cần thêm `pip install yt-dlp` và ffmpeg trong PATH.

| Bước | Việc | Công cụ | Đầu ra |
|---|---|---|---|
| 1 | Tìm ứng viên, xin phép chủ kênh, điền bảng | Tay; mẫu `candidates_template.csv` | `voice_clone/candidates.csv` |
| 2 | Tải đoạn ngắn (chỉ dòng có quyền) | `fetch_ref.py voice_clone/candidates.csv --out voice_clone/raw` | `raw/<cand_id>.wav`, `.meta.json`, `fetch_log.csv` |
| 3 | Cắt và xếp hạng đoạn 3–8 s | `pick_ref.py voice_clone/raw --out voice_clone/clips` | `clips/<cand_id>__c<k>.wav`, `phieu_chon_tham_chieu.csv` |
| 4 | Nghe chọn đoạn tham chiếu | Tay: điền `mot_nguoi_noi_YN`, `sach_YN`, `dung_giong_vung_YN`, `de_nghe_1_5`, `chon_YN` | `voice_clone/approved.csv` |
| 5 | Đăng ký giọng | `clone_validate.py register voice_clone/approved.csv` | `voice_clone/voices_clone.json` |
| 6 | Sinh câu thử: 8 câu đúng vùng/tiểu vùng × 2 seed, kèm 2 giọng đối chứng của vùng | `clone_validate.py gen --batch dot1` | `runs/clone_test/dot1/` |
| 7 | ASR như các lượt trước | `asr_check.py` (large, medium), `asr_diagnose.py` | `asr_*.jsonl`, `asr_diagnose.csv` |
| 8 | Báo cáo, sàng lọc, phiếu nghe mù | `clone_validate.py report --batch dot1 --lexicon ...` | `ket_qua.csv`, `tom_tat.md`, `nghe_mu/` |
| 9 | Nghe mù và quyết định | Người bản ngữ đúng tiểu vùng, ít nhất 2 người | Danh sách giọng nhận vào kho |

Chi tiết từng công cụ:

- **`pick_ref.py`** chỉ chọn đoạn có ít nhất 0,2 s im lặng trước và sau, để đoạn tham chiếu không bắt đầu giữa âm vị. Nó đo SNR ước lượng, tỷ lệ có tiếng, cắt đỉnh, vách cắt tần số (dấu hiệu nén mạnh) và mức nền trong quãng nghỉ (dấu hiệu nhạc nền), rồi gắn cờ `snr_thap`, `bang_thong_hep`, `cat_dinh`, `nen_lien_tuc`.
- **`clone_validate.py gen`** chọn 8 câu thử từ bộ v3, ưu tiên đúng tiểu vùng: 1 câu thuần Việt mỗi lớp độ dài, 2 câu có từ địa phương, 2 câu có từ ngoại lai, thiếu thì bù. Nó dùng cấu hình sinh A (như `run_pilot.py`), chạy `tts_checks` và đo **độ giống người nói** bằng chính bộ mã hóa VieNeu (cosine giữa embedding đầu ra và embedding tham chiếu).
- **`clone_validate.py report`** lấy CER nhỏ nhất qua mọi ASR (có biến thể từ điển), so với giọng đối chứng cùng nhóm, rồi tạo phiếu nghe mù có cột vùng và tiểu vùng nghe được.

## 6. Tiêu chí nhận giọng

**Sàng lọc tự động** (trong `tom_tat.md`):
- Không có lỗi kỹ thuật (cắt đầu, nói lan man, đọc thiếu).
- Trượt tối đa 2/16 câu (CER nhỏ nhất ≤ 0,1).
- CER trung bình không quá 2 lần giọng đối chứng kém hơn của cùng nhóm (tối thiểu 0,03).
- Độ giống người nói không thấp hơn đối chứng quá 0,05.

**Nghe mù** (bắt buộc với giọng qua sàng lọc):
- Đọc đúng lời ở ít nhất 15/16 câu.
- Dễ nghe trung bình ≥ 4/5.
- **Ít nhất 2/3 người nghe nhận đúng vùng, và đúng tiểu vùng với giọng Trung.** Đây là lý do chính để thêm giọng, nên là tiêu chí quan trọng nhất.

Với miền Trung, hai giọng đối chứng (Quang Sơn, Ngọc Trân) cũng có CER cao, nên so CER với đối chứng chỉ để chặn giọng tệ hơn. Kết luận về giọng vùng dựa vào người nghe.

## 7. Triển khai từ nhỏ đến lớn

| Đợt | Phạm vi | Mục đích | Điều kiện đi tiếp |
|---|---|---|---|
| 0 | 2–3 ứng viên bất kỳ có quyền | Chạy thông bước 2–8, sửa lỗi công cụ (`register` và `gen` chưa chạy thử) | Ra được `tom_tat.md` và phiếu nghe |
| 1 | Trung: mỗi tiểu vùng 2 ứng viên (8); Nam: 2 ứng viên nam | Lấp chỗ thiếu nhất | Có ít nhất 1 giọng đạt cho mỗi tiểu vùng Trung |
| 2 | Bù chỗ còn thiếu theo bảng mục 2 | Đủ nam và nữ mỗi tiểu vùng | Đạt bảng mục 2 |
| 3 | Chạy lại 100 câu thí điểm với kho giọng mới, gán lại giọng theo tiểu vùng | So CER, tỷ lệ đạt và nghe vùng với lượt cũ | Không tệ hơn lượt cũ ở Bắc/Nam; tốt hơn hoặc ngang ở Trung |

## 8. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Không xin được phép đủ người | Chuyển sang thu tình nguyện viên; giảm chỉ tiêu, ưu tiên Trung |
| Giọng clone không giữ được giọng vùng (khả năng giữ giọng vùng của VieNeu chỉ chấm 6/10) | Nghe mù là chốt chặn; nếu nhiều giọng trượt vì vùng, cân nhắc LoRA theo vùng |
| Đoạn tham chiếu YouTube bị nén, có nhạc | Cờ của `pick_ref.py` cộng nghe tay; thử `denoise` Y/N trong `approved.csv` nếu cần |
| Giọng clone cũng bị cắt đầu như Thái Sơn | `tts_checks` trong `gen`; giọng nào hay bị thì loại |
| Lộ dữ liệu giọng thật | Không đưa `raw/`, `clips/`, `voices_clone.json` vào git hay bản công bố |

## 9. Trạng thái công cụ

- `pick_ref.py`: đã thử trên bản ghi tổng hợp (ghép giọng TTS, thêm nhiễu, nhạc nền, cắt băng 8 kHz). Cờ `snr_thap` và `bang_thong_hep` bắt đúng.
- `clone_validate.py report` và phần chọn câu: đã thử với dữ liệu giả lập.
- `fetch_ref.py`, `clone_validate.py register` và `gen`: **chưa chạy thử**. Môi trường của tôi không truy cập được YouTube và không tải được mô hình VieNeu. Đợt 0 dùng để sửa lỗi phát sinh.
