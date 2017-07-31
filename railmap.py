import math
import pickle
from parserus import *
from database import *

class Station():
    def __init__(self, tuple_obj):
        assert len(tuple_obj) == 9
        self.name = tuple_obj[0]
        self.coordX = tuple_obj[-2]
        self.coordY = tuple_obj[-1]
        self.coords = (self.coordX, self.coordY)
        self.neighbors = []
        self.neighbors_num = 0
        self.neighbors_coords = []

    def set_neighbors(self):
        x = get_one_entry('neighbors', self.name)
        if x:
            self.neighbors = list(filter(lambda x: False if x == 'NULL' else True, x[2:]))
            self.neighbors_num = int(x[1])
        for i in self.neighbors:
            y = get_one_entry('stations', i, extend=True)
            if y:
                cx,cy = y[-2:]
                self.neighbors_coords.append((cx,cy))

    def get_over_station(self, name):
        return get_one_entry('stations', name, fild='name', extend=True)

    def get_over_station_coords(self, coords):
        return get_one_entry('stations', coords[0], fild='coordinateX', name2=coords[1], fild2='coordinateY')

    def check_neighbors(self, list_obj, coords_list):
        def math_check(self, neighbors_coords, coords_list, coordX=self.coordX, coordY=self.coordY, result=[], count=0):
            count += 1
            if count == 500:
                return result
            areaX = (coordX-0.00001, coordX+0.00001)
            areaY = (coordY-0.00001, coordY+0.00001)
            for i in neighbors_coords:
                if areaX[1] > i[0] > areaX[0] and areaY[1] > i[1] > areaY[0] and len(result) <4 and (i[0], i[1]) != self.coords:
                    result.append(i)
            for i in coords_list:
                if areaX[1] > i[0] > areaX[0] and areaY[1] > i[1] > areaY[0] and len(result) < 4 and (i[0], i[1]) != self.coords:
                    result.append(i)
            if len(result) == 4 or len(result) == len(neighbors_coords):
                return result
            else:
                return math_check(self, neighbors_coords, coords_list, coordX=coordX, coordY=coordY, result=result, count=count)

        x = []
        for i in list_obj:
            if i in self.neighbors_coords:
                x.append(i)

        if self.neighbors_num == len(list_obj):
            x = []
            for i in list_obj:
                x.append(i)
            print("List is: ", list_obj)
            self.parent = x

        elif self.neighbors_num != len(list_obj):
            alls = []
            coords = []
            for i in self.neighbors:
                x = self.get_over_station(i)
                if x and (x[0], x[-2],  x[-1]) not in alls and (x[-2],  x[-1]) not in coords:
                    alls.append((x[0], x[-2],  x[-1]))
                    coords.append((x[-2],  x[-1]))
            for i in list_obj:
                x = self.get_over_station_coords(i)
                if x and (x[0], x[-2],  x[-1]) not in alls and (x[-2],  x[-1]) not in coords:
                    alls.append((x[0], x[-2],  x[-1]))
                    coords.append((x[-2], x[-1]))
            self.parent = math_check(self, coords, coords_list)

 #       print(self.name, self.neighbors_num, x)

def bild_stations():
    def fail_parser():
        # Почему-то не добавляется, видимо происходит ошибка из-за ссылки не на координаты, а на область.
        insert_to_table('stations', ('Щелково', 'Щёлково', 'NULL', 'щелково', 'http://www.openstreetmap.org/node/4085266440#map=18/55.90939/38.01063&layers=N', 'NULL','NULL', '55.9093905', '38.0087521'), size='one')
        # Видимо переименовано в Болдино, у станции нет координат на карте
        insert_to_table('stations', ('Сушнево', 'Сушнево', 'NULL', 'сушнево', 'http://www.openstreetmap.org/#map=18/55.96049/39.77948&layers=N', 'NULL','NULL', '55.96049', '39.77948'), size='one')

    size='many'
    base_len = 9
    drop_table('stations')
    drop_table('neighbors')
    drop_table('error_stations')
    create_table('stations', params='(name TEXT, second_name TEXT, third_name TEXT, check_name TEXT, link TEXT, location TEXT, number REAL, coordinateX REAL, coordinateY REAL)')
    create_table('neighbors', params='(name TEXT, count REAL, neighbor1 TEXT, neighbor2 TEXT, neighbor3 TEXT, neighbor4 TEXT, neighbor5 TEXT)')
    create_table('error_stations', params='(name TEXT, second_name TEXT, third_name TEXT, check_name TEXT, link TEXT, location TEXT, number REAL)')
    for i in ['http://osm.sbin.ru/esr/region:mosobl:l', 'http://osm.sbin.ru/esr/region:ryazan:l', 'http://osm.sbin.ru/esr/region:tul:l',
              'http://osm.sbin.ru/esr/region:kaluzh:l', 'http://osm.sbin.ru/esr/region:smol:l', 'http://osm.sbin.ru/esr/region:tver:l',
              'http://osm.sbin.ru/esr/region:yarosl:l', 'http://osm.sbin.ru/esr/region:ivanov:l', 'http://osm.sbin.ru/esr/region:vladimir:l']:
        x = get_stations2(url=i)
        datas = list(filter(None, prepare_data(x, size=size, ver=2, base_len=base_len)))
        insert_to_table('stations', datas, size=size, len='({0})'.format(str('?,'*base_len)[:-1]))
        fail_parser()

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

