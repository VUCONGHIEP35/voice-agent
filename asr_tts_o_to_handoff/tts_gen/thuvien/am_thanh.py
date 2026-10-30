# -*- coding: utf-8 -*-
"""Ghi âm thanh: FLAC PCM_16, ghi tệp tạm rồi đổi tên (không để tệp dở khi bị ngắt)."""
import os

import numpy as np
import soundfile as sf


def write_flac(path, w, sr):
    tmp = path + ".tmp.flac"
    sf.write(tmp, np.clip(w, -1.0, 1.0), sr, format="FLAC", subtype="PCM_16")
    os.replace(tmp, path)
