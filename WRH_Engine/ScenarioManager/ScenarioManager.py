#!/usr/bin/python2.7
from WRH_Engine.WebApiLibrary import Response
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
# ...and communicates with other running Modules, to see if any of their most recent Measurements...
# ...matches any of the Scenarios' Conditions...
# ...if yes, then Scenario is executed, and Execution object uploaded


# region OPTIONS


CONFIGURATION_FILE = '.wrh.config'
socket_port = 2000
scenarios_changed_wait_time = 5  # (seconds) how often check with WebApi if Scenarios has changed

# endregion ~OPTIONS


# region GLOBAL VARIABLES


device_id = ''
device_token = ''
scenarios = []
measurements = dict()  # // [moduleId] - [Value]
doneScenarios = dict()  # // [scenarioId] - [number of times the scenario was executed]
lock = threading.Lock()
event = threading.Event()  # triggered when scenarios changed OR some measurement meet some scenarios' conditions
available_modules = []
scenarios_changed = True


# endregion ~GLOBAL VARIABLES


# region STARTUP AND CONFIGURATION METHODS


def signal_handler(signal, frame):
    print 'Scenario Manager shutting down...'
    sys.exit(0)


# read deviceId, deviceToken and modules from configuration file
def _read_configuration_file():
    global available_modules
    global device_id
    global device_token
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, available_modules) = config.parse_configuration_file(f)
    device_id = system_info[0]
    device_token = system_info[1]


# endregion ~STARTUP AND CONFIGURATION METHODS


# region COMMUNICATION WITH OTHER RUNNING MODULES


# wait for incoming connections (from running Modules), and accept them.
# accepted connection are then handled by _socket_communicate()
def _socket_accept():
    global socket_port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', socket_port))
    server_socket.listen(5)
    while True:
        (client_socket, address) = server_socket.accept()
        t = threading.Thread(target=_socket_communicate, args=(client_socket,))
        t.daemon = True
        t.start()


# communicate with client (some Module in our case).
# receive its most recent measurement
# and update global measurements table
def _socket_communicate(client_socket):
    global measurements
    module_id = client_socket.recv(4096)
    client_socket.send('ACK')
    value = client_socket.recv(4096)

    lock.acquire()
    measurements[str(module_id)] = value
    scenarios_to_execute = _get_scenarios_to_execute()  # check what Scenarios (if any) are triggered
    lock.release()
    if len(scenarios_to_execute) > 0:  # if there is at least one Scenario triggered, then set the event
        event.set()


# endregion ~COMMUNICATION WITH OTHER RUNNING MODULES


# region UPDATE SCENARIOS


# periodically check with WebApi if scenarios has changed. If yes, then set the event.
def _scenarios_changed():
    global scenarios_changed
    while True:
        time.sleep(scenarios_changed_wait_time)
        (status_code, result_content) = webapi.scenarios_changed(device_id, device_token)
        if status_code == Response.STATUS_OK:
            lock.acquire()
            scenarios_changed = True
            lock.release()
            event.set()
        elif status_code != Response.NO_CONTENT:
            print 'SM: webapi.scenarios_changed returned status code ' \
                  + str(status_code) \
                  + '. (in method _scenarios_changed'


# download Scenarios from WebApi
# lock must be acquired when invoking this method
def _get_scenarios():
    global scenarios
    (status_code, result_content) = webapi.get_scenarios(device_id, device_token)
    if status_code != Response.STATUS_OK:
        print 'SM: webapi.get_scenarios returned status code ' \
                  + str(status_code) \
                  + '. (in method _get_scenarios'
        scenarios = []
        return
    result_object = json.loads(result_content)
    scenarios = result_object  # lock is acquired


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
            continue  # there is no Measurement from Module with this Id (yet)
        value = measurements[str(scen["ConditionModuleId"])]
        print('>> sprawdzam scenariusze, ostatnia wartosc dla modulu o id: ' + str(
                scen["ConditionModuleId"]) + ' wynosi: ' + str(value))

        if not str(scen["Id"]) in doneScenarios:
            doneScenarios[str(scen["Id"])] = 0
        done = doneScenarios[str(scen["Id"])]
        if done > 0 and int(scen["Recurring"]) == 0:
            continue  # // scenario was already executed, and is not recurring

        conditionMet = False
        temp = ''
        wilg = ''
        if scen["Condition"] < 5:
            v = value.split(';')
            if len(v) != 2:
                continue  # not properly encoded value.
            temp = v[0]
            wilg = v[1]

        if scen["Condition"] == 1:  # Temperatura ponizej..
            if temp < scen["ValueInt"]:
                conditionMet = True
        if scen["Condition"] == 2:  # Temperatura powyzej..
            if temp > scen["ValueInt"]:
                conditionMet = True
        if scen["Condition"] == 3:  # Wilgotnosc ponizej..
            if wilg < scen["ValueInt"]:
                conditionMet = True
        if scen["Condition"] == 4:  # Wilgotnosc powyzej..
            if wilg > scen["ValueInt"]:
                conditionMet = True
        if scen["Condition"] == 5:  # Wykryto ruch
            print('Condition scenariusza - czy wykryto ruch?')
            if int(value) > 0:
                print('value=' + str(value) + '> 0, czyli tak')
                conditionMet = True
        if conditionMet:
            result.append(scen)

    return result


# endregion ~DETERMINE SCENARIOS TO BE EXECUTED


# region SCENARIO EXECUTION

# get a list of Scenarios which are supposed to be executed
# and try to execute them
# also, upload Execution object
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
        print('taking snapshot, port=' + str(module.address) + ' login:password')
        content = camera.get_camera_snapshot(str(module.address), "login", "password")
        print('snapshot taken, content = ')
        print(str(content))
        print('TODO: wyslac snapshot jako measurement')
        return True
    return False


# endregion ~SCENARIO EXECUTION


# region ENTRY AND MAIN METHOD

# in loop wait for event to be triggered, try to execute scenarios
def _main():
    global measurements
    global scenarios_changed

    while True:
        event.wait()
        lock.acquire()

        if scenarios_changed:
            _get_scenarios()
            scenarios_changed = False

        _try_execute_scenarios()

        # measurements need to be cleared, as to no Scenario is executed twice based on the same Measurement
        measurements = dict()

        event.clear()
        lock.release()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    print('Scenario Manager: Started.')
    _read_configuration_file()

    _get_scenarios()

    # thread responsible for communicating with running Modules
    t_accept = threading.Thread(target=_socket_accept)
    t_accept.daemon = True
    t_accept.start()

    # main routine thread
    t_main = threading.Thread(target=_main)
    t_main.daemon = True
    t_main.start()

    # checking with WebApi if Scenarios changed thread
    t_scenarios_changed = threading.Thread(target=_scenarios_changed)
    t_scenarios_changed.daemon = True
    t_scenarios_changed.start()

    signal.pause()  # wait for SIGINT, then shutdown

    print('Scenario Manager: Ended.')


# endregion ~ENTRY AND MAIN METHOD

