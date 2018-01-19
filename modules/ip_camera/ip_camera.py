import base64
import datetime
import os
import re
import signal
import subprocess
import sys
import time as t

import requests

from utils.decorators import in_thread
from utils.io import non_empty_input, non_empty_positive_numeric_input, log
from utils.processes import print_process_errors, end_process
from wrh_engine import module_base as base_module

ninput = non_empty_input
iinput = non_empty_positive_numeric_input


class IpCameraModule(base_module.Module):
    """
    This class works with USB webcams complying with V4L2.
    It takes snapshots from those cameras as well as provides streaming options
    via mjpg_streamer (mjpg_streamer has to be installed to work).
    """
    TYPE_NAME = "IP CAMERA"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);(.+?);(.+?);(.*)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.camera_address = self.camera_port = self.socat_process = None

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
        values = (self.id, self.name, self.camera_address, self.camera_port, self.port)
        return ('{};' * len(values))[:-1].format(*values)

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
        Returns base64 encoded string containing image taken from connected USB camera.
        None if the image capture failed.
        TODO: Currently only IP cameras using mjpg-streamer are supported!
        """
        try:
            r = requests.get("http://localhost:" + str(self.port) + "?action=snapshot")
            image = base64.b64encode(r.content)
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            image = None

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
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        self.name = raw_input('New module\'s name: ') or self.name
        self.camera_address = raw_input("Please input new IP address of camera: ") or self.camera_address
        self.camera_port = raw_input("Please input new port on which IP camera can be accessed: ") or self.camera_port
        self.port = iinput("Please input new port on which streamed images can be accessed: ",
                           allowed_empty=True) or self.port

    def start_work(self):
        """
        Starts working procedure.
        """
        signal.signal(signal.SIGINT, self._sigint_handler)
        self._socat_thread()
        self._snapshot_thread()

        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        This will be img object used for live view.
        :param website_host_address: ip camera_address of server
        :return:
        """
        return "<div class=\"card-panel\"><h5>" + self.name + "</h5> \
            <img style=\"width: 50%\" src = \"http://" + website_host_address + ":" + self.port + "/?action=stream\" /></div>"

    @in_thread
    def _socat_thread(self):
        command = ["socat", "TCP4-LISTEN:%s,fork" % str(self.port),
                   "TCP4:%s:%s" % (str(self.camera_address), str(self.camera_port))]
        self.socat_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ)
        print_process_errors(self.socat_process)

    @in_thread
    def _snapshot_thread(self):
        """
        Thread taking measurements in specified interval.
        """
        while True:
            t.sleep(15 * 60)
            image = self.get_measurement()
            # TODO: Change upload folder!
            if image is not None:
                try:
                    with open("/tmp/google_drive_upload/" + str(datetime.datetime.now()) + ".jpg", 'wb') as img:
                        img.write(base64.decodestring(image))
                except IOError:
                    pass

    def _sigint_handler(self, *_):
        self._should_end = True
        if self.socat_process is not None:
            end_process(self.socat_process, 5, True)


if __name__ == "__main__":
    log('IP Camera: started.')
    conf_line = sys.argv[1]

    camera = IpCameraModule(conf_line)
    camera.start_work()
