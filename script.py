#!/usr/bin/python2.7
import os.path as path
import os
import json
import signal
import subprocess
from WRH_Engine.RegisterDevice import RegisterDevice as register
from WRH_Engine.Configuration import configuration as config
from WRH_Engine.module.module import Module

CONFIGURATION_FILE = '.wrh.config'

def _siginit_handler(signal, frame):
    print 'SIGINT signal caught'


def _edit_module(system_info, modules) :
    print 'Choose which module to edit'
    while True:
        user_choice = raw_input('> ')
        try:
            module_number = int(user_choice)
        except ValueError:
            continue
        if module_number > len(modules) or module_number <= 0:
            continue
        break

    module = modules[module_number - 1]
    module.run_edit_procedure(system_info)
    with open(CONFIGURATION_FILE, 'w') as f:
        config.update_configuration_file(f, system_info, modules)


def _add_new_module(system_info, modules) :
    module = Module.register_new_module(system_info)
    if module :
        modules.append(module)
        with open(CONFIGURATION_FILE, 'a') as f:
            config.add_new_module(f, module)


def _remove_module(system_info, modules) :
    print 'Choose which module to remove'
    while True:
        user_choice = raw_input('> ')
        try:
            module_number = int(user_choice)
        except ValueError:
            continue
        if module_number > len(modules) or module_number <= 0:
            continue
        break
    module = modules[module_number - 1]
    if module.run_removal_procedure(system_info):
        modules.remove(module)
        with open(CONFIGURATION_FILE, 'w') as f:
            config.update_configuration_file(f, system_info, modules)


def _run_overlord():
    signal.signal(signal.SIGINT, _siginit_handler)
    command = "./WRH_Engine/Modules/OVERLORD/program"
    process = subprocess.Popen(command)
    process.wait()
    signal.signal(signal.SIGINT, _siginit_handler)


def _run_maintenance_work():
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, modules) = config.parse_configuration_file(f)

    while True :
        print '\n=== LIST OF REGISTERED MODULES==='
        for i, module in enumerate(modules) :
            print (str(i+1) + ') '),
            module.print_information_string()
        print '\n[1] Edit module\n[2] Add new module\n[3] Delete module\n[4] Start modules\n[5] Exit'
        user_choice = raw_input('> ')
        try :
            value = int(user_choice)
        except ValueError:
            continue
        if value == 1 :
            _edit_module(system_info, modules)
        elif value == 2 :
            _add_new_module(system_info, modules)
        elif value == 3 :
            _remove_module(system_info, modules)
        elif value == 4 :
            _run_overlord()
        elif value == 5 :
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
            with open(CONFIGURATION_FILE, 'a+') as f:
                system_info = json.loads(response_content)
                f.write(str(system_info['Id']) + ";" + str(system_info['Token']) + '\n')

if __name__ == "__main__":
    if os.getuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
    show_options()
