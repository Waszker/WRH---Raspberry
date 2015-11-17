#!/usr/bin/python2.7
import os.path as path
import json
from WRH_Engine.RegisterDevice import RegisterDevice as register
from WRH_Engine.Configuration import configuration as config
from WRH_Engine.module.module import Module

CONFIGURATION_FILE = '.wrh.config'

def _edit_module(modules) :
    print 'Editing module'

def _add_new_module() :
    print '\n***Adding new module***'
    print '[1] DHT\n[2] Camera\n[3] Motion\n[4] Wi-Fi Socket\n[5] Cancel'

    while True :
        choice = raw_input('> ')
        try:
            value = int(choice)
        except ValueError :
            continue
        if value == 5 :
            break
        continue


def _run_maintenance_work():
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, modules) = config.parse_configuration_file(f)
        while True :
            print '\n=== LIST OF REGISTERED MODULES==='
            for module in modules :
                module.get_information_string()
            print '\n[1] Edit module\n[2] Add new module\n[3] Exit'
            user_choice = raw_input('> ')
            try :
                value = int(user_choice)
            except ValueError:
                continue
            if value == 1 :
                _edit_module(modules)
            elif value == 2 :
                _add_new_module()
            elif value == 3 :
                break
            continue
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
