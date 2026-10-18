# Báo cáo vòng 2: app trên màn hình xe và từ ngoại lai (CHANGES_v3.md)

Ngày 15/10/2026. Bộ mới: `asr_tts_o_to_handoff/data/m1m2_10k_v3/` (gen10k-3.0, seed 20261013). Bộ v1, v2 giữ nguyên; sha256 mọi file của v2 vẫn khớp sau khi chạy.
Đầu vào: `CHANGES_v3.md`, `review/PHU_LUC_app_tren_man_hinh_va_tu_ngoai.md`, `review/BANG_tu_ngoai_lai.csv`, và các quyết định của người dùng ngày 15/10 (cuối báo cáo).

**Kiểm số gốc.** Chạy `diversity10k.py` trên bản chép v2 trong thư mục tạm, không ghi đè báo cáo của v2. Số khớp CHANGES_v3 mục 5: 7.228 lõi, tỷ lệ 0,723, mọi case ≥ 0,6 (thấp nhất CS03 0,606), 0 câu cos ≥ 0,9.

**Chạy sau mỗi bước.** Sau mỗi bước C1 → C3 → C2 → C4/C5 → C6 đều chạy `test_vnnum.py` (9/9 đạt) và `validate10k.py`.
- Trước C6, validate chạy trên bản chép v2 và các bản sinh thử: 0 lỗi.
- Sau C6, bản chép v2 báo lỗi vì thiếu các trường mới. Như vậy là đúng: kiểm tra mới có tác dụng.
- Bộ cuối: chạy thêm `diversity10k.py` và `compare10k.py`.

## 1. Bảng v2 → v3

| Chỉ số | v2 | v3 |
|---|---|---|
| Tổng câu | 10.000 | 10.000 |
| Hạn ngạch theo case | đủ | đủ, không đổi |
| Vùng Bắc / Trung / Nam | 3.333 / 3.334 / 3.333 | 3.333 / 3.334 / 3.333 |
| Câu nhóm G1–G8 | 0 (chưa có khung) | 770 |
| Số lõi khác nhau theo `carrier` (tỷ lệ) | 7.228 (0,723) | 7.032 (0,703) |
| Câu thuộc lõi lặp ≥ 10 lần (`carrier`) | 0 | 77 (lõi "mở <tên>", "đọc thông báo từ <tên>"…) |
| Lõi lặp nhiều nhất theo `carrier_cap` | 3 | 3 |
| Câu có hàng xóm cos ≥ 0,9 | 0 | 0 |
| Câu có hàng xóm cos ≥ 0,8 | 1.976 | 2.010 |
| Câu dựng từ mẫu `seen` | 682 | 605 |
| `cần duyệt` / `nên duyệt` / `không bắt buộc` | 4.517 / 1.301 / 4.182 | 5.161 / 1.211 / 3.628 |
| `language_mix` = "Việt + Anh" | 800 | 1.285 |
| `validate10k.py` | 0 lỗi | **1 lỗi** (CS07, mục 4) |

Số câu theo nhóm. Mục tiêu lấy từ CHANGES_v3 mục 6. Mọi nhóm đạt đủ, không nhóm nào thiếu khung.

| Nhóm | Mục tiêu | v3 | Case | Khung viết | Khung dùng | Lõi/câu (`carrier_cap`) |
|---|---|---|---|---|---|---|
| G1 mở app theo tên | 150 | 150 | CS04 | 15 | 15 | 0,81 |
| G2 điều khiển video/nhạc | 100 | 100 | CS04 | 71 | 62 | 0,67 |
| G3 tìm nội dung trong app | 100 | 100 | CS04 | 24 | 24 | 0,66 |
| G4 chuyển màn hình, chia đôi | 70 | 70 | CS04 | 22 | 22 | 0,76 |
| G5 xe đỗ / ghế sau | 40 | 40 | CS04 25 + CS11 15 | 21 | 20 | 0,95 |
| G6 chọn app bản đồ | 80 | 80 | CS01 55 + CS04 25 | 24 | 24 | 0,76 |
| G7 tin nhắn app bên thứ ba | 150 | 150 | CS05 | 22 | 22 | 0,74 |
| G8 thu phí không dừng | 80 | 80 | CS01 | 19 | 19 | 0,61 |
| Tổng | 770 | 770 | | 218 | 208 | |

