# -*- coding: utf-8 -*-
"""Tải mô hình đúng revision đã ghim vào <out>/<khóa>/ (chạy trên NÚT ĐẦU, có mạng; như ô 5 của notebook Colab).

Chạy:  venv_tts/bin/python tai_mo_hinh.py --out ~/asr_tts_o_to/hf_pinned
Mỗi thư mục có tệp .rev = revision; đã đúng revision thì bỏ qua. Ghi <out>/pins.json (repo, revision, giấy phép, tệp).
"""
import argparse
import json
import os

from cauhinh.mo_hinh import PINS  # noqa: E402  (ghim revision ở cauhinh/mo_hinh.py)
IGNORE = ["*.msgpack", "*.h5", "*.ot", "flax_model*", "tf_model*", "onnx/*", "onnx_int8/*", "onnx_update/*", "gguf/*"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from huggingface_hub import HfApi, snapshot_download
    api = HfApi()
    info = {}
    for key, (repo, rev, allow) in PINS.items():
        d = os.path.join(a.out, key)
        names = api.list_repo_files(repo, revision=rev)
        card = api.model_info(repo, revision=rev).card_data
        lic = getattr(card, "license", None) if card else None
        info[key] = dict(repo=repo, revision=rev, license=lic)
        if os.path.exists(os.path.join(d, ".rev")) and open(os.path.join(d, ".rev")).read() == rev:
            print("Đã có", key, rev[:8])
            continue
        ign = list(IGNORE)
        if key == "PhoWhisper-large":
            ign += ["*.safetensors"]          # CT2 chuyển từ pytorch_model.bin như laptop/Colab
        elif any(n.endswith(".safetensors") for n in names):
            ign += ["*.bin"]
        snapshot_download(repo, revision=rev, local_dir=d, allow_patterns=allow, ignore_patterns=ign)
        open(os.path.join(d, ".rev"), "w").write(rev)
        print("Tải", repo, rev[:8], "->", d)
    for key in info:
        d = os.path.join(a.out, key)
        info[key]["files"] = sorted(os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs
                                    if ".cache" not in r)
    json.dump(info, open(os.path.join(a.out, "pins.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Ghi", os.path.join(a.out, "pins.json"))


if __name__ == "__main__":
    main()
