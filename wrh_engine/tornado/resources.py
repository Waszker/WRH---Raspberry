#!/bin/python2
import datetime
import subprocess as s

from utils.system_info import get_uptime, get_cpu_temp
from wrh_engine.constants import WRH_MODULES_FOLDER
from wrh_engine.engine import ConfigurationParser
from wrh_engine.module_loader import ModuleDynamicLoader


def get_installed_modules_info():
    loader = ModuleDynamicLoader(WRH_MODULES_FOLDER)
    modules_classes = loader.get_module_classes()
    parser = ConfigurationParser(modules_classes)
    modules = parser.get_installed_modules()
    unique_classes = list({modules_classes[m.WRHID] for m in modules})
    return sorted(unique_classes, key=lambda x: x.WRHID), modules


def get_system_stats():
    now = datetime.datetime.now()
    stat_string = "Date: %02i-%02i-%02i <br />" % (now.day, now.month, now.year)
    stat_string += "Hour: %02i:%02i <br />" % (now.hour, now.minute)
    stat_string += "Uptime: " + get_uptime() + "<br />"
    stat_string += "CPU temp: " + str(round(get_cpu_temp(), 1)) + "&deg;C <br />"

    return stat_string


def restart():
    s.call("sudo reboot", shell=True)