- G1–G4 có 420 câu, bằng 35% hạn ngạch CS04.
- Toàn CS04 có 470 câu nhóm G (39%), vì G5 và G6 có phần nằm ở CS04.
- Khung dùng theo case: CS01 35, CS04 143, CS05 22, CS11 8.

Số câu chứa từng tên, đếm trên `text_raw` (v2 → v3):

| Tên | v2 → v3 | Tên | v2 → v3 |
|---|---|---|---|
| YouTube | 3 → 79 | Zalo | 133 → 182 |
| YouTube Music | 5 → 9 | Messenger | 16 → 76 |
| Spotify | 4 → 34 | Viber | 11 → 57 |
| Zing MP3 | 9 → 27 | Telegram | 6 → 55 |
| Apple Music | 6 → 7 | Facebook | 0 → 13 |
| Gmail | 0 → 14 | Google Maps | 0 → 42 |
| Vietmap | 0 → 41 | Waze | 0 → 37 |
| VETC | 0 → 48 | ePass | 0 → 41 |
| Apple CarPlay | 3 → 10 | Android Auto | 4 → 13 |

Lõi/câu theo case:
- Tiêu chí của người dùng: câu không thuộc G tính theo `carrier`, mỗi case không giảm quá 0,02 so với v2. Câu G tính theo `carrier_cap`, phải ≥ 0,5.
- Cột "chung" là số đo trên mọi câu của case theo `carrier`, ghi thêm để tham khảo.

| Case | v2 | v3 chung | v3 không thuộc G | Chênh (không G − v2) | Câu G | v3 G (`carrier_cap`) |
|---|---|---|---|---|---|---|
| CS01 | 0,755 | 0,741 | 0,754 | −0,001 | 135 | 0,68 |
| CS02 | 0,660 | 0,687 | 0,687 | +0,027 | 0 | |
| CS03 | 0,606 | 0,596 | 0,596 | −0,010 | 0 | |
| CS04 | 0,726 | 0,618 | 0,712 | −0,014 | 470 | 0,74 |
| CS05 | 0,731 | 0,687 | 0,722 | −0,009 | 150 | 0,74 |
| CS06 | 0,664 | 0,684 | 0,684 | +0,020 | 0 | |
| CS07 | 0,740 | 0,718 | 0,718 | **−0,022** | 0 | |
| CS08 | 0,789 | 0,797 | 0,797 | +0,008 | 0 | |
| CS09 | 0,777 | 0,813 | 0,813 | +0,036 | 0 | |
| CS10 | 0,809 | 0,805 | 0,805 | −0,004 | 0 | |
| CS11 | 0,697 | 0,723 | 0,723 | +0,026 | 15 | 0,93 |
| CS12 | 0,727 | 0,724 | 0,724 | −0,003 | 0 | |

Hai cột G của CS01, CS04, CS05, CS11 tính trên câu G trong từng case. Tỷ lệ theo từng nhóm G ở bảng trên.

Tỷ lệ chung của CS04 (0,618) và CS05 (0,687) giảm so với v2. Lý do: theo `carrier`, các lệnh ngắn "mở YouTube", "mở Zalo"… gom về một lõi. Phụ lục S2 và S4 đã lường trước việc này.

Vòng lọc TF‑IDF không gom nhầm lệnh "mở X":
- cos("mở youtube", "mở spotify") = 0,13;
- cos("mở youtube", "mở youtube lên") = 0,67;
- lọc 3 vòng: 771 → 26 → 0 câu.

## 2. Câu của v2 bị thay hoặc bị loại

So theo `text_raw` sau khi bỏ dấu câu và chữ hoa, không so theo `sample_id`: mã đánh theo vị trí trong case nên không so được. Danh sách đầy đủ ở `data/m1m2_10k_v3/so_voi_v2.tsv`, có 8.618 dòng `v2_khong_con_trong_v3` và 8.618 dòng `v3_moi`, mỗi dòng kèm `sample_id` và `frame_id` của bộ chứa câu.