def check_regexp(name):
    def check(name):
        count = 0
        x = get_one_entry('stations', name, extend=True)
        if x:
            count = 1
            y = get_many_entry('stations', x[0], limit=10, fild='name')
            if len(y) > 1:
                count = len(y)
                x = y
        return (x, count)

    def logic(symbol, name, checks, symbol2=None):
        if symbol in name or symbol2 and symbol in name and symbol2 in name:
            x = check(checks)
            if x[1]:
                return checks
        return None

    if check(name)[1]:
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
    tests.append(logic('ё', name, name.replace('ё', 'е', 1).lower()))
    tests.append(logic('И', name, name.replace('И', 'и').replace('М', 'м')))
    tests.append(logic('и', name, name.upper()))
    tests.append(logic('Депо', name, 'Депо'))
    tests.append(logic('Березки Дачные', name, 'Берёзки-Дачные'))
    tests.append(logic('оо', name, name.replace('оо', 'о')))
    tests.append(logic('ая', name, name.replace('ая', 'ое')))
    tests.append(logic('й', name, name.replace('й', 'и')))
    tests.append(logic('Пл.', name, name.replace('Пл. ', '')))
    tests.append(logic('Пл.', name, ' '.join(name.split(sep=' ')[1:3])))
    tests.append(logic('о.п.', name, ' '.join(name.split(sep=' ')[1:3])))
    tests.append(logic(' (по треб.)', name, name.replace(' (по треб.)', '')))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[0])))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[:1])))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[:2]).lower().replace('Пл. ', '')))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[:3]).lower().replace('Пл. ', '')))
    tests.append(logic('Москва ', name, name.replace('Москва ', 'Москва-Пассажирская-')))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[1:3])))
    tests.append(logic('(', name, ' '.join(name.split(sep=' ')[2:4]).replace('(', '').replace(')', '')))
    tests.append(logic(' Тов.', name, name.replace(' Тов.', '-II')))
    tests.append(logic(' Пасс.', name, name.replace(' Пасс.', '-I')))
    tests.append(logic(' Пасс.', name, name.replace(' Пасс.', '-Пассажирская')))
    tests.append(logic(' Тов.', name, name.replace(' Тов.', '')))
    tests.append(logic(' Пасс.', name, name.replace(' Пасс.', '')))
    tests.append(logic(' Тов.', name, name.replace(' Тов.', '-Товарная')))
    tests.append(logic(' Сорт.', name, name.replace(' Сорт.', '-Сотировочное')))
    tests.append(logic(' Сорт.', name, name.replace(' Сорт.', '-Сотировочная')))
    tests.append(logic(' Центр.', name, name.replace(' Центр.', '-Центральное')))
    tests.append(logic('Москва Савёловская', name, name.replace('Москва Савёловская', 'Москва-Бутырская')))
    tests.append(logic(' Белорусская', name, name.replace(' Белорусская', '-Пассажирская-Смоленская')))
    tests.append(logic(' Ленинградская', name, name.replace(' Ленинградская', '-Пассажирская')))
    tests.append(logic('Пос.', name, name.replace('Пос.', 'Посёлок')))
    tests.append(logic('Кашира', name, name.replace('Кашира', 'Кашира-Пассажирская')))
    tests.append(logic('Рязань', name, 'Рязань-I'))
    tests.append(logic('Бекасово Сорт.', name, 'Бекасово-Сортировочное'))
    tests.append(logic('Малые Вязёмы', name, 'Малая Вязёма'))
    tests.append(logic('Москва Сорт.', name, 'Москва-Сортировочная'))
    tests.append(logic('Каланчёвская', name, name.replace('Каланчёвская', 'Москва-Каланчёвская')))
    tests.append(logic('К', name, name + ' I'))
    tests.append(logic('О', name, name + ' I'))
    tests.append(logic('Е', name, name + ' I'))
    try:
        tests.append(logic(' ', name, ' '.join([name.split(sep=' ')[0], name.split(sep=' ')[1].upper()])))
    except:
        pass

    for i in tests:
        if i:
            return check(i)

    return False

