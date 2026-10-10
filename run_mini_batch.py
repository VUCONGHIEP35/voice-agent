import os
import subprocess
import time

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"🚀 Đang chạy: {script_name}")
    print(f"{'='*50}")
    
    # Sử dụng venv python
    python_exe = os.path.join("venv", "Scripts", "python.exe")
    script_path = os.path.join("src", "data_prep", script_name)
    
    start_time = time.time()
    result = subprocess.run([python_exe, script_path], capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ LỖI: {script_name} thất bại với mã lỗi {result.returncode}")
        exit(1)
        
    end_time = time.time()
    print(f"✅ Hoàn thành {script_name} trong {end_time - start_time:.1f} giây.\n")

if __name__ == "__main__":
    print("BẮT ĐẦU QUY TRÌNH TẠO DỮ LIỆU MINI-BATCH (PHA 1)")
    
    scripts = [
        "00_download_data.py", 
        "01_filter_snr.py", 
        "02_pairing.py", 
        "03_run_tts.py", 
        "04_merge_manifest.py"
    ]
    
    for script in scripts:
        run_script(script)
        
    print("\n🎉 XUẤT SẮC! Toàn bộ quy trình sinh Mini-batch đã hoàn tất.")
    print("Bạn có thể kiểm tra file kết quả tại: data/processed/manifest.jsonl")
    print("Tiếp theo, hãy chạy thử file 05_train_lora.py (đã được cấu hình an toàn cho máy bạn) để kiểm tra Dataloader.")
