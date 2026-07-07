# Phương Pháp Đo Năng Lượng Inference TinyML trên ESP32-S3 (INA228)

> **Cập nhật lần cuối:** 2026-07-07 (khởi tạo — phương pháp đo năng lượng/inference bằng INA228, gate bằng GPIO marker)
> Canonical source of truth cho **cách đo năng lượng tiêu thụ mỗi lần inference** của model TinyML trên ESP32-S3.
> Viết sẵn ở dạng report-ready để tái sử dụng cho chương thực nghiệm luận văn (không phải viết lại).
> Liên quan: [tinyml_model.md](tinyml_model.md) (§4 ESP-NN, latency chuẩn), [firmware.md](firmware.md), plan chi tiết triển khai:
> `datn_agent_skills/plans/firmware_energy_measurement_ina228_plan.md`.

---

## 1. Mục tiêu & đại lượng đo

Bổ sung cột **năng lượng** vào bảng so sánh model (đang có: tflite size · arena RAM · accuracy · Fall recall · Trans F1 · latency),
để chứng minh tính khả thi TinyML trên edge và định lượng lợi ích của **ESP-NN**.

| Ký hiệu | Đại lượng | Đơn vị | Ý nghĩa |
|---|---|---|---|
| `E_infer` | Năng lượng **gross** mỗi inference | µJ | Tổng năng lượng trong pha active chia cho số lần chạy |
| `E_dyn` | Năng lượng **động** (net) mỗi inference | µJ | `E_infer − P_idle × t_lat` — phần năng lượng do compute gây ra, đã trừ nền |
| `P_active` | Công suất trung bình khi inference | mW | Công suất trung bình pha marker HIGH |
| `P_idle` | Công suất nền (idle baseline) | mW | Công suất trung bình pha marker LOW (MCU rảnh, không WiFi/BLE) |
| `t_lat` | Latency mỗi inference | ms | Đo cả bằng `esp_timer` (DUT) lẫn thời gian pha active / K (node đo) |
| `V_bus` | Điện áp rail đo | V | ≈ 3.3 V (rail cấp cho module S3) |

> **Chỉ số chính báo cáo = `E_infer` (µJ/inference)** cho từng model × {ESP-NN ON, OFF}. `E_dyn` bổ trợ khi cần tách phần compute.

---

## 2. Sơ đồ hệ thống đo (topology)

```
  [PSU/USB 5V] ── [3V3 LDO] ──IN+──[INA228 R_shunt 0.015Ω]──IN+/OUT── 3V3 ─► [ESP32-S3  = DUT]
                                        │  I2C (SDA/SCL, 400kHz)                  │  (inference, KHÔNG WiFi/BLE/UART-PC)
                                   [ESP32 thường = NODE ĐO] ◄──── GPIO marker ────┘  (1 dây + GND chung)
                                        │  USB-Serial
                                        ▼
                                   [PC: energy_measure_tool.py] ─► energy_results.csv / report_*_energy.txt
```

- **INA228 mắc high-side** (nối tiếp trên đường 3.3V *vào* module S3, sau LDO) → đo đúng năng lượng MCU tiêu thụ khi inference.
- **DUT và NODE ĐO chung GND.** DUT kéo 1 chân **GPIO marker** làm tín hiệu đồng bộ (HIGH = đang inference, LOW = idle).
- DUT chạy standalone (chỉ cần nguồn qua shunt); **không stream USB/log nặng** lúc đo để tránh nhiễu năng lượng.
- NODE ĐO nối USB tới PC để log; **không cần biết** model/K/label — metadata do người vận hành truyền vào tool host.

---

## 3. Thiết bị & vai trò

