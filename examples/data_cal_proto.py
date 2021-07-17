"""

"""

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