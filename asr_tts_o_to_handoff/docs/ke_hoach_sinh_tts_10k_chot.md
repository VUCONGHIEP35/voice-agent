# Kế hoạch sinh TTS 10.000 câu (bản chốt, 25/10/2026)

Bản này thay phần kỹ thuật của `Kế hoạch sinh 10.000 mẫu TTS bằng VieNeu v3 Turbo.md`. Tệp gốc của người dùng giữ nguyên, không sửa.

Mỗi mục ghi rõ là **đã chốt** (người dùng quyết hoặc đã đo xong), **mặc định** (dùng nếu không ai đổi), hay **chờ quyết**.

## 1. Đã chốt

| Hạng mục | Chốt | Căn cứ |
|---|---|---|
| Mô hình TTS | VieNeu v3 Turbo, `vieneu==3.8.3`, trọng số bản `61b85e3d`, MOSS bản `6aa02b01`, bf16, lô 16, temperature 0,8, top_k 25 | pilot100, eval1000 A và B |
| Giọng | 24 giọng có sẵn của VieNeu, **không dùng Minh Triết**, không clone giọng, không lấy giọng từ YouTube | yêu cầu người dùng |
| Cách đọc từ ngoại | `lexicon/doc_tu_ngoai_tts.tsv` (người dùng duyệt 20/10); câu nào dùng thì thêm trường `tts_text` | — |
| Máy chạy | Cụm A100 HUST (`user04`, Slurm, tối đa 2 job). Môi trường dựng sẵn ở `~/asr_tts_o_to/`; script trong `tts_gen/server/` | setup 24/10, phần B chạy 13 phút |
| Kiểm kỹ thuật | `tts_checks` (cắt đầu, nói lan man, đọc thiếu); sinh lại tối đa 2 lần; đổi giọng 1 vòng; `check_run` | eval1000: sinh lại 4,6–4,8%, sau đổi giọng còn 0 lỗi |
| ASR chấm | Lõi: L (PhoWhisper-large CT2) và M (PhoWhisper-medium). Nguồn phụ: Z (Zipformer-30M) và c3 (wav2vec2). **Bỏ** c1 và c2 | c1, c2 tốn 12 phút mà chỉ thêm 0–1 câu |
| Mô hình đích | **PhoWhisper-small**. Chạy zero-shot làm cấu hình T, **chỉ đo, không dùng để lọc** | người dùng chọn 24/10 |
| Từ đệm | **Không có từ đệm ở đầu câu** ("ờ", "ê", "nè", "nì", "này" đứng một mình). Nhãn ASR không chép từ đệm; khi chấm, bỏ ở cả đáp án lẫn câu máy nghe ra | người dùng; 0/127 lệnh `seen` có từ đệm; Oviatt 1995 |
| Văn bản đầu vào | **v3.1** (`data/m1m2_10k_v31/`, `gen10k/make_v31.py`): v3 bỏ mọi từ đệm, tiếng gọi và lời gọi trợ lý trong văn bản. 228 câu trùng và 135 câu gần trùng sau khi bỏ được thay bằng 363 câu bù từ bộ sinh chạy seed khác. Kết quả: 10.000 câu, `validate10k` 0 lỗi, 0 cảnh báo | người dùng 25/10 |
| Từ đánh thức | **Không nằm trong văn bản.** Thêm bằng cách **ghép âm thanh**: cụm đánh thức sinh riêng + câu lệnh M1 đã sinh, cùng giọng. Danh sách: "Trợ lý ơi", "Hây trợ lý" (nhãn ghi "hây"). Nhãn **theo từng âm tiết**: âm tiết còn trọn thì ghi, âm tiết bị cắt dở thì bỏ | người dùng 25/10 (câu 3b, 5, 6) |
| Lưu trữ | Âm thanh 48 kHz FLAC (gốc) và 16 kHz (cho ASR). Không lưu bản đã trộn nhiễu (nhiễu và vang cộng khi huấn luyện). Không đẩy dữ liệu lên git | kế hoạch gốc |

## 2. Mặc định (đổi được)

1. **Dữ liệu ghép từ đánh thức** (`tts_gen/make_wake_aug.py`, sẽ viết):
   - chiếm **12% số câu lệnh M1** đã qua chấm, không áp cho câu M2;
   - chia **40% đủ cụm, 60% chỉ còn đuôi**, vì đuôi có nhiều vị trí cắt khác nhau nên cần nhiều mẫu hơn;
   - mỗi giọng × mỗi cụm sinh 3 bản với seed khác nhau; cụm đánh thức cũng qua kiểm `tts_checks`;
   - căn hàng âm tiết bằng CTC để cắt đuôi đúng ranh giới âm tiết (hoặc cắt dở có chủ ý, âm tiết dở thì bỏ khỏi nhãn);
   - cân mức âm lượng giữa hai đoạn; khoảng lặng ngẫu nhiên 0–300 ms; làm mờ 10 ms ở chỗ cắt và chỗ nối;
   - mỗi câu ghép có trường `parent_utt_id`; câu gốc và câu ghép luôn nằm **cùng tập** khi chia train/dev/test.
