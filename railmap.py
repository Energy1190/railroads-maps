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
            lines[i] = list(lines[i])
            for j in range(len(lines[i])):
                lines[i][j] = list(lines[i][j])
                for n in range(len(lines[i][j])):
                    if type(lines[i][j][n]) == str:
                        lines[i][j][n] = lines[i][j][n].replace(',', '.')
                    lines[i][j][n] = float(lines[i][j][n])
        return lines

    def file_create(lines):
        pickle.dump(lines, map_file(action='wb'))

    def check_stations_name():
        stations = []
        r = True

        for i in get_table('schedule', fild='train'):
            if i[4] not in stations:
                stations.append(i[4])

        for i in stations:
            if not get_one_entry('stations', i, extend=True):
                if not check_regexp(i):
                    print(i, 'not found')
                    r = False

        return r

    if not check_stations_name():
        print('Some station not found. Fail')
        return False

    x = schedule_in_memory()
    lines = generate_lines_name(x)
    for i in lines:
        lines[i] = enter_statuon_in_line(i, x, lines[i])
        lines[i] = sort_and_remove(lines[i])
        for j in range(len(lines[i])):
            y = check_regexp(lines[i][j][0])
            try:
                lines[i][j] = (lines[i][j][1], y[0], y[-2:])
            except:
                print("Lines object is ", lines[i][j], "as type", type(lines[i][j]))
                print("Regexp object is", y, "as type", type(y))
                raise

    for i in lines:
        for j in range(len(lines[i])):
            if j+1 < len(lines[i]) and lines[i][j][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j][2], lines[i][j+1][2]))
            elif j-1 > 0 and j+1 < len(lines[i]) and lines[i][j-1][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j-1][2], lines[i][j+1][2]))
            elif j-2 > 0 and j+1 < len(lines[i]) and lines[i][j-2][0] + 1 == lines[i][j+1][0]:
                coordinate_lines.append((lines[i][j-2][2], lines[i][j+1][2]))

    point = {}
    y = detect_duplicate(coordinate_lines)
    for i in float_filter(y[0]):
        if tuple(i[0]) not in point:
            point[tuple(i[0])] = []
        if tuple(i[1]) not in point:
            point[tuple(i[1])] = []
        if tuple(i[1]) not in point[tuple(i[0])]:
            point[tuple(i[0])].append(tuple(i[1]))
        if tuple(i[0]) not in point[tuple(i[1])]:
            point[tuple(i[1])].append(tuple(i[0]))

    pickle.dump(point, map_file(action='wb'))

def build_map():
    x = pickle.load(map_file())
    maps = []
    for i in x:
        y = Station(get_one_entry('stations', i[0], fild='coordinateX', name2=i[1], fild2='coordinateY'))
        y.set_neighbors()
        y.check_neighbors(x[i], [j for j in x])
        for i in y.parent:
            if (i, (y.coordX, y.coordY)) not in maps or ((y.coordX, y.coordY), i) not in maps:
                maps.append((i, (y.coordX, y.coordY)))
            print((i, (y.coordX, y.coordY)))
    return maps

def build_graph():
    result = []
    lines_list = ['https://www.tutu.ru/06.php', 'https://www.tutu.ru/01.php', 'https://www.tutu.ru/02.php', 'https://www.tutu.ru/05.php',
                  'https://www.tutu.ru/04.php', 'https://www.tutu.ru/08.php', 'https://www.tutu.ru/03.php', 'https://www.tutu.ru/07.php',
                  'https://www.tutu.ru/09.php', 'https://www.tutu.ru/10.php']
    for i in lines_list:
        result.append(get_line_map(i))

    pickle.dump(result, map_file(action='wb',filename='graph.db'))

# --------------------------------- main function ----------------------------------------------------------------------
# Если отсутсвуют данные собирает информация о станциях, поездах и линиях из модуля parserus.py. И Выполняет их обработку
# для построения карты линий и станций. Возвращает список всех необходимых к построению линий и список всех необходимых к
# построению станций.
def main():
    x = os.path.dirname(os.path.abspath(__file__))
    if not check_exist_table('stations'):
        bild_stations()
    if not check_exist_table('trains'):
        bild_schedule()
    if not os.path.exists(os.path.join(x, 'data', 'graph.db')):
        build_graph()
    if not os.path.exists(os.path.join(x, 'data', 'map.db')):
        build_line()
    for i in pickle.load(map_file(filename='graph.db')):
        for j in i:
            if not i[j]:
                print(i, j)

#    return ([list(map(list, i)) for i in build_map()], [[i[0], [float(i[-2]), float(i[-1])]] for i in get_table('stations') if str(i[-2]).isnumeric() and str(i[-1]).isnumeric()])

# ----------------------------------------------------------------------------------------------------------------------

main()