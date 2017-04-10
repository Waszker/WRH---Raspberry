#!/bin/python2.7
####################################################
# Set of functions to work with camera module
# connected to Raspberry Pi device.
####################################################

import base64
import os
import re
import subprocess
import sys
import threading
import time as t
from urllib2 import urlopen

import requests
from wrh_engine import module_base as base_module
from utils.processes import *
from utils.io import *

ninput = non_empty_input
iinput = non_empty_positive_numeric_input


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
        self.mjpeg_streamer, self.stunnel = None, None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
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
        return '%s;%s;%s;%s;%s;%s;%s' % tuple(map(str, (self.type_number, self.id, self.name,
                                                        self.gpio, self.address, self.login, self.password)))

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
        self.password = ninput("Please input password used to access the video stream: ") if self.login else ""

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
        signal.signal(signal.SIGINT, self._sigint_handler)
        self._start_camera_threads()

        while self._should_end is False:
            signal.pause()

    def _start_camera_threads(self):
        snapshot_thread = threading.Thread(target=self._snapshot_thread, args=())
        mjpeg_thread = threading.Thread(target=self._mjpeg_streamer_thread, args=())
        stunnel_thread = threading.Thread(target=self._stunnel_thread(), args=())
        threads = [snapshot_thread, mjpeg_thread, stunnel_thread]
        for thread in threads:
            thread.daemon = True
            thread.start()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        This will be img object used for live view.
        :param website_host_address: ip address of server
        :return:
        """
        return "<div class=\"card-panel\"><h5>" + self.name + "</h5> \
            <img style=\"width: 50%\" src = \"http://" + website_host_address + ":" + self.address + "/?action=stream\" /></div>"

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

    def _stunnel_thread(self):
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
        self.stunnel = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_process_errors(self.stunnel)

    def _mjpeg_streamer_thread(self):
        password_subcommand = "" if not self.password else " -c " + self.login + ":" + self.password
        os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib/'
        command = ["/usr/local/bin/mjpg_streamer", "-i", "input_uvc.so -n -q 50 -f 30 -d " + str(self.gpio),
                   "-o", "output_http.so -p " + self.address + password_subcommand]
        self.mjpeg_streamer = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)
        print_process_errors(self.mjpeg_streamer)

    def _sigint_handler(self, *_):
        self._should_end = True
        if self.mjpeg_streamer is not None:
            end_process(self.mjpeg_streamer, 5, True)
        if self.stunnel is not None:
            end_process(self.stunnel, 5, True)


if __name__ == "__main__":
    print 'Camera: started.'
    conf_line = sys.argv[1]

    camera = CameraModule(conf_line)
    camera.start_work()
