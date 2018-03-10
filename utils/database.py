import datetime
import json

from utils.decorators import with_open
from utils.sockets import open_connection
from wrh_engine.constants import WRH_DATABASE_CONFIGURATION_FILENAME


@with_open(WRH_DATABASE_CONFIGURATION_FILENAME, 'r')
def send_measurement(module_type, module_id, measurement, _file_=None):
    """
    Sends measured data to remote database.
    Remote server's credentials should be present in WRH server configuration file.
    :param module_type: identifier of module type that sends the measurement
    :type module_type: str
    :param module_id: id of module assigned by local WRH system
    :type module_id: int
    :param measurement: measurement value to be stored in database
    :type measurement: any
    :param _file_: parameter filled by function decorator
    :type _file_: file
    """
    conf = json.loads(_file_.read())
    data = {
        'token': conf['token'], 'module_type': module_type, 'module_id': module_id, 'measurement': measurement,
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open_connection((conf['host'], conf['port'])) as connection:
        connection.send(json.dumps(data))
