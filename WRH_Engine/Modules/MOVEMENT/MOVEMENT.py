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


# OPTIONS

relaxationSleepTime = 3 # time to sleep after detecting movement

# ~OPTIONS

# GLOBAL VARIABLES

deviceid = ''
devicetoken = ''
module = {}
PIR = 4
movementDetectedValue = 1

# ~GLOBAL VARIABLES





def _read_arguments(argv):
	global deviceid
	global devicetoken
	global module
	global PIR
	dev = config.get_device_entry_data(argv[0])
	deviceid = dev[0]
	devicetoken = dev[1]
	module = config.get_module_entry_data(argv[1])
	PIR = int(module.gpio)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(PIR, GPIO.IN)


# OBSOLETE
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
		try:
			GPIO.wait_for_edge(PIR, GPIO.FALLING)
		except:
			print('MOVEMENT: Failure on GPIO.wait_for_edge(). Exiting...')
			sys.exit(0)
		
		U.manage_measurement(deviceid,  devicetoken, module.id,  module.type, movementDetectedValue, '')

		time.sleep(relaxationSleepTime)
	print('main() end')

if __name__ == "__main__":
    main(sys.argv[1:])
