# Báo cáo làm theo góp ý vòng 1 (GOP_Y_v1.md + PHU_LUC_tu_vung_mien_Trung.md)

Ngày 14/10/2026. Bộ mới: `asr_tts_o_to_handoff/data/m1m2_10k_v2/` (gen10k-2.0, seed 20261013). Bộ cũ `data/m1m2_10k/` giữ nguyên.
Trước khi sửa đã chạy lại `review/diversity10k.py` trên bản sao bộ v1: các số khớp đúng góp ý (4.651 lõi; 986 câu gần trùng, 925 cùng khung; tỷ lệ lõi từng case; 74/55/52% câu không có từ vùng; đoán vùng 0,60).
Sau mỗi bước đều chạy `test_vnnum.py` (9/9 đạt), `validate10k.py` (0 lỗi ở mọi bước) và `diversity10k.py`.

## Bảng trước/sau

Cột "3b" là phụ lục mục 6.1–6.2 (hồ sơ người nói Trung). Bước 5 chỉ sửa tài liệu và bộ kiểm, không đổi dữ liệu, nên kết quả cuối giống cột 3b.

| Chỉ số | v1 | Bước 1 | Bước 2 | Bước 3 | Bước 3b = cuối |
|---|---|---|---|---|---|
| Tổng câu | 10.000 | 10.000 | 10.000 | 10.000 | 10.000 |
| Số lõi khác nhau | 4.651 | 6.639 | 7.132 | 7.127 | 7.228 |
| Tỷ lệ lõi / câu | 0,465 | 0,664 | 0,713 | 0,713 | 0,723 |
| Câu có hàng xóm cos ≥ 0,9 | 986 | 0 | 0 | 0 | 0 |
| … trong đó cùng khung | 925 | 0 | 0 | 0 | 0 |
| Cặp cùng khung cos ≥ 0,95 | 35 | 0 | 0 | 0 | 0 |
| Câu có hàng xóm cos ≥ 0,8 | 3.095 | 2.420 | 2.018 | 1.950 | 1.976 |
| Câu mở đầu "Làm ơn" | 527 (5,27%) | 523 | 492 | 102 (1,02%) | 101 (1,01%) |
| Đoán vùng từ chữ (acc) | 0,600 | 0,630 | 0,619 | 0,623 | 0,677* |

Tỷ lệ lõi theo case:

| Case | v1 | Bước 1 | Bước 2 | Bước 3 | Cuối |
|---|---|---|---|---|---|
| CS01 | 0,538 | 0,739 | 0,739 | 0,734 | 0,755 |
| CS02 | 0,370 | 0,520 | 0,660 | 0,677 | 0,660 |
| CS03 | 0,286 | 0,374 | 0,569 | 0,572 | 0,606 |
| CS04 | 0,373 | 0,679 | 0,720 | 0,713 | 0,726 |
| CS05 | 0,492 | 0,719 | 0,729 | 0,738 | 0,731 |
| CS06 | 0,392 | 0,514 | 0,662 | 0,654 | 0,664 |
| CS07 | 0,455 | 0,705 | 0,735 | 0,742 | 0,740 |
| CS08 | 0,570 | 0,764 | 0,789 | 0,789 | 0,789 |
| CS09 | 0,733 | 0,810 | 0,820 | 0,817 | 0,777 |
| CS10 | 0,593 | 0,798 | 0,794 | 0,803 | 0,809 |
| CS11 | 0,470 | 0,683 | 0,700 | 0,687 | 0,697 |
| CS12 | 0,498 | 0,717 | 0,720 | 0,710 | 0,727 |

Khung mới theo case (khung được dùng / khung viết; chưa ai duyệt):

| Case | Diễn đạt lại (LLM) | Chức năng xe (phụ lục mục 4) | Câu sinh từ khung mới |
|---|---|---|---|
| CS02 | 43/43 | 0 | 109 |
| CS03 | 169/170 | 38/38 | 570 |
| CS04 | 54/55 | 0 | 285 |
| CS05 | 22/22 | 0 | 246 |
| CS06 | 3/3 | 28/28 | 115 |
| CS07 | 21/21 | 2/3 | 107 |
| CS11 | 14/14 | 0 | 41 |
| Tổng | 326/328 | 68/69 | 1.473 |

\* Từ bước 3b, `lexicon_variant` = `vocab_source` (người Trung sống ở Hà Nội/TP.HCM dùng từ Bắc/Nam), nên nhãn để đoán vùng không còn cùng định nghĩa với v1. Tương tự, "câu không có từ vùng" của nhóm Trung (v1 55%, cuối 63%) ở v2 chỉ tính trên 1.377 câu Trung sống ở quê.

## Đã làm

