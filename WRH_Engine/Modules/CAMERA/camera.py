#!/bin/python2.7
from WRH_Engine.Configuration import configuration as C
import sys
import os
import subprocess
import signal

def signal_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    conf_line = sys.argv[2]
    camera = C.get_module_entry_data(conf_line)
    device_name = camera.gpio
    port = camera.address

    os.environ['LD_LIBRARY_PATH'] = '/usr/lib'
    command = ["/bin/mjpg_streamer",  "-i", "input_uvc.so -n -q 50 -f 1 -d " + str(device_name),
               "-o", "output_http.so -p " + port + " -c login:password"]
    print command
    p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = os.environ)
    for line in p.stderr.readlines():
        print line
    p.wait();
