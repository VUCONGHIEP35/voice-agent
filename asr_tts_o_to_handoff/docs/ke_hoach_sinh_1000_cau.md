# Kế hoạch sinh 1.000 câu đánh giá (giai đoạn 2), 24 giọng VieNeu

Viết ngày 20/10/2026 từ phiên Claude app. Trạng thái: **kế hoạch, chưa chạy**. Claude Code đọc file này cùng `docs/ban_giao_tu_claude_app.md`. Mục 4 liệt kê các thay đổi mã cần làm, mục 5 liệt kê lệnh chạy.

## 0. Quyết định đã chốt

- **Giọng:** chỉ dùng 24 giọng có sẵn của VieNeu v3 Turbo: Bắc 15, Nam 7, Trung 2. Bỏ Minh Triết.
  - Không clone giọng. Không lấy giọng từ YouTube hay từ mô hình khác.
  - `docs/ke_hoach_clone_giong_youtube.md` và thư mục `tts_gen/voice_clone/` đã dừng. Không dùng hai thứ này.
- **Ba trường văn bản:**
  - `text_raw` là nhãn ASR (theo `CLAUDE.md`).
  - `text_spoken` là dạng đọc chuẩn, dùng để chấm CER.
  - Trường mới `tts_text` là chữ thực sự đưa vào TTS. Trường này chỉ có giá trị khi khác `text_spoken`; hiện chỉ dùng cho nhánh phiên âm từ ngoại (mục 3).
- **Mục đích của 1.000 câu:** đo các con số cần để quyết định có chạy 10.000 câu hay không, và chạy với quy tắc nào. Bản thân 1.000 câu này không phải là đích. Cần đo:
  1. Tỷ lệ phải sinh lại.
  2. Tỷ lệ đạt theo vùng.
  3. Bộ chấm tự động sai bao nhiêu so với tai người.
  4. Giọng nào kém.
  5. Từ ngoại nên đọc kiểu nào.
  6. Cấu hình ASR nào đáng giữ.
  7. Thời gian cho 10.000 câu.

## 1. Bài học từ thí điểm và cách áp dụng

