import datetime

from utils.decorators import with_open
from utils.sockets import open_connection


@with_open('server.conf', 'r')
def send_measurement(module_id, measurement, _file_=None):
    conf = _file_.read()
    data = {'token': conf.token, 'module_id': module_id, 'measurement': str(measurement),
            'date': datetime.datetime.now()}
    with open_connection((conf.host, conf.port)) as connection:
        connection.send(data)
