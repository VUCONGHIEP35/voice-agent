# Phụ lục góp ý: app trên màn hình ô tô và từ ngoại lai

Khảo sát 14–15/10/2026. Mức bằng chứng: **[nguồn]** = có trong tài liệu đã đọc; **[đo]** = đo trên `data/m1m2_10k`; **[K1]** = suy luận của người khảo sát, chưa kiểm chứng, mọi ví dụ cần người bản ngữ duyệt.

## 1. Kết luận

1. Bộ đã phủ khá các nhóm app lớn (gọi điện, nhạc, dẫn đường, nhắn tin, sạc) nhưng **gần như không có lệnh mở app theo tên**: chỉ 4 câu dạng "mở YouTube / Spotify" trong 10.000 câu. [đo]
2. **Nhiều tên có 0 câu trong bộ.** Có trong nguồn khảo sát: VinFast, ViVi, Kiki, Vietmap, Waze, VETC, ePass. Không có trong nguồn nào về lệnh trên xe nhưng kiểm thử cho đủ: Grab, Netflix, TikTok, V-Green. Các tên còn lại có rất ít câu (Facebook 1, Apple Music 1, Google Maps 4, Spotify 5, Telegram 6, Viber 8, YouTube 11). [đo]
3. Từ ngoại lai xử lý không nhất quán: viết tắt (USB, FM, VOV, MHz, ABS, ATM) đã đổi sang chữ đọc; tên thương hiệu Latin (YouTube, Zalo, Spotify, Bluetooth, podcast, playlist, Apple CarPlay…) giữ nguyên nên cách đọc do TTS tự quyết. [đo]
4. **Luật chống trùng theo lõi ở GOP_Y_v1 mục 1 mâu thuẫn với lệnh mở app**: lõi che tên riêng, nên "mở YouTube", "mở Spotify", "mở Zalo" cùng một lõi và bị giới hạn 3 câu. Xem S2.

## 2. Mẫu còn thiếu

Số câu hiện có đếm bằng từ khóa trên `text_raw`, chỉ mang tính ước lượng. Khung ví dụ là tự biên [K1]. Số câu đề xuất là đề xuất, chưa có căn cứ thực nghiệm.

| Mã | Mẫu thiếu | Hiện có [đo] | Bằng chứng cần có | Khung ví dụ [K1] | Đề xuất |
|---|---|---|---|---|---|
| G1 | Mở app theo tên | 4 câu | [nguồn] Kiki: "mở YouTube"; Vietmap có YouTube, Spotify | "mở {app}", "bật {app} lên", "vào {app} đi", "chạy {app}", "mở ứng dụng {app}" | 300 |
| G2 | Điều khiển trong video/nhạc | "điều khiển phát" 93, chưa có tua/quảng cáo | [K1] | "tua đi {n} giây", "tua lại {n} giây", "bỏ qua quảng cáo", "phát lại từ đầu", "toàn màn hình", "bật phụ đề" | 200 |
| G3 | Tìm nội dung trong app | YouTube 11 câu | [nguồn] Kiki mở YouTube | "mở YouTube tìm {chủ đề}", "tìm trên YouTube {nội dung}", "xem kênh {tên kênh}" | 150 |
| G4 | Chuyển màn hình/app, chia đôi màn hình | không có intent riêng | [nguồn] Vietmap chia đôi màn hình | "quay lại bản đồ", "về màn hình chính", "chuyển sang {app}", "chia đôi màn hình bản đồ và nhạc" | 100 |
| G5 | Nói rõ ngữ cảnh xe đang đỗ | chưa kiểm | [K1] | "xe đang đỗ, mở video đi", "tôi ngồi ghế sau, bật phim" | 50 |
| G6 | Chọn app bản đồ | 111 câu có tên bản đồ, chưa có khung chọn app | [nguồn] Vietmap + Google Maps dùng song song; Kiki mở Google Maps | "dẫn đường bằng {map_app}", "mở {map_app} dẫn tới {địa điểm}", "đổi sang {map_app}" | 100 |
| G7 | Đọc/trả lời tin nhắn app bên thứ ba | "nhắn, gọi Zalo" 120; "đọc tin nhắn" 97; "đọc thông báo" 43 | [nguồn] Android Auto đọc WhatsApp, Messenger, Telegram, Google Messages; Zalo và Viber không được nhắc | "có tin {msg_app} mới không", "đọc tin {msg_app} của {ct}", "trả lời {msg_app} là {msg}" | 150 |
| G8 | Thu phí không dừng | 36 câu | [nguồn] VETC, ePass là hai thẻ | "số dư {etc} còn bao nhiêu", "nạp {tiền} vào {etc}", "còn bao xa tới trạm thu phí" | 100 |
| G9 | Gọi xe công nghệ | 12 câu | **Không có nguồn nào cho thấy lệnh này dùng trên xe**; hỏi lại phạm vi trước khi làm | "gọi xe {ride_app} đến {địa điểm}" | 0–50, chờ quyết định |
| G10 | Từ đánh thức theo nền tảng | 0 câu "Hey …" | [nguồn] "Hey VinFast"; "Hey Google". Kiki và Siri **chưa kiểm** | "Hey VinFast, …", "Hey Google, …" | không làm khi chưa có quyết định (CLAUDE.md đang cấm tên thương hiệu làm từ đánh thức) |

