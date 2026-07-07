# Plan — Đo năng lượng inference TinyML trên ESP32-S3 bằng INA228

> ⚠️ **Bản chính thức (theo quy ước CLAUDE.md):** `d:\datn\datn_agent_skills\plans\firmware_energy_measurement_ina228_plan.md`

## Context — Tại sao làm việc này

Bảng so sánh model trong báo cáo/slide hiện có: **tflite size · arena RAM · accuracy · Fall recall · Trans F1 · latency (ms)**
(nguồn: `firmware_test_tool/report_*_espnn_(ON|OFF)_sram_firmware.txt`, gom bởi `gather_stats.py`).
**Thiếu cột năng lượng/inference** — số liệu quan trọng để chứng minh tính khả thi TinyML trên edge và để so ESP-NN ON vs OFF.

Mục tiêu: đo **năng lượng tiêu thụ mỗi lần inference (µJ)** cho toàn bộ dòng model **v30 (mọi kiến trúc), v31, v32 (w128/w256)**, mỗi model ở **2 cấu hình ESP-NN ON/OFF**, rồi **bổ sung cột năng lượng vào bảng so sánh** trong report + slide.

Phương pháp (đã chốt với người dùng):
- **DUT** = ESP32-S3 chạy inference standalone (không WiFi/BLE/UART tới PC), loop 5 cửa sổ dữ liệu của 5 nhãn.
- **Node đo** = ESP32 thường + module **INA228** mắc high-side trên **rail 3.3V vào module S3**.
- **Đồng bộ** = S3 kéo 1 chân **GPIO marker** HIGH trong lúc chạy N inference, LOW khi idle. Node chốt thanh ghi
  **ENERGY (40-bit, tích lũy phần cứng)** của INA228 tại cạnh lên/xuống → `ΔE` Joule cho pha active (số chính),
  đồng thời cộng dồn P×t phần mềm để cross-check.

Ghi chú kỹ thuật: inference của CNN INT8 **không rẽ nhánh theo dữ liệu** → năng lượng/inference gần như đồng nhất giữa 5 nhãn.
Việc loop 5 nhãn chủ yếu để bám đúng phương pháp latency + lấy trung bình; per-label chỉ là breakdown kiểm chứng.

## Topology phần cứng

```
  [PSU/USB 5V] --> [3V3 reg] --IN+--[INA228 shunt]--IN- --> [ESP32-S3 module 3V3]   (DUT: inference, no comms)
                                        |  I2C (SDA/SCL)                |
                                   [ESP32 thường: node đo] <--- GPIO marker (S3 -> node, 1 dây + GND chung)
                                        |  USB serial
                                     [PC: energy_measure_tool.py -> energy_results.csv]
```
- S3 và node **chung GND**. GPIO marker: 1 output S3 → 1 input node (có ISR cạnh lên/xuống).
- S3 chạy bằng nguồn đi qua shunt (không cấp nguồn qua chân khác để khỏi bypass phép đo). USB của S3 chỉ để nạp firmware, khi đo có thể rút data (giữ nguồn) hoặc để nguyên — miễn không stream.
- Node đo nối USB tới PC để log. Node **fix CPU freq** và cấu hình rõ để phần đo ổn định.

---

## Hạng mục 1 — Project firmware DUT (ESP32-S3, self-contained) — user tự `idf.py create-project`

