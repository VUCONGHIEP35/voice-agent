# Cấu trúc mã dự án theo layer (tái cấu trúc 26–27/10/2026)

## Toàn dự án: dữ liệu chảy theo một chiều

```
sources/  ──►  gen10k/  ──►  data/m1m2_10k_v31/  ──►  tts_gen/  ──►  tts_gen/runs/ (âm thanh, chấm ASR)
nguồn gốc      sinh văn bản   văn bản đã sinh          sinh âm thanh + chấm ASR
(json)         (py -3.13)     (không sửa tay)          (.venv, cụm A100)
```

| Thư mục | Vai trò |
|---|---|
| `sources/` | Nguồn gốc: mẫu lệnh, từ vùng, đơn vị hành chính (chỉ đọc) |
| `gen10k/` | Bộ sinh văn bản; các lớp xem mục **gen10k** bên dưới |
| `data/` | Văn bản đã sinh theo phiên bản (`m1m2_10k`, `_v2`, `_v3`, `_v31`) và bảng v0.3. Không ghi đè phiên bản cũ |
| `tts_gen/` | Sinh âm thanh, chấm ASR, chạy cụm; các lớp xem mục **tts_gen** bên dưới |
| `snr_probe/` | Công cụ đo độ sạch âm thanh của giọng tham chiếu, kèm `safe_fetch` và test bảo mật. Đứng riêng, không phụ thuộc lớp nào |
| `docs/` | Kế hoạch, báo cáo, tài liệu này |
| `luutru/` | Thế hệ mã cũ, không bảo trì: `generator/` (khung bộ sinh dở dang của phiên đầu), `scripts/` (dựng bảng v0.3; nếu chạy sẽ ghi ra `luutru/out/`) |

`../review/` (ngoài dự án, gốc repo) chứa các tệp góp ý và `BANG_tu_ngoai_lai.csv`, mà `gen10k` đọc.

---

# tts_gen

## Các lớp và quy tắc phụ thuộc

```
cauhinh/   hằng số dùng chung: đường dẫn, bảng giọng + trọng số, mô hình ghim revision, ngưỡng
   ↑
thuvien/   thư viện, không có CLI: manifest, chuẩn hóa chữ, CER, căn hàng (theo từ, CTC), luật chấm, kiểm âm thanh, ghi FLAC
   ↑
buoc/      mỗi bước pipeline là một CLI:  python -m buoc.<tên>
   ↑                     ↑
phantich/  báo cáo,      dieuphoi/  bộ điều phối song song, Slurm (dieuphoi/slurm/), đóng gói, kiểm máy
phân tích, phiếu nghe              (gọi các bước qua python -m buoc.<tên>)

kiemthu/   test (được import mọi lớp)          luutru/   thí nghiệm / thí điểm đã xong, không bảo trì
```

Phụ thuộc chỉ đi **một chiều**, theo chiều mũi tên. Test `kiemthu/test_cau_truc.py` tự kiểm điều này:
- `cauhinh` không import gì của dự án;
- `thuvien` chỉ import `cauhinh`;
- `buoc` không import `phantich` hay `dieuphoi`;
- không lớp nào import `luutru`;
- gốc `tts_gen/` không còn `.py` rời.

Thư mục dữ liệu giữ nguyên chỗ cũ: `lexicon/`, `eval1000/`, `eval1000_tts/`, `full10k/`, `pilot/`, `reports/`, `runs/`, `dist/`, `giong_that/`, `.cache/`. Thư mục `voice_clone/` không đụng tới (theo yêu cầu cũ).

## Cách chạy

Luôn chạy từ thư mục `tts_gen/`, theo dạng mô-đun:

```bash
python -m buoc.chon_cau_10k                        # thay cho: python select_10k.py
python -m buoc.cham runs/full10k_p01 --lexicon lexicon/asr_bien_the.tsv --luat v2
python -m phantich.bao_cao runs/... --plan full10k/all_10k.jsonl
python -m dieuphoi.dong_goi --profile server
python -m unittest discover -s kiemthu -t .        # toàn bộ test
```

Đường dẫn dữ liệu trong mã tính từ `cauhinh.duong_dan.GOC`, tức thư mục `tts_gen/`.

## Một chỗ duy nhất cho cấu hình

