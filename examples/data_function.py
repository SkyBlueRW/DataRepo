import sys 
if "/home/ray/src/DataRepo" not in sys.path:
    sys.path.append("/home/ray/src/DataRepo")


import pandas as pd 

from datarepo import data_config

# --------------------  dates 数据更新实例 --------------------------

@data_config(
    status='update',
    table_name='dates_test_table',
    data_structure={
        'date': "CHAR(8)",
        'sid': "CHAR(6)",
        'value': 'FLOAT'
    },
    update_method='dates'
)
def dates_test_table(date):
    """
    本函数用于进行逐日进行类更新,函数参数应当为date

    其data_config中的字段update_method应当定义为dates，代表其每日计算当日数据并计算更新数据的方式
    """
    data = pd.DataFrame({
        'date': [date] * 3,
        'sid': ['000001', '000002', '000003'],
        'value': [pd.Timestamp(date).day] * 3
    })
    return data 


# ------------------ range 数据更新实例 --------------------------

@data_config(
    status='update',
    table_name='range_test_table',
    data_structure={
        'date': "CHAR(8)",
        'sid': "CHAR(6)",
        'value': 'FLOAT'
    },
    update_method='range',
    index=['date', 'sid']
)
def range_test_table(start_date, end_date):
    """
    本函数用于进行逐日进行类更新,函数参数应当为start_date, end_date

    其data_config中的字段update_method应当定义为range，代表其每日计算当日数据并计算更新数据的方式
    """
    dates = pd.date_range(start_date, end_date)
    dates = [x.strftime("%Y%m%d") for x in dates]
    data = pd.DataFrame({
        'date': dates,
        'sid': ['000001'] * len(dates),
        'value': [2] * len(dates)
    })
    return data 


# if __name__ == '__main__':
#     print(dates_test_table('20100101'))
#     print(range_test_table('20100101', '20100105'))