# Dự án: sinh dữ liệu lệnh giọng nói trong xe (tiếng Việt) cho huấn luyện ASR

Ngôn ngữ làm việc: tiếng Việt. Nói rõ điều gì đã kiểm, điều gì chỉ là nhận định; không bịa nguồn hay số liệu.

## Mục tiêu
- Không có dữ liệu thật tiếng Việt trong xe. Dùng TTS (clone giọng từ bộ dữ liệu thật có nhãn vùng Bắc/Trung/Nam) như công cụ SINH dữ liệu cho ASR, rồi trộn nhiễu xe thật + vang SAU khi sinh. Giọng tham chiếu và dữ liệu tinh chỉnh TTS phải sạch.
- Huấn luyện ASR trên: dữ liệu thật ngoài miền xe + dữ liệu sinh (M1, M2) + tập sinh ngoài miền xe (M3). Đánh giá trên bộ thật giữ riêng.
- Phi thương mại, nghiên cứu, một GPU A100.

## Mục đích dữ liệu
M1 lệnh người dùng · M2 trả lời ngắn · M3 tập đối chiếu ngoài miền xe (chưa có transcript) · M4 câu chẩn đoán chọn mô hình TTS · M5 lời trợ lý (ngoài phạm vi ASR).

## Yêu cầu gốc (đã hoàn thành, xem các dòng Trạng thái bên dưới)
Sinh khoảng 10.000 câu M1 + M2 theo mẫu câu × khe (data/…v0.3.xlsx, sheet Mau_khung, Chi_tieu), tổng hợp từ nhiều nguồn, chính xác, chia nhiều file JSONL, mỗi file ôm trọn một nhóm chủ đề.
Hạn ngạch theo case (sheet Chi_tieu, trọng số sửa được): CS01 1500, CS03 1400, CS04 1200, CS05 1200, CS12 900, CS10 1100, CS08 700, CS07 600, CS06 500, CS02 300, CS09 300, CS11 300.
Gợi ý chia file: dẫn đường (CS01) · điều khiển xe (CS03) · giải trí (CS04) · điện thoại (CS05) · trạng thái xe + sạc (CS06+CS07) · giao thông/thời tiết (CS08) · hội thoại chủ động (CS10) · trả lời ngắn/làm rõ (CS12) · khẩn cấp + an toàn + hành khách (CS02+CS09+CS11). Kèm manifest.json và README nguồn.
Yêu cầu chất lượng: mỗi mẫu có text_raw và text_spoken (không còn chữ số trong text_spoken); biến thể vùng Bắc/Trung/Nam cân bằng; cột review_status cho từ miền Trung và từ vựng chưa xác minh; không câu trùng; giới hạn tỷ trọng mỗi mẫu câu; phủ các yếu tố do câu quyết định (sheet Yeu_to, bước 1). Lược đồ dòng JSONL xem data/du_lieu_asr_tts_o_to_v0.3.jsonl.

**Trạng thái (2026-10-13):** đã sinh 10.000 câu vào data/m1m2_10k/ (9 file JSONL + manifest.json + qa_report.json + README_nguon.md) bằng gen10k/ (build10k.py, validate10k.py, test_vnnum.py; chạy bằng `py -3.13`). Kiểm tự động 0 lỗi. Việc tiếp: người bản ngữ duyệt các câu `review_status` = cần duyệt / nên duyệt; diễn đạt lại bằng LLM nếu cần thêm đa dạng. generator/ cũ không dùng (lý do trong README_nguon.md).