2. **Bộ kiểm có từ đánh thức**: thêm hai điều kiện "đủ cụm" và "chỉ còn đuôi", so WER với câu lệnh đứng một mình. Thêm một phần giọng thật: phiếu thu âm có câu đọc kèm từ đánh thức.
3. **Thái Sơn**: chạy với `--no-ref-codes`. Nếu thí nghiệm ở mục 4.3 vẫn còn cắt đầu trên 20% thì bỏ hẳn giọng này.
4. **Giọng đọc nhanh** (Thùy Dung, Thanh Bình, Hải Đăng, 5,5–5,7 âm tiết/giây): mỗi giọng nhận khoảng một nửa số câu của giọng thường. Không kéo giãn âm thanh.
5. **Thêm 0,25 s im lặng ở đầu tệp** khi đóng gói: hiện trung vị chỉ 0,12 s, và 31% số câu dưới 0,10 s.
6. **Luật chấm mới** (ngưỡng vẫn tạm 0,10):
   - dat: L và M cùng đạt;
   - Z chỉ được tính khi c3 cũng đạt, hoặc khi CER của Z ≤ 0,05;
   - thêm kiểm theo từ: không mất hoặc thay từ nội dung nào (ngoài các biến thể trong từ điển);
   - câu L, M, Z nghe từ đầu khác nhau thì thành can_nghe.

## 3. Đã quyết sau đó (25/10) và còn chờ

1. **Giọng Trung: giữ nguyên 2 giọng** (Ngọc Trân, Quang Sơn), chia câu như các giọng khác. Kết quả chấm của giọng Trung báo riêng (khoảng 33% dat ở eval1000).
2. **Tiểu từ Huế: đã thay trong v3.1.** "hí"/"nở" ở câu lệnh đổi thành "nghe" hoặc bỏ; "hí"/"hớ" ở câu hỏi đổi thành "rứa" hoặc bỏ. Bộ sinh đã sửa theo. Mọi câu Huế vẫn ở trạng thái "cần duyệt".
3. **Còn chờ — nhóm dat_1nguon** có đưa vào huấn luyện không: quyết sau khi nghe xong `runs/nghe_thu_tu_dau.xlsx`, áp luật chấm mới ở mục 2.6 rồi xem lại.

## 4. Các bước

| Bước | Việc | Ở đâu | Kiểm |
|---|---|---|---|
| 1 | v3.1: bỏ từ đệm, lời gọi; thay tiểu từ Huế — **XONG 25/10** | laptop | `test_vnnum` OK; `validate10k` 0 lỗi, 0 cảnh báo; gần trùng ≥ 0,9: 8 câu (v3 là 0), không cặp nào ≥ 0,95 |
| 1b | Ghép từ đánh thức (mục 2.1) — **XONG 25/10**: 1.002 câu | A100 + laptop | nhãn khớp số âm tiết còn lại; còn phải nghe 20 câu ghép |
| 5* | Sinh và chấm 10.000 câu — **XONG 25/10**, khoảng 2 giờ 10 phút máy (xem trạng thái trong CLAUDE.md) | A100 | 10.000/10.000, check_run đạt cả 10 phần |
| 2 | Luật chấm mới (mục 2.6) và bỏ từ đệm khi chấm, có test | laptop | chấm lại 1.000 câu; so với 2 phiếu nghe; luật mới không được để lọt nhiều câu "Sai" hơn |
| 3 | Thí nghiệm khoảng 200 câu: Thái Sơn với `--no-ref-codes`; lời gọi trợ lý có/không dấu phẩy | A100, khoảng 5 phút | tỷ lệ cắt đầu, lỗi từ đầu của L/M/Z/T, nghe một mẫu |
| 4 | Gán giọng cho 10.000 câu: mở rộng `select_eval1000.py` (cân vùng và giới, tỷ trọng giọng theo mục 2.3–2.4, câu Huế ưu tiên giọng Trung) → 10 phần × 1.000 câu | laptop | mỗi phần cân vùng; không có Minh Triết; `tts_text` đủ |
| 5 | Sinh và chấm 10 phần bằng `chay_eval.sbatch` (thêm `SHARD=p01..p10`), chạy 1 job một lúc. Ước khoảng 20–25 phút mỗi phần, tổng khoảng 3,5–4 giờ GPU (chưa đo) | A100 | `check_run` từng phần; tỷ lệ dat theo vùng phải nằm trong khoảng Wilson của eval1000 |
| 6 | Đóng gói: manifest hợp nhất (mục 10 của tài liệu quy trình: `layer=L2_synthetic`, `source=tts`, `voice_id`, `template_id`, kết quả chấm, `review_status`), audio48 + audio16, sha256 → tải về laptop | A100 → laptop | sha256 khớp; đủ 10.000 sample_id |
| 7 | Nghe kiểm: lấy mẫu phân tầng theo vùng, giọng, kết quả chấm | laptop | ghi tỷ lệ Đúng theo nhóm; chốt ngưỡng thay cho mốc tạm 0,10 |

## 5. Điểm dừng

- Mất hoặc trùng câu; `tts_text` không được dùng; quá 25% số câu phải sinh lại.
- Tỷ lệ dat của một phần lệch ra ngoài khoảng Wilson của eval1000.
- sha256 của mô hình hoặc của gói lệch; phiên bản thư viện khác bản ghim.
- Job chờ quá 24 giờ.
- Bước ASR báo rc=0 nhưng thiếu tệp kết quả (đã có kiểm `need` trong sbatch).

## 6. Không làm trong kế hoạch này

- Sinh thêm câu, hay viết lại câu bằng LLM.
- Clone giọng.
- Huấn luyện PhoWhisper-small. Phần đó có kế hoạch riêng: chia tập theo `template_id` và giọng, tăng cường dữ liệu, bộ test thật giữ riêng.
