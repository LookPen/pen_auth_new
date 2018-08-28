#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : generators.py
# @Author: Pen
# @Date  : 2018-08-28 16:00
# @Desc  : 生成相关属性的值

import random


class BaseHashGenerator:
    """
    生成器基类
    """
    UNICODE_ASCII_CHARACTER_SET = 'abcdefghijklmnopqrstuvwxyz' \
                                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                                  '0123456789'

    def hash(self):
        raise NotImplementedError()


class ClientIDGenerator(BaseHashGenerator):
    length = 40

    def hash(self):
        """
        随机取length 位UNICODE_ASCII_CHARACTER_SET 字符
        :return:
        """
        return ''.join(random.choice(self.UNICODE_ASCII_CHARACTER_SET) for i in range(self.length))


class ClientSecretGenerator(BaseHashGenerator):
    length = 128

    def hash(self):
        """
        随机取length 位UNICODE_ASCII_CHARACTER_SET 字符
        :return:
        """
        return ''.join(random.choice(self.UNICODE_ASCII_CHARACTER_SET) for i in range(self.length))
