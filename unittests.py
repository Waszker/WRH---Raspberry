import unittest
import WRH_Engine.ScenarioManager.ScenarioManager as scenariomanager
import WRH_Engine.Utils.utils as utils

class TestUtils(unittest.TestCase):

	def test_stub(self):
		self.assertEqual(1 == 1, True)

	def test_convert_datetime_to_python_correct(self):
		(success, datetime) = utils._convert_datetime_to_python("2015-12-14T16:23:30")
		self.assertEqual(success, True)
		self.assertEqual(datetime.year, 2015)
		self.assertEqual(datetime.month, 12)
		self.assertEqual(datetime.day, 14)
		self.assertEqual(datetime.hour, 16)
		self.assertEqual(datetime.minute, 23)
		self.assertEqual(datetime.second, 30)
	
	def test_convert_datetime_to_python_correctformat_incorrectlogic(self):
		(success, datetime) = utils._convert_datetime_to_python("2015-13-35T25:61:61")
		self.assertEqual(success, False)

	def test_convert_datetime_to_python_incorrect_date(self):
		(success, datetime) = utils._convert_datetime_to_python("2015-12-1416:23:30")
		self.assertEqual(success, False)
	
	def test_convert_datetime_to_python_nullorempty(self):
		(success, datetime) = utils._convert_datetime_to_python("")
		self.assertEqual(success, False)
		(success, datetime) = utils._convert_datetime_to_python(None)
		self.assertEqual(success, False)

class TestScenarioManager(unittest.TestCase):
	
	def test_get_active_scenarios_by_date(self):
		scenarios = []
		scen = {"Id" : 1,  "Name" : "pierwszy",  "startDate" : None,  "endDate" : ''}
		scenarios.append(scen)
		result = scenariomanager._get_active_scenarios_by_date(scenarios)
		self.assertEqual(len(result),  1)
		self.assertEqual(result[0]["Id"],  1)

if __name__ == '__main__':
    unittest.main()
