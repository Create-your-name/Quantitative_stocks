import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import json

params = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
}

lock = threading.Lock()  # 创建线程锁
def parallel_processing(url, page, page_size, pagedate):
    url = f"{url}&page={page}&psize={page_size}"
    #current_thread = threading.current_thread()
    #print(f"url：{url} 线程：{current_thread}")
    response = requests.get(url, params=params)  # 多线程 看看
    if response.status_code == 200:
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        trs = soup.find_all('tr')  # 获取所有的<td>元素

        # threads=[]
        # process_data_bound = partial(process_data, url=url)
        #
        # # Then you can use this bound function to create your threads
        for tr in trs:
            indata = {}
            tds = tr.find_all('td')  # 获取当前<tr>下的所有<td>元素
            i = 0
            for td in tds:
                if td.a:  # 如果<td>元素包含<a>标签，提取该标签的文本内容和href属性
                    a_tags = td.find_all('a')
                    for j, a_tag in enumerate(a_tags):
                        indata[f'相关Url{i}_{j}'] = a_tag.get_text()
                        indata[f'url{i}_{j}'] = a_tag['href']
                elif td.span:  # 如果<td>元素包含<span>标签，提取该标签的文本内容
                    indata[f'定投收益{i}'] = td.span.get_text()
                elif td.input:  # 如果<td>元素包含<input>标签，提取该标签的value属性
                    indata[f'基金代码'] = td.input['value'].split(',')[0]  # 只获取"530020" 部分
                    indata[f'基金名'] = td.input['value'].split(',')[1]  # 只获取"建信转债增强债券A" 部分
                    if True:
                        code = indata['基金代码']
                        get_data(code, indata)
            i = i + 1
            pagedate.put(indata)
    # while not pagedate.empty():
    #     data = pagedate.get()
    #     print(data)
                        # current_thread = threading.current_thread()
            #线程 共用一片内存空间
    #        t = threading.Thread(target=process_data_bound, args=(tr, pagedate, indata))
    #         t.start()
    #         threads.append(t)
    #
    # for t in threads:
    #     t.join()

##123

def get_bonds_data(code,indata):
    # 获取债券数据的代码
    bonds_url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=zqcc&code={code}"
    response1 = requests.get(bonds_url, params=params)

    if response1.status_code == 200:
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        div = soup1.find('div')

        if div:
            indiv = div.find('div')

            if indiv:
                table = div.find('table')

                if table:
                    tbody = table.find('tbody')

                    if tbody:
                        trs = tbody.find_all('tr')
                        if trs:
                            bonds_data = '/'.join([
                                                      f"{tr.find_all('td')[1].text.strip()}&{tr.find_all('td')[2].text.strip()}&{tr.find_all('td')[3].text.strip()}"
                                                      for tr in trs])
                            indata['基金的债卷组成'] = bonds_data

    # indata['基金的债卷组成']= {'我是一個小马骡'}
def get_stock_data(code,indata):
    # 获取股票数据的代码
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    stock_url = f"https://fund.eastmoney.com/pingzhongdata/{code}.js?v={formatted_time}"
    response2 = requests.get(stock_url, params=params)

    if response2.status_code == 200:
        stock_data = BeautifulSoup(response2.text, 'html.parser')
        pattern = r'stockCodes=\["(.*?)"\];'
        result = re.search(pattern, stock_data.text)

        if result:
            stock_codes = result.group(1).split('","')
            stock_codes = [code[:-1] for code in stock_codes]  # Remove the last digit from each element
            # indata['基金的股票组成'] = stock_codes
            #  判断 股票 方向
            url_template = "https://push2.eastmoney.com/api/qt/slist/get?fltt=1&invt=2&secid=0.{}&pn=1&np=1&spt=1"
            indata['股票分布'] = "股票分布："
            for stock in stock_codes:
                # 替换URL中的代码

                url_tep = url_template.format(stock)
                # 发送请求
                Dept = requests.get(url_tep, params=params)
                if Dept.status_code == 200:
                #if Dept.get("data") is not None:
                    # 请求成功
                    stock_data = BeautifulSoup(Dept.text, 'html.parser')
                    stock_data_dict = json.loads(stock_data.text)

                    if "rc" in stock_data_dict and stock_data_dict["rc"] == 0:
                        indata['股票分布'] += stock_data_dict["data"]["diff"][1]["f14"] + "/"
                    elif "rc" in stock_data_dict and stock_data_dict["rc"] == 102:

                            new_url = url_tep.replace('&secid=0.', '&secid=1.')
                            response = requests.get(new_url, params=params)
                            if response.status_code == 200:
                                # if Dept.get("data") is not None:
                                # 请求成功
                                stock_data = BeautifulSoup(Dept.text, 'html.parser')
                                stock_data_dict = json.loads(stock_data.text)
                                if "rc" in stock_data_dict and stock_data_dict["rc"] == 0:
                                    indata['股票分布'] += stock_data_dict["data"]["diff"][1]["f14"] + "/"

    # indata['基金的股票组成']={'未来可期'}
def get_data(code,indata):
    # 获取基金数据的代码
    bonds_data = get_bonds_data(code,indata)
    stock_data = get_stock_data(code,indata)

    # if bonds_data:
    #     indata['基金的债券组成'] = bonds_data
    # if stock_data:
    #     indata['基金的股票组成'] = stock_data
    # 创建两个线程，分别用于请求债券数据和股票数据
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     future1 = executor.submit(get_bonds_data, code, indata)
    #     future2 = executor.submit(get_stock_data, code, indata)
    # if bonds_thread:
    #     indata['基金的债券组成'] = bonds_thread
    # if stock_thread:
    #     indata['基金的股票组成'] = stock_thread
## 1234

def Bonds(url, sheet, page_index, page_size):
    result_queue = queue.Queue()
    with ThreadPoolExecutor(max_workers=50) as executor:  # 可根据需求调整最大工作线程数
        futures = [executor.submit(parallel_processing, url, page, page_size ,result_queue) for page in range(1, page_index + 1)]
        # 等待所有任务完成
    for future in as_completed(futures):  # 等待所有任务完成
        try:
            future.result()
        except Exception as e:


            print(f"Error occurred: {e}")

    data_list = []
    while not result_queue.empty():
        data = result_queue.get()
        data_list.append(data)
    df = pd.DataFrame(data_list)

    with pd.ExcelWriter('data.xlsx', mode='a', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)


    print("ojbk")

params_list = [
    {'url': 'http://fund.eastmoney.com/api/Dtshph.ashx?t=1&c=dwjz&s=desc&issale=1', 'sheet': '股票','page':8},
    {'url': 'http://fund.eastmoney.com/api/Dtshph.ashx?t=3&c=dwjz&s=desc&issale=1', 'sheet': '债卷', 'page': 23},
    {'url': 'http://fund.eastmoney.com/api/Dtshph.ashx?t=2&c=dwjz&s=desc&issale=1', 'sheet': '混合','page':58},
    {'url': 'http://fund.eastmoney.com/api/Dtshph.ashx?t=4&c=dwjz&s=desc&issale=1', 'sheet': '指数','page':17},
]
# 调用函数获取第一页，每页10条数据


page_size = 100
for page in params_list:
    data = Bonds(page['url'],page['sheet'],page['page'], page_size)
