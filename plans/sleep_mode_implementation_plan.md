# Plan triển khai: Live 4G signal quality qua CMUX cho field `rssi`

> **Lưu ý lịch sử:** File này trước đây là "Sleep Mode (Automatic Light Sleep)". Sau khi rà soát code thật, scope đã đổi:
> - **Bỏ MCU light sleep / esp_pm** khỏi demo — pin 1200mAh đủ; cơ chế PCNT đếm ngắt IMU không chạy được trong light sleep nên không đáng làm cho demo.
> - **Giữ PPPoS, không rewrite sang AT-MQTT** — chỉ cần khi pin là ràng buộc cứng (future work).
> - Việc thực sự đáng làm và được chốt: **bật CMUX để đọc cường độ sóng 4G (CSQ) live** điền vào field `rssi` đang publish nhưng luôn = 0 trên 4G.
> File này là spec để implement đúng phần đó. Có thể đổi tên file thành `cmux_signal_quality_plan.md` nếu muốn.

---

## 1. Context (vì sao làm)
Gói telemetry MQTT `eldercare/{device_id}/status` **đã** chứa field `rssi` (xem `firmware/components/svc_cloud/svc_cloud.c`, trong vòng publish telemetry: `cJSON_AddNumberToObject(root, "rssi", svc_network_get_rssi());`). Nhưng khi chạy 4G LTE, giá trị **luôn = 0** vì:
- Getter `svc_network_get_rssi()` (trong `firmware/components/svc_network/svc_network.c`) chỉ đọc được RSSI khi đang là WiFi; với 4G nó `return 0` kèm comment "chưa có CMUX".
- Module A7680C đang ở **PPPoS DATA mode** (`esp_modem_set_mode(s_dce, ESP_MODEM_MODE_DATA)`), nên không gửi được lệnh AT (`AT+CSQ`) trong khi đang truyền data.

**CMUX** (multiplexing 3GPP 27.010) cho phép esp_modem chạy **PPP/MQTT và lệnh AT song song** trên các kênh ảo của cùng một UART → đọc được CSQ live mà không cắt MQTT.

Đã xác nhận component `espressif__esp_modem` **v1.4.2** (trong `firmware/managed_components/`) hỗ trợ sẵn:
- `ESP_MODEM_MODE_CMUX` (enum trong `esp_modem_c_api_types.h`)
- `esp_err_t esp_modem_set_mode(esp_modem_dce_t *dce, esp_modem_dce_mode_t mode);`
- `esp_modem_get_signal_quality(dce, &rssi, &ber)` (sinh từ `esp_modem_command_declare.inc`)

## 2. Phạm vi
- **Chỉ sửa firmware đường 4G.** Không đổi protocol (field `rssi` đã tồn tại), **không** đụng backend/frontend, **không** đụng nhánh WiFi, **không** đụng power/sleep.
- File chạm vào: `svc_network.c`, `svc_network.h`, và 1 dòng doc trong `firmware.md`. **Không** sửa `svc_cloud.c`.

## 3. Thay đổi cụ thể

### 3.1. `firmware/components/svc_network/svc_network.c`

**(a) Đổi bring-up sang CMUX, có fallback.** Tìm chỗ cuối `svc_network_init_cellular()` hiện đang gọi:
```c
err = esp_modem_set_mode(s_dce, ESP_MODEM_MODE_DATA);
```
Đổi thành thử CMUX trước, lỗi thì fallback DATA (giữ đường mạng luôn lên được là ưu tiên cao hơn việc có signal):
```c
/// CMUX: ghép kênh UART để PPP (data) và lệnh AT chạy song song → đọc được CSQ
/// live trong lúc MQTT vẫn truyền. Nếu module/đường truyền không ổn với CMUX,
/// fallback về DATA mode thuần (rssi 4G sẽ là 0) để hệ thống vẫn hoạt động.
err = esp_modem_set_mode(s_dce, ESP_MODEM_MODE_CMUX);
if (err != ESP_OK)
{
    ESP_LOGW(TAG, "CMUX mode thất bại (err=%d), fallback DATA mode", err);
    err = esp_modem_set_mode(s_dce, ESP_MODEM_MODE_DATA);
}
if (err != ESP_OK)
{
    ESP_LOGE(TAG, "Chuyển PPP mode thất bại (err=%d)", err);
    return err;
}
```
> PPP vẫn nhận IP và bắn `IP_EVENT_PPP_GOT_IP` → `ppp_ip_event_handler` như cũ ở cả 2 mode; **không** đổi handler đó.

**(b) Lưu CSQ đọc lúc init làm giá trị khởi điểm.** Chỗ đang đọc CSQ chẩn đoán (`esp_modem_at(s_dce, "AT+CSQ", at_out, 2000)`), thêm parse và lưu vào biến cache (xem 3.1c). Tối thiểu: gọi `esp_modem_get_signal_quality()` một lần ngay sau khi vào CMUX để có giá trị đầu.

