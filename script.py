#!/usr/bin/python2.7
import os.path as path
import os
import json
import signal
import subprocess
from WRH_Engine.RegisterDevice import RegisterDevice as register
from WRH_Engine.Configuration import configuration as config
from WRH_Engine.Utils import dynamic_loader as d
from WRH_Engine.WebApiLibrary import WebApiClient as W

CONFIGURATION_FILE = '.wrh.config'


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _siginit_handler(signal, frame):
    print 'SIGINT signal caught'


def _edit_module(system_info, modules):
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
    (status, response_content) = module.edit(system_info[0], system_info[1])

    if status == W.Response.STATUS_OK:
        print bcolors.OKGREEN + 'Congratulations, your module has sucessfully been modified' + bcolors.ENDC
        with open(CONFIGURATION_FILE, 'w') as f:
            config.update_configuration_file(f, system_info, modules)
    else:
        print bcolors.FAIL + "There was an error trying to modify module."
        print "***Error code: " + str(status)
        print "***Error message: " + str(response_content) + bcolors.ENDC


def _add_new_module(system_info, modules, modules_classes):
    module_classes_list = []
    print "*** Adding new module"

    while True:
        i = 1
        for _, module_class in modules_classes.iteritems():
            print "[" + str(i) + "] " + str(module_class.type_name)
            module_classes_list.append(module_class)
            i += 1
        print "[" + str(i) + "] Cancel\n"

        try:
            choice = int(raw_input("> "))
        except ValueError:
            continue
        if choice < 1 or choice > i: continue
        if choice == i: break
        module = module_classes_list[choice - 1]()
        (status, response_content) = module.run_registration_procedure(system_info[0], system_info[1])
        if status == W.Response.STATUS_OK:
            print bcolors.OKGREEN + "Success! You module has been registered." + bcolors.ENDC
            modules.append(module)
            with open(CONFIGURATION_FILE, 'w') as f:
                config.update_configuration_file(f, system_info, modules)
            break
        else:
            print bcolors.FAIL + "There was an error trying to register module."
            print "***Error code: " + str(status)
            print "***Error message: " + str(response_content) + bcolors.ENDC


def _remove_module(system_info, modules):
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
    (status, response_content) = module.remove_from_wrh(system_info[0], system_info[1])
    if status == W.Response.STATUS_OK:
        print bcolors.OKGREEN + 'Succesfuly removed selected module' + bcolors.ENDC
        modules.remove(module)
        with open(CONFIGURATION_FILE, 'w') as f:
            config.update_configuration_file(f, system_info, modules)
    else:
        print bcolors.FAIL + "There was an error trying to remove module."
        print "***Error code: " + str(status)
        print "***Error message: " + str(response_content) + bcolors.ENDC


def _run_overlord():
    signal.signal(signal.SIGINT, _siginit_handler)
    command = ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.OVERLORD.overlord"]
    process = subprocess.Popen(command)
    process.wait()
    # TODO: Remove SIGINT handler!
    signal.signal(signal.SIGINT, _siginit_handler)


def _run_maintenance_work(modules_classes):
    with open(CONFIGURATION_FILE, 'r') as f:
        (system_info, modules) = config.parse_configuration_file(f, modules_classes)

    while True:
        print '\n=== LIST OF REGISTERED MODULES ==='
        for i, module in enumerate(modules):
            print (str(i + 1) + ') ') + module.type_name + " named " + module.name
        print '\n[1] Edit module\n[2] Add new module\n[3] Delete module\n[4] Start modules\n[5] Exit'
        user_choice = raw_input('> ')
        try:
            value = int(user_choice)
        except ValueError:
            continue
        if value == 1:
            _edit_module(system_info, modules)
        elif value == 2:
            _add_new_module(system_info, modules, modules_classes)
        elif value == 3:
            _remove_module(system_info, modules)
        elif value == 4:
            _run_overlord()
        elif value == 5:
            break
        continue
    return


def _is_configuration_file_sane(modules):
    with open(CONFIGURATION_FILE, 'r') as f:
        print 'Configuration file found\nChecking it for errors...'
        return config.check_configuration_file_sanity(f, modules)


def _is_configuration_file_present():
    return path.isfile(CONFIGURATION_FILE)


def _scan_and_list_modules():
    module_classes = {}
    print "Scanning for available modules..."
    modules = d.scan_and_returns_modules("WRH_Engine/Modules/")
    for module_name, (module_path, class_name) in modules.iteritems():
        print "Found \"" + module_name + "\" module"
        module = str(module_path + module_name).replace('/', '.')
        module = __import__(module, globals(), locals(), ['*'])
        m_class = getattr(module, class_name)
        module_classes[m_class.type_number] = m_class

    return module_classes


def show_options():
    print 'Welcome to Wild Raspberry House management program!'
    modules = _scan_and_list_modules()
    if _is_configuration_file_present() and _is_configuration_file_sane(modules):
        _run_maintenance_work(modules)
    else:
        (is_success, response_content) = register.register_procedure()
        if is_success:
            print 'Congratulations! Your device has successfully been registered!'
            with open(CONFIGURATION_FILE, 'a+') as f:
                system_info = json.loads(response_content)
                f.write(str(system_info['Id']) + ";" + str(system_info['Token']) + '\n')


if __name__ == "__main__":
    if os.getuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
    show_options()
