#!/usr/bin/env python

# from ..WebApiLibrary import WebApiClient as W
import time
import os
import re
import datetime
import socket
from os import listdir
from WRH_Engine.WebApiLibrary import WebApiClient as W


# method synchronize measurements with server and send last measurement to scenario manager
def manage_measurement(device_id, device_token, module_id, module_type, measurement, streaming_address):
    _send_measurement_to_scenario_manager(measurement, module_id)
    path = "/var/wrh/{}_{}".format(module_type, module_id)
    send_result = W.add_measurement(device_id, device_token, str(module_id), str(generate_proper_date()),
                                    str(measurement), streaming_address)
    if send_result[0] == W.Response.STATUS_OK:
        # sending this measurement succeeded, so try to send Measurements stored on memory card
        _send_old_measurements(path, device_id, device_token, module_id)
    else:
        # sending this measurement failed, so store it on card
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
                    f.write("{}${}".format(generate_proper_date(), str(measurement)))
            except IOError as err:
                raise IOError(err.message)


def _send_measurement_to_scenario_manager(measurement, module_id):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 2000))
    client_socket.send(str(module_id))
    client_socket.recv(4096)
    client_socket.send(str(measurement))


def _send_old_measurements(path, device_id, device_token, module_id):
    try:
        if os.path.exists(path):
            # ... for each file in measurement directory
            for file in listdir(path):
                # read content
                with open(os.path.join(path, file), 'r') as content_file:
                    content = content_file.read()
                # pull out timestamp and measurement
                pair = content.split('$')
                if (len(pair) != 2):
                    os.remove(os.path.join(path, file))
                # send measurement
                elif W.add_measurement(device_id, device_token, str(module_id), pair[0], pair[1], "")[
                    0] == W.Response.STATUS_OK:
                    # remove file if ok
                    os.remove(os.path.join(path, file))
    except IOError as err:
        raise IOError(err.message)


# generates proper date format: YYYY-MM-DDThh:mm:ss
def generate_proper_date():
    hour = int(time.strftime("%H"))
    if hour == 24:
        hour = 1
    elif hour == 23:
        hour = 0
    else:
        hour += 1
    return time.strftime("%Y-%m-%dT{}:%M:%S".format(hour), time.gmtime())


# make a python datetime object based on our datetime string
# YYYY-MM-DDThh:mm:ss
# returns: (success, datetime)
def convert_datetime_to_python(our_datetime):
    if not our_datetime:
        return False, ''
    date_time_pattern = re.compile(
        "^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9])T([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")
    does_match = date_time_pattern.match(our_datetime)
    if not does_match:
        our_datetime = str(our_datetime)[1:-1]
        does_match = date_time_pattern.match(our_datetime)
        if not does_match:
            return False, ''
    groups = re.search(date_time_pattern, our_datetime)
    success = True
    try:
        result = datetime.datetime(int(groups.group(1)), int(groups.group(2)), int(groups.group(3)),
                                   int(groups.group(4)), int(groups.group(5)), int(groups.group(6)))
    except:
        success = False
        result = ''

    return success, result


def get_non_empty_input(message):
    """
    Reads user input discarding all empty messages.
    :param message: Message to display
    :return: User's input
    """
    answer = None
    while answer is None or len(answer) == 0:
        answer = raw_input(message)
    return answer
