import math
from .GeoFunctions import Direct_Geodezian_Task
from .GeoFunctions import hgtFilenameOfLatLong
from .myFunc import bilinean_interpolation
from .myFunc import intersect_rectangles
from .myFunc import intersect_two_segments
from polls.models import AirportBuilding 
import json
from .GeoFunctions import Direct_Geodezian_Task
from .myFunc import intersect_direct_intervals
from . import PointToPointVisible

class DataForComputing(object):
    def __init__(self, lat_center_indeg: float, long_center_indeg: float, h_center_inmeters: float, \
                 h_flight_inmeters: float, limitOfDistInKm: float):
        self.lat_center = lat_center_indeg
        self.long_center = long_center_indeg
        self.h_center = h_center_inmeters
        self.h_flight = h_flight_inmeters
        if 4.2*(math.sqrt(h_center_inmeters+PointToPointVisible.heightFromLatLon(lat_center_indeg,long_center_indeg))+math.sqrt(h_flight_inmeters))*1000>limitOfDistInKm*1000:
            self.dMax=limitOfDistInKm*1000
        else:
            self.dMax = 4.2*(math.sqrt(h_center_inmeters+PointToPointVisible.heightFromLatLon(lat_center_indeg,long_center_indeg))+math.sqrt(h_flight_inmeters))*1000

        (north_point_lat, north_point_dlon,north_point_alfa) = Direct_Geodezian_Task(self.lat_center,0,self.dMax)
        (east_point_lat, east_point_dlon,east_point_alfa) = Direct_Geodezian_Task(self.lat_center,90,self.dMax)
        (south_point_lat, south_point_dlon,south_point_alfa) = Direct_Geodezian_Task(self.lat_center,180,self.dMax)
        (west_point_lat, west_point_dlon, west_point_alfa) = Direct_Geodezian_Task(self.lat_center,270,self.dMax)

        self.max_lat = max(north_point_lat, east_point_lat, south_point_lat, west_point_lat)
        self.min_lat = min(north_point_lat, east_point_lat, south_point_lat, west_point_lat)
        self.min_long = min(self.long_center+north_point_dlon, self.long_center+east_point_dlon, \
                           self.long_center+south_point_dlon, self.long_center+west_point_dlon)
        self.max_long = max(self.long_center+north_point_dlon, self.long_center+east_point_dlon, \
                           self.long_center+south_point_dlon, self.long_center+west_point_dlon)
        
        (self.int_min_lat, self.int_max_lat, self.int_min_long, self.int_max_long) = (math.trunc(self.min_lat), math.trunc(self.max_lat),\
                                                                                      math.trunc(self.min_long), math.trunc(self.max_long))
        
        self.dir_lat = (self.int_max_lat-self.int_min_lat+1) # размерность данных по вертикали количесвто файлов в столбиках
        self.dir_lon = (self.int_max_long-self.int_min_long+1) # размерность данных по вертикали количесвто файлов в строках
       
        try:
            data = open(hgtFilenameOfLatLong(self.int_max_lat,self.int_min_long),'rb')
            self.ss = data.read()
        except:
            data = open('polls\\mapsHgt\\NNNEEEE.hgt','rb') #файл с нулевыми значениями
            self.ss = data.read()
        i = self.int_max_lat
        while i>=self.int_min_lat:
            for j in range(self.int_min_long, self.int_max_long+1):
                if (i==self.int_max_lat and j==self.int_min_long):
                    pass
                else:
                    try:
                        data = open(hgtFilenameOfLatLong(i,j),'rb')
                        self.ss += data.read()
                    except:
                        # raise ValueError('нет файла '+hgtFilenameOfLatLong(i,j))
                        data = open('polls\\mapsHgt\\NNNEEEE.hgt','rb') #файл с нулевыми значениями
                        self.ss += data.read()
            i-=1 
        self.arrOfAirportBiulding = []
        for airport in AirportBuilding.objects.all():
            if intersect_rectangles(airport.min_lat,airport.max_lat,airport.min_lon,airport.max_lon,\
                                    self.min_lat, self.max_lat, self.min_long, self.max_long):
                self.arrOfAirportBiulding.append(json.loads(airport.polygons))
        
    def get_height(self, lat : float, long : float) -> float:       
        x_bi =1200.0*(long-math.trunc(long)) # 1201*1201 размерность одного файла hgt с шагом 3 секунды по два байта// долгота - столбцы
        y_bi =(1200.0*(math.trunc(lat)+1-lat))  # широта строки
        x1_bi = math.trunc(x_bi)    
        x2_bi = x1_bi+1
        y1_bi = math.trunc(y_bi)
        y2_bi = y1_bi+1
        pointInAngles = [[0.0,0.0],[0.0,0.0]]
        pointInAngles[0][0] = math.trunc(x_bi) #x1_bi
        pointInAngles[0][1] = math.trunc(y_bi) #y1_bi
        pointInAngles[1][0] = pointInAngles[0][0]+1 #x2_bi
        pointInAngles[1][1] = pointInAngles[0][1]+1 #y2_bi
        pre_memory = 1201*2*1201*(self.dir_lon*(math.trunc(self.int_max_lat+1-lat))+math.trunc(long-self.int_min_long))

        if (lat!=math.trunc(lat)) and (long!=math.trunc(long)):
            
            q = [[0.0,0.0],[0.0,0.0]]
            for i in range(0,2): # по X #Далее вытаскиваем значения в узлах прямоугольника (данных в сетке высот) в котором лежит точка
                for j in range(0,2): # по Y
                    q[i][j] = (self.ss[pre_memory+ pointInAngles[j][1]*1201*2+pointInAngles[i][0]*2])*256+\
                        (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[i][0]*2+1]) \
                            if self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[i][0]*2]<128 \
                                  else (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[i][0]*2]-256)*256+\
                                    (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[i][0]*2+1])
            res = bilinean_interpolation(x1_bi,y1_bi,x2_bi,y2_bi,q[0][0],q[0][1],q[1][0],q[1][1],x_bi,y_bi)
            return res
        if (lat!=math.trunc(lat)) and (long==math.trunc(long)):
            q = [[0.0,0.0],[0.0,0.0]]
            for j in range(0,2): # по Y
                q[0][j] = (self.ss[pre_memory+ pointInAngles[j][1]*1201*2+pointInAngles[0][0]*2])*256+\
                    (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[0][0]*2+1]) \
                        if self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[0][0]*2]<128 \
                                else (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[0][0]*2]-256)*256+\
                                (self.ss[pre_memory+pointInAngles[j][1]*1201*2+pointInAngles[0][0]*2+1])
            res = q[0][0]+(q[0][1]-q[0][0])*(y_bi-pointInAngles[0][1])/(pointInAngles[1][1]-pointInAngles[0][1])
            return res
        
        #работает неправильно
        if (long!=math.trunc(long)) and (lat==math.trunc(lat)):
            q = [[0.0,0.0],[0.0,0.0]]
            pre_memory = pre_memory-1201*1201*2*self.dir_lon
            for i in range(0,2): # по X #Далее вытаскиваем значения в узлах прямоугольника (данных в сетке высот) в котором лежит точка
                q[i][0] = (self.ss[pre_memory+ pointInAngles[0][1]*1201*2+pointInAngles[i][0]*2])*256+\
                    (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[i][0]*2+1]) \
                        if self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[i][0]*2]<128 \
                                else (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[i][0]*2]-256)*256+\
                                (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[i][0]*2+1])
            res = q[0][0]+(q[1][0]-q[0][0])*(x_bi-pointInAngles[0][0])/(pointInAngles[1][0]-pointInAngles[0][0])
            return res
        
        if (long==math.trunc(long)) and (lat==math.trunc(lat)):
            q00= (self.ss[pre_memory+ pointInAngles[0][1]*1201*2+pointInAngles[0][0]*2])*256+\
                        (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[0][0]*2+1]) \
                            if self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[0][0]*2]<128 \
                                  else (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[0][0]*2]-256)*256+\
                                    (self.ss[pre_memory+pointInAngles[0][1]*1201*2+pointInAngles[0][0]*2+1])
            return q00
        

    def get_height_with_user_objects(self, lat : float, long : float) -> float:
        h0 = self.get_height(lat,long)
        build_in = [] #Сюда будут сыпаться конкретные здания
        for building in self.arrOfAirportBiulding:
            for item in building.keys():
                if (lat<building[item]['max_lt_b']) and (lat>building[item]['min_lt_b']) \
                    and (long<building[item]['max_ln_b']) and (long>building[item]['min_ln_b']):
                      #проверка, 
                      build_in.append(building[item])
        if len(build_in)>0:
            # сейчас упрощенно - потом добавить анализ на содержание точки внутри многоугольника
            for item_b in build_in:
                #определим точку, относительно которой будем считать пересечения луча из точки со сторонами здания
                lat0 = item_b['max_lt_b']+(item_b['max_lt_b']-item_b['min_lt_b'])/2
                lon0 = (item_b['max_ln_b']+item_b['min_ln_b'])/2
                counter_intersection = 0
                for i in range(0,len(item_b['p']['polygon'])-1):
                    if intersect_two_segments(lat0,lon0,lat,long,item_b['p']['polygon'][i][0],item_b['p']['polygon'][i][1],\
                                              item_b['p']['polygon'][i+1][0],item_b['p']['polygon'][i+1][1]):
                        counter_intersection += 1
                
                if counter_intersection % 2 == 1:
                    return (item_b['height']+h0)   
                          
        return h0

