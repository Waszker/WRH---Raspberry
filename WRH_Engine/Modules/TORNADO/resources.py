#!/bin/python2
import Adafruit_DHT
import urllib2

DHT_DATA = "/tmp/.dht_data"

def get_cpu_temp():
    tempFile = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp)/1000

def get_dht_readings(gpio_pin):
    return Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, gpio_pin)

def getuptime():
    uptime_string = ""

    with open('/proc/uptime', 'r') as f:
        total_seconds = float(f.readline().split()[0])

        # Helper vars:
        MINUTE  = 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        # Get the days, hours, etc:
        days    = int( total_seconds / DAY )
        hours   = int( ( total_seconds % DAY ) / HOUR )
        minutes = int( ( total_seconds % HOUR ) / MINUTE )
        seconds = int( total_seconds % MINUTE )

        # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
        if days > 0:
            uptime_string += str(days) + " " + (days == 1 and "day" or "days" ) + ", "
        if len(uptime_string) > 0 or hours > 0:
            uptime_string += str(hours) + " " + (hours == 1 and "hour" or "hours" ) + ", "
        if len(uptime_string) > 0 or minutes > 0:
            uptime_string += str(minutes) + " " + (minutes == 1 and "minute" or "minutes" ) + ", "
        uptime_string += str(seconds) + " " + (seconds == 1 and "second" or "seconds" )
    return uptime_string

def getsystemstats():
    hum = temp = ""

    with open(DHT_DATA, "r", 0) as f:
        temp = f.readline()
        hum = f.readline()

    stat_string = ""
    stat_string += "Uptime: " + getuptime() + "<br />"
    stat_string += "CPU temp: " + str(round(get_cpu_temp(), 1)) + "*C <br />"
    stat_string += "Temp: " + temp + "*C <br/>"
    stat_string += "Humidity: " + hum + "% <br/>"

    return stat_string

def getelectricalsocketstate():
    url = "http://192.168.0.100/cgi-bin/relay.cgi?state"
    request = urllib2.Request(url)
    return urllib2.urlopen(request).read()

def setelectrcalsocketstate(state):
    url = "http://192.168.0.100/cgi-bin/relay.cgi?" + state
    request = urllib2.Request(url)
    return urllib2.urlopen(request).read()
