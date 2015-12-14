from ..WebApiLibrary import WebApiClient as W

class Module:
    'This class will represent generic module'
    types_strings = {
        1 : 'DHT',
        2 : 'CAMERA',
        3 : 'MOTION',
        4 : 'WI-FI SOCKET'
    }


    def __init__(self, id, type, gpio, name, address):
        self.id = int(id)
        self.type = int(type)
        self.gpio = str(gpio)
        self.name = str(name)
        self.address = str(address)


    def print_information_string(self):
        print (self.name + ' is module of type ' + Module.get_type_name(self.type)),
        if self.type == 1 or self.type == 3 :
            print ('connected to gpio ' + self.gpio)
        else:
            print ('available at address ' + self.address)


    def run_edit_procedure(self, system_info):
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_gpio = raw_input('New gpio or system device name: ')
        new_address = raw_input('New connection address: ')
        if new_name :
            is_success = self._update_module_information(system_info, new_name)
            if is_success:
                print 'Congratulations, your module has sucessfully been modified'
                self.name = new_name
            else :
                print '***Error modifying module.'
                print '***Please try again'
        if new_gpio : self.gpio = new_gpio
        if new_address : self.address = new_address


    def _update_module_information(self, system_info, new_name):
        (status, response_content) = W.edit_module(system_info[0], system_info[1], self.id, new_name)
        return status == W.Response.STATUS_OK


    def run_removal_procedure(self, system_info):
        is_success = False
        (status, response_content) = W.remove_module(system_info[0], system_info[1], self.id)
        if status == W.Response.STATUS_OK:
            print 'Succesfully removed selected module'
            is_success = True
        else:
            print '***There was an error trying to remove selected module'
            print '***Please try again'

        return is_success


    @staticmethod
    def get_type_name(type):
        try:
            type_name = Module.types_strings[type]
        except KeyError:
            type_name = "UNKNOWN"
        return type_name


    @staticmethod
    def register_new_module(system_info) :
        print '\n***Adding new module***'
        i = 1

        # Display all available module types
        for key, name in Module.types_strings.iteritems():
            print '[' + str(key) + '] ' + name
            i = i+1
        print '[' + str(i) + '] Cancel'

        # Get user selection and run registration procedure
        new_module = None
        while True :
            choice = raw_input('> ')
            try:
                value = int(choice)
            except ValueError :
                continue
            if value == i : # user wants to exit
                break
            elif Module.get_type_name(value) != "UNKNOWN":
                new_module = Module._run_registration_procedure(system_info, value)
                break
            continue
        return new_module


    @staticmethod
    def _run_registration_procedure((device_id, device_token), type):
        new_module = None

        while True:
            name = raw_input('Give ' + Module.get_type_name(type) + ' module name: ')
            if name : break
        gpio = raw_input('Enter GPIO or device name (e.g. for camera /dev/video0\'): ')
        address = raw_input('Enter web address at which device will be accessed: ')
        print 'Ok, all good. Now wait for registration procedure to finish...'
        (status, response_content) = W.add_module(device_id, device_token, name, type)
        if status != W.Response.STATUS_OK :
            print 'There was an error trying to register module.\nPlease try again'
            print '***Error code ' + str(status)
            print '***Error response ' + str(response_content)
        else:
            print 'Congratulations, your new module has been registered!'
            new_module = Module(response_content, type, gpio, name, address)

        return new_module

