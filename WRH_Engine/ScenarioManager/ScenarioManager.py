#!/usr/bin/python2.7
from WRH_Engine.WebApiLibrary import Response
from ..WebApiLibrary import WebApiClient as WebApiClient
from WRH_Engine.Configuration import configuration as config
from WRH_Engine.ScenarioManager.Scenario import Scenario
from WRH_Engine.ScenarioManager.Execution import Execution
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


# TODO: Periodically try to send unsent Execution objects


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
executions = []  # does not need lock, because used only by one thread


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
    scenarios = _convert_json_scenarios_to_python_objects(result_object)  # lock is acquired


# Convert dict type Scenarios to Scenario objects
def _convert_json_scenarios_to_python_objects(json_scenarios):
    object_scenarios = []
    for json_scenario in json_scenarios:
        object_scenarios.append(Scenario(json_scenario))
    return object_scenarios


# endregion ~UPDATE SCENARIOS


# region DETERMINE SCENARIOS TO BE EXECUTED


# from a list of Scenarios, get scenarios that are active (startDate <= DateTime.Now <= endDate)
def _get_active_scenarios_by_date(scenario_list):
    (success, now) = utils.convert_datetime_to_python(utils.generate_proper_date())
    if not success:
        print 'Scenario Manager: error in utils.generate_proper..() or utils.convert_datetime..().'
        return scenario_list
    result = []

    for scenario in scenario_list:
        active = True
        (success_start, start) = utils.convert_datetime_to_python(scenario.start_date)
        (success_end, end) = utils.convert_datetime_to_python(scenario.end_date)

        if success_start:  # Scenario has valid start date
            if now < start:
                active = False  # Scenario has not yet started
        if success_end:
            if now > end:
                active = False  # Scenario has finished

        if active:
            result.append(scenario)

    return result


# from a list of Scenarios, exclude scenarios with the lowest priority within scenarios with the same action module
def _get_active_scenarios_by_priority(scenario_list):
    result = []

    for scenario in scenario_list:
        active = True

        for other_scenario in scenario_list:
            if other_scenario.action_module_id == scenario.action_module_id:
                if other_scenario.priority > scenario.priority:
                    active = False  # there is a Scenario with higher Priority (to the same Action Module)
                    break

        if active:
            result.append(scenario)

    return result


# from a list of Scenarios, exclude scenarios that were done (and not recurring)
def _get_active_scenarios_by_done(scenario_list):
    result = []
    for scenario in scenario_list:
        if not str(scenario.id) in done_scenarios:
            done_scenarios[str(scenario.id)] = 0
        done = done_scenarios[str(scenario.id)]
        if done > 0 and scenario.recurring == 0:
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
        if not str(scenario.condition_module_id) in measurements:
            continue  # there is no Measurement from Condition Module (yet)
        value = measurements[str(scenario.condition_module_id)]

        condition_met = False
        temperature = ''
        humidity = ''
        if scenario.condition < 5:
            (temperature, humidity) = _decode_dht_value(value)

        if scenario.condition == 1:  # Temperature below...
            if temperature < scenario.value_int:
                condition_met = True
        if scenario.condition == 2:  # Temperature above...
            if temperature > scenario.value_int:
                condition_met = True
        if scenario.condition == 3:  # Humidity below...
            if humidity < scenario.value_int:
                condition_met = True
        if scenario.condition == 4:  # Humidity above...
            if humidity > scenario.value_int:
                condition_met = True
        if scenario.condition == 5:  # Movement
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

# create Execution object, after successfully executing Scenario
def _add_execution(scenario, action_value, condition_value):
    global executions
    now = utils.generate_proper_date()

    executions.append(Execution(device_id, device_token, condition_value, action_value,
                                now, scenario.id, scenario.condition, scenario.action))

    executions = _upload_executions(executions)
    return


# upload Executions to Web Api
# returns a list of NOT uploaded objects
def _upload_executions(execution_list):
    result = []
    for execution in execution_list:
        (status_code, content) = WebApiClient.add_execution(execution.device_id, execution.device_token,
                                                            execution.condition_value, execution.action_value,
                                                            execution.timestamp, execution.scenario.id,
                                                            execution.condition, execution.action)
        if status_code != Response.STATUS_OK:
            result.append(execution)
    return result


# get a list of Scenarios which are supposed to be executed
# and try to execute them one by one
# also, upload Execution object of successfully executed Scenarios
def _try_execute_scenarios():
    global measurements
    global done_scenarios
    global scenarios

    scenarios_to_execute = _get_scenarios_to_execute()
    for scenario in scenarios_to_execute:
        (success, action_value) = _execute_scenario(scenario)
        if success:
            done_scenarios[str(scenario.id)] += 1
            print 'Scenario Manager: successfully executed Scenario: ' + scenario.name + '\n'
            _add_execution(scenario, action_value, measurements[str(scenario.condition_module_id)])
        else:
            print 'Scenario Manager: failed to execute Scenario: ' + scenario.name + '\n'
    return


# execute a Scenario, return (success, value)
# if Action == take snapshot, then value = snapshot
def _execute_scenario(scenario):
    action_module_id = str(scenario.action_module_id)
    action = scenario.action
    for module in available_modules:
        if str(module.id) == str(action_module_id):
            module = module
            break
    if not module:
        print 'ScenarioManager: Action Module not found.'
        return False, ''  # Action module not found

    if action == 1:
        suffix = '?on'
    if action == 2:
        suffix = '?off'
    if action == 3:
        suffix = '?toggle'

    if 1 <= action <= 3:
        try:
            urllib2.urlopen('http://' + module.address + '/cgi-bin/relay.cgi' + suffix).read()
        except:
            print 'ScenarioManager: Unable to communicate with wi-fi socket.'
            return False, ''
        return True, ''

    if action == 4:
        try:
            content = camera.get_camera_snapshot(str(module.address), "login", "password")
        except:
            print 'ScenarioManager: Unable to take camera snapshot.'
            return False, ''
        return True, content

    print 'ScenarioManager: Unsupported scenario action.'
    return False, ''


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
