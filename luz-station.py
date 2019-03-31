#!/usr/bin/python3
#coding=utf-8


import os, sys, signal, threading
from datetime import datetime, timezone, timedelta, date
import pytz, time
import re
import pymysql as sql
import requests

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

from bmp280 import BMP280
import statistics as stat
import RPi.GPIO as GPIO
import Adafruit_DHT as dht
from svg.charts import time_series


#Импортируем конфиг
import config

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN) #DHT22 висит здесь, например



#Запиливаем стоп-сигналы
global stopsignal
stopsignal = False

###Погода с опевезермап
def owm_get():
   
    #Получаем погоду через апи ОВМ
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                     params={'id': config.city_id, 'units': 'metric', 'lang': 'ru', 'APPID': config.key})
        data = res.json()

    except Exception as e:
        print("Exception (weather):", e)
        pass

    #Записываем результаты в базу
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    time = datetime.now()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    #порядок в базе: date condition temp hmdt pres wind code (код - это код метеоусловий)
    query = "INSERT INTO webdata (`date`, `condition`, `temp`, `hmdt`, `pres`, `wind`,`code`) VALUES ('{5}', '{0}', {1}, {2}, {3}, {4},{6});".format(data['weather'][0]['description'], data['main']['temp'], data['main']['humidity'], int(data['main']['grnd_level']/1.333322), data['wind']['speed'], now, int(data['weather'][0]['id']))

    cursor.execute(query)
    db.commit()
    cursor.close()
    db.close()
    #print("Данные с OWM получены и занесены в базу")

###Прогноз с опевезермап
def forecast():
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast", params={'id': config.city_id, 'units': 'metric', 'lang': 'ru', 'APPID': config.key})
        data = res.json()
        for row in data['list']:
            query = "REPLACE INTO forecast (`condition`, `temp`, `hmdt`, `pres`, `wind`, `date`, `code`) VALUES ('{0}', {1}, {2}, {3}, {4}, '{5}', {6});".format(row['weather'][0]['description'], row['main']['temp'], row['main']['humidity'], int(row['main']['grnd_level']/1.333322), row['wind']['speed'], datetime.utcfromtimestamp(int(row['dt'])).strftime('%Y-%m-%d %H:%M:%S'), int(row['weather'][0]['id']))
            cursor.execute(query)
            db.commit()
    except Exception as e:
        print ("Exception (forecast):", e)
        pass

    cursor.close()
    db.close()
    #print("Прогноз OWM получен и занесён в базу")




def local_reader():
    bus = SMBus(1) #Шина датчика
    bmp280 = BMP280(i2c_dev=bus) #Создаём объект датчика
    global stopsignal
    
    temperature = []
    pressure = []
    humidity =[]
    
    #Считываем побольше показаний, чтобы усреднить колебания
    for i in range(0,12):
        dhthum, dhttemp = dht.read_retry(22, 18) #модель DHT и его пин
        if (humidity is not None) and (dhttemp is not None):
            temperature.append(dhttemp)
            humidity.append(dhthum)
        temperature.append(bmp280.get_temperature()) #Читаем температуру
        pressure.append(bmp280.get_pressure() / 1.333322) #Читаем давление и переводим в ммрст
        time.sleep(0.1)
    
    #берём медианы и окультуриваем значения
    mediantemp = float(round(stat.median(temperature), 1))
    medianpres = int(stat.median(pressure))
    medianhum = int(stat.median(humidity))
    #print('Медианы: {0}, {1}, {2}'.format(mediantemp, medianpres, medianhum))
    
    #Записываем результаты в базу
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    nowtime = datetime.now()
    now = nowtime.strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO localdata (`date`, `temp`, `pres`, `hmdt`) VALUES ('{0}', {1}, {2}, {3});".format(now, mediantemp, medianpres, medianhum)
    cursor.execute(query)
    db.commit()
    cursor.close()
    db.close()
    #print("Данные датчиков получены и занесены в базу")


