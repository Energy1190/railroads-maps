import pickle
from parserus import *
from database import *

def bild_stations():
    def fail_parser():
        # Почему-то не добавляется, видимо происходит ошибка из-за ссылки не на координаты, а на область.
        insert_to_table('stations', ('Щелково', 'Щёлково', 'NULL', 'щелково', 'http://www.openstreetmap.org/node/4085266440#map=18/55.90939/38.01063&layers=N', 'NULL','NULL', '55,9093905', '38,0087521'), size='one')
    size='many'
    base_len = 9
    drop_table('stations')
    drop_table('neighbors')
    drop_table('error_stations')
    create_table('stations', params='(name TEXT, second_name TEXT, third_name TEXT, check_name TEXT, link TEXT, location TEXT, number REAL, coordinateX REAL, coordinateY REAL)')
    create_table('neighbors', params='(name TEXT, neighbor1 TEXT, neighbor2 TEXT, neighbor3 TEXT, neighbor4 TEXT, neighbor5 TEXT)')
    create_table('error_stations', params='(name TEXT, second_name TEXT, third_name TEXT, check_name TEXT, link TEXT, location TEXT, number REAL)')
    for i in ['http://osm.sbin.ru/esr/region:mosobl:l', 'http://osm.sbin.ru/esr/region:ryazan:l', 'http://osm.sbin.ru/esr/region:tul:l',
              'http://osm.sbin.ru/esr/region:kaluzh:l', 'http://osm.sbin.ru/esr/region:smol:l', 'http://osm.sbin.ru/esr/region:tver:l',
              'http://osm.sbin.ru/esr/region:yarosl:l', 'http://osm.sbin.ru/esr/region:ivanov:l', 'http://osm.sbin.ru/esr/region:vladimir:l']:
        x = get_stations2(url=i)
        datas = list(filter(None, prepare_data(x, size=size, ver=2, base_len=base_len)))
        insert_to_table('stations', datas, size=size, len='({0})'.format(str('?,'*base_len)[:-1]))

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
    drop_table('working_days')
    create_table('trains', params='(number TEXT, link TEXT, departure TEXT, arrival TEXT, periodicity TEXT)')
    create_table('schedule', params='(train TEXT, departure TEXT, arrival TEXT, station_link TEXT, station_name TEXT, station_number REAL, coming_time BLOB,'
                                    ' waiting_time BLOB, out_time BLOB, total_time BLOB)')
    create_table('working_days', params='(train TEXT, departure TEXT, arrival TEXT, days BLOB)')
    lines, trains = get_schedule2('http://moskva.elektrichki.net/raspisanie/')

    trains_insert = []
    schedule_insert = []
    working_days_insert = []

    for i in trains:
        i['schedule'] = get_schedule_station(i['main_link'])
        da = i['path'].split(sep=' → ')
        for j in i['schedule']:
            times = generation_of_times([j['coming_time'], j['waiting_time'], j['out_time'], j['total_time']])
            times = list(map(pickle.dumps, times))
            schedule_insert.append((i['train_number'], da[0], da[1], j['link'], j['name'],
                                    j['station_number'], times[0],
                                    times[1], times[2], times[3]))
        if i.get('periodicity_link'):
            days = get_days_of_work(i['periodicity_link'])
            days = generation_of_dates(days)
            days = pickle.dumps(days)
        else:
            days = None
        trains_insert.append((i['train_number'], i['main_link'], da[0], da[1], i['periodicity']))
        working_days_insert.append((i['train_number'], da[0], da[1], days))

    insert_to_table('trains', trains_insert, size='many', len='(?,?,?,?,?)')
    insert_to_table('schedule', schedule_insert, size='many', len='(?,?,?,?,?,?,?,?,?,?)')
    insert_to_table('working_days', working_days_insert, size='many', len='(?,?,?,?)')

    drop_table('lines')
    create_table('lines', params='(list BLOB, empty TEXT)')

    insert_to_table('lines', [(pickle.dumps(lines), None)], size='many', len='(?,?)')

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
    return ([i for i in build_line()], [[i[0], [float(i[-2]), float(i[-1])]] for i in get_table('stations') if str(i[-2]).isnumeric() and str(i[-1]).isnumeric()])

