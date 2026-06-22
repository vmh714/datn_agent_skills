# TinyML Model Architecture (SisFall Fall-Detection / HAR)

> **Cập nhật lần cuối:** 2026-06-22 (thêm thí nghiệm v30_kd — knowledge distillation TCN→CNN; trước đó v32 window 128/256) · **Verified against `SisFall-PreProcessing/` code @ 2026-06-22**
> Canonical source of truth cho **model nhận diện té ngã + HAR chạy on-device trên ESP32-S3** (TFLM + ESP-NN).
> Quy ước: `path:line` neo vào code thật trong repo train **`SisFall-PreProcessing/`** (git repo `sis_fall_har_and_fall-detection_trainning`, là repo **riêng**, không nằm trong git monorepo). Mở full file chỉ khi cần SỬA.
> Rule/gotcha đầy đủ trong repo: **`SisFall-PreProcessing/AGENTS.md`** — file này tóm tắt phần "sự thật xuyên suốt" để agent monorepo không phải mở repo train.

## 1. Tổng quan & môi trường

- **Vị trí:** `SisFall-PreProcessing/` (cùng cấp với `backend/`, `frontend/`, `firmware/`). Rule riêng: `SisFall-PreProcessing/AGENTS.md`.
- **Mục tiêu:** raw SisFall (accel+gyro) → train → nén **INT8** → `model_data.cc/.h` → nhúng vào `firmware/` (`lib_model`, xem [firmware.md](firmware.md) + [PROJECT_MAP.md](PROJECT_MAP.md) §1.4).
- **Pipeline:** `raw .txt → tiền xử lý → windowing → cache .npy → train → export INT8 .tflite → model_data.cc/.h → firmware`.
- **Phiên bản hiện tại:** dòng **v30/v31** (CNN / ResNet1D / TCN tối ưu ESP-NN). v1–v29 đã archive trong `SisFall-PreProcessing/archive_trainings/`. **v32 (đang thử):** CNN từ v30 nhưng đổi window 200→**128/256** (xem §6).
- **Môi trường:**
  - **Local** = Windows (Python 3.14, **KHÔNG có TensorFlow**) — chỉ parse/check `.tflite`, gzip, dựng lại từ `.cc`.
  - **Train/convert** = server `har_fall` (SSH, conda env `har_fall`, **Python 3.11**, TF 2.21, RTX 2080 Ti dùng chung). Deps: `pip install -r requirements_kfold.txt`. Train nền: `nohup python train_xx.py > train.log 2>&1 &`.

## 2. Bài toán & dữ liệu (canonical)

- **5 nhãn:** `['Walk','Run','Idle','Trans','Fall']`, **Fall = index 4** — `ml_pipeline.py:158`, ví dụ khai báo `v30.py:222`. (Lie + StandSit gộp vào `Idle`.)
- **Cửa sổ:** **200 mẫu × 6 kênh** `(ax,ay,az,gx,gy,gz)` @ **100Hz** (downsample từ 200Hz). Windowing: `step2_windowing.py:11` (`extract_window(window_size=200)`), peak-based `:99`, sliding stride 100 `:114`.
- **KPI #1 = Fall recall** (bỏ sót té > báo nhầm). Đánh giá với **`fall_threshold = 0.25`** ép `prob[Fall] ≥ 0.25 → Fall` — `ml_pipeline.py:156,164`. **Luôn báo kèm Trans F1**, không kết luận bằng accuracy tổng.
  - ⚠️ Ngưỡng firmware **khác** (đang `0.6`, `tflite_wrapper.cpp:235`, xem [PROJECT_MAP.md](PROJECT_MAP.md) §1.4) — đây là 2 ngưỡng độc lập (eval offline vs runtime).
- **Split subject-independent** (KHÔNG trộn mẫu cùng người) — `ml_pipeline.py:18-20`:
  - TRAIN `SA01–18 + SE01–08` · VAL `SA19–21 + SE09–11` · TEST `SA22–23 + SE12–15` (`SA*`=trẻ, `SE*`=già).

