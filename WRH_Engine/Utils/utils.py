﻿#!/usr/bin/env python

# from ..WebApiLibrary import WebApiClient as W
import time
import os
import re
import datetime
from os import listdir
from WRH_Engine.WebApiLibrary import WebApiClient as W


def manage_measurement(dev, module, measurement):
    path = "/var/wrh/{}_{}".format(module.type, module.id)
    if W.add_measurement(dev[0], dev[1], module.id, generate_proper_date(), measurement, "")[0] == W.Response.STATUS_OK:
        # send old measurements
        _send_old_measurements(path, dev, module.id)
    else:
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            with open("{}/{}.wrh".format(path, time.strftime("%Y-%d-%m.%H:%M")), 'a+') as f:
                f.write("{}${}".format(generate_proper_date(), measurement))
        except IOError as err:
            try:
                # remove the oldest file
                file = listdir(path)[0]
                os.remove(os.path.join(path, file))
                # try to write measurement once again
                with open("{}/{}.wrh".format(path, time.strftime("%Y-%d-%m.%H:%M")), 'a+') as f:
                    f.write("{}${}".format(generate_proper_date(), measurement))
            except IOError as err:
                raise IOError(err.message)


def _send_old_measurements(path, dev, module_id):
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
				if W.add_measurement(dev[0], dev[1], module_id, pair[0], pair[1], "")[0] == W.Response.STATUS_OK:
					# remove file if ok
					os.remove(os.path.join(path, file))
    except IOError as err:
        raise IOError(err.message)


def generate_proper_date():
    # YYYY-MM-DDThh:mm:ss
    return time.strftime("%Y-%d-%mT%H:%M:%S")


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
