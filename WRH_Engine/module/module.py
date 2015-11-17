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

    def get_information_string(self):
        print (self.name + ' is module of type ' + Module.get_type_name(self.type)),
        if self.type == 1 or self.type == 3 :
            print ('connected to gpio ' + self.gpio)
        else:
            print ('available at address ' + self.address)

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
        for key, name in Module.types_strings.iteritems():
            print '[' + str(key) + '] ' + name
            i = i+1
        print '[' + str(i) + '] Cancel'

        new_module = None
        while True :
            choice = raw_input('> ')
            try:
                value = int(choice)
            except ValueError :
                continue
            if value == i :
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
            print '***Error code ' + status
            print '***Error response ' + response_content
        else:
            print 'Congratulations, your new module has been registered!'
            new_module = Module(response_content, type, gpio, name, address)

        return new_module

