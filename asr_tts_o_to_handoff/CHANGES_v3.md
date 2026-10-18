# CHANGES_v3: bổ sung app trên màn hình xe và từ ngoại lai

Đặt file này ở gốc dự án, cạnh `CLAUDE.md`. Người dùng không sửa code; Claude Code đọc file này rồi tự sửa `gen10k/`.

## 1. Bối cảnh và phạm vi

- GOP_Y_v1 đã chạy xong (xem `CLAUDE.md`, mục "Trạng thái 2026-10-14"). Đầu ra ở `data/m1m2_10k_v2/` (gen10k-2.0). **Không làm lại các mục của GOP_Y_v1.**
- Các file review nằm ở `../review/` (cùng chỗ `GOP_Y_v1.md`, `BAO_CAO_vong1.md`); với máy hiện tại là `D:\New folder (2)\asr_tts_o_to_handoff\review\`. Thư mục dự án là `D:\New folder (2)\asr_tts_o_to_handoff\asr_tts_o_to_handoff\`. Đầu vào đợt này, thêm vào đúng chỗ đó:
  - `../review/PHU_LUC_app_tren_man_hinh_va_tu_ngoai.md`
  - `../review/BANG_tu_ngoai_lai.csv`
- Đầu ra: `data/m1m2_10k_v3/`. **Không ghi đè v2.**
- Tổng số câu giữ 10.000 và **hạn ngạch theo case giữ nguyên**. Câu mới nằm trong hạn ngạch sẵn có, nên bộ sinh sẽ lấy ít hơn từ các khung cũ.

## 2. Tóm tắt thay đổi

| # | Thay đổi | Mục đích |
|---|---|---|
| C1 | Thêm hàm lõi riêng cho việc giới hạn trùng, không che tên app và từ ngoại | Lệnh ngắn "mở YouTube / Spotify / Zalo" không bị gom thành một lõi và cắt còn 3 câu |
| C2 | Thêm khung G1–G8 (mở app, điều khiển video, tìm nội dung, chuyển app, ngữ cảnh đỗ xe, chọn bản đồ, app nhắn tin thứ ba, thu phí) | Nhóm app đang thiếu hoặc rất mỏng |
| C3 | Thêm khe và danh sách tên mới: `map_app`, `etc_app`, tên kênh; mở rộng `APPS` | Cần cho C2 |
| C4 | Cách đọc từ ngoại thành biến thể có đánh dấu (`pron_variant`) | Một nhãn viết, nhiều cách đọc |
| C5 | Thêm trường `platform` | Phân biệt xe hãng, màn hình Android, kết nối điện thoại để báo WER theo nền tảng |
| C6 | Mở rộng `validate10k.py` | Kiểm các trường mới và số câu tối thiểu |

## 3. Chỉ định chỗ sửa

Số dòng đã đối chiếu với `gen10k-2.0` (bộ sinh sau GOP_Y_v1) ngày 15/10/2026. Nếu file đã đổi thì tìm theo tên hàm. Trường đã có từ v2 (`sub_region`, `residence`, `vocab_source`, `core`) giữ nguyên.

**Vì sao C1 cần làm trước:** `diversity10k.carrier` gắn nhãn `<TÊN>` cho mọi từ viết hoa không đứng đầu câu. Do đó "mở YouTube", "mở Spotify", "mở Zalo" đều thành lõi `mở <tên>` và chỉ còn 3 câu. Báo cáo vòng 1 đã ghi hiện tượng này: câu dựng từ mẫu `seen` giảm từ 839 xuống 682 vì trần 3 câu/lõi.

| # | Tệp | Chỗ sửa | Việc làm |
|---|---|---|---|
| C1 | `diversity10k.py` | Cạnh hàm `carrier` (dòng 89) | **Không đổi `carrier`** (vẫn dùng để đo, nếu đổi thì số v2 và v3 không so sánh được). Thêm hàm `carrier_cap(raw, masks, keep)`: trước khi gọi `carrier`, thay mỗi tên trong danh sách `keep` (app, từ ngoại trong `APPS`, bản đồ, thu phí) bằng một mã chữ thường không có khoảng trắng, để không bị gắn `<TÊN>` |
| C1 | `build10k.py` | Hàm `core_of` (dòng 354–355), chỗ dùng ở dòng 429 và `Shared.core_count` | Đếm lõi để áp trần 3 câu bằng `carrier_cap`. Vòng lọc gần trùng TF-IDF (hàm `tfidf_fit`, dòng 477; gọi quanh dòng 509) kiểm lại: các lệnh "mở X" ngắn có thể bị gom nhầm |
| C1 | `validate10k.py` | Mục 9b (dòng 176–186) đang gọi `DV.carrier` | Phần kiểm "một lõi vượt trần" đổi sang `carrier_cap`; phần tính tỷ lệ lõi/câu giữ `carrier`. Nếu bỏ sót chỗ này, `validate10k.py` sẽ báo sai "lõi vượt trần" |
| C2 | `gen10k/frames_app10k.py` (file mới) | Theo kiểu `frames_llm10k.py`; nối vào `load_frames()` trong `frames10k.py` (dòng 556–560, nơi đang `import frames_llm10k`) và tập `NEW_FIDS` (dòng 553) | Khung G1–G4, G6 vào **CS04**; G7 vào **CS05**; G5 vào CS04 hoặc case chứa lệnh giải trí; G8 và phần G6 liên quan dẫn đường vào case chứa intent dẫn đường/thu phí gần nhất. Mỗi khung `evidence="constructed"`, `frame_source="K1 app"`, mọi câu `cần duyệt` |
| C2 | `frames10k.py` | Từ điển trọng số `w` (quanh dòng 98–99) | Đặt trọng số để số câu thực tế gần mức ở mục 6 |
| C3 | `pools10k.py` | Dòng `APPS` (dòng 261) | Thêm Vietmap, Waze, VETC, ePass và danh sách riêng cho bản đồ, thu phí. Ghi nguồn bằng `src(...)` |
| C3 | `slots10k.py` | Bảng khe (khoảng dòng 719, nơi có `msg_app`, `music_app`) | Thêm hàm sinh khe `map_app`, `etc_app`, `kenh`, đăng ký vào bảng |
| C4 | `slots10k.py` | `g_link_src` (dòng 598), `g_app_from` (610), `g_app` (620) | Gom cả ba về một hàm tra bảng từ ngoại. Xem mục 4 |
| C4 | `build10k.py` | Tập `ENGLISH` (dòng 45) | Thêm các tên mới để `language_mix` nhận đúng từ mượn |
| C5 | `build10k.py` | Nơi ghép từng dòng JSONL (gần dòng 429) | Thêm `platform` (`oem_vinfast` / `android_head_unit` / `phone_projection` / `any`; mặc định `any`) và `pron_variant` |
| C6 | `validate10k.py` | `REQUIRED` (dòng 12) và hàm `main` (dòng 46) | Thêm các trường mới, các kiểm tra ở mục 6 |

## 4. Cách dùng bảng từ ngoại `../review/BANG_tu_ngoai_lai.csv`

- Mỗi dòng: `dang_viet(text_raw)` là nhãn; `cach_doc_de_xuat_1..3` là các cách đọc.
- Người duyệt ghi vào cột `nguoi_Bac_noi`, `nguoi_Trung_noi`, `nguoi_Nam_noi` danh sách số cách đọc mình dùng, ví dụ `1,2`, hoặc `0` nếu không dùng cách nào.
- Quy tắc cho Claude Code:
  1. Với câu có `speaker_region = X`, chỉ dùng các cách đọc ghi ở cột vùng X.
  2. Nếu cột vùng X **rỗng** (chưa duyệt): giữ cách đọc hiện tại trong `text_spoken` và gắn cờ `cách đọc chưa xác minh: <tên>`. **Không tự chọn.**
  3. Nếu có nhiều số: chọn ngẫu nhiên theo `rng` cố định, ghi `pron_variant` (ví dụ `L01-2`).
  4. `text_raw` luôn giữ nguyên dạng viết.
- **Hiện tại cột duyệt đều trống**, nên lần chạy v3 đầu tiên chỉ thêm trường `pron_variant` rỗng; hiệu quả thật của C4 chỉ có sau khi người bản ngữ điền bảng. C1, C2, C3, C5 làm ngay được.

## 5. Thứ tự thực hiện

1. Chạy `diversity10k.py` trên `m1m2_10k_v2` để lấy số liệu gốc (v2: 7.228 lõi, tỷ lệ 0,723, mọi case ≥ 0,6, 0 câu cos ≥ 0,9).
2. C1 (hàm lõi mới) **trước** các bước còn lại.
3. C3, rồi C2.
4. C4, C5.
5. C6, rồi sinh `data/m1m2_10k_v3/`.
6. Chạy `test_vnnum.py`, `validate10k.py`, `diversity10k.py`.
7. Cập nhật `CLAUDE.md` theo mục 8.

## 6. Tiêu chí nghiệm thu (đề xuất, sửa được)

- `validate10k.py`: 0 lỗi; vẫn không còn chữ số trong `text_spoken`.
- Tổng 10.000; vẫn chia đều 3 vùng; hạn ngạch theo case giữ nguyên.
- Số câu theo nhóm (mặc định, **đã tính hạn ngạch**): G1 150, G2 100, G3 100, G4 70, G5 40, G6 80, G7 150, G8 80. G1–G4 cộng khoảng 420 câu, tức khoảng 35% hạn ngạch CS04 (1.200); đừng vượt mức này nếu chưa có quyết định tăng hạn ngạch CS04 (mục 9). Nếu không đủ khung khác nhau, **giữ ít hơn và báo số thật**, không tự nới.
- Tỷ lệ lõi/câu (theo `carrier` cũ, không phải `carrier_cap`) mỗi case: **không thấp hơn v2** (hiện ≥ 0,6); câu gần trùng cos ≥ 0,9: vẫn 0.
- Mọi câu có tên trong bảng từ ngoại mà chưa duyệt đều có cờ `cách đọc chưa xác minh`.
- Mọi câu mới đều `cần duyệt`.

## 7. Không được làm

- **Không thêm tên thương hiệu trợ lý làm từ đánh thức** ("Hey VinFast", "Hey Google"): `CLAUDE.md` đang cấm (mục Giới hạn đã biết), việc đổi quy tắc chờ quyết định ở mục 9. Giữ khe `{wake}` hiện có.
- Không tự điền cách đọc cho dòng chưa duyệt trong bảng từ ngoại.
- Không thêm lệnh gọi xe công nghệ (G9) hay ví điện tử: chưa có quyết định phạm vi.
- Không tự sinh từ vựng miền Trung bằng suy luận.
- Không sửa tay file JSONL; chỉ sửa bộ sinh rồi chạy lại.
- Không đổi hàm `carrier` hiện có.

## 8. Cập nhật `CLAUDE.md`

Không viết lại `CLAUDE.md`. Sao lưu thành `CLAUDE_v1_truoc_v3.md` rồi chỉ làm bốn việc:

1. Đổi tiêu đề mục "Việc cần làm tiếp (yêu cầu mới nhất của người dùng)" thành "Yêu cầu gốc (đã hoàn thành, xem các dòng Trạng thái)".
2. Thêm khối dưới đây ngay sau khối "Trạng thái (2026-10-14), góp ý vòng 1".
3. Ở mục "Giới hạn đã biết", thêm vào cuối dòng "Không đưa tên thương hiệu trợ lý…" ghi chú: "(đang chờ quyết định về Hey VinFast / Hey Google, xem CHANGES_v3.md mục 9)".
4. Ở mục "Có sẵn trong thư mục này", thêm một dòng chỉ `../review/` và `CHANGES_v3.md`.

```markdown
**Trạng thái (2026-10-15), vòng 2 (v3):** chuẩn bị bổ sung app trên màn hình xe và từ ngoại lai, chưa chạy. Đọc `CHANGES_v3.md` trước khi sửa bộ sinh; đầu vào ở `../review/PHU_LUC_app_tren_man_hinh_va_tu_ngoai.md` và `../review/BANG_tu_ngoai_lai.csv`. Đầu ra dự kiến `data/m1m2_10k_v3/`, không ghi đè v2.
- Luật lõi: trần 3 câu/lõi dùng `carrier_cap` (giữ tên app và từ ngoại); `carrier` cũ giữ nguyên để đo, nếu không số v2 và v3 không so sánh được.
- `text_raw` là nhãn ASR (dạng viết); `text_spoken` là đầu vào TTS (dạng đọc). Cách đọc từ ngoại lấy từ `BANG_tu_ngoai_lai.csv`, chỉ dùng cách người bản ngữ đã duyệt theo vùng; chưa duyệt thì giữ nguyên và gắn cờ.
- Trường mới dự kiến: `platform`, `pron_variant` (cùng các trường đã có từ v2).
- Chưa có quyết định: gọi xe công nghệ và ví điện tử; Hey VinFast / Hey Google làm từ đánh thức; hạn ngạch CS04 cho G1–G4.
- Còn mở: người bản ngữ duyệt bảng từ ngoại; nghe lại hai cách đọc nghi ngờ (K-pop, AQI); tập kiểm thu thật trong xe.
```

## 9. Việc cần người, không giao Claude Code

1. **Quyết quy tắc từ đánh thức**: giữ cấm tên thương hiệu (mặc định), hay cho phép "Hey VinFast" và "Hey Google" theo `platform`. Nguồn chỉ cho thấy hai từ này là từ đánh thức thật; không có nguồn cho Kiki hay Siri.
2. **Quyết hạn ngạch CS04**: G1–G4 mặc định chiếm 35% hạn ngạch CS04. Nếu muốn nhiều hơn, tăng CS04 ở sheet `Chi_tieu` và giảm case khác.
3. Người Bắc, Trung, Nam điền `BANG_tu_ngoai_lai.csv`.
4. Nghe lại hai dòng nghi ngờ: K-pop đang đọc "ca pop", AQI đang đọc "a quy i".
5. Quyết phạm vi G9 (gọi xe công nghệ, ví điện tử).
6. Kiểm Zalo, Viber có hỗ trợ trong Android Auto hay không.
7. Thu 50–100 câu lệnh thật và một tập kiểm trong xe.

## 10. Báo cáo cần nộp khi xong

- Bảng v2 → v3: tổng câu, số câu theo G1–G8, lõi/câu theo case, số câu có hàng xóm ≥ 0,9.
- Danh sách `sample_id` bị thay hoặc bị loại, và số câu mất ở từng case.
- Số câu có cờ `cách đọc chưa xác minh`.
- Mục nào của file này không làm được, kèm lý do.