#Получаем нужный параметр за нужный интервал в часах
def dynamics(interval=12,column=''):
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    
    #Mariadb понимает обьекты датавремя только в ISO. Подгоняем под интервал
    nowtime = datetime.now().replace(microsecond=0)
    nowtime.isoformat(" ")
    divider = timedelta(hours=interval, seconds=30)
    starttime = nowtime - divider
    
    query = "SELECT date, {1} FROM localdata WHERE date >= '{0}' ORDER BY date DESC;".format(starttime,column)
    cursor.execute(query)
    data = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    tz = pytz.timezone('Europe/Moscow')
    #готовим данные на выгрузку
    prepared = []
    for string in data:
        lastdate = string[0].replace(tzinfo=timezone.utc).astimezone(tz)
        getdate = lastdate.strftime("%m.%d.%Y %H:%M:%S")
        prepared.append(getdate)
        if (column == 'temp'): #ибо десятые таки важны только для температуры
            prepared.append(float(string[1]))
        else:
            prepared.append(int(string[1]))
    return (prepared)

#Рисуем графики
def graph_draw(interval=12,column=''):

    g = time_series.Plot({})

        #Доступные параметры одним списком:
        #width = 640,
        #height = 480,
        #graph_title = "TS Title",
        #show_graph_title = True,
        #no_css = True,
        #key = True,
        #scale_x_integers = True,
        #scale_y_integers = True,
        #min_x_value = 0,
        #min_y_value = 0,
        #show_data_labels = True,
        #show_x_guidelines = True,
        #show_x_title = True,
        #x_title = "Time",
        #show_y_title = True,
        #y_title = "Ice Cream Cones",
        #y_title_text_direction = 'bt',
        #stagger_x_labels = True,
        #x_label_format = "%m/%d/%y",



    g.width = 1400
    g.height = 720
    g.show_graph_title = True
    
    g.show_data_labels = None
    g.show_y_title = True
    g.scale_y_integers = True
    
    g.stagger_x_labels = True
    g.show_x_guidelines = True
    g.x_title = "Число и время"
    g.show_x_title = True

### Здесь подготовим названия и интервалыдля для красоты на графике
    if (column == 'temp'):
        legend = "Температура"
        g.y_title = "Температура,  \N{DEGREE SIGN}C"
        g.graph_title = "Динамика температуры воздуха за "
    if (column == 'hmdt'):
        legend = "Влажность"
        g.y_title = "Влажность, %"
        g.graph_title = "Динамика влажности воздуха за "
    if (column == 'pres'):
        legend = "Давление"
        g.y_title = "Давление, ммрст"
        g.graph_title = "Динамика атмосферного давления за "


    if (interval == 24):
        g.x_label_format = '%H:%M'
        g.timescale_divisions = '1 hours'
        g.graph_title = g.graph_title + "сутки"
    if (interval == 72):
        g.x_label_format = '%d.%m %H:%M'
        g.timescale_divisions = '3 hours'
        g.graph_title = g.graph_title + "трое суток"
    if (interval == 168):
        g.x_label_format = '%d.%m %H:%M'
        g.timescale_divisions = '8 hours'
        g.graph_title = g.graph_title + "неделю"
    if (interval == 720):
        g.x_label_format = '%d.%m'
        g.timescale_divisions = '24 hours'
        g.graph_title = g.graph_title + "месяц"

### Готово, прожиг!
    g.add_data({'data': dynamics(interval,column), 'title':legend})
    if (interval == 24):
        graphic =g.burn()
    else:
        graphic = re.sub(r"\.dataPointLabel {(.*)}.\.stagger", ".dataPointLabel {\ndisplay: none;\n}\n.stagger", g.burn(), flags=re.S)
    
    return (graphic)


def draw_graph():
    time.sleep(30) #просто чтобы успели получиться свежие данные
    for interval in config.intervals:
        for column in config.measures:
            readygraph = graph_draw(interval,column)
            #Путь можно указать любой, на малине по дефолту он примерно такой
            with open('/home/pi/LuzStation/app/static/graph/graph{1}{0}.svg'.format(interval,column), 'w') as f:
                f.write(readygraph)
        #print ("Графики за {0} часов готовы".format(interval))

###Главная функция демона
def weatherdemon():
    while not stopsignal:
        threading.Thread(target=local_reader).start()
        threading.Thread(target=owm_get).start()
        threading.Thread(target=draw_graph).start()
        threading.Thread(target=forecast).start()
        time.sleep(1800) #Интервал обновления в секундах. Внимательно смотрим свой тариф! Полчаса вполне достаточно.

### Выключатель демона
def stop(signum, frame):
    global stopsignal
    stopsignal = True
    GPIO.cleanup() 
    sys.exit("Демон остановлен")


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
weatherdemon()