def build_graph():
    result = []
    lines_list = ['https://www.tutu.ru/06.php', 'https://www.tutu.ru/01.php', 'https://www.tutu.ru/02.php', 'https://www.tutu.ru/05.php',
                  'https://www.tutu.ru/04.php', 'https://www.tutu.ru/08.php', 'https://www.tutu.ru/03.php', 'https://www.tutu.ru/07.php',
                  'https://www.tutu.ru/09.php', 'https://www.tutu.ru/10.php']
    for i in lines_list:
        result.append(get_line_map(i))

    pickle.dump(result, map_file(action='wb',filename='graph.db'))

def bild_coord_graph():
    def check_duplicate_coord(obj_list, num):
        r = []
        x = obj_list[0][-2:]
        r.append(x)
        for i in range(num):
            if x != obj_list[i][-2:]:
                r.append(obj_list[i][-2:])
        return r

    def filter_station():
        nonlocal stations
        for i in stations:
            for j in stations[i]:
                while stations[i].count(j) > 1:
                    stations[i].remove(j)

    def pre_check_bild_stations():
        nonlocal fails, stations
        for i in pickle.load(map_file(filename='graph.db')):
            for j in i:
                flag = False
                g = []
                x = check_regexp(j)
                if x:
                    if x[1] > 1:
                        g = check_duplicate_coord(x[0], x[1])
                        if len(g) > 1:
                            flag = True
                    z = tuple(x[0])
                    if type(z[0]) == tuple:
                        z = z[0]
                    if not stations.get((j, z[-2:], tuple(g), flag)):
                        stations[(j, z[-2:], tuple(g), flag)] = i[j]
                    else:
                        stations[(j, z[-2:], tuple(g), flag)] = stations[(j, z[-2:], tuple(g), flag)] + i[j]
                else:
                    fails[j] = i[j]

    def correct_fail():
        nonlocal fails, stations
        # 'Пл. Аэропорт (Внуково) (старая платф.)' - исключение, удалить нафиг
        try:
            del fails['Пл. Аэропорт (Внуково) (старая платф.)']
        except:
            pass
        for i in fails:
            if fails[i] and len(fails[i]) == 2:
                for n in stations:
                    if fails[i][0] == n[0]:
                        stations[n].append(fails[i][1])
                    elif fails[i][1] == n[0]:
                        stations[n].append(fails[i][0])

    def get_graph_coord():
        nonlocal stations
        for i in stations:
            for j in range(len(stations[i])):
                g = []
                flag = False
                x = check_regexp(stations[i][j])
                if x:
                    if x[1] > 1:
                        g = check_duplicate_coord(x[0], x[1])
                        if len(g) > 1:
                            flag = True
                    z = tuple(x[0])
                    if type(z[0]) == tuple:
                        z = z[0]
                    stations[i][j] = (stations[i][j], z[-2:], tuple(g), flag)
                else:
                    print(stations[i][j])

    fails = {}
    stations = {}

    pre_check_bild_stations()
    filter_station()

    correct_fail()
    get_graph_coord()

    pickle.dump(stations, map_file(action='wb', filename='full_map.db'))

def bild_short_map(file):
    def build_sqad(obj, obj_list):
        x,y = obj
        for i in range(len(obj_list)):
            if i:
                l = []
                a, b = obj_list[i-1]
                a2, b2 = obj_list[i]
                for j in [(min(a,a2), max(b,b2), 4), (max(a,a2), min(b,b2), 2), (min(a,a2), min(b,b2), 1), (max(a,a2), max(b,b2), 3)]:
                    if j not in l:
                        l.append(j)
                l.sort(key=lambda x:x[-1])
                if l[0][0] < x < l[1][0] and l[0][1] < y < l[-1][1]:
                    return ((obj_list[i], obj_list[i-1]))


    def detect_coord(coord_list, over_coord_lists):
        check_list = []
        exit_list = []
        for i in over_coord_lists:
            if not i[-1]:
                check_list.append(i[1])
        if len(check_list) < 2:
            return (False, 0)
        else:
            result = []
            for i in coord_list:
                x = build_sqad(i, check_list)
                result.append(x)
            for i in range(len(result)):
                if result[i]:
                    exit_list.append((coord_list[i], result[i]))

        if exit_list and len(exit_list) == 1:
            return (exit_list[0][0],0)
        elif exit_list and len(exit_list) > 1:
            return (exit_list,len(exit_list))
        else:
            return (False, 0)

    def recusion_build(station_dict, num=1):
        exit_dict = {}
        for i in station_dict:
            if i[-num]:
                x,y = detect_coord(i[-2], [j for j in station_dict[i]])
                if x and not y:
                    exit_dict[(i[0], x, (), False, 0)] = station_dict[i]
                elif y:
                    for b in range(y):
                        exit_dict[(i[0], x[b][0], (), False, b)] = station_dict[i]
                else:
                    t = list(i)
                    t.append(0)
                    exit_dict[tuple(t)] = station_dict[i]
            else:
                t = list(i)
                t.append(0)
                exit_dict[tuple(t)] = station_dict[i]
        for i in exit_dict:
            for j in range(len(exit_dict[i])):
                for n in exit_dict:
                    if exit_dict[i][j][0] == n[0] and not n[-2]:
                        exit_dict[i][j] = n
        return exit_dict

    stations = pickle.load(map_file(filename=file))
    short_map = recusion_build(stations)
    for i in short_map:
        remove_elems = []
        obj = i[1]
        g = 1
        t = 1
        for j in range(len(short_map[i])):
            g = t
            if j:
                x,y = (short_map[i][j][1], short_map[i][j-1][1])
                if type(x) == tuple and type(y) == tuple:
                    t = build_sqad(obj,[x,y])
                    if not t and not g:
                        remove_elems.append(short_map[i][j-1])
        for j in remove_elems:
            short_map[i].remove(j)

    pickle.dump(short_map, map_file(action='wb', filename='short_map.db'))