def check_regexp(name):
    def check(name):
        return get_one_entry('stations', name, extend=True)

    def logic(symbol, name, checks, symbol2=None):
        if symbol in name or symbol2 and symbol in name and symbol2 in name:
            x = check(checks)
            if x:
                return checks
        return None

    if check(name):
        return check(name)

    tests = []
    tests.append(logic('-', name, 'Аэропорт', symbol2='Внуково'))
    tests.append(logic('Аэропорт Внуково', name, 'Аэропорт'))
    tests.append(logic('Аэропорт', name, name.replace(' ', '-')))
    tests.append(logic('Остановочный Пункт', name, ' '.join(name.split(sep= ' ')[0:2]).lower()))
    tests.append(logic('Платформа', name, ' '.join(name.split(sep=' ')[-2:]).lower(), symbol2='Км'))
    tests.append(logic('Пост', name, ' '.join(name.split(sep=' ')[-2:]).lower(), symbol2='Км'))
    tests.append(logic('1', name, name.replace(' 1', '-I')))
    tests.append(logic('1', name, name.replace(' 1', '-1')))
    tests.append(logic('1', name, name.replace(' 1', ' I')))
    tests.append(logic('2', name, name.replace(' 2', '-II')))
    tests.append(logic('2', name, name.replace(' 2', '-2')))
    tests.append(logic('2', name, name.replace(' 2', ' II')))
    tests.append(logic('3', name, name.replace(' 3', '-III')))
    tests.append(logic('3', name, name.replace(' 3', '-3')))
    tests.append(logic('3', name, name.replace(' 3', ' III')))
    tests.append(logic('1', name, name.replace(' 1', '')))
    tests.append(logic('2', name, name.replace(' 2', '')))
    tests.append(logic('3', name, name.replace(' 3', '')))
    tests.append(logic('Платформа', name, name.replace('Платформа ', '')))
    tests.append(logic(' ', name, name.replace(' ', '-')))
    tests.append(logic('е', name, name.replace('е', 'ё', 1)))
    tests.append(logic('И', name, name.replace('И', 'и').replace('М', 'м')))
    tests.append(logic('и', name, name.upper()))
    tests.append(logic('Депо', name, 'Депо'))
    tests.append(logic('Березки Дачные', name, 'Берёзки-Дачные'))
    tests.append(logic('оо', name, name.replace('оо', 'о')))
    tests.append(logic('ая', name, name.replace('ая', 'ое')))
    tests.append(logic('й', name, name.replace('й', 'и')))
    try:
        tests.append(logic(' ', name, ' '.join([name.split(sep=' ')[0], name.split(sep=' ')[1].upper()])))
    except:
        pass

    for i in tests:
        if i:
            return check(i)

    return False

def build_line():
    coordinate_lines = []
    def schedule_in_memory():
        return [i for i in get_table('schedule', fild='train')]

    def generate_lines_name(x):
        lines = {}
        for i in x:
            sep = ':'.join([i[1],i[2]])
            if sep not in lines:
                lines[sep] = []
        return lines

    def enter_statuon_in_line(line, schedule_list, line_list):
        var = line.split(sep=':')
        for i in schedule_list:
            if var[0] == i[1] and var[1] == i[2]:
                line_list.append((i[4], int(i[5])))
        return line_list

    def output(lines):
        for i in lines:
            print('-----------------------', i, '-----------------------')
            for j in lines[i]:
                print(j)

    def sort_and_remove(line):
        x = sorted(line, key=lambda x: x[1])
        for i in x:
            while x.count(i) > 1:
                x.remove(i)
        return x

    def detect_duplicate(lines):
        count = 0
        for i in lines:
            while lines.count(i) > 1:
                count += 1
                lines.remove(i)
        return lines, count

    def float_filter(lines):
        # Ужасно тормозит
        for i in range(len(lines)):
            for j in range(len(lines[i])):
                for n in range(len(lines[i][j])):
                    lines[i][j][n] = float(lines[i][j][n])
        return lines

    x = schedule_in_memory()
    lines = generate_lines_name(x)
    for i in lines:
        lines[i] = enter_statuon_in_line(i, x, lines[i])
        lines[i] = sort_and_remove(lines[i])
        for j in range(len(lines[i])):
            y = check_regexp(lines[i][j][0])
            lines[i][j] = (lines[i][j][1], y[0], y[-2:])

    for i in lines:
        for j in range(len(lines[i])):
            if j+1 < len(lines[i]) and lines[i][j][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j][2], lines[i][j+1][2]))
            elif j-1 > 0 and j+1 < len(lines[i]) and lines[i][j-1][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j-1][2], lines[i][j+1][2]))
            elif j-2 > 0 and j+1 < len(lines[i]) and lines[i][j-2][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j-2][2], lines[i][j+1][2]))

    y = detect_duplicate(coordinate_lines)
    return y[0]

def check_stations_name():
    stations = []

    for i in get_table('schedule', fild='train'):
        if i[4] not in stations:
            stations.append(i[4])

    for i in stations:
        if not get_one_entry('stations', i, extend=True):
            if not check_regexp(i):
                print(i)

for i in build_line():
    print(i)