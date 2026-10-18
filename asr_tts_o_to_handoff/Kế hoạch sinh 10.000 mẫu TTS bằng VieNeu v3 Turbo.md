# Kế hoạch sinh 10.000 mẫu TTS bằng VieNeu v3 Turbo

Oct 18, 2026 · @Hiep Vu

## Tóm tắt

**Sinh 10.000 câu bằng VieNeu v3 Turbo không nặng về tính toán; điểm nghẽn thật nằm ở ghi file, hậu xử lý, kiểm tra chất lượng bằng ASR và việc phiên Colab bị ngắt.** Theo số đo của nhà phát triển, GPU cỡ RTX 3060 chạy với RTF khoảng 0,02 khi gom lô, nghĩa là khoảng 8 giờ âm thanh (ước lượng cho 10.000 câu lệnh ngắn) cần cỡ 10 phút đến dưới một giờ GPU. CPU (ONNX, RTF khoảng 0,5) cần khoảng 3–6 giờ. Các con số này phải đo lại ở giai đoạn 0.

- **Chọn máy:** dùng máy cá nhân nếu có GPU NVIDIA từ 8 GB VRAM trở lên. Không có thì chạy TTS trên CPU ở nhà và đưa bước kiểm tra bằng ASR lên Colab, hoặc chạy toàn bộ trên Colab với cơ chế lưu tiến độ theo lô.
- **Bốn giai đoạn:** chạy thử 5–10 câu → thí điểm 100 câu → 1.000 câu → 10.000 câu. Chỉ sang giai đoạn sau khi đạt điều kiện đặt trước.
- **Chống nghẽn:** nạp mô hình một lần; mã hóa giọng tham chiếu một lần rồi lưu lại; gom câu theo giọng và theo độ dài để lô luôn đầy; tách GPU và CPU bằng hàng đợi có giới hạn; chia dữ liệu thành các phần 500 câu, ghi nguyên tử và chạy tiếp được sau khi bị ngắt; ghi ra ổ cục bộ rồi mới đóng gói lên Drive.
- **Không lưu bản có nhiễu:** chỉ lưu âm thanh TTS sạch; nhiễu cabin và RIR cộng khi huấn luyện ASR, để dung lượng không tăng gấp nhiều lần.
- **Vướng mắc lớn nhất không phải kỹ thuật:** miền Trung chỉ có 2 giọng sẵn có. Nếu không thêm giọng clone, mỗi giọng Trung phải đọc hàng nghìn câu.

## Đầu vào và đầu ra

**Đầu vào** là bộ câu v3 có sẵn trong dự án: 10.000 câu M1/M2 với các trường `text_raw`, `text_spoken`, `speaker_region`, `sub_region`. TTS đọc `text_spoken` (đã ở dạng đọc), để tránh việc bộ chuẩn hóa văn bản bên trong VieNeu đọc số hoặc từ viết tắt khác với nhãn. Giai đoạn 1 phải kiểm tra điều này bằng cách so lời đọc với `text_spoken`.

**Giọng:** 25 giọng sẵn có của v3 Turbo (15 Bắc, 8 Nam, 2 Trung, theo tệp `voices_v3_turbo.json` trong mã), cộng các giọng clone đăng ký bằng `add_voice` khi có đoạn tham chiếu đạt chuẩn.

**Đầu ra:**

| Tệp | Nội dung |
| --- | --- |
| `audio48/<shard>/<utt_id>.flac` | Bản gốc 48 kHz, chưa có nhiễu |
| `audio16/<shard>/<utt_id>.flac` | Bản 16 kHz cho ASR, sinh từ bản gốc |
| `manifest.jsonl` | Một dòng mỗi câu: `utt_id`, `line_id`, `text_spoken`, vùng, tiểu vùng, giọng, nguồn giọng (sẵn có hay clone), giới tính, seed, số lần thử, thời lượng, thời gian có tiếng, số âm tiết, tốc độ trước và sau chỉnh, hệ số co giãn, lời ASR đọc lại, CER, trạng thái kiểm tra |
| `voices.json` | Kho giọng đã mã hóa (embedding và mã tham chiếu), dùng lại giữa các lần chạy |
| `run_config.yaml` | Phiên bản gói `vieneu`, commit mã, dtype, có bật watermark không, tham số sinh, ngưỡng kiểm tra |
| `report.md` | Thống kê cuối: phân bố tốc độ, độ dài, số câu mỗi giọng và mỗi vùng, tỷ lệ sinh lại và loại bỏ |

