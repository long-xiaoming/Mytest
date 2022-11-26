from collections import defaultdict
import networkx as nx
import time
from pathlib import Path


# 使边表示形式由小到大，如（3，2）改为（2，3）
def exchange(node1, node2):
    if node1 > node2:
        return node2, node1
    return node1, node2


def sum_add_weight(edge):
    sum_weight = 0
    conflict_edge_list = single_edge_conflict_list[edge]
    if not conflict_edge_list:
        return 0
    for _edge in conflict_edge_list:
        sum_weight += weighted_edges[_edge]
    if sum_weight == 0:
        return 0
    else:
        return weighted_edges[edge]/sum_weight


# 判断是否形成回路
def prohibited(edge_ij, G):
    # 求包含某个节点的连通分量的节点集合nx.node_connected_component(G,Vi)
    if nx.node_connected_component(G, edge_ij[0]) != nx.node_connected_component(G, edge_ij[1]):
        return False
    else:
        return True


# 计算边的计算权值
def calculate_weight_edge():
    r_edge_weight_list = []
    for edge in conflict_edge_vertex:
        r_edge_weight = weighted_edges[edge] + (sum_add_weight(edge) +
                                                len(single_edge_conflict_list[edge])/(conflict_pair_number/edges_row)*(len(single_edge_conflict_list[edge])**2))*(all_weight*2/(edges_row**2))
        r_edge_weight_list.append([edge, r_edge_weight])
    r_edge_weight_list.sort(key=lambda edge_: edge_[1])  # 排序
    return r_edge_weight_list


# 移除对应边的冲突边集合元素
def remove_conflict_edge(r_edges):
    for _edge in single_edge_conflict_list[r_edges]:
        single_edge_conflict_list[_edge].remove(r_edges)   # 未找到元素不报错


# 按左小右大调整边集
def sorted_edges(edges):
    set_list = set()
    for edge in edges:
        set_list.add((exchange(edge[0], edge[1])))
    return set_list


# 以下筛选切边，若移除该边会使得原始图不连通,循环至找不到割边
def first_select(graph, must_add_edges, must_remove_edges):
    now_edges = sorted_edges(nx.bridges(graph)) - must_add_edges  # 割边筛选
    while now_edges:
        # print("步骤一循环")
        for bridge_edge in now_edges:
            must_add_edges.add(bridge_edge)
            graph_edge_of_edges = single_edge_conflict_list[bridge_edge].copy()
            must_remove_edges.update(graph_edge_of_edges)
            graph.remove_edges_from(graph_edge_of_edges)
            for c_edge in graph_edge_of_edges:
                remove_conflict_edge(c_edge)    # 移除对应边冲突关系
        now_edges = sorted_edges(nx.bridges(graph)) - must_add_edges
    for select_del_edge in must_remove_edges:
        conflict_edge_vertex.discard(select_del_edge)    # 更新边集数据


# 以下筛选边的冲突边集，若移除某边的冲突边集原始图不连通，则移除该边
def second_select(graph, must_remove_edges):
    judge = False
    single_select_edge = None
    for verge_edge in conflict_edge_vertex:
        graph_select_edges = single_edge_conflict_list[verge_edge].copy()
        graph.remove_edges_from(graph_select_edges)
        if not nx.is_connected(graph):
            single_select_edge = verge_edge
            must_remove_edges.add(verge_edge)
            graph.remove_edge(verge_edge[0], verge_edge[1])
            remove_conflict_edge(verge_edge)
            graph.add_edges_from(graph_select_edges)
            judge = True
            break
        graph.add_edges_from(graph_select_edges)
    conflict_edge_vertex.discard(single_select_edge)
    return judge


# 对删除的边集进行处理
def del_edges_operator(del_edges):
    for del_edge in del_edges:
        conflict_edge_vertex.remove(del_edge)
        remove_conflict_edge(del_edge)


