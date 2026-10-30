# Chạy trên cụm A100 HUST

Mọi thứ nằm trong `~/asr_tts_o_to/`. Không đụng `~/vieneu`, `~/venvs` hay job của người khác.

## Kiến trúc cụm (dò ngày 24/10/2026)

- Nút đầu `bcm-headnode02`: không có GPU, có mạng. Dùng để cài đặt và tải mô hình.
- Nút GPU `dgx01` và `dgx02`: mỗi nút 8 × A100-80GB, driver 575.57.08. Chạy bằng Slurm, partition `defq`.
- Tài khoản `user04` dùng chung với người khác: tối đa 2 job chạy cùng lúc, nộp tối đa 6 job, mỗi job 1 GPU. Người dùng chọn 25/10/2026: **mỗi lần chỉ 1 job** của mình (`nop_10k.sh` tự chặn).

## Các bước

Ở laptop (từ `tts_gen/`):

```powershell
python -m dieuphoi.dong_goi --profile server        # -> dist/server_eval_B.zip + .sha256
& "$env:WINDIR\System32\OpenSSH\scp.exe" dist\server_eval_B.zip dist\server_eval_B.zip.sha256 hust04:asr_tts_o_to/goi/
```

Trên nút đầu (`ssh hust04`):

```bash
cd ~/asr_tts_o_to/goi && sha256sum -c server_eval_B.zip.sha256 && unzip -o -q server_eval_B.zip -d ../code
bash ~/asr_tts_o_to/code/tts_gen/dieuphoi/slurm/setup_server.sh       # lần đầu: venv, mô hình ghim, CT2, Zipformer
cd ~/asr_tts_o_to/code/tts_gen
bash dieuphoi/slurm/nop_10k.sh "smoke p01" 1    # thử cỡ lô ASR + 24 câu + phần p01 (hiệu chỉnh)
bash dieuphoi/slurm/nop_10k.sh "p02 p03 p04 p05 p06 p07 p08 p09 p10"
bash dieuphoi/slurm/nop_10k.sh "wake"           # ghép lời gọi trợ lý, sau khi p01..p10 xong
```

Theo dõi: `tail -f runs/full10k_dieu_phoi.log` (bộ điều phối ghi bắt đầu/xong từng tác vụ, tỷ lệ dat mỗi phần).

Kết quả: `~/asr_tts_o_to/ket_qua/ket_qua_full10k_<phần>.tar.gz` và `.sha256`. Tải về bằng `scp.exe`, so sha256, giải nén vào thư mục mới trong `tts_gen/runs/`.

Job bị ngắt (hết giờ, lỗi nút) thì nộp lại đúng lệnh cũ: các bước đã có kết quả sẽ được bỏ qua. Có tệp `runs/DUNG_CHAT_LUONG` nghĩa là gặp điểm dừng chất lượng: đọc, xử lý, xóa tay rồi mới nộp lại.

Lệnh cũ của eval1000 (`chay_eval.sbatch`, `nop_job.sh`, `do_toc_do.sbatch`) nằm trong `luutru/slurm_cu/`, không bảo trì.
