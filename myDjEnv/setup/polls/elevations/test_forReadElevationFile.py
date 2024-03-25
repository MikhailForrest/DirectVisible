import unittest
from forReadElevationFile import readElevationFile
from scipy.interpolate import CubicSpline as cs

class Test_forReadElevationFile(unittest.TestCase): # py testmyfunc.py -v
    def test_readElevationFile(self):
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['azimuts'][0],0.7833333333333333)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['elevations'][0],2.56666666666667)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['azimuts'][535],358.65)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['elevations'][535],2.8)
        cs0 = cs(readElevationFile('dvorSVO.xlsx')['azimuts'],readElevationFile('dvorSVO.xlsx')['elevations'])

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()