# функция поиска наиболее удаленено точки зоны покрытия для reData
def maxDistForZoneInkm(reData) -> float:
    maxOfDist = 0.0
    for item in reData.keys():
        if len(reData[item])>0:
            if maxOfDist < reData[item][len(reData[item])-1][1]:
                maxOfDist = reData[item][len(reData[item])-1][1]
    return maxOfDist

# функция перевода данных о зоне в БД ввиде интервалов для азимута в более менее крупные полигоны folium                   
def zoneFromIntervals(lat,lon, stepOfAzimuth,reData):
    outerEdge = [] #внешняя граница
    hole_intervals = {} # словарь для хранения отрезков пробелов - нужно для вычисления сшивных внутренних дыр 
    for item in reData.keys():
        innerHoleSet = [] #для создания списка интервалов отсутствия связи
        if len(reData[item])>0:
            distOuterForAz = reData[item][len(reData[item])-1][1]
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)-stepOfAzimuth/2, 1000*distOuterForAz)
            outerEdge.append((lat_e, lon+dlong_e))
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)+stepOfAzimuth/2, 1000*distOuterForAz)
            outerEdge.append((lat_e, lon+dlong_e))
            
            if reData[item][0][0]!=0:
                         innerHoleSet.append([0,reData[item][0][0]])
            if len(reData[item])>1:
                # здесь добавляем удаляемые сегменты
                for i in range(0,len(reData[item])-1):
                    # forDelete.append(funcForSegment(lat,lon,float(item), stepOfAzimuth, \
                    #                                 reData[item][i][1], \
                    #                                     reData[item][i+1][0], 5))
                    innerHoleSet.append([reData[item][i][1],reData[item][i+1][0]])
        hole_intervals[item] = innerHoleSet
    
    hole_groups = [[]] 
    for item in hole_intervals.keys():
        for interval in hole_intervals[item]:
            intervalIsAppend = False # добавился ли интервал или создавать новую hole
            for hole in hole_groups:
                if len(hole)!=0:
                    if hole[-1][0]==float(item)-stepOfAzimuth:
                        if intersect_direct_intervals(hole[-1][1],hole[-1][2],interval[0],interval[1]):
                            intervalIsAppend = True
                            hole.append([float(item),interval[0],interval[1]])
                            break # подразумевается выходим из цикла если добавили отрезок
            if not intervalIsAppend:
                hole_groups.append([[float(item),interval[0],interval[1]]])
    
    forDeleteNew = []
    for item in hole_groups:             
        if len(item)!=0:
            island = []
            preRadius = 0
            preRadiusEnd = 0
            for subItem in item:
                if subItem[2]!=preRadius:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])-stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    preRadius=1000*subItem[2]
                else:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    preRadius=1000*subItem[1]
                if subItem[1]!=preRadiusEnd:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])-stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    preRadiusEnd=1000*subItem[1]
                else:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    preRadiusEnd=1000*subItem[1]

            forDeleteNew.append(island)    

    if len(forDeleteNew) ==0:
        zone = outerEdge
    else:
        zone = [outerEdge,forDeleteNew]
    return zone

