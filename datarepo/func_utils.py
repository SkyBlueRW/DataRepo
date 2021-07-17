"""
函数相关方法
"""

import types
import inspect 
import importlib
from functools import wraps, partial
from copy import deepcopy


def get_func(path):
    """
    以dictionary的形式获得 指定py文件中所有的function
    
    Parameters
    ---------
    path: str 
        指定的py文件路径
    """
    # 根据路径载入module
    spec = importlib.util.spec_from_file_location("temp_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    FUNC = inspect.getmembers(module, inspect.isfunction)
    FUNC = {x[0]: x[1] for x in FUNC}

    # 只保留有data_config属性的函数作为数据更新函数
    FUNC = {x: FUNC[x] for x in FUNC if hasattr(FUNC[x], 'data_config')}
    # 只保留当前状态为更新的
    FUNC = {x: FUNC[x] for x in FUNC if FUNC[x].data_config['status']=='update'}
    return FUNC


def gen_func_list(func, field_list, table_name, **params):
    """
    给定一个prototype的计算func: func(date, field, ....)
    将其复制并parse成
    {
        'field1': func(field='field1', **params),
        'field2': func(field='field2', **params),
                 ...
    }
    的形式
    """

    func_dict = dict()
    for x in field_list:
        _f = gen_curry_function(func)(field=x, **params)

        # 此处data_config的copy是有必要的，如不执行，不同的函数将会share同一个data_config
        # 从而导致无法正常的更新field值
        _f.data_config = deepcopy(_f.data_config)
        _f.data_config['field'] = x
        _f.data_config['table_name'] = table_name
        func_dict.update({x: _f})
        _f = None

    return func_dict 


class PositionalRebindNotAllowed(Exception):
    """
    positional的argument不应当被重新赋值
    """
    pass 


def gen_curry_function(func, exe_on_demand=False):
    """
    生成curried 类函数 (通过chained形式传入arguments), 可以实现函数参数的rebiding, 只有在通过chain argument的形式不足了函数运行的最低条件时才会运行

    def func(a,b,c,d='default): pass 
    gen_curry_function(func)(para1, para2)(para3)(d='test') => func(para1, para2, para3, 'test')
    gen_curry_function(func, True)(para1, para2)(para3)(d='test') => func(para1, para2, para3, 'test')()

    Parameters
    ---------
    func: func
        函数
    exe_on_demand: bool
        是否返回类似lazy形式需要再次调用才运行的对象

    Returns
    -------
    func object 或函数运行结果    
    """
    signature = signature_args(func)
    defaultargs = default_args(func)

    def _is_callable(elements):
        """Check we have available the minimum required arguments defined in'func'"""
        return sum(map(len, elements)) >= len(signature)

    @wraps(func)
    def f(*args, **kwargs):

        kwargs = {**defaultargs, **kwargs}

        if _is_callable([args, kwargs]) and not exe_on_demand:
            return func(*args, **kwargs if len(args) < len(signature) else {})

        @wraps(func)
        def g(*callargs, **callkwargs):

            args_to_kwargs = {k: v for k, v in zip(expected_args(func, kwargs), args + callargs)}

            newstate = {
                **kwargs,
                **args_to_kwargs,
                **callkwargs
            }

            if exe_on_demand and _is_callable([args, kwargs]) and len(callargs) > 0:
                raise PositionalRebindNotAllowed

            if any([
                not exe_on_demand and _is_callable([newstate]),
                exe_on_demand and sum(map(len, [callargs, callkwargs])) == 0 and _is_callable([newstate])
            ]):
                return func(**newstate)

            return f(**newstate)

        return g

    return f
            

def lazy(func):
    """
    用以赋予函数lazy特性的 decorator

    i.e:
    @lazy
    def f(a, b, c): return a+b+c
    r = f(1,2,3)
    r() # 6

    Returns
    ------
    函数的partial application
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return partial(func, *args, **kwargs)
    return wrapper


def signature_args(callable):
    """
    返回callable object的参数

    Returns
    -------
    list of str 
    """
    return list(inspect.signature(callable).parameters)


def default_args(func):
    """
    以dict的形式返回函数的default arguments

    Returns 
    -------
    dict
    """
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def expected_args(func, kwargs):
    """
    给定一个函数func以及dictionary of bounded arguments (kwargs), 按照位置顺序给出仍然缺失的参数名称

    Returns
    -------
    list of str 
    """
    return [a for a in signature_args(func) if a not in kwargs]


def is_lambda(obj):
    """
    判断是否是lambda 函数
    """
    return isinstance(obj, types.LambdaType) and obj.__name__ == '<lambda>'