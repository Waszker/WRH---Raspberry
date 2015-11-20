#!/usr/bin/python2.7
from ..WebApiLibrary import WebApiClient as W
import json
import threading
import time
import socket

#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '113'
devicetoken = '33f1308d-f669-4eee-85fb-cacff7b2745c'
socket_port = 2000
scenarios = []
measurements = []
rules = []
lock = threading.Lock()
event = threading.Event() #triggered when scenarios changed OR measurement meets rule

def _get_scenarios():
	global scenarios
	(status_code, result_content) = W.get_scenarios(deviceid, devicetoken)
	#print('status_code = ' + str(status_code))
	result_object = json.loads(result_content)
	scenarios = result_object

def _socket_communicate(clientsocket):
	print('socket_communicate() start')
	
	print('socket_communicate() end')

	
def _socket_accept():
	print('accept_socket_messages() start')
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind((socket.gethostname(), socket_port))
	serversocket.listen(5)
	while 1:
		(clientsocket, address) = serversocket.accept()
		t = threading.Thread(target=_socket_communicate, args=(clientsocket))
		t.start()
		
	print('accept_socket_messages() end')

def _scenarios_changed():
	print('scenarios_changed() start')
	while 1
		time.sleep(10)
		#check if scenarios changed, signal main() if yes (signal via Event)
		#event.set()
		#then exit, will be started again by main()
	print('scenarios_changed() end')
	
def main():
	print('main() start')
	_get_scenarios()
	print str(len(scenarios))
	t_accept = threading.Thread(target=_socket_accept)
	t_accept.daemon = True
	t_accept.start()
	
	t_scenarios_changed = threading.Thread(target=_scenarios_changed)
	t_scenarios_changed.daemon = True
	t_scenarios_changed.start()
	
	
	print('main() end')

if __name__ == "__main__":
    main()
