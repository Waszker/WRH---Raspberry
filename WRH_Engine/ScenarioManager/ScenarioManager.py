#!/usr/bin/python2.7
from ..WebApiLibrary import WebApiClient as webapi
from WRH_Engine.Configuration import configuration as config
import WRH_Engine.Modules.CAMERA.camera as camera
import WRH_Engine.Utils.utils as utils
import sys
import json
import threading
import time
import socket
import urllib2
import signal
import re
from datetime import datetime, timedelta

# SCENARIO MANAGER
# Module responsible for managing Scenarios assigned to this Device
# This Module is started by the Overlord
# Scenario Manager periodically checks for updated Scenarios...
# ...and communicated with other running Modules, to see if any of their most recent Measurements...
# ...matches any of the Scenarios...
# ...if yes, then Scenario is executed, and Execution object uploaded


# region OPTIONS

CONFIGURATION_FILE = '.wrh.config'
socket_port = 2000

# endregion ~OPTIONS


# region GLOBAL VARIABLES

device_id = ''
device_token = ''
scenarios = []
measurements = dict() # // pairs, moduleId and Value
doneScenarios = dict() # // pairs, scenarioId - number of times the scenario was executed
lock = threading.Lock()
event = threading.Event() # triggered when scenarios changed OR some measurement meet some scenarios' conditions
available_modules = []

# endregion ~GLOBAL VARIABLES


# region STARTUP AND CONFIGURATION METHODS

def signal_handler(signal, frame):
    print 'Scenario Manager shutting down...'
    sys.exit(0)


# read deviceId, deviceToken and Modules from configuration file
def _read_available_modules():
    global available_modules
    global device_id
    global device_token
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, available_modules) = config.parse_configuration_file(f)
    device_id = system_info[0]
    device_token = system_info[1]


# TODO: is it used? if so, is it working?
# get streaming address, port, login and password encoded into one field - streamingaddress
def _extract_info_from_streamingaddress(streaming_address):
    # TODO zrobic to (Piotrek zrobi)
    # we have encoded into camera module's streamingaddress four things:
    address = "" # actual streaming address
    port = ""
    login = "login"
    password = "password" # login and password are needed to make a snapshot
    return (address, port, login, password)


# endregion ~STARTUP AND CONFIGURATION METHODS


# region COMMUNICATION WITH OTHER RUNNING MODULES


# wait for incoming connections, and accept them. Accepted connection are then handled by _socket_communicate()
def _socket_accept():
    global socket_port
    print('accept_socket_messages() start')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', socket_port))
    print('_socket_accept bind: ' + str('localhost') + ' ' + str(socket_port))
    server_socket.listen(5)
    while 1:
        (client_socket, address) = server_socket.accept()
        t = threading.Thread(target=_socket_communicate, args=(client_socket,))
        t.daemon = True
        t.start()

    print('accept_socket_messages() end')


# communicate with client (some Module in our case). Read measurement from it
def _socket_communicate(clientsocket):
    print('socket_communicate() start')
    global measurements
    # read measurement, update global measurements array
    module_id = clientsocket.recv(4096)
    print('przyszedl measurement od modulu o id: ' + str(module_id))
    clientsocket.send('ACK')
    value = clientsocket.recv(4096)
    print('przyszla wartosc rowna: ' + str(value))
    lock.acquire()
    measurements[str(module_id)] = value
    scenarios_to_execute = _get_scenarios_to_execute()
    lock.release()
    if len(scenarios_to_execute) > 0:
        event.set()
    print('socket_communicate() end')

# endregion ~COMMUNICATION WITH OTHER RUNNING MODULES


# region UPDATE SCENARIOS

# periodically check with WebApi if scenarios has changed. If yes, then trigger event.
def _scenarios_changed():
    print('scenarios_changed() start')
    while True:
        time.sleep(5) #TODO magic number
        (status_code, result_content) = webapi.scenarios_changed(device_id, device_token)
        # check if scenarios changed, signal main() if yes (signal via Event)
        # event.set()
        # then exit, will be started again by main()
        if status_code == 200 : #TODO use enum
            print('SCENARIOS HAS CHANGED!')
            event.set()
            break
    print('scenarios_changed() end')


# download Scenarios from WebApi
def _get_scenarios():
    # lock is acquired
    global scenarios
    print('getting scenarios')
    (status_code, result_content) = webapi.get_scenarios(device_id, device_token)
    if status_code != 200: # TODO magic number
        print('_get_scenarios() status_code=' + str(status_code))
        scenarios = []
        return
    result_object = json.loads(result_content)
    scenarios = result_object


# endregion ~UPDATE SCENARIOS


# region DETERMINE SCENARIOS TO BE EXECUTED


# from list of scenarios, get scenarios that are active (startDate <= DateTime.Now <= endDate)
def _get_active_scenarios_by_date(scenarios):
    now = datetime.utcnow()
    result = []
    # TODO: not implemented
    for scen in scenarios:
        active = True

        if active:
            result.append(scen)

    return result


# from list of scenarios, exclude scenarios with the lowest priority within scenarios with the same action module
def _get_active_scenarios_by_priority(scenarios):
    result = []
    # TODO not implemented
    for scen in scenarios:
        result.append(scen)

    return result


# get a list of Ids of scenarios which are to be executed
# list is prepared based on: measurements, doneScenarios, and current time
def _get_scenarios_to_execute():
    global scenarios
    result = []
    # active_date_scenarios = _get_active_scenarios_by_date(scenarios)
    # active_scenarios = _get_active_scenarios_by_priority(active_date_scenarios)
    active_scenarios = scenarios

    for scen in active_scenarios:
        if not str(scen["ConditionModuleId"]) in measurements:
            continue # there is no Measurement from Module with this Id (yet)
        value = measurements[str(scen["ConditionModuleId"])]
        print('>> sprawdzam scenariusze, ostatnia wartosc dla modulu o id: ' + str(scen["ConditionModuleId"]) + ' wynosi: ' + str(value))

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
            print('Condition scenariusza - czy wykryto ruch?')
            if int(value) > 0:
                print('value=' + str(value)+ '> 0, czyli tak')
                conditionMet = True
        if conditionMet:
            result.append(scen)

    return result

# endregion ~DETERMINE SCENARIOS TO BE EXECUTED


# region SCENARIO EXECUTION

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
    for mod in available_modules:
        if str(mod.id) == str(actionmoduleid):
            module = mod
            break
    if not module:
        print(" >> nie znalazlem action modulu o id: " + str(mod.id))
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
        print('probuje togglowac gniazdko pod adresem: ' + address)
        # TODO try catch
        urllib2.urlopen(address).read()
        return True
    if action == '4':
        # TODO take snapshot
        print('taking snapshot, port=' + str(module.address) +' login:password')
        content = camera.get_camera_snapshot(str(module.address), "login", "password")
        print('snapshot taken, content = ')
        print(str(content))
        print('TODO: wyslac snapshot jako measurement')
        return True
    return False

# endregion ~SCENARIO EXECUTION

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
        # if t_scenarios_changed finished then I know that scenarios changed. Download new scenarios
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

    print('Scenario Manager started')
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

    print('Scenario Manager ended')


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    main()