Tổng G1–G8 khoảng 1.150 câu, **chưa tính hạn ngạch theo case**: G1–G4 một mình đã chiếm 750 trong hạn ngạch 1.200 của CS04. Sau GOP_Y_v1 không còn câu gần trùng để bớt (đã về 0), nên câu mới phải nằm **trong** hạn ngạch sẵn có và lấy chỗ của khung cũ. Số câu cuối cùng dùng theo `CHANGES_v3.md` mục 6 (đã tính hạn ngạch), không dùng cột "Đề xuất" ở trên.

Phạm vi G9 và thanh toán ví điện tử (MoMo, ZaloPay: 0 câu): nguồn khảo sát không cho thấy dùng bằng giọng nói trên xe, nên **không thêm khi chưa có quyết định**.

## 3. Cách giải quyết

**S1. Thêm module khung cho G1–G8.** Viết file mới (ví dụ `gen10k/frames_app10k.py`) theo kiểu `F(...)` hiện có trong `frames10k.py`. Mở rộng `pools10k.APPS` (hiện 11 mục) và thêm khe: `map_app` (Google Maps, Vietmap, Waze), `etc_app` (VETC, ePass), `tiền`, `kênh`. Mọi khung mới đặt `evidence = "constructed"`, `frame_source = "K1 app"`.

**S2. Sửa luật chống trùng cho lệnh ngắn.** Với lệnh ngắn, tên app chính là thứ ASR cần học. Đề xuất: thêm hàm lõi riêng (`carrier_cap`) **không che** tên app và từ ngoại trong `APPS`/bảng từ ngoại, dùng cho trần 3 câu/lõi. Giữ nguyên `carrier` hiện có để đo độ đa dạng khung, nếu không số v2 và v3 không so sánh được.

**S3. Biến thể cách đọc thành một khe riêng.** Thêm cột `pron_variant` (ví dụ `L01-a`). `text_raw` giữ nguyên ("YouTube"); `text_spoken` thay theo biến thể trong `BANG_tu_ngoai_lai.csv`. Mỗi thực thể cần đủ số câu để học: đề xuất khoảng 100–300 câu mỗi tên phổ biến, chưa có căn cứ thực nghiệm. Ghi `pron_variant` để báo WER theo biến thể sau này.

**S4. Lặp văn bản nhiều giọng, không bịa thêm văn bản.** Câu ngắn như "mở YouTube" chỉ có vài lõi khác nhau là bình thường. Đa dạng cần tăng ở phía âm thanh (nhiều giọng TTS, nhiều mức nhiễu, tốc độ khác nhau). Lưu ý: nếu một câu lặp quá nhiều trong tập huấn luyện, mô hình có thể học thuộc, nên trộn với dữ liệu thật.

**S5. Thêm trường `platform`.** Giá trị đề xuất: `oem_vinfast`, `android_head_unit`, `phone_projection`, `any`. Khung G7 gắn theo nền tảng vì nguồn cho thấy app nhắn tin được hỗ trợ khác nhau. Về từ đánh thức theo nền tảng: nguồn có "Hey VinFast" và "Hey Google"; Kiki và Siri chưa kiểm. **Lưu ý**: `CLAUDE.md` hiện cấm dùng tên thương hiệu trợ lý làm từ đánh thức, nên mặc định **không** thêm; chỉ đổi khi người dùng quyết (xem `CHANGES_v3.md` mục 9).

