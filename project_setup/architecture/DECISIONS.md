# DECISIONS — Nhật ký quyết định thiết kế (ADR rút gọn)

> **Cập nhật lần cuối:** 2026-06-30
> Ghi "TẠI SAO" của các quyết định không hiển nhiên — để agent/người đọc khỏi tái suy luận (rất tốn). Mỗi mục: bối cảnh → quyết định → lý do. Mới nhất ở trên.

---

### D-026 · Tự động chọn đường mạng theo hiện diện module 4G (runtime fail-fast); tổng hợp điểm yếu A7680C (2026-06-30)
- **Bối cảnh — điểm yếu của module A7680C như đang dùng trong đồ án (vì sao 4G *không* hợp với streaming):**
  1. **Không có hardware flow control (RTS/CTS) đấu nối.** Mạch breakout không kéo CTS/RTS → `ESP_MODEM_FLOW_CONTROL_NONE`. Khi nghẽn (burst handshake TLS / retransmit / stream), UART overrun → **rơi byte** → hỏng khung PPP/HDLC (FCS err) → TCP retransmit dồn → **"kẹt MQTT tĩnh"** (PPP IP còn up nhưng socket TCP chết). Đây là điểm yếu số 1 (gốc của D-024).
  2. **UART 115200 baud ≈ trần ~11.5 KB/s.** Đủ cho telemetry nhẹ, **marginal** cho stream 100Hz liên tục cộng burst TLS.
  3. **Đường vòng PPPoS:** ESP → UART → PPP → modem → trạm phát. Mỗi lớp thêm độ trễ & điểm hỏng so với WiFi native MAC; jitter mạng đẩy latency vọt 200-500ms.
  4. **Breakout không có chân PWRKEY** → không bật/tắt nguồn module chủ động được, chỉ dựa mạch auto-power-on (tụ) (D-019).
  5. **Chân RST bị vô hiệu** — đụng RST là module tắt ngúm trên board này (không auto-power-on sau reset) → firmware **không thể hard-reset module** để gỡ wedge → phải reboot cả MCU (watchdog B1/D-024) (D-019).
  6. **DATA mode chặn AT** — đo RSSI phải `+++`/`ATO` (đứt link 15-20s mỗi lần); CMUX (mux AT+PPP) **không chạy** trên A7680C+PPPoS → loại (D-022).
  7. **URC rác lúc boot** dễ đâm vào comms sớm → cần sync cẩn thận.
  → Tổng hợp 4+5+6: khi module/PPP wedge, **không có đường phục hồi in-band**, chỉ còn reboot MCU.