def bild_coords_map(file):
    def remove_exeption(exeption_name, exeption_val):
        nonlocal regenerate_maps
        nonlocal maps
        if regenerate_maps[exeption_name].count(exeption_val):
            regenerate_maps[exeption_name].remove(exeption_val)
        if maps.count((exeption_name, exeption_val)):
            maps.remove((exeption_name, exeption_val))
        if regenerate_maps[exeption_val].count(exeption_name):
            regenerate_maps[exeption_val].remove(exeption_name)
        if maps.count((exeption_val, exeption_name)):
            maps.remove((exeption_val, exeption_name))

    def check_objects(obj, obj2):
        def x(o):
            if type(o[0]) == tuple:
                return o[0]
            else:
                return o
        for i in range(10):
            r1 = x(obj)
            r2 = x(obj2)
        return (r1,r2)

    # Расстояние между станциями не должно быть слишком большим - 0.2 градусаов максимум
    def simple_len_check(obj, list_obj):
        def check_result(list_obj):
            r = []
            for i in range(len(list_obj)):
                if list_obj[i] > 0.2:
                    r.append(i)
            return r

        resultX = []
        resultY = []
        x,y = obj
        for i in list_obj:
            a,b = i
            l1 = max(a,x) - min(a,x)
            l2 = max(b,y) - min(b,y)
            resultX.append(l1)
            resultY.append(l2)
        x = check_result(resultX)
        y = check_result(resultY)
        if x or y:
            rem = list(set.union(set(x),set(y)))
            r = []
            for i in rem:
                r.append(list_obj[i])
            for i in r:
                list_obj.remove(i)
        return list_obj

    # Станция не может иметь больше 4 станций-соседей
    def simple_count_check(stations):
        nonlocal station_count
        if not station_count.get(stations):
            station_count[stations] = 1
        else:
            station_count[stations] = station_count[stations] + 1

    # Путь к станции не может пересекать другой путь, дважды так точно
    def simple_collision_check(line_obj, over_line):
        if line_obj[0] == over_line[0] or line_obj[0] == over_line[1]:
            return False
        elif line_obj[1] == over_line[0] or line_obj[1] == over_line[1]:
            return False
        line_obj = tuple(map(lambda x: tuple(map(lambda y: int(y * 10000000),x)), line_obj))
        over_line = tuple(map(lambda x: tuple(map(lambda y: int(y * 10000000),x)), over_line))
        x,y = line_obj[0]
        x1,y1 = line_obj[1]
        a,b = over_line[0]
        a1,b1 = over_line[1]
        ma = max(over_line[0][0], over_line[1][0])
        mia = min(over_line[0][0], over_line[1][0])
        mb = max(over_line[0][1], over_line[1][1])
        mib = min(over_line[0][1], over_line[1][1])
        mx = max(line_obj[0][0], line_obj[1][0])
        mix = min(line_obj[0][0], line_obj[1][0])
        my = max(line_obj[0][1], line_obj[1][1])
        miy = min(line_obj[0][1], line_obj[1][1])
        n = ((a*b1 - a1*b)*(x1-x) - (a1-a)*(x*y1 - x1*y)) / ((a1 - a)*(y-y1) - (x1-x)*(b-b1))
        if mia < n < ma and mix < n < mx:
            check = ((y-y1)*n + (x*y1 - x1*y)) / (x1-x)
            if mib < -check < mb and miy < -check < my:
                return True

    stations = pickle.load(map_file(filename=file))
    station_count = {}
    coords = {}
    maps = []
    for i in stations:
        coords[i[1]] = []
        for j in stations[i]:
            if type(j[1]) == tuple:
                coords[i[1]].append(j[1])

    for i in coords:
        coords[i] = simple_len_check(i, coords[i])

    for i in coords:
        for j in coords[i]:
            simple_count_check(j)

    for i in station_count:
        if station_count[i] > 4:
            for j in coords:
                for jj in coords[j]:
                    if i == jj:
                        coords[j].remove(jj)

    for i in coords:
        for j in coords[i]:
            x,y = check_objects(i,j)
            if (x,y) not in maps:
                maps.append((x,y))

    collision_fails = []
    for i in maps:
        for j in maps:
            if i != j:
                if simple_collision_check(i, j): collision_fails.append((i,j))

    collision_fails_count = {}
    for i in collision_fails:
        for j in i:
            if collision_fails_count.get(j):
                collision_fails_count[j] = collision_fails_count[j] + 1
            else:
                collision_fails_count[j] = 1

    for i in collision_fails_count:
        if collision_fails_count[i] > 4:
            maps.remove(i)

    regenerate_maps = {}
    for i in maps:
        if not regenerate_maps.get(i[0]):
            regenerate_maps[i[0]] = []
        if not regenerate_maps.get(i[1]):
            regenerate_maps[i[1]] = []
        if i[1] not in regenerate_maps[i[0]]: regenerate_maps[i[0]].append(i[1])
        if i[0] not in regenerate_maps[i[1]]: regenerate_maps[i[1]].append(i[0])

    # Линии-паразиты: [55.7285836, 37.640936],[55.745199, 37.6893076]
    #                 [55.7045344, 37.6238334],[55.745199, 37.6893076]
    #                 [55.7237247, 37.3974261],[55.6100116, 37.2660261]
    exeption_list = [((55.7285836, 37.640936),(55.745199, 37.6893076)),((55.7045344, 37.6238334),(55.745199, 37.6893076)),
                     ((55.7237247, 37.3974261),(55.6100116, 37.2660261))]

    for i in exeption_list:
        remove_exeption(i[0],i[1])

    pickle.dump(regenerate_maps, map_file(action='wb', filename='coords_maps.db'))
    pickle.dump(maps, map_file(action='wb', filename='maps.db'))

