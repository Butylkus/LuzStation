# -*- coding: utf-8 -*-

from app import app
from flask import url_for, send_from_directory, request, redirect
from flask import render_template


import os

from app import logic

@app.route('/favicon.ico')
def favicon():    
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

@app.route('/robots.txt')
def robots():    
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt')

@app.route('/main.css')
def css():    
    return send_from_directory(os.path.join(app.root_path, 'templates'), 'main.css')

@app.route('/graph.css')
def graphcss():    
    return send_from_directory(os.path.join(app.root_path, 'templates'), 'graph.css')

@app.route('/')
def index():
    title = logic.set_title()
    owmcast = logic.get_cast()
    localpreamble = "Текущая погода по датчикам"
    localweather = logic.get_local()   
    return render_template('base.html', title = title, owmcast = owmcast, localpreamble = localpreamble, localweather = localweather)

@app.route('/graph/<int:interval>')
def graph(interval):
    
    preamble = "Графики с датчиков за "
    if (interval == 24):
        preamble = preamble + "сутки"
        
        data = ("/graph/temperature24", '/graph/presure24', '/graph/humidity24')
    if (interval == 72):
        preamble = preamble + "трое суток"
        data = ("/graph/temperature72", '/graph/presure72', '/graph/humidity72')
    if (interval == 168):
        preamble = preamble + "неделю"
        data = ("/graph/temperature168", '/graph/presure168', '/graph/humidity168')
    if (interval == 720):
        preamble = preamble + "месяц"
        data = ("/graph/temperature720", '/graph/presure720', '/graph/humidity720')
        
    title = logic.set_title(preamble)
    return render_template('graph.html', title = title, preamble = preamble, data = data)

@app.route('/graph/presure24')
def pres24():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphpres24.svg')
@app.route('/graph/presure72')
def pres72():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphpres72.svg')
@app.route('/graph/presure168')
def pres168():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphpres168.svg')
@app.route('/graph/presure720')
def pres720():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphpres720.svg')

@app.route('/graph/humidity24')
def hmdt24():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphhmdt24.svg')
@app.route('/graph/humidity72')
def hmdt72():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphhmdt72.svg')
@app.route('/graph/humidity168')
def hmdt168():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphhmdt168.svg')
@app.route('/graph/humidity720')
def hmdt720():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphhmdt720.svg')

@app.route('/graph/temperature24')
def temp24():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphtemp24.svg')
@app.route('/graph/temperature72')
def temp72():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphtemp72.svg')
@app.route('/graph/temperature168')
def temp168():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphtemp168.svg')
@app.route('/graph/temperature720')
def temp720():
    return send_from_directory(os.path.join(app.root_path, 'static/graph/'), 'graphtemp720.svg')


### Прогноз погоды
@app.route('/forecast')
def forecats():
    title = logic.set_title("Погодное прогнозирование")
    preamble = "Прогноз на сегодня, завтра и послезавтра"
    today = logic.get_forecast(0)
    tomorow = logic.get_forecast(24)
    dayafter = logic.get_forecast(48)
    intervals = ("03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "00:00")
    return render_template('forecast.html', title = title, preamble = preamble, today = today, tomorow = tomorow, dayafter = dayafter, intervals = intervals)
