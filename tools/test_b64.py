import base64
import struct
import math

data_b64 = "uwAVAAUA5f8a/W4PvAAVAAUA5f8b/WwPvAAVAAUA5f8b/WoPvAAVAAUA5f8a/WkPvAAVAAUA5f8Z/WkPuwAVAAUA5f8X/WsPuwAVAAQA5f8Y/W4PvAAVAAQA5f8Z/XAPvQAVAAQA5f8X/W8PvAAVAAQA5f8W/XMPvQAVAAQA5f8U/XIPvQAVAAQA5f8U/XIPvwAVAAQA5P8S/XMPvgAUAAQA5P8U/XcPvQAUAAQA5P8W/XgPuwAVAAQA5f8X/XgPuQAVAAQA5f8Z/XUPugAVAAQA5f8Z/XQPuwAUAAQA5f8X/XEPvQAUAAQA5f8X/XMPvQAUAAQA5f8V/XQPvQAUAAQA5f8W/XQPvgAUAAQA5f8X/XEPvQAVAAQA5f8Z/W8PvQAVAAQA5f8a/WwPuwAVAAQA5f8Z/WwPuwAVAAQA5f8X/XAPvQAUAAQA5f8Z/XAPvAAUAAQA5f8a/XEPuAAUAAQA5f8a/XEPtwAUAAQA5f8Z/XEPuAAUAAQA5f8X/W0PuQAUAAQA5f8Z/W4PuQAUAAUA5f8Y/WwPugAUAAUA5f8Y/WwPugAUAAUA5f8X/WwPuwAUAAUA5f8W/XAPuwAUAAUA5f8T/XAPuwAUAAUA5f8R/W4PugAUAAUA5f8S/WwPuAAUAAUA5P8U/XAPuAAUAAUA5P8X/XMPugAUAAQA5P8X/XQPugAVAAQA5P8X/XAPuwAVAAQA5P8W/W8PugAVAAQA5P8V/XIPugAVAAQA5P8W/XMPuwAVAAQA5P8W/XUPuQAVAAQA5P8="

# add padding if missing
padding = len(data_b64) % 4
if padding:
    data_b64 += '=' * (4 - padding)

data = base64.b64decode(data_b64)

for i in range(len(data) // 12):
    offset = i * 12
    # ESP32 uses Little Endian
    ax_raw, ay_raw, az_raw, gx_raw, gy_raw, gz_raw = struct.unpack('<hhhhhh', data[offset:offset+12])
    
    ax = ax_raw / 4096.0
    ay = ay_raw / 4096.0
    az = az_raw / 4096.0
    
    gx = gx_raw / 16.4
    gy = gy_raw / 16.4
    gz = gz_raw / 16.4
    
    svm = math.sqrt(ax*ax + ay*ay + az*az)
    print(f"Sample {i}: ax={ax:.3f}, ay={ay:.3f}, az={az:.3f} | svm={svm:.3f}")
