#!/bin/python2.7
from WRH_Engine.Configuration import configuration as C
import sys
import os
import subprocess
import signal
import time as t
import threading
import requests

def get_camera_snapshot(port, login, password):
    r = requests.get("http://localhost:" + str(port) + "?action=snapshot",
                     auth=(str(login), str(password)))
    return r.content


def _snapshot_thread(port, login, password):
    while True:
        t.sleep(5)
        image = get_camera_snapshot(port, login, password)
        with open("snapshot.jpg", "w") as f:
            f.write(image)

def _signal_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    conf_line = sys.argv[1]
    camera = C.get_module_entry_data(conf_line)
    device_name = camera.gpio
    port = camera.address

    os.environ['LD_LIBRARY_PATH'] = '/usr/lib'
    command = ["/bin/mjpg_streamer",  "-i", "input_uvc.so -n -q 50 -f 1 -d " + str(device_name),
               "-o", "output_http.so -p " + port + " -c login:password"]
    print command

    # Preparing thread and subprocess
    thread = threading.Thread(target = _snapshot_thread, args = (port,'login','password'))
    p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = os.environ)

    # Start thread as daemon
    thread.daemon = True
    thread.start()

    # Await some response from subprocess
    for line in p.stderr.readlines():
        print line,
    p.wait();
