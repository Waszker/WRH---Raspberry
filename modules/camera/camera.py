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
import datetime

import requests
from wrh_engine import module_base as base_module
from utils.processes import *
from utils.io import *
from utils.decorators import in_thread

ninput = non_empty_input
iinput = non_empty_positive_numeric_input


class CameraModule(base_module.Module):
    """
    This class works with USB webcams complying with V4L2.
    It takes snapshots from those cameras as well as provides streaming options
    via mjpg_streamer (mjpg_streamer has to be installed to work).
    """
    TYPE_NAME = "USB WEBCAM"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);(.+?);(.+?);(.*?);(.*)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.mjpeg_streamer, self.stunnel = None, None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param configuration_line:
        :return:
        """
        checker = re.compile(CameraModule.CONFIGURATION_LINE_PATTERN)
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
        return '%s;%s;%s;%s;%s;%s' % tuple(map(str, (self.id, self.name, self.gpio, self.port,
                                                     self.login, self.password)))

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(CameraModule.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.gpio = matches.group(3)
        self.port = matches.group(4)
        self.login = matches.group(5)
        self.password = matches.group(6)

    def get_measurement(self):
        """
        Returns base64 encoded string containing image taken from connected USB camera.
        None if the image capture failed.
        """
        try:
            r = requests.get("http://localhost:" + str(self.port) + "?action=snapshot",
                             auth=(str(self.login), str(self.password)))
            image = base64.b64encode(r.content)
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            image = None

        return image

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "USB webcam V4L2 compatible. This module supports taking snapshots as well as " \
               "http streaming using mjpg_streamer."

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.gpio = ninput("Please input name of the webcam device (usually /dev/video#, # is the specific number): ")
        self.port = iinput("Please input port on which streamed images can be accessed: ")
        self.login = raw_input("Please input login used to access the video stream (press ENTER if none): ")
        self.password = ninput("Please input password used to access the video stream: ") if self.login else ""

    def edit(self):
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
        new_port = raw_input("Please input new port on which streamed images can be accessed: ")
        new_login = raw_input("Please input new login used to access the video stream: ")
        new_password = raw_input("Please input new password used to access the video stream: ")

        if new_gpio: self.gpio = new_gpio
        if new_port: self.port = new_port
        if new_login: self.login = new_login
        if new_password: self.password = new_password
        if new_name: self.name = new_name

    def start_work(self):
        """
        Starts working procedure.
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        self._snapshot_thread()
        self._mjpeg_streamer_thread()
        self._stunnel_thread()

        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        This will be img object used for live view.
        :param website_host_address: ip address of server
        :return:
        """
        return "<div class=\"card-panel\"><h5>" + self.name + "</h5> \
            <img style=\"width: 50%\" src = \"http://" + website_host_address + ":" + self.port + "/?action=stream\" /></div>"

    def _get_streaming_address(self):
        address = "https://"
        address += str(urlopen('http://ip.42.pl/raw').read())
        address += ":1" + str(self.port)
        return address

    @in_thread
    def _snapshot_thread(self):
        """
        Thread taking measurements in specified interval.
        """
        while True:
            t.sleep(15 * 60)
            image = self.get_measurement()
            if image is not None:
                pass
                # TODO: Change upload folder!
                # with open("/tmp/google_drive_upload/" + str(datetime.datetime.now()) + ".jpg", 'wb') as img:
                #     img.write(base64.decodestring(image))

    @in_thread
    def _stunnel_thread(self):
        filename = "/tmp/stunnel" + str(self.id) + ".conf"
        with open(filename, "w") as f:
            f.write("cert=.stunnel_config/cert.pem\n")
            f.write("key=.stunnel_config/key.pem\n")
            f.write("sslVersion = all\n")
            f.write("debug = 7\n\n")
            f.write("[https]\n")
            f.write("client = no\n")
            f.write("accept = 1" + str(self.port) + "\n")
            f.write("connect = 127.0.0.1:" + str(self.port))
        command = ["/usr/bin/stunnel", filename]
        self.stunnel = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_process_errors(self.stunnel)

    @in_thread
    def _mjpeg_streamer_thread(self):
        password_subcommand = "" if not self.password else " -c " + self.login + ":" + self.password
        os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib/'
        command = ["/usr/local/bin/mjpg_streamer", "-i", "input_uvc.so -n -q 50 -f 30 -d " + str(self.gpio),
                   "-o", "output_http.so -p " + self.port + password_subcommand]
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
