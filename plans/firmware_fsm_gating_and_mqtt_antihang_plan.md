# Firmware refactor: FSM service-gating + chống MQTT treo (4G PPP) + cập nhật docs

> **Ghi chú cho người implement:** Plan này gồm 3 phần độc lập (A, B, C), có thể làm và test riêng từng phần. Tuân thủ quy ước comment trong [firmware/CLAUDE.md](firmware/CLAUDE.md) (`/** */` đầu hàm, `///` cho quyết định thiết kế, `//` cho giải thích dòng). KHÔNG sửa file legacy `main/esp32s3_*.c` và `lib_model/model_data.cc`. Các tên field config nên đối chiếu lại với struct trong phiên bản ESP-IDF / esp_modem đang cài (esp-mqtt dùng config lồng nhau `.session/.network/.task`, đã thấy trong code hiện tại).

## Context

Hai vấn đề trên firmware 4G (A7680C PPPoS, broker TLS `mqtts://mqtt.toolhub.app:8883`):

1. **Service chạy không đúng state, phí CPU.** `imu_processing_task` là `while(1)` chạy bất kể state → pipeline IMU nặng (Kalman ×7/sample, pedometer, impact) chạy ở **mọi** state. [imu_service.c:265](firmware/components/svc_imu/imu_service.c#L265) còn gọi `svc_ai_process_window` ở **cả NORMAL lẫn STREAMING** — sai thiết kế (CLAUDE.md ghi STREAMING phải bỏ qua AI).

2. **MQTT treo không tự phục hồi — phải reset board tay.** Trên 4G, MQTT rớt với `esp-tls select() timeout` rồi reconnect fail vô hạn. Nguyên nhân gốc: UART nối A7680C ở 115200 baud **không có hardware flow control** → burst byte (TLS handshake/retransmit) gây RX overrun → khung PPP/HDLC hỏng → link tắc dù PPP IP vẫn "up". Vì `s_connected` còn `true` nên **không có** `NET_EVT_DISCONNECTED`, MQTT không được dọn/start lại sạch, và **không có watchdog** nào phát hiện "mạng còn kết nối nhưng MQTT chết kéo dài" → kẹt tới khi reset tay.

---

## PHẦN A — FSM service-gating (đúng thiết kế + tiết kiệm CPU)

### Thiết kế đích (ma trận service × state)

| Hoạt động | INIT | CONNECTING | NORMAL | STREAMING | OTA |
|---|---|---|---|---|---|
| Drain FIFO (luôn đọc, chống tràn FIFO) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Kalman ×7 + normalize `imu_win` | – | – | ✓ | ✓ | – |
| Impact/free-fall + pedometer + roll | – | – | ✓ | – | – |
| svc_ai inference (HAR + fall) | – | – | ✓ | – | – |
| Fill batch + publish `imu_stream` | – | – | – | ✓ | – |
| Telemetry `status` | – | – | ✓ | – | – |
| Alert `alert/fall` (event-driven) | – | – | ✓ | – | – |
| RSSI probe `+++`/ATO | – | – | ✓ | – | – |

**Nguyên tắc:** luôn `mpu6050_read_fifo()` mỗi lần thức (giữ FIFO sạch, tránh self-heal reset liên tục); chỉ phần **xử lý** mới gate theo state.

### File: [firmware/components/svc_imu/imu_service.c](firmware/components/svc_imu/imu_service.c) — `imu_processing_task` ([L100-282](firmware/components/svc_imu/imu_service.c#L100-L282))

Sau `mpu6050_read_fifo(...)` (giữ nguyên — luôn drain), tính state một lần và bỏ sớm các state không cần xử lý:
```c
system_state_t st = sys_manager_get_state();
bool is_normal    = (st == STATE_NORMAL);
bool is_streaming = (st == STATE_STREAMING);
if (!is_normal && !is_streaming) {
    continue;   // INIT/CONNECTING/OTA: đã drain FIFO, bỏ toàn bộ xử lý nặng
}
```
Thay biến cũ `bool is_streaming = ...` ([L124](firmware/components/svc_imu/imu_service.c#L124)) bằng khối trên (giữ `s_batch_data.count = 0` khi `!is_streaming`).

Trong vòng `for` mỗi sample:
- `mpu6050_raw_to_float` + đổi trục Body-frame: **luôn** (input cho Kalman).
- **Bọc trong `if (is_normal)`**: SVM/free-fall/impact tracking ([L170-198](firmware/components/svc_imu/imu_service.c#L170-L198)), pedometer ([L200-211](firmware/components/svc_imu/imu_service.c#L200-L211)), roll/posture ([L213-215](firmware/components/svc_imu/imu_service.c#L213-L215)).
- Kalman ×6 + normalize vào `imu_win` ([L217-233](firmware/components/svc_imu/imu_service.c#L217-L233)): **luôn** (đã `continue` ở trên nên chắc chắn NORMAL/STREAMING; cả hai đều cần).
- Fill batch ([L239-247](firmware/components/svc_imu/imu_service.c#L239-L247)): giữ nguyên `if (is_streaming && ...)`.

Khối debounce/HAR-gate bước + đọc `har_class` ([L129-155](firmware/components/svc_imu/imu_service.c#L129-L155)): chuyển vào nhánh `is_normal` (chỉ pedometer NORMAL cần).

Sau vòng `for`:
- Batch ready → callback ([L250-261](firmware/components/svc_imu/imu_service.c#L250-L261)): giữ `if (is_streaming ...)`.
- `svc_ai_process_window` ([L265](firmware/components/svc_imu/imu_service.c#L265)): đổi điều kiện thành **chỉ `if (is_normal)`**.
- Lưu steps NVS ([L273-276](firmware/components/svc_imu/imu_service.c#L273-L276)): bọc `if (is_normal)`.

### Trade-off (ghi nhận, chấp nhận)
- Không phát hiện ngã khi CONNECTING/OTA (AI chỉ NORMAL). Lưu ý ca MQTT kẹt nhưng PPP up: FSM **vẫn ở NORMAL** (MQTT_EVENT_DISCONNECTED không đổi state) → AI vẫn chạy, không tạo lỗ hổng.
- STREAMING không đếm bước/không track impact (đúng mục tiêu thu dataset). HAR "đóng băng" trong lúc stream — vô hại vì telemetry/bước không gửi ở STREAMING.
- Vào NORMAL từ state khác: `imu_win` cần ~2s (200 mẫu) đầy lại; fall cần cửa sổ xác nhận ~4s nên không gây alert giả.

---

## PHẦN B — Chống MQTT treo (tự phục hồi + giảm rớt)

### B1. Watchdog tự phục hồi (QUAN TRỌNG NHẤT — biến "reset tay" thành tự reset)
File: [firmware/components/svc_cloud/svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c), trong `svc_cloud_task` ([L372-502](firmware/components/svc_cloud/svc_cloud.c#L372-L502)). Các header cần (`esp_timer.h`, `esp_system.h`, `svc_network.h`) đã include sẵn.

Thêm biến cục bộ đầu task: `int64_t mqtt_down_since_us = 0;`
Thêm khối kiểm tra mỗi vòng lặp (đặt ở **cuối** thân `while(1)`, sau khối telemetry). Phục hồi 2 bậc:
```c
// Watchdog: mạng nói còn kết nối nhưng MQTT chết kéo dài → tự phục hồi (tránh kẹt phải reset tay)
if (!s_mqtt_connected && svc_network_is_connected()) {
    if (mqtt_down_since_us == 0) mqtt_down_since_us = esp_timer_get_time();
    int64_t down_ms = (esp_timer_get_time() - mqtt_down_since_us) / 1000;

    // Bậc 1 (~60s): ép socket/TLS mới sạch
    if (down_ms > 60000 && down_ms <= 150000) {
        static int64_t last_kick_us = 0;
        if (esp_timer_get_time() - last_kick_us > 30000000LL) { // tối đa 30s/lần
            ESP_LOGW(TAG, "Watchdog: MQTT kẹt %lld ms → stop/start client", down_ms);
            esp_mqtt_client_stop(s_mqtt_client);
            esp_mqtt_client_start(s_mqtt_client);
            last_kick_us = esp_timer_get_time();
        }
    }
    // Bậc 2 (~150s): A7680C/PPP wedge ở tầng dưới → chỉ reboot mới dọn
    else if (down_ms > 150000) {
        ESP_LOGE(TAG, "Watchdog: MQTT kẹt %lld ms → flush cache + esp_restart()", down_ms);
        svc_cloud_flush_cache_to_nvs();
        esp_restart();
    }
} else {
    mqtt_down_since_us = 0; // reset khi MQTT up (ca mất mạng thật đã có đường NET_EVT_DISCONNECTED xử lý)
}
```
Lưu ý: vòng lặp block tối đa 1s ở `xQueueReceive` nên watchdog có độ phân giải ~1s — đủ. Ngưỡng (60s/150s) có thể tinh chỉnh.

### B2. Chống UART overrun cho PPP (giảm rớt từ gốc)
File: [firmware/components/svc_network/svc_network.c](firmware/components/svc_network/svc_network.c), trong `svc_network_init_cellular`, khối cấu hình DTE ([L321-328](firmware/components/svc_network/svc_network.c#L321-L328)). Phóng to ring buffer UART + nâng prio task đọc UART để rút byte kịp trước khi overrun:
```c
dte_cfg.uart_config.rx_buffer_size  = 16384;  // mặc định 4096
dte_cfg.uart_config.tx_buffer_size  = 2048;   // mặc định 512
dte_cfg.uart_config.event_queue_size = 40;
dte_cfg.task_priority = 9;   // cao gần imu_task(10) để không bị bỏ đói khi crunch IMU+AI
dte_cfg.dte_buffer_size = 1024;
```
(Đối chiếu tên field với struct `esp_modem_dte_config_t` của phiên bản esp_modem đang cài; nếu khác thì map tương ứng.) **Không** đổi `flow_control` (vẫn NONE) vì chưa có dây RTS/CTS — xem Phần B phần cứng dưới.

### B3. Tune MQTT để phát hiện link chết nhanh & reconnect sạch
File: [firmware/components/svc_cloud/svc_cloud.c](firmware/components/svc_cloud/svc_cloud.c), `mqtt_cfg` trong `net_event_handler` ([L575-583](firmware/components/svc_cloud/svc_cloud.c#L575-L583)). Thêm vào struct (giữ nguyên broker/credentials/buffer hiện có):
```c
.session.keepalive            = 45,     // mặc định 120 → phát hiện socket chết nhanh hơn
.network.timeout_ms           = 15000,  // dư địa handshake TLS trên link 4G chậm
.network.reconnect_timeout_ms = 8000,
.task.priority                = 6,
.task.stack_size              = 6144,
```

### B4. (Tùy chọn — cần xác nhận) giảm tác nhân RSSI probe
File: [firmware/components/svc_network/svc_network.c](firmware/components/svc_network/svc_network.c). Vòng `+++`/ATO ([L53-122](firmware/components/svc_network/svc_network.c#L53-L122)) mỗi lần ngắt PPP ~5s, là tác nhân gây rớt ở NORMAL. Cân nhắc đổi mặc định `s_rssi_interval_ms` ([L34](firmware/components/svc_network/svc_network.c#L34)) từ `300000` → `0` (tắt), người dùng bật lại qua config nếu cần. **Đây là thay đổi chính sách (mất đo RSSI 4G định kỳ) — chỉ làm nếu được duyệt riêng; mặc định KHÔNG đụng trong vòng này.**

### (Phần cứng, dài hạn — KHÔNG nằm trong vòng implement này)
Nối RTS/CTS giữa ESP32-S3 ↔ A7680C, bật `ESP_MODEM_FLOW_CONTROL_HW` + set `rts_io_num`/`cts_io_num`. Đây là fix gốc cho PPP/TLS tin cậy. Ghi nhận như khuyến nghị.

---

## PHẦN D — Tối ưu thời gian khởi động (boot ~28s → ~vài giây)

Phần đầu init cellular hiện tốn ~28s phần lớn là **thừa**: 12s delay "chờ boot" (D2) + ~6s CFUN re-lock (D1/D3) + 10s URC wait. Ba mục dưới gỡ từng phần.

### D1 — Chỉ khóa LTE-only LẦN ĐẦU

**Vấn đề:** `svc_network_init_cellular` chạy nguyên chuỗi `CFUN=0 → CNMP=38 → CFUN=1` + `vTaskDelay(10000)` **mỗi lần boot** ([svc_network.c:391-405](firmware/components/svc_network/svc_network.c#L391-L405)). Nhưng `AT+CNMP=38` là **AUTO_SAVE** — module tự nhớ LTE-only trong NVRAM của nó, nên việc set lại + tắt/bật RF (CFUN cycle) + chờ 10s là **thừa** từ boot thứ 2 trở đi. Bỏ qua tiết kiệm ~15-25s mỗi lần khởi động.

**Giải pháp:** dùng cờ NVS (ESP32) đánh dấu "đã khóa LTE-only", kèm verify nhẹ bằng `AT+CNMP?` để an toàn khi đổi SIM/module factory-reset.

File: [firmware/components/svc_network/svc_network.c](firmware/components/svc_network/svc_network.c). Thêm `#include "nvs.h"` (hiện chưa có). Thay khối **6b** ([L385-405](firmware/components/svc_network/svc_network.c#L385-L405)) bằng:
```c
/// 6b. KHÓA LTE-ONLY (AT+CNMP=38, AUTO_SAVE) — chỉ cần làm LẦN ĐẦU.
/// Module tự nhớ trong NVRAM nên các boot sau bỏ qua CFUN cycle + chờ 10s → tiết kiệm ~15-25s.
uint8_t lte_locked = 0;
nvs_handle_t nh;
if (nvs_open("config", NVS_READONLY, &nh) == ESP_OK) {
    nvs_get_u8(nh, "lte_lock", &lte_locked);
    nvs_close(nh);
}

bool need_lock = true;
if (lte_locked) {
    // Fast-path: verify nhẹ phòng đổi SIM / module bị factory reset (cờ NVS bị "lệch")
    if (esp_modem_at(s_dce, "AT+CNMP?", at_out, 2000) == ESP_OK && strstr(at_out, "38")) {
        need_lock = false;
        ESP_LOGI(TAG, "LTE-only đã khóa sẵn (NVRAM module) → bỏ qua CFUN cycle, tiết kiệm boot");
    } else {
        ESP_LOGW(TAG, "Cờ NVS báo đã khóa nhưng module không ở CNMP=38 → khóa lại");
    }
}

if (need_lock) {
    esp_modem_at(s_dce, "AT+CFUN=0", at_out, 5000);
    vTaskDelay(pdMS_TO_TICKS(200));
    err = esp_modem_at(s_dce, "AT+CNMP=38", at_out, 3000);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "AT+CNMP=38 (LTE only) thất bại (err=%d)", err);
    } else {
        ESP_LOGI(TAG, "Đã khóa LTE-only (CNMP=38, AUTO_SAVE)");
        if (nvs_open("config", NVS_READWRITE, &nh) == ESP_OK) {
            nvs_set_u8(nh, "lte_lock", 1);   // đánh dấu để các boot sau bỏ qua
            nvs_commit(nh);
            nvs_close(nh);
        }
    }
    esp_modem_at(s_dce, "AT+CFUN=1", at_out, 10000);
    ESP_LOGI(TAG, "Đang chờ dọn dẹp UART URC và dò mạng LTE (10s)...");
    vTaskDelay(pdMS_TO_TICKS(10000));
}
```

**Lưu ý / trade-off:**
- Đường skip vẫn gửi 1 lệnh `AT+CNMP?` (~1s) để verify — rẻ hơn nhiều so với CFUN cycle + 10s wait. Nếu muốn nhanh tối đa có thể bỏ verify và tin hoàn toàn vào cờ NVS, nhưng kém an toàn khi đổi SIM/module.
- Khi skip, module đã tự attach LTE từ trạng thái lưu sẵn (sau `drv_a7680c_reset()` + 12s boot + `esp_modem_sync`); nếu thấy chưa kịp attach có thể thêm `vTaskDelay(pdMS_TO_TICKS(2000))` an toàn ở nhánh skip.
- Reset cờ: nếu cần ép khóa lại (đổi chiến lược mạng), xóa key `lte_lock` trong NVS namespace `config` (hoặc full erase NVS).
- Dùng chung namespace `config` (đã được svc_cloud/imu dùng) — không tạo namespace mới.

### D2 — Bỏ 12s "chờ boot sau reset" (reset đang là no-op)

**Vấn đề:** [svc_network.c:305](firmware/components/svc_network/svc_network.c#L305) có `vTaskDelay(pdMS_TO_TICKS(12000))` với ý "chờ module boot ~12s sau reset". Nhưng [drv_a7680c_reset()](firmware/components/drv_a7680c/drv_a7680c.c#L30-L40) hiện là **no-op** (phần GPIO RST bị comment vì board tắt nguồn khi đụng RST) → module **không bị reset**, vẫn đang chạy. Chờ 12s là phí trắng mỗi lần ESP khởi động lại. Cơ chế chờ-sẵn-sàng thật là vòng `esp_modem_sync` ngay sau ([L360-363](firmware/components/svc_network/svc_network.c#L360-L363), 15×1s) — log cho thấy nó OK ngay lần đầu (`SIM status` xuất hiện ngay sau delay).

**Sửa:**
- Cho `drv_a7680c_reset()` trả về cờ "đã reset thật" (hiện luôn `false` vì skip). Đổi chữ ký: `esp_err_t` → trả thêm thông tin, hoặc thêm out-param `bool *did_reset`.
- Trong `svc_network_init_cellular`: chỉ `vTaskDelay(12000)` khi reset **thật** xảy ra; ngược lại bỏ qua (hoặc settle ngắn ~300-500ms) rồi để vòng `esp_modem_sync` lo.
- (Phòng cold-boot thật khi có reset) có thể tăng nhẹ số retry sync. Vòng sync đã chịu được URC rác lúc boot nên gọi `esp_modem_new_dev` sớm không sao.
- **Tiết kiệm ~12s/boot.**

### D3 — Sửa verify CNMP fail (để fast-path D1 thực sự ăn)

**Triệu chứng (từ log):** `Cờ NVS báo đã khóa nhưng module không ở CNMP=38 → khóa lại` → verify thất bại nên vẫn chạy CFUN + 10s wait, D1 chưa tiết kiệm được gì.

**Chẩn đoán & sửa:**
- Điều kiện `esp_modem_at(..., "AT+CNMP?", at_out, 2000) == ESP_OK && strstr(at_out, "38")` fail vì **một trong hai**: (a) AT timeout 2s quá ngắn ngay sau loạt lệnh CPIN/IPR, hoặc (b) giá trị thật khác 38.
- Tăng timeout `AT+CNMP?` lên 3000-5000ms và **log nguyên `at_out`** để biết module trả gì.
- Nếu CNMP thật sự không giữ 38 qua reboot (AUTO_SAVE không như kỳ vọng trên A7680C) → bỏ verify, tin hẳn cờ NVS; hoặc chấp nhận khóa lại nhưng **bỏ 10s URC wait** ở nhánh đã-từng-khóa.

---

## PHẦN C — Cập nhật docs (sau khi A & B xong, phản ánh đúng hành vi mới)

- [firmware/components/svc_imu/README.md](firmware/components/svc_imu/README.md): nêu rõ STREAMING **không** chạy svc_ai/pedometer/impact; chỉ Kalman + fill batch. Thêm ma trận service × state (Phần A).
- [firmware/components/svc_cloud/README.md](firmware/components/svc_cloud/README.md): mô tả watchdog tự phục hồi 2 bậc (B1) và các tham số MQTT mới (B3).
- [firmware/components/svc_network/README.md](firmware/components/svc_network/README.md): ghi buffer UART DTE đã phóng to + prio task (B2); cảnh báo thiếu hardware flow control; ghi cơ chế khóa LTE-only **một lần** qua cờ NVS `lte_lock` (Phần D); ghi cách chọn transport (cờ force-wifi / activity-detect) + dập spam `Rx Break` (Phần F).
- [firmware/CLAUDE.md](firmware/CLAUDE.md): mục "FSM" thêm ma trận service × state; mục "Luồng dữ liệu" làm rõ STREAMING bỏ AI; thêm 1 dòng về watchdog MQTT.
- (Nếu tồn tại) cập nhật `datn-agent-skills/project_setup/firmware_architecture_update_080526.md` cho khớp.

---

## PHẦN E — Toàn vẹn dữ liệu thu (data-collection gap-detection) — chủ yếu FE/BE

> Quyết định nền: [DECISIONS.md D-025](datn_agent_skills/project_setup/architecture/DECISIONS.md). Mục tiêu: đảm bảo file `.txt` SisFall **liên tục nhân quả** bằng *kiểm chứng*, không bằng *cầu mong transport*. Phần lớn KHÔNG đụng firmware.

### E1 — Gap-detection ở FE (cốt lõi, KHÔNG đụng firmware)
Payload `imu_stream` đã có `ts`(ms), `fs`=100, `cnt`=50 ([svc_cloud.c:422-426](firmware/components/svc_cloud/svc_cloud.c#L422-L426)). Khi FE buffer 100Hz (trang `data-collection`, hook `useVerification.ts` — xem session report 2026-06-23):
- Giữ `lastTs`; mỗi batch nhận: kỳ vọng `Δts ≈ cnt/fs*1000` (=500ms) và `cnt==50`.
- Nếu `Δts` lệch quá ngưỡng jitter (vd > 750ms) hoặc `cnt != 50` → đánh dấu trial **có gap**: hiện cảnh báo đỏ + cho phép huỷ/đo lại; KHÔNG cho submit `.txt` "âm thầm hỏng" (hoặc submit kèm cờ `has_gap` để BE từ chối).
- (Tuỳ chọn) BE kiểm tra lại contiguity khi nhận `samples[]` ở `POST /sessions/{id}/data` như một lớp chặn thứ hai.

### E2 — (Tuỳ chọn) thêm `seq` vào payload (firmware, nhỏ)
Nếu muốn bắt gap chắc hơn `ts` (đề phòng `ts` jitter): thêm 1 biến đếm tăng đơn điệu mỗi batch trong `svc_cloud_task`, `cJSON_AddNumberToObject(root, "seq", s_stream_seq++)`. FE kiểm `seq` liên tục (+1). Reset `seq` khi vào STREAMING. Chi phí ~3 dòng.

### E3 — Hạ auto-stop xuống "van an toàn" (nếu đã/đang implement)
Nếu cơ chế auto-stop khi `publish` block >500ms đã được thêm: **không coi là cơ chế chính**. Yêu cầu tối thiểu nếu giữ: log to (`ESP_LOGW`), đẩy lý do lên FE (vd qua `config/status` hoặc 1 field trạng thái) để người thu biết "trial bị cắt vì mạng", và phủ **cả** đường rớt ở `svc_cloud_enqueue_imu_batch` (queue đầy) lẫn publish block. Khi đã có E1 thì auto-stop gần như thừa — ưu tiên để stream chạy và chỉ loại trial nếu E1 phát hiện gap thật.

### E4 — Không phình UART TX buffer như giải pháp
Giữ TX buffer nhỏ/mặc định. Lý do ở D-025: bufferbloat + che tín hiệu backpressure (làm E3 kém nhạy), không fix root (thiếu CTS/RTS). (RX buffer thì vẫn tăng theo B2 vì phục vụ chống overrun handshake TLS — khác hướng.)

### Khuyến nghị vận hành
Thu dataset → chạy **WiFi** (macro `NETWORK_USE_CELLULAR` off). 4G để dành production (telemetry nhẹ + alert). E1 vẫn áp dụng cho cả hai để chắc chắn data sạch.

---

## PHẦN F — Auto-detect module 4G (đã sửa theo log thực tế): có module → 4G, không → WiFi

> Quyết định nền: [DECISIONS.md D-026](datn_agent_skills/project_setup/architecture/DECISIONS.md). Fallback ĐÃ TỒN TẠI ([app_main.c:64-67](firmware/main/app_main.c#L64-L67)). **CẢNH BÁO — bản "5s AT-probe" trước đó SAI**: log cho thấy module *có mặt* vẫn phun `Rx Break` liên tục ~7s→24s rồi mới đáp AT (~31s). AT-response là tín hiệu **MUỘN** → probe ngắn sẽ kết luận "mất module" **oan** và rơi WiFi sai. Phải đổi nguyên tắc.

### F0 — Việc làm NGAY (bất kể hướng nào): dập spam `Rx Break`
`Rx Break` lúc module boot là vô hại. Trong `svc_network_init_cellular` (trước khi tạo modem):
```c
esp_log_level_set("uart_terminal", ESP_LOG_ERROR);   // (và/hoặc "esp_modem")
```

### F-CHECK — ĐÃ CÓ ĐÁP ÁN (từ 2 log thực, 2026-06-30)
- **Module CÓ** → `Rx Break` phun ngay lúc boot (bus có hoạt động).
- **Module KHÔNG** → bus **IM HOÀN TOÀN** (0 break, 0 byte) suốt 40s.
⇒ Phân biệt present/absent bằng **hoạt động bus UART** là tin cậy → chốt **Hướng A** (sniff bus). Không cần pull-up đặc biệt (line rảnh đã im).

### Thủ phạm 40s — cú `+++` escape block ~25s (PHẢI fix)
Log absent: attempt 6/10 @9567ms → gửi `+++` thoát DATA mode → `esp_modem` chờ ACK COMMAND mode → **kẹt ~25s** (tới attempt 7 @34577ms). Không có module thì +++ luôn tốn full timeout. **Tuyệt đối không `+++` khi bus im.**

### Hướng A (CHỐT) — Sniff bus UART trước khi giao cho esp_modem
1. Trước `esp_modem_new_dev`: `uart_driver_install` (có event queue) trên cổng modem.
2. Cửa sổ **~5s** đọc event queue: thấy **bất kỳ** `UART_BREAK`/`UART_DATA` → **PRESENT**; im suốt 5s → **ABSENT**.
   - Chọn ~5s (không phải ~2s) vì module boot đôi khi phun break trễ vài giây; absent đã im tuyệt đối nên 5s vẫn deterministic.
3. **PRESENT** → `uart_driver_delete` → `esp_modem_new_dev` → full init. **Vòng sync được rút gọn còn 10 lần (10s) thay vì 35s**, và `+++` được gửi sớm ở giây thứ 4. Lý do (theo log mới): nếu sniff bắt được tín hiệu ngay lập tức, đa phần là do module đang kẹt ở DATA mode (warm reboot) và liên tục nhả LCP echo. Đẩy `+++` sớm giúp thoát mạch ngay lập tức thay vì bắt người dùng đợi mòn mỏi.
4. **ABSENT** → `uart_driver_delete` → WiFi ngay (**~5s thay vì 40s**).
- Module kẹt DATA mode sau warm-reboot vẫn phát LCP echo → vẫn là "hoạt động bus" → sniff bắt được; nên ~5s đủ phủ cả ca này.

### F2 — Dọn tài nguyên ở nhánh ABSENT (bắt buộc, tránh leak)
Trước khi sang WiFi: nếu đã tạo thì `esp_modem_destroy(s_dce)` + `s_dce=NULL`; `esp_netif_destroy(s_ppp_netif)` + `esp_event_handler_unregister` 2 handler PPP + `s_ppp_netif=NULL`. (Nhánh sniff-absent thì chỉ cần `uart_driver_delete` vì chưa tạo esp_modem.)

### Hướng B — Cờ force-wifi (giữ làm tùy chọn phụ)
Vẫn hữu ích để **ép** WiFi khỏi phải sniff (board thu data biết chắc không gắn module): Kconfig `CONFIG_NETWORK_FORCE_WIFI` hoặc NVS `net_mode` → `app_main` bỏ qua cả bước sniff. Không bắt buộc khi đã có Hướng A nhanh.

---

## Verification (end-to-end)

Build + flash + monitor qua skill `esp-idf-build-manager`. Test theo từng phần:

**Phần A (gating):**
1. STREAMING (`start_stream`): log **không còn** `SVC_AI: --- AI INFERENCE RESULT ---`/posture; vẫn có `imu_stream` publish đều.
2. NORMAL (`stop_stream`): AI inference + telemetry `status` + đếm bước hoạt động lại; chuyển state qua lại nhiều lần không kẹt, `imu_win` phục hồi đúng.

**Phần B (chống treo):**
3. Chạy 4G ≥ 30 phút NORMAL và ≥ 30 phút STREAMING: số `select() timeout` / `MQTT Disconnected` giảm rõ; nếu rớt thì reconnect lại trong vài giây.
4. Mô phỏng kẹt (vd rút/chặn đường ra broker trong khi PPP vẫn up): xác nhận watchdog log Bậc 1 (stop/start) ~60s, và nếu vẫn kẹt thì Bậc 2 `esp_restart()` ~150s — thiết bị **tự** quay lại, không cần bấm reset.
5. Đối chiếu backend: telemetry/imu_stream/alert nhận liên tục, không có khoảng trống dài; alert cache (NVS/RAM) gửi lại đúng sau reboot.

**Phần D (LTE-only một lần):**
6. **Boot lần đầu** (sau full erase NVS): log có `Đã khóa LTE-only (CNMP=38, AUTO_SAVE)` + chạy CFUN cycle + chờ 10s.
7. **Reboot lần sau**: log có `LTE-only đã khóa sẵn ... bỏ qua CFUN cycle`, **không** còn 10s wait → đo thời gian từ reset tới `PPP got IP` giảm ~15-25s so với trước.
8. Vẫn vào được DATA mode / cấp IP bình thường ở cả hai trường hợp; thử đổi SIM/factory-reset module để xác nhận nhánh "khóa lại" hoạt động.

**Phần E (toàn vẹn data thu):**
9. Thu 1 trial trên WiFi, mạng tốt: FE không báo gap, `.txt` có `sample_count` = đúng `duration × 100`, `ts` các batch cách đều 500ms.
10. Cố ý gây gap (bóp băng thông / chạy 4G yếu): FE **phát hiện và cảnh báo** trial có gap, không cho submit âm thầm (hoặc BE từ chối file `has_gap`).

**Phần F (detect trên bus UART):**
11. **Không module:** sniff thấy bus im ~5s → sang WiFi trong **~5s** (đo trước fix là ~40s); **không** còn cú `+++` block 25s trong log.
12. **Có module:** sniff thấy `Rx Break`/byte ngay lập tức → vào cellular, gửi `+++` lúc giây thứ 4 để bẻ khóa DATA mode. Thành công thoát ra và lên PPP/MQTT bình thường chỉ trong <10s.
13. **F0:** log `Rx Break` đã tắt. **F2:** rút/cắm module nhiều lần, heap không tụt dần (không leak DCE/netif). Ca MCU warm-reboot khi module đang DATA mode: sniff vẫn bắt được (LCP echo) → vào cellular, không nhầm WiFi.

**Phần C:** đọc lại docs khớp hành vi mới.
