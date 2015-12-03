#!/usr/bin/python2.7
from ..WebApiLibrary import WebApiClient as W
import json
import threading
import time
import socket

#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '9'
devicetoken = 'dea763a0-5c0c-4555-bcc6-9f0cc1dcf030'
socket_port = 2000
scenarios = []
measurements = [] # // pairs, moduleId and Value
doneScenaros = [] # // pairs, scenarioId - number of times the scenario was executed
rules = [] # // rules, when to trigger event. (when measurement from specified module is .. )
lock = threading.Lock()
event = threading.Event() #triggered when scenarios changed OR slme measurement meets rule

def _get_scenarios():
	global scenarios
	print('gettingscenarios')
	(status_code, result_content) = W.get_scenarios(deviceid, devicetoken)
	result_object = json.loads(result_content)
	scenarios = result_object

def _socket_communicate(clientsocket):
	print('socket_communicate() start')
	# read measurement, update global measurements array
	print('socket_communicate() end')


def _socket_accept():
	print('accept_socket_messages() start')
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind((socket.gethostname(), socket_port))
	serversocket.listen(5)
	while 1:
		(clientsocket, address) = serversocket.accept()
		t = threading.Thread(target=_socket_communicate, args=(clientsocket))
		t.daemon = True
		t.start()

	print('accept_socket_messages() end')

def _scenarios_changed():
	print('scenarios_changed() start')
	while True:
		time.sleep(10)
		(status_code, result_content) = W.scenarios_changed(deviceid, devicetoken)
		#check if scenarios changed, signal main() if yes (signal via Event)
		#event.set()
		#then exit, will be started again by main()
		if status_code == W.Response.STATUS_OK :
			event.set()
			break
	print('scenarios_changed() end')


def _try_execute_scenarios():
	global measurements
	# // check if any scenarios is triggered, if yes then execute it

def _generate_rules():
	# // update global rules
    global rules

def main():
	print('main() start')
	_get_scenarios()
	print str(len(scenarios))
	t_accept = threading.Thread(target=_socket_accept)
	t_accept.daemon = True
	t_accept.start()



	while True:
		event.clear()
		t_scenarios_changed = threading.Thread(target=_scenarios_changed)
		t_scenarios_changed.daemon = True
		t_scenarios_changed.start()
		event.wait()
		lock.acquire()
		print('event triggered')
		time.sleep(1)
		#if t_scenarios_changed finished then I know that scenarios changed. Download new scenarios
		if not t_scenarios_changed.isAlive():
			t_scenarios_changed.join()
			_get_scenarios()
		else:
			print('event triggered by measurement meeting some rule')

		# check measurements, check if any scenario is triggered, execute
		_try_execute_scenarios()

		#generate rules based on scenarios
		_generate_rules()

		lock.release()

	print('main() end')

if __name__ == "__main__":
    main()