def correct_coords_map(file):
    def simple_len_check(obj1, obj2):
        x,y = obj1
        x1,y1 = obj2
        l1 = max(x1,x) - min(x1,x)
        l2 = max(y1,y) - min(y1,y)
        if l1 < 0.3 and l2 < 0.3:
            return True

    def return_neighbors(neighbors_list, exeption):
        result = []
        if not neighbors_list:
            return False
        for i in neighbors_list[2:]:
            if i != "NULL" or i != exeption:
                x = get_one_entry('stations', i)
                if x: result.append(x)
        if result:
            return result

    def get_parent():
        nonlocal stations, stations_end
        for i in stations:
            if len(stations[i]) <= 1:
                y = get_one_entry('stations', i[0], fild='coordinateX', name2=i[1], fild2='coordinateY')
                if len(stations[i]) == 1:
                    e = get_one_entry('stations', stations[i][0][0], fild='coordinateX', name2=stations[i][0][1],
                                      fild2='coordinateY')
                    if e: e = e[0]
                else:
                    e = "NULL"
                n = get_one_entry('neighbors', y[0])
                parent = return_neighbors(n, e)
                stations_end[y] = parent

    stations_end = {}
    stations = pickle.load(map_file(filename=file))

    get_parent()
    for i in stations_end:
        for j in stations_end:
            if stations_end[i] == stations_end[j] and i != j and stations_end[i] and stations_end[j]:
                if simple_len_check(i[-2:], stations_end[j][0][-2:]):
                    if stations_end[j][0][-2:] not in stations[i[-2:]]: stations[i[-2:]].append(stations_end[j][0][-2:])
                if simple_len_check(j[-2:], stations_end[j][0][-2:]):
                    if stations_end[j][0][-2:] not in stations[j[-2:]]: stations[j[-2:]].append(stations_end[j][0][-2:])

    stations_end = {}
    get_parent()
    for i in stations_end:
        if not stations[i[-2:]]:
            stations[i[-2:]].append(stations_end[i][0][-2:])

    stations_end = {}
    get_parent()
    for i in stations_end:
        for j in stations_end:
            if stations_end[j] and i[0] == stations_end[j][0][0]:
                if simple_len_check(i[-2:], j[-2:]):
                    if j[-2:] not in stations[i[-2:]]: stations[i[-2:]].append(j[-2:])
                    if i[-2:] not in stations[j[-2:]]: stations[j[-2:]].append(i[-2:])

    stations_end = {}
    get_parent()

    maps = []
    for i in stations:
        for j in stations[i]:
            if (i,j) not in maps:
                maps.append((i,j))

    pickle.dump(stations, map_file(action='wb', filename=file))
    pickle.dump(maps, map_file(action='wb', filename='maps.db'))

