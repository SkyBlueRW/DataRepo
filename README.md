# Data Repo

A data update pipeline that can be used for on-going and historical calculation given a python script.

## Data Update Function:
The functionality of data update centers around the class **core.DataUpdate**. The logic of the functionality is as follows
- Given a dictionary of data calculation function (it can be anything from portfolio construction, signal calculation, performance evaluation etc..) defined in python scripts.
- Check the availability of corresponding data in the data store and figure out periods of calculation for each calculation function as per the update method
- Conduct the calculation for missing bit and store in the data store

Any intermediary steps including the creation of data store, the search of data to be updated, update, logging can be automatically handled via configurations of the set. The configuration for each calculation function is passsed via the data_config decorator.


DataUpdate class can be initiated via the following static method
- **from_file_path** - initiate a DataUpdate instance to update all functions in a given python files with status of 'update'. The method helps to isolate the calculation function from data update module
    -  Refer to examples
    - calculation functions are defined in a py file (data_function.py). Calculation configuration is defined via the decorator of each function (fields of the data set, ways of update, frequencies of update ...)
    - define logger and execute the data update (run.py)

- **indicator_from_func** - initiate a DataUpdate prototypes to apply the same calculation on various datasets (I.E. calculate the alpha signal performance for all signals)
    - Refer to examples
    - The calculation of indicator takes fields as input and can be used for the same calculation on different data sets (implemented in data_cal_proto.py)
    - Logger is defined in data update file (proto_run.oy)



## data_config
> Configuration about the data update is defined in the decorator of calculation function
1. data_name
    mandatory, refers to corresponding data store (where)   
2. status
    mandatory: update/not_update refers to if it is actively updated (if)
3. data_structure
    mandatory: data structure of corresponding data. Data store will also be created accordingly as per the definition
    ```python{
        'date': 'CHAR(8)',
        'field': 'TEXT',
        'ic': 'FLOAT'
    }
    ```
4. index
    optional, for data store of SQL type, when the index (list of str) is declared, corresponding index will be created on the SQL table
5. field
    optional, reserved word, when field(str) is supplied, data update will proceed under the restriction of field==field value. It is used for the prototype update. I.E update alpha signal performance for different variables within different universes.


## 常用使用方式
1. 通过decorator的形式定义数据的类型与形式
```python
from datarepo import data_config

@data_config(
    status='update',
    table_name='sigperf',
    data_structure={
        'date': 'CHAR(8)',
        'field': 'TEXT',
        'ic': 'FLOAT'
    },
    update_method='dates'
)
def sigperf(date, field, ret):
    """
    此处可声明除date之外的其他参数，借助lazy function的方式进行传入
    """
    signal = get_signal(signal_name=field, date=date)
    perf = cal_ic(signal, ret)
    return perf 
```
    - 对应的数据表名称为sigperf
    - 数据的结构以data_structure形式声明

2. 在定义了数据的计算方式与结构后在数据更新文件中进行更新
```python
import logging
from datarepo import handler, DataUpdate

# loger设置
stream_handler = handler()
file_handler = handler(log_file_destination_path)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)

# 参数 
TRADE_DT = ['20110101', '20110102', '20110103', '20110104','20110105']     # 代表dates更新需要保有的所有日期， 会更新对应数据表中所缺失的日期
END_DATE = '20100106'    # 代表range更新的最新日期
conn = create_engine("postgresql://****:****@localhost:5432/stock_daily")  # 数据存储链接


#  数据更新 
# 声明数据计算函数所在的脚本，数据存储方式，数据存储链接方式，数据基期(数据创建后数据开始更新日期，只应用于range更新方式)
update_instance = DataUpdate.from_file_path(path="./data_function.py", storage_type="sql", conn=conn, base_date='20100101')
# 更新所有range方式的数据
update_instance.range_update_all(end_date=END_DATE)
# 更新交易日更新的数据
update_instance.dates_update_all(date_list=TRADE_DT)
```



## 更新方式
> 当前api支持**4种格式的数据存储方式**:
    > - sql: 以数据库表为数据存储单元
    > - postgresql: 类似sql，区别在于使用了针对postgresql的一些增添效率的api function
    > - pickle: 以pickle文件(pd.DataFrame数据结构)为数据存储单元
    > - csvfolder: 以folder为数据存储单元，单元中的文件为YYYYMMDD.csv的方式命名
    > - csv: 以csv文件为数据存储单元
> 以及**2种数据更新方式**:
    > - range: 找到数据最新的日期，从下一日开始更新一段range的数据
    > - dates: 给定一个date_list, 查看数据库中缺失的日期计算并更新


## 未来更新
> sql的update方法。dataframe.to_sql在很多应用场景下数据上传速度异常慢，其原因在于df中的数据类型与sql中的数据类型不一致。在上传过程中出现了硬转变。当下的数据更新依赖于使用者在构建数据更新函数的时候自行解决。未来可能增加数据格式检查与转变的方式。

> 多数据目标的更新方式。当下的数据更新逻辑依赖于每一数据计算函数对应以数据表，进行独立的检查与更新。未来预期增加同一更新流程针对多个数据更新的目标的形式。一个标准的使用场景为组合的监控。应当根据目标组合等规则用于判断是否应当更新，并且更新的数据结果为多种不同类型的数据(当下股票持仓，组合净值，当日发生的交易等等等。)，这依赖于多个函数之间的dependent先后关系的判断。








