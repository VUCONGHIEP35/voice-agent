> Ghi chú 27/10/2026: preset dùng mã E theo sheet Preset_moi_truong của data/du_lieu_asr_tts_o_to_v0.3.xlsx, không dùng mã P01–P08 bên dưới (đặc tả 15/10 không có trong repo). Trọng số micro và ghế theo đặc tả gốc (micro đều 4 vị trí; ghế 70/20/10 cho mọi case, kể cả CS11), không theo cột "Đề xuất". Bảng gán RIR không gán preset; preset gán ở bước cộng nhiễu. Bản đang làm: docs/ke_hoach_RIR_v2.md (28/10: ưu tiên RIR đo thật McVAMPIRE + CAVEMOVE, CC BY 4.0; RIR mô phỏng chỉ để bù).
Kế hoạch chèn RIR vào dữ liệu TTS sạch
Oct 26, 2026 · @Hiep Vu
Tóm tắt
Chèn RIR làm theo 6 giai đoạn, chạy hoàn toàn trên CPU, ước tính 6–9 ngày công nếu chưa có xe để đo. Đầu vào là âm thanh TTS đã qua lọc CER; đầu ra là bản đã có vang, căn trễ, cùng mức giọng, kèm rir_id để bước cộng nhiễu dùng tiếp. Kế hoạch bám đặc tả pipeline ngày 15/10 và chỉ chi tiết hóa phần RIR; phần nhiễu, SpecAugment và đánh giá giữ nguyên như đặc tả.
1. Chuẩn hóa âm thanh sạch: chuyển về 16 kHz mono, cắt lặng hai đầu, đưa về cùng mức giọng hoạt động.
2. Dựng kho RIR: RIR mô phỏng khoang xe (bắt đầu từ đây) cộng RIR đo của CAVEMOVE (khi đã kiểm giấy phép).
3. Kiểm định kho RIR: đo EDT, DRR, C50 từng RIR, loại RIR lệch dải, so phân bố mô phỏng với CAVEMOVE.
4. Gán RIR cho từng câu: theo preset (xác suất 0,8), ghế theo case, micro theo vị trí phổ biến trên xe thật.
5. Chập và lưu: chập FFT, căn lại độ trễ đường trực tiếp, giữ đuôi vang, khôi phục mức giọng, ghi manifest.
6. Kiểm tra chất lượng: tái lập bằng mã băm, nghe thử, đo CER của ASR trước và sau RIR để bắt lỗi pipeline.
Điểm khác hoặc thêm so với đặc tả (đề xuất, chờ bạn duyệt): hạt giống riêng cho mỗi câu thay vì một luồng rng chung; trọng số micro nghiêng về cụm micro trần theo khảo sát phần cứng; lưu bản "chỉ có vang" làm bộ đệm để chạy thêm hệ đối chứng RIR không nhiễu.
Điểm xuất phát
Kế hoạch bắt đầu khi có đủ ba thứ: âm thanh TTS đã lọc CER, manifest nối mỗi file với câu trong bộ v3, và hồ sơ người nói. Thứ tự đã thống nhất: TTS sạch → lọc CER bằng ASR → RIR → cộng nhiễu ở SNR chọn trước. RIR chỉ áp cho file đã qua lọc; file bị loại không đi tiếp.
Đầu vào
Cần có
Hiện trạng
Âm thanh TTS sạch
WAV mono, tần số gốc của TTS (22,05 hoặc 24 kHz)
Chưa xem được. Máy của bạn chưa kết nối thư mục nào với thread này
Manifest TTS
sample_id, speaker_id, đường dẫn file, CER sau lọc, cờ qua/loại
Chưa có định dạng chốt; đề xuất các trường này
Nhãn câu
text_raw, case_id, speaker_region, sub_region, length_class, core
Có trong data/m1m2_10k_v3 (10.000 câu)
Hồ sơ người nói
speaker_id, vùng, giới, nhóm tuổi
Sheet Ho_so_nguoi_noi mới có dòng ví dụ
Kho RIR
RIR mô phỏng và RIR đo
Chưa có; giai đoạn 1 dựng
Giả định đang dùng để ước lượng: mỗi câu được sinh bằng một giọng, khoảng 10.000 file, trung bình 2,5 giây (khoảng 7 giờ). Nếu mỗi câu sinh nhiều giọng thì dung lượng và thời gian chạy tăng tuyến tính, kế hoạch không đổi.
Giai đoạn 0: chuẩn hóa âm thanh sạch
Mục tiêu là mọi file sạch cùng tần số, cùng mức và không có khoảng lặng thừa, để RIR và SNR sau này có nghĩa như nhau trên mọi câu. Làm một lần, lưu vào clean16k/.
1. Đổi tần số về 16 kHz bằng bộ lấy mẫu lại chất lượng cao (soxr hoặc torchaudio, lọc chống chồng phổ). 16 kHz khớp với đầu vào của Whisper, Zipformer và với micro trong xe theo khảo sát phần cứng.
2. Cắt lặng hai đầu, chừa lại khoảng 150 ms mỗi bên. TTS hay đệm lặng dài; nếu để nguyên, đuôi vang và nhiễu rơi vào khoảng lặng và mức giọng bị tính sai.
3. Chuẩn hóa mức giọng hoạt động về −26 dBFS (đo trên phần có tiếng, bỏ khung lặng bằng VAD năng lượng đơn giản hoặc theo kiểu ITU‑T P.56). −26 dBFS chừa khoảng 20 dB trước khi cắt đỉnh.
4. Ghi lại thời lượng, mức đỉnh và mức giọng vào clean_manifest.jsonl; đánh dấu file ngắn hơn 0,4 giây hoặc dài hơn 10 giây để xem tay.
Lưu ý: nếu bước lọc CER đã làm sẵn việc đổi 16 kHz thì dùng lại, không lấy mẫu lại lần hai. File gốc 22,05/24 kHz giữ nguyên, không ghi đè.
Giai đoạn 1: dựng kho RIR
Đề xuất kho ban đầu khoảng 5.100 RIR mô phỏng từ 160 khoang xe, cộng tối đa 160 RIR đo của CAVEMOVE. Kho này đủ để mỗi RIR chỉ lặp lại khoảng 3–4 lần trên 20.000 bản trộn train, nên mô hình khó học thuộc một khoang cụ thể.
RIR mô phỏng (làm trước)
Dùng pyroomacoustics: phòng hộp chữ nhật, image source cho phần sớm cộng ray tracing cho đuôi, bật hấp thụ không khí, chạy ở 16 kHz, cắt RIR ở 0,25 giây.
Loại xe
Dài (m)
Rộng (m)
Cao (m)
Số khoang
Hạng A nhỏ
1,7–2,0
1,30–1,40
1,10–1,20
40
Sedan
1,9–2,2
1,40–1,50
1,10–1,20
40
SUV
2,0–2,5
1,45–1,60
1,20–1,35
40
MPV
2,4–2,8
1,45–1,60
1,20–1,35
40
Cách chia dải theo loại xe là nhận định của tôi, nằm trong dải chung của đặc tả (D 1,7–2,8; R 1,3–1,6; C 1,1–1,35); cần đối chiếu thông số nội thất xe thật.
• Vật liệu: mỗi mặt một hệ số hấp thụ theo dải octave. Kính trước, kính bên phản xạ mạnh; trần vải, ghế, sàn thảm hấp thụ cao. Bốc ngẫu nhiên quanh giá trị trong bảng vật liệu của pyroomacoustics, ±20%.
• Chọn khoang theo đích, không theo công thức Sabine: sinh khoang, đo EDT của RIR ghế lái, giữ khoang nếu EDT trong 0,03–0,15 giây, không thì bốc lại. Đặc tả đã ghi Sabine không áp được cho khoang xe.
• Toạ độ người nói: 4 ghế (lái bên trái vì xe Việt Nam tay lái thuận), miệng cao 0,6–0,75 m trên mặt ghế, lệch ±10 cm. Mỗi ghế 2 vị trí đầu.
• Toạ độ micro: 4 vị trí theo đặc tả: trần trước cạnh đèn đọc, gương chiếu hậu, cột A, táp‑lô.
• Số RIR: 160 khoang × 4 ghế × 4 micro × 2 vị trí đầu = 5.120 RIR, khoảng 80 MB dạng float32.
• Giới hạn: hộp chữ nhật không có lưng ghế, nên RIR ghế sau có đường trực tiếp không bị chắn và DRR cao hơn thực tế. Ghế sau vì vậy ưu tiên dùng RIR đo khi có.
• Hầm (P08): để sau, khi P08 có nguồn nhiễu.
RIR đo của CAVEMOVE (khi đã kiểm giấy phép)
Theo đặc tả: 4 xe, 5 vị trí người nói, 8 micro, tối đa 160 RIR. Bài báo không nêu giấy phép, nên bước đầu là đọc kho GitHub của họ; chưa rõ thì hỏi tác giả và chạy tiếp chỉ với RIR mô phỏng. Xử lý: đổi về 16 kHz (tần số gốc cần kiểm), cắt đuôi ở nền ồn, ghi giấy phép vào rir_manifest.
Chia train/dev theo khoang
Khoang là đơn vị chia, để dev kiểm được khả năng gặp khoang chưa thấy: 144 khoang mô phỏng vào train, 16 vào dev (4 mỗi loại xe). CAVEMOVE: 3 xe vào train, 1 xe giữ cho dev và cho phép kiểm "mô phỏng so với đo" ở giai đoạn 5.
Mỗi dòng banks/rir_manifest.jsonl ghi: rir_id (dạng rir_suv03_drv_ovh_h1), nguồn (mô phỏng/đo), loại xe, khoang, ghế, micro, toạ độ miệng và micro, kích thước và vật liệu (nếu mô phỏng), EDT, T20, DRR, C50, độ trễ đường trực tiếp, split, giấy phép, phiên bản công cụ và hạt giống.
Giai đoạn 2: kiểm định kho RIR
Kho RIR được dùng khi mọi RIR nằm trong dải chỉ số đặt trước và phân bố của bản mô phỏng không lệch hẳn so với CAVEMOVE. Việc này làm trên kho, trước khi chập bất kỳ câu nào.
Kiểm
Cách làm
Ngưỡng đề xuất
EDT
Theo dải octave 250 Hz–8 kHz
0,03–0,15 giây (cận dưới chưa có nguồn)
DRR
Năng lượng ±2,5 ms quanh đỉnh trực tiếp so với phần còn lại
Ghi lại, so phân bố với CAVEMOVE theo ghế
C50
Năng lượng 50 ms đầu so với phần sau
Phần lớn RIR cao, vì Liang 2024 ghi phản xạ đến trong 50 ms
Độ trễ trực tiếp
Vị trí đỉnh so với khoảng cách miệng–micro chia tốc độ âm
Lệch dưới 1 ms (bắt lỗi toạ độ)
Hình dạng
Không NaN, không đỉnh trước đường trực tiếp, đuôi tắt dần
0 RIR lỗi
Nghe thử
Chập 5 câu với 20 RIR mỗi loại xe
Không tiếng kim loại, không tiếng vọng nghe như phòng lớn
RIR trượt ngưỡng bị loại và sinh lại, không sửa tay. Xuất banks/rir_qa.json gồm phân bố EDT và DRR theo loại xe, ghế, micro, đặt cạnh phân bố của CAVEMOVE. Nếu DRR mô phỏng ở ghế sau cao hơn CAVEMOVE rõ rệt (dự đoán do không có lưng ghế), tăng tỷ lệ RIR đo cho ghế sau.
Khi có xe mục tiêu, đo RIR theo kế hoạch khảo sát trong đặc tả (sine sweep mũ, 4 ghế × vị trí micro thật + 2) và hiệu chỉnh hệ số hấp thụ cho tới khi EDT lệch tối đa 20%, DRR tối đa 2 dB ở các dải từ 500 Hz.
Giai đoạn 3: gán RIR cho từng câu
Mọi lựa chọn ngẫu nhiên được quyết định trước và ghi vào một bảng gán (assign_train.jsonl, assign_dev.jsonl), rồi mới chập. Bạn xem được phân bố trước khi tốn công tính, và bước cộng nhiễu đọc cùng bảng đó nên preset không bị lệch giữa hai bước.
1. ng.
2. Ghế: mặc định lái 70%, phụ 20%, sau 10% (sau trái và sau phải chia đều). Đề xuất riêng cho CS11 hành kMỗi bản trộn (train 2 bản mỗi câu, dev 1 bản) đi qua các bước sau:
    1. Preset: bốc trong các preset P01–P08 có case của câu (cột "Case dùng" của sheet Preset_moi_truong). Hai bản của cùng câu khác preset hoặc khác SNR.
    2. Có áp RIR không: bốc theo xác suất của preset (0,8 cho mọi preset theo đặc tả). Không áp thì rir_id rỗhách: lái 20%, phụ 30%, sau 50%, vì đặc tả nói ghế sau phục vụ CS11.
