import re
from lxml import html
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

def get_stations2(url='http://osm.sbin.ru/esr/region:mosobl:l'):
    # Парсим координаты с карты
    # Может перестать работать, если на карты будут наносить область станции, а не конкретную точку.
    # Пример ссылки на карту - http://www.openstreetmap.org/browse/node/419254131
    def get_geo_point(url):
        x = requests.get(url)
        txt = x.text
        geo_point = re.findall(r'<div class="details geo">[\:\"\w\s\\n\t]*<a href="/[\#\=\.\w\d]*/([\.\d]*)/([\.\d]*)">', txt)
        return geo_point

    x = requests.get(url)
    # txt = x.text

    result = []
    tree = html.fromstring(x.text)
    buy_info3 = tree.xpath('//table//tr')
    for i in range(0, len(buy_info3)):
        dictus = {}
        x = list(buy_info3[i].iterlinks())
        if x:
            for xx in x:
                if 'http://www.openstreetmap.org/browse/node' in xx[2] and '127.0.0.1' not in xx[2]:
                    dictus['link'] = xx[2]
        x = str(buy_info3[i].text_content()).replace('\n', '').split(sep='     ')
        x = list(map(str.strip, x))
        for xx in range(len(x)):
            if not x[xx]:
                x[xx] = None
            if x[xx] == '':
                x[xx] = None
        x = list(filter(None, x))

        if str(x[0]).isnumeric():
            dictus['number'] = x[0]
            dictus['name'] = x[2]
            dictus['second_name'] = x[1]
        if len(x) > 3 and 'РЖД' not in x[3]:
            dictus['neighbors'] = x[3]
        for i in x:
            if 'Московско-' in i:
                dictus['location'] = i

        if dictus.get('link'):
            result.append(dictus)

    for i in result:
        if '\xa0' in i['name']:
            x = str(i['name']).split(sep='\xa0')
            i['name'] = x[0]
            i['third_name'] = ''.join(x[1:])
        if i.get('location'):
            i['location'] = i['location'].split(sep=', ')[1]
        i['check_name'] = str(i['name']).lower().replace('ё', 'е')
        i['coordinates'] = get_geo_point(i['link'])

    return result

# Парсим расписание
# Источник http://moskva.elektrichki.net/raspisanie/
def get_schedule2(url):
    x = requests.get(url)
    txt = x.text
    x.close()
    start = r'(?<=<div id="search_result">)'
    alls = r'[\S\s]*'
    temp = re.findall(start + alls, txt)
    assert len(temp)
    temp = temp[0]
    fragment = r'(?:[\S]*[\s]*(?!</table>){1,1}(?!<table class="main_table">){1,1})*'
    fragments = re.findall(fragment, temp)
    result1 = []
    result2 = []
    result3 = []
    c = 0
    for i in fragments:
        h2 = r'<h2>([\-\.\s\d\w]*)</h2>'
        td_main = r'(?<=<td class="train_name">)'
        td_graph = r'(?<=<td class="frequency">)'
        td_end = r'(?:[\S]*[\s]*(?!</td>){1,1})*'
        h2g = re.findall(h2, i)
        for j in h2g:
            j = '<h>' + j + '<h>'
            j = (j, c)
            result1.append(j)
        td_main_g = re.findall(td_main + td_end, i)
        for j in td_main_g:
            c += 1
            link = re.findall(r'<a href=.([\:\/\.\-\~\w\d]*).>', j)
            num = re.findall(r'.train_number.>([\/\d\w]*)<', j)
            direct = re.findall(r'.train_direction.>([\-\→\s\w\d]*)</', j)
            if len(link) and len(num) and len(direct):
                j = (link[0], num[0], direct[0])
            else:
                print(j)
                print(link, num, direct)
                j = (link, num, direct)
            result2.append(j)
        td_graph_g = re.findall(td_graph + td_end, i)
        for j in td_graph_g:
            x = re.findall(r'>[\s]{0,5}([\.\-\w\d]*)</', j)
            y = re.findall(r'<a href=\'([\:\/\.\-\~\w\d]*)\'>', j)
            if not len(y):
                y = (None,)
            j = x[0], y[0]
            result3.append(j)
        x = [{'periodicity': result3[i][0], 'periodicity_link': result3[i][1], 'main_link': result2[i][0],
              'train_number': result2[i][1], 'path': result2[i][2]} for i in range(len(result2))]
    return (result1, x)