| # | Bài học | Bằng chứng | Áp dụng ở 1.000 câu |
|---|---|---|---|
| 1 | Một giọng kém làm hỏng cả phần dữ liệu của nó | Minh Triết: CER gấp 5–8 lần giọng đối chứng ở cả 4 cấu hình | Mỗi giọng nhận ít nhất 22 câu, đủ để sàng lọc. Báo cáo theo từng giọng. Giọng bị cờ thì kiểm theo cách đã làm với Minh Triết (mục 8) |
| 2 | Thí điểm quá ít câu mỗi giọng nên không kết luận được về từng giọng | Mỗi giọng Bắc/Nam chỉ có 2–5 câu | Bắc khoảng 22 câu/giọng, Nam khoảng 48, Trung 167 |
| 3 | Lỗi cắt đầu câu bám theo giọng | Thí điểm có 6/100 câu bị cắt đầu. Đổi seed sửa được 3; 3 câu còn lại (Thái Sơn 2, Thanh Bình 1) vẫn bị cắt sau 3 lần sinh | Sinh lại tối đa 2 lần bằng seed mới. Nếu vẫn lỗi thì **đổi sang giọng khác cùng vùng, cùng giới**, ghi `voice_fallback_from` |
| 4 | Chỉ dùng một mô hình ASR thì chấm không đáng tin | PhoWhisper-medium và large chấm khác nhau 15/100 câu. Gộp 5 cấu hình thì số câu đạt tăng từ 65–66 lên 75 | Large CT2 là mô hình chính, cộng medium, c1, c2 và c3 (wav2vec2). Đo xem mỗi cấu hình đóng góp thêm bao nhiêu câu đạt, để chọn bộ rẻ nhất cho 10.000 câu |
| 5 | ASR hay nghe nhầm câu ≤ 3 âm tiết | "Gọi" bị nghe thành "vợ" hoặc "đội" | Không bao giờ tự loại câu ngắn. Không khớp thì đưa vào hàng chờ nghe |
| 6 | ASR nghe sai thanh điệu giọng Trung | "Báo cháy" thành "chảy", "Tám" thành "tạm" | Câu Trung tính CER bỏ thanh. Câu chỉ sai thanh thì đưa đi nghe (`chi_loi_thanh`). Người nghe gốc Trung quyết định có tự nhận loại này ở 10.000 câu hay không |
| 7 | ASR đổi từ địa phương sang từ phổ thông | "tui" thành "tôi", "hông" thành "không" | Coi các cặp này là tương đương khi chấm. Nhãn vẫn giữ từ địa phương |
| 8 | VieNeu đọc chữ Latin theo âm Anh, lệch với cách người Việt nói | sea-g2p đọc Zalo là zˈɑːloʊ; "playlist" bị nghe thành "play list"; VETC chưa được đổi chữ | Từ điển đọc lập theo **từ khác nhau**, không theo câu: cả bộ 10.000 câu chỉ có 38 tên Latin chưa duyệt cộng vài chục viết tắt. Thử A/B: nửa số câu đọc chữ Latin, nửa đọc phiên âm |
| 9 | Ngưỡng 0,10 chưa được hiệu chỉnh bằng tai người | Phiếu nghe thí điểm chưa ai điền | Nghe là **bước bắt buộc**. Mẫu nghe chia tầng theo kết quả chấm để đo được tỷ lệ chấm sai |
| 10 | Phiếu nghe thí điểm không mù | Tên tệp chứa tên giọng (`…__Ngoc_Tran__a0.flac`), nên người nghe đoán được vùng | Phiếu mới đổi tên tệp thành mã. Khóa đối chiếu để ở tệp riêng |
| 11 | Nút nghẽn nằm ở ASR, không ở TTS | TTS có RTF 0,09. Mỗi cấu hình Whisper mất 0,5–0,9 giây mỗi câu | Ghi thời gian từng bước, ngoại suy cho 10.000 câu |
| 12 | Giọng Trung không khớp tiểu vùng | Cả 2 giọng Trung đều là giọng Huế; câu Trung trải 4 tiểu vùng | Ghi cờ `giong_khop_tieu_vung` và báo cáo tỷ lệ đạt theo cờ này. Không tuyên bố phủ được tiểu vùng |
| 13 | Lọc bằng ASR có thể bỏ nhiều câu khó (Trung, câu ngắn, từ ngoại) hơn câu dễ | Thí điểm: Bắc đạt 82%, Trung chỉ 70% | Theo dõi tỷ lệ giữ lại theo vùng, độ dài, case, intent. Chênh lệch lớn thì sửa bộ chấm, không lặng lẽ bỏ câu |

## 2. Chọn câu và gán giọng (đã có script)

`tts_gen/select_eval1000.py` (viết trong phiên Claude app, đã chạy thử trên bộ v3):

- Bỏ 104 câu đã sinh: 100 câu thí điểm và 4 câu thêm của bài kiểm tra Minh Triết.
- Chia 1.000 câu theo tỷ lệ của bộ 10.000 câu: vùng × case × nhóm độ dài. Nhờ vậy tỷ lệ đạt đo được ngoại suy được cho 10.000 câu.
- Trong mỗi ô, lấy lần lượt theo intent. Kết quả phủ 123/127 intent.
- Gán giọng sẵn ở bước này, trước khi dùng GPU. `run_pilot.py` giữ nguyên trường `voice` có sẵn trong đầu vào.
- Chia 2 phần A (498 câu) và B (502 câu); mỗi giọng có mặt ở cả hai phần.
- Cùng seed (20261020) thì luôn ra cùng kết quả.

Kết quả chạy thử:

| Vùng | Rất ngắn | Ngắn | Thường | Dài | Tổng | Giọng | Câu/giọng | Nam giới |
|---|---|---|---|---|---|---|---|---|
| Bắc | 17 | 151 | 144 | 21 | 333 | 15 (6 nữ, 9 nam) | 22–23 | 60% |
| Trung | 18 | 163 | 134 | 19 | 334 | 2 (giọng Huế) | 167 | 50% |
| Nam | 20 | 156 | 139 | 18 | 333 | 7 (4 nữ, 3 nam) | 47–48 | 43% |

- **Miền Trung:**
  - 68 câu có người nói sống ở quê và thuộc tiểu vùng Huế, khớp với giọng.
  - 76 câu có người nói sống ở quê nhưng thuộc tiểu vùng khác (Nghệ Tĩnh, Quảng Nam – Đà Nẵng).
  - 190 câu có người nói sống ở Hà Nội hoặc TP.HCM; nhóm này không xét khớp tiểu vùng.
