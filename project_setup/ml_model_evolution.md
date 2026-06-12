# Tiến Trình Phát Triển Mô Hình AI & Xử Lý Dữ Liệu

> Tài liệu này ghi lại toàn bộ quá trình thử nghiệm, cải tiến mô hình học máy và chiến lược xử lý dataset cho bài toán HAR + Fall Detection chạy TinyML trên ESP32-S3.

---

## 1. Tổng quan Dataset — SisFall

- **Nguồn**: SisFall public dataset — 23 người trẻ (SA) + 15 người cao tuổi (SE)
- **Tần số gốc**: 200 Hz → **Downsample xuống 100 Hz** để phù hợp tần số lấy mẫu của phần cứng
- **Cảm biến sử dụng**: 6 trục — gia tốc kế (ax, ay, az) + con quay hồi chuyển (gx, gy, gz)
- **Phân chia subjects (Leave-Subjects-Out — LSO)**:
  - Train: SA01–SA18, SE01–SE08
  - Val:   SA19–SA21, SE09–SE11
  - Test:  SA22–SA23, SE12–SE15

---

## 2. Chiến Lược Windowing (Cửa Sổ Trượt)

### Cấu hình cố định (không thay đổi khi không retrain)
- **Window size**: 200 mẫu = **2 giây** ở 100 Hz
- **Overlap/stride**: 50 mẫu = 0,5 giây (75% overlap)
- Mỗi file CSV windowed = 1 sample shape `(200, 6)`

### Tại sao window 2 giây?
Pha ngã hoàn chỉnh (mất thăng bằng → chạm đất) kéo dài trung bình 0,5–1,5 giây. Window 2 giây đảm bảo toàn bộ pha ngã nằm trong ít nhất 1 cửa sổ, overlap 75% đảm bảo không bỏ sót ngã xảy ra ở biên cửa sổ.

---

## 3. Tiến Trình Thiết Kế Nhãn (Label Design)

### Giai đoạn 1 — 4 nhãn đơn giản (v1–v12)

| Nhãn | Mã SisFall | Ghi chú |
|---|---|---|
| `Walk` (0) | D01, D02, D05, D06, **D19** | D19 = vấp ngã hụt, gộp vào Walk để model học phân biệt |
| `Run` (1) | D03, D04 | |
| `Static/ADL` (2) | D07–D18 | Gộp tất cả: đứng, ngồi, nằm, cúi, chuyển tư thế |
| `Fall` (3) | F01–F15 | |

**Vấn đề**: nhãn `Static/ADL` quá rộng — các hành động chuyển tư thế (đứng lên từ ngồi, nằm xuống) sinh xung gia tốc rất giống ngã → **False Positive** cao.

### Giai đoạn 2 — 5 nhãn chuyên biệt (v22+)

| Nhãn | Nội dung | Lý do tách |
|---|---|---|
| `Walk` (0) | D01, D02, D05, D06 | Di chuyển có nhịp điệu |
| `Run` (1) | D03, D04 | |
| `Idle` (2) | Đứng yên, ngồi, nằm (StandSit, Lie) | Trạng thái tĩnh — ít nhiễu |
| `Trans` (3) | Chuyển tư thế (ngồi→đứng, nằm→ngồi) | **Nhãn chống FP** — tách riêng để model học phân biệt với Fall |
| `Fall` (4) | F01–F15 | |

**Kết quả**: thêm nhãn `Trans` giúp model phân biệt được chuyển động đột ngột nhưng có chủ ý vs. té ngã ngoài ý muốn → giảm đáng kể False Positive trong sinh hoạt thường ngày.

---

## 4. Tiến Trình Kiến Trúc Mô Hình

### v1 — CNN-LSTM Baseline

```
Conv1D(64) → Conv1D(64) → MaxPool → Dropout(0.3)
→ LSTM(128, return_seq) → LSTM(64) → Dropout(0.4)
→ Dense(32) → Dense(4, softmax)
```

- Input: `(200, 6)`, 4 classes
- Class weight: `balanced` + Fall ×2.0
- **Vấn đề**: overfit, kích thước lớn (LSTM 128 nặng cho MCU)

---

### v4 — CNN-LSTM + BatchNorm + L2 Regularization

