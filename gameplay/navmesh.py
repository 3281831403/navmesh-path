"""导航网格寻路：启发式、代价与动态障碍。

实现要点（对应 README 中的 10 个问题）：

1. 启发式与真实代价一致：``manhattan`` 按四方向单步代价 1 累加，
   与网格上的实际移动代价口径相同，避免启发式高估导致拐角卡死。
2. 对角线代价按 √2 计算：``diagonal_cost`` 区分对角步与直线步，
   不再把对角线按直线长度 1 处理。
3. 动态障碍使缓存失效 / 9. 缓存键包含版本：``cache_key`` 把地图
   版本编入键中，障碍变化即换键，旧路径不会被错误命中。
4. 路径按视线平滑：``line_blocked`` 做视线检测，``smooth_weight``
   给出端点更重的平滑权重，拐角可沿视线拉直。
5. 人群分离力按半径叠加：``separation_force`` 只计入半径内邻居，
   并按距离归一化后再叠加，避免力随邻居数无界放大。
6. 分层网格坐标映射：``cell_to_world`` 统一按 cell_size 做线性映射，
   层间坐标不会错位。
7. 单步代价钳制：``clamp_cost`` 给单步代价封顶。
8. 过期异步结果丢弃：``stale_result`` 比较版本号，过期结果不采用。
10. 批量 agent 统一提交：``commit_agents`` 要求全部成功才整体提交。
"""

import math

#: 八方向移动中对角步的真实代价（√2）。
DIAGONAL_STEP_COST = math.sqrt(2)

#: 四方向直线步的代价。
STRAIGHT_STEP_COST = 1.0

#: 平滑时路径端点的权重。
ENDPOINT_WEIGHT = 1.0

#: 平滑时路径内部点的权重。
INTERIOR_WEIGHT = 0.5


def manhattan(start, goal):
    """四方向启发式距离。

    与四方向网格上每步代价为 1 的真实移动代价保持一致：
    横向与纵向格数之和，保证启发式既不高估也不低估。
    """
    sx, sy = start
    gx, gy = goal
    return abs(gx - sx) + abs(gy - sy)


def diagonal_cost(dx, dy):
    """八方向移动代价。

    取 ``min(dx, dy)`` 步对角移动，每步代价为 √2；剩余的
    ``|dx - dy|`` 步沿直线移动，每步代价为 1。对角线不再按
    直线代价计算，因此启发式与八方向真实代价一致。
    """
    dx = abs(dx)
    dy = abs(dy)
    diagonal_steps = min(dx, dy)
    straight_steps = abs(dx - dy)
    return diagonal_steps * DIAGONAL_STEP_COST + straight_steps * STRAIGHT_STEP_COST


def cache_key(start, goal, version):
    """路径缓存键包含起点、终点与地图版本。

    动态障碍变化时地图版本递增，版本编入键中使旧缓存自然失效，
    不会把障碍出现前算出的路径重新返回。
    """
    return f"{start}:{goal}:{version}"


def line_blocked(points, blocked):
    """视线上的点是否被障碍占据。

    用于路径平滑的视线检测：视线采样点中只要有任意一格落在
    ``blocked`` 障碍集合内，就认为该视线被阻断；全部畅通才可
    沿视线把拐角拉直。
    """
    return any(point in blocked for point in points)


def separation_force(pos, neighbors, radius):
    """人群分离力按半径叠加。

    只考虑距离不超过 ``radius`` 的邻居，半径外的邻居不产生斥力，
    因此贡献者数量有界。每个计入的邻居贡献一个沿
    "邻居 -> 自身" 方向的单位斥力向量（不再使用随距离趋零而
    发散的反距离权重），各向量直接叠加，近距离接触时力也不会爆掉。
    """
    px, py = pos
    force_x = 0.0
    force_y = 0.0
    for nx, ny in neighbors:
        dx = px - nx
        dy = py - ny
        distance = math.hypot(dx, dy)
        if distance > radius or distance == 0:
            continue
        force_x += dx / distance
        force_y += dy / distance
    return [force_x, force_y]


def clamp_cost(cost, max_cost):
    """单步代价钳制到上限。

    代价超过 ``max_cost`` 时截断为上限，防止异常高的单步代价
    污染整条路径的代价累计。
    """
    return min(cost, max_cost)


def stale_result(result_version, current_version):
    """异步结果版本过期则丢弃。

    异步寻路回写时，若结果所基于的地图版本早于当前版本（期间
    动态障碍已变化），判定为过期，调用方应丢弃该结果。
    """
    return result_version < current_version


def smooth_weight(index, count):
    """路径平滑时端点权重更高。

    路径首尾两个端点权重为 1.0 以锚定起止位置，内部点权重为
    0.5，允许拐角在视线平滑时向相邻路径靠拢、拉直。
    """
    if index <= 0 or index >= count - 1:
        return ENDPOINT_WEIGHT
    return INTERIOR_WEIGHT


def cell_to_world(cell, cell_size):
    """网格坐标转世界坐标。

    分层网格各层统一按 ``cell_size`` 做线性映射：
    ``world = cell * cell_size``，避免层间坐标缩放错位。
    """
    cx, cy = cell
    return [cx * cell_size, cy * cell_size]


def commit_agents(statuses):
    """批量 agent 全部成功才提交。

    任一 agent 的状态为失败即整体放弃提交，保证批量移动的
    原子性，不会出现只提交一半的情况。
    """
    return all(statuses)
