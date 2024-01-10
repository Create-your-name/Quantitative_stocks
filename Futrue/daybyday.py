import os
import datetime
import pandas as pd
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from bs4 import BeautifulSoup
import json

params = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
}
def GetLi(url ,bond,page):
    if page >3:
        url = f"{url}&page_time={page}"
    else:
        url=f"{url}"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.text

        # Define the patterns to match Chinese characters and data-code attribute
        chinese_pattern = re.compile(r'<span>([\u4e00-\u9fa5]+)</span>')
        code_pattern = re.compile(r'data-code="(\d+)"')

        # Find all matches for Chinese characters and data-code attributes
        chinese_matches = chinese_pattern.findall(data)
        code_matches = code_pattern.findall(data)

        # Filter out unwanted Chinese character matches
        filtered_chinese_matches = [match for match in chinese_matches if
                                    match not in ['验证码登录', '第三方账户登录', '使用微信扫一扫登录', '热榜', '视频']]
        # Combine the filtered Chinese characters with their corresponding data-code values
        combined_data = zip(filtered_chinese_matches, code_matches)

        # Insert the combined data into bond.put
        for item in combined_data:
            bond.put(f"{item[0]} {item[1]}")

def extract_number(item):
    match = re.search(r'\d+', item)  # 使用正则表达式匹配数字部分
    if match:
        return match.group()  # 返回匹配到的数字部分，转换为整数类型
    else:
        return None  # 如果没有匹配到数字部分，则返回None或者其他默认值
def kxInfo(url, sheet,page_index):
    bond = queue.Queue()
    with ThreadPoolExecutor(max_workers=1) as executor:  # 可根据需求调整最大工作线程数
        futures = [executor.submit(GetLi, url,bond,page) for page in range(1, page_index + 1)]
        # 等待所有任务完成
    for future in as_completed(futures):  # 等待所有任务完成
        try:
            future.result()
        except Exception as e:
            print(f"Error occurred: {e}")
    element_count = {}
    industry={}
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    year = current_date[:4]  # 获取年份（字符串的前4个字符）
    month_day = current_date[5:]  # 获取月日（字符串的第6个字符到末尾）

    data_list = [(year, month_day,"行业")]  # 给data_list赋值，第一列是年份，第二列是月日
    while not bond.empty():
        item = bond.get()
        if item in element_count:
            element_count[item] += 1
            number_part = extract_number(item)
            get_stock_data(number_part,industry,item)

        else:
            element_count[item] = 1
            number_part = extract_number(item)
            get_stock_data(number_part,industry,item)
        data_list.append((item, element_count[item],industry[item]))  #


    file_name = "每日咨询相关股.xlsx"
    new_df = pd.DataFrame(data_list, columns=["股票", "数量","行业"])  # 给每一列赋予实际意义的列名

    if not os.path.isfile(file_name):
        with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
            new_df.to_excel(writer, sheet_name="每日咨询", index=False)
    else:
        existing_df = pd.read_excel(file_name, sheet_name="每日咨询")
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)  # 将新数据追加到现有数据下面

        with pd.ExcelWriter(file_name, engine="openpyxl", mode="w") as writer:  # 使用"w"模式覆盖原文件
            updated_df.to_excel(writer, sheet_name="每日咨询", index=False)

def get_stock_data(code,industry,item):
        url_template = "https://push2.eastmoney.com/api/qt/slist/get?fltt=1&invt=2&secid=0.{}&pn=1&np=1&spt=1"
        url_tep = url_template.format(code)
        # 发送请求
        Dept = requests.get(url_tep, params=params)
        if Dept.status_code == 200:
            # 请求成功
            stock_data = BeautifulSoup(Dept.text, 'html.parser')
            stock_data_dict = json.loads(stock_data.text)
            if "rc" in stock_data_dict and stock_data_dict["rc"] == 0:
                industry[item]=stock_data_dict["data"]["diff"][1]["f14"]
            elif "rc" in stock_data_dict and stock_data_dict["rc"] == 102:
                new_url = url_tep.replace('&secid=0.', '&secid=1.')
                response2 = requests.get(new_url, params=params)
                if response2.status_code == 200:
                    # if Dept.get("data") is not None:
                    # 请求成功
                    stock_data = BeautifulSoup(response2.text, 'html.parser')
                    stock_data_dict = json.loads(stock_data.text)
                    if "rc" in stock_data_dict and stock_data_dict["rc"] == 0:
                        industry[item] = stock_data_dict["data"]["diff"][1]["f14"]
                    else:
                        industry[item] ="未知行业"

page= {'url': 'http://www.stcn.com/article/list.html?type=kx', 'sheet': '每日快讯','page_index':30};
data = kxInfo(page['url'],page['sheet'],page['page_index'])
