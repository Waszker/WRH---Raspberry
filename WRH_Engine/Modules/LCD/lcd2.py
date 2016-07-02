#!/bin/python2
import time
import RPi.GPIO as GPIO
from resources import get_dht_readings, _get_cpu_temp, DHT_DATA

# Zuordnung der GPIO Pins (ggf. anpassen)
DISPLAY_RS = 31
DISPLAY_E  = 29
DISPLAY_DATA4 = 35
DISPLAY_DATA5 = 11
DISPLAY_DATA6 = 40
DISPLAY_DATA7 = 15
DHT_GPIO = 4

DISPLAY_WIDTH = 16 	# Zeichen je Zeile
DISPLAY_LINE_1 = 0x80 	# Adresse der ersten Display Zeile
DISPLAY_LINE_2 = 0xC0 	# Adresse der zweiten Display Zeile
DISPLAY_CHR = True
DISPLAY_CMD = False
E_PULSE = 0.00005
E_DELAY = 0.00005


def get_cpu_speed():
        tempFile = open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
        cpu_speed = tempFile.read()
        tempFile.close()
        return float(cpu_speed)/1000


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DISPLAY_E, GPIO.OUT)
    GPIO.setup(DISPLAY_RS, GPIO.OUT)
    GPIO.setup(DISPLAY_DATA4, GPIO.OUT)
    GPIO.setup(DISPLAY_DATA5, GPIO.OUT)
    GPIO.setup(DISPLAY_DATA6, GPIO.OUT)
    GPIO.setup(DISPLAY_DATA7, GPIO.OUT)

    display_init()

    while True:
        humidity, temperature = get_dht_readings(DHT_GPIO)
        lcd_byte(DISPLAY_LINE_1, DISPLAY_CMD)
        lcd_string("CPU Temp: " + str(round(_get_cpu_temp(), 1)) + "*C")
        lcd_byte(DISPLAY_LINE_2, DISPLAY_CMD)
        if temperature is not None and humidity is not None:
            lcd_string('T={0:0.1f}*C H={1:0.1f}%'.format(temperature, humidity))
            with open(DHT_DATA, "w", 0) as f:
                f.write(str(round(temperature, 1)) + "\n" + str(round(humidity, 1)))
        time.sleep(10)

    GPIO.cleanup()

def display_init():
	lcd_byte(0x33,DISPLAY_CMD)
	lcd_byte(0x32,DISPLAY_CMD)
	lcd_byte(0x28,DISPLAY_CMD)
	lcd_byte(0x0C,DISPLAY_CMD)
	lcd_byte(0x06,DISPLAY_CMD)
	lcd_byte(0x01,DISPLAY_CMD)

def lcd_string(message):
	message = message.ljust(DISPLAY_WIDTH," ")
	for i in range(DISPLAY_WIDTH):
	  lcd_byte(ord(message[i]),DISPLAY_CHR)

def lcd_byte(bits, mode):
	GPIO.output(DISPLAY_RS, mode)
	GPIO.output(DISPLAY_DATA4, False)
	GPIO.output(DISPLAY_DATA5, False)
	GPIO.output(DISPLAY_DATA6, False)
	GPIO.output(DISPLAY_DATA7, False)
	if bits&0x10==0x10:
	  GPIO.output(DISPLAY_DATA4, True)
	if bits&0x20==0x20:
	  GPIO.output(DISPLAY_DATA5, True)
	if bits&0x40==0x40:
	  GPIO.output(DISPLAY_DATA6, True)
	if bits&0x80==0x80:
	  GPIO.output(DISPLAY_DATA7, True)
	time.sleep(E_DELAY)
	GPIO.output(DISPLAY_E, True)
	time.sleep(E_PULSE)
	GPIO.output(DISPLAY_E, False)
	time.sleep(E_DELAY)
	GPIO.output(DISPLAY_DATA4, False)
	GPIO.output(DISPLAY_DATA5, False)
	GPIO.output(DISPLAY_DATA6, False)
	GPIO.output(DISPLAY_DATA7, False)
	if bits&0x01==0x01:
	  GPIO.output(DISPLAY_DATA4, True)
	if bits&0x02==0x02:
	  GPIO.output(DISPLAY_DATA5, True)
	if bits&0x04==0x04:
	  GPIO.output(DISPLAY_DATA6, True)
	if bits&0x08==0x08:
	  GPIO.output(DISPLAY_DATA7, True)
	time.sleep(E_DELAY)
	GPIO.output(DISPLAY_E, True)
	time.sleep(E_PULSE)
	GPIO.output(DISPLAY_E, False)
	time.sleep(E_DELAY)

if __name__ == '__main__':
	main()

