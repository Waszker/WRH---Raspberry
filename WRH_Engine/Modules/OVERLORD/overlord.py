import os
import sys
import signal
import subprocess
import psutil
import WRH_Engine.Configuration.configuration as c
import WRH_Engine.Utils.dynamic_loader as d

__CONFIG_FILE__ = '.wrh.config'


class Overlord:
    """
    Overlord program takes care of all subprocesses registered in WRH.
    """
    processes = []
    commands = []

    def __init__(self, configuration_filename):
        with open(configuration_filename, 'r') as f:
            modules_classes = d.scan_and_return_module_classes("WRH_Engine/Modules/")
            (_, modules) = c.parse_configuration_file(f, modules_classes)
            self.modules = modules
            self.configuration_lines = []
            f.seek(0)
            for line in f: self.configuration_lines.append(line)
        signal.signal(signal.SIGINT, _siginit_handler)
        signal.signal(signal.SIGCHLD, _sigchld_handler)

    def start_work(self):
        """
        Starts overlord work which consists of starting subprocesses, and controling
        their lifetime.
        :return:
        """
        tornado_command = ["/usr/bin/python2.7", "-m", "WRH_Engine.Modules.TORNADO.server", __CONFIG_FILE__]
        Overlord.processes.append(subprocess.Popen(tornado_command))
        Overlord.commands.append(tornado_command)

        index = 1
        for m in self.modules:
            command = m.get_starting_command()
            command.append(self.configuration_lines[0])
            command.append(self.configuration_lines[index])
            process = subprocess.Popen(command)
            Overlord.processes.append(process)
            Overlord.commands.append(command)
            index += 1


def _siginit_handler(_, __):
    print 'OVERLORD: SIGINT signal caught'
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    for p in Overlord.processes:
        os.kill(p.pid, signal.SIGINT)
    sys.exit(0)


def _sigchld_handler(_, __):
    for i in range(0, len(Overlord.processes)):
        process, command = Overlord.processes[i], Overlord.commands[i]
        process_info = psutil.Process(process.pid)
        if process_info.status() == psutil.STATUS_ZOMBIE:
            process.wait()
            Overlord.processes[i] = subprocess.Popen(command)


if __name__ == "__main__":
    print 'Overlord: started.'
    signal.signal(signal.SIGINT, _siginit_handler)
    signal.signal(signal.SIGCHLD, _sigchld_handler)

    overlord = Overlord(__CONFIG_FILE__)
    overlord.start_work()
    while True:
        signal.pause()
