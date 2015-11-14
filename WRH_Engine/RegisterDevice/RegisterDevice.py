import re
import getpass
from ..WebApiLibrary import WebApiClient as W

def _is_device_color_convention_correct(color):
    pattern = re.compile("#[\d | A-F]{8}")
    return pattern.match(color)

def _get_device_information():
    while True:
        device_name = raw_input('Your device "name": ')
        if device_name :
            break
        print 'Please enter device\'s name'

    while True:
        device_color = raw_input('Device\'s color in HEX (e.g. #FFFF0000 for red): ')
        if _is_device_color_convention_correct(device_color) :
            break
        print 'Color has to start with # and be followed by 8 digits and/or letters from A - F'

    return (device_name, device_color)

def _is_username_convention_correct(username):
    pattern = re.compile("(.+?)@(.+?).(..)")
    return pattern.match(username)

def _get_login_information():
    while True:
        username = raw_input("Username: ")
        if _is_username_convention_correct(username) :
            break
        print 'Username has to be in form of email address: e.g. name@domain.com'

    password = getpass.getpass('Password: ')

    return (username, password)

def _register_device():
    (username, password) = _get_login_information()
    (device_name, device_color) = _get_device_information()

    print 'Trying to register device'
    (status_code, result_content) = W.register_device(username, password, device_name, device_color)
    is_success = False

    if status_code == W.Response.STATUS_OK.value :
        is_success = True
    else:
        print '***Failed to register device'
        print '***Response code: ' + str(status_code)
        print '***Response content: ' + str(result_content)

    return (is_success, result_content)

# Runs register procedure that asks user some important questions
def register_procedure():
    print "Register procedure requires you to have an account in WRH system"
    is_user_registered = raw_input('Do you have already an account? [Y/N]: ')

    if(is_user_registered == 'Y'):
        return _register_device()
    else:
        print 'Please use your browser or mobile app to create your account'
        print 'The WWW address is: https://wrhsystem.com'
        return (False, "")

if __name__ == "__main__":
    register_procedure()
