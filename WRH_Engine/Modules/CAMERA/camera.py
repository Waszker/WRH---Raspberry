#!/bin/python2.7
from WRH_Engine.Configuration import configuration as C
import sys
import os
import subprocess

if __name__ == "__main__":
    print sys.argv[1]
    conf_line = sys.argv[1]
    camera = C.get_module_entry_data(conf_line)

    os.environ['LD_LIBRARY_PATH'] = '/usr/lib'
    print 'Starting mjpeg-streamer'
    command = ["/bin/mjpg_streamer",  "-i", "input_uvc.so -n -q 50 -f 1", "-o", "output_http.so -p 8080 -c login:password"]
    p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = os.environ)
    for line in p.stdout.readlines():
        print line
    p.wait();
    print 'Ended mjpeg-streamer'
