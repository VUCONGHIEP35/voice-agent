A. Quy tắc nội dung (sinh cái gì)
A1. Mỗi lệnh xe ánh xạ đúng một JSON hợp lệ. Xây bảng Intent × Slot (nhiệt độ, quạt, kính, khóa cửa, đèn, gạt mưa, âm lượng...), khớp với schema CAN dùng ở tuần FSM. Câu nào không ánh xạ được sang JSON thì loại.
A2. Năm nhóm nhãn, có hạn mức số câu duy nhất (tổng ~5.000):
Nhóm	Ví dụ	Xử lý đúng	Số câu
CMD_EDGE	"Hạ kính xuống 50%."	Edge → JSON	1.800
INFO_EDGE	"Pin còn bao nhiêu?"	Edge	500
QA_CLOUD	"Mai Đà Nẵng có mưa không?"	Cloud	1.800
BOUNDARY	"Nóng quá.", "Bật điều hòa được không?"	Nhãn route mong đợi	600
Ngoài phạm vi / giá trị bất hợp lệ	"Chỉnh điều hòa 50 độ", câu về phanh/ga	Từ chối hoặc hỏi lại	300

Không intent nào vượt ~15% trong nhóm của nó, và mỗi intent có tối thiểu ~80 câu.

A3. Quy tắc an toàn khi mơ hồ. Câu mơ hồ mặc định không thực thi lệnh vật lý, chuyển Cloud hoặc hỏi lại. Nhãn nhóm BOUNDARY do 2 người gán độc lập, bất đồng thì giữ nhãn an toàn.
A4. Nhóm "ngoài phạm vi" chỉ để đo hành vi an toàn của router và FSM. FSM đảm bảo đúng định dạng, không đảm bảo giá trị hợp lệ, nên phải có bước kiểm dải giá trị riêng.
B. Quy tắc sinh câu
B1. Hai giai đoạn: khuôn rồi LLM diễn đạt lại. Khuôn (intent × slot × giá trị) đảm bảo phủ đủ và nhãn đúng. LLM viết lại để tăng đa dạng. Sinh theo lô nhỏ cho từng cặp (intent × phong cách) để LLM không lặp.
B2. Các trục biến thiên bắt buộc:
Mức lịch sự: "Bật giúp anh cái điều hòa" / "Bật điều hòa" / "điều hòa".
Dạng câu: mệnh lệnh, câu hỏi, than phiền gián tiếp.
Độ dài: 3–5, 6–12, 13–20 từ.
Khẩu ngữ: từ đệm, nói lửng, tự sửa ("mở kính... à không, đóng kính đi", nhãn theo ý định cuối).
B3. Phương ngữ ở cấp từ vựng, tách khỏi giọng mồi. Dùng bảng cặp từ (máy lạnh/điều hòa, kiếng/kính...). Khoảng 70% câu có từ vựng khớp miền giọng đọc, 30% chéo miền, vì người thật hay dùng lẫn.
B4. Bảng quy đổi số khẩu ngữ, mỗi biến thể có đúng một giá trị chuẩn. Ví dụ "hai mốt" → 21, "hai lăm" → 25, "một nửa" → 50%. Dạng đọc (text_spoken) là chữ, nhãn (text_gt) là chữ số.
B5. Không để dấu "?" thành đường tắt. Khoảng 20–30% câu hỏi tri thức không có "?", và có lệnh dạng hỏi có "?".
B6. Chống "giọng LLM sách vở". Đưa few-shot lấy từ cách nói thật (tin nhắn bạn bè, đoạn video bạn có). Tập test thật do người nói tự nghĩ câu, không dùng câu LLM.
B7. Loại trùng và giới hạn biến thể gần nhau. Loại trùng sau khi chuẩn hóa (chữ thường, bỏ dấu câu), loại câu gần trùng bằng độ tương đồng embedding, giữ tối đa ~5 biến thể mỗi khuôn.
B8. Soát tay tối thiểu 200 câu (khoảng 5%). Kiểm nhãn, độ tự nhiên, lặp. Lỗi vượt ngưỡng đã đặt thì sinh lại cả lô.
C. Quy tắc âm thanh
C1. Chia tập trước khi chạy TTS. Chia 80/10/10 theo khuôn (template_id), để mọi biến thể cùng nghĩa nằm cùng một tập. Giọng mồi của dev/test không xuất hiện trong train. Nhiễu và RIR của dev/test cũng không dùng trong train.
C2. Chọn giọng mồi. 40–60 giọng, cân bằng miền và giới tính, mỗi giọng không quá ~3% tổng số file.
C3. Bộ lọc. So sánh với dạng đọc, không so với nhãn chữ số. Sinh lại tối đa 3 lần. Báo cáo tỷ lệ qua lọc theo miền, intent và độ dài, và đặt mức tối thiểu sau lọc cho từng nhóm để không mất hết nhóm khó.
C4. Giả lập on-the-fly khi train. Mỗi lượt bốc ngẫu nhiên RIR, loại nhiễu, SNR. Cấm đổi cao độ (pitch shift) vì làm sai thanh điệu. Chỉ đổi tốc độ trong khoảng hẹp (ví dụ 0.9–1.1) và nghe kiểm.
C5. Bản cố định cho benchmark. Dev/test tổng hợp dùng seed cố định và lưu file, để bảng WER theo SNR lặp lại được.
D. Quy tắc quản lý
D1. Manifest (jsonl) kèm seed, phiên bản và số liệu thống kê cho mỗi lần sinh.
D2. Data card ghi rõ đây là dữ liệu tổng hợp, nguồn giọng mồi, phân phối, giới hạn đã biết.
D3. Cách ly dữ liệu thật. Giọng người thật trong tập test không được dùng làm giọng mồi cho train.
D4. Kiểm tra giấy phép từng nguồn (giọng mồi, nhiễu, RIR) trước khi dùng.