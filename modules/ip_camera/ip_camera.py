#!/bin/python2.7
####################################################
# Set of functions to work with ip camera module
# connected the network with Raspberry Pi device.
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


class IpCameraModule(base_module.Module):
    """
    This class works with USB webcams complying with V4L2.
    It takes snapshots from those cameras as well as provides streaming options
    via mjpg_streamer (mjpg_streamer has to be installed to work).
    """
    TYPE_NUMBER = 9
    TYPE_NAME = "IP CAMERA"
    CONFIGURATION_LINE_PATTERN = str(TYPE_NUMBER) + ";([0-9]{1,9});(.+?);(.+?);(.+?);(.*)$"

    def __init__(self, configuration_file_line=None):
        self.camera_address = self.camera_port = self.socat_process = None
        base_module.Module.__init__(self, configuration_file_line)

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed
        :param configuration_line:
        :return:
        """
        checker = re.compile(IpCameraModule.CONFIGURATION_LINE_PATTERN)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.ip_camera.ip_camera"]

    def get_configuration_line(self):
        """
        Creates module configuration line
        :return: Properly formatted configuration file line
        """
        return '%s;%s;%s;%s;%s;%s' % tuple(map(str, (IpCameraModule.TYPE_NUMBER, self.id, self.name,
                                                     self.camera_address, self.camera_port, self.port)))

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(IpCameraModule.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = matches.group(1)
        self.name = matches.group(2)
        self.camera_address = matches.group(3)
        self.camera_port = matches.group(4)
        self.port = matches.group(5)

    def get_measurement(self):
        """
        Returns base64 encoded string containing image taken from IP camera.
        TODO: Currently only IP cameras using mjpg-streamer are supported!
        """
        r = requests.get("http://localhost:" + str(self.port) + "?action=snapshot")
        image = base64.b64encode(r.content)
        return image

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "This module connects IP camera"

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.camera_address = ninput("Please input IP address of camera: ")
        self.camera_port = ninput("Please input port of IP camera: ")
        self.port = iinput("Please input port on which streamed images can be accessed: ")

    def edit(self):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_camera_address = raw_input("Please input new IP address of camera: ")
        new_camera_port = raw_input("Please input new port on which IP camera can be accessed: ")
        new_port = raw_input("Please input new port on which streamed images can be accessed: ")

        if new_name: self.name = new_name
        if new_camera_address: self.camera_address = new_camera_address
        if new_camera_port: self.camera_port = new_camera_port
        if new_port: self.port = new_port

    def start_work(self):
        """
        Starts working procedure.
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        self._start_camera_threads()

        while self._should_end is False:
            signal.pause()

    def _start_camera_threads(self):
        socat_thread = threading.Thread(target=self._socat_thread, args=())
        snapshot_thread = threading.Thread(target=self._snapshot_thread, args=())
        snapshot_thread.daemon = socat_thread.daemon = True
        snapshot_thread.start()
        socat_thread.start()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        This will be img object used for live view.
        :param website_host_address: ip camera_address of server
        :return:
        """
        return "<div class=\"card-panel\"><h5>" + self.name + "</h5> \
            <img style=\"width: 50%\" src = \"http://" + website_host_address + ":" + self.port + "/?action=stream\" /></div>"

    def _socat_thread(self):
        command = ["sockat", "TCP4-LISTEN:%s,fork" % self.port,
                   "TCP4:%s:%s" % (str(self.camera_address), str(self.camera_port))]
        self.socat_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)
        print_process_errors(self.socat_process)

    def _snapshot_thread(self):
        """
        Thread taking measurements in specified interval.
        """
        while True:
            t.sleep(60 * 60)
            image = self.get_measurement()
            # TODO: Image could be saved somewhere?

    def _sigint_handler(self, *_):
        self._should_end = True
        if self.socat_process is not None:
            end_process(self.socat_process, 5, True)


if __name__ == "__main__":
    print 'IP Camera: started.'
    conf_line = sys.argv[1]

    camera = IpCameraModule(conf_line)
    camera.start_work()
