---
name: esp-idf-build-manager
description: Handles ESP-IDF project compilation, flashing, and monitoring. Use this to build firmware, flash to ESP32 devices, and check logs.
---

# ESP-IDF Build Manager

This skill provides the environment and commands necessary to compile, flash, and monitor ESP32 firmware using the ESP-IDF framework on Windows.

## When to use this skill

- Use this when you need to compile (build) the current firmware project.
- Use this when you need to flash the compiled binary to an ESP32 device.
- Use this when you need to monitor the serial output of the device.
- Use this to check for compilation errors or runtime logs.

## How to use it

### 1. Environment Setup
All `idf.py` commands **must** be executed after sourcing the ESP-IDF environment script. Since each `run_command` call starts a new shell session by default, you must chain the export command with your actual command using a semicolon `;`.

**Export Script Path:**
`c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1`

### 2. Common Commands

#### Build the project
Run this from the firmware root directory (`d:\datn\firmware`).
```powershell
. "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py build
```

#### Clean and Build
Use this if you encounter weird linking issues or after changing core configurations.
```powershell
. "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py fullclean; idf.py build
```

#### Flash to device
Specify the COM port if known. If not specified, `idf.py` will attempt to auto-detect.
```powershell
. "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py -p COM3 flash
```

#### Monitor device output
To see the serial logs from the ESP32.
```powershell
. "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py -p COM3 monitor
```

#### Flash and Monitor (Recommended)
Combines flashing and immediately opening the serial monitor.
```powershell
. "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py -p COM3 flash monitor
```

### 3. Guidelines & Troubleshooting
- **Cwd:** Ensure you are in the directory containing `CMakeLists.txt` (usually `d:\datn\firmware`).
- **COM Port:** If the device isn't found, you can list available COM ports in PowerShell:
  ```powershell
  [System.IO.Ports.SerialPort]::GetPortNames()
  ```
- **Recursive Submodules:** If the build fails due to missing components in `managed_components` or submodules, try:
  ```powershell
  . "c:\Users\vuman\.antigravity\extensions\espressif.esp-idf-extension-2.1.0-universal\export.ps1"; idf.py reconfigure
  ```
- **Menuconfig:** If you need to change project settings, use `idf.py menuconfig`. Note that this is an interactive UI and might be tricky to handle via `send_command_input`. Prefer modifying `sdkconfig` directly or using `idf.py build` to see if it triggers the necessary prompts.
