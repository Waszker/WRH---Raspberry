import datetime
import json

from utils.decorators import with_open
from utils.sockets import open_connection
from wrh_engine.constants import WRH_DATABASE_CONFIGURATION_FILENAME


@with_open(WRH_DATABASE_CONFIGURATION_FILENAME, 'r')
def send_measurement(module_id, measurement, _file_=None):
    """
    Sends measured data to remote database. Remote server's credentials should be present in
    :param module_id:
    :param measurement:
    :param _file_:
    :return:
    """
    conf = json.loads(_file_.read())
    data = {'token': conf['token'], 'module_id': module_id, 'measurement': measurement,
            'date': str(datetime.datetime.now())}
    with open_connection((conf['host'], conf['port'])) as connection:
        connection.send(json.dumps(data))
