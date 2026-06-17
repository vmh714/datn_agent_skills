# PROJECT MAP (AUTO-GENERATED)

> Sinh tự động bởi `tools/gen_project_map.py` lúc 2026-06-17 17:07.
> KHÔNG sửa tay file này — sửa code rồi chạy lại script. Bản tay (có diễn giải): `PROJECT_MAP.md`.
>
> Mọi `path:line` TƯƠNG ĐỐI VỚI GỐC PROJECT FIRMWARE (vd `components/svc_imu/...`),
> portable bất kể firmware nằm ở `firmware/` (máy gốc) hay `firmware/<repo>/` (máy clone).

## Public API theo component
- **drv_a7680c**: `drv_a7680c_init` (components/drv_a7680c/include/drv_a7680c.h:18), `drv_a7680c_power_on` (components/drv_a7680c/include/drv_a7680c.h:27), `drv_a7680c_power_off` (components/drv_a7680c/include/drv_a7680c.h:33)
- **drv_battery**: `drv_battery_init` (components/drv_battery/include/drv_battery.h:15), `drv_battery_read_mv` (components/drv_battery/include/drv_battery.h:21), `drv_battery_read_percent` (components/drv_battery/include/drv_battery.h:27)
- **drv_mpu6050**: `mpu6050_init` (components/drv_mpu6050/include/mpu6050.h:133), `mpu6050_config` (components/drv_mpu6050/include/mpu6050.h:139), `mpu6050_read_raw` (components/drv_mpu6050/include/mpu6050.h:145), `mpu6050_read` (components/drv_mpu6050/include/mpu6050.h:151), `mpu6050_raw_to_float` (components/drv_mpu6050/include/mpu6050.h:158), `mpu6050_reset_fifo` (components/drv_mpu6050/include/mpu6050.h:163), `mpu6050_get_sample_rate` (components/drv_mpu6050/include/mpu6050.h:169), `mpu6050_calibrate_gyro` (components/drv_mpu6050/include/mpu6050.h:174), `mpu6050_read_fifo` (components/drv_mpu6050/include/mpu6050.h:182)
- **lib_kalman**: `kalman_init` (components/lib_kalman/include/kalman_filter.h:31), `kalman_get_angle` (components/lib_kalman/include/kalman_filter.h:41), `kalman_1d_init` (components/lib_kalman/include/kalman_filter.h:66), `kalman_1d_update` (components/lib_kalman/include/kalman_filter.h:74)
- **lib_pedometer**: `pedometer_init` (components/lib_pedometer/include/pedometer.h:36), `pedometer_process` (components/lib_pedometer/include/pedometer.h:49)
- **lib_tinyml**: `tflite_init` (components/lib_tinyml/include/tflite_wrapper.h:14), `tflite_run_inference` (components/lib_tinyml/include/tflite_wrapper.h:19), `get_input_bytes` (components/lib_tinyml/include/tflite_wrapper.h:47)
- **svc_ai**: `svc_ai_init` (components/svc_ai/include/svc_ai.h:22), `svc_ai_process_window` (components/svc_ai/include/svc_ai.h:35), `svc_ai_get_latest_prediction` (components/svc_ai/include/svc_ai.h:41), `svc_ai_get_latest_confidence` (components/svc_ai/include/svc_ai.h:47)
- **svc_cloud**: `svc_cloud_init` (components/svc_cloud/include/svc_cloud.h:16), `svc_cloud_is_connected` (components/svc_cloud/include/svc_cloud.h:22), `svc_cloud_publish` (components/svc_cloud/include/svc_cloud.h:32), `svc_cloud_enqueue_imu_batch` (components/svc_cloud/include/svc_cloud.h:40)
- **svc_imu**: `imu_service_init` (components/svc_imu/include/imu_service.h:40), `imu_service_get_latest_pitch` (components/svc_imu/include/imu_service.h:46), `imu_service_register_batch_callback` (components/svc_imu/include/imu_service.h:54), `imu_service_get_steps` (components/svc_imu/include/imu_service.h:61)
- **svc_network**: `svc_network_init` (components/svc_network/include/svc_network.h:13), `svc_network_is_connected` (components/svc_network/include/svc_network.h:19), `svc_network_init_cellular` (components/svc_network/include/svc_network.h:40)
- **sys_manager**: `sys_manager_init` (components/sys_manager/include/sys_manager.h:63), `sys_manager_get_state` (components/sys_manager/include/sys_manager.h:69), `sys_manager_set_state` (components/sys_manager/include/sys_manager.h:75)

