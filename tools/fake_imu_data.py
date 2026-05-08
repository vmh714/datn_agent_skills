import time
import json
import random
import math
import ssl
import paho.mqtt.client as mqtt
from pathlib import Path

# 1. Load config from Backend .env
def load_backend_env():
    env_path = Path(__file__).parent.parent.parent / "backend" / ".env"
    config = {}
    if not env_path.exists():
        print(f"❌ Not found .env at: {env_path}")
        return None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

env = load_backend_env()
MQTT_HOST = env.get("MQTT_HOST", "localhost")
MQTT_PORT = int(env.get("MQTT_PORT", 8883))
MQTT_USER = env.get("MQTT_USERNAME")
MQTT_PASS = env.get("MQTT_PASSWORD")
MQTT_PROTO = env.get("MQTT_PROTOCOL", "mqtts")
DEVICE_ID = "dev_01"

# 2. Cấu hình Motion (Hành động) - Đơn vị Accel: g, Gyro: deg/s
activities = {
    's': {'name': 'STANDING', 'acc_std': 0.02, 'gyro_std': 0.5, 'freq': 0},
    'w': {'name': 'WALKING',  'acc_std': 0.4,  'gyro_std': 40,  'freq': 1.8},
    'r': {'name': 'RUNNING',  'acc_std': 1.5,  'gyro_std': 150, 'freq': 3.2}
}
current_mode = 's'

# 3. MQTT Client Setup
client = mqtt.Client(client_id=f"{DEVICE_ID}_IMU", protocol=mqtt.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_PROTO in ["mqtts", "wss"]:
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

def generate_sample(mode_key, t):
    act = activities[mode_key]
    freq = act['freq']
    
    # Giả lập tín hiệu dao động (Sin wave + Noise)
    if freq > 0:
        # Accel: Z-axis has gravity (1.0g) + oscillation from movement
        # Khi đi bộ/chạy, trục Z dao động mạnh nhất do phản lực mặt đất
        ax = math.sin(2 * math.pi * freq * t) * (act['acc_std'] * 0.2) + random.uniform(-0.02, 0.02)
        ay = math.cos(2 * math.pi * freq * t) * (act['acc_std'] * 0.1) + random.uniform(-0.02, 0.02)
        az = 1.0 + math.sin(2 * math.pi * freq * t) * act['acc_std'] + random.uniform(-0.05, 0.05)
        
        # Gyro: Oscillations around 0
        gx = math.sin(2 * math.pi * freq * t) * act['gyro_std'] + random.uniform(-5, 5)
        gy = math.cos(2 * math.pi * freq * t) * (act['gyro_std'] * 0.5) + random.uniform(-5, 5)
        gz = random.uniform(-act['gyro_std'] * 0.3, act['gyro_std'] * 0.3)
    else:
        # Standing: Mostly static with small noise
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

try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    
    print(f"📡 IMU Streamer Started for {DEVICE_ID}")
    print("--- Controls ---")
    print("Press 's': STAND | 'w': WALK | 'r': RUN | 'Ctrl+C': STOP")
    
    sample_count = 0
    start_time = time.time()
    
    while True:
        batch = []
        # Tạo batch 50 mẫu (tương ứng 0.5 giây dữ liệu ở 100Hz)
        for _ in range(50):
            t = time.time()
            batch.append(generate_sample(current_mode, t))
            time.sleep(0.01) # 10ms/sample = 100Hz
            
        # Gửi MQTT
        topic = f"eldercare/{DEVICE_ID}/imu/raw"
        payload = {
            "ts": int(time.time() * 1000),       # Unix ms
            "fs": 100,                           # Sampling freq
            "mode": activities[current_mode]['name'],
            "d": [[s["ax"], s["ay"], s["az"], s["gx"], s["gy"], s["gz"]] for s in batch]
        }
        client.publish(topic, json.dumps(payload))
        
        print(f"📤 Sent 50 samples [{activities[current_mode]['name']}]")

        # Kiểm tra phím bấm
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key in activities:
                current_mode = key
                print(f"\n🔄 Switched to: {activities[key]['name']}")

except KeyboardInterrupt:
    print("\n👋 Stopping IMU Streamer...")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"💥 Error: {e}")