def build_stations_coord(file):
    addict = pickle.load(map_file(filename=file))
    add = []
    for i in addict:
        x = get_one_entry('stations', i[0], fild='coordinateX', name2=i[1], fild2='coordinateY')
        if x and (x[0], x[-2], x[-1]) not in add:
            add.append((x[0], x[-2], x[-1]))

    stations = []
    stations_for_schedule = []
    for i in get_table('schedule', fild='station_name'):
        if i[4] not in stations_for_schedule:
            stations_for_schedule.append(i[4])

    for i in stations_for_schedule:
        x = check_regexp(i)[0]
        if type(x) == list:
            for j in check_regexp(i)[0]:
                if (j[0], j[-2], j[-1]) not in stations:
                    stations.append((j[0], j[-2], j[-1]))
        else:
            if (x[0], x[-2], x[-1]) not in stations:
                stations.append((x[0], x[-2], x[-1]))

    for i in add:
        if i not in stations:
            stations.append(i)

    pickle.dump(stations, map_file(action='wb', filename='stations.db'))

def correct_map_and_stations(file_stations, file_coordinate, file_map):
    stations_name = pickle.load(map_file(filename=file_stations))
    stations_coords = pickle.load(map_file(filename=file_coordinate))
    stations_map = pickle.load(map_file(filename=file_map))
    combinate = {}

    removeble = []
    for i in stations_name:
        if i[-2:] in stations_coords:
            combinate[i] = stations_coords[i[-2:]]
            removeble.append(i)

    for i in removeble:
        stations_name.remove(i)
        del stations_coords[i[-2:]]

    for i in stations_coords:
        for j in stations_coords[i]:
            if (i,j) in stations_map: stations_map.remove((i, j))

    for i in stations_name:
        combinate[i] = []

    pickle.dump(combinate, map_file(action='wb', filename='combinate_maps.db'))
    pickle.dump(stations_map, map_file(action='wb', filename=file_map))

def correct_checks(file):
    def generate_ends():
        nonlocal ends, alone, combinate
        ends = {}
        alone = []
        for i in combinate:
            if len(combinate[i]) == 1:
                ends[i] = combinate[i]
            if len(combinate[i]) == 0:
                alone.append(i)

    def ends_simple_detect(ends):
        def get_lines(main, parent):
            r = [0,0]
            x,y = main
            x1,y1 = parent
            mX,mY,miX,miY=(max(x,x1),max(y,y1),min(x,x1),min(y,y1))
            if mX == x:
                r[0] = lambda main,b: True if main<b else False
            else:
                r[0] = lambda main,b: True if main>b else False
            if mY == y:
                r[1] = lambda main,b: True if main<b else False
            else:
                r[1] = lambda main,b: True if main>b else False
            return r

        def get_sqad(obj,obj2):
            x,y = obj
            x1,y1 = obj2
            mX, mY, miX, miY = (max(x, x1), max(y, y1), min(x, x1), min(y, y1))
            sqad = (mX, mY, miX, miY)
            return ((mX-miX), (mY-miY), sqad)

        def get_perimeter(sqad):
            l1 = sqad[0] - sqad[2]
            l2 = sqad[1] - sqad[3]
            return (l1,l2)

        def get_diag(obj,obj2):
            x = get_sqad(obj,obj2)
            l1,l2 = get_perimeter(x[-1])
            line = math.sqrt(l1*l1 + l2*l2)
            return line

        def recursive(num=0.15, noconnect=False):
            nonlocal ends, connect
            endings = []
            for i in ends:
                for j in ends:
                    if i != j:
                        x, y = get_lines(i[-2:], ends[i][0])
                        if x(i[1], j[1]) and y(i[2], j[2]):
                            xl, yl, sqad = get_sqad(i[-2:], j[-2:])
                            if xl < num and yl < num and 'Москва-Пассажирская' not in i[
                                0] and 'Москва-Пассажирская' not in j[0]:
                                if 'Москва-Рижская' not in i[0] and 'Москва-Рижская' not in j[0]:
                                    if not noconnect:
                                        for n in alone:
                                            if sqad[2] < n[1] < sqad[0] and sqad[3] < n[2] < sqad[1]:
                                                if not connect.get(n):
                                                    connect[n] = [i, j]
                                    else:
                                        endings.append((i,j))
            if noconnect:
                return endings

        nonlocal alone,combinate
        while True:
            connect = {}
            recursive()
            if any(connect):
                for i in connect:
                    l1 = get_diag(i[-2:], connect[i][0][-2:])
                    l2 = get_diag(i[-2:], connect[i][1][-2:])
                    if l1 > l2 and connect[i][1] not in combinate[i]:
                        combinate[i].append(connect[i][1])
                    elif l1 < l2 and connect[i][0] not in combinate[i]:
                        combinate[i].append(connect[i][0])
                generate_ends()
            else:
                x = recursive(num=0.1,noconnect=True)
                for i in x:
                    if i[1] not in combinate[i[0]]: combinate[i[0]].append(i[1])
                    if i[0] not in combinate[i[1]]: combinate[i[1]].append(i[0])
                break

    combinate = pickle.load(map_file(filename=file))
    maps = pickle.load(map_file(filename='maps.db'))
    stations = pickle.load(map_file(filename='stations.db'))
    maxX = max(combinate, key=lambda x:x[1] if combinate[x] else 0)[1]
    minX = min(combinate, key=lambda x:x[1] if combinate[x] else 1000)[1]
    maxY = max(combinate, key=lambda x:x[2] if combinate[x] else 0)[2]
    minY = min(combinate, key=lambda x:x[2] if combinate[x] else 1000)[2]
    sqad = (maxX, minX, maxY, minY)

    removeble = []
    for i in combinate:
        if not minX < i[1] < maxX or not minY < i[2] < maxY:
            removeble.append(i)

    for i in removeble:
        del combinate[i]

    ends = {}
    alone = []

    generate_ends()
    ends_simple_detect(ends)

    for i in combinate:
        for j in combinate[i]:
            if (i[-2:],j[-2:]) not in maps:
                maps.append((i[-2:],j[-2:]))

    pickle.dump(combinate, map_file(action='wb', filename=file))
    pickle.dump(stations, map_file(action='wb', filename='stations.db'))
    pickle.dump(maps, map_file(action='wb', filename='maps.db'))

