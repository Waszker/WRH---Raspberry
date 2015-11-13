#!/bin/python2
import requests
import json
from enum import Enum

class Response(Enum):
    STATUS_OK = 200
    STATUS_UNAUTHORIZED = 401
    STATUS_BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    
<<<<<<< HEAD
headers = {'content-type': 'application/json'}
base_address = 'https://wildraspberrywebapi.azurewebsites.net/'
register_device_url = base_address + 'api/wrh/registerdevice'
add_module_url = base_address + 'api/wrh/addmodule'
edit_module_url = base_address + ''
remove_module_url = base_address + ''
get_scenarios_url = base_address + ''
add_measurement_url = base_address + ''
	
def do_post_request(url, content):
	response = requests.post(url, data = json.dumps(content), headers = headers)
	return (response.status_code, response.text)
def register_device(username, password, device_name, device_color):
	content = {'Username': username, 'Password': password, 'Name': device_name, 'Color': device_color}
	return do_post_request(register_device_url, content)

def add_module(device_id, device_token, module_name, module_type):
	content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
	return do_post_request(add_module_url, content)

<<<<<<< HEAD
def edit_module(device_id, device_token, module_id,  module_name):
	content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
	return do_post_request(add_module_url, content)
	
def remove_module(device_id, device_token, module_id):
	content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
	return do_post_request(add_module_url, content)
	
def get_scenarios(device_id, device_token):
	content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
	return do_post_request(add_module_url, content)
	
def add_measurement(device_id, device_token, module_id, timestamp, value, streamingaddress):
	content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
