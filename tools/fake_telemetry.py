import time
import json
import random
import ssl
import paho.mqtt.client as mqtt
from pathlib import Path

# 1. Hàm đọc file .env thủ công (không cần cài thêm python-dotenv)
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

# 2. Khởi tạo cấu hình
env = load_backend_env()
if not env:
    exit(1)

MQTT_HOST = env.get("MQTT_HOST", "localhost")
MQTT_PORT = int(env.get("MQTT_PORT", 8883))
MQTT_USER = env.get("MQTT_USERNAME")
MQTT_PASS = env.get("MQTT_PASSWORD")
MQTT_PROTO = env.get("MQTT_PROTOCOL", "mqtts")
DEVICE_ID = "dev_01"  # ID giả lập

print(f"🚀 Starting Fake Device: {DEVICE_ID}")
print(f"📡 Connecting to {MQTT_PROTO}://{MQTT_HOST}:{MQTT_PORT}...")

# 3. Cấu hình MQTT Client
client = mqtt.Client(client_id=DEVICE_ID, protocol=mqtt.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_PROTO in ["mqtts", "wss"]:
    client.tls_set(cert_reqs=ssl.CERT_NONE) # Chấp nhận cert tự ký nếu có
    client.tls_insecure_set(True)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to Broker successfully!")
    else:
        print(f"❌ Connection failed with code {rc}")

client.on_connect = on_connect

# 4. Các hàm gửi dữ liệu
def send_status():
    topic = f"eldercare/{DEVICE_ID}/status"
    payload = {
        "device_id": DEVICE_ID,
        "status": "online",
        "battery_pct": random.randint(60, 95),
        "walk_steps": random.randint(100, 500),
        "run_steps": random.randint(100, 500),
        "timestamp": int(time.time())
    }
    client.publish(topic, json.dumps(payload))
    print(f"📤 Sent Heartbeat: {payload['battery_pct']}% battery, {payload['walk_steps']} steps")

def send_fall_alert():
    topic = f"eldercare/{DEVICE_ID}/alert/fall"
    payload = {
        "device_id": DEVICE_ID,
        "user_name": "Ông Hùng",
        "confidence": round(random.uniform(0.85, 0.99), 2),
        "message": "Cảnh báo: Phát hiện té ngã mạnh tại phòng khách!",
        "timestamp": int(time.time())
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

# 5. Vòng lặp chính
try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    print("\n--- Manual Triggers ---")
    print("Press 'f' to send FALL ALERT")
    print("Press 'e' to send SOS EVENT")
    print("Press 'Ctrl+C' to stop")
    print("-----------------------\n")

    last_heartbeat = 0
    while True:
        # Gửi status mỗi 15 giây
        if time.time() - last_heartbeat > 15:
            send_status()
            last_heartbeat = time.time()
        
        # Kiểm tra phím bấm (non-blocking đơn giản)
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'f':
                send_fall_alert()
            elif key == 'e':
                send_event()
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n👋 Stopping Fake Device...")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"💥 Error: {e}")
