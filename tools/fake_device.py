import time
import json
import random
import math
import ssl
import paho.mqtt.client as mqtt
from pathlib import Path
import threading

# 1. Hàm đọc file .env thủ công
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

print(f"🚀 Starting Fake Device (Merged): {DEVICE_ID}")
print(f"📡 Connecting to {MQTT_PROTO}://{MQTT_HOST}:{MQTT_PORT}...")

# 2. State & Activities
STATE_NORMAL = 0
STATE_DATA_STREAMING = 1
current_state = STATE_NORMAL

activities = {
    's': {'name': 'STANDING', 'acc_std': 0.02, 'gyro_std': 0.5, 'freq': 0},
    'w': {'name': 'WALKING',  'acc_std': 0.4,  'gyro_std': 40,  'freq': 1.8},
    'r': {'name': 'RUNNING',  'acc_std': 1.5,  'gyro_std': 150, 'freq': 3.2}
}
current_mode = 's'
walk_steps = random.randint(100, 500)
run_steps = random.randint(0, 100)
battery = random.randint(60, 95)
telemetry_interval = 5  # giây, đổi qua command set_interval
fall_threshold = 0.6    # ngưỡng xác suất chốt ngã, đổi qua command set_fall_threshold

# 3. Cấu hình MQTT Client
client = mqtt.Client(client_id=DEVICE_ID, protocol=mqtt.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_PROTO in ["mqtts", "wss"]:
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to Broker successfully!")
        client.subscribe(f"eldercare/{DEVICE_ID}/command")
        print(f"📥 Subscribed to eldercare/{DEVICE_ID}/command")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    global current_state, telemetry_interval, fall_threshold
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        if action == "start_stream":
            current_state = STATE_DATA_STREAMING
            print("🔄 Received command: start_stream -> Switched to DATA_STREAMING")
        elif action == "stop_stream":
            current_state = STATE_NORMAL
            print("🔄 Received command: stop_stream -> Switched to NORMAL")
        elif action == "set_interval":
            val = int(payload.get("val", telemetry_interval))
            if 1 <= val <= 3600:
                telemetry_interval = val
                print(f"🔄 Received command: set_interval -> {telemetry_interval}s")
        elif action == "set_fall_threshold":
            val = float(payload.get("val", fall_threshold))
            if 0.15 <= val <= 0.95:
                fall_threshold = val
                print(f"🔄 Received command: set_fall_threshold -> {fall_threshold}")
    except Exception as e:
        print(f"Error parsing command: {e}")

client.on_connect = on_connect
client.on_message = on_message

# 4. Các hàm gửi dữ liệu
def send_status():
    topic = f"eldercare/{DEVICE_ID}/status"
    payload = {
        "battery": battery,
        "steps": walk_steps + run_steps,
        "walk_steps": walk_steps,
        "run_steps": run_steps,
        "state": "NORMAL" if current_state == STATE_NORMAL else "STREAMING",
        "ai_pred": activities[current_mode]['name'],
        "ai_conf": round(random.uniform(0.7, 0.99), 2),
        "rssi": random.randint(-95, -55),
        "interval": telemetry_interval,
        "fall_threshold": fall_threshold,
    }
    client.publish(topic, json.dumps(payload))
    print(f"📤 Telemetry: {payload}")

def send_fall_alert():
    # Khớp AlertPayload backend: confidence bắt buộc; user_name/message optional.
    topic = f"eldercare/{DEVICE_ID}/alert/fall"
    payload = {
        "user_name": "",
        "message": "Fall detected",
        "confidence": round(random.uniform(0.85, 0.99), 2),
    }
    client.publish(topic, json.dumps(payload))
    print(f"🚨 ALERT SENT: FALL DETECTED with confidence {payload['confidence']}!")

def send_event(event_type="button_press", desc="SOS Button"):
    topic = f"eldercare/{DEVICE_ID}/event"
    payload = {
        "device_id": DEVICE_ID,
        "event_type": event_type,
        "description": desc,
        "timestamp": int(time.time())
    }
    client.publish(topic, json.dumps(payload))
    print(f"🔔 Event Sent: {event_type} ({desc})")

def generate_sample(mode_key, t):
    act = activities[mode_key]
    freq = act['freq']
    
    if freq > 0:
        ax = math.sin(2 * math.pi * freq * t) * (act['acc_std'] * 0.2) + random.uniform(-0.02, 0.02)
        ay = math.cos(2 * math.pi * freq * t) * (act['acc_std'] * 0.1) + random.uniform(-0.02, 0.02)
        az = 1.0 + math.sin(2 * math.pi * freq * t) * act['acc_std'] + random.uniform(-0.05, 0.05)
        
        gx = math.sin(2 * math.pi * freq * t) * act['gyro_std'] + random.uniform(-5, 5)
        gy = math.cos(2 * math.pi * freq * t) * (act['gyro_std'] * 0.5) + random.uniform(-5, 5)
        gz = random.uniform(-act['gyro_std'] * 0.3, act['gyro_std'] * 0.3)
    else:
        ax = random.uniform(-0.01, 0.01)
        ay = random.uniform(-0.01, 0.01)
        az = 1.0 + random.uniform(-0.02, 0.02)
        gx = random.uniform(-0.5, 0.5)
        gy = random.uniform(-0.5, 0.5)
        gz = random.uniform(-0.5, 0.5)

    return {
        "ax": round(ax, 2), "ay": round(ay, 2), "az": round(az, 2),
        "gx": round(gx, 2), "gy": round(gy, 2), "gz": round(gz, 2)
    }

# 5. Vòng lặp chính
try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    print("\n--- Controls ---")
    print("Press 's': STAND | 'w': WALK | 'r': RUN")
    print("Press 'f': Send FALL ALERT | 'e': Send SOS EVENT")
    print("Press 'Ctrl+C': STOP")
    print("-----------------------\n")

    last_heartbeat = 0
    last_step_time = time.time()

    while True:
        current_time = time.time()
        
        # Cập nhật số bước chân nếu đang đi/chạy (tách walk/run như firmware D-010)
        if current_mode in ['w', 'r'] and current_time - last_step_time > (1.0 / activities[current_mode]['freq']):
            if current_mode == 'w':
                walk_steps += 1
            else:
                run_steps += 1
            last_step_time = current_time

        if current_state == STATE_NORMAL:
            # Gửi status theo chu kỳ telemetry_interval (đổi được qua set_interval)
            if current_time - last_heartbeat > telemetry_interval:
                send_status()
                last_heartbeat = current_time
            time.sleep(0.1)
        
        elif current_state == STATE_DATA_STREAMING:
            # Fake IMU Data Streaming
            import struct
            import base64
            
            raw_bytes = bytearray()
            for _ in range(50):
                t = time.time()
                sample = generate_sample(current_mode, t)
                
                # Convert from float (g, deg/s) to int16_t like MPU-6050
                # Accel: ±8g => 4096 LSB/g
                # Gyro: ±2000dps => 16.4 LSB/dps
                ax_int = int(sample["ax"] * 4096)
                ay_int = int(sample["ay"] * 4096)
                az_int = int(sample["az"] * 4096)
                gx_int = int(sample["gx"] * 16.4)
                gy_int = int(sample["gy"] * 16.4)
                gz_int = int(sample["gz"] * 16.4)
                
                # Clamp values to int16 range
                ax_int = max(-32768, min(32767, ax_int))
                ay_int = max(-32768, min(32767, ay_int))
                az_int = max(-32768, min(32767, az_int))
                gx_int = max(-32768, min(32767, gx_int))
                gy_int = max(-32768, min(32767, gy_int))
                gz_int = max(-32768, min(32767, gz_int))

                raw_bytes.extend(struct.pack('<hhhhhh', ax_int, ay_int, az_int, gx_int, gy_int, gz_int))
                time.sleep(0.01) # 100Hz
            
            data_b64 = base64.b64encode(raw_bytes).decode('utf-8')
            topic = f"eldercare/{DEVICE_ID}/imu_stream"
            payload = {
                "ts": int(time.time() * 1000),
                "fs": 100,
                "cnt": 50,
                "data_b64": data_b64
            }
            client.publish(topic, json.dumps(payload))
            print(f"📤 Sent 50 IMU samples (Base64) [{activities[current_mode]['name']}]")

        # Kiểm tra phím bấm (non-blocking)
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key in activities:
                current_mode = key
                print(f"\n🔄 Switched mode to: {activities[key]['name']}")
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