**S6. Duyệt cách đọc bằng người bản ngữ.** Gửi `BANG_tu_ngoai_lai.csv`: mỗi người ghi cách mình thật sự nói vào ba cột `nguoi_Bac_noi`, `nguoi_Trung_noi`, `nguoi_Nam_noi`. Cách đọc nào ít người dùng thì bỏ khỏi bộ sinh. Hai dòng nghi ngờ lỗi cần nghe trước: **K-pop → "ca pop"** (L46) và **AQI → "a quy i"** (L36).

**S7. Lấy dữ liệu thật.** Không có nguồn công khai nào liệt kê đầy đủ câu lệnh. Cách đáng tin nhất là xin 50–100 câu lệnh người dùng Kiki hoặc xe VinFast thật sự nói, hoặc nhờ vài lái xe đọc theo kịch bản rồi so cách họ nói với `text_raw`. Cũng cần một tập kiểm thu trong xe, không sinh bằng TTS.

## 4. Việc cho Claude Code (bổ sung GOP_Y_v1)

1. Đọc `BANG_tu_ngoai_lai.csv`. Với các dòng đã có người duyệt, sinh `text_spoken` theo biến thể và ghi `pron_variant`. Dòng "chưa duyệt" giữ cách đọc hiện tại và gắn cờ `cần duyệt`.
2. Thêm G1–G8 theo S1; mỗi khung `cần duyệt`.
3. Sửa luật lõi theo S2 trước khi chạy bước chống trùng ở GOP_Y_v1 mục 1.
4. Thêm `platform` (S5). Không thêm tên thương hiệu trợ lý làm từ đánh thức khi chưa có quyết định (xem `CHANGES_v3.md` mục 9).
5. Số câu mỗi nhóm G1–G8 theo `CHANGES_v3.md` mục 6 (đã tính hạn ngạch); báo bảng trước/sau theo nhóm.

## 5. Giới hạn của khảo sát

- Không đọc được bài Zing News về trợ lý AI trên ô tô (cần cấp quyền URL) và bài VNReview hướng dẫn Kiki (robots chặn).
- Các bài báo chỉ nêu nhóm chức năng và vài ví dụ rời; không có danh sách câu lệnh chính thức của VinFast hay Kiki.
- Chưa kiểm Zalo/Viber có hỗ trợ trong Android Auto hay không.
- Mọi cách đọc trong CSV là suy luận; chưa nghe lại bằng TTS và chưa có người bản ngữ duyệt.

## Nguồn
- [Trợ lý ảo VinFast đã thay đổi thói quen lái xe](https://doanhnhan.baophapluat.vn/tro-ly-ao-vinfast-da-thay-doi-thoi-quen-lai-xe-cua-nguoi-viet-the-nao-64239.html): "Hey VinFast, tăng điều hòa lên 2 độ C", "Hey VinFast, gọi điện tới số 098xxxxxxx"
- [Trợ lý ảo ViVi](https://diendandoanhnghiep.vn/tro-ly-ao-vivi-vinfast-dau-an-moi-cua-ky-nguyen-cong-nghe-giong-noi-214119.html): "Hey VinFast", "Kể chuyện cười đi ViVi"
- [VF Connect](https://baohatinh.vn/tv/trai-nghiem-goi-vf-connect-tren-xe-dien-vinfast-tro-thu-thong-minh-cho-moi-hanh-trinh-39711.html): tìm trạm sạc, Vietmap Live
- [Kiki Auto 1 triệu lượt cài](https://baodautu.vn/1-trieu-o-to-tai-viet-nam-dung-tro-ly-ao-kiki-auto-d232759.html)
- [Kiki Auto (Zalo)](https://zalo.me/en/post/kiki-auto): "Chỉ đường tới cây xăng gần nhất"
- [Hướng dẫn cài Kiki](https://fptshop.com.vn/tin-tuc/thu-thuat/huong-dan-cai-dat-tro-ly-ao-kiki-giong-noi-tieng-viet-160618): "chỉ đường", "mở Youtube", "mở nhạc", "đọc tin tức mới nhất"
- [Màn hình Vietmap](https://fptshop.com.vn/tin-tuc/danh-gia/man-hinh-vietmap-199724): YouTube, Spotify, Google Maps, chia đôi màn hình
- [Android Auto: lệnh giọng nói](https://support.google.com/androidauto/answer/6348083)
- [Messaging apps on Android Auto](https://www.slashgear.com/1377182/best-messaging-apps-android-auto/)
