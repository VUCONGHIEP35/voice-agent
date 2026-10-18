# Phụ lục góp ý: từ ngữ miền Trung, nơi sống và cách nói với trợ lý trong xe

Khảo sát 14/10/2026 trên claude.ai. Ghi rõ mức bằng chứng: **[nguồn]** = có trong tài liệu đã đọc; **[suy luận]** = nhận định của người khảo sát, chưa kiểm chứng; mọi câu ví dụ đều cần người bản ngữ duyệt.

## 1. Kết luận chính
1. **Không tìm thấy nguồn nào về từ vựng ô tô riêng của miền Trung.** Khác biệt của miền Trung nằm ở từ chức năng (đâu, sao, gì, này, kia, bây giờ, không, thấy, làm), tiểu từ cuối câu, xưng hô và ngữ âm, không nằm ở tên bộ phận xe. [nguồn: các danh sách từ Huế, Nghệ, Quảng bên dưới đều không có từ về xe]
2. **Nơi sống đổi cách nói.** Người miền Trung sống ở Hà Nội hoặc TP.HCM được mô tả là học giọng, từ người bản địa khi giao tiếp với người ngoài; người Nghệ giữ tiếng quê trong cộng đồng đồng hương nhưng chuyển sang từ toàn dân với người vùng khác. [nguồn: Brands Vietnam; Báo Hà Tĩnh — đều là bài nêu ý kiến, không có số liệu] Có nghiên cứu học thuật về tiếp xúc phương ngữ theo lý thuyết thích nghi giao tiếp (Trịnh Cẩm Lan, CALA 2020), nhưng chỉ đọc được tóm tắt, không có số liệu.
3. **Nói với máy khác nói với người.** Nghiên cứu tiếng Anh (Cohn và cộng sự 2021, Alexa): người dùng nói chậm hơn với bot trong phòng thí nghiệm (4,17 → 2,93 âm tiết/giây), ở nhà gần như không đổi (3,13 → 3,07), và bắt chước tốc độ của bot. Không tìm thấy nghiên cứu tiếng Việt về cách nói với trợ lý ảo.
4. [suy luận] Khi ra lệnh cho trợ lý, người miền Trung có xu hướng giữ **giọng** (thanh điệu, ngữ âm) nhưng dùng **từ toàn dân hoặc từ của nơi đang sống**, vì nghĩ máy hiểu từ chuẩn tốt hơn. Từ vùng mạnh (mô, răng, nỏ, chộ) xuất hiện nhiều hơn ở câu hỏi tự nhiên, câu cụt, lúc vội hoặc bực, và ở người lớn tuổi sống tại quê. Chưa có dữ liệu kiểm chứng; cần thu một tập nhỏ thật để đo.

## 2. Từ miền Trung theo tiểu vùng [nguồn]

| Nghĩa phổ thông | Huế | Nghệ Tĩnh | Quảng Nam – Đà Nẵng | Nguồn |
|---|---|---|---|---|
| đâu / nào | mô | mô; mồ (nào) | mô | Đặng Diễm Đông 2024; VOH; Vinpearl |
| sao | răng | răng | răng | Vinpearl; Báo Hà Tĩnh |
| thế / vậy | rứa, ri | rứa | rứa | Đặng Diễm Đông 2024; VOH |
| gì | chi | chi | chi | Đặng Diễm Đông 2024 |
| này | ni | ni | ni | như trên |
| kia | tê | tê | tê | như trên |
| đó / ấy | nớ | nớ | nớ | như trên |
| bây giờ | (chừ: K1) | dừ | (chừ: K1) | VOH |
| không | — | nỏ | — | VOH |
| thấy | — | chộ | — | VOH |
| làm | — | mần | — | VOH; Di Động Việt |
| đường | — | đàng (miền Trung chung) | — | Di Động Việt |
| quán, tiệm | — | ốt | — | VOH |
| xem | coai | — | — | Đặng Diễm Đông 2024 |
| bữa đó / dạo này | — | bựa nớ, dạo ni | — | VOH |
| tôi | tui | tau (thân mật) | — | Đặng Diễm Đông 2024; VOH |
| cô / bà | o / mệ, mụ | — | — | Đặng Diễm Đông 2024 |

