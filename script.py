#!/usr/bin/python2.7
import os.path as path
from WRH_Engine.RegisterDevice import RegisterDevice as register

CONFIGURATION_FILE = '.wrh.config'

def run_maintenance_work():
    print 'Looks like your account has already been registered. Good!'
    return

def is_configuration_file_sane():
    return True

def is_configuration_file_present():
    return path.isfile(CONFIGURATION_FILE)

def show_options():
    print 'Welcome to Wild Raspberry House management program!'
    if(is_configuration_file_present() and is_configuration_file_sane()):
        run_maintenance_work()
    else:
        (is_success, response_content) = register.register_procedure()
        if(is_success):
            print 'Congratulations! Your device has successfully been registered!'
            with open(CONFIGURATION_FILE, 'w') as f:
                f.write(response_content)

if __name__ == "__main__":
    show_options()
