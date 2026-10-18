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

## Bắt buộc về đọc số (tự viết bộ đọc và có test)
linh (Bắc) / lẻ (Nam, Trung) — người dùng chọn theo sources/src_lang.json (L5, L14) ngày 2026-10-13, thay cho ghi ngược lại trước đây; sheet Tu_dia_phuong và câu M4 đã sửa ngày 2026-10-14; nghìn (Bắc) / ngàn (Nam, Trung); mười, hai mươi mốt, hai mươi tư, mười lăm, hai mươi lăm; một trăm lẻ năm; số điện thoại đọc từng chữ số; 115/113/114 đọc từng chữ số; phần trăm; độ; ki lô mét; tần số "chín mươi mốt mê ga héc".

## Có sẵn trong thư mục này
- data/: bảng v0.3 (12 case, 71 yếu tố, 79 câu mẫu, chỉ tiêu) và JSONL câu mẫu.
- scripts/: dữ liệu và code dựng bảng v0.3 (chạy từ thư mục scripts/, ghi ra out/).
- sources/: src_commands.json (1008 mẫu lệnh, 127 "seen" / 881 "constructed", kèm nguồn), src_lang.json (từ vựng vùng, quy tắc đọc số, tên, nhạc, thuật ngữ xe; nhiều mục mức chắc chắn trung bình/thấp), dvhcvn.json + tinh_tp.json + quan_huyen.json (đơn vị hành chính; kiểm lại tên sau sáp nhập 2025).
- generator/: khung bộ sinh dở dang từ phiên trước (engine.py, gen_core.py, pools.py, tplbase.py, tpl_a.py, tpl_b.py, build.py, part1-3.txt, build_geo_part1-2.py). CHƯA được chạy kiểm hoàn chỉnh; đọc kỹ, chạy thử, sửa lỗi trước khi tin kết quả. Có thể dùng lại hoặc viết lại gọn hơn.
- ../review/: các file góp ý (GOP_Y_v1.md, PHU_LUC_*.md, BANG_tu_ngoai_lai.csv, BAO_CAO_vong1.md). CHANGES_v3.md ở gốc dự án.
- docs/phien_claude_ai.jsonl: bản ghi toàn bộ cuộc trao đổi gốc (chỉ để tra cứu khi cần; không cần đọc hết).

## Giới hạn đã biết
- Các hạn ngạch (60 người nói, 10.000 câu, tỷ lệ thật:sinh 1:1) lấy từ bài báo tiếng Anh/Hàn/Mân Nam, chưa kiểm cho tiếng Việt.
- Từ miền Trung (rứa, mô, tê, răng, chi, nớ, ni...) phân tiểu vùng chưa chắc; mọi câu miền Trung phải đánh dấu cần người bản ngữ duyệt.
- Địa chỉ trong câu là tổng hợp (số nhà ghép với tên đường thật), phải gắn cờ synthetic_address.
- Không tìm được tài liệu lệnh giọng nói tiếng Việt của Hyundai, Toyota, Kia, Mazda, MG, Ford; nguồn lệnh thật chủ yếu từ VinFast.
- Không đưa tên thương hiệu trợ lý làm từ đánh thức; dùng khe {wake} tùy chọn. (Đang chờ quyết định về Hey VinFast / Hey Google, xem CHANGES_v3.md mục 9.)
