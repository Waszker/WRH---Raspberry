import time
import subprocess
import signal
from utils.io import IO, Color

log = IO.log


class Overlord:
    """
    Class taking care of running modules, each in as a separate subprocess.
    It also resurrects them in case of their failure and maintains their lifetime in case of whole system shutdown.
    """

    def __init__(self, configuration_parser):
        tornado_command = ["/usr/bin/python2.7", "-m", "wrh_engine.tornado.server",
                           configuration_parser.configuration_filename]
        self.is_ending = False
        self.modules = configuration_parser.get_installed_modules()
        self.commands = [module.get_starting_command() for module in self.modules]
        [command.append(self.modules[i].get_configuration_line()) for i, command in enumerate(self.commands)]
        self.commands = [tornado_command] + self.commands
        self.processes = []

    def start_and_maintain(self):
        """

        :return:
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        signal.signal(signal.SIGCHLD, self._sigchld_handler)
        self.processes = [subprocess.Popen(command) for command in self.commands]
        while self.is_ending is False:
            signal.pause()

    def _sigint_handler(self, *_):
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        self.is_ending = True
        log('OVERLORD: SIGINT signal caught')
        [Overlord._end_process(process) for process in self.processes]

    def _sigchld_handler(self, *_):
        for i in xrange(len(self.processes)):
            if self.processes[i].poll() is None: continue
            log('OVERLORD resurrecting ' + str(self.commands[i]))
            self.processes[i] = subprocess.Popen(self.commands[i])

    @staticmethod
    def _end_process(process):
        try:
            log('Sending SIGINT to process: ' + str(process.pid))
            process.send_signal(signal.SIGINT)
            timeout, retries = 1, 5
            while process.poll() is None and retries > 0:
                time.sleep(timeout)
                retries -= 1
            if process.poll() is None:
                log('Process ' + str(process.pid) + " not responding. Sending SIGTERM.", Color.WARNING)
                process.terminate()
        except OSError:
            pass