```
Conv1D(32) + BN → Conv1D(32) + BN → MaxPool → Dropout(0.3)
→ LSTM(64, return_seq) + L2 → LSTM(32) + L2 → Dropout(0.4)
→ Dense(16) + L2 → Dense(4, softmax)
```

- Thu gọn filters (64→32) và LSTM (128→64, 64→32)
- Thêm BatchNormalization + L2(0.001) trên mọi lớp
- **Cải thiện**: ít overfit hơn, nhỏ hơn nhưng LSTM vẫn khó quantize INT8 cho TFLite Micro

---

### v8 — TCN (Temporal Convolutional Network) — Bước ngoặt

```
BN(input)
→ 2 stacks × 4 dilations [1, 2, 4, 8]:
    Conv1D(32, k=3, dilation=d, padding='causal') + BN + Dropout(0.2) + Residual
→ GlobalAveragePooling1D
→ Dropout(0.3) → Dense(4, softmax)
```

- **Loại bỏ hoàn toàn LSTM** — thay bằng dilated causal convolution
- Receptive field = 2×(1+2+4+8)×(3-1) = 120 mẫu — đủ bao phủ 1,2 giây tín hiệu
- **Ưu điểm với MCU**: Conv1D quantize INT8 tốt hơn LSTM nhiều
- Export TFLite Full INT8 lần đầu thành công

---

### v12 — TCN + Valid Padding (MCU-friendly)

```
padding='causal' → padding='valid' + Cropping1D(crop_size = 2×d×(k-1))
```

- Chuyển từ `padding='causal'` sang `padding='valid'` + cắt residual bằng `Cropping1D`
- TFLite Micro hỗ trợ `VALID` padding tốt hơn `CAUSAL` trên ESP32-S3
- Xác nhận input chỉ dùng **6 kênh** (bỏ các kênh dư của dataset gốc)
- **Tự động export C++ firmware**: sinh `model_data.cc` + `model_data.h` trực tiếp từ script

---

### v22 — TCN + SE Block + 5 Nhãn + Label Smoothing

```
2 stacks × 4 dilations + SE Block (Squeeze-and-Excitation attention)
→ GlobalAveragePooling1D + GlobalMaxPooling1D (Dual Pooling)
→ Concatenate → Dropout → Dense(5, softmax)
```

- **SE Block**: attention cơ chế "channel re-weighting" — cho model tập trung vào trục cảm biến quan trọng nhất ở từng pha chuyển động
- **Dual Pooling (GAP + GMP)**: GAP nắm đặc trưng trung bình, GMP giữ đặc trưng cực trị — quan trọng cho phát hiện đỉnh gia tốc của cú ngã
- **Label Smoothing = 0.1**: giảm overconfidence, cải thiện calibration
- **Decision threshold = 0.25** cho Fall: nếu `P(Fall) ≥ 0.25` → kết luận ngã (thay vì 0.5 mặc định) — đánh đổi tăng Recall, giảm Precision, chấp nhận được trong ứng dụng y tế khẩn cấp
- Chuyển sang **5 nhãn** (thêm `Trans`)

---

### v25 — 1D ResNet (Kiến trúc cuối cùng) ✅

```
Stem: Conv1D(16, k=3, stride=2) + BN + relu6  [200×6 → 100×16]
Block 1: SeparableConv1D(16) × 2 + SE + Residual + Dropout  [100×16]
Block 2: SeparableConv1D(32, stride=2) × 2 + SE + Residual  [50×32]
Block 3: SeparableConv1D(32) × 2 + SE + Residual            [50×32]
Block 4: SeparableConv1D(64, stride=2) × 2 + SE + Residual  [25×64]
→ GAP + GMP → Concatenate → Dropout(0.3) → Dense(5, softmax)
```

**Tại sao chuyển từ TCN sang ResNet?**
- **Skip connection phân cấp** (mỗi block có residual riêng) tốt hơn TCN chỉ có residual ngang hàng
- **SeparableConv1D** = Depthwise + Pointwise: ESP-NN tăng tốc depthwise 6,3× so với Conv1D thường
- **relu6** thay cho relu: giới hạn giá trị [0, 6] — thân thiện với quantization INT8
- **Stride=2** trong 3 block: giảm độ dài chuỗi dần thay vì dùng MaxPooling
- Kế thừa toàn bộ từ v22: SE Block, Dual Pooling, Label Smoothing, threshold 0.25
- **Code refactored**: tách `DataPreprocessor` + `OutputReporter` thành `ml_pipeline.py` — dùng chung cho các version sau

