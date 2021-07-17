"""
用于数据检查/更新的方法
"""

import datetime

import pandas as pd 

from . import sql_method
from . import postgresql_method
from . import csvfolder_method
from . import pickle_method
from . import csv_method


DICT = {
    'sql': sql_method,
    'postgresql': postgresql_method, 
    'csvfolder': csvfolder_method,
    'pickle': pickle_method,
    'csv': csv_method
}


def check_connection(conn, storage_type):
    """
    检查是否可以和存储方式正常连接

    若连接正常，则返回True
    若未能连接，则返回False
    """
    return DICT[storage_type].check_connection(conn) 

def check_table_exist(conn, data_config, storage_type):
    """
    检查表是否已经存在

    若已存在，则返回True
    反之，则返回False
    """
    return DICT[storage_type].check_table_exist(conn, data_config)


def create_table(conn, data_config, storage_type):
    """
    创建表
    """
    DICT[storage_type].create_table(conn, data_config)


def range_start_date(conn, data_config, storage_type):
    """
    找到range更新开始更新的日期

    Returns
    -------
    返回 YYYYmmdd的str日期
    """
    dt = DICT[storage_type].max_date(conn, data_config)
    if dt is None:
        return None
    else:
        dt = (pd.Timestamp(str(int(dt))) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        return dt 

def existing_date_list(conn, data_config, storage_type):
    """
    列出数据已有的日期

    """
    dt_list = DICT[storage_type].list_date(conn, data_config)
    dt_list = [str(x) for x in dt_list]
    dt_list = pd.to_datetime(dt_list)
    dt_list = [x.strftime("%Y%m%d") for x in dt_list]
    return dt_list 


def update_data(data, conn, data_config, storage_type):
    """
    数据更新写入
    """
    DICT[storage_type].update_data(data, conn, data_config)



