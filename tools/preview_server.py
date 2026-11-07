"""
Podgląd interfejsu WRH bez Raspberry, bez pakietu `utils` i bez działających modułów.

Renderuje PRAWDZIWY szablon wrh_engine/tornado/index.html i PRAWDZIWE pliki modules/<moduł>/html/repr.html
(przez ten sam str.format(...), co moduły), a /uptime, /request i /restart zastępuje atrapami, które odpowiadają
w tym samym formacie JSON, co moduły (stan jest trzymany w pamięci, więc przyciski Włącz/Wyłącz działają).

Uruchomienie (z katalogu repozytorium):
    python3 -m venv venv && venv/bin/pip install tornado
    venv/bin/python tools/preview_server.py            # http://localhost:8890/
    venv/bin/python tools/preview_server.py --port 9000

Przydatne adresy:
    /                                   widok System
    /?class=RangoIrygaModule            nawadnianie (linia 2 włączona, pozostały 3 cykle)
    /?class=ESP8266SocketModule         gniazdka (jedno ON, jedno OFF, jedno symuluje brak odpowiedzi - port 9999)
    /?class=DHT22Module, /?class=SpeedTestModule
    /?class=RangoIrygaSchedulerModule   starszy moduł (markup w stylu Materialize), jeśli da się go zaimportować
    ...&theme=dark / ...&theme=light    wymuszenie motywu
    ...&delay=2500                      opóźnia zdarzenie load (do zrzutów: firefox --headless --screenshot)
"""
import argparse
import asyncio
import datetime
import json
import os
import sys
import types
from types import SimpleNamespace

import tornado.ioloop
import tornado.web