3. Micro: đặc tả đang bốc đều 4 vị trí. Đề xuất trần 50%, gương 20%, cột A 15%, táp‑lô 15%, vì khảo sát phần cứng ghi micro thường gắn theo cụm trên trần xe. Trọng số cụ thể là nhận định, chưa có số đếm.
4. RIR: lấy ngẫu nhiên đều trong kho đúng split (train hoặc dev) khớp ghế và micro. Hai bản của cùng câu không dùng chung một RIR.
Hạt giống riêng mỗi bản: seed = băm(sample_id, số thứ tự bản, hạt giống chung). Bộ sinh câu gen10k dùng một luồng rng chung nên thêm khung ở một case đã làm đổi câu mọi case sau. Với hạt giống theo bản, thêm hay bớt file TTS không làm đổi bản trộn của các file khác.
Kiểm bảng gán trước khi chập: tỷ lệ có RIR của mỗi preset lệch tối đa 2 điểm phần trăm; phân bố ghế, micro, loại xe theo case và theo vùng Bắc/Trung/Nam; không RIR dev nào xuất hiện trong bảng train.
Giai đoạn 4: chập và lưu
Mỗi bản có RIR đi qua 6 bước cố định; bản không RIR chỉ qua bước 5–6 để mọi file đến bước cộng nhiễu cùng định dạng và cùng mức.
1. Nạp file sạch 16 kHz và RIR đã gán, dạng float32.
2. Chập bằng FFT (scipy.signal.fftconvolve). Chỉ chập tiếng nói; nhiễu xe thu thật không bao giờ đi qua bước này.
3. Căn trễ: bỏ các mẫu trước đỉnh đường trực tiếp (vị trí lấy từ rir_manifest), để bản vang thẳng hàng với bản sạch.
4. Giữ đuôi vang: độ dài ra = độ dài sạch + tối đa 0,25 giây đuôi, không cắt về đúng độ dài gốc.
5. Khôi phục mức: đưa mức giọng hoạt động về lại −26 dBFS, đo trên các khung có tiếng của bản sạch (dùng lại mặt nạ VAD của giai đoạn 0) để đuôi vang không làm lệch phép đo. SNR ở bước sau tính trên chính bản đã có vang này, như đặc tả.
6. Chống cắt đỉnh: đỉnh vượt −1 dBFS thì hạ cả bản xuống và ghi mức hạ.
Lưu gì: đề xuất ghi bản "chỉ có vang" ra bộ đệm aug_v1/_reverb/ dạng WAV PCM 16 bit, ngoài thư mục train/dev chính thức. Bước cộng nhiễu đọc từ đây. Bộ đệm tốn khoảng 1,7 GB cho 20.000 bản, đổi lại: nghe riêng hiệu ứng RIR, chạy lại bước nhiễu với SNR khác mà không chập lại, và huấn luyện thêm một hệ đối chứng "RIR không nhiễu" nếu muốn tách đóng góp của RIR khỏi đóng góp của nhiễu trong F2.
Ghi vào manifest mỗi bản, thêm vào các trường đặc tả đã có: rir_id, rt60_s, drr_db, ghế, micro, toạ độ miệng và micro, độ trễ đã bỏ (mẫu), hệ số khôi phục mức (dB), mức hạ chống cắt đỉnh (dB), seed. Không ghi gì về SpecAugment.
Code dự kiến: rir_bank.py (sinh và đo kho), rir_assign.py (bảng gán), rir_apply.py (chập, chạy song song nhiều tiến trình), test_rir.py (test đơn vị: xung đơn vị cho ra đúng bản sạch, độ trễ bị bỏ đúng, mức ra đúng −26 dBFS), tất cả đọc aug_config.yaml. Chưa viết dòng nào; tôi chờ bạn đồng ý.
Giai đoạn 5: kiểm tra chất lượng
Bước RIR được coi là xong khi đạt cả danh sách dưới; ngưỡng là đề xuất, bạn sửa được. Các mục của bước nhiễu (SNR đo lại, cắt đỉnh sau trộn) vẫn theo tiêu chí chấp nhận của đặc tả.
[ ] Chạy lại với cùng aug_config.yaml và hạt giống cho ra file giống hệt, so bằng mã băm.
[ ] Thêm 100 file TTS giả vào đầu vào rồi chạy lại: mã băm của mọi file cũ không đổi (kiểm hạt giống theo bản).
[ ] Độ trễ giữa bản sạch và bản vang, đo bằng tương quan chéo, dưới 2 ms ở 99% bản.
[ ] Mức giọng hoạt động sau bước 5 trong −26 ± 0,5 dBFS ở 99% bản; không bản nào còn đỉnh trên −1 dBFS.
[ ] Tỷ lệ có RIR của mỗi preset lệch tối đa 2 điểm phần trăm; tỷ lệ ba miền trong train và dev lệch tối đa 2 điểm so với bộ câu.
[ ] splits.json chứng minh không khoang, không xe CAVEMOVE nào của dev xuất hiện trong train.
[ ] Người nghe kiểm 30 bản ngẫu nhiên mỗi loại xe và mỗi nhóm ghế (trước, sau): không click, không lặp, không vang kiểu phòng lớn.
[ ] CER của ASR lọc (cùng mô hình đã dùng ở bước lọc CER) trên 500 câu dev, trước và sau RIR, không nhiễu.
[ ] Kiểm "mô phỏng so với đo" của đặc tả: cùng tập TTS dev, chập với RIR xe CAVEMOVE giữ riêng và với RIR mô phỏng cùng ghế, chạy B0. WER chênh dưới 1 điểm phần trăm thì tin RIR mô phỏng; không thì tăng tỷ lệ RIR đo.
Về mục CER: khoang xe vang ngắn nên tôi dự đoán CER tăng nhẹ (chưa có số đo). Con số này dùng để bắt lỗi pipeline trên toàn tập, ví dụ sai độ trễ hay sai tần số RIR khiến CER tăng vọt. Không dùng nó để loại từng file sau RIR: câu khó hơn chính là thứ mô hình cần học, và lọc theo ASR sẽ bỏ đúng những câu đó.
Tài nguyên và lịch
Toàn bộ bước RIR chạy trên CPU; A100 chỉ cần cho bước kiểm bằng ASR. Dung lượng thêm khoảng 2,6 GB: kho RIR 80 MB, âm thanh sạch 16 kHz 0,8 GB, bộ đệm vang 1,7 GB (tính cho 10.000 file, 2,5 giây, 2 bản train). Thời gian sinh 5.120 RIR chưa đo; tôi ước vài giờ CPU và sẽ đo trên 50 RIR trước khi chạy cả kho. Chập FFT 20.000 bản dự kiến vài phút, chủ yếu là đọc ghi đĩa.
1. Giai đoạn 0, chuẩn hóa: 0,5 ngày.
2. Giai đoạn 1, kho RIR mô phỏng: 2 ngày. Gửi câu hỏi giấy phép CAVEMOVE ngay ngày đầu vì có thể phải chờ.
3. Giai đoạn 2, kiểm định kho: 1 ngày.
4. Giai đoạn 3, bảng gán: 0,5–1 ngày.
5. Giai đoạn 4, chập và test: 1 ngày.
6. Giai đoạn 5, QA và nghe thử: 1–2 ngày, chưa tính thời gian người nghe.
Cộng lại 6–7,5 ngày công; để biên lên 9 ngày nếu phải làm lại kho RIR sau kiểm định. Đo RIR trên xe mục tiêu không nằm trong lịch này.
Quyết định cần chốt
Kế hoạch đang chạy theo cột "Đề xuất"; sửa thẳng vào ô nếu bạn muốn khác.
Điểm
Đặc tả hiện tại
Đề xuất
Trọng số micro
Bốc đều 4 vị trí
Trần 50%, gương 20%, cột A 15%, táp‑lô 15%
Ghế cho CS11
Như mọi case: lái 70%, phụ 20%, sau 10%
Lái 20%, phụ 30%, sau 50%
Bộ đệm "chỉ có vang"
Không nhắc tới
Lưu, thêm 1,7 GB
Hệ đối chứng RIR không nhiễu
Không có (B0, F1, F2, F3)
Tùy chọn, chỉ chạy nếu cần giải thích kết quả F2
CAVEMOVE
Dùng sau khi kiểm giấy phép
Giữ nguyên; chạy trước với RIR mô phỏng
Mô phỏng âm sau xử lý của xe
Ngoài phạm vi (bước 5)
Giữ ngoài phạm vi, xem ghi chú dưới
Ghi chú: khảo sát phần cứng ghi âm thanh tới ASR trong xe đã qua khử vọng, khử nhiễu và tạo búp sóng theo ghế. Nếu đúng với xe đích, âm thật có thể ít vang hơn RIR thô tại micro (nhận định, chưa kiểm). Tỷ lệ 20% bản không RIR phần nào che điều này; kết luận chắc phải chờ bộ thu thật qua đúng chuỗi xử lý của xe.
Đã kiểm và giả định
• Đã đọc: đặc tả pipeline RIR + SpecAugment (15/10/2026), khảo sát phần cứng ô tô (21/10/2026), hướng dẫn dự án. Các số về EDT, CAVEMOVE, Liang 2024 lấy lại từ đặc tả, tôi không mở lại bài gốc.
• Chưa xem được: âm thanh TTS và manifest TTS trên máy bạn; số file, tần số và độ dài thật có thể khác giả định 10.000 file, 2,5 giây.
• Nhận định của tôi: dải kích thước theo loại xe, số khoang, trọng số micro và ghế CS11, mức −26 dBFS, độ dài đuôi 0,25 giây, các ngưỡng QA mới, ước lượng thời gian và dung lượng.