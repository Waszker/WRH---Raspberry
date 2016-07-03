import os
import signal
import subprocess
import WRH_Engine.Configuration.configuration as c
import WRH_Engine.Utils.dynamic_loader as d


class Overlord:
    """
    Overlord program takes care of all subprocesses registered in WRH.
    """
    processes = []

    def __init__(self, configuration_filename):
        with open(configuration_filename, 'r') as f:
            modules_classes = d.scan_and_return_module_classes("WRH_Engine/Modules/")
            (_, modules) = c.parse_configuration_file(f, modules_classes)
            self.modules = modules
        signal.signal(signal.SIGINT, _siginit_handler)
        signal.signal(signal.SIGCHLD, _sigchld_handler)

    def start_work(self):
        """
        Starts overlord work which consists of starting subprocesses, and controling
        their lifetime.
        :return:
        """
        for m in self.modules:
            p = subprocess.Popen("") # TODO: Provide command
            Overlord.processes.append(p.pid)




def _siginit_handler(signal, frame):
    print 'OVERLORD: SIGINT signal caught'
    for p in Overlord.processes:
        os.kill(p, signal.SIGINT)


def _sigchld_handler(signal, frame):
