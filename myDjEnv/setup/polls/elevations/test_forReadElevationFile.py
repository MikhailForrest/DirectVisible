import unittest
from forReadElevationFile import readElevationFile
from scipy.interpolate import CubicSpline as cs
from scipy.interpolate import interp1d as i1d
class Test_forReadElevationFile(unittest.TestCase): # py testmyfunc.py -v
    def test_readElevationFile(self):
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['azimuts'][0],0)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['elevations'][0],0)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['azimuts'][536],358.65)
        self.assertEqual(readElevationFile('dvorSVO.xlsx')['elevations'][536],2.8)
        # cs0 = cs(readElevationFile('dvorSVO.xlsx')['azimuts'],readElevationFile('dvorSVO.xlsx')['elevations'], axis=0, bc_type='periodic')
        # for i in range (0,355,5):
        #    print(cs0(i))
        # self.assertGreater(cs0(101.7),0.867)
        # self.assertLess(cs0(101.7),1.5666667)
        i1d0 = i1d(readElevationFile('dvorSVO.xlsx')['azimuts'],readElevationFile('dvorSVO.xlsx')['elevations'])
        for i in range (0,355,5):
            print(i1d0(i))

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()