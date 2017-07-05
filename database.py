import os
import sqlite3

def data():
    x = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(x, 'data')
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, 'data.db')
    return path

def check_exist_table(name):
    for i in get_table_list():
        for j in i:
            if j == name:
                return True
    return False

def get_table_list():
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''SELECT name FROM sqlite_master
                 WHERE type='table'
                 ORDER BY name;''')
    result = x.fetchall()
    c.close()
    return result

def create_table(name, params='(name TEXT, link TEXT, coordinateX REAL, coordinateY REAL)'):
    if check_exist_table(name):
        print('Table {0} already exists'.format(name))
        return True
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''CREATE TABLE {0}
                 {1}'''.format(name, params))
    c.commit()
    c.close()
    return True

def insert_to_table(name, datas, size='one', len='(?,?,?,?)'):
    if not check_exist_table(name):
        print('Table {0} does not exist'.format(name))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    if size == 'one':
        x.execute('''INSERT INTO {0} VALUES {1}'''.format(name, datas))
    else:
        x.executemany('''INSERT INTO {0} VALUES {1}'''.format(name, len), datas)
    c.commit()
    c.close()
    return True

def drop_table(name):
    if not check_exist_table(name):
        print('Table {0} does not exist'.format(name))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''DROP TABLE {0}'''.format(name))
    if not check_exist_table(name):
        print('Table {0} does not exist'.format(name))
        print('Success')
    c.commit()
    c.close()

def get_table(name, fild='name'):
    if not check_exist_table(name):
        print('Table {0} does not exist'.format(name))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    result = list(x.execute('''SELECT * FROM {0} ORDER BY {1}'''.format(name, fild)))[:]
    c.close()
    return [i for i in result]

def get_one_entry(table, name, fild='name', extend=False):
    if not check_exist_table(table):
        print('Table {0} does not exist'.format(table))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''SELECT * FROM {0} WHERE {2}='{1}' LIMIT 1'''.format(table, name, fild))
    result = x.fetchall()
    c.close()
    if len(result) == 1:
        return result[0]
    elif extend:
        x = ['second_name', 'third_name', 'check_name']
        for i in x:
            y = get_one_entry(table, name, fild=i)
            if y: return y
    else:
        return None

def get_many_entry(table, name, limit=10, fild='name'):
    if not check_exist_table(table):
        print('Table {0} does not exist'.format(table))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''SELECT * FROM {0} WHERE {3}='{1}' LIMIT {2}'''.format(table, name, limit, fild))
    result = x.fetchall()
    c.close()
    return result

def get_table_inner(name, name2):
    if not check_exist_table(name):
        print('Table {0} does not exist'.format(name))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    result = list(x.execute('''SELECT * FROM {0} INNER JOIN {1} ON ({0}.name={1}.name) ORDER BY name'''.format(name, name2)))[:]
    c.close()
    return [i for i in result]

def set_neighbors_table(name, list_data):
    def get_element_or_none(datas, num):
        try:
            return datas[num]
        except:
            return 'NULL'

    if not check_exist_table('neighbors'):
        print('Table {0} does not exist'.format('neighbors'))
        return None
    x = get_element_or_none
    datas = (name, x(list_data, 0), x(list_data, 1), x(list_data, 2), x(list_data, 3), x(list_data, 4))
    insert_to_table('neighbors', datas, size='one', len='(?,?,?,?,?,?)')

def table_len(num):
    return '({0})'.format(str('?,' * num)[:-1])

def set_nocoord_station(object):
    if not check_exist_table('error_stations'):
        print('Table {0} does not exist'.format('neighbors'))
        return None
    object['coordinates'] = ['1000','1000']
    x = prepare_data(object, size='one', ver=2, base_len=9)
    x = x[:-2]
    insert_to_table('error_stations', x, size='one', len='({0})'.format(str('?,'*7)[:-1]))

def prepare_data(datas, size='one', ver=1, base_len=0):
    def check_len(num, check):
        if num == check: return True
        print('Len check fail')
        return False

    def check_version(version):
        nonlocal datas
        if int(version) == 1: return (datas['name'], datas['link'], datas['coordinates'][0][0], datas['coordinates'][0][1])
        elif int(version) == 2: return (datas['name'], datas['second_name'], datas['third_name'], datas['check_name'], datas['link'],
                                        datas['location'], datas['number'], datas['coordinates'][0][0], datas['coordinates'][0][1])

    def refull_empty_fild(data2):
        if not data2.get('second_name'):
            data2['second_name'] = 'NULL'
        if not datas.get('second_name'):
            data2['second_name'] = 'NULL'
        if not datas.get('third_name'):
            data2['third_name'] = 'NULL'
        if not datas.get('check_name'):
            data2['check_name'] = 'NULL'
        if not datas.get('location'):
            data2['location'] = 'NULL'
        return data2

    if size == 'one':
        if datas.get('name') and datas.get('coordinates') and len(datas['coordinates']) and len(datas['coordinates'][0]):
            if datas.get('neighbors'):
                set_neighbors_table(datas['name'], datas['neighbors'])
            else:
                print('It looks like the station is not connected to any other station.')
                print(datas)
            datas = refull_empty_fild(datas)
            x = check_version(ver)
            if check_len(len(x), base_len): return x
            print(x)
            return None
        else:
            print('Error in the data, it seems like no name or missing coordinates')
            print(datas)
            set_nocoord_station(datas)
            return None
    else:
        return [prepare_data(i, size='one', ver=ver, base_len=base_len) for i in datas]

# x = [{'link': 'http://www.openstreetmap.org/browse/node/419254131', 'name': 'Черусти', 'neighbors': ['Струя', 'Воймежный'], 'coordinates': [('55.5422017', '40.0049896')]}, {'link': 'http://www.openstreetmap.org/browse/node/2496131234', 'name': 'Струя', 'neighbors': ['Черусти'], 'coordinates': [('55.5248998', '40.1079467')]}, {'link': 'http://www.openstreetmap.org/browse/node/61088523', 'name': 'Москва-Пассажирская-Курская', 'neighbors': ['Москва-Товарная Курская', 'Москва-Каланчевская', 'Серп и Молот'], 'coordinates': [('55.7577737', '37.6621837')]}, {'link': 'http://www.openstreetmap.org/browse/node/1994609812', 'name': 'Серп и молот', 'neighbors': ['Москва-Пассажирская-Курская', 'Карачарово'], 'coordinates': [('55.7480922', '37.6821069')]}]