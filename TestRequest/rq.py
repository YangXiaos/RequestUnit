# @Time         : 17-7-7 下午6:56
# @Author       : DioMryang
# @File         : rq.py
# @Description  :
# @Time         : 17-6-27 下午2:41
# @Author       : DioMryang
# @File         : request.py
# @Description  : 构建获取查询规则的爬虫测试单元
import time
import chardet
import requests
import threading
import functools
import itertools
from collections import defaultdict
from operator import itemgetter

from lxml import etree
from bs4 import BeautifulSoup
from bs4.element import Tag
from fuzzywuzzy import fuzz


from TestRequest.Utils import range_, getNodeQueryStringByHash

__all__ = ["requestUnit"]


class RequestUnits(object):
    """请求测试单元
    Attributes:
        headers: 当前请求头
        timeout: 超时设置
        session: 请求会话
        res: 当前响应结果

        __classCount: 类计数
    Methods:
        <property>
        url: 获得当前响应
    """
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
        self.timeout = 20
        self.session = requests.Session()
        self.res = None
        self.soup = None
        self.__classCount = defaultdict(int)

    @property
    def url(self):
        return self.res.url

    @property
    def html(self):
        """返回html页面"""
        return self.res.text

    @url.setter
    def url(self, value):
        """
        请求url
        :param value: url
        :return:
        """
        old = time.time()
        self.res = self.session.get(value, headers=self.headers)
        self.res.encoding = chardet.detect(self.res.content)["encoding"]
        self.soup = BeautifulSoup(self.res.content, "lxml")
        self.__classCount = defaultdict(int)

        new = time.time()
        print("运行时间", str(new - old)[:3], "秒")

        self.setClassCount()

    @property
    def classCount(self):
        if self.res is None:
            print("请设置请求url")
            return None
        return self.__classCount

    def query(self, query):
        """
        列表查询方法
        :param query: 查询规则
        :return:
        """
        if self.soup is None:
            print("请设置请求url")
        return self.soup.select(query)

    def queryOne(self, query):
        """单查询列表"""
        if self.soup is None:
            print("请设置请求url")
        return self.soup.select_one(query)

    def setClassCount(self):
        """获得类计数"""
        for tag in self.query("[class]"):
            for cls_ in tag.attrs["class"]:
                self.__classCount[cls_] += 1

    def __iterSoupDescendants(self):
        """
        迭代文档的所有子孙元素
        :param func: 元素处理方法
        :return:
        """
        for tag in self.soup.descendants:
            yield tag

    def testQueryString(self, queryString, tag):
        """
        测试查询规则
        :param queryString: 查询规则
        :param tag: 标签
        :return:
        """
        result = self.query(queryString)
        print(result, queryString)
        if len(result) == 1 and result[0] is tag:
            return True
        return False

    def getAllQueryStringByTag(self, tag):
        """
        获取所有的查询规则
        :param tag:
        :return:
        """
        tagQueryItemList = []

        while tag:
            itemList = []
            # 文档顶端判定
            if tag.name == "[document]":
                break

            if tag.name not in ["html", "body"]:
                # id查询规则
                if "id" in tag.attrs:
                    queryString = "{}#{}".format(tag.name, tag.attrs["id"])
                    itemList.append(queryString)

                # class查询规则获取
                if "class" in tag.attrs:
                    queryUniqueClass = [cls_ for cls_ in tag.attrs["class"]
                                        if cls_ in self.__classCount and self.__classCount[cls_] == 1]

                    # 对类进行排列组合
                    for _count in range_(len(queryUniqueClass)):
                        for items in itertools.combinations(queryUniqueClass, _count):
                            itemList.append("{}.{}".format(tag.name, ".".join(items)))

                # 获取位置查询规则
                previousAlikeTag = tag.find_previous_siblings(tag.name)
                nextAlikeTag = tag.find_next_siblings(tag.name)

                if not (previousAlikeTag and nextAlikeTag) and not itemList:
                    itemList.append(tag.name)
                else:
                    tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
                    itemList.append("{}:nth-of-type({})".format(tag.name, tagPosition))

            else:
                itemList = [tag.name]

            tagQueryItemList.insert(0, itemList)
            tag = tag.parent

        print(tagQueryItemList)
        for queryString in getNodeQueryStringByHash(tagQueryItemList, {}):
            yield queryString

    def openHtmlFile(self, file_path="data/temp.html"):
        """
        通过文件解析html
        :param file_path: 文件路径
        :return:
        """
        with open(file_path, "rb") as file:
            content = file.read()
        print(chardet.detect(content)["encoding"])
        text = content.decode(chardet.detect(content)["encoding"], errors="ignore")
        self.soup = BeautifulSoup(text, "lxml")

    def getQueryStringByTag(self, tag, allQuery=False):
        """
        传入Tag对象, 获取标签的最优查询规则
        :param tag: 查询的标签
        :param allQuery: 唯一性
        :param 是否获取所有queryString
        :return: 返回字符串
        """
        # 标签名, 查询规则列表
        tag_name = tag.name
        queryStringList = []

        # id查询规则
        if "id" in tag.attrs:
            queryString = "{}#{}".format(tag_name, tag.attrs["id"])

            # 判断查询规则是否成立
            if self.queryOne(queryString) is tag:
                if allQuery:
                    queryStringList.append(queryString)
                else:
                    return queryString

        # 类查询规则
        elif "class" in tag.attrs:
            queryUniqueClass = [cls_ for cls_ in tag.attrs["class"]
                                if cls_ in self.__classCount and self.__classCount[cls_] == 1]

            for cls_ in queryUniqueClass:
                queryString = "{}.{}".format(tag_name, cls_)

                if self.queryOne(queryString) is tag :
                    if allQuery:
                        queryStringList.append(queryString)
                    else:
                        return queryString

        # 遍历父母获取queryString
        # 相对位置获取节点queryString
        previousAlikeTag = tag.find_previous_siblings(tag.name)
        tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
        queryString = "{}:nth-of-type({})".format(tag.name, tagPosition)
        iterTag = tag.parent

        while iterTag.parent:
            # 获取节点相对父节点位置
            # 相对位置获取节点queryString
            previousAlikeTag = iterTag.find_previous_siblings(iterTag.name)
            tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
            queryString = "{}:nth-of-type({}) > ".format(iterTag.name, tagPosition) + queryString
            iterTag = iterTag.parent

        if self.queryOne(queryString) is tag:
            if not allQuery:
                return queryString
            queryStringList.append(queryString)
        return queryStringList

    def getTagsByText(self, text, tagNum=1, underScore=60):
        """
        通过查询文本获得对应tag
        :param text: 文本
        :param tagNum: 获取可能性最大的前几个tag
        :param underScore: 获得相似tag的最低分
        :return:
        """
        resultTagPy = {}

        def setTagPy(tag):
            if isinstance(tag, Tag):
                score = fuzz.ratio(tag.text, text)
                if score > underScore:
                    resultTagPy[tag] = score

        self.__iterSoupDescendants(setTagPy)
        sortedResult = sorted(resultTagPy.items(), key=itemgetter(1), reverse=True)

        if len(sortedResult)>tagNum:
            return [x for x, y in sortedResult[:tagNum]]

        return [x for x, y in sortedResult]

    def getTagByText(self, text, underScore=60):
        """
        根据文本, 获取可能性最大的Tag对象
        :param text: 文本
        :param underScore: 获取的底线分数
        :return:
        """
        resultTagPy = {}

        for tag in self.__iterSoupDescendants():
            if isinstance(tag, Tag):
                score = fuzz.ratio(tag.text, text)
                if score > underScore:
                    resultTagPy[tag] = score

        sortedResult = sorted(resultTagPy.items(), key=itemgetter(1), reverse=True)
        return sortedResult[0][0] if sortedResult else None

    def getQueryStringList(self, textList, queryStringNum=1):
        """
        输入文本列表, 输出对应内容的查询queryString
        :param textList: 内容列表
        :return:
        """
        queryStringList = []

        for text in textList:
            tag = self.getTagByText(text)

            if tag is not None:
                queryString = self.getQueryStringByTag(tag)
                queryStringList.append(queryString if queryString else None)
            else:
                queryStringList.append(None)

        return queryStringList

    def queryOneByQueryList(self, queryList):
        """
        根据列表的查询规则返回tag对象
        :param queryList: 列表的查询字符串
        :return:
        """
        for queryString in queryList:
            yield self.queryOne(queryString)


rqUnit = RequestUnits()

if __name__ == '__main__':
    pass
