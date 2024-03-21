import unittest
from forReadElevationFile import readElevationFile

class Test_forReadElevationFile(unittest.TestCase): # py testmyfunc.py -v
    def test_readElevationFile(self):
        self.assertEqual(readElevationFile('polls\elevations\dvorSVO.xlsx')['azimuts'][0],0.7833333333333333)
#2,56666666666667
# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()