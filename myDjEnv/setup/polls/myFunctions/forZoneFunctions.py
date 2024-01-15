from . import GeoFunctions

# def zonesFromIntervals(res_intervals,stepOfAzimuth, lat_in_deg, long_in_deg):
#     res_list = [] #сюда будем класть многоугольники зоны
#     azimuts = (x * stepOfAzimuth for x in range(0, int(360/stepOfAzimuth)))

#     for azimuth in azimuts:
#         if len(res_intervals[azimuth])>1: # думается что если несколько отрезков то дальние могут
#                                           # входить в состав островков потому проверяем их
#             # сейчас одиночные линии находим
#             for i in range(1,len(res_intervals[azimuth])): #рассматриваем каждый отрезок отдельно
#                 #рассматриваем на предыдущем шаге азимута
#                 isNotLonely = False#поменяется на True если будет пересечение
#                 if azimuth-stepOfAzimuth>=0:
#                     index1 = azimuth-stepOfAzimuth
#                 else:
#                     index1 = (int(360/stepOfAzimuth)-1)*stepOfAzimuth
#                 for j in range(0,len(res_intervals[index1])):
#                     if isIntersection(res_intervals[azimuth][i],res_intervals[index1][j]):
#                         isNotLonely = True
#                 if azimuth+stepOfAzimuth<=(int(360/stepOfAzimuth)-1)*stepOfAzimuth:
#                     index2 = azimuth+stepOfAzimuth
#                 else:
#                     index2 = 0
#                 #рассматриваем на следующем шаге азимута
#                 for j in range(0,len(res_intervals[index2])):
#                     if isIntersection(res_intervals[azimuth][i],res_intervals[index2][j]):
#                         isNotLonely = True
#                 if isNotLonely==False:
#                     (lat1, deltalong1, alfa2_1) = GeoFunctions.Direct_Geodezian_Task(lat_in_deg, azimuth-stepOfAzimuth/2, \
#                                                                                      1000*res_intervals[azimuth][i][0]) 
#                     (lat2, deltalong2, alfa2_2) = GeoFunctions.Direct_Geodezian_Task(lat_in_deg, azimuth-stepOfAzimuth/2, \
#                                                                                      1000*res_intervals[azimuth][i][1]) 
#                     (lat3, deltalong3, alfa2_3) = GeoFunctions.Direct_Geodezian_Task(lat_in_deg, azimuth+stepOfAzimuth/2, \
#                                                                                      1000*res_intervals[azimuth][i][1])
#                     (lat4, deltalong4, alfa2_4) = GeoFunctions.Direct_Geodezian_Task(lat_in_deg, azimuth+stepOfAzimuth/2, \
#                                                                                      1000*res_intervals[azimuth][i][0]) 
#                     res_list.append([(lat1,long_in_deg+deltalong1),(lat2,long_in_deg+deltalong2),\
#                                      (lat3,long_in_deg+deltalong3),(lat4,long_in_deg+deltalong4)])
#                     # надо убрать отрезок из дальнейшего анализа
                   
                            
#     return res_list

#функция определения пересечения интервалов дальностей (дальности по возрастанию) 
def isIntersection(list1, list2)->bool:
    if (list1[0]>=list2[1]) or (list1[1]<=list2[0]):
        return False
    else:
        return True
    
def funcForSegment(lat,long,azimuth, stepazimuth, dist0_in_km, dist1_in_km, roughness):
    segmentOfZone = []
    (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth-stepazimuth/2, 1000*dist0_in_km)
    segmentOfZone.append((lat1, long+dlong1))
    (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth-stepazimuth/2, 1000*dist1_in_km)
    segmentOfZone.append((lat1, long+dlong1))
    #далее верхняя дуга
    az = azimuth-stepazimuth/2+stepazimuth/roughness
    while az<azimuth+stepazimuth/2-stepazimuth/roughness:
        az+=stepazimuth/roughness 
        (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, az, 1000*dist1_in_km)
        segmentOfZone.append((lat1, long+dlong1))
    (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth+stepazimuth/2, 1000*dist1_in_km)
    segmentOfZone.append((lat1, long+dlong1))
    (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth+stepazimuth/2, 1000*dist0_in_km)
    segmentOfZone.append((lat1, long+dlong1))
    #далее нижняя дуга
    az = azimuth+stepazimuth/2-stepazimuth/roughness
    while az>azimuth-stepazimuth/2+stepazimuth/roughness:
        az-=stepazimuth/roughness
        (lat1, dlong1, alfa) = GeoFunctions.Direct_Geodezian_Task(lat, az, 1000*dist0_in_km)
        segmentOfZone.append((lat1, long+dlong1))
    return segmentOfZone
    