REPO = os.path.abspath(os.environ.get('WRH_REPO') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TORNADO_DIR = os.path.join(REPO, 'wrh_engine', 'tornado')

TIMEOUT_PORT = 9999          # symuluje moduł, który nie odpowiada (serwer zwraca 504)
REFUSED_PORT = 9998          # symuluje moduł, który nie działa (serwer zwraca 502)


class PreviewModule:
    """Atrapa instancji modułu: get_html_representation() robi to samo, co prawdziwe moduły."""

    def __init__(self, module_class, folder, id, name, port, **extra_format_keys):
        self.WRHID, self.TYPE_NAME = module_class.WRHID, module_class.TYPE_NAME
        self.folder, self.id, self.name, self.port, self.extra = folder, id, name, port, extra_format_keys

    def get_html_representation(self, website_host_address):
        with open(os.path.join(REPO, 'modules', self.folder, 'html', 'repr.html'), 'r') as f:
            return f.read().format(id=self.id, name=self.name, port=self.port, **self.extra)


def module_class(wrhid, type_name):
    return SimpleNamespace(WRHID=wrhid, TYPE_NAME=type_name)


RANGO = module_class('RangoIrygaModule', 'RANGO IRYGA')
ESP = module_class('ESP8266SocketModule', 'ESP8266 WIFI SOCKET')
DHT = module_class('DHT22Module', 'DHT22 TEMP./HUM. SENSOR')
SPEED = module_class('SpeedTestModule', 'INTERNET SPEED TEST')

MODULES = [
    PreviewModule(RANGO, 'rango_iryga', 1, 'Ogród', 5001),
    # esp8266 przekazuje dodatkowo input_text (patrz ESP8266SocketModule.get_html_representation)
    PreviewModule(ESP, 'esp8266_wifi_socket', '2', 'Pompa w studni', '5002', input_text='esp_timeout_2'),
    PreviewModule(ESP, 'esp8266_wifi_socket', '3', 'Lampki na tarasie', '5003', input_text='esp_timeout_3'),
    PreviewModule(ESP, 'esp8266_wifi_socket', '4', 'Oczko wodne', str(TIMEOUT_PORT), input_text='esp_timeout_4'),
    PreviewModule(DHT, 'dht22', 5, 'Szklarnia', 5005),
    PreviewModule(DHT, 'dht22', 6, 'Piwnica', REFUSED_PORT),
    PreviewModule(SPEED, 'speed_test', '7', 'Łącze internetowe', 5007),
]


def add_scheduler_if_possible():
    """
    Harmonogram (RangoIrygaSchedulerModule) generuje HTML w Pythonie. Próbujemy zaimportować prawdziwą klasę,
    podstawiając puste atrapy za `utils` i `requests` (tylko w tym procesie), żeby obejrzeć starszy markup.
    """
    def stub(name, **attrs):
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__dict__.update(attrs)
            sys.modules[name] = module

    identity_decorator = lambda *a, **k: (lambda f: f)
    stub('utils')
    stub('utils.decorators', in_thread=lambda f: f, log_exceptions=identity_decorator,
         with_open=identity_decorator, ignore_exceptions=identity_decorator)
    stub('utils.io', log=print, wrh_input=input, non_empty_input=input, non_empty_positive_numeric_input=input,
         Color=SimpleNamespace(EXCEPTION=None))
    stub('utils.sockets', await_connection=None, wait_bind_socket=None, open_connection=None, send_message=None)
    try:
        import requests  # noqa: F401
    except ImportError:
        stub('requests', ConnectionError=ConnectionError, get=None)
    sys.path.insert(0, REPO)
    try:
        from modules.rango_iryga_scheduler.rango_iryga_scheduler import RangoIrygaSchedulerModule, RangoScenario
    except Exception as e:  # pragma: no cover - podgląd ma działać także bez harmonogramu
        print('Pomijam harmonogram (nie udało się zaimportować):', e)
        return None
    scheduler = RangoIrygaSchedulerModule('9;Harmonogram;5009;5001')
    scheduler.scenarios = [RangoScenario('1*6,30*0,2,4*1,2*300,80*1,4'), RangoScenario('0*20,0*5,6*3*600*1')]
    MODULES.append(scheduler)
    return scheduler


SCHEDULER = add_scheduler_if_possible()

# ---------- stan atrap modułów ----------
STATE = {
    'rango': {5: ['OFF', 0], 4: ['ON', 3], 15: ['OFF', 0], 14: ['OFF', 0]},
    'esp': {'5002': 'ON', '5003': 'OFF'},
}


def module_response(port, message):
    """Zwraca bajty, które odesłałby moduł nasłuchujący na `port` (ten sam format, co w modules/*.py)."""
    parts = message.split(',')
    if port == 5001:  # RangoIrygaModule: "ON,<gpio>,<czas>,<cykle>" / "OFF,<gpio>,-1,-1" / "STATE"
        command = parts[0].upper()
        if command == 'STATE':
            relays = [{'gpio': g, 'state': s, 'repeats': r} for g, (s, r) in STATE['rango'].items()]
            return json.dumps({'relays': relays}).encode('utf-8')
        if command in ('ON', 'OFF') and len(parts) == 4 and int(parts[1]) in STATE['rango']:
            cycles = max(1, int(parts[3])) if command == 'ON' else 1
            STATE['rango'][int(parts[1])] = [command, cycles - 1 if command == 'ON' else 0]
        return b''
    if str(port) in STATE['esp']:  # ESP8266SocketModule: "ON,<czas>" / "OFF,<czas>" / "STATE"
        command = parts[0].upper()
        if command == 'STATE':
            return json.dumps({'state': STATE['esp'][str(port)]}).encode('utf-8')
        if command in ('ON', 'OFF'):
            STATE['esp'][str(port)] = command
        return b''
    if port == 5005:  # DHT22Module
        return json.dumps({'humidity': 61.3, 'temperature': 23.4}).encode('utf-8')
    if port == 5007:  # SpeedTestModule
        return json.dumps({'download': 54.21, 'upload': 9.87, 'unit': 'Mbit/s'}).encode('utf-8')
    if SCHEDULER is not None and port == SCHEDULER.port:  # starszy moduł - odpowiada HTML-em
        if message.startswith('MEASUREMENT'):
            return SCHEDULER.get_measurement().encode('utf-8')
        return b''
    return None


# Prosty test dymny (?selftest=1&delay=4000): klika przyciski tak jak użytkownik; wysłane polecenia widać w logu.
SELFTEST_JS = '''
setTimeout(function () {
    var click = function (el) { if (el) el.click(); };
    var line = document.querySelector('[data-gpio="5"]');
    if (line) {
        click(line.querySelector('[data-preset="180"]'));
        click(line.querySelector('[data-step="1"]'));
        click(line.querySelector('[data-step="1"]'));
        click(line.querySelector('[data-command="on"]'));
        click(document.querySelector('[data-gpio="4"] [data-command="off"]'));
    }
    var socket = document.querySelector('[data-port="5003"]');
    if (socket) {
        var unlimited = socket.querySelector('[data-role="unlimited"]');
        unlimited.checked = false;
        unlimited.dispatchEvent(new Event('change'));
        socket.querySelector('[data-role="time"]').value = '120';
        socket.querySelector('[data-role="time"]').dispatchEvent(new Event('input'));
        click(socket.querySelector('[data-command="ON"]'));
        click(document.querySelector('[data-port="5002"] [data-command="OFF"]'));
    }
}, 600);
'''


# ---------- handlery ----------
class Index(tornado.web.RequestHandler):
    def get(self):
        requested = self.get_argument('class', None)
        classes = sorted({m.WRHID: SimpleNamespace(WRHID=m.WRHID, TYPE_NAME=m.TYPE_NAME) for m in MODULES}.values(),
                         key=lambda c: c.WRHID)
        target = requested if requested in [c.WRHID for c in classes] else -1
        ip = str(self.request.host).split(':')[0]
        html = self.render_string('index.html', ipaddress=ip, target=target, classes=classes, modules=MODULES)
        delay = self.get_argument('delay', None)
        if self.get_argument('selftest', None):
            html = html.replace(b'</body>', b'<script>' + SELFTEST_JS.encode('utf-8') + b'</script></body>')
        if delay and delay.isdigit():
            # Do zrzutów ekranu (firefox --screenshot robi zdjęcie po zdarzeniu load): wolny obrazek opóźnia load,
            # żeby dane z atrap zdążyły się wczytać. Prawdziwy szablon pozostaje bez zmian.
            html = html.replace(b'</body>', b'<img src="/__delay?ms=' + delay.encode() + b'" alt="" hidden></body>')
        self.finish(html)


class Delay(tornado.web.RequestHandler):
    async def get(self):
        await asyncio.sleep(min(int(self.get_argument('ms', '0')), 10000) / 1000.0)
        self.set_header('Content-Type', 'image/gif')
        self.finish(b'GIF89a\x01\x00\x01\x00\x00\x00\x00;')


class Uptime(tornado.web.RequestHandler):
    def get(self):
        now = datetime.datetime.now()
        self.finish({'date': now.strftime('%d-%m-%Y'), 'time': now.strftime('%H:%M'),
                     'uptime': '5 days, 3:42', 'cpu_temp': 48.3})


class Restart(tornado.web.RequestHandler):
    def post(self):
        print('[podgląd] Restart Raspberry (atrapa - nic się nie dzieje)')
        self.finish({'status': 'restarting'})


class Request(tornado.web.RequestHandler):
    async def post(self):
        port = int(self.get_argument('port'))
        message = self.get_argument('message', '')
        print('[podgląd] port=%s message=%r' % (port, message), flush=True)
        await asyncio.sleep(0.3)
        if port == TIMEOUT_PORT:
            await asyncio.sleep(1.5)
            self.set_status(504)
            return self.finish({'error': 'timeout'})
        response = module_response(port, message)
        if response is None:
            self.set_status(502)
            return self.finish({'error': 'connection_refused'})
        # Ta sama logika Content-Type, co w wrh_engine/tornado/server.py
        try:
            json.loads(response.decode('utf-8'))
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
        except ValueError:
            self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.finish(response)

    get = post


def main():
    parser = argparse.ArgumentParser(description='Podgląd interfejsu WRH z atrapami modułów')
    parser.add_argument('--port', type=int, default=8890)
    args = parser.parse_args()
    import mimetypes
    mimetypes.add_type('application/manifest+json', '.webmanifest')
    app = tornado.web.Application([
        (r'/', Index), (r'/uptime', Uptime), (r'/restart', Restart), (r'/request', Request),
        (r'/__delay', Delay),
    ], template_path=TORNADO_DIR, static_path=TORNADO_DIR, debug=True)
    app.listen(args.port)
    print('Podgląd WRH: http://localhost:%d/' % args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
