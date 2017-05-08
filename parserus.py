import re
import requests

# Парсим расписание
# Пример ссылки на поезд - https://www.tutu.ru/view.php?np=947c0499
# 947c0499 - сущность поезда
def get_schedule(np=None):
    if not np:
        return [False, False, False, False, [False]]
    x = requests.get('https://www.tutu.ru/view.php?np=' + np)
    txt = x.text
    title = re.findall(r'<div class="title_block sched_title" style="margin-bottom:13px;">([\s<>\w\&;"=/→:.-]*)<div id="route-table">', txt)
    table = re.findall(r'<div class="dinamic_table center_elastic_block">([\s<>\w\&\%\d;"-\?=/→:,.]*)</tbody>', txt)
    type = re.findall(r'">([\w\s"]*)</', str(title))
    dest = re.findall(r'<b>([\w→\s]*)</b>', str(title))
    number = re.findall(r'">[\w\s"]*</[\s\\na-zA-Z>]*(\d*)', str(title))
    grath = str(re.findall(r'<div class="center_block movement_block">([\w\s\\n:]*)</div>', str(title))).replace('\\n','').replace('\\t','').replace('\\','').split(sep=':')[1][:-2]
    list_time_platform = re.findall(r'php\?nnst=\d*">([\.\w\d\s]*)[<>/atd\\n\t\s]*([-]*[:\d]*)[<>/atd\\n\t\s]*([-]*[:\d]*)[<>/atd\\n\t\s]*</tr>', str(table))
    return [str(type[0]), str(dest[0]), str(grath), str(number[0]), list_time_platform]

# Парсим станции
# Пример ссылки на список станций - http://osm.sbin.ru/esr/region:mosobl:l
def get_stations(url='http://osm.sbin.ru/esr/region:mosobl:l'):
    # Парсим координаты с карты
    # Пример ссылки на карту - http://www.openstreetmap.org/browse/node/419254131
    def get_geo_point(url):
        x = requests.get(url)
        txt = x.text
        geo_point = re.findall(r'<div class="details geo">[\:\"\w\s\\n\t]*<a href="/[\#\=\.\w\d]*/([\.\d]*)/([\.\d]*)">', txt)
        return geo_point

    result = []
    x = requests.get(url)
    txt = x.text
    start = r'(?<=<tr>)'
    simple_strings = r'(?:[\S]*[\s]*(?!</tr>){1,1})*'
    temp_txt = re.findall(start + simple_strings, txt)
    link = r'<a href="(http://www.openstreetmap.org/browse/node/[\d]*)">([\.\-\s\d\w]*)</'
    neighbors = r'<a href="#[\d]*">([\.\-\s\d\w]*)</a>'
    for i in range(len(temp_txt)):
        x = {}
        t = re.findall(link, temp_txt[i])
        if len(t) and len(t[0]) == 2:
            x['link'] = t[0][0]
            x['name'] = t[0][1]
        n = re.findall(neighbors, temp_txt[i])
        if n:
            x['neighbors'] = n
        if x.get('link'):
            x['coordinates'] = get_geo_point(x['link'])
        result.append(x)

    while True:
        for i in result:
            if not i:
                result.remove(i)
                break
        break

    return result