## 3. Data pipeline & tiền xử lý

- **Module dùng chung:** `ml_pipeline.py` → `DataPreprocessor` (`:10`, load/cache/split/scale) + `OutputReporter` (`:130`, history/confusion/report). Notebook/script kế thừa 2 class này (bản v30: `v30.py:28/115`, `v30_opt.py`, `v30_opt_v2.py`).
- **Scaling (`apply_preprocessing`)** — `ml_pipeline.py:108-115`: accel `clip(-8,8)/8`; gyro `/2000`.
- **Tiền xử lý raw (step1):** accel `×32/8192`, gyro `×(4000/65536)×(π/180)`, downsample 200→100Hz — `step1_extract_and_preprocess.py` (chi tiết: `AGENTS.md` §4.3).
- **Kỷ luật cache `.npy`** (quan trọng — windowing rất chậm):
  - Cache **chỉ phụ thuộc windowing, KHÔNG phụ thuộc kiến trúc** → nhiều thí nghiệm cùng windowing **dùng chung 1 `cache_dir`**. Đổi kiến trúc thì **KHÔNG cắt window lại**.
  - **KHÔNG dùng chung thư mục windowed giữa logic windowing khác nhau** (v25/KFold decimate+D09/D10/D14 → namespace riêng `*_v25`/`*_v27`), tránh load nhầm file cũ.

## 4. Kiến trúc & ràng buộc ESP-NN ⚠️ (trái tim của bài toán)

Mọi quyết định kiến trúc bị chi phối bởi tập lệnh **ESP-NN** (mục tiêu latency thấp trên ESP32-S3):
- **ESP-NN TĂNG TỐC:** Conv 1×1 pointwise (**14×**), relu6 (**11×**), MaxPool/FullyConnected (**~8×**), Depthwise 3×3 (**6×**), Conv 3×3 (**5.5×**), mean/GAP, elementwise add/mul. (Conv1D → TFLite map sang Conv2D H=1 nên vẫn được tăng tốc.)
- **ESP-NN KHÔNG tăng tốc** (chạy reference, chậm): **LSTM/GRU**, **dilated conv (dilation>1)**, **sigmoid/tanh**, hard_swish.
- → **Mạng tối ưu:** depthwise-separable Conv1D (k=3) + pointwise 1×1 + relu6 + MaxPool downsample + GAP + Dense.
- → **Tránh** trong nhánh tối ưu tốc độ: LSTM, dilated conv (TCN cổ điển chậm vì cái này), **SE block** (sigmoid + phình metadata INT8).

## 5. Export, Compression & gotchas

- **Bắt buộc INT8** để chạy MCU. Export = `export_tflite_with_ops.py:76` (`export_int8_with_ops`) → sinh `model_<ver>_int8.tflite` + `model_data_<ver>.cc/.h` **nhúng sẵn ops + quant + gợi ý `MicroMutableOpResolver`**.
- **Quét ops CHUẨN bằng gói `tflite`** (parse Flatbuffer trực tiếp) — `export_tflite_with_ops.py:112-124`. **TUYỆT ĐỐI KHÔNG** chỉ dùng `Interpreter()._get_ops_details()` → bỏ sót op ẩn (`MAX_POOL_2D` ép từ 1D, `STRIDED_SLICE`) → ESP32 **crash lúc boot** (`Didn't find op for builtin opcode`). Cảnh báo khi thiếu gói: `:130`.
- **LSTM/GRU → cần Keras 2:** đặt `os.environ['TF_USE_LEGACY_KERAS']='1'` **TRƯỚC import tensorflow** + cài `tf-keras` → fuse `UNIDIRECTIONAL_SEQUENCE_LSTM`. Keras 3 ra op `WHILE` → segfault TFLM. Convert phải clone sang `batch_shape=(1,200,6)` rồi kiểm ops không có `WHILE`. GRU thường vẫn ra `WHILE` → test export trước khi đầu tư.
- **INT8 size do SỐ TENSOR, không phải param count:** nhiều tensor nhỏ (SeparableConv+SE như v25: 19k params nhưng 80KB, ~75% overhead). Muốn nhỏ flash: ít tensor to > nhiều tensor nhỏ. TFLite KHÔNG nén (flatbuffer thô). Số liệu thật phải đo từ `.tflite` INT8 trên chip, không từ model float.