- **Câu có tên Latin chưa duyệt cách đọc:** 104 câu, chia 51 câu giữ chữ Latin (`giu_latin`) và 53 câu phiên âm (`phien_am`).
- **Giọng cần theo dõi** (từ thí điểm, cỡ mẫu rất nhỏ):

  | Giọng | Ghi nhận ở thí điểm |
  |---|---|
  | Xuân Vĩnh | 2/2 câu bị loại; đoạn tham chiếu chỉ khoảng 1 giây; nói nhanh nhất (5,48 âm tiết/giây) |
  | Thanh Bình | Cắt đầu |
  | Thái Sơn | Cắt đầu |
  | Hải Đăng | CER trung bình 0,148 |
  | Thùy Dung | CER trung bình 0,109 |

Tệp ghi ra trong `tts_gen/eval1000/`:

| Tệp | Nội dung |
|---|---|
| `eval_1000.jsonl` | Giữ mọi trường của bộ v3, cộng các trường mới: `voice`, `voice_gender`, `voice_style`, `voice_region`, `voice_sub_region`, `giong_khop_tieu_vung`, `loan_arm`, `loan_names`, `shard`, `tts_text`, `pron_variant`, `eval_idx` |
| `shard_A.jsonl`, `shard_B.jsonl` | Đầu vào cho `run_pilot.py` |
| `phan_bo.md` | Bảng phân bổ đầy đủ theo vùng, case, giọng, tiểu vùng, trạng thái duyệt |
| `tu_ngoai_can_doc.tsv` | Khung từ điển đọc, đã điền sẵn đề xuất K1 từ `../review/BANG_tu_ngoai_lai.csv`, có cột cảnh báo |

## 3. Chuẩn bị văn bản trước khi sinh (chỉ dùng CPU)

### 3.1 Từ điển đọc cho TTS (nhánh `phien_am`)

1. Chạy `python select_eval1000.py`, mở `eval1000/tu_ngoai_can_doc.tsv`. Tệp có khoảng 25 tên; người duyệt là người bản ngữ, cùng người duyệt `BANG_tu_ngoai_lai.csv` nếu có.
2. Sửa khóa có dấu `?` cho đúng chữ trong `text_spoken`:
   - `?Zing MP3` sửa thành `Zing` (vì `text_spoken` đã là "Zing em pê ba").
   - `?Wi-Fi` sửa thành `wifi`.
3. Ghi cách đọc vào các cột Bắc / Trung / Nam theo 3 quy tắc:
   - **Chỉ dùng âm tiết tiếng Việt hợp lệ**, không gạch nối, không có f/j/w/z, không có cụm phụ âm đầu như "pl", "bl", "gr", "xp". Ví dụ "da lô" thay cho "za lô", "pờ lây lít" thay cho "plây lít". Âm tiết không hợp lệ sẽ bị VieNeu đọc theo âm Anh. Cột `canh_bao` và script đều báo các âm tiết này.
   - Viết bằng chữ quốc ngữ, để giọng mỗi vùng tự áp âm của vùng mình. Ví dụ "da lô" được giọng Bắc đọc âm /z/, giọng Nam đọc âm /j/.
   - Ô vùng nào để trống thì script dùng ô có giá trị đầu tiên. Cột `nguon` ghi `duyet` hoặc `K1 chưa duyệt`.
4. Lưu tệp thành `tts_gen/lexicon/doc_tu_ngoai_tts.tsv`, rồi chạy lại `python select_eval1000.py --tts-lexicon lexicon/doc_tu_ngoai_tts.tsv`.
   - Câu, giọng, nhánh và phần giữ nguyên.
   - Chỉ có `tts_text` và `pron_variant` được điền thêm.
   - Script in ra các tên còn thiếu trong từ điển.
5. Không có người duyệt thì vẫn chạy được với đề xuất K1, sau khi đã sửa các âm tiết bị cảnh báo. Ghi rõ trong báo cáo là cách đọc chưa duyệt.

### 3.2 Từ điển biến thể để chấm ASR

