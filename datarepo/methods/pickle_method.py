"""
基于pickle的数据检查/更新方法
"""

import os 
import pickle

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
    path = os.path.join(conn, data_config['table_name']+".pic")
    return os.path.exists(path)


def create_table(conn, data_config):
    """
    创建表
    """
    path = os.path.join(conn, data_config['table_name']+".pic")
    if not os.path.exists(path):
        dat = pd.DataFrame(columns=data_config['data_structure'].keys())
        with open(path, 'wb') as f:
            pickle.dump(dat, f)


def max_date(conn, data_config):
    """
    找出当前已有的最大日期
    """
    path = os.path.join(conn, data_config['table_name']+".pic")
    
    content = None
    with open(path, 'rb') as f:
        content = pickle.load(f)
    if "field" in data_config:
        content = content.loc[content['field'] == data_config['field']]
    
    if len(content) > 0:
        return content['date'].max()
    else:
        return None 


def list_date(conn, data_config):
    """
    列出所有已有的日期
    """
    path = os.path.join(conn, data_config['table_name']+".pic")
    
    content = None
    with open(path, 'rb') as f:
        content = pickle.load(f)
    if "field" in data_config:
        content = content.loc[content['field'] == data_config['field']]
    
    dt = content['date'].unique()
    return sorted(dt)


def update_data(data, conn, data_config):
    """
    更新数据，写入表中
    """
    path = os.path.join(conn, data_config['table_name']+".pic")

    content = None
    with open(path, 'rb') as f:
        content = pickle.load(f)

    content = content.append(data)
    os.remove(path)

    with open(path, 'wb') as f:
        pickle.dump(content, f)

