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
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like G"
                                      "ecko) Chrome/4.0.249.0 Safari/532.5 "}
        self.timeout = 20
        self.session = requests.Session()
        self.res = None
        self.soup = None
        self.tree = None
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

        self.tree = etree.HTML(self.res.text)
        self.__classCount = defaultdict(int)

        new = time.time()
        print("运行时间", str(new - old)[:3], "秒")

        self.__setClassCount()

    @property
    def request(self):
        return self.res

    @request.setter
    def request(self, value):
        old = time.time()
        self.res = self.session.get(value, headers=self.headers)

        new = time.time()
        print("运行时间", str(new - old)[:3], "秒")

    @property
    def classCount(self):
        if self.res is None:
            print("请设置请求url")
            return None
        return self.__classCount

    @property
    def __iterSoupDescendants(self):
        """
        迭代文档的所有子孙元素
        :param func: 元素处理方法
        :return:
        """
        return self.soup.descendants

    def select(self, query, attr=None):
        """
        列表查询方法
        :param query: 查询规则
        :param attr: 属性
        :return:
        """
        if self.soup is None:
            print("请设置请求url")
        if attr is None:
            return self.soup.select(query)
        return (tag[attr] for tag in self.soup.select(query))

    def select_one(self, query):
        """单查询列表"""
        if self.soup is None:
            print("请设置请求url")
        return self.soup.select_one(query)

    def testQueryString(self, queryString, tag):
        """
        测试查询规则
        :param queryString: 查询规则
        :param tag: 标签
        :return:
        """
        result = self.select_one(queryString)
        if result is tag:
            return True
        return False

    def getAllQueryStringByTag(self, tag):
        """
        获取所有的查询规则
        :param tag:
        :return:
        """
        baseQueryList = []

        if "id" in tag.attrs:
            queryString = "{}#{}".format(tag.name, tag.attrs["id"])
            baseQueryList.append(queryString)

        # class查询规则获取
        if "class" in tag.attrs:
            # 对类进行排列组合
            for _count in range_(len(tag.attrs["class"])):
                for items in itertools.combinations(tag.attrs["class"], _count):
                    baseQueryList.append("{}.{}".format(tag.name, ".".join(items)))

        # 获取位置查询规则
        previousAlikeTag, nextAlikeTag = tag.find_previous_siblings(tag.name), tag.find_next_siblings(tag.name)

        if not (previousAlikeTag and nextAlikeTag) and not baseQueryList:
            baseQueryList.append(tag.name)
        else:
            tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
            baseQueryList.append("{}:nth-of-type({})".format(tag.name, tagPosition))

        tag = tag.parent
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
                    # 对类进行排列组合
                    for _count in range_(len(tag.attrs["class"])):
                        for items in itertools.combinations(tag.attrs["class"], _count):
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

        for queryString in getNodeQueryStringByHash(tagQueryItemList, {}):
            for baseQueryString in baseQueryList:
                yield "{} {}".format(queryString, baseQueryString)

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

    def getFirstQueryStringByTag(self, tag):
        """
        传入Tag对象, 获取标签的最优查询规则
        :param tag: 查询的标签
        :param allQuery: 唯一性
        :param 是否获取所有queryString
        :return: 返回字符串
        """
        # 标签名, 查询规则列表
        queryTag = tag
        tag_name = tag.name
        baseQueryStringList = []

        # id查询规则
        if "id" in tag.attrs:
            queryString = "{}#{}".format(tag_name, tag.attrs["id"])
            # 判断查询规则是否成立
            if self.testQueryString(queryString, tag):
                return queryString

        # 类查询规则
        elif "class" in tag.attrs:
            classList = [cls_ for cls_ in tag.attrs["class"] if cls_]

            for count_ in range_(len(classList)):
                for items in itertools.combinations(classList, count_):
                    queryString = "{}.{}".format(tag.name, ".".join(items))
                    if self.testQueryString(queryString, tag):
                        return queryString

                    baseQueryStringList.append(queryString)

        # 判断是否为父节点的唯一标签节点
        previousAlikeTag, nextAlikeTag = tag.find_previous_siblings(tag.name), tag.find_next_siblings(tag.name)
        if not (previousAlikeTag and nextAlikeTag) and baseQueryStringList:
            baseQueryStringList.append(tag_name)
        else:
            # 相对位置获取节点queryString
            tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
            baseQueryStringList.append("{}:nth-of-type({})".format(tag.name, tagPosition))

        # 遍历父母获取queryString
        tag = tag.parent
        parentList = []

        while tag:
            itemList = []
            # 文档顶端判定
            if tag.name == "[document]":
                break

            if tag.name not in ["html", "body"]:
                # id查询规则
                if "id" in tag.attrs:
                    # 判断查询规则是否成立
                    itemList.append("{}#{}".format(tag_name, tag.attrs["id"]))

                # class查询规则获取
                if "class" in tag.attrs:
                    # 对类进行排列组合
                    for _count in range_(len(tag.attrs["class"])):
                        for items in itertools.combinations(tag.attrs["class"], _count):
                            itemList.append("{}.{}".format(tag.name, ".".join(items)))

                # 获取位置查询规则
                previousAlikeTag, nextAlikeTag = tag.find_previous_siblings(tag.name), tag.find_next_siblings(tag.name)

                if previousAlikeTag:
                    tagPosition = (len(previousAlikeTag) if previousAlikeTag is not None else 0) + 1
                    itemList.append("{}:nth-of-type({})".format(tag.name, tagPosition))

                if not (previousAlikeTag and nextAlikeTag) and not itemList:
                    itemList.append(tag.name)
            else:
                itemList = [tag.name]

            parentList.insert(0, itemList)
            tag = tag.parent

        for queryString in getNodeQueryStringByHash(parentList, {}):
            for baseQueryString in baseQueryStringList:
                query = "{} {}".format(queryString, baseQueryString)
                if self.testQueryString(query, queryTag):
                    return query

        return ""

    def getTagsByText(self, text, tagNum=3, underScore=60):
        """
        通过查询文本获得对应tag
        :param text: 文本
        :param tagNum: 获取可能性最大的前几个tag
        :param underScore: 获得相似tag的最低分
        :return:
        """
        resultTagPy = {}
        for tag in self.__iterSoupDescendants:
            if isinstance(tag, Tag):
                score = fuzz.ratio(tag.text, text)
                if score > underScore:
                    resultTagPy[tag] = score
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

        for tag in self.__iterSoupDescendants:
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
            yield self.select_one(queryString)

    def saveResContent(self, filePath):
        """
        保存请求
        :param filePath:
        :return:
        """
        with open(filePath, "wb") as file:
            file.write(self.res.content)

    def __setClassCount(self):
        """获得类计数"""
        for tag in self.select("[class]"):
            for cls_ in tag.attrs["class"]:
                self.__classCount[cls_] += 1


rqUnit = RequestUnits()

if __name__ == '__main__':
    rqUnit.url = "http://www.1kkk.com/"
    # _tag = rqUnit.getTagByText("原创精品")
    # for query in list(rqUnit.getAllQueryStringByTag(_tag)):
    #     # print(query)
    #     pass
