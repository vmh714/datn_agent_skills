# Frontend — Fall Detection Dashboard

> **Path:** `frontend/` (code trực tiếp; đường dẫn dưới đây tương đối gốc repo frontend, vd `app/...`, `lib/...`)
> **Cập nhật lần cuối:** 2026-06-21

## Tech Stack
Next.js 16.2.4 (App Router) + React 19 + TypeScript, Zustand 5.0.12, TanStack React Query v5.99, mqtt 5.15.1 (WebSocket), Recharts 3.8.1, shadcn/Radix UI + Tailwind v4, Sonner toast, Vitest + Testing Library, ngrok (demo tunnel).

## Pages (app/)
| Page | Path | Chức năng |
|------|------|-----------|
| Dashboard | `app/page.tsx` | CriticalAlertBanner + DeviceGrid + PatientProfile + WeeklyActivityTrends |
| Lịch sử cảnh báo | `app/alerts/page.tsx` | Bộ lọc + AlertHistoryTable (giao diện full-width) |
| Thu thập IMU | `app/data-collection/page.tsx` | Record 100Hz IMU, AccelChart, GyroChart, CSV export |
| Cấu hình thiết bị | `app/device/[id]/settings/page.tsx` | DeviceConfig: chu kỳ telemetry, **slider ngưỡng phát hiện ngã `fall_threshold` 15–95%**, thời gian hồi cảnh báo `fall_cooldown`, bật/tắt theo dõi |
| Lịch sử hoạt động | `app/device/[id]/history/page.tsx` | Timeline biểu đồ bậc thang trạng thái hoạt động + Chi tiết logs |
| Nhật ký Telemetry | `app/device/[id]/telemetry/page.tsx` | Bảng log telemetry thô từ InfluxDB |
| Chỉ số thiết bị | `app/device/[id]/vitals/page.tsx` | Biểu đồ lịch sử Pin + RSSI di động (sóng SIM A7680C) |
| Quản lý thiết bị | `app/devices/page.tsx` | CRUD table + DeviceFormDialog |
| Quản lý bệnh nhân | `app/wearers/page.tsx` | CRUD table + WearerFormDialog |
| Cài đặt | `app/settings/page.tsx` | User preferences, MQTT config |
| Đăng nhập | `app/login/page.tsx` | JWT auth form |
| Server action | `app/actions/auth.ts` | Login/logout — set HTTP-only cookie |

## Components quan trọng
```
components/
├── layout/
│   ├── AppShell.tsx          # Root shell: Sidebar + TopNav + GlobalMqttInit + FallDetectionOverlay
│   ├── Sidebar.tsx           # Navigation menu
│   └── TopNav.tsx            # Header, user menu, MQTT status
├── features/dashboard/
│   ├── DeviceCard.tsx        # Card: status, battery bar, **steps realtime walk/run** (từ useTelemetryStore qua DeviceGrid), last alert
│   ├── CriticalAlertBanner.tsx # Banner đỏ nếu có fall chưa resolve trong 24h
│   ├── PatientProfile.tsx    # Panel phải: wearer info + device config + alert history
│   └── WeeklyActivityTrends.tsx # Recharts bar: walk/run steps 7 ngày
├── features/data-collection/
│   ├── ControlPanel.tsx      # Label selector, start/stop, sample count display
│   ├── AccelChart.tsx        # Line chart ax/ay/az/SVM (10Hz display)
│   └── GyroChart.tsx         # Line chart gx/gy/gz (10Hz display)
└── shared/
    ├── GlobalMqttInit.tsx    # Khởi tạo MQTT broker, subscribe global topics, refetch on fall
    ├── GlobalAlertToaster.tsx# Sonner toast cho low_battery, connection_lost
    └── FallDetectionOverlay.tsx # Full-screen modal đỏ: device, time, confidence + ack button + alarm
```

## Hooks
| Hook | File | Mô tả |
|------|------|-------|
| `useMqtt` | `hooks/useMqtt.ts` | Subscribe MQTT topics, parse IMU batch, dispatch to store. Returns `{isConnected, lastBatch, sendCommand}` |
| `useDevices` | `hooks/useDeviceData.ts` | React Query, poll 60s |
| `useAlerts`/`useCombinedAlerts` | `hooks/useDeviceData.ts` | Poll 30s, combine + sort descending |
| `useWearers`, `useWearer` | `hooks/useDeviceData.ts` | CRUD queries |
| `useSaveRecording` | `hooks/useDeviceData.ts` | Mutation POST /data-collection/sessions |
| `useStepsHistory` | `hooks/useDeviceData.ts` | GET /history/steps |

## Zustand Stores
| Store | File | State |
|-------|------|-------|
| `useAlertStore` | `store/useAlertStore.ts` | `alerts[]` (max 50), `onlineDevices[]`, `dismissedOverlayAlertIds[]` |
| `useTelemetryStore` | `store/useTelemetryStore.ts` | `telemetry: Record<deviceId, {battery_pct, walk_steps, run_steps, last_seen}>`, `mqttConnected` |
| `useSettingsStore` | `store/useSettingsStore.ts` | `mqttBrokerUrl`, `soundEnabled` (persist localStorage key: `vitalsguard-settings`) |

**Quy tắc:** Store chỉ cho dữ liệu MQTT realtime. REST data → React Query (không bỏ vào store).