## 6. Lịch sử model evolution (bối cảnh)

- `train_v1_*resize*` — CNN-LSTM thu nhỏ (LSTM 64→32, 32→16).
- `train_v8`–`train_v22` — TCN (dilated conv); **v22 tốt nhất** nhưng ~100ms/infer.
- `train_v25` — ResNet1D (SeparableConv + SE).
- `train_v27` — CNN thuần tối ưu ESP-NN; `train_v22_optimize` — TCN bỏ dilation.
- **v30/v31 (hiện tại)** — biến thể CNN/ResNet1D/TCN tối ưu ESP-NN: folder `train_v30`, `train_v30_tcn[_optimize[_v2]]`, `train_v30_resnet1d[_optimize]`, `train_v30_lstm32`, `train_v31` ở gốc repo (đang track). v1–v29 → `archive_trainings/`.
  - **Số liệu firmware INT8 (trên chip):** CNN v30 = **20ms / arena 16.5KB / tflite 25KB**, Trans F1 fw 0.85, Fall recall fw 96%. TCN v30 = **~2058ms / 50KB / 105KB** (dilated conv không được ESP-NN tăng tốc → KHÔNG deploy được), nhưng Trans F1 fw 0.94 → chỉ dùng làm **teacher**.
- **v30_kd (đã thử — KD, KẾT LUẬN: chạm trần kiến trúc):** `train_v30_kd/train_v30_kd.ipynb`, teacher = TCN v30, student = CNN v30 nguyên bản (tách `Dense(softmax)`→`Dense(logits)+Softmax`, graph tflite không đổi). Đã thử 4 recipe: KD-CE T=4, KD-KL T=2, selective per-class trust. **Idle F1 đóng băng ~0.909, Trans precision kẹt ~0.75 qua mọi recipe → không recipe nào thắng baseline v30 (acc 93.43%).** Nguyên nhân: teacher TCN yếu hơn baseline ở Fall (97.07<97.60) nên KD toàn cục kéo Fall xuống; và head `GAP+GMP` của CNN xóa trục thời gian → mù với dạng/vị trí transition (cặp Idle/Trans). KD ⇒ dead-end ở kiến trúc này.
- **v30_kd2 (student kiến trúc MỚI) — folder `train_v30_kd2/` chia subfolder theo thí nghiệm:** Sửa head `GAP+GMP` → `GAP+GMP+Flatten(map thô 12×96)` để giữ **cấu trúc thời gian** (phá nút thắt Idle/Trans), + 2 SeparableConv k3 stride-1 mỗi tầng + kênh 32/48/64/96. Vẫn thuần op ESP-NN (không dilation/LSTM/sigmoid). **Bản deploy dùng SINGLE-TCN teacher** (KHÔNG ensemble) + selective KD (α=0.5, T=2, trust `[1,0.6,1,1.3,0.25]`, Fall class-weight×3). Per-class F1 teacher (test): CNN Trans 0.799/Fall-rec 97.60%, TCN Idle 0.950/Trans 0.927/Fall-rec 97.07%, ResNet1D Idle 0.925/Trans 0.848. Dùng lại `cache_v30`.
  - **Subfolder:** `kd_alpha_0_5/` (= bản deploy, chứa artifacts + report firmware) · `kd_alpha_1_0_ablation/` (α=1.0 tắt KD, đo riêng kiến trúc) · `kd_alpha_0_3_teacher_heavy/` (α=0.3) · `fall_recall_boost/` (Fall weight 3→4, trust Fall→0.1) · `ensemble_teacher_alpha_0_5/` (thử teacher = 0.5·TCN+0.25·ResNet1D+0.25·CNN — chưa từng chạy).
  - **KẾT QUẢ 5 biến thể offline FLOAT (acc / Fall recall / Trans F1):** kd α=0.5 = 0.9532/97.20/0.906 · **α=1.0 (no-KD) = 0.9563/97.47/0.914** · α=0.3 = 0.9551/97.20/0.917 · **fall_boost = 0.9558/97.73/0.907** (Fall recall cao nhất, vượt baseline) · ensemble = 0.9571/97.33/0.912. **KẾT LUẬN QUAN TRỌNG: KD không giúp — α càng cao (ít KD) càng tốt, α=1.0 (no-KD) vượt mọi bản KD. Thắng lợi đến từ KIẾN TRÚC head giữ-thời-gian, KHÔNG phải distillation.**
