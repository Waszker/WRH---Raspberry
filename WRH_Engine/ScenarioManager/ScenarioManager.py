#!/usr/bin/python2.7
from WRH_Engine.WebApiLibrary import Response
from ..WebApiLibrary import WebApiClient as WebApiClient
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
from datetime import datetime, timedelta


# SCENARIO MANAGER
# Module responsible for managing Scenarios assigned to this Device
# This Module is started by the Overlord
# Scenario Manager periodically checks for updated Scenarios..
# ..and communicates with other running Modules, to see if any of their most recent Measurements..
# ..matches any of the Scenarios' Conditions..
# ..if yes, then Scenario is executed, and Execution object uploaded


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
done_scenarios = dict()  # // [scenarioId] - [number of times the scenario was executed]
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
        (status_code, result_content) = WebApiClient.scenarios_changed(device_id, device_token)
        if status_code == Response.STATUS_OK:
            lock.acquire()
            scenarios_changed = True
            lock.release()
            event.set()
        elif status_code != Response.NO_CONTENT:
            print 'Scenario Manager: WebApiClient.scenarios_changed returned status code ' \
                  + str(status_code) \
                  + '. (in method _scenarios_changed()'


# download Scenarios from WebApi
# lock must be acquired when invoking this method
def _get_scenarios():
    global scenarios
    (status_code, result_content) = WebApiClient.get_scenarios(device_id, device_token)
    if status_code != Response.STATUS_OK:
        print 'Scenario Manager: WebApiClient.get_scenarios returned status code ' \
                  + str(status_code) \
                  + '. (in method _get_scenarios()'
        scenarios = []
        return
    result_object = json.loads(result_content)
    scenarios = result_object  # lock is acquired


# endregion ~UPDATE SCENARIOS


# region DETERMINE SCENARIOS TO BE EXECUTED


# from a list of Scenarios, get scenarios that are active (startDate <= DateTime.Now <= endDate)
def _get_active_scenarios_by_date(scenario_list):
    now = datetime.utcnow()
    result = []
    # TODO: not implemented
    for scenario in scenario_list:
        active = True

        if active:
            result.append(scenario)

    return result


# from a list of Scenarios, exclude scenarios with the lowest priority within scenarios with the same action module
def _get_active_scenarios_by_priority(scenario_list):
    result = []
    # TODO not implemented
    for scenario in scenario_list:
        active = True

        if active:
            result.append(scenario)

    return result


# from a list of Scenarios, exclude scenarios that were done (and not recurring)
def _get_active_scenarios_by_done(scenario_list):
    result = []
    for scenario in scenario_list:
        if not str(scenario["Id"]) in done_scenarios:
            done_scenarios[str(scenario["Id"])] = 0
        done = done_scenarios[str(scenario["Id"])]
        if done > 0 and int(scenario["Recurring"]) == 0:
            continue  # exclude this Scenario
        result.append(scenario)
    return result


# return a tuple of Temperature and Humidity from single string value
def _decode_dht_value(encoded_value):
    v = encoded_value.split(';')
    return int(float(v[0])), int(float(v[1]))


# from a list of Scenarios, return Scenarios that should be executed based on recent Measurements
def _get_active_scenarios_by_measurements(scenario_list):
    result = []
    for scenario in scenario_list:
        if not str(scenario["ConditionModuleId"]) in measurements:
            continue  # there is no Measurement from Condition Module (yet)
        value = measurements[str(scenario["ConditionModuleId"])]

        condition_met = False
        temperature = ''
        humidity = ''
        if scenario["Condition"] < 5:
            (temperature, humidity) = _decode_dht_value(value)

        if scenario["Condition"] == 1:  # Temperature below...
            if temperature < int(scenario["ValueInt"]):
                condition_met = True
        if scenario["Condition"] == 2:  # Temperature above...
            if temperature > int(scenario["ValueInt"]):
                condition_met = True
        if scenario["Condition"] == 3:  # Humidity below...
            if humidity < int(scenario["ValueInt"]):
                condition_met = True
        if scenario["Condition"] == 4:  # Humidity above...
            if humidity > int(scenario["ValueInt"]):
                condition_met = True
        if scenario["Condition"] == 5:  # Movement
            if int(value) > 0:
                condition_met = True

        if condition_met:
            result.append(scenario)

    return result


# get a list of Scenarios that should be executed
# based on recent Measurements and current time..
# ..also consider if Scenarios were already executed
def _get_scenarios_to_execute():
    global scenarios
    result = scenarios
    result = _get_active_scenarios_by_done(result)
    result = _get_active_scenarios_by_date(result)
    result = _get_active_scenarios_by_priority(result)
    result = _get_active_scenarios_by_measurements(result)
    return result


# endregion ~DETERMINE SCENARIOS TO BE EXECUTED


# region SCENARIO EXECUTION

# get a list of Scenarios which are supposed to be executed
# and try to execute them
# also, upload Execution object
def _try_execute_scenarios():
    global measurements
    global done_scenarios
    global scenarios
    print('try_execute_scenarios, scenariuszy jest: ' + str(len(scenarios)))

    scensToExecute = _get_scenarios_to_execute()
    for scen in scensToExecute:
        print('trying to execute scenario ' + str(scen["Id"]))
        result = _execute_scenario(str(scen["ActionModuleId"]), str(scen["Action"]))
        if result == True:
            done_scenarios[str(scen["Id"])] = done_scenarios[str(scen["Id"])] + 1
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