Đặt trong `d:\datn\sis_fall_har_and_fall-detection_trainning\energy_bench_s3\` (project mới, tách khỏi
`sis_fall_firmware_inference/`). **Tái sử dụng gần như nguyên xi** từ project inference cũ:

**Reuse verbatim (copy vào `main/`):**
- `sis_fall_firmware_inference/main/tflite_wrapper.cpp` + `tflite_wrapper.h` — bộ init/Invoke, arena, quant hoá input, `esp_timer` timing.
- `sis_fall_firmware_inference/main/model_data.cc` + `model_data.h` — swap theo từng model cần đo.
- `sis_fall_firmware_inference/main/idf_component.yml` — kéo `espressif/esp-tflite-micro`.
- Cấu hình ESP-NN ON/OFF: copy `sdkconfig.on` / `sdkconfig.off` + `build_variants.ps1` (đã có sẵn cơ chế 2 build dir `build_on`/`build_off`).

**Viết mới:**
- `main/energy_bench_main.c` (thay cho `sis_fall_firmware_inference.c`): **bỏ toàn bộ UART handshake/rx_task**. Logic:
  1. `tflite_init()`; đọc `get_input_bytes()`.
  2. Cấu hình 1 GPIO output = **MARKER_GPIO** (hằng số, vd GPIO 2).
  3. Loop vô hạn: với mỗi nhãn trong `{Walk,Run,Idle,Trans,Fall}`:
     - `gpio_set_level(MARKER, 1)` → chạy **K = 200** lần `tflite_run_inference_with_data(sample[label], bytes)` → `gpio_set_level(MARKER, 0)`.
       (**K=200** để khớp bench tốc độ + pha active dài ~2.2s → ENERGY hw tích phân mượt.)
     - `vTaskDelay(IDLE_GAP_MS)` (pha idle để node đo baseline, vd 500 ms).
     - (tùy chọn) in latency `esp_timer` trung bình ra USB-JTAG log để đối chiếu — không bắt buộc.
  4. Ghi rõ **label hiện tại** bằng số nhịp marker khác nhau HOẶC in 1 dòng log để tool tách per-label (xem "đồng bộ nhãn" bên dưới).
- `main/bench_samples.h` — **hardcode 5 mảng 2D `static const float sample_<label>[WIN][6]`** (1 cửa sổ/nhãn),
  **fix cứng luôn, KHÔNG dùng tool sinh**. Giá trị lấy từ 5 file CSV trong `SisFall_dataset_Windowed_<pipeline>_TEST/`
  (mỗi nhãn 1 SA khác nhau tuỳ chọn). **Lưu ý quan trọng: giá trị mẫu KHÔNG ảnh hưởng năng lượng** (compute INT8 cố định,
  không rẽ nhánh theo dữ liệu) → chỉ cần **đúng độ dài WIN** của model. Cần 3 bản header theo dòng model:
  v30/v25 = 200, v32_w128 = 128, v32_w256 = 256 → đổi header khi đổi dòng (hiếm, 3 lần).

**sdkconfig (bench) — copy nguyên `sdkconfig.on`/`sdkconfig.off` từ `sis_fall_firmware_inference/` (đã VERIFY):**
- **ESP-NN toggle = điểm KHÁC BIỆT DUY NHẤT giữa 2 file** (đã `diff`): ON → `CONFIG_NN_OPTIMIZED=y` + `CONFIG_NN_OPTIMIZATIONS=1`;
  OFF → `CONFIG_NN_ANSI_C=y` + `CONFIG_NN_OPTIMIZATIONS=0`. Wrapper phân biệt bằng `#if defined(CONFIG_NN_OPTIMIZED)`. Toggle rất sạch.
- `CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y` — **đã có sẵn** (khớp latency chuẩn 11.20 ms; ON/OFF cùng freq). Không cần thêm gì.
- `CONFIG_BT_ENABLED` **đã off sẵn**. `CONFIG_COMPILER_OPTIMIZATION_PERF=y` (-O2) khớp report SRAM. Target `esp32s3`.
- WiFi: `CONFIG_ESP_WIFI_ENABLED=y` (lib compiled-in) nhưng firmware bench **không gọi `esp_wifi_init/start`** → radio tắt, ~0 W.
  Muốn baseline sạch tuyệt đối có thể đặt `CONFIG_ESP_WIFI_ENABLED=n` (tùy chọn; không bắt buộc vì radio đã off khi không init).