| Vai trò | Phần cứng | Nhiệm vụ |
|---|---|---|
| **DUT** | ESP32-S3 (vd Seeed XIAO ESP32-S3) | Chạy inference INT8 (TFLM + ESP-NN) trong vòng lặp cố định; kéo GPIO marker |
| **Node đo** | ESP32 thường + **module INA228** | Đọc thanh ghi ENERGY của INA228 theo cạnh GPIO; xuất CSV qua USB |
| **INA228** | Power/energy monitor I2C, ADC ΔΣ 20-bit | Đo dòng/áp/công suất; **tích lũy năng lượng bằng phần cứng** (thanh ghi 40-bit) |
| **PC** | `energy_measure_tool.py` | Gắn metadata, gom trung bình, ghi CSV + report + bảng so sánh |

**Vì sao INA228 (không phải INA226/219):** INA228 có **thanh ghi ENERGY 40-bit tích lũy công suất bằng phần cứng** theo từng
chu kỳ ADC. Node chỉ cần chốt giá trị tại 2 cạnh GPIO → `ΔE` ra thẳng **Joule**, **miễn nhiễm jitter I2C** và không cần
tích phân phần mềm. Đây là ưu điểm quyết định so với INA226/219 (chỉ có current/power tức thời).

---

## 4. Nguyên lý đo — GPIO gating + thanh ghi ENERGY

1. DUT vào pha active: `GPIO_marker = 1`, chạy **K** lần inference liên tiếp, rồi `GPIO_marker = 0`.
2. Node đo bắt **ngắt cạnh (ISR)** trên chân marker:
   - **Cạnh lên:** đọc `ENERGY` (E0) + timestamp `esp_timer` (t0).
   - **Cạnh xuống:** đọc `ENERGY` (E1) + timestamp (t1).
3. Năng lượng pha active: `ΔE_hw = (E1 − E0) × 16 × POWER_LSB` (Joule) — xem §5. Thời gian active: `Δt = t1 − t0`.
4. **Số chính:** `E_infer = ΔE_hw / K`. **Cross-check (song song, cùng firmware):** task nền lấy mẫu `POWER`/`CURRENT`
   nhanh trong pha active → tích phân phần mềm `ΔE_sw = Σ Pᵢ·Δtᵢ`. Hai đường phải khớp.
5. **Idle baseline:** trong pha marker LOW, task nền đọc `POWER` trung bình → `P_idle`.

> Thanh ghi `ENERGY` free-run (không reset giữa chu kỳ) — chỉ **chốt** tại 2 cạnh; 40-bit đủ headroom, không tràn trong 1 burst.
> Cờ tràn (`ENERGYOF`) trong `DIAG_ALRT` được kiểm tra để an toàn.

---

## 5. Hiệu chuẩn INA228 (calibration)

Công thức theo datasheet TI INA228 (chế độ `ADCRANGE = 0`, dải shunt ±163.84 mV):

```
CURRENT_LSB = I_max / 2^19            (A/LSB)   — I_max = dòng tối đa kỳ vọng (vd 1.0 A)
SHUNT_CAL   = 13107.2e6 × CURRENT_LSB × R_SHUNT           (ghi vào thanh ghi 0x02; ×4 nếu ADCRANGE=1)
POWER_LSB   = 3.2 × CURRENT_LSB       (W/LSB)
Current [A] = CURRENT_reg × CURRENT_LSB
Power  [W]  = POWER_reg   × POWER_LSB
Energy [J]  = ENERGY_reg  × 16 × POWER_LSB
```

**LSB cố định (không phụ thuộc calib):** `V_BUS`: 195.3125 µV/LSB · `V_SHUNT`: 312.5 nV/LSB (ADCRANGE=0) · `DIETEMP`: 7.8125 m°C/LSB.

**Ví dụ cấu hình dùng module Adafruit INA228 (`R_SHUNT = 0.015 Ω`, `I_max = 1.0 A`):**

| Tham số | Giá trị |
|---|---|
| `CURRENT_LSB` | 1.0 / 2¹⁹ ≈ **1.907 µA/LSB** |
| `SHUNT_CAL` (0x02) | 13107.2e6 × 1.907e-6 × 0.015 ≈ **375** |
| `POWER_LSB` | 3.2 × 1.907µA ≈ **6.104 µW/LSB** |
| Energy/LSB | 16 × 6.104µW ≈ **97.66 µJ/LSB** *(hệ số theo ENERGY_reg)* |