`utt_id` được tạo xác định từ `line_id`, `voice_id` và số lần thử, nên chạy lại luôn ra cùng tên file và bước nào đã xong thì bỏ qua được.

## Máy cá nhân hay Google Colab

Trước khi chọn, chạy kiểm tra máy một lần: `nvidia-smi` (loại GPU, VRAM), `torch.cuda.is_bf16_supported()`, số nhân CPU, `lscpu | grep -i vnni` (CPU có VNNI thì chạy được bản int8 nhanh hơn), dung lượng ổ còn trống. Mã VieNeu tự chọn: có CUDA thì chạy PyTorch (bf16 nếu GPU hỗ trợ, nếu không thì fp16), không có thì chạy ONNX trên CPU.

| Máy | TTS (VieNeu) | Kiểm tra bằng ASR (PhoWhisper-large) | Khuyến nghị |
| --- | --- | --- | --- |
| Cá nhân, GPU NVIDIA ≥ 8 GB (cỡ RTX 3060 trở lên) | Nhanh; nhà phát triển đo VRAM đỉnh 1,1 GB, RTF 0,01–0,02 khi gom lô | Chạy được, nên chạy sau TTS chứ không song song nếu VRAM sát | **Ưu tiên:** không giới hạn phiên, ổ cục bộ nhanh, dữ liệu không rời máy |
| Cá nhân, chỉ CPU hoặc Mac | Được, RTF khoảng 0,5 (fp32) hoặc 0,35 (int8, cần VNNI); 10.000 câu mất khoảng 3–6 giờ | Rất chậm trên CPU với mô hình large | TTS ở nhà, kiểm tra ASR trên Colab |
| Colab miễn phí | Loại GPU không được đảm bảo (thường T4, không có bf16 nên chạy fp16) | Được | Đủ cho toàn bộ việc vì tổng thời gian GPU ước tính dưới vài giờ, nhưng phiên tối đa 12 giờ và có thể bị ngắt khi rảnh, nên bắt buộc lưu tiến độ theo phần |
| Colab Pro, Pro+ | GPU mạnh hơn tùy tình trạng; Pro+ chạy liên tục tới 24 giờ | Được | Chỉ cần nếu sau này mở rộng (nhiều giọng mỗi câu, LoRA) |

**Quy tắc chọn:** có GPU NVIDIA từ 8 GB thì chạy tại máy. Không có thì chạy giai đoạn 0 cả trên CPU cá nhân và trên Colab, rồi chọn theo thời gian đo được. GPU không có bf16 (T4, dòng RTX 20xx) sẽ chạy fp16; chất lượng fp16 chưa được kiểm chứng nên giai đoạn 0 phải nghe so sánh với fp32.

**Trên Colab:** ghi mọi thứ ra ổ cục bộ `/content`, mỗi khi xong một phần thì đóng gói thành một tệp `.tar` và chép lên Drive. Google Drive không phải ổ tốc độ cao, và ghi hàng nghìn tệp nhỏ lên Drive đang gắn là nút nghẽn dễ gặp nhất. Đoạn tham chiếu và `voices.json` cũng lưu trên Drive để không phải mã hóa lại khi mở phiên mới.

## Triển khai từ nhỏ đến lớn

Mỗi giai đoạn có điều kiện để đi tiếp. Các ngưỡng có số dưới đây là mục tiêu ban đầu, cần chỉnh lại sau khi xem số liệu giai đoạn 1.

