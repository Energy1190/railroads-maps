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