1. **Chống trùng theo lõi.** Bộ sinh dùng chính `carrier()` của diversity10k. Mỗi lõi tối đa 3 câu toàn tập (`--core-cap`). Áp trần 2 trước, chỉ nâng lên 3 khi case cạn khung; không bao giờ nới quá 3. Thêm vòng lọc gần trùng TF‑IDF giống diversity10k: 832 → 24 → 0 câu sau 3 vòng. Đạt cả hai tiêu chí (0 cặp cùng khung ≥ 0,95; 0% câu có hàng xóm ≥ 0,9, ngưỡng là < 3%). Vẫn giữ đủ 10.000 câu, không case nào thiếu.
2. **Khung mới.** Viết 397 khung trong `gen10k/frames_llm10k.py`: 328 khung diễn đạt lại (`frame_source = "LLM diễn đạt lại (cần duyệt)"`, `evidence = "constructed"`) và 69 khung chức năng xe (phụ lục 6.3). Ưu tiên đúng thứ tự góp ý. Không thêm giá trị khe. Mọi case ≥ 0,5; thấp nhất CS03 0,606.
3. **Sửa lỗi cụ thể.**
   - "Làm ơn": xác suất tiền tố 8–10% → 2%, còn 1,01% số câu.
   - Danh sách VERBS bỏ "cảnh". Không coi câu bắt đầu bằng "cảnh báo", "điều hòa", "báo thức", "chỉ số", "kết quả"... là câu bắt đầu bằng động từ. Các câu ví dụ (F0613, F0915, F0933) không còn tiền tố "cho/giúp tui". Còn 7 câu khớp mẫu "cho … cảnh báo", nhưng đều là khung mới "cho {cảnh báo} báo sớm/muộn hơn" (nghĩa "làm cho"), đúng.
   - Không thêm từ đánh thức khi khung đã có "trợ lý" hoặc khe {wake}: 0 câu có "trợ lý" hai lần.
   - F0733: "sang VND" → "sang (tiền Việt|đồng Việt Nam)": 0 câu còn "VND".
   - 3b (phụ lục 6.1, 6.2): thêm `sub_region`, `residence`, `vocab_source`. Giọng Trung chia 40% ở quê, 30% Hà Nội, 30% TP.HCM. Người ở quê dùng từ chức năng theo bảng có nguồn của phụ lục (Huế: hí, nở, hớ, tui; Nghệ Tĩnh: dừ; cả ba: chi, mô, răng, rứa, ni). Bỏ nghe, giùm, chừ, hè, nì. Người sống ở Hà Nội dùng từ về xe theo Bắc, người ở TP.HCM theo Nam. Mọi câu giọng Trung vẫn `cần duyệt`.
4. **Miền Trung, chỉ chuẩn bị danh sách.** `data/m1m2_10k_v2/cho_nguoi_ban_ngu/khung_mien_Trung_can_viet_lai.tsv` liệt kê 2.282 khung xếp ưu tiên (150 khung ưu tiên 1 phủ 24,7% số câu), có cột trống cho 4 tiểu vùng. Kèm `bang_tu_xe_theo_tieu_vung.tsv` (bảng mục 5 của phụ lục). Script: `gen10k/make_trung_list.py`. Không tự điền từ xe cho miền Trung (phụ lục 6.4).
5. **Đồng bộ tài liệu.**
   - Sheet Tu_dia_phuong dòng "số 105" và cặp câu M4 CS07 "Số 105" trong xlsx đã sửa theo linh (Bắc) / lẻ (Trung, Nam). Cặp "Giá 1.200 đồng" vốn đã đúng nên không đổi.
   - Sửa thẳng XML trong file (`gen10k/fix_xlsx_105.py`), nên 708 công thức và giá trị đã tính còn nguyên. Đã kiểm `build10k` vẫn đọc được hạn ngạch từ Chi_tieu.
   - Đồng bộ cùng nội dung vào v0.3.jsonl, `scripts/data_v03.py`, `scripts/taxonomy_def.py`. Bản gốc ở `data/luu_truoc_sua_20261014/`.
   - diversity10k.py đã chép vào gen10k/. validate10k.py cảnh báo khi tỷ lệ lõi < 0,5 và báo lỗi khi một lõi vượt trần (chạy trên v1 ra đúng 8 case dưới 0,5).

## Không làm hoặc làm khác, và lý do

- **Các cặp từ xe chỉ có K1 trong phụ lục mục 4** (bấm còi/bóp kèn, lùi/de, lốp/vỏ xe, quay đầu/quay xe, bơm xăng, cầu vượt, lề đường): không thêm. Chưa có nguồn, và "bấm còi" hay "de" hiếm khi là lệnh nói với trợ lý. Chờ bảng mục 5.
- **"chừ" (Huế, Quảng Nam), "nỏ", "mần" (Nghệ Tĩnh):**
  - Không dùng "chừ" vì phụ lục ghi là K1.
  - "nỏ" (không), "mần" (làm) có nguồn, nhưng đổi máy móc dễ sai vị trí trong câu lệnh: "không" ở cuối câu hỏi không phải "nỏ"; "làm ơn" không thành "mần ơn".
- **Tiểu vùng Nam Trung Bộ cho người Trung ở quê:** phụ lục không có bảng từ, nên chỉ gán Nam Trung Bộ cho người sống ở Hà Nội/TP.HCM (từ ngữ không phụ thuộc tiểu vùng).
- **Đọc số theo nơi sống:** người Trung ở Hà Nội vẫn đọc "lẻ", "ngàn" theo giọng gốc. Chưa có nguồn cho việc đổi.
- **Câu dựng từ mẫu `seen`** giảm từ 839 xuống 682, vì trần 3 câu/lõi giới hạn lặp lại các mẫu nguồn ngắn. Không nới trần, đúng theo góp ý.
- **Số câu `cần duyệt`** tăng từ 3.592 lên 4.517, vì mọi câu sinh từ khung mới đều gắn `cần duyệt`, đúng nhãn "LLM diễn đạt lại (cần duyệt)".
- **README trong `data/m1m2_10k/`** vẫn ghi `build10k.py` sinh vào bộ cũ. Không sửa vì không ghi đè bộ cũ. Mặc định của `build10k.py` giờ là `data/m1m2_10k_v2/`.
