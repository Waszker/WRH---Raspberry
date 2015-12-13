#!/usr/bin/python2.7

import WRH_Engine.Modules.MOVEMENT.MOVEMENT
from WRH_Engine.WebApiLibrary import WebApiClient as W
from WRH_Engine.Configuration import configuration as C
import json
import threading
import time
import socket
import RPi.GPIO as GPIO


#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '17'
devicetoken = '6967a427-0bb9-4085-bf2e-a3d966f4115c'
moduleid = '28'
PIR = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR, GPIO.IN)

temp_cnt = 0
sleep_time = 1
after_sleep_time = 5

def _send_measurement_to_scenario_manager(measurement):
	print('wysylam measurement do scenario manager')
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 2000))
	clientsocket.send(moduleid)
	clientsocket.recv(4096)
	clientsocket.send(str(measurement))

def _save_to_card(measurement):
	print('zapisuje na karte SD')

def _sync_with_api(measurement):
	print('wysylam ostatni measurement do API')
	print('sprawdzam czy starsze dane na karcie nie sa zsynchronizowane, i wysylam je jesli nie byly wyslane')

def _read_movement():
	if GPIO.input(PIR):
		return 1
	else:
		return 0


def main():
	print('main() start MOVEMENT')
	conf_line = sys.argv[1]
	moduleobject = C.get_module_entry_data(conf_line)
	time.sleep(10)
	
	while True:		
		measurement = _read_movement()
		_save_to_card(measurement)
		_sync_with_api(measurement)
		_send_measurement_to_scenario_manager(measurement)
		if measurement == 0:
			time.sleep(sleep_time)
		else:
			time.sleep(after_sleep_time)		
		#break
	print('main() end')

if __name__ == "__main__":
    main()
