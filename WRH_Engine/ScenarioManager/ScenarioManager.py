#!/usr/bin/python2.7
from ..WebApiLibrary import WebApiClient as webapi
from WRH_Engine.Configuration import configuration as config
import os
import json
import threading
import time
import socket
import urllib2
import signal

CONFIGURATION_FILE = '.wrh.config'
#dane rasberaka uzytkownika przem321@wp.pl
deviceid = '18'
devicetoken = '0d41ace1-fa6b-439c-ac02-cafae7c09a26'
socket_port = 2000
scenarios = []
measurements = dict() # // pairs, moduleId and Value
doneScenarios = dict() # // pairs, scenarioId - number of times the scenario was executed
rules = [] # // rules, when to trigger event. (when measurement from specified module is .. )
lock = threading.Lock()
event = threading.Event() #triggered when scenarios changed OR slme measurement meets rule
availablemodules = []

def signal_handler(signal, frame):
    print 'Scenario Manager SIGINT routine'
    os.exit(0)

def _read_available_modules():
	print('reading available modules')
	global availablemodules
	with open(CONFIGURATION_FILE, 'r') as f:
		(system_info, availablemodules) = config.parse_configuration_file(f)
	deviceid = system_info[0]
	devicetoken = system_info[1]

def _get_scenarios():
	global scenarios
	print('gettingscenarios')
	(status_code, result_content) = webapi.get_scenarios(deviceid, devicetoken)
	result_object = json.loads(result_content)
	scenarios = result_object




def _socket_communicate(clientsocket):
	print('socket_communicate() start')
	global measurements
	# read measurement, update global measurements array
	moduleid = clientsocket.recv(4096)
	print('przyszedl measurement od modulu o id: ' + str(moduleid))
	clientsocket.send('ACK')
	value = clientsocket.recv(4096)
	print('przyszla wartosc rowna: ' + str(value))
	matchrule = False
	lock.acquire()
	measurements[str(moduleid)] = value
	matchrule = _does_measurement_match_rule(moduleid, value)
	lock.release()
	if matchrule:
		print('rule spelniona, uruchamiam event')
		event.set()
	else:
		print('niespelnia zadnej')
	print('socket_communicate() end')


def _socket_accept():
	global socket_port
	print('accept_socket_messages() start')
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', socket_port))
	print('_socket_accept bind: ' + str('localhost') + ' ' + str(socket_port))
	serversocket.listen(5)
	while 1:
		(clientsocket, address) = serversocket.accept()
		t = threading.Thread(target=_socket_communicate, args=(clientsocket,))
		t.daemon = True
		t.start()

	print('accept_socket_messages() end')

def _scenarios_changed():
	print('scenarios_changed() start')
	while True:
		time.sleep(1)
		(status_code, result_content) = webapi.scenarios_changed(deviceid, devicetoken)
		#check if scenarios changed, signal main() if yes (signal via Event)
		#event.set()
		#then exit, will be started again by main()
		print('\n\n')
		print('sc changed code: ' + str(status_code))
		print('\n\n')
		if status_code == 200 :
			print('SCENARIOS HAS CHANGED!')
			event.set()
			break
	print('scenarios_changed() end')


def _try_execute_scenarios():
	global measurements
	global doneScenarios
	global scenarios
	print('try_execute_scenarios')
	# // TODO: uwzglednienie priorytetow, oraz Recurring. (doneScenarios)
	# // check if any scenarios is triggered, if yes then execute it
	for scen in scenarios:
		if not scen["Name"]:
			continue
		print(str(scen["Name"]))
		# // datetime.now between starttime and endtime?
		if not str(scen["ConditionModuleId"]) in measurements:
			print('nie ma (jeszcze) pomiaru do takiego confitionmoduleid')
			continue #// pomiaru takiego nie ma
		value = measurements[str(scen["ConditionModuleId"])]
		print(str(scen["Condition"]))
		if str(scen["Condition"]) == '5': # // czy wykryto ruch?
			if str(value) == '1':

				if not str(scen["Id"]) in doneScenarios:
					doneScenarios[str(scen["Id"])] = 0
					print('zeruje donescenarios')
				done = doneScenarios[str(scen["Id"])]
				if done>0 and int(scen["Recurring"])==0:
					print('scenariusz juz byl wykonany a nie jest recurring.')
					continue # // scenariusz byl juz wykonany
				print('_execute_scenario()')
				result = _execute_scenario(str(scen["ActionModuleId"]), str(scen["Action"]))
				if result == True:
					doneScenarios[str(scen["Id"])] = done + 1
				else:
					print('nie udalo sie wykonac scenariusza')


	return

def _execute_scenario(actionmoduleid, action):
	print('wykonuje scenariusz')
	module = []
	for mod in availablemodules:
		if str(mod.id) == actionmoduleid:
			module = mod
			break
	if not module:
		return False

	if action == '3':
		print('akcja typu toggle gniazdko')
		address = module.address + '?toggle'
		urllib2.urlopen(address).read()


	return True


def _generate_rules():
	# // update global rules
    global rules
    global scenarios
    rules = []
    for scen in scenarios:
		if not scen["Name"]:
			continue
		print('rozwazam scenariusz ' + str(scen["Name"]))
		rule = (scen["ConditionModuleId"], scen["Condition"], scen["ValueInt"])
		print('Dodaje rule nastepujaca: ' + str(rule[0]) + ' ' + str(rule[1]) + ' ' + str(rule[2]))
		rules.append(rule)

def _does_measurement_match_rule(moduleid, value):
	print('czy measurement: ' + str(moduleid) + ' \n' + str(value) + '\n spelnia jakas rule?')
	# // lock jest nasz
	for rule in rules:
		if not str(rule[0]) == moduleid:
			continue

		rulecondition = rule[1]
		rulevalue = rule[1]

		if rulecondition == 5:
			# // motion detected
			if value == '1':
				return True
		#if rulecondition == 4: i tak dalej
	#~for
	return False #zadne rule nie spelnione
	
def _main_event_waiting():
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

def main_routine():

	print('main() start SCENARIOMANAGER')
	_read_available_modules()

	_get_scenarios()
	print str(len(scenarios))
	_generate_rules()

	t_accept = threading.Thread(target=_socket_accept)
	t_accept.daemon = True
	t_accept.start()

	t_event = threading.Thread(target=_main_event_waiting)
	t_event.daemon = True
	t_event.start()
	
	signal.pause()

	print('main() end')

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main_routine()
