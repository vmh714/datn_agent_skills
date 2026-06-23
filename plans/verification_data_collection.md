# Plan: Thu Data Verification cho Model Fall Detection

> **Mục tiêu:** Thu bộ data riêng (~5-6 người) để verify model `v30_optimize` đã train trên SisFall.  
> **Không train lại** — chỉ đánh giá mô hình trên data thực tế thu bằng thiết bị firmware.  
> **Ngày tạo:** 2026-06-23

---

## 1. Thông số kỹ thuật

| Thông số | Giá trị |
|----------|---------|
| Thiết bị | ESP32-S3 + MPU6050 |
| Sampling rate | **100 Hz** (đã đúng, không cần downsample) |
| Kênh dữ liệu | 6: `ax, ay, az, gx, gy, gz` |
| Đơn vị | Phải khớp sau scale: accel → g (clip -8..8 rồi /8), gyro → deg/s (/2000) |
| Window model | 200 mẫu × 6 kênh = 2 giây/window |
| Stride | 100 mẫu = 1 giây |
| Format file | `.txt`, mỗi dòng = 1 sample, 6 cột cách nhau dấu phẩy hoặc tab |
| Naming | `<CODE>_<SUBJECT_ID>_<TRIAL_NO>.txt` (giữ nguyên SisFall convention) |

### Lưu ý về đơn vị raw từ firmware

Firmware ESP32 cần output **đúng đơn vị** trước khi lưu file, hoặc ghi raw và note hệ số convert:

- **Accel:** đơn vị g (ví dụ: `±8g range` → LSB/mg × 9.8 → m/s² → /9.8 = g). Kiểm tra MPU6050 config.
- **Gyro:** đơn vị deg/s (gyro raw / sensitivity, ví dụ FS=2000dps → raw/16.4 = deg/s).

Pipeline SisFall (step1) dùng:
```
accel_g = raw * 32 / 8192          # ADXL345 13bit ±16g → g
gyro_dps = raw * 4000/65536 * π/180 # ITG3200 16bit ±2000dps → rad/s
```
→ Nếu firmware đã output đúng đơn vị g và deg/s, **bỏ qua step1**, chỉ cần bước scale trong `apply_preprocessing`.

---

## 2. Danh sách hoạt động cần thu

### 2a. ADL (Activities of Daily Living)

| Code | Activity | Nhãn model | Trials/người | Thời gian/trial |
|------|----------|-----------|-------------|----------------|
| D01 | Đi bộ bình thường trên đường phẳng | **Walk** | 1 | 60s |
| D02 | Đi bộ nhanh trên đường phẳng | **Walk** | 1 | 60s |
| D05 | Leo cầu thang lên rồi xuống chậm | **Walk** | 5 | 20s |
| D03 | Chạy chậm (jog) | **Run** | 1 | 60s |
| D07 | Ngồi xuống ghế thường, ngồi chờ 3s, đứng lên | **Trans + Idle** | 5 | 12s |
| D12 | Ngồi → nằm từ từ → chờ 3s → ngồi dậy | **Trans + Idle** | 5 | 15s |
| D15 | Đứng → gập gối cúi xuống → đứng lại | **Trans** | 5 | 12s |
| D00* | Đứng yên / ngồi yên tại chỗ | **Idle** | 2 | 30s |

> `*D00`: code tự đặt thêm. Chỉ dùng trong bộ verification này.
>
> ⚠️ **D05 = Walk**, không phải Trans — pipeline `step2_windowing.py:67` xếp D05 vào `cont_har` (sliding window liên tục), giống D01/D02. Confirmed tại `ml_pipeline.py:27`.
>
> D07 và D12 sinh ra cả 2 loại window: **Trans** (tại đỉnh peak) và **Idle** (đoạn tĩnh xa peak). Model sẽ classify mỗi window riêng biệt.

### 2b. Falls — 10 hành động (có đệm)

Nhóm theo tư thế bắt đầu để dễ tổ chức thu:

#### Nhóm A — Ngã từ tư thế đứng/đi (đứng cạnh đệm)

| Code | Activity | Hướng ngã | Trials/người | Thời gian/trial |
|------|----------|----------|-------------|----------------|
| F01 | Đang đi bộ → trượt ngã về phía trước | Forward | 5 | 15s |
| F02 | Đang đi bộ → trượt ngã ra phía sau | Backward | 5 | 15s |
| F03 | Đang đi bộ → trượt ngã sang bên | Lateral | 5 | 15s |
| F06 | Đang đi bộ → đổ thẳng xuống (giả lập ngất) | Vertical | 5 | 15s |

> F01/F02/F03: đi chậm, bước 2-3 bước rồi đổ có kiểm soát — **không cần trượt thật**, chỉ cần motion profile giống ngã.

#### Nhóm B — Ngã khi đang đứng dậy (ngồi dưới đệm, đứng lên rồi đổ)

