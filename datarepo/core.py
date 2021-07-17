"""
数据更新核心
"""

import logging 

import pandas as pd 

from .methods import methods
from .func_utils import get_func, gen_func_list


module_logger = logging.getLogger(__name__)



def data_config(status, table_name, data_structure, update_method, **kwargs):
    """
    定义数据属性用decorator

    Parameters
    ----------
    table_name: str 
        数据更新目标表名
    data_structure: dict
        生成数据的结构
    update_method: str 
        数据更新的方法

    可在kwargs中增添其他的数据更新特性
    可能的特性:
        field: 表中的信号或代码等名称，以便于逐个更新
    """
    def wrapper(f):
        f.data_config = dict()
        f.data_config.update({'status': status})
        f.data_config.update({'table_name': table_name})
        f.data_config.update({'update_method': update_method})
        f.data_config.update({'data_structure': data_structure})
        for i in kwargs:
            f.data_config.update({i: kwargs[i]})
        return f 
    return wrapper


class DataUpdate:
    """
    用于数据更新的基类
    """
    def __init__(self, func_dict, storage_type, conn, base_date='20080101'):
        """
        初始化

        Parameters
        ----------
        func_dict: dict of function
            一系列使用data_config作为decorator的数据计算方法
        storage_type:
            数据存储方式, sql, csvfolder, pickle
        conn: str / sqlalchemy.engine
            用于连接数据库的方式 
        """
        assert methods.check_connection(conn, storage_type), "未能成功连接服务器"
        assert storage_type in ('sql', "postgresql", 'pickle', 'csvfolder', 'csv'), "不支持的存储方式"
        self.func_dict = func_dict
        self.storage_type = storage_type
        self.conn = conn 
        self.base_date = base_date

    @classmethod
    def from_file_path(cls, path, storage_type, conn, base_date='20080101'):
        """
        根据path读取某一指定py文件中的数据更新函数并实例化 DataUpdate
        """
        FUNC = get_func(path)
        return cls(FUNC, storage_type, conn, base_date)

    @classmethod
    def indicator_from_func(cls, func, storage_type, conn, field_list, table_name, base_date='20080101', **kwargs):
        """
        根据某一prototype function对field延展成一个function dictionary, 
        每个元素function有不同的field

        kwargs通常用于计算函数多余需要的参数与数据
        """
        FUNC = gen_func_list(func, field_list, table_name,**kwargs)
        return cls(FUNC, storage_type, conn, base_date)


    def update(self, func, **kwargs):
        """
        数据更新
        """
        # 若表不存在，则创建表
        if not methods.check_table_exist(self.conn, func.data_config, self.storage_type):
            try:
                methods.create_table(self.conn, func.data_config, self.storage_type)
                module_logger.info("表{}创建成功".format(func.data_config['table_name']))
            except Exception as e:
                module_logger.error("表{}创建失败: {}".format(func.data_config['table_name'], e), exc_info=True)
        
        update_method = func.data_config['update_method']

        # 根据更新方法获取当前数据情况并计算待更新的数据
        if update_method == 'range':
            self.range_update(func, end_date=kwargs['end_date'])
        elif update_method == 'dates':
            self.dates_update(func, date_list=kwargs['date_list'])
        else:
            module_logger.error("不存在的update_method: {}".format(update_method))
            
    def range_update(self, func, end_date):
        """
        计算一段时间内的数据并更新
        """
        # 检索需要更新的时间范围
        start_date = methods.range_start_date(self.conn, func.data_config, self.storage_type)
        if start_date is None:
            start_date = self.base_date
        end_date = pd.Timestamp(end_date).strftime("%Y%m%d")

        label = func.data_config['table_name'] if "field" not in func.data_config \
            else "{}@{}".format(func.data_config['field'], func.data_config['table_name'])

        # 若更新开始时间在更新结束时间之后，则不必进行计算
        if start_date > end_date:
            module_logger.info("{} :已更新至{},无需更新".format(label, start_date))
        else:
            # 数据计算
            try:
                data = func(start_date=start_date, end_date=end_date)
                module_logger.debug("{} {} ~ {}数据计算成功".format(label, start_date, end_date))
            # 计算失败
            except Exception as e:
                module_logger.error("{} {} ~ {}数据计算错误: {}".format(label, start_date, end_date, e), exc_info=True)
            # 计算成功
            else:
                # 如有新数据
                if len(data) > 0:
                    # 数据更新
                    try:
                        methods.update_data(data, self.conn, func.data_config, self.storage_type)
                        module_logger.info("{} 数据更新成功, {} ~ {} 共 {} 条记录".format(
                            label, start_date, end_date, len(data)
                        ))
                    except Exception as e:
                        module_logger.error("{} {} ~ {}数据更新错误: {}".format(label, start_date, end_date, e), exc_info=True)
                # 如果没有新数据
                else:
                    module_logger.info("{} {}~{}未更新，计算结果得到0条记录".format(label, start_date, end_date))

    def dates_update(self, func, date_list):
        """
        逐日计算数据并更新
        """
        # 检索需要更新的日期
        existing = methods.existing_date_list(self.conn, func.data_config, self.storage_type)
        date_list = pd.to_datetime(date_list)
        date_list = [x.strftime("%Y%m%d") for x in date_list]
        update_list = [x for x in date_list if x not in existing]

        label = func.data_config['table_name'] if "field" not in func.data_config \
            else "{}@{}".format(func.data_config['field'], func.data_config['table_name'])

        # 若没有需要更新的日期，则不进行计算
        if len(update_list) == 0:
            module_logger.info("{} 无需更新".format(label))
        
        else:
            for dt in update_list:
                # 数据计算
                try:
                    data = func(date=dt)
                    module_logger.debug("{} {}数据计算成功".format(label, dt))
                except Exception as e:
                    module_logger.error("{} 数据计算错误, {}: {}".format(label, dt, e), exc_info=True)
                else: 
                    # 如有新数据
                    if len(data) > 0:
                        # 数据更新
                        try:
                            methods.update_data(data, self.conn, func.data_config, self.storage_type)
                            module_logger.info("{} 数据更新成功, {} 共 {} 条记录".format(
                                label, dt, len(data)
                            ))
                        except Exception as e:
                            module_logger.error("{} 数据更新错误, {}: {}".format(label, dt, e), exc_info=True)
                    # 如果没有新数据
                    else:
                        module_logger.info("{} {}未更新，计算结果得到0条记录".format(label, dt))

    def range_update_all(self, end_date):
        """
        更新所有range类数据至end_date

        Parameters
        ----------
        end_date: str 
            更新到的日期
        """
        for x in self.func_dict:
            if self.func_dict[x].data_config['update_method'] == 'range':
                self.update(func=self.func_dict[x], end_date=end_date)

    def dates_update_all(self, date_list, frequency=None):
        """
        更新驻日更新的数据

        Parameters
        ---------
        date_list: list of str 
            [YYYYmmdd]
        frequency: str, optional
            更新频率，对应data_config中的frequency, 用于标识
        """
        for x in self.func_dict:
            if self.func_dict[x].data_config['update_method'] == 'dates':
                self.update(func=self.func_dict[x], date_list=date_list)


