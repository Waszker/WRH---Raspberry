#!/usr/bin/python2.7
import os.path as path
import json
from WRH_Engine.RegisterDevice import RegisterDevice as register
from WRH_Engine.Configuration import configuration as config

CONFIGURATION_FILE = '.wrh.config'

def _run_maintenance_work():
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, modules) = config.parse_configuration_file(f)
        for module in modules :
            config.print_module_information(module)
    return

def _is_configuration_file_sane():
    with open(CONFIGURATION_FILE, 'r') as f:
        print 'Configuration file found\nChecking it for errors...'
        return config.check_configuration_file_sanity(f)
    return False

def _is_configuration_file_present():
    return path.isfile(CONFIGURATION_FILE)

def show_options():
    print 'Welcome to Wild Raspberry House management program!'
    if(_is_configuration_file_present() and _is_configuration_file_sane()):
        _run_maintenance_work()
    else:
        (is_success, response_content) = register.register_procedure()
        if(is_success):
            print 'Congratulations! Your device has successfully been registered!'
            with open(CONFIGURATION_FILE, 'w') as f:
                system_info = json.loads(response_content)
                f.write(str(system_info['Id']) + ";" + str(system_info['Token']))

if __name__ == "__main__":
    show_options()
