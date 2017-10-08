# @Time         : 17-7-5 下午10:03
# @Author       : DioMryang
# @File         : SoupGetter.py
# @Description  :
import re

from TestRequest.Query.Query import QueryType


class SoupGetter(object):
    """
    根据Query对象来查询获取数据

    Attitudes:
        rqUnit: 请求单元


    """
    def __init__(self, rqUnit):
        self.rqUnit = rqUnit

    def select(self, query):
        """
        查询方法
        :param query: Query对象
        :return:
        """





