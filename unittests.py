import unittest
import WRH_Engine.ScenarioManager.ScenarioManager

class TestStringMethods(unittest.TestCase):

  def test_upper(self):
      self.assertEqual('foo'.upper(), 'FOO')


if __name__ == '__main__':
    unittest.main()