| Thứ cần đổi | Tệp |
|---|---|
| Bảng 24 giọng, giọng bị loại, trọng số giọng | `cauhinh/giong.py` |
| Revision mô hình (VieNeu, MOSS, PhoWhisper, wav2vec2, Zipformer) | `cauhinh/mo_hinh.py` |
| Ngưỡng: CER 0,10 (tạm), câu ngắn, Z một mình 0,05, sinh lại tối đa 25%, điểm dừng dat theo vùng, kiểm cắt đầu / tốc độ | `cauhinh/nguong.py` |
| Đường dẫn gốc, từ điển | `cauhinh/duong_dan.py` |
| Bước RIR: loại xe (7 loại theo xe Việt Nam), ghế, micro, trọng số, vật liệu và hiệu chỉnh theo RIR đo, ngưỡng EDT, −26 dBFS, P(RIR), đầu vào luật v1 | `cauhinh/tang_cuong.py` |

Bước RIR (bản 3 ngày 28/10/2026: docs/ke_hoach_RIR_v3.md) chạy bằng venv riêng có pyroomacoustics (`.venv_rir` trên laptop, `venv_rir` trên cụm):
`buoc/rir_kho_do` (kho RIR đo thật: tải + dựng) và `buoc/rir_kho` (kho RIR mô phỏng) → `buoc/rir_gan` (bảng gán, ưu tiên RIR đo) → `buoc/rir_chap` (chập, bộ đệm "chỉ có vang") → `buoc.asr_whisper` trên `asr_dev/sach|vang` → `phantich/rir_qa`. So kho mô phỏng với kho đo (hiệu chỉnh, docs/ke_hoach_RIR_v3.md): `phantich/so_kho_rir`.

Bước trộn nhiễu (docs/ke_hoach_nhieu_v1.md; cấu hình `cauhinh/nhieu.py`): `buoc/nhieu_tai` (tải CAVEMOVE, AISHELL-5) → `phantich/do_nhieu`, `cat_doan_nghe`, `phieu_nghe_nhieu` (đo, phiếu nghe) → `buoc/nhieu_kho` (chỉ mục theo preset) → `buoc/nhieu_gan` → `buoc/nhieu_tron` (trộn, lượt ASR `asr_dev/nhieu`, lưới `asr_luoi`) → `buoc.asr_whisper` → `phantich/nhieu_qa`. Slurm: `dieuphoi/slurm/{tai_nhieu.sh, chay_nhieu.sbatch, nop_nhieu.sh}`. Hàm đo và chập ở `thuvien/rir.py`; phiếu nghe thử ở `phantich/phieu_nghe_rir.py`; Slurm ở `dieuphoi/slurm/{setup_rir.sh, chay_rir.sbatch, nop_rir.sh}`.

## Bảng đổi tên (tệp cũ → tệp mới)

