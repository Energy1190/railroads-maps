#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#        // Создание ломаной и добавление ее на карту
#        // map.addOverlay(new YMaps.Polyline([{% for i in data %} // new YMaps.GeoPoint({{ i[0] }}, {{ i[1] }}){% if not loop.last %},{% endif %}{% if loop.last %}]));{% endif %}
#        {% endfor %}

import time
import datetime
from flask import Flask, request, render_template, jsonify
from railmap import main as c_map

app = Flask(__name__)
maps = c_map()[0]
stations = c_map()[1]

@app.route("/", methods=['POST', 'GET'])
def hello():
    global maps, stations
    return render_template('main.html', data=maps, stations=stations, tochka=list((55,37)))

@app.route("/trains", methods=['POST', 'GET'])
def trains():
    args_r = {i: request.args.get(i) for i in list(request.args)}
    print(args_r['time'])
    print(datetime.datetime.now().timestamp())
    return jsonify(coordinate=[55,37])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