**Trạng thái (2026-10-14), góp ý vòng 1:** đã làm theo ../review/GOP_Y_v1.md và PHU_LUC_tu_vung_mien_Trung.md, báo cáo trước/sau ở ../review/BAO_CAO_vong1.md. Bộ mới data/m1m2_10k_v2/ (gen10k-2.0, mặc định của build10k.py; bộ v1 giữ nguyên).
- Kết quả: vẫn 10.000 câu. Tỷ lệ lõi 0,465 → 0,723, mọi case ≥ 0,6. Câu gần trùng cos ≥ 0,9 từ 986 xuống 0. "Làm ơn" 5,3% → 1,0%.
- Thay đổi chính:
  - Trần 3 câu/lõi (lõi = diversity10k.carrier) và vòng lọc gần trùng TF‑IDF.
  - 397 khung mới chưa duyệt trong gen10k/frames_llm10k.py.
  - Giọng Trung chia hồ sơ theo nơi sống: quê 40% (sub_region Huế / Nghệ Tĩnh / Quảng Nam – Đà Nẵng, từ chức năng theo bảng có nguồn), Hà Nội 30% (từ Bắc), TP.HCM 30% (từ xe Nam). Trường mới: sub_region, residence, vocab_source, core; lexicon_variant = vocab_source.
  - Xlsx đã sửa dòng "số 105" và cặp M4 theo linh/lẻ (bản gốc ở data/luu_truoc_sua_20261014/).
- Mỗi lần sinh chạy: test_vnnum.py, validate10k.py (có cảnh báo lõi < 0,5), diversity10k.py (cần numpy, scikit-learn).
- Việc tiếp:
  - Người bản ngữ Trung Bộ điền data/m1m2_10k_v2/cho_nguoi_ban_ngu/ (danh sách khung xếp ưu tiên + bảng từ xe theo tiểu vùng).
  - Người duyệt xem 4.517 câu "cần duyệt", gồm mọi câu sinh từ khung LLM.
  - Không tự sinh thêm từ Trung bằng K1.

**Trạng thái (2026-10-15), vòng 2 (v3):** đã làm theo `CHANGES_v3.md`, báo cáo ở ../review/BAO_CAO_vong2.md. Bộ mới data/m1m2_10k_v3/ (gen10k-3.0, mặc định của build10k.py; v1, v2 giữ nguyên).
- Kết quả: 10.000 câu, hạn ngạch và cân bằng vùng giữ nguyên. Nhóm G1–G8 có 770 câu, đủ mục tiêu mục 6. G1–G4 có 420 câu (35% CS04). 0 câu cos ≥ 0,9.
- Tỷ lệ lõi theo `carrier` cũ:
  - Toàn bộ: 0,723 → 0,703. Giảm do lệnh "mở <tên>" gom về một lõi; đã biết trước.
  - Câu không thuộc G: mọi case trong ±0,02 so với v2, trừ CS07 −0,022. CS07 không có khung G; người dùng chấp nhận đây là dao động rng. Vì vậy `validate10k.py` báo 1 lỗi, ngưỡng vẫn 0,02.
  - Câu G theo `carrier_cap`: 0,61–0,95.
- Luật lõi:
  - Trần 3 câu/lõi dùng `diversity10k.carrier_cap`, giữ tên app, bản đồ, thu phí, nguồn kết nối.
  - Trường `core` vẫn theo `carrier` như v2; trường mới `core_cap` là lõi dùng cho trần.
  - Không sửa `carrier`.
- Thay đổi chính:
  - 218 khung K1 app trong gen10k/frames_app10k.py: mọi câu `cần duyệt`, có trường `app_group`, trần cứng theo (nhóm, case), sinh trước khung cũ.
  - Khe mới: `map_app`, `etc_app`, `kenh` (tên kênh mô tả, không dùng tên thật).
  - Cách đọc từ ngoại tra trong gen10k/loanwords10k.py, đọc ../review/BANG_tu_ngoai_lai.csv (đổi đường dẫn bằng biến BANG_TU_NGOAI).
- Trường mới: `platform`, `pron_variant`, `core_cap`, `app_group`.
- Cách đọc từ ngoại:
  - `text_raw` là nhãn ASR (dạng viết); `text_spoken` là đầu vào TTS.
  - Chỉ dùng cách đọc ở cột vùng đã duyệt. Chưa duyệt thì giữ nguyên và gắn cờ:
    - tên giữ chữ Latin → "cách đọc chưa xác minh" → cần duyệt (1.001 câu);
    - viết tắt đã đổi chữ, từ vay Việt hóa → nên duyệt (284 câu).
  - Bảng chưa ai duyệt, nên `pron_variant` đang rỗng. Vietmap, Waze, VETC, ePass còn chữ Latin trong `text_spoken`.
