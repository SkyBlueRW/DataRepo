"""
sql通用的快速数据检查/更新方法
"""

import pandas as pd 
import sqlalchemy as sa 

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
    data.to_sql(data_config['table_name'], conn, index=False, if_exists='append')


def clean_db_df_duplicate(df, table_name, egn, dup_cols, filter_date_col, filter_categorical_col=None, schema=None):
    """
    清理更新入数据库的数据, 将根据dup_cols来判断重复的数据record并从df中删去
    reference: https://www.ryanbaumann.com/blog/2016/4/30/python-pandas-tosql-only-insert-new-rows
    注: df中的filter_date_col最终被转换为了时间戳，按需求调整

    Parameters
    ---------
    df: pd.DataFrame
        数据， 无index
    table_name: str
        对应表名
    egn: sqlalchemy.engine.base.Engine
        连接数据库用的引擎
    dup_cols: list
        用于查重的列
    filter_date_col: str
        知名哪一列对应的为时间戳。从数据库中读取数据时只读取对应的时间戳区间的
    filter_categorical_col: str, 可选
        以 in ()的形式限制需要从数据库中取得的数据量

    Returns
    -------
    df: pd.DataFrame
        不含与数据库中重复的dataframe

    """
    table_name_f = table_name if schema is None else "{}.{}".format(schema, table_name)
    # 将日期列的格式变换为日期
    df[filter_date_col] = pd.to_datetime(df[filter_date_col])
    qry = 'SELECT {0} FROM {1}'.format(', '.join('"{0}"'.format(w) for w in dup_cols),
                                       table_name_f)

    qry_date = "{0} BETWEEN '{1}' AND '{2}'".format(filter_date_col,
                                                    df[filter_date_col].min().strftime("%Y%m%d"),
                                                    df[filter_date_col].max().strftime("%Y%m%d"))
    qry_categorical = None
    if filter_categorical_col is not None:
        qry_categorical = '{0} IN {1}'.format(filter_categorical_col,
                                              str(tuple(df[filter_categorical_col].unique().tolist())).replace(',)', ')'))

    qry += ' WHERE ' + qry_date
    if qry_categorical:
        qry = qry + qry_categorical

    df.drop_duplicates(dup_cols, keep='last', inplace=True)
    df = pd.merge(df, pd.read_sql(qry, egn, parse_dates=[filter_date_col]),
                  how='left', on=dup_cols, indicator=True)
    df = df.query("_merge == 'left_only'")\
           .drop(['_merge'], axis='columns')

    return df  