**ADC_CONFIG (0x01):** đặt continuous mode, chọn conversion time + averaging sao cho có đủ phân giải thời gian trong pha
active (`≈ K × t_lat`). Gợi ý: VBUSCT/VSHCT ≈ 1052 µs, AVG = 1. `R_SHUNT`/`I_max` là **hằng số chỉnh được** trong `drv_ina228`.

---

## 6. Điều kiện chuẩn hóa (để so sánh công bằng)

Đã verify trong `sis_fall_firmware_inference/sdkconfig.on|off` — bench project copy nguyên các cấu hình này:

| Điều kiện | Giá trị | Ghi chú |
|---|---|---|
| CPU freq | **240 MHz** (`CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240`) | ON/OFF cùng freq; khớp latency chuẩn 11.20 ms |
| Compiler opt | **-O2** (`COMPILER_OPTIMIZATION_PERF`) | Khớp report SRAM |
| Bluetooth | **off** (`CONFIG_BT_ENABLED` not set) | |
| WiFi | lib compiled-in nhưng **không `esp_wifi_init/start`** → radio tắt (~0 W) | tùy chọn `CONFIG_ESP_WIFI_ENABLED=n` cho baseline sạch tuyệt đối |
| Tensor arena | **SRAM** (`ARENA_USE_PSRAM=0`) | Khớp latency chuẩn (weights ≤64 KB nằm trong cache) |
| PSRAM | `CONFIG_SPIRAM=y` (OCT) | Dòng tĩnh nằm trong `P_idle` → tự trừ khi tính `E_dyn` |
| **ESP-NN toggle** | ON: `CONFIG_NN_OPTIMIZED=y`, `CONFIG_NN_OPTIMIZATIONS=1` · OFF: `CONFIG_NN_ANSI_C=y`, `CONFIG_NN_OPTIMIZATIONS=0` | Là **khác biệt DUY NHẤT** giữa 2 sdkconfig; wrapper phân biệt bằng `#if defined(CONFIG_NN_OPTIMIZED)` |

---

## 7. Quy trình đo

Thông số chuẩn: **K = 200** inference/burst (khớp bench tốc độ; pha active ~2.2 s → ENERGY tích phân mượt),
**cycles = 3–5** chu kỳ 5-nhãn (đủ vì `E_infer` gần như tất định — CNN INT8 không rẽ nhánh theo dữ liệu).

Mỗi **model × {ESP-NN ON, OFF}**:
1. Swap `model_data.cc/.h` sang model cần đo. Nếu độ dài cửa sổ đổi (200↔128↔256) thì thay `bench_samples.h` (hardcode 5 mảng 2D, mỗi nhãn 1 cửa sổ — **giá trị mẫu không ảnh hưởng năng lượng**, chỉ cần đúng độ dài).
2. `./build_variants.ps1 -Only on -Flash on -Port COMx` (rồi `-Only off`).
3. Chạy tool host:
   `python firmware_test_tool/energy_measure_tool.py --port COMy --model-name <m> --pipeline <p> --espnn on --k 200 --cycles 5`
4. DUT loop tuần tự 5 nhãn `{Walk,Run,Idle,Trans,Fall}`, mỗi nhãn 1 burst marker; giữa các chu kỳ có pha idle dài hơn làm separator để tool tách ranh giới. Tool đọc M×5 burst, gom trung bình.

---

## 8. Công thức tính kết quả

```
t_lat      = Δt_active / K                       (ms)         — đối chiếu với esp_timer của DUT
P_active   = ΔE_hw / Δt_active                   (mW)
E_infer    = ΔE_hw / K                            (µJ)  ← chỉ số chính (gross)
E_dyn      = E_infer − P_idle × t_lat            (µJ)         — năng lượng động (net compute)
```

