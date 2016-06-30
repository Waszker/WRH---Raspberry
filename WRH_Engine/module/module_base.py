import abc
from ..WebApiLibrary import WebApiClient as W

class Module:
    """
    Abstract base class for modules used in WRH.
    """

    def __init__(self, configuration_file_line=None):
        """
        Creates instance of a specific module class from the information
        provided in configuration line.
        """
        if configuration_file_line is not None:
            self._parse_configuration_line(configuration_file_line)


    def _set_basic_information(self, id, module_name, type_number, type_name, port, address):
        """
        Sets basic information needed for every module in WRH.
        """
        self.id = id
        self.name = module_name
        self.type_number = type_number
        self.type_name = type_name
        self.port = port
        self.address = address


    def _register_in_WRH(self, device_id, device_token):
        (status, response_content) = W.add_module(device_id, device_token, self.name, self.type_number)
        if status == W.Response.STATUS_OK:
            print "Success! You module has been registered."
            self.token = response_content
        else:
            print "There was an error tying to register module."
            print "***Error code: " + str(status)
            print "***Error message: " + str(response_content)


    @abc.abstractmethod
    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """


    @abc.abstractmethod
    def get_measurement(self):
        """
        Returns data measured by this module.
        """

    @abs.abstractmethod
    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """


    @abs.abstractmethod
    def get_type_nymber_and_name(self):
        """
        Returns module type number and short name.
        """


    @abc.abstractmethod
    def run_registration_procedure(self, device_id, device_token):
        """
        Runs interactive procedure to register new module.
        """
        print "*** Registering new " + str(self.type_name) + " module ***"
        self.name = raw_input("Module name: ")
        # This method ends here because every module should have different
        # parameters descriptions


    @abc.abstractmethod
    def start_work(self, configuration_file_line):
        """
        Starts working procedure.
        """
