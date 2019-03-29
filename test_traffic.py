from trafficmap import *
import pytest


# CAR_DICT = dict_generate(Car, '../test_config/car.txt')
# ROAD_DICT = dict_generate(Road, '../test_config/road.txt')
# CROSS_DICT = dict_generate(Cross, '../test_config/cross.txt')
# TIME = 0
# map_construct(ROAD_DICT, CROSS_DICT)


cross1 = CROSS_DICT[1]
cross2 = CROSS_DICT[2]
cross3 = CROSS_DICT[3]
road1 = ROAD_DICT[1]
road2 = ROAD_DICT[2]
road3 = ROAD_DICT[3]
road4 = ROAD_DICT[4]
road5 = ROAD_DICT[5]

@pytest.fixture()
def test_car():
    car = Car(0, 0, 0, 4, 0) # (id,from,to,speed,planTime)
    return car

@pytest.fixture()
def init_schedule():
    schedule = Schedule()
    return schedule

@pytest.fixture()
def test_cross():
    cross = Cross(9,-1,-1,-1,-1)
    return cross

def road_clean(road):
    road.forward_channel = [[] for _ in range(road.channel_limit)]  # [{'pos':i,'car':Car}]
    road.backward_channel = [[] for _ in range(road.channel_limit)] if road.is_duplex else []  # [{'pos':i:'car':Car}]
    return


def block_car(on_road, channel, lane, pos, id = 0, from_v = 0, to_v = 0, speed = 4 , plan_time = 0):
    car = Car(id, from_v, to_v, speed, plan_time)
    block_channel = getattr(ROAD_DICT[on_road], channel + '_channel')
    block_channel[lane].append({'pos': pos,'car':car})
    return car

# *** CAR TEST *** #
def test_car_get_next_road(test_car):
    # 未上路
    assert test_car.get_next_road() == None
    # 准备上路
    test_car.plan_path = [1]
    assert test_car.get_next_road() == 1
    # 已经上路
    test_car.pass_path = [2]
    assert test_car.get_next_road() == 1
    # 到达终点
    test_car.plan_path = []
    assert test_car.get_next_road() == None

def test_car_get_cur_road(test_car):
    # 未上路
    assert test_car.get_cur_road() == None
    # 准备上路
    test_car.plan_path = [1]
    assert test_car.get_cur_road() == None
    # 已经上路
    test_car.pass_path = [2]
    assert test_car.get_cur_road() == 2
    # 到达终点
    test_car.plan_path = []
    assert test_car.get_cur_road() == 2

def test_car_get_heading_cross_id(test_car):
    # 未上路
    assert test_car.get_heading_cross_id() == None
    # 准备上路
    test_car.from_v = 2
    test_car.plan_path = [1]
    assert test_car.get_heading_cross_id() == 2
    # 已经上路
    test_car.pass_path = [2]
    assert test_car.get_heading_cross_id() == 1
    # 到达终点
    test_car.plan_path = []
    assert test_car.get_heading_cross_id() == test_car.to_v

def test_car_get_direction(test_car):
    test_car.pass_path = [4]
    # 左转
    test_car.plan_path = [2]
    assert test_car.get_direction() == 'l'
    # 直行
    test_car.plan_path = [3]
    assert test_car.get_direction() == 'd'
    # 右转
    test_car.plan_path = [5]
    assert test_car.get_direction() == 'r'
    # 停车
    test_car.plan_path = []
    test_car.to_v = 3
    assert test_car.get_direction() == 'd'

@pytest.mark.parametrize("car_speed, cur_road_speed, road_length, cur_pos, next_road_speed, res", [
    (5, 4, 8, 5, 4, 2),
    (5, 4, 7, 4, 5, 3),
    (5, 4, 10, 7, 3, 1),
    (5, 4, 5, 2, 1, 0),
    (5, 4, 7, 4, 2, 0),
    (5, 2, 7, 5, 5, 4),
    (5, 2, 6, 4, 3, 2),
])
def test_res_length(test_car, car_speed, cur_road_speed, road_length, cur_pos, next_road_speed, res):
    test_car.speed = car_speed
    assert test_car.res_length(road_length, cur_pos, cur_road_speed, next_road_speed) == res

def test_move_to_end(init_schedule, test_car):
    test_car.speed = 8
    test_car.to_v = 3
    test_car.from_v = 4
    test_car.pass_path = [4]
    init_schedule.cars_on_road = 1
    road4.backward_channel[0].append({'pos':19,'car':test_car})
    test_car.move_to_end(init_schedule)
    assert road4.backward_channel == [[]]
    assert test_car.arrive_time == TIME
    assert test_car.waiting == False
    assert  init_schedule.cars_on_road == 0
    road_clean(road4)