| Code | Activity | Hướng ngã | Trials/người | Thời gian/trial |
|------|----------|----------|-------------|----------------|
| F08 | Đang đứng dậy → ngã về phía trước | Forward | 5 | 15s |
| F09 | Đang đứng dậy → ngã sang bên | Lateral | 5 | 15s |

#### Nhóm C — Ngã khi đang ngồi xuống (ghế thấp, đệm xung quanh)

| Code | Activity | Hướng ngã | Trials/người | Thời gian/trial |
|------|----------|----------|-------------|----------------|
| F10 | Đang ngồi xuống → ngã về phía trước | Forward | 5 | 15s |
| F11 | Đang ngồi xuống → ngã ra phía sau | Backward | 5 | 15s |

#### Nhóm D — Ngã khi đang ngồi yên (ngồi trên đệm hoặc ghế thấp)

| Code | Activity | Hướng ngã | Trials/người | Thời gian/trial |
|------|----------|----------|-------------|----------------|
| F13 | Đang ngồi → ngã về phía trước (ngủ gật) | Forward | 5 | 15s |
| F15 | Đang ngồi → ngã sang bên | Lateral | 5 | 15s |

**Không thu:** F04 (trip khi đi — giống F01 nhưng cơ chế khó tái tạo), F05 (jogging trip — nguy hiểm dù có đệm), F07 (có bàn để chống — cần setup phức tạp), F12/F14 (lateral/backward sitting-down — tương tự F11/F15 đã cover).

**Lý do đủ đa dạng với 10 loại:**
- Cover hết 3 hướng ngã: forward / backward / lateral / vertical
- Cover hết 4 tư thế bắt đầu: walking / getting-up / sitting-down / seated
- Tổng 50 samples Fall/người → đủ để đánh giá recall phân loại theo hướng

#### Hướng dẫn an toàn khi thu Falls (có đệm):
- **Đệm dày ≥ 5cm**, trải rộng ít nhất 1.5m × 1.5m về phía sẽ ngã.
- **Luôn có người đứng phía sau/bên** để đỡ nếu mất kiểm soát.
- **Nhóm A (đứng/đi):** đi chậm 2-3 bước, đổ có chủ đích — không cần ngã nhanh, model nhận diện qua profile gia tốc không phải tốc độ.
- **Nhóm B/C/D:** tư thế thấp, gần đệm, rủi ro thấp nhất.
- Nghỉ **ít nhất 30s** giữa các trial ngã.
- Nếu ai không thoải mái với một loại: skip, ghi chú trong log.

---

## 3. Naming Convention (giữ y SisFall)

```
<CODE>_<SUBJECT_ID>_<TRIAL_NO>.txt

Ví dụ:
  D01_SV01_R01.txt   → Subject 01, đi bộ bình thường, trial 1
  F13_SV03_R04.txt   → Subject 03, Fall F13, trial 4
  D00_SV02_R02.txt   → Subject 02, idle, trial 2
```

### Subject IDs

| ID | Ghi chú |
|----|---------|
| SV01 | Người thứ nhất |
| SV02 | Người thứ hai |
| ... | ... |
| SV06 | Người thứ sáu |

> Prefix `SV` (Subject Verification) — không đụng với `SA`/`SE` của SisFall gốc.  
> Ghi thêm log thông tin: tuổi, giới tính, chiều cao, cân nặng (để báo cáo sau).

---

## 4. Folder Structure

```
SisFall-PreProcessing/
└── verification_dataset/
    ├── raw/                          ← file .txt thô từ firmware
    │   ├── SV01/
    │   │   ├── D01_SV01_R01.txt
    │   │   ├── D02_SV01_R01.txt
    │   │   ├── D05_SV01_R01.txt
    │   │   ├── ...
    │   │   └── F15_SV01_R05.txt
    │   ├── SV02/
    │   │   └── ...
    │   └── ...
    ├── subjects_log.csv              ← log thông tin người thu
    └── collection_notes.md          ← ghi chú bất thường trong quá trình thu
```

### subjects_log.csv

```csv
subject_id,age,gender,height_cm,weight_kg,date,notes
SV01,23,M,170,65,2026-06-25,
SV02,21,F,158,52,2026-06-25,
```

---

## 5. Quy trình thu mỗi session

### Chuẩn bị (10 phút)
- [ ] Sạc pin thiết bị ESP32, kiểm tra kết nối MPU6050
- [ ] Kiểm tra firmware output đúng 6 cột @ 100Hz
- [ ] Gắn thiết bị vào **cổ tay không thuận** hoặc **ngực** (phải nhất quán với vị trí training)
- [ ] Trải thảm tại khu vực thu Falls
- [ ] Mở serial log / file logging, tạo folder `SV0X/`

> **Quan trọng:** Vị trí gắn cảm biến phải nhất quán xuyên suốt. SisFall gắn ở **cổ tay** (ADXL345+ITG3200).

### Thu ADL (thứ tự đề xuất)