# Парсим расписание поезда
# Пример ссылки http://elektrichki.net/raspisanie/iksha~odintsovo~6213/
def get_schedule_station(url):
    result = []
    x = requests.get(url)
    txt = x.text
    x.close()
    start = r'(?<=<table class="main_table">)'
    alls = r'(?:[\S]*[\s]*(?!</table>){1,1})*'
    temp = re.findall(start + alls, txt)
    tr_start = r'(?<=<tr)'
    tr_end = r'(?:[\S]*[\s]*(?!</tr>){1,1})*'
    temp = re.findall(tr_start + tr_end, temp[0])

    for i in temp:
        x = {}
        number = r'.st_num.>([\d]*)</'
        link_and_name = r'.st_name.><a href=.([\,\-\/\:\.\w\d]*).>([\-\w\d\s]*)<'
        coming = r'\=.coming.>[\<\>\D\s]*([\:\d]*)</'
        time = r'\<td class=.time.><div class=.timetable_pathtime.>[\\n\s]*([\s\d\w]*)</'
        out = r'\=.outgo.>[\<\>\D\s]*([\:\d]*)</'
        sum_time = r'\=.pathtime.>[\<\>\D\s]*([\s\d\w]*)</'
        lan = re.findall(link_and_name, i)
        try:
            x['station_number'] = re.findall(number, i)[0]
            x['link'] = lan[0][0]
            x['name'] = lan[0][1]
            x['coming_time'] = re.findall(coming, i)[0]
            x['waiting_time'] = re.findall(time, i)[0]
            x['out_time'] = re.findall(out, i)[0]
            x['total_time'] = re.findall(sum_time, i)[0]
            if 'ч' in x['waiting_time']:
                print(i)
        except:
            x['Fail'] = True
        result.append(x)
    result = list(filter(lambda x: False if x.get('Fail') else True, result))
    return result

# Парсим дни работы
# Пример ссылки http://elektrichki.net/dni-sledovania/moskva-belorusskaya~kubinka-1~6701/
def get_days_of_work(url):
    result = []
    x = requests.get(url)
    txt = x.text
    x.close()
    start = r'(?<=<div id=.full_calendar.)'
    alls = r'(?:[\S]*[\s]*)*'
    temp = re.findall(start + alls, txt)
    cal = re.findall(r'<div class=.calendar_month[\s\_]?calendars_list.>[\s]*([\(\)\d\w]*)[\s]*</div>', temp[0])
    temp = re.split(r'</table', temp[0])
    for i in range(len(temp)):
        days = re.findall(r'<td class=.selected.>[\s]*<div>([\d]*)', temp[i])
        if len(days):
            r = {'mouth': cal[i], 'days': days}
            result.append(r)

    return result