| Giai đoạn | Quy mô | Việc cần làm | Điều kiện đi tiếp |
| --- | --- | --- | --- |
| **0. Chạy thử** | 5–10 câu | Cài `vieneu` (GPU: `vieneu[cuda]` và `transformers==4.57.6` theo README). Nạp mô hình, sinh câu ngắn và dài bằng giọng 3 vùng. Đo VRAM đỉnh, RTF, thời gian nạp. Sinh cùng câu có và không có watermark; nếu GPU không có bf16 thì so fp16 với fp32. Thử `add_voice` với một đoạn tham chiếu. | Chạy không lỗi; nghe thấy đọc đúng câu và đúng vùng; đã ghi số đo và chọn máy |
| **1. Thí điểm** | 100 câu | Chọn phân tầng theo vùng × nhóm độ dài (có câu 1–3 âm tiết) × loại lệnh. Chạy đủ quy trình từ chuẩn bị đến đóng gói. Người bản ngữ nghe cả 100 câu. Đo thời gian từng bước để tìm nút nghẽn. Vẽ phân bố CER và tốc độ. | Chốt được ngưỡng kiểm tra; giọng Trung được nhận đúng vùng; tốc độ sau chỉnh nằm trong 4,0–5,6 âm tiết/giây; `text_spoken` được đọc đúng như viết |
| **2. Quy mô vừa** | 1.000 câu (2 phần × 500) | Cố ý ngắt giữa chừng rồi chạy lại. Kiểm tra đồng bộ Drive, vòng sinh lại, cân bằng số câu mỗi giọng. Nghe ngẫu nhiên 50 câu. Ngoại suy thời gian cho 10.000 câu. | Chạy tiếp không tạo trùng, không mất câu; tỷ lệ phải sinh lại dưới khoảng 10%; GPU không ngồi chờ CPU hoặc ổ quá khoảng 20% thời gian; đủ giọng cho mỗi vùng |
| **3. Toàn bộ** | 10.000 câu (20 phần × 500) | Chạy theo từng phần, kiểm tra, một vòng sinh lại cho câu lỗi, viết báo cáo. Nghe ngẫu nhiên 100–200 câu phân tầng theo vùng. | Báo cáo khớp với manifest; tỷ lệ loại bỏ cuối cùng được ghi rõ |
| **4. Mở rộng** (tùy chọn) | Nhiều giọng mỗi câu | Thêm giọng clone hoặc LoRA cho miền Trung, rồi bắt đầu thí nghiệm ASR (chỉ dữ liệu thật so với thật cộng tổng hợp) | Theo kết quả WER trên tập thật |

**Giọng Trung là điều kiện chặn trước giai đoạn 3.** Nếu chỉ có 2 giọng sẵn có, mỗi giọng sẽ phải đọc một nửa số câu miền Trung. Phải có thêm giọng clone (ViSpeech nếu được phép, hoặc giọng tự thu) trước khi chạy toàn bộ.

## Kiến trúc pipeline và thuật toán chống nghẽn

&#91;embedded content: quy trình sinh dữ liệu · 6 bước, 1 vòng sinh lại\]

Mỗi bước đọc và ghi qua manifest, nên có thể dừng ở bất kỳ đâu rồi chạy tiếp. GPU chỉ làm hai việc nặng là sinh TTS và nhận dạng lại; mọi thứ còn lại chạy song song trên CPU.

