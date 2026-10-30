# -*- coding: utf-8 -*-
"""Mô hình ghim revision (tải trên nút đầu cụm A100 hoặc laptop). Đổi revision ở đây là đổi cho mọi bước."""



PINS = {
    "vieneu": ("pnnbao-ump/VieNeu-TTS-v3-Turbo", "61b85e3d937fbbacb387714180e8182823512523",
               ["config.json", "denoiser.onnx", "speaker_encoder.onnx", "update/*"]),
    "moss": ("OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano", "6aa02b01e445cc585582cf0ba480bc3ea6c8dd68", None),
    "PhoWhisper-medium": ("vinai/PhoWhisper-medium", "55a7e3eb6c906de891f8f06a107754427dd3be79", None),
    "PhoWhisper-large": ("vinai/PhoWhisper-large", "b9136a44b5f2ca664bd0b8f74baecf1715f6eeeb", None),
    # Mô hình ĐÍCH sẽ fine-tune (người dùng chọn 24/10/2026); main ngày 24/10/2026, giấy phép bsd-3-clause
    "PhoWhisper-small": ("vinai/PhoWhisper-small", "a86b604c346caf7148c37512eafe783a16420adb", None),
    "wav2vec2": ("nguyenvulebinh/wav2vec2-base-vietnamese-250h", "69e9000591623e5a4fc2f502407860bcdc0de0b2", None),
}

# Zipformer-30M (CC BY-NC-ND 4.0, chỉ đánh giá)
ZIPFORMER_REPO = "hynt/Zipformer-30M-RNNT-6000h"
ZIPFORMER_REV = "ad6f873b5f5b6ed083821253a88d81afed2505c4"     # commit main ngày 23/10/2026 (lastModified 2026-09-09)
