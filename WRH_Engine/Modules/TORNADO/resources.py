#!/bin/python2
from WRH_Engine.Configuration import configuration as c
from WRH_Engine.Utils import dynamic_loader as d
from contextlib import closing
import socket
import datetime


def get_available_module_types(configuration_file):
    modules_classes = d.scan_and_return_module_classes("WRH_Engine/Modules/")
    with open(configuration_file) as f:
        (_, modules) = c.parse_configuration_file(f, modules_classes)
    return modules_classes, modules


def getsystemstats():
    now = datetime.datetime.now()
    stat_string = "Date: %d-%d-%d <br />" % (now.day, now.month, now.year)
    stat_string += "Hour: %d-%d <br />" % (now.hour, now.minute)
    stat_string += "Uptime: " + _getuptime() + "<br />"
    stat_string += "CPU temp: " + str(round(_get_cpu_temp(), 1)) + "*C <br />"

    return stat_string


def get_request(host, port, message=None):
    """
    Receives message from host on provided port.
    :param host:
    :param port:
    :param message: message to send prior to receiving (can be None)
    :return:
    """
    data = None
    with closing(socket.socket()) as s:
        print "Connecting to " + host + " at port " + str(port)
        s.connect((host, int(port)))
        if message is not None or message != "":
            s.send(message)
        data = s.recv(1024)
    return data


def send_request(host, port, message):
    """
    Sends provided message to provided host and port.
    :param host:
    :param port:
    :param message:
    :return:
    """
    with closing(socket.socket()) as s:
        s.connect((host, int(port)))
        s.send(message)


def _get_cpu_temp():
    temp_file = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = temp_file.read()
    temp_file.close()
    return float(cpu_temp) / 1000


def _getuptime():
    uptime_string = ""

    with open('/proc/uptime', 'r') as f:
        total_seconds = float(f.readline().split()[0])

        # Helper vars:
        MINUTE = 60
        HOUR = MINUTE * 60
        DAY = HOUR * 24

        # Get the days, hours, etc:
        days = int(total_seconds / DAY)
        hours = int((total_seconds % DAY) / HOUR)
        minutes = int((total_seconds % HOUR) / MINUTE)
        seconds = int(total_seconds % MINUTE)

        # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
        if days > 0:
            uptime_string += str(days) + " " + (days == 1 and "day" or "days") + ", "
        if len(uptime_string) > 0 or hours > 0:
            uptime_string += str(hours) + " " + (hours == 1 and "hour" or "hours") + ", "
        if len(uptime_string) > 0 or minutes > 0:
            uptime_string += str(minutes) + " " + (minutes == 1 and "minute" or "minutes") + ", "
        uptime_string += str(seconds) + " " + (seconds == 1 and "second" or "seconds")
    return uptime_string