**Kiểm chứng (bắt buộc đạt trước khi tin số):**
- `ΔE_hw ≈ ΔE_sw` (thanh ghi phần cứng khớp tích phân phần mềm).
- `E_infer ≈ P_active × t_lat` (sanity năng lượng–công suất–thời gian).
- `t_lat` (node đo) ≈ latency `esp_timer` / report SRAM (≈ 11 ms cho v30_optimize @240 MHz).
- **`E_infer(OFF) > E_infer(ON)`** — ESP-NN chạy nhanh hơn nên tốn ít năng lượng hơn (kỳ vọng chính của thí nghiệm).

---

## 9. Nơi lưu kết quả & tái lập

| Artefact | Đường dẫn | Nội dung |
|---|---|---|
| CSV thô | `sis_fall_har_and_fall-detection_trainning/firmware_test_tool/energy_results.csv` | 1 dòng/nhãn: Model, Architecture, ESPNN, Pipeline, WindowLen, Label, K, Latency_ms, Vbus_V, I_active_mA, P_active_mW, P_idle_mW, E_per_infer_uJ, E_per_infer_sw_uJ, Timestamp |
| Report/model | `firmware_test_tool/report_<model>_espnn_(ON|OFF)_energy.txt` | Text kiểu report SRAM; dòng khóa `Năng lượng / inference: X µJ` để `gather_stats.py` regex |
| Bảng gom | `firmware_test_tool/model_comparison.csv` + `.md` | Ghép size · arena · accuracy · Fall recall · Trans F1 · latency · **E/infer · P_active · P_idle**; dán thẳng report/slide |

Driver + firmware: `energy_meter_ina228/` (node, có `components/drv_ina228/`), `energy_bench_s3/` (DUT). Chi tiết ở plan.

---

## 10. Nguồn sai số & hạn chế

- **Tổn hao trước LDO không tính** (đo sau regulator, đúng chủ đích "năng lượng MCU"); nếu cần "năng lượng hệ thống" phải đo ở rail 5V/pin.
- **Dòng tĩnh PSRAM/flash** nằm trong `P_idle` → dùng `E_dyn` khi muốn tách riêng phần compute.
- **Độ phân giải thời gian ADC**: chọn conversion time đủ nhỏ so với `t_lat`; K=200 làm pha active dài nên sai số bị pha loãng.
- **Nhiệt độ/điện áp nguồn**: giữ nguồn ổn định; `V_bus` được log để phát hiện sụt áp.
- `E_infer` phụ thuộc **CPU freq** → mọi so sánh phải cùng 240 MHz (đã chuẩn hóa §6).

---

## 11. Khung bảng kết quả cho báo cáo (điền số sau khi đo)

| Model | Kiến trúc | ESP-NN | tflite (KB) | Arena (KB) | Latency (ms) | **E/infer (µJ)** | P_active (mW) | P_idle (mW) |
|---|---|---|---|---|---|---|---|---|
| v30_optimize | DW-Sep CNN | ON | 55.8 | 28.3 | 11.20 | … | … | … |
| v30_optimize | DW-Sep CNN | OFF | 55.8 | 28.3 | … | … | … | … |
| v30_resnet1d | ResNet1D | ON/OFF | … | … | … | … | … | … |
| v30_tcn | TCN (dilated) | ON/OFF | 105 | 50 | 2014 | … | … | … |
| v31 | … | ON/OFF | … | … | … | … | … | … |
| v32_w128 / w256 | CNN (win 128/256) | ON/OFF | … | … | … | … | … | … |

Ánh xạ báo cáo: mở rộng bảng `tab:mcu_arch_compare` (Chương 5) thêm cột năng lượng; hình bar-chart E/infer ON vs OFF cho slide.

> **Bảo trì (rule):** đổi thiết bị/phương pháp đo, `R_SHUNT`/`I_max`, hoặc có bộ số liệu mới → cập nhật file này +
> `codebase_context.md` §2. Sau khi có số thật, đồng bộ cột năng lượng sang [tinyml_model.md](tinyml_model.md) và `report.md`.
