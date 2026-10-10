import os
import csv
import json
import random

def merge_manifests(tts_csv, output_manifest):
    manifest_data = []
    
    if not os.path.exists(tts_csv):
        print("Không tìm thấy tts_filtered.csv. Hãy chạy 03_run_tts.py trước.")
        return
        
    print(f"Đang đọc dữ liệu từ {tts_csv}...")
    with open(tts_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 1. Lấy thông tin split đã được phân bổ chặt chẽ từ bước 02_pairing.py
            split = row.get("split", "train")
                
            # 2. Xây dựng object theo đúng chuẩn schema manifest Lớp 2 đã tối ưu
            manifest_item = {
                "id": row["id"],
                "audio_filepath": row["audio_path"],
                "duration": float(row.get("duration", 0.0)),
                "layer": "L2_synthetic",
                "source": "tts",
                "template_id": row["template_id"],
                "text_spoken": row["text_spoken"],
                "text_gt": row["text_gt"],
                "intent": row["intent"],
                "target_json": json.loads(row["target_json"]),
                "voice_id": row["speaker_id"],
                "voice_region": "Unknown", # Thông tin này có thể map từ metadata giọng thật
                "snr_db": random.choice([10, 15, 20, 25]) if split == "train" else 15, # Cố định snr cho dev/test
                "rir_id": "none",
                "split": split
            }
            manifest_data.append(manifest_item)
            
    # 3. Ở giai đoạn thật, bạn sẽ append thêm phần tử Lớp 1 (PhoASR) và Lớp 3 (Giọng thật) vào đây.
    
    # Lưu ra định dạng chuẩn JSONL
    with open(output_manifest, 'w', encoding='utf-8') as f:
        for item in manifest_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Hoàn thành! Đã tạo manifest hợp nhất với {len(manifest_data)} dòng tại: {output_manifest}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    tts_csv = os.path.join(base_dir, "data", "processed", "tts_filtered.csv")
    output_manifest = os.path.join(base_dir, "data", "processed", "manifest.jsonl")
    
    merge_manifests(tts_csv, output_manifest)
