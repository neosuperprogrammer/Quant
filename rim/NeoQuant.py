import pandas as pd
import numpy as np
import requests
import bs4
import math
import time
import datetime
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
pd.set_option('display.max_colwidth', -1)
rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

def request_company_list(kospi = True):
    if kospi == True: 
        marketType = 'stockMkt'
    else:
        marketType = 'kosdaqMkt'
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13&marketType=' + marketType
    company = pd.read_html(url, header=0)[0]

    company = company[['종목코드', '회사명']]
    company = company.rename(columns={
        '종목코드': 'code'
        , '회사명': 'company'
    })
    company = company.sort_values(by='code')
    company.code = company.code.map('{:06d}'.format)
    company = company.set_index(company.columns[0])
    return company

def request_price_list(company_code, timeframe, count):
    request_code = company_code
    if request_code.startswith('A'):
        request_code = request_code.replace('A','')
    url = 'https://fchart.stock.naver.com/sise.nhn?requestType=0'
    price_url = url + '&symbol=' + request_code + '&timeframe=' + timeframe + '&count=' + str(count)
    price_data = requests.get(price_url)
    price_data_bs = bs4.BeautifulSoup(price_data.text, 'lxml')
    item_list = price_data_bs.find_all('item')
    
    date_list = []
    price_list = []
    for item in item_list:
        temp_data = item['data']
        datas = temp_data.split('|')
        date_list.append(datas[0])
        price_list.append(datas[4])

    price_list = pd.to_numeric(price_list)
    price_df = pd.DataFrame({company_code:price_list}, index=date_list)
    price_df.index = pd.to_datetime(price_df.index)
    
    return price_df

def get_company_list(kospi = True):
    if kospi == True: 
        file_loc = 'data/kospi.xlsx'
    else:
        file_loc = 'data/kosdaq.xlsx'

    company = pd.read_excel(file_loc)
    company.code = company.code.map('{:06d}'.format)
    company = company.set_index(company.columns[0])
    return company

def get_all_company_list():
    kospi = get_company_list(True)
    kosdaq = get_company_list(False)
    kospi['type'] = 'kospi'
    kosdaq['type'] = 'kosdaq'
    companies = pd.concat([kospi, kosdaq], sort=False)
    return companies

def get_company_code(name, company_df):
    if len(company_df[company_df['company'] == name]) > 0:
        return company_df[company_df['company'] == name].index[0]
    else:
#         print('no company code with ' + name)
        return ''

def show_company_candidate(name, company_df):
    return company_df[company_df['company'].str.contains(name)]

def get_total_stock_count(snapshot_tables):
    stock_count = 0

    info = snapshot_tables[0]
    info = info.set_index(info.columns[0])
    stock_count_info = info.loc['발행주식수(보통주/ 우선주)'][1]
    stock_counts = stock_count_info.split('/')
    for count in stock_counts:
#         print(count)
        stock_count = stock_count + int(count.replace(',',''))

    return stock_count

def get_self_stock_count(snapshot_tables):
    self_stock_count = 0
    info = snapshot_tables[4]
    info = info.set_index(info.columns[0])
    count = info.loc[['자기주식\xa0(자사주+자사주신탁)']]['보통주'][0]
#     print(count)
    if not math.isnan(count):
        self_stock_count = int(count)
    return self_stock_count


def get_standard_col_name(snapshot_tables):
    big_col_name = 'Annual'
    roe_index_name = 'ROE'
    asset_index_name = '지배주주지분'
    
    info = snapshot_tables[10]
    info = info.set_index(info.columns[0])

    stadard_col_name = ''
    roes = info.loc[roe_index_name][big_col_name]
    assets = info.loc[asset_index_name][big_col_name]
    for index in reversed(assets.index):
        if not math.isnan(assets[index]) and not math.isnan(roes[index]):
            stadard_col_name = index
            break
    return stadard_col_name

def get_base_year_name(fr_df):
    big_col_name = 'Annual'
    roe_index_name = 'ROE'
    asset_index_name = '지배주주지분'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    stadard_col_name = ''
    roes = info.loc[roe_index_name][big_col_name]
    assets = info.loc[asset_index_name][big_col_name]
    for index in reversed(assets.index):
        if index.endswith(('(E)')):
            continue
        if not math.isnan(assets[index]) and not math.isnan(roes[index]):
            stadard_col_name = index
            break
    return stadard_col_name

