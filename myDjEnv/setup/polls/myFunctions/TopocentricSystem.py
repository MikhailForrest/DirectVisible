import math
from math import pi
from .GeoFunctions import X_space as xDecart
from .GeoFunctions import Y_space as yDecart
from .GeoFunctions import Z_space as zDecart


class TopocentricSysCoord(object):
    def __init__(self, latCenter: float, lonCenter: float, hCenter: float):
        self.latCenter = latCenter
        self.lonCenter = lonCenter
        self.hCenter = hCenter
        self.XECEFCenter = xDecart(self.latCenter,self.lonCenter,self.hCenter)
        self.YECEFCenter = yDecart(self.latCenter,self.lonCenter,self.hCenter)
        self.ZECEFCenter = zDecart(self.latCenter,self.hCenter)
        self.matrixIn = [[0,0,0],[0,0,0],[0,0,0]]
        self.matrixIn[0][0] = -math.sin(pi*self.lonCenter/180)
        self.matrixIn[0][1] = math.cos(pi*self.lonCenter/180)
        self.matrixIn[0][2] = 0
        self.matrixIn[1][0] = -math.sin(pi*self.latCenter/180)*math.cos(pi*self.lonCenter/180)
        self.matrixIn[1][1] = -math.sin(pi*self.latCenter/180)*math.sin(pi*self.lonCenter/180)
        self.matrixIn[1][2] = math.cos(pi*self.latCenter/180)
        self.matrixIn[2][0] = math.cos(pi*self.latCenter/180)*math.cos(pi*self.lonCenter/180)
        self.matrixIn[2][1] = math.cos(pi*self.latCenter/180)*math.sin(pi*self.lonCenter/180)
        self.matrixIn[2][2] = math.sin(pi*self.latCenter/180)
        determinantFormatrixIn = self.matrixIn[0][0]*self.matrixIn[1][1]*self.matrixIn[2][2]+\
            self.matrixIn[0][1]*self.matrixIn[1][2]*self.matrixIn[2][0]+\
                self.matrixIn[0][2]*self.matrixIn[1][0]*self.matrixIn[2][1]-\
                    self.matrixIn[0][2]*self.matrixIn[1][1]*self.matrixIn[2][0]-\
                        self.matrixIn[0][1]*self.matrixIn[1][0]*self.matrixIn[2][2]-\
                            self.matrixIn[0][0]*self.matrixIn[2][1]*self.matrixIn[1][2]
        self.reverseOfmatrixIn = [[0,0,0],[0,0,0],[0,0,0]]
        if determinantFormatrixIn!=0:
            self.reverseOfmatrixIn[0][0] = (self.matrixIn[1][1]*self.matrixIn[2][2]-\
                                           self.matrixIn[1][2]*self.matrixIn[2][1])/determinantFormatrixIn
            self.reverseOfmatrixIn[1][0] = - (self.matrixIn[1][0]*self.matrixIn[2][2]-\
                                            self.matrixIn[2][0]*self.matrixIn[1][2])/determinantFormatrixIn
            self.reverseOfmatrixIn[2][0] = (self.matrixIn[1][0]*self.matrixIn[2][1]-\
                                           self.matrixIn[2][0]*self.matrixIn[1][1])/determinantFormatrixIn
            self.reverseOfmatrixIn[0][1] = -(self.matrixIn[0][1]*self.matrixIn[2][2]-\
                                            self.matrixIn[2][1]*self.matrixIn[0][2])/determinantFormatrixIn
            self.reverseOfmatrixIn[1][1] = (self.matrixIn[0][0]*self.matrixIn[2][2]-\
                                           self.matrixIn[2][0]*self.matrixIn[0][2])/determinantFormatrixIn
            self.reverseOfmatrixIn[2][1] = -(self.matrixIn[0][0]*self.matrixIn[2][1]-\
                                            self.matrixIn[2][0]*self.matrixIn[0][1])/determinantFormatrixIn
            self.reverseOfmatrixIn[0][2] = (self.matrixIn[0][1]*self.matrixIn[1][2]-\
                                           self.matrixIn[0][2]*self.matrixIn[1][1])/determinantFormatrixIn
            self.reverseOfmatrixIn[1][2] = -(self.matrixIn[0][0]*self.matrixIn[1][2]-\
                                            self.matrixIn[0][2]*self.matrixIn[1][0])/determinantFormatrixIn
            self.reverseOfmatrixIn[2][2] = (self.matrixIn[0][0]*self.matrixIn[1][1]-\
                                           self.matrixIn[0][1]*self.matrixIn[1][0])/determinantFormatrixIn

    def getUCoord(self, lat : float, long : float, height: float) -> float:
        xSpace = xDecart(lat,long,height)
        ySpace = yDecart(lat,long,height)
        zSpace = zDecart(lat,height)
        return (xSpace-self.XECEFCenter)*self.matrixIn[0][0]+\
            (ySpace-self.YECEFCenter)*self.matrixIn[0][1]+(zSpace-self.ZECEFCenter)*self.matrixIn[0][2]
    
    def getVCoord(self, lat : float, long : float, height: float) -> float:
        xSpace = xDecart(lat,long,height)
        ySpace = yDecart(lat,long,height)
        zSpace = zDecart(lat,height)
        return (xSpace-self.XECEFCenter)*self.matrixIn[1][0]+\
            (ySpace-self.YECEFCenter)*self.matrixIn[1][1]+(zSpace-self.ZECEFCenter)*self.matrixIn[1][2]
    
    def getWCoord(self, lat : float, long : float, height: float) -> float:
        xSpace = xDecart(lat,long,height)
        ySpace = yDecart(lat,long,height)
        zSpace = zDecart(lat,height)
        return (xSpace-self.XECEFCenter)*self.matrixIn[2][0]+\
            (ySpace-self.YECEFCenter)*self.matrixIn[2][1]+(zSpace-self.ZECEFCenter)*self.matrixIn[2][2]
    
    def getElevationInDeg(self, lat : float, long : float, height: float) -> float:
        return 180*math.atan(self.getWCoord(lat,long,height)/ \
                             (math.sqrt(\
                                 math.pow(self.getUCoord(lat,long,height),2) + math.pow(self.getVCoord(lat,long,height),2)\
                                    )))/pi