1. **Lập việc xác định.** Đọc bộ câu, gán giọng, chia thành 20 phần 500 câu, mỗi phần cân bằng vùng và độ dài. Seed của mỗi câu tính từ `line_id`, nên chạy lại luôn ra cùng kế hoạch.
2. **Gán giọng cân bằng.** Trong mỗi vùng: xáo câu bằng seed cố định, sắp theo loại lệnh rồi nhóm độ dài, chia vòng tròn cho các giọng của vùng, xen kẽ nam và nữ. Mỗi giọng nhận số câu gần bằng nhau và cùng phân bố độ dài, loại lệnh. Đặt trần số câu cho mỗi giọng; vùng thiếu giọng thì dừng và báo, không âm thầm dồn câu vào vài giọng.
3. **Mã hóa giọng một lần.** Đăng ký mỗi đoạn tham chiếu bằng `add_voice` (bật `denoise` chỉ khi đoạn chưa sạch), lưu `voices.json`, các lần chạy sau chỉ nạp lại. Không truyền `ref_audio` cho từng câu, vì mỗi lần như vậy là một lần khử nhiễu và mã hóa lại.
4. **Gom lô đúng cách.** Mỗi lệnh `infer_batch` nhận vài trăm câu cùng một giọng (hàm này yêu cầu cùng giọng). Bên trong, VieNeu tự sắp câu theo độ dài âm vị, gom tối đa `max_batch_size` (mặc định 32) câu mỗi lượt, chặn số khung tối đa theo độ dài câu, và tự sinh lại câu từ 3 âm tiết trở xuống nếu bị "nói thêm". Chỉnh `batch_size` theo VRAM đo ở giai đoạn 0.
5. **Sản xuất – tiêu thụ có giới hạn.** Luồng GPU đẩy âm thanh vào một hàng đợi chỉ chứa vài lô; một nhóm tiến trình CPU (số nhân trừ 1) lấy ra để hậu xử lý và ghi file. Hàng đầy thì GPU chờ, nhờ vậy RAM không phình ra. Nếu giữ watermark và đo thấy nó tốn thời gian, gọi `infer_batch(..., apply_watermark=False)` rồi áp watermark trong nhóm CPU.
6. **Ghi nguyên tử và chạy tiếp.** Ghi vào tệp tạm rồi đổi tên; mỗi phần có tệp trạng thái. Khởi động lại thì bỏ qua câu đã có tệp hợp lệ trong manifest, nên một lần ngắt Colab chỉ mất phần đang dở.
7. **Không để hai mô hình tranh GPU.** Trên GPU nhỏ, chạy TTS xong một phần rồi mới chạy ASR cho phần đó, ASR cũng gom lô theo độ dài. Trên GPU lớn có thể chạy hai bước chồng nhau giữa các phần.
8. **Sinh lại thành lượt riêng.** Câu lỗi không được sinh lại ngay (làm lô vơi), mà gom lại sau khi xong phần, dùng seed mới, tối đa 2 lần, sau đó đánh dấu loại.
9. **Tái lập được.** Đặt `torch.manual_seed` theo (phần, giọng, lô) trước mỗi lệnh sinh và ghi vào manifest. Mã VieNeu ghi rõ sinh theo lô cho kết quả tương đương nhưng không giống hệt từng bit với sinh từng câu.
10. **Theo dõi theo phần.** Mỗi phần ghi số câu mỗi giây, tỷ lệ thời gian GPU bận, số câu lỗi; tự dừng nếu tỷ lệ lỗi vượt ngưỡng, để không đốt hết phiên vào một lỗi cấu hình.

**Nhiễu và RIR không làm ở đây.** Chỉ lưu bản TTS sạch; nhiễu cabin và RIR được cộng ngẫu nhiên khi huấn luyện ASR (hoặc cộng một lần cho tập đánh giá cố định). Lưu sẵn nhiều biến thể nhiễu sẽ nhân dung lượng lên nhiều lần và khóa cứng tỷ lệ trộn.

## Kiểm soát chất lượng và vòng sinh lại

Các bước kiểm tra sắp từ rẻ đến đắt: câu nào hỏng ở bước CPU thì không tốn thời gian GPU cho ASR.

