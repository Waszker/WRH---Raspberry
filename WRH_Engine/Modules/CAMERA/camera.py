#!/bin/python2.7
from WRH_Engine.Configuration import configuration as C
from WRH_Engine.Utils import utils as U
import sys
import os
import subprocess
import signal
import time as t
import threading
import requests

def _start_stunnel(camera):
    filename = "/tmp/stunnel" + str(camera.id) + ".conf"
    with open(filename, "w") as f:
        f.write("cert=.stunnel_config/cert.pem\n");
        f.write("key=.stunnel_config/key.pem\n");
        f.write("sslVersion = all\n")
        f.write("debug = 7\n\n")
        f.write("[https]\n")
        f.write("client = no\n")
        f.write("accept = 1" + str(camera.address) + "\n")
        f.write("connect = 127.0.0.1:" + str(camera.address))
    command = ["/usr/bin/stunnel", filename]
    p = subprocess.Popen(command)
    p.wait()


def _snapshot_thread(camera, login, password):
    port = camera.address;

    while True:
        t.sleep(5)
        image = get_camera_snapshot(port, login, password)
        U.write_measurement(camera.type, camera.id, image)
        U.add_measurement("test");


def _signal_handler(signal, frame):
    command = ["/usr/bin/killall", "stunnel"]
    p = subprocess.Popen(command)
    p.wait()
    sys.exit(0)


def _start_camera_thread(camera):
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib'
    command = ["/bin/mjpg_streamer",  "-i", "input_uvc.so -n -q 50 -f 1 -d " + str(camera.gpio),
               "-o", "output_http.so -p " + camera.address + " -c login:password"]
    print(command)

    # Preparing thread and subprocess
    thread1 = threading.Thread(target = _snapshot_thread, args = (camera, 'login', 'password'))
    thread2 = threading.Thread(target = _start_stunnel, args = (camera,))
    p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = os.environ)
    thread1.daemon = thread2.daemon = True
    thread1.start()
    thread2.start()

    return p


def get_camera_snapshot(port, login, password):
    r = requests.get("http://localhost:" + str(port) + "?action=snapshot",
                     auth=(str(login), str(password)))
    return r.content


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    conf_line = sys.argv[2]

    camera = C.get_module_entry_data(conf_line)
    process = _start_camera_thread(camera)

    # Await some response from subprocess
    for line in process.stderr.readlines():
        print(line),
    process.wait();
