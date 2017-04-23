#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import re
import sys
import signal
import time
import datetime
import threading
from wrh_engine import module_base as base_module
from utils.sockets import send_message
from utils.io import non_empty_positive_numeric_input as iinput


class RangoScenario:
    """
    Class for private use only that represents Rango Iryga scenario to run at a certain time.
    """

    def __init__(self, request):
        """
        Creates scenario from the provided information.
        :param request: line containing information about scenario, sent after user creates new request
        """
        self.request = str(request)
        self.is_active = True
        start, days, lines, times, repeats = request.split(';')
        hour, minute = map(int, start.split(','))
        self.start_time = datetime.datetime(2000, 1, 1, hour, minute)
        self.active_on_days = list(map(int, days.split(',')))
        self.active_lines = list(map(int, lines.split(',')))
        self.line_activation_times = list(map(int, times.split(',')))
        self.line_activation_repeats = list(map(int, repeats.split(',')))

    def get_html_information_string(self):
        """
        Returns HTML formatted string to display one the tornado web page.
        :return: HTML formatted string
        """
        html_information = "Czas rozpoczęcia %i:%i<br />" % (self.start_time.hour, self.start_time.minute)
        html_information += "Aktywne linie: <ul>"
        for relay, time, repeats in zip(self.active_lines, self.line_activation_times, self.line_activation_repeats):
            html_information += "<li>linia %i na %i sekund z %i powtórzeniami</li>" % (relay, time, repeats)
        html_information += "</ul><br />"
        html_information += "Obowiązuje w dni: %s" % str(self.active_on_days)
        return html_information

    def time_changed(self, date, rango_port):
        """
        Reacts to time change and runs scenario (self) if needed.
        :param date: current date (day of the month, etc.)
        :param rango_port: port of the Rango Iryga system
        """
        if self._should_activate(date):
            # Log action to file?
            self._activate(rango_port)

    def _should_activate(self, date):
        return self.is_active and \
               (date.weekday() in self.active_on_days) and \
               (date.hour == self.start_time.hour) and \
               (date.minute == self.start_time.minute)

    def _activate(self, rango_port):
        state = "ON"
        for relay, time, repeats in zip(self.active_lines, self.line_activation_times, self.line_activation_repeats):
            message = "%s,%s,%s,%s" % tuple(map(str, (state, relay, time, repeats)))
            send_message("127.0.0.1", rango_port, message)


