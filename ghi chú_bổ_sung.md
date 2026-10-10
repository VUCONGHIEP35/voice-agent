### Các điểm cần lưu ý bổ sung thêm vào phần chuẩn bị cấu hình & chạy thử:

1. **Tối ưu Disk I/O (Rất quan trọng cho Dataloader):**
   - Đọc hàng ngàn file audio rời rạc (WAV, FLAC) trong một folder sẽ làm tắc nghẽn quá trình I/O của ổ cứng, GPU sẽ bị đói dữ liệu.
   - **Giải pháp:** Nên dùng định dạng **WebDataset** (đóng gói audio thành các file `.tar` lớn từ 1-2GB) để stream dữ liệu tuần tự. 
   - **Mẹo nhỏ:** Nếu lưu trữ file nguyên bản, nên ưu tiên dùng định dạng **WAV (uncompressed PCM 16-bit)** thay vì FLAC. Mặc dù WAV tốn nhiều dung lượng ổ cứng hơn nhưng lại đọc cực kỳ nhanh và giải phóng gánh nặng giải nén cho CPU.

2. **Tinh chỉnh num_workers cho DataLoader:**
   - Đừng mặc định đặt `num_workers` bằng với tổng số core CPU. Trong PyTorch, đặt quá nhiều worker có thể gây tràn RAM do hiện tượng nhân bản dữ liệu rác.
   - **Thực hành tốt nhất:** Bắt đầu với `num_workers = 2` hoặc `4`. Vừa chạy thử vài epoch vừa mở `htop` để theo dõi lượng RAM tiêu thụ, từ đó tăng dần để tìm được điểm cân bằng.

3. **Lựa chọn Mixed-Precision (fp16 vs bf16):**
   - Dòng lệnh của bạn nhắc đến mixed-precision. Nếu bạn dùng GPU đời mới (kiến trúc Ampere trở lên như dòng RTX 30xx, RTX 40xx, A10, A100), hãy ưu tiên dùng **bf16 (bfloat16)** thay vì `fp16`.
   - **Lý do:** fp16 rất dễ gặp lỗi tràn số dẫn đến Loss bị NaN khi huấn luyện các mô hình lớn dựa trên Transformer (như Whisper). Dải biểu diễn số của bf16 rộng ngang với fp32 nên an toàn hơn nhiều.
