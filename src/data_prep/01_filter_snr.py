import os
import json
import shutil
import librosa
import numpy as np

# Giả lập hoặc import pysepm nếu có
try:
    import pysepm
    HAS_PYSEPM = True
except ImportError:
    HAS_PYSEPM = False
    print("Thư viện pysepm chưa được cài đặt. Dùng phương pháp ước tính SNR bằng librosa thay thế.")

def estimate_snr_fallback(audio_path):
    """
    Hàm fallback ước tính SNR (Signal-to-Noise Ratio) đơn giản nếu không có pysepm.
    Cách này chỉ dùng mức năng lượng của tín hiệu và phần nhiễu (dựa trên các đoạn im lặng).
    """
    y, sr = librosa.load(audio_path, sr=None)
    # Lấy envelope của năng lượng
    rms = librosa.feature.rms(y=y)[0]
    
    # Coi 10% âm thanh nhỏ nhất là nhiễu, 10% lớn nhất là tín hiệu
    noise_est = np.percentile(rms, 10)
    signal_est = np.percentile(rms, 90)
    
    if noise_est == 0:
        return 50.0 # SNR rất cao nếu không có tiếng ồn nền
        
    snr = 20 * np.log10(signal_est / noise_est)
    return snr

def filter_good_voices(raw_dir, output_dir, snr_threshold=25.0):
    os.makedirs(output_dir, exist_ok=True)
    transcript_path = os.path.join(raw_dir, "ref_transcripts.json")
    
    if not os.path.exists(transcript_path):
        print(f"Không tìm thấy file {transcript_path}. Hãy chạy 00_download_data.py trước.")
        return
        
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcripts = json.load(f)
        
    good_transcripts = {}
    print(f"Bắt đầu lọc audio có SNR > {snr_threshold}dB...")
    
    for filename, meta in transcripts.items():
        audio_path = os.path.join(raw_dir, filename)
        if not os.path.exists(audio_path):
            continue
            
        if HAS_PYSEPM:
            snr_value = estimate_snr_fallback(audio_path)
        else:
            snr_value = estimate_snr_fallback(audio_path)
            
        if snr_value > snr_threshold:
            print(f"[ĐẠT] {filename} - SNR: {snr_value:.2f}dB")
            good_transcripts[filename] = meta
            shutil.copy2(audio_path, os.path.join(output_dir, filename))
        else:
            print(f"[LOẠI] {filename} - SNR: {snr_value:.2f}dB")
            
    # Lưu lại transcript của các file đã lọc
    out_transcript_path = os.path.join(output_dir, "filtered_transcripts.json")
    with open(out_transcript_path, 'w', encoding='utf-8') as f:
        json.dump(good_transcripts, f, ensure_ascii=False, indent=4)
        
    print(f"Đã lọc thành công {len(good_transcripts)}/{len(transcripts)} file. Lưu tại {output_dir}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_dir = os.path.join(project_root, "data", "raw", "vivos")
    output_dir = os.path.join(project_root, "data", "processed", "voices_ref")
    
    filter_good_voices(raw_dir, output_dir, snr_threshold=25.0) # Đặt 25dB theo đúng chuẩn của tài liệu