def get_roe(snapshot_tables, stadard_col_name):
    big_col_name = 'Annual'
    roe_index_name = 'ROE'
    
    info = snapshot_tables[10]
    info = info.set_index(info.columns[0])

    roe = info.loc[roe_index_name][big_col_name, stadard_col_name]
    return roe

def get_asset(snapshot_tables, stadard_col_name):
    big_col_name = 'Annual'
    asset_index_name = '지배주주지분'
    
    info = snapshot_tables[10]
    info = info.set_index(info.columns[0])

    asset = info.loc[asset_index_name][big_col_name, stadard_col_name]
    asset = asset * 100000000
    return asset

def get_roe2(fr_df, base_year_name):
    big_col_name = 'Annual'
    roe_index_name = 'ROE'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    roe = info.loc[roe_index_name][big_col_name, base_year_name]
    return roe

def get_per(fr_df, base_year_name):
    big_col_name = 'Annual'
    per_index_name = 'PER'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    per = info.loc[per_index_name][big_col_name, base_year_name]
    return per

def get_net_income(fr_df, base_year_name):
    big_col_name = 'Annual'
    index_name = '당기순이익'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    income = info.loc[index_name][big_col_name, base_year_name]
    income = income * 100000000
    return income

def get_net_profit(fr_df, base_year_name):
    big_col_name = 'Annual'
    profit_index_name = '지배주주지분'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    profit = info.loc[profit_index_name][big_col_name, base_year_name]
    profit = profit * 100000000
    return profit

def get_op_profit(fr_df, base_year_name):
    big_col_name = 'Annual'
    profit_index_name = '영업이익'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    profit = info.loc[profit_index_name][big_col_name, base_year_name]
    profit = profit * 100000000
    return profit

def get_asset2(fr_df, base_year_name):
    big_col_name = 'Annual'
    asset_index_name = '자산총계'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    asset = info.loc[asset_index_name][big_col_name, base_year_name]
    asset = asset * 100000000
    return asset

def get_dividend(fr_df, base_year_name):
    big_col_name = 'Annual'
    index_name = '배당수익률'
    
    fr_df = fr_df.set_index(fr_df.columns[0])

    info = fr_df.loc[index_name][big_col_name, base_year_name]
    return info

def get_adequate_price(net_profit, roe, expected_ratio, stock_count, persist_factor = 1):
    excess_profit = (roe - expected_ratio) * net_profit / 100
#     print(excess_profit)
    accumulate_profit = (persist_factor * excess_profit) / (1 + expected_ratio / 100 - persist_factor)
    adequate_stock_price = net_profit + accumulate_profit
#     print(adequate_stock_price)
    price = (net_profit + accumulate_profit) / stock_count
    price = int(round(price))
    return price

def get_ex_profits(net_profit, expected_ratio, roe, persist_factor, iteration = 10):
    next_net_profit = net_profit
    ex_profits = []
    ex_profit_ratio = roe - expected_ratio
    next_roe = roe
    for _ in range(iteration):
        ex_profit_ratio = ex_profit_ratio * persist_factor
        next_roe = expected_ratio + ex_profit_ratio
        profit = next_net_profit * (next_roe / 100)
        ex_profit = next_net_profit * ex_profit_ratio / 100
        ex_profits.append(ex_profit)
        next_net_profit = next_net_profit + profit
    return ex_profits
def get_npv_profit(ex_profits, expected_ratio):
    npv_value = 0
    for num, ex_profit in enumerate(ex_profits):
        ex_profit = ex_profit *  1 / (1 + expected_ratio / 100) ** (num + 1)
#         print(ex_profit)
        npv_value = npv_value + ex_profit

    return npv_value

def get_sum_of_profit(net_profit, expected_ratio, roe, persist_factor, iteration = 10):
    ex_profits = get_ex_profits(net_profit, expected_ratio, roe, persist_factor, iteration)
    sum_of_profit = get_npv_profit(ex_profits, expected_ratio)
    return sum_of_profit

def get_more_adequate_price(net_profit, roe, expected_ratio, stock_count, persist_factor = 1, iteration = 10):
    accumulate_profit = get_sum_of_profit(net_profit, expected_ratio, roe, persist_factor, iteration)
    adequate_stock_price = net_profit + accumulate_profit
    price = (net_profit + accumulate_profit) / stock_count
    price = int(round(price))
    return price

