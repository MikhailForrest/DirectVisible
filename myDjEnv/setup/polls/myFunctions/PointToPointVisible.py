import math
from math import pi 
from . import GeoFunctions
from . import myFunc
from . import workWithData

# функция вытаскивания значения высоты из файлов - медленная - использовать только для одиночных редких обращений
def heightFromLatLon (lat, lon):
    # определяем из какого файла берем значение
    s = GeoFunctions.hgtFilenameOfLatLong(lat, lon)       
    data = open(s,'rb') #'polls\\mapsHgt\\N54E042.hgt'
    ss = data.read()
    x_bi =1200.0*(lon-math.floor(lon)) # 1201*1201 размерность одного файла hgt с шагом 3 секунды по два байта// долгота - столбцы
    y_bi =(1200.0*(math.floor(lat)+1-lat))  # широта строки
    x1_bi = math.floor(x_bi)    
    x2_bi = x1_bi+1
    y1_bi = math.floor(y_bi)
    y2_bi = y1_bi+1
    #return s+'; '+str('{:7.4f}'.format(x_bi))+'; '+str('{:7.4f}'.format(y_bi))
    if (x2_bi<1201) and (y2_bi<1201):
        q11 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[y1_bi*1201*2+x1_bi*2]<128 else \
            (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
        q12 = (ss[y2_bi*1201*2+x1_bi*2])*256+(ss[y2_bi*1201*2+x1_bi*2+1]) if ss[y1_bi*1201*2+x1_bi*2]<128 else \
            (ss[y2_bi*1201*2+x1_bi*2]-256)*256+(ss[y2_bi*1201*2+x1_bi*2+1])
        q21 = (ss[y1_bi*1201*2+x2_bi*2])*256+(ss[y1_bi*1201*2+x2_bi*2+1]) if ss[y1_bi*1201*2+x2_bi*2]<128 else \
            (ss[y1_bi*1201*2+x2_bi*2]-256)*256+(ss[y1_bi*1201*2+x2_bi*2+1])
        q22 = (ss[y2_bi*1201*2+x2_bi*2])*256+(ss[y2_bi*1201*2+x2_bi*2+1]) if ss[y2_bi*1201*2+x2_bi*2]<128 else \
            (ss[y2_bi*1201*2+x2_bi*2]-256)*256+(ss[y2_bi*1201*2+x2_bi*2+1])
        s = myFunc.bilinean_interpolation(x1_bi,y1_bi,x2_bi,y2_bi,q11,q12,q21,q22,x_bi,y_bi)
    elif (y2_bi<1201):
        q1 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[y1_bi*1201*2+x1_bi*2]<128 else \
            (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
        q2 = (ss[y2_bi*1201*2+x1_bi*2])*256+(ss[y2_bi*1201*2+x1_bi*2+1]) if ss[y2_bi*1201*2+x1_bi*2]<128 else \
            (ss[y2_bi*1201*2+x1_bi*2]-256)*256+(ss[y2_bi*1201*2+x1_bi*2+1])
        s = q1+(q2-q1)*(y_bi-y1_bi)/(y2_bi-y1_bi)
    elif (x2_bi<1201):
        q1 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[y1_bi*1201*2+x1_bi*2]<128 else \
            (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
        q2 = (ss[y1_bi*1201*2+x2_bi*2])*256+(ss[y1_bi*1201*2+x2_bi*2+1]) if ss[y1_bi*1201*2+x2_bi*2]<128 else \
            (ss[y1_bi*1201*2+x2_bi*2]-256)*256+(ss[y1_bi*1201*2+x2_bi*2+1])
        s = q1+(q2-q1)*(x_bi-x1_bi)/(x2_bi-x1_bi)
    else:
        s = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[y1_bi*1201*2+x1_bi*2]<128 else \
            (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
    return s


# функция определения прямой геометрической видимости
def DirVisUnit(lat0, lon0, h0, lat, lon, h, limitOfDistance, fileOfHGT, useUsersObj): # широты и долготы в градусах
                           # limitOfDistance в км - ограничение по расстоянию сверху, если дистанция выше, то прямой видимости нет     
    innerBool = True #если встретит препятствие. то станет ложью: для результата функции
    deltaB = abs(lat0-lat)
    deltaL = abs(lon0-lon)
    if (deltaL>0.05) and (deltaB>0.05):
        stepB = pi/(240*180) # в радианах
        stepL = pi/(240*180) # в радианах
    elif (deltaB>0.05):
        stepB = pi/(240*180) 
        stepL = pi/(240*180*20) 
    elif (deltaL>0.05):
        stepB = pi/(240*180*20) 
        stepL = pi/(240*180)
    else:
        stepB = pi/(240*180*20) 
        stepL = pi/(240*180*20) 
    
    # далее координаты в метрах
    point_Home = [GeoFunctions.X_space(lat0, lon0, h0), GeoFunctions.Y_space(lat0, lon0, h0), GeoFunctions.Z_space(lat0, h0)]
    point_End = [GeoFunctions.X_space(lat, lon, h), GeoFunctions.Y_space(lat, lon, h), GeoFunctions.Z_space(lat, h)]

    # далее определяем параметр ограничения дальности - либо введенный в параметры, \
    # если он меньше оценочного - по формуле дальности от высот антенн для положительной рефракции
    if limitOfDistance>0:
        if limitOfDistance>4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h))): # в км
            limitD = 4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h)))
        else:
            limitD = limitOfDistance
    else:
        limitD = 4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h)))
    data = open(fileOfHGT,'rb') #'polls\\mapsHgt\\N54E042.hgt'
    ss = data.read()
    if GeoFunctions.DistanceInDecart(point_Home[0],point_Home[1],point_Home[2],point_End[0],point_End[1],point_End[2])/1000<limitD:
        # далее условия поиска по какой оси больше перепад координаты, чтобы потом по ней разбивать
        if (abs(point_Home[0]-point_End[0])>=abs(point_Home[1]-point_End[1])) and \
            (abs(point_Home[0]-point_End[0])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по X
            # опреление шага итерации по оси X - строго положительное
            delta_x = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.cos(lon0*pi/180))*stepB),\
                    abs((-(GeoFunctions.N_rad(lat0))*math.cos(lat0*pi/180)*math.sin(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.cos(lon*pi/180))*stepB),\
                            abs((-(GeoFunctions.N_rad(lat))*math.cos(lat*pi/180)*math.sin(lon*pi/180))*stepL))/2
            if point_Home[0]<=point_End[0]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_x *=sign_
            x = point_Home[0]
            i = 0
            while sign_*x<=sign_*point_End[0]:
                y = point_Home[1]+(point_End[1]-point_Home[1])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                x_bi =1200*(current_point[1]-42) # 1201*1201 размерность одного файла hgt с шагом 3 секунды по два байта// долгота - столбцы
                y_bi =1200*(55-current_point[0])  # широта строки
                x1_bi = math.trunc(x_bi)    
                x2_bi = x1_bi+1
                y1_bi = math.trunc(y_bi)
                y2_bi = y1_bi+1
                q11 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
                q12 = (ss[y2_bi*1201*2+x1_bi*2])*256+(ss[y2_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x1_bi*2]-256)*256+(ss[y2_bi*1201*2+x1_bi*2+1])
                q21 = (ss[y1_bi*1201*2+x2_bi*2])*256+(ss[y1_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x2_bi*2]-256)*256+(ss[y1_bi*1201*2+x2_bi*2+1])
                q22 = (ss[y2_bi*1201*2+x2_bi*2])*256+(ss[y2_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x2_bi*2]-256)*256+(ss[y2_bi*1201*2+x2_bi*2+1])
                s = myFunc.bilinean_interpolation(x1_bi,y1_bi,x2_bi,y2_bi,q11,q12,q21,q22,x_bi,y_bi)
                if s >= current_point[2]:
                    innerBool = False # будет означать, что нет прямой видимости
                    break
                x+=delta_x
                i+=1
        elif (abs(point_Home[1]-point_End[1])>=abs(point_Home[0]-point_End[0])) and \
            (abs(point_Home[1]-point_End[1])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по Y
            delta_y = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.sin(lon0*pi/180))*stepB),\
                    abs((GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*math.cos(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.sin(lon*pi/180))*stepB),\
                            abs((GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*math.cos(lon*pi/180))*stepL))/2
            if point_Home[1]<point_End[1]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_y *=sign_
            y = point_Home[1]
            i = 0
            while sign_*y<=sign_*point_End[1]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                x_bi =1200*(current_point[1]-42) # 1201*1201 размерность одного файла hgt с шагом 3 секунды по два байта// долгота - столбцы
                y_bi =1200*(55-current_point[0])  # широта строки
                x1_bi = math.trunc(x_bi)    
                x2_bi = x1_bi+1
                y1_bi = math.trunc(y_bi)
                y2_bi = y1_bi+1
                q11 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
                q12 = (ss[y2_bi*1201*2+x1_bi*2])*256+(ss[y2_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x1_bi*2]-256)*256+(ss[y2_bi*1201*2+x1_bi*2+1])
                q21 = (ss[y1_bi*1201*2+x2_bi*2])*256+(ss[y1_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x2_bi*2]-256)*256+(ss[y1_bi*1201*2+x2_bi*2+1])
                q22 = (ss[y2_bi*1201*2+x2_bi*2])*256+(ss[y2_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x2_bi*2]-256)*256+(ss[y2_bi*1201*2+x2_bi*2+1])
                s = myFunc.bilinean_interpolation(x1_bi,y1_bi,x2_bi,y2_bi,q11,q12,q21,q22,x_bi,y_bi)
                if s >= current_point[2]:
                    innerBool = False # будет означать, что нет прямой видимости
                    break
                y+=delta_y
                i+=1
        else: #тут должно быть больше по Z
            delta_z = max(abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                              GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*stepB),\
                                abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                                    GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*stepB))/2
            if point_Home[2]<point_End[2]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_z *=sign_
            z = point_Home[2]
            i = 0
            while sign_*z<=sign_*point_End[2]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                y = point_Home[1]+(point_End[1]-point_Home[1])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                x_bi =1200*(current_point[1]-42) # 1201*1201 размерность одного файла hgt с шагом 3 секунды по два байта// долгота - столбцы
                y_bi =1200*(55-current_point[0])  # широта строки
                x1_bi = math.trunc(x_bi)    
                x2_bi = x1_bi+1
                y1_bi = math.trunc(y_bi)
                y2_bi = y1_bi+1
                q11 = (ss[y1_bi*1201*2+x1_bi*2])*256+(ss[y1_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x1_bi*2]-256)*256+(ss[y1_bi*1201*2+x1_bi*2+1])
                q12 = (ss[y2_bi*1201*2+x1_bi*2])*256+(ss[y2_bi*1201*2+x1_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x1_bi*2]-256)*256+(ss[y2_bi*1201*2+x1_bi*2+1])
                q21 = (ss[y1_bi*1201*2+x2_bi*2])*256+(ss[y1_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y1_bi*1201*2+x2_bi*2]-256)*256+(ss[y1_bi*1201*2+x2_bi*2+1])
                q22 = (ss[y2_bi*1201*2+x2_bi*2])*256+(ss[y2_bi*1201*2+x2_bi*2+1]) if ss[0]<128 else \
                        (ss[y2_bi*1201*2+x2_bi*2]-256)*256+(ss[y2_bi*1201*2+x2_bi*2+1])
                s = myFunc.bilinean_interpolation(x1_bi,y1_bi,x2_bi,y2_bi,q11,q12,q21,q22,x_bi,y_bi)
                if s >= current_point[2]:
                    innerBool = False # будет означать, что нет прямой видимости
                    break
                z+=delta_z
                i+=1
    else:
        return False
    return innerBool


