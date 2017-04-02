#!/bin/python2.7
####################################################
# Set of functions to work with camera module
# connected to Raspberry Pi device.
####################################################

import base64
import os
import re
import signal
import subprocess
import sys
import threading
import time as t
from urllib2 import urlopen

import requests
from wrh_engine import module_base as base_module
from utils.io import IO

ninput = IO.non_empty_input
iinput = IO.non_empty_numeric_input

# Those two variables will be used by sigint handler
# CAUTION: Those are global variables - don't use them unless you're sure what you're doing!
stunnel_pid = None
mjpg_streamer_pid = None


class CameraModule(base_module.Module):
    """
    This class works with USB webcams complying with V4L2.
    It takes snapshots from those cameras as well as provides streaming options
    via mjpg_streamer (mjpg_streamer has to be installed to work).
    """
    type_number = 2
    type_name = "USB WEBCAM"
    configuration_line_pattern = str(type_number) + ";([0-9]{1,9});(.+?);(.+?);(.+?);(.*?);(.*)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = CameraModule.type_number
        self.type_name = CameraModule.type_name

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=2 ; ID=INT ; NAME=STRING ; GPIO=STRING ; ADDRESS=STRING ; LOGIN=STRING ; PASSWORD=STRING
        checker = re.compile(CameraModule.configuration_line_pattern)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.camera.camera"]

    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """
        return str(self.type_number) + ";" + str(
            self.id) + ";" + self.name + ";" + self.gpio + ";" + self.address + ";" + self.login + ";" + self.password

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(CameraModule.configuration_line_pattern, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = matches.group(3)
        self.address = matches.group(4)
        self.login = matches.group(5)
        self.password = matches.group(6)

    def get_measurement(self):
        """
        Returns base64 encoded string containing image taken from connected USB camera.
        """
        r = requests.get("http://localhost:" + str(self.address) + "?action=snapshot",
                         auth=(str(self.login), str(self.password)))
        image = base64.b64encode(r.content)
        return image

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "USB webcam V4L2 compatible. This module supports taking snapshots as well as " \
               "http streaming using mjpg_streamer."

    def get_type_number_and_name(self):
        """
        Returns module type number and short name (as two separate variables)
        """
        return self.type_number, self.type_name

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.gpio = ninput("Please input name of the webcam device (usually /dev/video#, # is the specific number): ")
        self.address = iinput("Please input port on which streamed images can be accessed: ")
        self.login = raw_input("Please input login used to access the video stream (press ENTER if none): ")
        if self.login:
            self.password = ninput("Please input password used to access the video stream: ")
        else:
            self.password = ""

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_gpio = raw_input(
            "Please input new name of the webcam device (usually /dev/video# where # is the specific number): ")
        new_address = raw_input("Please input new port on which streamed images can be accessed: ")
        new_login = raw_input("Please input new login used to access the video stream: ")
        new_password = raw_input("Please input new password used to access the video stream: ")

        if new_gpio: self.gpio = new_gpio
        if new_address: self.address = new_address
        if new_login: self.login = new_login
        if new_password: self.password = new_password
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        return self._start_camera_thread()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        This will be img object used for live view.
        :param website_host_address: ip address of server
        :return:
        """
        return "<div class=\"card-panel\"><h5>" + self.name + "</h5> \
            <img style=\"width: 50%\" src = \"http://" + website_host_address + ":" + self.address + "/?action=stream\" /></div>"

    def _start_stunnel(self):
        global stunnel_pid
        filename = "/tmp/stunnel" + str(self.id) + ".conf"
        with open(filename, "w") as f:
            f.write("cert=.stunnel_config/cert.pem\n")
            f.write("key=.stunnel_config/key.pem\n")
            f.write("sslVersion = all\n")
            f.write("debug = 7\n\n")
            f.write("[https]\n")
            f.write("client = no\n")
            f.write("accept = 1" + str(self.address) + "\n")
            f.write("connect = 127.0.0.1:" + str(self.address))
        command = ["/usr/bin/stunnel", filename]
        p = subprocess.Popen(command)
        stunnel_pid = p.pid
        p.wait()

    def _get_streaming_address(self):
        address = "https://"
        address += str(urlopen('http://ip.42.pl/raw').read())
        address += ":1" + str(self.address)
        return address

    def _snapshot_thread(self):
        """
        Thread taking measurements in specified interval.
        """
        while True:
            t.sleep(60 * 60)
            image = self.get_measurement()
            # TODO: Image could be saved somewhere?
            # u.manage_measurement(device_id, device_token, self.id,
            #                     self.type_number, image, self._get_streaming_address())

    def _start_camera_thread(self):
        global mjpg_streamer_pid
        password_subcommand = ""
        if self.password != "":
            password_subcommand = " -c " + self.login + ":" + self.password

        os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib/'
        # os.environ['LD_PRELOAD'] = '/usr/lib/uv4l/uv4lext/armv6l/libuv4lext.so'
        command = ["/usr/local/bin/mjpg_streamer", "-i", "input_uvc.so -n -q 50 -f 30 -d " + str(self.gpio),
                   "-o", "output_http.so -p " + self.address + password_subcommand]

        # Preparing thread and subprocess
        thread1 = threading.Thread(target=self._snapshot_thread, args=())
        thread2 = threading.Thread(target=self._start_stunnel, args=())
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)
        mjpg_streamer_pid = p.pid
        thread1.daemon = thread2.daemon = True
        thread1.start()
        thread2.start()

        return p


def _try_to_kill_process(pid):
    try:
        os.kill(pid, signal.SIGINT)
    except OSError:
        pass


def _signal_handler(*_):
    global stunnel_pid, mjpg_streamer_pid
    if stunnel_pid is not None: _try_to_kill_process(stunnel_pid)
    if mjpg_streamer_pid is not None: _try_to_kill_process(mjpg_streamer_pid)
    sys.exit(0)


if __name__ == "__main__":
    print 'Camera: started.'
    signal.signal(signal.SIGINT, _signal_handler)
    conf_line = sys.argv[1]

    camera = CameraModule(conf_line)
    process = camera.start_work()

    # Await some response from subprocess
    for line in process.stderr.readlines():
        print(line),
    process.wait()
