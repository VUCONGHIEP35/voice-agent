import os
import time
import psutil

try:
    import torch
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("Cảnh báo: Chưa cài đặt thư viện PyTorch (torch). Một số bài test liên quan đến GPU/VRAM sẽ bị bỏ qua.")

# 1. Đánh giá cấu hình tĩnh (CPU, RAM, GPU)
def print_system_info():
    print("="*60)
    print(" BÁO CÁO CẤU HÌNH PHẦN CỨNG MÁY CHỦ/LOCAL ")
    print("="*60)
    
    # CPU & RAM
    print(f"[CPU] Số Core Vật lý: {psutil.cpu_count(logical=False)} Cores")
    print(f"[CPU] Số Core Logic (Luồng): {psutil.cpu_count(logical=True)} Threads")
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"[RAM] Tổng bộ nhớ RAM: {ram_gb:.1f} GB")
    print(f"[RAM] RAM đang trống: {(psutil.virtual_memory().available / (1024**3)):.1f} GB")
    
    # GPU
    if HAS_TORCH and torch.cuda.is_available():
        print(f"[GPU] CUDA Available: True (Đang nhận {torch.cuda.device_count()} GPU)")
        for i in range(torch.cuda.device_count()):
            prop = torch.cuda.get_device_properties(i)
            vram_gb = prop.total_memory / (1024**3)
            print(f"  - GPU {i}: {prop.name} | Tổng VRAM: {vram_gb:.1f} GB")
        print(f"[SYS] Phiên bản PyTorch: {torch.__version__} | Phiên bản CUDA: {torch.version.cuda}")
    else:
        print("[GPU] CUDA Available: False (Hệ thống sẽ dùng CPU để xử lý tensor)")
    print("="*60)

# =========================================================================
# Lớp Dữ liệu mô phỏng để test I/O Dataloader
# (Để tránh lỗi đa luồng trên Windows, class này phải để ngoài hàm)
# =========================================================================
if HAS_TORCH:
    class DummyAudioDataset(Dataset):
        def __init__(self, num_samples=1000):
            self.num_samples = num_samples
            self.audio_shape = (16000,) # Giả lập audio 1 giây, 16000Hz
            
        def __len__(self):
            return self.num_samples
            
        def __getitem__(self, idx):
            # Giả lập độ trễ I/O (đọc file từ ổ đĩa)
            time.sleep(0.001) 
            # Giả lập dữ liệu và nhãn
            data = torch.randn(self.audio_shape)
            label = torch.randint(0, 10, (1,))
            return data, label

# 2. Đánh giá tốc độ Disk I/O & DataLoader (num_workers)
def benchmark_dataloader():
    if not HAS_TORCH:
        return
        
    print("\n[BENCHMARK] Đang test tốc độ DataLoader với các mức num_workers khác nhau...")
    print("Mục đích: Tìm ra số luồng (workers) tối ưu để không bị nghẽn (bottleneck) lúc load audio.")
    
    dataset = DummyAudioDataset(num_samples=2000)
    batch_size = 32
    
    # Thử nghiệm với các worker phổ biến
    workers_to_test = [0, 2, 4, 8]
    
    for w in workers_to_test:
        loader = DataLoader(dataset, batch_size=batch_size, num_workers=w, shuffle=True)
        start = time.time()
        for _ in loader:
            pass # Chỉ mô phỏng đọc/nạp data vào RAM, không train
        end = time.time()
        fps = 2000 / (end - start)
        print(f" => num_workers = {w}: Xử lý {fps:.1f} mẫu/giây (Tốn {end-start:.2f} giây)")
        
# 3. Đánh giá Peak VRAM (Chạy mini-batch test)
def benchmark_vram():
    if not (HAS_TORCH and torch.cuda.is_available()):
        return
        
    print("\n[BENCHMARK] Đo lường VRAM tiêu thụ lớn nhất (Peak VRAM) khi chạy mô hình giả lập...")
    print("Mục đích: Đảm bảo khi set batch_size, VRAM thực tế đỉnh (peak) không vượt ngưỡng OOM.")
    
    # Tạo mô hình MLP đơn giản chiếm chút bộ nhớ
    model = torch.nn.Sequential(
        torch.nn.Linear(16000, 2048),
        torch.nn.ReLU(),
        torch.nn.Linear(2048, 2048),
        torch.nn.ReLU(),
        torch.nn.Linear(2048, 10)
    ).cuda()
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()
    
    batch_size = 128
    print(f"Đang chạy Mini-batch (batch_size={batch_size})...")
    
    # Reset tracking VRAM
    torch.cuda.reset_peak_memory_stats()
    
    # Train thử vài step để kiểm tra (Sanity Check)
    for step in range(5): 
        inputs = torch.randn(batch_size, 16000).cuda()
        labels = torch.randint(0, 10, (batch_size,)).cuda()
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        print(f" - Step {step}: Loss = {loss.item():.4f} (Đang hội tụ bình thường)")
            
    peak_mb = torch.cuda.max_memory_allocated() / (1024**2)
    print(f"\n[KẾT QUẢ] Peak VRAM Usage: {peak_mb:.1f} MB (Đây là dung lượng cao nhất thực tế bị cấp phát)")

if __name__ == "__main__":
    print_system_info()
    
    # Chặn lỗi đa luồng DataLoader đặc thù trên Windows
    try:
        benchmark_dataloader()
    except Exception as e:
        print(f"Lỗi DataLoader: {e}")
        
    benchmark_vram()
    print("\nHoàn tất script đánh giá cấu hình!")
