import math 

def rectangle_folium(lat, lon, step):
    listOfCoord = []
    listOfCoord.append([lat+step, lon-step])
    listOfCoord.append([lat+step, lon+step])
    listOfCoord.append([lat-step, lon+step])
    listOfCoord.append([lat-step, lon-step])
    return listOfCoord

def bilinean_interpolation(x1,y1,x2,y2,Q11,Q12,Q21,Q22,x,y): # расчет значения внутри прямоугольной сетки с известными значениями в узлах
                                                             # по билинейной интерполяции
    if ((x2-x1)!=0) and  ((y2-y1)!=0):
        k1 = Q11/((x2-x1)*(y2-y1))
        k2 = Q21/((x2-x1)*(y2-y1))
        k3 = Q12/((x2-x1)*(y2-y1))
        k4 = Q22/((x2-x1)*(y2-y1))
        bI = k1*(x2-x)*(y2-y)+k2*(x-x1)*(y2-y)+k3*(x2-x)*(y-y1)+k4*(x-x1)*(y-y1)
    elif ((x2-x1)==0) and  ((y2-y1)==0):
        bI = (Q11+Q12+Q21+Q22)/4
    elif ((x2-x1)==0):
        bI = (Q11+Q21)/2+((Q12+Q22)/2-(Q11+Q21)/2)(y-y1)/(y2-y1)
    else: 
        bI = (Q11+Q12)/2+((Q21+Q22)/2-(Q11+Q12)/2)(x-x1)/(x2-x1)
    return bI
     
def height_to_color(height):  # функция перевода высоты в метрах в цвет для красивой физической карты
    values = {0: '#009500', 10: '#009B00', 20: '#00A000', 30: '#00A300', 40: '#00A800', 50: '#00B000', 60: '#00B800',\
            70: '#00C000', 80: '#00C800', 90: '#00D000', 100: '#00D800', 125: '#00E000', 150: '#00E800', 175: '#00F500', \
            200: '#00FE30', 225: '#00FE50', 250: '#00FE70', 275: '#00FF90', 300: '#00FFA0', 325: '#00FFB0', 350: '#00FFC0', \
            375: '#00FFD0', 400: '#00FFE0', 425: '#00FFF0', 450: '#00FFFF', 475: '#00FAFF', 500: '#00F5FF', 550: '#00F0FF', \
            600: '#00EAFF', 650: '#00E5FF', 700: '#00E0FF', 750: '#00DAFF', 800: '#00D5FF', 850: '#00D0FF', 900: '#00CAFF', \
            950: '#00C5FF', 1000: '#00C0FF', 1050: '#00BAFF', 1100: '#00B5FF', 1150: '#00B0FF', 1200: '#00AAFF', 1250: '#00A5FF',\
            1300: '#000A0FF', 1350: '#009AFF', 1400: '#0095FF', 1450: '#0090FF', 1500: '#008AFF', 1550: '#0085FF', \
            1600: '#0080FF', 1650: '#0080FA', 1700: '#0080F5', 1750: '#0080F0', 1800: '#0080EA', 1850: '#0080E5', \
            1900: '#0080E0', 1950: '#0080DA', 2000: '#0080D5', 2050: '#0080D0', 2100: '#0080CA', 2150: '#0080C5', \
            2200: '#0080C0', 2250: '#0080C5', 2300: '#0080C0', 2350: '#0080BA', 2400: '#0080B5', 2450: '#0080B0',\
            2500: '#0080AA', 2550: '#0080A5', 2600: '#0080A0', 2650: '#00809E', 2700: '#00809C', 2750: '#00809B', 2800: '#00809A',\
            2850: '#007C99', 2900: '#007898', 2950: '#007494', 3000: '#007090', 3100: '#006B8B', 3200: '#006888', 3300: '#006080', \
            3500: '#005070', 4000: '#004060', 4500: '#003050', 5000: '#002040', 6000: '#001030', 11000: '#000020'
              }
    if (height<=0):
        return values[0]
    elif (height<100):
        return values[10*(math.trunc(height/10)+1)]
    elif (height<500):
        return values[25*(math.trunc(height/25)+1)]
    elif (height<3000):
        return values[50*(math.trunc(height/50)+1)]
    elif (height<3300):
        return values[100*(math.trunc(height/100)+1)]
    elif (height<3500):
        return values[3500]
    elif (height<5000):
        return values[500*(math.trunc(height/500)+1)]
    elif (height<6000):
        return values[6000]
    else:
        return values[11000]
    