| Case | v2 | Câu v2 còn nguyên | Câu v2 không còn | Câu mới ở v3 | Trong đó nhóm G |
|---|---|---|---|---|---|
| CS01 | 1.500 | 127 | 1.373 | 1.373 | 135 |
| CS02 | 300 | 49 | 251 | 251 | 0 |
| CS03 | 1.400 | 284 | 1.116 | 1.116 | 0 |
| CS04 | 1.200 | 114 | 1.086 | 1.086 | 470 |
| CS05 | 1.200 | 62 | 1.138 | 1.138 | 150 |
| CS06 | 500 | 125 | 375 | 375 | 0 |
| CS07 | 600 | 62 | 538 | 538 | 0 |
| CS08 | 700 | 91 | 609 | 609 | 0 |
| CS09 | 300 | 66 | 234 | 234 | 0 |
| CS10 | 1.100 | 98 | 1.002 | 1.002 | 0 |
| CS11 | 300 | 60 | 240 | 240 | 15 |
| CS12 | 900 | 244 | 656 | 656 | 0 |
| Tổng | 10.000 | 1.382 | 8.618 | 8.618 | 770 |

**Vì sao gần như mọi câu đều đổi.** Bộ sinh dùng một luồng `rng` chung, đi qua các case theo thứ tự CS01 → CS12. Thêm khung ở CS01 (G6, G8) làm đổi mọi lần rút ngẫu nhiên phía sau, nên câu khác nhau dù khung cũ không đổi. Đây không phải là khung cũ bị bỏ:
- mã khung cũ giữ nguyên, vì khung mới được nối vào cuối danh sách;
- số khung cũ được dùng gần như không đổi ở các case không có G.

**Số câu mất thật ở từng case** là số chỗ trong hạn ngạch nhường cho nhóm G: CS01 135, CS04 470, CS05 150, CS11 15; các case khác 0. Ý định bị lấy chỗ nhiều nhất (v3 so với v2):

| Ý định | Thay đổi |
|---|---|
| CS04 phát bài/ca sĩ | −196 |
| CS04 phát thể loại/playlist | −113 |
| CS05 gửi tin nhắn | −75 |
| CS04 thích/lưu bài | −48 |
| CS01 dẫn đường đến địa chỉ | −40 |
| CS04 radio | −33 |
| CS05 gọi theo tên | −32 |

CS08 thời tiết cũng −32, nhưng đó là dao động `rng`, vì CS08 không có khung G.

## 3. Cờ cách đọc từ ngoại

Cột duyệt vùng trong bảng đều trống. Vì vậy chưa câu nào được thay cách đọc: `pron_variant` rỗng ở cả 10.000 câu.

- **1.001 câu** có cờ `cách đọc chưa xác minh: <tên>` (mức cần duyệt). Theo tên:
  - Zalo 182, YouTube 79, Messenger 76, Viber 57, Telegram 55, VETC 48, Mall 43, Google Maps 42, Vietmap 41, ePass 41, Waze 37, Spotify 34, podcast 34;
  - Vinhomes 28, Zing MP3 27, Aeon 22, playlist 21, Wi-Fi 16, Gmail 14, Takashimaya 13, Facebook 13, Android Auto 13, Apple CarPlay 10, Bluetooth 10, YouTube Music 9;
  - Lotte 8, Eco 8, Apple Music 7, hip hop 7, lo-fi 6, remix 6, ballad 5, Cruise Control 5, air-con 4, Normal 4, Sport 3, K-pop 3.