# Парсим карту станций
# Пример ссылки https://www.tutu.ru/06.php
def get_line_map(url):
    def get_html_text(url):
        x = requests.get(url)
        tree = html.fromstring(x.text)
        x.close()
        return tree

    def get_parser(obj):
        info = obj.xpath('.//body/div[@id="wrapper"]/div/div[@id="scheme_table"]/div/div/div[@class="row"]/*')
        zonenum = obj.xpath('.//body/div[@id="wrapper"]/div/div[@id="scheme_table"]/div/div')
        col_in_row = int(len(info) / len((zonenum)))
        return (info, col_in_row)

    def format_array(array, num):
        count = 0
        row = 0
        rows = [[]]
        for i in range(len(array)):
            if 'path' in list(array[i].classes):
                # rows[row].append(list(info[i].classes))
                if list(array[i].classes) == ['col', 'path', 'vertical']:
                    rows[row].append(('NULL', count, row))
                if 'round' in list(array[i].classes)[-1]:
                    rows[row].append((list(array[i].classes)[-1].replace('round', ''), count, row))
                x = array[i].text_content().replace('\n', '').replace('\t', '').replace('\xa0', '')
                if 'path' in list(array[i].classes)[-1] and list(array[i].classes)[-1].replace('path', ''):
                    rows[row].append(('NULL', count, row))
                if x:
                    rows[row].append(
                        (info[i].text_content().replace('\n', '').replace('\t', '').replace('\xa0', ''), count, row))
            count += 1
            if not count % num:
                row += 1
                count = 0
                rows.append([])
        return rows

    def generate_temp_dict(obj):
        nonlocal station_map
        temp = {}
        row_list = []
        for i in range(len(rows)):
            for j in range(len(rows[i])):
                if not station_map.get(rows[i][j][0]) and '...' not in rows[i][j][0] and 'NULL' not in rows[i][j][0]:
                    station_map[rows[i][j][0]] = []
                temp[(rows[i][j][1], rows[i][j][2])] = rows[i][j][0]

        for i in range(len(temp)):
            x = list(temp)[i]
            if x[0] not in row_list: row_list.append(x[0])

        row_list.sort()
        temp = {(row_list.index(i[0]) + 1, i[1]): temp[i] for i in temp}
        return temp

    def remove_null():
        nonlocal station_map
        nonlocal round_list
        for i in station_map:
            for j in station_map[i]:
                try:
                    if i not in station_map[j]:
                        station_map[j].append(i)
                except KeyError:
                    pass

        for i in round_list:
            try:
                del station_map[i]
            except:
                pass
    # Основная логика, основана на анализе карты
    def generate_graph(obj, temp, append_flag=False):
        def check_alg(obj, obj2, x, obj2check=True):
            nonlocal station_map
            nonlocal temp
            nonlocal append_flag
            nonlocal round_list
            for i in ['T', 'TL', 'TR', 'L', 'R']:
                if obj == i:
                    return False
            if obj and obj not in station_map[temp[x]]:
                if obj2check and obj2 not in round_list or not obj2check:
                    station_map[temp[x]].append(obj)
                    if obj != 'NULL': append_flag=True
                    return True
            return False

        nonlocal station_map
        nonlocal round_list
        i = obj
        for j in station_map:
            station_map[j] = list(filter(lambda x: False if x == "NULL" else True, station_map[j]))
            station_map[j] = list(filter(lambda x: False if 'T' in str(x) else True, station_map[j]))
            station_map[j] = list(filter(lambda x: False if 'R' in str(x) else True, station_map[j]))
            station_map[j] = list(filter(lambda x: False if 'L' in str(x) else True, station_map[j]))

        x = list(temp)[i]
        if '...' not in temp[x] and ',' not in temp[x] and 'NULL' not in temp[x] and temp[x] not in round_list:
            g = 0
            count = 0
            t = temp.get((x[0], x[1] + 1))
            while t == 'NULL' or t in round_list:
                if t == 'NULL':
                    count += 1
                    t = temp.get((x[0], x[1] + count))
                if t and t in round_list:
                    if t and 'TR' in t or t and 'RB' in t or t and 'BR' in t:
                        count2 = 0
                        while not t and count2 < 10 or t in round_list and count2 < 10:
                            count2 += 1
                            t = temp.get((x[0] - count2, x[1] + count))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] - count2, x[1] - count + 1))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] - count2, x[1] - count - 1))
                    if t and 'TL' in t or t and 'LB' in t or t and 'BL' in t:
                        count2 = 0
                        while not t and count2 < 10 or t in round_list and count2 < 10:
                            count2 += 1
                            t = temp.get((x[0] + count2, x[1] + count))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] + count2, x[1] - count + 1))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] + count2, x[1] - count - 1))
            check_alg(t, g, x, obj2check=False)
            count = 0
            t = temp.get((x[0], x[1] - 1))
            while t == 'NULL' or t in round_list:
                if t == 'NULL':
                    count += 1
                    t = temp.get((x[0], x[1] - count))
                if t and t in round_list:
                    if t and 'TR' in t or t and 'RB' in t or t and 'BR' in t:
                        if temp[x] == 'Аэропорт (Шереметьево)': print('Start DEBUG')
                        count2 = 0
                        while not t and count2 < 10 or t in round_list and count2 < 10:
                            count2 += 1
                            t = temp.get((x[0] - count2, x[1] - count))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] - count2, x[1] - count - 1))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] - count2, x[1] - count + 1))
                            if temp[x] == 'Аэропорт (Шереметьево)': print('End t', t)
                    if t and 'TL' in t or t and 'LB' in t or t and 'BL' in t:
                        count2 = 0
                        while not t and count2 < 10 or t in round_list and count2 < 10:
                            count2 += 1
                            t = temp.get((x[0] + count2, x[1] - count))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] + count2, x[1] - count - 1))
                            if not t or t and t in round_list:
                                t = temp.get((x[0] + count2, x[1] - count + 1))
            check_alg(t, g, x, obj2check=False)

    round_list = ['T', 'TL', 'TR', 'L', 'R', 'RB', 'BL']
    station_map = {}
    tree = get_html_text(url)
    info, col_in_row = get_parser(tree)
    rows = format_array(info, col_in_row)
    temp = generate_temp_dict(rows)

    for i in range(len(temp)):
        generate_graph(i, temp)

    remove_null()
    return station_map