#функция определения списка для построения зоны из данных по расчету в БД
def createZoneFromElementOfDB(reData, lat, lon, stepOfAzimuth):
    outerEdge = [] #внешняя граница
    hole_intervals = {} # словарь для хранения отрезков пробелов - нужно для вычисления сшивных внутренних дыр 
    for item in reData.keys():
        innerHoleSet = [] #для создания списка интервалов отсутствия связи
        if len(reData[item])>0:
            distOuterForAz = reData[item][len(reData[item])-1][1]
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)-stepOfAzimuth/2, 1000*distOuterForAz)
            outerEdge.append((lat_e, lon+dlong_e))
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)+stepOfAzimuth/2, 1000*distOuterForAz)
            outerEdge.append((lat_e, lon+dlong_e))
            
            if len(reData[item])>1:
                # здесь добавляем удаляемые сегменты
                for i in range(0,len(reData[item])-1):
                    # forDelete.append(funcForSegment(lat,lon,float(item), stepOfAzimuth, \
                    #                                 reData[item][i][1], \
                    #                                     reData[item][i+1][0], 5))
                    innerHoleSet.append([reData[item][i][1],reData[item][i+1][0]])
        else:
            #если вообще связи нет в данном азимуте
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)-stepOfAzimuth/2, 1)
            outerEdge.append((lat_e, lon+dlong_e))
            (lat_e, dlong_e, alfe_e) = Direct_Geodezian_Task(lat, float(item)+stepOfAzimuth/2, 1)
            outerEdge.append((lat_e, lon+dlong_e))
        hole_intervals[item] = innerHoleSet
    
    hole_groups = [[]] 
    for item in hole_intervals.keys():
        for interval in hole_intervals[item]:
            intervalIsAppend = False # добавился ли интервал или создавать новую hole
            for hole in hole_groups:
                if len(hole)!=0:
                    if hole[-1][0]==float(item)-stepOfAzimuth:
                        if intersect_direct_intervals(hole[-1][1],hole[-1][2],interval[0],interval[1]):
                            intervalIsAppend = True
                            hole.append([float(item),interval[0],interval[1]])
                            break # подразумевается выходим из цикла если добавили отрезок
            if not intervalIsAppend:
                hole_groups.append([[float(item),interval[0],interval[1]]])
    
    forDeleteNew = []
    for item in hole_groups:             
        if len(item)!=0:
            island = []
            preRadius = 0
            preRadiusEnd = 0
            for subItem in item:
                if subItem[2]!=preRadius:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])-stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    preRadius=1000*subItem[2]
                else:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[2])
                    island.append((lat_,lon+dlong_))
                    preRadius=1000*subItem[1]
                if subItem[1]!=preRadiusEnd:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])-stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    preRadiusEnd=1000*subItem[1]
                else:
                    (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, \
                        float(subItem[0])+stepOfAzimuth/2, 1000*subItem[1])
                    island.insert(0,(lat_,lon+dlong_))
                    preRadiusEnd=1000*subItem[1]

            forDeleteNew.append(island)    
    island = []
    for item in reData.keys():
        isOpened = False
        
        if len(reData[item])>0:
            if reData[item][0][0]!=0:
                (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, float(item)-stepOfAzimuth/2, 1000*reData[item][0][0])
                island.append((lat_,lon+dlong_))
                (lat_, dlong_, alfe_) = Direct_Geodezian_Task(lat, float(item)+stepOfAzimuth/2, 1000*reData[item][0][0])
                island.append((lat_,lon+dlong_))
            else:
                if len(island)>0:
                    island.append((lat,lon))
                    forDeleteNew.append(island)
                    island = []
        else:
            if len(island)>0:
                island.append((lat,lon))
                forDeleteNew.append(island)
                island = []
    if len(island)>0:
        island.append((lat,lon))
        forDeleteNew.append(island)
        island = []            

    if len(forDeleteNew) ==0:
        zone = outerEdge
    else:
        zone = [outerEdge,forDeleteNew]

    return zone    

        
def createZoneFromElementOfDBWithLimits(reData, lat, lon, stepOfAzimuth, limitOfDist):
    reData1=reData
    for item in reData1.keys():
        if len(reData1[item])>0:
            for i in range(0,len(reData1[item])):
                if (reData1[item][i][0]<limitOfDist) and (reData1[item][i][1]>limitOfDist):
                    reData1[item][i][1] = limitOfDist
                if (reData1[item][i][0]>limitOfDist) and (reData1[item][i][1]>limitOfDist):
                    for j in range(i,len(reData1[item])):
                        reData1[item].pop(len(reData1[item])-1)
                    break
    zone1 = createZoneFromElementOfDB(reData1, lat, lon, stepOfAzimuth)
    return zone1
