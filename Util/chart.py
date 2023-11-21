import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import re
import os
def process_excel_data(file_path, x_column, y_column):
    # 读取Excel文件
    data = pd.read_excel(file_path)
    # 如果x轴对应的是数字，则跳过这一行
    if isinstance(data[x_column].iloc[0], (int, float)):
        print("X-axis data is numeric, skipping the plot.")
        return

    # 设置中文字体
    plt.rcParams['font.family'] = 'SimHei'  # 设置为中文字体
    plt.rcParams['font.size'] = 8  # 设置字体大小

    # 提取指定的两列数据，并进行去重和求和操作
    grouped_data = data.groupby(x_column)[y_column].sum()
    y_data = [item for item in grouped_data.index.astype(str) if "行业" not in item or len(item) > 2]
    x_data = [int(re.sub(r'\D', '', str(item))) for item in grouped_data.values.astype(str) if '-' not in str(item)]
    min_y_value = 0  # 设置y轴最低值为0

    # 绘制图表
    fig, ax = plt.subplots(figsize=(10, 6))  # 设置图表尺寸
    ax.bar(y_data, x_data)
    ax.set_xlabel('行业')
    ax.set_ylabel('数量')
    ax.tick_params(axis='x', rotation=90)  # 设置x轴标签竖直显示
    ax.set_ylim(bottom=min_y_value)  # 设置y轴最低值
    today = datetime.today().strftime('%Y-%m-%d')  # 将当前日期转化为指定格式的字符串
    ax.set_title(f'({today})')  # 使用当前日期作为标题
    plt.tight_layout()  # 自动调整图表布局，防止标签重叠

    # 添加滚动条
    plt.subplots_adjust(bottom=0.2)  # 留出底部空间放置滚动条
    ax.set_xlim([-1, len(y_data)])
    print(today)
    plt.savefig(f'{today}.png')  # 将生成的图表保存到本地
    plt.show()

file_path = "../Futrue/每日咨询相关股.xlsx"
x_column = '行业'  # Assuming the column name is 'C', if it's a different name, replace it with the actual column name.
y_column = '数量'  # Assuming the column name is 'B', if it's a different name, replace it with the actual column name.

process_excel_data(file_path, x_column, y_column)