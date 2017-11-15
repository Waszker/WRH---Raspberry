import datetime
import os
import re
import signal
import sys
import time

from google_drive.google_drive import GoogleDriveManager
from utils.decorators import in_thread
from utils.io import log
from utils.io import non_empty_input as ninput
from utils.io import non_empty_positive_numeric_input as iinput
from wrh_engine import module_base as base_module


class GoogleDriveUploader(base_module.Module):
    """
    This WRH module takes care of uploading files that appear in its "upload" folder.
    """
    TYPE_NAME = "GOOGLE DRIVE UPLOADER"
    UPLOAD_FOLDER = "/tmp/google_drive_upload"
    UPLOAD_DRIVE_FOLDER = "WRH UPLOADS"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);([1-9][0-9]{0,9});(.+)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.last_upload = self.drive = self.html_repr = None

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param configuration_line:
        :return:
        """
        checker = re.compile(GoogleDriveUploader.CONFIGURATION_LINE_PATTERN)
        return checker.match(configuration_line) is not None

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.google_drive_uploader.google_drive_uploader"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        return "%i;%s;%i;%s" % (self.id, self.name, self.port, self.api_location)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(self.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.port = int(matches.group(3))
        self.api_location = str(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module.
        Google Uploader returns the date of last upload.
        """
        return self.last_upload

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Google Drive Uploader uploads files and media to online storage"

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.port = iinput("Please input port on which this module will be listening for commands: ")
        self.api_location = ninput("Please input filesystem path to GoogleAPI key: ")
        self.drive = GoogleDriveManager(self.api_location, self.id)

    def edit(self):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        log('Please note that changes other than name will always succeed')
        new_name = raw_input('New module\'s name: ')
        new_port = raw_input("Please input new port on which this module will be listening for commands: ")
        new_api_location = raw_input("Please input new GoogleAPI key location: ")

        if new_port: self.port = new_port
        if new_name: self.name = new_name
        if new_api_location:
            self.api_location = new_api_location
            self.drive = GoogleDriveManager(self.api_location, self.id)

    def start_work(self):
        """
        Starts working procedure.
        """
        if not os.path.exists(self.UPLOAD_FOLDER):
            os.makedirs(self.UPLOAD_FOLDER)
        base_module.Module.start_work(self)
        self._uploader_thread()

        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        if not self.html_repr:
            with open('modules/google_drive_uploader/html/repr.html', 'r') as f:
                html = f.read()
                self.html_repr = html.format(id=self.id, name=self.name, port=self.port)
        return self.html_repr

    @in_thread
    def _uploader_thread(self):
        """
        Check for possible scenario execution each minute.
        """

        @in_thread
        def upload_files():
            if self.drive is None: self.drive = GoogleDriveManager(self.api_location, self.id)
            drive_folder = "%s - %s" % (self.UPLOAD_DRIVE_FOLDER, self.name)
            if self.drive.check_if_exists(drive_folder) is False:
                self.drive.create_folder(drive_folder)
            for f in os.listdir(self.UPLOAD_FOLDER):
                if self.drive.upload_image(f, self.UPLOAD_FOLDER + os.sep + f, drive_folder):
                    os.remove(self.UPLOAD_FOLDER + os.sep + f)

        while True:
            upload_files()
            self.last_upload = datetime.datetime.now()
            time.sleep(15 * 60)

    def _react_to_connection(self, connection, _):
        """
        Generally respond to incoming connection.
        Maybe send some information about current module state?
        """
        connection.send("Last upload done {} minutes ago".format(
            int((datetime.datetime.now() - self.last_upload).total_seconds() / 60)
            if self.last_upload is not None else "..."))


if __name__ == "__main__":
    log('Google Drive Uploader module: started.')
    conf_line = sys.argv[1]

    uploader = GoogleDriveUploader(conf_line)
    uploader.start_work()
