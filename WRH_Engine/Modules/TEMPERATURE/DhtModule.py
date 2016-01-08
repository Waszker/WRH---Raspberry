#!/usr/bin/env python

import socket
import time
import sys
import signal
import Adafruit_DHT
from WRH_Engine.Configuration import configuration as C
from WRH_Engine.Utils import utils as U


def _send_measurement_to_scenario_manager(measurement):
	print('wysylam measurement do scenario manager')
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 2000))
	clientsocket.send("1234") # moduleId
	clientsocket.recv(4096)
	clientsocket.send(measurement)


dev = ''
module = ''


def main(argv):
    global module
    global dev
    # check arguments
    if len(argv) != 2:
        raise ValueError("Bad parameters")

    # pull out dev and module data
    dev = C.get_device_entry_data(argv[0])
    module = C.get_module_entry_data(argv[1])

    while True:
		time.sleep(5 * 60)
		measurement = _get_measurement(module.gpio)
		U.manage_measurement(dev[0],  dev[1], module.id,  module.type, measurement, "")

def _get_measurement(gpio):
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, gpio)
    return "{0:0.1f};{1:0.1f}".format(float(temperature), float(humidity))


def _signal_handler():
    sys.exit(0)


def _sigalrm_handler(signal, frame):
    measurement = _get_measurement(module.gpio)
    U.manage_measurement(dev[0],  dev[1], module.id,  module.type, measurement, "")


if __name__ == "__main__":
    print 'Dht: Started'
    signal.signal(signal.SIGINT, _signal_handler)
    #signal.signal(signal.SIGALRM, _sigalrm_handler)
    # signal.alarm(3)
    main(sys.argv[1:])
