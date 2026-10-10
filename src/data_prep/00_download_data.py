import os
import json
import soundfile as sf
from datasets import load_dataset
from tqdm import tqdm

def download_vivos_sample(output_dir, sample_size=50):
    """
    Tải một lượng nhỏ dữ liệu VIVOS từ Hugging Face để làm dữ liệu mồi cho Mini-batch.
    """
    print(f"Đang tải {sample_size} mẫu từ VIVOS dataset...")
    
    # Tạo thư mục nếu chưa có
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset VIVOS (chỉ lấy tập train cho mẫu bằng streaming để không tải toàn bộ)
    try:
        dataset = load_dataset("AILAB-VNUHCM/vivos", split="train", streaming=True, trust_remote_code=True)
    except Exception as e:
        print(f"Lỗi khi tải dataset VIVOS: {e}. Vui lòng kiểm tra lại kết nối mạng hoặc thử lại sau.")
        return

    transcripts = {}
    
    print(f"Đang trích xuất và lưu vào {output_dir}...")
    for i, item in enumerate(tqdm(dataset, total=sample_size)):
        if i >= sample_size:
            break
            
        audio_array = item['audio']['array']
        sample_rate = item['audio']['sampling_rate']
        speaker_id = item['speaker_id']
        sentence = item['sentence']
        
        # Định dạng tên file: speakerId_index.wav
        filename = f"{speaker_id}_{i:03d}.wav"
        filepath = os.path.join(output_dir, filename)
        
        # Lưu file audio
        sf.write(filepath, audio_array, sample_rate)
        
        # Lưu transcript
        transcripts[filename] = {
            "speaker_id": speaker_id,
            "text": sentence
        }
        
    # Lưu file JSON chứa transcript
    transcript_path = os.path.join(output_dir, "ref_transcripts.json")
    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=4)
        
    print(f"Đã lưu {sample_size} file audio và {transcript_path} thành công!")

if __name__ == "__main__":
    # Đường dẫn thư mục output tính từ root của project
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_dir = os.path.join(project_root, "data", "raw", "vivos")
    
    download_vivos_sample(output_dir, sample_size=50)