class RangoIrygaSchedulerModule(base_module.Module):
    """
    Rango Iryga Scheduler is a module responsible for automatically running watering scenarios.
    """
    type_number = 8
    type_name = "RANGO IRYGA SCHEDULER"
    configuration_line_pattern = str(type_number) + ";([0-9]{1,9});(.+?);([1-9][0-9]{0,9});([1-9][0-9]{0,9})$"
    _saved_scenarios_file = "modules/rango_iryga_scheduler/.scenarios"

    def __init__(self, configuration_file_line=None):
        base_module.Module.__init__(self, configuration_file_line)
        self.type_number = RangoIrygaSchedulerModule.type_number
        self.type_name = RangoIrygaSchedulerModule.type_name
        self.scenarios = []

    @staticmethod
    def is_configuration_line_sane(configuration_line):
        """
        Checks if configuration line for this module is well formed.
        :param self:
        :param configuration_line:
        :return:
        """
        # Configuration line for camera should look like this:
        # TYPE_NUM=7 ; ID=INT ; NAME=STRING ; ADDRESS=STRING ; PORT=INT
        checker = re.compile(RangoIrygaSchedulerModule.configuration_line_pattern)
        return checker.match(configuration_line) is not None

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
        return "%i;%i;%s;%i;%i" % (self.type_number, self.id, self.name, self.port, self.rango_port)

    def _parse_configuration_line(self, configuration_file_line):
        """
        Initializes class variables from provided configuration line.
        """
        matches = re.search(RangoIrygaSchedulerModule.configuration_line_pattern, configuration_file_line)
        self.id = int(matches.group(1))
        self.name = str(matches.group(2))
        self.port = int(matches.group(3))
        self.rango_port = int(matches.group(4))

    def get_measurement(self):
        """
        Returns measurements taken by this module.
        Rango Scheduler returns html table containing all scenarios data.
        """
        html_table = '<table style="margin: 0px auto; max-width: 95%; width: auto"> \
                      <tr><td colspan="3">Obecne scenariusze</td></tr>'

        for i, scenario in enumerate(self.scenarios):
            html_table += '<tr>' \
                          '<td>%s</td>' % scenario.get_html_information_string()
            html_table += '<td><div class="switch" onclick="toggleScenario(%i)' \
                          '<label>OFF<input %s type="checkbox"><span class="level"></span>ON</label>' \
                          '</div></td>' % (i, "checked" if scenario.is_active else "")
            html_table += '<td><a onclick="removeScenario(%i)">Usuń</a></td>' % i

        html_table += '</table>'
        return html_table

    def get_module_description(self):
        """
        Returns module description to be viewed by user.
        """
        return "Rango Iryga Scheduler module used to maintain scenarios for the Rango Iryga irrigation system " \
               "for garden."

    def get_type_number_and_name(self):
        """
        Returns module type number and short name (as two separate variables)
        """
        return self.type_number, self.type_name

    def run_registration_procedure(self, new_id):
        """
        Runs interactive procedure to register new module.
        """
        base_module.Module.run_registration_procedure(self, new_id)
        self.port = iinput("Please input port on which this module will be listening for commands: ")
        self.rango_port = iinput("Please input port number of Rango Iryga installed in this system: ")

    def edit(self, device_id, device_token):
        """
        Runs interactive procedure to edit module.
        Returns connection status and response.
        """
        print 'Provide new module information (leave fields blank if you don\'t want to change)'
        print 'Please note that changes other than name will always succeed'
        print 'Name changing requires active Internet connection'
        new_name = raw_input('New module\'s name: ')
        new_port = raw_input("Please input new port on which this module will be listening for commands: ")
        new_rango_port = raw_input("Please input new port number of Rango Iryga installed in this system: ")

        if new_rango_port: self.rango_port = new_rango_port
        if new_port: self.port = new_port
        if new_name: self.name = new_name

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
        representation += '<div id="rangoIrygaSchedulerSocketDiv' + id + '" class="socketDiv" style="height: 50px; margin: auto"> \
                           <img src="static/images/loading_spinner.gif" style="width: 50px;"/> \
                           </div> \
                           <table style="margin: 0px auto; max-width: 95%; width: auto">'

        for i in xrange(4):
            representation += ' <tr> \
                                <td> \
                                    <input type="checkbox" id="line' + str(i + 1) + id + '"/> \
                                    <label for="line' + str(i + 1) + id + '">Linia ' + str(i + 1) + '</label> \
                                </td> \
                                <td> \
                                    <div style="margin: 3%; width: 100%"><p class="input-field"><input id="line' + str(
                i + 1) + '_time' + id + '" type="number" style="width: 90%" value="-1"/></div> \
                                </td> \
                                <td> \
                                    <div style="margin: 3%; width: 100%"><p class="input-field"><input id="line' + str(
                i + 1) + '_repeats' + id + '" type="number" style="width: 90%" value="-1"/></div> \
                                </td> \
                            </tr>'
        representation += ' <tr> \
                            <td colspan="3"> \
                                <p class="range-field"> \
                                    <input type="range" id="hour' + id + '" min="0" max="23"/> \
                                </p> \
                                <p class="range-field"> \
                                    <input type="range" id="minute' + id + '" min="0" max="59"/> \
                                </p> \
                            </td> \
                        </tr> \
                        <tr> \
                            <td colspan="3"> \
                                <input type="checkbox" id="monday' + id + '"/> \
                                <label for="monday' + id + '">Pon</label> \
                                <input type="checkbox" id="tuesday' + id + '"/> \
                                <label for="tuesday' + id + '">Wto</label> \
                                <input type="checkbox" id="wednesday' + id + '"/> \
                                <label for="wednesday' + id + '">Śro</label> \
                                <input type="checkbox" id="thursday' + id + '"/> \
                                <label for="thursday' + id + '">Czw</label> \
                                <input type="checkbox" id="friday' + id + '"/> \
                                <label for="friday' + id + '">Pią</label> \
                                <input type="checkbox" id="saturday' + id + '"/> \
                                <label for="saturday' + id + '">Sob</label> \
                                <input type="checkbox" id="sunday' + id + '"/> \
                                <label for="sunday' + id + '">Nie</label> \
                            </td> \
                        </tr> \
                        <tr> \
                            <td colspan="3"> \
                                <button class="waves-effect waves-light btn grey darken-3" type="button" onclick="saveScenario' + id + '()"> \
                                    Zapisz \
                                </button> \
                            </td> \
                        </tr> \
                    </table>'
        representation += '<script>\n \
                        function getScenarios' + id + '() {\n \
                            document.getElementById("rangoIrygaSchedulerSocketDiv' + id + '").innerHTML = "<img src=\\"static/images/loading_spinner.gif\\" style=\\"width: 50px;\\" />";\n \
                            getRequest("localhost", ' + port + ', "MEASUREMENT", update_scenarios_view' + id + ');\n \
                        }\n \
                        function update_scenarios_view' + id + '(text) {\n \
                                   document.getElementById("rangoIrygaSchedulerSocketDiv' + id + '").innerHTML = text;\n \
                        }\n \
                        function toggleScenario' + id + '(number) {\n \
                            sendRequest("localhost", ' + port + ', "ACT|" + number);\n \
                            getScenarios' + id + '();\n \
                        }\n \
                        function removeScenario' + id + '(number) {\n \
                            sendRequest("localhost", ' + port + ', "DEL|" + number);\n \
                            getScenarios' + id + '();\n \
                        }\n \
                        function saveScenario' + id + '() {\n \
                            sendRequest("localhost", ' + port + ', "ADD|" + scenarioString' + id + '());\n \
                            getScenarios' + id + '();\n \
                        }\n \
                        function scenarioString' + id + '() {\n \
                            scenarioString = getTime' + id + '() + ";";\n \
                            scenarioString += getWeekDays' + id + '() + ";";\n \
                            return scenarioString + getLineInformation' + id + '();\n \
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
                                if (!document.getElementById(weekdays[i]' + id + ').checked) continue;\n \
                                weekdayString += "" + i + ",";\n \
                            }\n \
                            return weekdayString;\n \
                        }\n \
                        function getLineInformation' + id + '() {\n \
                            isValid = false;\n \
                            linesString = "";\n \
                            timesString = "";\n \
                            repeatsString = "";\n \
                            for (i = 0; i < 4; i++) {\n \
                                if (document.getElementById("line" + (i+1)' + id + ').checked) {\n \
                                    isValid = true;\n \
                                    separator = (linesString === "" ? "" : ",");\n \
                                    linesString += separator + (i+1);\n \
                                    timesString += separator + document.getElementById("line" + (i+1) + "_time"' + id + ').value;\n \
                                    repeatsString += separator + document.getElementById("line" + (i+1) + "_repeats"' + id + ').value;\n \
                                 }\n \
                            }\n \
                            if (!isValid) return "-1;0;0";\n \
                            return linesString + ";" + timesString + ";" + repeatsString;\n \
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
        start_time = time.time()
        while True:
            # TODO: Check for no connection situation!
            current_time = datetime.datetime.utcnow()
            [scenario.time_changed(current_time, self.rango_port) for scenario in self.scenarios]
            time.sleep(60.0 - ((time.time() - start_time) % 60.0))

    def _react_to_connection(self, connection, _):
        data = connection.recv(1024)
        action, request = data.split('|')
        if action == "ADD" or action == "add":
            self.scenarios.append(RangoScenario(request))
        elif action == "DEL" or action == "del":
            del self.scenarios[int(request)]
        elif action == "ACT" or action == "act":
            self.scenarios[int(request)].is_active = not self.scenarios[int(request)].is_active
        elif action == "MEASUREMENT" or action == "measurement":
            connection.send(self.get_measurement())
            return

        with open(RangoIrygaSchedulerModule._saved_scenarios_file, 'w+') as f:
            f.writelines([scenario.request for scenario in self.scenarios])


if __name__ == "__main__":
    print 'Rango Iryga module: started.'
    conf_line = sys.argv[1]

    rango_iryga_scheduler = RangoIrygaSchedulerModule(conf_line)
    rango_iryga_scheduler.start_work()