1. Chạy `text_audit.py --jsonl eval1000/eval_1000.jsonl --out reports/text_audit_eval1000 --bang ../review/BANG_tu_ngoai_lai.csv`.
2. Từ `lexicon_template.tsv` của lần chạy đó, cộng với tệp tương ứng của thí điểm, lập `lexicon/asr_bien_the.tsv`. Mỗi dòng gồm dạng chuẩn và các cách viết mà ASR được phép ra. Ví dụ:
   - `playlist` → `play list`, `plây lít`, `pờ lây lít`
   - `Vy` → `vi`
3. Thêm cả cách đọc trong `doc_tu_ngoai_tts.tsv`. Mục 4, việc T3 tự cộng `tts_text` vào danh sách đáp án.
4. Xem `foreign_tokens.csv` để tìm chữ Latin không bị gắn cờ, ví dụ "Ocean Park", "Top". Những chữ này chỉ cần thêm biến thể chấm, không thêm vào nhánh A/B.

## 4. Thay đổi mã (việc cho Claude Code)

Mỗi việc có test nhỏ, theo kiểu `test_tts_checks.py`. Không đổi kết quả của các lượt chạy cũ.

| Việc | Tệp | Nội dung | Kiểm |
|---|---|---|---|
| T1 | `select_eval1000.py` | Đã có. Chạy bằng `.venv` để script so bảng giọng với `voices_v3_turbo.json` (lệch thì dừng) | `phan_bo.md` có 24 giọng, không có Minh Triết |
| T2 | `run_pilot.py` | (a) Đưa vào TTS `j.get("tts_text") or j["text_spoken"]`; `vieneu_text` tính từ chữ thực sự đọc. (b) Ghi vào manifest: `tts_text`, `pron_variant`, `loan_arm`, `eval_idx`, `voice_fallback_from`, `giong_khop_tieu_vung`. (c) Thêm `EXCLUDED_VOICES = {"Minh Triết": …}`: loại khỏi `vmeta`, dừng nếu đầu vào có giọng này, ghi vào `run_config.json`. (d) Chạy tiếp hoặc đổi giọng vào cùng thư mục thì không được ghi đè `run_config.json`: gộp `calls` mới vào tệp cũ, nếu không sẽ mất số đo thời gian dùng để ngoại suy | Chạy 24 câu (mỗi giọng 1 câu) không lỗi; câu nhánh `phien_am` có `tts_text` trong manifest |
| T3 | `asr_check.py` | Thêm `norm(tts_text)` vào danh sách đáp án (`ref_variants`) khi trường này có giá trị | Test: hyp "mở diu túp" khớp câu có `tts_text` |
| T4 | `make_fallback.py` (mới) | Tìm câu có dòng manifest cuối cùng mà `tts_check` khác `dat`. Chọn giọng khác cùng vùng, cùng giới: giọng ít câu nhất trong phần, ưu tiên giọng không bị cờ cắt đầu, hòa thì xét theo băm. Miền Trung không có giọng cùng giới nên lấy giọng còn lại và ghi `doi_gioi=true`. Ghi jsonl có `voice` và `voice_fallback_from`, rồi chạy `run_pilot.py --input <tệp> --out <cùng thư mục>`. Chỉ đổi giọng 1 vòng | Câu đổi giọng có 2 dòng manifest; hàm `active_rows()` chọn đúng dòng cuối |
| T5 | `gate_union.py` (mới) | Gộp mọi cấu hình ASR, chấm theo quy tắc ở mục 6. Ghi `gate_hop.csv`. In tóm tắt theo vùng và **đóng góp biên** của từng cấu hình: số câu chỉ đạt nhờ cấu hình đó, và số câu đạt khi dùng {L}, {L,M}, {L,c3}, {L,M,c3}, đủ 5 cấu hình | Chạy trên `runs/pilot100`: tổng `dat` + `dat_1nguon` phải xấp xỉ con số "hợp 5 cấu hình" trước đây (75/100); chênh thì giải thích (từ điển, quy tắc câu ngắn) |
| T6 | `report_eval.py` (mới) | Đọc các phần A/B, `eval_1000.jsonl`, `gate_hop.csv`. Báo cáo theo nhóm (mục 8). Ghi `reports/eval1000/bao_cao.md` và `theo_giong.csv` | Số câu trong báo cáo khớp manifest |
| T7 | `make_listen_sheet.py` (mới), `score_listening.py` (mới) | Lấy mẫu nghe phân tầng, chép tệp thành mã, lập phiếu mù và khóa (mục 7). Sau khi nghe thì chấm kết quả | Phiếu không lộ tên giọng, vùng hay kết quả chấm |

