# @Time         : 17-7-8 下午1:54
# @Author       : DioMryang
# @File         : UrlsRqQueryTest.py
# @Description  : 输入字典或列表,的测试query集合, urls测试集单元进行测试
import requests
import functools

from TestRequest.Common import WINDOWS_HEADERS, TIMEOUT
from TestRequest.Utils import getHtmlSoupBySession


class RqQueryTestUtil(object):
    """
    urls 单元 querys测试集

    Attributes:

        querySequence: 查询序列
            一种是二维列表: 不含特征唯度名称 [ ["html b", "html div b"], ["div p p", "div div.c p"] ]
            另一种是字典序列: 含有特征名的 序列 { "维度名": [query, query, query] }
        querySequenceType: 查询序列的类型, list 或者 dict

    Methods:
        testQueryByUrls: 测试查询规则

    """
    def __init__(self, querySequence, headers=WINDOWS_HEADERS, timeout=TIMEOUT):
        self.querySequence = querySequence
        self.querySequenceType = type(querySequence)

        self.__session = requests.Session()
        self.headers = headers
        self.timeout = timeout

    def testQueryByUrls(self, urls, headers=None, timeout=None):
        """
        测试urls
        :param urls: url集合
        :param headers: 请求头
        :param timeout: 超时
        :return: {"http://www.xxx.com": [["result", "result"], ["result", "result"], ["result", "result"]]} or
        {"http://www.xxx.com": {"name": ["result", "result"], "content": ["result", "result"]}}
        """

        getHtmlSoupBySession_ = functools.partial(getHtmlSoupBySession, **{"session": self.__session, "headers":
            self.headers if headers is None else headers, "timeout": self.timeout if timeout is None else timeout})
        results = {}
        for url in urls:
            soup = getHtmlSoupBySession_(url)

            # soup 处理相关, 修改位置
            if self.querySequenceType is list:
                result = []
                for queryList in self.querySequence:
                    result.append([self.testQueryBySoup(soup, query) for query in queryList])

            elif self.querySequenceType is dict:
                result = {}
                for featureName, queryList in self.querySequence.items():
                    result[url] = [self.testQueryBySoup(soup, query) for query in queryList]

            else:
                result = None
            results[url] = result
        return results

    def testQueryBySoup(self, soup, query):
        """
        从soup 获取数据
        :param soup:
        :param query:
        :return:
        """
        tag = soup.select_one(query)
        if tag:
            return tag.text
        else:
            return None
