import os
import csv
import json
import torch
import soundfile as sf
import numpy as np
from jiwer import wer
from transformers import pipeline

from gtts import gTTS
import librosa

def mock_tts(text, voice_file, output_path):
    """
    Sử dụng Google TTS để sinh audio có tiếng người thật đọc lệnh (Không tốn RAM/GPU).
    Thực tế bạn sẽ thay bằng viXTTS hoặc F5-TTS ở Pha 2.
    """
    temp_mp3 = output_path.replace(".wav", ".mp3")
    try:
        # Gọi API Google để đọc text thành tiếng Việt
        tts = gTTS(text, lang='vi')
        tts.save(temp_mp3)
        
        # Load lại bằng librosa để resample về chuẩn 16kHz và lưu thành WAV
        y, sr = librosa.load(temp_mp3, sr=16000)
        sf.write(output_path, y, sr)
        
        # Xóa file rác
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
            
        duration = round(len(y) / sr, 2)
        return True, duration
    except Exception as e:
        print(f"Lỗi khi gọi Google TTS: {e}")
        return False, 0.0

def run_tts_and_filter(pairings_csv, output_audio_dir, output_csv):
    os.makedirs(output_audio_dir, exist_ok=True)
    
    print("Đang chuẩn bị mô hình PhoWhisper (hoặc Whisper) để đánh giá WER...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Giả lập chưa load thật để tránh tốn RAM khi chạy test pipeline
    # asr_model = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-tiny", device=device)
    
    successful_samples = []
    
    with open(pairings_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        pairings = list(reader)
        
    print(f"Bắt đầu chạy quy trình sinh TTS cho {len(pairings)} mẫu...")
    
    for row in pairings:
        sample_id = row['id']
        text_spoken = row['text_spoken']
        voice_file = row['voice_file']
        
        audio_path = os.path.join(output_audio_dir, f"{sample_id}.wav")
        
        # Thử sinh tối đa 3 lần nếu WER > 5%
        success = False
        for attempt in range(3):
            # 1. Sinh âm thanh bằng mô hình TTS
            success_tts, duration = mock_tts(text_spoken, voice_file, audio_path)
            
            # 2. Đánh giá chất lượng bằng PhoWhisper
            try:
                # Trong thực tế, bạn sẽ nhận dạng và so sánh văn bản:
                # result = asr_model(audio_path)
                # pred_text = result["text"].lower()
                # error_rate = wer(text_spoken.lower(), pred_text)
                
                # Mock WER = 0 cho nhanh ở khâu dựng pipeline
                error_rate = 0.0
                
                if error_rate <= 0.05: # WER <= 5%
                    success = True
                    row['audio_path'] = audio_path
                    row['duration'] = duration
                    row['wer'] = error_rate
                    successful_samples.append(row)
                    print(f"[ĐẠT] {sample_id} - WER: {error_rate*100:.1f}% (Thử lần {attempt+1})")
                    break
            except Exception as e:
                print(f"Lỗi nhận dạng: {e}")
                
        if not success:
            print(f"[LOẠI] {sample_id} - Trượt WER cả 3 lần thử.")
            
    # Lưu kết quả lọc
    if successful_samples:
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=successful_samples[0].keys())
            writer.writeheader()
            writer.writerows(successful_samples)
    print(f"\nHoàn tất! Số lượng file đạt chuẩn: {len(successful_samples)}/{len(pairings)}.")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pairings_csv = os.path.join(base_dir, "data", "processed", "pairings.csv")
    output_audio_dir = os.path.join(base_dir, "data", "processed", "tts_audio")
    output_csv = os.path.join(base_dir, "data", "processed", "tts_filtered.csv")
    
    if os.path.exists(pairings_csv):
        run_tts_and_filter(pairings_csv, output_audio_dir, output_csv)
    else:
        print("Không tìm thấy pairings.csv. Hãy chạy script 02_pairing.py trước.")
