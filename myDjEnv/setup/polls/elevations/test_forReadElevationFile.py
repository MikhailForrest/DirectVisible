import unittest
from forReadElevationFile import readElevationFile

class Test_forReadElevationFile(unittest.TestCase): # py testmyfunc.py -v
    def test_readElevationFile(self):
        self.assertEqual(readElevationFile('polls\elevations\dvorSVO.xlsx')['azimuts'][0],0.7833333333333333)
        self.assertEqual(readElevationFile('polls\elevations\dvorSVO.xlsx')['elevations'][0],2.56666666666667)
        self.assertEqual(readElevationFile('polls\elevations\dvorSVO.xlsx')['azimuts'][568],358.65)
        self.assertEqual(readElevationFile('polls\elevations\dvorSVO.xlsx')['elevations'][568],2.8)

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()