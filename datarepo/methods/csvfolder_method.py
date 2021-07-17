"""
csvfolder 数据检索/更新方法
需要注意的是csvfolder并不支持field字段进行字段内检索
"""

import os 
import pandas as pd 


def check_connection(conn):
    """
    检查数据连接是否存在
    """
    return os.path.exists(conn)

def check_table_exist(conn, data_config):
    """
    检查表是否存在
    """
    path = os.path.join(conn, data_config['table_name'])
    return os.path.exists(path)

def create_table(conn, data_config):
    """
    创建表
    """
    path = os.path.join(conn, data_config['table_name'])
    if not os.path.exists(path):
        os.mkdir(path)

def max_date(conn, data_config):
    """
    找出当前已有的最大日期
    """
    path = os.path.join(conn, data_config['table_name'])
    dt_list = os.listdir(path)
    dt_list = [x.split('.')[0] for x in dt_list]
    if len(dt_list) > 0:
        return max(dt_list)
    else:
        return None

def list_date(conn, data_config):
    """
    列出当前已有的所有日期
    """
    path = os.path.join(conn, data_config['table_name'])
    dt_list = os.listdir(path)
    dt_list = [x.split('.')[0] for x in dt_list]
    return sorted(dt_list)


def update_data(data, conn, data_config):
    """
    更新数据存储为每日一个csv文件的形式
    """
    path = os.path.join(conn, data_config['table_name'])

    data['date'] = pd.to_datetime(data['date'].astype(str))
    data['date'] = data.date.dt.strftime("%Y%m%d")
    all_dt = data['date'].unique()
    for i in all_dt:
        data.loc[data['date'] == i].drop(['date'], axis=1).to_csv(os.path.join(path, "{}.csv".format(i)), index=False)


