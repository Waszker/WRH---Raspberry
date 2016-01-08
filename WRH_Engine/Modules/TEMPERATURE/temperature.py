# https://www.youtube.com/watch?v=Skr2uPZzviM&feature=youtu.be
import sys
import Adafruit_DHT

humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 25)
print 'Temp={0:0.1f}*C Humidity={1:0.1f}%'.format(temperature, humidity)