## Lib Utilities
| File | Chức năng |
|------|-----------|
| `lib/mqtt-client.ts` | Singleton MQTT WebSocket client, ref-counting, mock mode, topics: imu_stream/telemetry/alert/fall |
| `lib/imu-parser.ts` | Parse Base64 int16_t binary → IMUSample[]. Scale: accel÷4096 G, gyro÷16.4 deg/s |
| `lib/apiClient.ts` | Fetch wrapper: đọc JWT từ cookie → Bearer header |
| `lib/alarm.ts` | Web Audio API: 880Hz square wave 0.6s (fall alarm) |
| `lib/jwt.ts` | Client-side JWT decode + expiry check (không verify signature) |
| `lib/utils.ts` | `cn()`, `computeSVM()`, `downsample(100Hz→10Hz)`, `formatTime()`, `exportToCSV()` |
| `lib/query-client.ts` | TanStack singleton: staleTime 30s, 1 retry, no refetchOnWindowFocus |

## services/api.ts — API Layer (duy nhất gọi HTTP)
```typescript
api.getDevices() / getDevice(id) / registerDevice() / updateDevice() / deleteDevice()
api.assignDevice(id, wearerId) / unassignDevice(id) / sendDeviceCommand(id, start_stream|stop_stream)  // B5: lệnh qua backend
api.updateDevice(id, {telemetry_interval, fall_threshold, fall_cooldown, ...})  // PUT → backend publish set_interval/set_fall_threshold/set_fall_cooldown
api.getAlerts(limit) / getDeviceAlerts(deviceId, limit) / acknowledgeAlert(alertId)
api.getWearers() / getWearer(id) / createWearer() / updateWearer() / deleteWearer()
api.getDeviceConfig(deviceId) / updateDeviceConfig(deviceId, config)
api.getStepsHistory(days) / saveRecordingSession(session)
```
Mapping: `BackendDevice → Device`, `BackendAlert → Alert` (mapDevice, mapAlert functions).

## TypeScript Types (src/types/index.d.ts)
```typescript
ActivityLabel = 'walking' | 'standing' | 'running' | 'falling'
IMUSample = {timestamp, ax, ay, az (G), gx, gy, gz (deg/s)}
IMUBatch = {deviceId, batchId, startTimestamp, samples[]}
Alert = {id, deviceId, deviceName, severity, type, message, timestamp, acknowledged}
Device = {id, name, model, status, lastSeen, lastAlert, firmwareVersion, location, batteryLevel?, wearerId?, fall_threshold?, fall_cooldown?}
WearerInfo = {id, full_name, height_cm}
DeviceConfig = {deviceId, name, samplingRate, fallThreshold, transmitInterval, alertEnabled}
RecordingSession = {deviceId, label, startTimestamp, endTimestamp, sampleCount, samples}
```
Source of truth API types: `openapi.json` ở root frontend.

## IMU Binary Protocol
- Topic: `eldercare/{deviceId}/imu_stream`
- Format: `{data_b64: "<Base64>"}` — encode int16_t[6 × N_samples] Little Endian
- Scale: `accel_g = raw / 4096` (±8g, 4096 LSB/g), `gyro_dps = raw / 16.4` (±2000dps)
- Batch: 50 samples @ 100Hz = 500ms/batch
- Legacy fallback: `{d: [[ax,ay,az,gx,gy,gz], ...]}` (2D array)

## Luồng Fall Detection Realtime
```
MQTT Broker (WSS)
  └── mqtt-client.ts singleton
        └── GlobalMqttInit.tsx (subscribe global topics)
              ├── eldercare/+/alert/fall
              │     ├── useAlertStore.addAlert()
              │     ├── alarm.ts → 880Hz beep
              │     ├── FallDetectionOverlay (full-screen red modal)
              │     └── useAlerts().refetch() (React Query invalidate)
              └── eldercare/+/status   (battery, walk_steps, run_steps)
                    └── useTelemetryStore.updateTelemetry()
```

> ℹ️ Firmware đã publish cảnh báo lên `eldercare/{id}/alert/fall` (payload có `confidence`) khớp subscribe của frontend. Xem `protocol.md` mục 1.2.
> ℹ️ Realtime telemetry: FE subscribe `eldercare/+/status` (topic firmware publish thật). Map `battery`→`battery_pct`. KHÔNG có topic `telemetry` — trước đây FE sub nhầm `telemetry` nên store không bao giờ cập nhật (đã sửa).
> ℹ️ `WeeklyActivityTrends.tsx` đã nối `useStepsHistory(7)` — vẽ tổng bước chân 7 ngày (cột trống cho ngày thiếu, highlight hôm nay, tooltip kèm km).

## Luồng IMU Data Collection (data-collection/page.tsx)
```
MQTT → mqtt-client.ts (100Hz, imu-parser.ts) → useMqtt.lastBatch
  → useEffect: downsample 10Hz → AccelChart / GyroChart (Recharts)
  → recordBuffer (useRef): accumulate full 100Hz
  → on stop: exportToCSV() + api.saveRecordingSession() → POST /api/v1/data-collection/sessions
```
> ℹ️ **B5:** start/stop_stream KHÔNG còn publish MQTT thẳng từ FE — gọi `POST /devices/{id}/command` qua `useSendDeviceCommand` (React Query `isPending` → nút hiện "Đang gửi lệnh…"; chỉ vào trạng thái recording sau khi backend xác nhận). FE vẫn giữ MQTT chỉ để **subscribe** realtime.

## Performance Patterns
- IMU binary (Base64 int16_t) thay JSON text → ~50% bandwidth reduction
- Lazy IMU subscription: chỉ subscribe `imu_stream` khi data-collection page active
- Downsample 100Hz → 10Hz cho chart (giảm render)
- useRef cho IMU buffer (tránh 100Hz re-render)
- React Query staleTime 30s (giảm redundant polling)

## Dev Config
```
NEXT_PUBLIC_BACKEND_URL   # Backend URL
NEXT_PUBLIC_MQTT_BROKER   # MQTT WebSocket URL
npm run dev               # Next.js dev
npm run share             # build + start + ngrok tunnel (demo)
proxy.ts                  # /api/* → backend (dev proxy)
```