- **v30_optimize (đóng gói kiến trúc kd2, BỎ KD):** `train_v30_optimize/train_v30_optimize.ipynb` — clone pipeline supervised thuần của v30 baseline, thay `build_model` = kiến trúc kd2 (GAP+GMP+Flatten + 2 SepConv/tầng + kênh 32/48/64/96, plain softmax, ~26.6k params), **bỏ hẳn teacher/Distiller**. Train chuẩn (Fall×3/Trans×0.55, augment Trans, val_loss+ModelCheckpoint). Dùng lại `cache_v30`. Kỳ vọng ≈ `kd_alpha_1_0` (acc ~0.956). Đây là framing đúng: "cải tiến kiến trúc CNN", không phải KD.
  - **K-fold:** `train_v30_optimize/SisFall_KFold_Experiments_v6.ipynb` (v6 = v30_optimize; kế thừa khung K-Fold v4: pipeline `decimate(q=2)`, windowing `v3kf`, cache `cache_kfold_v3`, 5 kịch bản S1_Elderly/S2_Young/S3-S4 cross/S5_Both; thay build_model + monitor `val_accuracy`). Out: `KFold_Results_v6/`. (v3=CNN baseline, v4=TCN.)
  - **KẾT QUẢ offline FLOAT (test, thr 0.25):** acc 0.9532, Idle F1 0.942, Trans F1 0.906 (baseline 0.799 → +10.7), Fall F1 0.986/recall 97.20%, params 26.6k.
  - ✅ **FIRMWARE-VERIFIED, DEPLOY-READY** (INT8 trên ESP32-S3, bộ test 1000 mẫu): acc **0.9530** (≈ float, quantize gần như không suy hao), Idle 0.926, Trans **0.945**, Fall 0.987, **Fall recall 97.50%** (vượt baseline 96.0% & teacher 97.0%). Latency **56.7ms** / arena **28.3KB** / tflite **55.8KB** — bằng/vượt teacher TCN (acc 0.952, 2058ms) mà **nhanh ~36×**. So baseline firmware: Trans +9.2, Idle +6.7, Fall recall +1.5. → **kd2 thay baseline v30 làm model deploy chính.** (Latency 56.7ms OK: infer theo window ~1s, ~5-6% duty cycle.)
