"""
logger 相关设置
"""

import logging 

formatter = logging.Formatter('%(levelname)s | %(asctime)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                             #  信息层级 |  发生时间 | 信息


def handler(path=None, level=logging.INFO, fmt=formatter):
    """
    返回设置好的file handler

    Parameters
    ----------
    path: str, optional
        当提供地址时，返回file handler
        当不提供地址时，返回stream handler
    level: 
        logging level: logging.INFO, logging.DEBUG, ... etc
    fmt: str
        信息格式
    """
    if path is not None:
        h = logging.FileHandler(path)
    else:
        h = logging.StreamHandler()
    h.setLevel(level)
    h.setFormatter(fmt)

    return h