Dùng chung hàm `active_rows(manifest)`: với mỗi `sample_id`, lấy dòng cuối có `tts_check == "dat"`; không có thì lấy dòng cuối.

## 5. Thứ tự chạy

Chạy từ `tts_gen/` bằng `.venv/Scripts/python`. TTS và ASR không chạy cùng lúc, vì GPU chỉ có 4 GB.

1. **Chuẩn bị** (mục 3): chạy `select_eval1000.py`, lập từ điển, rồi chạy lại với `--tts-lexicon`. Lập `asr_bien_the.tsv`.
2. **Chạy thử 24 câu**, mỗi giọng 1 câu lấy từ đầu phần A, ra `runs/eval1000_smoke`. Kiểm T2: có các trường mới, có `tts_text`, Minh Triết bị chặn.
3. **Phần A, kèm thử ngắt rồi chạy tiếp:**
   1. Chạy `run_pilot.py --input eval1000/shard_A.jsonl --out runs/eval1000_A`.
   2. Ngắt bằng Ctrl+C khi đã xong khoảng một nửa số giọng, rồi chạy lại đúng lệnh đó.
   3. Kiểm:
      - 498 `sample_id` duy nhất.
      - Không trùng `utt_id`.
      - Mọi tệp `audio48` và `audio16` đều tồn tại.
   4. Ghi chú: câu sinh lại sau khi ngắt có thể khác bản không ngắt, vì thành phần lô thay đổi. Điều này chấp nhận được, chỉ cần ghi lại.
4. **Đổi giọng cho câu vẫn lỗi:** `make_fallback.py runs/eval1000_A`, rồi chạy `run_pilot.py` với tệp nó ghi ra, cùng `--out`.
5. **ASR phần A**, theo thứ tự (`asr_diagnose` đọc c0 từ jsonl của medium):
   1. `asr_check.py runs/eval1000_A --model vinai/PhoWhisper-medium --lexicon lexicon/asr_bien_the.tsv`
   2. `asr_check.py runs/eval1000_A --model vinai/PhoWhisper-large --backend ct2 --ct2-dir .cache/ct2/PhoWhisper-large-int8 --lexicon lexicon/asr_bien_the.tsv`
   3. `asr_diagnose.py runs/eval1000_A --whisper vinai/PhoWhisper-medium`
   4. `gate_union.py runs/eval1000_A --lexicon lexicon/asr_bien_the.tsv`
6. **Điểm dừng sau phần A.** Chỉ dừng khi có một trong 3 điều sau, còn lại thì chạy tiếp phần B, vì cần đủ cỡ mẫu mới kết luận được về từng giọng:
   - Lỗi quy trình: mất hoặc trùng câu, hoặc `tts_text` không được dùng.
   - Hơn 25% số câu phải sinh lại.
   - Nhãn lệch có hệ thống, tức nhiều câu sai cùng một kiểu.
7. **Phần B:** làm lại bước 3–5 với `shard_B.jsonl` và `runs/eval1000_B`, lần này không cần thử ngắt.
8. **Báo cáo:** `report_eval.py runs/eval1000_A runs/eval1000_B --plan eval1000/eval_1000.jsonl --out reports/eval1000`
9. **Nghe** (mục 7), sau đó chạy `score_listening.py`.
10. **Quyết định** (mục 8). Ghi vào `reports/eval1000/quyet_dinh_10k.md` và cập nhật tài liệu kế hoạch 10.000 câu.

Thí nghiệm phụ, tùy chọn, tốn dưới 1 phút GPU: với các câu vẫn bị cắt đầu sau 3 lần sinh, gồm 3 câu thí điểm và các câu mới, sinh lại bằng cấu hình B của `test_voice_config.py` (`use_ref_codes=False`) trên chính giọng cũ. Nếu cách này sửa được, nó có thể thay cho việc đổi giọng ở 10.000 câu, giữ được cân bằng giọng.

## 6. Quy tắc chấm gộp (`gate_union.py`)

