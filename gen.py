import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.text import Text
import matplotlib.patches as patches
import textwrap
import re
import os
import mpld3
from svgpan import *


# Note: You'll need to define svg_javascript() function
# Also make sure to import os module at the top of your file

def pretty_size(size, units=('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')):
    if size == 0:
        return "0B"
    
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.2f}{units[unit_index]}"

def gen_image1(chains_with_weights):
    # # 输入的链表和权值
    G = nx.DiGraph()

    # 初始化节点权值字典
    node_weights = {}
    tot_w = 0

    # 遍历链表和权值，更新节点权值
    for weight, chain in chains_with_weights:
        tot_w += weight
        for node in chain:
            if node in node_weights:
                node_weights[node] += weight
            else:
                node_weights[node] = weight

    # 添加边到图中（反向添加边）
    for _, chain in chains_with_weights:
        for i in range(len(chain) - 1, 0, -1):  # 从后向前遍历链表
            if chain[i] != chain[i - 1]:
                G.add_edge(chain[i], chain[i - 1])  # 添加反向边
    
    for nv in sorted(node_weights.items(), key=lambda x: x[1]):
        print("{} =====> {}% / {}".format(nv[0], nv[1] / tot_w * 100, pretty_size(nv[1])))
    print("tot_w {}".format(pretty_size(tot_w)))

    # G = nx.petersen_graph()
    # 使用 spring_layout 作为初始布局
    # pos = nx.nx_agraph.graphviz_layout(G, args="-Goverlap=compress -Nshape=box")

    H = nx.convert_node_labels_to_integers(G, label_attribute="node_label")
    H_layout = nx.nx_pydot.pydot_layout(H, prog="dot")
    pos = {H.nodes[n]["node_label"]: p for n, p in H_layout.items()}

    # pos = {k: (v[0]/10, v[1]/10) for (k, v) in pos.items()}

    x_values = [pos[node][0] for node in G.nodes()]
    y_values = [pos[node][1] for node in G.nodes()]
    x_range = max(x_values) - min(x_values)
    y_range = max(y_values) - min(y_values)
    print("[{},{}] - [{},{}]".format(min(x_values), max(x_values), min(y_values), max(y_values)))


    # 计算图形的边界范围
    pos['malloc'] = [min(x_values) + x_range / 2, max(y_values) + 0.1]  # 将节点 "a" 放在 (0, 1) 的位置

    # 动态调整画布比例
    fig, ax = plt.subplots(figsize=(x_range * 0.2, y_range * 0.2))
    # 绘制有向图
    # nx.draw(G, pos, node_shape = "s", node_color='lightblue', alpha = 0.5, edge_color='gray', node_size=10000, arrows=True, arrowsize=16)
    nx.draw(G, pos, alpha = 1, edge_color='black', arrows=True, arrowsize=48)

    def nice(x):
        a = textwrap.fill(x[1:-1], width=40).split("(")[0]
        return a
    
    # def nice(x):
    #     return x

    labels = {node: f"{nice(node)}\n({pretty_size(node_weights[node])})" for node in G.nodes()}

    nx.draw_networkx_labels(G, pos, labels=labels, font_size=48)  # 调整字体大小以避免重叠

    # 调整布局以避免箭头重叠
    plt.tight_layout()

    # 保存为 SVG 文件
    plt.savefig("directed_graph_with_weights.svg", format="svg")
    # mpld3.save_html(fig, "output.html") 

    # rewrite_svg("directed_graph_with_weights.svg")
    # 显示图形
    # plt.show()


def parse_log(file_path):
    # 定义正则表达式模式
    pattern = re.compile(r'(\d+) bytes allocated at:\n(.*?)(?=\n\s+\1|$)', re.DOTALL)
    result = []

    # 打开文件并读取内容
    with open(file_path, 'r') as file:
        log_content = file.read()

    def handle(x):
        return "\"" + x.strip('\t').split("+")[0] + "\""

    # 使用正则表达式匹配日志内容
    for match in pattern.finditer(log_content):
        allocated_bytes = int(match.group(1))  # 提取分配的字节数
        stack_trace = match.group(2).strip().split('\n')  # 提取堆信息栈并分割为列表
        stack_trace = list(map(handle, stack_trace))
        stack_trace.reverse()
        result.append((allocated_bytes, stack_trace))  # 将结果添加到列表中

    result = list(filter(lambda x: x[0] > 1024 * 10, result))
    return result


def parse_ml_log(file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    def handle(x):
        return "\"" + x.strip('\t').split("+")[0] + "\""

    result = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = re.match(r'\s*(\d+) bytes in (\d+) allocations from stack', lines[i])
        if match:
            bytes_alloc = int(match.group(1))
            alloc_count = int(match.group(2))
            i += 1
            stack = []
            while i < len(lines) and lines[i].strip().startswith('0x'):
                # 提取符号信息（地址后面那部分）
                parts = lines[i].split('\t')[-1]
                stack.append(parts)
                i += 1
            stack = list(map(handle, stack))
            stack = list(filter(lambda x: x!="\"[unknown]\"", stack))
            stack.reverse()
            stack.append("malloc")
            # Include frequency
            # result.append((bytes_alloc, alloc_count, stack))
            result.append((bytes_alloc, stack))
            # if len(result) > 3:
            #     break
        else:
            i += 1
    result = list(filter(lambda x: x[0] > 1, result))
    return result


if __name__ == '__main__':
    arr = parse_ml_log("mleak.txt")
    # for a in arr[:2]:
    #     print("{}".format(a))
        
    # print("arr {}".format(arr[:2]))
    gen_image1(arr)
