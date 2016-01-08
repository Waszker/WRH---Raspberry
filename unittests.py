import unittest
import WRH_Engine.ScenarioManager.ScenarioManager as scenariomanager
import WRH_Engine.Utils.utils as utils
import time
from WRH_Engine.ScenarioManager.Scenario import Scenario
from WRH_Engine.ScenarioManager.Execution import Execution


class TestUtils(unittest.TestCase):

    def test_stub(self):
        self.assertEqual(1 == 1, True)

    def test_convert_datetime_to_python_correct(self):
        (success, datetime) = utils.convert_datetime_to_python("2015-12-14T16:23:30")
        self.assertEqual(success, True)
        self.assertEqual(datetime.year, 2015)
        self.assertEqual(datetime.month, 12)
        self.assertEqual(datetime.day, 14)
        self.assertEqual(datetime.hour, 16)
        self.assertEqual(datetime.minute, 23)
        self.assertEqual(datetime.second, 30)

    def test_convert_datetime_to_python_correctformat_incorrectlogic(self):
        (success, datetime) = utils.convert_datetime_to_python("2015-13-35T25:61:61")
        self.assertEqual(success, False)

    def test_convert_datetime_to_python_incorrect_date(self):
        (success, datetime) = utils.convert_datetime_to_python("2015-12-1416:23:30")
        self.assertEqual(success, False)

    def test_convert_datetime_to_python_nullorempty(self):
        (success, datetime) = utils.convert_datetime_to_python("")
        self.assertEqual(success, False)
        (success, datetime) = utils.convert_datetime_to_python(None)
        self.assertEqual(success, False)


class TestScenarioManager(unittest.TestCase):

    def test_get_active_scenarios_by_date_no_date(self):
        scenarios = []
        scen = Scenario(1, 1, 1, 1, 1, '', 'first', 1, 1, 1, None, '', 1)
        scenarios.append(scen)
        result = scenariomanager._get_active_scenarios_by_date(scenarios)
        self.assertEqual(len(result),  1)
        self.assertEqual(result[0].id,  1)

    def test_get_active_scenarios_by_date_ended(self):
        scenarios = []
        scen = Scenario(1, 1, 1, 1, 1, '', 'first', 1, 1, 1, None, utils.generate_proper_date(), 1)
        time.sleep(2)  # scenario ends
        scenarios.append(scen)
        result = scenariomanager._get_active_scenarios_by_date(scenarios)
        self.assertEqual(len(result),  0)

    def test_get_active_scenarios_by_priority(self):
        scenarios = []

        scen = Scenario(1, 1, 1, 1, 1, '', 'first', 1, 1, 7, None, '', 1)
        scenarios.append(scen)

        scen = Scenario(2, 1, 1, 1, 1, '', 'second', 3, 1, 7, None, '', 1)  # this
        scenarios.append(scen)

        scen = Scenario(3, 1, 1, 1, 1, '', 'third', 2, 1, 7, None, '', 1)
        scenarios.append(scen)

        scen = Scenario(4, 1, 1, 1, 1, '', 'fourth', 5, 1, 55, None, '', 1)  # this
        scenarios.append(scen)

        scen = Scenario(5, 1, 1, 1, 1, '', 'fifth', 5, 1, 55, None, '', 1)  # this
        scenarios.append(scen)

        result = scenariomanager._get_active_scenarios_by_priority(scenarios)
        self.assertEqual(len(result),  3)
        ids = [result[0].id, result[1].id, result[2].id]
        self.assertTrue(2 in ids)
        self.assertTrue(4 in ids)
        self.assertTrue(5 in ids)


if __name__ == '__main__':
    unittest.main()
