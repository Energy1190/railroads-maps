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

def get_one_entry(table, name):
    if not check_exist_table(table):
        print('Table {0} does not exist'.format(table))
        return False
    c = sqlite3.connect(data())
    x = c.cursor()
    x.execute('''SELECT * FROM {0} WHERE name='{1}' LIMIT 1'''.format(table, name))
    result = x.fetchall()
    c.close()
    if len(result) == 1:
        return result[0]

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

def prepare_data(datas, size='one'):
    if size == 'one':
        if datas.get('name') and datas.get('coordinates') and len(datas['coordinates']) and len(datas['coordinates'][0]):
            if datas.get('neighbors'):
                set_neighbors_table(datas['name'], datas['neighbors'])
            else:
                print('It looks like the station is not connected to any other station.')
                print(datas)
                return None
            x = (datas['name'], datas['link'], datas['coordinates'][0][0], datas['coordinates'][0][1])
            return x
        else:
            print('Error in the data, it seems like no name or missing coordinates')
            print(datas)
            return None
    else:
        return [prepare_data(i, size='one') for i in datas]

# x = [{'link': 'http://www.openstreetmap.org/browse/node/419254131', 'name': 'Черусти', 'neighbors': ['Струя', 'Воймежный'], 'coordinates': [('55.5422017', '40.0049896')]}, {'link': 'http://www.openstreetmap.org/browse/node/2496131234', 'name': 'Струя', 'neighbors': ['Черусти'], 'coordinates': [('55.5248998', '40.1079467')]}, {'link': 'http://www.openstreetmap.org/browse/node/61088523', 'name': 'Москва-Пассажирская-Курская', 'neighbors': ['Москва-Товарная Курская', 'Москва-Каланчевская', 'Серп и Молот'], 'coordinates': [('55.7577737', '37.6621837')]}, {'link': 'http://www.openstreetmap.org/browse/node/1994609812', 'name': 'Серп и молот', 'neighbors': ['Москва-Пассажирская-Курская', 'Карачарово'], 'coordinates': [('55.7480922', '37.6821069')]}]