def show_price_chart(company_code, company_name, price_df):
    plt.figure(figsize=(20, 12))
    plt.plot(price_df.index, price_df[company_code], color='darkblue',linewidth=1.0)
    if 'price_very_low' in price_df.columns:
        plt.plot(price_df.index, price_df['price_very_low'], color='grey',linewidth=3.0, label='very low')
    plt.plot(price_df.index, price_df['price_low'], color='blue',linewidth=3.0, label='low')
    plt.plot(price_df.index, price_df['price_middle'], color='green',linewidth=3.0, label='middle')
    plt.plot(price_df.index, price_df['price_high'], color='red',linewidth=3.0, label='high')
    plt.title(company_name)
    plt.xlabel("duration")
    plt.ylabel("price")
    plt.legend(loc='upper right')
    # plt.grid()
    plt.show() 
    
def get_snapshot_from_fnguide(company_code):
#     company_code = get_company_code(company_name, companies)
#     print('firm name : ' + company_name)
#     print('firm code : ' + company_code)
    if len(company_code) == 0:
        return []
    
    if not company_code.startswith('A'):
        company_code = 'A' + company_code

    snapshot_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701&gicode=' + company_code
    snapshot_page = requests.get(snapshot_url)
    snapshot_tables = pd.read_html(snapshot_page.text)
    return snapshot_tables

def show_adequate_price_chart(company_name):
    company_code = get_company_code(company_name, companies)
    print('firm name : ' + company_name)
    print('firm code : ' + company_code)

    if not company_code.startswith('A'):
        company_code = 'A' + company_code

    snapshot_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701&gicode=' + company_code
    snapshot_page = requests.get(snapshot_url)
    snapshot_tables = pd.read_html(snapshot_page.text)
    
    stock_count = get_total_stock_count(snapshot_tables) - get_self_stock_count(snapshot_tables)
    print('stock count : ' + str(stock_count))
    
    stadard_col_name = get_standard_col_name(snapshot_tables)
    print('stadard_col_name : ' + stadard_col_name)
    roe =  get_roe(snapshot_tables, stadard_col_name)
    asset = get_asset(snapshot_tables, stadard_col_name)
    print('standard date : ' + stadard_col_name)
    print('asset : ' + str(asset))
    print('roe : ' + str(roe))
    
    price_high = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 1)
    price_middel = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 0.9)
    price_low = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 0.8)

    print('buy : below ' + str(price_low))
    print('sell 1/3 : ' + str(price_middel))
    print('sell 1/3 : ' + str(price_high))
    
    price_df = request_price_list(company_code, 'day', 1000)

    price_df['price_low'] = [price_low] * len(price_df)
    price_df['price_middle'] = [price_middel] * len(price_df)
    price_df['price_high'] = [price_high] * len(price_df)
    
    show_price_chart(company_code, company_name, price_df)
    

def show_more_adequate_price_chart(company_name, companies, expected_ratio):
    company_code = get_company_code(company_name, companies)
    print('company name : ' + company_name)
    print('company code : ' + company_code)

    if len(company_code) == 0:
        print('>>> no company code with ' + company_name)
        return

    snapshot_tables = get_snapshot_from_fnguide(company_code)
    
    stock_count = get_total_stock_count(snapshot_tables) - get_self_stock_count(snapshot_tables)
    print('stock count : ' + str(stock_count))
    
    stadard_col_name = get_standard_col_name(snapshot_tables)
    print('stadard_col_name : ' + stadard_col_name)
    if len(stadard_col_name) == 0:
        print('>>> no financial data with ' + company_name)
        return

    roe =  get_roe(snapshot_tables, stadard_col_name)
    asset = get_asset(snapshot_tables, stadard_col_name)
    print('standard date : ' + stadard_col_name)
    print('asset : ' + str(asset))
    print('roe : ' + str(roe))


    price_high = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 1)
    price_middel = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 0.9)
    price_low = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 0.8)
    price_very_low = get_more_adequate_price(asset, roe, expected_ratio, stock_count, 0.5)

    print('buy : below ' + str(price_low))
    print('sell 1/3 : ' + str(price_middel))
    print('sell 1/3 : ' + str(price_high))
    
    price_df = request_price_list(company_code, 'day', 1000)

    current_price = price_df[company_code][-1]
    print('current price : ' + str(current_price))
    discrepancy_rate = current_price / price_low 
    print('discrepancy rate : ' + str(discrepancy_rate))

    price_df['price_very_low'] = [price_very_low] * len(price_df)
    price_df['price_low'] = [price_low] * len(price_df)
    price_df['price_middle'] = [price_middel] * len(price_df)
    price_df['price_high'] = [price_high] * len(price_df)
    
    show_price_chart(company_code, company_name, price_df)
    