def test_onto_road(test_car, init_schedule):
    test_car.plan_time = 1
    test_car.from_v = 4
    test_car.to_v = 2
    test_car.speed = 10
    test_car.plan_path = [4, 2, 1]
    # 未到发车时间
    assert test_car.onto_road(init_schedule) == -1
    assert  init_schedule.cars_on_road == 0
    # 有空位无阻挡
    test_car.plan_time = 0
    assert test_car.onto_road(init_schedule) == 0
    assert ROAD_DICT[4].backward_channel[0][-1]['pos'] == 6
    assert ROAD_DICT[4].backward_channel[0][-1]['car'] == test_car
    assert init_schedule.cars_on_road == 1
    # 有空位有阻挡
    block_car(4, 'backward', 0, 3)
    test_car.plan_path = [4, 2, 1]
    test_car.pass_path = []
    test_car.speed = 4
    assert test_car.onto_road(init_schedule) == 0
    assert ROAD_DICT[4].backward_channel[0][-1]['pos'] == 2
    assert ROAD_DICT[4].backward_channel[0][-1]['car'] == test_car
    assert init_schedule.cars_on_road == 2
    # 没空位
    block_car(4, 'backward', 0, 0)
    test_car.plan_path = [4, 2, 1]
    test_car.pass_path= []
    test_car.speed = 4
    assert test_car.onto_road(init_schedule) == -2
    assert init_schedule.cars_on_road == 2
    road_clean(road4)

def test_move_to_next_road(init_schedule):
    # 空路
    car1 = block_car(4,'backward',0,18)
    car1.pass_path = [4]
    car1.plan_path = [3]
    car1.speed = 10
    assert car1.move_to_next_road(init_schedule) == True
    assert road3.forward_channel[0][0] == {'pos':4,'car':car1}
    # 无阻挡路
    car2 = block_car(4, 'backward', 0, 18)
    car2.pass_path = [4]
    car2.plan_path = [3]
    car2.speed = 4
    assert car2.move_to_next_road(init_schedule) == True
    assert road3.forward_channel[0][1] == {'pos':2,'car':car2}
    # 阻挡不等待
    car3= block_car(4, 'backward', 0, 19)
    car3.pass_path = [4]
    car3.plan_path = [3]
    car3.speed = 6
    assert car3.move_to_next_road(init_schedule) == True
    assert road3.forward_channel[0][2] == {'pos':1,'car':car3}
    # 阻挡等待
    car3.waiting = True
    car4 = block_car(4, 'backward', 0, 14)
    car4.pass_path = [4]
    car4.plan_path = [3]
    car4.speed = 8
    assert car4.move_to_next_road(init_schedule) == False
    assert car4.waiting == True
    # 下一条路可行距离为0
    road_clean(road3)
    road4.backward_channel[0][0]['pos'] = 12 # 13-14-15-16-17-18-19:7 res_length = 0
    assert car4.move_to_next_road(init_schedule) == True
    assert car4.waiting == False
    assert road4.backward_channel[0][0] == {'pos': 19, 'car': car4}
    road_clean(road3)
    road_clean(road4)

# *** ROAD TEST *** #
def test_road_choose_channel():
    assert road2.choose_channel(3, 'input') is road2.backward_channel
    assert road2.choose_channel(3, 'output') is road2.forward_channel
    assert road2.choose_channel(1, 'input') is road2.forward_channel
    assert road2.choose_channel(1, 'output') is road2.backward_channel

def test_road_get_priority_lane_in():
    # 车道全空
    assert road2.get_priority_lane_in(3) is road2.backward_channel[0]
    # 一车道有车但有空位
    block_car(2,'backward',0,1)
    assert road2.get_priority_lane_in(3) is road2.backward_channel[0]
    # 一车道有车没空位
    block_car(2,'backward',0,0)
    assert road2.get_priority_lane_in(3) is road2.backward_channel[1]
    # 没空位
    block_car(2,'backward',1,0)
    assert road2.get_priority_lane_in(3) is None
    road_clean(road2)

