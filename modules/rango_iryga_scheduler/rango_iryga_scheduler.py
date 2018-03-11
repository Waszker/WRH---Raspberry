# -*- coding: utf-8 -*-

import datetime
import os
import re
import signal
import sys
import threading
import time

from modules.rango_iryga.rango_iryga import RangoIrygaModule
from utils.io import log
from utils.io import non_empty_positive_numeric_input as iinput
from wrh_engine import module_base as base_module


class WateringThread(threading.Thread):
    def __init__(self, rango_port, line_number, activation_time, repeats, delay=0):
        """
        Creates watering thread that activates Rango Iryga lines.
        :param rango_port: port at which Rango Iryga module listens for connection
        :param line_number: number of the line to activate (1, 2, 3 or 4)
        :param activation_time: duration (in seconds) of watering procedure
        :param repeats: number of watering procedure repeats
        :param delay: time (in seconds) to wait before starting watering procedure
        """
        threading.Thread.__init__(self)
        self.rango_port = rango_port
        self.relay = self.get_real_relay_number(line_number)
        self.activation_time = activation_time
        self.repeats = repeats
        self.delay = delay
        self.timer = threading.Timer(delay, self._change_relay_state, args=(True,))

    def run(self):
        self.timer.daemon = True
        self.timer.start()
        self.timer.join()

    def cancel(self):
        message = "%s,%s,%s,%s" % tuple(map(str, ("OFF", self.relay, -1, -1)))
        send_message("127.0.0.1", self.rango_port, message)
        self.timer.cancel()

    def _change_relay_state(self, turn_on):
        state = "ON" if turn_on else "OFF"
        activation_time = self.activation_time if turn_on else -1
        repeats = self.repeats if turn_on else -1
        message = "%s,%s,%s,%s" % tuple(map(str, (state, self.relay, activation_time, repeats)))
        send_message("127.0.0.1", self.rango_port, message)

    @staticmethod
    def get_real_relay_number(relay_order_number):
        real_numbers = {i + 1: RangoIrygaModule.RELAYS[i] for i in xrange(4)}
        try:
            real_number = real_numbers[relay_order_number]
        except (KeyError, ValueError):
            real_number = -1
        return real_number


class RangoScenario:
    """
    Class for private use only that represents Rango Iryga scenario to run at a certain time.
    """
    REQUEST_SEPARATOR = SEP = '*'
    PART_SEPARATOR = PSEP = ','

    def __init__(self, request):
        """
        Creates scenario from the provided information.
        :param request: line containing information about scenario, sent after user creates new request
        """
        self.request = request = str(request).replace('\n', '')
        active, start, days, lines, times, repeats = request.split(RangoScenario.SEP)
        self.is_active = (int(active) == 1)
        hour, minute = map(int, start.split(RangoScenario.PSEP))
        self.start_time = datetime.datetime(2000, 1, 1, hour, minute)
        self.active_on_days = list(map(int, days.split(RangoScenario.PSEP)))
        self.active_lines = list(map(int, lines.split(RangoScenario.PSEP)))
        self.line_activation_times = list(map(int, times.split(RangoScenario.PSEP)))
        self.line_activation_repeats = list(map(int, repeats.split(RangoScenario.PSEP)))
        self.watering_threads = []

    def get_html_information_string(self):
        """
        Returns HTML formatted string to display one the tornado web page.
        :return: HTML formatted string
        """
        weekdays = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
        html_information = "<p>Czas rozpoczęcia <b>%02i:%02i</b></p>" % (self.start_time.hour, self.start_time.minute)
        for relay, time, repeats in zip(self.active_lines, self.line_activation_times, self.line_activation_repeats):
            html_information += "<p>Linia %i na %i sekund z %i powtórzeniami</p>" % (relay, time, repeats)
        html_information += "<p>Dni: "
        for day in self.active_on_days:
            html_information += "&nbsp;<b>%s</b>" % weekdays[day]
        html_information += "</p><p>Status: "
        html_information += "<a style=\"color:%s;\">%s</a></p>" % (
            ('green', 'ON') if self.is_active else ('red', 'OFF'))
        return html_information

    def time_changed(self, date, rango_port):
        """
        Reacts to time change and runs scenario (self) if needed.
        :param date: current date (day of the month, etc.)
        :param rango_port: port of the Rango Iryga system
        """
        if self._should_activate(date):
            # Log action to file?
            thread = threading.Thread(target=self._activate, args=(rango_port,))
            thread.daemon = True
            thread.start()

    def toggle_activity(self):
        """
        Turns scenario on or off.
        Off scenarios are never activated and the turning off procedure even shuts remaining watering threads.
        :return:
        """
        self._cancel_all_watering_threads()
        self.is_active = not self.is_active
        request_parts = self.request.split(RangoScenario.SEP)
        request_parts[0] = str(1 if self.is_active else 0)
        self.request = RangoScenario.SEP.join(request_parts)

    def _cancel_all_watering_threads(self):
        for thread in self.watering_threads:
            thread.cancel()
            thread.join()
        del self.watering_threads[:]

    def _should_activate(self, date):
        return self.is_active and \
               (date.weekday() in self.active_on_days) and \
               (date.hour == self.start_time.hour) and \
               (date.minute == self.start_time.minute)

    def _activate(self, rango_port):
        self._cancel_all_watering_threads()
        delay = 0
        for line, atime, repeats in zip(self.active_lines, self.line_activation_times, self.line_activation_repeats):
            watering_thread = WateringThread(rango_port, line, atime, repeats, delay=delay)
            watering_thread.start()
            self.watering_threads.append(watering_thread)
            delay += (atime + RangoIrygaModule.DELAY) * repeats