1. **Kỹ thuật (CPU).** Không rỗng; thời lượng hợp lý so với số âm tiết (khoảng cho phép chốt ở giai đoạn 1); không bị cắt đỉnh; cắt im lặng đầu và cuối về một độ dài cố định. Câu quá dài so với số âm tiết thường là "nói thêm" mà bộ chặn của VieNeu chưa bắt được.
2. **Tốc độ nói (CPU).** Đo tốc độ phát âm r = số âm tiết / thời gian có tiếng (VAD, không tính quãng nghỉ). Mục tiêu r\* của mỗi câu được lấy từ phân bố đã chốt (trung bình khoảng 4,8 trong khoảng 4,0–5,6 âm tiết/giây, thấp hơn khoảng 0,2 với câu sẽ gắn preset ồn) ngay từ lúc lập việc. Hệ số α = r\* / r:
   - |α − 1| ≤ 0,12: co giãn giữ cao độ trên bản 48 kHz, trước khi hạ xuống 16 kHz.
   - Vượt quá: sinh lại thay vì co giãn mạnh.
   - Câu 1–3 âm tiết: chỉ co giãn trong 1,0 ± 0,05, vì đo tốc độ trên vài âm tiết rất nhiễu.
   - Ghi α vào manifest. Nghiên cứu đã đọc cho thấy co giãn có thể làm WER tăng nhẹ, nên cần giữ để sau này so có và không co giãn.
3. **Nội dung (GPU).** PhoWhisper-large đọc lại bản 16 kHz, tính CER so với `text_spoken` sau khi chuẩn hóa (chữ thường, bỏ dấu câu). Ngưỡng chốt sau khi xem phân bố CER ở giai đoạn 1, chặt hơn với câu ngắn vì sai một âm tiết là sai cả lệnh.
4. **Giống người nói (GPU, chỉ với giọng clone).** Độ giống embedding WavLM-ECAPA giữa đoạn tham chiếu và đầu ra, để bắt giọng clone bị trôi.
5. **Giọng vùng (người nghe).** Không có cách tự động đáng tin, nên nghe theo mẫu: 100% ở giai đoạn 1, 5% ở giai đoạn 2, 1–2% ở giai đoạn 3, người nghe không biết nhãn vùng.

**Chính sách sinh lại:** lần 1 dùng seed mới; lần 2 dùng seed mới và hạ `temperature` (ví dụ từ 0,8 xuống 0,6) để đầu ra ổn định hơn; sau đó đánh dấu loại và giữ lại để phân tích. Thống kê tỷ lệ loại theo từng giọng: giọng nào hỏng nhiều bất thường thì rút khỏi kho giọng và chia lại câu.

**Cẩn thận thiên lệch khi lọc bằng ASR:** loại câu mà PhoWhisper đọc sai cũng có thể loại đúng những câu khó hoặc giọng vùng đậm, làm dữ liệu "dễ" hơn thực tế. Nên nghe một mẫu trong số câu bị loại và so tỷ lệ loại giữa ba vùng.

## Ước lượng tài nguyên

Giả định mỗi câu lệnh dài 2–4 giây (chưa đo trên bộ v3; giai đoạn 1 sẽ cho số thật). RTF lấy từ README của VieNeu đo trên RTX 3060 và Core i5 thế hệ 12; cận trên 0,1 cho GPU là mức tôi đặt để tính chi phí cố định của câu rất ngắn.

| Độ dài trung bình | Tổng âm thanh | TTS trên GPU (RTF 0,02–0,1) | TTS trên CPU (RTF 0,35–0,5) | WAV 48 kHz | WAV 16 kHz |
| --- | --- | --- | --- | --- | --- |
| 2 giây | 5,6 giờ | 7–33 phút | 1,9–2,8 giờ | 1,9 GB | 0,6 GB |
| 3 giây | 8,3 giờ | 10–50 phút | 2,9–4,2 giờ | 2,9 GB | 1,0 GB |
| 4 giây | 11,1 giờ | 13–67 phút | 3,9–5,6 giờ | 3,8 GB | 1,3 GB |