- **284 câu** có cờ `cách đọc từ ngoại đã đổi chữ, chưa duyệt theo vùng: <tên>` (mức nên duyệt). Theo tên: video 99, camera 67, MHz 48, FM 44, USB 13, ABS 13, AQI 9, radio 9, USD 7, ATM 6, PM2.5 4, kWh 4.
- Một câu có thể mang cả hai mức, và có thể đã "cần duyệt" vì lý do khác (giọng Trung, khung v2/v3).
- Validate kiểm rằng mọi tên trong bảng xuất hiện ở `text_raw` mà chưa duyệt đều có cờ đúng mức: 0 lỗi.
- Nhánh "đã duyệt" mới chỉ thử bằng một bảng giả, chưa chạy trên dữ liệu thật:
  - YouTube, Bắc ghi `1,2` → `text_spoken` thành "diu túp", `pron_variant` = `L01-1`;
  - YouTube, Nam ghi `0` → giữ "YouTube" và gắn cờ cần duyệt;
  - USB, Bắc ghi `2` → "diu ét bi", `L32-2`.

## 4. Mục chưa làm được hoặc làm khác CHANGES_v3.md

1. **Tiêu chí mục 6 "validate 0 lỗi" chưa đạt: còn 1 lỗi.** CS07 có tỷ lệ lõi/câu (câu không thuộc G) 0,718, giảm 0,022 so với v2, quá ngưỡng 0,02.
   - CS07 không có khung G. Mức giảm do `rng` đổi khi sửa hai khung ở CS04.
   - Đo trên ba seed, mức lệch so với v2 nằm trong khoảng −0,038 đến +0,050 mỗi case. Một bản sinh trước đó (trước khi sửa hai khung lỗi nghĩa) đạt 0 lỗi.
   - Người dùng chọn chấp nhận là dao động và giữ ngưỡng 0,02. Không đổi seed, không thêm cơ chế ưu tiên lõi mới.
2. **C4 chưa có hiệu quả thật** vì bảng chưa ai duyệt (CHANGES_v3 mục 4 đã báo trước).
   - Vietmap, Waze, VETC, ePass chưa có cách đọc nào, nên `text_spoken` giữ chữ Latin và TTS sẽ tự đọc. Cần duyệt bảng trước khi sinh âm thanh.
3. **`seen` không hồi phục.** Lý do C1 là lấy lại câu `seen` bị trần lõi cắt (839 → 682), nhưng v3 còn 605. Trần theo `carrier_cap` cho phép thêm câu có tên app, nhưng 770 chỗ nhường cho nhóm G đã lấy phần lớn từ ý định giải trí và tin nhắn, vốn nhiều khung `seen`.
4. **Chỗ không khớp code ở mục 3 của CHANGES_v3**, làm theo code như người dùng chỉ định:
   - dòng JSONL được ghép trong `main()` của `build10k.py`, không phải gần dòng 429;
   - số câu theo nhóm điều khiển bằng trần cứng theo (nhóm, case) cộng với sinh nhóm G trước. Không dùng trọng số `w`, vì trường `w` của `F(...)` không được bộ sinh đọc.
5. **Mục 5 bước 1:** chạy `diversity10k.py` trên bản chép v2. Chạy thẳng trên v2 sẽ ghi đè báo cáo của v2.
6. **Mục 8:** CLAUDE.md đã có sẵn bốn việc của mục 8 từ trước. Không tạo `CLAUDE_v1_truoc_v3.md`: người dùng chỉ định dùng `CLAUDEv1.md` có sẵn làm bản lưu. Chỉ cập nhật khối "Trạng thái vòng 2".
7. **Trường thêm ngoài spec**, người dùng đã đồng ý:
   - `core_cap`: lõi dùng cho trần; `core` vẫn theo `carrier` như v2;
   - `app_group`;
   - tập `APP_FIDS`, tách khỏi `NEW_FIDS`.
8. **Phân case** (CHANGES_v3 để ngỏ):
   - G5: CS04 (xe đỗ) và CS11 (ghế sau);
   - G6: CS01 (dẫn đường) và CS04 (đổi app bản đồ);
   - G8: CS01. Ở v2, câu có "thu phí" chỉ nằm ở CS01 và CS10.
