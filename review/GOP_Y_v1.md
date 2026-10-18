# Góp ý cho bộ m1m2_10k (gen10k-1.0) — vòng 1

Nguồn: kiểm độc lập trên claude.ai ngày 13/10/2026, đo bằng `review/diversity10k.py` (kết quả trong `diversity_report.json`, `diversity_near_dups.tsv`).
Đây là góp ý, không phải lệnh tuyệt đối: nếu thấy mục nào sai hoặc không hợp, ghi lý do vào báo cáo thay vì làm theo.

## Kết luận
Bộ đạt yêu cầu cấu trúc (hạn ngạch, cân bằng vùng, không trùng chuỗi, không còn chữ số), nhưng đa dạng thật thấp hơn con số 10.000:
- Chỉ 4.651/10.000 "lõi" câu khác nhau (che số, tên riêng, giá trị khe; bỏ tiền tố và tiểu từ).
- 986 câu có câu khác giống ≥ 0,9 (925 trong số đó cùng khung, chỉ khác "cho tui/giúp tui", "đi", "ạ").
- Tỷ lệ lõi/câu theo case: CS03 0,29 · CS02 0,37 · CS04 0,37 · CS06 0,39 · CS11 0,47 · CS07 0,46 · CS05 0,49 · CS12 0,50 · CS01 0,54 · CS08 0,57 · CS10 0,59 · CS09 0,73.
- Vùng: câu không có từ vùng nào — Bắc 74%, Trung 55%, Nam 52%. Đoán vùng từ chữ đạt 60%. Câu Trung chủ yếu khác bằng "tui/nghe/giùm", giống câu Nam.

## Việc cần làm (theo thứ tự)

### 1. Chống trùng theo lõi (bắt buộc)
- Thêm hàm lõi vào bộ sinh (có thể lấy `carrier()` trong `review/diversity10k.py`).
- Mỗi lõi tối đa 3 câu trên toàn bộ tập (ngưỡng đề xuất, sửa được bằng tham số).
- Tiêu chí đạt: không câu nào có hàng xóm cos ≥ 0,95 cùng khung; số câu có hàng xóm ≥ 0,9 giảm dưới 3%.

### 2. Thêm khung mới (bắt buộc)
- Mục tiêu: tỷ lệ lõi/câu ≥ 0,5 ở mọi case (ngưỡng đề xuất, chưa có bài báo kiểm). Ưu tiên CS03, CS02, CS04, CS06, CS11, CS07, CS05.
- Cách: diễn đạt lại bằng LLM từ khung hiện có (đổi cấu trúc câu, trật tự, động từ, câu hỏi gián tiếp, câu cụt), lưu vào file khung riêng với `frame_source = "LLM diễn đạt lại (cần duyệt)"`, `evidence = "constructed"`.
- Không tăng đa dạng bằng cách thêm giá trị khe; đó không phải điểm yếu.
- Nếu không đủ khung để giữ 10.000 câu sau bước 1, giữ ít câu hơn và báo số thật, đừng nới trần lõi.

### 3. Sửa lỗi cụ thể
- Tiền tố "Làm ơn" xuất hiện 527 câu (5%): giảm xuống khoảng 1%.
- "cho/giúp tui|tôi" gắn trước câu bắt đầu bằng "cảnh báo" làm sai nghĩa: bỏ "cảnh" (và các từ vừa là danh từ vừa là động từ) khỏi danh sách VERBS hoặc kiểm từ thứ hai. Ví dụ: CS08-M1-00224, CS08-M1-00331 (F0613), CS02-M1-00044, CS02-M1-00135 (F0915), CS02-M1-00260 (F0933).
- Gọi từ đánh thức hai lần: CS10-M1-00737 (F0759) "Này trợ lý, làm ơn kể chuyện cười đi trợ lý." Không thêm wake khi khung đã có "trợ lý".
- "VND" đọc "vê en đê": đổi khung F0733 thành "sang tiền Việt"/"sang đồng Việt Nam" (CS10-M1-00045, 00090, 00442, 00481).

### 4. Miền Trung (cần người bản ngữ, làm sau)
- Không tự sinh thêm từ Trung bằng K1. Chuẩn bị danh sách khung để người bản ngữ Trung Bộ viết lại theo tiểu vùng (Huế / Quảng Nam – Đà Nẵng / Nghệ Tĩnh); thêm trường `sub_region` nếu làm.

### 5. Đồng bộ tài liệu
- Sửa sheet Tu_dia_phuong (dòng "số 105") và hai cặp câu M4 CS07 trong `data/du_lieu_asr_tts_o_to_v0.3.xlsx` theo quy tắc linh (Bắc) / lẻ (Trung, Nam).
- Chép `review/diversity10k.py` vào `gen10k/`, chạy sau mỗi lần sinh; thêm chỉ số lõi vào `validate10k.py` (cảnh báo khi tỷ lệ lõi < 0,5).

## Báo cáo khi xong
Bảng trước/sau: tổng câu, số lõi, tỷ lệ lõi theo case, số câu gần trùng ≥ 0,9, tỷ lệ "Làm ơn", số khung mới theo case; danh sách mục không làm và lý do.