def test_road_get_priority_lane_out():
    # 全空
    assert road2.get_priority_lane_out(3) is None
    # 1车道有车
    car1 = block_car(2, 'forward', 0, 15)
    assert road2.get_priority_lane_out(3) is road2.forward_channel[0]
    # 1车道有车但是终止
    car1.waiting = False
    assert road2.get_priority_lane_out(3) is None
    # 1车道没车/终止 2车道有车
    block_car(2, 'forward', 1, 16)
    assert road2.get_priority_lane_out(3) is road2.forward_channel[1]
    # 1车道有车 比 2车道后
    car1.waiting = True
    assert road2.get_priority_lane_out(3) is road2.forward_channel[1]
    # 1车道有车 比 2车道前
    road2.forward_channel[0] = []
    block_car(2, 'forward', 0, 17)
    assert road2.get_priority_lane_out(3) is road2.forward_channel[0]
    # 1车2车道都有车 并排
    block_car(2, 'forward', 1, 17)
    assert road2.get_priority_lane_out(3) is road2.forward_channel[0]
    road_clean(road2)

def test_road_get_priority_block_out():
    # 空
    assert road2.get_priority_block_out(3) is None
    # 1车道
    car1 = block_car(2, 'forward', 0, 15)
    assert road2.get_priority_block_out(3) is road2.forward_channel[0][0]
    # 2车道
    car2 = block_car(2, 'forward', 1, 16)
    assert road2.get_priority_block_out(3) is road2.forward_channel[1][0]
    road_clean(road2)

def test_road_get_priority_car():
    # 空
    assert road2.get_priority_car(3) is None
    # 1车道
    car1 = block_car(2, 'forward', 0, 15)
    assert road2.get_priority_car(3) is car1
    # 2车道
    car2 = block_car(2, 'forward', 1, 16)
    assert road2.get_priority_car(3) is car2
    road_clean(road2)

def test_road_get_priority_car_pos():
    # 空
    assert road2.get_priority_car_pos(3) is None
    # 1车道
    car1 = block_car(2, 'forward', 0, 15)
    assert road2.get_priority_car_pos(3) == 15
    # 2车道
    car2 = block_car(2, 'forward', 1, 16)
    assert road2.get_priority_car_pos(3) == 16
    road_clean(road2)

def test_road_provide_car():
    car1 = Car(11, 0, 0, 4, 0)
    car2 = Car(12, 0, 0, 4, 0)
    car3 = Car(13, 0, 0, 4, 0)
    car4 = Car(14, 0, 0, 4, 0)
    car5 = Car(15, 0, 0, 4, 0)
    car6 = Car(16, 0, 0, 4, 0)
    road2.forward_channel = [[{'pos':15,'car':car1},{'pos':14,'car':car3},{'pos':13,'car':car4}],
                             [{'pos':15,'car':car2},{'pos':13,'car':car5},{'pos':12,'car':car6}]]
    assert road2.provide_car(3) == {'pos':15,'car':car1}
    assert road2.forward_channel[0] ==[{'pos':14,'car':car3},{'pos':13,'car':car4}]
    assert road2.provide_car(3) == {'pos':15,'car':car2}
    assert road2.provide_car(3) == {'pos':14,'car':car3}
    assert road2.provide_car(3) == {'pos':13,'car':car4}
    assert road2.provide_car(3) == {'pos':13,'car':car5}
    assert road2.provide_car(3) == {'pos':12,'car':car6}
    assert road2.provide_car(3) is None
    road_clean(road2)

def test_road_receive_car(test_car):
    test_car.from_v =2
    test_car.to_v = 3
    test_car.pass_path = [1]
    test_car.plan_path = [2]
    road2.receive_car(test_car, 3)
    assert road2.forward_channel[0][0] ==  {'pos':3, 'car':test_car}
    road_clean(road2)

def test_road_lane_schedule():
    car1 = block_car(4,'backward',0,17)
    car1.speed = 6
    car2 = block_car(4,'backward',0,15)
    car2.speed = 6
    car3 = block_car(4, 'backward', 0, 10)
    car3.speed = 2
    car4 = block_car(4, 'backward', 0, 9)
    car4.speed = 4
    road4.lane_schedule(road4.backward_channel[0])
    assert car1.waiting == True
    assert car2.waiting == True
    assert car3.waiting == False
    assert car4.waiting == False
    assert road4.backward_channel[0] == [{'pos':17,'car':car1},{'pos':15,'car':car2},{'pos':12,'car':car3},{'pos':11,'car':car4}]
    road_clean(road4)

def test_road_get_equ_len():
    road4.get_equ_len(3)
    pass



# *** CROSS TEST *** #
def test_cross_is_scheduled():
    car1 = block_car(2,'forward', 0, 15)
    car3 = block_car(4, 'backward', 0, 15)
    car4 = block_car(5, 'backward', 0, 15)
    car1.waiting = False
    car3.waiting = False
    car4.waiting = False
    assert cross3.is_scheduled() == True
    car3.waiting = True
    assert cross3.is_scheduled() == False
    road_clean(road2)
    road_clean(road4)
    road_clean(road5)