#функция определения пересечения двух интервалов значений - интервал от меньшего к большему
def intersect_direct_intervals(start1: float, end1: float, start2: float, end2: float):
    innerBool = True
    if (end1<start2):
        innerBool = False
    if (start1>end2) :
        innerBool = False
    return innerBool

#Функция определения пересечения двух отрезков
#(не учитывает случай, если прямые совпадают - выдает False)
def intersect_two_segments (lat1OfFirst,lon1OfFirst,lat2OfFirst,lon2OfFirst,lat1OfSecond,lon1OfSecond,lat2OfSecond,lon2OfSecond) ->bool:
    if (lat1OfFirst!=lat2OfFirst) and (lat1OfSecond!=lat2OfSecond):
        a_its = (lon1OfFirst-lon2OfFirst)/(lat1OfFirst-lat2OfFirst)
        b_its = (lon1OfSecond-lon2OfSecond)/(lat1OfSecond-lat2OfSecond)
        if a_its != b_its:
            #Находим точку пересечения прямых
            latOfIntersect = ((lon1OfSecond-lon1OfFirst)+a_its*lat1OfFirst-b_its*lat1OfSecond)/(a_its-b_its)
            if lat2OfFirst>=lat1OfFirst:
                if (latOfIntersect>=lat1OfFirst) and (latOfIntersect<=lat2OfFirst):
                    if lat2OfSecond>=lat1OfSecond:
                        if (latOfIntersect>=lat1OfSecond) and (latOfIntersect<=lat2OfSecond): return True
                        else: return False
                    else:   
                        if (latOfIntersect>=lat2OfSecond) and (latOfIntersect<=lat1OfSecond): return True
                        else:  return False
                else: return False
            else:
                if (latOfIntersect<=lat1OfFirst) and (latOfIntersect>=lat2OfFirst):
                    if lat2OfSecond>=lat1OfSecond:
                        if (latOfIntersect>=lat1OfSecond) and (latOfIntersect<=lat2OfSecond): return True
                        else: return False
                    else:
                        if (latOfIntersect>=lat2OfSecond) and (latOfIntersect<=lat1OfSecond): return True
                        else: return False
                else: return False  
        else:  return False      
    else:
        # далее если хотя бы одна из прямых вертикальная
        if (lat1OfFirst!=lat2OfFirst):
            lonOfIntersect=(lon2OfFirst-lon1OfFirst)*(lat1OfSecond-lat2OfFirst)/(lat2OfFirst-lat1OfFirst)+lon2OfFirst
            if lat1OfFirst<lat2OfFirst:
                if (lat1OfSecond>=lat1OfFirst) and (lat1OfSecond<=lat2OfFirst):
                    if ((lonOfIntersect<=lon1OfSecond)and (lonOfIntersect>=lon2OfSecond)) \
                        or ((lonOfIntersect>=lon1OfSecond)and (lonOfIntersect<=lon2OfSecond)): return True
                    else: return False
                else: return False
            else:
                if (lat1OfSecond<=lat1OfFirst) and (lat1OfSecond>=lat2OfFirst):
                    if ((lonOfIntersect<=lon1OfSecond)and \
                        (lonOfIntersect>=lon2OfSecond)) or ((lonOfIntersect>=lon1OfSecond)and (lonOfIntersect<=lon2OfSecond)):
                        return True
                    else: return False
                else: return False
        else:
            if (lat1OfSecond!=lat2OfSecond):
                lonOfIntersect=(lon2OfSecond-lon1OfSecond)*(lat1OfFirst-lat2OfSecond)/(lat2OfSecond-lat1OfSecond)+lon2OfSecond
                if lat1OfSecond<lat2OfSecond:
                    if (lat1OfFirst>=lat1OfSecond) and (lat1OfFirst<=lat2OfSecond):
                        if ((lonOfIntersect<=lon1OfFirst)and (lonOfIntersect>=lon2OfFirst)) \
                            or ((lonOfIntersect>=lon1OfFirst)and (lonOfIntersect<=lon2OfFirst)): return True
                        else: return False
                    else: return False
                else:
                    if (lat1OfFirst<=lat1OfSecond) and (lat1OfFirst>=lat2OfSecond):
                        if ((lonOfIntersect<=lon1OfFirst)and (lonOfIntersect>=lon2OfFirst))\
                            or ((lonOfIntersect>=lon1OfFirst)and (lonOfIntersect<=lon2OfFirst)): return True
                        else: return False
                    else: return False
            else: return False

