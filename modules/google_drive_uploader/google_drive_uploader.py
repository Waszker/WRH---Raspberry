import signal
import os
import sys
import re
import threading
import time
import datetime
from wrh_engine import module_base as base_module
from utils.io import non_empty_positive_numeric_input as iinput
from utils.io import non_empty_input as ninput
from utils.io import log, Color
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google_drive.google_drive import GoogleDriveManager


class GoogleDriveUploader(base_module.Module):
    """
    This WRH module takes care of uploading files that appear in its "upload" folder.
    """
    TYPE_NUMBER = 9
    TYPE_NAME = "GOOGLE DRIVE UPLOADER"
    UPLOAD_FOLDER = "/tmp/google_drive_upload"
    UPLOAD_DRIVE_FOLDER = "WRH UPLOADS"
    CONFIGURATION_LINE_PATTERN = str(TYPE_NUMBER) + ";([0-9]{1,9});(.+?);([1-9][0-9]{0,9});(.+)$"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.last_upload = None
        self.drive = GoogleDriveManager(self.api_location, self.id) if configuration_file_line is not None else None

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
        return "%i;%i;%s;%i;%s" % (self.TYPE_NUMBER, self.id, self.name, self.port, self.api_location)

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
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
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
        uploader_thread = threading.Thread(target=self._uploader_thread)
        uploader_thread.daemon = True
        uploader_thread.start()

        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, website_host_address):
        """
        Returns html code to include in website.
        """
        id, port = str(self.id), str(self.port)
        return '<div class="card-panel"> \
               <script>  \
               function updateLastUpload_' + id + '(text) { \n\
                    document.getElementById("googleDriveUploaderDiv' + id + '").innerHTML = text;\n \
               } \n\
               function getLastUpload' + id + '() { \n\
                    getRequest("localhost", ' + port + ', "", updateLastUpload_' + id + ');\n\
               } \
               getLastUpload_' + id + '(); \
               setInterval(function() { \n\
                    getLastUpload_' + id + '(); \n\
               }, 60*1000);\n\
               </script> \n\
               <h5>' + self.name + '</h5>\
               <div id="googleDriveUploaderDiv' + id + '" class="googleDriveUploaderDiv"> </div>\
               </div>'

    def _uploader_thread(self):
        """
        Check for possible scenario execution each minute.
        """

        def _upload_file(filename, file_path):
            if self.drive is None: return
            drive_folder = "%s - %s" % (self.UPLOAD_DRIVE_FOLDER, self.name)
            if self.drive.check_if_exists(drive_folder) is False:
                self.drive.create_folder(drive_folder)
            if self.drive.upload_image(filename, file_path, drive_folder):
                os.remove(file_path)

        while True:
            [_upload_file(f, self.UPLOAD_FOLDER + os.sep + f) for f in os.listdir(self.UPLOAD_FOLDER)]
            self.last_upload = datetime.datetime.now()
            time.sleep(15 * 60)

    def _react_to_connection(self, connection, _):
        """
        Generally respond to incoming connection.
        Maybe send some information about current module state?
        """
        connection.send("Last upload done on: %s" % str(self.last_upload) if self.last_upload is not None else "...")


if __name__ == "__main__":
    print 'Google Drive Uploader module: started.'
    conf_line = sys.argv[1]

    uploader = GoogleDriveUploader(conf_line)
    uploader.start_work()