def correct_exeptions():
    def get_coord(name, count=0):
        nonlocal combinate, stations
        x = 0
        for i in combinate:
            if i[0] == name:
                x = i[-2:]
                if not count:
                    return x
                else:
                    count -= 1
        for i in stations:
            if i[0] == name:
                x = i[-2:]
                if not count:
                    return x
                else:
                    count -= 1
        if x:
            return x

    def maps_operator(obj, operator=None):
        nonlocal maps
        if operator == 'add' and obj not in maps:
            maps.append(obj)
        elif operator == 'rem':
            if obj in maps:
                maps.remove(obj)
            if (obj[1], obj[0]) in maps:
                maps.remove((obj[1], obj[0]))

    def len_check(x,y):
        a,b = x
        a1,b1 = y
        if max(a,a1) - min(a,a1) < 0.3 and max(b,b1) - min(b,b1) < 0.3:
            return True

    def added(station_name, station_name2, combinate):
        x = get_coord(station_name)
        y = get_coord(station_name2)
        count = 0
        while not len_check(x,y) and count < 10:
            count += 1
            x = get_coord(station_name, count)
            y = get_coord(station_name2, count)
        if x and y:
            for i in combinate:
                if i[-2:] == x and y not in combinate[i]:
                    combinate[i].append(y)
                if i[-2:] == y and x not in combinate[i]:
                    combinate[i].append(x)
            maps_operator((x,y), 'add')
        else:
            print('Error')
            print(station_name, station_name2)
            print(x,y)
        return combinate

    def removed(station_name, station_name2, combinate):
        x = get_coord(station_name)
        y = get_coord(station_name2)
        for i in combinate:
            for j in range(len(combinate[i])):
                if len(combinate[i][j]) == 3: combinate[i][j] = combinate[i][j][-2:]
            if i[-2:] == x and y in combinate[i]:
                combinate[i].remove(y)
            if i[-2:] == y and x in combinate[i]:
                combinate[i].remove(x)
        maps_operator((x, y), 'rem')
        return combinate

    combinate = pickle.load(map_file(filename='combinate_maps.db'))
    stations = pickle.load(map_file(filename='stations.db'))
    maps = pickle.load(map_file(filename='maps.db'))

    combinate = added('Москва-Товарная-Павелецкая', 'ЗИЛ', combinate)
    combinate = removed('Новопеределкино', 'Ромашково', combinate)
    combinate = removed('Захарово', 'Сушкинская', combinate)
    combinate = added('Голицыно', 'Захарово', combinate)
    combinate = added('199 км', 'Кубинка I', combinate)
    combinate = added('Туманово', 'Мещёрская', combinate)
    combinate = added('Азарово', 'Садовая (154 км)', combinate)
    combinate = added('Муратовка', 'Садовая (154 км)', combinate)
    combinate = added('Калуга II', 'Горенская', combinate)
    combinate = added('Тихонова Пустынь', 'Сляднево', combinate)
    combinate = added('Нара', 'Зосимова Пустынь', combinate)
    combinate = added('Бекасово I', 'Ожигово', combinate)
    combinate = removed('Латышская', 'Пожитково', combinate)
    combinate = removed('Зосимова Пустынь', 'Пожитково', combinate)
    combinate = removed('Зосимова Пустынь', 'Ожигово', combinate)
    combinate = removed('Ожигово', 'Пожитково', combinate)
    combinate = removed('Зосимова Пустынь', 'Посёлок Киевский', combinate)
    combinate = added('Бекасово I', 'Посёлок Киевский', combinate)
    combinate = added('Бекасово I', 'Пожитково', combinate)
    combinate = added('Сандарово', 'Столбовая', combinate)
    combinate = added('Космос', 'Аэропорт-Домодедово', combinate)
    combinate = added('Ленинская', 'Домодедово', combinate)
    combinate = added('Лагерный', 'Рязань-II', combinate)
    combinate = added('Рязань-I', 'Рязань-II', combinate)
    combinate = added('Осаново', 'Пожога', combinate)
    combinate = added('Ундол', 'Сушнево', combinate)
    combinate = added('Металлург', 'Фрязево', combinate)
    combinate = added('Наугольный', '81 км', combinate)
    combinate = added('Бужаниново', '90 км', combinate)
    combinate = added('Арсаки', '90 км', combinate)
    combinate = added('Струнино', 'Александров', combinate)
    combinate = added('Струнино', 'Александров-2', combinate)
    combinate = added('Александров', 'Александров-2', combinate)
    combinate = added('Александров', 'Мошнино', combinate)
    combinate = added('71 км', 'Костино', combinate)
    combinate = removed('Жилино', 'Поваровка', combinate)
    combinate = removed('Депо', 'Поваровка', combinate)
    combinate = added('Депо', 'Жилино', combinate)
    combinate = removed('Поваровка', 'Берёзки-Дачные', combinate)
    combinate = added('Поварово I', 'Берёзки-Дачные', combinate)
    combinate = added('Шереметьевская', 'Аэропорт Шереметьево', combinate)
    combinate = added('Манихино I', '50 км', combinate)
    combinate = added('Ромашково', 'Рабочий Посёлок', combinate)
    combinate = removed('Депо', '142 км', combinate)

    pickle.dump(combinate, map_file(action='wb', filename='combinate_maps.db'))
    pickle.dump(stations, map_file(action='wb', filename='stations.db'))
    pickle.dump(maps, map_file(action='wb', filename='maps.db'))

