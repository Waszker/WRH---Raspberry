#!/bin/python2
import requests
import json
from enum import Enum

# WebApiClient - Module used for communication with Web Api
# Available Web Api methods are documented here: https://wildraspberrywebapi.azurewebsites.net/swagger/ui/index#/


class Response(Enum):
    STATUS_OK = 200
    STATUS_UNAUTHORIZED = 401
    STATUS_BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    NO_CONTENT = 204
    CONNECTION_ERROR = -1

headers = {'content-type': 'application/json'}
base_address = 'https://wildraspberrywebapi.azurewebsites.net/'
register_device_url = base_address + 'api/wrh/registerdevice'
add_module_url = base_address + 'api/wrh/addmodule'
edit_module_url = base_address + 'api/wrh/editmodule'
remove_module_url = base_address + 'api/wrh/removemodule'
get_scenarios_url = base_address + 'api/wrh/getscenariosdevice'
add_measurement_url = base_address + 'api/wrh/addmeasurement'
scenarios_changed_url = base_address + 'api/wrh/scenarioschanged'
add_execution_url = base_address + 'api/wrh/addexecution'
get_user_last_active_url = base_address + 'api/wrh/getuserlastactive'


# Generic method for making HTTP POST requests
def do_post_request(url, content):
    try:
        response = requests.post(url, data = json.dumps(content), headers = headers)
        result = (response.status_code, response.text)
    except requests.exceptions.ConnectionError:
        result = (Response.CONNECTION_ERROR, "No Internet connection")

    return result


# Register Device in the WRH system
def register_device(username, password, device_name, device_color):
    content = {'Username': username, 'Password': password, 'Name': device_name, 'Color': device_color}
    return do_post_request(register_device_url, content)


# Add a new Module
def add_module(device_id, device_token, module_name, module_type):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
    return do_post_request(add_module_url, content)


# Edit an existing Module
def edit_module(device_id, device_token, module_id, module_name):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Id': module_id, 'Gpio': 0, 'Name': module_name}
    return do_post_request(edit_module_url, content)


# Remove an existing Module
def remove_module(device_id, device_token, module_id):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Id': module_id}
    return do_post_request(remove_module_url, content)


# Get Scenarios for this Device
def get_scenarios(device_id, device_token):
    content = {'Id': device_id, 'Token': device_token}
    return do_post_request(get_scenarios_url, content)


# Add a new Measurement
# streamingaddress is optional, used for specifying Camera's address
def add_measurement(device_id, device_token, module_id, timestamp, value, streamingaddress):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'ModuleId': module_id, 'Timestamp': timestamp, 'Value': value, 'StreamingAddress': streamingaddress}
    return do_post_request(add_measurement_url, content)


# Check if list of Scenarios has changed
def scenarios_changed(device_id, device_token):
    content = {'Id': device_id, 'Token': device_token}
    return do_post_request(scenarios_changed_url, content)


# Add a new Scenario Execution
def add_execution(device_id, device_token, value_condition, value_action, timestamp, scenario_id, condition, action):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'ValueCondition': value_condition, 'ValueAction': value_action, 'Timestamp': timestamp, 'ScenarioId': scenario_id, 'Condition': condition, 'Action': action }
    return do_post_request(add_execution_url, content)


# Get datetime of User's last activity in any of the client apps
def get_user_last_active(device_id, device_token):
    content = {'Id': device_id, 'Token': device_token}
    return do_post_request(get_user_last_active_url, content)