def get_fr_df_index(snapshot_tables):
    fr_df_index = -1
    for num, snapshot in enumerate(snapshot_tables):
        if 'Annual' in snapshot.columns:
            if len(snapshot['Annual'].columns) > 4:
#                 print('bingo ' + str(num))
                fr_df_index = num
                break
    return fr_df_index

def get_year_name_list(fr_df, until_this_year = False):
    big_col_name = 'Annual'
    roe_index_name = 'ROE'
    asset_index_name = '지배주주지분'
    
    info = fr_df
    info = info.set_index(info.columns[0])

    year_name_list = []
    
    year_name = ''
    roes = info.loc[roe_index_name][big_col_name]
    assets = info.loc[asset_index_name][big_col_name]
    today_year = datetime.date.today().year
    for index in assets.index:
#         if index.endswith(('(E)')):
#             continue
        if until_this_year:
            year = int(index[:4])
            if year > today_year:
                continue
        if not math.isnan(assets[index]) and not math.isnan(roes[index]):
            year_name = index
#             year_name = str(pd.to_datetime(year_name).year)
            year_name_list.append(year_name)
    return year_name_list


def show_sequence_adequate_price_chart(company_name, companies, base_profit_ratio, until_this_year = False):
    company_code = get_company_code(company_name, companies)
    print('company name : ' + company_name)
    print('company code : ' + company_code)

    if len(company_code) == 0:
        print('>>> no company code with ' + company_name)
        return

    snapshot_tables = get_snapshot_from_fnguide(company_code)
    
    stock_count = get_total_stock_count(snapshot_tables) - get_self_stock_count(snapshot_tables)
#     print('stock count : ' + str(stock_count))
    
    fr_df_index = get_fr_df_index(snapshot_tables)