- `CONFIG_SPIRAM=y` (OCT) — PSRAM có dòng tĩnh nhưng nằm trong **idle baseline** nên trừ được. Giữ `ARENA_USE_PSRAM=0` (arena ở SRAM) để khớp latency chuẩn.

**Đồng bộ nhãn (label ↔ burst):** đơn giản nhất — S3 chạy tuần tự 5 nhãn theo thứ tự cố định, mỗi nhãn 1 burst marker,
giữa 5 nhãn là 1 pha idle dài hơn (vd 1500 ms) làm "separator" để tool host nhận biết ranh giới chu kỳ. Tool đếm 5 burst/chu kỳ.
(Nếu cần chắc chắn: S3 in 1 dòng log `LBL:<name>` qua USB-JTAG, tool đọc kèm — nhưng tránh mọi giao tiếp làm nhiễu năng lượng S3, nên ưu tiên cách đếm burst.)

## Hạng mục 2 — Project firmware node đo (ESP32 thường + INA228) — user tự `idf.py create-project`

Đặt trong `d:\datn\sis_fall_har_and_fall-detection_trainning\energy_meter_ina228\`.

**Driver mới `components/drv_ina228/`** — clone pattern từ `d:\datn\firmware\components\drv_mpu6050\` (API `driver/i2c_master.h` mới):
- `ina228_init(i2c_master_bus_handle_t bus)` → `i2c_master_bus_add_device()` (addr **0x40** mặc định).
- Register map: `CONFIG=0x00, ADC_CONFIG=0x01, SHUNT_CAL=0x02, VSHUNT=0x04, VBUS=0x05, DIETEMP=0x06, CURRENT=0x07, POWER=0x08, ENERGY=0x09 (5 bytes/40-bit), CHARGE=0x0A, DIAG_ALRT=0x0B, DEVICE_ID=0x3F`.
- Đọc: `i2c_master_transmit_receive(dev,&reg,1,buf,n,to)`; ghi: `i2c_master_transmit(dev,{reg,hi,lo},3,to)`.
- **Calibration (hằng số cấu hình):** `R_SHUNT` (module Adafruit INA228 = **0.015 Ω** — để làm hằng số chỉnh được),
  `I_MAX` (vd 1.0 A) → `CURRENT_LSB = I_MAX/2^19`; `SHUNT_CAL = 13107.2e6 * CURRENT_LSB * R_SHUNT`;
  `POWER_LSB = 3.2 * CURRENT_LSB`; `ENERGY_LSB = 16 * POWER_LSB` (Joule/LSB). Đặt ADC_CONFIG = continuous, chọn conversion time/averaging hợp lý (vd 1052 µs, avg 1) để có độ phân giải thời gian tốt trong pha active ~ K×latency.
- Hàm tiện ích: `ina228_read_energy_j()`, `ina228_read_vbus_v()`, `ina228_read_current_a()`, `ina228_read_power_w()`.

**`main/energy_meter_main.c`:**
- Tạo I2C bus (giống `firmware/main/app_main.c:94-103`), `ina228_init`.
- Cấu hình **MARKER_IN_GPIO** = input + ISR cạnh lên/xuống (`gpio_install_isr_service`).
  - Cạnh **lên**: đọc `ENERGY` (E0) + `esp_timer_get_time()` (t0), push vào queue.
  - Cạnh **xuống**: đọc `ENERGY` (E1) + t1 → `ΔE_hw = E1-E0` (J), `Δt = t1-t0` (µs), push record.
  - (cross-check) task nền lấy mẫu `POWER`/`CURRENT` nhanh trong pha active, tích phân P×Δt phần mềm → `ΔE_sw`.
- Task xuất CSV qua USB serial cho PC, mỗi burst 1 dòng:
  `t_ms, vbus_v, i_active_mA, p_active_mW, dE_hw_uJ, dt_active_ms, dE_sw_uJ`
  (node **không** biết K/model/label — host tool gắn metadata đó lúc log).
- Đo **idle baseline**: trong pha marker LOW, task nền đọc `POWER` trung bình → in dòng `IDLE, p_idle_mW`.

Lưu ý: node đo **không cần biết** K, model, ESP-NN ON/OFF — những thứ đó do người vận hành truyền vào host tool (giống `--model-name`/`--pipeline` của tool cũ).

---

## Hạng mục 3 — Tool host: đo + gom bảng (không có tool sinh sample)

Đặt trong `firmware_test_tool/` và root (bám cấu trúc hiện có).

**(a) `bench_samples.h` — hardcode tay, KHÔNG làm tool sinh.** Chọn 5 file CSV (mỗi nhãn 1 file, có thể mỗi nhãn 1 SA khác)
trong `SisFall_dataset_Windowed_<pipeline>_TEST/`, dán thẳng thành 5 mảng 2D vào header. Vì giá trị không ảnh hưởng năng lượng
nên chỉ cần đúng độ dài WIN. (Việc chuyển CSV→mảng C làm 1 lần bằng snippet vứt đi, không phải tool được maintain.)

**(b) `firmware_test_tool/energy_measure_tool.py` (mới)** — driver đo:
- Args: `--port COMx`, `--model-name`, `--pipeline`, `--espnn on|off`, `--k 200` (mặc định, khớp bench tốc độ), `--cycles 3` (mặc định 3–5, đủ vì E/inference tất định).
- Mở serial node đo, đọc M×5 dòng burst (+ dòng IDLE), gắn nhãn theo thứ tự burst trong chu kỳ.
- Tính: **E/inference (µJ)** = `dE_hw_uJ / K` (số chính) và bản `_sw` để cross-check; latency đo được = `dt_active_ms / K`
  (đối chiếu với `esp_timer` của model — nếu lệch nhiều → cảnh báo). Gom TB theo model×espnn (+ per-label breakdown).
- Ghi 2 output **mirror shape của report SRAM cũ** để `gather_stats.py` parse được:
  - Append `firmware_test_tool/energy_results.csv`, cột:
    `Model, Architecture, ESPNN, Pipeline, WindowLen, Label, K, Latency_ms, Vbus_V, I_active_mA, P_active_mW, P_idle_mW, E_per_infer_uJ, E_per_infer_sw_uJ, Timestamp`
  - Ghi `firmware_test_tool/report_<model>_espnn_(ON|OFF)_energy.txt` (text kiểu Việt như report SRAM):
    `Model`, `ESP-NN ON/OFF`, `CPU Freq`, `Vbus (V)`, `Số inference đo (K×cycles)`, `Latency TB (ms)`,
    `Công suất active TB (mW)`, `Công suất idle baseline (mW)`, **`Năng lượng / inference: X µJ`** (dòng khoá để regex).

**(c) `gather_stats.py` (sửa)** — biến thành "tool bảng" thực sự:
- Sửa `base_dir` stale (`d:\New folder\...`) → dùng `os.path.dirname(os.path.abspath(__file__))` (portable).
- Mở rộng `models` gồm mọi dòng cần đo: các `v30*` (cnn/resnet1d/tcn/optimize...), `v31`, `v32_w128`, `v32_w256`.
- Thêm regex đọc `report_*_espnn_*_energy.txt`: `Năng lượng / inference: ([\d\.]+) µJ`, `Công suất active TB: ([\d\.]+) mW`, `Công suất idle baseline: ([\d\.]+) mW`.
- **Xuất bảng thật** (không chỉ stdout): ghi `firmware_test_tool/model_comparison.csv` + `model_comparison.md` gồm cột:
  `Model | tflite KB | Arena KB | Accuracy | Fall recall | Trans F1 | Latency ms | E/infer µJ | P_active mW | P_idle mW`,
  mỗi model có 2 dòng ESP-NN ON/OFF. Đây là bảng dán thẳng vào report/slide.

**(d) (tùy chọn) plot** — mở rộng `plot_mcu_evolution.py` thêm cụm cột "Energy/infer (µJ)" ON vs OFF cho slide.
Chỉ làm nếu cần hình cho slide (memory: slide bảo vệ visual-first).

---

## Files chạm vào (tóm tắt)

**Mới:**
- `energy_bench_s3/` (project S3) — `main/energy_bench_main.c`, `main/bench_samples.h` (**hardcode 5 mảng 2D**), + copy `tflite_wrapper.*`, `model_data.*`, `sdkconfig.on/off`, `build_variants.ps1`.
- `energy_meter_ina228/` (project ESP32) — `components/drv_ina228/{ina228.c,include/ina228.h}`, `main/energy_meter_main.c`.
- `firmware_test_tool/energy_measure_tool.py` (chỉ 1 tool host — không có tool sinh sample).

**Sửa:**
- `gather_stats.py` (fix base_dir + energy column + xuất CSV/MD).

**Template tham chiếu (chỉ đọc):**
- `d:\datn\firmware\components\drv_mpu6050\{mpu6050.c,include/mpu6050.h}` (driver I2C mẫu).
- `d:\datn\firmware\main\app_main.c:94-103` (tạo I2C bus).
- `sis_fall_firmware_inference/main/tflite_wrapper.cpp`, `.../sis_fall_firmware_inference.c`, `build_variants.ps1`.

## Verification (end-to-end)

1. **Build DUT:** đảm bảo `bench_samples.h` đã hardcode đúng WIN của model; trong `energy_bench_s3/`:
   `./build_variants.ps1 -Only on -Flash on -Port COMx`. Xác nhận S3 boot, log in đúng ESP-NN ACTIVE, marker GPIO nhấp nháy (soi bằng logic analyzer/LED nếu có).
2. **Build node đo:** flash `energy_meter_ina228/`. Xác nhận `DEVICE_ID` INA228 đọc đúng (0x2280/0x2281), `Vbus ≈ 3.3V`, `p_idle` hợp lý (vài chục–trăm mW).
3. **Đo 1 model:** `python firmware_test_tool/energy_measure_tool.py --port COMy --model-name v30_optimize --pipeline v30 --espnn on --k 200 --cycles 5`.
   Kiểm: `E/infer` ổn định giữa 5 nhãn (sai lệch nhỏ), `dE_hw ≈ dE_sw` (cross-check khớp), `latency đo ≈ 11 ms` (khớp `esp_timer`/report SRAM).
   Chạy lại `--espnn off` → E/infer OFF phải **cao hơn** ON (ESP-NN tiết kiệm).
4. **Sanity năng lượng:** `E/infer (µJ) ≈ P_active(mW) × latency(ms)` — hai đường tính phải nhất quán.
5. **Gom bảng:** đo hết các model (v30*, v31, v32_w128, v32_w256 × ON/OFF), swap `model_data.*` mỗi lần; chỉ khi đổi độ dài WIN (200→128→256) mới thay `bench_samples.h`.
   `python gather_stats.py` → mở `firmware_test_tool/model_comparison.csv/.md`, xác nhận cột E/infer đầy đủ mọi model, dán vào report/slide.

## Rủi ro / lưu ý

- **Cách 3 (ENERGY hw) là số chính**; nếu xử lý thanh ghi/overflow rắc rối → fallback cách 1 (`dE_sw`) vẫn có sẵn trong cùng firmware (không phải làm lại).
- Cửa sổ hardcode phải **khớp WindowLen của model** (200/128/256) — nếu lệch, `get_input_bytes()` vs mảng sẽ đọc sai/tràn. Đổi header khi đổi dòng model.
- ON/OFF phải **cùng CPU freq (240 MHz)** để so sánh công bằng.
- Không stream USB/log nặng trên S3 lúc đo (nhiễu năng lượng) — ưu tiên đếm burst thay vì in `LBL:` mỗi nhãn.
- Sau khi có số: cập nhật `tinyml_model.md`/`report.md` (thêm cột năng lượng) theo rule codebase_context §2.
