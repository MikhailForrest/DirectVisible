import math
from math import pi

RADIUS_OF_EARTH = 6378137 # радиус Земли в метрах WGS
ECCENTRICITY_OF_EARTH = 0.081819190842622 # эксцентриситет Земли в метрах WGS

#радиус эллипса по широте 
def N_rad(lat_in_degrees):
   return RADIUS_OF_EARTH/math.sqrt(1-math.pow(ECCENTRICITY_OF_EARTH,2)*math.pow(math.sin(lat_in_degrees*math.pi/180),2))

# X координата в декартовой системе
def X_space(latX_s,lonX_s,HX_s): #координаты в градусах / система WGS-8
   return (N_rad(latX_s)+HX_s)*math.cos(latX_s*math.pi/180)*math.cos(lonX_s*math.pi/180) # выдает в метрах в декартовой системе ECEF
# Y координата в декартовой системе
def Y_space(latY_s,lonY_s,HY_s):
   return (N_rad(latY_s)+HY_s)*math.cos(latY_s*math.pi/180)*math.sin(lonY_s*math.pi/180) # выдает в метрах в декартовой системе ECEF  
# Z координата в декартовой системе
def Z_space(latZ_s,HZ_s):
   return ((1-math.pow(ECCENTRICITY_OF_EARTH,2))*N_rad(latZ_s)+HZ_s)\
    *math.sin(latZ_s*math.pi/180) # выдает в метрах в декартовой системе ECEF

# Функция вычисления расстояния по декартовым координатам двух точек
def DistanceInDecart(X1,Y1,Z1,X2,Y2,Z2):
   return math.sqrt(math.pow((X1-X2),2)+math.pow((Y1-Y2),2)+math.pow((Z1-Z2),2)) #выдает в той же размерности, в какой координаты

# Функция вычисления расстояния по сферическим координатам двух точек
def DistanceInLatLonHeight(lat1,lon1,h1,lat2,lon2,h2): # в метрах
   x1 = X_space(lat1,lon1,h1) 
   y1 = Y_space(lat1,lon1,h1)
   z1 = Z_space(lat1,h1)
   x2 = X_space(lat2,lon2,h2) 
   y2 = Y_space(lat2,lon2,h2)
   z2 = Z_space(lat2,h2)
   return DistanceInDecart(x1,y1,z1,x2,y2,z2)


def XYZ_to_BLH(X_in_m, Y_in_m, Z_in_m): # пересчитывает декартовые глобальные в метрах в сферические в градусах
   asq1 = math.pow(RADIUS_OF_EARTH,2)
   esq = math.pow(ECCENTRICITY_OF_EARTH,2)
   b = math.sqrt(asq1*(1-esq))
   bsq = math.pow(b,2)
   ep = math.sqrt((asq1-bsq)/bsq)
   p = math.sqrt(math.pow(X_in_m,2)+math.pow(Y_in_m,2))
   th = math.atan2(RADIUS_OF_EARTH*Z_in_m,b*p)
   lonAlter = math.atan2(Y_in_m, X_in_m)
   latAlter = math.atan2((Z_in_m+ep*ep*b*math.pow(math.sin(th),3)),(p-esq*RADIUS_OF_EARTH*math.pow(math.cos(th),3)))
   NNN = RADIUS_OF_EARTH/(math.sqrt(1-esq*math.pow(math.sin(latAlter),2)))
   hAlter = p/math.cos(latAlter)-NNN
   latAlter*=(180/math.pi)
   lonAlter*=(180/math.pi) 
   if lonAlter<0: lonAlter+=360
   return [latAlter,lonAlter,hAlter]

# Функция определения азимута по двум географическим координатам
def azimut_LATLON(lat1,lat2,lon1,lon2):   # в градусах координаты
    try:
      cosGamma = math.cos(pi/2-pi*(lat1)/180)*math.cos(pi/2-pi*(lat2)/180)*(math.cos(pi*(lon1)/180-pi*(lon2)/180)-1)+\
        math.cos(pi*(lat1)/180-pi*(lat2)/180)
      if lon2>=lon1:
        sinGamma = math.sqrt(1-cosGamma*cosGamma)
      else:
        sinGamma = -math.sqrt(1-cosGamma*cosGamma)    
      if (sinGamma!=0) and (math.sin(pi/2-pi*(lat1)/180)!=0):
          helpovaya = (math.cos(pi/2-pi*(lat2)/180)-math.cos(pi/2-pi*(lat1)/180)*cosGamma)/\
            (sinGamma*math.sin(pi/2-pi*(lat1)/180))
          if sinGamma>0:
            return (180/pi)*math.acos(helpovaya)
          else:
            return 180+(180/pi)*math.acos(helpovaya)
      else:
        return 0
    except Exception:
       return 0

#Прямая геодезическая задача (по материалам Морозов "Курс сфероидической геодезии")
def Direct_Geodezian_Task(lat_in_Deg, azimuth_in_Deg, spherical_Distance_in_meters):
   phi1 = lat_in_Deg*pi/180 #Широта исходной точки в радианах
   alfa1 = azimuth_in_Deg*pi/180 #Азимут в радианах на искомую точку
   sigma = spherical_Distance_in_meters/RADIUS_OF_EARTH #Сферическое расстояние до искомой точки
   phi2 = math.asin(math.sin(phi1)*math.cos(sigma)+math.cos(phi1)*math.sin(sigma)*math.cos(alfa1)) # в радианах
   # lambd - разность долгот от исходной точки
   lambd = math.atan2(math.sin(sigma)*math.sin(alfa1),(math.cos(phi1)*math.cos(sigma)-math.sin(phi1)*math.sin(sigma)*math.cos(alfa1))) 
   alfa2 = math.atan2(math.cos(phi1)*math.sin(alfa1),(math.cos(phi1)*math.cos(sigma)*math.cos(alfa1)-math.sin(phi1)*math.sin(sigma)))
   return (180*phi2/pi,180*lambd/pi,180*alfa2/pi)

def hgtFilenameOfLatLong (lat,long): # функция определения 
    if lat >0:
        if math.floor(lat) <10:
            s = 'N0'+str(math.floor(lat))
        else:
            s = 'N'+str(math.floor(lat))
    else:
        if abs(math.floor(lat))<10:
            s = 'W0'+str(abs(math.floor(lat)))
        else:
            s = 'W'+str(abs(math.floor(lat)))
    if long >0: 
        if math.floor(long)<10:
            s = s+'E00'+str(math.floor(long))
        elif math.floor(long)<100:
            s = s+'E0'+str(math.floor(long))
        else:
            s = s+'E'+str(math.floor(long))
    return 'polls\\mapsHgt\\'+s+'.hgt'