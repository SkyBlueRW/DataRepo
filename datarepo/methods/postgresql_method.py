"""
针对postgresql的数据检查/更新方法
"""
import pandas as pd 
import sqlalchemy as sa 

from io import StringIO


def check_connection(conn):
    """
    检查是否可以和存储方式正常连接

    若连接正常，则返回True
    若未能连接，则返回False
    """
    try:
        c = conn.raw_connection()
        c.close()
        return True 
    except:
        return False


def check_table_exist(conn, data_config):
    """
    检查表是否已经存在

    若已存在，则返回True
    反之，则返回False
    """
    all_tables = sa.inspect(conn).get_table_names()
    flag = data_config['table_name'] in all_tables 
    return flag


def create_table(conn, data_config):
    """
    创建表
    """
    # 创建表
    data_structure_txt = ["{} {}".format(x, data_config['data_structure'][x])
                          for x in data_config['data_structure']]
    data_structure_txt = ", ".join(data_structure_txt)
    sql = """
        CREATE TABLE IF NOT EXISTS {0} (
            {1}
        );
    """.format(data_config['table_name'], data_structure_txt)

    c = conn.raw_connection()
    cur = c.cursor()
    cur.execute(sql)
    
    # 创建index
    if "index" in data_config:
        sql2 = """
            CREATE INDEX IF NOT EXISTS {} ON {} ({});
        """.format("idx_{}_{}".format(data_config['table_name'], "_".join(data_config['index'])),
                    data_config['table_name'], ", ".join(data_config['index'])
        )
        cur.execute(sql2)

    c.commit()
    c.close()
    
def max_date(conn, data_config):
    """
    获取表中的最大日期
    当data_config中存在field字段时，将只在对应的field字段下进行检索
    """
    if "field" in data_config:
        dt = pd.read_sql("SELECT MAX(date) FROM {} WHERE field='{}'".format(
            data_config['table_name'], data_config['field']
        ), conn)
    else:
        dt = pd.read_sql("SELECT MAX(date) FROM {}".format(data_config['table_name']), conn)

    if len(dt) > 0:
        return dt.values[0][0]
    else:
        return None

def list_date(conn, data_config):
    """
    获取表中所有存在的日期
    当data_config中存在field字段时，将只在对应的field字段下进行检索
    """
    if "field" in data_config:
        dt = pd.read_sql("SELECT DISTINCT date FROM {} WHERE field='{}'".format(
            data_config['table_name'], data_config['field']
        ), conn)
    else:
        dt = pd.read_sql("SELECT DISTINCT date FROM {}".format(data_config['table_name']), conn)
    
    dt = dt['date'].tolist()
    return sorted(dt)


def update_data(data, conn, data_config):
    """
    数据更新，写入表中, 需要对齐顺序
    """
    output = StringIO()
    if "data_structure" in data_config:
        data = data.reindex(columns=data_config['data_structure'].keys())
    data.to_csv(output, sep='\x01', header=False, encoding='utf-8', index=False)
    output.seek(0)

    c = conn.raw_connection()
    cur = c.cursor()
    cur.copy_from(output, data_config['table_name'], sep='\x01', null='')
    c.commit()
    cur.close()
    c.close()



