#!/usr/bin/env python

# from ..WebApiLibrary import WebApiClient as W
import time
import os
import re
import datetime

def write_measurement(module_type, module_id, measurement):
    path = "/var/wrh/{}_{}".format(module_type, module_id)
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        with open("{}/{}.wrh".format(path, time.strftime("%Y-%d-%m.%H:%M")), 'a+') as f:
            f.write(measurement)
    except IOError as err:
        raise IOError(err.message)


def generate_proper_date_format():
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
		result = datetime.datetime(int(groups.group(1)),  int(groups.group(2)),  int(groups.group(3)),  int(groups.group(4)),  int(groups.group(5)),  int(groups.group(6)))
	except:
		success = False
		result = ''
	
	return (success,  result)


def add_measurement(insert_arguments_here):
    print ""
