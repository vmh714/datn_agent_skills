# Kế hoạch cải thiện thuật toán đọc và tính toán % Pin (Battery Accuracy)

Dựa trên quá trình phân tích đặc tuyến pin Li-ion và phần cứng mạch đo, dưới đây là kế hoạch nâng cấp module `drv_battery.c` nhằm giải quyết triệt để các vấn đề nhiễu tín hiệu, sụt áp do tải và đặc tuyến xả phi tuyến của pin.

## 1. Nâng cấp Thuật toán Lọc Nhiễu
Hiện tại, việc lấy giá trị lớn nhất (MAX) trong cửa sổ 5 mẫu chỉ giải quyết được sự cố sụt áp khi tải nặng, nhưng lại dễ bị đánh lừa bởi các gai nhiễu dương (spikes).
- **Giải pháp:** Sử dụng **Median Filter (Lọc trung vị)** kết hợp **EMA (Exponential Moving Average)**.
  1. Đọc ADC, lưu vào mảng 5 mẫu.
  2. Sắp xếp mảng và lấy giá trị giữa (mẫu số 3) để loại bỏ hoàn toàn cả nhiễu âm (dips) và nhiễu dương (spikes).
  3. Đưa giá trị trung vị này qua bộ lọc EMA để làm mượt dài hạn: `V_EMA = alpha * V_new + (1 - alpha) * V_EMA` (với `alpha ~ 0.1`).

## 2. Ánh xạ Tuyến tính hóa bằng LUT (Look-up Table)
Pin Li-ion tụt áp rất nhanh ở khoảng 4.2V -> 4.0V và 3.5V -> 3.3V, nhưng lại đi ngang rất lâu ở khúc giữa. Map tuyến tính thông thường sẽ gây cảm giác pin sụt nhanh đột ngột.
- **Giải pháp:** Xây dựng bảng tra 11 điểm (từ 0% đến 100%):
```c
const uint16_t bat_voltage_lut[11] = {
    3000, // 0%   (Đã điều chỉnh xuống 3.0V thay vì 3.3V)
    3500, // 10%
    3600, // 20%
    3680, // 30%
    3740, // 40%
    3770, // 50%
    3800, // 60%
    3850, // 70%
    3950, // 80%
    4050, // 90%
    4200  // 100%
};
```
- Sử dụng **Nội suy tuyến tính (Linear Interpolation)** để tìm giá trị % chính xác khi điện áp nằm giữa 2 mốc trong LUT.

## 3. Logic Monotonic Discharging (Chỉ giảm, không tăng)
Khi hệ thống chạy tải nặng (inference AI hoặc đẩy MQTT qua 4G), điện áp pin sẽ dao động, dẫn đến % pin nhảy lên nhảy xuống.
- **Giải pháp phần mềm:** Biến lưu % pin hiện tại (`current_battery_percent`) sẽ **chỉ được phép giữ nguyên hoặc giảm xuống**. Các tính toán trả về % cao hơn sẽ bị bỏ qua (trừ khi thiết bị đang cắm sạc).

## 4. Những Cải tiến & Yêu cầu về Phần Cứng
Việc đo trực tiếp tại chân B+/B- (trước mạch bảo vệ DW01) giúp đọc điện áp thật của cell, nhưng mang lại vài hệ lụy cần fix cả cứng lẫn mềm:
1. **Hiệu chuẩn ADC:** Cần gọi API hiệu chuẩn (`esp_adc_cal_...`) của ESP-IDF thay vì chỉ nhân tĩnh hệ số `s_ratio`, vì ESP32 ADC có độ cong lớn.
2. **Quiescent Current (Dòng rò tĩnh):** Mạch phân áp gắn trực tiếp B+/B- sẽ ăn điện 24/7. Cần đổi cặp trở phân áp thành giá trị lớn (**100kΩ - 100kΩ** hoặc **470kΩ - 470kΩ**) để dòng rò tụt xuống cỡ vài µA. Khi dùng trở lớn, bắt buộc mắc thêm **tụ gốm 0.1µF** song song điện trở dưới (xuống GND) để lọc nhiễu Low-Pass và ổn định dòng nạp cho tụ lấy mẫu ADC.
3. **Cờ sạc (Charging Flag) & Hiện tượng pin đầy ảo:** Khi cắm sạc (TP4056 vọt lên 4.2V), phải có một chân GPIO nối đường 5V/USB để nhận biết.
   - Nếu có cắm sạc: `is_charging = true` -> bỏ qua logic "chỉ giảm", có thể show animation sạc.
   - Khi rút sạc: Phải **Reset bộ lọc EMA** để tránh áp 4.2V lưu luyến làm sai kết quả.
4. **Điểm neo 0% (Cut-off voltage):** Mạch bảo vệ ngắt ở 2.5-2.8V, mức 3.3V thực tế vẫn còn năng lượng. Hạ điểm 0% của LUT xuống **3.0V** là hợp lý nhất.