def algorithm_iterative():
    # 数据预处理
    must_remove_edges = set()  # 必须移除的边
    must_add_edges = set()  # 必须添加的边,割边
    graph = nx.Graph()  # 原始图
    graph.add_edges_from(conflict_edge_vertex)
    # 以下筛选
    first_select(graph, must_add_edges, must_remove_edges)
    while second_select(graph, must_remove_edges):
        first_select(graph, must_add_edges, must_remove_edges)
    for edge_add in must_add_edges:
        conflict_edge_vertex.remove(edge_add)
    # 算法开始
    start = time.perf_counter()  # 程序开始运行
    check_set = set()  # 检验集
    check_set.update(must_add_edges)  # 添加必须边集作为初始检验集
    G = nx.Graph()  # 检验集形成的无向图
    G.add_nodes_from([x for x in range(0, nodes_len)])
    G.add_edges_from(check_set)
    r_edge_weight_list = calculate_weight_edge()  # 存储边的计算权值
    while conflict_edge_vertex:
        del_edges = set()   # 该次循环删除的边集
        now_select_edge = None   # 尝试添加的边
        for select_edge in r_edge_weight_list:
        # isdisjoint()函数的功能：判断两个集合是否包含相同的元素，如果没有返回 True ， 否则就返回 False
            if not prohibited(select_edge[0], G):
                now_select_edge = select_edge[0]
                del_edges.add(select_edge[0])
                break
            else:
                del_edges.add(select_edge[0])
                graph.remove_edge(select_edge[0][0], select_edge[0][1])
        if not now_select_edge:
            break
        graph_now = graph.copy()  # 保存当前初始图
        check_set_now = check_set.copy()  # 保存当前初始检验集
        del_edges_now = del_edges.copy()    # 保存当前删除集合
        graph.remove_edges_from(single_edge_conflict_list[now_select_edge])
        check_set.add(now_select_edge)
        del_edges.update(single_edge_conflict_list[now_select_edge])
        # 添加割边
        all_edges = sorted_edges(nx.bridges(graph)) - check_set
        while all_edges:
            for cutting_edge in all_edges:
                graph.remove_edges_from(single_edge_conflict_list[cutting_edge])
                del_edges.update(single_edge_conflict_list[cutting_edge])
            if nx.is_connected(graph):
                check_set.update(all_edges)
                del_edges.update(all_edges)
            else:
                graph_now.remove_edge(now_select_edge[0], now_select_edge[1])
                graph = graph_now
                check_set = check_set_now
                del_edges = del_edges_now
                break
            all_edges = sorted_edges(nx.bridges(graph)) - check_set
        del_edges_operator(del_edges)   # 对删除的边集进行处理
        G.add_edges_from(check_set)
        if not nx.is_connected(graph):
            break
        r_edge_weight_list = calculate_weight_edge()
    solution_all_weight = 0
    if nx.is_connected(G):
        for pair_edge in check_set:
            solution_all_weight += weighted_edges[pair_edge]
        print(f"solution_all_weight:{solution_all_weight}")
    else:
        print("无解")
        solution_all_weight = "无解"
    end = time.perf_counter()  # 程序结束运行
    print('算法 Running time: %s Seconds' % (end - start))


if __name__ == "__main__":
    # 直接输入数据
    nodes_len = int(input())
    edges_row = int(input())
    conflict_pair_number = int(input())
    weighted_edges = {}     # 每条边的权重
    all_weight = 0
    for _ in range(edges_row):
        per = list(map(int, input().strip().split()))
        weighted_edges[(exchange(per[0], per[1]))] = per[2]
        all_weight += per[2]
    average_weight = all_weight/edges_row
    conflict_edge_match = []    # 冲突对边的集合
    single_edge_conflict_list = defaultdict(set)    # 每条边所对应的冲突边的集合
    for _ in range(conflict_pair_number):
        per = list(map(int, input().strip().split()))
        edge1 = (exchange(per[0], per[1]))
        edge2 = (exchange(per[2], per[3]))
        conflict_edge_match.append({edge1, edge2})
        single_edge_conflict_list[edge1].add(edge2)     # 不需要先创建一个空集合
        single_edge_conflict_list[edge2].add(edge1)
    conflict_edge_vertex = set()    # 存储全部的边
    for edge in weighted_edges.keys():
        conflict_edge_vertex.add(edge)
    algorithm_iterative()
    # 文件批处理
    '''p = Path("C:\\Users\\long\\Desktop\\CMST\\CMST\\SamurInstances")
    FileList = list(p.glob("**/*.txt"))
    for File in FileList:
        with open(File, 'r') as file:
            nodes_len = int(file.readline().strip())
            edges_row = int(file.readline().strip())
            conflict_pair_number = int(file.readline().strip())
            weighted_edges = {}  # 每条边的权重
            all_weight = 0  # 原始图总权重值
            for _ in range(edges_row):
                per = list(map(int, file.readline().strip().split()))
                weighted_edges[(exchange(per[0], per[1]))] = per[2]
                all_weight += per[2]
            conflict_edge_match = []  # 冲突对边的集合
            single_edge_conflict_list = defaultdict(set)  # 每条边所对应的冲突边的集合
            for _ in range(conflict_pair_number):
                per = list(map(int, file.readline().strip().split()))
                edge1 = (exchange(per[0], per[1]))
                edge2 = (exchange(per[2], per[3]))
                conflict_edge_match.append({edge1, edge2})
                single_edge_conflict_list[edge1].add(edge2)  # 不需要先创建一个空集合
                single_edge_conflict_list[edge2].add(edge1)
            conflict_edge_vertex = set()  # 存储全部的边
            for edge in weighted_edges.keys():
                conflict_edge_vertex.add(edge)
            algorithm_iterative()'''