| Cũ | Mới |
|---|---|
| `run_pilot.py` | `buoc/tts.py` (hàm ghi FLAC → `thuvien/am_thanh.py`) |
| `check_run.py` | `buoc/kiem_luot.py` |
| `make_fallback.py` | `buoc/doi_giong.py` |
| `asr_check.py` | `buoc/asr_whisper.py` (norm, CER, đáp án biến thể → `thuvien/cham_chu.py`) |
| `asr_diagnose.py` | `buoc/asr_chan_doan.py` |
| `asr_zipformer.py` | `buoc/asr_zipformer.py` |
| `gate_union.py` | `buoc/cham.py` (luật v1/v2 → `thuvien/luat_cham.py`) |
| `make_audio16.py` | `buoc/dung_audio16.py` |
| `make_wake_aug.py` | `buoc/ghep_loi_goi.py` |
| `fetch_zipformer.py` | `buoc/tai_zipformer.py` |
| `select_10k.py`, `select_eval1000.py` | `buoc/chon_cau_10k.py`, `buoc/chon_cau_eval1000.py` (hàm chung → `thuvien/chon_cau.py`) |
| `nghe_giong_that.py` | `buoc/giong_that.py` |
| `report_eval.py` | `phantich/bao_cao.py` |
| `phan_tich_vi_tri_loi.py` | `phantich/vi_tri_loi.py` (căn hàng theo từ → `thuvien/can_hang.py`) |
| `do_toc_do_am_tiet.py` | `phantich/toc_do_am_tiet.py` (căn hàng CTC → `thuvien/can_hang.py`) |
| `so_nghe_voi_may.py` | `phantich/so_nghe_voi_may.py` |
| `make_phieu_nghe_tu_dau.py`, `make_phieu_nghe_full10k.py` | `phantich/phieu_nghe_tu_dau.py`, `phantich/phieu_nghe_full10k.py` |
| `asr_error_mining.py` | `phantich/khai_thac_loi_asr.py` (chuẩn hóa chữ, thanh, từ điển → `thuvien/van_ban.py`) |
| `text_audit.py` | `phantich/kiem_van_ban.py` |
| `tts_env.py`, `eval_common.py`, `tts_checks.py` | `thuvien/moi_truong.py`, `thuvien/manifest.py`, `thuvien/kiem_am_thanh.py` |
| `pack_colab.py`, `check_hw.py` | `dieuphoi/dong_goi.py`, `dieuphoi/kiem_may.py` |
| `server/dieu_phoi.py`, `ghi_buoc.py`, `tai_mo_hinh.py` | `dieuphoi/dieu_phoi.py`, `dieuphoi/ghi_buoc.py`, `dieuphoi/tai_mo_hinh.py` |
| `server/setup_server.sh`, `chay_10k.sbatch`, `nop_10k.sh`, `HUONG_DAN.md` | `dieuphoi/slurm/…` |
| `server/chay_eval.sbatch`, `nop_job.sh`, `do_toc_do.sbatch` | `luutru/slurm_cu/` |
| `select_pilot.py`, `report_pilot.py`, `compare_dtype.py`, `test_voice_config.py`, `mem_watch.py`, `colab_eval_A.ipynb` | `luutru/` |
| `test_*.py` | `kiemthu/` (thêm `test_cau_truc.py`) |
| `*.log`, `hw_report.json` ở gốc | `luutru/nhat_ky/` |

Các tài liệu và báo cáo viết **trước** 26/10/2026 vẫn ghi tên cũ. Tra bảng trên để biết tên mới.

Notebook `luutru/colab_eval_A.ipynb` dùng tên script cũ, nên không chạy được nếu không sửa. Nó được giữ để tra cứu cách đã chạy phần A.

## Đã kiểm sau khi tái cấu trúc (26/10/2026)

- 71 test đều đạt (68 test cũ + 3 test cấu trúc). `pyflakes` sạch, trừ một cảnh báo f-string có từ trước.
- Trên dữ liệu thật, mã mới cho kết quả **giống từng byte** mã cũ ở các phần sau:
  - chấm luật v1 và v2 (phần p01: trên laptop so với mốc chụp từ mã cũ; trên máy chủ so với `gate_hop*.csv` của lượt chạy thật);
  - gán giọng 10.000 câu (11 tệp);
  - báo cáo (`bao_cao.md`, `theo_giong.csv`);
  - phân tích vị trí lỗi;
  - `kiem_luot`;
  - so phiếu nghe với máy;
  - chọn câu cho phiếu nghe.
- Khác biệt duy nhất: tên script được in trong tiêu đề hoặc lời nhắn.
- Trên máy chủ: import các bước trong cả hai venv đều ổn. Mã cũ ở đó được chuyển sang `~/asr_tts_o_to/cache/ma_cu_<ngày>/`, không xóa.
- **Chưa chạy lại** các bước dùng GPU (TTS, ASR) bằng mã mới. Phần logic của chúng chỉ được chuyển chỗ và đổi import, không viết lại. Lần chạy GPU tới nên bắt đầu bằng `smoke`.

---

# gen10k (tái cấu trúc 27/10/2026)

## Các lớp

```
cauhinh/      duong_dan.py: GOC (gen10k/), ROOT (thư mục dự án: data/, sources/)
   ↑
nguyen_lieu/  "nguyên liệu" của câu: kho giá trị khe (pools10k), khung câu (frames10k, frames_app10k, frames_llm10k),
   ↑          từ vùng và tiểu từ (lexicon10k), cách đọc từ ngoại (loanwords10k)
thuvien/      đọc số (vnnum), điền khe (slots10k), khung mang / lõi câu (diversity10k). Không có CLI
   ↑
buoc/         build10k (sinh bộ câu), make_v31 (v3 → v3.1), validate10k (kiểm QA)
   ↑
phantich/     diversity_report10k (báo cáo đa dạng), compare10k (so hai bộ), make_trung_list (danh sách cho người bản ngữ Trung)

kiemthu/      test_vnnum, test_cau_truc          luutru/   fix_xlsx_105 (sửa một lần bảng v0.3, đã xong)
```

