#!/usr/bin/env python

# from ..WebApiLibrary import WebApiClient as W
import time
import os
import re
import datetime
import socket
from os import listdir
from WRH_Engine.WebApiLibrary import WebApiClient as W


def manage_measurement(device_id, device_token,  module_id,  module_type, measurement, streaming_address):
    _send_measurement_to_scenario_manager(measurement)
    path = "/var/wrh/{}_{}".format(module_type, module_id)
    send_result = W.add_measurement(device_id, device_token, str(module_id), str(generate_proper_date()), str(measurement), streaming_address)
    if send_result[0] == W.Response.STATUS_OK:
        # send old measurements
        print('man_meas: udalo sie wyslac')
        _send_old_measurements(path, device_id,  device_token, module_id)
    else:
        print('man_meas: nie udalo sie wyslac, code:' + str(send_result[0]))
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            with open("{}/{}.wrh".format(path, time.strftime("%Y-%d-%m.%H:%M:%S")), 'a+') as f:
                f.write("{}${}".format(str(generate_proper_date()), str(measurement)))
        except IOError as err:
            try:
                # remove the oldest file
                file = listdir(path)[0]
                os.remove(os.path.join(path, file))
                # try to write measurement once again
                with open("{}/{}.wrh".format(path, time.strftime("%Y-%d-%m.%H:%M:%S")), 'a+') as f:
                    f.write("{}${}".format(generate_proper_date(), measurement))
            except IOError as err:
                raise IOError(err.message)


def _send_measurement_to_scenario_manager(measurement):
	print('wysylam measurement do scenario manager')
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 2000))
	clientsocket.send(str(module.id))
	clientsocket.recv(4096)
	clientsocket.send(str(measurement))


def _send_old_measurements(path, device_id,  device_token, module_id):
    try:
        if os.path.exists(path):
			# ... for each file in measurement directory
			for file in listdir(path):
				content = ''
				# read content
				with open(os.path.join(path, file), 'r') as content_file:
					content = content_file.read()
				# pull out timestamp and measuremet
				pair = content.split('$')
				# send measurement
				if W.add_measurement(device_id, device_token, str(module_id), pair[0], pair[1], "")[0] == W.Response.STATUS_OK:
					# remove file if ok
					os.remove(os.path.join(path, file))
    except IOError as err:
        raise IOError(err.message)


def generate_proper_date():
    # YYYY-MM-DDThh:mm:ss
    hour = int(time.strftime("%H"))
    if hour == 24:
        hour = 00
    else:
        hour = hour + 1
    return time.strftime("%Y-%d-%mT{}:%M:%S".format(hour), time.gmtime())


# make a python datetime object based on our datetime string
# YYYY-MM-DDThh:mm:ss
# returns: (success, datetime)
def _convert_datetime_to_python(our_datetime):
	if not our_datetime:
		return (False,  '')
	datetimepattern = re.compile("^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9])T([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")
	does_match = datetimepattern.match(our_datetime)
	if not does_match:
		return (False,  '')
	groups = re.search(datetimepattern,  our_datetime)
	success = True
	result = ''
	try:
		result = datetime.datetime(int(groups.group(1)), int(groups.group(2)), int(groups.group(3)), int(groups.group(4)), int(groups.group(5)), int(groups.group(6)))
	except:
		success = False
		result = ''
	
	return (success,  result)
