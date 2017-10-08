# @Time         : 17-7-7 下午6:20
# @Author       : DioMryang
# @File         : QueryFunction.py
# @Description  :
import itertools


def range_(i, n=None, h=None):
    # 单个参数
    if n is None and h is None:
        return range(1, i+1)
    args_list = [i]
    if n is not None:
        args_list.append(n+1)
    if h is not None:
        args_list.append(h)
    return range(*args_list)


def getNodeQueryStringByHash(queryNodeLists, hash_):
    """
    获取节点向下的queryString
    :param queryNodeLists: 二维向下的结点列表
    :param hash_: 缓存哈希
    :return:
    """

    if str(queryNodeLists) in hash_:
        return hash_[str(queryNodeLists)]

    if len(queryNodeLists) == 1:
        hash_[str(queryNodeLists)] = queryNodeLists[0]
        return queryNodeLists[0]

    else:
        result = []

        # 第一行列表
        firstQueryNodeList, otherQueryNodeLists = queryNodeLists[0], queryNodeLists[1:]

        for firstQueryNode in firstQueryNodeList:
            for count_ in range_(len(otherQueryNodeLists)):
                for queryNodeLists_ in itertools.combinations(otherQueryNodeLists, count_):
                    for queryString_ in getNodeQueryStringByHash(queryNodeLists_, hash_):
                        nodeQueryString_ = "{} {}".format(firstQueryNode, queryString_)
                        if nodeQueryString_ not in result:
                            result.append(nodeQueryString_)
                        if queryString_ not in result:
                            result.append(queryString_)

        hash_[str(queryNodeLists)] = result
        return result

# hash_ = {}
# i = list(getNodeQueryStringByHash([["html"],["body"],["div", "div.gg"], ["b", "b.fd"]], hash_))
# print(len(i), len(set(i)))
# for _ in i:
#     print(_)