- **Cộng thêm sinh lại:** khoảng 10% nếu tỷ lệ lỗi như mục tiêu.
- **Lưu trữ:** lưu FLAC thay WAV sẽ nhỏ hơn (mức nén cần đo trên dữ liệu thật). Tổng dưới 5 GB, nằm thoải mái trong ổ cục bộ của Colab hoặc máy cá nhân. Khoảng 20.000 tệp âm thanh, đóng thành 20 tệp `.tar` khi đưa lên Drive.
- **Bộ nhớ:** nhà phát triển đo VRAM đỉnh của TTS khoảng 1,1 GB. Một lô 32 câu dài 4 giây ở 48 kHz chiếm khoảng 25 MB RAM, nên hàng đợi vài lô không đáng kể. PhoWhisper-large là mô hình cỡ Whisper large, cần vài GB VRAM ở fp16, vì vậy trên GPU nhỏ nên chạy nó sau TTS chứ không cùng lúc.
- **Chưa ước lượng được:** thời gian ASR kiểm tra, thời gian co giãn và watermark. Ba con số này đo ở giai đoạn 0 và 1. Khả năng cao là ASR kiểm tra mất thời gian ngang hoặc lâu hơn chính bước TTS, nên đây là bước cần gom lô cẩn thận nhất.

**Kết luận về máy:** với 10.000 câu, ngay cả Colab miễn phí cũng đủ nếu giữ tiến độ theo phần. Máy chỉ có CPU vẫn sinh được trong một buổi, nhưng bước ASR kiểm tra nên đưa lên GPU.

## Rủi ro và điểm chưa xác minh

| Rủi ro | Ảnh hưởng | Cách xử lý |
| --- | --- | --- |
| Miền Trung chỉ có 2 giọng sẵn có | Hai giọng đọc hết phần Trung, dữ liệu lệch | Thêm giọng clone trước giai đoạn 3; đặt trần số câu mỗi giọng |
| Giọng sẵn có chưa được nghe kiểm | Nhãn vùng có thể sai với âm thanh | Nghe mù ở giai đoạn 1 |
| Watermark Resemble Perth bật mặc định | Chưa biết ảnh hưởng đến ASR và tốc độ | So có và không ở giai đoạn 0. Nếu tắt, vẫn ghi rõ trong metadata rằng đây là giọng tổng hợp |
| GPU không hỗ trợ bf16 chạy fp16 | Chất lượng chưa kiểm chứng | So fp16 với fp32 ở giai đoạn 0 |
| VieNeu chuẩn hóa văn bản khác `text_spoken` | Nhãn không khớp lời đọc | Bước ASR kiểm tra bắt được; nghe câu có số, ký hiệu, từ tiếng Anh |
| Câu rất ngắn bị "nói thêm" | Nhãn sai | VieNeu có bộ chặn cho câu từ 3 âm tiết trở xuống; thêm kiểm tra thời lượng và CER |
| Colab ngắt phiên hoặc đổi loại GPU | Mất tiến độ, số đo không ổn định | Lưu theo phần, ghi loại GPU vào `run_config.yaml` |
| Mã VieNeu thay đổi nhanh | Kết quả không tái lập | Ghim `vieneu==3.8.3`, `transformers==4.57.6`, ghi commit `bd0f88e` |
| Dữ liệu tổng hợp khác phân bố giọng thật | ASR học được ít hơn mong đợi | Trộn với dữ liệu thật; đo WER trên tập thật, không đo trên dữ liệu tổng hợp |

**Chưa xác minh:**

- Giấy phép của trọng số v3 Turbo trên Hugging Face; chỉ mã nguồn được xác nhận là Apache-2.0.
- Mọi con số tốc độ và VRAM là của nhà phát triển, chưa chạy trên máy của bạn. Môi trường làm việc của tôi không tải được trọng số nên chưa chạy thử bước nào.
- Watermark Perth chạy trên CPU hay GPU và tốn bao lâu.
- Độ dài thật của câu trong bộ v3, nên bảng ước lượng còn là khoảng.
- Các ngưỡng (tỷ lệ sinh lại 10%, GPU chờ 20%, CER) là mục tiêu ban đầu của tôi, sẽ chỉnh sau giai đoạn 1.

Nguồn: mã VieNeu-TTS trên GitHub (`pnnbao97/VieNeu-TTS`, commit `bd0f88e`, đọc ngày 17–18/10/2026); hướng dẫn Colab của Hivenet (kiểm lại với tài liệu Colab ngày 20/8/2026).
