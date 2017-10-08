# @Time         : 17-7-8 下午2:40
# @Author       : DioMryang
# @File         : RequestFunction.py
# @Description  : 请求函数
import requests
import chardet

from bs4 import BeautifulSoup
from TestRequest.Common import WINDOWS_HEADERS, TIMEOUT


def getHtmlSoupByRequest(url, headers=WINDOWS_HEADERS, timeout=TIMEOUT):
    """
    请求获取网页soup
    :param url: 请求链接
    :param headers: 浏览器头
    :return:
    """
    res = requests.get(url, headers=headers, timeout=timeout)
    res.encoding = chardet.detect(res.content)["encoding"]

    soup = BeautifulSoup(res.content, "lxml")
    return soup


def getHtmlSoupBySession(session, url, headers=WINDOWS_HEADERS, timeout=TIMEOUT):
    """
    请求获取网页soup
    :param session: 会话
    :param url: 请求链接
    :param headers: 浏览器头
    :return:
    """
    res = session.get(url, headers=headers, timeout=timeout)
    res.encoding = chardet.detect(res.content)["encoding"]

    soup = BeautifulSoup(res.content, "lxml")
    return soup
