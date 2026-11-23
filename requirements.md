# Requirements for weather_station
## Software
Install rpi_lcd_i2c_micropython to control lcd
### Installing rpi_lcd_i2c_micropython
1. Go to Thonny
2. Select Tools
3. Select 'Manage Packages' in the dropdown
4. Write 'rpi_lcd_i2c_micropython' in the search bar
5. Click 'search micropython-lib and PyPl'
6. click the package by 'Samarth Joneja'
7. Let the Download Complete
8. Done
### Change variables
#### Network
1. Get a 2.4GHz compatible network
2. Replace the python string variables with your wifi ssid and password
3. Done
#### TimeZone
1. Go to 'https://timeapi.io/swagger/index.html'
2. Go down to Timezones
3. Click the first option
4. Run the code
5. Look for your time zone
6. Copy it
7. Go to the next button
8. Paste the code in the place where it says timezone
9. Run the code
10. Get the URL under it
11. Paste it in the Micropython code at line 135 where it says 'URL_FOR_TIME_ZONE'
12. Done
## Hardware
- A Raspberry Pi Pico W
- DS3231 AT24C32 IIC RTC Module Clock Timer
- IIC/I2C/TWI LCD1602 Display
- JTAREA DHT22 Temperature and Humidity Sensor
