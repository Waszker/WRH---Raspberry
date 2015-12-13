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
from datetime import datetime, timedelta

verbose = False # should I print comments what is happening?
CONFIGURATION_FILE = '.wrh.config'

deviceid = ''
devicetoken = ''
socket_port = 2000
scenarios = []
measurements = dict() # // pairs, moduleId and Value
doneScenarios = dict() # // pairs, scenarioId - number of times the scenario was executed
lock = threading.Lock()
event = threading.Event() #triggered when scenarios changed OR some measurement meet some scenarios' conditions
availablemodules = []


# get streaming address, port, login and password encoded into one field - streamingaddress
def _extract_info_from_streamingaddress(streaming_address):
	# TODO zrobic to
	# we have encoded into camera module's streamingaddress four things:
	address = "" # actual streaming address
	port = ""
	login = ""
	password = "" # login and password are needed to make a snapshot
	return (address, port, login, password)


def signal_handler(signal, frame):
    print 'Scenario Manager SIGINT routine'
    os.exit(0)
    
   
# read deviceId, deviceToken and Modules from configuration file
def _read_available_modules():
	print('reading available modules')
	global availablemodules
	with open(CONFIGURATION_FILE, 'r') as f:
		(system_info, availablemodules) = config.parse_configuration_file(f)
	deviceid = system_info[0]
	devicetoken = system_info[1]

# download Scenarios from WebApi
def _get_scenarios():
	# lock is acquired
	global scenarios
	print('gettingscenarios')
	(status_code, result_content) = webapi.get_scenarios(deviceid, devicetoken)
	result_object = json.loads(result_content)
	scenarios = result_object
	print('\n')
	print('sciagnalem ' + str(len(scenarios)) + ' scenariuszy!')
	print('\n')

# communicate with client (some Module in our case). Read measurement from it
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
	scens = _get_scenarios_to_execute()
	lock.release()
	if len(scens) > 0:
		print('rule spelniona, uruchamiam event')
		event.set()
	else:
		print('niespelnia zadnej')
	print('socket_communicate() end')

# wait for incoming connections, and accept them. Accepted connection are then handled by _socket_communicate()
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

# periodically check with WebApi if scenarios has changed. If yes, then trigger event.
def _scenarios_changed():
	print('scenarios_changed() start')
	while True:
		time.sleep(5) #TODO magic number
		(status_code, result_content) = webapi.scenarios_changed(deviceid, devicetoken)
		#check if scenarios changed, signal main() if yes (signal via Event)
		#event.set()
		#then exit, will be started again by main()
		if status_code == 200 : #TODO use enum
			print('SCENARIOS HAS CHANGED!')
			event.set()
			break
	print('scenarios_changed() end')

# make a python datetime object based on our datetime string
# YYYY-MM-DDThh:mm:ss
# returns: (success, datetime)
def _convert_datetime_to_python(datetime):
	return (False, '')


# from list of scenarios, get scenarios that are active (startDate <= DateTime.Now <= endDate)
def _get_active_scenarios_by_date(scenarios):
	now = datetime.utcnow()
	result = []
	for scen in scenarios:
		active = True
		(successStart, datetimeStart) = _convert_datetime_to_python(scen["startDate"])
		(successEnd, datetimeEnd) = _convert_datetime_to_python(scen["startDate"])
		
		if successStart:
			if datetimeStart > now:
				active = False
		if successEnd:
			if datetimeEnd < now:
				active = False
		
		if active:
			result.append(scen)
	
	return result
	

# from list of scenarios, exclude scenarios with the lowest priority within scenarios with the same action module
def _get_active_scenarios_by_priority(scenarios):
	result = []
	#TODO
	for scen in scenarios: 
		result.append(scen)
	
	return result

