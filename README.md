# Data Repo

A data update pipeline that can be used for on-going and historical calculation given a python script.

## Data Update Function:
> The functionality of data update centers around the class **core.DataUpdate**. The logic of the functionality is as follows
>     1. Given a dictionary of data calculation function (it can be anything from portfolio construction, signal calculation, performance evaluation etc..) defined in python scripts.
>     2. Check the availability of corresponding data in the data store and figure out periods of calculation for each calculation function as per the update method
>     3. Conduct the calculation for missing bit and store in the data store
>
> Any intermediary steps including the creation of data store, the search of data to be updated, update, logging can be automatically via configurations of the set. The configuration for each calculation function is passsed via the data_config decorator.
>
> 
> 借助**from_file_path**的类初始化方式，DataUpdate类可以实现，更新指定py脚本(full path)中所有状态为update的函数，从而实现数据计算函数与更新模块的独立。
    > 参见examples中的例子
    > 1. 在py文件(data_function.py)中定义各数据的数据计算函数，并通过data_config decorator的方式定义该数据的基础属性(包括哪些字段，使用何种方式进行更新等)
    > 2. 在数据更新文件(run.py)中定义logger，数据库连接等，运行数据进行数据更新

> 借助**indicator_from_func**的类初始化方式，DataUpdate类可以实现，根据prototype数据计算函数，通过改变特定参数以获得dict of 数据计算函数的方法。当下该方法用于信号表现的计算更新(不同信号表现只需要更改信号名称作为)
    > 参见examples中的例子
    > 1. 定义用于信号指标的计算方法，其应当接受field作为字段，用于对多个信号进行同样的信号表现计算(在data_cal_proto.py中实现)。
    > 2. 在数据更新文件(proto_run.py)中定义Logger，借助indicator_from_func函数进行多个信号表现的计算



## data_config
> 使用decorator的形式来记录数据的属性
1. data_name
    必须，定义该数据对应的表名称
2. status
    必须， update, not_update,该数据是否用于更新
3. data_structure
    必须，声明计算所得数据的数据结构，被用于创建表，格式应当类似, 需要注意的是后边应当对应sql中的数据格式以确保表创建无误
    ```python{
        'date': 'CHAR(8)',
        'field': 'TEXT',
        'ic': 'FLOAT'
    }
    ```
4. index
    可选，适用于数据以sql表的形式存储，当声明index(list of str)时，将会根据提供的list在创建表时创建对应的index
5. field
    可选，保留字段，当提供field(str)时, 数据的更新将会在field==field的约束下进行更新，通常用于多个数据更新函数对应同一表的情况。比如
    针对多个股票池计算函数: broad, broader, hs300, zz500。将计算结果存储在同一表中这种应用情况。


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








