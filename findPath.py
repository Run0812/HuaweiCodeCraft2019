
""""该函数的目的是为了找出distTO（）中最小的数的下标（即下一个放松的顶点）"""
def findMin(distTo, alreadyRelax):
    minNum = float("inf")
    ret = -1
    for i in (distTo.keys()):
        if i in alreadyRelax:
            continue
        else:
            if distTo[i] < minNum:
                minNum = distTo[i]
                ret = i
    return ret

def Initialization(CROSS_DICT):
    """distTo用来存储与各个节点的距离,初始值为正无穷大。path用来到达各个节点的路径"""
    distTo = {}
    path = {}
    total_vertices = 0
    for key in CROSS_DICT.keys():
        distTo[key] = float("inf")
        path[key] = []
        total_vertices += 1
    return distTo, path, total_vertices


def ShortestPath(car, CROSS_DICT):
    hyperP = 1
    distTo, path, total_vertices = Initialization(CROSS_DICT)
    start, end = car.from_v, car.to_v
    """起点到起点的距离为0，路径为起点"""
    distTo[start] = 0
    path[start] = [start]

    """优先队列，每次都放松第一个节点"""
    alreadyRelax = [start]
    relaxP = start
    while len(alreadyRelax) < total_vertices:
        """接下来遍历放松节点的邻接点，如果起点与放松节点的距离加上放松节点与邻接节点的距离之和小于起点和该邻接
        节点当前的距离，那么就得改变该邻接节点的距离以及路径，路径为起点到现在放松节点路径加上邻接节点"""
        crosses = CROSS_DICT[relaxP].point_to  #此处是一个字典
        for point_to_cross_id in crosses.keys():
            adjacentP = point_to_cross_id                 #相连的另一个节点
            connect_road = crosses[point_to_cross_id]
            speed_comp = (min(car.speed, connect_road.speed)/max(car.speed, connect_road.speed)) ** hyperP
            weight = connect_road.weight[point_to_cross_id] / (car.speed  * speed_comp)
            if distTo[adjacentP] > distTo[relaxP] + weight:
                distTo[adjacentP] = distTo[relaxP] + weight
                path[adjacentP] = path[relaxP] +[adjacentP]

        relaxP = findMin(distTo, alreadyRelax)

        """如果已经找到最后的终点，就不要在计算了"""
        if relaxP == end:
            ret = []
            prevCross = path[relaxP][0]
            for currCross in path[relaxP][1:]:
                ret.append(CROSS_DICT[prevCross].point_to[currCross].id)
                prevCross = currCross
            return ret

        alreadyRelax.append(relaxP)