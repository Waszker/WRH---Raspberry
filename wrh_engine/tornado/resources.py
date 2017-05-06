#!/bin/python2
import datetime
import subprocess as s
from wrh_engine.module_loader import ModuleDynamicLoader
from wrh_engine.engine import ConfigurationParser
from utils.system_info import get_uptime, get_cpu_temp


def get_available_module_types():
    loader = ModuleDynamicLoader('modules/')
    modules_classes = loader.get_module_classes()
    parser = ConfigurationParser('.', modules_classes)
    modules = parser.get_installed_modules()
    return modules_classes, modules


def get_system_stats():
    def _convert_to_two_digit_number(number):
        result_number = str(number)
        if number < 10:
            result_number = "0" + str(number)
        return result_number

    now = datetime.datetime.now()
    stat_string = "Date: %s-%s-%s <br />" % (_convert_to_two_digit_number(now.day),
                                             _convert_to_two_digit_number(now.month),
                                             _convert_to_two_digit_number(now.year))
    stat_string += "Hour: %s:%s <br />" % (_convert_to_two_digit_number(now.hour),
                                           _convert_to_two_digit_number(now.minute))
    stat_string += "Uptime: " + get_uptime() + "<br />"
    stat_string += "CPU temp: " + str(round(get_cpu_temp(), 1)) + "*C <br />"

    return stat_string


def restart():
    print "Restarting system"
    s.call("sudo reboot", shell=True)
    return
