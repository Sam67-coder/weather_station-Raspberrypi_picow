# Raspberry Pi Pico W Weather Station & Data Logger

A MicroPython project for the Raspberry Pi Pico W that syncs a DS3231 Real-Time Clock (RTC) over Wi-Fi on boot, disconnects Wi-Fi to save power and reduce thermal drift, displays live time and sensor readings on a 16x2 I2C LCD, and logs temperature and humidity to a local CSV file.

---

## Hardware & Pinout

| Component | Interface | Pico W Pin(s) | Notes |
| :--- | :--- | :--- | :--- |
| **DS3231 RTC** | I2C Bus 0 (100 kHz) | SDA: `GP16`, SCL: `GP17` | I2C Address: `0x68` |
| **16x2 I2C LCD** | I2C Bus 1 (50 kHz) | SDA: `GP2`, SCL: `GP3` | I2C Address: `0x27` |
| **DHT22 Sensor** | Digital GPIO | Data: `GP15` | Polled every 2 seconds |

---

## Key Features & Fixes Included

* **Initialization & Safety:** Initializes `CSV_LOG_INTERVAL_SEC`, `last_dht_ms`, and `last_log_ms` before the main loop, and guards CSV logging until valid sensor values exist.
* **Latency Compensation (`TIME_OFFSET_SEC = 2`):** Uses `time.mktime()` and `time.localtime()` to safely add a 2-second offset (handling minute/hour/day rollovers) right before writing to the RTC to compensate for HTTPS request latency.
* **HTTP & JSON Validation:** Verifies `res.status_code == 200` before parsing JSON and properly closes sockets and runs `gc.collect()` in a `finally` block to prevent memory leaks.
* **Flicker-Free Display & Drift Compensation:** Updates the LCD in place without clearing the screen every second and calculates exact remaining sleep milliseconds (`1000 - elapsed`) to keep the clock ticking smoothly.
