# @Time         : 17-7-5 下午9:04
# @Author       : DioMryang
# @File         : __init__.py
# @Description  : 查询规则

from enum import Enum, unique


@unique
class QueryType(Enum):
    """查询类型的枚举类"""
    queryOne = 0
    queryList = 1
    findOne = 2
    findMany = 3
    reMatch = 4
    reSearch = 5
    xpathOne = 6
    xpathList = 7
