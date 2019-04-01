from findPath import ShortestPath
from dataread import dict_generate
from dataread import map_construct
import logging
class Car(object):

    def __init__(self, id, from_v, to_v, speed, planTime):
        # *** static parameters ***#
        self.id = id
        self.from_v = from_v
        self.to_v = to_v
        self.speed = speed
        self.plan_time = planTime
        # *** dynamic parameters ***#
        self.fact_time = planTime
        self.pass_path = []
        self.plan_path = []
        self.waiting = True  # 0 = wait 1 = finish
        self.arrive_time = None
        self.is_arrived = False
        self.is_out = False

    def get_next_road(self):
        return self.plan_path[0] if self.plan_path else None

    def get_cur_road(self):
        return self.pass_path[-1] if self.pass_path else None

    def get_heading_cross_id(self):
        cur = self.get_cur_road()
        next = self.get_next_road()
        if cur is None and next is None:
            logging.info("car {} Haven't Depart".format(self.id))
            # print("car {} Haven't Depart".format(self.id))
            return None
        elif next is None:
            return self.to_v
        elif cur is None:
            return self.from_v
        cur_road, next_road = ROAD_DICT[cur], ROAD_DICT[next]
        if cur_road.to_v in [next_road.to_v, next_road.from_v]:
            return cur_road.to_v
        else:
            return cur_road.from_v

    def get_direction(self):
        cur_cross = CROSS_DICT[self.get_heading_cross_id()]
        cross_roads = cur_cross.roads
        cur_road = self.get_cur_road()
        next_road = self.get_next_road()
        if cur_road is None or next_road is None:
            direction = 'd'
        else:
            cur_r_i = cross_roads.index(cur_road)
            next_r_i = cross_roads.index(next_road)
            d_i = (next_r_i - cur_r_i) % 4
            if d_i == 1:
                direction = 'l'
            elif d_i == 3:
                direction = 'r'
            else:
                direction = 'd'
        return direction

    def res_length(self, road_length, cur_pos, cur_road_speed, next_road_speed):
        cur_road_res_length = road_length - cur_pos -1
        res_length = min(self.speed, next_road_speed) - cur_road_res_length
        if res_length < 0:
            res_length = 0
        return res_length

    def move_to_next_road(self, schedule):
        is_moved = False
        # 是否抵达终点
        next_road_id = self.get_next_road()
        if next_road_id is None:
            is_moved = True
            self.move_to_end(schedule)
        else:
            # 有没有空位
            next_road = ROAD_DICT[next_road_id]
            cross_id = self.get_heading_cross_id()
            in_lane = next_road.get_priority_lane_in(cross_id)
            if in_lane is not None:
                # 有空位
                # 计算距离
                cur_road = ROAD_DICT[self.get_cur_road()]
                cur_pos = cur_road.get_priority_car_pos(cross_id)
                res_length = self.res_length(cur_road.length, cur_pos, cur_road.speed, next_road.speed)
                if res_length == 0:
                    # 下一路可行距离为0则不过路口
                    cur_block = cur_road.get_priority_block_out(cross_id)
                    cur_block['pos'] = cur_road.length - 1
                    self.waiting = False
                    is_moved = True
                    return is_moved
                # 是否阻挡
                if in_lane:
                    pre_block = in_lane[-1]
                    if res_length >= pre_block['pos']:
                        # 阻挡
                        if pre_block['car'].waiting:
                            return is_moved
                        else:
                            res_length = pre_block['pos']
                # 清理当前道路
                cur_road.provide_car(cross_id)
                # 加入下一道路
                next_road.receive_car(self, res_length - 1)
                # 修改pass_path plan_path
                self.pass_path.append(self.plan_path.pop(0))
                # 修改waiting
                self.waiting = False
                is_moved = True
            else:
                # 没空位
                for lane in next_road.choose_channel(cross_id,'input'):
                    # 检测该路优先是否完毕
                    if lane[-1]['car'].waiting:
                        break
                else:
                    self.waiting = False
                    is_moved =  True
        return is_moved

    def move_to_end(self, schedule):
        # 停车入库
        # 清理当前路
        cross_id = self.to_v
        cur_road_id = self.get_cur_road()
        cur_road = ROAD_DICT[cur_road_id]
        cur_road.provide_car(cross_id)
        # 记时间
        self.arrive_time = TIME
        # 改状态
        self.waiting = False
        self.is_arrived = True
        # 路上车辆-1
        schedule.cars_on_road -= 1 # 调度器属性
        schedule.cars_arrived += 1
        # 目的地前往计数
        CROSS_DICT[self.to_v].car_heading_to -= 1
        return

    def onto_road(self, schedule):
        """
        让车上路
        :param schedule:调度器实例
        :return: -1 -> 提前发车
                 -2 -> 没有空位
                  0 -> 正常上路
        """
        global TIME
        # 校验TIME
        if TIME < self.plan_time:
            logging.info('Car {} starts earlier than plan time'.format(self.id))
            # print('Car {} starts earlier than plan time'.format(self.id))
            return -1
        else:
            self.fact_time = TIME
        # 获得优先车道
        next_road = ROAD_DICT[self.get_next_road()]
        priority_lane = next_road.get_priority_lane_in(self.from_v)
        if priority_lane is not None:
            # 有空位
            speed = min(self.speed, next_road.speed)
            pre_pos =  priority_lane[-1]['pos'] if priority_lane else next_road.length - 1 # 预防优先车道为空
            if speed >= pre_pos:
                pos = pre_pos - 1
            else:
                pos = speed
            next_road.receive_car(self, pos)
            self.waiting = False
            self.is_out = True
            self.pass_path.append(self.plan_path.pop(0))
            schedule.cars_on_road += 1
            # 目的地前往计数
            CROSS_DICT[self.to_v].car_heading_to += 1
            return 0
        else:
            # 没空位
            logging.info('Car {} cannot get on the road {} NO EMPTY'.format(self.id, next_road.id))
            # print('Car {} cannot get on the road {} NO EMPTY'.format(self.id, next_road.id))
            return -2