- **v32 (đang thử, CHƯA có kết quả) — đổi window size:** clone từ `train_v30/trans_weight_0_55/train_v30.ipynb` (CNN thuần ESP-NN, head avg+max).
  - `train_v32_w128/train_v32_w128.ipynb` (window **128** ≈1.28s) và `train_v32_w256/train_v32_w256.ipynb` (window **256** ≈2.56s, pooling power-of-2 sạch).
  - **Notebook self-contained**: mọi tham số window gom ở cell cấu hình (`WINDOW_SIZE`, `VTAG`, `FALL_SHIFTS`, `FALL_LEFT_RATIO`); 5 cell còn lại dùng chung qua biến đó. Step1 (`SisFall_dataset_Processed_v32`) độc-lập-window → dùng chung; windowing → namespace riêng `SisFall_dataset_Windowed_<VTAG>` + cache `cache_<VTAG>`.
  - **Fall cắt event-centered theo đỉnh accel-SVM, căn lệch `FALL_LEFT_RATIO`** (w128=0.45 để chừa chỗ pha settle; w256=0.5). Cơ sở: phân tích max-SVM trên 1798 file Fall → impact-complex ≤128 mẫu cho 98.2% ca, win128 peak-centered giữ ≥95% năng lượng va chạm cho 98.6% ca (script `analyze_fall_window_128.py`).
  - ⚠️ Window 128: biên mỏng → **bắt buộc** cắt event-centered (không sliding mù); cảnh báo realtime firmware cần đặt impact đủ sâu trong buffer.

## 7. Quy ước tạo thí nghiệm & workflow agent

1. Tạo folder `train_vXX[_mô_tả]/`, clone notebook/script gần nhất.
2. Chỉ đổi `build_model`, `self.version`, `out_dir`; **giữ nguyên `cache_dir`** để dùng lại cache. Đổi kiến trúc-only → skip cell windowing, để `load_or_create_dataset()` nạp thẳng cache.
3. Export kiểu nhúng ops (§5). Ghi bảng so sánh: **params · tflite KB · acc (float & INT8) · Fall recall · Trans F1 · inference ms (ESP32-S3)**.
4. **Sửa notebook `.ipynb` BẮT BUỘC qua `manage_notebook_cells.py`** (ở gốc repo) — KHÔNG sửa tay JSON. Trên server GPU chung: bật memory growth + **Shut Down kernel sau train** (tránh ôm VRAM).
5. **Sau khi đổi Model / Pipeline / Compression / thêm thí nghiệm → cập nhật file này** (theo [codebase_context.md](codebase_context.md) §2) và bump dòng "Cập nhật lần cuối".

## 8. Anchor map (file:line — phục vụ reading protocol, gốc `SisFall-PreProcessing/`)

| Cần tra | Anchor |
|---|---|
| 5 nhãn / Fall index | `ml_pipeline.py:158`, `v30.py:222` |
| Subject-independent split | `ml_pipeline.py:18-20` |
| `fall_threshold=0.25` (eval) | `ml_pipeline.py:156,164` |
| Scaling train (clip/8, gyro/2000) | `ml_pipeline.py:108-115` |
| `DataPreprocessor` / `OutputReporter` | `ml_pipeline.py:10` / `:130` |
| Windowing (window=200, stride 100) | `step2_windowing.py:11,99,114` |
| Export INT8 + nhúng ops | `export_tflite_with_ops.py:76` |
| Quét ops chuẩn (gói `tflite`) | `export_tflite_with_ops.py:112-124` |
| Rule/gotcha đầy đủ | `SisFall-PreProcessing/AGENTS.md` (§4 gotchas) |
| Tool sửa notebook | `SisFall-PreProcessing/manage_notebook_cells.py` |

## 9. Đừng (Don'ts)

- ❌ Commit `venv/`, `SisFall_dataset/`, `.npy` cache lớn, `build/` firmware; sửa/xoá `SisFall_dataset/` raw hay cache đang dùng chung.
- ❌ Thêm LSTM/GRU/dilated-conv/sigmoid vào nhánh "tối ưu ESP-NN" mà không cảnh báo latency.
- ❌ Để kernel GPU sống sau train trên server chung; đánh giá chỉ bằng accuracy tổng; kết luận size/acc từ model float thay vì `.tflite` INT8.
- ❌ Sửa tay JSON `.ipynb`; quét ops chỉ bằng `_get_ops_details()`.