- Mỗi lần sinh chạy: test_vnnum.py, validate10k.py, diversity10k.py. Thêm compare10k.py (so v2/v3 theo text_raw, ghi so_voi_v2.tsv) và make_trung_list.py.
- Bộ sinh dùng một luồng rng chung, nên thêm khung ở một case đổi câu mọi case sau. Chỉ 1.382 câu v2 còn nguyên trong v3. Câu `seen` 682 → 605.
- Chưa có quyết định: gọi xe công nghệ và ví điện tử; Hey VinFast / Hey Google làm từ đánh thức; tăng hạn ngạch CS04.
- Còn mở:
  - người bản ngữ duyệt bảng từ ngoại;
  - nghe lại K-pop, AQI;
  - duyệt 218 khung K1 app;
  - kiểm Zalo, Viber trên Android Auto;
  - tập kiểm thu thật trong xe.

**Trạng thái (2026-10-25), v3.1:** bộ data/m1m2_10k_v31/ tạo bằng gen10k/make_v31.py từ v3, không sinh lại; v3 giữ nguyên.
- Người dùng chốt: bỏ hẳn từ đệm và tiếng gọi đầu câu (ờ, ê, nè, nì, "này," trống, "bạn ơi,"); bỏ từ đánh thức khỏi văn bản ("trợ lý ơi", "này trợ lý", khe {wake}). "Ờ không, …" (sửa lệnh) đổi thành "Không, …". Giữ "à" nghi vấn cuối câu và "Ừ" trong câu trả lời ngắn.
- Từ đánh thức ("Trợ lý ơi", "Hây trợ lý") sẽ thêm bằng ghép âm thanh ở bước TTS, không nằm trong văn bản. Nhãn theo từng âm tiết: âm tiết trọn thì ghi, âm tiết bị cắt dở thì bỏ.
- Tiểu từ Huế (người dùng 25/10): bỏ "hí", "nở", "hớ". Câu lệnh đổi sang "nghe" (60%) hoặc bỏ; câu hỏi đổi sang "rứa" (50%) hoặc bỏ. Nguồn: Đặng Diễm Đông 2024 tr. 103 và Bảng 2 (docs/kiem_tra_nguon_tieu_tu_Hue.md). Không dùng "giùm" vì validate10k cấm ở hồ sơ Trung quê. Trường `v31_tieu_tu_hue` ghi cũ→mới.
- Bộ sinh đã sửa theo cùng quyết định: lexicon10k bỏ tiền tố đệm, bỏ hí/nở/hớ (nhé→nghe, nhỉ→bỏ), "nghe" thành có nguồn; build10k wake_p = 0; khe {wake} để trống.
- Giữ 2 giọng TTS miền Trung (Ngọc Trân, Quang Sơn), người dùng chốt 25/10.
- Câu sửa xong mà trùng chữ (246), gần trùng cos ≥ 0,9 (133) hoặc trùng lõi do đổi tiểu từ Huế (139) đều bỏ và bù: 518 câu từ bộ sinh seed 7001–7004. Câu bù cùng case, purpose, vùng, app_group; lượt đầu bắt buộc cùng loại câu và cùng sub_region + residence; mỗi khung ≤ 5% case. 15 câu phải khác loại câu (câu cụt đã cạn khung). Trường `v31_bo` ghi đã bỏ gì hoặc câu bù cho câu nào; log ở v31_thay_doi.json.
- Kết quả: 10.000 câu; validate10k 0 lỗi, 0 cảnh báo; 8 câu có hàng xóm cos ≥ 0,9 (v3 là 0), không cặp nào ≥ 0,95. Hồ sơ Trung giữ nguyên (lệch ≤ 3 câu).
- Kế hoạch TTS chốt: docs/ke_hoach_sinh_tts_10k_chot.md.

**Trạng thái (2026-10-25), TTS 10.000 câu v3.1 trên A100:** chạy xong trên cụm HUST (tts_gen/server/, 1 job tại một thời điểm, chạy song song trong job bằng dieu_phoi.py).
- Thời gian máy khoảng 2 giờ 10 phút: thử cỡ lô + smoke + p01 mất 19 phút; p02–p10 mất 1 giờ 38 phút; ghép lời gọi mất 13 phút. ASR lô 16 (giống lô 2 ở 99,5% câu).
- Kết quả: 10.000/10.000 sample_id, 0 trùng, check_run đạt cả 10 phần; 6,66 giờ âm thanh.
  - 438 câu phải sinh lại; 114 câu đổi giọng (Thái Sơn 49 dù đã tắt ref codes; Thanh Bình 28; Thục Đoan 27).