class Cross(object):
    """
    Cross
    - id
    - other vertex which this one points to
    """
    def __init__(self, id, roadId1, roadId2, roadId3, roadId4):
        # *** static parameters ***#
        self.id = id
        self.roads = [roadId1, roadId2, roadId3, roadId4]
        self.point_to = {}
        self.point_from = {}
        # *** dynamic parameters ***#
        # self.is_updated = False
        self.car_heading_to = 0

    def is_scheduled(self):
        all_priority_car = self.get_all_priority_car()
        for car in all_priority_car.values():
            if car is None:
                # 如果路口无车 或 断头路 将会返回None
                continue
            if car.waiting == True:
                # 仍然有车等待调度
                return False
        return True

    def get_all_priority_lane(self):
        road_lane = {}
        for road in self.point_from.values():
            lane = road.get_priority_lane_out(self.id)
            if lane is not None:
                road_lane[road.id] = lane
        return road_lane

    def get_all_priority_car(self):
        road_car = {}
        for road in self.point_from.values():
            car = road.get_priority_car(self.id)
            if car is not None:
                road_car[road.id] = car
        return road_car

    def is_conflict(self, road):
        cur_car = road.get_priority_car(self.id) # 判断车辆
        road_car = self.get_all_priority_car() # 当前路口各路的第一优先车
        for road_id in road_car:
            if road_id != road.id:
                other_car = road_car[road_id]
                a = cur_car.get_direction()
                b = other_car.get_direction()
                if cur_car.get_next_road() == other_car.get_next_road() and cur_car.get_direction() > other_car.get_direction():
                    # 'd' < 'l' < 'r'
                    return True
        return False


