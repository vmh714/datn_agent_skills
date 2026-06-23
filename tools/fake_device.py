import time
import json
import random
import math
import ssl
import struct
import base64
import threading
import paho.mqtt.client as mqtt
from pathlib import Path

# 1. Load .env
def load_backend_env():
    env_path = Path(__file__).parent.parent.parent / "backend" / ".env"
    config = {}
    if not env_path.exists():
        print(f"❌ Không tìm thấy file .env tại: {env_path}")
        return None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

env = load_backend_env()
if not env:
    exit(1)

MQTT_HOST = env.get("MQTT_HOST", "localhost")
MQTT_PORT = int(env.get("MQTT_PORT", 8883))
MQTT_USER = env.get("MQTT_USERNAME")
MQTT_PASS = env.get("MQTT_PASSWORD")
MQTT_PROTO = env.get("MQTT_PROTOCOL", "mqtts")
DEVICE_ID = "dev_01"

print(f"🚀 Starting Fake Device: {DEVICE_ID}")
print(f"📡 Connecting to {MQTT_PROTO}://{MQTT_HOST}:{MQTT_PORT}...")

# 2. State & Activities
STATE_NORMAL = 0
STATE_DATA_STREAMING = 1
current_state = STATE_NORMAL

# Cadence thực tế:
#   Đi bộ: ~105-120 steps/min ≈ 1.9 Hz
#   Chạy:  ~160-175 steps/min ≈ 2.8 Hz
activities = {
    's': {'name': 'STANDING', 'acc_std': 0.02, 'gyro_std': 0.5,  'freq': 0.0, 'cadence': 0.0},
    'w': {'name': 'WALKING',  'acc_std': 0.20, 'gyro_std': 20.0, 'freq': 1.9, 'cadence': 1.9},
    'r': {'name': 'RUNNING',  'acc_std': 1.2,  'gyro_std': 110.0,'freq': 2.8, 'cadence': 2.8},
}
current_mode = 's'
walk_steps = 0
run_steps = 0
battery = float(random.randint(70, 95))
telemetry_interval = 5
fall_threshold = 0.6

_lock = threading.Lock()          # bảo vệ walk_steps, run_steps, battery, current_mode
# CSQ (AT+CSQ): 0-31, 99=unknown. 0→-113dBm, 31→-51dBm, step 2dBm
# 4G LTE thực tế thường 12-25 (tốt), dưới 10 là yếu
_csq_current = float(random.randint(14, 22))
_csq_target  = float(random.randint(14, 22))
_last_mode_change = time.time()    # để ramp AI confidence

# 3. Background threads

def _step_counter_thread():
    """Đếm bước chân dựa trên cadence, độc lập với vòng lặp chính."""
    global walk_steps, run_steps
    last_t = time.time()
    walk_acc = 0.0
    run_acc  = 0.0
    while True:
        time.sleep(0.05)           # cập nhật 20 Hz
        now = time.time()
        dt = now - last_t
        last_t = now

        with _lock:
            mode = current_mode
            cadence = activities[mode]['cadence']

        if mode == 'w' and cadence > 0:
            # jitter ±8% mô phỏng nhịp bước không đều
            walk_acc += cadence * random.uniform(0.92, 1.08) * dt
            n = int(walk_acc)
            if n > 0:
                with _lock:
                    walk_steps += n
                walk_acc -= n
        elif mode == 'r' and cadence > 0:
            run_acc += cadence * random.uniform(0.92, 1.08) * dt
            n = int(run_acc)
            if n > 0:
                with _lock:
                    run_steps += n
                run_acc -= n
        else:
            walk_acc = 0.0
            run_acc  = 0.0

def _battery_drain_thread():
    """Pin hao theo hoạt động: đứng < đi bộ < chạy."""
    global battery
    drain = {'s': 0.0003, 'w': 0.0008, 'r': 0.0018}  # %/giây
    while True:
        time.sleep(1.0)
        with _lock:
            mode = current_mode
        battery = max(0.0, battery - drain.get(mode, 0.0003))

