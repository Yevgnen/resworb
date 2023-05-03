# -*- coding: utf-8 -*-

import abc
import urllib.request

import lxml.html

from resworb.base import URLItem


class Formatter(metaclass=abc.ABCMeta):
    def __call__(self, item: URLItem) -> URLItem:
        if self.match(item):
            return self.format(item)

        return item

    def match(self, item: URLItem) -> bool:
        raise NotImplementedError

    def format(self, item: URLItem) -> URLItem:
        raise NotImplementedError


class WeixinFormatter(Formatter):
    def match(self, item: URLItem) -> bool:
        return item["url"].startswith("https://mp.weixin.qq.com")

    def format(self, item: URLItem) -> URLItem:
        with urllib.request.urlopen(item["url"]) as io:
            parsed = lxml.html.parse(io)
            match = parsed.find("//h1[@class='rich_media_title']")
            title = match.text.strip() if match is not None else item["title"]

            return {**item, "title": title}
