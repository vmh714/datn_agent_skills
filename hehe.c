// === PCNT ISR Callback ===
// MPU6050 only fires an interrupt per sample (100Hz = 100 ISRs/sec).
// Instead of waking the CPU for every single sample, the PCNT hardware
// peripheral counts those pulses autonomously. When it reaches
// IMU_BATCH_SIZE (50), this callback fires — waking the task only once
// every ~0.5s. The CPU is free to sleep or run other tasks in between.
static bool IRAM_ATTR pcnt_on_reach(pcnt_unit_handle_t unit, const pcnt_watch_event_data_t *edata, void *user_ctx)
{
    BaseType_t high_task_wakeup = pdFALSE;
    vTaskNotifyGiveFromISR(imu_task_handle, &high_task_wakeup);
    return high_task_wakeup == pdTRUE;
}

// === Main IMU Processing Task ===
// Pipeline: PCNT wakeup → FIFO burst read → raw-to-float → axis remap
//           → Kalman filter → sliding window (for TinyML) + batch stream (to cloud)
static void imu_processing_task(void *pvParameters)
{
    mpu6050_data_raw_t raw_data[IMU_BATCH_SIZE];
    uint16_t count;
    uint16_t sample_rate = mpu6050_get_sample_rate();
    if (sample_rate == 0) sample_rate = 100;
    float dt = 1.0f / (float)sample_rate;

    while (1) {
        // Block until PCNT fires (50 samples ready) or timeout after 1s
        // Timeout = self-healing: if MPU6050 hangs, reset FIFO and retry
        uint32_t notified = ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(1000));
        if (notified == 0) {
            mpu6050_reset_fifo();
            pcnt_unit_clear_count(pcnt_unit);
            continue;
        }

        count = IMU_BATCH_SIZE;
        if (mpu6050_read_fifo(raw_data, &count) == ESP_OK && count > 0) {
            bool is_streaming = (sys_manager_get_state() == STATE_STREAMING);
            if (!is_streaming) s_batch_data.count = 0;

            for (int i = 0; i < count; i++) {
                mpu6050_data_t processed_data;
                mpu6050_raw_to_float(&raw_data[i], &processed_data);

                // Axis remapping: PCB mounts the sensor in a different
                // orientation than the body. Transform to Forward-Left-Up
                // (FLU) so Roll=0, Pitch=0 when the device is upright.
                float ax_body = processed_data.az;
                float ay_body = processed_data.ax;
                float az_body = processed_data.ay;
                float gx_body = processed_data.gz;
                float gy_body = processed_data.gx;

                float accel_roll  = atan2(ay_body, az_body) * RAD_TO_DEG;
                float accel_pitch = atan2(-ax_body, sqrt(ay_body * ay_body + az_body * az_body)) * RAD_TO_DEG;

                // During a fall (pitch > 75°), accelerometer roll degrades
                // due to gimbal lock + impact forces → trust gyro more
                kal_roll.R_measure = (fabsf(accel_pitch) > 75.0f) ? 2.0f : 0.05f;

                // Kalman sensor fusion: fuse noisy accel angle with gyro
                // rate to get a clean, drift-free orientation estimate
                last_roll  = kalman_get_angle(&kal_roll,  accel_roll,  gx_body, dt);
                last_pitch = kalman_get_angle(&kal_pitch, accel_pitch, gy_body, dt);

                // Sliding window (circular buffer): keeps the last 1s of
                // filtered angles ready for on-device TinyML fall inference
                imu_win.roll[imu_win.head]  = last_roll;
                imu_win.pitch[imu_win.head] = last_pitch;
                imu_win.head = (imu_win.head + 1) % IMU_WINDOW_SIZE;

                // When FSM is in STREAMING state (commanded by cloud),
                // also buffer raw data to send to the web for monitoring
                if (is_streaming && s_batch_data.count < IMU_BATCH_SIZE) {
                    s_batch_data.data[s_batch_data.count].ax = raw_data[i].ax;
                    s_batch_data.data[s_batch_data.count].ay = raw_data[i].ay;
                    s_batch_data.data[s_batch_data.count].az = raw_data[i].az;
                    s_batch_data.data[s_batch_data.count].gx = raw_data[i].gx;
                    s_batch_data.data[s_batch_data.count].gy = raw_data[i].gy;
                    s_batch_data.data[s_batch_data.count].gz = raw_data[i].gz;
                    s_batch_data.count++;
                }
            }

            // Batch full → dispatch to cloud service via registered callback
            if (is_streaming && s_batch_data.count >= IMU_BATCH_SIZE) {
                if (s_batch_callback) s_batch_callback(&s_batch_data);
                s_batch_data.count = 0;
            }
        }
    }
}

// === Initialization ===
esp_err_t imu_service_init(gpio_num_t int_pin)
{
    kalman_init(&kal_roll);
    kalman_init(&kal_pitch);
    memset(&imu_win, 0, sizeof(imu_window_t));

    // Hot Start: read the real angle NOW and seed the Kalman state,
    // so it doesn't have to "ramp up" from 0° at boot
    mpu6050_data_t init_data = mpu6050_read();
    float init_roll  = atan2(init_data.ax, init_data.ay) * RAD_TO_DEG;
    float init_pitch = atan2(-init_data.az, sqrt(init_data.ax * init_data.ax + init_data.ay * init_data.ay)) * RAD_TO_DEG;
    kal_roll.angle = init_roll;   kal_pitch.angle = init_pitch;
    last_roll = init_roll;        last_pitch = init_pitch;

    mpu6050_reset_fifo();
    xTaskCreate(imu_processing_task, "imu_task", 4096, NULL, 10, &imu_task_handle);

    // PCNT setup: wire MPU6050's INT pin to the hardware pulse counter.
    // It counts falling edges autonomously until IMU_BATCH_SIZE, then
    // fires pcnt_on_reach → wakes the processing task. No CPU overhead
    // for the 49 samples in between.
    pcnt_unit_config_t unit_config = { .high_limit = IMU_BATCH_SIZE, .low_limit = -1 };
    pcnt_new_unit(&unit_config, &pcnt_unit);
    pcnt_unit_set_glitch_filter(pcnt_unit, &(pcnt_glitch_filter_config_t){ .max_glitch_ns = 1000 });

    pcnt_chan_config_t chan_config = { .edge_gpio_num = int_pin, .level_gpio_num = -1 };
    pcnt_channel_handle_t pcnt_chan = NULL;
    pcnt_new_channel(pcnt_unit, &chan_config, &pcnt_chan);
    pcnt_channel_set_edge_action(pcnt_chan, PCNT_CHANNEL_EDGE_ACTION_HOLD, PCNT_CHANNEL_EDGE_ACTION_INCREASE);

    pcnt_unit_add_watch_point(pcnt_unit, IMU_BATCH_SIZE);
    pcnt_event_callbacks_t cbs = { .on_reach = pcnt_on_reach };
    pcnt_unit_register_event_callbacks(pcnt_unit, &cbs, NULL);

    pcnt_unit_enable(pcnt_unit);
    pcnt_unit_clear_count(pcnt_unit);
    pcnt_unit_start(pcnt_unit);

    return ESP_OK;
}