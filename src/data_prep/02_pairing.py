import os
import json
import random

def generate_mock_paraphrase(template):
    """
    Hàm sinh câu mock đơn giản từ template. 
    Trong thực tế, bạn sẽ dùng LLM để sinh paraphrase.
    """
    temp_val = random.randint(16, 30)
    artist_val = random.choice(["Sơn Tùng", "Mỹ Tâm", "Đen Vâu", "Hoàng Thuỳ Linh"])
    
    text_spoken = ""
    text_gt = ""
    target_json = template.get("json_target", {}).copy()
    
    group = template.get("group", template.get("intent"))
    
    if group == "CMD_EDGE":
        text_spoken = f"chỉnh điều hòa xuống {temp_val} độ"
        text_gt = f"Chỉnh điều hòa xuống {temp_val} độ."
        if "temp" in template.get("slot_schema", {}):
            target_json["temp"] = temp_val
    elif group == "INFO_EDGE":
        text_spoken = "pin xe còn bao nhiêu phần trăm"
        text_gt = "Pin xe còn bao nhiêu phần trăm?"
    elif group == "QA_CLOUD":
        text_spoken = "thời tiết hà nội hôm nay thế nào"
        text_gt = "Thời tiết Hà Nội hôm nay thế nào?"
        if "location" in template.get("slot_schema", {}):
            target_json["location"] = "Hà Nội"
    elif group == "BOUNDARY":
        text_spoken = "trong xe nóng quá"
        text_gt = "Trong xe nóng quá."
    elif group == "OUT_OF_SCOPE":
        text_spoken = f"chỉnh điều hòa lên {temp_val + 30} độ" # Invalid temp
        text_gt = f"Chỉnh điều hòa lên {temp_val + 30} độ."
    else:
        text_spoken = "thực hiện một lệnh mẫu"
        text_gt = "Thực hiện một lệnh mẫu."
        if "temp" in template.get("slot_schema", {}):
            target_json["temp"] = temp_val + 30
            
    return {
        "template_id": template["template_id"],
        "intent": template["intent"],
        "text_spoken": text_spoken,
        "text_gt": text_gt,
        "target_json": target_json
    }

def create_pairings(templates_path, voices_path, output_csv, num_samples=100):
    with open(templates_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    templates = []
    if isinstance(data, dict) and "templates" in data:
        for group, tmpl_list in data["templates"].items():
            templates.extend(tmpl_list)
    elif isinstance(data, list):
        templates = data
    else:
        print("Định dạng templates.json không hợp lệ!")
        return
        
    with open(voices_path, 'r', encoding='utf-8') as f:
        voices_meta = json.load(f)
        
    voice_ids = list(voices_meta.keys())
    if not voice_ids:
        print("Chưa có giọng mồi nào được lọc! Hãy chạy 01_filter_snr.py trước.")
        return
        
    # CHIA SPLIT CHO TEMPLATE VÀ GIỌNG (Rule C1: dev/test không xuất hiện trong train)
    random.shuffle(templates)
    random.shuffle(voice_ids)
    
    num_templates = len(templates)
    num_voices = len(voice_ids)
    
    t_train_idx = max(1, int(0.8 * num_templates))
    t_dev_idx = max(t_train_idx + 1, int(0.9 * num_templates))
    
    train_templates = templates[:t_train_idx]
    dev_templates = templates[t_train_idx:t_dev_idx]
    test_templates = templates[t_dev_idx:] if t_dev_idx < num_templates else templates[-1:]
    
    v_train_idx = max(1, int(0.8 * num_voices))
    v_dev_idx = max(v_train_idx + 1, int(0.9 * num_voices))
    
    train_voices = voice_ids[:v_train_idx]
    dev_voices = voice_ids[v_train_idx:v_dev_idx]
    test_voices = voice_ids[v_dev_idx:] if v_dev_idx < num_voices else voice_ids[-1:]
    
    splits = [
        {"templates": train_templates, "voices": train_voices, "split": "train"},
        {"templates": dev_templates, "voices": dev_voices, "split": "dev"},
        {"templates": test_templates, "voices": test_voices, "split": "test"}
    ]
    
    max_per_voice = max(1, int(num_samples * 0.03))
    voice_usage = {v: 0 for v in voice_ids}
    
    pairings = []
    used_pairs = set() # Track (template_id, voice_id)
    
    print(f"Đang sinh {num_samples} câu và ghép cặp theo chuẩn chia tập 80/10/10...")
    
    samples_per_split = {
        "train": int(num_samples * 0.8),
        "dev": int(num_samples * 0.1),
        "test": num_samples - int(num_samples * 0.8) - int(num_samples * 0.1)
    }
    
    for split_data in splits:
        split_name = split_data["split"]
        s_templates = split_data["templates"]
        s_voices = split_data["voices"]
        s_num = samples_per_split[split_name]
        
        if not s_templates or not s_voices:
            continue
            
        for _ in range(s_num):
            template = random.choice(s_templates)
            sample = generate_mock_paraphrase(template)
            
            valid_voices = [
                v for v in s_voices 
                if voice_usage.get(v, 0) < max_per_voice 
                and (template["template_id"], v) not in used_pairs
            ]
            
            if not valid_voices:
                valid_voices = [v for v in s_voices if (template["template_id"], v) not in used_pairs]
                if not valid_voices:
                    valid_voices = s_voices # Fallback
                    
            chosen_voice = random.choice(valid_voices)
            
            voice_usage[chosen_voice] = voice_usage.get(chosen_voice, 0) + 1
            used_pairs.add((template["template_id"], chosen_voice))
            
            speaker_id = voices_meta[chosen_voice]["speaker_id"]
            pairings.append({
                "id": f"syn_{split_name}_{len(pairings):04d}",
                "template_id": template["template_id"],
                "voice_file": chosen_voice,
                "speaker_id": speaker_id,
                "text_spoken": sample["text_spoken"],
                "text_gt": sample["text_gt"],
                "intent": sample["intent"],
                "target_json": json.dumps(sample["target_json"], ensure_ascii=False),
                "split": split_name
            })
            
    import csv
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        if pairings:
            writer = csv.DictWriter(f, fieldnames=pairings[0].keys())
            writer.writeheader()
            writer.writerows(pairings)
            
    print(f"Đã ghép cặp thành công {len(pairings)} câu! Lưu tại {output_csv}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    templates_path = os.path.join(project_root, "src", "config", "templates.json")
    voices_path = os.path.join(project_root, "data", "processed", "voices_ref", "filtered_transcripts.json")
    output_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "pairings.csv")
    
    create_pairings(templates_path, voices_path, output_csv, num_samples=100)
