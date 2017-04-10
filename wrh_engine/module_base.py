import signal
import socket
from abc import abstractmethod
import threading
from utils.io import log
from utils.sockets import await_connection, wait_bind_socket


class Module:
    """
    Abstract base class for modules used in WRH.
    """
    type_number = -1
    type_name = "AbstractModule"

    def __init__(self, configuration_file_line=None):
        """
        Creates instance of a specific module class from the information
        provided in configuration line.
        """
        if configuration_file_line is not None:
            self._parse_configuration_line(configuration_file_line)
        else:
            self._set_basic_information(None, None, None, None, None, None)

        self._should_end, self._socket = False, None

    def _set_basic_information(self, module_id, module_name, type_number, type_name, gpio, port):
        """
        Sets basic information needed for every module in WRH.
        """
        self.id = module_id
        self.name = module_name
        self.type_number = type_number
        self.type_name = type_name
        self.gpio = gpio
        self.port = port

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
        pass

    @abstractmethod
    def start_work(self):
        """
        Starts working procedure.
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        web_service_thread = threading.Thread(target=self._web_service_thread)
        web_service_thread.daemon = False
        web_service_thread.start()

    @abstractmethod
    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        Tornado server will be responsible for pasting it.
        :param website_host_address: ip address of server
        :return:
        """
        pass

    def _web_service_thread(self):
        predicate = (lambda: self._should_end is False)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_result = wait_bind_socket(self.socket, '', self.port, 10, predicate=predicate,
                                       error_message="%s %s port bind failed. \
                                       (ERROR_CODE, ERROR_MESSAGE) = " % (Module.type_name, self.name))
        if bind_result is True:
            log("%s %s started listening" % (self.type_name, self.name))
            self.socket.listen(10)
            await_connection(self.socket, self._react_to_connection, predicate=predicate)

    def _react_to_connection(self, connection, client_address):
        """
        Send some information about current module state.
        """
        pass

    def _sigint_handler(self, *_):
        self._should_end = True
        if self.socket is not None:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