# --------------------------------- main function ----------------------------------------------------------------------
# Если отсутсвуют данные собирает информация о станциях, поездах и линиях из модуля parserus.py. И Выполняет их обработку
# для построения карты линий и станций. Возвращает список всех необходимых к построению линий и список всех необходимых к
# построению станций. Создание большого кол-ва вспомогательных файлов обусловленно большим временем исполнения операции
def main():
    x = os.path.dirname(os.path.abspath(__file__))
    def parser_work():
        if not check_exist_table('stations'):
            bild_stations()
        if not check_exist_table('trains'):
            bild_schedule()

    def maps_work(x):
        if not os.path.exists(os.path.join(x, 'data', 'graph.db')):
            build_graph()
        if not os.path.exists(os.path.join(x, 'data', 'full_map.db')):
            bild_coord_graph()
        if not os.path.exists(os.path.join(x, 'data', 'short_map.db')):
            bild_short_map('full_map.db')
        if not os.path.exists(os.path.join(x, 'data', 'coords_maps.db')):
            bild_coords_map('short_map.db')

    def stations_work(x):
        if not os.path.exists(os.path.join(x, 'data', 'stations.db')):
            build_stations_coord('coords_maps.db')

    def correction_work(x):
        correct_coords_map('coords_maps.db')
        correct_map_and_stations('stations.db', 'coords_maps.db', 'maps.db')
        correct_checks('combinate_maps.db')
        correct_exeptions()

    def final_correct(x):
        y = pickle.load(map_file(filename='combinate_maps.db'))
        for i in ['maps.db', 'stations.db', 'full_map.db', 'graph.db', 'short_map.db', 'coords_maps.db',
                  'combinate_maps.db']:
            map_file(filename=i).close()
            if os.path.exists(os.path.join(x, 'data', i)):
                os.remove(os.path.join(x, 'data', i))

        removeble = []
        for i in y:
            if not y[i]:
                removeble.append(i)
            for j in range(len(y[i])):
                if len(y[i][j]) == 3: y[i][j] = y[i][j][-2:]

        for i in removeble:
            del y[i]

        pickle.dump(y, map_file(action='wb', filename='fmaps.db'))

    def generate_maps(dict_obj):
        maps = []
        for i in xd:
            for j in xd[i]:
                if (i[-2:], j) not in maps and (j, i[-2:]) not in maps:
                    maps.append((i[-2:], j))

        maps = list(map(list, maps))
        for i in range(len(maps)):
            maps[i] = list(map(list, maps[i]))

        return maps

    if not os.path.exists(os.path.join(x, 'data', 'data.db')):
        parser_work()

    if not os.path.exists(os.path.join(x, 'data', 'fmaps.db')):
        maps_work(x)
        stations_work(x)
        correction_work(x)
        final_correct(x)

    x = map_file(filename='fmaps.db')
    xd = pickle.load(x)
    stations = [[i[0], [i[-2],i[-1]]] for i in xd]
    maps = generate_maps(xd)

    return (maps, stations)

# ----------------------------------------------------------------------------------------------------------------------

main()
