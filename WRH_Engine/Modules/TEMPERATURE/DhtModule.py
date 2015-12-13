#!/usr/bin/env python

import sys
import signal
import Adafruit_DHT
from WRH_Engine.Configuration import configuration as C
from WRH_Engine.WebApiLibrary import WebApiClient as W
from WRH_Engine.Utils import utils as U
from WRH_Engine.module.module import Module


def _send_measurement_to_scenario_manager(measurement):
	print('wysylam measurement do scenario manager')
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 2000))
	clientsocket.send("1234") # moduleId
	clientsocket.recv(4096)
	clientsocket.send(measurement)


global dev, module


def main(argv):
    # check arguments
    if len(argv) != 2:
        raise ValueError("Bad parameters")

    # pull out dev and module data
    dev = C.get_device_entry_data(argv[1])
    module = C.get_module_entry_data(argv[2])


def _get_measurement(gpio):
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, gpio)
    return "{0:0.1f};{1:0.1f}".format(temperature, humidity)


def _signal_handler():
    sys.exit(0)


def _sigalrm_handler():
    timestamp = U.generate_proper_date_format()
    measurement = _get_measurement(module.gpio)
    _send_measurement_to_scenario_manager(measurement)
    if not W.add_measurement(dev[0], dev[1], module.id, timestamp, measurement, "")[0] == Response.STATUS_OK:
        U.write_measurement(module.type, module.id, measurement)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGALRM, _sigalrm_handler)
    signal.alarm(300)
    main(sys.argv[1:])
