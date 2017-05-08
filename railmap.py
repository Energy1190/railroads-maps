
from parserus import *
from database import *

def get_info():
    size='many'
    x = get_stations(url='http://osm.sbin.ru/esr/region:mosobl:l')
    drop_table('stations')
    drop_table('neighbors')
    create_table('stations')
    create_table('neighbors', params='(name TEXT, neighbor1 TEXT, neighbor2 TEXT, neighbor3 TEXT, neighbor4 TEXT, neighbor5 TEXT)')
    datas = list(filter(None, prepare_data(x, size=size)))
    insert_to_table('stations', datas, size=size)

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
        get_info()
    return ([i['coordinate'] for i in generate_coordinate_map()], [[i[0], [i[2], i[3]]] for i in get_table('stations')])