# Функция определения пересечения прямоугольников параллельных осям
def intersect_rectangles (latmin_f,latmax_f,lonmin_f,lonmax_f,\
                          latmin_s,latmax_s,lonmin_s,lonmax_s) -> bool:
    # если есть пересечения ребер или если после проверки пересечения любая точка одного лежит внутри другого,
    # то пересекаются
    if intersect_two_segments(latmin_f,lonmin_f,latmax_f,lonmin_f,latmin_s,lonmin_s,latmax_s,lonmin_s):
        return True
    elif intersect_two_segments(latmin_f,lonmin_f,latmax_f,lonmin_f,latmax_s,lonmin_s,latmax_s,lonmax_s):
        return True
    elif intersect_two_segments(latmin_f,lonmin_f,latmax_f,lonmin_f,latmax_s,lonmax_s,latmin_s,lonmax_s):
        return True
    elif intersect_two_segments(latmin_f,lonmin_f,latmax_f,lonmin_f,latmin_s,lonmax_s,latmin_s,lonmin_s):
        return True  
    elif intersect_two_segments(latmax_f,lonmin_f,latmax_f,lonmax_f,latmin_s,lonmin_s,latmax_s,lonmin_s):
        return True
    elif intersect_two_segments(latmax_f,lonmin_f,latmax_f,lonmax_f,latmax_s,lonmin_s,latmax_s,lonmax_s):
        return True
    elif intersect_two_segments(latmax_f,lonmin_f,latmax_f,lonmax_f,latmax_s,lonmax_s,latmin_s,lonmax_s):
        return True
    elif intersect_two_segments(latmax_f,lonmin_f,latmax_f,lonmax_f,latmin_s,lonmax_s,latmin_s,lonmin_s):
        return True
    elif intersect_two_segments(latmax_f,lonmax_f,latmin_f,lonmax_f,latmin_s,lonmin_s,latmax_s,lonmin_s):
        return True
    elif intersect_two_segments(latmax_f,lonmax_f,latmin_f,lonmax_f,latmax_s,lonmin_s,latmax_s,lonmax_s):
        return True
    elif intersect_two_segments(latmax_f,lonmax_f,latmin_f,lonmax_f,latmax_s,lonmax_s,latmin_s,lonmax_s):
        return True
    elif intersect_two_segments(latmax_f,lonmax_f,latmin_f,lonmax_f,latmin_s,lonmax_s,latmin_s,lonmin_s):
        return True
    elif intersect_two_segments(latmin_f,lonmax_f,latmin_f,lonmin_f,latmin_s,lonmin_s,latmax_s,lonmin_s):
        return True
    elif intersect_two_segments(latmin_f,lonmax_f,latmin_f,lonmin_f,latmax_s,lonmin_s,latmax_s,lonmax_s):
        return True
    elif intersect_two_segments(latmin_f,lonmax_f,latmin_f,lonmin_f,latmax_s,lonmax_s,latmin_s,lonmax_s):
        return True
    elif intersect_two_segments(latmin_f,lonmax_f,latmin_f,lonmin_f,latmin_s,lonmax_s,latmin_s,lonmin_s):
        return True
    elif (latmin_s>latmin_f) and (latmin_s<latmax_f) and (lonmin_s>lonmin_f) and (lonmin_s<lonmax_f):
        return True
    elif (latmin_f>latmin_s) and (latmin_f<latmax_s) and (lonmin_f>lonmin_s) and (lonmin_f<lonmax_s):
        return True
    else:
        return False
    
# Функция для перевода шага итерации в отличный от предыдущего цвет
def intToColor (i: int):
    innerDict = {0: 'red', 1: 'coral', 2: 'yellow', 3: 'springgreen', 4: 'green', 5: 'lightseagreen',\
                 6: 'dodgerblue', 7: 'mediumblue', 8: 'indigo', 9: 'magenta', 10: 'violet', 11: 'crimson', \
                 12: 'olive', 13: 'navy', 14: 'fucsia', 15: 'chocolate'}
    return innerDict[i%16]

