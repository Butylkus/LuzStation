#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import os, sys, signal, threading
from datetime import datetime, timezone, timedelta, date
import pytz
import pymysql as sql
import config

#Показывает данные с ОВМ
def get_cast():
    echoer = []
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    query = "SELECT * FROM webdata ORDER BY date DESC LIMIT 1;"
    cursor.execute(query)
    cast = cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()
    
    #Получаем и конвертируем дату
    tz = pytz.timezone('Europe/Moscow')
    lastdate = cast[0].replace(tzinfo=timezone.utc).astimezone(tz)
    castdate = lastdate.strftime("%d.%m %H:%M")
    echoer.append("{0}".format(castdate))
        
    desc = cast[1] #Описание погоды
    echoer.append("{0}".format(desc))
       
    temp = float(cast[2]) #Температура С
    echoer.append(temp)
    
    hum = int(cast[3]) #Влажность %
    echoer.append(hum)
    
    press = int(cast[4]) #Давление ммрст
    echoer.append(press)
    
    wind = float(cast[5]) #Ветер м/с
    echoer.append(wind)
    
    code = int(cast[6]) #Код метеусловий цифрами
    #Тут будет много ифов, список кодов тут: https://openweathermap.org/weather-conditions
    if (code == 801 or code == 802):
        pictogram = "fa-cloud-sun"
    if (code == 803 or code == 804):
        pictogram = "fa-cloud"
    if (code == 800):
        pictogram = "fa-sun"
    if (code == 771):
        pictogram = "fa-wind"
    if (code == 615 or code == 616):
        pictogram = "fa-cloud-meatball"
    if (code == 620 or code == 621 or code == 622 or code == 602 or code == 600):
        pictogram = "fa-snowflake"
    if (code > 510  and code < 532 ):
        pictogram = "fa-cloud-showers-heavy"
    if (code > 500 and code < 510):
        pictogram = "fa-cloud-rain"
    if (code == 500):
        pictogram = "fa-umbrella"
    if (code > 299 and code < 322):
        pictogram = "fa-cloud-meatball"
    if (code == 201 or code == 200):
        pictogram = "fa-bolt"
    if (code >201 and code < 299):
        pictogram = "fa-poo-storm"
    
    echoer.append(pictogram)
    
    return (echoer)


#Локальные замеры
def get_local():
    echoer = []
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    query = "SELECT * FROM localdata ORDER BY date DESC LIMIT 1;"
    cursor.execute(query)
    localdata = cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()

    #Получаем и конвертируем дату
    tz = pytz.timezone('Europe/Moscow')
    lastdate = localdata[0].replace(tzinfo=timezone.utc).astimezone(tz)
    getdate = lastdate.strftime("%d.%m %H:%M")
    echoer.append(getdate)
    
    temp = float(localdata[1]) #Температура С
    echoer.append(temp)
    
    hum = localdata[2] #Влажность %
    echoer.append(hum)
    
    press = localdata[3] #Давление ммрст
    echoer.append(press)

    return (echoer)

def set_title(string="Главная"):
    ender = ". Погодная станция Бутылкуса"
    return (string+ender)

def get_forecast(offset=0):
    structured = []
    echoer = []
    start = datetime.today()
    shift = timedelta(hours = 24)
    stop = start + shift
   
    if (offset == 24):
       start = datetime.today() + timedelta(hours = 24)
       stop = start + shift
    if (offset == 48):
       start = datetime.today() + timedelta(hours = 48)
       stop = start + shift
    
    
    db = sql.connect(host=config.dbhost, database=config.dbbase, user=config.dbuser, password=config.dbpassword, use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM forecast WHERE `date` >= %s AND `date` < %s ORDER BY `date`", (start.strftime('%Y-%m-%d'), stop.strftime('%Y-%m-%d 00:00')))
    forecast_today = cursor.fetchall()
    
    cursor.close()
    db.close()

    for row in forecast_today:
        
        desc = row[2] #Описание погоды
        echoer.append("{0}".format(desc))
       
        temp = float(row[3]) #Температура С
        echoer.append(temp)
    
        hum = int(row[4]) #Влажность %
        echoer.append(hum)
    
        press = int(row[5]) #Давление ммрст
        echoer.append(press)
    
        wind = float(row[6]) #Ветер м/с
        echoer.append(wind)
    
        code = int(row[1]) #Код метеусловий цифрами
        #Тут будет много ифов, список кодов тут: https://openweathermap.org/weather-conditions
        if (code == 801 or code == 802):
            pictogram = "fa-cloud-sun"
        if (code == 803 or code == 804):
            pictogram = "fa-cloud"
        if (code == 800):
            pictogram = "fa-sun"
        if (code == 771):
            pictogram = "fa-wind"
        if (code == 615 or code == 616):
            pictogram = "fa-cloud-meatball"
        if (code == 620 or code == 621 or code == 622 or code == 602 or code == 600):
            pictogram = "fa-snowflake"
        if (code > 510  and code < 532 ):
            pictogram = "fa-cloud-showers-heavy"
        if (code > 500 and code < 510):
            pictogram = "fa-cloud-rain"
        if (code == 500):
            pictogram = "fa-umbrella"
        if (code > 299 and code < 322):
            pictogram = "fa-cloud-meatball"
        if (code == 201 or code == 200):
            pictogram = "fa-bolt"
        if (code >201 and code < 299):
            pictogram = "fa-poo-storm"
    
        echoer.append(pictogram)
    
        structured.append([echoer])
        echoer = []
    structured.append(start.strftime('%d.%m.%y')) #Это выведется как дата в прогнозе
    return(structured)



# Вставка нового значения
# INSERT INTO `tasks` (status, content) VALUES (1, "Вторая запись (сделано)");


# Перевод в сделано
# UPDATE `tasks` SET `endtime`='{1}', `status`=1 WHERE id={0};


#delete from `tasks` where `id`=6;
