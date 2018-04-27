import datetime
import os
import re
import signal
import sys
import time

from modules.google_drive_uploader.google_drive.google_drive import GoogleDriveManager
from utils.decorators import in_thread, log_exceptions
from utils.io import log, Color, wrh_input
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
        self.last_upload = self.drive = self.api_location = None
        base_module.Module.__init__(self, configuration_file_line)

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python3.6", "-m", "modules.google_drive_uploader.google_drive_uploader"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        values = (self.id, self.name, self.port, self.api_location)
        return ('{};' * len(values))[:-1].format(*values)

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
        self.name = wrh_input(message='New module\'s name: ', allowed_empty=True) or self.name
        self.port = iinput("Please input new port on which this module will be listening for commands: ",
                           allowed_empty=True) or self.port
        new_api_location = wrh_input(message="Please input new GoogleAPI key location: ", allowed_empty=True)
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
    @log_exceptions()
    def _uploader_thread(self):
        """
        Check for possible scenario execution each minute.
        """

        @in_thread
        @log_exceptions()
        def upload_files():
            if self.drive is None:
                self.drive = GoogleDriveManager(self.api_location, self.id)
            drive_folder = "%s - %s" % (self.UPLOAD_DRIVE_FOLDER, self.name)
            if self.drive.check_if_exists(drive_folder) is False:
                self.drive.create_folder(drive_folder)
            for f in os.listdir(self.UPLOAD_FOLDER):
                if self.drive.upload_image(f, self.UPLOAD_FOLDER + os.sep + f, drive_folder):
                    os.remove(self.UPLOAD_FOLDER + os.sep + f)
                    self.last_upload = datetime.datetime.now()

        while True:
            upload_files()
            time.sleep(15 * 60)

    def _react_to_connection(self, connection, _):
        """
        Generally respond to incoming connection.
        Maybe send some information about current module state?
        """
        connection.send("Last successful upload done {} minutes ago".format(
            int((datetime.datetime.now() - self.last_upload).total_seconds() / 60)
            if self.last_upload is not None else "..."
        ).encode('utf-8'))


if __name__ == "__main__":
    try:
        log('Google Drive Uploader module: started.')
        conf_line = sys.argv[1]

        uploader = GoogleDriveUploader(conf_line)
        uploader.start_work()
    except Exception as e:
        log(e, Color.EXCEPTION)
