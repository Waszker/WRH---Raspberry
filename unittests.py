import unittest
import WRH_Engine.ScenarioManager.ScenarioManager as sm

class TestScenarioManager(unittest.TestCase):

	def test_stub(self):
		self.assertEqual(1 == 1, True)

	def test_convert_datetime_to_python_correct_date(self):
		(success, datetime) = sm._convert_datetime_to_python("2015-12-14T16:23:30")
		self.assertEqual(success, True)


if __name__ == '__main__':
    unittest.main()