1. **D00 Idle** (×2 trials × 30s) — đứng/ngồi yên tại chỗ
2. **D01 Walk** (×1 trial × 60s) — đi bộ bình thường
3. **D02 Walk fast** (×1 trial × 60s) — đi bộ nhanh
4. **D05 Stairs** (×5 trials × 20s) — leo/xuống cầu thang *(nhãn = Walk)* — nghỉ 10s giữa trials
5. **D03 Jog** (×1 trial × 60s) — chạy chậm
6. **D07 Sit-Stand** (×5 trials × 12s) — sinh Trans+Idle — nghỉ 5s giữa trials
7. **D12 Lie-Sit** (×5 trials × 15s) — sinh Trans+Idle — nghỉ 5s giữa trials
8. **D15 Bend** (×5 trials × 12s) — sinh Trans — nghỉ 5s giữa trials

### Thu Falls (sau khi xong ADL)

9. Giải thích + demo cho người thu
10. **F06** (×5 trials × 15s) — nghỉ 30s giữa trials
11. Nghỉ 2 phút
12. **F10** (×5 trials × 15s)
13. Nghỉ 2 phút
14. **F13** (×5 trials × 15s)
15. Nghỉ 2 phút
16. **F15** (×5 trials × 15s)

### Kết thúc session (5 phút)
- [ ] Copy file từ thiết bị / serial log
- [ ] Đặt tên file đúng convention `<CODE>_<SUBJECT_ID>_<TRIAL_NO>.txt`
- [ ] Ghi vào `subjects_log.csv`
- [ ] Ghi bất thường vào `collection_notes.md`

---

## 6. Ước tính thời gian / người

| Phần | Thời gian |
|------|----------|
| Chuẩn bị + gắn thiết bị | 10 phút |
| ADL (D00-D15) | ~25 phút |
| Falls (F06-F15) | ~20 phút (gồm nghỉ) |
| Đặt tên file + ghi log | 5 phút |
| **Tổng** | **~60 phút/người** |

**5 người × 60 phút = ~5 tiếng** (nên chia 2 ngày, 2-3 người/buổi).

---

## 7. Preprocessing — tích hợp vào pipeline

Vì firmware thu @ 100Hz (đã downsample, không cần step1), tạo script verify riêng:

```python
# verify_pipeline.py (đặt trong SisFall-PreProcessing/)

import numpy as np
import pandas as pd
from pathlib import Path

VERIFICATION_DIR = Path("verification_dataset/raw")
MODEL_PATH = "train_v30_optimize/model_v30_optimize_int8.tflite"

LABELS = ['Walk', 'Run', 'Idle', 'Trans', 'Fall']
FALL_IDX = 4
WINDOW_SIZE = 200
STRIDE = 100
FALL_THRESHOLD = 0.25   # dùng ngưỡng eval offline, không phải firmware threshold 0.6

def load_verification_file(path):
    """Load file .txt 6 cột, return numpy (N, 6)."""
    df = pd.read_csv(path, header=None)
    return df.values.astype(np.float32)

def apply_scale(data):
    """Khớp với ml_pipeline.py:108-115."""
    data[:, :3] = np.clip(data[:, :3], -8, 8) / 8   # accel
    data[:, 3:] = data[:, 3:] / 2000                  # gyro
    return data

def extract_windows(data, window_size=WINDOW_SIZE, stride=STRIDE):
    windows = []
    for i in range(0, len(data) - window_size + 1, stride):
        windows.append(data[i:i+window_size])
    return np.array(windows)

def get_label_from_code(code):
    """Map file code sang nhãn model."""
    mapping = {
        'D00': 'Idle',
        'D01': 'Walk', 'D02': 'Walk', 'D03': 'Run',
        'D05': 'Trans', 'D07': 'Trans', 'D12': 'Trans', 'D15': 'Trans',
        'F06': 'Fall', 'F10': 'Fall', 'F13': 'Fall', 'F15': 'Fall',
    }
    return mapping.get(code, 'Unknown')
```

> Script đầy đủ (load tflite, infer, confusion matrix) tạo sau khi có data.  
> Ngưỡng eval: `fall_threshold = 0.25` (giống pipeline train), KHÔNG dùng `0.6` (firmware runtime).

---

## 8. Checklist cuối cùng trước khi thu

- [ ] Firmware output format: 6 cột, 100Hz, đơn vị g và deg/s đã xác nhận
- [ ] Vị trí gắn cảm biến đã thống nhất (cổ tay / ngực)
- [ ] Folder `verification_dataset/raw/SV0X/` đã tạo
- [ ] Thảm tập đã chuẩn bị
- [ ] Có người giám sát khi thu Falls
- [ ] `subjects_log.csv` đã có dòng cho người thu hôm nay

---

## 9. Mapping nhãn tóm tắt

```
Walk  ← D01, D02, D05          # D05 (stairs) = Walk! — sliding window liên tục
Run   ← D03
Idle  ← D00 + đoạn tĩnh của D07/D12
Trans ← đoạn peak của D07, D12, D15
Fall  ← F01, F02, F03, F06, F08, F09, F10, F11, F13, F15
```

> Nguồn: `ml_pipeline.py:22-29` + `step2_windowing.py:66-68`
