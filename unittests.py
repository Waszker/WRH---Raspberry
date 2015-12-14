import unittest
import WRH_Engine.ScenarioManager.ScenarioManager as scenariomanager
import WRH_Engine.Utils.utils as utils

class TestScenarioManager(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
