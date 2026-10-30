# -*- coding: utf-8 -*-
"""Test cho check_hw.danh_gia bằng số liệu giả (không cần phần cứng thật). Chạy: python -m unittest test_check_hw"""
import unittest

from dieuphoi.kiem_may import danh_gia  # noqa: E402


def facts(**kw):
    f = {"torch": {"installed": True, "cuda_available": True, "total_gb": 12.0, "bf16": True, "capability": "8.6",
                   "matmul_2048": {"bf16": {"ms": 1.0}}},
         "nvidia_smi_gpus": [{"name": "GPU", "mem_total_mb": 12288}], "ram_total_gb": 32.0, "cpu_flags": ["avx2"],
         "disks": {"C:": {"free_gb": 100.0, "total_gb": 200.0}, "D:": {"free_gb": 80.0, "total_gb": 250.0}},
         "project_drive": "D:", "hf_cache_drive": "C:", "on_battery": False, "ffmpeg": True}
    for k, v in kw.items():
        if k == "torch":
            f["torch"].update(v)
        else:
            f[k] = v
    return f


def as_dict(out):
    return {m: (k, l) for m, k, l in out}


class DanhGia(unittest.TestCase):
    def test_gpu_lon_co_bf16(self):
        d = as_dict(danh_gia(facts()))
        self.assertEqual(d["Máy chạy TTS"][0], "ưu tiên chạy tại máy")
        self.assertEqual(d["Kiểu số trên GPU"][0], "bf16")
        self.assertNotIn("RAM", d)

    def test_gpu_4gb_may_nay(self):
        d = as_dict(danh_gia(facts(torch={"total_gb": 4.0}, nvidia_smi_gpus=[{"name": "3050 Ti", "mem_total_mb": 4096}])))
        self.assertIn("đo VRAM", d["Máy chạy TTS"][0])
        self.assertIn("Colab", d["ASR kiểm tra (PhoWhisper-large)"][0])

    def test_khong_gpu_khong_vnni(self):
        d = as_dict(danh_gia(facts(torch={"cuda_available": False}, nvidia_smi_gpus=[], cpu_flags=["avx2"])))
        self.assertEqual(d["Máy chạy TTS"][0], "CPU (ONNX)")
        self.assertEqual(d["int8 trên CPU"][0], "KHÔNG dùng")

    def test_khong_gpu_co_avx_vnni(self):
        d = as_dict(danh_gia(facts(torch={"cuda_available": False}, nvidia_smi_gpus=[], cpu_flags=["avx2", "avx_vnni"])))
        self.assertIn("nghe thử", d["int8 trên CPU"][0])

    def test_gpu_khong_bf16_dung_fp16(self):
        d = as_dict(danh_gia(facts(torch={"bf16": False})))
        self.assertIn("fp16", d["Kiểu số trên GPU"][0])

    def test_thu_bf16_bi_loi(self):
        d = as_dict(danh_gia(facts(torch={"matmul_2048": {"bf16": {"error": "RuntimeError()"}}})))
        self.assertIn("fp16", d["Kiểu số trên GPU"][0])

    def test_co_gpu_nhung_chua_cai_torch(self):
        d = as_dict(danh_gia(facts(torch={"installed": False, "cuda_available": False})))
        self.assertEqual(d["torch"][0], "chưa cài")

    def test_co_gpu_nhung_torch_ban_cpu(self):
        d = as_dict(danh_gia(facts(torch={"cuda_available": False})))
        self.assertEqual(d["torch"][0], "không dùng được CUDA")

    def test_ram_8gb(self):
        d = as_dict(danh_gia(facts(ram_total_gb=7.6)))
        self.assertIn("4 tiến trình", d["RAM"][1])

    def test_o_c_con_9gb_chua_cache(self):
        d = as_dict(danh_gia(facts(disks={"C:": {"free_gb": 9.5, "total_gb": 196.0}, "D:": {"free_gb": 81.9, "total_gb": 258.0}})))
        self.assertIn("C:", d["Ổ chứa cache Hugging Face"][0])
        self.assertIn("D:", d["Ổ chứa cache Hugging Face"][1])
        self.assertNotIn("Ổ chứa dự án / đầu ra", d)

    def test_dang_chay_pin(self):
        d = as_dict(danh_gia(facts(on_battery=True)))
        self.assertIn("pin", d["Nguồn điện"][0])


if __name__ == "__main__":
    unittest.main()