class Road(object):
    """
    map edge
    - id... ,etc attrs
    """

    def __init__(self, id, channel, from_v, isDuplex, to_v, length, speed):
        # *** static parameters ***#
        self.id = id
        self.channel_limit = channel
        self.from_v = from_v
        self.is_duplex = isDuplex
        self.to_v = to_v
        self.length = length
        self.speed = speed
        # *** dynamic parameters ***#
        # channel = [lane1,lane2, ...]
        self.forward_channel = [[] for _ in range(channel)] # [{'pos':i,'car':Car}]
        self.weight = {to_v: length}
        if isDuplex:
            self.backward_channel = [[]for _ in range(channel)] # [{'pos':i:'car':Car}]
            self.weight[from_v] = length
        else:
            self.backward_channel = []

    def choose_channel(self, cross_id, condition):
        if cross_id == self.to_v and condition == 'output':
            return self.forward_channel
        elif cross_id == self.to_v and condition == 'input':
            return self.backward_channel
        elif cross_id == self.from_v and condition == 'output':
            return self.backward_channel
        elif cross_id == self.from_v and condition == 'input':
            return self.forward_channel
        else:
            logging.info("Road.choose_channel(cross_id, condition) with wrong args")
            # print("Road.choose_channel(cross_id, condition) with wrong args")

    def get_equ_len(self, to_v):
        """
        L* = sum(res_length * road speed / current speed) / car_number
        :param to_v: to cross id
        :return: float
        """
        channels = self.choose_channel(to_v, 'output')
        L = self.length
        car_number = sum(map(len, channels)) + 1
        for lane in channels:
            front_car_speed = self.speed
            for block in lane:
                car, pos = block['car'], block['pos']
                cur_car_speed = min(car.speed, front_car_speed)
                L += (self.length - pos - 1) * self.speed / cur_car_speed
                front_car_speed = cur_car_speed
        return L / car_number

    def get_priority_lane_in(self, cross_id):
        """
        get the lane that next car drives in
        if no channel empty return None
        :return: lane = {pos:Car} or None
        """
        channels = self.choose_channel(cross_id, 'input')
        priority_lane = None
        for lane in channels:
            # lane = [{pos:Car}]
            if not lane or lane[-1]['pos'] != 0:
                priority_lane = lane
                break
        return priority_lane


    def get_priority_lane_out(self, cross_id):
        """
        得到当前优先级第一的车道
        None = 无车优先
        :return: lane or None
        """
        channels = self.choose_channel(cross_id, 'output')
        first_order_pos = -1
        priority_lane = None
        for lane in channels:
            if lane and lane[0]['pos'] > first_order_pos and lane[0]['car'].waiting:
                first_order_pos = lane[0]['pos']
                priority_lane = lane
        return priority_lane

    def get_priority_block_out(self, cross_id):
        lane = self.get_priority_lane_out(cross_id)
        return lane[0] if lane is not None else None

    def get_priority_car(self, cross_id):
        priority_block = self.get_priority_block_out(cross_id)
        return priority_block['car'] if priority_block is not None else None

    def get_priority_car_pos(self, cross_id):
        priority_block = self.get_priority_block_out(cross_id)
        return priority_block['pos'] if priority_block is not None else None

    def provide_car(self, cross_id): # todo:可重构
        priority_lane = self.get_priority_lane_out(cross_id)
        if priority_lane:
            block = priority_lane.pop(0)
            self.weight[cross_id] = self.get_equ_len(cross_id)
        else:
            block = None
        return block

    # todo: 可以添加一个方法判断是否阻挡waiting

    def receive_car(self, car, res_length): # todo:可重构为接受provide_car的输出
        cross_id = car.get_heading_cross_id()
        lane = self.get_priority_lane_in(cross_id)
        if lane is not None:
            lane.append({'pos':res_length, 'car':car})
            # 更新权值
            self.weight[cross_id] = self.get_equ_len(cross_id)
            return 1
        else:
            # 没有位置进入
            return None


    def lane_schedule(self, lane):
        """
        对某个车道按顺序标记一轮
        :return: None
        """
        if not lane:
            return
        for block_order in range(len(lane)):
            pos, car = lane[block_order]['pos'], lane[block_order]['car']
            if not car.waiting:
                continue
            speed = min(car.speed, self.speed)
            next_pos = pos + speed # 最远位置
            pre_block = lane[block_order - 1]
            pre_pos, pre_car = pre_block['pos'], pre_block['car']
            if block_order - 1 >= 0 and next_pos >= pre_pos:
                # 阻碍
                if pre_car.waiting:
                    # 前车等待
                    car.waiting = True
                else:
                    # 前车终止
                    lane[block_order]['pos'] = pre_pos - 1
                    car.waiting = False
            else:
                # 未阻碍
                if next_pos >= self.length:
                    # 出路口
                    car.waiting = True
                else:
                    # 未出路口
                    lane[block_order]['pos'] = next_pos
                    car.waiting = False
        return



