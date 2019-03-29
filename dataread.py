def data_read(path):
    """
    read in file path and transform into dict
    {Id: {attr: number}}
    ATTENTION:
    from -> from_v
    to -> to_v
    roadId -> roadId1 - roadId4
    :param path: string
    :return: dict
    """
    with open(path, 'r') as raw:
        attr = raw.readline()[2:-2].split(',')
        if attr[1] == 'from':
            attr[1] = 'from_v'
            attr[2] ='to_v'
        elif attr[4] == 'from':
            attr[4] = 'from_v'
            attr[5] = 'to_v'
        elif attr[1] == 'roadId':
            for i in range(1,5):
                attr[i] = attr[i] + str(i)
        data = {}
        for line in raw:
            line = line.replace('\n','')[1:-1].split(',')
            n_line = [int(s) for s in line]
            data[n_line[0]] = dict(zip(attr[1:], n_line[1:]))
    return data

def dict_generate(Cls, path):
    """
    read in file path and transform into OBJECT dict
    {Id: Obj}
    ATTENTION:
    from -> from_v
    to -> to_v
    roadId -> [roadId1, roadId2, roadId3, roadId4]
    :param path: string
    :param Cls: Car / Road / Cross
    :return: dict
    """
    obj_dict = {}
    with open(path, 'r') as raw:
        attr = raw.readline()[2:-2].split(',')

        if attr[1] == 'from':
            attr[1] = 'from_v'
            attr[2] ='to_v'
        elif attr[4] == 'from':
            attr[4] = 'from_v'
            attr[5] = 'to_v'
        elif attr[1] == 'roadId':
            for i in range(1,5):
                attr[i] = attr[i] + str(i)

        for line in raw:
            line = line.replace('\n','')[1:-1].split(',')
            n_line = [int(s) for s in line]
            obj_dict[n_line[0]] = Cls(**dict(zip(attr, n_line)))
    return obj_dict

def map_construct(roads, crosses):
    """
    connect the map
    :param roads: ROAD_DICT
    :param crosses: CROSS_DICT
    :return: None
    """
    for road_id in roads:
        # 从from指向to的路
        road = roads[road_id]
        crosses[road.from_v].point_to[road.to_v] = road
        crosses[road.to_v].point_from[road.from_v] = road
        if road.is_duplex:
            #从to指向from的路
            crosses[road.to_v].point_to[road.from_v] = road
            crosses[road.from_v].point_from[road.to_v] = road
    return

# *** test *** #
# from trafficmap import Car
# from trafficmap import Road
# from trafficmap import Cross
# cars = dict_generate(Car, '../1-map-training-1/car.txt')
# roads = dict_generate(Road, '../1-map-training-1/road.txt')
# crosses = dict_generate(Cross, '../1-map-training-1/cross.txt')
#
# map_construct(roads,crosses)
# print()