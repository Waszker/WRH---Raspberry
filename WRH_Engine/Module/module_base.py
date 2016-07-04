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
        else:
            self._set_basic_information(None, None, None, None, None, None)

    def _set_basic_information(self, module_id, module_name, type_number, type_name, gpio, address):
        """
        Sets basic information needed for every module in WRH.
        """
        self.id = module_id
        self.name = module_name
        self.type_number = type_number
        self.type_name = type_name
        self.gpio = gpio
        self.address = address

    def register_in_wrh(self, device_id, device_token):
        """
        Registers module in WRH database.
        :param device_id: id of device module is connected to
        :param device_token: secret device's token
        :return: tuple containing operation status and response content
        """
        (status, response_content) = W.add_module(device_id, device_token, self.name, self.type_number)
        if status == W.Response.STATUS_OK:
            self.id = response_content
        return (status, response_content)

    def update_module_information_in_wrh(self, device_id, device_token, new_name):
        """
        Updates module information in WRH database.
        :param device_id:
        :param device_token:
        :param new_name:
        :return: tuple containing operation status and response content
        """
        (status, response_content) = W.edit_module(device_id, device_token, self.id, new_name)
        if status == W.Response.STATUS_OK:
            self.name = new_name
        return (status, response_content)

    def remove_from_wrh(self, device_id, device_token):
        """
        Remove module in WRH system.
        :param device_id: id of device module is connected to
        :param device_token: secret device's token
        :return: tuple containing operation status and response content
        """
        is_success = False
        return W.remove_module(device_id, device_token, self.id)

    @staticmethod
    @abc.abstractmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param configuration_line:
        :return:
        """

    @staticmethod
    @abc.abstractmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """

    @abc.abstractmethod
    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """

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

    @abc.abstractmethod
    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """

    @abc.abstractmethod
    def get_type_number_and_name(self):
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
    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        """

    @abc.abstractmethod
    def start_work(self, device_id, device_token):
        """
        Starts working procedure.
        """

    @abc.abstractmethod
    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        Tornado server will be responsible for pasting it.
        :param website_host_address: ip address of server
        :return:
        """


class BadConfigurationException(Exception):
    """
    Class for exceptions thrown/raised after configuration file sanity check fails.
    """

    def __init__(self):
        self.message = "Badly formatted configuration line!"