# функция определения прямой геометрической видимости без обращения к файлу высот
def DirVisUnit_0(lat0, lon0, h0, lat, lon, h, limitOfDistance, useUsersObj): # широты и долготы в градусах
                           # limitOfDistance в км - ограничение по расстоянию сверху, если дистанция выше, то прямой видимости нет     
    innerBool = True #если встретит препятствие. то станет ложью: для результата функции
    deltaB = abs(lat0-lat)
    deltaL = abs(lon0-lon)
    if (deltaL>0.05) and (deltaB>0.05):
        stepB = pi/(240*180) # в радианах
        stepL = pi/(240*180) # в радианах
    elif (deltaB>0.05):
        stepB = pi/(240*180) 
        stepL = pi/(240*180*20) 
    elif (deltaL>0.05):
        stepB = pi/(240*180*20) 
        stepL = pi/(240*180)
    else:
        stepB = pi/(240*180*20) 
        stepL = pi/(240*180*20) 
    
    # далее координаты в метрах
    point_Home = [GeoFunctions.X_space(lat0, lon0, h0), GeoFunctions.Y_space(lat0, lon0, h0), GeoFunctions.Z_space(lat0, h0)]
    point_End = [GeoFunctions.X_space(lat, lon, h), GeoFunctions.Y_space(lat, lon, h), GeoFunctions.Z_space(lat, h)]

    # далее определяем параметр ограничения дальности - либо введенный в параметры, \
    # если он меньше оценочного - по формуле дальности от высот антенн для положительной рефракции
    if limitOfDistance>0:
        if limitOfDistance>4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h))): # в км
            limitD = 4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h)))
        else:
            limitD = limitOfDistance
    else:
        limitD = 4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h)))
    if GeoFunctions.DistanceInDecart(point_Home[0],point_Home[1],point_Home[2],point_End[0],point_End[1],point_End[2])/1000<limitD:
        # далее условия поиска по какой оси больше перепад координаты, чтобы потом по ней разбивать
        if (abs(point_Home[0]-point_End[0])>=abs(point_Home[1]-point_End[1])) and \
            (abs(point_Home[0]-point_End[0])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по X
            # опреление шага итерации по оси X - строго положительное
            delta_x = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.cos(lon0*pi/180))*stepB),\
                    abs((-(GeoFunctions.N_rad(lat0))*math.cos(lat0*pi/180)*math.sin(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.cos(lon*pi/180))*stepB),\
                            abs((-(GeoFunctions.N_rad(lat))*math.cos(lat*pi/180)*math.sin(lon*pi/180))*stepL))/2
            if point_Home[0]<=point_End[0]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_x *=sign_
            x = point_Home[0]
            i = 0
            while sign_*x<=sign_*point_End[0]:
                y = point_Home[1]+(point_End[1]-point_Home[1])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                s= heightFromLatLon(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                x+=delta_x
                i+=1
        elif (abs(point_Home[1]-point_End[1])>=abs(point_Home[0]-point_End[0])) and \
            (abs(point_Home[1]-point_End[1])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по Y
            delta_y = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.sin(lon0*pi/180))*stepB),\
                    abs((GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*math.cos(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.sin(lon*pi/180))*stepB),\
                            abs((GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*math.cos(lon*pi/180))*stepL))/2
            if point_Home[1]<point_End[1]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_y *=sign_
            y = point_Home[1]
            i = 0
            while sign_*y<=sign_*point_End[1]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                s= heightFromLatLon(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                y+=delta_y
                i+=1
        else: #тут должно быть больше по Z
            delta_z = max(abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                              GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*stepB),\
                                abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                                    GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*stepB))/2
            if point_Home[2]<point_End[2]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_z *=sign_
            z = point_Home[2]
            i = 0
            while sign_*z<=sign_*point_End[2]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                y = point_Home[1]+(point_End[1]-point_Home[1])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                s= heightFromLatLon(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                z+=delta_z
                i+=1
    else:
        return False
    return innerBool

def DirVisUnit_1(lat0, lon0, h0, lat, lon, h, dataForComputing: workWithData.DataForComputing, useUsersObj): # широты и долготы в градусах
                           # limitOfDistance в км - ограничение по расстоянию сверху, если дистанция выше, то прямой видимости нет     
    innerBool = True #если встретит препятствие. то станет ложью: для результата функции
    deltaB = abs(lat0-lat)
    deltaL = abs(lon0-lon)
    if (deltaL>0.05) and (deltaB>0.05):
        stepB = pi/(240*180) # в радианах
        stepL = pi/(240*180) # в радианах
    elif (deltaB>0.05):
        stepB = pi/(240*180) 
        if (deltaL>0.025):
            stepL = pi/(240*180*20)
        else: 
            stepL = pi/(240*180*100)       
    elif (deltaL>0.05):
        if (deltaB>0.025):
            stepB = pi/(240*180*20)
        else: 
            stepB = pi/(240*180*100)  
        stepL = pi/(240*180)
    else:
        if (deltaB>0.025):
            stepB = pi/(240*180*20)
        else: 
            stepB = pi/(240*180*100) 
        if (deltaL>0.025):
            stepL = pi/(240*180*20)
        else: 
            stepL = pi/(240*180*100)   
    # далее координаты в метрах
    point_Home = [GeoFunctions.X_space(lat0, lon0, h0), GeoFunctions.Y_space(lat0, lon0, h0), GeoFunctions.Z_space(lat0, h0)]
    point_End = [GeoFunctions.X_space(lat, lon, h), GeoFunctions.Y_space(lat, lon, h), GeoFunctions.Z_space(lat, h)]

    # далее определяем параметр ограничения дальности - либо введенный в параметры, \  
    limitD = dataForComputing.dMax#4.2*(math.sqrt(abs(h0))+math.sqrt(abs(h)))

    if GeoFunctions.DistanceInDecart(point_Home[0],point_Home[1],point_Home[2],point_End[0],point_End[1],point_End[2])/1000<limitD:
        # далее условия поиска по какой оси больше перепад координаты, чтобы потом по ней разбивать
        if (abs(point_Home[0]-point_End[0])>=abs(point_Home[1]-point_End[1])) and \
            (abs(point_Home[0]-point_End[0])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по X
            # опреление шага итерации по оси X - строго положительное
            delta_x = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.cos(lon0*pi/180))*stepB),\
                    abs((-(GeoFunctions.N_rad(lat0))*math.cos(lat0*pi/180)*math.sin(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.cos(lon*pi/180))*stepB),\
                            abs((-(GeoFunctions.N_rad(lat))*math.cos(lat*pi/180)*math.sin(lon*pi/180))*stepL))/2
            if point_Home[0]<=point_End[0]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_x *=sign_
            x = point_Home[0]
            i = 0
            while sign_*x<=sign_*point_End[0]:
                y = point_Home[1]+(point_End[1]-point_Home[1])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(x-point_Home[0])/(point_End[0]-point_Home[0])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                if useUsersObj:
                    s= dataForComputing.get_height_with_user_objects(current_point[0], current_point[1])
                else:
                    s= dataForComputing.get_height(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                x+=delta_x
                i+=1
        elif (abs(point_Home[1]-point_End[1])>=abs(point_Home[0]-point_End[0])) and \
            (abs(point_Home[1]-point_End[1])>=abs(point_Home[2]-point_End[2])): #тут должно быть больше по Y
            delta_y = max(\
                abs((-(GeoFunctions.N_rad(lat0))*math.sin(lat0*pi/180)*math.sin(lon0*pi/180))*stepB),\
                    abs((GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*math.cos(lon0*pi/180))*stepL),\
                        abs((-(GeoFunctions.N_rad(lat))*math.sin(lat*pi/180)*math.sin(lon*pi/180))*stepB),\
                            abs((GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*math.cos(lon*pi/180))*stepL))/2
            if point_Home[1]<point_End[1]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_y *=sign_
            y = point_Home[1]
            i = 0
            while sign_*y<=sign_*point_End[1]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                z = point_Home[2]+(point_End[2]-point_Home[2])*(y-point_Home[1])/(point_End[1]-point_Home[1])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                if useUsersObj:
                    s= dataForComputing.get_height_with_user_objects(current_point[0], current_point[1])
                else:
                    s= dataForComputing.get_height(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                y+=delta_y
                i+=1
        else: #тут должно быть больше по Z
            delta_z = max(abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                              GeoFunctions.N_rad(lat0)*math.cos(lat0*pi/180)*stepB),\
                                abs((1-math.pow(GeoFunctions.ECCENTRICITY_OF_EARTH,2))*\
                                    GeoFunctions.N_rad(lat)*math.cos(lat*pi/180)*stepB))/2
            if point_Home[2]<point_End[2]: 
                sign_ = 1 
            else: 
                sign_ = -1
            delta_z *=sign_
            z = point_Home[2]
            i = 0
            while sign_*z<=sign_*point_End[2]:
                x = point_Home[0]+(point_End[0]-point_Home[0])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                y = point_Home[1]+(point_End[1]-point_Home[1])*(z-point_Home[2])/(point_End[2]-point_Home[2])
                current_point = GeoFunctions.XYZ_to_BLH(x,y,z) # точка в сферических координатах
                if useUsersObj:
                    s= dataForComputing.get_height_with_user_objects(current_point[0], current_point[1])
                else:
                    s= dataForComputing.get_height(current_point[0], current_point[1])
                if s >= current_point[2]:
                    return False # будет означать, что нет прямой видимости
                z+=delta_z
                i+=1
    else:
        return False
    return innerBool
