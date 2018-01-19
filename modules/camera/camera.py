import base64
import os
import re
import signal
import subprocess
import sys
import time as t
from urllib2 import urlopen

import requests

from utils.decorators import in_thread
from utils.io import non_empty_input, non_empty_positive_numeric_input, log
from utils.processes import print_process_errors, end_process
from wrh_engine import module_base as base_module

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
        self.mjpeg_streamer = self.stunnel = None
        self.login = self.password = ''

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
        values = (self.id, self.name, self.gpio, self.port, self.login, self.password)
        return ('{};' * len(values))[:-1].format(*values)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(CameraModule.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = self.name = self.gpio = self.port = self.login = self.password = matches.groups()

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
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        self.name = raw_input('New module\'s name: ') or self.name
        self.gpio = raw_input("Please input new name of the webcam device"
                              "(usually /dev/video# where # is the specific number): ") or self.gpio
        self.port = iinput("Please input new port on which streamed images can be accessed: ",
                           allowed_empty=True) or self.port
        self.login = raw_input("Please input new login used to access the video stream: ") or self.login
        self.password = raw_input("Please input new password used to access the video stream: ") or self.password

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
    log('Camera: started.')
    conf_line = sys.argv[1]

    camera = CameraModule(conf_line)
    camera.start_work()