# get a list of Ids of scenarios which are to be executed
# list is prepared based on: measurements, doneScenarios, and current time
def _get_scenarios_to_execute():
	global scenarios
	result = []
	active_date_scenarios = _get_active_scenarios_by_date(scenarios)
	active_scenarios = _get_active_scenarios_by_priority(active_date_scenarios)
    
	for scenario in active_scenarios:
		if not str(scen["ConditionModuleId"]) in measurements:
			continue # there is no Measurement from Module with this Id (yet)
		value = measurements[str(scen["ConditionModuleId"])]
		
		if not str(scen["Id"]) in doneScenarios:
			doneScenarios[str(scen["Id"])] = 0
		done = doneScenarios[str(scen["Id"])]
		if done>0 and int(scen["Recurring"])==0:
			continue # // scenario was already executed, and is not recurring
		
		conditionMet = False
		temp = ''
		wilg = ''
		if scen["Condition"] < 5:
			v = value.split(';')
			if len(v) != 2:
				continue # not properly encoded value.
			temp = v[0]
			wilg = v[1]

		if scen["Condition"] == 1: # Temperatura ponizej..
			if temp < scen["ValueInt"]:
				conditionMet = True
		if scen["Condition"] == 2: # Temperatura powyzej..
			if temp > scen["ValueInt"]:
				conditionMet = True
		if scen["Condition"] == 3: # Wilgotnosc ponizej..
			if wilg < scen["ValueInt"]:
				conditionMet = True
		if scen["Condition"] == 4: # Wilgotnosc powyzej..
			if wilg > scen["ValueInt"]:
				conditionMet = True
		if scen["Condition"] == 5: # Wykryto ruch
			if value > 0:
				conditionMet = True
		if conditionMet:
			result.append(scen["Id"])
	
	return result

# try to execute all scenarios taken from _get_scenarios_to_execute()
def _try_execute_scenarios():
	global measurements
	global doneScenarios
	global scenarios
	print('try_execute_scenarios, scenariuszy jest: ' + str(len(scenarios)))
	
	scensToExecute = _get_scenarios_to_execute()
	for scen in scensToExecute:
		print('trying to execute scenario ' + str(scen["Id"]))
		result = _execute_scenario(str(scen["ActionModuleId"]), str(scen["Action"]))
		if result == True:
			doneScenarios[str(scen["Id"])] = doneScenarios[str(scen["Id"])] + 1
		else:
			print('nie udalo sie wykonac scenariusza')
	return

# execute one scenario
def _execute_scenario(actionmoduleid, action):
	print('wykonuje scenariusz')
	module = []
	for mod in availablemodules:
		if str(mod.id) == actionmoduleid:
			module = mod
			break
	if not module:
		return False

	if action == '1':
		address = module.address + '?on'
		# TODO try catch
		urllib2.urlopen(address).read()
		return True
	if action == '2':
		address = module.address + '?off'
		# TODO try catch
		urllib2.urlopen(address).read()
		return True
	if action == '3':
		address = module.address + '?toggle'
		# TODO try catch
		urllib2.urlopen(address).read()
		return True
	if action == '4':
		# TODO take snapshot
		return True
	return False


# in loop wait for event to be triggered, try to execute scenarios
def _main_event_waiting():
	global measurements
	t_scenarios_changed = threading.Thread(target=_scenarios_changed)
	t_scenarios_changed.daemon = True
	t_scenarios_changed.start()
	while True:
		event.clear()
		event.wait()
		lock.acquire()
		print('event triggered')
		time.sleep(1)
		#if t_scenarios_changed finished then I know that scenarios changed. Download new scenarios
		if not t_scenarios_changed.isAlive():
			print('event triggered by scenarios changed')
			t_scenarios_changed.join()
			time.sleep(2)
			_get_scenarios()
			_try_execute_scenarios()
			t_scenarios_changed = threading.Thread(target=_scenarios_changed)
			t_scenarios_changed.daemon = True
			t_scenarios_changed.start()
		else:
			print('event triggered by measurement meeting some rule')
			_try_execute_scenarios()
		
		# clear measurements, zeby nie byl wykonany scenariusz znowu na podstawie tego samego measurement
		measurements = dict()
		lock.release()


def main():

	print('main() start SCENARIOMANAGER')
	_read_available_modules()

	_get_scenarios()
	print str(len(scenarios))

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
    
    main()
