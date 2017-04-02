from abc import abstractmethod


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

    @staticmethod
    @abstractmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param configuration_line:
        :return: boolean
        """

    @staticmethod
    @abstractmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """

    @abstractmethod
    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """

    @abstractmethod
    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """

    @abstractmethod
    def get_measurement(self):
        """
        Returns data measured by this module.
        """

    @abstractmethod
    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """

    @abstractmethod
    def get_type_number_and_name(self):
        """
        Returns module type number and short name.
        """

    @abstractmethod
    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        print "*** Registering new " + str(self.type_name) + " module ***"
        self.id = new_id
        self.name = raw_input("Module name: ")
        # This method ends here because every module should have different
        # parameters descriptions

    @abstractmethod
    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        """

    @abstractmethod
    def start_work(self):
        """
        Starts working procedure.
        """

    @abstractmethod
    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        Tornado server will be responsible for pasting it.
        :param website_host_address: ip address of server
        :return:
        """