Tiểu từ cuối câu Huế [nguồn: Đặng Diễm Đông 2024]: hì/hi/hí (nhỉ, nhé), nở (nhé), nờ (nào, à), chơ (chứ), tề (kìa), đỏ (đó), hớ (hả), mờ (mà), bơ (rồi). Bài không có "hè".
Quảng Nam đổi vần nhiều (côm = cơm, bèn = bằng) [nguồn: Vinpearl] — phần này nằm ở giọng, TTS phải tạo, không viết được vào văn bản.

**Hệ quả cho bộ sinh:** bộ hiện dùng "nghe", "giùm", "tui" làm dấu hiệu chính của câu Trung; "nghe" và "giùm" không có trong nguồn Huế đã đọc. Tiểu từ có nguồn là hí, nở, nờ, chơ, tề. Nên tách `sub_region` (Huế / Nghệ Tĩnh / Quảng Nam – Đà Nẵng / Nam Trung Bộ) và gán từ theo bảng trên thay vì trộn chung.

## 3. Hồ sơ người nói: quê gốc × nơi sống [suy luận, cần dữ liệu thật]

| Hồ sơ | Giọng (TTS) | Từ về xe, đường | Từ chức năng, tiểu từ | Ví dụ (cần duyệt) |
|---|---|---|---|---|
| Trung, sống ở quê | Trung (tiểu vùng) | trộn, theo tiểu vùng (chưa có nguồn) | mô, răng, chi, rứa, ni; hí, nờ (Huế); nỏ, dừ (Nghệ) | "Trạm sạc gần nhất ở mô?" · "Răng bản đồ chỉ đàng ni?" |
| Trung, sống ở Hà Nội | Trung | Bắc: điều hòa, rẽ, đỗ xe, tắc đường, ngõ | chủ yếu toàn dân; giữ ít tiểu từ quê | "Rẽ trái vào ngõ 28 nhé." (giọng Trung) |
| Trung, sống ở TP.HCM | Trung | Nam: máy lạnh, quẹo, đậu xe, kẹt xe, hẻm | toàn dân; có thể thêm nha, tui | "Quẹo phải vô hẻm 12 nha." (giọng Trung) |
| Bắc | Bắc | điều hòa, kính, rẽ, đỗ, tắc đường, ngõ | nhé, nhỉ, ạ | "Bật điều hòa 24 độ nhé." |
| Nam | Nam | máy lạnh, kiếng, quẹo, đậu, kẹt xe, hẻm | nha, nghen, tui, dạ | "Mở máy lạnh 24 độ nha." |

Đề xuất tỷ lệ (thay thế được): trong phần giọng Trung, khoảng 40% "sống ở quê", 30% "sống ở Hà Nội", 30% "sống ở TP.HCM". Thêm trường `residence` (Quê / Hà Nội / TP.HCM) và `vocab_source` (Trung / Bắc / Nam) vào mỗi dòng; giọng TTS vẫn theo `speaker_region`.

## 4. Từ vựng xe cần thêm cho cả ba miền
Có trong `sources/src_lang.json` nhưng bộ sinh chưa dùng: xi nhan / đèn báo rẽ; kiếng chiếu hậu (Nam); thắng tay, đạp thắng (Nam); thay nhớt (Nam); bánh sơ-cua; ca-pô; táp lô; số D/R/P, cần số; đạp ga, nhả ga; nổ máy, tắt máy; đầy bình, hết xăng; bình điện, yếu bình; bật pha, bật cốt; đèn khẩn cấp.
Chưa có nguồn [K1, cần duyệt]: bấm còi (Bắc) / bóp kèn (Nam); lùi / de (Nam); lốp / vỏ xe (Nam); quay đầu / quay xe; bơm xăng; cầu vượt; lề đường.
Miền Trung: chưa có nguồn cho các cặp trên; để người bản ngữ từng tiểu vùng điền (bảng mục 5).

