# @Time         : 17-7-5 下午10:01
# @Author       : DioMryang
# @File         : Query.py
# @Description  : Query查询
import itertools
import functools

from TestRequest.Query import QueryType


class QueryNode(object):
    """
    提供查询方法SoupGetter的查询规则

    Attitudes:
        queryString: 查询字符串
        queryDict: 查询参数
        queryWay: 查询方法
        nextQuery: 下一条查询规则
        tag: 标签
        unique: 是否为父节点的唯一子节点

    Methods:
        setNextQuery: 设置下条查询规则

        < property >
        nthQuery: 位置query

        < classmethod >
        buildQuery: 创建查询链

        < staticmethod >
        buildQueryNode: 创建查询链节点
    """
    def __init__(self, tagName, tag, soup, id_=None, clsDict=None, clsList=None, nth=None,
                 parentNode=None, unique=False):
        self.tag = tag
        self.soup = soup
        self.tagName = tagName

        self.id = id_
        self.clsDict = clsDict if isinstance(clsDict, dict) else {}
        self.clsList = clsList if isinstance(clsList, list) else []

        self.parentNode = parentNode
        self.nth = nth
        self.unique = unique

    def __str__(self):
        return "{}{}{}".format(self.tagName,  # 标签名
                               "#" + self.id if self.id is not None else "",  # id
                               "".join(["." + clsName for clsName in self.clsDict]))  # 类名

    def __repr__(self):
        return "{}{}{}".format(self.tagName,  # 标签名
                               "#" + self.id if self.id is not None else "",  # id
                               "".join(["." + clsName for clsName in self.clsDict]))  # 类名

    @property
    def nthQuery(self):
        return "{}:nth-of-type({})".format(self.tagName, self.nth)

    def setParentQuery(self, parentQuery):
        self.parentQuery = parentQuery

    def getQuery(self, limit=3):
        """
        获取提取规则
        :param limit: 查询规则数
        :return:
        """
        queryList = []
        # 获取直接get query
        queryList.extend(list(self.getIdQuery()))

        # 获取直接class
        queryList.extend(list(self.getClsQuerys()))

        # 该标签query
        baseQuery = self.tagName if self.unique else self.nthQuery

        # 获取
        curNode = self.parentNode
        while curNode is not None and len(queryList) < limit:
            # 查看是否可通过id，class抽取
            querys = list(curNode.getIdQuery()) + list(curNode.getClsQuerys())

            for query_ in querys:
                query_ = "{} > {}".format(query_, baseQuery)
                if self.checkQuery(query_):
                    queryList.append(query_)

            baseQuery = "{} > {}".format(curNode.tagName if curNode.unique else curNode.nthQuery, baseQuery)
            curNode = curNode.parentNode

        return queryList

    def getIdQuery(self):
        """
        获取id的抽取规则
        :param testQueryFn: 测试函数
        :param soup: 解析对象
        :return:
        """
        if self.id:
            yield self.checkQuery("#{}".format(self.id))

    def getClsQuerys(self):
        """
        获取单类抽取规则
        :return:
        """
        for cls_, count_ in self.clsDict.items():
            query = ".{}".format(cls_)
            if count_ == 1:
                if self.checkQuery(query):
                    yield query
            else:
                if self.parentNode and self.parentNode.checkQueryBySelf(query, self.tag):
                    yield query

    def checkQuery(self, query):
        """
        测试抽取规则
        :param query: 抽取规则
        :return:
        """
        res = self.soup.select(query)

        if len(res) == 1 and res[0] == self.tag:
            return query

    def checkQueryBySelf(self, query, tag):
        """
        通过标签测试抽取规则
        :param query:
        :return:
        """
        res = self.tag.select(query)
        if len(res) == 1 and res[0] == tag:
            return query

    @classmethod
    def buildQuery(cls, tag, rq, queryType=QueryType.queryOne):
        """
        创建查询链
        :param tag: 标签
        :param rq: 测试单元
        :param queryType: 抽取规则类型
        :return:
        """
        childQueryNode = cls.buildQueryNode(tag, rq)
        lastNode = childQueryNode

        # 循环设置父级节点
        while tag.parent:
            if tag.name in ["[document]", "html", "body"]:
                break

            node = cls.buildQueryNode(tag.parent, rq)
            lastNode.parentNode, lastNode = node, node

            tag = tag.parent

        return childQueryNode

    @staticmethod
    def buildQueryNode(tag, rq):
        """
        创建query节点
        :param tag: 标签
        :param soup: 解析器
        :param rq: 测试单元
        :return:
        """
        # 设置底层query
        tagArgs = {"tagName": tag.name, "tag": tag, "soup": rq.soup}
        tagArgs.update({"id_": None if "id" not in tag.attrs else tag.attrs["id"]})

        # 类计数
        clsDict = {}
        for cls_ in tag.attrs.get("class", []):
            if cls_ in rq.classCount:
                clsDict[cls_] = rq.classCount[cls_]
        tagArgs.update({"clsDict": clsDict})

        # 位置
        preTag, nextTag = tag.find_previous_siblings(tag.name), tag.find_next_siblings(tag.name)
        nth = len(preTag) + 1
        tagArgs.update({"nth": nth})

        # 是否为唯一子节点
        if not (preTag or nextTag):
            tagArgs.update({"unique": True})

        return QueryNode(**tagArgs)


if __name__ == '__main__':
    from TestRequest.request import rqUnit
    rqUnit.url = "http://stock.eastmoney.com/news/1406,20170921779372559.html"
    data = """今日沪指涨0.21% 非银金融行业涨幅最大"""
    tag_ = rqUnit.getTagByText(data)

    node = QueryNode.buildQuery(tag_, rqUnit)
    print(node.getQuery())