`kiemthu/test_cau_truc.py` kiểm các điều sau:
- phụ thuộc chỉ đi theo chiều mũi tên;
- gốc `gen10k/` không còn `.py` rời;
- không còn kiểu import phẳng cũ (`import pools10k`), vốn chỉ chạy được khi `sys.path` trỏ vào `gen10k/`.

`make_v31` dùng các hàm trợ giúp của `build10k` (`asr_key`, `tfidf_fit`, …). Đây là import trong cùng lớp `buoc/`, được phép.

Tên tệp giữ nguyên, chỉ chuyển vào thư mục lớp. Có một ngoại lệ: phần CLI của `diversity10k.py` (các hàm `load`, `main` và việc đọc tham số dòng lệnh) được tách sang `phantich/diversity_report10k.py`. Phần thư viện ở lại `thuvien/diversity10k.py`.

## Cách chạy (từ `gen10k/`, Python 3.13 hệ thống)

```bash
py -3.13 -m buoc.build10k --seed 20261013 --out ../data/<thư mục mới>     # cũ: py -3.13 build10k.py
py -3.13 -m buoc.make_v31 --src ../data/m1m2_10k_v3 --out ../data/<mới> --refill-pool <thư mục> ...
py -3.13 -m buoc.validate10k ../data/m1m2_10k_v31
py -3.13 -m phantich.diversity_report10k ../data/m1m2_10k_v31             # cũ: py -3.13 diversity10k.py
py -3.13 -m phantich.compare10k ../data/m1m2_10k_v3 ../data/m1m2_10k_v31
py -3.13 -m unittest discover -s kiemthu -t .                              # 13 test
```

## Bảng đổi chỗ (gen10k)

| Cũ (`gen10k/…`) | Mới |
|---|---|
| `pools10k.py`, `frames10k.py`, `frames_app10k.py`, `frames_llm10k.py`, `lexicon10k.py`, `loanwords10k.py` | `nguyen_lieu/` |
| `vnnum.py`, `slots10k.py` | `thuvien/` |
| `diversity10k.py` | `thuvien/diversity10k.py` (thư viện) + `phantich/diversity_report10k.py` (CLI) |
| `build10k.py`, `make_v31.py`, `validate10k.py` | `buoc/` |
| `compare10k.py`, `make_trung_list.py` | `phantich/` |
| `fix_xlsx_105.py` | `luutru/` |
| `test_vnnum.py` | `kiemthu/` |

Các chuỗi ghi nguồn gốc nằm *trong* dữ liệu (ví dụ "generator/tpl_a.py, tpl_b.py (phiên trước, K1)" trong `frames10k`, `pools10k`) giữ nguyên chữ để dữ liệu sinh ra không đổi. Hiện `generator/` nằm ở `luutru/generator/`.

## Đã kiểm sau khi tái cấu trúc (27/10/2026)

Mã cũ và mã mới đều chạy cùng một bộ lệnh, kết quả ghi vào scratchpad, không ghi vào `data/`:
- `build10k` với seed 20261013 và seed 7001;
- `make_v31` từ `data/m1m2_10k_v3`, dùng 4 bộ câu bù `pool_7001..7004` đã dùng cho v3.1 thật;
- `validate10k`, `diversity10k`, `compare10k`, `make_trung_list`, `test_vnnum`.

Kết quả so sánh:
- **46 tệp kết quả giống nhau**: các tệp JSONL, `README_nguon.md`, TSV và báo cáo JSON giống từng byte. Khi so manifest, bỏ qua `elapsed_sec` và `created`.
- Khác biệt duy nhất: tên thư mục kết quả được in trong log.
- Mã cũ (đo ngay trước khi chuyển) sinh lại `data/m1m2_10k_v31/` thật giống từng byte (9 tệp JSONL), nên mốc so sánh là đúng.
- 13 test đạt (9 test đọc số + 4 test cấu trúc).
- `pyflakes` chỉ còn các cảnh báo có từ trước, cố ý để nguyên vì không đổi hành vi: import `SV`, `P`, `DIG` không dùng; khóa `podcast` bị lặp trong `frames10k`; `os` trong `fix_xlsx_105`.