#     print('fr_df_index : ' + str(fr_df_index))
    if fr_df_index < 0:
        print('>>> fr df index fail : ' + str(fr_df_index))
        return
    fr_df = snapshot_tables[fr_df_index]
    
    year_name_list = get_year_name_list(fr_df, until_this_year)
    
    price_df = request_price_list(company_code, 'day', 1500)
    price_df['price_very_low'] = 0
    price_df['price_low'] = 0
    price_df['price_middle'] = 0
    price_df['price_high'] = 0
    

    final_year = price_df.iloc[-1].name.year

    for year_name in year_name_list:
    #     print(year_name)
        roe =  get_roe2(fr_df, year_name)
        net_profit = get_net_profit(fr_df, year_name)
        per = get_per(fr_df, year_name)
        dividend = get_dividend(fr_df, year_name)

        price_high = get_more_adequate_price(net_profit, roe, base_profit_ratio, stock_count, 1)
        price_middle = get_more_adequate_price(net_profit, roe, base_profit_ratio, stock_count, 0.9)
        price_low = get_more_adequate_price(net_profit, roe, base_profit_ratio, stock_count, 0.8)
        price_very_low = get_more_adequate_price(net_profit, roe, base_profit_ratio, stock_count, 0.5)


        print('=====================================')
        print('base year : ' + year_name)
        print('net profit : ' + str(net_profit))
        print('roe : ' + str(roe))
        print('per : ' + str(per))
        print('dividend : ' + str(dividend))
        print('very low : ' + str(price_very_low))
        print('buy : below ' + str(price_low))
        print('sell 1/3 : ' + str(price_middle))
        print('sell 1/3 : ' + str(price_high))


    #     if (price_very_low >= price_low):
    #         price_low = int(price_very_low * 1.05)
    #         price_middle = int(price_low * 1.05)
    #         price_high = int(price_middle * 1.05)

    #         print('======= modify ===============')
    #         print('very low : ' + str(price_very_low))
    #         print('buy : below ' + str(price_low))
    #         print('sell 1/3 : ' + str(price_middle))
    #         print('sell 1/3 : ' + str(price_high))

        if (year_name.endswith('(E)')):
    #         continue
            year_name = year_name.replace('(E)', '')

        base_year = pd.to_datetime(year_name).year
        try:
            final_year_price = price_df.loc[str(base_year)][company_code][-1]
            print('final year price : ' + str(final_year_price))
            if price_low < price_high:
                print('dis rate : ' + str(final_year_price / price_low))
            else:
                print('dis rate : ' + str(final_year_price / price_high))
        except KeyError:
            print('key error')

        if (base_year == final_year):
            start_date = price_df.iloc[-1].name + timedelta(days=1)
            end_date = pd.to_datetime(str(final_year) + '-12-31')
            year_list = pd.date_range(start_date, end_date, freq='d')
            year_df = pd.DataFrame(0, index=year_list, columns=price_df.columns)
            price_df = price_df.append(year_df)

        if (base_year > final_year):
    #         print(base_year)
            start_year = pd.to_datetime(str(base_year))
            year_list = pd.date_range(start_year, freq=pd.DateOffset(days=1), periods=365)
            year_df = pd.DataFrame(0, index=year_list, columns=price_df.columns)
            price_df = price_df.append(year_df)


        base_year = str(base_year)
        try:
            price_df.loc[base_year]['price_very_low'] = [price_very_low] * len(price_df.loc[base_year])
            price_df.loc[base_year]['price_low'] = [price_low] * len(price_df.loc[base_year])
            price_df.loc[base_year]['price_middle'] = [price_middle] * len(price_df.loc[base_year])
            price_df.loc[base_year]['price_high'] = [price_high] * len(price_df.loc[base_year])
        except KeyError:
            print('key error')
    
    show_price_chart(company_code, company_name, price_df)
        
def get_total_stock_count(snapshot_tables):
    stock_count = 0

    info = snapshot_tables[0]
    info = info.set_index(info.columns[0])
    stock_count_info = info.loc['발행주식수(보통주/ 우선주)'][1]
    stock_counts = stock_count_info.split('/')
    for count in stock_counts:
#         print(count)
        stock_count = stock_count + int(count.replace(',',''))

    return stock_count

def get_self_stock_count(snapshot_tables):
    self_stock_count = 0
    info = snapshot_tables[4]
    info = info.set_index(info.columns[0])
    try:
        count = info.loc[['자기주식\xa0(자사주+자사주신탁)']]['보통주'][0] 
    except KeyError:
        count = 0
#     print(count)
    if not math.isnan(count):
        self_stock_count = int(count)
    return self_stock_count

# stock_count = get_total_stock_count(snapshot_tables) - get_self_stock_count(snapshot_tables)
# print('stock count : ' + str(stock_count))

def make_basic_df(company_code, company_name, snapshot_tables):
    info = snapshot_tables[0]
    info = info.set_index(info.columns[0])
    info = info.fillna(0)
    price = int(info.loc['종가/ 전일대비'].iloc[0].split('/')[0].replace(',', ''))
    foreigner = float(info.loc['수익률(1M/ 3M/ 6M/ 1Y)'].iloc[2])
    market_value = int(info.loc['시가총액(보통주,억원)'].iloc[0]) * 100000000
    if market_value == 0:
        market_value = int(info.loc['시가총액(상장예정포함,억원)'].iloc[0]) * 100000000

    average_stock_count = get_total_stock_count(snapshot_tables)
    self_stock_count = get_self_stock_count(snapshot_tables)

    basic_df = pd.DataFrame({'name': company_name, 'price': price, '총주식수': average_stock_count, '자사주': self_stock_count}, index = [company_code])
    basic_df['주식수'] = basic_df['총주식수'] - basic_df['자사주']


#     basic_df['price'] = price
    basic_df['외국인'] = foreigner
    basic_df['시가총액'] = market_value
    return basic_df

def make_fr_df(company_code, snapshot_tables):
    fr_df_index = -1
    for num, snapshot in enumerate(snapshot_tables):
        if 'Annual' in snapshot.columns:
            if len(snapshot['Annual'].columns) > 4:
