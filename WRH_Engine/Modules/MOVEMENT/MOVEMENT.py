#!/usr/bin/python2.7

import WRH_Engine.Modules.MOVEMENT.MOVEMENT
from WRH_Engine.WebApiLibrary import WebApiClient as W
from WRH_Engine.Configuration import configuration as config
from WRH_Engine.Utils import utils as U
import json
import threading
import time
import socket
import RPi.GPIO as GPIO
import sys


#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = ''
devicetoken = ''
module = {}
PIR = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR, GPIO.IN)

temp_cnt = 0
sleep_time = 1
after_sleep_time = 5

def _read_arguments(argv):
	global deviceid
	global devicetoken
	global module
	dev = config.get_device_entry_data(argv[0])
	deviceid = dev[0]
	devicetoken = dev[1]
	module = config.get_module_entry_data(argv[1])


def _read_movement():
	result = 0
	try:
		if GPIO.input(PIR):
			result = 1
	except:
		result = 0
	return result


def main(argv):
	print('main() start MOVEMENT')
	_read_arguments(argv)
	time.sleep(4)
	
	while True:		
		measurement = _read_movement()
		U.manage_measurement(deviceid,  devicetoken, module.id,  module.type, measurement, '')

		if measurement == 0:
			time.sleep(sleep_time)
		else:
			time.sleep(after_sleep_time)		
		#break
	print('main() end')

if __name__ == "__main__":
    main(sys.argv[1:])