## 5. Bảng cho người bản ngữ điền
Mỗi người điền cách mình thật sự nói với trợ lý trong xe (không phải cách nói với người).

| Khái niệm | Huế | Nghệ Tĩnh | Quảng Nam – Đà Nẵng | Nam Trung Bộ (Quy Nhơn, Nha Trang) | Ghi chú |
|---|---|---|---|---|---|
| điều hòa / máy lạnh | | | | | |
| kính / kiếng (cửa xe) | | | | | |
| rẽ / quẹo | | | | | |
| đỗ / đậu xe | | | | | |
| tắc / kẹt xe | | | | | |
| ngõ / hẻm / kiệt | | | | | |
| phanh / thắng | | | | | |
| còi / kèn | | | | | |
| lùi xe | | | | | |
| lốp / vỏ | | | | | |
| xi nhan | | | | | |
| đổ / bơm xăng | | | | | |
| "ở đâu?" khi hỏi trợ lý | | | | | |
| tiểu từ cuối lệnh (nhé/nha/hí...) | | | | | |
| có dùng từ quê khi nói với máy không? | | | | | |

## 6. Việc cho Claude Code (bổ sung GOP_Y_v1.md)
1. Thêm `sub_region`, `residence`, `vocab_source`; câu "Trung sống ở Hà Nội/TP.HCM" dùng bộ viết lại Bắc/Nam cho từ về xe, giữ `speaker_region = Trung`.
2. Thay tiểu từ Trung: bỏ ưu tiên "nghe"/"giùm"; dùng hí, nở, nờ, chơ, tề (Huế), dừ/nỏ/mần chỉ cho Nghệ Tĩnh; mọi câu vẫn `cần duyệt`.
3. Thêm khung cho các chức năng xe chưa có (mục 4) ở cả ba miền.
4. Không tự điền từ xe cho miền Trung; để trống chờ bảng mục 5.

## Nguồn
- Đặng Diễm Đông (2024), *Phương ngữ Huế trong một số tình huống giao tiếp mua bán hiện nay*, Tạp chí Khoa học ĐH Huế 133(6C): https://jos.hueuni.edu.vn/index.php/hujos-ssh/article/view/7163
- VOH, *Những câu nói Nghệ An khó hiểu*: https://voh.com.vn/song-dep/nhung-cau-noi-nghe-an-kho-hieu-564712.html
- Báo Hà Tĩnh, *"Đặc sản" của vùng đất Nghệ - Tĩnh*: https://baohatinh.vn/dac-san-cua-vung-dat-nghe-tinh-post257801.html
- Di Động Việt, *Khu mấn là gì? Trốc tru là gì?*: https://didongviet.vn/dchannel/khu-man-la-gi-troc-tru-la-gi/
- Vinpearl, *Điều thú vị về tiếng Quảng Nam*: https://vinpearl.com/vi/dieu-thu-vi-ve-tieng-quang-nam
- Brands Vietnam, *Giọng vùng miền trong giao tiếp*: https://www.brandsvietnam.com/congdong/topic/327262-giong-vung-mien-trong-giao-tiep-rao-can-hay-dau-an
- Trịnh Cẩm Lan, *Dialect Contact in Vietnam from Accommodation Theory Perspective* (CALA 2020, chỉ đọc tóm tắt): https://glocal.soas.ac.uk/cala2020-58/
- Andrea Hoa Pham, *Vietnamese dialects* (Quảng Nam, Hà Tĩnh, Thanh Hóa): https://www.degruyterbrill.com/document/doi/10.1075/slcs.211.03pha/html
- Cohn và cộng sự (2021), *Speech Rate Adjustments in Conversations With an Amazon Alexa Socialbot*, Frontiers in Communication: https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2021.671429/pdf
- VnExpress, *5 trợ lý ảo nói tiếng Việt*: https://vnexpress.net/5-tro-ly-ao-noi-tieng-viet-4412071.html