#                 print('bingo ' + str(num))
                fr_df_index = num
                break

    if fr_df_index == -1:
        raise ValueError('>>>>> no fr dataframe with ' + str(company_code))
        
    data_df = snapshot_tables[fr_df_index]
#     if len(data_df) < 20:
#         data_df = snapshot_tables[11]
    data_df.index = data_df[data_df.columns[0]]
    data_df.index.name = ''
    data_df.drop(data_df.columns[0], axis = 1, inplace = True)
    
#     data_df = data_df.set_index(data_df.columns[0])
    data_df = data_df['Annual']

    for num, name in enumerate(data_df.columns):
        if name.endswith(('(E)', '(P)')):
            continue
        temp_df = pd.DataFrame({company_code: data_df[name]})
        temp_df = temp_df.loc[['영업이익', '지배주주순이익', '자산총계', '부채총계', '자본총계', '지배주주지분', '부채비율', '유보율', 'ROE', 'ROA', 'PER', 'PBR', '배당수익률']]
        temp_df = temp_df.T
        rim_roa = float(temp_df['영업이익']) / float(temp_df['자산총계']) * 100.0
        rim_roa = round(rim_roa, 2)
        temp_df['RIM_ROA'] = rim_roa
        temp_df.columns = [[name] * len(temp_df.columns), temp_df.columns]
        if num == 0:
            total_df = temp_df
        else:
            total_df = pd.merge(total_df, temp_df, how='outer', left_index=True, right_index=True)    
    return total_df


def request_fnguide_snapshot(company_code):
    if not company_code.startswith('A'):
        company_code = 'A' + company_code
    
    snapshot_url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701&gicode=' + company_code
    snapshot_page = requests.get(snapshot_url)
    snapshot_tables = pd.read_html(snapshot_page.text)
    return snapshot_tables

def get_ex_profits(asset, expected_ratio, roe, persist_factor, iteration = 10):
    next_asset = asset
    ex_profits = []
    ex_profit_ratio = roe - expected_ratio
    next_roe = roe
    for _ in range(iteration):
        ex_profit_ratio = ex_profit_ratio * persist_factor
        next_roe = expected_ratio + ex_profit_ratio
        profit = next_asset * (next_roe / 100)
        ex_profit = next_asset * ex_profit_ratio / 100
        ex_profits.append(ex_profit)
        next_asset = next_asset + profit
    return ex_profits
def get_npv_profit(ex_profits, expected_ratio):
    npv_value = 0
    for num, ex_profit in enumerate(ex_profits):
        ex_profit = ex_profit *  1 / (1 + expected_ratio / 100) ** (num + 1)
#         print(ex_profit)
        npv_value = npv_value + ex_profit

    return npv_value

def get_sum_of_profit(asset, expected_ratio, roe, persist_factor, iteration = 10):
    ex_profits = get_ex_profits(asset, expected_ratio, roe, persist_factor, iteration)
    sum_of_profit = get_npv_profit(ex_profits, expected_ratio)
    return sum_of_profit

def get_more_adequate_price(asset, roe, expected_ratio, stock_count, persist_factor = 1, iteration = 10):
    accumulate_profit = get_sum_of_profit(asset, expected_ratio, roe, persist_factor, iteration)
#     print(accumulate_profit)
    adequate_stock_price = asset + accumulate_profit
#     print(adequate_stock_price)
    price = (asset + accumulate_profit) / stock_count
    price = int(round(price))
    return price

def get_company_name(code, company_df):
    name = company_df.loc[code]['company']
    if len(name) > 0:
        return name
    else:
        return ''    

def get_base_profit_ratio():
    spread_url = 'https://www.kisrating.co.kr/ratingsStatistics/statics_spread.do'
    spread_page = requests.get(spread_url)
    spread_tables = pd.read_html(spread_page.text)
    spread = spread_tables[0]
    expected_ratio = spread.set_index(spread.columns[0]).loc['BBB-']['5년']
    return expected_ratio  

def get_company_code_list(company_name_list, companies):
    company_code_list = []
    for name in company_name_list:
        company_code = get_company_code(name, companies)
        company_code_list.append(company_code)
    return company_code_list

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def generally_increasing(lst, n=4):
    return np.all(np.diff(moving_average(np.array(lst), n))>0)


    