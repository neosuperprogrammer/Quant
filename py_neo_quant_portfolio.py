# %load py_neo_quant_portfolio.py
import pandas as pd
import numpy as np
# import requests
# import bs4
# import time
# import datetime
import matplotlib.pyplot as plt
# from dateutil import parser
from matplotlib import font_manager, rc
# from IPython.display import HTML
# pd.set_option('display.max_colwidth', -1)

rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False
# pd.options.display.max_rows = 60
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)
%matplotlib inline

########################## API ################################

# def get_portfolio_file_name():
#     return r'data/my_portfolio.xlsx'

# def get_price_file_name():
#     return r'data/my_portfolio_price.xlsx'

def save_price_data(price_df):
    price_df.to_excel(get_price_file_name())  

def load_price_data():
    price_df = pd.read_excel(get_price_file_name())
    return price_df


def make_my_portfolio(pf_stock_num, start_date, price_df):
    strategy_price = price_df[my_portfolio_code_list][start_date:]

    pf_df = pd.DataFrame(pf_stock_num, index=[strategy_price.iloc[0].name])
    pf_df['cash'] = 0
    
    return pf_df

def save_my_portfolio(pf_df):
    pf_df.to_excel(get_portfolio_file_name())  

def load_my_portfolio():
    total_pf_df = pd.read_excel(get_portfolio_file_name())
    total_pf_df = total_pf_df.set_index(total_pf_df.columns[0])
    total_pf_df.index.name = ''
    
#     cache_df = pd.DataFrame({'buy_date':start_date}, index=total_pf_df.columns[:-1])
#     for code in cache_df.index:
#         last_buy_date = get_last_buy_date(total_pf_df, code)
#         cache_df.at[code, 'buy_date'] = last_buy_date
    
    return total_pf_df

def test_date_overlap(origin_price_df, firm_list, count):
    origin_final_date = origin_price_df.iloc[-1].name
    test_firm_code = firm_list[0]
    test_price_df = make_price_dataframe(test_firm_code, 'day', count)
    test_price_df.index = pd.to_datetime(test_price_df.index)
    test_first_date = test_price_df.iloc[0].name
    if origin_final_date >= test_first_date:
        return True
    else:
        return False
    
def update_portfolio_price_df(total_pf_df, total_price_df, count):
    start_date = total_pf_df.iloc[0].name
#     firm_list = total_pf_df.columns[:-1]
    firm_list = get_hold_firm_list(total_pf_df)
    if file_exists(get_price_file_name()):
        print('exists')
        origin_price_df = load_price_data()
        origin_price_df = origin_price_df.set_index(origin_price_df.columns[0])
        origin_price_df.index.name = ''
    else:
        print('not exists')
        origin_price_df = total_price_df[firm_list][start_date:]
        origin_price_df.index.name = ''
# save_price_data(origin_price_df)
    if not test_date_overlap(origin_price_df, firm_list, count):
        print('>>>>>>> date not overlap, add more count')
        return origin_price_df
    
    exist_firm_list = []
    not_exist_firm_list = []
    for firm_code in firm_list:
        if firm_code in origin_price_df.columns:
            exist_firm_list.append(firm_code)
        else:
            not_exist_firm_list.append(firm_code)

    update_price_df = update_prices(exist_firm_list, origin_price_df, count)  
    for firm_code in not_exist_firm_list:
        temp_price_df = make_price_dataframe(firm_code, 'day', count)
        temp_price_df.index = pd.to_datetime(temp_price_df.index)
        temp_price_df[firm_code] = temp_price_df[firm_code].astype(float)
        update_price_df = pd.concat([update_price_df, temp_price_df], axis=1)
        update_price_df = update_price_df.fillna(method='bfill')
    return update_price_df








