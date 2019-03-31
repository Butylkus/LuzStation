#!/usr/bin/python3
#coding=utf-8

import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'SomeFuckingLongSecretPhraseThatMightBeUsefullInFuture' 

key='d24355' #ключ для OWM, получаем его в личном кабинете: https://openweathermap.org/price . Бесплатного ключа заглаза
city_id='490069' #Айди ближайшего серьёзного города или своего населённогой пункта

#доступы в базу
#не забываем создать свою базу, юзверя в правами на запил и выпил данных. Само собой, не стоит оставлять всё по дефолту
dbhost = 'localhost'
dbbase = 'luz'
dbuser='luz'
dbpassword='luz'

#Для рисования графиков нам нужны интервалы (за 12, 40, 100500 часов от сего момента) и измерения (давление, влажность, температура).
intervals = [24,72,168,720] #в часах - сутки, трое суток, неделя, месяц
measures = ["temp","pres","hmdt"] #очевидно