class Schedule(object):

    def __init__(self):
        self.dead = False
        self.dead_cross = None
        self.cars_on_road = 0
        self.cars_arrived = 0
        self.all_cars = None


    def stage_1(self): # todo:test
        for road in ROAD_DICT.values():
            for lane in road.forward_channel:
                road.lane_schedule(lane)
            for lane in road.backward_channel:
                road.lane_schedule(lane)
        return

    def stage_2(self, this_round_cross_id): # todo:test
        next_round_cross_id = []
        for cross_id in this_round_cross_id:
            cross = CROSS_DICT[cross_id]
            import operator
            for road in sorted(cross.point_from.values(), key=operator.attrgetter('id')):
                # 道路Id升序
                while road.get_priority_car(cross_id): # 有优先车返回Car 无优先车返回None 有车但终止=无优先车
                    # 当有车在该路上等待时
                    cur_car = road.get_priority_car(cross_id)
                    if cross.is_conflict(road):
                        # 判断行车冲突
                        break
                    # 尝试让车过路口
                    this_channel = road.get_priority_lane_out(cross_id)
                    is_moved = cur_car.move_to_next_road(self)
                    if is_moved:
                        # 如果车被设置成完成，则该车道的后方进行一轮调度
                        # print(cur_car.id,"MOVED")
                        logging.info("%d MOVED" % (cur_car.id))
                        cross.is_updated = True
                        self.dead = False # 如果有路的车在此轮中被设置完成，则说明未卡死 todo:如何得知卡死在某路口
                        road.lane_schedule(this_channel)
                    else:
                        # 不能移动
                        break
            if not cross.is_scheduled():
                next_round_cross_id.append(cross_id)
        return next_round_cross_id

    def put_car_on_road(self, cars, path): # todo:test
        # 上路器
        # 循环列表上路
        # ID升序调度
        for car_id in sorted(cars):
            # 调用康哥findpath找到路径 设置car的plan_path
            cur_car = CAR_DICT[car_id]
            cur_car.plan_path = path(cur_car)
            # 调用car.on_road
            res = cur_car.onto_road(self)
            if res == -2:
                # 上路失败
                pass
            elif res == -1:
                pass
        return

    def set_cars_on_road_waiting(self): # todo:text
        for road_id in ROAD_DICT:
            road = ROAD_DICT[road_id]
            for lane in road.forward_channel:
                for block in lane:
                    block['car'].waiting = True
            for lane in road.backward_channel:
                for block in lane:
                    block['car'].waiting = True
        return


    def step(self): # todo:test
        # 将路上的车设置为waiting=True
        self.set_cars_on_road_waiting()
        # stage 1:
        self.stage_1()
        # stage 2:
        unfinished_cross_id = sorted(list(CROSS_DICT.keys())) # 路口Id升序
        while unfinished_cross_id:
            # 调度至所有路口都完成
            self.dead = True
            unfinished_cross_id = self.stage_2(unfinished_cross_id)
            if self.dead and unfinished_cross_id:
                print("DEAD!!! @ %d" % (TIME))
                logging.info("DEAD!!! @ %d" % (TIME))
                # todo:启动卡死回退
        return

    def simulator(self, answer_path):
        global TIME
        # 读文件
        ANSWER = {}
        with open(answer_path, 'r') as ans:
            ans.readline()
            for line in ans:
                car_id, car_fact_time, *path = line[1:-2].split(',')
                ANSWER[car_fact_time] = {car_id: path}
        while self.cars_arrived:
            TIME += 1
            self.step()
            # 获得上路车列表 todo:
            cars_waiting_onto_road = ANSWER[TIME] # todo:有问题
            self.put_car_on_road(cars_waiting_onto_road.keys(), lambda k:cars_waiting_onto_road[k.id])
        return

    def calculator(self, motor_cade): # todo:test
        global TIME
        while self.all_cars != self.cars_arrived:
            TIME += 1
            logging.info("------------TIME:%d----------" % (TIME))
            # 调度一步
            self.step()
            # 获得上路车列表
            this_round_waiting_cars = motor_cade.make_cade()
            def path(car):
                return ShortestPath(car, CROSS_DICT)
            self.put_car_on_road(this_round_waiting_cars, path)
        return

    def output(self, answer_path):
        with open(answer_path, 'w', encoding = 'UTF-8') as ans:
            ans.write('#(carId,StartTime,RoadId...)\n')
            for car_id in CAR_DICT:
                car = CAR_DICT[car_id]
                l = [car.id, car.fact_time]
                l.extend(car.pass_path)
                s = '(' + ','.join(map(str,l)) + ')\n'
                ans.write(s)
        return

    # init
    def read_file(self, car_path, road_path, cross_path):
        global CAR_DICT, ROAD_DICT, CROSS_DICT, TIME
        CAR_DICT = dict_generate(Car, car_path)
        ROAD_DICT = dict_generate(Road, road_path)
        CROSS_DICT = dict_generate(Cross, cross_path)
        TIME = 0
        map_construct(ROAD_DICT, CROSS_DICT)
        self.all_cars = len(CAR_DICT)
        return

