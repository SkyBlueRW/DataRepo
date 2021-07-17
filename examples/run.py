import sys 
if "/home/ray/src/DataRepo" not in sys.path:
    sys.path.append("/home/ray/src/DataRepo")
import logging
from datarepo import handler
from sqlalchemy import create_engine
from datarepo import DataUpdate



# ---------------------------- logger定义 ------------------------
stream_handler = handler()
# file_handler = handler(log_file_destination_path)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(stream_handler)
# root_logger.addHandler(file_handler)


# -----------------------------  参数 ----------------------------
TRADE_DT = ['20110101', '20110102', '20110103', '20110104', '20110105']     # 代表dates更新需要保有的所有日期， 会更新对应数据表中所缺失的日期
END_DATE = '20100106'                                                       # 代表range更新的最新日期
conn = create_engine("postgresql://****:****@localhost:5432/stock_daily")  # 数据存储链接


# ----------------------------- 数据更新 --------------------------
# 声明数据计算函数所在的脚本，数据存储方式，数据存储链接方式，数据基期(数据创建后数据开始更新日期，只应用于range更新方式)
update_instance = DataUpdate.from_file_path(path="./data_function.py", storage_type="sql", conn=conn, base_date='20100101')
# 更新所有range方式的数据
update_instance.range_update_all(end_date=END_DATE)
# 更新交易日更新的数据
update_instance.dates_update_all(date_list=TRADE_DT)