- **Cấu hình:**

  | Mã | Cấu hình |
  |---|---|
  | L | PhoWhisper-large CT2 int8, beam 5 |
  | M | PhoWhisper-medium |
  | c1 | M + đệm im lặng, giải mã tham lam |
  | c2 | M + đệm im lặng + beam 5 |
  | c3 | wav2vec2 CTC, không mô hình ngôn ngữ |

- **Đáp án:** gồm `text_spoken`, `tts_text` và các biến thể trong `asr_bien_the.tsv`. Từ địa phương được coi là tương đương (như `asr_check.py`).
- **Ngưỡng:** 0,10 cho cả ba vùng. Đây là ngưỡng **TẠM**, sẽ chốt lại sau khi nghe.

Xét theo thứ tự:

1. **Lỗi kỹ thuật:** `tts_check` không đạt.
   - Chưa đổi giọng thì ghi `sinh_lai`.
   - Đã đổi giọng mà vẫn lỗi thì ghi `can_nghe` (lý do `tts`).
2. **Câu ≤ 3 âm tiết:**
   - Có cấu hình bất kỳ cho CER = 0 thì ghi `dat`.
   - Không có thì ghi `can_nghe` (lý do `cau_ngan`).
3. **Cả L và M đạt** (≤ ngưỡng): ghi `dat`.
4. **Có ít nhất một cấu hình đạt, nhưng không đủ cả L và M:** ghi `dat_1nguon`, kèm tên các cấu hình đạt.
   - c3 đạt là bằng chứng tốt về âm thanh, vì CTC không có mô hình ngôn ngữ nên không tự sửa lời thành câu đúng.
   - Chỉ c1/c2 đạt nghĩa là lỗi nằm ở cách giải mã của ASR.
5. **Không cấu hình nào đạt:**
   - Giọng Trung mà CER bỏ thanh ≤ ngưỡng thì ghi `can_nghe` (lý do `chi_loi_thanh`).
   - Còn lại ghi `loai`.

## 7. Nghe mù có phân tầng

Lấy mẫu theo kết quả chấm, để đo được bộ chấm sai bao nhiêu ở từng nhóm. Lấy ngẫu nhiên đều thì nhóm hiếm sẽ quá ít câu.

| Tầng | Số tệp | Dùng để đo |
|---|---|---|
| S1 `dat` | 15 mỗi vùng = 45 | Tỷ lệ nhận nhầm câu sai |
| S2 `dat_1nguon` | Tối đa 15 mỗi vùng = 45 | Có tự nhận nhóm này ở 10.000 câu được không |
| S3 `can_nghe` | Tất cả (dự kiến 80–120; nếu quá 120 thì lấy phân tầng theo vùng và lý do) | Phải quyết định từng câu; đồng thời đo tỷ lệ đúng của `chi_loi_thanh` và `cau_ngan` |
| S4 `loai` | 15 mỗi vùng = 45 | Tỷ lệ loại nhầm câu đúng, tức lọc có thiên lệch hay không |
| Bổ sung | Đủ ≥ 15 câu mỗi nhánh từ ngoại; đủ ≥ 3 tệp mỗi giọng | So A/B cách đọc; nhận vùng theo từng giọng |

Tổng khoảng 250–300 tệp.

**Cách tổ chức:**

