"""
csv 数据检索/更新方法
"""

import os 

import numpy as np 
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
    path = os.path.join(conn, "{}.csv".format(data_config['table_name']))
    return os.path.exists(path)


def create_table(conn, data_config):
    """
    创建csv文件表
    """
    col = list(data_config['data_structure'].keys())
    pd.DataFrame(columns=col).to_csv(os.path.join(conn, "{}.csv".format(data_config['table_name'])), index=False)


def max_date(conn, data_config):
    """
    获取表中的最大日期
    当data_config中存在field字段时，将只在对应的field字段下进行检索
    """
    if 'field' in data_config:
        dt = pd.read_csv(os.path.join(conn, "{}.csv".format(data_config['table_name']))).query("field=='{}'".format(data_config['field']))['date'].tolist()
    else:
        dt = pd.read_csv(os.path.join(conn, "{}.csv".format(data_config['table_name'])))['date'].tolist()
    
    if len(dt) > 0:
        return max(dt)
    else:
        return None 


def list_date(conn, data_config):
    """
    获取表中所有存在的日期
    当data_config中存在field字段时，将只在对应的field字段下进行检索
    """
    dt = pd.read_csv(os.path.join(conn, "{}.csv".format(data_config['table_name'])))
    if "field" in data_config:
        dt = dt.query("field=='{}'".format(data_config['field']))
    dt = np.unique(dt['date'])
    dt = sorted(dt)
    return dt 


def update_data(data, conn, data_config):
    """
    数据更新
    """
    data = data.reindex(columns=data_config['data_structure'].keys())
    data.to_csv(os.path.join(conn, "{}.csv".format(data_config['table_name'])), mode='a', index=False, header=False)


