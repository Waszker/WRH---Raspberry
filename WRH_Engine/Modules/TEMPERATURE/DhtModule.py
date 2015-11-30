#!/usr/bin/env python

import sys
# import Adafruit_DHT

def main(argv):
    # check arguments
    if len(argv) != 9:
        raise ValueError("Bad parameters")
        return

    compressed_argv = argv # list for cmd parameters without semi-colons

    try:
        semi_col = ';'
        while semi_col in compressed_argv: # remove all semi-colons
            compressed_argv.remove(semi_col); 
    except ValueError as e:
        raise ValueError(e);
    
    # get gpio number
    gpio = int(compressed_argv[2])
    print(gpio) # for test only

    # humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, gpio)
    # print "Temp={0:0.1f}*C Humidity={1:0.1f}%".format(temperature, humidity)

if __name__ == "__main__":
   main(sys.argv[1:])