class RangoIrygaSchedulerModule(base_module.Module):
    """
    Rango Iryga Scheduler is a module responsible for automatically running watering scenarios.
    """
    TYPE_NAME = "RANGO IRYGA SCHEDULER"
    CONFIGURATION_LINE_PATTERN = "([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"
    _saved_scenarios_file = "modules/rango_iryga_scheduler/.scenarios"

    def __init__(self, configuration_file_line=None):
        self.rango_port = None
        self.scenarios = []
        base_module.Module.__init__(self, configuration_file_line)

    @staticmethod
    def get_starting_command():
        """
        Returns command used to start module as a new process.
        :return: Command to be executed when starting new process
        """
        return ["/usr/bin/python2.7", "-m", "modules.rango_iryga_scheduler.rango_iryga_scheduler"]

    def get_configuration_line(self):
        """
        Creates module configuration line.
        :return: Properly formatted configuration file line
        """
        values = (self.id, self.name, self.port, self.rango_port)
        return ('{};' * len(values))[:-1].format(*values)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(self.CONFIGURATION_LINE_PATTERN, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.port = int(matches.group(3))
        self.rango_port = int(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module.
        Rango Scheduler returns html table containing all scenarios data.
        """
        html_table = '<br/><br/><ul class="collection with-header"> \
                      <li class="collection-header" style="background-color: #a7aaaf"><h5>Obecne scenariusze</h5></li>'

        for i, scenario in enumerate(self.scenarios):
            html_table += '<li style="background-color: #a7aaaf" class="collection-item">' \
                          '<div>%s' % scenario.get_html_information_string()
            html_table += '<button class="waves-effect waves-light btn grey darken-3" type="button" ' \
                          'onclick="removeScenario' + str(self.id) + '(%i)">Usuń</button>' % i

            html_table += '&nbsp;&nbsp;&nbsp;<button class="waves-effect waves-light btn grey darken-3" type="button"' \
                          'onclick="toggleScenario' + str(self.id) + '(%i)">%s</button> \
                          <br/></div></li>' % (i, "Wyłącz" if scenario.is_active else "Włącz")

        return html_table

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Rango Iryga Scheduler module used to maintain scenarios for the Rango Iryga irrigation system " \
               "for garden."

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.port = iinput("Please input port on which this module will be listening for commands: ")
        self.rango_port = iinput("Please input port number of Rango Iryga installed in this system: ")

    def edit(self):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        log('Provide new module information (leave fields blank if you don\'t want to change)')
        log('Please note that changes other than name will always succeed')
        self.name = raw_input('New module\'s name: ') or self.name
        self.port = iinput("Please input new port on which this module will be listening for commands: ",
                           allowed_empty=True) or self.port
        self.rango_port = iinput("Please input new port number of Rango Iryga installed in this system: ",
                                 allowed_empty=True) or self.rango_port

    def start_work(self):
        """
        Starts working procedure.
        """
        self._read_scenarios_from_file()
        base_module.Module.start_work(self)
        scheduler = threading.Thread(target=self._scheduler_thread)
        scheduler.daemon = True
        scheduler.start()
        while self._should_end is False:
            signal.pause()

    def get_html_representation(self, _):
        """
        Returns html code to include in website.
        """
        id = str(self.id)
        port = str(self.port)

        representation = '<div class="card-panel">'
        representation += '<h5>%s</h5>' % self.name
        representation += '<div id="rangoIrygaSchedulerSocketDiv' + id + '" class="socketDiv" style="height: auto; margin: auto">\n \
                           <img src="static/images/loading_spinner.gif" style="width: 50px;"/>\n \
                           </div>\n \
                           <table style="margin: 0px auto; max-width: 95%; width: auto"> \
                           <tr><td colspan="3" style="text-align:center; vertical-align:middle"><h5>Dodaj nowy scenariusz</h5></td></tr> \
                           <tr><td style="text-align:center; vertical-align:middle"><b>Linia</b></td> \
                               <td style="text-align:center; vertical-align:middle"><b>Czas</b></td> \
                               <td style="text-align:center; vertical-align:middle"><b>Powtórzeń</b></td></tr>'

        repeats = [1, 4, 1, 1]
        times = [300, 80, 300, 300]
        for i in xrange(4):
            representation += ' <tr>\n \
                                <td>\n \
                                    <input type="checkbox" id="line' + str(i + 1) + id + '"/>\n \
                                    <label for="line' + str(i + 1) + id + '">Linia ' + str(i + 1) + '</label>\n \
                                </td>\n \
                                <td>\n \
                                    <div style="margin: 3%; width: 100%"><p class="input-field"><input id="line' + str(
                i + 1) + '_time' + id + '" type="number" style="width: 90%" value="' + str(times[i]) + '"/></div>\n \
                                </td>\n \
                                <td>\n \
                                    <div style="margin: 3%; width: 100%"><p class="input-field"><input id="line' + str(
                i + 1) + '_repeats' + id + '" type="number" style="width: 90%" value="' + str(repeats[i]) + '"/></div>\n \
                                </td>\n \
                            </tr>'
        representation += ' <tr>\n \
                            <td colspan="3">\n \
                            <p>Godzina</p> \
                                <p class="range-field">\n \
                                    <input type="range" id="hour' + id + '" min="0" max="23"/>\n \
                                </p>\n \
                            <p>Minuta</p> \
                                <p class="range-field">\n \
                                    <input type="range" id="minute' + id + '" min="0" max="59"/>\n \
                                </p>\n \
                            </td>\n \
                        </tr>\n \
                        <tr>\n \
                            <td colspan="3">\n \
                                <input type="checkbox" id="monday' + id + '"/>\n \
                                <label for="monday' + id + '">Pon</label><br />\n \
                                <input type="checkbox" id="tuesday' + id + '"/>\n \
                                <label for="tuesday' + id + '">Wto</label><br />\n \
                                <input type="checkbox" id="wednesday' + id + '"/>\n \
                                <label for="wednesday' + id + '">Śro</label><br />\n \
                                <input type="checkbox" id="thursday' + id + '"/>\n \
                                <label for="thursday' + id + '">Czw</label><br />\n \
                                <input type="checkbox" id="friday' + id + '"/>\n \
                                <label for="friday' + id + '">Pią</label><br />\n \
                                <input type="checkbox" id="saturday' + id + '"/>\n \
                                <label for="saturday' + id + '">Sob</label><br />\n \
                                <input type="checkbox" id="sunday' + id + '"/>\n \
                                <label for="sunday' + id + '">Nie</label><br />\n \
                            </td>\n \
                        </tr>\n \
                        <tr>\n \
                            <td colspan="3">\n \
                                <button class="waves-effect waves-light btn grey darken-3" type="button" onclick="saveScenario' + id + '()">\n \
                                    Zapisz\n \
                                </button>\n \
                            </td>\n \
                        </tr>\n \
                    </table>'
        representation += '<script>\n \
                        function getScenarios' + id + '() {\n \
                            document.getElementById("rangoIrygaSchedulerSocketDiv' + id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";\n \
                            postRequest("localhost", ' + port + ', "MEASUREMENT|null", update_scenarios_view' + id + ');\n \
                        }\n \
                        function update_scenarios_view' + id + '(text) {\n \
                                   document.getElementById("rangoIrygaSchedulerSocketDiv' + id + '").innerHTML = text;\n \
                        }\n \
                        function toggleScenario' + id + '(number) {\n \
                            sendRequest("localhost", ' + port + ', "ACT|" + number);\n \
                            setTimeout(getScenarios' + id + ', 500);\n \
                        }\n \
                        function removeScenario' + id + '(number) {\n \
                            sendRequest("localhost", ' + port + ', "DEL|" + number);\n \
                            setTimeout(getScenarios' + id + ', 500);\n \
                        }\n \
                        function saveScenario' + id + '() {\n \
                            saveRequest = "ADD|" + scenarioString' + id + '();\n \
                            sendRequest("localhost", ' + port + ', saveRequest);\n \
                            setTimeout(getScenarios' + id + ', 500);\n \
                        }\n \
                        function scenarioString' + id + '() {\n \
                            scenarioString = getTime' + id + '() + "*";\n \
                            scenarioString += getWeekDays' + id + '() + "*";\n \
                            scenarioString += getLineInformation' + id + '();\n \
                            return scenarioString;\n \
                        }\n \
                        function getTime' + id + '() {\n \
                            hour = document.getElementById("hour' + id + '").value;\n \
                            minute = document.getElementById("minute' + id + '").value;\n \
                            return "" + hour + "," + minute;\n \
                        }\n \
                        function getWeekDays' + id + '() {\n \
                            weekdaysString = "";\n \
                            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];\n \
                            for (i = 0; i < 7; i++) {\n \
                                if (!document.getElementById(weekdays[i] + ' + id + ').checked) continue;\n \
                                weekdaysString += (weekdaysString === "" ? "" : ",") + i;\n \
                            }\n \
                            return weekdaysString;\n \
                        }\n \
                        function getLineInformation' + id + '() {\n \
                            isValid = false;\n \
                            linesString = "";\n \
                            timesString = "";\n \
                            repeatsString = "";\n \
                            for (i = 0; i < 4; i++) {\n \
                                if (document.getElementById("line" + (i+1) + ' + id + ').checked) {\n \
                                    isValid = true;\n \
                                    separator = (linesString === "" ? "" : ",");\n \
                                    linesString += separator + (i+1);\n \
                                    timesString += separator + document.getElementById("line" + (i+1) + "_time" + ' + id + ').value;\n \
                                    repeatsString += separator + document.getElementById("line" + (i+1) + "_repeats" + ' + id + ').value;\n \
                                 }\n \
                            }\n \
                            if (!isValid) return "-1;0;0";\n \
                            return linesString + "*" + timesString + "*" + repeatsString;\n \
                        }\n \
                        getScenarios' + id + '();\n \
                    </script>\n \
                    </div>'
        return representation

    def _read_scenarios_from_file(self):
        mode = "r+" if os.path.isfile(RangoIrygaSchedulerModule._saved_scenarios_file) else "w+"
        with open(RangoIrygaSchedulerModule._saved_scenarios_file, mode) as f:
            self.scenarios.extend([RangoScenario(line) for line in f])

    def _scheduler_thread(self):
        """
        Check for possible scenario execution each minute.
        """
        time.sleep(60 - datetime.datetime.now().second)
        start_time = time.time()
        while True:
            current_time = datetime.datetime.now()
            if current_time.year >= 2000:
                [scenario.time_changed(current_time, self.rango_port) for scenario in self.scenarios]
            time.sleep(60.0 - ((time.time() - start_time) % 60.0))

    def _react_to_connection(self, connection, _):
        action, request = str(connection.recv(1024)).split('|')
        if action == "ADD" or action == "add":
            self.scenarios.append(RangoScenario(str(1) + RangoScenario.SEP + request))
        elif action == "DEL" or action == "del":
            del self.scenarios[int(request)]
        elif action == "ACT" or action == "act":
            self.scenarios[int(request)].toggle_activity()
        elif action == "MEASUREMENT" or action == "measurement":
            connection.send(self.get_measurement())
            return

        with open(RangoIrygaSchedulerModule._saved_scenarios_file, 'w+') as f:
            f.writelines([(scenario.request + "\n") for scenario in self.scenarios])


if __name__ == "__main__":
    log('Rango Iryga module: started.')
    conf_line = sys.argv[1]

    rango_iryga_scheduler = RangoIrygaSchedulerModule(conf_line)
    rango_iryga_scheduler.start_work()