class Motorcade(object):

    def __init__(self, limit = 500):
        self.limit_num = limit  # 车辆限制数目 todo:设置方法能够自动根据地图大小调整
        self.current_id = None   # 记录未出发的车辆的第一个车
        self.current_last_id = None  # 记录当前时间，最后一辆能够出发的车的ID
        self.car_list_plan_time = sorted(CAR_DICT.keys(), key=lambda d: CAR_DICT[d].plan_time)
        #self.car_pool=car_list
        # self.current_time = current   # 当前时间

    def get_last_id(self):
        last_index = 0
        for i in range(len( self.car_list_plan_time)):
            if CAR_DICT[ self.car_list_plan_time[i]].plan_time <= TIME and i > last_index and not CAR_DICT[self.car_list_plan_time[i]].is_out :
                last_index = i
                self.current_last_id =  self.car_list_plan_time[i].id

    def is_aim_place_crowded(self, car):
        # 降低未来卡死可能性
        # 检测当前车目的地
        check_cross =  CROSS_DICT[car.to_v]
        if check_cross.car_heading_to >= 20:
            # 如果目的地拥挤，则不安排上路
            return True
        return False


    def make_cade(self):
        global TIME
        car_candidate = []
        for car_id in  self.car_list_plan_time:
            if len(car_candidate) < self.limit_num:
                cur_car = CAR_DICT[car_id]
                if cur_car.plan_time <= TIME and not cur_car.is_out and not self.is_aim_place_crowded(cur_car):
                    car_candidate.append(car_id)  # 增加准备上车的ID
                    # CAR_DICT[car_id].is_out = True  # 将车辆是否出发的标志位设置为已出发
            else:
                break
        return car_candidate

    # def receive(self,back_car):
    #     for back_car_id in back_car:
    #         CAR_DICT[back_car_id].is_out = False



logging.basicConfig(level=logging.DEBUG,
                    filename='../logs/CodeCraft-2019.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')