**(c) Hoàn thiện `svc_network_get_rssi()` cho 4G — có cache + rate-limit.** Thêm các static ở đầu file (gần `s_dce`):
```c
static int s_cell_rssi_dbm = 0;             // cache RSSI 4G (dBm), 0 = chưa có
static TickType_t s_cell_rssi_last = 0;     // mốc tick lần refresh gần nhất

/// Quy đổi chỉ số CSQ (0..31) của AT+CSQ sang dBm. 99 = chưa bắt được sóng.
static int csq_to_dbm(int csq)
{
    if (csq >= 0 && csq <= 31) return -113 + 2 * csq;
    return 0;  // 99 hoặc ngoài dải → coi như chưa có sóng
}
```
Sửa thân `svc_network_get_rssi()` (giữ nguyên nhánh WiFi), thay phần `return 0` của 4G:
```c
int svc_network_get_rssi(void)
{
    // Nhánh WiFi: giữ nguyên như hiện tại (esp_wifi_sta_get_ap_info → ap.rssi)
    ...

    // Nhánh 4G (CMUX): đọc CSQ qua esp_modem, rate-limit ~10s để khỏi
    // chịu round-trip AT blocking trên mỗi chu kỳ telemetry.
    if (s_dce != NULL && s_connected)
    {
        TickType_t now = xTaskGetTickCount();
        if (s_cell_rssi_last == 0 ||
            (now - s_cell_rssi_last) >= pdMS_TO_TICKS(10000))
        {
            int csq = 99, ber = 0;
            if (esp_modem_get_signal_quality(s_dce, &csq, &ber) == ESP_OK)
                s_cell_rssi_dbm = csq_to_dbm(csq);
            s_cell_rssi_last = now;
        }
        return s_cell_rssi_dbm;
    }
    return 0;
}
```
> Quy đổi sang dBm để **đồng nhất đơn vị với nhánh WiFi** (WiFi trả dBm âm). Backend/frontend nhận cùng kiểu số.

### 3.2. `firmware/components/svc_network/include/svc_network.h`
Cập nhật doc-comment của `svc_network_get_rssi()` — bỏ "0 nếu dùng 4G LTE (đợi làm CMUX sau)", đổi thành:
```c
/**
 * @brief Lấy RSSI kết nối hiện tại (dBm).
 * @return RSSI (dBm, âm) cho WiFi; với 4G (qua CMUX) là dBm quy từ CSQ;
 *         0 nếu chưa có sóng / chưa kết nối.
 */
int svc_network_get_rssi(void);
```

### 3.3. KHÔNG sửa `svc_cloud.c`
Field `rssi` đã được publish sẵn trong gói status — đây là điểm tái sử dụng. Không thêm field/topic.

### 3.4. Cập nhật doc kiến trúc (bắt buộc theo rule codebase_context)
`datn-agent-skills/project_setup/architecture/firmware.md`:
- Ở mô tả `svc_network`: ghi chú đã bật **CMUX** (PPP + AT song song; cấp `rssi` 4G cho telemetry).
- Cập nhật dòng `> **Cập nhật lần cuối:**` sang ngày thực hiện.

## 4. Hàm/tài nguyên tái sử dụng (đừng viết lại)
- `esp_modem_get_signal_quality()` — không tự parse chuỗi `AT+CSQ`.
- `esp_modem_set_mode(..., ESP_MODEM_MODE_CMUX)` — không tự cài CMUX.
- Field `rssi` trong gói status (`svc_cloud.c`) và getter `svc_network_get_rssi()` — đã có, chỉ điền giá trị thật.
- `ppp_ip_event_handler` + event `NET_EVT_CELLULAR_CONNECTED` — giữ nguyên.

## 5. Rủi ro & giảm thiểu
- **Ổn định CMUX trên A7680C (rủi ro chính):** CMUX đổi đóng khung đường data → **bắt buộc test lại MQTT + alert/fall thật chạy qua CMUX** trên phần cứng 4G. Giảm thiểu: fallback DATA mode khi CMUX init lỗi (mục 3.1a).
- **AT blocking trên task `svc_cloud`:** giảm bằng cache + rate-limit ~10s (mục 3.1c) — `get_rssi()` không gọi AT mỗi lần publish.

## 6. Verification (test end-to-end trên phần cứng 4G)
1. Bật `#define NETWORK_USE_CELLULAR 1` trong `firmware/main/hardware_config.h`; build + flash + monitor (skill `esp-idf-build-manager`).
2. **Regression (quan trọng nhất):** log có `PPP got IP`, MQTT connect, gói `status` publish đều; chủ động kích một fall event để chắc `alert/fall` (QoS1) vẫn lên broker qua CMUX.
3. Subscribe `eldercare/<device_id>/status` (vd `mosquitto_sub` hoặc `tools/fake_device.py`): `rssi` là **dBm âm hợp lý** (vd −60…−95), không còn 0.
4. Che/giảm anten → `rssi` tụt theo (chứng minh live, không phải giá trị tĩnh); đối chiếu log `Signal: +CSQ:` lúc init.
5. Build lại bản **WiFi** (comment `NETWORK_USE_CELLULAR`) → `rssi` vẫn trả RSSI WiFi (không regression nhánh WiFi).

