import network
import urequests
import dht
import time
import rp2
from machine import Pin, I2C
from rpi_lcd_i2c_micropython import I2cLcd

# --- Settings ---
SSID = "YOUR_2.4GHZ_NETWORK"
PASSWORD = "THE_PASSWORD"
WIFI_TIMEOUT_SEC = 30
CSV_LOG_INTERVAL_SEC = 60  # Save to CSV once per minute

# --- Hardware Setup ---
rtc_i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
lcd_i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=50000)

lcd = I2cLcd(lcd_i2c, 0x27, 2, 16)
sensor = dht.DHT22(Pin(15))

def lcd_write(row0, row1=""):
    lcd.clear()
    time.sleep_ms(5)
    lcd.putstr(row0)
    if row1:
        lcd.move_to(0, 1)
        lcd.putstr(row1)

def dec_to_bcd(val):
    return ((val // 10) << 4) + (val % 10)

def bcd_to_dec(val):
    return ((val >> 4) * 10) + (val & 0x0F)

def get_rtc_raw():
    data = rtc_i2c.readfrom_mem(0x68, 0x00, 7)
    sec = bcd_to_dec(data[0] & 0x7F)
    minute = bcd_to_dec(data[1])
    hour = bcd_to_dec(data[2] & 0x3F)
    weekday = bcd_to_dec(data[3])
    day = bcd_to_dec(data[4])
    month = bcd_to_dec(data[5] & 0x1F)
    year = bcd_to_dec(data[6]) + 2000
    return year, month, day, weekday, hour, minute, sec

def get_rtc_time():
    year, month, day, _, hour, minute, sec = get_rtc_raw()
    return f"{year:04d}-{month:02d}-{day:02d}", f"{hour:02d}:{minute:02d}:{sec:02d}"

def adjust_rtc_seconds(delta_sec):
    # Read current RTC time, convert to epoch seconds, add delta, and write back
    year, month, day, weekday, hour, minute, sec = get_rtc_raw()
    # MicroPython mktime tuple: (year, month, mday, hour, minute, second, weekday 0-6, yearday)
    epoch = time.mktime((year, month, day, hour, minute, sec, weekday - 1, 0))
    new_t = time.localtime(epoch + delta_sec)
    
    ny, nm, nd, nh, nmin, nsec, nwd, _ = new_t
    rtc_bytes = bytearray([
        dec_to_bcd(nsec),
        dec_to_bcd(nmin),
        dec_to_bcd(nh),
        dec_to_bcd(nwd + 1),
        dec_to_bcd(nd),
        dec_to_bcd(nm),
        dec_to_bcd(ny - 2000)
    ])
    rtc_i2c.writeto_mem(0x68, 0x00, rtc_bytes)

def calibrate_seconds_in_thonny():
    lcd_write("Calibrating Time", "Check Thonny...")
    print("\n--- RTC Seconds Calibration ---")
    print("Enter offset in seconds (e.g. -1 if 1s behind, 1 if 1s ahead), or 'q' to finish:")
    
    while True:
        d_str, t_str = get_rtc_time()
        ans = input(f"Current RTC [{d_str} {t_str}] -> Adjust sec (or 'q'): ").strip().lower()
        
        if ans == "q":
            print("Calibration complete!\n")
            break
        try:
            offset = int(ans)
            # If clock is behind (-1), add +1s to catch it up; if ahead (+1), subtract 1s
            adjust_rtc_seconds(-offset)
            new_d, new_t = get_rtc_time()
            print(f"Updated RTC time to: {new_d} {new_t}")
        except ValueError:
            print("Invalid input. Type a whole number (like -1 or 2) or 'q'.")

def sync_if_online():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    lcd_write("Checking WiFi...")
    
    steps = 16
    sub_checks = int((WIFI_TIMEOUT_SEC / steps) / 0.1)
    skipped_by_user = False
    
    for i in range(steps):
        if wlan.isconnected():
            lcd.move_to(0, 1)
            lcd.putstr("#" * 16)
            break
            
        lcd.move_to(0, 1)
        lcd.putstr("#" * (i + 1) + "." * (steps - i - 1))
        
        for _ in range(sub_checks):
            if rp2.bootsel_button() == 1:
                skipped_by_user = True
                break
            if wlan.isconnected():
                break
            time.sleep(0.1)
            
        if skipped_by_user or wlan.isconnected():
            if wlan.isconnected():
                lcd.move_to(0, 1)
                lcd.putstr("#" * 16)
            break

    if skipped_by_user:
        wlan.active(False)
        lcd_write("WiFi Skipped!", "Offline RTC Mode")
        time.sleep(2)
        return
        
    if wlan.isconnected():
        lcd_write("WiFi Connected!")
        time.sleep(2)
        try:
            url = "URL_FOR_TIME_ZONE"
            headers = {"User-Agent": "Mozilla/5.0 (RaspberryPiPicoW)"}
            res = urequests.get(url, headers=headers)
            data = res.json()
            
            
            lt = data["local_time"]
            date_part, time_part = lt.split("T")
            year, month, day = [int(x) for x in date_part.split("-")]
            hms = time_part.split(".")[0]
            hour, minute, second = [int(x) for x in hms.split(":")]
            
            days = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
                    "Friday": 5, "Saturday": 6, "Sunday": 7}
            ds_weekday = days.get(data["day_of_week"], 1)
            
            wlan.active(False)
            time.sleep(0.2)
            
            rtc_bytes = bytearray([
                dec_to_bcd(second),
                dec_to_bcd(minute),
                dec_to_bcd(hour),
                dec_to_bcd(ds_weekday),
                dec_to_bcd(day),
                dec_to_bcd(month),
                dec_to_bcd(year - 2000)
            ])
            rtc_i2c.writeto_mem(0x68, 0x00, rtc_bytes)
            
            lcd_write("WiFi Connected!", "HTTPS Time Sync!")
            print(f"Synced: {year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
            time.sleep(1)
            
            # Ask in Thonny Shell to fine-tune seconds until 'q' is typed
            calibrate_seconds_in_thonny()
            
        except Exception as e:
            wlan.active(False)
            lcd_write("WiFi Connected!", "API Fail->UseRTC")
            print("HTTPS Error:", e)
            time.sleep(2)
    else:
        wlan.active(False)
        lcd_write("Offline Mode", "Using RTC Clock")
        time.sleep(2)

# --- Startup ---
sync_if_online()
lcd.clear()
time.sleep_ms(5)

last_dht_ms = -2000
last_log_ms = 0
temp_c = 0.0
hum = 0.0
use_fahrenheit = False
prev_bootsel = 0

def update_temp_display():
    if use_fahrenheit:
        temp_f = (temp_c * 9 / 5) + 32
        lcd.move_to(0, 1)
        lcd.putstr(f"T:{temp_f:.1f}F H:{hum:.0f}%   ")
    else:
        lcd.move_to(0, 1)
        lcd.putstr(f"T:{temp_c:.1f}C H:{hum:.0f}%   ")

# --- Main Loop (Ticks every 1 second) ---
while True:
    loop_start = time.ticks_ms()
    
    try:
        # 1. Read RTC & update Top Row every 1 second
        date_str, time_str = get_rtc_time()
        lcd.move_to(0, 0)
        lcd.putstr(f"{date_str[5:]} {time_str}  ")
        
        # 2. Read DHT22 every 2 seconds
        if time.ticks_diff(loop_start, last_dht_ms) >= 2000:
            sensor.measure()
            temp_c = sensor.temperature()
            hum = sensor.humidity()
            last_dht_ms = loop_start
            update_temp_display()
            
        # 3. Log to CSV once every 60 seconds (logs both °C and °F)
        if time.ticks_diff(loop_start, last_log_ms) >= CSV_LOG_INTERVAL_SEC * 1000:
            last_log_ms = loop_start
            temp_f = (temp_c * 9 / 5) + 32
            line = f"{date_str} {time_str},{temp_c:.1f},{temp_f:.1f},{hum:.1f}\n"
            print("Logged:", line.strip())
            with open("data_log.csv", "a") as f:
                f.write(line)
                
    except Exception as e:
        lcd_write("Err: " + str(e)[:11])
        print("Loop Error:", e)
        
    # Poll BOOTSEL every 50 ms during the remainder of the 1-second wait for instant toggle
    while time.ticks_diff(time.ticks_ms(), loop_start) < 1000:
        btn = rp2.bootsel_button()
        if btn == 1 and prev_bootsel == 0:
            use_fahrenheit = not use_fahrenheit
            update_temp_display()
        prev_bootsel = btn
        time.sleep_ms(50)