- Chấm luật v1 (dat theo vùng): Bắc 82,3%, Nam 76,0%, Trung 36,5%. Cộng thêm dat_1nguon: Bắc 95,3%, Nam 93,0%, Trung 77,5%.
- Chấm luật v2 (chặt hơn): dat chỉ còn Bắc 57,8%, Nam 51,5%, Trung 14,1%.
- CER trung bình: Z 0,058; L 0,082; M 0,084; T (PhoWhisper-small, mô hình đích) 0,103. T trên nhóm dat là 0,045; trên dat_1nguon là 0,162.
- Ghép lời gọi: 1.002 câu (407 đủ cụm, 595 còn đuôi). dat (v1) 62,7% ở câu đủ cụm, 46,2% ở câu còn đuôi; câu cắt giữa âm tiết đầu hoặc giữa chỉ 18–23%.
- Kết quả và báo cáo: máy chủ ~/asr_tts_o_to/ket_qua/; laptop tts_gen/dist/tai_ve/full10k/ → runs/ket_qua_full10k/.

**Trạng thái (2026-10-26), tái cấu trúc tts_gen/ theo layer:** cauhinh → thuvien → buoc → phantich / dieuphoi, cộng kiemthu và luutru. Xem docs/cau_truc_ma.md (quy tắc phụ thuộc, bảng tên cũ → mới, cách chạy).
- Chạy bằng `python -m <lớp>.<tên>` từ tts_gen/. Test: `python -m unittest discover -s kiemthu -t .` (71 test).
- Cấu hình chỉ ở cauhinh/: giọng, mô hình ghim, ngưỡng.
- Kết quả đã kiểm giống từng byte mã cũ trên dữ liệu thật (chấm v1/v2, gán giọng, báo cáo…). Bước GPU chưa chạy lại bằng mã mới; lần tới chạy `smoke` trước.
- Tài liệu và lệnh ghi trước ngày này dùng tên script cũ.

**Trạng thái (2026-10-27), tái cấu trúc gen10k/ theo layer:** cauhinh → nguyen_lieu (kho khe, khung câu, từ vùng, từ ngoại) → thuvien (vnnum, slots10k, diversity10k) → buoc (build10k, make_v31, validate10k) → phantich, cộng kiemthu và luutru. Tên tệp giữ nguyên.
- Chạy từ gen10k/: `py -3.13 -m buoc.build10k …`. Test: `py -3.13 -m unittest discover -s kiemthu -t .` (13 test).
- CLI đa dạng đổi thành `-m phantich.diversity_report10k`.
- Mã cũ và mã mới cho ra bộ dữ liệu giống từng byte (build hai seed, make_v31, validate, diversity, compare).
- generator/ và scripts/ chuyển vào luutru/; xóa out/ rỗng. Sơ đồ toàn dự án: docs/cau_truc_ma.md.

**Trạng thái (2026-10-27), sau phiếu nghe full10k (49 câu, người nghe Bắc):** tạm chốt **luật v1**.
- v1 dat: 20/21 câu nghe đúng; v2 vứt 13/26 câu nghe đúng.
- Ghép lời gọi chỉ giữ kiểu đủ cụm và kiểu cắt đúng ranh giới. Kiểu cắt giữa âm tiết: người nghe đúng 1/6, nên bỏ.
- Trung và dat_1nguon để mở, chờ người miền Trung nghe.
- Zing đọc "ding": đã sửa lexicon. 25 câu Zing chưa sinh lại.
- Bảng preset: sheet Preset_moi_truong (mã E) trong xlsx v0.3. Mã P01–P08 trong RIR.md không dùng.
- **Việc tiếp: bước RIR theo docs/ke_hoach_RIR_v1.md** (đã duyệt hướng; quyết định ghi ở đầu docs/danh_gia_RIR.md).
  - Đầu vào 6.961 file v1 (6.491 câu thường + 470 câu ghép lời gọi), khoảng 4,9 giờ.
  - Preset (mã E) gán ở bước nhiễu, không ở bảng gán RIR; P(RIR) = 0,8.
  - pyroomacoustics trong venv riêng trên cụm.
  - Trọng số theo đặc tả gốc.
  - Không lọc CER sau RIR.