def test_cross_get_all_priority_lane():
    car1 = block_car(2, 'forward', 0, 15)
    car3 = block_car(4, 'backward', 0, 15)
    car4 = block_car(5, 'backward', 0, 15)
    car1.waiting = False
    car3.waiting = True
    car4.waiting = False
    assert cross3.get_all_priority_lane() ==  {4:road4.backward_channel[0]}
    car1.waiting = True
    car4.waiting = True
    assert cross3.get_all_priority_lane() ==  {2:road2.forward_channel[0], 4:road4.backward_channel[0], 5:road5.backward_channel[0]}
    road_clean(road2)
    road_clean(road4)
    road_clean(road5)

def test_cross_get_all_priority_car():
    car1 = block_car(2, 'forward', 0, 15)
    car3 = block_car(4, 'backward', 0, 15)
    car4 = block_car(5, 'backward', 0, 15)
    car1.waiting = False
    car3.waiting = True
    car4.waiting = False
    assert cross3.get_all_priority_car() ==  {4:road4.backward_channel[0][0]['car']}
    car1.waiting = True
    car4.waiting = True
    assert cross3.get_all_priority_car() ==  {2:road2.forward_channel[0][0]['car'], 4:road4.backward_channel[0][0]['car'], 5:road5.backward_channel[0][0]['car']}
    road_clean(road2)
    road_clean(road4)
    road_clean(road5)

def test_cross_is_conflict():
    car1 = block_car(4, 'backward',0, 17)
    car1.pass_path = [4]
    car1.plan_path = [3]
    # 当前直行 无他车
    assert cross3.is_conflict(road4) == False
    # 当前直行 他车左转
    car2 = block_car(2, 'forward',0, 17)
    car2.pass_path = [2]
    car2.plan_path = [3]
    assert cross3.is_conflict(road4) == False
    # 当前直行 他车右转
    car3 = block_car(5, 'backward', 0, 17)
    car3.pass_path = [5]
    car3.plan_path = [3]
    assert cross3.is_conflict(road4) == False
    # 当前左转 他车直行
    assert cross3.is_conflict(road2) == True
    # 当前左转 他车右转
    car1.waiting = False
    assert cross3.is_conflict(road2) == False
    # 当前右转 他车直行
    car1.waiting = True
    assert cross3.is_conflict(road5) == True
    # 当前右转 他车左转
    car1.waiting = False
    assert cross3.is_conflict(road5) == True
    # 当前右转 他车左转 但不进入同一路
    car1.plan_path = [2]
    car3.waiting = False
    assert cross3.is_conflict(road2) == False
    road_clean(road2)
    road_clean(road4)
    road_clean(road5)

# *** SCHEDULE TEST *** #
def test_schedule_stage_1():
    pass

def test_schedule_stage_2(init_schedule):
    cars_id = [[100, 200, 300, 101, 201, 301],
               [400, 500, 600, 401, 501, 601],
               [700, 800, 900, 701, 801, 901]]
    def lane():
        i = -1
        while True:
            i += 1
            if i > 2:
                i = 0
            yield i

    def pos():
        i = 0
        car = 0
        p = 19
        while True:
            if car == 6:
                car = 0
                i = 0
                p = 19
            i += 1
            car += 1
            yield p
            if i == 3:
                i = 0
                p -= 1


    l = lane()
    p = pos()
    road6 = ROAD_DICT[6]
    road7 = ROAD_DICT[7]
    road8 = ROAD_DICT[8]
    road9 = ROAD_DICT[9]
    for id in cars_id[0]:
        car = block_car(6, 'forward', next(l), next(p), id, 6, 8, 5)
        car.pass_path = [6]
        car.plan_path = [8]
    for id in cars_id[1]:
        car = block_car(7, 'forward', next(l), next(p), id, 7, 8, 5)
        car.pass_path = [7]
        car.plan_path = [8]
    for id in cars_id[2]:
        car = block_car(9, 'forward', next(l), next(p), id, 9, 8, 5)
        car.pass_path = [9]
        car.plan_path = [8]

    print(road6.forward_channel)
    print(road7.forward_channel)
    print(road9.forward_channel)
    init_schedule.stage_2([10])
    print(road6.forward_channel)
    print(road7.forward_channel)
    print(road9.forward_channel)
    pass

def test_schedule_step():
    # 试验判断死锁
    pass