- **Tệp nghe:** chép tệp 48 kHz gốc vào `nghe_mu/` với tên mã (`nghe_0001.flac`…), xáo thứ tự bằng seed.
- **Khóa đối chiếu:** `nghe_mu/khoa_KHONG_DUA_NGUOI_NGHE.csv` ghi mã → `utt_id`, giọng, vùng, tầng, kết quả chấm.
- **Cột trong phiếu:** `ma_tep`, `cau_can_doc` (lấy `tts_text` nếu có, không thì `text_spoken`), `doc_dung` (Đ/S/?), `tu_sai`, `loi_ky_thuat` (cắt đầu / méo / nói thêm / bỏ chữ / khác), `vung_nghe_duoc` (Bắc/Trung/Nam/không rõ), `tu_nhien_1_5`, `tu_ngoai_tu_nhien` (C/K, chỉ với câu có từ ngoại), `ghi_chu`.
- **Người nghe:** ít nhất 2 người bản ngữ; ít nhất 1 người gốc Trung (tốt nhất là người Huế) nghe các tệp Trung.
  - Mỗi người nghe hết để tính độ đồng thuận (Cohen's kappa).
  - Thiếu thời gian thì chia đôi, giữ khoảng 25% tệp chung.
  - Mỗi người nghe 5 tệp làm quen trước, lấy từ thí điểm, không tính điểm.
- **Thời gian:** khoảng 20 giây mỗi tệp, tức khoảng 1,5 giờ mỗi người nghe.
- Phiếu thí điểm (`runs/pilot100/phieu_nghe.csv`) **không** cần điền nữa. Muốn tận dụng thì chỉ lấy 33 câu Trung, đổi tên tệp cho mù.

`score_listening.py` tính:

- Tỷ lệ `doc_dung` theo tầng và vùng (lấy theo đa số người nghe), kèm khoảng tin cậy Wilson 95%.
- Kappa giữa các người nghe.
- Ma trận nhầm vùng theo từng giọng.
- Điểm tự nhiên trung bình theo giọng.
- So sánh hai nhánh từ ngoại.

## 8. Báo cáo và điều kiện đi tiếp lên 10.000 câu

**`report_eval.py` báo cáo** theo vùng, giọng, nhóm độ dài, case, `review_status`, `loan_arm`, `giong_khop_tieu_vung`. Mỗi nhóm gồm:

- n, tỷ lệ sinh lại, tỷ lệ còn lỗi sau khi đổi giọng;
- số câu ở từng kết quả chấm, tỷ lệ `dat` kèm khoảng tin cậy Wilson;
- CER trung bình của câu > 3 âm tiết;
- trung vị âm tiết/giây;
- thời gian từng bước;
- đóng góp biên của từng cấu hình ASR;
- ngoại suy cho 10.000 câu: thời gian, và số câu sẽ rơi vào hàng chờ nghe.

**Cờ giọng.** Một giọng bị cờ khi gặp một trong ba điều sau:

- Cận trên Wilson 95% của tỷ lệ `dat` thấp hơn tỷ lệ chung của vùng.
- CER trung bình lớn hơn 2 lần trung vị của vùng.
- Từ 5% số câu trở lên vẫn bị cắt đầu sau khi sinh lại.

Giọng bị cờ thì kiểm theo `docs/kiem_tra_giong_minh_triet.md`: 8 câu × 2 seed × 4 cấu hình, so với 2 giọng đối chứng, cộng nghe. Sau đó quyết định giữ hay bỏ.

- Bắc còn 15 giọng nên bỏ được nếu cần.
- Nam còn 7 giọng; bỏ giọng nam nào thì giọng nam chỉ còn 2.
- Trung không bỏ được giọng nào. Chỉ ghi giới hạn và chuyển câu lỗi đi nghe.

**Điều kiện đi tiếp.** Đây là các mốc TẠM. Không đạt thì sửa rồi chạy lại phần liên quan, không chạy 10.000 câu.

| Mã | Điều kiện |
|---|---|
| G1 | Ngắt rồi chạy tiếp: không trùng, không mất câu; báo cáo khớp manifest |
| G2 | Tỷ lệ phải sinh lại ≤ 10%. Sau khi đổi giọng, số câu còn cắt đầu ≤ 0,5%. Không giọng nào phải sinh lại quá 25% số câu |
| G3 | Sau khi áp quy tắc đã hiệu chỉnh bằng nghe, tỷ lệ giữ lại mỗi vùng ≥ 85% và chênh nhau giữa các vùng ≤ 10 điểm %. Nếu không đạt, sửa bộ chấm cho vùng bị thiệt trước |
| G4 | Theo kết quả nghe: S1 có ≤ 3% câu sai, nếu không thì hạ ngưỡng và chấm lại (chấm lại không tốn GPU). S2 có ≤ 10% câu sai thì tự nhận `dat_1nguon` ở 10.000 câu. `chi_loi_thanh` đúng ≥ 80% thì tự nhận ở 10.000 câu. Nếu S4 có ≥ 30% câu đúng ở một vùng, sửa từ điển hoặc ngưỡng của vùng đó |
| G5 | Không còn giọng bị cờ chưa xử lý. Người nghe nhận đúng vùng của giọng Bắc/Nam ≥ 80% và của giọng Trung ≥ 70% |
| G6 | Đã chọn cách đọc từ ngoại cho 10.000 câu: Latin, phiên âm, hoặc trộn 50/50 nếu cả hai đều đạt và nghe tự nhiên (trộn thì đa dạng cách phát âm hơn) |
| G7 | Đã chọn bộ cấu hình ASR cho 10.000 câu theo đóng góp biên: bỏ cấu hình nào thêm < 1% số câu đạt. Số câu ngoại suy rơi vào hàng chờ nghe phải nằm trong sức nghe; nếu không thì biến quy tắc thành tự nhận hoặc tự loại theo kết quả hiệu chỉnh |

## 9. Ước lượng thời gian và tài nguyên (RTX 3050 Ti Laptop 4 GB)

| Bước | 1.000 câu | Ngoại suy 10.000 câu | Cơ sở |
|---|---|---|---|
| TTS | Khoảng 40 phút âm thanh; khoảng 4 phút GPU, cộng 20 giây nạp mô hình mỗi lượt và khoảng 10% sinh lại | Khoảng 6,8 giờ âm thanh; khoảng 40 phút GPU | RTF 0,09; 0,277 giây âm thanh mỗi âm tiết (thí điểm) |
| ASR L | Khoảng 12 phút | Khoảng 2 giờ | 70,4 giây/100 câu |
| ASR M | Khoảng 14 phút | Khoảng 2,4 giờ | 85,8 giây/100 câu |
| c1 + c2 | Khoảng 23 phút | Khoảng 3,8 giờ | 49 + 88 giây/100 câu |
| c3 | Dưới 1 phút | Khoảng 4 phút | 2,1 giây/100 câu |
| Tổng GPU | **Khoảng 55 phút** | Khoảng 9 giờ nếu giữ đủ 5 cấu hình; khoảng 2 giờ nếu chỉ L + c3 | |
| Ổ đĩa | Khoảng 100 MB FLAC | Khoảng 1 GB | Thí điểm: 7,6 MB cho 247 giây ở 48 kHz |
| Người | Lập từ điển 1–2 giờ; nghe khoảng 1,5 giờ mỗi người | | |

## 10. Giới hạn ghi vào báo cáo

- **Miền Trung chỉ có 2 giọng, cả hai là giọng Huế.** Ở 10.000 câu, mỗi giọng đọc khoảng 1.667 câu, nên ASR có thể học thuộc 2 giọng này. Không tuyên bố phủ được tiểu vùng Nghệ Tĩnh hay Quảng Nam.
  - Câu sống ở quê thuộc tiểu vùng khác Huế vẫn được đọc bằng giọng Huế.
  - Cách giảm nhẹ:
    - Đánh giá ASR riêng cho miền Trung trên dữ liệu thật.
    - Tăng cường dữ liệu bằng tốc độ, nhiễu xe và vang ở bước sau.
    - Cân nhắc tỷ trọng câu Trung tổng hợp khi huấn luyện; việc này thuộc thí nghiệm ASR.
- Nam chỉ có 3 giọng nam, trong đó Thái Sơn có lỗi cắt đầu.
- Đoạn tham chiếu của Xuân Vĩnh chỉ dài khoảng 1 giây.
- Cách đọc từ ngoại theo đề xuất K1 là chưa duyệt, nếu không có người duyệt.
- Ngưỡng 0,10 và mọi mốc trong mục 8 là mốc tạm.
- Bộ chấm dựa vào ASR. Câu đúng mà ASR nghe sai vẫn có thể bị loại; tầng S4 đo phần này.
- Âm thanh không có watermark, nên metadata phải ghi rõ đây là giọng tổng hợp.
- Vẫn chưa có tập kiểm thử thu thật trong xe. Không có tập này thì không đo được dữ liệu tổng hợp giúp ASR được bao nhiêu (tỷ lệ WR).

## 11. Không làm trong giai đoạn này

- Clone giọng; lấy giọng từ YouTube hay mô hình khác; tinh chỉnh LoRA.
- Co giãn tốc độ; thêm nhiễu hay vang (các việc này thuộc bước sau, làm trên bộ đã lọc).
- Huấn luyện ASR.
- Sửa bộ câu v3: lỗi văn bản phát hiện được ghi vào báo cáo để sửa ở vòng sau của `gen10k/`.
