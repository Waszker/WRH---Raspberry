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
    TYPE_NUMBER = -1
    TYPE_NAME = "AbstractModule"

    def __init__(self, configuration_file_line=None):
        """
        Creates instance of a specific module class from the information
        provided in configuration line.
        """
        self.id = self.name = self.gpio = self.port = None
        self._should_end, self._socket = False, None
        if configuration_file_line is not None:
            self._parse_configuration_line(configuration_file_line)

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
    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        print "*** Registering new " + str(Module.TYPE_NAME) + " module ***"
        self.id = new_id
        self.name = raw_input("Module name: ")
        # This method ends here because every module should have different
        # parameters descriptions

    @abstractmethod
    def edit(self):
        """
        Runs interactive procedure to edit module.
        """
        pass

    @abstractmethod
    def start_work(self):
        """
        Starts working procedure.
        Implementation already present in this class creates new web thread that takes care of listening for incoming
        connections on the port specified during module registration. Every module instance should have self.port
        variable defined, but probably not every module will use it the same way so call this method only if web thread
        is needed.
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
                                       (ERROR_CODE, ERROR_MESSAGE) = " % (Module.TYPE_NAME, self.name))
        if bind_result is True:
            log("%s %s started listening" % (Module.TYPE_NAME, self.name))
            self.socket.listen(10)
            await_connection(self.socket, self._start_new_connection_thread, predicate=predicate)

    def _start_new_connection_thread(self, connection, client_address):
        thread = threading.Thread(target=self._react_to_connection, args=(connection, client_address))
        thread.daemon = True
        thread.start()
        thread.join()

    def _react_to_connection(self, connection, client_address):
        """
        Generally respond to incoming connection.
        Maybe send some information about current module state?
        """
        pass

    def _sigint_handler(self, *_):
        self._should_end = True
        if self.socket is not None:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
