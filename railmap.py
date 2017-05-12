import pickle
from parserus import *
from database import *

def bild_stations():
    size='many'
    x = get_stations(url='http://osm.sbin.ru/esr/region:mosobl:l')
    drop_table('stations')
    drop_table('neighbors')
    create_table('stations')
    create_table('neighbors', params='(name TEXT, neighbor1 TEXT, neighbor2 TEXT, neighbor3 TEXT, neighbor4 TEXT, neighbor5 TEXT)')
    datas = list(filter(None, prepare_data(x, size=size)))
    insert_to_table('stations', datas, size=size)

def bild_schedule():
    def generation_of_dates(list_object):
        result = []
        mouth_list = [0, 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        for i in list_object:
            x = i['mouth'].split(sep='(')
            year = x[1][:-1]
            if x[0] in mouth_list:
                mouth = mouth_list.index(x[0])
            else:
                assert False
            for j in i['days']:
                y = (year, mouth, j)
                result.append(y)
        return result

    def generation_of_times(time_list):
        result = []
        if len(time_list) != 4:
            return False
        if time_list[0] and len(time_list[0]) and ':' in time_list[0]:
            x = time_list[0].split(sep=':')
            result.append((int(x[0]), int(x[1])))
        else:
            result.append(None)
        if time_list[1] and len(time_list[1]) and 'м' in time_list[1]:
            x = re.findall(r'(\d*)\s?ч?м?\s?(\d*)\s?м?', time_list[1])
            x = x[0]
            if len(x) == 2 and x[1]:
                result.append((int(x[0]), int(x[1])))
            else:
                result.append((None, int(x[0])))
        else:
            result.append(None)
        if time_list[2] and len(time_list[2]) and ':' in time_list[2]:
            x = time_list[0].split(sep=':')
            result.append((int(x[0]), int(x[1])))
        else:
            result.append(None)
        if time_list[3] and len(time_list[3]) and 'м' in time_list[3]:
            x = re.findall(r'(\d*)\s?ч?м?\s?(\d*)\s?м?', time_list[3])
            x = x[0]
            if len(x) == 2 and x[1]:
                result.append((int(x[0]), int(x[1])))
            else:
                result.append((None, int(x[0])))
        else:
            result.append(None)
        return result

    drop_table('trains')
    drop_table('schedule')
    drop_table('working days')
    create_table('trains', params='(number TEXT, link TEXT, departure TEXT, arrival TEXT, periodicity TEXT)')
    create_table('schedule', params='(train TEXT, departure TEXT, arrival TEXT, station_link TEXT, station_name TEXT, station_number REAL, coming_time BLOB,'
                                    ' waiting_time BLOB, out_time BLOB, total_time BLOB)')
    create_table('working days', params='(train TEXT, departure TEXT, arrival TEXT, days BLOB)')
    lines, trains = get_schedule2('http://moskva.elektrichki.net/raspisanie/')

    trains_insert = []
    schedule_insert = []
    working_days_insert = []
    for i in trains:
        i['schedule'] = get_schedule_station(i)
        if i.get('periodicity_link'):
            i['work_days'] = get_days_of_work(i['periodicity_link'])

    for i in trains:
        da = i['path'].split(sep=' → ')
        times = generation_of_times([i['schedule']['coming_time'], i['schedule']['waiting_time'], i['schedule']['out_time'],i['schedule']['total_time']])
        times = list(map(pickle.dumps, times))
        if i['periodicity_link']:
            days = get_days_of_work(i['periodicity_link'])
            days = generation_of_dates(days)
            days = list(map(pickle.dumps, days))
        else:
            days = None
        trains_insert.append((i['train_number'], i['main_link'], da[0], da[1]))
        schedule_insert.append((i['train_number'], da[0], da[1], i['schedule']['link'], i['schedule']['name'], i['schedule']['station_number'], times[0],
                                times[1], times[2], times[3]))
        working_days_insert.append((i['train_number'], da[0], da[1], days))

    insert_to_table('trains', trains_insert, size='many', len='(?,?,?,?,?)')
    insert_to_table('schedule', schedule_insert, size='many', len='(?,?,?,?,?,?,?,?,?,?)')
    insert_to_table('working days', working_days_insert, size='many', len='(?,?,?,?)')

    drop_table('lines')
    create_table('lines', params='(list BLOB)')

    insert_to_table('lines', pickle.dumps(lines), len='(?)')

def bild_dependencies(lines):
    trains = []
    for i in get_table('schedule', fild='train'):
        trains.append(i[0])

    for i in get_many_entry('schedule', fild='train', limit=100):
        pass

def generate_coordinate_map():
    def lazy_check(x1, x2, y1, y2):
        xc1 =(round(x1, 3) + 0.2)*1000
        xc2 = (round(x1, 3) - 0.2)*1000
        yc1 = (round(y1, 3) + 0.2)*1000
        yc2 = (round(y1, 3) - 0.2)*1000
        xc = [i for i in range(int(xc2),int(xc1))]
        yc = [i for i in range(int(yc2),int(yc1))]
        x = int(round(x2, 3)*1000)
        y = int(round(y2, 3)*1000)
        if x in xc and y in yc:
            return True
        else:
            return False

    def get_coord(obj):
        names = obj
        cx = get_one_entry('stations', names[0])
        cy = get_one_entry('stations', names[1])
        try:
            if not lazy_check(cx[2], cy[2], cx[3], cy[3]):
                return None
            return {'name': names, 'coordinate': ([cx[2], cx[3]], [cy[2], cy[3]])}
        except TypeError:
            return None
    x = []
    for i in get_table_inner('stations', 'neighbors'):
        list(map(x.append, [(i[0], j) for j in [i[5], i[6], i[7], i[8], i[9]] if j != 'NULL']))

    while True:
        for i in x:
            i = list(i)
            i.reverse()
            i = tuple(i)
            if i in x:
                x.remove(i)
                break
        break

    for i in range(len(x)):
        x[i] = get_coord(x[i])

    x = list(filter(None, x))
    x = list(filter(lambda i: True if type(i) == dict else False, x))
    return x

def main():
    if not check_exist_table('stations'):
        bild_stations()
    if not check_exist_table('trains'):
        bild_schedule()
    return ([i['coordinate'] for i in generate_coordinate_map()], [[i[0], [i[2], i[3]]] for i in get_table('stations')])


