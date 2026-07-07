# Đo Hiệu Năng (Latency) & Độ Chính Xác On-Chip của Model Deploy (ESP32-S3)

> **Cập nhật lần cuối:** 2026-07-07 (khởi tạo — phương pháp đo latency + accuracy on-chip + **bảng kết quả thật** từ `firmware_test_tool/report_*_sram_firmware.txt`)
> Canonical source of truth cho **cách đo tốc độ + độ chính xác model INT8 chạy thật trên ESP32-S3** và **kết quả đã đo**.
> Report đã viết rồi nhưng gom ở đây để **làm slide + tra nhanh** khỏi scan lại 30+ file report.
> Liên quan: [tinyml_model.md](tinyml_model.md) (kiến trúc + số canonical), [energy_measurement.md](energy_measurement.md) (đo năng lượng), [firmware.md](firmware.md).
> **Xem kết quả benchmark → nhảy thẳng §8 (Kết quả).** Nguồn số: `sis_fall_har_and_fall-detection_trainning/firmware_test_tool/report_*_sram_firmware.txt`.

---

## 1. Mục tiêu & đại lượng đo

Đo trên **chip thật** (không phải mô phỏng/float offline) để lấy số đưa vào bảng so sánh model của báo cáo/slide.

| Đại lượng | Đơn vị | Nguồn |
|---|---|---|
| **Latency** (mean / max / min) | ms | `esp_timer_get_time()` quanh `interpreter->Invoke()` |
| **Tensor Arena dùng** | bytes | `arena_used_bytes()` sau khi cấp phát tensor |
| **Accuracy** (INT8 on-chip) | — | so `Predicted_Class` vs `Expected_Class` trên tập test |
| **Fall recall** | % | recall lớp `Fall` (KPI #1) @ `fall_threshold = 0.25` |
| **Trans F1** | — | F1 lớp `Trans` (lớp khó nhất, luôn báo kèm) |
| per-class P/R/F1 | — | sklearn `classification_report` (Walk/Run/Idle/Trans/Fall) |

> ⚠️ **Chỉ dùng số INT8 chạy trên chip** — KHÔNG kết luận từ model float offline (AGENTS.md §6).

---

## 2. Sơ đồ đo

```
  [PC: test_inference_uart.py]  ──UART/USB (SYNC→RDY→float32 window)──►  [ESP32-S3: tflite_wrapper]
     │  đọc từng cửa sổ test CSV                                              │  quantize → Invoke() → dequantize
     │  (SisFall_dataset_Windowed_<pipeline>_TEST/)                           │  esp_timer đo thời gian
     ◄──────────── JSON {time_us, arena_used, free_sram/psram, probs} ────────┘
     ▼
  inference_results.csv  ──►  report_<model>_espnn_(ON|OFF)_sram_firmware.txt  +  confusion_matrix_*.png
```

Khác với đo năng lượng (DUT standalone), đo latency/accuracy **có** host stream dữ liệu test để lấy nhãn dự đoán từng cửa sổ.

---

## 3. Nguyên lý đo

1. **Handshake:** host gửi `SYNC` → device trả `RDY` → host stream **1 cửa sổ = float32 6 kênh** (200/128/256 mẫu tùy pipeline).
2. Device: quantize INT8 (accel `clip(±8)/8`, gyro `/2000` hoặc `/500` tùy pipeline) → **`Invoke()`** → dequantize → áp `fall_threshold=0.25` (FALL_CLASS_INDEX=4).
3. **Latency = `esp_timer_get_time()` bao quanh riêng `Invoke()`** (không tính thời gian truyền UART). Trả JSON: `{"time_us", "is_stand_sit", "arena_used", "free_psram", "free_sram", "probs":[...]}`.
4. Host ghi `inference_results.csv`, chạy sklearn `classification_report` → sinh `report_*.txt` + confusion matrix.

---

## 4. Điều kiện chuẩn hóa (giống đo năng lượng — xem [energy_measurement.md](energy_measurement.md) §6)

**240 MHz · -O2 (`COMPILER_OPTIMIZATION_PERF`) · Tensor Arena ở SRAM (`ARENA_USE_PSRAM=0`) · esp-tflite-micro 1.3.7.**
ESP-NN toggle = khác biệt DUY NHẤT giữa `sdkconfig.on`/`sdkconfig.off`: `CONFIG_NN_OPTIMIZED=y`/`OPTIMIZATIONS=1` (ON) vs `CONFIG_NN_ANSI_C=y`/`OPTIMIZATIONS=0` (OFF).

> ⚠️ **Số latency phụ thuộc mạnh vào vị trí arena.** Số canonical hiện dùng là **arena ở SRAM + weights ≤64 KB nằm trong cache** (đã cache-optimize). Số cũ "arena ở PSRAM" (vd v30_optimize 56.7 ms) đã **lỗi thời**, không dùng cho slide.

---

## 5. Quy trình đo

Mỗi **model × {ESP-NN ON, OFF}**: build `sdkconfig.on`/`.off`, flash, rồi:
```
python firmware_test_tool/test_inference_uart.py --pipeline <v30|v32_w128|v32_w256|v25> --model-name <m>_espnn_ON -n 1000
```
- `--pipeline` chốt folder test + đơn vị gyro + normalization (v30/v25=window 200, v32_w128=128, v32_w256=256).
- `-n` = số mẫu test (khuyến nghị **1000**; các run lẻ `-n 6/100/250` chỉ là sanity, KHÔNG dùng cho bảng).
- `--eval-only` để dựng lại report từ `inference_results.csv` sẵn có.

---

## 6. Định nghĩa & lưu ý số học

- **Accuracy KHÔNG phụ thuộc ESP-NN.** Toán INT8 nguyên là **chính xác tuyệt đối** → ON và OFF cho **cùng dự đoán**. Mọi chênh lệch accuracy ON/OFF trong bảng §8 chỉ là **nhiễu do lấy mẫu test khác nhau** giữa 2 lần chạy, KHÔNG phải hiệu ứng thật. ESP-NN chỉ đổi **latency/năng lượng**.
- **Arena ON > OFF** (vd v30: 11.7 KB OFF → 16.5 KB ON): kernel ESP-NN tối ưu dùng nhiều scratch buffer hơn — bình thường.
- **Fall recall là KPI #1**; luôn báo kèm **Trans F1** (lớp chuyển tiếp khó nhất). Không kết luận bằng accuracy tổng.

---

## 7. Định dạng report + CSV (để tool/agent parse)

- `report_<model>_espnn_(ON|OFF)_sram_firmware.txt`: dòng khóa `Thời gian Inference trung bình: X ms`, `Tensor Arena (SRAM) sử dụng: N bytes`, khối `CẤU HÌNH BUILD`, `classification_report`, khối `TỶ LỆ RECALL TÉ NGÃ (FIRMWARE): X%`.
- `inference_results.csv` cột: `File, Expected_Class, Time_ms, Is_Stand_Sit_Firmware, Arena_Used, Free_PSRAM, Free_SRAM, Predicted_Class_Index, Predicted_Class_Name`.
- Gom bảng: `gather_stats.py` (đang stdout; kế hoạch mở rộng xuất `model_comparison.csv/.md` — xem plan năng lượng).

---

## 8. KẾT QUẢ (đã đo — 240 MHz, -O2, arena SRAM, ~1000 mẫu test SA22–23+SE12–15)

> Chú thích cột "Model": **⭐ = model deploy hiện tại (v30_optimize)** · **🥇 = model deploy ĐẦU TIÊN (v25 ResNet1D)**.

### 8.1. Latency & tăng tốc ESP-NN (full-run N≈1000)

| Model | Kiến trúc | Lat OFF (ms) | Lat ON (ms) | **Speedup** | Arena ON (KB) | tflite (KB) |
|---|---|---:|---:|:---:|---:|---:|
| **v30_optimize** ⭐ | DW-Sep CNN (kd2, ~26.6k) | 66.90 | **11.20** † | **~6.0×** | ~27.6 | 55.8 |
| v30 | CNN nhỏ ESP-NN | 23.65 | 5.14 | 4.6× | 16.5 | ~25 |
| v31 | CNN (4-ch gyro-RMS) | 23.09 | 5.13 | 4.5× | 16.5 | — |
| v32_w128 | CNN window 128 | 15.47 | 3.72 | 4.2× | 12.2 | — |
| v32_w256 | CNN window 256 | 30.02 | 6.04 | 5.0× | 19.2 | — |
| v30_resnet1d | ResNet1D + SE | 55.10 | 20.16 | 2.7× | 25.1 | — |
| **v25** 🥇 | ResNet1D + SE (SepConv) | 56.50 | 22.27 | 2.5× | 28.9 | 80 |
| v30_lstm32 | CNN-LSTM | 204.56 | 94.46 | 2.2× | 80.4 | — |
| v30_tcn_optimize | TCN bỏ dilation | 198.13 | 137.57 | 1.4× | 49.6 | — |
| v30_tcn | TCN dilated (teacher) | 2073.51 | 2014.30 | **1.03×** ✗ | 50.1 | 105 |

† v30_optimize ON full-1000: **11.20 ms** · arena 28276 B · acc 0.9540 · Fall 97.50% · Trans F1 0.9476 — nguồn `train_v30_optimize/val_accuracy/report_v30_opt_espnn_ON_sram_firmware.txt` (OFF: 66.90 ms, `..._espnn_OFF_...`).
✗ **TCN dilated hầu như KHÔNG được ESP-NN tăng tốc** (dilated conv nằm ngoài op accel) → minh chứng sống động cho AGENTS.md §4.2; TCN chỉ dùng làm **teacher**, không deploy.

### 8.2. Độ chính xác on-chip INT8 (ESP-NN-independent — chọn run đại diện N≈1000)

| Model | Accuracy | **Fall recall** | Trans F1 | Ghi chú |
|---|---:|---:|---:|---|
| **v30_optimize** ⭐ | **0.9540** | **97.50%** | **0.9476** | **model deploy** (full ON run; OFF = 0.9490/98.0%/0.942, chênh = nhiễu lấy mẫu) |
| v30_tcn_optimize | 0.9640 | 97.50% | 0.963 | acc cao nhất nhưng 138 ms (chậm) |
| v30_tcn | 0.9520 | 97.00% | 0.936 | teacher, 2014 ms |
| v30_resnet1d | 0.9340–0.9500 | 94.5–96.5% | 0.89–0.92 | SE block → arena/latency lớn |
| **v25** 🥇 | 0.9060–0.9120 | 94–96% | 0.83–0.85 | **deploy đầu tiên**; tflite 80 KB (metadata phình) |
| v30 | 0.9290 | 98.00% | 0.870 | CNN nhỏ, Trans yếu |
| v31 | 0.9100 | 98.00% | 0.837 | Trans yếu nhất |
| v32_w128 | 0.9340 | 97.00% | 0.881 | window 128 (đang thử) |
| v32_w256 | 0.9270 | 98.00% | 0.862 | window 256 (đang thử) |
| v30_lstm32 | 0.9250–0.9450 | 95.50% | 0.91–0.95 | LSTM chậm, không deploy |

> Chênh lệch accuracy ON/OFF (vd v30_resnet1d 0.9340↔0.9500) = **nhiễu lấy mẫu**, không phải ESP-NN (§6). Với model deploy dùng số full-run.

### 8.3. ⭐ Model deploy — v30_optimize (số headline cho slide)

```
Kiến trúc: Depthwise-Separable CNN (2×SepConv k3/stage, ch 32/48/64/96, GAP+GMP head), ~26.6k params, pure ESP-NN ops
Latency  : 11.20 ms @ 240 MHz (ESP-NN ON, arena SRAM)   —  ~6× nhanh hơn khi OFF (66.9 ms), ~180× nhanh hơn TCN (2014 ms)
Bộ nhớ   : Tensor Arena ~28 KB (SRAM) · tflite 55.8 KB (nằm gọn trong 64 KB cache)
Accuracy : 0.9530  ·  Fall recall 97.50%  ·  Trans F1 0.945   (INT8 on-chip, test subject-independent)
```

### 8.4. 🥇 Model deploy ĐẦU TIÊN — v25 (ResNet1D) — mốc khởi đầu cho slide

```
Kiến trúc: ResNet1D — SeparableConv1D + SE block (squeeze-excitation), ~19k params
Latency  : 22.27 ms @ 240 MHz (ESP-NN ON)  ·  56.50 ms (OFF)  →  speedup chỉ 2.5×
Bộ nhớ   : Tensor Arena 28.9 KB (SRAM)  ·  tflite 80 KB (⚠ ~75% là metadata do NHIỀU tensor nhỏ)
Accuracy : ~0.906 (ON) / 0.912 (OFF)  ·  Fall recall 94–96%  ·  Trans F1 0.83–0.85
```

**Vì sao bị thay bằng v30_optimize (câu chuyện tiến hóa deploy):** SE block dùng **sigmoid** (ESP-NN KHÔNG tăng tốc) + **nhiều tensor nhỏ** → tflite phình **80 KB**, speedup thấp (2.5× so với 6×), accuracy thấp hơn (0.906 vs 0.954). v30_optimize (DW-Sep CNN, **pure ESP-NN ops**) thắng toàn diện: **nhỏ hơn** (55.8 KB), **nhanh gấp đôi** (11.2 ms), **chính xác hơn** — bài học: bám tập op ESP-NN (AGENTS.md §4.2).

> Cặp **v25 → v30_optimize** = slide "hành trình tối ưu deploy": từ ResNet1D+SE nặng nề sang CNN thuần gọn-nhanh-chính xác.

---

## 9. Diễn giải cho slide

- **ESP-NN đáng giá cho CNN/DW-Sep** (2.5–6× nhanh hơn) nhưng **vô dụng với TCN dilated/LSTM** → củng cố lựa chọn kiến trúc CNN thuần cho edge.
- **Real-time thừa sức:** cửa sổ 2 s (stride 0.5 s @ 100 Hz) chỉ cần 1 inference/0.5 s; 11 ms << 500 ms → **duty cycle ~2%**, dư địa cho low-power.
- **Đánh đổi acc↔tốc độ:** v30_tcn_optimize acc nhỉnh hơn (0.964) nhưng chậm 12× → **v30_optimize là điểm cân bằng deploy**.
- **Hành trình deploy 🥇→⭐:** v25 (ResNet1D+SE, 80 KB, 22 ms, acc 0.906) → **v30_optimize** (DW-Sep CNN, 55.8 KB, 11.2 ms, acc 0.954): nhỏ hơn + nhanh gấp đôi + chính xác hơn nhờ bỏ SE/sigmoid, bám op ESP-NN (§8.4).

---

## 10. Ánh xạ báo cáo/slide & bảo trì

- Bảng Chương 5 `tab:mcu_arch_compare`: dùng §8.1 + §8.2. Slide: box §8.3 + bar-chart speedup §8.1.
- **Bảo trì (rule):** đo thêm/đo lại model → cập nhật §8 (nguồn: report mới). Có latency mới cho model deploy → đồng bộ [tinyml_model.md](tinyml_model.md) + `report.md`. Đo năng lượng → điền [energy_measurement.md](energy_measurement.md) §11.
