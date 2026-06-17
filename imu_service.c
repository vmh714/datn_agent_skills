// ============================================================================
//  imu_service.c — 100 Hz IMU acquisition, denoise & windowing pipeline (ESP32-S3)
//  Wearable HAR / fall-detection for elderly care. ESP-IDF; layered firmware.
// ============================================================================
#include "imu_service.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/pulse_cnt.h"
#include "kalman_filter.h"
#include "svc_ai.h"
#include "sys_manager.h"
#include <math.h>

#define RAD_TO_DEG 57.2957795131f
static TaskHandle_t         imu_task_handle  = NULL;
static pcnt_unit_handle_t   pcnt_unit        = NULL;
static kalman_1d_t          kf_ax, kf_ay, kf_az, kf_gx, kf_gy, kf_gz; // per-axis denoise
static kalman_t             kal_pitch;        // 2-state fusion: posture (lie/sit/stand)
static float                last_pitch;
static imu_window_t         imu_win;          // sliding window feeding the TinyML model
static float                s_accel_fs, s_gyro_fs; // full-scale ranges for [-1,1] scaling
static imu_batch_data_t     s_batch_data;     // staging buffer for raw-data streaming
static imu_batch_callback_t s_batch_callback = NULL;

// PCNT ISR — the MPU6050 pulses its INT pin once per sample (100 Hz). A hardware
// pulse counter tallies them autonomously; only on reaching IMU_BATCH_SIZE (50)
// does this fire, waking the task once per ~0.5 s instead of 100 times a second.
static bool IRAM_ATTR pcnt_on_reach(pcnt_unit_handle_t unit,
                                    const pcnt_watch_event_data_t *edata, void *ctx)
{
    BaseType_t hp_woken = pdFALSE;
    vTaskNotifyGiveFromISR(imu_task_handle, &hp_woken);
    return hp_woken == pdTRUE;
}

// Main task: wake -> FIFO burst read -> axis remap -> Kalman -> normalize -> window.
static void imu_processing_task(void *arg)
{
    mpu6050_data_raw_t raw[IMU_BATCH_SIZE];
    uint16_t count;
    float dt = 1.0f / 100.0f;

    while (1) {
        // Sleep until the pulse counter signals a full batch (50 samples) is ready.
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

        // Burst-read the whole batch from the sensor FIFO in one I2C transaction.
        count = IMU_BATCH_SIZE;
        mpu6050_read_fifo(raw, &count);

        bool streaming = (sys_manager_get_state() == STATE_STREAMING);
        if (!streaming) s_batch_data.count = 0;

        for (int i = 0; i < count; i++) {
            mpu6050_data_t d;
            mpu6050_raw_to_float(&raw[i], &d);

            // Remap sensor axes -> Forward-Left-Up body frame.
            float ax = -d.ax, ay = -d.ay, az = d.az;
            float gx = -d.gx, gy = -d.gy, gz = d.gz;

            // Pitch via 2-state Kalman (accel + gyro fusion) -> posture detection.
            float accel_pitch = atan2(-ax, sqrt(ay * ay + az * az)) * RAD_TO_DEG;
            last_pitch = kalman_get_angle(&kal_pitch, accel_pitch, gy, dt);

            // Denoise each of the 6 axes, then normalize to [-1,1] — the exact
            // input format the INT8-quantized TinyML model was trained on.
            float n_ax = kalman_1d_update(&kf_ax, ax) / s_accel_fs;
            float n_ay = kalman_1d_update(&kf_ay, ay) / s_accel_fs;
            float n_az = kalman_1d_update(&kf_az, az) / s_accel_fs;
            float n_gx = kalman_1d_update(&kf_gx, gx) / s_gyro_fs;
            float n_gy = kalman_1d_update(&kf_gy, gy) / s_gyro_fs;
            float n_gz = kalman_1d_update(&kf_gz, gz) / s_gyro_fs;

            imu_win.ax[imu_win.head] = n_ax; imu_win.ay[imu_win.head] = n_ay;
            imu_win.az[imu_win.head] = n_az; imu_win.gx[imu_win.head] = n_gx;
            imu_win.gy[imu_win.head] = n_gy; imu_win.gz[imu_win.head] = n_gz;
            imu_win.head = (imu_win.head + 1) % IMU_WINDOW_SIZE;

            // In STREAMING mode, stage the SAME preprocessed data (scaled to
            // int16) so the collected dataset matches what inference sees.
            if (streaming && s_batch_data.count < IMU_BATCH_SIZE) {
                imu_sample_t *o = &s_batch_data.data[s_batch_data.count++];
                o->ax = n_ax * 32767; o->ay = n_ay * 32767; o->az = n_az * 32767;
                o->gx = n_gx * 32767; o->gy = n_gy * 32767; o->gz = n_gz * 32767;
            }
        }

        // Feed the AI service every batch (0.5 s sliding step).
        svc_ai_process_window(&imu_win);

        // Streaming batch full -> hand off to the cloud uploader via callback.
        if (streaming && s_batch_data.count >= IMU_BATCH_SIZE) {
            if (s_batch_callback) s_batch_callback(&s_batch_data);
            s_batch_data.count = 0;
        }
    }
}
