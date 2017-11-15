import os

import googleapiclient
import httplib2
from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from utils.io import log, Color


class GoogleDriveManager:
    """
    Takes care of obtaining permissions for Google Drive modification.
    """
    SCOPES = 'https://www.googleapis.com/auth/drive'
    APPLICATION_NAME = 'WRH Server Uploader'

    def __init__(self, client_secret_location, credential_file_id):
        self._secret = client_secret_location
        self._file_id = credential_file_id
        self._credentials = self._credentials_procedure()
        http = self._credentials.authorize(httplib2.Http())
        self._service = discovery.build('drive', 'v3', http=http)

    def create_folder(self, folder_name, path=None):
        """
        Creates folder in the Google Drive.
        :param folder_name: name of the folder
        :param path: placement of the folder in the drive filesystem
        :return: id of newly created folder or None if an error occurred
        """
        # TODO: Add support for path parameter!
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }

        folder_id = None
        try:
            folder = self._service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
        except googleapiclient.errors.HttpError as e:
            log(str(e), Color.FAIL)

        return folder_id

    def get_folder_id(self, folder_name, path=None):
        """
        Returns id of the folder in the drive.
        :param folder_name:
        :param path: placement of the folder in the drive filesystem
        :return: id of the folder, None if such folder does not exist
        """
        folder_id = None
        response = self._service.files().list(q="name='%s' and trashed=false" % folder_name).execute()
        if len(response.get('files', [])) > 0:
            folder_id = response.get('files', [])[0].get('id')
        return folder_id

    def check_if_exists(self, file_name, path=None):
        """
        Checks if file or folder with provided name exists.
        :param file_name: name of the file
        :param path: placement of the folder in the filesystem
        :return: boolean
        """
        response = self._service.files().list(q="name='%s' and trashed=false" % file_name).execute()
        return len(response.get('files', [])) > 0

    def upload_image(self, image_name, image_path, parent_folder_name=None):
        """
        Uploads provided image to the drive location.
        :param image_name: name of the image on the Google drive
        :param image_path: location of the image on the local filesystem
        :param parent_folder_name: name of the parent folder in the google drive
        :return: boolean if the operation was successful
        """
        parent_folder_id = self.get_folder_id(parent_folder_name)
        file_metadata = {'name': image_name}
        if parent_folder_id is not None: file_metadata['parents'] = [parent_folder_id]
        media = MediaFileUpload(image_path, mimetype='image/jpeg')
        try:
            self._service.files().create(body=file_metadata,
                                         media_body=media,
                                         fields='id').execute()
            success = True
        except googleapiclient.errors.HttpError as e:
            log(str(e), Color.FAIL)
            success = False

        return success

    def _credentials_procedure(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, 'wrh_uploader_%i.json' % int(self._file_id))

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            try:
                import argparse

                flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
            except ImportError:
                flags = None
            flow = client.flow_from_clientsecrets(self._secret, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            flags.noauth_local_webserver = True
            credentials = tools.run_flow(flow, store, flags)
            log('Storing credentials to ' + credential_path)
        return credentials
