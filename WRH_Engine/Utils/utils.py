#!/usr/bin/env python

# from ..WebApiLibrary import WebApiClient as W
import time
import os


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


def add_measurement(insert_arguments_here):
    print ""