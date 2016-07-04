import os
import sys
import signal
import subprocess
import psutil
from sets import Set
import WRH_Engine.Configuration.configuration as c
import WRH_Engine.Utils.dynamic_loader as d


class Overlord:
    """
    Overlord program takes care of all subprocesses registered in WRH.
    """
    processes = Set()

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
        tornado_command = "/usr/bin/python2.7 -m WRH_Engine.Modules.TORNADO.server"
        Overlord.processes.add((subprocess.Popen(tornado_command), tornado_command))

        for m in self.modules:
            process = subprocess.Popen(m.get_starting_command())
            Overlord.processes.add((process, m.get_starting_command()))


def _siginit_handler(signal, frame):
    print 'OVERLORD: SIGINT signal caught'
    for p in Overlord.processes:
        os.kill(p, signal.SIGINT)
    sys.exit(0)


def _sigchld_handler(signal, frame):
    zombies = Set()
    for (process, command) in Overlord.processes:
        process_info = psutil.Process(process.pid)
        if process_info.status() == psutil.STATUS_ZOMBIE:
            process.wait()
            zombies.add((process, command))
            zombies.add((subprocess.Popen(command), command))
    Overlord.processes = Overlord.processes.symmetric_difference_update(zombies)


if __name__ == "__main__":
    print 'Overlord: started.'
    signal.signal(signal.SIGINT, _siginit_handler)
    signal.signal(signal.SIGCHLD, _sigchld_handler)

    overlord = Overlord('.wrh_config')
    overlord.start_work()
    while True:
        signal.pause()