9. **`platform`:** chưa có câu `oem_vinfast`. Không có nguồn lệnh riêng cho màn hình VinFast ngoài từ đánh thức, mà từ đánh thức đang chờ quyết định (mục 9.1). G7 với Zalo, Viber ghi `any`, chờ kiểm Android Auto (mục 9.6).
10. **Không làm theo CHANGES_v3 mục 7** và quyết định của người dùng:
    - không thêm Hey VinFast / Hey Google;
    - không thêm G9 gọi xe hay ví điện tử;
    - không thêm Netflix, TikTok, V-Green;
    - không tự điền cách đọc;
    - không thêm từ miền Trung;
    - không sửa `carrier`;
    - không sửa tay JSONL.
11. **Chưa chính xác về chất lượng câu:**
    - 218 khung G là K1, chưa duyệt. Một số tổ hợp khe nghe gượng ("quay lại ePass", "ứng dụng lịch").
    - Hai khung lỗi nghĩa đã sửa trước bản cuối: "mở Waze giải trí chút" và câu trần "Lịch.".
    - Trong từng nhóm G, ba vùng chưa chia đều tuyệt đối (ví dụ G4: Bắc 31, Trung 22, Nam 17), dù từng case vẫn cân bằng.
12. **`review/diversity10k.py` và `gen10k/diversity10k.py` nay khác nhau.** Bản trong `gen10k/` có thêm `build_keep` và `carrier_cap`; hàm `carrier` giữ nguyên. Nếu muốn chạy đo bằng bản trong `review/`, cần chép lại.

## Tệp đã sửa hoặc thêm

- Sửa:
  - `gen10k/diversity10k.py`: thêm `build_keep`, `carrier_cap`.
  - `gen10k/build10k.py`: gen10k-3.0; trần lõi theo `carrier_cap`; trần theo nhóm và sinh nhóm G trước; quét bảng từ ngoại; thêm `platform`, `pron_variant`, `core_cap`, `app_group`; mặc định ghi v3.
  - `gen10k/pools10k.py`: `APPS` thêm 4 tên; thêm `MUSIC_APPS`, `MSG_APPS`, `MAP_APPS`, `ETC_APPS`, `LINK_SRC`, `CHANNELS`, có ghi nguồn.
  - `gen10k/slots10k.py`: `g_named` thay cho `g_link_src` / `g_app_from` / `g_app`; thêm khe `map_app`, `etc_app`, `kenh`.
  - `gen10k/frames10k.py`: nạp `frames_app10k`, thêm `APP_FIDS`.
  - `gen10k/validate10k.py`: thêm trường và kiểm tra mục 6.
- Thêm:
  - `gen10k/frames_app10k.py`;
  - `gen10k/loanwords10k.py`;
  - `gen10k/compare10k.py`.

## Quyết định của người dùng (15/10/2026)

- Tiêu chí lõi:
  - câu không thuộc G theo `carrier`, mỗi case giảm không quá 0,02 so với v2;
  - câu G theo `carrier_cap`, ≥ 0,5;
  - vẫn báo số chung theo `carrier`.
- CS07 −0,022: chấp nhận là dao động `rng`.
- Hai mức cờ:
  - nên duyệt: từ vay Việt hóa, viết tắt đã đổi chữ;
  - cần duyệt: tên giữ chữ Latin hoặc chưa có cách đọc.
- Không thêm Netflix, TikTok, V-Green.
- G3 dùng tên kênh mô tả.
- Chạy diversity cho số gốc trên bản chép.
- `core` giữ như v2; thêm `core_cap` và `app_group`.

## Còn chờ người (CHANGES_v3 mục 9)

- Quy tắc từ đánh thức.
- Có tăng hạn ngạch CS04 không (G1–G4 hiện đúng 35%).
- Người Bắc, Trung, Nam điền `BANG_tu_ngoai_lai.csv`. Ưu tiên Zalo, YouTube, Messenger, Viber, Telegram, VETC, ePass, Vietmap, Waze, Google Maps: nhiều câu nhất và chưa có cách đọc.
- Nghe lại K-pop "ca pop" và AQI "a quy i".
- Phạm vi G9.
- Kiểm Zalo, Viber trên Android Auto.
- Tập kiểm thu thật trong xe.
- Duyệt 218 khung K1 app.
