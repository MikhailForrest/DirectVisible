from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView
from django.contrib import messages

from django.utils import timezone
import folium
from folium.plugins import MousePosition
from .forms import forZones
from .forms import DirVis
from .forms import forEnterHeight
from .forms import forHeigths
from django.core.exceptions import MultipleObjectsReturned

from .models import Choice, Question
from .models import ZoneForDB
from .models import TraceAN
from .models import AirportBuilding
from .myFunctions  import myFunc
from .myFunctions import PointToPointVisible
from .myFunctions import GeoFunctions
import math
from .myFunctions.workWithData import DataForComputing
from .myFunctions.workWithData import zoneFromIntervals
from .myFunctions.workWithData import maxDistForZoneInkm
from .myFunctions.workWithData import createZoneFromElementOfDB
from .myFunctions.workWithData import createZoneFromElementOfDBWithLimits
from .myFunctions.forZoneFunctions import funcForSegment
from .myFunctions.TopocentricSystem import TopocentricSysCoord
import json
from PyPDF2 import PdfReader
import osmnx as ox
import time
import pandas as pd
import xml.etree.ElementTree as ET
import socket, ssl, sys # firehose - поставщика ADS-B
from .forFireHose import InflateStream
from .forFireHose import parse_json
import os

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
    
def map_button(request):
    map = folium.Map(
            location = [54, 41],
            zoom_start = 9, control_scale=True, prefer_canvas = True, zoom_control = False,
            tiles = 'OpenStreetMap')
   
    #вывод координат курсора
    formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
    MousePosition(position="topright",\
                  separator=" ; ",
                  empty_string="NaN",
                  lng_first=False,
                  num_digits=20,
                  prefix="Coordinates:",
                  lat_formatter=formatter,
                  lng_formatter=formatter,).add_to(map)
        
    if  (request.method == "POST") and ('Direct Visibility' in request.POST):  
        form = DirVis(request.POST)
        if form.is_valid():  
            position = form.cleaned_data['position']
            lat = form.cleaned_data['lat']  # чтение данных с формы g
            lon = form.cleaned_data['lon']  
            height = form.cleaned_data['heightOnGround']
            heightOfAircraft = form.cleaned_data['heightFlight']
            limitForDist_in_km = form.cleaned_data['distance_limitation_in_km']
            isOnGround = form.cleaned_data['AboveGroundLevel']
            map.location = [lat, lon]
            
            dataForComputing = \
                DataForComputing(lat,lon,height+PointToPointVisible.heightFromLatLon(lat,lon),heightOfAircraft,limitForDist_in_km)

            # отрисовка рельефа по галочке 
            if form.cleaned_data['isDrawingRelief']:
                stepInDegrees = (dataForComputing.max_lat-dataForComputing.min_lat)/200
                rLat = float(dataForComputing.max_lat)
                while rLat>dataForComputing.min_lat-stepInDegrees:
                    rLong = float(dataForComputing.min_long)
                    while rLong<dataForComputing.max_long+stepInDegrees:
                        s = dataForComputing.get_height(rLat,rLong)
                        folium.Polygon(myFunc.rectangle_folium(rLat,rLong,(stepInDegrees/2)), weight =0, color=myFunc.height_to_color(s), \
                                       fill = True, fill_opacity=0.8, fill_color=myFunc.height_to_color(s)).add_to(map)
                        rLong += stepInDegrees
                    rLat -= stepInDegrees 

            res_intervals = {} # dictionary для хранения результатов дальности по отрезкам

            stepOfAzimuth = float(dict(DirVis.STEPS_OF_AZIMUTH).get(request.POST['accuracyOfAzimuth']))
            countForDistance = int(dict(DirVis.COUNTS_OF_SPLIT).get(request.POST['divisionOfDistance'])) 
            azimuts = (x * stepOfAzimuth for x in range(0, int(360/stepOfAzimuth)))
            topocentric = TopocentricSysCoord(lat, lon, height+PointToPointVisible.heightFromLatLon(lat,lon))
            for azimuth in azimuts:
                dist_in_km = 0.001 
                innerSet = []
                helpVar = 0.0
                isOpenedInterval = False
                while dist_in_km < dataForComputing.dMax/1000:
                    (lat_f,dlon_f,alfa2_f) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth, 1000*dist_in_km)
                    if not isOnGround:
                        if (PointToPointVisible.DirVisUnit_1(lat, lon, height+PointToPointVisible.heightFromLatLon(lat,lon),\
                                                                 lat_f, lon+dlon_f, heightOfAircraft, dataForComputing, \
                                                                    form.cleaned_data['isUseUsersObjects'])) and \
                            (topocentric.getElevationInDeg(lat_f, lon+dlon_f, heightOfAircraft)<\
                             form.cleaned_data['limitUpperAngle']) and \
                            (topocentric.getElevationInDeg(lat_f, lon+dlon_f, heightOfAircraft)>\
                             form.cleaned_data['limitLowerAngle']):
                            if not isOpenedInterval:
                                helpVar = dist_in_km
                                isOpenedInterval = True
                        else:
                            if isOpenedInterval:
                                innerSet.append([helpVar,dist_in_km-dataForComputing.dMax/(2000*countForDistance)])
                                isOpenedInterval = False
                    else:
                        if PointToPointVisible.DirVisUnit_1(lat, lon, height+PointToPointVisible.heightFromLatLon(lat,lon),\
                                                                 lat_f, lon+dlon_f, \
                                                                    heightOfAircraft+PointToPointVisible.heightFromLatLon(lat_f,lon+\
                                                                                                                          dlon_f),
                                                                    dataForComputing, form.cleaned_data['isUseUsersObjects']) and \
                            (topocentric.getElevationInDeg(lat_f, lon+dlon_f, heightOfAircraft+\
                                                           PointToPointVisible.heightFromLatLon(lat_f,lon+dlon_f))<\
                                                            form.cleaned_data['limitUpperAngle']) and \
                            (topocentric.getElevationInDeg(lat_f, lon+dlon_f, heightOfAircraft+\
                                                           PointToPointVisible.heightFromLatLon(lat_f,lon+dlon_f))>\
                                                            form.cleaned_data['limitLowerAngle']):
                            if not isOpenedInterval:
                                helpVar = dist_in_km
                                isOpenedInterval = True
                        else:
                            if isOpenedInterval:
                                innerSet.append([helpVar,dist_in_km-dataForComputing.dMax/(2000*countForDistance)])
                                isOpenedInterval = False
                    dist_in_km+=dataForComputing.dMax/(1000*countForDistance)
                if isOpenedInterval:
                                innerSet.append([helpVar,dist_in_km])

                res_intervals[azimuth] = innerSet
            
            # далее отрисовка
            # res_zone = []  # - внутренний многоугольник по отрезкам по первому отрезку 
            # azimuts = (x * stepOfAzimuth for x in range(0, int(360/stepOfAzimuth)))
            # for azimuth in azimuts: #range(0,360):   
            #     if len(res_intervals[azimuth])!=0:
            #         (lat_r,dlon_r,alfa2_f) = GeoFunctions.Direct_Geodezian_Task(lat, azimuth, 1000*res_intervals[azimuth][0][1])                                 
            #         res_zone.append((lat_r,lon+dlon_r))
            '''#тут отрисовка прямыми отрезками отдельных островков
            # islandsOfLonelyInterval = zonesFromIntervals(res_intervals,stepOfAzimuth,lat, lon)
            # for sub in islandsOfLonelyInterval:
            #     folium.Polygon(sub,color = 'green', opacity = 0.6, fill =True, fill_opacity = 0.6,\
            #                     fill_color = 'green').add_to(map) '''

            # res_zone_out= []  # - внутренний многоугольник по отрезкам по внешнему отрезку 
            # azimuts = (x * stepOfAzimuth for x in range(0, int(360/stepOfAzimuth)))
            # for azimuth in azimuts: #range(0,360):   
            #     if len(res_intervals[azimuth])!=0:
            #         (lat_r,dlon_r,alfa2_f) = \
            #             GeoFunctions.Direct_Geodezian_Task(lat, azimuth,\
            #                                                1000*res_intervals[azimuth][len(res_intervals[azimuth])-1][1])                                 
            #         res_zone_out.append((lat_r,lon+dlon_r))
            # if len(res_zone_out)!=0:
            #     folium.Polygon(res_zone_out, tooltip='zone= '+str(lat)+'  '+str(lon)+'  hAntenna='+str(height)+\
            #                 '  hAircraft='+str(heightOfAircraft), color = 'blue', opacity = 0.4, fill =True, fill_opacity = 0.4,\
            #                     fill_color = 'blue').add_to(map) 
            
            '''# НЕ УДАЛЯТЬ ОСТАВИТЬ КАК ЗАПАСНОЙ ДЛЯ ОТРИСОВКИ
            # отрисовка отрезков с прямой видимостью по азимутальной разбивке
            # for item in res_intervals.keys():
            #     for inList in res_intervals[item]:
            #         folium.Polygon(funcForSegment(lat,lon,float(item), stepOfAzimuth, inList[0], inList[1], 10),weight = 1, 
            #                        opacity = 0.3, color = 'orange',
            #                        fill =True, fill_opacity = 0.6, fill_color = 'orange').add_to(map)'''
            folium.CircleMarker( location=[lat,lon],radius=2,color='green',fill=True,fill_color='red').add_to(map)
            
            # отрисовка для масштаба эквидистантных кругов вокруг расчетной точки если поставлена галочка
            if form.cleaned_data['isDrawingCircles']: 
                if dataForComputing.dMax>10000:
                    radiusesInM = [i*math.trunc(dataForComputing.dMax/5) for i in range(1,6)]
                else:
                    radiusesInM = [2000, 4000, 6000, 8000, 10000]
                for radiusU in radiusesInM:
                    folium.Circle(location=[lat,lon],
                        radius=radiusU,
                        color='black',
                        weight=1,
                        fill=False
                        ).add_to(map)
                    dist = math.trunc(radiusU/1000)
                    for az in (0,90,180,270):
                        (lat_,dlon_,alfa2_) = GeoFunctions.Direct_Geodezian_Task(lat, az, 1000*dist)
                        folium.Marker(location=[lat_,lon+dlon_],
                                    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str(dist)+'km'}</p></div></html>''',
                                    class_name="mapText")).add_to(map)

            #опыты с json и БД
            dataJSON = json.dumps(res_intervals, indent = 4) # создание JSON из словаря результатов
            if not isOnGround:
                nameOfResults = 'zone= '+str(lat)+'  '+str(lon)+'  hAntenna='+str(height)+\
                    '  hAircraft='+str(heightOfAircraft)+'AMSL'
            else: 
                nameOfResults = 'zone= '+str(lat)+'  '+str(lon)+'  hAntenna='+str(height)+\
                    '  hAircraft='+str(heightOfAircraft)+'AGL'
                
            ZoneForDB.objects.create(name = nameOfResults, latOfCenter = lat, longOfCenter = lon, \
                                     stepOfAzimuth = stepOfAzimuth, intervals = dataJSON, \
                                        position = position) # загрузка результатов в БД
            
            try:
                exampleOfZone = ZoneForDB.objects.get(name = nameOfResults) 
            except MultipleObjectsReturned: #исключение если с одинаковым названием несколько - берем последний
                exampleOfZone = ZoneForDB.objects.filter(name = nameOfResults).last()
           
            reData = json.loads(exampleOfZone.intervals)

            # рисуем по сегментарным отрезкам
            # for item in reData.keys():
            #     for inList in reData[item]:
            #         folium.Polygon(funcForSegment(lat,lon,float(item), stepOfAzimuth, inList[0], inList[1], 10),weight = 1, 
            #                        opacity = 0.3, color = 'orange',
            #                        fill =True, fill_opacity = 0.6, fill_color = 'orange').add_to(map)

            # folium.Marker(location=[54.0359091,41.0765076],
            #                         icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str(topocentric.getElevationInDeg(54.0359091,41.0765076,10000))}</p></div></html>''',
            #                         class_name="mapText")).add_to(map)

            zone1 = createZoneFromElementOfDB(reData, lat, lon, stepOfAzimuth)

            try:
                folium.Polygon(zone1, color = 'green',  opacity = 0.0, weight = 0,  fill =True, fill_opacity = 0.6,\
                            fill_color = 'green').add_to(map)    
            except ValueError: # добавил обработку исключения, поскольку при нулевых значениях выпадала ошибка
                pass
            
            folium.CircleMarker( location=[exampleOfZone.latOfCenter,exampleOfZone.longOfCenter],radius=2,tooltip = exampleOfZone.name, color='green',fill=True,fill_color='red').add_to(map)
            folium.Marker(location=[exampleOfZone.latOfCenter,exampleOfZone.longOfCenter],
                                    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{exampleOfZone.position}</p></div></html>''',
                                    class_name="mapText")).add_to(map)
            
            # # здесь показывается как сделать зону с вырезами
            # help_zone = [(54.27,41.41),(54.57,41.78),(54.34,41.96),(54.03,41.74)]
            # help_lll = [(54.28,41.61),(54.28,42.2),(53.99,41.94)] # пробую бублик как в GeoJson , что вырезается
            # res_zone1 = [help_zone,help_lll]
            # if len(res_zone1)!=0:
            #     folium.Polygon(res_zone1, color = 'orange', opacity = 0.6, fill =True, fill_opacity = 0.6,\
            #                     fill_color = 'orange').add_to(map) 
            map = map._repr_html_()
            return render(request,'polls/map.html',{'form':form,'map': map})
        
    elif (request.method == "POST") and ('DrawUserObjects' in request.POST):  
        form = DirVis(request.POST)
        if form.is_valid():
            for airport in AirportBuilding.objects.all():
                arrayOfBuilding = json.loads(airport.polygons)
                coord_arr = []
                for item_1 in arrayOfBuilding.keys():
                    coord_arr = []
                    for item_2 in arrayOfBuilding[item_1]['p']['polygon']:
                        coord_arr.append((item_2[0],item_2[1]))
                        folium.PolyLine(coord_arr, color = 'yellow', width = 3).add_to(map)
            map = map._repr_html_()
            return render(request,'polls/map.html', {'form':form,'map': map})
    else:
        form = DirVis() 
    
    map = map._repr_html_()
    contex = {'form':form, 'map': map}    
    return render(request,'polls/map.html', contex)

def zones(request):
    map1 = folium.Map(
            location = [54, 41],
            zoom_start = 9, control_scale=True, prefer_canvas = True, zoom_control = False,
            tiles = 'OpenStreetMap')
   
    #вывод координат курсора
    formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
    MousePosition(position="topright",\
                  separator=" ; ",
                  empty_string="NaN",
                  lng_first=False,
                  num_digits=20,
                  prefix="Coordinates:",
                  lat_formatter=formatter,
                  lng_formatter=formatter,).add_to(map1)
    
    if  (request.method == "POST") and ('LoadPosition' in request.POST): #загрузка высот зданий для аэропорта   
        form = forZones(request.POST)
        if form.is_valid() :
            # проба работы с osmnx
            place_name = form.cleaned_data['PositionForFind']
            try:
                point = ox.geocode(place_name) #поиск 
                map1 = folium.Map(location = point,zoom_start = 15, control_scale=True, prefer_canvas = True, zoom_control = False,\
                                tiles = 'OpenStreetMap')
                #вывод координат курсора
                formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
                MousePosition(position="topright",\
                            separator=" ; ",
                            empty_string="NaN",
                            lng_first=False,
                            num_digits=20,
                            prefix="Coordinates:",
                            lat_formatter=formatter,
                            lng_formatter=formatter,).add_to(map1)
                area = ox.geocode_to_gdf(place_name, which_result=1)

                buildings = ox.geometries_from_place(place_name, {"building": True}) #возвращает GeoDataFrame
                folium.GeoJson(area,style_function=lambda feature: {
                                        "fillOpacity": 0,
                                        "weight": 5,
                                    }).add_to(map1)
                     
                # for item in buildings.geometry:
                #     folium.GeoJson(item,
                #                    style_function=lambda feature: {
                #                         "fillColor": "#ffff00",
                #                         "color": "red",
                #                         "weight": 1.5,
                #                     }).add_to(map)
                if request.session.get('airport_','') == place_name:
                    num_buildings = request.session.get('num_buildings', 0)
                    request.session['num_buildings'] = num_buildings+1
                    num_buildings = request.session.get('num_buildings', 0)
                else: 
                    request.session['num_buildings'] = 0
                    num_buildings = request.session.get('num_buildings', 0)
                    request.session['step'] = {}
                    request.session['steps'] = {}

                

                # отрисовка зданий внутри площади аэропорта
                help_int = 0
                for item in buildings.geometry:
                    help_int+=1
                    
                if help_int <= num_buildings:
                    help_arr = request.session.get('steps',{})
                    # здесь надо определить границы по широте-долготе данного здания
                    edge_curr = request.session.get('step',{})['polygon']
                    initFind = False
                    for it_cur in edge_curr:
                        if initFind:
                            if it_cur[0] < min_lat_cur: min_lat_cur = it_cur[0]
                            if it_cur[0] > max_lat_cur: max_lat_cur = it_cur[0]
                            if it_cur[1] < min_lon_cur: min_lon_cur = it_cur[1]
                            if it_cur[1] > max_lon_cur: max_lon_cur = it_cur[1]
                        else:
                            max_lat_cur = it_cur[0]
                            min_lat_cur = it_cur[0]
                            min_lon_cur = it_cur[1]
                            max_lon_cur = it_cur[1]
                            initFind = True
                    help_arr[str(help_int)] = {'p': request.session.get('step',{}), 'height': form.cleaned_data['height_building'],\
                                               'min_lt_b': min_lat_cur, 'max_lt_b': max_lat_cur,\
                                                'min_ln_b': min_lon_cur, 'max_ln_b': max_lon_cur}
                    request.session['steps'] = help_arr

                    request.session['num_buildings'] = 0  
                    num_buildings = request.session.get('num_buildings', 0)  
                    #здесь добавить к БД  
                    AeroportJSON = json.dumps(request.session['steps'], indent=4)
                    isInitializedEdges = False

                    # поиск max_lat, min_lat, min_lon, max_lon
                    for item_1 in request.session.get('steps',{}).keys():
                        for item_2 in request.session.get('steps',{})[item_1]['p']['polygon']:
                            if isInitializedEdges:
                                try:
                                    if item_2[0] < min_lat: min_lat = item_2[0]
                                    if item_2[0] > max_lat: max_lat = item_2[0]
                                    if item_2[1] < min_lon: min_lon = item_2[1]
                                    if item_2[1] > max_lon: max_lon = item_2[1]
                                except TypeError:
                                    pass
                            else:
                                max_lat = item_2[0]
                                min_lat = item_2[0]
                                min_lon = item_2[1]
                                max_lon = item_2[1]
                                isInitializedEdges = True
                    folium.Rectangle([(max_lat,min_lon),(min_lat,max_lon)], color = 'yellow').add_to(map1)
                    AirportBuilding.objects.create(name = request.session.get('airport_',''), polygons = AeroportJSON, \
                                                   max_lat = max_lat, min_lat = min_lat, min_lon = min_lon, max_lon = max_lon) # загрузка результатов в БД          
                    request.session['step'] = {}
                    request.session['steps'] = {}

                    #Проверка построения всех зданий
                    try:
                        exampleOfAirport = AirportBuilding.objects.get(name = request.session.get('airport_','')) 
                    except MultipleObjectsReturned: #исключение если с одинаковым названием несколько - берем последний
                        exampleOfAirport = AirportBuilding.objects.filter(name = request.session.get('airport_','')).last()
                
                    arrayOfBuilding = json.loads(exampleOfAirport.polygons)
                    coord_arr = []
                    for item_1 in arrayOfBuilding.keys():
                        coord_arr = []
                        for item_2 in arrayOfBuilding[item_1]['p']['polygon']:
                            coord_arr.append((item_2[0],item_2[1]))
                            folium.PolyLine(coord_arr, color = 'yellow', width = 3).add_to(map1)
                    
    
                request.session['airport_'] = place_name
                airport_name = request.session.get('airport_','')
        
                help_int = 0    
                for item in buildings.geometry:
                    edges = [] #границы данного элемента
                    str2 = str(item)
                    str2 = str2.replace('POLYGON ((','')
                    str2 = str2.replace('))','')   #оставляем только координаты
                    if not 'POINT' in str2:
                        coords = str2.split(',')
                        for item_coord in coords:
                            item_coord = item_coord.lstrip()
                            
                            in_arr = item_coord.split(' ')
                            try:
                                try:
                                    lat_in = float(in_arr[1])
                                except ValueError:
                                    lat_in = float(''.join(c for c in in_arr[1] if c.isdigit() or c == '.')) # удалаяет все кроме цифры и точки
                                try:
                                    lon_in = float(in_arr[0])
                                except ValueError:  
                                    lon_in = float(''.join(c for c in in_arr[0] if c.isdigit() or c == '.')) 
                                    
                                edges.append((lat_in,lon_in))
                            except ValueError:
                                lat_in = float(''.join(c for c in in_arr[1] if c.isdigit() or c == '.')) # удалаяет все кроме цифры и точки
                                lon_in = float(''.join(c for c in in_arr[0] if c.isdigit() or c == '.'))
                                edges.append((lat_in,lon_in))#
                        
                        color = 'orange'
                        if help_int == num_buildings:
                            color = 'purple'
                            if len(request.session.get('step',{}))!=0:
                                help_arr = request.session.get('steps',{})
                                edge_curr = request.session.get('step',{})['polygon']
                                initFind = False
                                for it_cur in edge_curr:
                                    if initFind:
                                        try:
                                            if it_cur[0] < min_lat_cur: min_lat_cur = it_cur[0]
                                            if it_cur[0] > max_lat_cur: max_lat_cur = it_cur[0]
                                            if it_cur[1] < min_lon_cur: min_lon_cur = it_cur[1]
                                            if it_cur[1] > max_lon_cur: max_lon_cur = it_cur[1]
                                        except TypeError:
                                            pass
                                    else:
                                        max_lat_cur = it_cur[0]
                                        min_lat_cur = it_cur[0]
                                        min_lon_cur = it_cur[1]
                                        max_lon_cur = it_cur[1]
                                        initFind = True
                                help_arr[str(help_int)] = {'p': request.session.get('step',{}), 'height': form.cleaned_data['height_building'],\
                                                'min_lt_b': min_lat_cur, 'max_lt_b': max_lat_cur,\
                                                    'min_ln_b': min_lon_cur, 'max_ln_b': max_lon_cur}
                                request.session['steps'] = help_arr
                                
                            request.session['step'] = {'polygon':edges}
                            request.session.modified = True
                        else:
                            color = 'orange'
    
                        map1.location = (edges[0][0],edges[0][1])
                        folium.Polygon(edges, color = 'red',  opacity = 0.9, weight = 1,  fill =True, fill_opacity = 0.6,\
                                fill_color = color).add_to(map1)
                        if color == 'purple':
                            map1.location = (edges[0][0],edges[0][1])
                            folium.Circle((edges[0][0],edges[0][1]),radius=50, opacity = 0.5, fill_opacity = 0.5, color = 'yellow',\
                                        fill_color = 'yellow').add_to(map1)

                    
                    help_int+=1
                    
                # str1 = buildings.columns
                # #рисование html документа на карте, не удалять - оставить для примера
                # title_html = '''<h3 style="position: fixed; top: 50px; left: 350px; width: 550px; height: 70px; 
                #         z-index: 900; font-size:12px"><b>{}</b></h3>
                #         '''.format(str1) 
                # map.get_root().html.add_child(folium.Element(title_html)) # добавляет html элемент на карту

                map1 = map1._repr_html_()
                steps = request.session.get('steps',{})
                contex = {'form': form, 'zones': map1, 'airport': airport_name, 'num_buildings': num_buildings, 'step_':steps}    
                return render(request,'polls/zones.html', contex)           
            except ox._errors.InsufficientResponseError:
                pass
            except:
                pass
    elif (request.method == "POST") and ('Load Aeroflot Tracks' in request.POST):
        form = forZones(request.POST)
        if form.is_valid():    
            #далее закомментить
            map1 = folium.Map(location = [55,45],zoom_start = 3, control_scale=True, prefer_canvas = True, zoom_control = False,\
                                tiles = 'OpenStreetMap')
            for  zone in ZoneForDB.objects.filter(name__contains = 'hAircraft=810.0AMSL'): #'hAircraft=8100.0AMSL'):
                reData = json.loads(zone.intervals)
            
                zone1 = createZoneFromElementOfDBWithLimits(reData, zone.latOfCenter, zone.longOfCenter, zone.stepOfAzimuth, \
                                                            500)

                try:
                    folium.Polygon(zone1, color = 'green',  opacity = 0.0, weight = 0,  fill =True, fill_opacity = 0.6,\
                                fill_color = 'green').add_to(map1)    
                except ValueError: # добавил обработку исключения, поскольку при нулевых значениях выпадала ошибка
                    pass

                # try:
                #     folium.Polygon(zoneFromIntervals(zone.latOfCenter,zone.longOfCenter,zone.stepOfAzimuth,reData), color = 'green',  \
                #                    opacity = 0.0, weight = 0,  fill =True, fill_opacity = 0.6,\
                #                 fill_color = 'green').add_to(map)
                # except ValueError: # добавил обработку исключения, поскольку при нулевых значениях выпадала ошибка
                #     pass
                
                

                folium.CircleMarker( location=[zone.latOfCenter,zone.longOfCenter],radius=2,tooltip = zone.name, \
                                    color='green',fill=True,fill_color='red').add_to(map1)
                folium.Marker(location=[zone.latOfCenter,zone.longOfCenter],
                                    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{zone.position}</p></div></html>''',
                                    class_name="mapText")).add_to(map1)
            
            #конец того, что комментить
            
            excel_data = pd.read_excel('polls\pointsOfAeroflot.xlsx')
            data = pd.DataFrame(excel_data, columns=['RouteId', 'DepStn','ArrStn','PointNr','StnName','FIR','Airway','Latitude',\
                                         'Longitude','Speed','FlightLevel','EET','Distance','CountryCode'])
            lst_RouteId = data['RouteId'].to_list()
            lst_DepStn = data['DepStn'].to_list()
            lst_ArrStn = data['ArrStn'].to_list()
            lst_PointNr = data['PointNr'].to_list()
            lst_StnName = data['StnName'].to_list()
            lst_FIR = data['FIR'].to_list()
            lst_Airway = data['Airway'].to_list()
            lst_Latitude = data['Latitude'].to_list()
            lst_Longitude = data['Longitude'].to_list()
            lst_Speed = data['Speed'].to_list()
            lst_FlightLevel = data['FlightLevel'].to_list()
            lst_EET = data['EET'].to_list()
            lst_Distance = data['Distance'].to_list()
            lst_CountryCode = data['CountryCode'].to_list()
            
            #загрузка данных расчета на 8000
            # strForKMLFile = "polls/8000_1.xml"
            # tree = ET.parse(strForKMLFile)
            # root = tree.getroot()
            # for i in range(0,len(root[0])):
            #     if root[0][i].tag == 'Placemark':
            #         for j in range(0,len(root[0][i])):
            #             if root[0][i][j].tag == 'Polygon':
            #                 for k in range(0,len(root[0][i][j])):
            #                     if root[0][i][j][k].tag == 'outerBoundaryIs':
            #                         rootCoordinates = root[0][i][j][k][0][0].text
            #                         listCoordStr = list(map(str,rootCoordinates.split(' ')))
            #                         listCoord= []
            #                         for item in listCoordStr:
            #                             str1 = ''.join(c for c in item if c.isdigit() or c == '.' or c == ',')
            #                             try:
            #                                 l1 = list(map(float,str1.split(',')))
            #                                 listCoord.append([l1[1],l1[0]])
            #                             except:
            #                                 pass
            #                         # folium.Marker(location=[54,41],
            #                         #    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{rootCoordinates}</p></div></html>''',
            #                         #             class_name="mapText")).add_to(map1)
            #         folium.Polygon(listCoord, color='green',opacity = 0.65, fill = True, fill_color = 'green',fill_opacity=0.6).add_to(map1)
            # tree = ET.parse("polls/8000centers.xml")
            # root = tree.getroot()
            # for i in range(0,len(root[0])):
            #     if root[0][i].tag == 'Placemark':
            #         for j in range(0,len(root[0][i])):
            #             if root[0][i][j].tag == 'name': 
            #                 nameCenter = root[0][i][j].text
            #             if root[0][i][j].tag == 'Point':
            #                 for k in range(0,len(root[0][i][j])):
            #                     if root[0][i][j][k].tag == 'coordinates':
            #                         l1 = list(map(float, root[0][i][j][k].text.split(',')))
            #                         latCenter = l1[1]
            #                         lonCenter = l1[0]
                    
            #         folium.CircleMarker(location = [latCenter,lonCenter], color = 'navy', opacity = 0.6, radius = 2).add_to(map1)
            #         folium.Marker(location=[latCenter,lonCenter],
            #                            icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{nameCenter}</p></div></html>''',
            #                                     class_name="mapText")).add_to(map1)

            #вывод координат курсора
            formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
            MousePosition(position="topright",\
                        separator=" ; ",
                        empty_string="NaN",
                        lng_first=False,
                        num_digits=20,
                        prefix="Coordinates:",
                        lat_formatter=formatter,
                        lng_formatter=formatter,).add_to(map1)
            fff = open('xyz.txt','w')
            lat =0 
            lon =0
            lat_pre =0 
            lon_pre =0
            help_str = ''
            for i in range(0, len(lst_ArrStn)):
                if (str(lst_Latitude[i])!='nan') and (str(lst_Longitude[i])!='nan'):
                    if str(lst_Latitude[i])[0] == 'N':
                        lat = int(str(lst_Latitude[i])[1:3])+float(str(lst_Latitude[i])[3:])/60
                    elif str(lst_Latitude[i])[0] == 'S':
                        lat = -(int(str(lst_Latitude[i])[1:3])+float(str(lst_Latitude[i])[3:])/60)
                    else:
                        lat = 0
                    if str(lst_Longitude[i])[0] == 'E':
                        lon = int(str(lst_Longitude[i])[1:4])+float(str(lst_Longitude[i])[4:])/60
                    elif str(lst_Longitude[i])[0] == 'W':
                        lon = -(int(str(lst_Longitude[i])[1:4])+float(str(lst_Longitude[i])[4:])/60)
                    else:
                        lon = 0
                    icon1 = folium.CustomIcon('polls/pod.ico',icon_size=(7, 7))
                    folium.Marker(location=[lat,lon], icon= icon1,).add_to(map1)
                    
                    if (lat_pre!=0) and (lon_pre!=0):
                        folium.PolyLine([(lat_pre,lon_pre),(lat, lon)],\
                                            opacity = 0.8, color='black',weight=1).add_to(map1)                      
                    help_str += str(lon)+','+str(lat)+',0 '
                    lat_pre =lat 
                    lon_pre =lon
                else:
                    if lat_pre!=0 and lon_pre!=0:
                        help_str += str(lon)+','+str(lat)+',0 '
                        fff.write('		<Placemark>\n')
                        fff.write('			<name>Aeroflot</name>\n')
                        fff.write('			<styleUrl>#msn_ylw-pushpin</styleUrl>\n')
                        fff.write('			<LineString>\n')
                        fff.write('				<tessellate>1</tessellate>\n')
                        fff.write('				<coordinates>\n')
                        fff.write('					'+help_str+'\n')
                        fff.write('				</coordinates>\n')
                        fff.write('			</LineString>\n')
                        fff.write('		</Placemark>\n')
                        help_str =''
                    lat =0
                    lon =0
                    lat_pre =lat 
                    lon_pre =lon

            fff.close
            map1 = map1._repr_html_()
            contex = {'form': form, 'zones': map1, 'airport': lst_Latitude}    
            return render(request,'polls/zones.html', contex) 
          
    elif (request.method == "POST") and ('LoadZones' in request.POST):
        form = forZones(request.POST)
        if form.is_valid():
            heightOfAircraft = form.cleaned_data['heightFlight']
            if form.cleaned_data['AboveGroundLevel']:
                help_str = 'hAircraft='+str(heightOfAircraft)+'.0AGL'
            else:
                help_str = 'hAircraft='+str(heightOfAircraft)+'.0AMSL'
            for  zone in ZoneForDB.objects.filter(name__contains = help_str):
                reData = json.loads(zone.intervals)
                
                #оставил для гарантированной прорисовки, чтобы проверять zoneFromIntervals
                # for intervals in reData.keys():
                #     for inList in reData[intervals]:
                #         folium.Polygon(funcForSegment(zone.latOfCenter,zone.longOfCenter,float(intervals), zone.stepOfAzimuth, \
                #                                     inList[0], inList[1], 10),weight = 1,\
                #                                         opacity = 0.3, color = 'orange',\
                #                                             fill =True, fill_opacity = 0.6, fill_color = 'orange').add_to(map1)
                #конец блока под удаление        
            
                zone1 = createZoneFromElementOfDBWithLimits(reData, zone.latOfCenter, zone.longOfCenter, zone.stepOfAzimuth, \
                                                            form.cleaned_data['limitDist'])

                try:
                    folium.Polygon(zone1, color = 'green',  opacity = 0.0, weight = 0,  fill =True, fill_opacity = 0.6,\
                                fill_color = 'green').add_to(map1)    
                except ValueError: # добавил обработку исключения, поскольку при нулевых значениях выпадала ошибка
                    pass

                # try:
                #     folium.Polygon(zoneFromIntervals(zone.latOfCenter,zone.longOfCenter,zone.stepOfAzimuth,reData), color = 'green',  \
                #                    opacity = 0.0, weight = 0,  fill =True, fill_opacity = 0.6,\
                #                 fill_color = 'green').add_to(map)
                # except ValueError: # добавил обработку исключения, поскольку при нулевых значениях выпадала ошибка
                #     pass
                
                if form.cleaned_data['isDrawingCircles']:  
                    radiusesInM = []
                    for i in range(1,math.trunc(maxDistForZoneInkm(reData)/50)+2):
                        radiusesInM.append(i*50000)
                    for radiusU in radiusesInM:
                        folium.Circle(location=[zone.latOfCenter,zone.longOfCenter],
                            radius=radiusU,
                            color='black',
                            weight=1,
                            fill=False
                            ).add_to(map1)
                        dist = math.trunc(radiusU/1000)
                        for az in (0,90,180,270):
                            (lat_,dlon_,alfa2_) = GeoFunctions.Direct_Geodezian_Task(zone.latOfCenter, az, 1000*dist)
                            folium.Marker(location=[lat_,zone.longOfCenter+dlon_],
                                        icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str(dist)+'km'}</p></div></html>''',
                                        class_name="mapText")).add_to(map1)

                folium.CircleMarker( location=[zone.latOfCenter,zone.longOfCenter],radius=2,tooltip = zone.name, \
                                    color='green',fill=True,fill_color='red').add_to(map1)
                folium.Marker(location=[zone.latOfCenter,zone.longOfCenter],
                                    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{zone.position}</p></div></html>''',
                                    class_name="mapText")).add_to(map1)
            
            # сюда добавляем проверку и отображение трасс
            if  form.cleaned_data['DrawTracks']:
                for track in TraceAN.objects.all():
                    pods = json.loads(track.pods)
                    lat_pre = 0
                    lon_pre = 0
                    for item in pods.keys():
                        if bool(pods[item][2]):
                            icon1 = folium.CustomIcon('polls/pnd.ico',icon_size=(10, 10))
                        else:
                            icon1 = folium.CustomIcon('polls/pod.ico',icon_size=(10, 10))
                        folium.Marker(location=[pods[item][0], pods[item][1]], icon= icon1,).add_to(map1)
                        folium.Marker(location=[pods[item][0]-0.0025*5,pods[item][1]+0.0083*5],\
                                      icon=folium.DivIcon(html=\
                                                          f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{item}</p></div></html>''',
                                            class_name="mapText"),
                        ).add_to(map1)
                        if lat_pre!=0 and lon_pre!=0:
                            folium.PolyLine([(lat_pre,lon_pre),(pods[item][0], pods[item][1])],\
                                            color='gray',weight=1).add_to(map1)
                            folium.Marker(location=[(pods[item][0]+lat_pre)/2,(pods[item][1]+lon_pre)/2],
                                        icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{track.name}</p></div></html>''',
                                        class_name="mapText")).add_to(map1)
                            lat_pre = pods[item][0]
                            lon_pre = pods[item][1]
                        else:
                            lat_pre = pods[item][0]
                            lon_pre = pods[item][1] 
    elif (request.method == "POST") and ('LoadKML' in request.POST):
        form = forZones(request.POST)
        if form.is_valid():
            strForKMLFile = "polls/8000_1.xml"
            tree = ET.parse(strForKMLFile)
            root = tree.getroot()
            for i in range(0,len(root[0])):
                if root[0][i].tag == 'Placemark':
                    for j in range(0,len(root[0][i])):
                        if root[0][i][j].tag == 'Polygon':
                            for k in range(0,len(root[0][i][j])):
                                if root[0][i][j][k].tag == 'outerBoundaryIs':
                                    rootCoordinates = root[0][i][j][k][0][0].text
                                    listCoordStr = list(map(str,rootCoordinates.split(' ')))
                                    listCoord= []
                                    for item in listCoordStr:
                                        str1 = ''.join(c for c in item if c.isdigit() or c == '.' or c == ',')
                                        try:
                                            l1 = list(map(float,str1.split(',')))
                                            listCoord.append([l1[1],l1[0]])
                                        except:
                                            pass
                                    # folium.Marker(location=[54,41],
                                    #    icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{rootCoordinates}</p></div></html>''',
                                    #             class_name="mapText")).add_to(map1)
                    folium.Polygon(listCoord, color='green',opacity = 0.65, fill = True, fill_color = 'green',fill_opacity=0.6).add_to(map1)
            tree = ET.parse("polls/8000centers.xml")
            root = tree.getroot()
            for i in range(0,len(root[0])):
                if root[0][i].tag == 'Placemark':
                    for j in range(0,len(root[0][i])):
                        if root[0][i][j].tag == 'name': 
                            nameCenter = root[0][i][j].text
                        if root[0][i][j].tag == 'Point':
                            for k in range(0,len(root[0][i][j])):
                                if root[0][i][j][k].tag == 'coordinates':
                                    l1 = list(map(float, root[0][i][j][k].text.split(',')))
                                    latCenter = l1[1]
                                    lonCenter = l1[0]
                    
                    folium.CircleMarker(location = [latCenter,lonCenter], color = 'navy', opacity = 0.6, radius = 2).add_to(map1)
                    folium.Marker(location=[latCenter,lonCenter],
                                       icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{nameCenter}</p></div></html>''',
                                                class_name="mapText")).add_to(map1)
                    
                    #for 22:34
            
    elif (request.method == "POST") and ('ViewDataHeight' in request.POST):
        form = forZones(request.POST)
        if form.is_valid():
            map1 = folium.Map(location = [55,100],zoom_start = 3, control_scale=True, prefer_canvas = True, zoom_control = False,\
                                tiles = 'OpenStreetMap')
            formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
            MousePosition(position="topright",\
                        separator=" ; ",
                        empty_string="NaN",
                        lng_first=False,
                        num_digits=20,
                        prefix="Coordinates:",
                        lat_formatter=formatter,
                        lng_formatter=formatter,).add_to(map1)
            arrHGT = [x for x in os.listdir('polls\mapsHgt') if x.endswith(".hgt")]
            for item in arrHGT:
                try:
                    latI = int(item[1:3])
                    lonI = int(item[4:7])
                    folium.Rectangle(   [(latI,lonI), (latI+1,lonI+1)], color='orange',opacity = 0.65, fill = True, \
                             fill_color = 'orange',fill_opacity=0.6, tooltip=item).add_to(map1)
                except:
                    pass
            
            
                    
    else:
        form = forZones()
            
    map1 = map1._repr_html_()
    contex = {'form': form, 'zones': map1}    
    return render(request,'polls/zones.html', contex)

def heights(request): # where is image results for all values of heights for position ()
    map = folium.Map(
            location = [54, 41],
            zoom_start = 9, control_scale=True, prefer_canvas = True, zoom_control = False,
            tiles = 'OpenStreetMap')
    #вывод координат курсора
    formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
    MousePosition(position="topright",\
                  separator=" ; ",
                  empty_string="NaN",
                  lng_first=False,
                  num_digits=20,
                  prefix="Coordinates:",
                  lat_formatter=formatter,
                  lng_formatter=formatter,).add_to(map)
    
    if  (request.method == "POST") and ('Zones' in request.POST): #загрузка высот зданий для аэропорта   
        form = forHeigths(request.POST)
        if form.is_valid() :
            caption = form.cleaned_data['position']
            if form.cleaned_data['AboveGroundLevel']:
                help_str = 'AGL'
                maxD = 150
                delD = 25
            else:
                help_str = 'AMSL'
                maxD = 300
                delD = 50
            zones = {}
            zones_ = {}
            for  zone in ZoneForDB.objects.filter(name__contains = help_str ):
                if zone.position ==caption:
                    reData = json.loads(zone.intervals) 
                    zone1 = createZoneFromElementOfDBWithLimits(reData, zone.latOfCenter, zone.longOfCenter, zone.stepOfAzimuth, \
                                                            500)     
                    zone2 = createZoneFromElementOfDBWithLimits(reData, zone.latOfCenter, zone.longOfCenter, zone.stepOfAzimuth, \
                                                            500)      
                    zones[int(zone.name[zone.name.index('hAircraft=')+10:zone.name.index('.0A')])] = zone1
                    #вторую надо чтобы не было при первой отрисовке влияния на вторую, поскольку объекты меняются
                    zones_[int(zone.name[zone.name.index('hAircraft=')+10:zone.name.index('.0A')])] = zone2

            map.location = [zone.latOfCenter,zone.longOfCenter]
            if len(zones)>0:
                # первая отрисовка
                zones_S = sorted(zones.items())
                for i in range(0,len(zones_S)):
                    if i == 0:
                        col = myFunc.intToColor(i)
                        folium.Polygon(zones_S[i][1], color = col,  opacity = 0.2, weight = 1.0,  fill =True, fill_opacity = 0.4,\
                                fill_color = col).add_to(map) 
                    else:
                        zone_h = zones_S[i][1]
                        zone_h[1].append(zones_S[i-1][1][0]) # добавляет в исключаемые островки внешний контур меньшей высоты
                        col = myFunc.intToColor(i)
                        folium.Polygon(zone_h, color = col,  opacity = 0.2, weight = 1.0,  fill =True, fill_opacity = 0.4,\
                                fill_color = col).add_to(map) 
                # вторая отрисовка  - здесь заполняются внутренние островки
                zones_S_ = sorted(zones_.items())
                for i in range(0,len(zones_S_)):
                    if i == 0:
                        pass
                    else: 
                        col = myFunc.intToColor(i)
                        folium.Polygon(zones_S_[i-1][1][1], color = col,  opacity = 0.2, weight = 1.0,  fill =True, fill_opacity = 0.4,\
                                fill_color = col).add_to(map)
                        
                # image position of center
                folium.CircleMarker(location = [zone.latOfCenter,zone.longOfCenter], color = 'navy', opacity = 0.6, radius = 2).\
                    add_to(map)
                folium.Marker(location=[zone.latOfCenter-0.01,zone.longOfCenter+0.01], opacity = 0.6,
                                icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{zone.position}</p></div></html>''',
                                class_name="mapText")).add_to(map)

            radiusesInM = []
            for i in range(1,math.trunc(maxD/delD)+2):
                radiusesInM.append(i*delD*1000)
            for radiusU in radiusesInM:
                folium.Circle(location=[zone.latOfCenter,zone.longOfCenter],
                    radius=radiusU,
                    color='black',
                    weight=1,
                    fill=False,
                    opacity = 0.5
                    ).add_to(map)
                dist = math.trunc(radiusU/1000)
                for az in (0,90,180,270):
                    (lat_,dlon_,alfa2_) = GeoFunctions.Direct_Geodezian_Task(zone.latOfCenter, az, 1000*dist)
                    folium.Marker(location=[lat_,zone.longOfCenter+dlon_], opacity = 0.6,
                                icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str(dist)+'km'}</p></div></html>''',
                                class_name="mapText")).add_to(map)  

            if  form.cleaned_data['DrawTracks']:
                for track in TraceAN.objects.all():
                    pods = json.loads(track.pods)
                    lat_pre = 0
                    lon_pre = 0
                    for item in pods.keys():
                        #рисуем только вокруг зоны отображения трассы, чтобы карта не глючила
                        if GeoFunctions.DistanceInLatLonHeight(zone.latOfCenter,zone.longOfCenter,0,pods[item][0], pods[item][1],0)<700000:
                            if bool(pods[item][2]):
                                icon1 = folium.CustomIcon('polls/pnd.ico',icon_size=(10, 10))
                            else:
                                icon1 = folium.CustomIcon('polls/pod.ico',icon_size=(10, 10))
                            folium.Marker(location=[pods[item][0], pods[item][1]], icon= icon1,).add_to(map)
                            folium.Marker(location=[pods[item][0]-0.0025*5,pods[item][1]+0.0083*5],\
                                        icon=folium.DivIcon(html=\
                                                            f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{item}</p></div></html>''',
                                                class_name="mapText"),
                            ).add_to(map)
                            if lat_pre!=0 and lon_pre!=0:
                                folium.PolyLine([(lat_pre,lon_pre),(pods[item][0], pods[item][1])],\
                                                color='gray',weight=1).add_to(map)
                                folium.Marker(location=[(pods[item][0]+lat_pre)/2,(pods[item][1]+lon_pre)/2],
                                            icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{track.name}</p></div></html>''',
                                            class_name="mapText")).add_to(map)
                                lat_pre = pods[item][0]
                                lon_pre = pods[item][1]
                            else:
                                lat_pre = pods[item][0]
                                lon_pre = pods[item][1] 
    else:
        form = forHeigths()

    map = map._repr_html_()
    contex = {'form': form,'heights': map}
    return render(request,'polls/heights.html', contex)

# нужен только на период создания БД по трассам
def fortraces(request):
    map = folium.Map(
            location = [54, 41],
            zoom_start = 9, control_scale=True, prefer_canvas = True, zoom_control = False,
            tiles = 'OpenStreetMap')
   
    #вывод координат курсора
    formatter = "function(num) {return L.Util.formatNum(num, 7) + ' &deg; ';};"
    MousePosition(position="topright",\
                  separator=" ; ",
                  empty_string="NaN",
                  lng_first=False,
                  num_digits=20,
                  prefix="Coordinates:",
                  lat_formatter=formatter,
                  lng_formatter=formatter,).add_to(map)
    
    if  (request.method == "POST") and ('Load Traces' in request.POST):
        #сюда добавляем рабочий код создания БД треков
        folium.CircleMarker(location = [54, 41], radius = 2).add_to(map)
        nameOfFilesOfRoutes = ["polls/enr3.1.1.pdf","polls/enr3.1.2.pdf","polls/enr3.2.pdf","polls/enr3.3.pdf"]
        for str_fn in  nameOfFilesOfRoutes:   
            reader = PdfReader(str_fn)
            number_of_pages = len(reader.pages)
            traced_opened = False #Переходит в True после присвоения первой точки трассы
            traceAN = {} # traceAN.clear() - очистка словаря
            name_of_trace =''
            lat_pre = 0
            lon_pre = 0
            i_pre = 0

            for page in reader.pages:         
                text = page.extract_text()              
                for i in range(0, len(text)-3):
                    if (ord(text[i])==61472 and text[i+1].isalpha and ord(text[i+1])!=32 and ord(text[i+2])==32 and text[i+3].isdigit)\
                        or (ord(text[i])==61472 and text[i+1].isalpha and ord(text[i+1])!=32 and text[i+2].isalpha and ord(text[i+2])!=32 \
                            and ord(text[i+3])==32 and text[i+3].isdigit):
                        if text[i+1:i+15].find('conti')<0:   #надо проверить не является ли продолжением трассы с предыдущей страницы        
                            traced_opened=False  # переход на другую трассу
                            # здесь надо загрузить в БД предыдущую трассу
                            traceJSON = json.dumps(traceAN, indent = 4)
                            TraceAN.objects.create(name = name_of_trace, pods = traceJSON)

                            # обнуляем предыдущий словарь, содержащий пункты донесения
                            traceAN.clear()

                            name_of_trace= text[i+1:i+7].replace(' ','')#определение наименования трассы

                    if (ord(text[i])==61472)  and (ord(text[i-1])==61554 or ord(text[i-1])==61552): # определение начала строки с символа 
                                                                                                    # пункта донесения
                        j = text.find(' ', i+1)
                        str1 = ''           
                        j = text.find('N', j)
                        while not ((text[j-1].isdigit()) or (text[j-2].isdigit())):
                            j = text.find('N', j+1)   # поскольку повторения есть 'N' после пробелов

                        for k in range(i+1,j-8): str1=str1+text[k]
                        m = (str1.find(' '))
                        if m==-1:
                            str2 = str1 #только для печати первой части до пробела b
                        else:
                            str2 = str1[:m]

                        m = 0
                        for k in range(1,7):
                            if text[j-k].isdigit(): m=m+1 # проверка сколько цифр входит до N

                        if m ==6:
                            latPND = int(text[j-6]+text[j-5])+int(text[j-4]+text[j-3])/60+int(text[j-2]+text[j-1])/3600
                        else:
                            str_in = ''  
                            for k in range(1,7+(6-m)):
                                if text[j-(7+(6-m)-k)].isdigit(): str_in = str_in+text[j-(7+(6-m)-k)]
                            latPND = int(str_in[0]+str_in[1])+int(str_in[2]+str_in[3])/60+int(str_in[4]+str_in[5])/3600
                        
                        m = text.find('E', j, j+15)
                        if m<0: m = text.find('W', j, j+15)
                        n=0
                        for k in range (1,8):
                            if (text[m-k].isdigit()): n=n+1
                        if n==7: 
                            lonPND = int(text[m-7]+text[m-6]+text[m-5])+int(text[m-4]+text[m-3])/60+int(text[m-2]+text[m-1])/3600
                        else:
                            str_in = ''
                            for k in range(1,8+(7-n)):
                                if text[m-(8+(7-n)-k)].isdigit(): str_in = str_in+text[m-(8+(7-n)-k)]
                            lonPND = int(str_in[0]+str_in[1]+str_in[2])+int(str_in[3]+str_in[4])/60+int(str_in[5]+str_in[6])/3600
                        
                        # подписывает ПОД
                        folium.Marker(location=[latPND-0.0025*5,lonPND+0.0083*5],
                        icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str2}</p></div></html>''',
                                            class_name="mapText"),
                        ).add_to(map)

                        # здесь надо добавить ПОД в словарь
                        

                        if ord(text[i-1])==61554:
                            icon1 = folium.CustomIcon('polls/pnd.png',icon_size=(11, 11))
                            traceAN[str2] = (latPND,lonPND,True)
                        else:
                            icon1 = folium.CustomIcon('polls/pod.png',icon_size=(11, 11))
                            traceAN[str2] = (latPND,lonPND,False)
                            
                        folium.Marker(location=[latPND,lonPND],
                        icon= icon1,
                        ).add_to(map)
                        if traced_opened: #рисует отрезок между двумя ПОДами
                            if lat_pre!=0 and lon_pre!=0 and text[i_pre:i].find('Далее')<0:
                                folium.PolyLine([(lat_pre,lon_pre),(latPND,lonPND)],popup=name_of_trace,
                                            color='gray',weight=1).add_to(map)
                                folium.Marker(location=[(latPND+lat_pre)/2,(lonPND+lon_pre)/2],
                                        icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{name_of_trace}</p></div></html>''',
                                        class_name="mapText")).add_to(map)
                            lat_pre = latPND
                            lon_pre = lonPND
                            i_pre = i
                        else:
                            lat_pre = latPND
                            lon_pre = lonPND
                            i_pre = i
                            traced_opened = True


    map = map._repr_html_()
    contex = {'fortraces': map}
    return render(request,'polls/fortraces.html', contex)

def firehose(request): #https://github.com/flightaware/firehose_examples/blob/master/python/example1/example1.py
    username = "treushnikovmv"
    apikey = "948c15180804e46a8d414cc792bec7451d256c84"
    compression = None        # set to "deflate", "decompress", or "gzip" to enable compression
    servername = "firehose.flightaware.com"
    map1 = folium.Map(
            location = [54, 41],
            zoom_start = 3, control_scale=True, prefer_canvas = True, zoom_control = False,
            tiles = 'OpenStreetMap')
    # Create socket
    sock = socket.socket(socket.AF_INET)
    # Create a SSL context with the recommended security settings for client sockets, including automatic certificate verification
    context = ssl.create_default_context()
    # the folowing line requires Python 3.7+ and OpenSSL 1.1.0g+ to specify minimum_version
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    ssl_sock = context.wrap_socket(sock, server_hostname = servername)
    # print("Connecting...")
    ssl_sock.connect((servername, 1501)) #не работает с VPN
    # print("Connection succeeded")

    # build the initiation command:
    initiation_command = "live username {} password {}".format(username, apikey)
    if compression is not None:
        initiation_command += " compression " + compression

    # send initialization command to server:
    initiation_command += "\n"
    if sys.version_info[0] >= 3:
        ssl_sock.write(bytes(initiation_command, 'UTF-8'))
    else:
        ssl_sock.write(initiation_command)

    # return a file object associated with the socket
    if compression is not None:
        file = InflateStream(sock = ssl_sock, mode = compression)
    else:
        file = ssl_sock.makefile('r')

    # use "while True" for no limit in messages received
    str1 = ''
    count = 1000
    while (count > 0):
        try :
            # read line from file:
            inline = file.readline()
            if inline == '':
                break

            str1+=json.dumps(inline, indent =4)
            j1 = json.loads(inline)
            if 'type' in j1:
                if j1['type']=='position':
                    try:
                        latV = float(j1['lat'])
                        lonV = float(j1['lon'])
                        strIdent = j1['ident']+'\\n'
                        if 'hexid' in j1:
                            strIdent+=j1['hexid']
                        folium.CircleMarker(location = [latV, lonV], radius = 2, tooltip=strIdent).add_to(map1)
                    except:
                        pass

            count = count - 1
        except socket.error as e:
            pass #print('Connection fail', e)

    # wait for user input to end
    # input("\n Press Enter to exit...");
    # close the SSLSocket, will also close the underlying socket
    ssl_sock.close()

    # folium.Marker(location=[54, 41],icon=folium.DivIcon(html=f'''<!DOCTYPE html><html><div style="font-size: 8pt"><p>{str1}</p></div></html>''',
    #                                     class_name="mapText")).add_to(map1)

    map1 = map1._repr_html_()
    contex = {'firehose': map1}
    return render(request,'polls/firehose.html', contex)