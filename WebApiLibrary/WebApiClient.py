#!/bin/python2
import requests
import json
from enum import Enum

headers = {'content-type': 'application/json'}
base_address = 'https://wildraspberrywebapi.azurewebsites.net/'
register_device_url = base_address + 'api/wrh/registerdevice'
add_module_url = base_address + 'api/wrh/addmodule'

class Response(Enum):
    STATUS_OK = 200
    STATUS_UNAUTHORIZED = 401
    STATUS_BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500

def register_device(username, password, device_name, device_color):
    content = {'Username': username, 'Password': password, 'Name': device_name, 'Color': device_color}
    return do_post_request(register_device_url, content)

def add_module(device_id, device_token, module_name, module_type):
    content = {'DeviceId': device_id, 'Devicetoken': device_token, 'Name': module_name, 'Type': module_type}
    return do_post_request(add_module_url, content)

def do_post_request(url, content):
    response = requests.post(url, data = json.dumps(content), headers = headers)
    return (response.status_code, response.text)

