#!/usr/bin/python2.7

import WRH_Engine.Modules.MOVEMENT.MOVEMENT
from WRH_Engine.WebApiLibrary import WebApiClient as W
import json
import threading
import time
import socket
# // import WebApiLibrary

#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '9'
devicetoken = 'dea763a0-5c0c-4555-bcc6-9f0cc1dcf030'
moduleid = '14'
temp_cnt = 0
sleep_time = 10

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
	return 1
	global temp_cnt
	temp_cnt = temp_cnt + 1
	if temp_cnt % 5 == 0:
		return 1
	return 0

def main():
	print('main() start')
	
	while True:		
		measurement = _read_movement()
		_save_to_card(measurement)
		_sync_with_api(measurement)
		_send_measurement_to_scenario_manager(measurement)
		#time.sleep(sleep_time)
		break
	print('main() end')

if __name__ == "__main__":
    main()