- **Hệ quả kiến trúc:** stream thu dataset (tải cao) qua 4G không tin cậy → **WiFi cho collection/bench/dev**; telemetry production (nhẹ) chấp nhận 4G **nhờ watchdog** chống kẹt tĩnh. Vì một board có thể chạy ở 2 ngữ cảnh (đeo thật vs để bàn), việc chọn đường mạng nên **tự động theo phần cứng hiện diện**, không cứng hoá compile-time.
- **Quyết định:**
  - **Bỏ macro compile-time** `NETWORK_USE_CELLULAR` (chat nhắc nhưng **không tồn tại** trong code). Fallback runtime đã có ở [app_main.c:64-67](firmware/main/app_main.c#L64-L67) (`svc_network_init_cellular() != ESP_OK` → WiFi).
  - **⚠️ Không detect bằng "AT-probe timeout"**: log cho thấy module *có mặt* phun `Rx Break` ~7s→24s rồi mới đáp AT ~31s → AT-response MUỘN, probe ngắn sẽ false-negative module thật.
  - **CHỐT — detect bằng HOẠT ĐỘNG BUS UART** (đã đo bằng 2 log 2026-06-30): module CÓ → có `Rx Break`/byte ngay; module KHÔNG → **bus im tuyệt đối** (0 break, 0 byte) suốt 40s. ⇒ sniff raw UART event queue ~5s: có `UART_BREAK`/`UART_DATA` → present (rồi cho boot ~30s); im 5s → absent → WiFi. Phát hiện vắng module: **40s → ~5s**.
  - **Fix thủ phạm 40s — cú `+++`:** log absent cho thấy `esp_modem_set_mode(COMMAND)` (gửi `+++` thoát DATA mode khi AT fail) **kẹt ~25s** chờ ACK khi không có module. ⇒ **chỉ `+++` ở nhánh present** (đã thấy hoạt động bus); tuyệt đối không `+++` khi bus im. Giữ `+++` cho ca module-kẹt-DATA sau MCU warm-reboot (D-024) — chỉ gate lại.
  - **Cờ force-wifi** (Kconfig `CONFIG_NETWORK_FORCE_WIFI`/NVS `net_mode`) giữ làm tùy chọn ép WiFi khỏi sniff (board thu data không gắn module).
  - **Phải làm kèm:** dập spam log (`esp_log_level_set("uart_terminal", ESP_LOG_ERROR)`) + dọn DCE/netif PPP ở nhánh absent (tránh leak).
- **Lý do:** (1) Sniff bus là discriminator điện **đã được log xác nhận** (absent = im tuyệt đối) — không còn "đu dây". (2) Cú `+++` block 25s là phần lớn của 40s; gate nó theo hoạt động bus là cú ăn lớn nhất. (3) Boot module ~25-31s là bản chất phần cứng, KHÔNG cắt ngắn nhầm thành "mất module" (vì thế sniff dựa hoạt động *sớm*, không dựa AT *muộn*). (4) Khớp D-025 (thu data trên WiFi); cờ force-wifi để chủ động khi cần.
- **Trạng thái (đã implement & verify 2026-06-30):** sniff trong `svc_network_init_cellular` — pull-up RX + xả event rác + ngưỡng **≥5 event bền** (chống false-positive do glitch chân thả nổi), cửa sổ **10s**, sync kiên nhẫn **35s**, `+++` chỉ khi `saw_data`. Log thực: **không module → WiFi ~11s** (trước ~40s), hết `Rx Break` flood, hết `+++` block. Chi tiết: [svc_network README §3.1](../../../firmware/components/svc_network/README.md).

---

### D-025 · Toàn vẹn dữ liệu thu (data-collection): detect-and-discard bằng timestamp, không drop/teardown âm thầm (2026-06-30)
- **Bối cảnh:** Thu dataset SisFall qua stream `imu_stream` (device → MQTT → backend → **FE buffer `useRef`** → `.txt`). Drop batch giữa luồng → file `.txt` đứt nhân quả (nhảy thời gian) → hỏng eval/train. Đề xuất ban đầu: auto-stop stream khi `publish` bị chặn >500ms (phát `CLOUD_CMD_STOP_STREAM`) + phình UART TX buffer 2KB→8KB.
- **Nguyên lý nền:** KHÔNG thể backpressure cảm biến 100Hz chạy tự do — chặn consumer thì FIFO MPU6050 tràn → self-heal reset FIFO (`imu_service.c`) → **vẫn mất mẫu**. Vậy khi link không kham nổi chỉ có 2 đường: **(1) detect-and-discard** (cứ stream, phát hiện gap, loại trial) hoặc **(2) buffer-to-storage** (đệm PSRAM/flash, tách rate). Auto-stop chỉ là biến thể *thô* của (1) — discard sớm kể cả khi chưa hề có gap.
- **Quyết định:**
  - **Chính — detect-and-discard ở FE/backend bằng metadata SẴN CÓ:** payload đã mang `ts`(ms), `fs`=100, `cnt`=50 → hai batch liên tiếp phải cách `Δts ≈ cnt/fs*1000 = 500ms` và `cnt==50`. FE kiểm tra liên tục khi buffer; `Δts` nhảy ~1000ms+ → có gap → **cảnh báo + huỷ/đánh dấu trial để đo lại**. KHÔNG cần đổi firmware. (Tuỳ chọn sạch hơn: thêm `seq` tăng đơn điệu vào payload.)
  - **Thu data bằng WiFi** (macro `NETWORK_USE_CELLULAR` dev/prod, D-009) để giảm gap từ gốc; 4G để dành production telemetry nhẹ.
  - **Auto-stop → hạ xuống "van an toàn" tuỳ chọn**, nếu giữ phải log to + đẩy trạng thái "trial aborted: network" lên FE + phủ *cả hai* đường rớt (queue enqueue đầy lẫn publish block). Không phải cơ chế chính.
  - **Không dựa vào phình TX buffer**: giữ nhỏ/bỏ.
- **Lý do:** (1) Auto-stop KHÔNG đảm bảo zero-loss như tuyên bố: queue `s_imu_queue` depth-5 có thể tràn → `svc_imu` drop âm thầm *trước khi* publish kịp block 500ms. (2) "Kiểm chứng > cầu mong": verify contiguous bằng `ts` không phụ thuộc độ tin cậy transport, chạy đúng trên cả WiFi/4G, và cho phép giữ trial khi thực tế không có gap (thay vì cắt vụn trên 4G). (3) TX buffer to gây bufferbloat + làm publish lâu mới block → detector 500ms kém nhạy (hai thay đổi đánh nhau); root cause là thiếu CTS/RTS (xem D-024), buffer chỉ dời vách đá chứ không xoá. (4) FE đã là "bể chứa" trong pipeline hiện tại → không cần thêm buffer-to-storage on-device (over-engineering cho dataset verify trial ngắn).

---

### D-024 · Tối ưu FSM Gating, MQTT Watchdog & Boot Fast-path (2026-06-29)
- **Quyết định:** (1) **FSM Gating (`svc_imu`)**: Chỉ chạy AI inference, đếm bước, và tính impact ở `STATE_NORMAL`; bỏ qua ở `STATE_STREAMING` (chỉ thu thập/scale batch data). (2) **MQTT Watchdog (`svc_cloud`)**: Phục hồi 2 bậc nếu IP vẫn kết nối nhưng MQTT ngắt quá lâu: ép stop/start MQTT sau 60s, restart toàn mạch (flush cache) sau 150s. (3) **Boot Fast-path (`svc_network`)**: Dùng cờ NVS `lte_lock` để xác nhận module 4G đã cấu hình `AT+CNMP=38`. Ở các lần khởi động sau, nếu có cờ, module gửi lại lệnh khóa nhưng bỏ qua quy trình rườm rà (toggle `CFUN`) và delay chết 10s, dùng `AT+CGATT?` polling để kết nối nhanh nhất. Tăng UART RX buffer lên 16KB và thêm lệnh escape `+++` nếu module mắc kẹt ở PPP mode.
- **Lý do:** Khắc phục tình trạng "kẹt MQTT tĩnh" (PPP connection up nhưng socket TCP layer hỏng do A7680C không có CTS/RTS hardware flow control gây mất frame khi MQTT retransmit). Tối ưu FSM giúp CPU rảnh tay, không chạy nhầm AI lúc đang thu dataset (tiết kiệm điện năng). Boot fast-path và PPP escape loại bỏ các lần khởi động chậm (30s) và các ca module bị treo do MCU hard reset lệch pha.

---

### D-023 · Tự động xử lý cảnh báo quá 24h (Auto-resolve) bằng background task (asyncio loop)
- **Quyết định:** Sử dụng vòng lặp `asyncio` (`auto_resolve_stale_alerts_loop`) được chạy song song trong `lifespan` của FastAPI thay vì dùng thư viện lập lịch (scheduler) bên thứ ba như Celery hay APScheduler. Tác vụ quét DB và bulk update `is_resolved = True` cho các alert cũ hơn 24h mỗi 1 giờ.
- **Lý do:** (1) Tránh phình to dependency (không thêm APScheduler/Celery/Redis) cho một logic quá đơn giản. (2) Tận dụng cơ chế `asyncio.create_task` trong lifespan đã áp dụng thành công cho MQTT service. (3) Bulk update `UPDATE alerts SET is_resolved=True WHERE is_resolved=False AND created_at < NOW - 24h` là thao tác Idempotent (chạy nhiều lần/nhiều worker không gây tác dụng phụ), an toàn với multi-worker.

### D-022 · RSSI 4G: chu kỳ đo cấu hình được (0=tắt) + guard comms-critical; CMUX loại (2026-06-29)
- **Bối cảnh:** Đo RSSI 4G làm bằng cách thoát PPP → `AT+CSQ` → `ATO` (`cellular_rssi_update_task` trong `svc_network.c`), mỗi lần **đứt MQTT socket 15-20s**, chạy hardcode mỗi 120s và **chỉ trong `STATE_NORMAL`** → ~12-17% thời gian đường cảnh báo chết NGAY trong chế độ giám sát ngã. Một cú ngã rơi đúng cửa sổ chết → alert trễ nguyên chu kỳ reconnect (vẫn cache QoS1/NVS nhưng trễ). CMUX (ghép kênh AT+PPP, đo không cần đứt link) đã thử trước đây **không chạy** trên A7680C+PPPoS.
- **Quyết định:**
  - **Cách 1 — `rssi_interval` (giây, `0 = tắt hẳn`) cấu hình từ xa** xuyên FW↔BE↔FE theo đúng khuôn `fall_threshold`/`fall_cooldown`. NVS key `rssi_int`; cột `devices.rssi_interval`; field trong `config/set` + echo `config/status`. Default 300s (giảm từ 120s), range hợp lệ `0|60|120|300|600`, firmware clamp non-zero `<60`→60.
  - **Cách 2 — guard comms-critical:** KHÔNG đo RSSI (không `+++`) khi đang xác nhận ngã (FSM `CONFIRMING`) hoặc trong `fall_cooldown` sau alert. Cờ đặt ở **`sys_manager`** (`sys_manager_bump_comms_critical(ms)` / `sys_manager_is_comms_critical()`) dùng **monotonic expiry** (lấy max mốc hết hạn) để `svc_ai` + `svc_cloud` cùng ghi không tranh xoá. `svc_network` đọc cờ này trước khi `+++`.
  - CMUX: loại khỏi phạm vi đồ án.
- **Lý do:** (1) Giá trị lớn nhất của knob là `0=off` — tắt được hành vi rớt-link khi deploy thật, chỉ bật lúc demo, không cần reflash. (2) Cờ ở `sys_manager` né circular-dep CMake: `svc_cloud → svc_network` đã có nên `svc_network` KHÔNG được include `svc_cloud`/`svc_ai`; `sys_manager` là tầng mọi service đều phụ thuộc (`svc_network` vốn đã gọi `sys_manager_get_state()`). (3) Monotonic expiry tránh race 2-writer. (4) Cách 2 là van an toàn cốt lõi, độc lập với knob — giữ kể cả khi bỏ config. Đảo ngược một phần D-015 (vốn hoãn 4G-RSSI để né đứt link): nay chấp nhận hack + thêm van an toàn vì CMUX bất khả thi.

### D-021 · Phát hiện ngã 2 pha: ML trigger + Post-Impact Confirmation FSM (2026-06-29)
- **Bối cảnh:** `svc_ai` báo ngã tức thì chỉ từ 1 window (`prob[Fall] ≥ fall_threshold` → post thẳng `AI_EVT_FALL_DETECTED`). Cooldown 15s ở `svc_cloud` chỉ chống *spam*, không chống *sai* → dương tính giả lẻ (ngồi phịch, nhảy, va chạm) vẫn bắn alert. KPI #1 = Fall recall (thà báo nhầm hơn bỏ sót) nên không được hi sinh recall để lọc.
- **Quyết định:** Giữ ML làm **trigger nhạy** (bảo toàn recall), nhưng **không alert ngay** → vào FSM `CONFIRMING` quan sát **pha post-impact** (`Idle` + ROLL=lying) qua đa số window trong **N giây** rồi mới `CONFIRMED` → post event. ABORT nếu hồi phục (Walk/Run + upright). Kèm impact detector per-sample (SVM accel **thô** ở `svc_imu`, bắt free-fall<0.6g → impact>2.5g, getter `imu_service_get_last_impact()`) làm bằng chứng boost (KHÔNG hard-gate để giữ recall). N = `fall_confirm_window` cấu hình NVS/MQTT (default 4s, range 1–15), pipeline mirror `fall_cooldown`.
  - **Bỏ ý tưởng majority-vote cứng trên output ML:** window trượt 0.5s nên 5 kết quả gần nhất trải 2.5s, chữ ký Fall chỉ tồn tại 1-2 window → vote cứng sẽ **giết recall**. Vote được fold vào pha CONFIRMING trên đúng tín hiệu (đa số window là Idle+lying).
- **Lý do:** Post-impact là tín hiệu *đồng pha* recall & precision: người ngã thật nằm im, người "ngồi phịch rồi đứng dậy" tự loại → lọc báo giả gần như không mất recall. Đúng tên hệ thống "Post-Impact Fall Detection" và hiện thực hóa backlog precision-filter của **D-013** (nay đã làm). Đánh đổi: alert trễ ~N giây — bản chất post-impact, chấp nhận được.

### D-020 · Định danh thiết bị: MAC = khóa topic, device_id ngữ nghĩa do BE sinh + auto-provision (2026-06-28)
- **Bối cảnh:** Firmware hardcode `CONFIG_DEVICE_ID "esp32_eldercare_01"` → nhiều board cùng id, đụng topic; form FE lại ghi sai "Device ID (MAC Address)" trong khi firmware không dùng MAC. Backend khớp tuyệt đối `device_id == topic[1]` và **không auto-provision** (device chưa đăng ký tay → bỏ mọi MQTT). Muốn: cắm máy là tự lên dashboard, id đẹp & tuần tự.
- **Quyết định:**
  - **Multi-tenancy = per-org broker.** Mỗi org 1 full-stack (broker + backend + DB). Org của auto-provision = org của deployment (`settings.ORG_ID`, hoặc org duy nhất trong DB) → không đoán.
  - **MAC = vân tay phần cứng = khóa topic MQTT** (`eldercare/<mac>/...`). Firmware lấy MAC từ eFuse (`esp_read_mac`) → ổn định qua erase-flash/OTA, không cần provision id. Thêm cột `devices.mac` (unique).
  - **device_id (PK) = tên ngữ nghĩa do backend sinh** (`esp32_eldercare_NN`, tuần tự trong org) khi auto-provision; là id hiển thị + đích lệnh/OTA. Backend publish lệnh/config/OTA tới `eldercare/<device.mac>/...` (tra `mac` từ PK).
  - **Auto-provision** ở `mqtt_service`: nhận MQTT theo MAC lạ (ưu tiên `config/status` vì fire lúc connect) → `_get_or_create_device_by_mac` sinh `esp32_eldercare_NN` + lưu mac. Admin chỉ gán wearer.
  - **firmware_version auto-report**: firmware gửi `fw_version` kèm `config/status` (lúc connect/reconnect) → BE tự cập nhật `Device.firmware_version`; FE bỏ ô nhập tay, chỉ hiển thị read-only.
  - **Broker URI**: `#define CONFIG_MQTT_BROKER_URI` = broker org (default, NVS reset vẫn đúng); NVS override (`config/mqtt_uri`) chỉ cần khi 1 build dùng chung nhiều org.
  - **Influx tag** = `device.device_id` (semantic), không phải mac → history/FE nhất quán.
- **Lý do:** (1) Id trong topic chỉ là *claim*, không phải auth → dùng MAC không kém an toàn hơn semantic; MAC ở eFuse nên miễn nhiễm NVS reset/OTA, không cần provision per-board. (2) device_id ngữ nghĩa do BE sinh giữ UX đẹp + tuần tự mà không cần firmware handshake (firmware chỉ biết MAC của nó). (3) Per-org broker biến "org nào" thành câu hỏi đã-trả-lời-bởi-deployment, bỏ logic đoán org. (4) `fw_version` đi cùng `config/status` (metadata tĩnh, theo event connect) thay vì nhồi status 5s.
- **Bảo mật (ghi chú, chưa làm):** rủi ro spoofing thật nằm ở creds MQTT dùng chung, KHÔNG ở định dạng MAC. Per-org broker là tuyến đầu. Hardening tương lai: credential per-device + ACL `eldercare/<id>/#`, hoặc mTLS client cert (đều tái xuất hiện bước provision). Phạm vi đồ án: giữ nguyên.

### D-019 · Vô hiệu hóa chân RST của module 4G A7680C trong Firmware (2026-06-25)
- **Bối cảnh:** Lúc đầu firmware kéo chân RST xuống LOW 250ms để khởi động lại module 4G trước khi tạo PPP session. Mạch breakout A7680C của user có các chân: `rst, tx, rx, ring, dtr, mcn, mcp, spkn, spkp` nhưng **KHÔNG CÓ** chân `PWRKEY` (chân nút nguồn).
- **Quyết định:** Gỡ bỏ toàn bộ code điều khiển chân `RST` trong file `drv_a7680c.c`. Để mạch 4G hoàn toàn tự do và chỉ bật lên nhờ mạch Auto-Power-On (tụ điện) tích hợp sẵn trên board khi có nguồn.
- **Lý do:** Khi kéo RST xuống LOW, chip Baseband của A7680C bị reset và rơi vào trạng thái TẮT (Power Off). Thông thường, để bật lại cần kéo chân `PWRKEY` xuống mức thấp trong 1.5s. Do board không ra chân `PWRKEY`, module sẽ "chết lâm sàng" không thể thức dậy (gây lỗi Autobaud sync timeout 15/15) cho đến khi người dùng tự tay rút pin cắm lại để kích hoạt mạch Auto-Power-On phần cứng. Quyết định cấm ESP32 đụng vào RST giải quyết triệt để lỗi này.

### D-018 · Tránh dùng GPIO 43/44 (UART0 mặc định) cho các UART khác trên ESP32-S3 (2026-06-24)
- **Bối cảnh:** Mạch XIAO ESP32-S3 sử dụng USB Native (USB CDC) để in log, nên ban đầu thiết kế gán GPIO 43 và 44 (chân TX/RX vật lý) cho module 4G qua `UART_NUM_2` thông qua GPIO Matrix vì nghĩ 2 chân này đang rảnh. Tuy nhiên kết nối 4G qua PPP và CMUX bị rớt gói liên tục, hoạt động rất "chập cheng".
- **Quyết định:** Định tuyến lại (hàn lại mạch) module 4G sang **TX = GPIO 5**, **RX = GPIO 4** và **RST = GPIO 6**. Tuyệt đối không dùng GPIO 43/44 cho các ngoại vi UART Mux.
- **Lý do:** Trên chip ESP32-S3, GPIO 43 và 44 được nối cứng trong silicon ở **Priority 3** (mức ưu tiên cao nhất của IO MUX) cho `U0TXD` và `U0RXD` (UART0 Bootloader/Console). Việc cố ép GPIO Matrix gán tín hiệu từ UART2 vào hai chân này không đè được Priority 3, dẫn đến việc luồng dữ liệu 4G bị các đoạn log ẩn của ROM Bootloader hoặc ESP-IDF "phun" rác vào giữa chừng làm hỏng toàn bộ packet của giao thức CMUX. Khi đổi sang GPIO 4 và 5 (vốn ở Mux Priority 1/2), mạch chạy hoàn hảo mượt mà. Đóng gói bài học thiết kế phần cứng đắt giá.

### D-017 · Thu data verify dán nhãn SisFall: lưu raw `.txt`, bỏ luồng train→InfluxDB (2026-06-23)
- **Bối cảnh:** Cần bộ data thực (đeo thiết bị) để **đánh giá** model `v30_optimize` (đã train trên SisFall), không train lại trên web. Ban đầu định làm pipeline đầy đủ: thu → backend cắt window/augment → ghi InfluxDB `imu_windowed` → train. Đánh giá lại: data telemetry tần suất thấp + thời gian đồ án có hạn + train offline mới là chuẩn.
- **Quyết định:**
  - **Chỉ verify**: thu → lưu **raw `.txt` đúng format SisFall** (`<ACT>_<SV>_<R>.txt`, 6 cột `%.6f`, đơn vị g/deg/s) ra đĩa + metadata Postgres (`verification_sessions`) → download/export ZIP → train/eval **offline**.
  - **Gỡ hẳn chế độ train→InfluxDB**: xoá endpoint `data_collection` (windowing/scipy → `imu_windowed`), deps `numpy/scipy`, và toàn bộ tàn dư FE (`useSaveRecording`, `ControlPanel`, `DeviceSelector`, `exportToCSV`…). InfluxDB giờ chỉ còn `telemetry`.
  - **Gộp 1 trang** `/data-collection` (giữ tên cũ), luồng 2 bước Kết nối→preview→ghi; **chọn người đeo thật** + đặt mã `SVxx` trên FE (localStorage theo `wearerId`), bỏ hardcode subject.
  - **Đặt tên API** prefix/tag = `data-collection` (tên trống sau khi xoá endpoint train); giữ tên nội bộ `verification*`.
- **Lý do:** (1) Data 5s/lần không cần TSDB cho dataset; file SisFall đọc thẳng được bởi pipeline `SisFall-PreProcessing`, khỏi query+pivot+convert (tránh drift đơn vị/thứ tự). (2) InfluxDB không lưu "file" — nhồi point rồi dựng lại `.txt` là thừa và rủi ro. (3) Validate **device đã mount wearer** để snapshot ai đeo (gắn metadata nhân trắc học khi báo cáo). (4) Train offline trên data tải về = cách làm nghiên cứu chuẩn (train SisFall → validate data thực), dễ bảo vệ hơn pipeline online.
- **Đánh đổi / future work:** đĩa Render ephemeral → mitigate bằng export ZIP ngay/chạy local; nếu cần bền vững chuyển sang object storage (Supabase Storage). `verify_pipeline.py` (eval → confusion matrix) còn nợ. Giữ dual-DB (Postgres + InfluxDB telemetry) — narrative bảo vệ: polyglot persistence, đúng công cụ cho đúng loại dữ liệu.
- **Chi tiết phiên:** `session_report_2026-06-23_sisfall_data_collection.md`.

### D-016 · Log alert/event thuộc về Wearer, không phải Device (2026-06-23)
- **Bối cảnh (lỗi gốc):** `Alert` và `DeviceEvent` có cột `wearer_id` nhưng toàn bộ query layer (`history.py`) lọc theo `device_id`. Kịch bản lỗi: (1) Wearer A đeo device X → alert ghi `device_id=X, wearer_id=A`; (2) Wearer A chuyển sang device Y → query `device_id=X` mất hết lịch sử của A; (3) Device X gán cho Wearer B → query trả về cả log của A lẫn B lẫn nhau. `mqtt_service.py` đã ghi `wearer_id` đúng từ đầu — lỗi nằm hoàn toàn ở tầng query.
- **Quyết định:** Toàn bộ query alert/timeline đổi sang lọc theo `wearer_id`:
  - `GET /history/alerts` nhận param `wearer_id` (UUID) thay vì `device_id`; org-scope đổi sang `Alert.wearer_id.in_(org_wearer_ids)` thay vì `device_id.in_(org_device_ids)` — alert `wearer_id=NULL` tự bị loại.
  - `GET /history/{id}/timeline` đổi path param từ `device_id` → `wearer_id`; verify wearer thuộc org trực tiếp thay vì đi qua device.
  - `AlertHistory` response schema thêm trường `wearer_id`.
  - FE `alerts/page.tsx`: filter dropdown đổi từ device sang wearer (`useWearers`), lọc `a.wearerId`.
  - FE `AlertFilters.tsx`: nhận `BackendWearer[]` thay `Device[]`.
  - FE hooks `useDeviceAlerts` / `useDeviceTimeline`: giữ nguyên signature `(deviceId)` nhưng tự resolve `device.wearerId` qua `useDevice` nội bộ → `ActivityHistory` và `AlertHistory` component không cần sửa.
  - `mqtt_service.process_alert`: bỏ qua (skip) nếu `wearer_id is None` — không tạo alert khi chưa mount wearer (dataset raw vẫn đủ vì `process_event` không bị chặn).
  - `openapi.json`: cập nhật param + schema `AlertHistory` + timeline path.
- **Lý do:** Log theo device thì device đổi chủ là mất/lẫn lịch sử — sai về mặt nghiệp vụ chăm sóc bệnh nhân. Log theo wearer đảm bảo lịch sử đi theo người bất kể thiết bị nào đang đeo. Alert `wearer_id=NULL` (device chưa mount ai) không có ý nghĩa lâm sàng — đúng khi bỏ qua ở UI lẫn không tạo mới.
- **Lưu ý data cũ:** Các alert tạo trước fix này có `wearer_id=NULL` — không hiện trên UI sau fix (hành vi đúng, không backfill vì không biết wearer nào đã đeo lúc đó).

### D-015 · Thêm RSSI vào Telemetry (PostgreSQL + InfluxDB)
- **Quyết định:** Đưa thông tin cường độ sóng (RSSI) từ firmware (hiện hỗ trợ WiFi, chừa chỗ cho 4G LTE qua CMUX) lên MQTT. Backend sẽ lưu trữ lịch sử RSSI vào InfluxDB (cho vẽ chart) và cập nhật `last_rssi` vào bảng `devices` trong PostgreSQL (cho hiển thị dashboard thời gian thực).
- **Lý do:** Tách biệt luồng lưu trữ RSSI: InfluxDB gánh dữ liệu Time-series cho biểu đồ Vitals (sâu, nặng). PostgreSQL lưu trữ bản snapshot `last_rssi` nhẹ nhàng để Dashboard tổng fetch O(1) mà không chạm vào InfluxDB, giúp cải thiện tốc độ tải màn hình chính. Luồng 4G LTE tạm hoãn chờ làm CMUX vì PPPoS data mode không cho phép chèn lệnh AT+CSQ mà không làm đứt kết nối.

### D-014 · `set_fall_cooldown` cấu hình được từ xa và lưu NVS
- **Quyết định:** Biến thời gian hồi cảnh báo ngã (cooldown) từ hằng số 15s thành biến cấu hình được. Thêm trường `fall_cooldown` vào DB, tạo lệnh MQTT `set_fall_cooldown`, và lưu vào NVS flash (`config/fall_cd`) trên firmware.
- **Lý do:** Giống với `set_fall_threshold` và `set_interval`, việc hardcode gây bất tiện khi muốn thử nghiệm thực tế hoặc điều chỉnh theo từng bệnh nhân. Đưa cấu hình lên dashboard giúp bác sĩ hoặc kỹ thuật viên dễ dàng tinh chỉnh (từ 5s đến 300s) mà không cần nạp lại firmware.

### D-013 · Fall = class "Fall" HAR; High-G + orientation (ROLL) là backlog precision-filter
> ✅ **(2026-06-29) Backlog precision-filter đã hiện thực** dưới dạng Post-Impact Confirmation FSM — xem **D-021** (impact/free-fall qua SVM accel thô + post-impact ROLL=lying confirm).
- **Bối cảnh:** `instruction.md` mô tả fall = post-impact (High-G peak + orientation, <1s); `tinyml_model.md`
  lại để `Fall` là 1 class HAR → 2 cơ chế. High-G CHƯA code; ưu tiên hiện tại là pedometer.
- **Quyết định:** (1) Hiện tại fall = output class "Fall" của HAR model, không thêm High-G/orientation ngay.
  (2) High-G peak + orientation đẩy backlog, sau gắn làm **bộ lọc precision** (không phải pre-gate).
  (3) Khi làm orientation check: dùng **ROLL** (mounting thắt lưng trước), thay pitch ở D-003.
- **Lý do:** `svc_ai` đã chạy inference liên tục để gate pedometer (D-010) → High-G "gác cổng tiết kiệm điện"
  vô nghĩa vì ML đã chạy sẵn; vai trò đúng của High-G là **precision**, không phải power. Ship pedometer
  trước đúng ưu tiên; fall thuần ML rẻ nhất, đủ giai đoạn đầu. Roll thay pitch vì với mounting thắt lưng
  trước, trục phân biệt đứng/nằm là roll. Phát alert + cooldown vẫn ở svc_cloud (D-006).
- **Phase:** Phase 1 (thu data train v25→v30) song song Phase 2 (edge inference).

### D-012 · `set_fall_threshold` mirror `set_interval`; control command (start/stop) đi qua backend (B5)
- **Quyết định:** (1) Thêm chỉnh **ngưỡng phát hiện ngã** từ xa: cột `devices.fall_threshold` (float 0.25 - đổi default khớp ngưỡng θ train) + command `set_fall_threshold` (val 0.15–0.95), publish khi PUT `/devices/{id}` — **giống hệt pipeline `set_interval`**; device echo `fall_threshold` trong status để đồng bộ. (2) `start_stream`/`stop_stream` chuyển từ FE-publish-MQTT-thẳng sang `POST /devices/{id}/command` (backend authz org rồi publish).
- **Lý do:** Nhất quán một khuôn cấu hình (cột DB + command + echo status) cho mọi tham số áp xuống device. Đưa control command về backend → có authz/audit + bớt một đường client tự publish (bước đệm tiến tới M3, dù creds subscribe vẫn ở client nên chưa bịt hẳn). Range 0.15–0.95: dưới 0.15 quá nhạy (spam báo nhầm), trên 0.95 gần như không bao giờ kích.
- **UX:** FE dùng React Query `isPending` cho nút start/stop ("Đang gửi lệnh…") và chỉ vào trạng thái recording sau khi backend xác nhận — tránh "bấm xong không thấy gì".

### D-011 · FE realtime telemetry subscribe thẳng `status` (không tạo topic `telemetry`)
- **Bối cảnh:** FE từng subscribe `eldercare/+/telemetry` nhưng không hệ nào publish topic đó (firmware publish `status`, backend chỉ sub→ghi DB, không republish) → `useTelemetryStore` chết với thiết bị thật, chỉ "sống" ở mock.
- **Quyết định:** FE subscribe thẳng `eldercare/+/status` (topic firmware publish thật), map `battery`→`battery_pct`. KHÔNG thêm backend republish `status`→`telemetry`.
- **Lý do:** Ít tầng nhất (sửa 1 file FE, 0 đụng backend), đúng tinh thần "firmware/status là canonical". Đánh đổi: FE coupling nhẹ với schema status firmware (đã xử lý bằng fallback `battery_pct ?? battery`). Cùng lúc backend nhận thêm `walk_steps`/`run_steps` trong `StatusPayload` để tính distance đúng (0.415 vs 0.5 × height) thay vì dùng tổng `steps × 0.415` (sai cho người chạy).

### D-010 · Pedometer đặt ở svc_imu, gate theo HAR, đếm walk/run riêng
- **Quyết định:** `lib_pedometer` (band-pass 0.5–3.5Hz + peak-detect ngưỡng động + trơ); gọi per-sample trong `svc_imu`; chỉ đếm khi HAR=Walk/Run; tách `walk_steps`/`run_steps`; lưu NVS định kỳ.
- **Lý do:** HAR classifier đã có sẵn → gate loại gần hết false-positive mà pedometer truyền thống phải vật lộn. Đếm riêng walk/run để khớp công thức distance của backend (0.415 vs 0.5 × height). Per-sample cho độ phân giải đỉnh tốt; gán nhãn bằng `svc_ai_get_latest_prediction()` (trễ ≤0.5s, đủ vì gait đổi chậm). Band-pass ăn accel **thô** (không phải data Kalman làm mượt vốn làm cùn đỉnh).

### D-009 · 4G LTE qua PPPoS bằng esp_modem; drv_a7680c chỉ lo nguồn
- **Quyết định:** Dùng component `esp_modem` (UART+AT+PPP+netif); `drv_a7680c` chỉ điều khiển PWRKEY (Ton~50ms, Toff 2.5s). Switch WiFi(dev)/Cellular(prod) bằng macro.
- **Lý do:** esp_modem là component chính chủ Espressif, xử lý sẵn state machine PPP/LCP/IPCP → ít bug hơn tự viết. Tách lớp: driver thuần GPIO, service lo giao thức. MQTT/svc_cloud chạy trên 4G mà không cần sửa (PPP cấp IP routable).

### D-008 · Khóa LTE-only sớm (AT+CNMP=38) để chống sụt dòng
- **Quyết định:** Gửi `AT+CNMP=38` (LTE only) ngay sau AT sync, trước khi attach; kèm `CFUN=0→CNMP→CFUN=1`.
- **Lý do:** Phần cứng A7680C: quét GSM/2G gây xung dòng tức thời (dù đã có 3 tụ tantalum). `CNMP=38` là **AUTO_SAVE** (lưu NVRAM) → từ boot thứ 2 module vào thẳng LTE, không quét 2G. Đây là yêu cầu phần cứng cụ thể của dự án.

### D-007 · MQTT alert: firmware theo contract chung `alert/fall` (đã ĐẢO quyết định ban đầu)
- **Quyết định:** Firmware publish cảnh báo lên `eldercare/{id}/alert/fall`, payload khớp `AlertPayload` backend (`user_name`, `message`, `confidence`). Các topic status/imu_stream/command vốn đã khớp.
- **Lý do:** Ban đầu định lấy firmware làm canonical (`/alert`), nhưng phát hiện `tools/fake_device.py` + backend + frontend (3 hệ đã test với nhau) đều dùng `alert/fall`. Sửa 1 file firmware rẻ hơn sửa 3 hệ. Firmware thêm `confidence` (từ `svc_ai_get_latest_confidence()`) vì FE cần hiển thị.
- **Đã dọn (2026-06-17):** `AlertPayload` cho `user_name`/`message` optional; `fake_device.py` gửi đúng `{user_name,message,confidence}` (+ walk/run/rssi/interval ở status, xử lý `set_interval`); `handle_message` log `[MQTT][DROP]` thay vì nuốt.
- **Còn nợ:** firmware chưa publish `event` (backend có handler); firmware chưa gửi `rssi` (AT+CSQ) — backend đã sẵn đường ghi Influx khi payload có; cô lập đa tenant tầng MQTT (M3 — chờ quyết định hạ tầng).
- `datn-agent-skills/CLAUDE_firmware.md` còn ghi topic cũ `v1/devices/{id}/...` — **stale**, cần sync về canonical `eldercare/{id}/alert/fall|status|imu_stream|command` (`firmware/CLAUDE.md` đã đúng).

### D-006 · Cooldown chống spam alert nằm ở svc_cloud (KHÔNG ở svc_ai)
- **Quyết định:** `FALL_COOLDOWN_US = 15s` cố định trong `svc_cloud.c`. `svc_ai` phát event mỗi lần phát hiện, không cooldown.
- **Lý do:** Tách trách nhiệm: svc_ai chỉ suy luận; chính sách phát/giới hạn alert thuộc tầng cloud. (Lưu ý: tài liệu cũ từng ghi nhầm cooldown ở svc_ai 10–20s — đã sửa.)

### D-005 · Streaming gửi data ĐÃ tiền xử lý (không phải raw)
- **Quyết định:** Ở STATE_STREAMING, batch gửi lên MQTT là data đã đổi hệ trục + Kalman + chuẩn hóa (scale int16), KHÔNG phải raw.
- **Lý do:** Tránh lệch phân phối train/serve — dataset thu thập phải đi qua đúng pipeline tiền xử lý như lúc inference thì model mới hoạt động đúng khi chạy thật.

### D-004 · Giao tiếp giữa service: event loop cho tín hiệu, queue/callback cho data lớn
- **Quyết định:** `svc_*` giao tiếp qua `esp_event` (loose coupling); mảng dữ liệu lớn (window/batch) đi qua FreeRTOS queue hoặc callback, KHÔNG qua event loop.
- **Lý do:** Tránh phụ thuộc vòng tròn khi build (CMake) và không nghẽn event loop bằng payload lớn; tiết kiệm PSRAM/CPU.

### D-003 · Tiền xử lý IMU: Kalman 1D 6 trục + chuẩn hóa [-1,1]; pitch riêng bằng Kalman 2-state
- **Quyết định:** Lọc Kalman 1D từng trục → chuẩn hóa [-1,1] làm input TinyML INT8. Pitch tính riêng bằng Kalman 2-state (góc+bias) để xác định tư thế.
- **Lý do:** Input model cần đồng nhất định dạng đã train (INT8 quantize). Pitch cần fusion accel+gyro chống trôi để phân biệt nằm/đứng/ngồi.
- (2026-06-21) Posture chuyển pitch → ROLL cho hợp mounting thắt lưng trước — xem D-013.

### D-002 · Sliding window 200 mẫu, trượt 50 — cố định
- **Quyết định:** `IMU_WINDOW_SIZE=200` (2s@100Hz), trượt `IMU_BATCH_SIZE=50` (0.5s).
- **Lý do:** Là kích thước input cố định model đã train — **không đổi mà không retrain**.

### D-001 · PCNT đếm xung INT để gom batch IMU (chống sụt dòng + tiết kiệm điện)
- **Quyết định:** Nối chân INT MPU6050 vào ngoại vi PCNT; chỉ ngắt CPU mỗi 50 xung (0.5s).
- **Lý do:** MPU6050 **không có** ngắt theo ngưỡng FIFO (chỉ data-ready từng mẫu / FIFO-full), và I2C của ESP32-S3 **không có DMA** → nếu không gom, CPU phải thức 100 lần/giây. PCNT "tự chế" ra ngắt gom-lô bằng phần cứng → CPU thức 2 lần/giây. Đây là sáng kiến cốt lõi của firmware.
