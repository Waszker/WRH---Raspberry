import subprocess
from utils.processes import *


class Overlord:
    """
    Class taking care of running modules, each in as a separate subprocess.
    It also resurrects them in case of their failure and maintains their lifetime in case of whole system shutdown.
    """

    def __init__(self, configuration_parser):
        """
        Creates instance of Overlord class that prepares commands for starting modules.
        :param configuration_parser: parser that returns information about modules registered for this particular system
        """
        tornado_command = ["/usr/bin/python2.7", "-m", "wrh_engine.tornado.server",
                           configuration_parser.configuration_filename]
        self.is_ending = False
        self.modules = configuration_parser.get_installed_modules()
        self.commands = [module.get_starting_command() for module in self.modules]
        [command.append(self.modules[i].get_configuration_line()) for i, command in enumerate(self.commands)]
        self.commands = [tornado_command] + self.commands
        self.processes = []

    def start_modules(self):
        """
        Starts module processes.
        """
        self.processes = [subprocess.Popen(command) for command in self.commands]

    def handle_signal(self, signal_type):
        """
        Performs actions based on received signal.
        :param signal_type: received signal
        """
        if signal_type == signal.SIGINT: self._sigint_handler()
        if signal_type == signal.SIGCHLD: self._sigchld_handler()

    def _sigint_handler(self, *_):
        log('OVERLORD: SIGINT signal caught')
        [end_process(process, 5) for process in self.processes]

    def _sigchld_handler(self, *_):
        for i in xrange(len(self.processes)):
            if self.processes[i].poll() is None: continue
            log('OVERLORD resurrecting ' + str(self.commands[i]))
            self.processes[i] = subprocess.Popen(self.commands[i])