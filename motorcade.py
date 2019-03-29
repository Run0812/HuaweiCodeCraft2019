# from trafficmap import CAR_DICT, TIME
global CAR_DICT
class Motorcade(object):

    def __init__(self, limit = 500):
        self.limit_num = limit  # 车辆限制数目
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


    def aim_place_diff(self):
        pass

    def make_cade(self):
        global TIME
        car_candidate = []
        for car_id in  self.car_list_plan_time:
            if len(car_candidate) < self.limit_num :
                if CAR_DICT[car_id].plan_time <= TIME and not CAR_DICT[car_id].is_out:
                    car_candidate.append(car_id)  # 增加准备上车的ID
                    # CAR_DICT[car_id].is_out = True  # 将车辆是否出发的标志位设置为已出发
            else:
                break
        return car_candidate

    def receive(self,back_car):
        for back_car_id in back_car:
            CAR_DICT[back_car_id].is_out = False