def _csq_update_thread():
    """CSQ trôi dần về target (EMA), mô phỏng tín hiệu 4G biến động chậm."""
    global _csq_current, _csq_target
    while True:
        time.sleep(4.0)
        if random.random() < 0.25:
            _csq_target = float(random.randint(8, 28))
        _csq_current += (_csq_target - _csq_current) * 0.25 + random.gauss(0, 0.5)
        _csq_current = max(0.0, min(31.0, _csq_current))

# 4. MQTT Setup
client = mqtt.Client(client_id=DEVICE_ID, protocol=mqtt.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_PROTO in ["mqtts", "wss"]:
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to Broker!")
        client.subscribe(f"eldercare/{DEVICE_ID}/command")
        print(f"📥 Subscribed to eldercare/{DEVICE_ID}/command")
    else:
        print(f"❌ Connection failed rc={rc}")

def on_message(client, userdata, msg):
    global current_state, telemetry_interval, fall_threshold
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        if action == "start_stream":
            current_state = STATE_DATA_STREAMING
            print("🔄 start_stream → DATA_STREAMING")
        elif action == "stop_stream":
            current_state = STATE_NORMAL
            print("🔄 stop_stream → NORMAL")
        elif action == "set_interval":
            val = int(payload.get("val", telemetry_interval))
            if 1 <= val <= 3600:
                telemetry_interval = val
                print(f"🔄 set_interval → {telemetry_interval}s")
        elif action == "set_fall_threshold":
            val = float(payload.get("val", fall_threshold))
            if 0.15 <= val <= 0.95:
                fall_threshold = val
                print(f"🔄 set_fall_threshold → {fall_threshold}")
    except Exception as e:
        print(f"Error parsing command: {e}")

client.on_connect = on_connect
client.on_message = on_message

# 5. Helpers

def _ai_confidence():
    """Ramp từ 0.65 lên 0.97 trong ~8s sau khi đổi mode, mô phỏng model cần vài frame để ổn định."""
    stable = min(8.0, time.time() - _last_mode_change)
    base = 0.65 + stable * 0.04
    return round(min(0.97, base) + random.gauss(0, 0.02), 2)

def send_status():
    topic = f"eldercare/{DEVICE_ID}/status"
    with _lock:
        ws   = walk_steps
        rs   = run_steps
        batt = battery
        mode = current_mode
    payload = {
        "battery":        round(batt, 1),
        "steps":          ws + rs,
        "walk_steps":     ws,
        "run_steps":      rs,
        "state":          "NORMAL" if current_state == STATE_NORMAL else "STREAMING",
        "ai_pred":        activities[mode]['name'],
        "ai_conf":        _ai_confidence(),
        "csq":            int(_csq_current),
        "interval":       telemetry_interval,
        "fall_threshold": fall_threshold,
    }
    client.publish(topic, json.dumps(payload))
    print(f"📤 [{activities[mode]['name']}] "
          f"batt={payload['battery']}% "
          f"steps={ws}w/{rs}r "
          f"csq={payload['csq']} "
          f"conf={payload['ai_conf']}")

def send_fall_alert():
    topic = f"eldercare/{DEVICE_ID}/alert/fall"
    payload = {
        "user_name":  "",
        "message":    "Fall detected",
        "confidence": round(random.uniform(0.85, 0.99), 2),
    }
    client.publish(topic, json.dumps(payload))
    print(f"🚨 FALL ALERT sent confidence={payload['confidence']}")

def send_event(event_type="button_press", desc="SOS Button"):
    topic = f"eldercare/{DEVICE_ID}/event"
    payload = {
        "device_id":   DEVICE_ID,
        "event_type":  event_type,
        "description": desc,
        "timestamp":   int(time.time()),
    }
    client.publish(topic, json.dumps(payload))
    print(f"🔔 Event: {event_type} ({desc})")

# 6. IMU sample generation
def generate_sample(mode_key, t):
    act  = activities[mode_key]
    freq = act['freq']

    if freq > 0:
        # Trục Z (dọc): va chạm chính + harmonic bậc 2 (đặc trưng bước chân)
        az = (1.0
              + act['acc_std'] * math.sin(2 * math.pi * freq * t)
              + act['acc_std'] * 0.28 * math.sin(4 * math.pi * freq * t)
              + random.gauss(0, 0.05))
        # Trục X (tiến): swing lệch pha 90°, biên độ ~50% Z
        ax = (act['acc_std'] * 0.5 * math.sin(2 * math.pi * freq * t + math.pi / 2)
              + random.gauss(0, 0.03))
        # Trục Y (ngang): lắc lư nhỏ, lệch pha 45°
        ay = (act['acc_std'] * 0.2 * math.sin(2 * math.pi * freq * t + math.pi / 4)
              + random.gauss(0, 0.02))

        gx = act['gyro_std'] * math.sin(2 * math.pi * freq * t) + random.gauss(0, 4)
        gy = act['gyro_std'] * 0.6 * math.cos(2 * math.pi * freq * t) + random.gauss(0, 4)
        gz = act['gyro_std'] * 0.2 * math.sin(2 * math.pi * freq * t + math.pi / 3) + random.gauss(0, 3)
    else:
        # Đứng yên: drift rất nhỏ
        ax = random.gauss(0, 0.008)
        ay = random.gauss(0, 0.008)
        az = 1.0 + random.gauss(0, 0.012)
        gx = random.gauss(0, 0.35)
        gy = random.gauss(0, 0.35)
        gz = random.gauss(0, 0.25)

    return {
        "ax": round(ax, 3), "ay": round(ay, 3), "az": round(az, 3),
        "gx": round(gx, 2), "gy": round(gy, 2), "gz": round(gz, 2),
    }

# 7. Main loop
try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    for target in [_step_counter_thread, _battery_drain_thread, _csq_update_thread]:
        threading.Thread(target=target, daemon=True).start()

    print("\n--- Controls ---")
    print("'s': STAND  |  'w': WALK  |  'r': RUN")
    print("'f': Fall Alert  |  'e': SOS Event")
    print("Ctrl+C: Stop")
    print("-" * 32 + "\n")

    last_heartbeat = 0.0

    while True:
        now = time.time()

        if current_state == STATE_NORMAL:
            if now - last_heartbeat > telemetry_interval:
                send_status()
                last_heartbeat = now
            time.sleep(0.05)

        elif current_state == STATE_DATA_STREAMING:
            raw_bytes = bytearray()
            with _lock:
                mode = current_mode

            for _ in range(50):
                sample = generate_sample(mode, time.time())
                ax_i = max(-32768, min(32767, int(sample["ax"] * 4096)))
                ay_i = max(-32768, min(32767, int(sample["ay"] * 4096)))
                az_i = max(-32768, min(32767, int(sample["az"] * 4096)))
                gx_i = max(-32768, min(32767, int(sample["gx"] * 16.4)))
                gy_i = max(-32768, min(32767, int(sample["gy"] * 16.4)))
                gz_i = max(-32768, min(32767, int(sample["gz"] * 16.4)))
                raw_bytes.extend(struct.pack('<hhhhhh', ax_i, ay_i, az_i, gx_i, gy_i, gz_i))
                time.sleep(0.01)   # 100 Hz

            payload = {
                "ts":       int(time.time() * 1000),
                "fs":       100,
                "cnt":      50,
                "data_b64": base64.b64encode(raw_bytes).decode('utf-8'),
            }
            client.publish(f"eldercare/{DEVICE_ID}/imu_stream", json.dumps(payload))
            print(f"📤 IMU stream 50 samples [{activities[mode]['name']}]")

        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            if key in activities:
                with _lock:
                    current_mode = key
                _last_mode_change = time.time()
                print(f"\n🔄 Mode → {activities[key]['name']}")
            elif key == 'f':
                send_fall_alert()
            elif key == 'e':
                send_event()

except KeyboardInterrupt:
    print("\n👋 Stopping Fake Device...")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"💥 Error: {e}")
