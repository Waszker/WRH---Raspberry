class Module:
    'This class will represent generic module'
    type = -1
    id = -1
    gpio = ""
    name = ""
    address = ""

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

    def get_type_name(self):
        try:
            type_name = Module.types_strings[type]
        except KeyError:
            type_name = "UNKNOWN"
        return type_name

    def get_information_string(self):
        print (self.name + ' is module of type ' + str(self.get_type_name())),
        if type == 1 or type == 3 :
            print ('connected to gpio ' + self.gpio)
        else:
            print ('available at address ' + self.address)