**Tối ưu hóa ESP-NN tích hợp trong kiến trúc:**
| Kỹ thuật | Tăng tốc ESP-NN |
|---|---|
| SeparableConv (depthwise) | 6,3× |
| Pointwise Conv 1×1 | 14,2× |
| relu6 | 11,5× |
| INT8 Quantization toàn bộ | ~4× memory + ~2× latency |

---

## 5. Tối Ưu Hóa Phần Cứng — PCNT + Light Sleep

### PCNT (Pulse Counter) cho lấy mẫu IMU chính xác

ESP32-S3 sử dụng peripheral **PCNT (Pulse Counter)** để tạo ngắt lấy mẫu 100 Hz thay vì dùng `vTaskDelay` trong FreeRTOS task.

**Lý do:**
- `vTaskDelay` bị drift do jitter của FreeRTOS scheduler → tần số lấy mẫu không ổn định
- PCNT chạy độc lập, không bị ảnh hưởng bởi CPU load → jitter < 1 µs

**Nguyên lý:** Một timer hardware phát xung 100 Hz vào chân PCNT. Khi đếm đủ 1 xung, ISR được kích hoạt → đọc MPU6050 qua I2C → đẩy vào ring buffer của `svc_imu`.

### Automatic Light Sleep (Phase 4.2 — chưa triển khai)

Kế hoạch: giữa các ngắt PCNT (10ms/lần), ESP32-S3 tự động vào **Automatic Light Sleep** (Tickless Idle của FreeRTOS):

- CPU clock giảm xuống XTAL 40 MHz (thay vì PLL 240 MHz) trong thời gian idle
- I2C và PCNT clock chuyển sang nguồn RTC để duy trì ngắt khi CPU ngủ
- Tiết kiệm ước tính 30–50% điện năng so với chạy liên tục

**Lưu ý khi triển khai**: phải cấu hình lại clock source của I2C và PCNT sang `XTAL_CLK`/`RTC_CLK` trước khi bật `esp_pm_configure()` — nếu không I2C sẽ bị mất clock khi CPU ngủ.

---

## 6. Chiến Lược Xử Lý Class Imbalance

SisFall bị mất cân bằng nặng: ~80% ADL, ~20% Fall.

| Kỹ thuật | Áp dụng từ |
|---|---|
| `class_weight='balanced'` (sklearn) | v1 |
| Fall weight ×2.0 bổ sung | v1 |
| Fall weight ×3.0 | v12, v22, v25 |
| Label Smoothing = 0.1 | v22, v25 |
| Decision threshold = 0.25 cho Fall | v12, v22, v25 |

**Triết lý**: trong ứng dụng y tế khẩn cấp, **Recall của Fall > Precision**. Chấp nhận một số False Positive (cảnh báo nhầm) để tránh bỏ sót True Fall. Nhân viên y tế có thể xác nhận tại chỗ, nhưng bỏ sót cú ngã thực sự là không thể chấp nhận.

---

## 7. Pipeline Huấn Luyện Chuẩn (từ v25)

```
SisFall raw (200Hz) → Downsample (100Hz) → Sliding Window (200×6, overlap 50)
→ CSV files → ThreadPoolExecutor load → NumPy cache (.npy)
→ class_weight balanced + Fall×3 → One-hot encoding
→ Train (LSO) / Val (LSO) / Test (LSO)
→ ModelCheckpoint (val_loss) + EarlyStopping(patience=15) + ReduceLROnPlateau
→ TFLite Float32 export → C++ array (model_data.cc + model_data.h)
```

---

## 8. File Liên Quan

| File | Nội dung |
|---|---|
| `firmware_architecture_design.md` | Kiến trúc tích hợp model vào firmware (svc_ai, sliding window, cooldown) |
| `firmware_architecture_update_080526.md` | Cập nhật kiến trúc mới nhất |
| `schema.md` | Cấu trúc DB — nơi kết quả inference được lưu (InfluxDB telemetry) |
| `protocol.md` | Cấu trúc MQTT payload khi Fall được phát hiện |