## 7. Tiết kiệm pin (VẬN HÀNH — không cần code, độc lập với CMUX)
Đây là lever tiết kiệm pin lớn nhất ở thời điểm hiện tại, và **đã có sẵn cơ chế trong code** — không phải việc implement, chỉ là cấu hình:
- **Telemetry interval (đã runtime-tunable):** đổi qua lệnh `set_interval` từ dashboard, lưu NVS (`svc_cloud.c` — `s_telemetry_interval_ms`, default 5s). **Demo:** chỉnh 1s/5s cho nhìn live. **Triển khai thật:** đặt **60s** (1 phút). **Không cần build lại firmware.**
- **MQTT keepalive:** code không set → esp_mqtt mặc định **120s**, đã hợp lý → **để nguyên** (đừng đẩy quá dài hơn timeout NAT nhà mạng, kẻo TCP bị reap → reconnect tốn hơn).
- **Lưu ý:** alert ngã là event-driven, **bắn tức thì bất kể interval** (`ai_event_handler`) → giãn interval chỉ làm telemetry lên dashboard chậm hơn, KHÔNG làm chậm cảnh báo.
- Tương thích hoàn toàn với CMUX (tham số tầng app, không đụng transport).

## 8. Ngoài scope (ghi nhận, KHÔNG làm trong plan này)
- MCU light sleep / esp_pm — đã loại.
- **CSCLK+DTR hardware sleep (giữ PPPoS, future work):** cho A7680C ngủ UART/baseband qua chân DTR (set `AT+CSCLK=1` một lần lúc init, rồi điều khiển bằng GPIO). **Kỳ vọng thực tế ~vài mA tiết kiệm thêm trên sàn idle-DRX (~10–20mA), KHÔNG phải 1–2mA** (1–2mA là PSM, mà PSM buông kết nối). Cần: đi thêm **dây DTR + RING** (hiện chỉ có PWRKEY), tắt LCP echo của PPP, giãn keepalive, dùng `uart_set_wakeup_threshold` cho downlink. **Loại trừ lẫn nhau với CMUX** trên cùng link → chỉ cân khi pin thành ràng buộc cứng.
- Modem deep sleep PSM + chuyển AT-MQTT thay PPPoS — chỉ khi pin là ràng buộc cứng. PPPoS được giữ vì: chung 1 codebase MQTT cho WiFi(dev) lẫn 4G(prod), full IP stack (HTTP fallback, OTA, TLS qua mbedTLS), ESP-MQTT bền (QoS1/reconnect/LWT).

## 8. Future Work: Chế độ Hardware Sleep với CSCLK + DTR (Giữ nguyên PPPoS)
Trong tương lai, nếu dung lượng Pin trở thành rào cản cứng, ta có thể cân nhắc triển khai chế độ Sleep một phần cho Module 4G (giảm dòng tĩnh Idle xuống mức ~10-20mA, thay vì 1-2mA như chế độ PSM cắt đứt kết nối). Cơ chế này dựa trên việc tắt UART và Baseband một phần qua chân DTR.
Để đạt được độ ổn định (giữ socket MQTT/TCP sống trên PPPoS) với cơ chế này, bắt buộc phải thỏa mãn 4 điều kiện kỹ thuật:
1. **Interval Telemetry phải đủ dài:** Phải giãn tần suất telemetry lên > 30-60s (thay vì 5s). Ở mức 5s, thời gian RRC_CONNECTED (Inactivity tail timer của nhà mạng, thường ~10s) sẽ nuốt trọn toàn bộ cửa sổ ngủ, modem sẽ không bao giờ thực sự ngủ được.
2. **Quản lý triệt để Keepalive & LCP Echo:** Phải chủ động tắt chu kỳ LCP Echo của bộ giao thức PPP trong lwIP, đồng thời giãn thời gian Keepalive của MQTT ra đủ rộng để tránh đánh thức modem liên tục hoặc gây Teardown kết nối PPP do mất gói.
3. **Sử dụng `uart_set_wakeup_threshold` cho Downlink:** Không được tin cậy vào ngắt phần cứng chân RING/RI khi hoạt động ở PPPoS Data Mode. Chân RI thường chỉ chuẩn đối với Call/SMS/URC (ở AT command mode). Để an toàn nhận data IP downlink (VD: Lệnh `set_interval` từ MQTT), cần sử dụng cấu hình Wakeup bằng ngõ vào RX của ESP32.
4. **Đo đạc dòng thực tế (Current Profiling):** Phải dùng Oscilloscope / Power Profiler đo dòng tiêu thụ thực tế để kỳ vọng chuẩn xác ở mức 10-20mA (Idle-DRX registered), tuyệt đối không nhầm lẫn với dòng 1-2mA của cấu hình PSM.
