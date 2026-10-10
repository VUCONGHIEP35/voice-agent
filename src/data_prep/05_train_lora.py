import os
import torch
from datasets import load_dataset
from transformers import (
    WhisperForConditionalGeneration, 
    WhisperProcessor, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def train_lora_whisper(manifest_path, output_dir):
    if not os.path.exists(manifest_path):
        print("Không tìm thấy manifest.jsonl. Hãy chạy 04_merge_manifest.py trước.")
        return
        
    print("1. Đang tải dữ liệu từ Manifest JSONL...")
    dataset = load_dataset("json", data_files=manifest_path, split="train")
    
    from datasets import Audio
    from dataclasses import dataclass
    from typing import Any, Dict, List, Union

    # Bổ sung tính năng tự động tải và resample audio từ filepath
    dataset = dataset.cast_column("audio_filepath", Audio(sampling_rate=16000))

    # Lọc dataset theo Split đã gán ở bước 04
    train_dataset = dataset.filter(lambda x: x["split"] == "train")
    dev_dataset = dataset.filter(lambda x: x["split"] == "dev")
    print(f"Tổng số mẫu: Train ({len(train_dataset)}), Dev ({len(dev_dataset)})")
    
    model_name_or_path = "openai/whisper-small"
    print(f"2. Khởi tạo mô hình {model_name_or_path}...")
    processor = WhisperProcessor.from_pretrained(model_name_or_path, language="vi", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(model_name_or_path)
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []
    
    # Hàm map tiền xử lý
    def prepare_dataset(batch):
        audio = batch["audio_filepath"] # Đã được load thành object dict {array, sampling_rate}
        batch["input_features"] = processor.feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
        batch["labels"] = processor.tokenizer(batch["text_gt"]).input_ids
        return batch

    print("Đang tiền xử lý (Extract Features & Tokenize)...")
    train_dataset = train_dataset.map(prepare_dataset, remove_columns=dataset.column_names, num_proc=1)
    dev_dataset = dev_dataset.map(prepare_dataset, remove_columns=dataset.column_names, num_proc=1)

    print("3. Cấu hình kẹp LoRA (PEFT)...")
    config = LoraConfig(
        r=8, 
        lora_alpha=16, 
        target_modules=["q_proj", "v_proj"], # Các lớp Attention của Whisper
        lora_dropout=0.05,
        bias="none"
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    
    @dataclass
    class DataCollatorSpeechSeq2SeqWithPadding:
        processor: Any
        def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
            input_features = [{"input_features": feature["input_features"]} for feature in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
            label_features = [{"input_ids": feature["labels"]} for feature in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
            if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
                labels = labels[:, 1:]
            batch["labels"] = labels
            return batch
            
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    print("4. Thiết lập tham số huấn luyện (Dựa trên cấu hình máy hiện tại)...")
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2, 
        gradient_accumulation_steps=4, 
        dataloader_num_workers=4,
        learning_rate=1e-4,
        num_train_epochs=1, 
        fp16=False,
        bf16=False,
        use_cpu=True if not torch.cuda.is_available() else False,
        logging_steps=5,
        evaluation_strategy="steps",
        eval_steps=10,
        save_steps=10,
        remove_unused_columns=False,
    )
    
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        data_collator=data_collator
    )
    
    print("\n[MÔ PHỎNG] Mã huấn luyện đã sẵn sàng! Bắt đầu chạy Sanity Check...")
    trainer.train()
    
if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = os.path.join(base_dir, "data", "processed", "manifest.jsonl")
    output_dir = os.path.join(base_dir, "models", "whisper_lora_vi")
    
    train_lora_whisper(manifest_path, output_dir)