## Enum (FSM states / event ids / class...)
- `accel_fs_t` (components/drv_mpu6050/include/mpu6050.h): ACCEL_FS_2G, ACCEL_FS_4G, ACCEL_FS_8G, ACCEL_FS_16G
- `ai_event_id_t` (components/sys_manager/include/sys_manager.h): AI_EVT_FALL_DETECTED
- `ai_posture_class_t` (components/lib_tinyml/include/tflite_wrapper.h): AI_CLASS_WALK, AI_CLASS_RUN, AI_CLASS_IDLE, AI_CLASS_TRANSITION, AI_CLASS_FALL, AI_CLASS_UNKNOWN
- `cloud_event_id_t` (components/sys_manager/include/sys_manager.h): CLOUD_EVT_MQTT_CONNECTED, CLOUD_CMD_START_STREAM, CLOUD_CMD_STOP_STREAM
- `gyro_fs_t` (components/drv_mpu6050/include/mpu6050.h): GYRO_FS_250DPS, GYRO_FS_500DPS, GYRO_FS_1000DPS, GYRO_FS_2000DPS
- `imu_event_id_t` (components/sys_manager/include/sys_manager.h): IMU_EVT_BATCH_READY, IMU_EVT_WINDOW_READY
- `mpu6050_dlpf_t` (components/drv_mpu6050/include/mpu6050.h): DLPF_CFG_260HZ, DLPF_CFG_184HZ, DLPF_CFG_94HZ, DLPF_CFG_44HZ, DLPF_CFG_21HZ, DLPF_CFG_10HZ, DLPF_CFG_5HZ, DLPF_CFG_REVERSED
- `net_event_id_t` (components/sys_manager/include/sys_manager.h): NET_EVT_WIFI_CONNECTED, NET_EVT_CELLULAR_CONNECTED, NET_EVT_DISCONNECTED
- `sys_event_id_t` (components/sys_manager/include/sys_manager.h): SYS_EVT_READY, SYS_EVT_ENTER_STREAM_MODE, SYS_EVT_ENTER_NORMAL_MODE
- `system_state_t` (components/sys_manager/include/sys_manager.h): STATE_INIT, STATE_CONNECTING, STATE_NORMAL, STATE_STREAMING, STATE_OTA, STATE_ERROR

## Hằng số (#define)
- `ACCEL_CONFIG = 0x1C` (components/drv_mpu6050/include/mpu6050.h:12)
- `ACCEL_FS_POS = 3` (components/drv_mpu6050/include/mpu6050.h:28)
- `ACCEL_XOUT_H = 0x3B` (components/drv_mpu6050/include/mpu6050.h:13)
- `ACCEL_XOUT_L = 0x3C` (components/drv_mpu6050/include/mpu6050.h:14)
- `FIFO_COUNT_H = 0x72` (components/drv_mpu6050/include/mpu6050.h:23)
- `FIFO_COUNT_L = 0x73` (components/drv_mpu6050/include/mpu6050.h:24)
- `FIFO_EN = 0x23` (components/drv_mpu6050/include/mpu6050.h:22)
- `FIFO_R_W = 0x74` (components/drv_mpu6050/include/mpu6050.h:25)
- `GYRO_CONFIG = 0x1B` (components/drv_mpu6050/include/mpu6050.h:11)
- `GYRO_FS_POS = 3` (components/drv_mpu6050/include/mpu6050.h:29)
- `IMU_BATCH_SIZE = 50` (components/svc_imu/include/imu_service.h:10)
- `IMU_WINDOW_SIZE = 200` (components/svc_imu/include/imu_service.h:9)
- `INT_ENABLE = 0x38` (components/drv_mpu6050/include/mpu6050.h:19)
- `INT_PIN_CFG = 0x37` (components/drv_mpu6050/include/mpu6050.h:18)
- `INT_STATUS = 0x3A` (components/drv_mpu6050/include/mpu6050.h:20)
- `MPU_ADDR = 0x68` (components/drv_mpu6050/include/mpu6050.h:6)
- `MPU_FREQ = 400000` (components/drv_mpu6050/include/mpu6050.h:7)
- `MPU_REG_CONFIG = 0x1A` (components/drv_mpu6050/include/mpu6050.h:15)
- `MPU_REG_SMPLRT_DIV = 0x19` (components/drv_mpu6050/include/mpu6050.h:16)
- `PWR_MGMT_1 = 0x6B` (components/drv_mpu6050/include/mpu6050.h:9)
- `PWR_MGMT_2 = 0x6C` (components/drv_mpu6050/include/mpu6050.h:10)
- `USER_CTRL = 0x6A` (components/drv_mpu6050/include/mpu6050.h:21)
- `WHO_AM_I = 0x75` (components/drv_mpu6050/include/mpu6050.h:8)

## MQTT topics (chuỗi trong code)
- `eldercare/%s/alert/fall` (components/svc_cloud/svc_cloud.c:348)
- `eldercare/%s/command` (components/svc_cloud/svc_cloud.c:63)
- `eldercare/%s/imu_stream` (components/svc_cloud/svc_cloud.c:246)
- `eldercare/%s/status` (components/svc_cloud/svc_cloud.c:290)