**Trạng thái (2026-10-27), bước RIR:** mã xong (tts_gen: cauhinh/tang_cuong, thuvien/rir, buoc/rir_kho|rir_gan|rir_chap, phantich/rir_qa|phieu_nghe_rir, dieuphoi/slurm/*rir*; 86 test đạt). Tiến độ, cách chạy và 10 chỗ khác kế hoạch ở đầu docs/ke_hoach_RIR_v1.md.
- Trên cụm đã có venv_rir; job thử `thu` (15295) nộp 27/10, chờ suất job.
- Hai điểm dừng chờ người dùng: phiếu nghe thử RIR; phân bố bảng gán (gồm tỷ lệ câu dev 10% theo băm câu gốc, là nhận định).
- Laptop có `tts_gen/.venv_rir` (pyroomacoustics) để thử mã RIR.

**Trạng thái (2026-10-28), RIR đo thật:** người nghe thấy kho mô phỏng "hơi vang" (7/20). Đo hai bộ RIR thật (docs/danh_gia_rir_that.md): mô phỏng vang gần gấp đôi 4 xe CAVEMOVE, chủ yếu ở 250 Hz. Người dùng chọn **ưu tiên RIR thật**.
- Kế hoạch chính: **docs/ke_hoach_RIR_v2.md** (v1 giữ làm lịch sử).
- Kho đo `buoc/rir_kho_do.py`: In-Car McVAMPIRE + CAVEMOVE (CC BY 4.0, phải trích dẫn), 1.214 RIR từ 5 xe; Golf làm dev. Kênh micro quy về 4 vị trí đặc tả.
- Bảng gán ưu tiên RIR đo với P_RIR_DO = 0,7; kho mô phỏng (vật liệu "hút âm hơn") bù chỗ thiếu. Thử trên laptop: train 69% RIR đo, dev 54%.
- 93 test đạt. Mã mới CHƯA lên cụm; chờ người dùng chọn chia dev, xác nhận P_RIR_DO/xe dev, cho chạy setup_rir.sh và nộp "kho kho_do gan".

**Trạng thái (2026-10-28, sau), RIR bản 3:** kế hoạch chính là **docs/ke_hoach_RIR_v3.md** (v2 giữ làm lịch sử). Khảo sát xe Việt Nam ở docs/kich_thuoc_xe_vn.md và docs/xe_vn_va_rir.md.
- Người dùng chọn: P_RIR_DO = 0,5; 7 loại khoang mô phỏng theo xe Việt Nam (mini, hanga, sedan, suv_b, suv_c, bay_cho, ban_tai), đều 40 khoang mỗi loại; chia train/dev theo frame_id.
- Mô phỏng đã hiệu chỉnh theo RIR đo (phantich/so_kho_rir.py): miệng cardioid p = 0,6, HAP_THU_THEM theo dải; kho đầy đủ trên laptop đạt 77/77 mục tiêu EDT/DRR.
- Thư mục chạy trên cụm: runs/rir_v2. Bước sbatch mới: so, nghe. 97 test đạt.
- Job 15463 (28/10) chạy "kho kho_do so nghe gan goi": đạt hết (77/77, mọi kiểm gán). Kết quả ở tts_gen/runs/ket_qua_rir_v2/ (docs/ke_hoach_RIR_v3.md mục 7). Người nghe thấy bán tải hơi vang -> sửa vách sau bán tải (ghế 0,8 / kính 0,2; EDT 0,080 -> 0,057 s). Job 15467 chạy lại cả chuỗi "kho so nghe gan chap asr qa goi" (kho cũ chuyển sang runs/rir_v2_cu_15463): đạt hết; 13.126 bản vang ở runs/rir_v2/aug_v1/_reverb/ trên cụm; CER dev trước→sau: L 0,0267→0,0341, M 0,0264→0,0366, T 0,0505→0,0519; RIR đo và mô phỏng tác động ngang nhau. Kết quả: tts_gen/runs/ket_qua_rir_v2_15467/, docs/ke_hoach_RIR_v3.md mục 9. Bước tiếp: cộng nhiễu (preset mã E).

**Trạng thái (2026-10-28), nhãn nơi xử lý (tại biên / cloud / cả hai):** đề xuất theo ý định, chờ người dùng duyệt.
- Tệp: data/nhan_xu_ly_y_dinh/nhan_xu_ly_y_dinh.xlsx (để duyệt; có danh sách chọn) và .tsv. Sinh bằng `gen10k/ -m phantich.nhan_xu_ly_y_dinh`.
- Có 129 cặp (case, ý định), từ 127 intent_id.
  - Tại biên: 80 ý định, 5.436 câu.
  - Cả hai: 32 ý định, 3.101 câu.
  - Cloud: 17 ý định, 1.463 câu.
  - 18 ý định đánh dấu "cần duyệt".
- Nhãn nói về việc thực hiện yêu cầu có cần Internet không. Gọi điện và SMS qua điện thoại = tại biên. Khẩn cấp và báo mất mạng bắt buộc tại biên. Chưa ghép nhãn vào JSONL hay manifest.

**Trạng thái (2026-10-28), bước nhiễu (preset mã E):** chưa có mã. Khảo sát nguồn ở docs/khao_sat_nguon_nhieu_preset.md.
- Mã E02–E08 trong trường `factors_covered` của câu là yếu tố nội dung (sheet Yeu_to), KHÔNG phải preset. Khi gán preset, dùng tên trường khác (ví dụ `preset_moi_truong`).
- Người dùng đồng ý 28/10: bỏ cột "SNR mục tiêu" của sheet (có lẽ dành cho loa phát, M5). SNR bốc đều theo nhóm:
  - E01, E08: 15–30 dB.
  - E02, E06, E11, E14, E15: 5–20 dB.
  - Các preset ồn cao: −5–15 dB.
- Nguồn:
  - CAVEMOVE (CC BY 4.0): tên tệp mang tốc độ, kính và mức quạt, phủ E02, E03, E05, E06, E09 (chỉ đường nhám ở 30 km/h). Mưa có thể nằm trong `unc_###`, chưa có nhãn.
  - AISHELL-5 (CC BY-SA 4.0, 13 GB, xe hybrid điện) phủ E05, E06, E08. Chưa biết tệp nhiễu có mã cảnh không.
  - E10 hầm, E12 còi kiểu Việt Nam, E14 âm báo xe: không có nguồn mở; cần mô phỏng, tổng hợp hoặc tự ghi.
- Chưa chốt: luật gán preset theo "Case dùng" (thuần hay trộn 60/40), trọng số, E09 (sheet chưa gán case), E11/E15.

## Bắt buộc về đọc số (tự viết bộ đọc và có test)
linh (Bắc) / lẻ (Nam, Trung) — người dùng chọn theo sources/src_lang.json (L5, L14) ngày 2026-10-13, thay cho ghi ngược lại trước đây; sheet Tu_dia_phuong và câu M4 đã sửa ngày 2026-10-14; nghìn (Bắc) / ngàn (Nam, Trung); mười, hai mươi mốt, hai mươi tư, mười lăm, hai mươi lăm; một trăm lẻ năm; số điện thoại đọc từng chữ số; 115/113/114 đọc từng chữ số; phần trăm; độ; ki lô mét; tần số "chín mươi mốt mê ga héc".

## Có sẵn trong thư mục này
- data/: bảng v0.3 (12 case, 71 yếu tố, 79 câu mẫu, chỉ tiêu) và JSONL câu mẫu.
- Cấu trúc thư mục và các lớp mã: docs/cau_truc_ma.md (sources → gen10k → data → tts_gen).
- luutru/scripts/: dữ liệu và code dựng bảng v0.3 (chạy từ thư mục đó, ghi ra luutru/out/). Lưu trữ, không bảo trì.
- sources/: src_commands.json (1008 mẫu lệnh, 127 "seen" / 881 "constructed", kèm nguồn), src_lang.json (từ vựng vùng, quy tắc đọc số, tên, nhạc, thuật ngữ xe; nhiều mục mức chắc chắn trung bình/thấp), dvhcvn.json + tinh_tp.json + quan_huyen.json (đơn vị hành chính; kiểm lại tên sau sáp nhập 2025).
- luutru/generator/ (lưu trữ; bộ sinh đang dùng là gen10k/): khung bộ sinh dở dang từ phiên trước (engine.py, gen_core.py, pools.py, tplbase.py, tpl_a.py, tpl_b.py, build.py, part1-3.txt, build_geo_part1-2.py). CHƯA được chạy kiểm hoàn chỉnh; đọc kỹ, chạy thử, sửa lỗi trước khi tin kết quả. Có thể dùng lại hoặc viết lại gọn hơn.
- ../review/: các file góp ý (GOP_Y_v1.md, PHU_LUC_*.md, BANG_tu_ngoai_lai.csv, BAO_CAO_vong1.md). CHANGES_v3.md ở gốc dự án.
- docs/phien_claude_ai.jsonl: bản ghi toàn bộ cuộc trao đổi gốc (chỉ để tra cứu khi cần; không cần đọc hết).

## Giới hạn đã biết
- Các hạn ngạch (60 người nói, 10.000 câu, tỷ lệ thật:sinh 1:1) lấy từ bài báo tiếng Anh/Hàn/Mân Nam, chưa kiểm cho tiếng Việt.
- Từ miền Trung (rứa, mô, tê, răng, chi, nớ, ni...) phân tiểu vùng chưa chắc; mọi câu miền Trung phải đánh dấu cần người bản ngữ duyệt.
- Địa chỉ trong câu là tổng hợp (số nhà ghép với tên đường thật), phải gắn cờ synthetic_address.
- Không tìm được tài liệu lệnh giọng nói tiếng Việt của Hyundai, Toyota, Kia, Mazda, MG, Ford; nguồn lệnh thật chủ yếu từ VinFast.
- Không đưa tên thương hiệu trợ lý làm từ đánh thức; dùng khe {wake} tùy chọn. (Đang chờ quyết định về Hey VinFast / Hey Google, xem CHANGES_v3.md mục 9.)

**Trạng thái (2026-10-29), bước trộn nhiễu:** đã tải nhiễu CAVEMOVE (7,6 GB) và AISHELL-5 (13,4 GB) về cụm `~/asr_tts_o_to/nhieu/` (buoc/nhieu_tai.py). AISHELL-5 không có bảng tra cảnh công khai; đã đo đặc trưng (phantich/do_nhieu.py) và làm phiếu nghe `tts_gen/runs/nhieu_v1/do/nghe2/phieu_nghe_nhieu.xlsx`. Kế hoạch: docs/ke_hoach_nhieu_v1.md; chờ người dùng nghe và quyết mục 7. Preset của bản ghi vào `preset_moi_truong`, KHÔNG dùng `factors_covered` (mã E của sheet Yeu_to).
- Người dùng chọn 29/10: giai đoạn 1 chỉ dùng CAVEMOVE có nhãn, 6 preset (E01, E02, E03, E05, E06, E09), gán 60/40 theo sheet, thử ASR bằng lưới SNR {20,10,5,0} × 6 preset trên 500 bản dev (L, M, T). Ba phương án nguồn nhiễu lưu ở docs/ke_hoach_nhieu_v1.md mục 2. Mã xong (14 test); thử nhỏ trên nút đầu đạt; job 15535 nộp 29/10, đầu ra runs/nhieu_v1/ trên cụm.
- Job 15535 xong 29/10 (1 giờ 37 phút): mọi kiểm trộn đạt. Kết quả: docs/ket_qua_nhieu_gd1.md. PhoWhisper-small: sạch 0,0505, chỉ vang 0,0519, lưới 20/10/5/0 dB 0,058/0,066/0,076/0,108, bộ sinh ra 0,062. E06 quạt gây hại nhất (0,233 ở 0 dB) vì 32% năng lượng nằm trong dải tiếng nói; ồn đường chủ yếu dưới 100 Hz. Báo cáo dùng CER chặn trần ở 1 (vài câu bị ảo giác).
